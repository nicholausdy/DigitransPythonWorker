import asyncio
import json
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout, ErrNoServers 

from chartHandler import asyncRenderHandler
from statisticHandler import createChiSquaredStatistic

import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

url = os.getenv("NATS_URL")

async def runEventListener(loop):
  try:
    nc = NATS()
    await nc.connect(url, loop=loop)

    async def chart_handler(msg):
      try:
        reply = msg.reply
        data = json.loads(msg.data.decode())
        procResult = await asyncRenderHandler(data['questionnaire_id'], data['question_id'], data['chart_type'])
        await nc.publish(reply, json.dumps(procResult).encode())
      except (ErrConnectionClosed, ErrTimeout, ErrNoServers) as error:
        raise Exception(error)   

    async def stat_handler(msg):
      try:
        reply = msg.reply
        data = json.loads(msg.data.decode())
        procResult = await createChiSquaredStatistic(data['questionnaire_id'], data['ind_question_id'], data['dep_question_id'])
        await nc.publish(reply, json.dumps(procResult).encode())
      except (ErrConnectionClosed, ErrTimeout, ErrNoServers) as error:
        raise Exception(error)   

    chartRequestListener = await nc.subscribe("chartCall", "chart.workers", chart_handler)
    statRequestListener = await nc.subscribe("statisticCall", "stat.workers", stat_handler)
    
  except Exception as error:
    print(error)

def eventListener():
  loop = asyncio.get_event_loop()
  try:
    asyncio.ensure_future(runEventListener(loop)) 
    loop.run_forever()
  except KeyboardInterrupt:
    pass
  finally:
    print("Closing loop")
    loop.close()

eventListener() 
