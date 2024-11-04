from typing import List
import re

def new_connection_dialog(games_exist: bool = False):
    print("\n-------------------------------------------")
    print("welcome. please select an option:")
    print("1. start a new game")
    if games_exist: print("2. join an existing game")
    print("3. exit")
    option = input("Enter the number of your choice: ")
    options = ['1', '3']
    if games_exist: options.append('2')
    if option not in options:
        print("Invalid choice. please try again.")
        return new_connection_dialog()
    return int(option)

def create_game_dialog(available_chapters: List[int] = [1, 2, 3], max_questions: int = 20, curr_games: List[str] = [], curr_players: List[str] = []):

    print("\n-------------------------------------------")
    print("creating a new game...\n")
    print("enter a player name. no spaces or funny characters allowed ")
    player_name = input()
    while not re.match("^[a-zA-Z0-9_]*$", player_name) or player_name in curr_players or len(player_name) < 1:
        print("invalid player name. please try again.")
        return create_game_dialog(available_chapters, max_questions, curr_games)

    print("enter a game name. can't be a current game name. no spaces or funny characters allowed ")
    game_name = input()
    while not re.match("^[a-zA-Z0-9_]*$", game_name) or game_name in curr_games or len(game_name) < 1:
        print("invalid game name. please try again.")
        game_name = input()

    print("select chapters from the following list: " + " ".join([str(ch) for ch in available_chapters]))
    print("select chapters as a space separated list (ex: '1 2 3')")
    chapters = []
    try: chapters = [int(ch) for ch in input().split()]
    except: pass
    while len(chapters) < 1 or (not all(ch in available_chapters for ch in chapters)):
        print("invalid input. please try again.")
        try: chapters = [int(ch) for ch in input().split()]
        except: pass

    print(f"enter the total number of questions. max is {max_questions}")
    num_questions = 0
    try: num_questions = int(input())
    except: pass
    while num_questions < 1 or num_questions > max_questions:
        print("invalid input. please try again.")
        try: num_questions = int(input())
        except: pass

    return {
        "message_type": "create_game",
        "game_name": game_name,
        "player_name": player_name,
        "is_private": False,
        "password": "",
        "chapters": chapters,
        "num_questions": num_questions,
    }

def join_game_dialog(curr_games: List[str] = [], curr_players: List[str] = []):

    print("\n-------------------------------------------")
    print("joining an existing game...\n")
    print("Enter your player name. No spaces or special characters allowed:")
    player_name = input()
    while not re.match("^[a-zA-Z0-9_]*$", player_name) or player_name in curr_players or len(player_name) < 1:
        print("invalid player name or name already taken. Please try again.")
        player_name = input()

    print(f"enter the game name to join. available games: {', '.join(curr_games)}")
    game_name = input()
    while not re.match("^[a-zA-Z0-9_]*$", game_name) or game_name not in curr_games or len(game_name) < 1:
        print("Game not found or invalid name. Please try again.")
        game_name = input()

    return {
        "message_type": "join_game",
        "player_name": player_name,
        "game_name": game_name,
    }
def quiz_question_dialog(question_data: dict) -> str:
    # get question and answers
    question = question_data.get("question", "No question found.")
    offered_answers = question_data.get("offered-answers", [])

    # check for missing data/answers
    if not offered_answers:
        print("No answers found for the question.")
        return "No Answer"

    # display question and answers
    print("\nQuestion: " + question)
    for index, answer_obj in enumerate(offered_answers, start=1):
        answer_text = answer_obj.get("answer", "No answer text provided.")
        print(f"{index}. {answer_text}")

    # prompt the player for response
    while True:
        try:
            user_choice = int(input("Enter the number of your answer: "))
            if 1 <= user_choice <= len(offered_answers):
                return offered_answers[user_choice - 1]["answer"]  # return answer
            else:
                print("Invalid choice, please enter a number associated with one of the options available.")
        except ValueError:
            print("Invalid input, please enter a number.")
