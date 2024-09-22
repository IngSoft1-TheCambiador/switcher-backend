import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from connections import ConnectionManager
from pony.orm import db_session
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
        await manager.disconnect(websocket)
