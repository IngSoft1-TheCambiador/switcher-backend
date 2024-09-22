import requests

from models import JoinGameRequest, CreateGameRequest
from test_orm import test_game_creation
from main import join_game, create_game
from orm import Game, Player, db_session
from test_orm import test_game_creation

def test_game_listing():
    test_game_creation()
    games = requests.get("http://127.0.0.1:8000/list_games")
    print(games.json())
    assert games.json()['games_list']
    games = requests.get("http://127.0.0.1:8000/list_games?page=2")
    assert not games.json()['games_list']
    for _ in range(10):
        test_game_creation()
    games = requests.get("http://127.0.0.1:8000/list_games?page=2")
    assert len(games.json()['games_list']) > 0
    print(games.json())
  
def test_game_listing():
    test_game_creation()
    print("\nShowing games at root/list_games in JSON format.")
    games = requests.get("http://127.0.0.1:8000/list_games")
    print(games.json())
    print("\nAsserting that games_list is not null...")
    assert games.json()['games_list']
    print("\nSuccess\n")
    print("\nRetrieving games at root/list_games?page=2\n")
    games = requests.get("http://127.0.0.1:8000/list_games?page=2")
    print("Retrieved games:")
    print(games.json())
    print("Asserting that games_list in page 2 is empty...\n")
    assert not games.json()['games_list']
    print("Success\n")
    print("Creating ten games...\n")
    for _ in range(10):
        test_game_creation()
    #games = requests.get("http://127.0.0.1:8000/list_games?page=2")
    #print("Asserting that game list at page 2 has more than zero games...\n")
    #print(games.json())
    #assert len(games.json()['games_list']) > 0
    #print(games.json())
    print("Success...\n")

def test_join_game():
    with db_session:
        test_game_creation()
        print("\nShowing games at root/list_games in JSON format.")
        games = requests.get("http://127.0.0.1:8000/list_games").json()
        print("Randomly selected a join to insert a player")
        random_game = Game.select_random(1)[0]
        length_old = len(random_game.players)
        print("Printing players at this room before join call")
        random_game.dump_players()
        print("\nProcessing join request")
        join_request = JoinGameRequest(game_id = random_game.id, player_name="TheOneWhoJoins")
        join_game(join_request)
        print("\nPrinting players at this room before join call")
        random_game.dump_players()
        length_new = len(random_game.players)

        print(length_old, length_new)
        assert length_new == length_old + 1
        assert "TheOneWhoJoins" in [p.name for p in random_game.players]

        print("All assertions passed. Success")

def test_create_game_endpint():
    with db_session():
        print("\nShowing games at root/list_games in JSON format.")
        games = requests.get("http://127.0.0.1:8000/list_games").json()
        print(games)
        
        print("\nProceeding to create game.")

        req = CreateGameRequest(player_name = "Clark, the creator",
                                game_name = "Clark's game")

        create_game(req)
        print("\nShowing games at root/list_games in JSON format.")
        games = requests.get("http://127.0.0.1:8000/list_games").json()
        print(games)
        game = Game[1]
        game.dump_players()

        assert "Clark, the creator" in [p.name for p in game.players]
        assert len(game.players) == 1


  
#test_join_game()
#test_game_listing()
test_create_game_endpint()
