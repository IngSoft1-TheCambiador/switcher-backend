import pytest
from unittest.mock import patch
from main import search_games
from constants import *

# Mock Game class
class MockGame:
    def __init__(self, id, name, min_players, max_players, players, is_init, private):
        self.id = id
        self.name = name
        self.min_players = min_players
        self.max_players = max_players
        self.players = players
        self.is_init = is_init
        self.private = private

@pytest.fixture
def mock_games():
    return [
        # Should be skipped, list_games logic is preserved
        MockGame(1, 'apple',        2, 4, ['player1'], True, False),
        MockGame(2, 'apple',        2, 2, ['player1', 'player2'], False, True),

        # Should be skipped, appl not in banana
        MockGame(3, 'banana',       2, 4, ['player1'], False, True),

        # Should be skipped, it does not contemplate minimal differences in text
        MockGame(4, 'maples',       2, 4, ['player1'], False, True),
        MockGame(5, 'appetizer',    2, 4, ['player1'], False, False),

        MockGame(6, 'apple',        2, 4, ['player1'], False, False),
        MockGame(7, 'aPPle',        2, 4, ['player1'], False, False),
        MockGame(8, 'application',  2, 4, ['player1'], False, False),
        MockGame(9, 'APPLICATION',  2, 3, ['player1'], False, True),
        MockGame(10, 'pineapple',    2, 4, ['player1'], False, True),
        MockGame(11, 'pineapple',    2, 4, ['player1'], False, False),
        MockGame(12, 'pineapple',    3, 4, ['player1'], False, True),
        MockGame(13, 'pineapple',    2, 2, ['player1'], False, False),
        MockGame(14, 'pineapple',    2, 4, ['player1'], False, True)
    ]

@patch('orm.Game.select')  
def test_search_games_matching_text(mock_select, mock_games):

    mock_select.return_value.order_by.return_value = mock_games

    response = search_games(page=1, text="appl", min="", max="")

    expected = {
        GAMES_LIST: [
            {GAME_ID: 6, GAME_NAME: 'apple', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: False},
            {GAME_ID: 7, GAME_NAME: 'aPPle', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: False},
            {GAME_ID: 8, GAME_NAME: 'application', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: False},
            {GAME_ID: 9, GAME_NAME: 'APPLICATION', GAME_MIN: 2, GAME_MAX: 3, PRIVATE: True},
            {GAME_ID: 10, GAME_NAME: 'pineapple', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: True},
            {GAME_ID: 11, GAME_NAME: 'pineapple', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: False},
            {GAME_ID: 12, GAME_NAME: 'pineapple', GAME_MIN: 3, GAME_MAX: 4, PRIVATE: True},
            {GAME_ID: 13, GAME_NAME: 'pineapple', GAME_MIN: 2, GAME_MAX: 2, PRIVATE: False}
        ],
        STATUS: SUCCESS
    }

    assert response == expected
    mock_select.assert_called_once()

@patch('orm.Game.select')  
def test_search_games_all_default_values(mock_select, mock_games):

    mock_select.return_value.order_by.return_value = mock_games

    response = search_games(page=1, text="", min="", max="")

    expected = {
        GAMES_LIST: [
            {GAME_ID: 3, GAME_NAME: 'banana', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: True},
            {GAME_ID: 4, GAME_NAME: 'maples', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: True},
            {GAME_ID: 5, GAME_NAME: 'appetizer', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: False},
            {GAME_ID: 6, GAME_NAME: 'apple', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: False},
            {GAME_ID: 7, GAME_NAME: 'aPPle', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: False},
            {GAME_ID: 8, GAME_NAME: 'application', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: False},
            {GAME_ID: 9, GAME_NAME: 'APPLICATION', GAME_MIN: 2, GAME_MAX: 3, PRIVATE: True},
            {GAME_ID: 10, GAME_NAME: 'pineapple', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: True}
        ],
        STATUS: SUCCESS
    }

    assert response == expected
    mock_select.assert_called_once()

@patch('orm.Game.select')  
def test_search_games_invalid_range(mock_select, mock_games):

    mock_select.return_value.order_by.return_value = mock_games

    response = search_games(page=1, text="", min="", max="7")

    expected = {"error": "Invalid search",
                    STATUS: FAILURE}

    assert response == expected

@patch('orm.Game.select')  
def test_search_games_full_search(mock_select, mock_games):

    mock_select.return_value.order_by.return_value = mock_games

    response = search_games(page=1, text="appl", min="2", max="4")

    expected = {
        GAMES_LIST: [
            {GAME_ID: 6, GAME_NAME: 'apple', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: False},
            {GAME_ID: 7, GAME_NAME: 'aPPle', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: False},
            {GAME_ID: 8, GAME_NAME: 'application', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: False},
            {GAME_ID: 10, GAME_NAME: 'pineapple', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: True},
            {GAME_ID: 11, GAME_NAME: 'pineapple', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: False},
            {GAME_ID: 14, GAME_NAME: 'pineapple', GAME_MIN: 2, GAME_MAX: 4, PRIVATE: True}
        ],
        STATUS: SUCCESS
    }

    assert response == expected
    mock_select.assert_called_once()
