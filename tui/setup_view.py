# tui/setup_view.py

import curses
from typing import Dict, Any, Optional
from . import utils
from vtm_npc_logic import VtMCharacter, ATTRIBUTES_LIST, ABILITIES_LIST, VIRTUES_LIST

class SetupView:
    def __init__(self, stdscr):
        self.stdscr = stdscr

    def run(self) -> Optional[VtMCharacter]:
        """Orchestrates the entire character setup process."""
        character = self._setup_character()
        if not character:
            return None
        
        self._setup_initial_traits(character)
        return character

    def _setup_character(self) -> Optional[VtMCharacter]:
        """Handles the first screen for basic character info."""
        prompts = [
            ("Character Name", None, None), ("Clan", None, None),
            ("Age (0-5600+)", 0, 10000), ("Generation (2-16)", 2, 16)
        ]
        entered_info: Dict[str, Any] = {}

        def draw_setup_screen():
            h, w = self.stdscr.getmaxyx()
            self.stdscr.clear()
            container_width, container_height = 70, 18
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
            title = "VAMPIRE: THE MASQUERADE - NPC PROGRESSION TOOL"
            self.stdscr.addstr(start_y - 3, (w - len(title)) // 2, title, curses.color_pair(utils.COLOR_MAGENTA) | curses.A_BOLD)
            utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, "Character Setup")
            list_y = start_y + 2
            for info_label, info_value in entered_info.items():
                self.stdscr.addstr(list_y, start_x + 2, f"{info_label}: {info_value}", curses.color_pair(utils.COLOR_GREEN)); list_y += 1
            return start_y, start_x, list_y

        for label, min_val, max_val in prompts:
            value = None
            while value is None:
                start_y, start_x, list_y = draw_setup_screen()
                if min_val is not None:
                    value = utils.get_number_input(self.stdscr, f"{label}: ", list_y, start_x + 2, min_val, max_val, draw_setup_screen)
                else:
                    value = utils.get_string_input(self.stdscr, f"{label}: ", list_y, start_x + 2, draw_setup_screen)
            entered_info[label] = value
        
        character = VtMCharacter(entered_info["Character Name"], entered_info["Clan"], entered_info["Age (0-5600+)"], entered_info["Generation (2-16)"])
        
        h, w = self.stdscr.getmaxyx()
        container_width, container_height = 70, 18
        start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
        self.stdscr.clear()
        utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, "Character Created")
        list_y = start_y + 2
        for info_label, info_value in entered_info.items():
            self.stdscr.addstr(list_y, start_x + 2, f"{info_label}: {info_value}", curses.color_pair(utils.COLOR_GREEN)); list_y += 1
        self.stdscr.addstr(list_y + 1, start_x + 2, f"Character created with {character.total_freebies} Freebie Points!", curses.color_pair(utils.COLOR_GREEN) | curses.A_BOLD)
        self.stdscr.addstr(list_y + 3, start_x + 2, "Press any key to set initial traits...", curses.color_pair(utils.COLOR_YELLOW))
        self.stdscr.refresh()
        if self.stdscr.getch() == 24: raise utils.QuitApplication()
        
        return character

    def _setup_initial_traits(self, character: VtMCharacter):
        """Handles all subsequent screens for setting trait values."""
        
        def run_setup_loop(title_text, item_list, min_val, max_val, is_freeform=False):
            entered_items: Dict[str, Any] = {}
            
            def draw_loop_screen(current_item_name=None):
                h, w = self.stdscr.getmaxyx()
                self.stdscr.clear()
                container_width, container_height = 60, min(40, h-4)
                start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
                utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, title_text)
                self.stdscr.addstr(start_y + 2, start_x + 2, f"Set initial values ({min_val}-{max_val})", curses.color_pair(utils.COLOR_YELLOW))
                if is_freeform: self.stdscr.addstr(start_y + 3, start_x + 2, "Type 'done' to finish.", curses.color_pair(utils.COLOR_YELLOW))

                list_y = start_y + 5
                max_display = container_height - 9
                start_idx = max(0, len(entered_items) - max_display + 1)
                for name, value in list(entered_items.items())[start_idx:]:
                    if list_y >= start_y + container_height - 3: break
                    self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(utils.COLOR_GREEN)); list_y += 1
                if current_item_name:
                    self.stdscr.addstr(list_y, start_x + 2, f"{title_text[:-1]} Name: {current_item_name}")
                return start_y, start_x, list_y

            if is_freeform:
                while True:
                    start_y, start_x, list_y = draw_loop_screen()
                    item_name = utils.get_string_input(self.stdscr, f"{title_text[:-1]} Name: ", list_y, start_x + 2, draw_loop_screen)
                    if item_name.lower() == 'done': break
                    val = None
                    while val is None:
                        val = utils.get_number_input(self.stdscr, "  Value: ", list_y + 1, start_x + 2, min_val, max_val, draw_loop_screen, current_item_name=item_name)
                    entered_items[item_name] = val
                    character.set_initial_trait(title_text.lower(), item_name, val)
            else:
                for item in item_list:
                    val = None
                    while val is None:
                        val = utils.get_number_input(self.stdscr, f"{item}: ", draw_loop_screen()[2], draw_loop_screen()[1] + 2, min_val, max_val, draw_loop_screen)
                    entered_items[item] = val
                    character.set_initial_trait(title_text.lower(), item, val)
            return entered_items

        run_setup_loop("Attributes", ATTRIBUTES_LIST, 1, 10)
        run_setup_loop("Abilities", ABILITIES_LIST, 0, 10)
        run_setup_loop("Disciplines", [], 1, 10, is_freeform=True)
        run_setup_loop("Backgrounds", [], 1, 10, is_freeform=True)
        
        # Unified Virtues/Path section
        entered_virtues: Dict[str, Any] = {}
        humanity: Optional[int] = None
        willpower: Optional[int] = None

        def draw_virtues_screen():
            h, w = self.stdscr.getmaxyx()
            self.stdscr.clear()
            container_width, container_height = 60, 20
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
            utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, "Virtues & Path")
            self.stdscr.addstr(start_y + 2, start_x + 2, "Set initial values (1-10)", curses.color_pair(utils.COLOR_YELLOW))
            
            list_y = start_y + 4
            for name, value in entered_virtues.items():
                self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(utils.COLOR_GREEN)); list_y += 1
            if humanity is not None:
                self.stdscr.addstr(list_y, start_x + 2, f"Humanity/Path: {humanity}", curses.color_pair(utils.COLOR_GREEN)); list_y += 1
            if willpower is not None:
                self.stdscr.addstr(list_y, start_x + 2, f"Willpower: {willpower}", curses.color_pair(utils.COLOR_GREEN)); list_y += 1
            return start_y, start_x, list_y

        for virtue in VIRTUES_LIST:
            val = None
            while val is None:
                val = utils.get_number_input(self.stdscr, f"{virtue}: ", draw_virtues_screen()[2], draw_virtues_screen()[1] + 2, 1, 10, draw_virtues_screen)
            entered_virtues[virtue] = val
            character.set_initial_trait("virtues", virtue, val)
        
        while humanity is None:
            humanity = utils.get_number_input(self.stdscr, "Humanity/Path: ", draw_virtues_screen()[2], draw_virtues_screen()[1] + 2, 1, 10, draw_virtues_screen)
        character.set_initial_value("humanity", humanity)

        while willpower is None:
            willpower = utils.get_number_input(self.stdscr, "Willpower: ", draw_virtues_screen()[2], draw_virtues_screen()[1] + 2, 1, 10, draw_virtues_screen)
        character.set_initial_value("willpower", willpower)