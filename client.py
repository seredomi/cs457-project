import socket
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Client:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
            logging.info(f"Connected to server at {self.host}:{self.port}")
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.start()
            self.send_messages()
        except ConnectionRefusedError:
            logging.error("Connection failed. Server might be offline.")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                logging.info(f"Received: {message}")
            except Exception as e:
                logging.error(f"Error receiving message: {e}")
                break

    def send_messages(self):
        while True:
            try:
                message = input()
                self.client_socket.send(message.encode('utf-8'))
                if message.lower() == 'quit':
                    break
            except Exception as e:
                logging.error(f"Error sending message: {e}")
                break

    def disconnect(self):
        logging.info("Disconnecting from server...")
        self.client_socket.close()

if __name__ == "__main__":
    client = Client()
    try:
        client.connect()
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect()