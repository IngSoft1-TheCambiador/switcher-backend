from typing import DefaultDict
from collections import defaultdict
import datetime

from fastapi import WebSocket

LISTING_ID = 0
PULL_GAMES = "PULL GAMES"
UPDATE_GAME = "UPDATE GAME"
GAME_ENDED = "GAME_ENDED"


def get_time():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


class ConnectionManager:
    """
    This class is responsible for handling the connections of users to the
    server via WebSockets, keeping track of which users are connected, their
    states, and the games they are involved in. It maintains a mapping of user
    IDs to their WebSocket connections, allowing for personal messaging,
    broadcasting to all users in a specific game, or to those in a listing of
    games.

    Attributes 
    ----------
    sockets_by_id : (dict[int, WebSocket])
        A dictionary mapping IDs to WebSocket objects.
    user_state : (dict[int, str])
        A dictionary tracking the state of each user.
    game_to_sockets : (DefaultDict[int, list[int]])
        A mapping from a game ID to a list of socket IDs, the connection in the game. 
        The constant key `LISTING_ID` (0) is such that `game_to_sockets[LISTING_ID]` 
        maps to the websockets whose connection has been establish but not associated 
        with a particular game. 
    socket_to_game : (DefaultDict[int, int])
        A mapping from a socket ID to the game where the websocket is.
    current_id : (int)
        An integer used to assign unique IDs to each WebSocket connection. Holds 
        the id of the websocket which connected last.
    """

    def __init__(self) -> list[(int, WebSocket)]:
        """
        Initialization method. All attributes are set to the empty values corresponding 
        to their types.
        """

        self.sockets_by_id : dict[int, WebSocket] = {}
        self.user_state : dict[int, str] = {}
        self.game_to_sockets : DefaultDict[int, list[int]] = defaultdict(lambda : [])
        self.socket_to_game : DefaultDict[int, int] = defaultdict(lambda : [])
        self.current_id : int = 0


    async def connect(self, websocket: WebSocket) -> int:
        """

        This method links a new websocket to the connection manager,
        effectively creating a new connection. It stores 

        Parameters
        ----------
        
        websocket : Websocket 
            The websocket through which a user will communicate with the server.
        """

        await websocket.accept()
        self.current_id += 1
        self.sockets_by_id[self.current_id] = websocket
        self.game_to_sockets[LISTING_ID].append(self.current_id)
        return self.current_id

    def disconnect(self, socket_id: int) -> None:
        """

        This method removes a socket from the game it is active in,
        if such game exists.

        Parameters 
        ----------
        socket_id : int 
            The ID of the websocket to disconnect.

        """

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
        """ 

        This methods sends a personal (i.e. socket-specific) message.   

        Parameters 
        ---------- 
        socket_id : int 
            The ID of the websocket through which the message will be sent.
        message : str 
            The message to be sent.

        """

        await self.sockets_by_id[socket_id].send_text(message)

    async def broadcast_in_game(self, game_id: int, message: str) -> None:
        """ 

        This methods broadcasts a public message to all websockets within a game.

        Parameters 
        ---------- 
        game_id : int 
            The ID of the game whose websockets will receive the message.
        message : str 
            The message to be sent.

        """

        for socket_id in self.game_to_sockets[game_id]:
            #if socket_id in self.sockets_by_id.keys():
            await self.sockets_by_id[socket_id].send_text(message)
            
    async def broadcast_in_list(self, message : str) -> None:
        """ 
        This methods broadcasts a public message to all websockets whose 
        connection has been established but not associated to a particular 
        game. (See the documentation of the `game_to_sockets` attribute.)

        Parameters 
        ---------- 
        message : str 
            The message to be sent.
        """

        for socket_id in self.game_to_sockets[LISTING_ID]:
            await self.sockets_by_id[socket_id].send_text(message)

    async def trigger_updates(self, game_id: int) -> None:
        """ 
        This methods triggers an update on the state of all websockets 
        in a given game, broadcasting a message with the current time.

        Parameters 
        ---------- 
        game_id : int 
            The game whose websockets are to be updated.
        """

        for game_id in self.game_to_sockets:
            await self.broadcast_in_game(game_id, f"{UPDATE_GAME} {get_time()}")
        print(f"{UPDATE_GAME} {get_time()}")
        
    async def end_game(self, game_id : int, winner : str) -> None:
        game_ended = f"{GAME_ENDED} {winner} {get_time()}"
        sockets_in_game = self.game_to_sockets[game_id].copy()
        for socket_id in sockets_in_game:
            await self.send_personal_message(socket_id, game_ended)
            await self.remove_from_game(socket_id, game_id)
                                                                     
    async def remove_from_game(self, socket_id : int, game_id : int) -> None:
        """ 
        This methods removes a game socket from a given game. This involves 
        (a) removing it from the list of websockets associated to that game,
        and (b) reintroducing it to the list of connected websockets that 
        belong to no game.

        Parameters 
        ---------- 
        socket_id : int 
            The ID of the websocket which will be removed.
        game_id : int 
            The ID of the game from which to remove the websocket.
        """
        del self.socket_to_game[socket_id]
        self.game_to_sockets[game_id].remove(socket_id)
        self.game_to_sockets[LISTING_ID].append(socket_id) 
        await self.broadcast_in_list(f"{PULL_GAMES} {get_time()}")

    async def add_to_game(self, socket_id: int, game_id: int) -> None:
        """ 
        This methods adds a websocket to a game. The connection of said 
        websocket is assumed to have been established already. The process 
        involves not only adding the websocket to the list of websockets 
        in the game, but removing it from the list of websockets not 
        associated to any game. 

        Both websockets not yet associated to a game as well as websockets 
        in the targeted game are notified of the addition.

        Parameters 
        ---------- 
        socket_id : int 
            The ID of the websocket which will be added.
        game_id : int 
            The ID of the game from which to remove the websocket.
        """
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