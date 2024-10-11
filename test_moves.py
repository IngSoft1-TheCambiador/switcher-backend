import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from pony.orm import db_session, Set
from main import app, Game, Player  # Adjust import according to your project structure
from orm import DEFAULT_BOARD


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

def test_join_game(client, mock_game):
    mock_game_id = 5

    with patch('main.db_session'):
       
        mock_game_instance = MagicMock(Game)
        mock_game_instance.id = mock_game_id
        mock_game_instance.board = DEFAULT_BOARD
        mock_game_instance.old_board = DEFAULT_BOARD
        mock_game.__getitem__.return_value = mock_game_instance


        a, b, x, y = 0, 0, 3, 5
        
        response = client.post(f"/partial_move?game_id={mock_game_id}&a={a}&b={b}&x={x}&y={y}")
        assert response.status_code == 200
        
        assert response.json() == {
            "actual_board": "yrrrrrbbbbbbggggggyyyyyrrrrrrrbbbbbb",
            "old_board": "r" * 9 + "b" * 9 + "g" * 9 + "y" * 9
        }

        a, b, x, y = 0, 0, 5, 5
        # Optionally, check the call count or other properties on the mock
        assert mock_game_instance.exchange_blocks.called  # Ensures create_player was called


