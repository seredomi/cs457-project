
import urwid
import asyncio
from queue import Queue
from src.utils.messages import send_message

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
        if hasattr(self.loop, 'event_loop') and hasattr(self.loop.event_loop, '_loop'):
            try:
                self.loop.event_loop._loop.stop()
            except Exception:
                pass
        if hasattr(self.loop, 'idle_handle'):
            self.loop.remove_watch_file(self.loop.idle_handle)
        try:
            self.loop.stop()
        except Exception:
            pass

    def update_display(self, loop, user_data):
        # Process message queue
        while not self.message_queue.empty():
            msg = self.message_queue.get()
            if msg["message_type"] == "new_connection_prompt":
                self.curr_screen = "main_menu"
            elif msg["message_type"] == "game_update":
                if msg["subtype"] == "game_end":
                    if msg["game_id"] == self.client.game_id or self.client.game_id == "":
                        self.client.game_id = ""
                        self.curr_screen = "main_menu"
            elif msg["message_type"] == "quiz_question":
                self.curr_screen = "quiz_question"
            elif msg["message_type"] == "results":
                pass

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
            self.txt_instructions.set_text(f"choose chapters from this list: {' '.join(self.client.available_chapters.keys())}\nenter as space separated numbers: ")
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

        if self.running:
            self.loop.set_alarm_in(0.1, self.update_display)

    def handle_input(self, key):
        if key in ('q', 'Q'):
            self.running = False
            raise urwid.ExitMainLoop()

        if key == 'enter':
            user_input = self.input_box.get_edit_text()

            if self.curr_screen == "main_menu":
                if user_input == "1":
                    self.curr_screen = "create_game_1"
                elif user_input == "2" and self.client.curr_games:
                    self.curr_screen = "join_game_1"
                elif user_input == "3":
                    self.running = False
                    raise urwid.ExitMainLoop()

            elif self.curr_screen == "create_game_1":
                if user_input not in self.client.curr_players:
                    self.client.player_name = user_input
                    self.curr_screen = "create_game_2"
            elif self.curr_screen == "create_game_2":
                if user_input not in self.client.curr_games:
                    self.client.game_name = user_input
                    self.curr_screen = "create_game_3"
            elif self.curr_screen == "create_game_3":
                chapters = user_input.split()
                if all([c in self.client.available_chapters.keys() for c in chapters]):
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
                            "game_name": self.client.game_name,
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
                    self.client.game_name = user_input
                    message = {
                        "message_type": "join_game",
                        "player_name": self.client.player_name,
                        "game_name": self.client.game_name
                    }
                    send_message(self.logger, message, self.client.sock)

            elif self.curr_screen == "quiz_question":
                if user_input.lower() in [chr(x) for x in range(65, 65 + len(self.client.curr_question['possible_answers']))]:
                    message = {
                        "message_type": "quiz_answer",
                        "player_name": self.client.player_name,
                        "game_id": self.client.game_id,
                        "answer": ord(user_input.upper()) - 65
                    }
                    send_message(self.logger, message, self.client.sock)
                    self.client.response_progress[self.client.player_name] = user_input
                    self.curr_screen = "quiz_question_waiting"


            self.input_box.set_edit_text("")
