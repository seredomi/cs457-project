import unittest
from src.server.game_class import Game

class TestGame(unittest.TestCase):
    def setUp(self):
        self.questions = [
            {"question": "Q1", "possible_answers": [{"answer": "A", "is_correct": True}]},
            {"question": "Q2", "possible_answers": [{"answer": "B", "is_correct": False}]}
        ]
        self.game = Game("test_game", "owner_id", "owner", self.questions)

    def test_init(self):
        """Test game initialization"""
        self.assertEqual(self.game.game_id, "test_game")
        self.assertEqual(self.game.owner_id, "owner_id")
        self.assertEqual(self.game.curr_qi, 0)
        self.assertEqual(len(self.game.questions), 2)

    def test_add_remove_player(self):
        """Test adding and removing players"""
        self.game.add_player("player1")
        self.assertIn("player1", self.game.player_responses)

        self.game.remove_player("player1")
        self.assertNotIn("player1", self.game.player_responses)

    def test_store_response(self):
        """Test storing player responses"""
        self.game.add_player("player1")
        self.game.store_response("player1", 0)

        self.assertEqual(self.game.player_responses["player1"], 0)

    def test_advance_question(self):
        """Test question advancement"""
        initial_q = self.game.curr_qi
        self.game.advance_question()
        self.assertEqual(self.game.curr_qi, initial_q + 1)

    def test_get_response_progress(self):
        """Test response progress tracking"""
        self.game.add_player("player1")
        self.game.add_player("player2")

        progress = self.game.get_response_progress()
        self.assertEqual(progress, (0, 3))  # Including owner

        self.game.store_response("player1", 0)
        progress = self.game.get_response_progress()
        self.assertEqual(progress, (1, 3))

    def test_advance_question_when_no_more_questions(self):
        self.game.advance_question()
        self.game.advance_question()
        self.assertEqual(self.game.curr_qi, 1)

    def test_get_current_question(self):
        self.assertEqual(self.game.get_current_question(), self.questions[0])
        self.game.advance_question()
        self.assertEqual(self.game.get_current_question(), self.questions[1])

    def test_game_info(self):
        self.game.add_player("Player1")
        expected_info = "Game ID: test_game, Owner: owner, Players: owner Player1, Current Question: 1/2"
        self.assertEqual(self.game.info(), expected_info)

    def test_game_equality(self):
        self.assertNotEqual(self.game, "ABC")
        self.assertNotEqual(self.game, "XYZ")

    def test_generate_game_id(self):
        self.game.generate_game_id()
        self.assertEqual(len(self.game.game_id), 3)
        self.assertTrue(self.game.game_id.isalpha())
