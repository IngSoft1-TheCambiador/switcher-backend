import pytest
from unittest.mock import AsyncMock, Mock
from fastapi import WebSocket
from connections import ConnectionManager, LISTING_ID, PULL_GAMES, UPDATE_GAME, GAME_ENDED

@pytest.fixture
def connection_manager():
    return ConnectionManager()

@pytest.fixture
def mock_websocket():
    return AsyncMock(spec=WebSocket)

@pytest.mark.asyncio
async def test_connect(connection_manager, mock_websocket):
    socket_id = await connection_manager.connect(mock_websocket)
    
    assert socket_id == connection_manager.current_id
    assert connection_manager.sockets_by_id[socket_id] == mock_websocket
    assert socket_id in connection_manager.game_to_sockets[LISTING_ID]

@pytest.mark.asyncio
async def test_disconnect(connection_manager, mock_websocket):
    socket_id = await connection_manager.connect(mock_websocket)
    connection_manager.disconnect(socket_id)
    
    assert socket_id not in connection_manager.sockets_by_id
    assert socket_id not in connection_manager.game_to_sockets[LISTING_ID]

@pytest.mark.asyncio
async def test_send_personal_message(connection_manager, mock_websocket):
    socket_id = await connection_manager.connect(mock_websocket)
    
    message = "Hello, user!"
    await connection_manager.send_personal_message(socket_id, message)
    
    mock_websocket.send_text.assert_called_once_with(message)

@pytest.mark.asyncio
async def test_broadcast_in_game(connection_manager, mock_websocket):
    socket_id = await connection_manager.connect(mock_websocket)
    game_id = 1
    
    await connection_manager.add_to_game(socket_id, game_id)
    
    message = "Game update"
    await connection_manager.broadcast_in_game(game_id, message)
    
    assert mock_websocket.send_text.call_count == 2

@pytest.mark.asyncio
async def test_trigger_updates(connection_manager, mock_websocket):
    socket_id = await connection_manager.connect(mock_websocket)
    game_id = 1
    
    await connection_manager.add_to_game(socket_id, game_id)
    
    await connection_manager.trigger_updates(game_id)
    
    assert mock_websocket.send_text.call_count == 2

@pytest.mark.asyncio
async def test_end_game(connection_manager, mock_websocket):
    socket_id = await connection_manager.connect(mock_websocket)
    game_id = 1
    winner = "Player 1"
    
    await connection_manager.add_to_game(socket_id, game_id)
    
    await connection_manager.end_game(game_id, winner)
    
    assert mock_websocket.send_text.call_count == 3

