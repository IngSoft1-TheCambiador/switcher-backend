import requests

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
  
test_game_listing()
