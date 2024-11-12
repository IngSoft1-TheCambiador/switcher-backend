import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app, manager  
from constants import STATUS, SUCCESS
from datetime import datetime


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
def mock_message(mocker):
    mock_message = mocker.patch('main.PlayerMessage')
    return mock_message

@pytest.fixture
def mock_manager():
    """Mock the ConnectionManager"""
    with patch.object(manager, 'remove_from_game', new_callable=AsyncMock) as mock_add:
        yield mock_add


def test_send_message(client, mock_game, mock_player, mock_message, mock_manager):

    with patch('main.db_session'):
      
        player_a = mock_player.return_value 
        player_a.name = "A"
        player_a.id = 1
        player_a.color = "r"
        mock_player.get.return_value = player_a



        mock_game_instance = mock_game.return_value
        mock_game_instance.id = 100
        mock_game.get.return_value = mock_game_instance

        message = "This is a test message: Fran rocks! Mateo rocks! Juli rocks! Edu rocks! Santi rocks!"


        mock_message_instance = mock_message.return_value
        mock_message_instance.timestamp = datetime.strptime("00:00:00", '%H:%M:%S')
        
        response =client.post(f"/send_message?game_id={mock_game_instance.id}&sender_id={player_a.id}&txt={message}")

        assert response.status_code == 200
        assert response.json() == {
            "message": message,
            "sender_color": player_a.color,
            "sender_name": player_a.name,
            "time": "00:00",
            STATUS: SUCCESS
        }

        

