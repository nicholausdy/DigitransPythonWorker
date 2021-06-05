from math import ceil
from scipy.stats import chi2_contingency

import numpy as np
import pandas as pd

import asyncio
from asyncHandler import asyncTransform 

import databaseHandler

async def initializeContingencyTable(questionnaireId, questionIdInd, questionIdDep):
  try:
    indQuestion = asyncTransform(databaseHandler.getFromQuestionTable, questionnaireId, questionIdInd)
    depQuestion = asyncTransform(databaseHandler.getFromQuestionTable, questionnaireId, questionIdDep)
    aggregateQuery = await asyncio.gather(indQuestion, depQuestion)
    if ((aggregateQuery[0]['type'] != 'radio') or (aggregateQuery[1]['type'] != 'radio')):
      raise Exception('Invalid question type')

    indOptions = asyncTransform(databaseHandler.getFromOptionsTable, questionnaireId, questionIdInd)
    depOptions = asyncTransform(databaseHandler.getFromOptionsTable, questionnaireId, questionIdDep)
    aggregateOptionsQuery = await asyncio.gather(indOptions, depOptions)

    contingencyTable = []
    for i in range(len(aggregateOptionsQuery[0])):
      nestedTable = []
      for j in range(len(aggregateOptionsQuery[1])):
        nestedTable.append(0)
      contingencyTable.append(nestedTable)
    return contingencyTable

  except Exception as e:
    raise Exception(e.args[0])

async def incrementContingencyTable(indIndex, depIndex, answersIndDep):
  try:
    count = 0
    for i in range(len(answersIndDep)):
      if (len(answersIndDep[i]['ind_option']) != 0 and len(answersIndDep[i]['dep_option']) != 0):
        indOptionIdAns = answersIndDep[i]['ind_option'][0] 
        depOptionIdAns = answersIndDep[i]['dep_option'][0]
        if ((indOptionIdAns == indIndex) and (depOptionIdAns == depIndex)):
          count += 1
    return count
  
  except Exception as e:
    raise Exception(e.args[0])

async def createContingencyTableFromAnswers(questionnaireId, questionIdInd, questionIdDep):
  try:
    asyncContingencyTable = initializeContingencyTable(questionnaireId, questionIdInd, questionIdDep)
    asyncAnswersIndDep = asyncTransform(databaseHandler.getFromAnswersTableIndDep, questionnaireId, questionIdInd, questionIdDep)

    asyncAgg = await asyncio.gather(asyncContingencyTable, asyncAnswersIndDep)
    contingencyTable = asyncAgg[0]
    answersIndDep = asyncAgg[1]

    if (len(answersIndDep) == 0):
      raise Exception('Records are empty')
    
    for i in range(len(contingencyTable)):
      asyncOp = []
      for j in range(len(contingencyTable[i])):
        count = incrementContingencyTable(i, j, answersIndDep)
        asyncOp.append(count)
      asyncResult = await asyncio.gather(*asyncOp) # use asterisk to unpack list
      contingencyTable[i] = asyncResult

    return contingencyTable

  except Exception as e:
    raise Exception(e.args[0])

async def checkValidity(observedContingencyTable):
  try:
    for i in range(len(observedContingencyTable)):
      for j in range(len(observedContingencyTable[i])):
        if (observedContingencyTable[i][j] < 5):
          return False
    return True

  except Exception as e:
    raise Exception(e.args[0])


async def calculateChiSquared(questionnaireId, questionIdInd, questionIdDep):
  try:
    observedContingencyTable = await createContingencyTableFromAnswers(questionnaireId, questionIdInd, questionIdDep)
    aggResult = await asyncio.gather(checkValidity(observedContingencyTable), asyncTransform(chi2_contingency, observedContingencyTable, False))
    return {'isValid' : aggResult[0], 'chi2': aggResult[1][0], 'p': aggResult[1][1], 'dof': aggResult[1][2]}

  except Exception as e:
    errorString = str(e.args[0])
    isZeroElementFound = errorString.find('The internally computed table of expected frequencies has a zero element at')
    if (isZeroElementFound != -1):
      raise Exception('Jumlah sampel kurang banyak')
    raise Exception(e.args[0])
  
async def createChiSquaredStatistic(questionnaireId, questionIdInd, questionIdDep, confInterval):
  try:
    result = {}
    result['detail'] = {}
    chiSquaredStat = await calculateChiSquared(questionnaireId, questionIdInd, questionIdDep)
    result['detail']['chi2'] = chiSquaredStat['chi2']
    result['detail']['p'] = chiSquaredStat['p']
    result['detail']['dof'] =  chiSquaredStat['dof']

    if (not(chiSquaredStat['isValid'])):
      result['detail']['validity'] = 'Validitas hasil dipertanyakan karena ada frekuensi kategori bernilai di bawah 5'
    else:
      result['detail']['validity'] = 'Hasil valid'
    
    p_test = 1 - confInterval
    if (chiSquaredStat['p'] < p_test):
      result['message'] = 'Kedua variabel MUNGKIN BERHUBUNGAN'
    else:
      result['message'] = 'Kedua variabel TIDAK BERHUBUNGAN'
    result['success'] = True
    return result
  
  except Exception as e:
    return {'success': False, 'message': e.args[0]}

async def getZValue(conf_level):
  try:
    zValueDict = {
      0.8: 1.28,
      0.9: 1.645,
      0.95: 1.96,
      0.98: 2.33,
      0.99: 2.58
    }
    return zValueDict[conf_level]
  
  except Exception as e:
    raise Exception(e.args[0])

async def intermediateResCalc(conf_level, error_margin, sample_prop):
  try:
    # calculate (Z^2 * p * (1-p)) / e^2
    # assume p (sample_proportion) = 0.5
    z_value = await getZValue(conf_level)
    result = ((z_value**2) * sample_prop * (1 - sample_prop)) / (error_margin**2)
    return result
  
  except Exception as e:
    raise Exception(e.args[0])

async def calculateSampleSize(pop, conf_level, error_margin, sample_prop = 0.5):
  try:
    intermediate_res = await intermediateResCalc(conf_level, error_margin, sample_prop)
    sample_size = (pop * intermediate_res) / (pop - 1 + intermediate_res)
    return {'success': True, 'message': ceil(sample_size)}

  except Exception as e:
    return {'success': False, 'message': e.args[0]}

async def initializeScoreDict(questionnaireID, listOfQuestionID):
  try:
    scoresFromDB = await asyncTransform(databaseHandler.getQuestionsOptionsScoresForSelectedQuestions, questionnaireID, listOfQuestionID)
    dictResult = {}
    for i in range(len(scoresFromDB)):
      key1 = scoresFromDB[i]['question_id']
      key2 = scoresFromDB[i]['option_id']
      value = scoresFromDB[i]['score']

      if key1 not in dictResult:
        dictResult[key1] = {}

      dictResult[key1][key2] = value

    return dictResult

  except Exception as e:
    raise Exception(e.args[0])

async def createInputDictForCov(questionnareID, listOfQuestionID):
  try:
    scoreDict = await initializeScoreDict(questionnareID, listOfQuestionID)
    dictResult = {}
    for i in range(len(listOfQuestionID)):
      key = listOfQuestionID[i]
      dictResult[key] = []

    answersFromDB = await asyncTransform(databaseHandler.getAnswersForSelectedQuestions, questionnareID, listOfQuestionID)
    for i in range(len(answersFromDB)):
      key1 = answersFromDB[i]['question_id']
      key2 = answersFromDB[i]['option_id'][0]
      score = scoreDict[key1][key2]
      dictResult[key1].append(score)

    return dictResult 

  except Exception as e:
    raise Exception(e.args[0])

async def createCovMatrix(questionnaireID, listOfQuestionID):
  try:
    # create correlation matrix from dict containing list of scores for each questions
    inputDictForCov = await createInputDictForCov(questionnaireID, listOfQuestionID)
    df = await asyncTransform(pd.DataFrame, inputDictForCov)
    covMatrix = await asyncTransform(df.cov)
    return covMatrix

  except Exception as e:
    raise Exception(e.args[0])

async def calculateCovMeanAndVarMean(questionnareID, listOfQuestionID):
  try:
    covMatrix = await createCovMatrix(questionnareID, listOfQuestionID)
    listOfVar = []
    for i in range(len(listOfQuestionID)):
      variance = covMatrix.at[listOfQuestionID[i], listOfQuestionID[i]]
      listOfVar.append(variance)
      covMatrix.at[listOfQuestionID[i], listOfQuestionID[i]] = np.NaN

    mean_var = await asyncTransform(np.mean, listOfVar)
    mean_covs_cols = await asyncTransform(covMatrix.mean)
    mean_covs = await asyncTransform(mean_covs_cols.mean)
    return mean_var, mean_covs

  except Exception as e:
    raise Exception(e.args[0])

async def calculateCronbachAlpha(questionnaireID, listOfQuestionID):
  try:
    n = len(listOfQuestionID)
    mean_var, mean_covs = await calculateCovMeanAndVarMean(questionnaireID, listOfQuestionID)
    cronbach_alpha = (n * mean_covs) / (mean_var + (n-1) * mean_covs)
    cronbach_alpha = round(cronbach_alpha, 2)
    consistency = await cronbachConsistency(cronbach_alpha)
    return {'success': True, 'message':{'cronbach_alpha': cronbach_alpha, 'consistency': consistency}}

  except Exception as e:
    return {'success': False, 'message': 'Kalkulasi gagal. Pastikan semua responden menjawab semua pertanyaan yang dimasukkan (tidak ada jawaban kosong) serta dimasukkan lebih dari 1 pertanyaan'}
  
    
async def cronbachConsistency(cronbach_alpha):
  try:
    if (cronbach_alpha >= 0.9):
      return 'Sangat Baik / Excellent'
    elif ((cronbach_alpha >= 0.8) and (cronbach_alpha < 0.9)):
      return 'Baik / Good'
    elif ((cronbach_alpha >= 0.7) and (cronbach_alpha < 0.8)):
      return 'Dapat diterima / Acceptable'
    elif ((cronbach_alpha >=0.6) and (cronbach_alpha < 0.7)):
      return 'Dipertanyakan / Questionable'
    elif ((cronbach_alpha >=0.5) and (cronbach_alpha < 0.6)):
      return 'Buruk / Poor'
    else:
      return 'Tidak bisa diterima / Unacceptable'

  except Exception as e:
    raise Exception(e.args[0])

# async def main():
#   # res = await createChiSquaredStatistic('$2b$10$WzUzmKnkqOW6OrG.I1Mxz.me/Y9xTiANzzbr6FovVL7jJFJbCLepW', 2, 3)
#   # res = await calculateSampleSize(20000, 0.99, 0.05)
#   res = await calculateCronbachAlpha('$2b$10$WzUzmKnkqOW6OrG.I1Mxz.me/Y9xTiANzzbr6FovVL7jJFJbCLepW',[3,4,5,6,7])
#   print(res)

# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())
# loop.close()


