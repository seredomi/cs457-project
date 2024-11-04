from typing import List, Any
import random
from player import Player 

class Game:
    def __init__(
        self,
        game_id: str,
        selected_chapters: List[int],
        owner: Player,
        all_game_ids: List[str],
    ):
        self.generate_game_id()
        while self.game_id in all_game_ids:  # ensure game ID is unique
            self.generate_game_id()

        self.connected_players: List[Player] = [owner]
        self.questions: List[Any] = []  # to be loaded with quiz data
        self.current_question_index = -1  # index of current question
        self.owner = owner
        self.selected_chapters = selected_chapters

    def generate_game_id(self):
        self.game_id: str = "".join([chr(random.randint(65, 90)) for _ in range(3)])  # a-z

    def load_questions(self, questions: List[Any]):
        # load questions from quizdataloader
        self.questions = questions

    def add_player(self, player: Player):
        if player not in self.connected_players:
            self.connected_players.append(player)

    def remove_player(self, player: Player):
        if player in self.connected_players:
            self.connected_players.remove(player)

    def advance_question(self) -> bool:
        # go to next q if available
        if self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            for player in self.connected_players:
                player.response = None  # clear responses
            return True
        return False

    def get_current_question(self) -> Any:
        # get current q basedd on index 
        if 0 <= self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None

    def record_response(self, player: Player, response: Any):
        # record player response 
        if player in self.connected_players:
            player.response = response

    def all_players_responded(self) -> bool:
        # check for response from all players for current q
        return all(player.response is not None for player in self.connected_players)

    def __str__(self):
        return (
            f"Game ID: {self.game_id}, "
            f"Owner: {self.owner.name if self.owner.name else 'no_name'}, "
            f"Players: {len(self.connected_players)}, "
            f"Current Question: {self.current_question_index + 1}/{len(self.questions)}"
        )
    def __eq__(self, other: Any):
        if isinstance(other, str):
            return self.game_id == other
        elif isinstance(other, Game):
            return self.game_id == other.game_id
        return False
