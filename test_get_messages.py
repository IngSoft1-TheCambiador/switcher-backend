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
        mock_game_instance1 = Mock()
        mock_game_instance2 = Mock()
        mock_game_instance1.id = 100
        mock_game_instance2.id = 20
        mock_game.get.return_value = mock_game_instance1

        # Mock the Player object
        player_a = Mock()
        player_b = Mock() 
        player_c = Mock()

        player_a.name = "A"
        player_b.name = "B"
        player_c.name = "C"
        player_a.color = "r"
        player_b.color = "b"
        player_c.color = "g"
        player_a.id = 1
        player_b.id = 2
        player_c.id = 3
        player_a.game = mock_game_instance1
        player_b.game = mock_game_instance1
        player_c.game = mock_game_instance2

        # Mock the Message instances with attributes
        message1 = Mock()
        message1.content = "First message"
        message1.timestamp = datetime.strptime("00:00:00", '%H:%M:%S')
        message1.game = mock_game_instance1
        message1.player = player_a

        message2 = Mock()
        message2.content = "Second message"
        message2.timestamp = datetime.strptime("01:01:01", '%H:%M:%S')
        message2.game = mock_game_instance1
        message2.player = player_b

        message3 = Mock()
        message3.content = "Third message, in another game"
        message3.timestamp = datetime.strptime("09:23:47", '%H:%M:%S')
        message3.game = mock_game_instance2
        message3.player = player_c

        log1 = Mock()
        log1.content = "A ha saltado su turno. Te toca, B!"
        log1.timestamp = datetime.strptime("00:30:00", '%H:%M:%S')
        log1.game = mock_game_instance1
        log1.player = player_a
        log1.log = True

        log2 = Mock()
        log2.content = "B ha usado: &?&B ha completado la figura: "
        log2.timestamp = datetime.strptime("01:01:03", '%H:%M:%S')
        log2.game = mock_game_instance1
        log2.player = player_b
        log2.log = True
        log2.played_cards = ["h7", "mov2", "mov7"]
        
        log3 = Mock()
        log3.content = "C le ha bloqueado a CBrother la figura: "
        log3.timestamp = datetime.strptime("05:55:55", '%H:%M:%S')
        log3.game = mock_game_instance2
        log3.player = player_c
        log3.log = True
        log3.played_cards = ["h5"]

        # Mock the select method to return our mock messages
        """ 
        me parece que no deberia forzarse esto, porque hay que testear que 
        el endpoint devuelva solo la lista de mensajes de la partida con el game_id
        del request

        mock_message.select.return_value = [message1, message2]

        """
        # Make the get request
        response = client.get(f"/get_messages?game_id={mock_game_instance1.id}")

        assert response.status_code == 200
        response_json = response.json()
        print(message1.game.id)
        print(message2.game.id)
        print(message3.game.id)
        print(log1.game.id)
        print(log2.game.id)
        print(log3.game.id)
        print(player_a.color)
        print(player_b.name)
        print(player_c.id)
        print(log2.played_cards)
        print(mock_game_instance1.id)
        print(response_json)
        
        # Check that response contains the expected messages in order
        assert response_json == {
            'message_list': [{
                                "sender": "A",
                                "color": "r",
                                "message": "First message",
                                "time": "00:00"
                            },
                            {
                                "sender": "Log",
                                "color": "log",
                                "message": "A ha saltado su turno. Te toca, B!",
                                "time": "00:30",
                                "cards": [],
                            },
                            {
                                "sender": "B",
                                "color": "b",
                                "message": "Second message",
                                "time": "01:01"
                            },
                            {
                                "sender": "Log",
                                "color": "log",
                                "message": "B ha usado: &?&B ha completado la figura: ",
                                "time": "01:01",
                                "cards": ["h7", "mov2", "mov7"],
                            }
                            ], 
            'response_status': 0}
