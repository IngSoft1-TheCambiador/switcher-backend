import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app, manager
from orm import DEFAULT_BOARD, Color
from constants import STATUS, SUCCESS, FAILURE

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_game(mocker):
    mock_game = mocker.patch('main.Game')
    return mock_game

def test_game_not_init(client, mock_game):
    mock_game_instance = mock_game.return_value
    mock_game.get.return_value = mock_game_instance
    mock_game_instance.is_init = False
    mock_game_instance.id = 1
    response = client.get(f"/get_current_time?game_id=1")
    assert response.json() == {"current_time": -1} 