# conftest.py
import pytest
from pony.orm import db_session, Database
from orm import db, Game, Player  # Import your database object and entity classes

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
def test_initialize_game():
    game = Game(name="Test Game")
    game.create_player("Alice")
    game.create_player("Bob")
    
    game.initialize()

    assert len(game.players.current_shapes) == 6    # 6 porque cada uno deberia tener 3 (hay 2 players)
    assert len(game.players.shapes) == 50           # 50 porque cada uno deberia tener 25 en total
    assert len(game.players.moves) == 6             # 6 porque cada uno deberia tener 3

    assert game.is_init is True
    assert game.current_player_id is not None
    assert len(game.players) == 2

@db_session
def test_remove_players():
    game = Game(name="Test Game")
    game.create_player("Alice")
    game.create_player("Bob")
    
    assert len(game.players) == 2

    game.remove_player("Alice")

    assert len(game.players) == 1
    assert [p.name for p in game.players] == [ "Bob" ]

@db_session
def test_exchange_blocks():
    game = Game(name="Test Game")
    game.create_player("Alice")
    game.create_player("Bob")
    game.initialize()  # Initialize to shuffle the board

    initial_board = game.board
    game.exchange_blocks(1, 2, 5, 4)  # Exchange colors of two blocks
    
    assert game.board != initial_board  # Ensure board has changed
    assert game.get_block_color(1, 2) != game.get_block_color(5, 4)  # Ensure colors exchanged
