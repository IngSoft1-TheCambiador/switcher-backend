import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from pony.orm import db_session, Set
from main import app, Game, Player  # Adjust import according to your project structure


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

def test_join_game(client, mock_game, mock_player):
    mock_game_id = 5
    mock_player_name = "Hi"
    mock_player_id = 10

    with patch('main.db_session'):
       
        mock_player_instance = MagicMock(Player)
        mock_player_instance.name = "John"

        mock_game_instance = MagicMock(Game)
        mock_game_instance.id = mock_game_id
        mock_game_instance.players = [mock_player_instance]
        mock_game_instance.max_players = 4
        mock_game_instance.create_player.return_value = mock_player_id
        
        mock_game.get.return_value = mock_game_instance
        
        response = client.post(f"/join_game?game_id={mock_game_id}&player_name={mock_player_name}")

        assert response.status_code == 200
        
        assert response.json() == {
            "player_id": mock_player_id,
            "game_id": mock_game_id,
            "message": f"Player {mock_player_id} joined the game {mock_game_id}"
        }

        # Optionally, check the call count or other properties on the mock
        assert mock_game_instance.create_player.called  # Ensures create_player was called


def test_join_game_errors(client, mock_game, mock_player):
    mock_game_id = 5
    mock_player_id = 10

    with patch('main.db_session'):
       
        # Mock the case where Game.get(id) is None; i.e. request to join non-existing 
        # game.
        mock_game.get.return_value = None
        response = client.post(f"/join_game?game_id=123123123&player_name=Anything")
        assert response.json() == {"error": "Game not found"}
       

        # Test "Game is full" error.
        mock_game_instance = MagicMock(Game)
        mock_game_instance.id = mock_game_id
        mock_game.get.return_value = mock_game_instance
        # We make len(players) > max_players; it's okay that the list does not 
        # contain player objects, the _join_game function does not reach any check of this
        # before raising the "Game is full" exception.
        mock_game_instance.players = [1, 2, 3, 4 ]
        mock_game_instance.max_players = 3
        response = client.post(f"/join_game?game_id={mock_game_id}&player_name=Anything")
        assert response.json() == {"error": "Game is already full"}

        # Test "A player with this name already exists in the game" error
        mock_game_instance.create_player.return_value = mock_player_id
        mock_player_instance = MagicMock(Player)
        mock_player_instance.name = "John"
        mock_game_instance.players = [mock_player_instance]
        
        response = client.post(f"/join_game?game_id={mock_game_id}&player_name=John")
        assert response.json() == {"error": "A player with this name already exists in the game"}
        
        assert not mock_game_instance.create_player.called  # Ensure player was NOT created
