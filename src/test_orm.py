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

        print("Assertion of game creation completed: Success\n")

def test_initialization_and_block_swapping():
    with db_session:
        sample_game = Game(name="some game")
        sample_game.create_player("Martin")
        sample_game.create_player("Jorge")
        sample_game.create_player("Unga")
        old_board = sample_game.board
        old_five = sample_game.get_block_color(5, 5)
        old_three = sample_game.get_block_color(3, 3)
        sample_game.exchange_blocks(3, 3, 5, 5)
        print(sample_game.board)
        new_five = sample_game.get_block_color(5, 5)
        new_three = sample_game.get_block_color(3, 3)
        for index, char in enumerate(old_board):
            same = old_board[index] == sample_game.board[index]
            if index != 35 and index != 21:
                assert old_board[index] == sample_game.board[index]
        assert new_three == old_five and new_five == old_three

def test_player_deletion():
    with db_session:
        sample_game = Game(name="some game")
        sample_game.create_player("Martin")
        sample_game.create_player("Jorge")
        sample_game.create_player("Unga")
        sample_game.initialize()
        for player in sample_game.players:
            old_player = player
            break
        old_name = old_player.name
        sample_game.remove_player(old_player)
        for p in sample_game.players:
            assert p.name != old_name

def quick_showcase():
    with db_session:
        sample_game = Game(name="some game")
        sample_game.create_player("Martin")
        sample_game.create_player("Jorge")
        sample_game.create_player("Unga")
        sample_game.initialize()
        print(sample_game.board)
        old_board = sample_game.board
        old_five = sample_game.get_block_color(5, 5)
        old_three = sample_game.get_block_color(3, 3)
        sample_game.exchange_blocks(3, 3, 5, 5)
        print(sample_game.board)
        new_five = sample_game.get_block_color(5, 5)
        new_three = sample_game.get_block_color(3, 3)
        for index, char in enumerate(old_board):
            same = old_board[index] == sample_game.board[index]
            if index != 35 and index != 21:
                assert old_board[index] == sample_game.board[index]
        assert new_three == old_five and new_five == old_three
        for p in sample_game.players:
           print("id: ",  p.id, "name: ", p.name, "next: ", p.next, "color: ", p.color)
        print("Current: ", sample_game.current_player_id)
        sample_game.end_turn()
        print("Current: ", sample_game.current_player_id)
        sample_game.end_turn()
        print("Current: ", sample_game.current_player_id)
        sample_game.end_turn()
        print("Current: ", sample_game.current_player_id)
        sample_game.end_turn()
        for player in sample_game.players:
            old_player = player
            break
        old_name = old_player.name
        print("Removing ", old_name)
        sample_game.remove_player(old_player)
        print("Now in game:")
        for p in sample_game.players:
            print(p.name) 

#quick_showcase()
