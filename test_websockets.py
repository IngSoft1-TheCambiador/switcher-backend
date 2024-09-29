from fastapi.testclient import TestClient
from asyncio import run
import main

def test_websocket():
    client = TestClient(main.app)
    with client.websocket_connect("/ws/connect") as websocket:
        data = websocket.receive_json()
        assert '1' in data.keys()
        assert data['1'] == "Hello WebSocket"
    assert 1 not in main.manager.sockets_by_id