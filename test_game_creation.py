import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app, manager  
from pony.orm import db_session
from constants import *

client = TestClient(app)


@pytest.fixture
def mock_manager():
    """Mock the ConnectionManager"""
    with patch.object(manager, 'add_to_game', new_callable=AsyncMock) as mock_add:
        yield mock_add

@pytest.fixture 
def mock_player(mocker):
    mock_player = mocker.patch('main.Player')
    return mock_player

@pytest.mark.asyncio
@patch("main.Game")
async def test_create_game(mock_game_class, mock_manager, mock_player):
    # Mock data
    socket_id = 1
    game_name = "Test Game"
    player_name = "Host"

    mock_game_instance = mock_game_class.return_value
    mock_game_instance.id = 42
    mock_player_instance = mock_player.return_value
    mock_player_instance.id = 1

    def mock_create_player(player_name):
        player = mock_player_instance
        if len(mock_game_instance.players) == 0:
            mock_game_instance.owner_id = player.id
        mock_game_instance.players.add(player)
        return player.id

    mock_game_instance.create_player.side_effect = mock_create_player

    
    # Call the endpoint
    response = client.put(
        f"/create_game?socket_id={socket_id}&game_name={game_name}&player_name={player_name}"
    )
    
    assert response.status_code == 200
    response_data = response.json()
   
    print(response_data)
    # Check the response and mock calls
    assert response_data['game_id'] == mock_game_instance.id  # Check mocked game ID
    assert response_data['player_id'] == 1  # Check mocked player ID
    
    # Assert that the WebSocket manager's add_to_game was called with the correct args
    mock_manager.assert_called_once_with(socket_id, 42)



@patch("main.Game")
def test_create_multiple_games(mock_game_class, mock_manager, mock_player):
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

    mock_player_instance = mock_player.return_value

    for i, game in enumerate(games):
        # Create a mock instance for each game
        mock_game_instance.create_player.return_value = mock_player_ids[i]
        mock_game_instance.id = mock_game_ids[i]
        mock_game_instance.max_players = games[i]["max_players"]
        mock_game_instance.min_players = games[i]["min_players"]
        mock_player_instance.id = mock_player_ids[i]
        
        def mock_create_player(player_name):
            player = mock_player_instance
            if len(mock_game_instance.players) == 0:
                mock_game_instance.owner_id = player.id
            mock_game_instance.players.add(player)
         
            return player.id

        mock_game_instance.create_player.side_effect = mock_create_player

        game = games[i]
        response = client.put(
            f"""create_game?socket_id={socket_ids[i]}&game_name={game['game_name']}&player_name={game['player_name']}&max_players={game['max_players']}&min_players={game['min_players']}"""
        )

        assert response.status_code == 200

        response_data = response.json()
        assert response_data == {
            GAME_ID: mock_game_instance.id,
            PLAYER_ID: mock_game_instance.owner_id,
            GAME_MAX: games[i]["max_players"],
            GAME_MIN: games[i]["min_players"]
        }

