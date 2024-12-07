import sys
import os
import socket
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import unittest
from unittest.mock import patch, MagicMock
print("Running test...")
from src.client.client import Client

class TestClient(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock()
        self.client = Client(self.mock_logger)

    def test_client_initialization(self):
        self.assertEqual(self.client.host, "localhost")
        self.assertEqual(self.client.port, 5000)
        self.assertFalse(self.client.is_connected)
        self.assertFalse(self.client.running)

    @patch("socket.socket.connect")
    def test_connect_success(self, mock_connect):
        self.client.connect()
        mock_connect.assert_called_with(("localhost", 5000))
        self.assertTrue(self.client.is_connected)

    @patch("socket.socket.connect", side_effect=ConnectionRefusedError)
    def test_connect_failure(self, mock_connect):
        self.client.connect()
        self.mock_logger.error.assert_called_with("Connection failed. Server might be offline.")
        self.assertFalse(self.client.is_connected)

    @patch("socket.socket.recv", side_effect=[b'{"message_type": "error", "message": "Test Error"}', b''])
    def test_receive_messages_error(self, mock_recv):
        self.client.running = True
        self.client.receive_messages()
        self.mock_logger.error.assert_called_with("\nServer error: Test Error")
        self.assertFalse(self.client.running)

    @patch("socket.socket.recv", side_effect=[b'{"message_type": "game_update", "subtype": "game_created", "game_id": "12345"}', b''])
    def test_receive_messages_game_created(self, mock_recv):
        self.client.running = True
        self.client.receive_messages()
        self.assertIn("12345", self.client.curr_games)

    @patch("socket.socket.recv", side_effect=[b'{"message_type": "game_update", "subtype": "game_end", "game_id": "12345"}', b''])
    def test_receive_messages_game_end(self, mock_recv):
        self.client.curr_games = ["12345"]
        self.client.running = True
        self.client.receive_messages()
        self.assertNotIn("12345", self.client.curr_games)

    @patch("socket.socket.recv", side_effect=[b'{"message_type": "game_update", "subtype": "player_connect", "player_id": "player1", "game_id": "12345"}', b''])
    def test_receive_messages_player_connect(self, mock_recv):
        self.client.running = True
        self.client.receive_messages()
        self.assertIn("player1", self.client.curr_players)

    @patch("socket.socket.recv", side_effect=[b'{"message_type": "game_update", "subtype": "player_disconnect", "player_id": "player1", "game_id": "12345"}', b''])
    def test_receive_messages_player_disconnect(self, mock_recv):
        self.client.curr_players = ["player1"]
        self.client.running = True
        self.client.receive_messages()
        self.assertNotIn("player1", self.client.curr_players)


if __name__ == "__main__":
    unittest.main()
