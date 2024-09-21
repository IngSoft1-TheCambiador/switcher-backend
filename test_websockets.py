from fastapi.testclient import TestClient
import main

def test_websocket():
    client = TestClient(main.app)
    with client.websocket_connect("/ws/connect") as websocket:
        data = websocket.receive_json()
        assert data == {"msg": "Hello WebSocket"}
        assert main.manager.player_sockets != []
        websocket.close()
    assert main.manager.player_sockets == []