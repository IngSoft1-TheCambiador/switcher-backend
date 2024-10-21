import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app, manager  
from constants import STATUS, SUCCESS

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_game(mocker):
    # Create a mock for the Game model
    mock_game = mocker.patch('main.Game')  # Adjust the path as necessary
    return mock_game


@pytest.fixture
def mock_manager():
    """Mock the ConnectionManager"""
    with patch.object(manager, 'add_to_game', new_callable=AsyncMock) as mock_add:
        yield mock_add

def test_start_game(client, mock_game, mock_manager):

    with patch('main.db_session'):
       

        mock_game_instance = mock_game.return_value
        mock_game_instance.id = 666
        mock_game.get.return_value = mock_game_instance
        
        response = client.put(f"/start_game?game_id={mock_game_instance.id}")

        assert response.status_code == 200
        
        assert response.json() == {
            "message": "Starting 666",
            STATUS: SUCCESS
        }

        assert mock_game_instance.initialize.called  # Ensures create_player was called


