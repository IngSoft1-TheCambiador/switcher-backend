import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock
from main import app, manager  
from constants import STATUS, SUCCESS, FAILURE
from orm import Player, Game, LogMessage
import datetime

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
def mock_log_message(mocker):
    mock_msg = mocker.patch('main.LogMessage')
    return mock_msg

@pytest.fixture
def mock_manager():
    """Mock the ConnectionManager"""
    with patch.object(manager, 'add_to_game', new_callable=AsyncMock) as mock_add:
        yield mock_add

def test_join_game(client, mock_game, mock_player, mock_log_message, mock_manager):
    mock_game_id = 5
    mock_player_name = "Hi"
    mock_player_id = 10

    with patch('main.db_session'):
       
        mock_player_instance = mock_player.return_value
        mock_player_instance.name = "John"
        mock_player_instance.id = 5

        mock_game_instance = mock_game.return_value
        mock_game_instance.owner_id = mock_player_instance.id
        mock_game_instance.players = [mock_player_instance]
        mock_game_instance.max_players = 4
        mock_game_instance.create_player.return_value = mock_player_id
        
        mock_game.get.return_value = mock_game_instance
        
        response = client.post(f"/join_game?socket_id={0}&game_id={mock_game_id}&player_name={mock_player_name}")

        assert response.status_code == 200
        
        assert response.json() == {
            "player_id": mock_player_id,
            "owner_id": mock_game_id,
            "player_names": ["John"],
            STATUS: SUCCESS
        }

        assert mock_game_instance.create_player.called  # Ensures create_player was called


def test_game_already_full(client, mock_game, mock_player, mock_manager):
    mock_game_id = 5

    with patch('main.db_session'):
       
        # Mock the case where Game.get(id) is None; i.e. request to join non-existing 
        # game.
        mock_game.get.return_value = None
        response = client.post("/join_game?socket_id=0&game_id=123123123&player_name=Anything")
        assert response.json() == {"error": "Game not found", STATUS: FAILURE}
       

        # Test "Game is full" error.
        mock_game_instance = mock_game.return_value
        mock_game_instance.id = mock_game_id
        mock_game.get.return_value = mock_game_instance
        # We make len(players) > max_players; it's okay that the list does not 
        # contain player objects, the _join_game function does not reach any check of this
        # before raising the "Game is full" exception.
        mock_game_instance.players = [1, 2, 3, 4]
        mock_game_instance.max_players = 4
        response = client.post(f"/join_game?socket_id={0}&game_id={mock_game_id}&player_name=Anything")
        assert response.json() == {"error": "Game is already full",
                                   STATUS: FAILURE}

def test_invalid_password(client, mock_game, mock_player, mock_manager):
    mock_game_id = 5

    with patch('main.db_session'):

        mock_player_instance = mock_player.return_value
        mock_player_instance.name = "John"
        mock_player_instance.id = 5

        mock_game_instance = mock_game.return_value
        mock_game_instance.owner_id = mock_player_instance.id
        mock_game_instance.players = [mock_player_instance]
        mock_game_instance.max_players = 4
       
        mock_game_instance = mock_game.return_value
        mock_game_instance.password = "TheCorrectPassword1"
        
        mock_game.get.return_value = mock_game_instance
        
        response = client.post(f"/join_game?socket_id={0}&game_id={mock_game_id}&player_name=John&password=TheIncorrectPassword2")

        assert response.status_code == 200
        
        assert response.json() == {
            "error": "Incorrect password",
            STATUS: FAILURE
        }

        assert not mock_game_instance.create_player.called  # Ensures create_player was called


def test_rejoin(client, mock_game, mock_player, mock_manager):

    with patch('main.db_session'):
     
        player_a = Mock(spec=Player)
        player_b = Mock(spec=Player)

        player_a.name = "A"
        player_a.id = 1
        player_a.next = player_b
        player_b.name = "B"

        mock_game_instance = mock_game.return_value
        mock_game_instance.current_player = player_b
        mock_game_instance.id = 100
        mock_game_instance.owner_id = player_a.id
        mock_game_instance.players = [player_a, player_b]
        mock_game_instance.max_players = 4
        mock_game.get.return_value = mock_game_instance

        mock_player.get.return_value = player_a
        
        response = client.post(f"/join_game?socket_id={1}&game_id={mock_game_instance.id}&player_name={player_a.name}&player_id={player_a.id}")

        assert response.status_code == 200
        assert response.json() == { 
            "player_id": player_a.id,
            "owner_id": mock_game_instance.owner_id,
            "player_names": [p.name for p in mock_game_instance.players],
            STATUS: SUCCESS
        }

# This tests includes that the win event is correctly called
def test_join_different_game(client, mock_game, mock_player, mock_log_message, mock_manager):

    with patch('main.db_session'), \
        patch('main.trigger_win_event', new_callable=AsyncMock) as mock_trigger_win_event:

        log_msg = Mock(spec=LogMessage)
     
        player_a = mock_player.return_value

        player_a.name = "A"
        player_a.id = 1
        player_b = Mock(spec=Player)
        player_c = Mock(spec=Player)
        player_b.name = "B"
        player_b.id = 2
        player_c.name = "C"
        player_c.id = 3

        game_1 = Mock(spec=Game)
        game_2 = Mock(spec=Game)


        # A game with player_a
        game_1.current_player = player_a
        game_1.id = 100
        game_1.owner_id = player_b.id
        game_1.players = [player_a, player_b]
        game_1.max_players = 4
        game_1.is_init = True

        # A game without player_a
        game_2.current_player = player_b
        game_2.id = 101
        game_2.owner_id = player_b.id
        game_2.players = [player_b, player_c]
        game_2.max_players = 4
        game_2.is_init = False
        game_2.password = ""

        assert player_a not in game_2.players
        
        log_msg.content = "Abandono partida"
        log_msg.game = game_1.id,
        log_msg.timestamp = datetime.datetime.now()
        mock_log_message.return_value = log_msg


        mock_game.get.return_value = game_2
        mock_game.select.return_value = [game_1]
        mock_player.get.return_value = player_a


        game_2.create_player.return_value = 123
        
        response = client.post(f"/join_game?socket_id={1}&game_id={game_2.id}&player_name={player_a.name}&player_id={player_a.id}")

        assert response.status_code == 200
        assert player_a not in game_1.players

        mock_trigger_win_event.assert_called_once_with(game_1, player_b)

        assert response.json() == { 
            "player_id": 123,
            "owner_id": game_2.owner_id,
            "player_names": [p.name for p in game_2.players],
            "is_init": game_2.is_init,
            STATUS: SUCCESS
        }

