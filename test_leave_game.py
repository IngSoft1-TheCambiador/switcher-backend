import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app, manager  
from constants import STATUS, SUCCESS


@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_game(mocker):
    # Create a mock for the Game model
    mock_game = mocker.patch('main.Game')  # Adjust the path as necessary
    return mock_game

@pytest.fixture 
def mock_player(mocker):
    mock_player = mocker.patch('main.Player')
    return mock_player


@pytest.fixture
def mock_manager():
    """Mock the ConnectionManager"""
    with patch.object(manager, 'remove_from_game', new_callable=AsyncMock) as mock_add:
        yield mock_add

def test_leave_game(client, mock_game, mock_player, mock_manager):

    with patch('main.db_session'):
      
        player_a = mock_player.return_value 
        player_b = mock_player.return_value 

        player_a.name = "A"
        player_a.id = 1
        player_b.name = "B"
        player_b.id = 2

        mock_game_instance = mock_game.return_value
        mock_game_instance.id = 100
        mock_game_instance.owner_id = player_a.id
        mock_game_instance.players = [player_a, player_b]
        mock_game_instance.max_players = 4
        
        mock_game.get.return_value = mock_game_instance
        
        response = client.post(f"/leave_game?socket_id={1}&game_id={mock_game_instance.id}&player_id={player_b.id}")

        assert response.status_code == 200
        assert mock_game_instance.players == [player_a]
        
        assert response.json() == {
            "game_id": mock_game_instance.id,
            "message": f"Succesfully removed player with id 2 from game {mock_game_instance.id}", STATUS: SUCCESS
        }

def test_turn_adjustment(client, mock_game, mock_player, mock_manager):

    with patch('main.db_session'):
      
        player_a = mock_player.return_value 
        player_b = mock_player.return_value 
        player_c = mock_player.return_value 

        player_a.name = "A"
        player_a.id = 1
        player_a.next = player_b
        player_b.name = "B"
        player_b.id = 2
        player_b.next = player_c
        player_c.name = "C"
        player_c.id = 3
        player_c.next = player_a
        # Ensure the `Player.get(next=p.id)` line points to `player_a`, since
        # the current turn is `player_b` and `player_a == player_b.next ≡ True`.
        mock_player.get.return_value = player_a


        mock_game_instance = mock_game.return_value
        mock_game_instance.current_player = player_b
        mock_game_instance.id = 100
        mock_game_instance.owner_id = player_a.id
        mock_game_instance.players = [player_a, player_b]
        mock_game_instance.max_players = 4
        
        mock_game.get.return_value = mock_game_instance
        
        response = client.post(f"/leave_game?socket_id={1}&game_id={mock_game_instance.id}&player_id={player_b.id}")

        assert response.status_code == 200
        assert mock_game_instance.players == [player_a]
        assert mock_game_instance.current_player == player_a
        assert player_a.next == player_c

        

def test_game_ending(client, mock_game, mock_player, mock_manager):

    with patch('main.db_session'):
      
        player_a = mock_player.return_value 
        player_b = mock_player.return_value 

        player_a.name = "A"
        player_a.id = 1
        player_b.name = "B"
        player_b.id = 2

        mock_game_instance = mock_game.return_value
        mock_game_instance.id = 100
        mock_game_instance.owner_id = player_a.id
        mock_game_instance.players = [player_a, player_b]
        mock_game_instance.max_players = 4

        mock_game.get.return_value = mock_game_instance
        
        response = client.post(f"/leave_game?socket_id={1}&game_id={mock_game_instance.id}&player_id={player_b.id}")

        assert response.status_code == 200

        assert mock_game_instance.cleanup.called



#def test_leave_game_errors(client, mock_game, mock_player, mock_manager):
#    mock_game_id = 5
#    mock_player_id = 10
#
#    with patch('main.db_session'):
#       
#        player_a = mock_player.return_value 
#        player_b = mock_player.return_value 
#
#        player_a.name = "A"
#        player_a.id = 1
#        player_b.name = "B"
#        player_b.id = 2
#
#        mock_game_instance = mock_game.return_value
#        mock_game_instance.id = 100
#        mock_game_instance.owner_id = player_a.id
#        mock_game_instance.players = [player_a, player_b]
#        mock_game_instance.max_players = 4
#        
#        mock_game.get.return_value = mock_game_instance
#        
#        response = client.post(f"/leave_game?socket_id={1}&game_id={mock_game_instance.id}&player_id=123123")
#
#        assert response.status_code == 200
#        
#        assert response.json() == {
#            "game_id": mock_game_instance.id,
#            "message": f"Succesfully removed player with id 2 from game {mock_game_instance.id}"
#        }
