import sys
import socket
import threading
import logging
import time
import ipaddress
import re
from typing import List
from src.messages import send_message, receive_message, MOCKS

# configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')

def join_game_dialog(curr_games: List[str] = [], curr_players: List[str] = []):
    print("Enter your player name. No spaces or special characters allowed:")
    player_name = input()
    while not re.match("^[a-zA-Z0-9_]*$", player_name) or player_name in curr_players or len(player_name) < 1:
        print("Invalid player name or name already taken. Please try again.")
        player_name = input()

    print("Enter the game name to join. It should match an existing game name:")
    game_name = input()
    while not re.match("^[a-zA-Z0-9_]*$", game_name) or game_name not in curr_games or len(game_name) < 1:
        print("Game not found or invalid name. Please try again.")
        game_name = input()

    print("Is this a private game? Enter 'yes' or 'no':")
    is_private = input().strip().lower() == 'yes'
    password = ""
    if is_private:
        print("Enter the game password:")
        password = input()

    return {
        "message_type": "join_game",
        "player_name": player_name,
        "game_name": game_name,
        "password": password,
    }

class Client:
    def __init__(self, host='localhost', port=50000):
        self.host: str = host
        self.port: int = port
        self.client_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running: bool = False
        self.receive_thread = None

    # connect to server
    def connect(self):
        try:
            logging.info(f"Attempting to connect to {self.host}:{self.port}")
            self.client_socket.connect((self.host, self.port))
            logging.info(f"Connected to server at {self.host}:{self.port}")
            self.running = True
            # new thread for receiving messages
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.start()
            # loop for sending messages
            self.send_messages()
        except ConnectionRefusedError: logging.error("Connection failed. Server might be offline.")
        except Exception as e: logging.error(f"An error occurred: {e}")
        return

    # loop for receiving messages
    def receive_messages(self):
        while self.running:
            try:
                self.client_socket.settimeout(1.0)
                # blocking call awaits message from server
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    logging.info("Server connection closed.")
                    self.running = False
                    break
                # server has shut down
                if message == "SERVER_SHUTDOWN":
                    logging.info("Server is shutting down. Press enter to exit")
                    self.running = False
                    break
                logging.info(f"Received message: {message}")
            except socket.timeout: continue
            except Exception as e:
                if self.running:
                    logging.error(f"Error receiving message: {e}")
                    self.running = False
                break
        return

    # loop runs to take user input and send to server
    def send_messages(self):
        temp_shortcut_map = {
            'ncp': "new_connection_prompt",
            'sg': "start_game",
            'stg': "stop_game",
            'jg': "join_game",
            'qq': "quiz_question",
            'qa': "quiz_answer",
            'r': "results"
        }

        while self.running:
            try:
                time.sleep(0.1)
                message = input("\nEnter message type\n" + "\n".join([f" - '{k}' to send {v}" for k, v in temp_shortcut_map.items()]) + "\n' - q' to exit\n")
                message = message.lower()
                if message == 'q':
                    break
                elif message == 'jg':
                # Call join_game_dialog to get input details for joining a game
                    join_game_data = join_game_dialog(curr_games=["game1", "game2"], curr_players=["player1", "player2"])
                    send_message(join_game_data, self.client_socket)
                elif message in temp_shortcut_map:
                    send_message(MOCKS[temp_shortcut_map[message]], self.client_socket)
                else:
                    logging.error("Invalid input. Please try again.")
                    continue
            except Exception as e:
                if self.running: logging.error(f"Error sending message: {e}")
                self.running = False
                break
        return

    def disconnect(self):
        logging.info("Disconnecting from server...")
        self.running = False
        self.client_socket.close()

if __name__ == "__main__":
    client= None

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
            logging.error(f"Bad arguments: {' '.join(sys.argv)} resulted in error: {e}\nUsage: client.py [IP address] [port number")
            sys.exit(1)
        # instantiate server based on args
        client = Client(ip, port)

    # no args -- use defaults
    elif len(sys.argv) == 1:
        logging.info("No arguments passed. Using default IP address and port number")
        client = Client()

    # wrong number of args
    else:
        logging.error(f"Bad arguments: {' '.join(sys.argv)}.\nUsage: server.py [IP address] [port number]")
        exit(1)

    # connect to server, disconnect on exception
    try: client.connect()
    except KeyboardInterrupt: pass
    finally: client.disconnect()
