from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from connections import ConnectionManager
from pony.orm import db_session
from orm import Game, Player
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

manager = ConnectionManager()

# Response field names
PLAYER_ID = "player_id"
GAME_ID = "game_id"
PAGE_INTERVAL = 8 # Number of games listed per page
GAME_NAME = "game_name"
GAME_MIN = "min_players"
GAME_MAX = "max_players"
GAMES_LIST = "games_list"
# Error details
GENERIC_SERVER_ERROR = '''The server received data with an unexpected format or failed to respond due to unknown reasons'''

origins = ["*"]
socket_id  : int
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        sorted_games = Game.select().order_by(Game.id)[begin:end]
        response_data = []
        for game in sorted_games:
            if len(game.players) < game.max_players and not game.is_init:
                game_row = {GAME_ID : game.id, 
                    GAME_NAME : game.name,
                    GAME_MIN : game.min_players,
                    GAME_MAX : game.max_players}
                response_data.append(game_row)
        return { GAMES_LIST : response_data }

@app.put("/create_game/")
async def create_game(socket_id : int, game_name : str, player_name : str, min_players : int =2, max_players : int =4):
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
    try:
        with db_session:
            new_game = Game(name=game_name)
            player_id = new_game.create_player(player_name)
            new_game.owner_id = player_id
            new_game.max_players = int(max_players)
            new_game.min_players = int(min_players)
            game_id = new_game.id
            game_data = {GAME_ID : game_id, PLAYER_ID : player_id}
            await manager.add_to_game(socket_id, game_id)
            return game_data
    except Exception as e:
        print(type(e))
        print(e.args)
        print(e)
        #raise HTTPException(status_code=400,
                            #detail=GENERIC_SERVER_ERROR)

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
            print("Game not found. Rasing HTTP Exception 400")
            raise HTTPException(status_code=400, detail=GENERIC_SERVER_ERROR)
        
        p = next(( p for p in game.players if p.id == player_id ), None)
        
        if p is None:
            print("Player not found. Rasing HTTP Exception 400")
            raise HTTPException(status_code=400, detail=GENERIC_SERVER_ERROR)
        
        if (game.is_init):
            previous = Player.get(next=p.id)
            previous.next = p.next
        
            if game.current_player_id == p.id:
                game.current_player_id = p.next
        
        game.players.remove(p)
        p.delete()
        manager.remove_from_game(socket_id, game_id)
        
        if ((len(game.players) == 1) & game.is_init):
            # Handle: ganador por abandono
            for p in game.players:
                winner_name = p.name
            await manager.end_game(game_id, winner_name)
            game.cleanup()
        else:
            await manager.broadcast_in_game(game_id, "LEAVE {game_id} {player_id}")

        return(
                {GAME_ID : game_id, 
                 "message": f"Succesfully removed player with id {player_id} from game {game_id}"}
                )

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
        return {"Players": [p.name for p in g.players]}


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
async def join_game(socket_id : int, game_id : int, player_name : str):
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
    game_player : str 
        The name of the created player.
        
    """
    with db_session:
        # Retrieve the game by its ID
        game = Game.get(id=game_id)
        
        # Check if the game exists
        if not game:
            return {"error": "Game not found"}
        
        # Check if the game has enough room for another player
        if len(game.players) >= game.max_players:
            return {"error": "Game is already full"}

        #if player_name in [ p.name for p in game.players ]:
            #return{"error" : "A player with this name already exists in the game"}

        pid = game.create_player(player_name)
        await manager.add_to_game(socket_id, game_id)
        return ({
                "player_id": pid,
                "owner_id": game.owner_id,
                "player_names": [p.name for p in game.players]
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
        return({"error:" : "Socket not in a game"})

    game_id = manager.socket_to_game[socket_id]

    with db_session:
        game = Game.get(id=game_id)
        
        if game is None:
            print("Game not found. Rasing HTTP Exception 400")
            raise HTTPException(status_code=400, detail=GENERIC_SERVER_ERROR)

        f_cards, f_hands, m_cards, names, colors = {}, {}, {}, {}, {}
        player_ids = []
        for p in game.players:
            player_ids.append(p.id)
            f_cards[p.id] = [p.shape_type for p in p.shapes ]
            f_hands[p.id] = [p.shape_type for p in p.current_shapes ]
            m_cards[p.id] = [p.move_type for p in p.moves ]
            names[p.id] = p.name
            colors[p.id] = p.color

        return({
            "initialized":  game.is_init,
            "player_ids": player_ids,
            "current_player": game.current_player_id,
            "player_names": names,
            "player_colors": colors,
            "player_f_cards": f_cards,
            "player_f_hand": f_hands,
            "player_m_cards": m_cards,
            "owner_id" : game.owner_id,
            "max_players" : game.max_players,
            "min_players" : game.min_players,
            "name" : game.name,
            "actual_board" : game.board,
            "old_board" : game.old_board,
            "move_deck" : game.move_deck
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
        ID of the game
    player_id : int
        ID of the player
    """
    try:
        with db_session:
            # This fails if there is no game with game_id as id
            game = Game[game_id]
            if player_id == game.current_player_id and game.is_init:
                current = Player[player_id]
                next_id = current.next
                game.current_player_id = next_id
                await manager.broadcast_in_game(game_id, "SKIP {game_id} {player_id}")
                return {"message" : f"Player {player_id} skipped in game {game_id}"}
            else:
                failure_message = f'''
                Received a skip request in game {game_id} with player id {player_id},
                but either there is no such game, no such player, no such player in
                such game, or the player is not currently holding the 'current player'
                position.
                '''
                return {"message" : failure_message}
    except:
        raise HTTPException(status_code=400,
                            detail=f"Failed to skip turn in game {game_id} with player id {player_id}")
    


@app.post("/partial_move")
async def partial_move(game_id : int, a : int, b : int, x : int, y : int): 
    """
    Effects a partial move - i.e. changes the board in accordance to a played 
    movement card.
    """

    with db_session:
        game = Game[game_id]
        if game is None:
            print("Game not found. Rasing HTTP Exception 400")
            raise HTTPException(status_code=400, detail=GENERIC_SERVER_ERROR)
        game.exchange_blocks(a, b, x, y)
        await manager.broadcast_in_game(game_id, "PARTIAL MOVE EFFECTED")
        return {
            "actual_board" : game.board, 
            "old_board" : game.old_board
        }

@app.post("/commit_board")
async def commit_board(game_id : int): 
    """
    Takes a snapshot of the current board and stores it as the `old_board` in the game,
    effectively creating a checkpoint to return to if partial moves must be undone.

    Parameters
    ----------
    game_id : int 
        ID of the game where the new checkpoint board is to be committed.
    """

    with db_session:
        game = Game[game_id]
        if game is None:
            print("Game not found. Rasing HTTP Exception 400")
            raise HTTPException(status_code=400, detail=GENERIC_SERVER_ERROR)
        game.commit_board()
        await manager.broadcast_in_game(game_id, "PARTIAL MOVES WERE PERMANENTLY APPLIED")
        return {
            "true_board" : game.board
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
    try:
        with db_session:
            game_id = int(game_id) # ¿?
            game = Game[game_id]
            game.initialize()
            await manager.broadcast_in_game(game_id, "INITIALIZED")
            return {"message" : f"Starting {game_id}"}
    except:
        raise HTTPException(status_code=400,
                            detail=f"Failed to initialize game {game_id}")

