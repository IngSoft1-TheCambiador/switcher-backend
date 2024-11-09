import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app, manager  
from constants import STATUS, SUCCESS, FAILURE


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
    with patch.object(manager, 'add_to_game', new_callable=AsyncMock) as mock_add:
        yield mock_add

def test_join_game(client, mock_game, mock_player, mock_manager):
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
