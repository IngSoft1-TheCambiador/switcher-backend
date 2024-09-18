from pydantic import BaseModel

class JoinGameRequest(BaseModel):
    player_id: int
    game_id: int
