from typing import List, Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel_id: str):
        await websocket.accept()
        if channel_id not in self.active_connections:
            self.active_connections[channel_id] = []
        self.active_connections[channel_id].append(websocket)

    def disconnect(self, websocket: WebSocket, channel_id: str):
        if channel_id in self.active_connections:
            self.active_connections[channel_id].remove(websocket)
            if not self.active_connections[channel_id]:
                del self.active_connections[channel_id]

    async def broadcast(self, message: str, channel_id: str):
        if channel_id in self.active_connections:
            for connection in self.active_connections[channel_id]:
                await connection.send_text(message)

manager = ConnectionManager()
