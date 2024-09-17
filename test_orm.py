from orm import Game, Player, db_session

def test_game_creation():
    with db_session:
        sample = Game(name="some game")
        sample.create_player("Martin")
        sample.create_player("Jorge")
        sample.create_player("Unga")
        assert len(sample.players) == 3
        names = set()
        for p in sample.players:
            names.append(p.name)
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
            swapped = new_three == old_five and new_five == old_three
            assert  (same or swapped)
        assert old_board != sample.board

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
            swapped = new_three == old_five and new_five == old_three
            assert  (same or swapped)
        assert old_board != sample.board
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

quick_showcase()
