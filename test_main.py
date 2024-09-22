import requests

from test_orm import test_game_creation
from orm import Game, Player
from orm import db_session
from main import GAME_ID, PLAYER_ID
from pony.orm import commit

def test_game_listing():
    test_game_creation()
    games = requests.get("http://127.0.0.1:8000/list_games")
    assert games.json()['games_list']
    for _ in range(10):
        test_game_creation()
    games = requests.get("http://127.0.0.1:8000/list_games?page=4")
    assert len(games.json()['games_list']) > 0
    print("Games at the current page:")
    print(games.json()['games_list'])

def test_game_creation_request():
    # Try creating a new game with default parameters
    try:
        intended_game_name = "polola"
        intended_player_name = "pololita"
        new_game = requests.put(f"http://127.0.0.1:8000/create_game?game_name={intended_game_name}&player_name={intended_player_name}")
        new_game_data = new_game.json()
        new_game_id = new_game_data[GAME_ID]
        new_player_id = new_game_data[PLAYER_ID]
        with db_session:
            actual_name = Game[new_game_id].name
            actual_player_name = Player[new_player_id].name
            assert actual_name == intended_game_name
            assert actual_player_name == intended_player_name
    except:
        assert False
    # Pending:
    # Try creating a new game, with custom valid and invalid parameters


def test_leave_game():
    with db_session:
        r = requests.put(f"http://127.0.0.1:8000/create_game?game_name=abc&player_name=ThePlayer").json()
        game = Game.get(id=r["game_id"])
        # Show players prior to joining NewGuy
        requests.get(f"http://127.0.0.1:8000/list_players?game_id={game.id}")
        requests.post(f"http://127.0.0.1:8000/join_game?game_id={game.id}&player_name=NewGuy")
        # Show players after joining NewGuy
        requests.get(f"http://127.0.0.1:8000/list_players?game_id={game.id}")
        requests.post(f"http://127.0.0.1:8000/leave_game?game_id={game.id}&player_name=NewGuy")
        # Show players after removing NewGuy
        requests.get(f"http://127.0.0.1:8000/list_players?game_id={game.id}")
        







#test_game_listing()
#test_game_creation_request()
test_leave_game()
