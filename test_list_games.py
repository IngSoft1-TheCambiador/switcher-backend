import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from pony.orm import db_session
from main import app  # Adjust import according to your project structure

PAGE_INTERVAL = 10  # Assuming this is defined somewhere in your application
# Response field names
PLAYER_ID = "player_id"
GAME_ID = "game_id"
PAGE_INTERVAL = 8 # Number of games listed per page
GAME_NAME = "game_name"
GAME_MIN = "min_players"
GAME_MAX = "max_players"
GAMES_LIST = "games_list"

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_game(mocker):
    # Create a mock for the Game model
    mock_game = mocker.patch('main.Game')  # Adjust the path as necessary
    return mock_game

def test_list_games(client, mock_game):
    # Create a mock for the Game model with proper attributes
    mock_game_instance_1 = MagicMock()
    mock_game_instance_1.id = 1
    mock_game_instance_1.name = 'Game 1'
    mock_game_instance_1.min_players = 2
    mock_game_instance_1.max_players = 3

    mock_game_instance_2 = MagicMock()
    mock_game_instance_2.id = 2
    mock_game_instance_2.name = 'Game 2'
    mock_game_instance_2.min_players = 3
    mock_game_instance_2.max_players = 4

    # Mock the behavior of the Game.select().order_by(Game.id)
    mock_games = [mock_game_instance_1, mock_game_instance_2]
    
    # Configure the mock to return the mock_games list
    mock_game.select.return_value.order_by.return_value = mock_games

    response = client.get("/list_games?page=1")
    assert response.status_code == 200

    print(response.json())
    expected_response = {
        GAMES_LIST: [
            {GAME_ID: 1, GAME_NAME: 'Game 1', GAME_MIN: 2, GAME_MAX: 3},
            {GAME_ID: 2, GAME_NAME: 'Game 2', GAME_MIN: 3, GAME_MAX: 4},
        ]
    }
    
    assert response.json() == expected_response
