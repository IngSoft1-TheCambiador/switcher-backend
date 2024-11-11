import threading
import time
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from connections import ConnectionManager
from pony.orm import db_session, select
from connections import ConnectionManager, get_time
from orm import Game, Player, Shape, PlayerMessage, LogMessage
from fastapi.middleware.cors import CORSMiddleware
from board_shapes import shapes_on_board
from constants import PLAYER_ID, GAME_ID, PAGE_INTERVAL, GAME_NAME, GAME_MIN, GAME_MAX, GAMES_LIST, STATUS, MAX_MESSAGE_LENGTH, PRIVATE
from constants import SUCCESS, FAILURE, TURN_DURATION
from wrappers import is_valid_figure, make_partial_moves_effective, search_is_valid, is_valid_password
import json
from datetime import datetime

class Timer(threading.Thread):
    def __init__(self, game_id : int):
        threading.Thread.__init__(self)
        self.current_time = TURN_DURATION
        self.game_id = game_id
        self.is_running = True
                
    def run(self):
        while self.is_running:
            time.sleep(1)
            if self.current_time == 0:
                with db_session:
                    game = Game.get(id=self.game_id)
                    player = Player.get(id = game.current_player_id)            
                    game.current_player_id = player.next
                    game.complete_player_hands(player)

                    # Send log report
                    nextPlayer = Player.get(id=player.next)

                    message = LogMessage(
                        content = f"A {player.name} se le ha acabado el tiempo. Te toca, {nextPlayer.name}!",
                        game = game,
                        timestamp = datetime.now(),
                    )
                    
                    broadcast_log = "LOG:" + json.dumps({
                    "message": message.content,
                    "time": message.timestamp.strftime('%H:%M')
                    })
                asyncio.run(manager.broadcast_in_game(self.game_id,f"TIMER_SKIP {get_time()}"))
                asyncio.run(manager.broadcast_in_game(self.game_id, broadcast_log))

                
                
            self.current_time = (self.current_time - 1) % (TURN_DURATION + 1) 
            
    def stop(self):
        self.is_running = False
        self.join()   
        
                
app = FastAPI()

manager = ConnectionManager()

timers : dict[int, Timer] = {}

origins = ["*"]
socket_id  : int
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def trigger_win_event(g : Game, p : Player):
    await manager.end_game(g.id, p.name)
    if g.id in timers.keys():
        timers[g.id].stop()
        del timers[g.id]
    g.cleanup()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/list_games")
def list_games(page : int =1):
    """
    
    This GET endpoint wraps available games into 8-element pages and 
    returns a sorted list of games in a given page. Games are sorted by 
    id. The information sent per each game is: (0) its ID, (1) its name, and
    (2) its min/max players configuration, 

    Arguments
    ----------
    page : int 
        The page to return.


    """
    with db_session:
        page = page # ¿?
        begin = PAGE_INTERVAL * (page - 1)
        end = PAGE_INTERVAL * page
        all_games = Game.select().order_by(Game.id)
        games = [game for game in all_games if not game.is_init and len(game.players) < game.max_players][begin:end]
        response_data = []
        for game in games:
            game_row = {GAME_ID : game.id, 
                GAME_NAME : game.name,
                GAME_MIN : game.min_players,
                GAME_MAX : game.max_players}
            response_data.append(game_row)
        return { GAMES_LIST : response_data,
                STATUS : SUCCESS }


@app.get("/search_games")
def search_games(player_id : int, page : int =1, text : str ="", min : str ="", max : str =""):
    """
    This GET endpoint is equivalent to list_games but it filters the games
    that include <text> in their name, ignoring the letter case
    and that have the specified max and min values
    - if a parameter has its default value, it is not filtered by this value
    - if they have an invalid value, it returns error

    Arguments
    ----------
    page : int 
        The page to return.
    text : str
        The string to filter the games with.
    min : int
        Minimum number of players.
    max : int
        Maximum number of players.
    """

    if not search_is_valid(text, min, max):
        return {"error": "Invalid search",
                    STATUS: FAILURE}

    with db_session:
        begin = PAGE_INTERVAL * (page - 1)
        end = PAGE_INTERVAL * page
        all_games = Game.select().order_by(Game.id)
        games = [game for game in all_games
            if not game.is_init and len(game.players) < game.max_players
        ]

        # Filter the list of games
        games = [game for game in games
            if  text.lower() in game.name.lower()
                and (min == "" or game.min_players == int(min))
                and (max == "" or game.max_players == int(max))
        ]
        
        response_data = []
        
        for game in all_games:
            p = Player.get(id=player_id)
            if p in game.players:
                response_data.append({GAME_ID : game.id, 
                    GAME_NAME : game.name,
                    GAME_MIN : game.min_players,
                    GAME_MAX : game.max_players,
                    PRIVATE : game.private,
                    "active" : True})
            

        games = games[begin:end]
        for game in games:
            game_row = {GAME_ID : game.id, 
                GAME_NAME : game.name,
                GAME_MIN : game.min_players,
                GAME_MAX : game.max_players,
                PRIVATE : game.private,
                "active" : False}
            response_data.append(game_row)
        return { GAMES_LIST : response_data,
                STATUS : SUCCESS }

    

@app.put("/create_game/")
async def create_game(socket_id : int, game_name : str, player_name : str,
                      min_players : int =2, max_players : int = 4,
                      password : str = ""):
    """
    This PUT endpoint creates a new `Game` object in the database. The game is
    immediately associated to (a) a player (its host or creator) and (b) a
    websocket through which communication with the host is carried out.

    Arguments 
    ---------
    socket_id : int 
        The ID of the websocket which will allow for communication with the host of the game. 
    game_name : str 
        The name of the game.
    player_name : str 
        The name of the host. 
    (optional) min_players : int = 2 
        Minimum number of players which must join the game before it may be started.
    (optional) max_players : int = 4
        Maximum number of players which can join the game.
    """
    with db_session:

        if not is_valid_password(password):
            return {
                "error": f"Invalid password {password}. Valid passwords should either be the empty string (for no password), or a password of >= 8 characters with at least one number and at least one uppercase character",
                STATUS: FAILURE
            }

        new_game = Game(name=game_name, 
                        min_players=min_players,
                        max_players=max_players,
                        password=password,
                        private=len(password) > 0
                        )




        pid = new_game.create_player(player_name)
        new_game.owner_id = pid
        await manager.add_to_game(socket_id, new_game.id)
        await manager.broadcast_in_list("GAMES LIST UPDATED")
        return {

            GAME_ID : new_game.id, 
            PLAYER_ID : pid,
            GAME_MAX : new_game.max_players,
            GAME_MIN : new_game.min_players,
            "password": password,
            STATUS : SUCCESS,
        }

@app.post("/leave_game")
async def leave_game(socket_id : int, game_id : int, player_id : int):
    """
    Removes a player from a game.

    Arguments 
    ---------
    game_id : int 
        The ID of the game from which to remove the player.
    player_id : int 
        The id of the player to remove.
    """
    with db_session:
        # somewhat ugly code raising the exception at two different places...
        game = Game.get(id=game_id)

        if game is None:
            return {"message": f"Game {game_id} does not exist.",
                    STATUS : FAILURE }
        
        p = next(( p for p in game.players if p.id == player_id ), None)
        
        if p is None:
            return {"message": f"Player {player_id} is not in game {game_id}.",
                    STATUS : FAILURE }
        
        
        if (game.is_init):
            for x in Player.select(lambda x: x.next == p.id and x.id != p.id):
                x.next = p.next
        
            if game.current_player_id == p.id:
                game.current_player_id = p.next
                timers[game_id].stop()
                timers[game_id] = Timer(game_id)
                timers[game_id].start()

           # Send log report
            '''message = LogMessage(
                content = f"{p.name} abandono la partida.",
                game = game,
                timestamp = datetime.now(),
            )

            broadcast_log = "LOG:" + json.dumps({
                "message": message.content,
                "time": message.timestamp.strftime('%H:%M')
                })
            await manager.broadcast_in_game(game_id, broadcast_log)'''
        
        '''game.players.remove(p)
        p.delete()'''
        await manager.remove_from_game(socket_id, game_id)

        if (not game.is_init and len(game.players) +1 == game.max_players):
            await manager.broadcast_in_list("GAMES LIST UPDATED")
        
        '''if ((len(game.players) == 1) and game.is_init):
            # Handle: ganador por abandono
            for p in game.players:
                await trigger_win_event(game, p)'''

        # Cancel game if owner leaves
        '''if (not game.is_init and game.owner_id == player_id):
            await manager.broadcast_in_game(game_id, "GAME CANCELLED BY OWNER")
            # unlink from the game all websockets remaining
            sockets_in_game = manager.game_to_sockets[game_id].copy()
            
            for s in sockets_in_game:
                print(f"manager.game_to_sockets[{game_id}]: {manager.game_to_sockets[game_id]}  (tomo socket {s}), socket_to_game: {manager.socket_to_game[s]}")
                await manager.remove_from_game(s, game_id)

            game.cleanup()'''

        await manager.broadcast_in_game(game_id, "LEAVE {game_id} {player_id}")

        return(
            {GAME_ID : game_id, 
                "message": f"Succesfully removed player with id {player_id} from game {game_id}",
             STATUS : SUCCESS
             })

@app.get("/list_players")
def list_players(game_id : int):
    """
    Lists all players in a given game. 

    Arguments 
    --------- 
    game_id : int 
        The ID of the game whose players will be listed.
    """
    with db_session:
        g = Game.get(id=game_id)
        g.dump_players()
        return {"Players": [p.name for p in g.players],
                STATUS : SUCCESS}


@app.websocket("/ws/connect")
async def connect(websocket: WebSocket):
    """
    
    Establishes a websocket connection in the server.

    Arguments 
    --------- 
    websocket: WebSocket 
        The websocket through which connection will be established.


    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    for reference, see: 
        https://fastapi.tiangolo.com/advanced/websockets/#create-a-websocket
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """
    socket_id = await manager.connect(websocket)
    await websocket.send_json({"socketId": socket_id})
    try:
        while True:
            try:
                data = await websocket.receive_text()
            except WebSocketDisconnect:
                print(f'The connection with id {socket_id} closed! Now cleaning up associated data')
                manager.disconnect(socket_id)
                return
    except WebSocketDisconnect:
        manager.disconnect(socket_id)


@app.post("/join_game")
async def join_game(socket_id : int, game_id : int, player_name : str,
                    password : str = "", player_id : int = -1):
    """
    
    Creates a new player in a game. This function handles creating the `Player`
    object in the corresponding `Game` object of the database as well as 
    setting the websocket connection of the player in the game. 

    Arguments 
    --------- 
    socket_id : int 
        ID of the websocket through which communication with the new player will occur. 
    game_id : int 
        The ID of the game where the new player will be created.
    player_name : str 
        The name of the created player.
    password : str | defaults to ""
        A password which must match that of the game
        
    """
    with db_session:
        # Retrieve the game by its ID
        game = Game.get(id=game_id)
        
        # Check if the game exists
        if not game:
            return {"error": "Game not found",
                    STATUS : FAILURE}
        
        if len(game.players) +1 == game.max_players:
            await manager.broadcast_in_list("GAMES LIST UPDATED")

        if len(game.password) > 0 and password != game.password:
            return {"error": "Incorrect password",
                    STATUS : FAILURE}
            
        if player_id != -1:
            p = Player.get(id=player_id)
            if p in game.players:
                for x in Player.select(lambda x: x.next == p.next and x.id != p.id):
                    x.next = p.id
                await manager.add_to_game(socket_id, game_id)
                return ({
                    "player_id": player_id,
                    "owner_id": game.owner_id,
                    "player_names": [p.name for p in game.players],
                    STATUS: SUCCESS
                    })
            else:
                 # Check if the game has enough room for another player
                if len(game.players) >= game.max_players:
                    return {"error": "Game is already full",
                            STATUS: FAILURE}
                    
                for x in Game.select(lambda x : p in x.players):
                    message = LogMessage(
                        content = f"{p.name} abandono la partida.",
                        game = x,
                        timestamp = datetime.now(),
                    )

                    broadcast_log = "LOG:" + json.dumps({
                        "message": message.content,
                        "time": message.timestamp.strftime('%H:%M')
                        })
                    await manager.broadcast_in_game(x.id, broadcast_log)
                    x.players.remove(p)
                    p.delete()

                    if (not x.is_init and x.owner_id == player_id):
                        await manager.broadcast_in_game(x.id, "GAME CANCELLED BY OWNER")
                        # unlink from the game all websockets remaining
                        sockets_in_game = manager.game_to_sockets[x.id].copy()
                    
                        for s in sockets_in_game:
                            print(f"manager.game_to_sockets[{x.id}]: {manager.game_to_sockets[x.id]}  (tomo socket {s}), socket_to_game: {manager.socket_to_game[s]}")
                            await manager.remove_from_game(s, x.id)

                        x.cleanup()
                    
                    elif ((len(x.players) == 1) and x.is_init):
                    # Handle: ganador por abandono
                        for p in x.players:
                            await trigger_win_event(x, p)
                    await manager.broadcast_in_game(x.id, "LEAVE {game_id} {player_id}")
                
                pid = game.create_player(player_name)
                await manager.add_to_game(socket_id, game_id)
                return ({
                        "player_id": pid,
                        "owner_id": game.owner_id,
                        "player_names": [p.name for p in game.players],
                        "is_init" : game.is_init,
                        STATUS: SUCCESS
                        })
                
        else:
             # Check if the game has enough room for another player
            if len(game.players) >= game.max_players:
                return {"error": "Game is already full",
                        STATUS: FAILURE}
            pid = game.create_player(player_name)
            await manager.add_to_game(socket_id, game_id)
            return ({
                    "player_id": pid,
                    "owner_id": game.owner_id,
                    "player_names": [p.name for p in game.players],
                    STATUS: SUCCESS
                    })
    
@app.get("/game_state")
def game_state(socket_id : int):
    """
    
    Given the ID of a websocket, it retrieves relevant data from the game where 
    the websocket lives. Retrieved data is: 

        ~ The name of the game.
        ~ The ID of the owner (or host) of the game.
        ~ Is the game initialized?
        ~ The IDs of all players in the game. 
        ~ The names of all players in the game.
        ~ The player whose turn is. 
        ~ The color of all players in the game. 
        ~ The figure cards each player has. 
        ~ The movement cards each player has. 
        ~ Max and min players allowed in the game. 

    Arguments 
    --------- 
    socket_id : int 
        ID of a websocket that lives in the game of interest.
        
    """
    
    if socket_id not in manager.socket_to_game.keys():
        return({"error" : "Socket not in a game",
               STATUS : FAILURE})

    game_id = manager.socket_to_game[socket_id]

    with db_session:
        game = Game.get(id=game_id)
        
        if game is None:
            return {"message": f"Game {game_id} does not exist.",
                    STATUS : FAILURE }

        f_cards, m_cards, names, colors, f_deck_ids = {}, {}, {}, {}, {}
        f_hands, f_hand_ids, f_hand, f_hand_blocked = {}, {}, {}, {}
        player_ids = []
        for p in game.players:
            player_ids.append(p.id)
            f_cards[p.id] = sorted([f.shape_type for f in p.shapes ])
            f_deck_ids[p.id] = sorted([f.id for f in p.shapes])
            m_cards[p.id] = sorted([f.move_type for f in p.moves ])
            names[p.id] = p.name
            colors[p.id] = p.color

            f_hands[p.id] = sorted(p.current_shapes)
            f_hand_ids[p.id] = [f.id for f in f_hands[p.id]]
            f_hand[p.id] = [f.shape_type for f in f_hands[p.id] ]
            f_hand_blocked[p.id] = [f.is_blocked for f in f_hands[p.id] ]
        
        ingame_shapes = []
        
        for cards in f_hands.values():
            ingame_shapes += [card.shape_type for card in cards if not card.is_blocked]
            
        boolean_boards = [b for b in shapes_on_board(game.board) if b.shape_code in ingame_shapes]
        highlighted_squares = [0 for _ in range(36)]
        
        for b in boolean_boards:
            flat_board = b.board.reshape(-1)
            highlighted_squares = highlighted_squares + flat_board
                
        return({
            "initialized":  game.is_init,
            "player_ids": player_ids,
            "current_player": game.current_player_id,
            "player_names": names,
            "player_colors": colors,
            "player_f_cards": f_cards,
            "player_f_hand": f_hand,
            "player_f_hand_blocked": f_hand_blocked,
            "player_f_hand_ids": f_hand_ids,
            "player_f_deck_ids": f_deck_ids,
            "player_m_cards": m_cards,
            "owner_id" : game.owner_id,
            "max_players" : game.max_players,
            "min_players" : game.min_players,
            "name" : game.name,
            "actual_board" : game.board,
            "old_board" : game.old_board,
            "move_deck" : game.move_deck,
            "highlighted_squares" : ''.join(str(x) for x in highlighted_squares),
            "forbidden_color": game.forbidden_color,
            STATUS : SUCCESS
            })
            
@app.put("/skip_turn")
async def skip_turn(game_id : int, player_id : int):
    """
    Let the player with `player_id` as ID skip a turn in the game 
    with `game_id` as ID.
    
    If `player_id` is the current player of the `Game` object with 
    `game_id` as ID, and that game is already running (i.e. 
    `game.is_init == True`), assign `Game[game_id].current_player_id` 
    to `Player[player_id].next`.
    
    Otherwise, nothing happens.
    
    Arguments
    ---------
    game_id : int 
        ID of the game.
    player_id : int
        ID of the player.
    """
    with db_session:
       # This fails if there is no game with game_id as id

        game = Game.get(id=game_id)
        player = Player.get(id = player_id)

        if game is None or player is None:
            return {"message": f"Game {game_id} or player {player_id} do not exist.",
                    STATUS : FAILURE}
        if not game.is_init:
            return { "message": f"Game {game_id} has not yet begun.",
                    STATUS : FAILURE}
        if player not in game.players:
            return { "message": f"Game {game_id} has no player with id {player_id}.",
                    STATUS : FAILURE}
        if game.current_player_id != player_id:
            return { "message": f"It is not the turn of player {player_id}.",
                    STATUS: FAILURE }
            
        game.current_player_id = player.next
        game.complete_player_hands(player)
        if game_id in timers.keys():
            timers[game_id].stop()
            timers[game_id] = Timer(game_id)
            timers[game_id].start()
        await manager.broadcast_in_game(game_id, "SKIP {game_id} {player_id}")

       # Send log report
        nextPlayer = Player.get(id=player.next)

        message = LogMessage(
            content = f"{player.name} ha saltado su turno. Te toca, {nextPlayer.name}!",
            game = game,
            timestamp = datetime.now(),
        )

        broadcast_log = "LOG:" + json.dumps({
            "message": message.content,
            "time": message.timestamp.strftime('%H:%M')
            })
        await manager.broadcast_in_game(game_id, broadcast_log)

        return {
            "message" : f"Player {player_id} skipped in game {game_id}",
            STATUS : SUCCESS
        }


@app.post("/partial_move")
async def partial_move(game_id : int, player_id : int, mov : int, a : int, b : int, x : int, y : int): 
    """
    Effects a partial move - i.e. changes the board in accordance to a played 
    movement card.

    Parameters
    ----------
    game_id : int 
        ID of the game where the new checkpoint board is to be committed.
    player_id : int
        ID of the player who used the move card.
    mov : int
        id of the mov (of the player).
    a,b,x,y: int
        Positions of the board to be swapped
        Swap coordinates (a,b) and (x,y)
    """

    with db_session:
        game = Game.get(id=game_id)
        player = Player.get(id=player_id)
        if game is None:
            return {"message": f"Game {game_id} does not exist.",
                    STATUS : FAILURE}
        if player is None:
            return {"message": f"Game {game_id} does not exist.",
                    STATUS : FAILURE}
        if game.current_player_id != player_id:
            return { "message": f"It is not the turn of player {player_id}.",
                    STATUS: FAILURE }
        game.exchange_blocks(a, b, x, y)
        await manager.broadcast_in_game(game_id, "PARTIAL_MOVE {} {}".format(player_id, mov))
        return {
            "actual_board" : game.board, 
            "old_board" : game.old_board,
            STATUS: SUCCESS
        }

@app.post("/undo_moves")
async def undo_moves(game_id : int): 
    """
    Undoes all the partial moves

    Parameters
    ----------
    game_id : int 
        ID of the game where the new checkpoint board is to be committed.
    """

    with db_session:
        game = Game.get(id=game_id)
        if game is None:
            return {"message": f"Game {game_id} does not exist.",
                    STATUS : FAILURE }

        game.undo_moves() # <-------------------

        await manager.broadcast_in_game(game_id, "PARTIAL MOVES WERE DISCARDED")
        return {
            "true_board" : game.board,
            STATUS: SUCCESS
        }


@app.put("/start_game")
async def start_game(game_id : int):
    """
    Calls the initialization function of a specified game. The call triggers 
    dealing of cards, assignment of turns, and other steps required for the game 
    to begin. Players are informed of the initialization through a websocket broadcast.
    
    Arguments 
    ---------
    game_id : int 
        ID of the game to start.
    """
    with db_session:
        game = Game.get(id=game_id)
        game.initialize()
        await manager.broadcast_in_game(game_id, "INITIALIZED")
        timers[game_id] = Timer(game_id)
        timers[game_id].start()
        return {"message" : f"Starting {game_id}",
                STATUS: SUCCESS}


@app.put("/block_figure") 
async def block_figure(game_id: int, player_id: int,
                       fig_id: int, used_movs : str,
                       x: int, y : int):
    """

    When a player attempts to block a rival's figure card, a request to this
    endpoint is sent. The endpoint checks if the chosen position of the board
    actually contains the specified figure. If it does, it blocks the figure
    card and commits the board.
    
    Arguments 
    ---------
    game_id : int 
        ID of the game.
    player_id : int 
        ID of the player who wants to block a rival's fig card.
    fig_id : int 
        The ID of the figure card that the player attempts to block.
    used_movs : str 
        A string of the form `m₁,m₂,…,mₙ` with mᵢ being the 
        ith movement card used by the current player.
    x : int 
        x-coord of the board position sent by player.
    y : int 
        y-coord of the board position sent by player.
    """

    with db_session:

        game = Game.get(id=game_id)
        p = Player.get(id = player_id)

        if game is None or p is None:
            return {"message": f"Game {game_id} or p {player_id} do not exist.",
                    STATUS: FAILURE}
        if game.current_player_id != player_id:
            return { "message": f"It is not the turn of player {player_id}.",
                    STATUS: FAILURE }
        
        if game.get_block_color(x, y) == game.forbidden_color:
            return {
                "message": f"({x}, {y}) has the forbidden color {game.forbidden_color}",
                    STATUS: FAILURE}

        shape = Shape.get(id=fig_id)

        if shape is None:
            return {"message": f"Figure card {fig_id} does not exist",
                    STATUS: FAILURE}
        
        if shape.owner_hand.id == player_id:
            return {"message": f"Can't block your own card.",
                    STATUS: FAILURE}
        
        if shape.is_blocked:
            return {"message": f"The card is already blocked.",
                    STATUS: FAILURE}
        
        if any(f.is_blocked for f in shape.owner_hand.current_shapes):
            return {"message": f"Another card of {shape.owner_hand.id} has already been blocked.",
                    STATUS: FAILURE}
        
        if len(shape.owner_hand.current_shapes) == 1:
            return {"message": f"Can't block the last card of the hand.",
                    STATUS: FAILURE}

        is_valid_response = is_valid_figure(game.board, shape.shape_type, x, y)

        if is_valid_response[STATUS] == FAILURE:
            return is_valid_response
       
        # If the code reaches this point, it is because: (a) the player has 
        # the figure card, and (b) the figure exists at pos (x, y).
        game.forbidden_color = game.get_block_color(x, y)
        make_partial_moves_effective(game, used_movs, player_id)
        shape.is_blocked = True

        # Send log report of used cards
        blocked_player = shape.owner_hand
        cards_to_send = [shape.shape_type]

        if used_movs != '':
            cards_to_send.extend(used_movs.split(","))
            msg_content = f"{p.name} ha usado: &?&{p.name} le ha bloqueado a {blocked_player.name} la figura: "
        else:
            msg_content = f"{p.name} le ha bloqueado a {blocked_player.name} la figura: "

        message = LogMessage(
            content = msg_content,
            game = game,
            timestamp = datetime.now(),
            played_cards = cards_to_send
        )

        broadcast_log = "LOG:" + json.dumps({
            "message": message.content,
            "time": message.timestamp.strftime('%H:%M'),
            "cards": cards_to_send
            })
        await manager.broadcast_in_game(game_id, broadcast_log)

        return {
            "true_board" : game.board,
            STATUS: SUCCESS
        }

        


@app.put("/claim_figure")
async def claim_figure(game_id : int, 
                          player_id : int, 
                          fig_id : int, 
                          used_movs : str,
                          x : int, y: int
                          ):
    """

    When a player attempts to claim a figure card of his hand by 
    pointing to a figure in the board, a request to this endpoint 
    is sent. The endpoint checks if the chosen position of the 
    board actually contains the specified figure. If it does, 
    it removes the figure card from the player's hand, the 
    movement cards he may have used, and commits the board.
    
    Arguments 
    ---------
    game_id : int 
        ID of the game.
    player_id : int 
        ID of the player.
    fig_id : int 
        The ID of the figure card that the player attempts to claim.
    used_movs : str 
        A string of the form `m₁,m₂,…,mₙ` with mᵢ being the 
        ith movement card used by the current player.
    x : int 
        x-coord of the board position sent by player.
    y : int 
        y-coord of the board position sent by player.
    """
    with db_session:

        game = Game.get(id=game_id)
        p = Player.get(id = player_id)

        if game is None or p is None:
            return {"message": f"Game {game_id} or p {player_id} do not exist.",
                    STATUS: FAILURE}
        if game.current_player_id != player_id:
            return { "message": f"It is not the turn of player {player_id}.",
                    STATUS: FAILURE }

        if game.get_block_color(x, y) == game.forbidden_color:
            return {
                "message": f"({x}, {y}) has the forbidden color {game.forbidden_color}",
                    STATUS: FAILURE}
        
        shape = Shape.get(id=fig_id)

        if shape is None:
            return {"message": f"Figure card {fig_id} does not exist",
                    STATUS: FAILURE}
        
        if shape.owner_hand.id != player_id:
            return {"message": f"p {player_id} does not have the {shape.shape_type} card.",
                    STATUS: FAILURE}
       
        if shape.is_blocked:
            return {"message": f"The card is blocked.",
                    STATUS: FAILURE}

        is_valid_response = is_valid_figure(game.board, shape.shape_type, x, y)

        if is_valid_response[STATUS] == FAILURE:
            return is_valid_response

        # If the code reaches this point, it is because: (a) the player has 
        # the figure card, and (b) the figure exists at pos (x, y).
        game.forbidden_color = game.get_block_color(x, y)
        make_partial_moves_effective(game, used_movs, player_id)


        # Send log report of used cards
        cards_to_send = [shape.shape_type]

        if used_movs != '':
            cards_to_send.extend(used_movs.split(","))
            msg_content = f"{p.name} ha usado: &?&{p.name} ha completado la figura: "
        else:
            msg_content = f"{p.name} ha completado la figura: "

        message = LogMessage(
            content = msg_content,
            game = game,
            timestamp = datetime.now(),
            played_cards = cards_to_send
        )

        broadcast_log = "LOG:" + json.dumps({
            "message": message.content,
            "time": message.timestamp.strftime('%H:%M'),
            "cards": cards_to_send
            })

        shape.delete()

        if len(p.current_shapes) == 0 and len(p.shapes) == 0:
            await trigger_win_event(game, p)
            return {"message" : f"Player {p.name} won the game"}
        
        await manager.broadcast_in_game(game_id, broadcast_log)

        if len(p.current_shapes) == 1:
            s = [s for s in p.current_shapes]
            if s[0].is_blocked:
                s[0].is_blocked = False
                s[0].was_blocked = True

                # Send log report for card unlock
                message = LogMessage(
                    content = f"{p.name} desbloqueo su figura: ",
                    game = game,
                    timestamp = datetime.now(),
                    played_cards = [s[0].shape_type]
                )

                broadcast_log = "LOG:" + json.dumps({
                    "message": message.content,
                    "time": message.timestamp.strftime('%H:%M'),
                    "cards": message.played_cards
                })

                await manager.broadcast_in_game(game_id, broadcast_log)

        return {
            "true_board" : game.board,
            STATUS: SUCCESS
        }


@app.post("/send_message")
async def send_message(game_id : int, sender_id : int, txt : str):
    """

    Creates a Message object in the database and broadcasts the message
    via weboscket.
    
    Arguments 
    ---------
    game_id : int 
        ID of the game where the message is sent.
    sender_id : int 
        ID of the player who sent the message. Set to -1 to specify that this
        message was sent by the system - i.e. it's a log message.
    txt : str 
        The message to be sent
    """
    with db_session:

        if len(txt) > MAX_MESSAGE_LENGTH:
            return

        game = Game.get(id=game_id)
        p = Player.get(id=sender_id)

        if game is None or p is None:
            return {"message": f"Game {game_id} or p {sender_id} do not exist.",
                    STATUS: FAILURE}

        message = PlayerMessage(
            content = txt,
            game = game,
            player = p,
            timestamp = datetime.now()
        )

        broadcast_messasge = "NEW CHAT MSG:" + json.dumps({
            "message": txt,
            "sender_color": p.color,
            "sender_name": p.name,
            "time": message.timestamp.strftime('%H:%M')
        })


        await manager.broadcast_in_game(game_id, broadcast_messasge)
        return {
            'message': txt,
            'sender_color': p.color,
            'sender_name': p.name,
            'time': message.timestamp.strftime('%H:%M'),
            STATUS: SUCCESS
        }


@app.get("/get_messages")
async def get_messages(game_id : int):
    """

    Gets all messages in the database and returns them ordered by their 
    timestamp.
    
    Arguments 
    ---------
    game_id : int 
        ID of the game where the messages we want to retrieve were sent.
    """
    with db_session:


        game = Game.get(id=game_id)

        if game is None:
            return {"message": f"Game {game_id} does not exist.",
                    STATUS: FAILURE}

        L = []
        log_messages = sorted(LogMessage.select(lambda message: message.game.id == game_id), key=lambda message: message.timestamp)
        player_messages = sorted(PlayerMessage.select(lambda message: message.game.id == game_id), key=lambda message: message.timestamp)
        all_messages = sorted(log_messages + player_messages, key=lambda message: message.timestamp)

        for msg in all_messages:
            print(msg.content)
            # Ideally, we would use `isinstance`, but doesn't seem to work with 
            # db.Entities.
            class_name = msg.__class__.__name__
            if class_name == 'PlayerMessage':
                formatted_msg = {
                        "sender": msg.player.name,
                        "color": msg.player.color,
                        "message": msg.content,
                        "time": msg.timestamp.strftime('%H:%M')
                    }
            elif class_name == 'LogMessage':
                formatted_msg = {
                        "sender": "Log",
                        "color": "log",
                        "message": msg.content,
                        "time": msg.timestamp.strftime('%H:%M'),
                        "cards": msg.played_cards
                    }
            else: 
                return{"error": "CRITICAL ERROR: Non-specific message type found among the message database.", 
                       STATUS: FAILURE}
            L.append(formatted_msg)


        return {
            'message_list': L,
            STATUS: SUCCESS
        }
      

@app.get("/get_current_time") 
async def get_current_time(game_id : int):
    with db_session:
        game = Game.get(id=game_id)
        print(f"INFO: {game}")
        if game is None or not game.is_init:
            return {"current_time" : -1}
        
    return {"current_time" : timers[game_id].current_time}

@app.put("/relink_to_game")
async def relink_to_game(socket_id : int, game_id : int):
    await manager.add_to_game(socket_id, game_id)
        
