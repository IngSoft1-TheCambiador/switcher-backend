from pydantic import BaseModel

class JoinGameRequest(BaseModel):
    player_name: str
    game_id: int
