# tui/final_view.py

import curses
from . import utils
from . import theme
from vtm_npc_logic import VtMCharacter

class FinalView:
    def __init__(self, stdscr, character: VtMCharacter):
        self.stdscr = stdscr
        self.character = character

    def show(self):
        """Display the final character sheet before exiting."""
        while True:
            self.stdscr.erase()
            h, w = self.stdscr.getmaxyx()
            container_width = min(130, w - 2)
            container_height = min(55, h - 6)
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
            
            utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, "FINAL CHARACTER SHEET")
            
            sheet_y, sheet_x = start_y + 2, start_x + 2
            
            self.stdscr.addstr(sheet_y, sheet_x, f"{self.character.name} ({self.character.clan})", theme.CLR_TITLE()); sheet_y += 1
            self.stdscr.addstr(sheet_y, sheet_x, f"Age: {self.character.age} | Gen: {self.character.generation}th | Max: {self.character.max_trait_rating}", theme.CLR_ACCENT()); sheet_y += 1
            
            if self.character.is_free_mode:
                spent_str = f"Total Freebie Points Spent: {self.character.spent_freebies}"
                color = theme.CLR_ACCENT()
            else:
                remaining = self.character.total_freebies - self.character.spent_freebies
                spent_str = f"Freebie Points: {self.character.spent_freebies}/{self.character.total_freebies} spent" + (f" ({remaining} remaining)" if remaining > 0 else "")
                color = theme.CLR_ACCENT()
            self.stdscr.addstr(sheet_y, sheet_x, spent_str, color); sheet_y += 2
            
            # --- [3-Column Layout] ---
            col_width = (container_width - 6) // 3
            start_draw_y, max_draw_y = sheet_y, start_y + container_height - 3
            col1_x = sheet_x
            col2_x = sheet_x + col_width + 2
            col3_x = sheet_x + (col_width * 2) + 4

            # Draw Vertical Separators
            for i in range(max_draw_y - start_draw_y - 1):
                self.stdscr.addstr(start_draw_y + i, col1_x + col_width, theme.SYM_BORDER_V, theme.CLR_BORDER())
                self.stdscr.addstr(start_draw_y + i, col2_x + col_width, theme.SYM_BORDER_V, theme.CLR_BORDER())

            # --- [Column 1: ATTRIBUTES] ---
            y_c1 = start_draw_y
            self.stdscr.addstr(y_c1, col1_x, f"{theme.SYM_HEADER_L}ATTRIBUTES{theme.SYM_HEADER_R}"[:col_width], theme.CLR_ACCENT()); y_c1 += 1
            for n, d in self.character.attributes.items():
                if y_c1 >= max_draw_y: break
                self._display_trait(y_c1, col1_x, n, d, col_width); y_c1 += 1

            # --- [Column 2: ABILITIES] ---
            y_c2 = start_draw_y
            self.stdscr.addstr(y_c2, col2_x + 2, f"{theme.SYM_HEADER_L}ABILITIES{theme.SYM_HEADER_R}"[:col_width - 2], theme.CLR_ACCENT()); y_c2 += 1
            for n, d in [(n, d) for n, d in self.character.abilities.items() if d['new'] > 0]:
                if y_c2 >= max_draw_y: break
                self._display_trait(y_c2, col2_x + 2, n, d, col_width - 2); y_c2 += 1

            # --- [Column 3: EVERYTHING ELSE] ---
            y_c3 = start_draw_y
            for cat in ["disciplines", "backgrounds"]:
                if getattr(self.character, cat) and y_c3 < max_draw_y:
                    self.stdscr.addstr(y_c3, col3_x + 2, f"{theme.SYM_HEADER_L}{cat.upper()}{theme.SYM_HEADER_R}"[:col_width - 2], theme.CLR_ACCENT()); y_c3 += 1
                    for n, d in getattr(self.character, cat).items():
                        if y_c3 >= max_draw_y: break
                        self._display_trait(y_c3, col3_x + 2, n, d, col_width - 2); y_c3 += 1
                    y_c3 += 1
            
            if y_c3 < max_draw_y:
                self.stdscr.addstr(y_c3, col3_x + 2, f"{theme.SYM_HEADER_L}VIRTUES{theme.SYM_HEADER_R}"[:col_width - 2], theme.CLR_ACCENT()); y_c3 += 1
                for n, d in self.character.virtues.items():
                    if y_c3 >= max_draw_y: break
                    self._display_trait(y_c3, col3_x + 2, n, d, col_width - 2); y_c3 += 1
                if y_c3 < max_draw_y: self._display_trait(y_c3, col3_x + 2, "Humanity", self.character.humanity, col_width - 2); y_c3 += 1
                if y_c3 < max_draw_y: self._display_trait(y_c3, col3_x + 2, "Willpower", self.character.willpower, col_width - 2)
            
            # --- [EXPORT PROMPT] ---
            controls = "E: Export to Text | Any other key: Exit"
            self.stdscr.addstr(start_y + container_height - 2, start_x + (container_width - len(controls)) // 2, controls, theme.CLR_BORDER())
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            
            if key == ord('e') or key == ord('E'):
                self._export_character(start_y + container_height - 2, start_x + 2)
            elif key != curses.KEY_RESIZE:
                return

    def _export_character(self, prompt_y, prompt_x):
        """Handles the logic for exporting character to a text file."""
        def dummy_redraw():
            pass 
            
        default_name = f"{self.character.name.replace(' ', '_').lower()}.txt"
        
        self.stdscr.move(prompt_y, 0)
        self.stdscr.clrtoeol()
        
        try:
            # Wrapped in try/except InputCancelled
            filename = utils.get_string_input(self.stdscr, f"Filename (default: {default_name}): ", prompt_y, prompt_x, dummy_redraw)
        except utils.InputCancelled:
            return # Cancel export and go back to sheet loop
        
        if not filename:
            filename = default_name
        
        if not filename.endswith('.txt'):
            filename += ".txt"
            
        try:
            with open(filename, 'w') as f:
                f.write(self.character.get_text_sheet())
            utils.show_popup(self.stdscr, "Success", f"Character saved to {filename}", theme.CLR_ACCENT())
        except Exception as e:
            utils.show_popup(self.stdscr, "Error", f"Failed to save: {str(e)}", theme.CLR_ERROR())

    def _display_trait(self, y: int, x: int, name: str, data: Dict, width: int):
        max_name_len = width - 9
        name_part = f"{name[:max_name_len]:<{max_name_len}}"
        if data['base'] == data['new']:
            trait_str = f"{name_part} [{data['new']}]"
            self.stdscr.addstr(y, x, trait_str[:width], theme.CLR_TEXT())
        else:
            trait_str = f"{name_part} [{data['base']}]→[{data['new']}]"
            self.stdscr.addstr(y, x, trait_str[:width], theme.CLR_ACCENT())