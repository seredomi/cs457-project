import unittest
from unittest.mock import Mock, patch
import socket
import json
from src.client.client import Client

class TestClient(unittest.TestCase):
    def setUp(self):
        self.logger = Mock()
        # Patch socket at class level
        self.socket_patcher = patch('socket.socket')
        self.mock_socket = self.socket_patcher.start()
        self.client = Client(self.logger, "localhost", 5000)

        # Mock the ui_handler to prevent display loop
        self.client.ui_handler = Mock()

    def tearDown(self):
        self.socket_patcher.stop()

    def test_init(self):
        """Test client initialization"""
        self.assertEqual(self.client.host, "localhost")
        self.assertEqual(self.client.port, 5000)
        self.assertFalse(self.client.running)
        self.assertFalse(self.client.is_connected)
        self.assertEqual(self.client.curr_games, [])
        self.assertEqual(self.client.curr_players, [])
        self.assertEqual(self.client.game_id, "")
        self.assertEqual(self.client.player_name, "")

    def test_disconnect(self):
        """Test client disconnect"""
        self.client.running = True
        self.client.player_name = "test_player"

        self.client.disconnect()

        self.assertFalse(self.client.running)
        self.mock_socket.return_value.close.assert_called_once()
        self.client.ui_handler.stop.assert_called_once()

    def test_receive_messages_game_update(self):
        """Test handling of game update messages"""
        # Set up mock socket behavior
        mock_socket_instance = self.mock_socket.return_value

        # Set up a sequence of responses
        message = {
            "message_type": "game_update",
            "subtype": "game_created",
            "game_id": "test_game"
        }

        # Make recv return our message once, then raise socket.timeout
        mock_socket_instance.recv.side_effect = [
            json.dumps(message).encode('utf-8'),
            socket.timeout
        ]

        self.client.running = True
        self.client.receive_messages()

        self.assertIn("test_game", self.client.curr_games)

    def test_receive_messages_new_connection(self):
        """Test handling of new connection messages"""
        # Set up mock socket behavior
        mock_socket_instance = self.mock_socket.return_value

        message = {
            "message_type": "new_connection_prompt",
            "current_players": ["player1", "player2"],
            "current_games": ["game1"],
            "chapters_available": {"1": 5, "2": 3}
        }

        # Make recv return our message once, then raise socket.timeout
        mock_socket_instance.recv.side_effect = [
            json.dumps(message).encode('utf-8'),
            socket.timeout
        ]

        self.client.running = True
        self.client.receive_messages()

        self.assertEqual(self.client.curr_players, ["player1", "player2"])
        self.assertEqual(self.client.curr_games, ["game1"])
        self.assertEqual(self.client.available_chapters, {"1": 5, "2": 3})

    def test_receive_messages_quiz_question(self):
        """Test handling of quiz questions"""
        # Set up mock socket behavior
        mock_socket_instance = self.mock_socket.return_value

        question = {
            "message_type": "quiz_question",
            "question": "Test question?",
            "possible_answers": [
                {"answer": "A", "is_correct": True},
                {"answer": "B", "is_correct": False}
            ]
        }

        # Make recv return our message once, then raise socket.timeout
        mock_socket_instance.recv.side_effect = [
            json.dumps(question).encode('utf-8'),
            socket.timeout
        ]

        self.client.running = True
        self.client.receive_messages()

        self.assertEqual(self.client.curr_question, question)

    def test_receive_messages_server_shutdown(self):
        """Test handling of server shutdown message"""
        # Set up mock socket behavior
        mock_socket_instance = self.mock_socket.return_value

        message = {
            "message_type": "server_shutdown"
        }

        # Make recv return our message once, then raise socket.timeout
        mock_socket_instance.recv.side_effect = [
            json.dumps(message).encode('utf-8'),
            socket.timeout
        ]

        self.client.running = True
        self.client.receive_messages()

        self.assertFalse(self.client.running)

    @patch('threading.Thread')
    def test_connect(self, mock_thread):
        """Test client connection"""
        self.client.connect()

        self.assertTrue(self.client.is_connected)
        self.assertTrue(self.client.running)
        mock_thread.assert_called_once()
        self.client.ui_handler.start.assert_called_once()
