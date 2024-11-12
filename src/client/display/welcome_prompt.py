import curses


def new_connection_prompt(stdscr):
    # predefine text and options
    title = "welcome to the cs 457 quiz game"
    subtitle = "navigate with arrow keys and enter"
    options = ["[s] [start a new game]", "[j] [join an existing game]", "[q] [quit]"]
    curr_option = 0

    # until enter is pressed
    while True:
        # clear the screen and display title and subtitle
        stdscr.clear()
        stdscr.addstr(1, 3, title, curses.color_pair(1))
        stdscr.addstr(2, 5, subtitle, curses.color_pair(2))

        # display options
        for i, option in enumerate(options):
            x = 5
            y = i + 4
            # color is blue if this is the current option
            color = curses.color_pair(4) if i == curr_option else curses.color_pair(3)
            stdscr.addstr(y, x, option, color)

        # await keypress
        key = stdscr.getch()
        # shortcuts
        if key == ord("s"):
            curr_option = 0
        elif key == ord("j"):
            curr_option = 1
        elif key == ord("q"):
            curr_option = 2
        # up and down arrows
        elif key == curses.KEY_UP and curr_option > 0:
            curr_option -= 1
        elif key == curses.KEY_DOWN and curr_option < len(options) - 1:
            curr_option += 1
        # enter. break the true loop to call the funcion
        elif key == curses.KEY_ENTER or key in [10, 13]:
            break

    show_selection(stdscr, options[curr_option])


# this will obviously get replaced with the next page, whatever that is
def show_selection(stdscr, option):
    stdscr.clear()
    stdscr.addstr(1, 3, f"you chose {option}", curses.color_pair(1))
    stdscr.addstr(2, 5, "press any key to exit", curses.color_pair(2))
    stdscr.getch()
    stdscr.refresh()
