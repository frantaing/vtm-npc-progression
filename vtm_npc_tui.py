#!/usr/bin/env python3

"""
vtm_tui.py

This module contains the UI for the tool. It handles all rendering and
user input, and uses on vtm_npc_logic.py for character management.
"""

# --- [IMPORTS] ---
import curses
import sys
from typing import Dict, Optional
from vtm_npc_logic import ( # Import from vtm_npc_logic.py
    VtMCharacter,
    ATTRIBUTES_LIST,
    ABILITIES_LIST,
    VIRTUES_LIST
)

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

    def get_string_input(self, prompt: str, y: int, x: int) -> str:
        """Get string input from user."""
        curses.echo()
        curses.curs_set(1)
        self.stdscr.addstr(y, x, prompt, curses.color_pair(3))
        self.stdscr.refresh()
        result = self.stdscr.getstr(y, x + len(prompt), 30).decode('utf-8').strip()
        curses.noecho()
        curses.curs_set(0)
        return result

    def get_number_input(self, prompt: str, y: int, x: int, min_val: int, max_val: int) -> Optional[int]:
        """Get validated number input from user."""
        while True:
            try:
                val_str = self.get_string_input(prompt, y, x)
                if not val_str:
                    return None
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

    def setup_character(self) -> bool:
        """Initial character setup screen."""
        h, w = self.stdscr.getmaxyx()
        
        container_width = 70
        container_height = 18
        start_x = (w - container_width) // 2
        start_y = (h - container_height) // 2
        
        entered_info = {}
        prompts = [
            ("Character Name", "name", None, None),
            ("Clan", "clan", None, None),
            ("Age (0-5600+)", "age", 0, 10000),
            ("Generation (2-16)", "generation", 2, 16)
        ]
        
        for i, (label, key, min_val, max_val) in enumerate(prompts):
            self.stdscr.clear()
            
            title = "VAMPIRE: THE MASQUERADE - NPC PROGRESSION TOOL"
            self.stdscr.addstr(start_y - 3, (w - len(title)) // 2, title, curses.color_pair(5) | curses.A_BOLD)
            
            self.draw_box(start_y, start_x, container_height, container_width, "Character Setup")
            
            list_y = start_y + 2
            for info_label, info_value in entered_info.items():
                self.stdscr.addstr(list_y, start_x + 2, f"{info_label}: {info_value}", curses.color_pair(1))
                list_y += 1
            
            if min_val is not None:
                value = self.get_number_input(f"{label}: ", list_y, start_x + 2, min_val, max_val)
                if value is None: return False
            else:
                value = self.get_string_input(f"{label}: ", list_y, start_x + 2)
                if not value: return False
            
            entered_info[label] = value
        
        self.character = VtMCharacter(
            entered_info["Character Name"],
            entered_info["Clan"],
            entered_info["Age (0-5600+)"],
            entered_info["Generation (2-16)"]
        )
        
        self.stdscr.clear()
        self.draw_box(start_y, start_x, container_height, container_width, "Character Created")
        
        list_y = start_y + 2
        for info_label, info_value in entered_info.items():
            self.stdscr.addstr(list_y, start_x + 2, f"{info_label}: {info_value}", curses.color_pair(1))
            list_y += 1
        
        list_y += 1
        freebie_msg = f"Character created with {self.character.total_freebies} Freebie Points!"
        self.stdscr.addstr(list_y, start_x + 2, freebie_msg, curses.color_pair(1) | curses.A_BOLD)
        
        list_y += 2
        self.stdscr.addstr(list_y, start_x + 2, "Press any key to set initial traits...", curses.color_pair(3))
        self.stdscr.refresh()
        self.stdscr.getch()
        
        if not self.setup_initial_traits():
            return False
        
        return True

    def setup_initial_traits(self) -> bool:
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
                self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(1))
                list_y += 1
            
            val = self.get_number_input(f"{attr}: ", list_y, start_x + 2, 1, 10)
            if val is None: return False
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
                self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(1))
                list_y += 1
            
            val = self.get_number_input(f"{abil}: ", list_y, start_x + 2, 0, 10)
            if val is None: return False
            entered_abils[abil] = val
            self.character.set_initial_trait("abilities", abil, val)
        
        # Disciplines & Backgrounds (Loops)
        for trait_type in ["Disciplines", "Backgrounds"]:
            entered_items = {}
            while True:
                self.stdscr.clear()
                container_width, container_height = 60, 25
                start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
                
                self.draw_box(start_y, start_x, container_height, container_width, f"Initial {trait_type}")
                self.stdscr.addstr(start_y + 2, start_x + 2, f"Enter {trait_type.lower()} (empty name when done)", curses.color_pair(3))
                
                list_y = start_y + 4
                for name, value in entered_items.items():
                    self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(1))
                    list_y += 1
                
                item_name = self.get_string_input(f"{trait_type[:-1]} Name: ", list_y, start_x + 2)
                if not item_name: break
                
                val = self.get_number_input("  Value: ", list_y + 1, start_x + 2, 1, 10)
                if val is None: continue
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
                self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(1))
                list_y += 1
            
            val = self.get_number_input(f"{virtue}: ", list_y, start_x + 2, 1, 10)
            if val is None: return False
            entered_virtues[virtue] = val
            self.character.set_initial_trait("virtues", virtue, val)
        
        # Humanity and Willpower
        self.stdscr.clear()
        container_width, container_height = 60, 15
        start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
        
        self.draw_box(start_y, start_x, container_height, container_width, "Final Values")
        
        list_y = start_y + 2
        for name, value in entered_virtues.items():
            self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(1))
            list_y += 1
        
        list_y += 1
        humanity = self.get_number_input("Humanity/Path: ", list_y, start_x + 2, 1, 10)
        if humanity is None: return False
        self.character.set_initial_value("humanity", humanity)
        
        willpower = self.get_number_input("Willpower: ", list_y + 1, start_x + 2, 1, 10)
        if willpower is None: return False
        self.character.set_initial_value("willpower", willpower)
        
        return True

    def display_character_sheet(self, y: int, x: int, width: int):
        """Display the character sheet in a container."""
        start_y = y
        
        # Header
        header = f"{self.character.name} ({self.character.clan})"
        self.stdscr.addstr(y, x, header[:width], curses.color_pair(5) | curses.A_BOLD)
        y += 1
        
        info = f"Age: {self.character.age} | Gen: {self.character.generation}th | Max: {self.character.max_trait_rating}"
        self.stdscr.addstr(y, x, info[:width], curses.color_pair(3))
        y += 1
        
        remaining = self.character.total_freebies - self.character.spent_freebies
        freebie_str = f"Freebie: {remaining}/{self.character.total_freebies}"
        color = curses.color_pair(1) if remaining > 0 else curses.color_pair(2)
        self.stdscr.addstr(y, x, freebie_str, color | curses.A_BOLD)
        y += 2
        
        # Attributes
        self.stdscr.addstr(y, x, "═══ ATTRIBUTES ═══", curses.color_pair(4) | curses.A_BOLD)
        y += 1
        for name, data in self.character.attributes.items():
            if y >= start_y + 40: break
            self.display_trait(y, x, name, data, width)
            y += 1
        y += 1
        
        # Abilities (show only non-zero)
        self.stdscr.addstr(y, x, "═══ ABILITIES ═══", curses.color_pair(4) | curses.A_BOLD)
        y += 1
        abilities_shown = [(name, data) for name, data in self.character.abilities.items() if data['new'] > 0]
        for name, data in abilities_shown[:8]:
            if y >= start_y + 40: break
            self.display_trait(y, x, name, data, width)
            y += 1
        y += 1
        
        # Other categories
        for category in ["disciplines", "backgrounds"]:
            if getattr(self.character, category):
                self.stdscr.addstr(y, x, f"═══ {category.upper()} ═══", curses.color_pair(4) | curses.A_BOLD)
                y += 1
                for name, data in getattr(self.character, category).items():
                    if y >= start_y + 40: break
                    self.display_trait(y, x, name, data, width)
                    y += 1
                y += 1

        # Virtues
        self.stdscr.addstr(y, x, "═══ VIRTUES & PATH ═══", curses.color_pair(4) | curses.A_BOLD)
        y += 1
        for name, data in self.character.virtues.items():
            self.display_trait(y, x, name, data, width)
            y += 1
        self.display_trait(y, x, "Humanity", self.character.humanity, width)
        y += 1
        self.display_trait(y, x, "Willpower", self.character.willpower, width)

    def display_trait(self, y: int, x: int, name: str, data: Dict, width: int = 30):
        """Display a single trait with progression."""
        if data['base'] == data['new']:
            trait_str = f"{name[:15]:<15} [{data['new']}]"
            self.stdscr.addstr(y, x, trait_str[:width])
        else:
            trait_str = f"{name[:15]:<15} [{data['base']}] -> {{{data['new']}}}"
            self.stdscr.addstr(y, x, trait_str[:width], curses.color_pair(1))

    def main_menu(self):
        """Main menu for spending freebie points with split view."""
        selected = 0
        menu_items = [
            ("Attributes", "Attribute"), ("Abilities", "Ability"),
            ("Disciplines", "Discipline"), ("Backgrounds", "Background"),
            ("Virtues", "Virtue"), ("Humanity/Path", "Humanity"),
            ("Willpower", "Willpower"),
        ]
        
        while True:
            h, w = self.stdscr.getmaxyx()
            self.stdscr.clear()

            container_width = min(100, w - 10)
            container_height = min(50, h - 6)
            start_x = (w - container_width) // 2
            start_y = (h - container_height) // 2
            
            left_width = 35
            right_width = container_width - left_width - 3
            
            self.draw_box(start_y, start_x, container_height, container_width, "VTM Elder Creator")
            
            self.display_character_sheet(start_y + 2, start_x + 2, left_width)
            
            for i in range(1, container_height - 1):
                self.stdscr.addstr(start_y + i, start_x + left_width + 2, "│", curses.color_pair(4))
            
            right_x = start_x + left_width + 4
            menu_y = start_y + 2
            
            self.stdscr.addstr(menu_y, right_x, "SPEND FREEBIE POINTS", curses.color_pair(3) | curses.A_BOLD)
            menu_y += 2
            
            from vtm_logic import FREEBIE_COSTS
            for i, (label, category) in enumerate(menu_items):
                if menu_y >= start_y + container_height - 2: break
                cost = FREEBIE_COSTS.get(category, "N/A")
                prefix = "► " if i == selected else "  "
                menu_str = f"{prefix}{label} (Cost: {cost}/dot)"
                attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
                self.stdscr.addstr(menu_y + i, right_x, menu_str[:right_width], attr)
            
            if self.message:
                self.stdscr.addstr(start_y + container_height - 2, start_x + 2, self.message[:container_width-4], curses.color_pair(self.message_color))
            
            controls = "↑/↓: Navigate | Enter: Select | Ctrl+Q: Finalize & Exit"
            self.stdscr.addstr(h - 1, (w - len(controls)) // 2, controls, curses.color_pair(3))
            
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            
            if key == curses.KEY_RESIZE:
                self.message = ""
                continue
            elif key == curses.KEY_UP:
                selected = (selected - 1 + len(menu_items)) % len(menu_items)
                self.message = ""
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(menu_items)
                self.message = ""
            elif key == ord('\n'):
                self.handle_improvement_menu(menu_items[selected][0], menu_items[selected][1])
            elif key == 17:  # Ctrl+Q
                return

    def handle_improvement_menu(self, label: str, category: str):
        """Handle improvement of a specific category with split view."""
        trait_list_map = {
            "Attribute": ATTRIBUTES_LIST, "Ability": ABILITIES_LIST,
            "Discipline": list(self.character.disciplines.keys()),
            "Background": list(self.character.backgrounds.keys()),
            "Virtue": VIRTUES_LIST,
        }
        if category in ["Humanity", "Willpower"]:
            self.improve_single_trait(category, "Humanity/Path" if category == "Humanity" else "Willpower")
            return
        
        trait_list = trait_list_map.get(category, [])
        selected, scroll_offset = 0, 0
        can_add = category in ["Discipline", "Background"]

        while True:
            h, w = self.stdscr.getmaxyx()
            self.stdscr.clear()

            container_width = min(100, w - 10)
            container_height = min(50, h - 6)
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
            
            left_width = 35
            
            self.draw_box(start_y, start_x, container_height, container_width, f"Improve {label}")
            self.display_character_sheet(start_y + 2, start_x + 2, left_width)
            
            for i in range(1, container_height - 1):
                self.stdscr.addstr(start_y + i, start_x + left_width + 2, "│", curses.color_pair(4))

            right_x = start_x + left_width + 4
            menu_y = start_y + 2
            
            remaining = self.character.total_freebies - self.character.spent_freebies
            self.stdscr.addstr(menu_y, right_x, f"Available: {remaining} points", curses.color_pair(1) | curses.A_BOLD)
            menu_y += 2
            
            max_display_items = container_height - 10
            if selected < scroll_offset: scroll_offset = selected
            if selected >= scroll_offset + max_display_items: scroll_offset = selected - max_display_items + 1

            display_list = trait_list + (["** Add New **"] if can_add else [])
            for i in range(max_display_items):
                idx = scroll_offset + i
                if idx >= len(display_list): break
                
                trait_name = display_list[idx]
                prefix = "► " if idx == selected else "  "
                
                if trait_name == "** Add New **":
                    trait_str = f"{prefix}{trait_name}"
                else:
                    current = self.character.get_trait_data(category, trait_name)['new']
                    trait_str = f"{prefix}{trait_name[:18]:<18} [{current}]"
                
                attr = curses.A_REVERSE if idx == selected else curses.A_NORMAL
                self.stdscr.addstr(menu_y + i, right_x, trait_str, attr)

            if self.message:
                self.stdscr.addstr(start_y + container_height - 2, start_x + 2, self.message, curses.color_pair(self.message_color))
            
            controls = "↑/↓: Navigate | Enter: Improve | Esc: Back"
            self.stdscr.addstr(h - 1, (w - len(controls)) // 2, controls, curses.color_pair(3))
            
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            
            if key == curses.KEY_RESIZE:
                self.message = ""
                continue
            elif key == curses.KEY_UP:
                selected = (selected - 1 + len(display_list)) % len(display_list)
                self.message = ""
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(display_list)
                self.message = ""
            elif key == ord('\n'):
                if can_add and selected == len(trait_list):
                    new_name = self.get_string_input("New name: ", start_y + container_height - 3, start_x + 2)
                    if new_name:
                        self.character.set_initial_trait(category.lower(), new_name, 0)
                        trait_list.append(new_name)
                        self.improve_single_trait(category, new_name)
                elif selected < len(trait_list):
                    self.improve_single_trait(category, trait_list[selected])
            elif key == 27:  # Escape
                self.message = ""
                return

    def improve_single_trait(self, category: str, trait_name: str):
        """Improve a single trait with centered input dialog."""
        trait_data = self.character.get_trait_data(category, trait_name)
        current = trait_data['new']
        max_val = self.character.max_trait_rating
        
        if current >= max_val:
            self.show_message(f"{trait_name} is already at maximum ({max_val})", 2)
            return
        
        h, w = self.stdscr.getmaxyx()
        
        dialog_width, dialog_height = 50, 8
        dialog_x, dialog_y = (w - dialog_width) // 2, (h - dialog_height) // 2
        
        self.draw_box(dialog_y, dialog_x, dialog_height, dialog_width, "Improve Trait")
        
        self.stdscr.addstr(dialog_y + 2, dialog_x + 2, f"Trait: {trait_name}", curses.color_pair(3))
        self.stdscr.addstr(dialog_y + 3, dialog_x + 2, f"Current: [{current}]", curses.color_pair(1))
        self.stdscr.addstr(dialog_y + 4, dialog_x + 2, f"Max: {max_val}", curses.color_pair(3))
        
        prompt = f"New value ({current+1}-{max_val}): "
        target = self.get_number_input(prompt, dialog_y + 5, dialog_x + 2, current + 1, max_val)
        
        if target is not None:
            success, msg = self.character.improve_trait(category, trait_name, target)
            self.show_message(msg, 1 if success else 2)

    def run(self):
        """Main application loop."""
        if not self.setup_character():
            return
        
        self.main_menu()
        self.show_final_sheet()

    def show_final_sheet(self):
        """Display the final character sheet before exiting."""
        while True:
            self.stdscr.clear()
            h, w = self.stdscr.getmaxyx()

            container_width = min(90, w - 10)
            container_height = min(55, h - 6)
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
            
            self.draw_box(start_y, start_x, container_height, container_width, "FINAL CHARACTER SHEET")
            
            sheet_x, sheet_y = start_x + 2, start_y + 2
            
            self.stdscr.addstr(sheet_y, sheet_x, f"{self.character.name} ({self.character.clan})", curses.color_pair(5) | curses.A_BOLD)
            sheet_y += 1
            self.stdscr.addstr(sheet_y, sheet_x, f"Age: {self.character.age} | Gen: {self.character.generation}th | Max: {self.character.max_trait_rating}", curses.color_pair(3))
            sheet_y += 1
            
            remaining = self.character.total_freebies - self.character.spent_freebies
            spent_str = f"Freebie Points: {self.character.spent_freebies}/{self.character.total_freebies} spent"
            if remaining > 0: spent_str += f" ({remaining} remaining)"
            self.stdscr.addstr(sheet_y, sheet_x, spent_str, curses.color_pair(1) if remaining == 0 else curses.color_pair(3) | curses.A_BOLD)
            sheet_y += 2
            
            left_col_x, right_col_x = sheet_x, sheet_x + 40
            
            # Left Column
            col_y_left = sheet_y
            self.stdscr.addstr(col_y_left, left_col_x, "═══ ATTRIBUTES ═══", curses.color_pair(4) | curses.A_BOLD)
            col_y_left += 1
            for name, data in self.character.attributes.items():
                self.display_trait(col_y_left, left_col_x, name, data, 38); col_y_left += 1
            
            col_y_left += 1
            self.stdscr.addstr(col_y_left, left_col_x, "═══ ABILITIES ═══", curses.color_pair(4) | curses.A_BOLD)
            col_y_left += 1
            abilities_shown = [(n, d) for n, d in self.character.abilities.items() if d['new'] > 0]
            for name, data in abilities_shown:
                self.display_trait(col_y_left, left_col_x, name, data, 38); col_y_left += 1

            # Right Column
            col_y_right = sheet_y
            for cat_name in ["disciplines", "backgrounds"]:
                category = getattr(self.character, cat_name)
                if category:
                    self.stdscr.addstr(col_y_right, right_col_x, f"═══ {cat_name.upper()} ═══", curses.color_pair(4) | curses.A_BOLD)
                    col_y_right += 1
                    for name, data in category.items():
                        self.display_trait(col_y_right, right_col_x, name, data, 38); col_y_right += 1
                    col_y_right += 1

            self.stdscr.addstr(col_y_right, right_col_x, "═══ VIRTUES & PATH ═══", curses.color_pair(4) | curses.A_BOLD)
            col_y_right += 1
            for name, data in self.character.virtues.items():
                self.display_trait(col_y_right, right_col_x, name, data, 38); col_y_right += 1
            self.display_trait(col_y_right, right_col_x, "Humanity", self.character.humanity, 38); col_y_right += 1
            self.display_trait(col_y_right, right_col_x, "Willpower", self.character.willpower, 38)
            
            exit_msg = "Press any key to exit the program..."
            self.stdscr.addstr(start_y + container_height - 2, start_x + (container_width - len(exit_msg)) // 2, exit_msg, curses.color_pair(1) | curses.A_BOLD)
            
            self.stdscr.refresh()
            
            if self.stdscr.getch(): return


def main(stdscr):
    """The main entry point for the curses application."""
    app = TUIApp(stdscr)
    app.run()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nExiting program. Goodbye!")
        sys.exit(0)
    except Exception as e:
        import traceback
        traceback.print_exc()
        input(f"\nAn error occurred: {e}. Press Enter to exit.")