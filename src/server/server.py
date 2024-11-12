import sys
import socket
import threading
import signal
import logging
import json
from typing_extensions import NewType
import uuid
from typing import List
import ipaddress
from prettytable import PrettyTable

from src.utils.messages import send_message, receive_message, MOCKS
from src.server.player_class import Player
from src.server.game_class import Game
from src.server.quiz_data.data_loader import QuizDataLoader
from src.utils.display import print_header

# configure logging
from src.utils.logger import setup_logger
logger = setup_logger("server.log")

class Server:
    def __init__(self, logger, host="127.0.0.1", port_num=5000):
        self.host: str = host
        self.port_num: int = port_num
        self.server_socket: socket.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.players: List[Player] = []
        self.running = False
        self.curr_games: List[Game] = []
        self.logger = logger

    def print_info(self):
        player_table = PrettyTable()
        player_table.field_names = ["name", "curr_game", "ip", "port"]
        for player in self.players:
            player_table.add_row([player.name, player.curr_game, player.sock.getpeername()[0], player.sock.getpeername()[1]])
        print_header("current server info")
        print("Players:")
        print(player_table)

        game_table = PrettyTable()
        game_table.field_names = ["id", "owner", "curr q", "all qs"]
        for game in self.curr_games:
            game_table.add_row([
                game.game_id,
                game.owner_name,
                f"{sum([1 if not val is None else 0 for val in game.player_responses.values()])}/{len(game.player_responses)}",
                f"{game.current_question_index + 1}/{len(game.questions)}"
            ])
        print("\nGames:")
        print(game_table)
        print()


    def start(self):
        # attempt to connect
        self.running = True
        try:
            self.logger.info(f"Attempting to connect to {self.host}:{self.port_num}")
            self.server_socket.bind((self.host, self.port_num))
            self.server_socket.listen(5)
            self.logger.info(f"Server started on {self.host}:{self.port_num}\nListening for connections...")

            # call shutdown if keyboard interruption
            signal.signal(signal.SIGINT, self.shutdown)

            # accept connections continually until not running
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    # blocking call awaits new connections
                    client_socket, addr = self.server_socket.accept()
                    # new thread for each new connection
                    self.players.append(Player(client_socket))
                    client_thread = threading.Thread(
                        target=self.handle_client, args=(client_socket, addr)
                    )
                    client_thread.start()
                    self.print_info()

                except socket.timeout: continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Error accepting connection: {e}")

        # exceptions handled from connection errors
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            self.cleanup()

    # gets called for each incoming connection
    def handle_client(self, client_socket, addr):
        try:
            self.logger.debug(f"New connection from {addr}")

            new_connection_prompt = {
                "message_type": "new_connection_prompt",
                "current_games": [game.game_id for game in self.curr_games] if len(self.curr_games) > 0 else [],
                "current_players": [player.name if player.name is not None else "" for player in self.players] if len(self.players) > 0 else [],
                "chapters_available": [1, 2],
                "max_questions": 20
            }
            send_message(self.logger, new_connection_prompt, client_socket)

            while self.running:
                try:
                    client_socket.settimeout(1.0)
                    # blocking call awaits message from client
                    message = client_socket.recv(1024).decode('utf-8')
                    if not message: break
                    receive_message(self.logger, message, client_socket)
                    msg_obj = json.loads(message)
                    msg_type = msg_obj["message_type"]

                    if msg_type == "create_game":
                        player_name = msg_obj["player_name"]
                        game_name = msg_obj["game_name"]
                        pi = self.players.index(client_socket)
                        self.players[pi].curr_game = game_name
                        self.players[pi].name = player_name

                        self.logger.debug(f"player {player_name} wants to start a game named {game_name}")
                        self.print_info()
                        self.handle_create_game(msg_obj, self.players[pi].id)

                    elif msg_type == "join_game":
                        player_name = msg_obj["player_name"]
                        game_name = msg_obj["game_name"]
                        pi = self.players.index(client_socket)
                        self.players[pi].curr_game = game_name
                        self.players[pi].name = player_name
                        self.handle_join_game(msg_obj, self.players[pi].id)

                    else:
                        self.logger.error(f"unknown message type from {addr}")
                        raise Exception("unknown message type")

                except socket.timeout:
                    continue
                except Exception as e:
                    self.logger.error(f"error handling client {addr}: {e}")
                    error_message = {"message_type": "error", "message": str(e)}
                    send_message(self.logger, error_message, client_socket)
                    break
        finally:
            self.players.remove(client_socket)
            client_socket.close()
            self.logger.debug(f"connection from {addr} closed")
            self.print_info()

    # start game
    def handle_create_game(self, msg_obj, player_id):
        pi = self.players.index(player_id)
        game_id = msg_obj.get("game_name", "unknown_game_id")
        self.print_info()
        # gi = self.curr_games.index(game_id)
        selected_chapters = msg_obj.get("chapters", [])

        try:
            # check if game exists
            # if gi != -1: raise Exception(f"Game {game_id} already exists")
            self.print_info()

            # new game
            new_game = Game(
                game_id=game_id,
                selected_chapters=selected_chapters,
                all_game_ids=[game.game_id for game in self.curr_games],
                owner_id = player_id,
                owner_name = self.players[pi].name
            )
            self.curr_games.append(new_game)  # add new game to curr_games

            # confirmation
            response = {
                "message_type": "game_update",
                "subtype": "game_created",
                "game_id": game_id,
                "player_id": player_id,
                "message": f"game {game_id} created successfully by {self.players[pi].name}"
            }
            self.logger.debug(f"game {game_id} created successfully by {player_id}")
            self.broadcast(response)
            self.print_info()

        except Exception as e:
            error_message = {"message_type": "error", "message": f"error creating game: {e}"}
            send_message(self.logger, error_message, self.players[pi].sock)

    # join game
    def handle_join_game(self, msg_obj, player_id):
        pi = self.players.index(player_id)
        game_id = msg_obj.get("game_name")
        gi = self.curr_games.index(game_id)

        try:
            # find game by game_id in curr_games
            if gi == -1: raise Exception(f"game id {game_id} not found")

            self.curr_games[gi].add_player(player_id)

            response = {
                "message_type": "game_update",
                "subtype": "player_join",
                "game_id": game_id,
                "player_id": player_id,
                "message": f"player {self.players[pi].name} successfully joined game {game_id}"
            }
            send_message(self.logger, response, self.players[pi].sock)
            self.logger.info(f"player {player_id} joined game {game_id}")

            self.broadcast(response)
            self.print_info()

        except Exception as e:
            error_message = {"message_type": "error", "message": f"error joining game: {e}"}
            send_message(self.logger, error_message, self.players[pi].sock)

    # delete game
    def delete_game(self, game_id):
        try:
            # find game by game_id in curr_games
            gi = self.curr_games.index(game_id)
            if gi == -1: raise Exception(f"game id {game_id} not found")

            self.curr_games.pop(gi)
            response = {
                "message_type": "game_update",
                "subtype": "game_end",
                "game_id": game_id,
                "message": f"game {game_id} has ended"
            }
            self.logger.info(f"game {game_id} deleted successfully.")

            self.broadcast(response, game_i=gi)

        except Exception as e:
            self.logger.error(f"error deleting game {game_id}: {e}")


    # send a message to subset of clients
    def broadcast(self, message, game_i=None):
        list = self.players

        # if given a game index, broadcast to players in that game
        if game_i:
            list = [
                self.players[self.players.index(player_id)]
                for player_id in self.curr_games[game_i].connected_players
            ]

        for player in list:
            try:
                send_message(self.logger, message, player.sock)
            except Exception as e:
                self.logger.error(f"Error broadcasting message {message} to client: {e}")


    # handle self shutdown
    def shutdown(self, signum, frame):
        self.logger.info("Shutting down server...")
        self.running = False
        # notifies clients upon shutdown, which they use to shutdown themselves
        self.broadcast({"message_type": "server_shutdown"})

    def cleanup(self):
        self.logger.info("Cleaning up server resources...")
        for player in self.players:
            try:
                player.sock.close()
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
            logger.error(
                f"Bad arguments: {' '.join(sys.argv)} resulted in error: {e}\nUsage: server.py [IP address] [port number]"
            )
            sys.exit(1)
        # instantiate server based on args
        server = Server(logger, ip, port)


    # no args -- use defaults
    elif len(sys.argv) == 1:
        logger.debug("No arguments passed. Using default IP address and port number")
        server = Server(logger)

    # wrong number of args
    else:
        logger.error(
            f"Bad arguments: {' '.join(sys.argv)}.\nUsage: server.py [IP address] [port number]"
        )
        exit(1)

    # qd_loader = QuizDataLoader()
    # qd_loader.load_quiz_files()
    # qd_data = qd_loader.get_quiz_data()

    # start the server!
    server.start()
