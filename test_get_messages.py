import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock
from main import app, manager  
from constants import STATUS, SUCCESS
from datetime import datetime

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_game(mocker):
    mock_game = mocker.patch('main.Game')
    return mock_game

@pytest.fixture 
def mock_player(mocker):
    mock_player = mocker.patch('main.Player')
    return mock_player

@pytest.fixture 
def mock_message(mocker):
    mock_message = mocker.patch('main.Message')
    return mock_message

@pytest.fixture
def mock_manager():
    with patch.object(manager, 'remove_from_game', new_callable=AsyncMock) as mock_add:
        yield mock_add

def test_get_messages(client, mock_game, mock_player, mock_message, mock_manager):
    with patch('main.db_session'):
        # Mock the Game object
        mock_game_instance = mock_game.return_value
        mock_game_instance.id = 100
        mock_game.get.return_value = mock_game_instance

        # Mock the Player object
        player_a = mock_player.return_value
        player_a.name = "A"
        player_a.id = 1
        mock_player.get.return_value = player_a

        # Mock the Message instances with attributes
        message1 = Mock()
        message1.txt = "First message"
        message1.timestamp = datetime.strptime("00:00:00", '%H:%M:%S')
        message1.player = player_a

        message2 = Mock()
        message2.txt = "Second message"
        message2.timestamp = datetime.strptime("01:01:01", '%H:%M:%S')
        message2.player = player_a

        # Mock the select method to return our mock messages
        mock_message.select.return_value = [message1, message2]

        # Make the get request
        response = client.get(f"/get_messages?game_id={mock_game_instance.id}")

        assert response.status_code == 200
        response_json = response.json()
        print(response_json)
        
        # Check that response contains the expected messages in order
        assert response_json == {
            'message_list': ['{"message": "First message", "sender_id": 1, "sender_name": "A", "time": "00:00"}', '{"message": "Second message", "sender_id": 1, "sender_name": "A", "time": "01:01"}'], 'response_status': 0}
