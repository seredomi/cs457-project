from typing import List, Any, Dict, Optional, Tuple
import random

class Game:
    def __init__(
        self,
        game_id: str,
        owner_id: str,
        owner_name: str,
        questions: List[Any],
    ):
        self.game_id = game_id
        self.owner_id = owner_id
        self.owner_name = owner_name
        self.player_responses: Dict[str, Optional[int]] = {
            self.owner_name: None
        }  # responses from players
        self.questions = questions
        self.curr_qi = 0  # index of current question
        self.results: List[Dict[str, bool]] = []  # [{name: correct?}]

    def generate_game_id(self):
        self.game_id = "".join(
            [chr(random.randint(65, 90)) for _ in range(3)]
        )  # A-Z

    def get_response_progress(self) -> Tuple[int, int]:
        return (
            sum([1 if val is not None else 0 for val in self.player_responses.values()]),
            len(self.player_responses.keys())
        )

    def get_response_progress_str(self) -> str:
        return f"{self.get_response_progress()[0]}/{self.get_response_progress()[1]}"

    def get_total_status(self) -> Tuple[int, int]:
        return self.curr_qi, len(self.questions)

    def add_player(self, player_name: str):
        if player_name not in self.player_responses:
            self.player_responses[player_name] = None

    def remove_player(self, player_name: str):
        if player_name in self.player_responses:
            self.player_responses.pop(player_name)

    def store_response(self, player_name: str, response: int) -> bool:
        if player_name in self.player_responses:
            self.player_responses[player_name] = response
            possible_answers = self.get_current_question().get("possible_answers", [])
            if 0 <= response < len(possible_answers):
                is_correct = possible_answers[response].get("is_correct", False)
            else:
                is_correct = False  # Invalid response index

            # Initialize results for the current question if not already
            if len(self.results) <= self.curr_qi:
                self.results.append({player_name: is_correct})
            else:
                self.results[self.curr_qi][player_name] = is_correct
        print(self.results)
        if self.all_players_responded():
            return True  # Indicate that all players have responded
        return False

    def advance_question(self) -> bool:
        # go to next question if available
        if self.curr_qi < len(self.questions) - 1:
            self.curr_qi += 1
            self.player_responses = {player_name: None for player_name in self.player_responses.keys()}
            return True
        return False

    def get_current_question(self) -> Any:
        # get current question based on index
        if 0 <= self.curr_qi < len(self.questions):
            return self.questions[self.curr_qi]
        return None

    def record_response(self, player_name: str, response: int):
        # record player response
        if player_name in self.player_responses:
            self.player_responses[player_name] = response

    def all_players_responded(self) -> bool:
        # check for response from all players for current question
        return all(response is not None for response in self.player_responses.values())

    def info(self):
        string = f"Game ID: {self.game_id}, "
        string += f"Owner: {self.owner_name}, "
        string += f"Players: {' '.join(self.player_responses.keys())}, "
        string += f"Current Question: {self.curr_qi + 1}/{len(self.questions)}"
        return string

    def __str__(self):
        return f"id: {self.game_id} owner: {self.owner_name} curr q: {self.get_response_progress_str()} all qs: {self.get_total_status()[0]}/{self.get_total_status()[1]}"

    def __eq__(self, other: Any):
        if isinstance(other, str):
            return self.game_id == other
        elif isinstance(other, Game):
            return self.game_id == other.game_id
        return False
