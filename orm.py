from random import shuffle, choice
from pony.orm import Database, PrimaryKey, Required, Set, Optional
from pony.orm import db_session, select, commit

db = Database()

DEFAULT_BOARD = "r" * 9 + "b" * 9 + "g" * 9 + "y" * 9
DEFAULT_HARD_SHAPES = ["h1", "h2", "h3", "h4", "h5", "h6", "h7", "h8", "h9", "h10", "h11", "h12", "h13", "h14", "h15", "h16", "h17", "h18"]*2
DEFAULT_SIMPLE_SHAPES = ["s1", "s2", "s3", "s4", "s5", "s6", "s7"]*2
DEFAULT_MOVES = ["mov1", "mov2", "mov3", "mov4", "mov5", "mov6", "mov7"]*7

class Shape(db.Entity):
    """
    This class represents a shape card (carta de figura).

    Attributes
    ---------- 
    id : int 
        The ID of the instance. 
    shape_type : str 
        A description of the kind of figure the instance is. 
    is_blocked : bool 
        Is the figure blocked? 
    (optional) owner : Player
        The Player who owns the card. 
    (optional) owner_hand : Player 
        ?
    """
    id = PrimaryKey(int, auto=True)
    shape_type = Required(str)
    is_blocked = Required(bool, default=False)
    owner = Optional("Player", reverse="shapes")
    owner_hand = Optional("Player", reverse="current_shapes") # Pony does not support owner^ = shapes_deck | current_shapes

class Move(db.Entity):
    """
    This class represents movement cards. 

    Attributes
    -----------
    id : int 
        The ID of the instance.
    move_type : str 
        A description of the kind of movement the card effects. 
    (optional) owner : Player
        The Player who owns the card. 

    """
    id = PrimaryKey(int, auto=True)
    move_type = Required(str)
    owner = Optional("Player", reverse="moves")

class Player(db.Entity):
    """
    This class represents players in the game. Every player is associated to a game:
    users who aren't in a game do not constitute instances of this class. 

    Attributes 
    ----------
    id : int 
        The ID of the instance. 
    (optional) color : str 
        The color which was assigned to this player in the game. 
    name : str 
        The name of this player.
    game : Game
        The game this player is part of.
    moves : Set("Move")
        The set of movement cards this player has.
    shapes : Set(Shape)
        The set of shape cards this player has.
    current_shapes : Set(Shape) 
        The shapes the players can see, discard and unblock.
    next : int 
        The ID of the player who follows this player in the turn order.
    """
    id = PrimaryKey(int, auto=True)
    color = Optional(str)
    name = Required(str)
    game = Required("Game", reverse="players")
    moves = Set("Move", reverse="owner")
    shapes = Set(Shape, reverse="owner")
    current_shapes = Set(Shape, reverse="owner_hand") 
    next = Required(int, default=0) 

    @db_session
    def add_move(self, move):
        """
        Adds a movement card to the set of movement cards a player has.

        Parameters 
        ---------
        move : Move 
            A Move object (representing a movement card).
        """
        self.moves.add(move)
        
    @db_session
    def add_shape(self, shape):
        """
        Adds a shape card to the set of shape cards a player has.

        Parameters 
        ---------
        move : Move 
            A Shape object (representing a movement card).
        """
        self.shapes.add(shape)
    
    @db_session    
    def add_current_shape(self, shape):
        """
        Adds a shape to the set of shapes the player can see, 
        discard or unblock.

        Parameters 
        ---------
        move : Move 
            A Shape object.
        """
        self.current_shapes.add(shape)

    @db_session
    def remove(self):
        '''
        Delete a player after deleting its shapes and movements.
        '''
        for shape in self.shapes:
            shape.delete()
        for shape in self.current_shapes:
            shape.delete()
        for move in self.moves:
            move.delete()
        self.delete()
        commit()

class Game(db.Entity):
    """
    This class represents Switcher games.

    Attributes 
    ----------
    id : int
        The ID of this game.
    name : str 
        : The name of this game.
    min_players : int 
        Minimum number of players required for the game to be played.
    max_players : int 
        Maximum number of players allowed in the game. 
    is_init : bool 
        Has the game begun?
    owner_id : int 
        The ID of the host/owner of the game.
    current_player_id : int 
        The ID of the player whose turn is.
    players : Set(Player) 
        The set of players in this game.
    board : str 
        A string representation of the game board.
    """
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
        """
        Creates a Player in a game, storing it in the 
        database.

        Parameters 
        ---------- 
        player_name : str 
            The name of the player to be created.
        """
        player = Player(name=player_name, game=self)
        if len(self.players) == 0:
            self.owner_id = player.id
        self.players.add(player)
        commit()
        return player.id

    @db_session          
    def remove_player(self, player_name):
        """
        Removes a player from a game.
        """
        player = Player.get(name=player_name, game=self)
        self.players.remove(player)

    @db_session            
    def end(self):
        """This function ends the game. (...)"""
        pass

    @db_session            
    def initialize(self):
        """ 
        Initializes the game. The initialization process consists of: 

            (a) Shuffling the board, which prior to initialization is in a default state. 
            (b) Setting up the order in which players will play. 
            (c) Shuffling and dealing cards to the players.
        """
        self.is_init = True
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
        # Set player cards
        p_quantity = len(self.players)
        hard_shapes = list(DEFAULT_HARD_SHAPES)
        shuffle(hard_shapes)
        simple_shapes = list(DEFAULT_SIMPLE_SHAPES)
        shuffle(simple_shapes)
        move_types = list(DEFAULT_MOVES)
        shuffle(move_types)
        for player in self.players:
            shapes = []
            moves = []
            shapes_in_hand = []
            match p_quantity:
                case 2:
                    for x in range(7):
                        shapes.append(simple_shapes.pop())
                    for x in range(18):
                        shapes.append(hard_shapes.pop())
                    shuffle(shapes)
                case 3:
                    for x in range(4):
                        shapes.append(simple_shapes.pop())
                    for x in range(12):
                        shapes.append(hard_shapes.pop())
                    shuffle(shapes)
                case 4:
                    for x in range(3):
                        shapes.append(simple_shapes.pop())
                    for x in range(9):
                        shapes.append(hard_shapes.pop())
                    shuffle(shapes)
            for x in range(3):
                moves.append(move_types.pop())
                shapes_in_hand.append(shapes.pop())
            for m in moves:
                mov = Move(move_type=m, owner=player)
                player.moves.add(mov)
            for s in shapes:
                shape = Shape(shape_type=s, owner=player)
                player.shapes.add(shape)
            for h in shapes_in_hand:
                hand = Shape(shape_type=h, owner_hand=player)
                player.shapes.add(hand)

        # Set current_player
        self.current_player_id = choice(all_ids)
        commit()
    
    @db_session            
    def get_block_color(self, i, j):
        """
        Returns the color of the square at position (i, j) in the board.

        Arguments 
        ---------
        i : int 
            Self explanatory.
        j : int 
            Self explanatory.
        """
        return self.board[i * 6 + j]

    @db_session            
    def exchange_blocks(self, i, j, k, l):
        """
        Swaps the squares at positions (i, j) and (k, l) in the board.

        Arguments 
        ---------
        i : int 
            Self explanatory.
        j : int 
            Self explanatory.
        k : int 
            Self explanatory.
        l : int 
            Self explanatory.
        """
        board = list(self.board)
        first_color = board[i * 6 + j]
        second_color = board[k * 6 + l]
        board[i * 6 + j] = second_color
        board[k * 6 + l] = first_color
        self.board = "".join(board)
        commit()

    @db_session        
    def end_turn(self):
        """
        Ends the turn of the current player and begins the turn of his successor in 
        the turn order.
        """
        current_player = Player.get(id=self.current_player_id)
        self.current_player_id = current_player.next
        commit()
        
    # just a helper for debugging
    @db_session 
    def dump_players(self):
        """
        Helper (debugging) function. Prints all players in the current game.
        """
        print(f"Dumping players of game {self.id}")
        for p in self.players:
            print(p.name)

    @db_session        
    def cleanup(self):
        """
        Deletes a game, its players, their shapes and their movements.
        """
        for player in self.players:
            # Call 'custom' player removal method, which
            # handles all moves and shapes depending on
            # a given player
            player.remove()
        # Call Pony's delete for the Game instance
        self.delete()
        commit()

db.bind("sqlite", "switcher_storage.sqlite", create_db=True)
db.generate_mapping(create_tables=True)
