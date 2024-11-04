from __future__ import annotations
from typing import Union
import socket
import uuid

class Player:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.id = str(uuid.uuid1())
        self.name = None
        self.curr_game = None
        # self.socket_thread = socket_thread

    def __str__(self):
        return f"{self.name if self.name else "no_name"} in game {self.curr_game if self.curr_game else "no_game"} {self.sock.getpeername()}"

    def __eq__(self, other):
        if isinstance(other, socket.socket):
            return self.sock == other
        elif isinstance(other, Player):
            return self.sock == other.sock
        elif isinstance(other, str):
            return self.id == other
        else: return False
