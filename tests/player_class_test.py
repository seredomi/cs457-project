import unittest
import socket
from src.server.player_class import Player  # Assuming Player class is in 'player.py'


class TestPlayer(unittest.TestCase):

    def setUp(self):
        # mock sock
        self.mock_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.player = Player(self.mock_sock)

    def test_player_initialization(self):
        self.assertEqual(self.player.name, "no_name")
        self.assertEqual(self.player.curr_game, "no_game")
        self.assertIsInstance(self.player.id, str)
        self.assertEqual(len(self.player.id), 36) 

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

if __name__ == "__main__":
    unittest.main()
