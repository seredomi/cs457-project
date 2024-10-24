import sys
import socket
import threading
import signal
import logging
from typing import List
import ipaddress
from src.messages import receive_message, MOCKS

# configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')

class Server:
    def __init__(self, host='127.0.0.1', port_num=5000):
        self.host: str = host
        self.port_num: int = port_num
        self.server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients: List[socket.socket] = []
        self.running = False

    def start(self):
        # attempt to connect
        self.running = True
        try:
            logging.info(f"Attempting to connect to {self.host}:{self.port_num}")
            self.server_socket.bind((self.host, self.port_num))
            self.server_socket.listen(5)
            logging.info(f"Server started on {self.host}:{self.port_num}")

            # call shutdown if keyboard interruption
            signal.signal(signal.SIGINT, self.shutdown)

            # accept connections continually until not running
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    # blocking call awaits new connections
                    client_socket, addr = self.server_socket.accept()
                    # new thread for each new connection
                    client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                    client_thread.start()
                except socket.timeout: continue
                except Exception as e:
                    if self.running:
                        logging.error(f"Error accepting connection: {e}")

        # exceptions handled from connection errors
        except Exception as e: logging.error(f"Server error: {e}")
        finally: self.cleanup()

    # gets called for each incoming connection
    def handle_client(self, client_socket, addr):
        try:
            logging.info(f"New connection from {addr}")
            self.clients.append(client_socket)

            while self.running:
                try:
                    client_socket.settimeout(1.0)
                    # blocking call awaits message from client
                    message = client_socket.recv(1024).decode('utf-8')
                    if not message: break
                    receive_message(message, client_socket)
                except socket.timeout: continue
                except Exception as e: logging.error(f"Error handling client {addr}: {e}")
        # protocol for removing client
        finally:
            self.clients.remove(client_socket)
            client_socket.close()
            logging.info(f"Connection from {addr} closed")

    # send a message to all clients
    def broadcast(self, message):
        for client in self.clients:
            try:
                client.send(message.encode('utf-8'))
            except Exception as e:
                logging.error(f"Error broadcasting to a client: {e}")

    # handle self shutdown
    def shutdown(self, signum, frame):
        logging.info("Shutting down server...")
        self.running = False
        # notifies clients upon shutdown, which they use to shutdown themselves
        self.broadcast("SERVER_SHUTDOWN")

    def cleanup(self):
        logging.info("Cleaning up server resources...")
        for client in self.clients:
            try: client.close()
            except: pass
            self.server_socket.close()

if __name__ == "__main__":
    server = None
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
            logging.error(f"Bad arguments: {' '.join(sys.argv)} resulted in error: {e}\nUsage: server.py [IP address] [port number")
            sys.exit(1)
        # instantiate server based on args
        server = Server(ip, port)

    # no args -- use defaults
    elif len(sys.argv) == 1:
        logging.info("No arguments passed. Using default IP address and port number")
        server = Server()

    # wrong number of args
    else:
        logging.error(f"Bad arguments: {' '.join(sys.argv)}.\nUsage: server.py [IP address] [port number]")
        exit(1)

    # start the server!
    server.start()
