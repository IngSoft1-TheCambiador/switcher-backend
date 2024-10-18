import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from pony.orm import db_session
from main import app, manager
from orm import Shape, DEFAULT_BOARD
from constants import STATUS, SUCCESS, FAILURE

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
    mock_shapes = mocker.patch('main.shapes_on_board')
    return mock_shapes

@pytest.fixture 
def mock_shape(mocker):
    mock_shape = mocker.patch("orm.Shape")
    return mock_shape

def test_claim_figure_success(client, mock_game, mock_player, mock_manager, mock_shapes_on_board, mock_shape):
    mock_game_id = 1
    mock_player_id = 10
    x, y = 0, 0
    fig = "h1"

    with patch('main.db_session'):
        mock_shape_instance = mock_shape.return_value 
        mock_shape_instance.shape_type = fig
        # Setup mock player
        mock_player_instance = mock_player.return_value
        mock_player_instance.shapes = []
        mock_player_instance.current_shapes = [mock_shape_instance]

        # Setup mock game
        mock_game_instance = mock_game.return_value
        mock_game.get.return_value = mock_game_instance
        mock_player.get.return_value = mock_player_instance
        mock_game_instance.board = DEFAULT_BOARD

        # Mock the shapes on board to return the matching figure at position (x, y)
        mock_shapes_on_board.return_value = {fig: [[1, 0, 0], [1, 1, 1], [1, 0, 0]]}

        response = client.put(f"/claim_figure?game_id={mock_game_id}&player_id={mock_player_id}&fig={fig}&x={x}&y={y}")

        assert response.status_code == 200
        assert response.json() == {
            "true_board": mock_game_instance.board,
            STATUS: SUCCESS
        }


def test_claim_figure_game_or_player_not_found(client, mock_game, mock_player):
    mock_game_id = 1
    mock_player_id = 10
    fig = "h1"
    x, y = 5, 5

    with patch('main.db_session'):
        # Mock the case where the game or player does not exist
        mock_game.get.return_value = None
        mock_player.get.return_value = None

        response = client.put(f"/claim_figure?game_id={mock_game_id}&player_id={mock_player_id}&fig={fig}&x={x}&y={y}")
        
        assert response.status_code == 200
        assert response.json() == {"message": f"Game {mock_game_id} or p {mock_player_id} do not exist.", STATUS: FAILURE}

def test_claim_figure_shape_not_found(client, mock_game, mock_player, mock_shape):
    mock_game_id = 1
    mock_player_id = 10
    fig = "h1"
    x, y = 5, 5

    with patch('main.db_session'):
        # Setup mock player without the figure in their hand
        mock_shape_instance = mock_shape.return_value 
        mock_shape_instance.shape_type = fig
        mock_player_instance = mock_player.return_value
        mock_player_instance.current_shapes = [mock_shape_instance]
        mock_game_instance = mock_game.return_value

        mock_game.get.return_value = mock_game_instance
        mock_player.get.return_value = mock_player_instance

        response = client.put(f"/claim_figure?game_id={mock_game_id}&player_id={mock_player_id}&fig=h2&x={x}&y={y}")

        assert response.status_code == 200
        assert response.json() == {"message": f"p {mock_player_id} does not have the h2 card.", STATUS: FAILURE}

def test_claim_figure_not_on_board(client, mock_game, mock_player, mock_shapes_on_board, mock_shape):
    mock_game_id = 1
    mock_player_id = 10
    fig = "h1"
    x, y = 5, 5

    with patch('main.db_session'):
        mock_shape_instance = mock_shape.return_value 
        mock_shape_instance.shape_type = fig
        mock_player_instance = mock_player.return_value
        mock_player_instance.current_shapes = [mock_shape_instance]
        mock_game_instance = mock_game.return_value

        mock_game.get.return_value = mock_game_instance
        mock_player.get.return_value = mock_player_instance

        # Mock shapes_on_board to return empty (i.e., no matching figures on the board)
        mock_shapes_on_board.return_value = {
                            "s2": [[1, 1], [1, 1]],                 
                            "s3": [[1, 1, 0], [0, 1, 1]],           
                            "s4": [[0, 1, 0], [1, 1, 1]]
        }

        response = client.put(f"/claim_figure?game_id={mock_game_id}&player_id={mock_player_id}&fig={fig}&x={x}&y={y}")

        assert response.status_code == 200
        assert response.json() == {"message": f"The figure {fig} is not in the current board.", STATUS: FAILURE}
#
def test_claim_figure_not_at_position(client, mock_game, mock_player, mock_shapes_on_board, mock_shape):
    mock_game_id = 1
    mock_player_id = 10
    fig = "h1"
    x, y = 0, 0

    with patch('main.db_session'):
        mock_shape_instance = mock_shape.return_value 
        mock_shape_instance.shape_type = fig
        # Setup mock player and game
        mock_player_instance = mock_player.return_value
        mock_player_instance.current_shapes = [mock_shape_instance]
        mock_game_instance = mock_game.return_value

        mock_game.get.return_value = mock_game_instance
        mock_player.get.return_value = mock_player_instance

        # Mock shapes_on_board to return figure at different position
        mock_shapes_on_board.return_value = {fig: [[0, 1, 1], [1, 1, 1], [1, 1, 1]]}

        response = client.put(f"/claim_figure?game_id={mock_game_id}&player_id={mock_player_id}&fig={fig}&x={x}&y={y}")

        assert response.status_code == 200
        assert response.json() == {
            "message" : f"Figure {fig} exists in board, but not at ({x}, {y})",
            STATUS: FAILURE
        }
