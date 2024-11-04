from __future__ import annotations
import socket
import random
from typing import List, Any

class Game:
    def __init__(
        self,
        game_id: str,
        all_questions: List[Any],
        selected_chapters: List[int],
        owner_id: str,
        all_game_ids: List[str],
    ):
        self.generate_game_id()
        while self.game_id in all_game_ids: # check for collisions
            self.generate_game_id()

        self.connected_players: List[str] = [owner_id]
        self.questions = []
        self.current_question = -1
        self.current_responses = {
            owner_id
        }
        self.owner_id = owner_id

    def generate_game_id(self):
        self.game_id: str = "".join([ chr(random.randint(65, 91)) for _ in range(3) ])

    def add_player(self, id: str): self.connected_players.append(id)
    def remove_player(self, id: str): self.connected_players.remove(id)

    def __str__(self): return f"{self.game_id} question: {self.current_question}/{len(self.questions)} connected players: {len(self.connected_players)}"

    # this overload allows us to remove a client from the list by comparing the socket
    def __eq__(self, other: Any):
        if isinstance(other, str):
            return self.game_id == other
        else: # its a Game
            return self.game_id == other.game_id
