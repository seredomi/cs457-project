from src.utils.display import print_header
from typing import List
import re

def new_connection_dialog(games_exist: bool = False):
    print_header("welcome to cs457 quiz game")
    print("select an option:")
    print("1. start a new game")
    if games_exist: print("2. join an existing game")
    print("3. exit")
    option = input("Enter the number of your choice: ")
    options = ['1', '3']
    if games_exist: options.append('2')
    if option not in options:
        print("\nInvalid choice. please try again.")
        return new_connection_dialog()
    return int(option)

def create_game_dialog(available_chapters: List[int] = [1, 2, 3], max_questions: int = 20, curr_games: List[str] = [], curr_players: List[str] = []):

    print_header("creating a new game")
    print("enter a player name. no spaces or funny characters allowed ")
    player_name = input()
    while not re.match("^[a-zA-Z0-9_]*$", player_name) or player_name in curr_players or len(player_name) < 1:
        print("\ninvalid player name. please try again.")
        return create_game_dialog(available_chapters, max_questions, curr_games)

    print("\nenter a game name. can't be a current game name. no spaces or funny characters allowed ")
    game_name = input()
    while not re.match("^[a-zA-Z0-9_]*$", game_name) or game_name in curr_games or len(game_name) < 1:
        print("\ninvalid game name. please try again.")
        game_name = input()

    print("\nselect chapters from the following list: " + " ".join([str(ch) for ch in available_chapters]))
    print("enter chapters as a space separated list (ex: '1 3')")
    chapters = []
    try: chapters = [int(ch) for ch in input().split()]
    except: pass
    while len(chapters) < 1 or (not all(ch in available_chapters for ch in chapters)):
        print("\ninvalid input. please try again.")
        try: chapters = [int(ch) for ch in input().split()]
        except: pass

    print(f"\nenter the total number of questions. max is {max_questions}")
    num_questions = 0
    try: num_questions = int(input())
    except: pass
    while num_questions < 1 or num_questions > max_questions:
        print("\ninvalid input. please try again.")
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

    print_header("joining an existing game")
    print("enter your player name. No spaces or special characters allowed:")
    player_name = input()
    while not re.match("^[a-zA-Z0-9_]*$", player_name) or player_name in curr_players or len(player_name) < 1:
        print("\ninvalid player name or name already taken. Please try again.")
        player_name = input()

    print(f"\nenter the game name to join. available games: {', '.join(curr_games)}")
    game_name = input()
    while not re.match("^[a-zA-Z0-9_]*$", game_name) or game_name not in curr_games or len(game_name) < 1:
        print("\nGame not found or invalid name. Please try again.")
        game_name = input()

    return {
        "message_type": "join_game",
        "player_name": player_name,
        "game_name": game_name,
    }
