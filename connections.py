from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.player_sockets : list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.player_sockets.append(websocket)

    def disconnect(self, websocket : WebSocket):
        self.player_sockets.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.player_sockets:
            await connection.send_text(message)