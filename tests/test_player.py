import unittest
from unittest.mock import Mock
from src.server.player_class import Player
import socket

class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.mock_socket = Mock()
        self.player = Player(self.mock_socket)

    def test_init(self):
        """Test player initialization"""
        self.assertEqual(self.player.name, "no_name")
        self.assertEqual(self.player.curr_game, "no_game")
        self.assertIsNotNone(self.player.id)

    def test_equality(self):
        """Test player equality comparisons"""
        player2 = Player(self.mock_socket)

        # Same socket should be equal
        self.assertEqual(self.player, player2)

        # Different socket should not be equal
        different_socket = Mock()
        player3 = Player(different_socket)
        self.assertNotEqual(self.player, player3)

        def test_player_str(self):
            expected_str = f"player {self.player.name} in game {self.player.curr_game} {self.mock_sock.getpeername()}"
            self.assertEqual(str(self.player), expected_str)

        def test_player_equality_with_other_player(self):
            mock_sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            player2 = Player(mock_sock2)
            self.assertNotEqual(self.player, player2)

        def test_player_equality_with_socket(self):
            self.assertEqual(self.player, self.mock_sock)

        def test_player_equality_with_id(self):
            self.assertEqual(self.player, self.player.id)
