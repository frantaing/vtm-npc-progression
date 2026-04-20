"""
tui/renderer.py

Shared rendering logic for the 3-column character sheet body.
Used by both MainView (interactive) and FinalView (static).
"""

import curses
from . import theme
from . import utils
from typing import NamedTuple

# --- [SHEET ITEM] ---
class SheetItem(NamedTuple):
    category: str
    name: str
    data: dict = {}

# --- [SINGLE TRAIT ROW] ---
def draw_trait_row(stdscr, y: int, x: int, name: str, data: dict, width: int, is_selected: bool = False, is_modified: bool = False, is_interactive: bool = False):
    """
    Renders a single trait row.

    In interactive mode (MainView):
      - Selected row gets gold highlight + < name [val] > brackets
      - Modified/dynamic traits (passed via is_modified) get CLR_ACCENT
    In static mode (FinalView):
      - Modified traits show [base]→[new] in CLR_ACCENT
      - Unmodified traits show [val] in CLR_TEXT
    """
    max_name_len = width - 9
    name_part = f"{name[:max_name_len]:<{max_name_len}}"

    if is_selected:
        val_str = f"[{data['new']}]"
        display_str = f"{theme.SYM_SELECTED_L}{name_part}{val_str}{theme.SYM_SELECTED_R}"
        stdscr.addstr(y, x - 2, display_str, theme.CLR_HIGHLIGHT())
    else:
        # Static mode (FinalView) shows arrows; Interactive shows current value
        if not is_interactive and data['base'] != data['new']:
            val_str = f"[{data['base']}]→[{data['new']}]"
        else:
            val_str = f"[{data['new']}]"
            
        display_str = f"{name_part}{val_str}"
        style = theme.CLR_ACCENT() if is_modified else theme.CLR_TEXT()
        stdscr.addstr(y, x, display_str, style)

# --- [SYSTEM/ADD ROW] ---
def draw_system_row(stdscr, y: int, x: int, name: str, width: int, is_selected: bool = False):
    """Renders an 'Add Discipline' / 'Add Background' action row."""
    text = f"[ {name} ]"
    if is_selected:
        display_str = f"{theme.SYM_SELECTED_L}{text:<{width - 4}}{theme.SYM_SELECTED_R}"
        stdscr.addstr(y, x - 2, display_str, theme.CLR_HIGHLIGHT())
    else:
        stdscr.addstr(y, x, text, theme.CLR_TEXT())

# --- [SINGLE COLUMN] ---
def draw_column(stdscr, start_y: int, start_x: int, width: int, items: list, col_idx: int, max_rows: int, active_col: int, active_row: int, is_interactive: bool = False, dynamic_categories: tuple = ()):
    """Renders one column of the character sheet."""
    scroll_offset = 0
    if is_interactive and active_col == col_idx:
        if active_row >= max_rows:
            scroll_offset = active_row - max_rows + 1

    for i in range(max_rows):
        idx = scroll_offset + i
        if idx >= len(items):
            break

        item = items[idx]
        row_y = start_y + i

        if item.category == "Spacer":
            continue

        if item.category == "Header":
            header_text = f"{theme.SYM_HEADER_L}{item.name}{theme.SYM_HEADER_R}"
            pad = (width - len(header_text)) // 2
            stdscr.addstr(row_y, start_x + max(0, pad), header_text[:width], theme.CLR_BORDER())
            continue

        is_selected = is_interactive and (active_col == col_idx) and (active_row == idx)

        if item.category == "System":
            draw_system_row(stdscr, row_y, start_x + 2, item.name, width, is_selected=is_selected)
            continue

        is_modified = item.data['base'] != item.data['new']
        if is_interactive and item.category in dynamic_categories:
            is_modified = True

        draw_trait_row(stdscr, row_y, start_x + 2, item.name, item.data, width, is_selected, is_modified, is_interactive)

# --- [CONTAINER + HEADER] ---
def draw_sheet_container(stdscr, character, title: str, freebie_str: str, freebie_color, container_width: int, container_height: int) -> dict:
    """
    Draws the outer box, character header block, and freebie line.
    Returns a layout dict ready to pass to draw_character_sheet_columns().

    Caller is responsible for formatting freebie_str and freebie_color.
    """
    h, w = stdscr.getmaxyx()
    start_x = (w - container_width) // 2
    start_y = (h - container_height) // 2

    utils.draw_box(stdscr, start_y, start_x, container_height, container_width, title)

    # Line 1: Name + Clan
    header_y = start_y + 1
    name_str = f"{character.name} ({character.clan})"
    stdscr.addstr(header_y, start_x + 2, name_str, theme.CLR_TITLE())

    # Line 2: Age + Gen + Max trait
    header_y += 1
    meta_str = f"Age: {character.age} | Gen: {character.generation}th | Max: {character.max_trait_rating}"
    stdscr.addstr(header_y, start_x + 2, meta_str, theme.CLR_ACCENT())

    # Line 3: Freebie points (caller-formatted)
    header_y += 1
    stdscr.addstr(header_y, start_x + 2, freebie_str, freebie_color)

    # Layout calculations for the sheet body
    col_width = (container_width - 4) // 3
    cx1 = start_x + 2
    cx2 = cx1 + col_width + 1
    cx3 = cx2 + col_width + 1
    content_y = header_y + 2

    return {
        "start_x":           start_x,
        "start_y":           start_y,
        "content_y":         content_y,
        "cx1":               cx1,
        "cx2":               cx2,
        "cx3":               cx3,
        "col_width":         col_width,
        "container_height":  container_height,
        "container_start_y": start_y,
    }

# --- [FULL 3-COLUMN SHEET] ---
def draw_character_sheet_columns(stdscr, character, col1_items: list, col2_items: list, col3_items: list, layout: dict, active_col: int = 0, active_row: int = 0, is_interactive: bool = False):
    """
    Draws the full 3-column character sheet body.

    layout dict expects:
        {
            "start_y":           int,
            "cx1":               int,
            "cx2":               int,
            "cx3":               int,
            "col_width":         int,
            "max_rows":          int,
            "container_height":  int,
            "container_start_y": int,
        }

    Items must be pre-resolved SheetItems (carrying their own data).
    """
    start_y          = layout["start_y"]
    cx1              = layout["cx1"]
    cx2              = layout["cx2"]
    cx3              = layout["cx3"]
    col_width        = layout["col_width"]
    max_rows         = layout["max_rows"]
    container_height  = layout["container_height"]
    container_start_y = layout["container_start_y"]

    # Draw vertical separators
    sep_start = start_y
    sep_end = container_start_y + container_height - 2
    for i in range(sep_start, sep_end):
        stdscr.addstr(i, cx2 - 1, theme.SYM_BORDER_V, theme.CLR_BORDER())
        stdscr.addstr(i, cx3 - 1, theme.SYM_BORDER_V, theme.CLR_BORDER())

    dynamic = ("Discipline", "Background")

    draw_column(stdscr, start_y, cx1, col_width, col1_items, 0, max_rows, active_col, active_row, is_interactive, dynamic)
    draw_column(stdscr, start_y, cx2, col_width, col2_items, 1, max_rows, active_col, active_row, is_interactive, dynamic)
    draw_column(stdscr, start_y, cx3, col_width, col3_items, 2, max_rows, active_col, active_row, is_interactive, dynamic)