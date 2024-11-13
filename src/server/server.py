from logging import PercentStyle
import sys
import socket
import threading
import signal
import json
import random
from typing import List
import ipaddress
from prettytable import PrettyTable

from src.utils.messages import send_message, receive_message
from src.server.player_class import Player
from src.server.game_class import Game
from src.server.data.loader import QuizDataLoader
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
        self.quiz_data = QuizDataLoader(self.logger).quiz_data
        self.chapters_available = {}
        self.populate_chapters_available()

    def populate_chapters_available(self):
        for chapter, questions in self.quiz_data.items():
            self.chapters_available[chapter] = len(questions)

    def print_info(self):
        player_table = PrettyTable()
        player_table.field_names = ["name", "curr_game", "ip", "port"]
        for player in self.players:
            player_table.add_row(
                [
                    player.name,
                    player.curr_game,
                    player.sock.getpeername()[0],
                    player.sock.getpeername()[1],
                ]
            )
        print_header("current server info")
        print("Players:")
        print(player_table)

        game_table = PrettyTable()
        game_table.field_names = ["id", "owner", "curr q", "all qs"]
        for game in self.curr_games:
            game_table.add_row(
                [
                    game.game_id,
                    game.owner_name,
                    f"{sum([1 if val is not None else 0 for val in game.player_responses.values()])}/{len(game.player_responses)}",
                    f"{game.current_question_index + 1}/{len(game.questions)}",
                ]
            )
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
            self.logger.info(
                f"Server started on {self.host}:{self.port_num}\nListening for connections..."
            )

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

                except socket.timeout:
                    continue
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
                "current_games": [game.game_id for game in self.curr_games],
                "current_players": [player.name for player in self.players],
                "chapters_available": self.chapters_available,
            }
            send_message(self.logger, new_connection_prompt, client_socket)

            while self.running:
                try:
                    client_socket.settimeout(1.0)
                    # blocking call awaits message from client
                    message = client_socket.recv(1024).decode("utf-8")
                    if not message:
                        break
                    receive_message(self.logger, message, client_socket)
                    msg_obj = json.loads(message)
                    msg_type = msg_obj["message_type"]

                    if msg_type == "create_game":
                        player_name = msg_obj["player_name"]
                        game_name = msg_obj["game_name"]
                        player = next((p for p in self.players if p.sock == client_socket), None)
                        if player is None:
                            self.logger.error(f"Player not found for socket {client_socket}")
                            return
                        player.curr_game = game_name
                        player.name = player_name
                        self.logger.debug(
                            f"Player {player_name} wants to start a game named {game_name}"
                        )
                        self.print_info()
                        self.handle_create_game(msg_obj, player)

                    elif msg_type == "join_game":
                        player_name = msg_obj["player_name"]
                        game_name = msg_obj["game_name"]
                        player = next((p for p in self.players if p.sock == client_socket), None)
                        if player is None:
                            self.logger.error(f"Player not found for socket {client_socket}")
                            return
                        player.curr_game = game_name
                        player.name = player_name
                        self.handle_join_game(msg_obj, player)


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
            player = next((p for p in self.players if p.sock == client_socket), None)
            if player:
                self.handle_player_disconnect(player)
            client_socket.close()
            self.logger.debug(f"Connection from {addr} closed")
            self.print_info()


    # start game
    def handle_create_game(self, msg_obj, player: Player):
        game_id = msg_obj.get("game_name", "unknown_game_id")
        player_id = player.id  # Define player_id
        self.print_info()

        # client has returned a set of chapters and the total number of questions to be included
        # we need to create a subset of self.quiz_data that includes only the selected chapters
        # and also only the number of questions requested, with respect to the number of questions in each chapter
        selected_chapters = msg_obj.get("chapters", [])
        num_questions = msg_obj.get("num_questions", 0)
        total_possible_questions = sum(
            [len(self.quiz_data[chapter]) for chapter in selected_chapters]
        )
        percentage_per_chapter = num_questions / total_possible_questions
        questions = []
        for i, ch in enumerate(selected_chapters):
            full_chapter = self.quiz_data[ch]
            random.shuffle(full_chapter)
            questions.extend(full_chapter[0:int(percentage_per_chapter * len(full_chapter))])

            # if last chapter and not enough questions, add more
            if i == len(selected_chapters) - 1 and len(questions) < num_questions:
                start = int(percentage_per_chapter * len(full_chapter))
                remainder = num_questions - len(questions)
                end = start + remainder if start + remainder < len(full_chapter) else len(full_chapter)
                questions.extend(full_chapter[start : end])

        try:
            # Check if game already exists
            if any(g.game_id == game_id for g in self.curr_games):
                raise Exception(f"Game {game_id} already exists")

            # new game
            new_game = Game(
                game_id=game_id,
                owner_id=player_id,
                owner_name=player.name,
                questions=questions,
            )
            self.curr_games.append(new_game)  # add new game to curr_games

            # confirmation
            response = {
                "message_type": "game_update",
                "subtype": "game_created",
                "game_id": game_id,
                "player_id": player_id,
                "message": f"game {game_id} created successfully by {player.name}",
            }
            self.logger.debug(f"game {game_id} created successfully by {player_id}")
            self.broadcast(response)
            self.print_info()

        except Exception as e:
            error_message = {
                "message_type": "error",
                "message": f"error creating game: {e}",
            }
            send_message(self.logger, error_message, player.sock)

    # join game
    def handle_join_game(self, msg_obj, player: Player):
        game_id = msg_obj.get("game_name")
        game = next((g for g in self.curr_games if g.game_id == game_id), None)
        player_id = player.id

        try:
            # find game by game_id in curr_games
            if not game:
                raise Exception(f"game id {game_id} not found")

            game.add_player(player.id)

            response = {
                "message_type": "game_update",
                "subtype": "player_join",
                "game_id": game_id,
                "player_id": player_id,
                "message": f"player {player.name} successfully joined game {game_id}",
            }
            send_message(self.logger, response, player.sock)
            self.logger.info(f"player {player_id} joined game {game_id}")

            self.broadcast(response)
            self.print_info()

        except Exception as e:
            error_message = {
                "message_type": "error",
                "message": f"error joining game: {e}",
            }
            send_message(self.logger, error_message, player.sock)

    def handle_player_disconnect(self, player: Player):
        # Remove player from any games they are in
        game = next((g for g in self.curr_games if player.id in g.player_responses), None)
        if game:
            # Remove player from the game
            game.remove_player(player.id)
            self.logger.info(f"Player {player.name} removed from game {game.game_id}")

            # Check if the player is the owner of the game
            if game.owner_id == player.id:
                # End the game
                self.delete_game(game.game_id)
                # Broadcast to other players that the game has ended
                response = {
                    "message_type": "game_update",
                    "subtype": "game_end",
                    "game_id": game.game_id,
                    "message": f"Game {game.game_id} has ended because the owner {player.name} left."
                }
                self.broadcast(response, game=game)
            else:
                # Broadcast to other players that the player left
                response = {
                    "message_type": "game_update",
                    "subtype": "player_left",
                    "game_id": game.game_id,
                    "player_id": player.id,
                    "message": f"Player {player.name} has left the game."
                }
                self.broadcast(response, game=game)

                # Proceed to next question if all other responses are collected
                if game.all_players_responded():
                    if game.advance_question():
                        # Send the next question to all players
                        question = game.get_current_question()
                        response = {
                            "message_type": "question",
                            "game_id": game.game_id,
                            "question": question
                        }
                        self.broadcast(response, game=game)
                    else:
                        # Game over
                        self.delete_game(game.game_id)
                        response = {
                            "message_type": "game_update",
                            "subtype": "game_end",
                            "game_id": game.game_id,
                            "message": f"Game {game.game_id} has ended."
                        }
                        self.broadcast(response, game=game)
        else:
            self.logger.info(f"Player {player.name} was not in any game.")

        # Remove the player from the server's player list
        if player in self.players:
            self.players.remove(player)
        # Close the player's socket
        try:
            player.sock.close()
        except Exception as e:
            self.logger.error(f"Error closing socket for {player.name}: {e}")
        # delete game

    def delete_game(self, game_id):
        try:
            # Find game by game_id in curr_games
            game = next((g for g in self.curr_games if g.game_id == game_id), None)
            if not game:
                raise Exception(f"Game id {game_id} not found")

            self.curr_games.remove(game)
            response = {
                "message_type": "game_update",
                "subtype": "game_end",
                "game_id": game_id,
                "message": f"Game {game_id} has ended",
            }
            self.logger.info(f"Game {game_id} deleted successfully.")

            self.broadcast(response, game=game)

        except Exception as e:
            self.logger.error(f"Error deleting game {game_id}: {e}")

    # send a message to subset of clients
    def broadcast(self, message, game=None):
        recipients = self.players

        # If given a game, broadcast to players in that game
        if game:
            recipients = []
            for player_id in game.player_responses.keys():
                player = next((p for p in self.players if p.id == player_id), None)
                if player:
                    recipients.append(player)

        for player in recipients:
            try:
                send_message(self.logger, message, player.sock)
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                self.logger.error(f"Error broadcasting to {player.name}: {e}")
                # Handle the disconnection
                self.handle_player_disconnect(player)


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
            except Exception:
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

    # start the server!
    server.start()
