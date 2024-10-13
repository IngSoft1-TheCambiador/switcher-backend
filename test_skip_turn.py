import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

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

@patch('main.manager.broadcast_in_game', MagicMock())  
@pytest.mark.asyncio
async def test_skip_turn_success(client, mock_player, mock_game):

    mock_game_instance = mock_game.return_value
    mock_game_instance.id = 1
    mock_game_instance.current_player_id = 1
    mock_game_instance.is_init = True

    mock_player_instance = mock_player.return_value
    mock_player_instance.id = 1
    mock_player_instance.next = 2  # Ensure correct attribute name is mocked

    # Ensure `Game.get()` and `Player.get()` return the mocked instances
    mock_game.get.return_value = mock_game_instance
    mock_player.get.return_value = mock_player_instance

    # Make the request with query params
    response = client.put(
        "/skip_turn",
        json={"game_id": 1, "player_id": 1}
    )

    expected = {"message": "Player 1 skipped in game 1"}

    assert response.status_code == 200
    assert response.json() == expected

#    manager.broadcast_in_game.assert_called_once_with(1, "SKIP {game_id} {player_id}")

#@patch('main.db_session', MagicMock())  # Mock db_session
#@patch('main.Game')  # Mock Game entity
#@patch('main.Player')  # Mock Player entity
#@pytest.mark.asyncio
#async def test_skip_turn_invalid(mock_player, mock_game):
#    # Create a mock game where the current player is not player 1, or the game is not initialized
#    mock_game.__getitem__.return_value = MockGame(id=1, current_player_id=2, is_init=False)
#
#    # Mock player 1
#    mock_player.__getitem__.return_value = MockPlayer(id=1, next_player_id=2)
#
#    # Call the endpoint with invalid game state (game not initialized or player not current)
#    response = await client.put("/skip_turn", json={"game_id": 1, "player_id": 1})
#
#    # Expected failure response
#    expected_failure_message = '''
#    Received a skip request in game 1 with player id 1,
#    but either there is no such game, no such player, no such player in
#    such game, or the player is not currently holding the 'current player'
#    position.
#    '''
#
#    # Assert the response is correct
#    assert response.status_code == 200
#    assert response.json() == {"message": expected_failure_message}
#
#@patch('main.db_session', MagicMock())  # Mock db_session
#@pytest.mark.asyncio
#async def test_skip_turn_exception():
#    # Simulate an exception being raised during the process
#    response = await client.put("/skip_turn", json={"game_id": 999, "player_id": 999})
#
#    # Assert that an HTTPException is raised
#    assert response.status_code == 400
#    assert response.json()["detail"] == "Failed to skip turn in game 999 with player id 999"
