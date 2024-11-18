from typing import List, Any, Dict, Optional, Tuple
import random
from src.utils.messages import send_message


class Game:
    def __init__(
        self,
        game_name: str,
        owner_id: str,
        owner_name: str,
        questions: List[Any],
    ):
        self.game_name = game_name
        self.owner_id = owner_id
        self.owner_name = owner_name
        self.player_responses: Dict[str, Optional[int]] = {
            self.owner_name: None
        }  # responses from players
        self.questions = questions
        self.curr_qi = 0  # index of current question

    def generate_game_id(self):
        self.game_name: str = "".join(
            [chr(random.randint(65, 90)) for _ in range(3)]
        )  # a-z

    def get_response_progress(self) -> Tuple[int, int]:
        return (
            sum([1 if val is not None else 0 for val in self.player_responses.values()]),
            len(self.player_responses.keys())
        )

    def get_response_progress_string(self) -> str:
        return f"{self.get_response_progress()[0]}/{self.get_response_progress()[1]}"

    def get_total_status(self) -> Tuple[int, int]:
        return self.curr_qi, len(self.questions)


    def add_player(self, player_name: str):
        if player_name not in self.player_responses:
            self.player_responses[player_name] = None

    def remove_player(self, player_name: str):
        if player_name in self.player_responses:
            self.player_responses.pop(player_name)
        if not self.player_responses or (
            self.curr_qi == len(self.questions) - 1 and self.all_players_responded()
        ):
            self.send_results()
            self.delete_game()

    def store_response(self, player_name: str, response: int) -> bool:
        if player_name in self.player_responses:
            self.player_responses[player_name] = response
            is_correct = self.get_current_question().get("possible_answers")[response].get("is_correct")
            if len(self.results) == self.curr_qi +1:
                self.results[self.curr_qi][player_name] = is_correct
            else:
                self.results.append({player_name: is_correct})
                
            if self.all_players_responded():
                if self.curr_qi == len(self.questions) - 1:
                    self.send_results()
                    self.delete_game()
                    return True
                else:
                    self.advance_question()
                    return True
            return False

    def advance_question(self) -> bool:
        # go to next q if available
        if self.curr_qi < len(self.questions) - 1:
            self.curr_qi += 1
            self.player_responses.update(
                {player_name: None for player_name in self.player_responses.keys()}
            )
            return True
        return False

    def get_current_question(self) -> Any:
        # get current q basedd on index
        if 0 <= self.curr_qi < len(self.questions):
            return self.questions[self.curr_qi]
        return None

    def record_response(self, player_name: str, response: int):
        # record player response
        if player_name in self.player_responses:
            self.player_responses[player_name] = response

    def all_players_responded(self) -> bool:
        # check for response from all players for current q
        return all(response is not None for response in self.player_responses.values())
    
    def send_results(self):
        results_message = {
            "message_type": "results",
            "results": self.results,
    }
        for player_name in self.player_responses.keys():
            player_socket = self.get_player_socket(player_name)
            if player_socket:
                send_message(self.logger, results_message, player_socket)

    def info(self):
        string = f"Game ID: {self.game_name}, "
        string += f"Owner: {self.owner_name}, "
        string += f"Players: {' '.join(self.player_responses.keys())}, "
        string += f"Current Question: {self.curr_qi + 1}/{len(self.questions)}"
        return string

    def __str__(self):
        return f"id: {self.game_name} owner: {self.owner_name} curr q: {sum([1 if val is not None else 0 for val in self.player_responses.values()])}/{len(self.player_responses.keys())} all qs: {self.curr_qi + 1}/{len(self.questions)}"

    def __eq__(self, other: Any):
        if isinstance(other, str):
            return self.game_name == other
        elif isinstance(other, Game):
            return self.game_name == other.game_name
        return False
