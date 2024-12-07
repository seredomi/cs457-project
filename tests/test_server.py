import unittest
from unittest.mock import MagicMock, patch
from src.server.server import Server
import socket
import threading
import json
from unittest.mock import Mock

class TestServer(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock()
        self.server = Server(self.mock_logger)

    def test_server_initialization(self):
        self.assertEqual(self.server.host, "127.0.0.1")
        self.assertEqual(self.server.port_num, 5000)
        self.assertFalse(self.server.running)
        self.assertEqual(len(self.server.players), 0)
        self.assertEqual(len(self.server.curr_games), 0)

    def test_populate_chapters_available(self):
        self.server.populate_chapters_available()
        self.assertGreater(len(self.server.chapters_available), 0)

    @patch("socket.socket")
    def test_start_server_success(self, mock_socket):
        mock_socket_instance = MagicMock()
        mock_socket_instance.accept.return_value = (MagicMock(), ("127.0.0.1", 5000))
        mock_socket.return_value = mock_socket_instance

        with patch("server.Server.print_info") as mock_print_info:
            self.server.start()
            mock_print_info.assert_called() 

    @patch("socket.socket")
    def test_start_server_fail(self, mock_socket):
        mock_socket_instance = MagicMock()
        mock_socket_instance.accept.side_effect = Exception("Socket error")
        mock_socket.return_value = mock_socket_instance

        with patch("server.Server.print_info") as mock_print_info:
            self.server.start()
            mock_print_info.assert_not_called() 

    @patch("server.receive_message")
    @patch("server.send_message")
    @patch("socket.socket.recv", return_value=b'{"message_type": "create_game", "player_name": "Alice", "game_id": "game123"}')
    def test_handle_create_game(self, mock_recv, mock_send_message, mock_receive_message):
        mock_socket = MagicMock()
        mock_addr = ("127.0.0.1", 5000)
        
        player_mock = MagicMock()
        self.server.players.append(player_mock)
        
        self.server.handle_client(mock_socket, mock_addr)
        
        self.assertEqual(player_mock.curr_game, "game123")
        mock_send_message.assert_called() 
        mock_receive_message.assert_called() 

    @patch("signal.signal")
    def test_server_shutdown(self, mock_signal):
        with patch("server.Server.cleanup") as mock_cleanup:
            self.server.running = True
            self.server.shutdown(None, None)
            mock_cleanup.assert_called_once() 
            self.assertFalse(self.server.running) 

    @patch("server.send_message")
    @patch("server.receive_message")
    def test_handle_player_disconnect(self, mock_receive_message, mock_send_message):
        message = json.dumps({
            "message_type": "game_update",
            "subtype": "player_disconnect",
            "player_name": "Alice"
        })
        mock_socket = MagicMock()
        mock_socket.recv.return_value = message.encode('utf-8')
        
        player_mock = MagicMock(name="Alice")
        self.server.players.append(player_mock)
        
        self.server.handle_client(mock_socket, ("127.0.0.1", 5000))
        
        self.server.handle_player_disconnect(player_mock)
        mock_send_message.assert_called()
        
if __name__ == "__main__":
    unittest.main()
