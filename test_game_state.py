import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Mock Player class
class MockPlayer:
    def __init__(self, id, name, color, shapes, current_shapes, moves):
        self.id = id
        self.name = name
        self.color = color
        self.shapes = shapes  
        self.current_shapes = current_shapes  
        self.moves = moves  

class MockShape:
    def __init__(self, shape_type):
        self.shape_type = shape_type

class MockMove:
    def __init__(self, move_type):
        self.move_type = move_type

# Mock Game class
class MockGame:
    def __init__(self, id, name, is_init, players, current_player_id, owner_id, max_players, min_players, board, old_board, move_deck):
        self.id = id
        self.name = name
        self.is_init = is_init
        self.players = players
        self.current_player_id = current_player_id
        self.owner_id = owner_id
        self.max_players = max_players
        self.min_players = min_players
        self.board = board
        self.old_board = old_board
        self.move_deck = move_deck

@pytest.fixture
def mock_game():
    # Create mock players
    player1 = MockPlayer(1, "Player1", "Red", [MockShape("Circle")], [MockShape("Square")], [MockMove("Move1")])
    player2 = MockPlayer(2, "Player2", "Blue", [MockShape("Triangle")], [MockShape("Circle")], [MockMove("Move2")])

    # Create a mock game
    return MockGame(
        id=1,
        name="Test Game",
        is_init=True,
        players=[player1, player2],
        current_player_id=1,
        owner_id=1,
        max_players=4,
        min_players=2,
        board="Board data",
        old_board="Old board data",
        move_deck=["Move1", "Move2"]
    )

@patch('main.manager.socket_to_game', {1: 1})  # Mock socket to game mapping
@patch('orm.db_session', MagicMock())  
@patch('orm.Game.get')  
def test_game_state(mock_get, mock_game):
    mock_get.return_value = mock_game

    response = client.get("/game_state", params={"socket_id": 1})

    expected = {
        "initialized": True,
        "player_ids": [1, 2],
        "current_player": 1,
        "player_names": {'1': "Player1", '2': "Player2"},
        "player_colors": {'1': "Red", '2': "Blue"},
        "player_f_cards": {'1': ["Circle"], '2': ["Triangle"]},
        "player_f_hand": {'1': ["Square"], '2': ["Circle"]},
        "player_m_cards": {'1': ["Move1"], '2': ["Move2"]},
        "owner_id": 1,
        "max_players": 4,
        "min_players": 2,
        "name": "Test Game",
        "actual_board": "Board data",
        "old_board": "Old board data",
        "move_deck": ["Move1", "Move2"]
    }

    assert response.status_code == 200
    assert response.json() == expected
    mock_get.assert_called_once_with(id=1)

@patch('main.manager.socket_to_game', {})  # Mock an empty socket_to_game mapping
def test_game_state_invalid_socket():
    # Test the endpoint with an invalid socket_id
    response = client.get("/game_state", params={"socket_id": 999})

    # Assert the response is an error
    assert response.status_code == 200
    assert response.json() == {"error:": "Socket not in a game"}
