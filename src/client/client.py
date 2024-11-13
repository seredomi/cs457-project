import sys
import socket
import ipaddress
import json
import threading


from src.client.dialogs import (
    new_connection_dialog,
    create_game_dialog,
    join_game_dialog,
    quiz_question_dialog,
)
from src.utils.messages import send_message, receive_message
from src.utils.logger import setup_logger
from src.client.ui_thread import UIHandler

# configure logging
logger = setup_logger("client.log")


class Client:
    def __init__(self, logger, host="localhost", port=5000):
        self.host: str = host
        self.port: int = port
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running: bool = False
        self.receive_thread = None
        self.is_connected = False

        self.curr_games = []
        self.curr_players = []
        self.available_chapters = {}
        self.chosen_chapters = []
        self.game_id = ""
        self.player_name = ""
        self.curr_question = {}
        self.response_progress = ""

        self.logger = logger
        self.current_window = "main_menu"
        self.ui_handler = UIHandler(self, logger)

    # connect to server
    def connect(self):
        try:
            self.logger.info(f"Attempting to connect to {self.host}:{self.port}")
            self.sock.connect((self.host, self.port))
            self.logger.info(f"Connected to server at {self.host}:{self.port}")
            self.is_connected = True
            self.running = True

            # new thread for receiving messages
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.start()

            self.ui_handler.start()

        except ConnectionRefusedError:
            self.logger.error("Connection failed. Server might be offline.")
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
        return

    # loop for receiving messages
    def receive_messages(self):
        while self.running:
            try:
                self.sock.settimeout(1.0)
                # blocking call awaits message from server
                message = self.sock.recv(1024).decode("utf-8")
                if not message:
                    self.logger.info("Server connection closed.")
                    self.running = False
                    break
                receive_message(self.logger, message, self.sock)
                msg_obj = json.loads(message)
                msg_type = msg_obj.get("message_type")

                self.ui_handler.message_queue.put(msg_obj)

                # server has shut down
                if msg_type == "server_shutdown":
                    self.logger.info("Server is shutting down. Press enter to exit")
                    self.running = False
                    break

                if msg_type == "error":
                    self.logger.error(f"Server error: {msg_obj.get('message', '')}")
                    self.running = False
                    break

                if msg_type == "game_update":
                    msg_subtype = msg_obj.get("subtype")
                    if msg_subtype == "game_created":
                        self.curr_games.append(msg_obj.get("game_id"))
                        self.logger.debug(f"New game: {msg_obj.get('game_id')}")
                        self.logger.debug(f"Current games: {self.curr_games}")
                    elif msg_subtype == "game_end":
                        self.curr_games.remove(msg_obj.get("game_id"))
                        self.logger.debug(f"Game ended: {msg_obj.get('game_id')}")
                        self.logger.debug(f"Current games: {self.curr_games}")
                    elif msg_subtype == "player_join":
                        self.logger.debug(
                            f"Player {msg_obj.get('player_id')} joined game {msg_obj.get('game_id')}"
                        )
                        self.curr_players.append(msg_obj.get("player_id"))
                    elif msg_subtype == "player_leave":
                        self.logger.debug(
                            f"Player {msg_obj.get('player_id')} left game {msg_obj.get('game_id')}"
                        )
                        self.curr_players.remove(msg_obj.get("player_id"))

                if msg_type == "new_connection_prompt":
                    self.curr_players = msg_obj.get("current_players")
                    self.curr_games = msg_obj.get("current_games")
                    self.max_questions = msg_obj.get("max_questions")
                    self.available_chapters = msg_obj.get("chapters_available")

                #     decision = -1
                #     decision = new_connection_dialog(len(self.curr_games) > 0)
                #     if decision == 1:
                #         create_game = create_game_dialog(
                #             available_chapters=self.available_chapters,
                #             curr_games=self.curr_games,
                #             curr_players=self.curr_players,
                #         )
                #         send_message(self.logger, create_game, self.sock)
                #     elif decision == 2:
                #         join_game = join_game_dialog(self.curr_games)
                #         send_message(self.logger, join_game, self.sock)
                #     elif decision == 3:
                #         self.running = False
                #         break

                # elif msg_type == "quiz_question":
                #     # use quiz_question_dialog to get the user answer
                #     user_answer = quiz_question_dialog(msg_obj)
                #     answer_message = {
                #         "message_type": "quiz_answer",
                #         "question": msg_obj.get("question"),
                #         "answer": user_answer,
                #     }
                #     send_message(self.logger, answer_message, self.sock)

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error receiving message: {e}")
                    self.running = False
                break
        return

    def disconnect(self):
        self.logger.info("Disconnecting from server...")
        self.running = False
        self.ui_handler.stop()
        self.sock.close()


if __name__ == "__main__":
    client = None

    # correct number of args if specifying IP and port
    if len(sys.argv) == 3:
        ip = None
        port = None
        # check that arguments are valid
        try:
            # checks that IP is valid by instantiating ipaddress based on it
            ipaddress.ip_address(sys.argv[1])
            ip = sys.argv[1]
            port = int(sys.argv[2])
        except Exception as e:
            logger.error(
                f"Bad arguments: {' '.join(sys.argv)} resulted in error: {e}\nUsage: client.py [IP address] [port number"
            )
            sys.exit(1)
        # instantiate server based on args
        client = Client(logger, ip, port)

    # no args -- use defaults
    elif len(sys.argv) == 1:
        logger.info("No arguments passed. Using default IP address and port number")
        client = Client(logger)

    # wrong number of args
    else:
        logger.error(
            f"Bad arguments: {' '.join(sys.argv)}.\nUsage: server.py [IP address] [port number]"
        )
        exit(1)

    # connect to server, disconnect on exception
    try:
        client.connect()
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect()
