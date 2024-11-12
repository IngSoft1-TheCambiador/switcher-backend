import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app, manager  # Adjust the import as necessary
from constants import STATUS, SUCCESS, FAILURE
from orm import DEFAULT_BOARD

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_game(mocker):
    # Create a mock for the Game model
    mock_game = mocker.patch('main.Game')
    return mock_game

@pytest.fixture
def mock_player(mocker):
    mock_player = mocker.patch('main.Player')
    return mock_player

@pytest.fixture
def mock_manager(mocker):
    # Mock the manager object that maps socket IDs to games
    mock_manager = mocker.patch('main.manager')
    return mock_manager

def test_game_state(client, mock_game, mock_player, mock_manager):
    mock_socket_id = 123
    mock_game_id = 5

    # Mock the manager's socket_to_game mapping
    mock_manager.socket_to_game = {mock_socket_id: mock_game_id}

    with patch('main.db_session'):

        # Mock the Game instance
        mock_game_instance = MagicMock()
        mock_game_instance.id = mock_game_id
        mock_game_instance.is_init = True
        mock_game_instance.current_player_id = 2
        mock_game_instance.owner_id = 1
        mock_game_instance.max_players = 4
        mock_game_instance.min_players = 2
        mock_game_instance.name = "Test Game"
        mock_game_instance.board = DEFAULT_BOARD
        mock_game_instance.old_board = DEFAULT_BOARD
        mock_game_instance.move_deck = ["mov1", "mov2"]
        mock_game_instance.forbidden_color = "RED"
        mock_game.get.return_value = mock_game_instance

        # Mock the Player instances and their attributes
        mock_player1 = MagicMock()
        mock_player1.id = 1
        mock_player1.name = "Player 1"
        mock_player1.color = "r"
        mock_player1.shapes = [MagicMock(shape_type="s1")]
        mock_player1.current_shapes = [MagicMock(shape_type="h1")]
        mock_player1.moves = [MagicMock(move_type="mov1")]
        mock_player1.shapes[0].id = 10
        mock_player1.current_shapes[0].id = 11

        mock_player2 = MagicMock()
        mock_player2.id = 2
        mock_player2.name = "Player 2"
        mock_player2.color = "b"
        mock_player2.shapes = [MagicMock(shape_type="s2")]
        mock_player2.current_shapes = [MagicMock(shape_type="h2")]
        mock_player2.moves = [MagicMock(move_type="mov2")]
        mock_player2.shapes[0].id = 20
        mock_player2.current_shapes[0].id = 21

        # Assign players to the game
        mock_game_instance.players = [mock_player1, mock_player2]

        # Simulate request to the game_state endpoint
        response = client.get(f"/game_state?socket_id={mock_socket_id}")
        
        # Expected JSON response
        expected_response = {
            "initialized": True,
            "player_ids": [1, 2],
            "current_player": 2,
            "player_names": {
                '1': "Player 1",
                '2': "Player 2"
            },
            "player_colors": {
                '1': "r",
                '2': "b"
            },
            "player_f_cards": {
                '1': ["s1"],
                '2': ["s2"]
            },
            "player_f_hand": {
                '1': ["h1"],
                '2': ["h2"]
            },
            "player_f_hand_blocked": {
                '1': [ {} ],
                '2': [ {} ]
            },
            "player_f_hand_ids": {
                '1': [11],
                '2': [21]
            },
            "player_f_deck_ids": {
                '1': [10],
                '2': [20]
            },
            "player_m_cards": {
                '1': ["mov1"],
                '2': ["mov2"]
            },
            "owner_id": 1,
            "max_players": 4,
            "min_players": 2,
            "name": "Test Game",
            "actual_board": DEFAULT_BOARD,
            "old_board": DEFAULT_BOARD,
            "move_deck": ["mov1", "mov2"],
            "highlighted_squares": "000000000000000000000000000000000000",
            "forbidden_color": "RED",
            STATUS: SUCCESS
        }

        # Assert that the response matches the expected output
        assert response.status_code == 200
        assert response.json() == expected_response

def test_game_state_socket_not_found(client, mock_manager):
    # Mock a socket ID that does not exist
    mock_socket_id = 999

    # Ensure the socket is not in the manager's mapping
    mock_manager.socket_to_game = {}

    response = client.get(f"/game_state?socket_id={mock_socket_id}")

    # Assert the error response when the socket is not found
    assert response.status_code == 200
    assert response.json() == {
        "error": "Socket not in a game",
        STATUS: FAILURE
    }
