import pygal
from pygal.style import Style
import asyncio
from asyncHandler import asyncTransform 

import databaseHandler

import os

from pathlib import Path
from dotenv import load_dotenv

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# get options info and question description
async def getChartInfo(questionnaireId, questionId):
  try:
    objResult = {}
    questionInfo = await asyncTransform(databaseHandler.getFromQuestionTable, questionnaireId, questionId)
    if ((questionInfo['type'] == 'checkbox') or (questionInfo['type'] == 'radio') ):
      optionInfo = await asyncTransform(databaseHandler.getFromOptionsTable, questionnaireId, questionId)
      objResult['optionInfo'] = optionInfo
      objResult['questionDesc'] = questionInfo['question_description']
      objResult['success'] = True
    else:
      objResult['success'] = False
    return objResult
  except Exception as error:
    print(error)
    raise Exception(error)

def renderPie(chartInfoObject):
  try:
    # styling
    custom_style = Style(
      title_font_size=3,
      legend_font_size=2,
      tooltip_font_size=3    #hover element
    )
    pie_chart = pygal.Pie(
      width=130, 
      height=130, 
      margin=10,
      legend_box_size=2, 
      tooltip_border_radius=1,
      style = custom_style)
    pie_chart.title = chartInfoObject['questionDesc']
    for i in range(len(chartInfoObject['optionInfo'])):
      optionObj = chartInfoObject['optionInfo'][i]
      pie_chart.add(optionObj['description'], optionObj['number_chosen'])
    filenameQuestionnairePart = chartInfoObject['optionInfo'][i]['questionnaire_id'].replace("/","")
    filenameQuestionnairePart =filenameQuestionnairePart.replace(".","")
    filenameQuestionPart = str(chartInfoObject['optionInfo'][i]['question_id'])
    directory = os.getenv("CHART_DIR") + 'chart-' + filenameQuestionnairePart + '-' + filenameQuestionPart + '.svg'
    pie_chart.render_to_file(directory)
    return directory
  except Exception as error:
    print(error)
    raise Exception(error)

async def asyncRenderHandler(questionnaireId, questionId):
  try:
    result = {}
    chartInfoObject = await getChartInfo(questionnaireId, questionId)
    if (not(chartInfoObject['success'])):
      result['success'] = False
    else:
      result['directory'] = await asyncTransform(renderPie, chartInfoObject)
      result['success'] = True
    return result
  except Exception as error:
    print(error)
    result = {}
    result['success'] = False
    return result
    
