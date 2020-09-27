import psycopg2
import psycopg2.extras
import os

from pathlib import Path
from dotenv import load_dotenv

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

def connect():
  try:
    conn = psycopg2.connect(database=os.getenv("POSTGRES_DBNAME"), user=os.getenv("POSTGRES_USERNAME"), password=os.getenv("POSTGRES_PASSWORD"), host=os.getenv("POSTGRES_ADDRESS"), port=os.getenv("POSTGRES_PORT"))
    return conn
  except Exception as error:
    print(error)
    raise Exception('Failed connecting to DB')

conn = connect()

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
    if cur:
      cur.close()

def getFromQuestionTable(questionnaireId, questionId):
  try:
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
    if cur:
      cur.close()

