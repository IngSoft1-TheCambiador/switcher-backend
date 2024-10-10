from typing import DefaultDict
from collections import defaultdict
import datetime

from fastapi import WebSocket

LISTING_ID = 0
PULL_GAMES = "PULL GAMES"
UPDATE_GAME = "UPDATE GAME"

def get_time():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

class ConnectionManager:

    def __init__(self) -> list[(int, WebSocket)]:

        self.sockets_by_id : dict[int, WebSocket] = {}
        self.user_state : dict[int, str] = {}
        self.game_to_sockets : DefaultDict[int, list[int]] = defaultdict(lambda : [])
        self.socket_to_game : DefaultDict[int, int] = defaultdict(lambda : [])
        self.current_id : int = 0

    async def connect(self, websocket: WebSocket) -> int:
        await websocket.accept()
        self.current_id += 1
        self.sockets_by_id[self.current_id] = websocket
        self.game_to_sockets[LISTING_ID].append(self.current_id)
        return self.current_id

    def disconnect(self, socket_id: int) -> None:
        # Remove the socket from the game it is active in, if there is one
        if socket_id in self.socket_to_game.keys():
            game = self.socket_to_game[socket_id]
            self.game_to_sockets[game].remove(socket_id)
        if socket_id in self.game_to_sockets[LISTING_ID]:
            self.game_to_sockets[LISTING_ID].remove(socket_id)
        # Delete the socket object and remove the key from the dictionary
        # storing all connections
        self.sockets_by_id[socket_id] = None
        del self.sockets_by_id[socket_id]
        self.socket_to_game[socket_id] = None
        del self.socket_to_game[socket_id]

    async def send_personal_message(self, socket_id : int, message : str) -> None:
        await self.sockets_by_id[socket_id].send_text(message)

    async def broadcast_in_game(self, game_id: int, message: str) -> None:
        for socket_id in self.game_to_sockets[game_id]:
            #if socket_id in self.sockets_by_id.keys():
            await self.sockets_by_id[socket_id].send_text(message)
            
    async def broadcast_in_list(self, message : str) -> None:
        for socket_id in self.game_to_sockets[LISTING_ID]:
            await self.sockets_by_id[socket_id].send_text(message)

    async def trigger_updates(self, game_id: int) -> None:
        for game_id in self.game_to_sockets:
            await self.broadcast_in_game(game_id, f"{UPDATE_GAME} {get_time()}")
        print(f"{UPDATE_GAME} {get_time()}")
        
    async def end_game(self, game_id : int, winner : str) -> None:
        game_ended = f"{GAME_ENDED} {winner} {get_time()}"
        for socket_id in self.game_to_sockets[game_id]:
            await self.send_personal_message(socket_id, game_ended)
                                                                     
    async def remove_from_game(self, socket_id : int, game_id : int) -> None:
        self.game_to_sockets[game_id].remove(socket_id)
        self.game_to_sockets[LISTING_ID].append(socket_id) 
        await self.broadcast_in_list(f"{PULL_GAMES} {get_time()}")

    async def add_to_game(self, socket_id: int, game_id: int) -> None:
        if game_id not in self.game_to_sockets.keys():
            self.game_to_sockets[game_id] = []
            print("EL PROBLEMA NO ES GAME_TO_SOKTS")
        self.game_to_sockets[game_id].append(socket_id)
        # This is linear in the number of players currently not in a game, so we should make it a set instead of a list
        self.socket_to_game[socket_id] = game_id
        if socket_id in self.game_to_sockets[LISTING_ID]:
            self.game_to_sockets[LISTING_ID].remove(socket_id)
        print("EL PROBLEMA NO ES SOCKET_TO_GAME")
        await self.broadcast_in_list(f"{PULL_GAMES} {get_time()}") # In case a game was filled
        #await self.trigger_updates(game_id)
        await self.broadcast_in_game(game_id, f"{PULL_GAMES} {get_time()}")
