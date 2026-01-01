# tui/main_view.py

import curses
import textwrap
from typing import Dict, Any, Optional
from . import utils
from . import theme
from vtm_npc_logic import VtMCharacter, ATTRIBUTES_LIST, ABILITIES_LIST, VIRTUES_LIST, FREEBIE_COSTS
from .utils import QuitApplication, InputCancelled

class MainView:
    def __init__(self, stdscr, character: VtMCharacter):
        self.stdscr = stdscr
        self.character = character
        self.message = ""
        self.message_color = theme.CLR_ACCENT()

    def run(self):
        selected = 0
        menu_items = [
            ("Attributes", "Attribute"), ("Abilities", "Ability"), ("Disciplines", "Discipline"),
            ("Backgrounds", "Background"), ("Virtues", "Virtue"), ("Humanity/Path", "Humanity"),
            ("Willpower", "Willpower"),
        ]
        
        while True:
            self._draw_main_menu_screen(selected, menu_items)
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            if key == 24: return
            elif key == curses.KEY_RESIZE: self.message = ""
            elif key == curses.KEY_UP: selected = (selected - 1 + len(menu_items)) % len(menu_items); self.message = ""
            elif key == curses.KEY_DOWN: selected = (selected + 1) % len(menu_items); self.message = ""
            elif key == ord('\n'):
                label, category = menu_items[selected]
                self._handle_improvement_menu(label, category)

    def _display_character_sheet(self, y: int, x: int, width: int, height: int):
        # Header Info
        self.stdscr.addstr(y, x, f"{self.character.name} ({self.character.clan})"[:width], theme.CLR_TITLE()); y += 1
        self.stdscr.addstr(y, x, f"Age: {self.character.age} | Gen: {self.character.generation}th | Max: {self.character.max_trait_rating}"[:width], theme.CLR_ACCENT()); y += 1
        
        if self.character.is_free_mode:
            freebie_str = f"Freebie Points Spent: {self.character.spent_freebies}"
            color = theme.CLR_ACCENT()
        else:
            remaining = self.character.total_freebies - self.character.spent_freebies
            freebie_str = f"Freebie: {remaining}/{self.character.total_freebies}"
            color = theme.CLR_ACCENT() if remaining > 0 else theme.CLR_ERROR()
        self.stdscr.addstr(y, x, freebie_str, color); y += 2

        # --- [3-Column Layout Calculations] ---
        # Subtracting 2 for the vertical separators
        col_width = (width - 2) // 3
        
        start_y = y
        max_y = y + height
        
        col1_x = x
        col2_x = x + col_width + 1
        col3_x = x + (col_width * 2) + 2

        # Draw Column Separators
        for i in range(height - 1):
            if start_y + i < max_y:
                self.stdscr.addstr(start_y + i, col1_x + col_width, theme.SYM_BORDER_V, theme.CLR_BORDER())
                self.stdscr.addstr(start_y + i, col2_x + col_width, theme.SYM_BORDER_V, theme.CLR_BORDER())

        # --- [Column 1: ATTRIBUTES] ---
        y_c1 = start_y
        self.stdscr.addstr(y_c1, col1_x, f"{theme.SYM_HEADER_L}ATTRIBUTES{theme.SYM_HEADER_R}"[:col_width], theme.CLR_ACCENT()); y_c1 += 1
        for name, data in self.character.attributes.items():
            if y_c1 >= max_y: break
            self._display_trait(y_c1, col1_x, name, data, col_width); y_c1 += 1

        # --- [Column 2: ABILITIES] ---
        y_c2 = start_y
        # Padding adjustment: X + 2, Width - 2
        self.stdscr.addstr(y_c2, col2_x + 2, f"{theme.SYM_HEADER_L}ABILITIES{theme.SYM_HEADER_R}"[:col_width - 2], theme.CLR_ACCENT()); y_c2 += 1
        abilities_shown = [(n, d) for n, d in self.character.abilities.items() if d['new'] > 0]
        for name, data in abilities_shown:
            if y_c2 >= max_y: break
            self._display_trait(y_c2, col2_x + 2, name, data, col_width - 2); y_c2 += 1

        # --- [Column 3: EVERYTHING ELSE] ---
        y_c3 = start_y
        
        # Disc & BG
        for cat_name in ["disciplines", "backgrounds"]:
            category = getattr(self.character, cat_name)
            if category and y_c3 < max_y:
                # Padding adjustment: X + 2, Width - 2
                self.stdscr.addstr(y_c3, col3_x + 2, f"{theme.SYM_HEADER_L}{cat_name.upper()}{theme.SYM_HEADER_R}"[:col_width - 2], theme.CLR_ACCENT()); y_c3 += 1
                for name, data in category.items():
                    if y_c3 >= max_y: break
                    self._display_trait(y_c3, col3_x + 2, name, data, col_width - 2); y_c3 += 1
                y_c3 += 1
        
        # Virtues & Others
        if y_c3 < max_y:
            # Padding adjustment: X + 2, Width - 2
            self.stdscr.addstr(y_c3, col3_x + 2, f"{theme.SYM_HEADER_L}VIRTUES{theme.SYM_HEADER_R}"[:col_width - 2], theme.CLR_ACCENT()); y_c3 += 1
            for name, data in self.character.virtues.items():
                if y_c3 >= max_y: break
                self._display_trait(y_c3, col3_x + 2, name, data, col_width - 2); y_c3 += 1
            if y_c3 < max_y: self._display_trait(y_c3, col3_x + 2, "Humanity", self.character.humanity, col_width - 2); y_c3 += 1
            if y_c3 < max_y: self._display_trait(y_c3, col3_x + 2, "Willpower", self.character.willpower, col_width - 2)

    def _draw_main_menu_screen(self, selected, menu_items):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.erase()
        
        # Maximize width (w-2) to fit 3 columns
        container_width = min(130, w - 2)
        container_height = min(50, h - 4)
        start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
        
        utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, "VTM Elder Creator")
        
        # Adjust panel split
        right_panel_width = 30 # Made menu slightly narrower
        left_panel_width = container_width - right_panel_width - 3 # Maximize sheet space
        panel_content_height = container_height - 6
        
        self._display_character_sheet(start_y + 2, start_x + 2, left_panel_width, panel_content_height)
        
        # Separator between Sheet and Menu
        for i in range(1, container_height - 1): 
            self.stdscr.addstr(start_y + i, start_x + left_panel_width + 1, theme.SYM_BORDER_V, theme.CLR_BORDER())
        
        right_x, menu_y = start_x + left_panel_width + 3, start_y + 2
        self.stdscr.addstr(menu_y, right_x, "SPEND FREEBIE POINTS", theme.CLR_TITLE()); menu_y += 2
        
        for i, (label, category) in enumerate(menu_items):
            prefix = theme.SYM_POINTER if i == selected else "  "
            menu_str = f"{prefix}{label} (Cost: {FREEBIE_COSTS.get(category, 'N/A')}/dot)"
            self.stdscr.addstr(menu_y + i, right_x, menu_str[:right_panel_width], theme.CLR_SELECTED() if i == selected else theme.CLR_TEXT())
        
        if self.message:
            msg_y = start_y + container_height - 2
            wrapped_lines = textwrap.wrap(self.message, right_panel_width - 2)
            msg_start_y = msg_y - (len(wrapped_lines) - 1)
            utils.draw_wrapped_text(self.stdscr, msg_start_y, right_x, self.message, right_panel_width - 2, self.message_color)
        
        controls = "↑/↓: Navigate | Enter: Select | Ctrl+X: Finalize & Exit"
        self.stdscr.addstr(h - 1, (w - len(controls)) // 2, controls, theme.CLR_ACCENT())

    def _handle_improvement_menu(self, label: str, category: str):
        if category in ["Humanity", "Willpower"]:
            self._improve_single_trait(label, category, "Humanity/Path" if category == "Humanity" else "Willpower", self._draw_main_menu_screen, 0, [])
            return
        
        trait_list_map = { "Attribute": ATTRIBUTES_LIST, "Ability": ABILITIES_LIST, "Discipline": list(self.character.disciplines.keys()), "Background": list(self.character.backgrounds.keys()), "Virtue": VIRTUES_LIST }
        trait_list = trait_list_map.get(category, [])
        selected, scroll_offset = 0, 0
        can_add = category in ["Discipline", "Background"]

        while True:
            display_list = trait_list + (["** Add New **"] if can_add else [])
            container_height = min(50, self.stdscr.getmaxyx()[0] - 6)
            max_items = container_height - 12
            if selected < scroll_offset: scroll_offset = selected
            if selected >= scroll_offset + max_items: scroll_offset = selected - max_items + 1

            start_x, start_y, container_height, right_x, right_panel_width = self._draw_improvement_menu_screen(label, category, trait_list, selected, scroll_offset, can_add)
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            if key == 24: raise utils.QuitApplication()
            elif key == 27: self.message = ""; return
            elif key == curses.KEY_RESIZE: self.message = ""
            elif key == curses.KEY_UP: selected = (selected - 1 + len(display_list)) % len(display_list); self.message = ""
            elif key == curses.KEY_DOWN: selected = (selected + 1) % len(display_list); self.message = ""
            elif key == ord('\n'):
                redraw_args = (label, category, trait_list, selected, scroll_offset, can_add)
                if can_add and selected == len(trait_list):
                    prompt_y = start_y + container_height - 4
                    # Handle ESC
                    try:
                        new_name = utils.get_string_input(self.stdscr, f"New {category[:-1]} Name: ", prompt_y, right_x, self._draw_improvement_menu_screen, *redraw_args)
                        if new_name and new_name.lower() != 'done':
                            self.character.set_initial_trait(category.lower() + 's', new_name, 0)
                            trait_list.append(new_name)
                            self._improve_single_trait(label, category, new_name, self._draw_improvement_menu_screen, *redraw_args)
                    except utils.InputCancelled:
                        self.message = "Cancelled."
                elif selected < len(trait_list):
                    self._improve_single_trait(label, category, trait_list[selected], self._draw_improvement_menu_screen, *redraw_args)
    
    def _draw_improvement_menu_screen(self, label, category, trait_list, selected, scroll_offset, can_add):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.erase()
        
        container_width, container_height = min(130, w - 2), min(50, h - 4) # Match main menu sizing
        start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
        
        right_panel_width = 30
        left_panel_width = container_width - right_panel_width - 3
        panel_content_height = container_height - 6
        
        utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, f"Improve {label}")
        self._display_character_sheet(start_y + 2, start_x + 2, left_panel_width, panel_content_height)
        
        for i in range(1, container_height - 1): self.stdscr.addstr(start_y + i, start_x + left_panel_width + 1, theme.SYM_BORDER_V, theme.CLR_BORDER())
        right_x, menu_y = start_x + left_panel_width + 3, start_y + 2
        
        if self.character.is_free_mode:
            self.stdscr.addstr(menu_y, right_x, f"Total Cost: {self.character.spent_freebies}", theme.CLR_ACCENT()); menu_y += 2
        else:
            self.stdscr.addstr(menu_y, right_x, f"Available: {self.character.total_freebies - self.character.spent_freebies}", theme.CLR_ACCENT()); menu_y += 2
        
        max_display_items = container_height - 12
        display_list = trait_list + (["** Add New **"] if can_add else [])
        for i in range(max_display_items):
            idx = scroll_offset + i
            if idx >= len(display_list): break
            trait_name = display_list[idx]
            prefix = theme.SYM_POINTER if idx == selected else "  "
            if trait_name == "** Add New **": trait_str = f"{prefix}{trait_name}"
            else:
                current = self.character.get_trait_data(category, trait_name)['new']
                trait_str = f"{prefix}{trait_name[:18]:<18} [{current}]"
            self.stdscr.addstr(menu_y + i, right_x, trait_str[:right_panel_width], theme.CLR_SELECTED() if idx == selected else theme.CLR_TEXT())
        if self.message:
            msg_y = start_y + container_height - 2
            wrapped_lines = textwrap.wrap(self.message, right_panel_width - 2)
            msg_start_y = msg_y - (len(wrapped_lines) - 1)
            utils.draw_wrapped_text(self.stdscr, msg_start_y, right_x, self.message, right_panel_width - 2, self.message_color)
        self.stdscr.addstr(h - 1, (w - len("placeholder"))//2, "↑/↓: Navigate | Enter: Improve | Esc: Back", theme.CLR_BORDER())
        return start_x, start_y, container_height, right_x, right_panel_width
            
    def _improve_single_trait(self, parent_label: str, category: str, trait_name: str, parent_draw_func, *redraw_args):
        trait_data = self.character.get_trait_data(category, trait_name)
        current, base, max_val = trait_data['new'], trait_data['base'], self.character.max_trait_rating
        
        def draw_improve_dialog():
            parent_draw_func(*redraw_args)
            h, w = self.stdscr.getmaxyx()
            dialog_width, dialog_height = 50, 8
            dialog_x, dialog_y = (w - dialog_width) // 2, (h - dialog_height) // 2
            utils.draw_box(self.stdscr, dialog_y, dialog_x, dialog_height, dialog_width, "Improve Trait")
            self.stdscr.addstr(dialog_y + 2, dialog_x + 2, f"Trait: {trait_name}", theme.CLR_ACCENT())
            self.stdscr.addstr(dialog_y + 3, dialog_x + 2, f"Current: [{current}] (Base: {base})", theme.CLR_TEXT())
            self.stdscr.addstr(dialog_y + 4, dialog_x + 2, f"Max: {max_val}", theme.CLR_BORDER())
            return dialog_y + 5, dialog_x + 2

        target = None
        while target is None:
            prompt_y, prompt_x = draw_improve_dialog()
            try:
                target = utils.get_number_input(self.stdscr, f"New value ({base}-{max_val}): ", prompt_y, prompt_x, base, max_val, draw_improve_dialog)
            except utils.InputCancelled:
                self.message = ""
                return
        
        success, msg = self.character.improve_trait(category, trait_name, target)
        if success: self.message, self.message_color = msg, theme.CLR_ACCENT()
        else: utils.show_popup(self.stdscr, "Error", msg, theme.CLR_ERROR())

    def _display_trait(self, y: int, x: int, name: str, data: Dict, width: int):
        max_name_len = width - 9
        name_part = f"{name[:max_name_len]:<{max_name_len}}"
        if data['base'] == data['new']:
            trait_str = f"{name_part} [{data['new']}]"
            self.stdscr.addstr(y, x, trait_str[:width], theme.CLR_TEXT())
        else:
            trait_str = f"{name_part} [{data['base']}]→[{data['new']}]"
            self.stdscr.addstr(y, x, trait_str[:width], theme.CLR_ACCENT())