
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
        self.txt_status = urwid.Text("Connecting...")
        self.txt_games = urwid.Text("")
        self.txt_players = urwid.Text("")
        self.input_box = urwid.Edit("> ")

        # Create main UI layout
        self.frame = urwid.Frame(
            urwid.Filler(urwid.Pile([
                self.txt_status,
                urwid.Divider(),
                self.txt_games,
                self.txt_players,
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

        # Update display based on current screen
        if self.curr_screen == "connecting":
            self.txt_status.set_text("Connecting...")
            if self.client.is_connected:
                self.curr_screen = "main_menu"

        elif self.curr_screen == "main_menu":
            menu_text = "=== Main Menu ===\n1. Create Game"
            if self.client.curr_games:
                menu_text += "\n2. Join Game"
            menu_text += "\n3. Exit"

            self.txt_status.set_text(menu_text)
            self.txt_games.set_text(f"Current Games: {self.client.curr_games}")
            self.txt_players.set_text(f"Players Online: {self.client.curr_players}")
            self.input_box.set_caption("Choose option: ")

        elif self.curr_screen == "create_game":
            self.txt_status.set_text("=== Create Game ===")
            self.txt_games.set_text(f"Available chapters: {list(self.client.available_chapters.keys())}")
            self.input_box.set_caption("Enter chapter number (or 'back'): ")

        if self.running:
            self.loop.set_alarm_in(0.1, self.update_display)

    def handle_input(self, key):
        if key in ('q', 'Q'):
            self.running = False
            raise urwid.ExitMainLoop()

        if key == 'enter':
            user_input = self.input_box.get_edit_text()
            self.input_box.set_edit_text("")

            if self.curr_screen == "main_menu":
                if user_input == "1":
                    self.curr_screen = "create_game"
                elif user_input == "2" and self.client.curr_games:
                    self.curr_screen = "join_game"
                elif user_input == "3":
                    self.running = False
                    raise urwid.ExitMainLoop()

            elif self.curr_screen == "create_game":
                if user_input == "back":
                    self.curr_screen = "main_menu"
                elif user_input in self.client.available_chapters:
                    message = {
                        "message_type": "create_game",
                        "player_name": "player1",
                        "game_name": "game1",
                        "is_private": False,
                        "chapters": [user_input],
                        "num_questions": 5
                    }
                    send_message(self.logger, message, self.client.sock)
                    self.curr_screen = "main_menu"
