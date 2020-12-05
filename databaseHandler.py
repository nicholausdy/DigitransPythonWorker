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

