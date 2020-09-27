from asyncHandler import asyncTransform
import databaseHandler
import chartHandler
import asyncio
import time

async def main():
  #result1 =  asyncTransform(databaseHandler.getFromOptionsTable, '$2b$10$2UAoj3wreUWFoa/UaUBdlOZcbD34LJSZsIB69WmKAlu2OIUwEnQAG', 1)
  #result2 =  asyncTransform(databaseHandler.getFromQuestionTable, '$2b$10$2UAoj3wreUWFoa/UaUBdlOZcbD34LJSZsIB69WmKAlu2OIUwEnQAG', 1)
  #resultList = await asyncio.gather(result1, result2) #concurrent function call
  svgDir = await chartHandler.asyncRenderHandler('$2b$10$2UAoj3wreUWFoa/UaUBdlOZcbD34LJSZsIB69WmKAlu2OIUwEnQAG',5)
  #print(resultList[0])
  #print(resultList[1])
  print(svgDir)
  

if __name__ == '__main__':
  start_time = time.time()
  loop = asyncio.get_event_loop()
  loop.run_until_complete(main())
  print((time.time() - start_time) * 1000)