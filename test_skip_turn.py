import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from main import app, manager
from constants import SUCCESS, FAILURE, STATUS

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_game(mocker):
    # Create a mock for the Game model
    mock_game = mocker.patch('main.Game')  # Adjust the path as necessary
    return mock_game

@pytest.fixture 
def mock_player(mocker):
    mock_player = mocker.patch('main.Player')
    return mock_player


@pytest.fixture
def mock_manager():
    """Mock the ConnectionManager"""
    with patch.object(manager, 'broadcast_in_game', new_callable=AsyncMock) as mock_broadcast:
        yield mock_broadcast

@pytest.mark.asyncio
async def test_skip_turn_success(client, mock_player, mock_game, mock_manager):

    mock_game_instance = mock_game.return_value
    mock_game_instance.id = 1
    mock_game_instance.current_player_id = 1
    mock_game_instance.is_init = True

    mock_player_instance = mock_player.return_value
    mock_player_instance.id = 1
    mock_player_instance.next = 2  # Ensure correct attribute name is mocked

    mock_game_instance.players = [mock_player_instance]
    # Ensure `Game.get()` and `Player.get()` return the mocked instances
    mock_game.get.return_value = mock_game_instance
    mock_player.get.return_value = mock_player_instance

    # Make the request with query params
    response = client.put(
        f"/skip_turn?game_id={mock_game_instance.id}&player_id={mock_player_instance.id}"
    )

    expected = {"message": "Player 1 skipped in game 1", STATUS: SUCCESS}

    assert response.status_code == 200
    assert response.json() == expected

