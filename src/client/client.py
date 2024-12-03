import sys
import socket
import ipaddress
import json
import threading
import urwid

from src.utils.messages import send_message, receive_message
from src.utils.logger import setup_logger
from src.client.ui import UIHandler

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
        self.results = []

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
        buffer = ""  # Initialize buffer
        while self.running:
            try:
                self.sock.settimeout(1.0)
                # Blocking call awaits message from server
                data = self.sock.recv(2048).decode("utf-8")
                if not data:
                    self.logger.error("\nServer connection closed. Press Ctrl+C to exit")
                    self.disconnect()
                    break
                buffer += data  # Append incoming data to buffer

                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)  # Split at first newline
                    if not message.strip():
                        continue  # Skip empty messages
                    receive_message(self.logger, message, self.sock)
                    msg_obj = json.loads(message)
                    msg_type = msg_obj.get("message_type")

                    # Process the message based on its type
                    if msg_type == "server_shutdown":
                        self.logger.info("\nServer is shutting down. Press Ctrl+C to exit")
                        self.disconnect()
                        break

                    elif msg_type == "error":
                        self.logger.error(f"\nServer error: {msg_obj.get('message', '')}")
                        self.disconnect()
                        break

                    elif msg_type == "game_update":
                        # Handle game updates
                        self.handle_game_update(msg_obj)

                    elif msg_type == "new_connection_prompt":
                        # Update available chapters and other info
                        self.curr_players = msg_obj.get("current_players", [])
                        self.curr_games = msg_obj.get("current_games", [])
                        self.available_chapters = msg_obj.get("chapters_available", {})
                        self.logger.debug(f"Available chapters: {self.available_chapters}")

                    elif msg_type == "quiz_question":
                        self.curr_question = msg_obj

                    elif msg_type == "results":
                        self.results = msg_obj.get("results", [])

                    # Pass the message to the UI handler
                    self.ui_handler.message_queue.put(msg_obj)

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error receiving message: {e}")
                    self.running = False
                break
        return

    def handle_game_update(self, msg_obj):
        subtype = msg_obj.get("subtype")
        if subtype == "game_created":
            game_id = msg_obj.get("game_id")
            self.curr_games.append(game_id)
            self.logger.debug(f"Game created: {game_id}")
            # Proceed to the next window, e.g., start the quiz or update the UI
            self.ui_handler.message_queue.put(msg_obj)
        elif subtype == "game_end":
            game_id = msg_obj.get("game_id")
            if game_id in self.curr_games:
                self.curr_games.remove(game_id)
            self.logger.debug(f"Game ended: {game_id}")
            self.ui_handler.message_queue.put(msg_obj)
        elif subtype == "player_connect":
            player_name = msg_obj.get("player_name")
            self.curr_players.append(player_name)
            self.logger.debug(f"Player connected: {player_name}")
            self.ui_handler.message_queue.put(msg_obj)
        elif subtype == "player_disconnect":
            player_name = msg_obj.get("player_name")
            if player_name in self.curr_players:
                self.curr_players.remove(player_name)
            self.logger.debug(f"Player disconnected: {player_name}")
            self.ui_handler.message_queue.put(msg_obj)
        elif subtype == "response_update":
            self.response_progress = msg_obj.get("message")
            self.logger.debug(f"Response progress updated: {self.response_progress}")
            self.ui_handler.message_queue.put(msg_obj)
        else:
            self.logger.error(f"Unknown game_update subtype: {subtype}")



    def disconnect(self):
        self.logger.info("Disconnecting from server...")
        disconnect_message = {
            "message_type": "game_update",
            "subtype": "player_disconnect",
            "player_name": self.player_name,
        }
        send_message(self.logger, disconnect_message, self.sock)
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
                f"Bad arguments: {' '.join(sys.argv)} resulted in error: {e}\nUsage: client.py [IP address] [port number]"
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
        try:
            client.disconnect()
        except urwid.ExitMainLoop:
            pass
