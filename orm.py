from random import shuffle, sample
from pony.orm import Database, PrimaryKey, Required, Set, Optional, StrArray
from pony.orm import db_session, commit
from enum import StrEnum
from datetime import datetime

db = Database()

DEFAULT_BOARD = "r" * 9 + "b" * 9 + "g" * 9 + "y" * 9
Color = StrEnum("Color", ["r", "b", "g", "y", "NULL_COLOR"])

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
    was_blocked : bool
        If the figure has been unblocked but not used
    (optional) owner : Player
        The Player who owns the card. 
    (optional) owner_hand : Player 
        The Player who owns the card and has it in its current hand.
    """
    id = PrimaryKey(int, auto=True)
    shape_type = Required(str)
    is_blocked = Required(bool, default=False)
    was_blocked = Required(bool, default=False)
    owner = Optional("Player", reverse="shapes")
    owner_hand = Optional("Player", reverse="current_shapes") 

class Move(db.Entity): 
    """ 
    This class represents movement cards. Attributes -----------
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
    color = Optional(str, default=Color.NULL_COLOR)
    name = Required(str)
    game = Required("Game", reverse="players")
    moves = Set("Move", reverse="owner")
    shapes = Set(Shape, reverse="owner")
    current_shapes = Set(Shape, reverse="owner_hand") 
    next = Required(int, default=0) 
    messages = Set("PlayerMessage", reverse="player")

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
        previous = list(self.game.players.filter(lambda p: p.next == self.id))
        if previous:
            previous = previous[0]
            previous.next = self.next
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
    old_board : str 
        A string representation of the game board as it was before the 
        last (yet unapplied) partial moves.
        on it.
    move_deck : list of strings 
        A list of strings representing movement cards not held by any player.
    forbidden_color : Optional(str, default=Color.NULL_COLOR)
        The forbidden color in the game.
    player_messages : Set("PlayerMessage", reverse="game")
        The messages sent by players in this game.
    log_messages : Set("LogMessage", reverse="game")
        The messages sent by the system in this game.
    password : str 
        The password of the game 
    private : bool 
        Does the game have a password?
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
    old_board = Optional(str, default=DEFAULT_BOARD)
    move_deck = Optional(StrArray, default = [f"mov{i}" for i in range(1, 8)] * 7)
    forbidden_color = Optional(str, default=Color.NULL_COLOR)
    player_messages = Set("PlayerMessage", reverse="game")
    log_messages = Set("LogMessage", reverse="game")
    password = Optional(str, default="")
    private = Optional(bool, default=False)

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
    def set_turns_and_colors(self):
        colors = [Color.r, Color.b, Color.y, Color.g]
        players = [p for p in self.players]
        shuffle(players)
        shuffle(colors)
        N = len(self.players)

        for i in range(N):
            players[i].next = players[(i+1) % N].id
            players[i].color = colors[i] 

        self.current_player_id = players[0].id
    

    @staticmethod
    @db_session
    def sample_cards(k, cards, adjust_to_shortage=False):
        """
        Randomly sample k cards (without replacement) from a list of cards
        in-place. The list is understood to be a list of strings. This entails
        this method is applicable to `self.move_deck`. 

        To ensure type consistency, this method always returns a list. If k == 0,
        an empty list is returned. Otherwise, the sampled cards are returned.

        Attributes 
        ----------
        k : int 
            Number of cards to sample without replacement. 
        cards : list{
            The list to sample from.
        """

        if k < 0:
            raise(ValueError("Cannot sample k < 0 cards from a deck."))

        if k == 0:
            return []

        if k > len(cards):
            if not adjust_to_shortage:
                raise(
                        ValueError("""
                        k > len(cards) : Cannot sample more elements than exist. If you 
                        wish to deal as many cards as possible to handle this situation,
                        set the `adjust_to_shortage` parameter to `True`.
                                 """
                    ))
            k = len(cards)
    
        S = sample(cards, k)
        
        for s in S:
            cards.remove(s)

        return(S)

    @db_session 
    def deal_cards_randomly(self):
        """
        This function samples hands from their respective decks without
        replacement, dealing them to the players. Importantly, it gives 
        players the figure cards without specifying which of those will 
        be in their hand. In other words, the `current_shapes` attribute 
        of all players is left unmodified.

        """
        # (H)ard figures, (S)imple figures
        H = [f"h{i}" for i in range(1, 19)] * 2
        S = [f"s{i}" for i in range(1, 8)] * 2

        decks = [self.move_deck, H, S]
        ℓ = lambda x: len(x) // len(self.players)
        cards_to_deal = [3, ℓ(H), ℓ(S)]

        for player in self.players:
            # Deal cards to player.
            dealt_hands = [Game.sample_cards(k, cards) for (k, cards) in zip(cards_to_deal, decks)]
            
            # Transform dealt cards (strings) to corresponding Pony entities.
            [player.moves.add( Move(move_type=m, owner=player) ) for m in dealt_hands[0]]
            [player.shapes.add( Shape(shape_type=h, owner = player) ) for h in dealt_hands[1]]
            [player.shapes.add( Shape(shape_type=s, owner = player) ) for s in dealt_hands[2]]



    @db_session
    def complete_player_hands(self, player : Player):
        """
        At any given point in time, a player may have less than 
        49 // number_of_players movement cards and/or less than 
        three figure cards in its current shapes. This method 
        resolves this situation by dealing the necessary number 
        of (a) movement cards from the `self.move_deck` and/or (b)
        figure cards from `player.shapes`.

        Parameters 
        ----------
        player : Player 
            The player whose figure and movement hands will be completed.
        """

        m_cards_to_deal = 3 - len(player.moves)
        f_cards_to_deal = 3 - len(player.current_shapes)

        if m_cards_to_deal > 0:
            dealt_move_cards = Game.sample_cards(m_cards_to_deal, self.move_deck)
            [player.moves.add( Move(move_type=card, owner=player) ) for card in dealt_move_cards]

        if len(player.current_shapes) == 1:
            shape = [s for s in player.current_shapes]
            if shape[0].is_blocked:
                shape[0].is_blocked = False
                shape[0].was_blocked = True

        if any( [(f.is_blocked or f.was_blocked) for f in player.current_shapes] ):
            return

        if f_cards_to_deal > 0: 
            shapes = [s for s in player.shapes]
            dealt_fig_cards = Game.sample_cards(f_cards_to_deal, shapes, adjust_to_shortage=True)
            [player.current_shapes.add(card) for card in dealt_fig_cards]
            # This is necessary because `sample_cards` will remove the sampled 
            # cards from the local list `shapes`, not from the player's 
            # `Set`.
            [player.shapes.remove(card) for card in dealt_fig_cards]


    @db_session 
    def retrieve_player_move_cards(self, player_id :int, move_types : list):

        p = Player.get(id=player_id) 
            
        for m_type in move_types:
            m_card = next ( (m for m in p.moves if m.move_type == m_type), None )
            if m_card is None:
                continue
            self.move_deck.append(m_type)
            m_card.delete()


        

    @db_session            
    def initialize(self):
        """ 
        Initializes the game. The initialization process consists of: 

            (a) Shuffling the board, which prior to initialization is in a default state. 
            (b) Setting up the order in which players will play. 
            (c) Shuffling and dealing cards to the players.
        """

        if self.is_init:
            raise(RuntimeError("Calling `initialize` on an already initialized game will cause errors."))
        # Shuffle the board
        board_list = list(self.board)  # Convert the string to a list
        shuffle(board_list)            # Shuffle the list in place
        self.board = "".join(board_list)  # Join the shuffled list back into a string
        self.old_board = self.board
        # Set turns
        self.set_turns_and_colors()
        # Deal cards
        self.deal_cards_randomly()
        # Pass figure cards from `shapes` to `current_shapes` in all players 
        [self.complete_player_hands(p) for p in self.players]
        # Ready to go!
        self.is_init = True


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
    def commit_board(self):
        """
        Takes a snapshot of the current board and stores it as the `old_board`
        in the game, effectively creating a checkpoint to return to if partial
        moves must be undone.
        """
        self.old_board = self.board 
        commit()

    @db_session 
    def undo_moves(self):
        """
        Undoes the partial moves storing the `old_board` in the `new_board`
        """
        self.board = self.old_board 
        commit()

    @db_session            
    def exchange_blocks(self, i, j, k, l):
        """
        Swaps the squares at positions (i, j) and (k, l) in the board board.
        This changes are not reflected on the actual board until 
        a call to apply_board_changes() is made.

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
        
        if any(arg > 5 for arg in [i, j, k, l]):
            raise(ValueError("""Invalid swap coordinates: in a 6x6 board, 
                             all coordinate values must range in {0, 1, …, 5}"""))

        board = list(self.board)
        board[k * 6 + l], board[i * 6 + j] = board[i * 6 + j], board[k * 6 + l]
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



class PlayerMessage(db.Entity):
    id = PrimaryKey(int, auto=True)
    content = Required(str)
    timestamp = Required(datetime)
    game = Required(Game, reverse='player_messages')
    player = Required(Player, reverse='messages')

class LogMessage(db.Entity):
    id = PrimaryKey(int, auto=True)
    content = Required(str)
    timestamp = Required(datetime)
    game = Required(Game, reverse='log_messages')
    played_cards = Required(StrArray, default=[])











db.bind("sqlite", "switcher_storage.sqlite", create_db=True)
db.generate_mapping(create_tables=True)
