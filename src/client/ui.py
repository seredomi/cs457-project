import urwid
import asyncio
from queue import Queue
from src.utils.messages import send_message
from prettytable import PrettyTable
from typing import Dict, List


class UIHandler:
    def __init__(self, client, logger):
        self.client = client
        self.logger = logger
        self.message_queue = Queue()
        self.curr_screen = "connecting"
        self.running = False

        # Create UI elements
        self.txt_title = urwid.Text("Connecting...")
        self.txt_instructions = urwid.Text("")
        self.input_box = urwid.Edit("> ")

        # Create main UI layout
        self.frame = urwid.Frame(
            urwid.Filler(urwid.Pile([
                self.txt_title,
                urwid.Divider(),
                self.txt_instructions,
                urwid.Divider(),
                self.input_box
            ])),
        )

    def start(self):
        self.running = True
        # Instead of creating a thread, we'll create the loop
        self.loop = urwid.MainLoop(
            self.frame,
            unhandled_input=self.handle_input,
            event_loop=urwid.AsyncioEventLoop(loop=asyncio.get_event_loop())
        )
        self.loop.set_alarm_in(0.1, self.update_display)
        self.loop.run()

    def stop(self):
        self.running = False
        raise urwid.ExitMainLoop()

    def update_display(self, loop, user_data):
        # Process message queue
        while not self.message_queue.empty():
            msg = self.message_queue.get()
            if msg["message_type"] == "new_connection_prompt":
                self.curr_screen = "main_menu"
            elif msg["message_type"] == "results":
                self.curr_screen = "results"
            elif msg["message_type"] == "quiz_question":
                self.curr_screen = "quiz_question"

        # Update display based on current screen
        if self.curr_screen == "connecting":
            self.txt_title.set_text("connecting...")
            if self.client.is_connected:
                self.curr_screen = "main_menu"

        elif self.curr_screen == "main_menu":
            menu_text = "1. start a new game"
            if self.client.curr_games:
                menu_text += "\n2. join a current game"
            menu_text += "\n3. exit"

            self.txt_title.set_text("=== main menu ===")
            self.txt_instructions.set_text(menu_text)
            self.input_box.set_caption("choose option: ")

        elif self.curr_screen == "create_game_1":
            self.txt_title.set_text("=== create game ===")
            self.txt_instructions.set_text("enter your player name. cant be a current player")
            self.input_box.set_caption("")
        elif self.curr_screen == "create_game_2":
            self.txt_title.set_text("=== create game ===")
            self.txt_instructions.set_text("enter game name")
            self.input_box.set_caption("")
        elif self.curr_screen == "create_game_3":
            self.txt_title.set_text("=== create game ===")
            chapters_sorted = sorted([int(c) for c in self.client.available_chapters.keys()])
            self.txt_instructions.set_text(
                f"choose chapters from this list: {' '.join([str(c) for c in chapters_sorted])}\nenter as chapter numbers separated by spaces: "
            )
            self.input_box.set_caption("")
        elif self.curr_screen == "create_game_4":
            self.txt_title.set_text("=== create game ===")
            self.txt_instructions.set_text(f"enter number of questions. max: {sum([self.client.available_chapters[c] for c in self.client.chosen_chapters])}\nenter as a plain normal number")
            self.input_box.set_caption("")

        elif self.curr_screen == "join_game_1":
            self.txt_title.set_text("=== join game ===")
            self.txt_instructions.set_text("enter your player name. cant be a current player")
            self.input_box.set_caption("")
        elif self.curr_screen == "join_game_2":
            self.txt_title.set_text("=== join game ===")
            self.txt_instructions.set_text(f"enter game name from this list: {' '.join(self.client.curr_games)}")
            self.input_box.set_caption("")

        elif self.curr_screen == "quiz_question":
            self.txt_title.set_text(f"=== {self.client.curr_question['topic']} ===")
            content = f"player answers: {self.client.response_progress}\n"
            content += f"\n{self.client.curr_question['question']}\n\n"
            for i, option in enumerate(self.client.curr_question['possible_answers']):
                content += f"{chr(65+i)}. {option['answer']}\n"
            self.txt_instructions.set_text(
                content
            )
            self.input_box.set_caption("choose option: ")

        elif self.curr_screen == "quiz_question_waiting":
            self.txt_instructions.set_text(f"player answers: {self.client.response_progress}\nwaiting for all responses")

        elif self.curr_screen == "results":
            self.txt_title.set_text("=== quiz results ===")
            self.txt_instructions.set_text(self.print_quiz_results())
            self.input_box.set_caption("press enter to return to main menu")

        if self.running:
            self.loop.set_alarm_in(0.1, self.update_display)

    def handle_input(self, key):
        if key == 'enter':
            user_input = self.input_box.get_edit_text()

            if self.curr_screen == "results":
                self.client.player_name = "no_name"
                self.curr_screen = "main_menu"

            elif user_input.lower() == 'q':
                if self.curr_screen == "main_menu":
                    self.client.disconnect()
                else:
                    message = {
                        "message_type": "game_update",
                        "subtype": "player_leave",
                        "player_name": self.client.player_name,
                        "game_id": self.client.game_id
                    }
                    self.client.game_id = "no_game"
                    send_message(self.logger, message, self.client.sock)

            elif self.curr_screen == "main_menu":
                if user_input == "1":
                    self.curr_screen = "create_game_1"
                elif user_input == "2" and self.client.curr_games:
                    self.curr_screen = "join_game_1"
                elif user_input == "3":
                    self.client.disconnect()

            elif self.curr_screen == "create_game_1":
                if user_input not in self.client.curr_players and user_input != "no_name":
                    self.client.player_name = user_input
                    self.curr_screen = "create_game_2"
            elif self.curr_screen == "create_game_2":
                if user_input not in self.client.curr_games:
                    self.client.game_id = user_input
                    self.curr_screen = "create_game_3"
            elif self.curr_screen == "create_game_3":
                chapters = user_input.split()
                if len(chapters) > 0 and all([c in self.client.available_chapters.keys() for c in chapters]):
                    self.client.chosen_chapters = chapters
                    self.curr_screen = "create_game_4"
            elif self.curr_screen == "create_game_4":
                try:
                    num_questions = int(user_input)
                    if 0 < num_questions <= sum([self.client.available_chapters[c] for c in self.client.chosen_chapters]):
                        self.client.num_questions = num_questions
                        self.curr_screen = "main_menu"
                        message = {
                            "message_type": "create_game",
                            "player_name": self.client.player_name,
                            "game_id": self.client.game_id,
                            "chapters": self.client.chosen_chapters,
                            "num_questions": self.client.num_questions,
                            "is_private": False
                        }
                        send_message(self.logger, message, self.client.sock)
                except Exception:
                    pass

            elif self.curr_screen == "join_game_1":
                if user_input not in self.client.curr_players:
                    self.client.player_name = user_input
                    self.curr_screen = "join_game_2"
            elif self.curr_screen == "join_game_2":
                if user_input in self.client.curr_games:
                    self.client.game_id = user_input
                    message = {
                        "message_type": "join_game",
                        "player_name": self.client.player_name,
                        "game_id": self.client.game_id
                    }
                    send_message(self.logger, message, self.client.sock)
                    self.client.game_id = user_input

            elif self.curr_screen == "quiz_question":
                if user_input.upper() in [chr(x) for x in range(65, 65 + len(self.client.curr_question['possible_answers']))]:
                    message = {
                        "message_type": "quiz_answer",
                        "player_name": self.client.player_name,
                        "game_id": self.client.game_id,
                        "answer": ord(user_input.upper()) - 65
                    }
                    send_message(self.logger, message, self.client.sock)
                    self.curr_screen = "quiz_question_waiting"

            elif self.curr_screen == "results":
                self.curr_screen = "results"

            self.input_box.set_edit_text("")

    def print_quiz_results(self):
        name = self.client.player_name
        results = self.client.results

        if not results:
            return "no results to show."

        # find the first and last question indices where the player participated
        start_idx = -1
        end_idx = -1

        for i, question_results in enumerate(results):
            if isinstance(question_results, dict) and name in question_results:
                if start_idx == -1:
                    start_idx = i
                end_idx = i

        if start_idx == -1:
            return "looks like you didn't answer any questions.\nno results to show."

        # get all players who participated in all questions in this range
        players = set(results[start_idx].keys())
        for i in range(start_idx + 1, end_idx + 1):
            players = players.intersection(set(results[i].keys()))

        if len(players) == 0:
            return "no consistent players found throughout your session."

        # calculate scores for each consistent player
        scores = {}
        num_questions = end_idx - start_idx + 1
        for player in players:
            correct_answers = sum(1 for i in range(start_idx, end_idx + 1)  if results[i][player])
            scores[player] = (correct_answers, num_questions)

        # sort players by score (descending)
        sorted_players = sorted(scores.items(),  key=lambda x: (x[1][0]/x[1][1], x[0]),  reverse=True)

        # create and populate the table
        results_table = PrettyTable()
        results_table.field_names = ["rank", "player", "score", "percentage"]

        for rank, (player, (correct, total)) in enumerate(sorted_players, 1):
            percentage = (correct / total) * 100
            results_table.add_row([
                rank,
                player,
                f"{correct}/{total}",
                f"{percentage:.1f}%"
            ])

        return str(results_table)
