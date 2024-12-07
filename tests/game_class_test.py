import unittest
from typing import Any, List
from src.server.game_class import Game


class TestGame(unittest.TestCase):
    
    def setUp(self):
        # sample game
        self.questions = [
            {"question": "What is 2 + 2?", "possible_answers": [{"answer": "3", "is_correct": False}, {"answer": "4", "is_correct": True}]},
            {"question": "What is the capital of France?", "possible_answers": [{"answer": "Berlin", "is_correct": False}, {"answer": "Paris", "is_correct": True}]}
        ]
        self.game = Game(game_id="ABC", owner_id="1", owner_name="Owner", questions=self.questions)

    def test_initial_game_state(self):
        self.assertEqual(self.game.game_id, "ABC")
        self.assertEqual(self.game.owner_name, "Owner")
        self.assertEqual(len(self.game.questions), 2)
        self.assertEqual(self.game.curr_qi, 0)
        self.assertEqual(self.game.player_responses, {"Owner": None})

    def test_add_player(self):
        self.game.add_player("Player1")
        self.assertIn("Player1", self.game.player_responses)
        self.assertEqual(self.game.player_responses["Player1"], None)

    def test_remove_player(self):
        self.game.add_player("Player1")
        self.game.remove_player("Player1")
        self.assertNotIn("Player1", self.game.player_responses)

    def test_store_response(self):
        self.game.add_player("Player1")
        self.game.store_response("Owner", 1)  
        self.game.store_response("Player1", 1)  
        self.assertTrue(self.game.all_players_responded())
        self.assertEqual(self.game.curr_qi, 1)  

    def test_store_incorrect_response(self):
        self.game.add_player("Player1")
        self.game.store_response("Owner", 0)  
        self.game.store_response("Player1", 1)  
        self.assertEqual(self.game.results, [{"Owner": False, "Player1": True}])

    def test_advance_question(self):
        self.game.advance_question()
        self.assertEqual(self.game.curr_qi, 1)

    def test_advance_question_when_no_more_questions(self):
        self.game.advance_question() 
        self.game.advance_question() 
        self.assertEqual(self.game.curr_qi, 1)

    def test_get_current_question(self):
        self.assertEqual(self.game.get_current_question(), self.questions[0])
        self.game.advance_question()
        self.assertEqual(self.game.get_current_question(), self.questions[1])

    def test_get_response_progress(self):
        self.game.add_player("Player1")
        self.assertEqual(self.game.get_response_progress(), (1, 2)) 
        self.game.store_response("Owner", 1)
        self.game.store_response("Player1", 1)
        self.assertEqual(self.game.get_response_progress(), (2, 2))

    def test_all_players_responded(self):
        self.game.add_player("Player1")
        self.assertFalse(self.game.all_players_responded())
        self.game.store_response("Owner", 1)
        self.assertFalse(self.game.all_players_responded())
        self.game.store_response("Player1", 1)
        self.assertTrue(self.game.all_players_responded())

    def test_game_info(self):
        self.game.add_player("Player1")
        expected_info = "Game ID: ABC, Owner: Owner, Players: Owner Player1, Current Question: 1/2"
        self.assertEqual(self.game.info(), expected_info)

    def test_game_str(self):
        self.game.add_player("Player1")
        self.game.store_response("Owner", 1)
        self.game.store_response("Player1", 1)
        expected_str = "id: ABC owner: Owner curr q: 2/2 all qs: 1/2"
        self.assertEqual(str(self.game), expected_str)

    def test_game_equality(self):
        game2 = Game(game_id="ABC", owner_id="2", owner_name="Owner2", questions=self.questions)
        self.assertEqual(self.game, game2)
        self.assertNotEqual(self.game, "ABC")
        self.assertNotEqual(self.game, "XYZ")

    def test_generate_game_id(self):
        self.game.generate_game_id()
        self.assertEqual(len(self.game.game_id), 3)
        self.assertTrue(self.game.game_id.isalpha())

if __name__ == "__main__":
    unittest.main()
