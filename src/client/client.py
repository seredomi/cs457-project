import sys
import socket
import threading
import logging
import time
import ipaddress
import json
import re
from typing import List
from src.messages import send_message, receive_message, MOCKS
from src.client.dialogs import new_connection_dialog, create_game_dialog, join_game_dialog, quiz_question_dialog

# configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')

class Client:
    def __init__(self, host='localhost', port=5000):
        self.host: str = host
        self.port: int = port
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running: bool = False
        self.receive_thread = None
        self.curr_games = []
        self.max_questions = -1
        self.available_chapters = []

    # connect to server
    def connect(self):
        try:
            logging.info(f"Attempting to connect to {self.host}:{self.port}")
            self.sock.connect((self.host, self.port))
            logging.info(f"Connected to server at {self.host}:{self.port}")
            self.running = True
            # new thread for receiving messages
            # self.receive_thread = threading.Thread(target=self.receive_messages)
            # self.receive_thread.start()
            self.receive_messages()
            # loop for sending messages
            # self.send_messages()
        except ConnectionRefusedError: logging.error("Connection failed. Server might be offline.")
        except Exception as e: logging.error(f"An error occurred: {e}")
        return

    # loop for receiving messages
    def receive_messages(self):
        while self.running:
            try:
                self.sock.settimeout(1.0)
                # blocking call awaits message from server
                message = self.sock.recv(1024).decode('utf-8')
                if not message:
                    logging.info("Server connection closed.")
                    self.running = False
                    break
                receive_message(message, self.sock)
                msg_obj = json.loads(message)
                logging.info(f"Received message: {message}")

                msg_type = msg_obj.get("message_type")

                # server has shut down
                if msg_type == "server_shutdown":
                    logging.info("Server is shutting down. Press enter to exit")
                    self.running = False
                    break
                if msg_type == "new_connection_prompt":
                    self.curr_players = msg_obj.get("current_players")
                    self.curr_games = msg_obj.get("current_games")
                    self.max_questions = msg_obj.get("max_questions")
                    self.available_chapters = msg_obj.get("chapters_available")

                    decision = -1
                    decision = new_connection_dialog(len(self.curr_games) > 0)
                    if decision == 1:
                        create_game = create_game_dialog(
                            self.available_chapters,
                            self.max_questions,
                            self.curr_games,
                            self.curr_players
                        )
                        send_message(create_game, self.sock)
                    elif decision == 2:
                        join_game = join_game_dialog(self.curr_games)
                        send_message(join_game, self.sock)
                    elif decision == 3:
                        self.disconnect()
                
                elif msg_type == "quiz_question":
                    # use quiz_question_dialog to get the user answer
                    user_answer = quiz_question_dialog(msg_obj)
                    answer_message = {
                        "message_type": "quiz_answer",
                        "question": msg_obj.get("question"),
                        "answer": user_answer
                    }
                    send_message(answer_message, self.sock)

            except socket.timeout: continue
            except Exception as e:
                if self.running:
                    logging.error(f"Error receiving message: {e}")
                    self.running = False
                break
        return

    def disconnect(self):
        logging.info("Disconnecting from server...")
        self.running = False
        self.sock.close()

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
