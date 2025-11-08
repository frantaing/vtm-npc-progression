# tui/utils.py

import curses
import textwrap

# --- [UI CONSTANTS] ---
COLOR_GREEN = 1
COLOR_RED = 2
COLOR_YELLOW = 3
COLOR_CYAN = 4
COLOR_MAGENTA = 5

# --- [DRAWING HELPERS] ---

def draw_box(stdscr, y, x, height, width, title=""):
    """Draw a box with optional title."""
    stdscr.attron(curses.color_pair(COLOR_CYAN))
    for i in range(height):
        if i == 0: stdscr.addstr(y + i, x, "┌" + "─" * (width - 2) + "┐")
        elif i == height - 1: stdscr.addstr(y + i, x, "└" + "─" * (width - 2) + "┘")
        else: stdscr.addstr(y + i, x, "│" + " " * (width - 2) + "│")
    
    if title:
        stdscr.addstr(y, x + 2, f" {title} ", curses.color_pair(COLOR_YELLOW) | curses.A_BOLD)
    stdscr.attroff(curses.color_pair(COLOR_CYAN))

def draw_wrapped_text(stdscr, y, x, text, width, color_pair_num=1):
    """Draws text that wraps within a given width at a specified position."""
    color = curses.color_pair(color_pair_num)
    wrapped_lines = textwrap.wrap(text, width)
    for i, line in enumerate(wrapped_lines):
        stdscr.addstr(y + i, x, line, color)

def show_popup(stdscr, title: str, message: str, color: int = COLOR_RED):
    """Displays a modal pop-up and waits for a key press to dismiss."""
    h, w = stdscr.getmaxyx()
    
    wrapped_lines = textwrap.wrap(message, 40)
    dialog_height = len(wrapped_lines) + 4
    dialog_width = 50
    
    dialog_y = (h - dialog_height) // 2
    dialog_x = (w - dialog_width) // 2
    
    draw_box(stdscr, dialog_y, dialog_x, dialog_height, dialog_width, title)
    
    for i, line in enumerate(wrapped_lines):
        stdscr.addstr(dialog_y + 2 + i, dialog_x + 2, line, curses.color_pair(color))

    dismiss_msg = "Press any key to continue..."
    stdscr.addstr(dialog_y + dialog_height - 2, dialog_x + (dialog_width - len(dismiss_msg)) // 2, dismiss_msg, curses.color_pair(COLOR_YELLOW))
    
    stdscr.refresh()
    stdscr.getch()

# --- [INPUT HELPERS] ---

class QuitApplication(Exception):
    """Custom exception to signal a clean, immediate exit from the app."""
    pass

def get_string_input(stdscr, prompt: str, y: int, x: int, current_screen_func, *args, **kwargs) -> str:
    curses.curs_set(1)
    input_str = ""
    input_x_start = x + len(prompt)

    while True:
        current_screen_func(*args, **kwargs)
        stdscr.addstr(y, x, prompt, curses.color_pair(COLOR_YELLOW))
        stdscr.addstr(y, input_x_start, " " * 30)
        stdscr.addstr(y, input_x_start, input_str)
        stdscr.move(y, input_x_start + len(input_str))
        stdscr.refresh()

        key = stdscr.getch()

        if key == 24: raise QuitApplication()
        elif key in (curses.KEY_ENTER, ord('\n')) and input_str: break
        elif key in (curses.KEY_BACKSPACE, 127, 8): input_str = input_str[:-1]
        elif 32 <= key <= 126 and len(input_str) < 30: input_str += chr(key)
    
    curses.curs_set(0)
    return input_str.strip()

def get_number_input(stdscr, prompt: str, y: int, x: int, min_val: int, max_val: int, current_screen_func, *args, **kwargs):
    try:
        val_str = get_string_input(stdscr, prompt, y, x, current_screen_func, *args, **kwargs)
        val = int(val_str)
        if min_val <= val <= max_val:
            return val
        show_popup(stdscr, "Invalid Range", f"Please enter a number between {min_val} and {max_val}.")
        return None
    except ValueError:
        show_popup(stdscr, "Invalid Input", "That is not a valid number. Please try again.")
        return None