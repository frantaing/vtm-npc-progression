# --- [IMPORTS] ---
import curses
from typing import Dict, Any, Optional
from . import utils
from .utils import QuitApplication, safe_input, InputCancelled
from . import theme
from vtm_npc_logic import VtMCharacter, ATTRIBUTES_LIST, ABILITIES_LIST, VIRTUES_LIST
from vtm_data import CLAN_DATA

class SetupView:
    def __init__(self, stdscr):
        self.stdscr = stdscr

    def run(self, is_free_mode: bool) -> Optional[VtMCharacter]:
        character = self._setup_character(is_free_mode)
        if not character:
            return None
        
        if is_free_mode:
            # Skip the wizard and just initialize everything to 0
            self._fill_blank_traits(character)
        else:
            self._setup_initial_traits(character)
            
        return character

    def _fill_blank_traits(self, character: VtMCharacter):
        """Silently populates the character with 0s for Free Mode."""
        for attr in ATTRIBUTES_LIST:
            character.set_initial_trait("attributes", attr, 0)
            
        for abil in ABILITIES_LIST:
            character.set_initial_trait("abilities", abil, 0)
            
        for virt in VIRTUES_LIST:
            character.set_initial_trait("virtues", virt, 0)

    def _setup_character(self, is_free_mode: bool) -> Optional[VtMCharacter]:
        clan_list = sorted(list(CLAN_DATA.keys()))

        prompts = [
            ("Character Name", None, None, None),
            ("Clan", clan_list, None, None),
            ("Age (0-5600+)", None, 0, 10000),
            ("Generation (2-16)", None, 2, 16)
        ]
        entered_info: Dict[str, Any] = {}

        def draw_setup_screen():
            h, w = self.stdscr.getmaxyx()
            self.stdscr.erase()
            container_width, container_height = 70, 18
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
            title = "VAMPIRE: THE MASQUERADE - NPC PROGRESSION TOOL"
            self.stdscr.addstr(start_y - 3, (w - len(title)) // 2, title, theme.CLR_TITLE())
            utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, "Character Setup")
            list_y = start_y + 2
            for info_label, info_value in entered_info.items():
                self.stdscr.addstr(list_y, start_x + 2, f"{info_label}: ", theme.CLR_ACCENT())
                self.stdscr.addstr(list_y, start_x + 2 + len(info_label) + 2, f"{info_value}", theme.CLR_TEXT())
                list_y += 1
            return start_y, start_x, list_y

        for label, option_list, min_val, max_val in prompts:
            start_y, start_x, list_y = draw_setup_screen()

            if min_val is not None:
                value = safe_input(utils.get_number_input, self.stdscr, f"{label}: ", list_y, start_x + 2, min_val, max_val, draw_setup_screen)
            elif option_list is not None:
                value = safe_input(utils.get_selection_input, self.stdscr, f"{label}: ", list_y, start_x + 2, option_list, draw_setup_screen)
            else:
                value = safe_input(utils.get_string_input, self.stdscr, f"{label}: ", list_y, start_x + 2, draw_setup_screen)

            entered_info[label] = value

        character = VtMCharacter(
            entered_info["Character Name"], entered_info["Clan"],
            entered_info["Age (0-5600+)"], entered_info["Generation (2-16)"],
            is_free_mode=is_free_mode
        )

        h, w = self.stdscr.getmaxyx()
        container_width, container_height = 70, 18
        start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
        self.stdscr.erase()
        utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, "Character Created")
        list_y = start_y + 2
        for info_label, info_value in entered_info.items():
            self.stdscr.addstr(list_y, start_x + 2, f"{info_label}: {info_value}", theme.CLR_ACCENT()); list_y += 1

        freebie_msg = "Freebie Points: Unlimited" if is_free_mode else f"Character created with {character.total_freebies} Freebie Points!"
        self.stdscr.addstr(list_y + 1, start_x + 2, freebie_msg, theme.CLR_ACCENT())

        prompt_msg = "Press any key to enter character sheet..." if is_free_mode else "Press any key to set initial traits..."
        self.stdscr.addstr(list_y + 3, start_x + 2, prompt_msg, theme.CLR_BORDER())

        self.stdscr.refresh()
        key = self.stdscr.getch()
        if key == 24: raise utils.QuitApplication()

        return character

    def _setup_initial_traits(self, character: VtMCharacter):

        def run_setup_loop(title_text, item_list, min_val, max_val, is_freeform=False):
            entered_items: Dict[str, Any] = {}

            def draw_loop_screen(current_item_name=None):
                h, w = self.stdscr.getmaxyx()
                self.stdscr.erase()
                container_width, container_height = 60, min(40, h - 4)
                start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
                utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, title_text)
                self.stdscr.addstr(start_y + 2, start_x + 2, f"Set initial values ({min_val}-{max_val})", theme.CLR_BORDER())
                if is_freeform:
                    self.stdscr.addstr(start_y + 3, start_x + 2, "Type 'done' or Press Esc to finish.", theme.CLR_BORDER())

                list_y = start_y + 5
                max_display = container_height - 9
                start_idx = max(0, len(entered_items) - max_display + 1)
                for name, value in list(entered_items.items())[start_idx:]:
                    if list_y >= start_y + container_height - 3: break
                    self.stdscr.addstr(list_y, start_x + 2, f"{name}: ", theme.CLR_ACCENT())
                    self.stdscr.addstr(list_y, start_x + 2 + len(name) + 2, f"{value}", theme.CLR_TEXT())
                    list_y += 1
                if current_item_name:
                    self.stdscr.addstr(list_y, start_x + 2, f"{title_text[:-1]} Name: {current_item_name}", theme.CLR_TEXT())
                return start_y, start_x, list_y

            if is_freeform:
                while True:
                    start_y, start_x, list_y = draw_loop_screen()
                    try:
                        item_name = utils.get_string_input(self.stdscr, f"{title_text[:-1]} Name: ", list_y, start_x + 2, draw_loop_screen)
                    except utils.InputCancelled:
                        break  # Esc in freeform = done adding items

                    if item_name.lower() == 'done':
                        break

                    val = safe_input(utils.get_number_input, self.stdscr, "  Value: ", list_y + 1, start_x + 2, min_val, max_val, draw_loop_screen, current_item_name=item_name)
                    entered_items[item_name] = val
                    character.set_initial_trait(title_text.lower(), item_name, val)
            else:
                for item in item_list:
                    _, start_x, list_y = draw_loop_screen()
                    val = safe_input(utils.get_number_input, self.stdscr, f"{item}: ", list_y, start_x + 2, min_val, max_val, draw_loop_screen)
                    entered_items[item] = val
                    character.set_initial_trait(title_text.lower(), item, val)

            return entered_items

        run_setup_loop("Attributes", ATTRIBUTES_LIST, 1, 10)
        run_setup_loop("Abilities", ABILITIES_LIST, 0, 10)

        entered_virtues: Dict[str, Any] = {}
        humanity = None
        willpower = None

        def draw_virtues_screen():
            h, w = self.stdscr.getmaxyx()
            self.stdscr.erase()
            container_width, container_height = 60, 20
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
            utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, "Virtues & Path")
            self.stdscr.addstr(start_y + 2, start_x + 2, "Set initial values (1-10)", theme.CLR_BORDER())
            list_y = start_y + 4
            for name, value in entered_virtues.items():
                self.stdscr.addstr(list_y, start_x + 2, f"{name}: ", theme.CLR_ACCENT())
                self.stdscr.addstr(list_y, start_x + 2 + len(name) + 2, f"{value}", theme.CLR_TEXT())
                list_y += 1
            if humanity is not None:
                self.stdscr.addstr(list_y, start_x + 2, "Humanity/Path: ", theme.CLR_ACCENT())
                self.stdscr.addstr(list_y, start_x + 2 + len("Humanity/Path: "), f"{humanity}", theme.CLR_TEXT())
                list_y += 1
            if willpower is not None:
                self.stdscr.addstr(list_y, start_x + 2, "Willpower: ", theme.CLR_ACCENT())
                self.stdscr.addstr(list_y, start_x + 2 + len("Willpower: "), f"{willpower}", theme.CLR_TEXT())
                list_y += 1
            return start_y, start_x, list_y

        for virtue in VIRTUES_LIST:
            _, start_x, list_y = draw_virtues_screen()
            val = safe_input(utils.get_number_input, self.stdscr, f"{virtue}: ", list_y, start_x + 2, 1, 10, draw_virtues_screen)
            entered_virtues[virtue] = val
            character.set_initial_trait("virtues", virtue, val)

        _, start_x, list_y = draw_virtues_screen()
        humanity = safe_input(utils.get_number_input, self.stdscr, "Humanity/Path: ", list_y, start_x + 2, 1, 10, draw_virtues_screen)
        character.set_initial_value("humanity", humanity)

        _, start_x, list_y = draw_virtues_screen()
        willpower = safe_input(utils.get_number_input, self.stdscr, "Willpower: ", list_y, start_x + 2, 1, 10, draw_virtues_screen)
        character.set_initial_value("willpower", willpower)