import asyncio
import pandas as pd
from asyncHandler import asyncTransform 

from databaseHandler import getFromAnswersTable

import os

from pathlib import Path
from dotenv import load_dotenv

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

async def createAnswersDataFrame(questionnaireId):
  try:
    answersListOfDict = await asyncTransform(getFromAnswersTable, questionnaireId)
    answersDataFrame = await asyncTransform(pd.DataFrame, answersListOfDict)
    return answersDataFrame

  except Exception as e:
    raise Exception(e.args[0])

def saveDataFrameAsXls(questionnaireId, answersDataFrame):
  try:
    filenameAnswersPart = questionnaireId.replace("/","")
    filenameAnswersPart = filenameAnswersPart.replace(".","")
    directory = os.getenv("SPREADSHEET_DIR") + 'answers-' + filenameAnswersPart +'.xlsx'
    answersDataFrame.to_excel(directory, index=False)
    return directory
  
  except Exception as e:
    raise Exception(e.args[0])

def saveDataFrameAsCSV(questionnaireId, answersDataFrame):
  try:
    filenameAnswersPart = questionnaireId.replace("/","")
    filenameAnswersPart = filenameAnswersPart.replace(".","")
    directory = os.getenv("SPREADSHEET_DIR") + 'answers-' + filenameAnswersPart +'.csv'
    answersDataFrame.to_csv(directory, index=False)
    return directory

  except Exception as e:
    raise Exception(e.args[0])


async def saveAnswersAsSpreadsheet(questionnaireId, spreadSheetFormat):
  try:
    answersDataFrame = await createAnswersDataFrame(questionnaireId)
    selector = {
      "xlsx": saveDataFrameAsXls,
      "csv": saveDataFrameAsCSV
    }
    directory = await asyncTransform(selector[spreadSheetFormat], questionnaireId, answersDataFrame)
    return {"success": True, "message": directory}
  
  except Exception as e:
    return {"success": False, "message": e.args[0]}


# async def main():
#   res1 = await saveAnswersAsSpreadsheet('$2b$10$WzUzmKnkqOW6OrG.I1Mxz.me/Y9xTiANzzbr6FovVL7jJFJbCLepW', 'xls')
#   res2 = await saveAnswersAsSpreadsheet('$2b$10$WzUzmKnkqOW6OrG.I1Mxz.me/Y9xTiANzzbr6FovVL7jJFJbCLepW','csv')
#   print(res1)
#   print(res2)

# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())
# loop.close()



