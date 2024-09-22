from fastapi.testclient import TestClient
from asyncio import run
import main

async def test_websocket():
    client = TestClient(main.app)
    with client.websocket_connect("/ws/connect") as websocket:
        data = websocket.receive_json()
        assert "new_id" in data.keys()
        assert data["msg"] == "Hello WebSocket"
        new_id = data["new_id"]
        await main.manager.disconnect(new_id)
    assert new_id not in main.manager.sockets_by_id

run(test_websocket())
