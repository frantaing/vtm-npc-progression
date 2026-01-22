# tui/theme.py

# This flle contains all colors and symbols of the app

import curses

# --- [SYMBOLS] ---

# Box borders
SYM_BORDER_H = "─"
SYM_BORDER_V = "│"
SYM_CORNER_TL = "┌"
SYM_CORNER_TR = "┐"
SYM_CORNER_BL = "└"
SYM_CORNER_BR = "┘"
SYM_HEADER_L = "═══ "
SYM_HEADER_R = " ═══"

SYM_POINTER = "► "
SYM_ARROW = "→" # Not used as much in the new view, but good to keep

# New indicators for selection
SYM_SELECTED_L = "< "
SYM_SELECTED_R = " >"

# --- [COLOR PAIR ID] ---

# These have to be initialize after curses starts...abs
_ID_TEXT = 1
_ID_ACCENT = 2
_ID_DIM = 3
_ID_ERROR = 4
_ID_HIGHLIGHT = 5 # NEW

def init_colors():
    """Initializes the curses color pairs. Must be called after stdscr is active."""
    # Pair 1: Standard Text (White on Black)
    curses.init_pair(_ID_TEXT, curses.COLOR_WHITE, curses.COLOR_BLACK)
    
    # Pair 2: Accent/Blood (Red on Black)
    curses.init_pair(_ID_ACCENT, curses.COLOR_RED, curses.COLOR_BLACK)
    
    # Pair 3: Dim/Stone (White on Black)
    curses.init_pair(_ID_DIM, curses.COLOR_WHITE, curses.COLOR_BLACK)
    
    # Pair 4: Error (Red on Black)
    curses.init_pair(_ID_ERROR, curses.COLOR_RED, curses.COLOR_BLACK)
    
    # NEW Pair 5: Highlight/Select (Gold/Yellow on Black)
    curses.init_pair(_ID_HIGHLIGHT, curses.COLOR_YELLOW, curses.COLOR_BLACK)

def apply_background(stdscr):
    """
    Sets the default background style for the entire window.
    Make sure the black background fills the whole screen, not just text.
    """
    stdscr.bkgd(' ', curses.color_pair(_ID_TEXT))

# --- [COLOR HELPERS] ---
# Return coorect curses attributes

def CLR_TEXT():
    """Standard text (Bone/Pale)"""
    return curses.color_pair(_ID_TEXT)

def CLR_ACCENT():
    """Primary Highlight (Blood Red)"""
    return curses.color_pair(_ID_ACCENT) | curses.A_BOLD

def CLR_BORDER():
    """UI Borders (Stone Grey)"""
    return curses.color_pair(_ID_DIM) | curses.A_DIM

def CLR_TITLE():
    """Headings/Titles (Bold Red)"""
    return curses.color_pair(_ID_ACCENT) | curses.A_BOLD | curses.A_UNDERLINE

def CLR_SELECTED():
    """Selected Menu Items (Inverse Red)"""
    return curses.color_pair(_ID_ACCENT) | curses.A_REVERSE

def CLR_ERROR():
    """Error messages"""
    return curses.color_pair(_ID_ERROR) | curses.A_BOLD
    
def CLR_HIGHLIGHT():
    """NEW: Gold/Yellow for the active cursor selection"""
    return curses.color_pair(_ID_HIGHLIGHT) | curses.A_BOLD