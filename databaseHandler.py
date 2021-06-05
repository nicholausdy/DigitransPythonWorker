import psycopg2
import psycopg2.extras
from psycopg2_pool import ThreadSafeConnectionPool
import os

from pathlib import Path
from dotenv import load_dotenv

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

dsn = "dbname=" + os.getenv("POSTGRES_DBNAME") + " user=" + os.getenv("POSTGRES_USERNAME") + " host=" + os.getenv("POSTGRES_ADDRESS") + " port=" + os.getenv("POSTGRES_PORT") + " password=" + os.getenv("POSTGRES_PASSWORD")
db_pool = ThreadSafeConnectionPool(minconn=4, dsn=dsn)


def transformToListofDict(cursorResult):
  try:
    result = []
    for row in cursorResult:
      result.append(dict(row))
    return result
  except Exception as error:
    print(error)
    raise Exception('Transform to list of dict failed')

def getFromOptionsTable(questionnaireId, questionId):
  try:
    conn = db_pool.getconn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('''select * from options where questionnaire_id = %s
AND question_id = %s''', (questionnaireId, questionId))
    cursorResult = cur.fetchall()
    if (not(cursorResult)):
      raise Exception('Empty record')
    return transformToListofDict(cursorResult)
  except Exception as error:
    print(error)
    raise Exception('Failed getting result')
  finally:
    if conn:
      cur.close()
      db_pool.putconn(conn)

def getFromQuestionTable(questionnaireId, questionId):
  try:
    conn = db_pool.getconn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('''select * from questions where questionnaire_id = %s
AND question_id = %s''', (questionnaireId, questionId))
    cursorResult = cur.fetchone()
    if (not(cursorResult)):
      raise Exception('Empty record')
    return dict(cursorResult)
  except Exception as error:
    print(error)
    raise Exception('Failed getting result')
  finally:
    if conn:
      cur.close()
      db_pool.putconn(conn)

def getFromAnswersTableIndDep(questionnaireId, questionIdInd, questionIdDep):
  try:
    conn = db_pool.getconn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('''select A.answerer_email, A.option_id as ind_option, B.option_id as dep_option  from answers as A inner join answers as B 
on A.answerer_email = B.answerer_email
where A.questionnaire_id = %s
AND B.questionnaire_id = %s
AND A.question_id = %s
AND B.question_id = %s''', (questionnaireId, questionnaireId, questionIdInd, questionIdDep))
    cursorResult = cur.fetchall()
    if (not(cursorResult)):
      raise Exception('Empty record')
    return transformToListofDict(cursorResult)
  except Exception as error:
    print(error)
    raise Exception('Failed getting result')
  finally:
    if conn:
      cur.close()
      db_pool.putconn(conn)

def getFromAnswersTable(questionnaireId):
  try:
    conn = db_pool.getconn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('''select * from answers where questionnaire_id = %s 
ORDER BY question_id''', (questionnaireId,))
    cursorResult = cur.fetchall()
    if (not(cursorResult)):
      raise Exception('Empty record')
    return transformToListofDict(cursorResult)
  except Exception as error:
    print(error)
    raise Exception('Failed getting result')
  finally:
    if conn:
      cur.close()
      db_pool.putconn(conn)

def manyConditionIterator(listOfCols, listOfOperator, listofCondition):
  #Example:
  #listOfCols = ['bananaID', 'appleID', 'orangeID']
  #listofCondition = ['banana3','apple2','orange1']
  #listOfOperator = ['AND','OR']
  #output: "(bananaID = 'banana3' AND appleID = 'apple2' OR orangeID = 'orange1')""
  try:
    if ((len(listOfCols) == 0) or (len(listofCondition) == 0) or (len(listOfOperator) == 0)):
      raise Exception('No empty list allowed')
    if ((len(listOfCols) != len(listofCondition)) or (len(listofCondition) - 1 != len(listOfOperator))):
      raise Exception('Size of cols should be equal to condition AND size of operators equals to size of conditions - 1')

    text = '(' + listOfCols[0] +' = '+ listofCondition[0] + ' '
    for i in range(1, len(listOfCols)):
      text = text + listOfOperator[i-1] + ' ' + listOfCols[i] +' = '+ listofCondition[i] + ' '
    text = text + ')'
    return text

  except Exception as e:
    print(e)
    raise Exception(e.args[0])

def getQuestionsOptionsScoresForSelectedQuestions(questionnaireID, listOfQuestionID):
  try:
    query = '''select questionnaire_id, question_id, option_id, score from options
    WHERE questionnaire_id =%s AND'''

    listOfCols = []
    listOfCondition = []
    listOfOperator = []
    for i in range(len(listOfQuestionID)):
      listOfCols.append('question_id')
      listOfCondition.append(str(listOfQuestionID[i]))
    for i in range(len(listOfQuestionID)-1):
      listOfOperator.append('OR')

    query_ext = manyConditionIterator(listOfCols, listOfOperator, listOfCondition)
    query = query + ' ' + query_ext

    conn = db_pool.getconn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(query, (questionnaireID,))
    cursorResult = cur.fetchall()

    if (not(cursorResult)):
      raise Exception('Empty record')
    return transformToListofDict(cursorResult)

  except Exception as e:
    print(e)
    raise Exception(e.args[0])

  finally:
    if conn:
      cur.close()
      db_pool.putconn(conn)

def getAnswersForSelectedQuestions(questionnaireID, listOfQuestionID):
  try:
    query = '''select question_id, option_id from answers
    WHERE questionnaire_id =%s AND'''

    listOfCols = []
    listOfCondition = []
    listOfOperator = []
    for i in range(len(listOfQuestionID)):
      listOfCols.append('question_id')
      listOfCondition.append(str(listOfQuestionID[i]))
    for i in range(len(listOfQuestionID)-1):
      listOfOperator.append('OR')

    query_ext = manyConditionIterator(listOfCols, listOfOperator, listOfCondition)
    query = query + ' ' + query_ext

    conn = db_pool.getconn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(query, (questionnaireID,))
    cursorResult = cur.fetchall()

    if (not(cursorResult)):
      raise Exception('Empty record')
    return transformToListofDict(cursorResult)

  except Exception as e:
    print(e)
    raise Exception(e.args[0])

  finally:
    if conn:
      cur.close()
      db_pool.putconn(conn)

# def main():
#   result = getQuestionsOptionsScoresForSelectedQuestions('$2b$10$WzUzmKnkqOW6OrG.I1Mxz.me/Y9xTiANzzbr6FovVL7jJFJbCLepW', [3,4,5,6,7,8])
#   print(result)
#   print(len(result))
#   result2 = getAnswersForSelectedQuestions('$2b$10$WzUzmKnkqOW6OrG.I1Mxz.me/Y9xTiANzzbr6FovVL7jJFJbCLepW', [3,4,5,6,7,8])
#   print(result2)
#   print(len(result2))

# main()

