import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from connections import ConnectionManager
from pony.orm import db_session, delete, commit
from orm import Game, Player
from fastapi.testclient import TestClient

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

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/list_games")
def list_games(page=1):
    with db_session:
        page = int(page)
        begin = PAGE_INTERVAL * (page - 1)
        end = PAGE_INTERVAL * page
        sorted_games = Game.select().order_by(Game.id)[begin:end]
        response_data = []
        for game in sorted_games:
            game_row = {GAME_ID : game.id, 
                GAME_NAME : game.name,
                GAME_MIN : game.min_players,
                GAME_MAX : game.max_players}
            response_data.append(game_row)
        return { GAMES_LIST : response_data }

@app.put("/create_game/")
def create_game(game_name, player_name, min_players=2, max_players=4):
    try:
        with db_session:
            new_game = Game(name=game_name)
            player_id = new_game.create_player(player_name)
            new_game.owner_id = player_id
            game_id = new_game.id
            game_data = {GAME_ID : game_id, PLAYER_ID : player_id}
            return game_data
    except:
        raise HTTPException(status_code=400,
                            detail=GENERIC_SERVER_ERROR)

@app.post("/leave_game")
def leave_game(game_id : int, player_name : str):
    with db_session:
        # somewhat ugly code raising the exception at two different places...
        game = Game.get(id=game_id)

        if game is None:
            raise HTTPException(status_code=400, detail=GENERIC_SERVER_ERROR)
        
        p = next(( p for p in game.players if p.name == player_name ), None)
        
        if p is None:
            raise HTTPException(status_code=400, detail=GENERIC_SERVER_ERROR)

        if len(game.players) == 2:
            # Handle: ganador por abandono
            pass

        if len(game.players) == 1:
            # Handle: el creador abandono antes de que se una nadie
            pass

        game.players.remove(p)
        p.delete()

        return(
                {GAME_ID : game_id, 
                 "message": f"Succesfully removed player {player_name} from game {game_id}"}
                )

@app.get("/list_players")
def list_players(game_id : int):
    with db_session:
        g = Game.get(id=game_id)
        g.dump_players()
        return {"Players": [p.name for p in g.players]}


@app.websocket("/ws/connect")
async def connect(websocket: WebSocket):
    await manager.connect(websocket)
    await websocket.send_json({"msg": "Hello WebSocket"})
    try:
        while True:
            # will remove later because the client
            # doesnt use their websocket to send
            # data to the server, but the other 
            # way around
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/join_game")
def join_game(game_id, player_name):
    with db_session:
        # Retrieve the game by its ID
        game = Game.get(id=game_id)
        
        # Check if the game exists
        if not game:
            return {"error": "Game not found"}
        
        # Check if the game has enough room for another player
        if len(game.players) >= game.max_players:
            return {"error": "Game is already full"}

        if player_name in [ p.name for p in game.players ]:
            return{"error" : "A player with this name already exists in the game"}

        pid = game.create_player(player_name)

        return ({
                "player_id": pid,
                "game_id": game.id,
                "message": f"Player {pid} joined the game {game_id}"
                })

