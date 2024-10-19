# conftest.py
import pytest
from pony.orm import db_session
from orm import db, Game, Player, Shape, Move, DEFAULT_BOARD  # Import your database object and entity classes

# Para referencia de qué hace esto, ver: 
# https://stackoverflow.com/questions/57639915/pony-orm-tear-down-in-testing
# scope = function ---> ejecuta este setup antes de cada test 
# autouse = True -----> usa este fixture en todos los tests, sin necesidad de que te lo especifique
@pytest.fixture(scope='function', autouse=True)
def setup_database():
    db.provider = db.schema = None
    db.bind(provider='sqlite', filename=':memory:')
    db.generate_mapping(create_tables=True)

    with db_session:
        yield

    db.rollback()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Game class tests
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@db_session
def test_create_game():
    game = Game(name="Test Game")
    assert game.name == "Test Game"
    assert game.is_init is False
    assert len(game.players) == 0

@db_session
def test_create_and_add_player():
    game = Game(name="Test Game")
    player_name = "Alice"
    
    player_id = game.create_player(player_name)
    player = Player.get(id=player_id)

    assert player.name == player_name
    assert player.game == game
    assert len(game.players) == 1

@db_session
def test_turn_and_color_setting():

    game = Game(name = "Test Game")

    pids = [game.create_player(name) for name in ["Chipá", "Carpincho", "Tucán"]]

    old_order = [Player[id] for id in pids]

    # Assert no player has a color set
    assert all( [Player[id].color == "" for id in pids] )
    # Assert no player has cards
    game.set_turns_and_colors()
    assert not any( [Player[id].color == "" for id in pids] )
    assert game.current_player_id is not None


@db_session
def test_complete_player_hands():


    game = Game(name = "asdaosjd")

    pids = [game.create_player(name) for name in ["Chipá", "Carpincho", "Tucán"]]
    game.initialize()


    p = Player[pids[0]]

    player_f_hand = [card for card in p.current_shapes]
    player_m_hand = [card for card in p.moves]

    player_f_deck = [card for card in p.shapes]

    L = len(p.moves)
    ℓ = len(game.move_deck)

    # Remove two cards from the movement cards of the player
    player_f_hand[0].delete()
    player_f_hand[1].delete()
    player_m_hand[0].delete()
    player_m_hand[1].delete()

    assert len(p.moves) == L - 2
    assert len(p.current_shapes) == 1

    game.complete_player_hands(p)
    
    assert len(p.current_shapes) == 3
    assert len(p.moves) == L
    assert len(game.move_deck) == ℓ - 2

    # Empty shape deck
    [shape.delete() for shape in p.shapes]
    # Empty shape hand
    [shape.delete() for shape in p.current_shapes]

    # Create artifical shape deck with only 1 card
    p.shapes.add(Shape(shape_type="a"))
    # Create artifical shape hand with only 1 card
    p.current_shapes.add(Shape(shape_type="b"))

    assert len(p.current_shapes) == 1 
    assert len(p.shapes) == 1
    # Call complete_player_hands in the limit case, where 
    # 2 hands are requested from deck but only one exist.
    game.complete_player_hands(p)

    assert len(p.current_shapes) == 2 
    assert len(p.shapes) == 0



@db_session
def test_initialize_game(n_players = 2):



    # Valid f-cards
    𝕍_fig = ["s1", "s2", "s3", "s4", "s5", "s6", "s7", 
         "h1", "h2", "h3", "h4", "h5", "h6", "h7", 
         "h8", "h9", "h10", "h11", "h12", "h13", "h14", 
         "h15", "h16", "h17", "h18"
               ]
    # Valid m-cards
    𝕍_mov = ["mov1", "mov2", "mov3", "mov4", "mov5", "mov6", "mov7"]
    game = Game(name="Test Game")


    for i in range(n_players):
        game.create_player(str(i))

    game.initialize()

    # Best to check that everything went okay in the specific dealing 
    # with each player before checking the global aspectos of the `game`.
    for p in game.players:
        assert len([h for h in p.current_shapes]) == 3
        assert len([s for s in p.shapes]) == (50 // len(game.players) ) - 3
        assert len([m for m in p.moves]) == 3

        assert all(shape.shape_type in 𝕍_fig for shape in p.shapes)
        assert all(move.move_type in 𝕍_mov for move in p.moves)

    assert len(game.move_deck) == 49 - 3*len(game.players)
    assert game.is_init is True
    assert game.current_player_id is not None
    assert len(game.players) == n_players
    assert game.board == game.old_board




@db_session
def test_remove_players():
    game = Game(name="Test Game")
    alice_id = game.create_player("Alice")
    bob_id = game.create_player("Bob")
    carl_id = game.create_player("Carl")
    alice = Player[alice_id]
    bob = Player[bob_id]
    carl = Player[carl_id]
    alice.next = bob_id
    bob.next = carl_id
    carl.next = alice_id
    assert len(game.players) == 3
    carl.remove()
    assert len(game.players) == 2
    assert set([p.name for p in game.players]) == set([ "Alice", "Bob" ])
    assert bob.next == alice_id

# This test is wrong! game.initialize() randomizes the board,
# so the swap sometimes swaps equivalent elements, causing the 
# the test to fail even though it performed correctly.
@db_session
def test_exchange_blocks():
    game = Game(name="Test Game")
    game.create_player("Alice")
    game.create_player("Bob")
    game.initialize()  # Initialize to shuffle the board

    game.board = DEFAULT_BOARD
    game.exchange_blocks(0, 0, 5, 5)  # Exchange colors of two blocks
    
    assert game.board == "yrrrrrrrrbbbbbbbbbgggggggggyyyyyyyyr"

@db_session 
def test_retrieve_move_cards():

    game = Game(name="Test Game")


    ids = [game.create_player(str(i)) for i in range(3)]
    game.initialize()

    p = Player.get(id=ids[1])

    game.move_deck = []
    p.moves = [Move(move_type="m1"), Move(move_type="m2"), Move(move_type="m3"), 
               Move(move_type="m3"), Move(move_type="m2") ]

    game.retrieve_player_move_cards(p.id, ["m2", "m3", "m3"])

    assert len(p.moves) == 2 
    assert [m.move_type for m in p.moves] == [ "m2", "m1" ]
    assert len(game.move_deck) == 3 
    assert game.move_deck == ["m2", "m3", "m3"]


@db_session
def test_game_cleanup():
    game_name = "Test Game"
    game = Game(name=game_name)
    game.create_player("Alice")
    game.create_player("Bob")
    game.initialize()
    all_names = set([game.name for game in Game.select()])
    assert game_name in all_names
    game.cleanup()
    all_names = set([game.name for game in Game.select()])
    assert game_name not in all_names
    

























