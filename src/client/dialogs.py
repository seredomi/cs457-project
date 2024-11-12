from src.utils.display import print_header
from typing import List, Dict
import re


def new_connection_dialog(games_exist: bool = False):
    print_header("welcome to cs457 quiz game")

    print("select an option:")
    print("1. start a new game")
    options = ["1", "3"]
    if games_exist:
        print("2. join an existing game")
        options.append("2")
    print("3. exit")
    option = input("Enter the number of your choice: ").strip()

    if option not in options:
        print("\nInvalid choice. please try again.")
        return new_connection_dialog()
    return int(option)


def create_game_dialog(
    available_chapters: List[Dict[str, int]] = [
        {"chapter": 1, "questions": 20},
        {"chapter": 2, "questions": 5},
    ],
    curr_games: List[str] = [],
    curr_players: List[str] = [],
):
    print_header("creating a new game")
    print("enter a player name. no spaces or funny characters allowed ")
    player_name = input()
    while (
        not re.match("^[a-zA-Z0-9_]*$", player_name)
        or player_name in curr_players
        or len(player_name) < 1
    ):
        print("\ninvalid player name. please try again.")
        return create_game_dialog(available_chapters, curr_games, curr_players)

    print(
        "\nenter a game name. can't be a current game name. no spaces or funny characters allowed "
    )
    game_name = input()
    while (
        not re.match("^[a-zA-Z0-9_]*$", game_name)
        or game_name in curr_games
        or len(game_name) < 1
    ):
        print("\ninvalid game name. please try again.")
        game_name = input()

    print(
        "\nselect chapters from the following list: "
        + " ".join([str(ch) for ch in available_chapters])
    )
    print("enter chapters as a space separated list (ex: '1 3')")
    chapters = []
    try:
        chapters = [int(ch) for ch in input().split()]
    except Exception:
        pass

    while len(chapters) < 1 or (not all(ch in available_chapters for ch in chapters)):
        print("\ninvalid input. please try again.")
        try:
            chapters = [int(ch) for ch in input().split()]
        except Exception:
            pass

    print(
        f"\nenter the total number of questions. max is {sum(ch['questions'] for ch in available_chapters)}"
    )
    num_questions = 0
    try:
        num_questions = int(input())
    except Exception:
        pass
    while num_questions < 1 or num_questions > sum(
        ch["questions"] for ch in available_chapters
    ):
        print("\ninvalid input. please try again.")
        try:
            num_questions = int(input())
        except Exception:
            pass

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
    print_header("joining an existing game")
    print("enter your player name. No spaces or special characters allowed:")
    player_name = input()
    while (
        not re.match("^[a-zA-Z0-9_]*$", player_name)
        or player_name in curr_players
        or len(player_name) < 1
    ):
        print("\ninvalid player name or name already taken. Please try again.")
        player_name = input()

    print(f"\nenter the game name to join. available games: {', '.join(curr_games)}")
    game_name = input()
    while (
        not re.match("^[a-zA-Z0-9_]*$", game_name)
        or game_name not in curr_games
        or len(game_name) < 1
    ):
        print("\nGame not found or invalid name. Please try again.")
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
                print(
                    "Invalid choice, please enter a number associated with one of the options available."
                )
        except ValueError:
            print("Invalid input, please enter a number.")
