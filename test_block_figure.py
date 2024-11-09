import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app, manager
from orm import DEFAULT_BOARD, Color
from constants import STATUS, SUCCESS, FAILURE
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
def mock_manager():
    """Mock the ConnectionManager"""
    with patch.object(manager, 'broadcast_in_game', new_callable=AsyncMock) as mock_broadcast:
        yield mock_broadcast

@pytest.fixture
def mock_shapes_on_board(mocker):
    """Mock the shapes_on_board function"""
    mock_shapes = mocker.patch('wrappers.shapes_on_board')
    return mock_shapes

@pytest.fixture 
def mock_shape(mocker):
    mock_shape = mocker.patch("main.Shape")
    return mock_shape

@pytest.fixture 
def mock_move(mocker):
    mock_shape = mocker.patch("orm.Move")
    return mock_shape

@pytest.fixture 
def mock_message(mocker):
    mock_message = mocker.patch('main.Message')
    return mock_message

@pytest.fixture 
def mock_bool_board(mocker):
    mock_bool_board = mocker.patch("board_shapes.BooleanBoard")
    return mock_bool_board

def test_block_figure_success(client, mock_game, mock_player, mock_manager,
                              mock_shapes_on_board, mock_shape, mock_move,
                              mock_bool_board, mock_message):
    mock_game_id = 1
    mock_player_id = 10
    x, y = 0, 0
    fig_id = 666
    fig = "h1"

    with patch('main.db_session'):
        mock_shape_instance = mock_shape.return_value 
        mock_shape_instance.id = fig_id
        mock_shape_instance.shape_type = fig
        mock_shape_instance.is_blocked = False
        mock_shape.get.return_value = mock_shape_instance
        print(mock_shape_instance.shape_type)

        mock_player_instance = mock_player.return_value
        mock_player_instance.shapes = []
        mock_player_instance.current_shapes = [mock_shape_instance]

        movs = [mock_move.return_value]
        movs[0].move_type = "mov1"
        mock_player_instance.moves = movs
        mock_player.get.return_value = mock_player_instance

        # Mock message
        mock_message_instance = mock_message.return_value
        mock_message_instance.content = "i am a mockero, and i need a mock-hero"
        mock_message_instance.timestamp = datetime.strptime("00:00:00", '%H:%M:%S')

        # Setup mock game
        mock_game_instance = mock_game.return_value
        mock_game.get.return_value = mock_game_instance
        mock_game_instance.board = DEFAULT_BOARD
        mock_game_instance.get_block_color.return_value = Color.r 
        mock_game_instance.forbidden_color = Color.y
        mock_game_instance.current_player_id = mock_player_id

        print(mock_game_instance.board)

        # Create separate instances for mock_bool_board
        mock_bool_board_instance = mock_bool_board.return_value
        mock_bool_board_instance.shape_code = fig
        mock_bool_board_instance.board = [[1, 0, 0], [1, 1, 1], [1, 0, 0]]
        
        mock_shapes_on_board.return_value = [mock_bool_board_instance]


        response = client.put(f"/block_figure?game_id={mock_game_id}&player_id={mock_player_id}&fig_id={fig_id}&used_movs=mov1,mov2&x={x}&y={y}")

        assert response.status_code == 200
        assert response.json() == {
            "true_board": mock_game_instance.board,
            STATUS: SUCCESS
        }
        assert mock_game_instance.retrieve_player_move_cards.called
        assert mock_shape_instance.is_blocked is True
        assert mock_game_instance.forbidden_color == Color.r