from pony.orm import Database, PrimaryKey, Required, Set, Optional

db = Database()

class Shape(db.Entity):
    id = PrimaryKey(int, auto=True)
    shape_type = Required(str)
    is_blocked = Required(bool, default=False)
    owner = Optional("Player", reverse="shapes")

class Move(db.Entity):
    id = PrimaryKey(int, auto=True)
    move_type = Required(str)
    owner = Optional("Player", reverse="moves")

class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    game = Required("Game", reverse="players")
    moves = Set("Move", reverse="owner")
    shapes = Set(Shape, reverse="owner")

    def assign_movs(self):
        pass
    def assign_shapes(self):
        pass

class Game(db.Entity):
    id = PrimaryKey(int, auto=True) 
    name = Required(str)
    min_players = Required(int, default=2, py_check=lambda x: x >= 2 and x <= 4)
    max_players = Required(int, default=4, py_check=lambda x: x >= 2 and x <= 4)
    is_init = Required(bool, default=False)
    owner_id = Required(int)
    current_player_id = Required(int)
    players = Set(Player, reverse="game")

    def add_player(self):
        pass
    def delete_player(self):
        pass
    def start(self):
        pass
    def end(self):
        pass
    def init_board(self):
        pass

db.bind("sqlite", "switcher_storage.sqlite", create_db=True)
db.generate_mapping(create_tables=True)