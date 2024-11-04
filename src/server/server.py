import sys
import socket
import threading
import signal
import logging
import json
import uuid
from typing import List
import ipaddress
from src.messages import send_message, receive_message, MOCKS
from src.server.player_class import Player

# configure logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] - %(message)s")


class Server:
    def __init__(self, host="127.0.0.1", port_num=5000):
        self.host: str = host
        self.port_num: int = port_num
        self.server_socket: socket.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients: List[socket.socket] = []
        self.players: List[Player] = []
        self.running = False
        self.curr_games: List[Any] = []
        self.client_mapping = {}

    def print_players(self):
        print("\nPlayers:")
        for i, player in enumerate(self.players):
            print(f"{i + 1}. {str(player)}")
        print()

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
                    client_thread = threading.Thread(
                        target=self.handle_client, args=(client_socket, addr)
                    )
                    client_thread.start()
                    self.players.append(Player(client_socket, self))
                    self.print_players()

                except socket.timeout: continue
                except Exception as e:
                    if self.running:
                        logging.error(f"Error accepting connection: {e}")

        # exceptions handled from connection errors
        except Exception as e:
            logging.error(f"Server error: {e}")
        finally:
            self.cleanup()

    # gets called for each incoming connection
    def handle_client(self, client_socket, addr):
        try:
            player_id = str(addr)
            logging.info(f"New connection from {addr}")
            self.clients.append(client_socket)

            send_message(MOCKS["new_connection_prompt"], client_socket)
            while self.running:
                try:
                    client_socket.settimeout(1.0)
                    # blocking call awaits message from client
                    message = client_socket.recv(1024).decode('utf-8')
                    if not message: break
                    receive_message(message, client_socket)
                    msg_obj = json.loads(message)
                    msg_type = msg_obj["message_type"]
                    if msg_type == "create_game":
                        player_name = msg_obj["player_name"]
                        game_name = msg_obj["game_name"]
                        pi = self.players.index(client_socket)
                        self.players[pi].curr_game = game_name
                        self.players[pi].name = player_name

                        # TODO: actually instantiate the game, add to games, and start it
                        logging.info(f"Player {player_name} wants to start a game named {game_name}")
                        self.print_players()

                    if msg_type == "start_game":
                        self.handle_start_game(message, client_socket, addr)
                    elif msg_type == "join_game":
                        self.handle_join_game(message, client_socket, addr)
                    else:
                        logging.error(f"unknown message type from {addr}")
                        error_message = {"error": "unknown message type."}
                        send_message(error_message, client_socket)

                except socket.timeout:
                    continue
                except Exception as e:
                    logging.error(f"error handling client {addr}: {e}")
                    break
        finally:
            self.clients.remove(client_socket)
            client_socket.close()
            logging.info(f"connection from {addr} closed")

    def get_client_socket_by_id(self, player_id):
        return self.client_mapping.get(player_id)

    # start game
    def handle_start_game(self, message, client_socket, addr):
        try:
            message_obj = json.loads(message)
            game_id = message_obj.get("game_id")
            selected_chapters = message_obj.get("chapters", [])
            owner_id = str(addr)

            # check if game exists
            if any(game.game_id == game_id for game in self.curr_games):
                error_message = {"error": "game ID already exists. try again"}
                send_message(error_message, client_socket, self.logger)
                return

            # new game
            new_game = Game(
                game_id=game_id,
                selected_chapters=selected_chapters,
                owner_id=owner_id,
                all_game_ids=[game.game_id for game in self.curr_games],
            )
            self.curr_games.append(new_game)  # add new game to curr_games

            # confirmation
            response = {"status": "game_created", "game_id": game_id}
            send_message(response, client_socket, self.logger)
            self.logger.info(f"Game {game_id} created successfully by {owner_id}")

            self.broadcast_game_state(new_game)  # broadcast

        except json.JSONDecodeError:
            error_message = {"error": "invalid msg format. couldn't parse."}
            send_message(error_message, client_socket, self.logger)

    # join game
    def handle_join_game(self, message, client_socket, addr):
        try:
            message_obj = json.loads(message)
            game_id = message_obj.get("game_id")

            # find game by game_id in curr_games
            game = next((g for g in self.curr_games if g.game_id == game_id), None)
            if not game:
                error_message = {"error": "game ID not found."}
                send_message(error_message, client_socket, self.logger)
                return

            player_id = str(addr)
            game.add_player(player_id)

            response = {"status": "joined_game", "game_id": game_id}
            send_message(response, client_socket, self.logger)
            self.logger.info(f"Player {addr} joined game {game_id}")

            self.broadcast_game_state(game)

        except json.JSONDecodeError:
            error_message = {"error": "invalid msg format. couldn't parse."}
            send_message(error_message, client_socket, self.logger)

    # delete game
    def delete_game(self, game_id):
        try:
            # find game by game_id in curr_games
            game = next((g for g in self.curr_games if g.game_id == game_id), None)
            if not game:
                logging.error(f"game {game_id} not found for deletion.")
                return

            # remove game from curr_games
            self.curr_games.remove(game)
            logging.info(f"game {game_id} deleted successfully.")
            # notify all connected players in game about deletion
            game_state = {"message_type": "game_deleted", "game_id": game_id}
            for player_id in game.connected_players:
                try:
                    client_socket = self.get_client_socket_by_id(player_id)
                    if client_socket:
                        client_socket.send(json.dumps(game_state).encode("utf-8"))
                except Exception as e:
                    logging.error(
                        f"error notifying player {player_id} of game deletion: {e}"
                    )
        except Exception as e:
            logging.error(f"error deleting game {game_id}: {e}")

    # gamestate sync/broadcast game state when it changes
    def broadcast_game_state(self, game):
        game_state = {
            "message_type": "game_state_update",
            "game_id": game.game_id,
            "current_question": game.current_question,
            "players": game.connected_players,  # send player IDs as list
            "responses": game.current_responses,
        }
        for player_id in game.connected_players:
            try:
                client_socket = self.get_client_socket_by_id(player_id)
                if client_socket:
                    client_socket.send(json.dumps(game_state).encode("utf-8"))
            except Exception as e:
                logging.error(f"error sending game state to {player_id}: {e}")

    # handle self shutdown
    def shutdown(self, signum, frame):
        logging.info("Shutting down server...")
        self.running = False
        # notifies clients upon shutdown, which they use to shutdown themselves
        self.broadcast({"message_type": "server_shutdown"})

    def cleanup(self):
        logging.info("Cleaning up server resources...")
        for client in self.clients:
            try:
                client.close()
            except:
                pass
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
            logging.error(
                f"Bad arguments: {' '.join(sys.argv)} resulted in error: {e}\nUsage: server.py [IP address] [port number]"
            )
            sys.exit(1)
        # instantiate server based on args
        server = Server(ip, port)

    # no args -- use defaults
    elif len(sys.argv) == 1:
        logging.info("No arguments passed. Using default IP address and port number")
        server = Server()

    # wrong number of args
    else:
        logging.error(
            f"Bad arguments: {' '.join(sys.argv)}.\nUsage: server.py [IP address] [port number]"
        )
        exit(1)

    # start the server!
    server.start()
