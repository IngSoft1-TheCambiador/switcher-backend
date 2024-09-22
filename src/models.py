from pydantic import BaseModel

class JoinGameRequest(BaseModel):
    player_name: str
    game_id: int

class CreateGameRequest(BaseModel):
    player_name: str
    game_name: str 
    min_players: int | None = None  # Optional, since Game() class has default.
    max_players: int | None = None  # Same as above
