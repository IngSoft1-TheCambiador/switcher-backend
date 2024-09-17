from fastapi import FastAPI
from pydantic import BaseModel
from pony.orm import db_session
from orm import Player, Game
from urllib.error import HTTPException

# Requests 

class JoinGameRequest(BaseModel):
    game_id: int 
    player_id: int

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/join-game/")
async def join_game(request: JoinGameRequest):
    with db_session:
        # Fetch the player and game from the database
        player = Player.get(_id=request.player_id)
        game = Game.get(_id=request.game_id)
        
        if player is None:
            raise HTTPException(status_code=404, detail="Player not found")
        
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Check if the player is already in the game
        if player in game.players:
            raise HTTPException(status_code=400, detail="Player is already in the game")
        
        # Check if the game has reached the maximum number of players
        if len(game.players) >= game.max_players:
            # We need to handle this appropriately
            raise HTTPException(status_code=400, detail="Game is full")
        
        # Add the player to the game
        game.add_player(request.player_id)
        
        return {"message": "Player added to the game successfully"}
