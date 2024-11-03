import sys
import socket
import threading
import logging
import time
import ipaddress
from src.messages import send_message, receive_message, MOCKS

# configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')

class Client:
    def __init__(self, host='localhost', port=5000):
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
            'jg': "join_game",
            'qq': "quiz_question",
            'qa': "quiz_answer",
            'r': "results"
        }

        while self.running:
            try:
                # time sleep is a temp fix for race condition of server response coming in after prompt, which looks confusing for user
                # in the future, info logs will only be printed via a -v flag, so this shouldn't be an issue
                time.sleep(0.1)
                message = input("\nEnter message type\n" + "\n".join([f" - '{k}' to send {v}" for k, v in temp_shortcut_map.items()]) + "\n - 'q' to exit\n")
                message = message.lower()
                if message == 'q':
                    break
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
