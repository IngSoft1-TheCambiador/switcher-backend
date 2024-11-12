import pytest
from unittest.mock import AsyncMock, patch, Mock
from fastapi.testclient import TestClient
from orm import Game, Player, LogMessage
from main import app, manager  
from constants import *
import datetime

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


@pytest.fixture 
def mock_log_message(mocker):
    mock_message = mocker.patch('main.LogMessage')
    return mock_message

@pytest.mark.asyncio
@patch("main.Game")
async def test_create_game(mock_game_class, mock_manager, mock_player):
    # Mock data
    socket_id = 1
    game_name = "Test Game"
    player_name = "Host"
    password = "Apassword123"

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
        f"/create_game?socket_id={socket_id}&game_name={game_name}&player_name={player_name}&password={password}"
    )
    
    assert response.status_code == 200
    response_data = response.json()
   
    assert response_data['game_id'] == mock_game_instance.id  
    assert response_data['player_id'] == 1  
    assert response_data['password'] == password 
    
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
            GAME_MIN: games[i]["min_players"],
            "password": "",
            STATUS: SUCCESS
        }



@pytest.mark.asyncio
@patch("main.Game")
async def test_invalid_password(mock_game_class, mock_manager, mock_player):

   
    # Password with number and uppercase, but incorrect length
    password = "Aasd1"
    # Call the endpoint
    response = client.put(
        f"/create_game?socket_id={1}&game_name=Whatever&player_name=Whatever2&password={password}"
    )

    
    assert response.status_code == 200
    response_data = response.json()

    assert response_data == {
                "error": f"Invalid password {password}. Valid passwords should either be the empty string (for no password), or a password of >= 8 characters with at least one number and at least one uppercase character",
                STATUS: FAILURE
    }


    # Password with correct length and uppercase, but no number
    password = "Asdasdasdasd"
    # Call the endpoint
    response = client.put(
        f"/create_game?socket_id={1}&game_name=Whatever&player_name=Whatever2&password={password}"
    )

    
    assert response.status_code == 200
    response_data = response.json()

    assert response_data == {
                "error": f"Invalid password {password}. Valid passwords should either be the empty string (for no password), or a password of >= 8 characters with at least one number and at least one uppercase character",
                STATUS: FAILURE
    }
   
    # Password with correct length and number, but no uppercase
    password = "1sdasdasdasd"
    # Call the endpoint
    response = client.put(
        f"/create_game?socket_id={1}&game_name=Whatever&player_name=Whatever2&password={password}"
    )

    
    assert response.status_code == 200
    response_data = response.json()

    assert response_data == {
                "error": f"Invalid password {password}. Valid passwords should either be the empty string (for no password), or a password of >= 8 characters with at least one number and at least one uppercase character",
                STATUS: FAILURE
    }
   
    

@pytest.mark.asyncio
@patch("main.Game")
async def test_create_with_previous_games(mock_game_class, mock_manager, mock_player, mock_log_message):
    # Mock data
    socket_id = 1
    game_name = "Test Game"
    player_name = "Host"
    password = "Apassword123"


    log_msg = Mock(spec=LogMessage)
    
    player_a = mock_player.return_value

    player_a.name = "A"
    player_a.id = 1

    game_1 = Mock(spec=Game)
    game_2 = Mock(spec=Game)

    player_b = Mock(spec=Player)
    player_b.id = 123123
    player_b.name = "B"


    # A game with player_a
    game_1.current_player = player_a
    game_1.id = 100
    game_1.owner_id = player_b.id
    game_1.players = [player_a, player_b]
    game_1.max_players = 4
    game_1.is_init = True

    # A game without player_a
    game_2.current_player = player_a
    game_2.id = 101
    game_2.owner_id = player_a.id
    game_2.players = [player_a, player_b]
    game_2.max_players = 4
    game_2.is_init = False
    game_2.password = ""

    log_msg.content = "Abandono partida"
    log_msg.game = game_1.id,
    log_msg.timestamp = datetime.datetime.now()
    mock_log_message.return_value = log_msg


    mock_player.get.return_value = player_a
    mock_game_class.select.return_value = [game_1, game_2]


    game_2.create_player.return_value = 123

    mock_game_instance = mock_game_class.return_value
    mock_game_instance.id = 42
    mock_player_instance = mock_player.return_value
    mock_player_instance.id = 1


    assert len(game_1.players) == 2
    assert len(game_2.players) == 2

    def mock_create_player(player_name):
        player = mock_player_instance
        if len(mock_game_instance.players) == 0:
            mock_game_instance.owner_id = player.id
        mock_game_instance.players.add(player)
        return player.id

    mock_game_instance.create_player.side_effect = mock_create_player

    
    # Call the endpoint
    response = client.put(
        f"/create_game?socket_id={socket_id}&game_name={game_name}&player_name={player_name}&password={password}"
    )
    
    assert response.status_code == 200
    response_data = response.json()
   
    assert response_data['game_id'] == mock_game_instance.id  
    assert response_data['player_id'] == 1  
    assert response_data['password'] == password 
    assert len(game_1.players) == 1
    assert len(game_2.players) == 1
    assert player_a not in game_1.players
    assert player_a not in game_2.players
    
    # Assert that the WebSocket manager's add_to_game was called with the correct args
    mock_manager.assert_called_once_with(socket_id, 42)
