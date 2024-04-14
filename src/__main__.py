import uvicorn
import uvloop
import sys
import pathlib
import logging


sys.path.append(str(pathlib.Path().resolve()) + '/src')
from config import env
from server import app


async def start_webhook():
    uvicorn.run('server:app', host='localhost',
                port=int(env.PORT.get_secret_value()), reload=True, log_level=logging.INFO)


if __name__ == "__main__":
    import asyncio
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.create_task(start_webhook())
    loop.run_forever()