from fastapi import WebSocket
import asyncio
from utils import notify_admin_error


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self.lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        # Снимаем срез под блокировкой, а саму отправку делаем уже без неё:
        # медленный или мёртвый клиент не должен блокировать остальных.
        async with self.lock:
            connections = list(self.active_connections)

        if not connections:
            return

        results = await asyncio.gather(
            *(connection.send_json(data) for connection in connections),
            return_exceptions=True,
        )

        disconnected = [
            connection
            for connection, result in zip(connections, results)
            if isinstance(result, Exception)
        ]

        if disconnected:
            async with self.lock:
                for connection in disconnected:
                    if connection in self.active_connections:
                        self.active_connections.remove(connection)
            await notify_admin_error(
                RuntimeError(f"ws broadcast: отключено соединений — {len(disconnected)}"),
                "ws broadcast",
            )


manager = ConnectionManager()
