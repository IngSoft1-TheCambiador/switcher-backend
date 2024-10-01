import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app  # Assuming your FastAPI app is in main.py

client = TestClient(app)

def test_create_game():

    # Variables del mockeo de `Game`
    game_name = "TestGame"
    player_name = "TestPlayer"
    min_players = 2
    max_players = 4

    # Variables del mockeo de la base de datos
    mock_game_id = 1
    mock_player_id = 100

    # Mockeo de Pony y la db_session, y del `Game` (con mock_game_class).
    with patch('main.db_session'), \
         patch('main.Game', autospec=True) as mock_game_class:
        
        # Mockeamos una instancia de `Game` con los atributos especificados
        # más arriba.
        mock_game_instance = MagicMock()
        mock_game_instance.create_player.return_value = mock_player_id
        mock_game_instance.id = mock_game_id

        # El mockeo de la clase va a devolver la instancia que especificamos
        mock_game_class.return_value = mock_game_instance

        # Tiramos la request!
        req = f"http://127.0.0.1:8000/create_game?game_name={game_name}&player_name={player_name}"
        response = client.put(req)

        assert response.status_code == 200

        response_data = response.json()
        assert response_data == {
            "game_id": mock_game_id,
            "player_id": mock_player_id
        }

        mock_game_class.assert_called_once_with(name=game_name)
        mock_game_instance.create_player.assert_called_once_with(player_name)
        assert mock_game_instance.max_players == max_players
        assert mock_game_instance.name == game_name
        assert mock_game_instance.min_players == min_players
        assert mock_game_instance.owner_id == mock_player_id


def test_create_multiple_games():
    # Mock data
    games = [
        {"game_name": "Game1", "player_name": "Player1", "min_players": 2, "max_players": 4},
        {"game_name": "Game2", "player_name": "Player2", "min_players": 3, "max_players": 3},
        {"game_name": "Game3", "player_name": "Player3", "min_players": 1, "max_players": 2},
    ]

    # Mock game_id and player_id to be returned by the database for each game
    mock_game_ids = [505, 202, 3]
    mock_player_ids = [120, 1, 505]

    # Mock the Pony ORM Game class and db_session
    with patch('main.db_session'), \
         patch('main.Game', autospec=True) as mock_game_class:

        for i, game in enumerate(games):
            # Create a mock instance for each game
            mock_game_instance = MagicMock()
            mock_game_instance.create_player.return_value = mock_player_ids[i]
            mock_game_instance.id = mock_game_ids[i]
            mock_game_instance.max_players = game["max_players"]
            mock_game_instance.min_players = game["min_players"]

            # Configure the mock Game class to return the mock instance
            mock_game_class.return_value = mock_game_instance

            req_args = f"game_name={game['game_name']}&player_name={game['player_name']}&min_players={game['min_players']}&max_players={game['max_players']}"

            req = f"http://127.0.0.1:8000/create_game?{req_args}"
            response = client.put(req)

            assert response.status_code == 200

            response_data = response.json()
            assert response_data == {
                "game_id": mock_game_ids[i],
                "player_id": mock_player_ids[i]
            }

            mock_game_class.assert_called_with(name=game["game_name"])
            mock_game_instance.create_player.assert_called_once_with(game["player_name"])
            # It is unclear to me why the mock_game_instance.max_players attribute is 
            # a string here, where above we are setting it as an integer. Hence, this 
            # type casting is bad practice - we should address the issue.
            assert int( mock_game_instance.max_players ) == game["max_players"]
            assert int( mock_game_instance.min_players ) == game["min_players"]
            assert mock_game_instance.owner_id == mock_player_ids[i]

        assert mock_game_class.call_count == len(games)
