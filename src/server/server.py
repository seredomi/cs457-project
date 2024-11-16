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
        print("=== server info ===")
        print("Players:")
        print(player_table)

        game_table = PrettyTable()
        game_table.field_names = ["id", "owner", "curr responses", "quiz progress"]
        for game in self.curr_games:
            game_table.add_row(
                [
                    game.game_id,
                    game.owner_name,
                    game.get_response_progress_str(),
                    f"{game.curr_qi + 1}/{len(game.questions)}",
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
                    message = client_socket.recv(2048).decode("utf-8")
                    if not message:
                        break
                    receive_message(self.logger, message, client_socket)
                    msg_obj = json.loads(message)
                    msg_type = msg_obj["message_type"]

                    if msg_type == "create_game":
                        player_name = msg_obj["player_name"]
                        game_id = msg_obj["game_id"]
                        player = next((p for p in self.players if p.sock == client_socket), None)
                        if player is None:
                            self.logger.error(f"Player not found for socket {client_socket}")
                            return
                        player.curr_game = game_id
                        player.name = player_name
                        self.logger.debug(
                            f"Player {player_name} wants to start a game named {game_id}"
                        )
                        self.print_info()
                        self.handle_create_game(msg_obj, player)

                    elif msg_type == "join_game":
                        player_name = msg_obj["player_name"]
                        game_id = msg_obj["game_id"]
                        player = next((p for p in self.players if p.sock == client_socket), None)
                        if player is None:
                            self.logger.error(f"Player not found for socket {client_socket}")
                            return
                        player.curr_game = game_id
                        player.name = player_name
                        self.handle_join_game(msg_obj, player)

                    elif msg_type == "game_update":
                        subtype = msg_obj["subtype"]
                        player_name = msg_obj["player_name"]
                        if subtype == "player_disconnect":
                            player = next((p for p in self.players if p == player_name), None)
                            if player:
                                self.handle_player_disconnect(player)
                        elif subtype == "player_leave":
                            self.logger.info("player_leave: looking for player")
                            player = next((p for p in self.players if p.name == player_name), None)
                            if player:
                                self.logger.info("player_leave: found player")
                                self.handle_player_leave(player)
                            else:
                                self.logger.info(f"player_leave: player {player_name} not found. players: {[str(player) for player in self.players]}")
                        self.print_info()

                    elif msg_type == "quiz_answer":
                        player_name = msg_obj["player_name"]
                        game_id = msg_obj["game_id"]
                        game = next((g for g in self.curr_games if g == game_id), None)
                        if game:
                            reponses_done = game.store_response(player_name, msg_obj["answer"])
                            if reponses_done:
                                # get and broadcast next question
                                question = game.get_current_question()
                                self.broadcast({
                                    "message_type": "quiz_question",
                                    **question
                                }, game)

                            # broadcast response progress regardless
                            self.broadcast({
                                "message_type": "game_update",
                                "subtype": "response_update",
                                "message": game.get_response_progress_str()
                            }, game)
                        self.print_info()

                    else:
                        self.logger.error(f"unknown message type from {addr}")
                        raise Exception(f"unknown message type {msg_obj}")

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

    def handle_player_update(self, old_name: str, old_game: str, new_name: str, new_game: str):
        remove_msg = {
            "message_type": "game_update",
            "subtype": "player_disconnect",
            "player_name": old_name,
            "game_id": old_game
        }
        self.broadcast(remove_msg)

        update_msg = {
            "message_type": "game_update",
            "subtype": "player_connect",
            "player_name": new_name,
            "game_id": new_game
        }
        self.broadcast(update_msg)

    # start game
    def handle_create_game(self, msg_obj, player: Player):
        game_id = msg_obj.get("game_id", "unknown_game_id")
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

            # broadcast game created
            response = {
                "message_type": "game_update",
                "subtype": "game_created",
                "game_id": game_id,
                "player_id": player_id,
                "message": f"game {game_id} created successfully by {player.name}",
            }
            self.logger.debug(f"game {game_id} created successfully by {player_id}")
            self.broadcast(response)

            self.handle_player_update("no_name", "no_game", player.name, new_game.game_id)

            # send first question to player
            question = new_game.get_current_question()
            message = {
                "message_type": "quiz_question",
                **question,
            }
            send_message(self.logger, message, player.sock)
            message = {
                "message_type": "game_update",
                "subtype": "response_update",
                "message": new_game.get_response_progress_str()
            }
            send_message(self.logger, message, player.sock)

            self.print_info()

        except Exception as e:
            error_message = {
                "message_type": "error",
                "message": f"error creating game: {e}",
            }
            send_message(self.logger, error_message, player.sock)

    # join game
    def handle_join_game(self, msg_obj, player: Player):
        game_id = msg_obj.get("game_id")
        game = next((g for g in self.curr_games if g.game_id == game_id), None)

        try:
            # find game by game_id in curr_games
            if not game:
                raise Exception(f"game id {game_id} not found")

            game.add_player(player.name)

            self.handle_player_update("no_name", "no_game", player.name, game.game_id)

            game.add_player(player.name)

            # broadcast game reponse progress
            response = {
                "message_type": "game_update",
                "subtype": "response_update",
                "message": game.get_response_progress_str()
            }
            self.broadcast(response, game=game)

            # send current question to player
            question = game.get_current_question()
            message = {
                "message_type": "quiz_question",
                **question,
            }
            send_message(self.logger, message, player.sock)
            self.print_info()

        except Exception as e:
            error_message = {
                "message_type": "error",
                "message": f"error joining game: {e}",
            }
            send_message(self.logger, error_message, player.sock)

    def handle_player_leave(self, player: Player):
        # Remove player from current game
        self.logger.info("handle_pl: looking for game!!")
        game = next((g for g in self.curr_games if player.name in g.player_responses), None)
        if game:
            self.logger.info("handle_pl: game found")
            # attempt to send player results
            # self.send_results(game, player)

            # Remove player from the game
            game.remove_player(player.name)
            self.logger.info(f"Player {player.name} removed from game {game.game_id}")

            # Check if the player is the owner of the game
            if game.owner_name == player.name:
                # End the game
                self.delete_game(game.game_id)
                # Broadcast to other players that the game has ended
                response = {
                    "message_type": "game_update",
                    "subtype": "game_end",
                    "game_id": game.game_id,
                    "message": f"Game {game.game_id} has ended because the owner {player.name} left."
                }
                self.broadcast(response)

            else:
                # Broadcast to other players that the player left
                response = {
                    "message_type": "game_update",
                    "subtype": "player_leave",
                    "game_id": game.game_id,
                    "player_name": player.name,
                    "message": f"Player {player.name} has left game {game.game_id}"
                }
                self.broadcast(response)

                # Proceed to next question if all other responses are collected
                if game.all_players_responded():
                    if game.advance_question():
                        # send response update
                        response = {
                            "message_type": "game_update",
                            "subtype": "response_update",
                            "message": game.get_response_progress_str()
                        }
                        self.broadcast(response, game=game)
                        # Send the next question to all players
                        question = game.get_current_question()
                        response = {
                            "message_type": "quiz_question",
                            **question
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

        player.name = "no_name"
        player.curr_game = "no_game"
        self.logger.info(f"handle_pl: games: {self.curr_games} players: {self.players}")

    def handle_player_disconnect(self, player: Player):
        self.handle_player_leave(player)

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
            self.logger.info(self.curr_games)

            self.broadcast(response, game=game)

        except Exception as e:
            self.logger.error(f"Error deleting game {game_id}: {e}")

    # send a message to subset of clients
    def broadcast(self, message, game=None):
        recipients = self.players

        # If given a game, broadcast to players in that game
        if game:
            recipients = []
            for player_name in game.player_responses.keys():
                player = next((p for p in self.players if p.name == player_name), None)
                if player:
                    recipients.append(player)

        for player in recipients:
            try:
                send_message(self.logger, message, player.sock)
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                self.logger.error(f"Error broadcasting to {player.name}: {e}")

    def send_results(self, game, player=None):
        results_message = {
            "message_type": "results",
            "results": game.results
        }
        if player:
            send_message(self.logger, results_message, player.sock)
        else:
            self.broadcast(results_message, game)

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
