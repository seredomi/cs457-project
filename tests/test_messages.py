import unittest
from unittest.mock import Mock
import json
from src.utils.messages import send_message, receive_message

class TestMessages(unittest.TestCase):
    def setUp(self):
        self.logger = Mock()

    def test_validate_create_game_message(self):
        """Test create game message validation"""
        valid_msg = {
            "message_type": "create_game",
            "player_name": "test",
            "game_id": "game1",
            "is_private": False,
            "chapters": ["1", "2"],
            "num_questions": 5
        }

        # Should not raise exception
        receive_message(self.logger, json.dumps(valid_msg))

    def test_send_message(self):
        """Test message sending"""
        mock_socket = Mock()
        msg = {
            "message_type": "game_update",
            "subtype": "game_created",
            "game_id": "test"
        }

        send_message(self.logger, msg, mock_socket)
        mock_socket.send.assert_called_once()
