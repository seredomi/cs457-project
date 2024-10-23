import curses
from curses import wrapper

from src.client.display.welcome_prompt import new_connection_prompt

def initialize(stdscr):

    # set up colors
    # 1 = black on white (important text)
    curses.init_pair(1, 232, 255)
    # 2 = grey on white (subtext)
    curses.init_pair(2, 244, 255)
    # 3 = red on white (an option/button)
    curses.init_pair(3, 9, 255)
    # 4 = blue on white (currently selected option/button)
    curses.init_pair(4, 12, 255)
    # 5 = white on white (probably just for the background)
    curses.init_pair(5, 255, 255)

    # blank background, don't show cursor
    stdscr.bkgd(' ', curses.color_pair(5))
    curses.curs_set(0)

    # call the welcome prompt
    # maybe we actually want to call an intermediary to handle the connection
    new_connection_prompt(stdscr)

if __name__ == "__main__":
    # this wrapper handles setup and teardown of curses screen
    wrapper(initialize)
