import unittest
from unittest.mock import Mock
from src.server.player_class import Player

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
