#!/usr/bin/env python3

"""
vtm_tui.py

This module contains the UI for the tool. It handles all rendering and
user input, and uses on vtm_npc_logic.py for character management.
"""

# --- [IMPORTS] ---
import curses
import sys
import textwrap
from typing import Dict, Optional
from vtm_npc_logic import ( # Import from vtm_npc_logic.py
    VtMCharacter,
    ATTRIBUTES_LIST,
    ABILITIES_LIST,
    VIRTUES_LIST,
    FREEBIE_COSTS
)

# --- [EXIT] ---
class QuitApplication(Exception):
    """Custom exception to signal a clean, immediate exit from the app."""
    pass

# --- [TUI] ---
class TUIApp:
    """Manages the curses UI for character progression."""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.character: Optional[VtMCharacter] = None
        self.message = ""
        self.message_color = 1
        
        # Initialize colors
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        
        curses.curs_set(0)  # Hide cursor
        self.stdscr.keypad(True)

    def show_message(self, msg: str, color: int = 1):
        """Store a message to display at the bottom of the screen."""
        self.message = msg
        self.message_color = color

    def draw_box(self, y, x, height, width, title=""):
        """Draw a box with optional title."""
        self.stdscr.attron(curses.color_pair(4))
        for i in range(height):
            if i == 0:
                self.stdscr.addstr(y + i, x, "┌" + "─" * (width - 2) + "┐")
            elif i == height - 1:
                self.stdscr.addstr(y + i, x, "└" + "─" * (width - 2) + "┘")
            else:
                self.stdscr.addstr(y + i, x, "│" + " " * (width - 2) + "│")
        
        if title:
            title_str = f" {title} "
            self.stdscr.addstr(y, x + 2, title_str, curses.color_pair(3) | curses.A_BOLD)
        self.stdscr.attroff(curses.color_pair(4))

    def draw_wrapped_text(self, y, x, text, width, color_pair_num=1):
        """Draws text that wraps within a given width at a specified position."""
        color = curses.color_pair(color_pair_num)
        wrapped_lines = textwrap.wrap(text, width)
        for i, line in enumerate(wrapped_lines):
            self.stdscr.addstr(y + i, x, line, color)

    def get_string_input(self, prompt: str, y: int, x: int) -> str:
        """
        Get string input from the user, building it character by character.
        - Does not accept empty strings on Enter.
        - Raises QuitApplication if Ctrl+X is pressed.
        """
        curses.curs_set(1)
        
        input_str = ""
        input_x_start = x + len(prompt)

        while True:
            self.stdscr.addstr(y, x, prompt, curses.color_pair(3))
            self.stdscr.addstr(y, input_x_start, " " * 30)
            self.stdscr.addstr(y, input_x_start, input_str)
            self.stdscr.move(y, input_x_start + len(input_str))
            self.stdscr.refresh()

            key = self.stdscr.getch()

            if key == 24: # Ctrl+X
                raise QuitApplication()
            
            elif key in (curses.KEY_ENTER, ord('\n')):
                if input_str:
                    break
            
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                if input_str:
                    input_str = input_str[:-1]
            
            elif 32 <= key <= 126 and len(input_str) < 30:
                input_str += chr(key)
        
        curses.curs_set(0)
        return input_str.strip()

    def get_number_input(self, prompt: str, y: int, x: int, min_val: int, max_val: int) -> int:
        """Get validated number input from user. Loops until valid input is given."""
        while True:
            try:
                val_str = self.get_string_input(prompt, y, x)
                val = int(val_str)
                
                if min_val <= val <= max_val:
                    return val
                
                self.show_message(f"Please enter a number between {min_val} and {max_val}", 2)
                self.stdscr.refresh()
                curses.napms(1500)
            except ValueError:
                self.show_message("Invalid input. Please enter a number.", 2)
                self.stdscr.refresh()
                curses.napms(1500)

    def setup_character(self):
        """Initial character setup screen. Returns on completion, raises QuitApplication on exit."""
        h, w = self.stdscr.getmaxyx()
        
        container_width, container_height = 70, 18
        start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
        
        entered_info = {}
        prompts = [
            ("Character Name", "name", None, None), ("Clan", "clan", None, None),
            ("Age (0-5600+)", "age", 0, 10000), ("Generation (2-16)", "generation", 2, 16)
        ]
        
        for label, key, min_val, max_val in prompts:
            self.stdscr.clear()
            title = "VAMPIRE: THE MASQUERADE - NPC PROGRESSION TOOL"
            self.stdscr.addstr(start_y - 3, (w - len(title)) // 2, title, curses.color_pair(5) | curses.A_BOLD)
            self.draw_box(start_y, start_x, container_height, container_width, "Character Setup")
            
            list_y = start_y + 2
            for info_label, info_value in entered_info.items():
                self.stdscr.addstr(list_y, start_x + 2, f"{info_label}: {info_value}", curses.color_pair(1)); list_y += 1
            
            if min_val is not None:
                value = self.get_number_input(f"{label}: ", list_y, start_x + 2, min_val, max_val)
            else:
                value = self.get_string_input(f"{label}: ", list_y, start_x + 2)
            entered_info[label] = value
        
        self.character = VtMCharacter(
            entered_info["Character Name"], entered_info["Clan"],
            entered_info["Age (0-5600+)"], entered_info["Generation (2-16)"]
        )
        
        self.stdscr.clear()
        self.draw_box(start_y, start_x, container_height, container_width, "Character Created")
        list_y = start_y + 2
        for info_label, info_value in entered_info.items():
            self.stdscr.addstr(list_y, start_x + 2, f"{info_label}: {info_value}", curses.color_pair(1)); list_y += 1
        
        list_y += 1
        self.stdscr.addstr(list_y, start_x + 2, f"Character created with {self.character.total_freebies} Freebie Points!", curses.color_pair(1) | curses.A_BOLD)
        self.stdscr.addstr(list_y + 2, start_x + 2, "Press any key to set initial traits...", curses.color_pair(3))
        self.stdscr.refresh()
        if self.stdscr.getch() == 24: raise QuitApplication()

        self.setup_initial_traits()

    def setup_initial_traits(self):
        """Setup initial trait values with list display."""
        h, w = self.stdscr.getmaxyx()
        
        # Attributes
        entered_attrs = {}
        for attr in ATTRIBUTES_LIST:
            self.stdscr.clear()
            container_width, container_height = 60, 20
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
            self.draw_box(start_y, start_x, container_height, container_width, "Initial Attributes")
            self.stdscr.addstr(start_y + 2, start_x + 2, "Set initial attribute values (1-10)", curses.color_pair(3))
            list_y = start_y + 4
            for name, value in entered_attrs.items():
                self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(1)); list_y += 1
            val = self.get_number_input(f"{attr}: ", list_y, start_x + 2, 1, 10)
            entered_attrs[attr] = val
            self.character.set_initial_trait("attributes", attr, val)
        
        # Abilities
        entered_abils = {}
        for abil in ABILITIES_LIST:
            self.stdscr.clear()
            container_width, container_height = 60, min(40, h - 4)
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
            self.draw_box(start_y, start_x, container_height, container_width, "Initial Abilities")
            self.stdscr.addstr(start_y + 2, start_x + 2, "Set initial ability values (0-10)", curses.color_pair(3))
            list_y = start_y + 4
            max_display = container_height - 8
            start_idx = max(0, len(entered_abils) - max_display + 1)
            for name, value in list(entered_abils.items())[start_idx:]:
                if list_y >= start_y + container_height - 4: break
                self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(1)); list_y += 1
            val = self.get_number_input(f"{abil}: ", list_y, start_x + 2, 0, 10)
            entered_abils[abil] = val
            self.character.set_initial_trait("abilities", abil, val)
        
        # Disciplines & Backgrounds
        for trait_type in ["Disciplines", "Backgrounds"]:
            entered_items = {}
            while True:
                self.stdscr.clear()
                container_width, container_height = 60, 25
                start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
                self.draw_box(start_y, start_x, container_height, container_width, f"Initial {trait_type}")
                self.stdscr.addstr(start_y + 2, start_x + 2, "Enter names, or type 'done' to finish", curses.color_pair(3))
                list_y = start_y + 4
                for name, value in entered_items.items():
                    self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(1)); list_y += 1
                item_name = self.get_string_input(f"{trait_type[:-1]} Name: ", list_y, start_x + 2)
                if item_name.lower() == 'done': break
                val = self.get_number_input("  Value: ", list_y + 1, start_x + 2, 1, 10)
                entered_items[item_name] = val
                self.character.set_initial_trait(trait_type.lower(), item_name, val)
        
        # Virtues
        entered_virtues = {}
        for virtue in VIRTUES_LIST:
            self.stdscr.clear()
            container_width, container_height = 60, 15
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
            self.draw_box(start_y, start_x, container_height, container_width, "Virtues & Path")
            self.stdscr.addstr(start_y + 2, start_x + 2, "Set virtue values (1-10)", curses.color_pair(3))
            list_y = start_y + 4
            for name, value in entered_virtues.items():
                self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(1)); list_y += 1
            val = self.get_number_input(f"{virtue}: ", list_y, start_x + 2, 1, 10)
            entered_virtues[virtue] = val
            self.character.set_initial_trait("virtues", virtue, val)
        
        # Humanity and Willpower
        self.stdscr.clear()
        container_width, container_height = 60, 15
        start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
        self.draw_box(start_y, start_x, container_height, container_width, "Final Values")
        list_y = start_y + 2
        for name, value in entered_virtues.items():
            self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(1)); list_y += 1
        humanity = self.get_number_input("Humanity/Path: ", list_y + 1, start_x + 2, 1, 10)
        self.character.set_initial_value("humanity", humanity)
        willpower = self.get_number_input("Willpower: ", list_y + 2, start_x + 2, 1, 10)
        self.character.set_initial_value("willpower", willpower)

    def display_character_sheet(self, y: int, x: int, width: int, height: int):
        """Displays character sheet with a dynamic two-column layout."""
        self.stdscr.addstr(y, x, f"{self.character.name} ({self.character.clan})"[:width], curses.color_pair(5) | curses.A_BOLD); y += 1
        self.stdscr.addstr(y, x, f"Age: {self.character.age} | Gen: {self.character.generation}th | Max: {self.character.max_trait_rating}"[:width], curses.color_pair(3)); y += 1
        remaining = self.character.total_freebies - self.character.spent_freebies
        self.stdscr.addstr(y, x, f"Freebie: {remaining}/{self.character.total_freebies}", (curses.color_pair(1) if remaining > 0 else curses.color_pair(2)) | curses.A_BOLD); y += 2

        start_y, max_y = y, y + height
        col1_x, col_width = x, 28
        col2_x = x + col_width + 2

        y_left = start_y
        self.stdscr.addstr(y_left, col1_x, "═══ ATTRIBUTES ═══", curses.color_pair(4) | curses.A_BOLD); y_left += 1
        for name, data in self.character.attributes.items():
            if y_left > max_y: break
            self.display_trait(y_left, col1_x, name, data, col_width); y_left += 1
        y_left += 1
        if y_left <= max_y:
            self.stdscr.addstr(y_left, col1_x, "═══ ABILITIES ═══", curses.color_pair(4) | curses.A_BOLD); y_left += 1
            abilities_shown = [(n, d) for n, d in self.character.abilities.items() if d['new'] > 0]
            for name, data in abilities_shown:
                if y_left > max_y: break
                self.display_trait(y_left, col1_x, name, data, col_width); y_left += 1

        y_right = start_y
        for cat_name in ["disciplines", "backgrounds"]:
            category = getattr(self.character, cat_name)
            if category and y_right <= max_y:
                self.stdscr.addstr(y_right, col2_x, f"═══ {cat_name.upper()} ═══", curses.color_pair(4) | curses.A_BOLD); y_right += 1
                for name, data in category.items():
                    if y_right > max_y: break
                    self.display_trait(y_right, col2_x, name, data, col_width); y_right += 1
                y_right += 1
        
        if y_right <= max_y:
            self.stdscr.addstr(y_right, col2_x, "═══ VIRTUES & PATH ═══", curses.color_pair(4) | curses.A_BOLD); y_right += 1
            for name, data in self.character.virtues.items():
                if y_right > max_y: break
                self.display_trait(y_right, col2_x, name, data, col_width); y_right += 1
            if y_right <= max_y: self.display_trait(y_right, col2_x, "Humanity", self.character.humanity, col_width); y_right += 1
            if y_right <= max_y: self.display_trait(y_right, col2_x, "Willpower", self.character.willpower, col_width)

    def display_trait(self, y: int, x: int, name: str, data: Dict, width: int):
        max_name_len = width - 9
        name_part = f"{name[:max_name_len]:<{max_name_len}}"
        if data['base'] == data['new']:
            trait_str = f"{name_part} [{data['new']}]"
            self.stdscr.addstr(y, x, trait_str[:width])
        else:
            trait_str = f"{name_part} [{data['base']}]→[{data['new']}]"
            self.stdscr.addstr(y, x, trait_str[:width], curses.color_pair(1))

    def main_menu(self):
        """Main menu loop. Returns when user presses Ctrl+X."""
        selected = 0
        menu_items = [
            ("Attributes", "Attribute"), ("Abilities", "Ability"), ("Disciplines", "Discipline"),
            ("Backgrounds", "Background"), ("Virtues", "Virtue"), ("Humanity/Path", "Humanity"),
            ("Willpower", "Willpower"),
        ]
        
        while True:
            h, w = self.stdscr.getmaxyx()
            self.stdscr.clear()

            container_width = min(110, w - 4)
            container_height = min(50, h - 6)
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
            
            self.draw_box(start_y, start_x, container_height, container_width, "VTM Elder Creator")
            
            right_panel_width = 32
            left_panel_width = container_width - right_panel_width - 5
            panel_content_height = container_height - 6

            self.display_character_sheet(start_y + 2, start_x + 2, left_panel_width, panel_content_height)
            
            for i in range(1, container_height - 1):
                self.stdscr.addstr(start_y + i, start_x + left_panel_width + 2, "│", curses.color_pair(4))
            
            right_x, menu_y = start_x + left_panel_width + 4, start_y + 2
            
            self.stdscr.addstr(menu_y, right_x, "SPEND FREEBIE POINTS", curses.color_pair(3) | curses.A_BOLD); menu_y += 2
            
            for i, (label, category) in enumerate(menu_items):
                prefix = "► " if i == selected else "  "
                menu_str = f"{prefix}{label} (Cost: {FREEBIE_COSTS.get(category, 'N/A')}/dot)"
                self.stdscr.addstr(menu_y + i, right_x, menu_str[:right_panel_width], curses.A_REVERSE if i == selected else curses.A_NORMAL)
            
            if self.message:
                msg_y = start_y + container_height - 2
                wrapped_lines = textwrap.wrap(self.message, right_panel_width)
                msg_start_y = msg_y - (len(wrapped_lines) - 1)
                self.draw_wrapped_text(msg_start_y, right_x, self.message, right_panel_width, self.message_color)
            
            controls = "↑/↓: Navigate | Enter: Select | Ctrl+X: Finalize & Exit"
            self.stdscr.addstr(h - 1, (w - len(controls)) // 2, controls, curses.color_pair(3))
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            if key == 24: return
            elif key == curses.KEY_RESIZE: self.message = ""
            elif key == curses.KEY_UP: selected = (selected - 1 + len(menu_items)) % len(menu_items); self.message = ""
            elif key == curses.KEY_DOWN: selected = (selected + 1) % len(menu_items); self.message = ""
            elif key == ord('\n'): self.handle_improvement_menu(menu_items[selected][0], menu_items[selected][1])

    def handle_improvement_menu(self, label: str, category: str):
        if category in ["Humanity", "Willpower"]:
            self.improve_single_trait(category, "Humanity/Path" if category == "Humanity" else "Willpower"); return
        
        trait_list_map = { "Attribute": ATTRIBUTES_LIST, "Ability": ABILITIES_LIST, "Discipline": list(self.character.disciplines.keys()), "Background": list(self.character.backgrounds.keys()), "Virtue": VIRTUES_LIST }
        trait_list = trait_list_map.get(category, [])
        selected, scroll_offset = 0, 0
        can_add = category in ["Discipline", "Background"]

        while True:
            h, w = self.stdscr.getmaxyx()
            self.stdscr.clear()
            container_width = min(110, w - 4); container_height = min(50, h - 6)
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
            
            right_panel_width = 32
            left_panel_width = container_width - right_panel_width - 5
            panel_content_height = container_height - 6

            self.draw_box(start_y, start_x, container_height, container_width, f"Improve {label}")
            self.display_character_sheet(start_y + 2, start_x + 2, left_panel_width, panel_content_height)
            
            for i in range(1, container_height - 1):
                self.stdscr.addstr(start_y + i, start_x + left_panel_width + 2, "│", curses.color_pair(4))

            right_x, menu_y = start_x + left_panel_width + 4, start_y + 2
            
            self.stdscr.addstr(menu_y, right_x, f"Available: {self.character.total_freebies - self.character.spent_freebies} points", curses.color_pair(1) | curses.A_BOLD); menu_y += 2
            
            max_display_items = container_height - 12
            if selected < scroll_offset: scroll_offset = selected
            if selected >= scroll_offset + max_display_items: scroll_offset = selected - max_display_items + 1

            display_list = trait_list + (["** Add New **"] if can_add else [])
            for i in range(max_display_items):
                idx = scroll_offset + i
                if idx >= len(display_list): break
                trait_name = display_list[idx]
                prefix = "► " if idx == selected else "  "
                if trait_name == "** Add New **": trait_str = f"{prefix}{trait_name}"
                else:
                    current = self.character.get_trait_data(category, trait_name)['new']
                    trait_str = f"{prefix}{trait_name[:18]:<18} [{current}]"
                self.stdscr.addstr(menu_y + i, right_x, trait_str[:right_panel_width], curses.A_REVERSE if idx == selected else curses.A_NORMAL)

            if self.message:
                msg_y = start_y + container_height - 2
                wrapped_lines = textwrap.wrap(self.message, right_panel_width)
                msg_start_y = msg_y - (len(wrapped_lines) - 1)
                self.draw_wrapped_text(msg_start_y, right_x, self.message, right_panel_width, self.message_color)
            
            self.stdscr.addstr(h - 1, (w - len("placeholder"))//2, "↑/↓: Navigate | Enter: Improve | Esc: Back", curses.color_pair(3))
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            if key == 24: raise QuitApplication()
            elif key == curses.KEY_RESIZE: self.message = ""
            elif key == curses.KEY_UP: selected = (selected - 1 + len(display_list)) % len(display_list); self.message = ""
            elif key == curses.KEY_DOWN: selected = (selected + 1) % len(display_list); self.message = ""
            elif key == ord('\n'):
                if can_add and selected == len(trait_list):
                    new_name = self.get_string_input("New name: ", start_y + container_height - 3, start_x + 2)
                    if new_name and new_name.lower() != 'done':
                        self.character.set_initial_trait(category.lower() + 's', new_name, 0)
                        trait_list.append(new_name)
                        self.improve_single_trait(category, new_name)
                elif selected < len(trait_list): self.improve_single_trait(category, trait_list[selected])
            elif key == 27: self.message = ""; return

    def improve_single_trait(self, category: str, trait_name: str):
        current = self.character.get_trait_data(category, trait_name)['new']
        max_val = self.character.max_trait_rating
        if current >= max_val: self.show_message(f"{trait_name} is already at maximum ({max_val})", 2); return
        
        h, w = self.stdscr.getmaxyx()
        dialog_width, dialog_height = 50, 8
        dialog_x, dialog_y = (w - dialog_width) // 2, (h - dialog_height) // 2
        
        self.draw_box(dialog_y, dialog_x, dialog_height, dialog_width, "Improve Trait")
        self.stdscr.addstr(dialog_y + 2, dialog_x + 2, f"Trait: {trait_name}", curses.color_pair(3))
        self.stdscr.addstr(dialog_y + 3, dialog_x + 2, f"Current: [{current}]", curses.color_pair(1))
        self.stdscr.addstr(dialog_y + 4, dialog_x + 2, f"Max: {max_val}", curses.color_pair(3))
        
        target = self.get_number_input(f"New value ({current+1}-{max_val}): ", dialog_y + 5, dialog_x + 2, current + 1, max_val)
        success, msg = self.character.improve_trait(category, trait_name, target)
        self.show_message(msg, 1 if success else 2)

    def run(self):
        """Main application orchestrator."""
        try:
            self.setup_character()
        except QuitApplication:
            return

        self.main_menu()
        self.show_final_sheet()

    def show_final_sheet(self):
        """Display the final character sheet before exiting."""
        while True:
            self.stdscr.clear()
            h, w = self.stdscr.getmaxyx()
            container_width = min(110, w - 4)
            container_height = min(55, h - 6)
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
            
            self.draw_box(start_y, start_x, container_height, container_width, "FINAL CHARACTER SHEET")
            
            sheet_y, sheet_x = start_y + 2, start_x + 2
            
            self.stdscr.addstr(sheet_y, sheet_x, f"{self.character.name} ({self.character.clan})", curses.color_pair(5) | curses.A_BOLD); sheet_y += 1
            self.stdscr.addstr(sheet_y, sheet_x, f"Age: {self.character.age} | Gen: {self.character.generation}th | Max: {self.character.max_trait_rating}", curses.color_pair(3)); sheet_y += 1
            remaining = self.character.total_freebies - self.character.spent_freebies
            spent_str = f"Freebie Points: {self.character.spent_freebies}/{self.character.total_freebies} spent" + (f" ({remaining} remaining)" if remaining > 0 else "")
            self.stdscr.addstr(sheet_y, sheet_x, spent_str, (curses.color_pair(1) if remaining == 0 else curses.color_pair(3)) | curses.A_BOLD); sheet_y += 2
            
            panel_width = container_width - 4
            panel_height = container_height - 8
            self.display_character_sheet(sheet_y, sheet_x, panel_width, panel_height)

            exit_msg = "Press any key to exit the program..."
            self.stdscr.addstr(start_y + container_height - 2, start_x + (container_width - len(exit_msg)) // 2, exit_msg, curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.refresh()
            
            if self.stdscr.getch() != curses.KEY_RESIZE:
                return

# --- [APP] ---
def main(stdscr):
    """The main entry point for the curses application."""
    app = TUIApp(stdscr)
    app.run()

# --- [MAIN] ---
if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except QuitApplication:
        print("\nExiting program. Goodbye!")
    except KeyboardInterrupt:
        print("\nExiting program. Goodbye!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        input(f"\nAn error occurred: {e}. Press Enter to exit.")