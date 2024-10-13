import pytest
from unittest.mock import patch, MagicMock
from main import list_games

PLAYER_ID = "player_id"
GAME_ID = "game_id"
GAME_NAME = "game_name"
GAME_MIN = "min_players"
GAME_MAX = "max_players"
GAMES_LIST = "games_list"

# Mock Game class
class MockGame:
    def __init__(self, id, name, min_players, max_players, players, is_init):
        self.id = id
        self.name = name
        self.min_players = min_players
        self.max_players = max_players
        self.players = players
        self.is_init = is_init

@pytest.fixture
def mock_games():
    return [
        MockGame(1, 'Game 1', 2, 4, ['player1'], False),
        MockGame(2, 'Game 2', 2, 4, ['player1', 'player2'], True),  # should be skipped
        MockGame(3, 'Game 3', 3, 6, ['player1'], False),
        MockGame(4, 'Game 4', 2, 4, [], False)
    ]

@patch('orm.Game.select')  
def test_list_games(mock_select, mock_games):
    """
    Idea of this test: `list_pages` calls `Game.select` an orders 
    the resulting list of games by id. So we mock `Game.select` with 
    a function that returns a list of our `mock_games`.
    """
    mock_select.return_value.order_by.return_value = mock_games

    response = list_games(page=1)

    expected = {
        GAMES_LIST: [
            {GAME_ID: 1, GAME_NAME: 'Game 1', GAME_MIN: 2, GAME_MAX: 4},
            {GAME_ID: 3, GAME_NAME: 'Game 3', GAME_MIN: 3, GAME_MAX: 6},
            {GAME_ID: 4, GAME_NAME: 'Game 4', GAME_MIN: 2, GAME_MAX: 4},
        ]
    }

    assert response == expected
    mock_select.assert_called_once()
