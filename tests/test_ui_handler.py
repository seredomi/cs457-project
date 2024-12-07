import unittest
from unittest.mock import Mock, patch
import urwid
from src.client.ui import UIHandler

class TestUIHandler(unittest.TestCase):
    def setUp(self):
        self.logger = Mock()
        self.client = Mock()
        self.ui_handler = UIHandler(self.client, self.logger)

    def test_init(self):
        """Test UI handler initialization"""
        self.assertEqual(self.ui_handler.curr_screen, "connecting")
        self.assertFalse(self.ui_handler.running)
        self.assertIsInstance(self.ui_handler.txt_title, urwid.Text)
        self.assertIsInstance(self.ui_handler.txt_instructions, urwid.Text)
        self.assertIsInstance(self.ui_handler.input_box, urwid.Edit)

    def test_stop(self):
        """Test UI handler stop"""
        self.ui_handler.running = True
        with self.assertRaises(urwid.ExitMainLoop):
            self.ui_handler.stop()
        self.assertFalse(self.ui_handler.running)

    def test_handle_input_quit(self):
        """Test handling quit input"""
        self.ui_handler.curr_screen = "main_menu"
        self.ui_handler.input_box.set_edit_text('q')
        self.ui_handler.handle_input('enter')
        self.client.disconnect.assert_called_once()

    def test_handle_input_main_menu(self):
        """Test handling main menu input"""
        self.ui_handler.curr_screen = "main_menu"
        self.ui_handler.input_box.set_edit_text('1')
        self.ui_handler.handle_input('enter')
        self.assertEqual(self.ui_handler.curr_screen, "create_game_1")
