from fastapi import FastAPI
from pony.orm import db_session
from orm import Game, Player
from models import JoinGameRequest

app = FastAPI()

PLAYER_ID = "player_id"
GAME_ID = "game_id"
PAGE_INTERVAL = 8 # Number of games listed per page
GAME_NAME = "game_name"
GAME_MIN = "min_players"
GAME_MAX = "max_players"
GAMES_LIST = "games_list"

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


@app.post("/join-game")
def join_game(request: JoinGameRequest):
    with db_session:
        # Retrieve the game by its ID
        game = Game.get(id=request.game_id)
        player = Player.get(id=request.player_id)
        
        # Check if the game exists
        if not game:
            return {"error": "Game not found"}
        
        # Check if the game has enough room for another player
        if len(game.players) >= game.max_players:
            return {"error": "Game is already full"}

        # Create a new player and associate with the game
        player_id = game.add_player(player)

        return {
            "message": f"Player {request.player_id} successfully joined the game {request.game_id}",
        }
