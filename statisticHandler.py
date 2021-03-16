from math import ceil
from scipy.stats import chi2_contingency

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


    
# async def main():
#   # res = await createChiSquaredStatistic('$2b$10$WzUzmKnkqOW6OrG.I1Mxz.me/Y9xTiANzzbr6FovVL7jJFJbCLepW', 2, 3)
#   res = await calculateSampleSize(20000, 0.99, 0.05)
#   print(res)

# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())
# loop.close()


