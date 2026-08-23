import logging
import pathlib
import sys

import uvicorn

sys.path.append(str(pathlib.Path().resolve()) + "/src")

# Импорт проверяет, что приложение вообще собирается, до старта сервера.
from server import app  # noqa: F401

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    # uvicorn.run() сам создаёт и запускает event loop.
    # Раньше он вызывался внутри asyncio.run(), из-за чего старт падал с
    # "asyncio.run() cannot be called from a running event loop",
    # а контейнер уходил в бесконечный перезапуск.
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8081,
        log_level="info",
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
