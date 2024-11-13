from prompt_toolkit.shortcuts import input_dialog

def main_menu():
    return input_dialog(
        title="Main Menu",
        text="1. Create a new game\n2. Join a game\n3. Quit",
    ).run()
