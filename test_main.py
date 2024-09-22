import requests

from random import randint
from test_orm import test_game_creation
from orm import Game, Player, Shape, Move
from orm import db_session, commit
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
        # Show players prior to joining SillyGuy
        requests.get(f"http://127.0.0.1:8000/list_players?game_id={game.id}")
        jr = requests.post(f"http://127.0.0.1:8000/join_game?game_id={game.id}&player_name=SillyGuy").json()
        # Show players after joining SillyGuy
        requests.get(f"http://127.0.0.1:8000/list_players?game_id={game.id}")
        requests.post(f"http://127.0.0.1:8000/leave_game?game_id={game.id}&player_name=SillyGuy")
        # Show players after removing SillyGuy
        requests.get(f"http://127.0.0.1:8000/list_players?game_id={game.id}")

        # assert that removed player no longer exists in database
        assert Player.get(id = jr["player_id"]) is None



        
        requests.post(f"http://127.0.0.1:8000/leave_game?game_id={game.id}&player_name=AGuyThatDoesntExist")
        requests.post(f"http://127.0.0.1:8000/leave_game?game_id={game.id + 10000}&player_name=ThePlayer")

        



def test_game_state():
    with db_session:
        r = requests.put(f"http://127.0.0.1:8000/create_game?game_name=abc&player_name=TheCreator").json()

        game = Game.get(id=r["game_id"])
        game.create_player("Johnny")
        game.create_player("Stewart")

        r = requests.get(f"http://127.0.0.1:8000/game_state?game_id={game.id}")
        print(r.json())

        game.is_init = True

        shape_types = ["ASD", "???", "010"]
        move_types = ["***", "~~~", "-_-"]
        colors = ["Blue", "Green", "Red"]
        i = 0
        for p in game.players:
            p.color = colors[i]
            # Add cards and shapes. This functionality is not needed yet
            #p.shapes.add(Shape(shape_type=shape_types[i]))
            #p.moves.add(Move(move_type=move_types[i]))
            i+=1

        commit()
        r = requests.get(f"http://127.0.0.1:8000/game_state?game_id={game.id}")
        print(r.json())

#test_game_listing()
#test_game_creation_request()
#test_leave_game()
#test_game_state()
