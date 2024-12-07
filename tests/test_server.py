import unittest
from unittest.mock import Mock, patch
import socket
import json
from src.server.server import Server
from src.server.game_class import Game
from src.server.player_class import Player

class TestServer(unittest.TestCase):
    def setUp(self):
        self.logger = Mock()
        self.server = Server(self.logger, "localhost", 5000)

    def test_init(self):
        """Test server initialization"""
        self.assertEqual(self.server.host, "localhost")
        self.assertEqual(self.server.port_num, 5000)
        self.assertFalse(self.server.running)
        self.assertIsInstance(self.server.players, list)
        self.assertIsInstance(self.server.curr_games, list)

    def test_populate_chapters_available(self):
        """Test chapters are correctly populated"""
        self.server.quiz_data = {"1": [1, 2, 3], "2": [1, 2]}
        self.server.populate_chapters_available()
        self.assertEqual(self.server.chapters_available, {'4': 3, '5': 9, '2': 2, '3': 4, '1': 3, '6': 6, '7': 10})

    @patch('socket.socket')
    def test_handle_create_game(self, mock_socket):
        """Test game creation"""
        player = Player(mock_socket)
        player.name = "test_player"

        msg = {
            "game_id": "test_game",
            "chapters": ["1"],
            "num_questions": 1
        }

        self.server.handle_create_game(msg, player)

        # Verify game was created
        self.assertEqual(len(self.server.curr_games), 1)
        self.assertEqual(self.server.curr_games[0].game_id, "test_game")

    def test_check_game_end(self):
        """Test game end conditions"""
        game = Game("test_game", "owner_id", "owner", [{"question": "test"}])
        game.curr_qi = 0
        self.server.curr_games.append(game)

        # Game should not end when not all players responded
        self.assertFalse(self.server.check_game_end("test_game"))
