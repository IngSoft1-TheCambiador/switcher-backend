from random import choice
from orm import Game, Player, db_session
from main import list_games
import requests


def test_game_creation():
    print("Asserting game creation...\nAttempting to create game with three players...")
    with db_session:
        Game.delete_all_games()
        sample_game = Game(name="some game")
        sample_game.create_player("Martin")
        sample_game.create_player("Jorge")
        sample_game.create_player("Unga")
        assert len(sample_game.players) == 3
        names = set()
        for p in sample_game.players:
            names.add(p.name)
        assert "Martin" in names
        assert "Jorge" in names
        assert "Unga" in names

def test_initialization_and_block_swapping():
    with db_session:
        sample = Game(name="some game")
        sample.create_player("Martin")
        sample.create_player("Jorge")
        sample.create_player("Unga")
        old_board = sample.board
        old_five = sample.get_block_color(5, 5)
        old_three = sample.get_block_color(3, 3)
        sample.exchange_blocks(3, 3, 5, 5)
        print(sample.board)
        new_five = sample.get_block_color(5, 5)
        new_three = sample.get_block_color(3, 3)
        for index, char in enumerate(old_board):
            same = old_board[index] == sample.board[index]
            if index != 35 and index != 21:
                assert old_board[index] == sample.board[index]
        assert new_three == old_five and new_five == old_three

def test_player_deletion():
    with db_session:
        sample = Game(name="some game")
        sample.create_player("Martin")
        sample.create_player("Jorge")
        sample.create_player("Unga")
        sample.initialize()
        for player in sample.players:
            old_player = player
            break
        old_name = old_player.name
        sample.remove_player(old_player)
        for p in sample.players:
            assert p.name != old_name

def quick_showcase():
    with db_session:
        sample = Game(name="some game")
        sample.create_player("Martin")
        sample.create_player("Jorge")
        sample.create_player("Unga")
        sample.initialize()
        print(sample.board)
        old_board = sample.board
        old_five = sample.get_block_color(5, 5)
        old_three = sample.get_block_color(3, 3)
        sample.exchange_blocks(3, 3, 5, 5)
        print(sample.board)
        new_five = sample.get_block_color(5, 5)
        new_three = sample.get_block_color(3, 3)
        for index, char in enumerate(old_board):
            same = old_board[index] == sample.board[index]
            if index != 35 and index != 21:
                assert old_board[index] == sample.board[index]
        assert new_three == old_five and new_five == old_three
        for p in sample.players:
           print("id: ",  p.id, "name: ", p.name, "next: ", p.next, "color: ", p.color)
        print("Current: ", sample.current_player_id)
        sample.end_turn()
        print("Current: ", sample.current_player_id)
        sample.end_turn()
        print("Current: ", sample.current_player_id)
        sample.end_turn()
        print("Current: ", sample.current_player_id)
        sample.end_turn()
        for player in sample.players:
            old_player = player
            break
        old_name = old_player.name
        print("Removing ", old_name)
        sample.remove_player(old_player)
        print("Now in game:")
        for p in sample.players:
            print(p.name) 

#quick_showcase()
