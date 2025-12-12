# tui/utils.py

import curses
import textwrap
from . import theme

# --- [DRAWING HELPERS] ---
def draw_box(stdscr, y, x, height, width, title=""):
    """Draw a box with optional title using theme symbols."""
    stdscr.attron(theme.CLR_BORDER())
    for i in range(height):
        if i == 0:
            stdscr.addstr(y + i, x, theme.SYM_CORNER_TL + theme.SYM_BORDER_H * (width - 2) + theme.SYM_CORNER_TR)
        elif i == height - 1:
            stdscr.addstr(y + i, x, theme.SYM_CORNER_BL + theme.SYM_BORDER_H * (width - 2) + theme.SYM_CORNER_BR)
        else:
            stdscr.addstr(y + i, x, theme.SYM_BORDER_V + " " * (width - 2) + theme.SYM_BORDER_V)
    stdscr.attroff(theme.CLR_BORDER())
    
    if title:
        # Titles appear in Bold Red
        stdscr.addstr(y, x + 2, f" {title} ", theme.CLR_ACCENT())

def draw_wrapped_text(stdscr, y, x, text, width, color_attr=None):
    """Draws text that wraps within a given width."""
    if color_attr is None:
        color_attr = theme.CLR_TEXT()
        
    wrapped_lines = textwrap.wrap(text, width)
    for i, line in enumerate(wrapped_lines):
        stdscr.addstr(y + i, x, line, color_attr)

def show_popup(stdscr, title: str, message: str, color_attr=None):
    """Displays a modal pop-up."""
    if color_attr is None:
        color_attr = theme.CLR_ERROR()

    h, w = stdscr.getmaxyx()
    
    wrapped_lines = textwrap.wrap(message, 40)
    dialog_height = len(wrapped_lines) + 4
    dialog_width = 50
    
    dialog_y = (h - dialog_height) // 2
    dialog_x = (w - dialog_width) // 2
    
    draw_box(stdscr, dialog_y, dialog_x, dialog_height, dialog_width, title)
    
    for i, line in enumerate(wrapped_lines):
        stdscr.addstr(dialog_y + 2 + i, dialog_x + 2, line, color_attr)

    dismiss_msg = "Press any key to continue..."
    stdscr.addstr(dialog_y + dialog_height - 2, dialog_x + (dialog_width - len(dismiss_msg)) // 2, dismiss_msg, theme.CLR_TEXT())
    
    stdscr.refresh()
    stdscr.getch()

# --- [INPUT HELPERS] ---
class QuitApplication(Exception):
    pass

class InputCancelled(Exception):
    """Used when the user cancels an input (via ESC)"""
    pass

def get_string_input(stdscr, prompt: str, y: int, x: int, current_screen_func, *args, **kwargs) -> str:
    curses.curs_set(1)
    input_str = ""
    input_x_start = x + len(prompt)

    while True:
        current_screen_func(*args, **kwargs)
        stdscr.addstr(y, x, prompt, theme.CLR_ACCENT()) 
        stdscr.addstr(y, input_x_start, " " * 30)
        stdscr.addstr(y, input_x_start, input_str, theme.CLR_TEXT()) 
        stdscr.move(y, input_x_start + len(input_str))
        stdscr.refresh()

        key = stdscr.getch()

        if key == 24: raise QuitApplication() # Ctrl+X
        elif key == 27: raise InputCancelled() # Esc Key
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