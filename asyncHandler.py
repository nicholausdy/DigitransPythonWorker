import concurrent
import asyncio

def threadExecutor():
  try:
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    return executor
  except Exception as error:
    print(error)
    raise Exception('Failed getting thread executor')

executor = threadExecutor()

# Asterisk indicates excess positional argument
async def asyncTransform(functionName, *params):
  try:
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, functionName, *params)
    return result
  except Exception as error:
    print(error)
    raise Exception(error)

