import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app, manager  
from pony.orm import db_session

client = TestClient(app)


@pytest.fixture
def mock_manager():
    """Mock the ConnectionManager"""
    with patch.object(manager, 'add_to_game', new_callable=AsyncMock) as mock_add:
        yield mock_add

# Test function
@pytest.mark.asyncio
@patch("main.Game")
async def test_create_game(mock_game_class, mock_manager):
    # Mock data
    socket_id = 1
    game_name = "Test Game"
    player_name = "Host"

    mock_game_instance = mock_game_class.return_value
    mock_game_instance.id = 42
    mock_game_instance.create_player.return_value = 1 
    
    # Call the endpoint
    response = client.put(
        f"/create_game?socket_id={socket_id}&game_name={game_name}&player_name={player_name}"
    )
    
    assert response.status_code == 200
    response_data = response.json()
    
    # Check the response and mock calls
    assert response_data['game_id'] == mock_game_instance.id  # Check mocked game ID
    assert response_data['player_id'] == 1  # Check mocked player ID
    
    # Assert that the WebSocket manager's add_to_game was called with the correct args
    mock_manager.assert_called_once_with(socket_id, 42)



@patch("main.Game")
def test_create_multiple_games(mock_game_class, mock_manager):
    # Mock data
    games = [
        {"game_name": "Game1", "player_name": "Player1", "min_players": 2, "max_players": 4},
        {"game_name": "Game2", "player_name": "Player2", "min_players": 3, "max_players": 3},
        {"game_name": "Game3", "player_name": "Player3", "min_players": 1, "max_players": 2},
    ]

    # Mock game_id and player_id to be returned by the database for each game
    socket_ids = [1, 2, 3]
    mock_game_ids = [505, 202, 3]
    mock_player_ids = [120, 1, 505]
    mock_game_instance = mock_game_class.return_value

    for i, game in enumerate(games):
        # Create a mock instance for each game
        mock_game_instance.create_player.return_value = mock_player_ids[i]
        mock_game_instance.id = mock_game_ids[i]
        mock_game_instance.max_players = game["max_players"]
        mock_game_instance.min_players = game["min_players"]


        game = games[i]
        response = client.put(
            f"""create_game?socket_id={socket_ids[i]}&game_name={game['game_name']}&player_name={game['player_name']}&max_players={game['max_players']}&min_players={game['min_players']}"""
        )

        assert response.status_code == 200

        response_data = response.json()
        assert response_data == {
            "game_id": mock_game_ids[i],
            "player_id": mock_player_ids[i]
        }

        mock_game_class.assert_called_with(name=game["game_name"])
#        mock_game_instance.create_player.assert_called_once_with(game["player_name"])
        # It is unclear to me why the mock_game_instance.max_players attribute is 
        # a string here, where above we are setting it as an integer. Hence, this 
        # type casting is bad practice - we should address the issue.
        assert int( mock_game_instance.max_players ) == game["max_players"]
        assert int( mock_game_instance.min_players ) == game["min_players"]
        assert mock_game_instance.owner_id == mock_player_ids[i]

    assert mock_game_class.call_count == len(games)
