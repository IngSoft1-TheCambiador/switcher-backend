from random import shuffle, choice
from pony.orm import Database, PrimaryKey, Required, Set, Optional
from pony.orm import db_session, select, commit

db = Database()

DEFAULT_BOARD = "r" * 9 + "b" * 9 + "g" * 9 + "y" * 9

class Shape(db.Entity):
    id = PrimaryKey(int, auto=True)
    shape_type = Required(str)
    is_blocked = Required(bool, default=False)
    owner = Optional("Player", reverse="shapes")
    owner_hand = Optional("Player", reverse="current_shapes") # Pony does not support owner^ = shapes_deck | current_shapes

class Move(db.Entity):
    id = PrimaryKey(int, auto=True)
    move_type = Required(str)
    owner = Optional("Player", reverse="moves")

class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    color = Optional(str)
    name = Required(str)
    game = Required("Game", reverse="players")
    moves = Set("Move", reverse="owner")
    shapes = Set(Shape, reverse="owner")
    current_shapes = Set(Shape, reverse="owner_hand") # The shapes the players can see, discard and unblock
    next = Required(int, default=0) # Id of the next player, based on turn order

    @db_session
    def add_move(self, move):
        self.moves.add(move)
        
    @db_session
    def add_shape(self, shape):
        self.shapes.add(shape)
    
    @db_session    
    def add_current_shape(self, shape):
        self.current_shapes.add(shape)

class Game(db.Entity):
    id = PrimaryKey(int, auto=True) 
    name = Required(str)
    min_players = Required(int, default=2, py_check=lambda x: x >= 2 and x <= 4)
    max_players = Required(int, default=4, py_check=lambda x: x >= 2 and x <= 4)
    is_init = Required(bool, default=False)
    owner_id = Optional(int)
    current_player_id = Optional(int)
    players = Set(Player, reverse="game")
    board = Required(str, default=DEFAULT_BOARD)
    
    @db_session
    def create_player(self, player_name):
        player = Player(name=player_name, game=self)
        if len(self.players) == 0:
            self.owner_id = player.id
        self.players.add(player)
        commit()
        return player.id

    @db_session    
    def add_player(self, player):
        self.players.add(player)

    @db_session          
    def remove_player(self, player):
        pass

    @db_session            
    def start(self):
        self.is_init = True

    @db_session            
    def end(self):
        pass

    @db_session            
    def initialize(self):
        # Set board state
        board = list(self.board)
        shuffle(board)
        self.board = "".join(board)
        # Set player order
        all_ids = []
        for p in self.players:
            all_ids.append(p.id)
        shuffle(all_ids)
        next_id = {}
        for index in range(len(all_ids)):
            current_id = all_ids[index]
            next_id[current_id] =  all_ids[(index + 1) % len(all_ids)]
        for player in self.players:
            player.next = next_id[player.id]
        # Set player colors
        colors = ["r", "g", "b", "y"]
        shuffle(colors)
        for position, player in enumerate(self.players):
            player.next = next_id[player.id]

        # Set current_player
        self.current_player_id = choice(all_ids)
        commit()
    
    @db_session            
    def get_block_color(self, i, j):
        return self.board[i * 6 + j]

    @db_session            
    def exchange_blocks(self, i, j, k, l):
        board = list(self.board)
        first_color = board[i * 6 + j]
        second_color = board[k * 6 + l]
        board[i * 6 + j] = second_color
        board[k * 6 + l] = first_color
        self.board = "".join(board)
        commit()

    @db_session        
    def end_turn(self):
        current_player = Player.get(id=self.current_player_id)
        self.current_player_id = current_player.next
        commit()

    # static, useful for testing
    @db_session
    def delete_all_games():
        Game.select().delete(bulk=True)

    @db_session 
    def dump_players(self):
        print(f"Dumping players of game {self.id}")
        for p in self.players:
            print(p.name)

db.bind("sqlite", "switcher_storage.sqlite", create_db=True)
db.generate_mapping(create_tables=True)
