import uvicorn
import sys
import pathlib
import logging

sys.path.append(str(pathlib.Path().resolve()) + "/src")
from server import app


async def start_webhook():
    try:
        uvicorn.run(
            "server:app",
            host="127.0.0.1",
            port=8080,
            reload=True,
            log_level=logging.INFO,
        )
    except Exception as e:
        logging.error(f"ERROR {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(start_webhook())
