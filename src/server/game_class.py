from typing import List, Any, Dict, Optional
import random
from src.server.player_class import Player

class Game:
    def __init__(
        self,
        game_id: str,
        selected_chapters: List[int],
        owner_id: str,
        owner_name: str,
        all_game_ids: List[str],
    ):
        # self.generate_game_id()
        # while self.game_id in all_game_ids:  # ensure game ID is unique
        #     self.generate_game_id()

        self.game_id = game_id
        self.owner_id = owner_id
        self.owner_name = owner_name
        self.player_responses: Dict[str, Optional[int]] = {self.owner_id: None}   # responses from players
        self.questions: List[Any] = []  # to be loaded with quiz data
        self.current_question_index = -1  # index of current question
        self.selected_chapters = selected_chapters

    def generate_game_id(self):
        self.game_id: str = "".join([chr(random.randint(65, 90)) for _ in range(3)])  # a-z

    def load_questions(self, questions: List[Any]):
        # load questions from quizdataloader
        self.questions = []

    def add_player(self, player_id: str):
        if player_id not in self.player_responses: self.player_responses[player_id] = None

    def remove_player(self, player_id: str):
        if player_id in self.player_responses: self.player_responses.pop(player_id)

    def advance_question(self) -> bool:
        # go to next q if available
        if self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            self.player_responses.update({player_id: None for player_id in self.player_responses})
            return True
        return False

    def get_current_question(self) -> Any:
        # get current q basedd on index
        if 0 <= self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None

    def record_response(self, player_id: str, response: int):
        # record player response
        if player_id in self.player_responses: self.player_responses[player_id] = response

    def all_players_responded(self) -> bool:
        # check for response from all players for current q
        return all(response is not None for response in self.player_responses.values())

    def info(self):
        return (
            f"Game ID: {self.game_id}, "
            f"Owner: {self.owner_name}, "
            f"Players: {" ".join(self.player_responses.keys())}, "
            f"Current Question: {self.current_question_index + 1}/{len(self.questions)}"
        )

    def __str__(self):
        return f"id: {self.game_id} owner: {self.owner_name} curr q: {sum([1 if not val is None else 0 for val in self.player_responses.values()])}/{len(self.player_responses.keys())} all qs: {self.current_question_index + 1}/{len(self.questions)}"

    def __eq__(self, other: Any):
        if isinstance(other, str):
            return self.game_id == other
        elif isinstance(other, Game):
            return self.game_id == other.game_id
        return False