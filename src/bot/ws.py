from fastapi import WebSocket
import asyncio


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
        async with self.lock:
            for connection in self.active_connections:
                try:
                    await connection.send_json(data)
                except Exception as e:
                    print(f"Ошибка при отправке сообщения: {e}")
                    await self.disconnect(connection)


manager = ConnectionManager()
