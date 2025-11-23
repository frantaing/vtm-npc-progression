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
            self.stdscr.clear()
            h, w = self.stdscr.getmaxyx()
            container_width = min(110, w - 4); container_height = min(55, h - 6)
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
            
            utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, "FINAL CHARACTER SHEET")
            
            sheet_y, sheet_x = start_y + 2, start_x + 2
            
            self.stdscr.addstr(sheet_y, sheet_x, f"{self.character.name} ({self.character.clan})", theme.CLR_TITLE()); sheet_y += 1
            self.stdscr.addstr(sheet_y, sheet_x, f"Age: {self.character.age} | Gen: {self.character.generation}th | Max: {self.character.max_trait_rating}", theme.CLR_BORDER()); sheet_y += 1
            
            if self.character.is_free_mode:
                spent_str = f"Total Freebie Points Spent: {self.character.spent_freebies}"
                color = theme.CLR_ACCENT()
            else:
                remaining = self.character.total_freebies - self.character.spent_freebies
                spent_str = f"Freebie Points: {self.character.spent_freebies}/{self.character.total_freebies} spent" + (f" ({remaining} remaining)" if remaining > 0 else "")
                color = theme.CLR_ACCENT()
            self.stdscr.addstr(sheet_y, sheet_x, spent_str, color); sheet_y += 2
            
            start_draw_y, max_draw_y = sheet_y, start_y + container_height - 3
            col1_x, col_width = sheet_x, 28
            col2_x = sheet_x + col_width + 4

            y_left = start_draw_y
            self.stdscr.addstr(y_left, col1_x, f"{theme.SYM_HEADER_L}ATTRIBUTES{theme.SYM_HEADER_R}", theme.CLR_ACCENT()); y_left += 1
            for n, d in self.character.attributes.items():
                if y_left >= max_draw_y: break
                self._display_trait(y_left, col1_x, n, d, col_width); y_left += 1
            y_left += 1
            if y_left < max_draw_y:
                self.stdscr.addstr(y_left, col1_x, f"{theme.SYM_HEADER_L}ABILITIES{theme.SYM_HEADER_R}", theme.CLR_ACCENT()); y_left += 1
                for n, d in [(n, d) for n, d in self.character.abilities.items() if d['new'] > 0]:
                    if y_left >= max_draw_y: break
                    self._display_trait(y_left, col1_x, n, d, col_width); y_left += 1

            y_right = start_draw_y
            for cat in ["disciplines", "backgrounds"]:
                if getattr(self.character, cat) and y_right < max_draw_y:
                    self.stdscr.addstr(y_right, col2_x, f"{theme.SYM_HEADER_L}{cat.upper()}{theme.SYM_HEADER_R}", theme.CLR_ACCENT()); y_right += 1
                    for n, d in getattr(self.character, cat).items():
                        if y_right >= max_draw_y: break
                        self._display_trait(y_right, col2_x, n, d, col_width); y_right += 1
                    y_right += 1
            
            if y_right < max_draw_y:
                self.stdscr.addstr(y_right, col2_x, f"{theme.SYM_HEADER_L}VIRTUES{theme.SYM_HEADER_R}", theme.CLR_ACCENT()); y_right += 1
                for n, d in self.character.virtues.items():
                    if y_right >= max_draw_y: break
                    self._display_trait(y_right, col2_x, n, d, col_width); y_right += 1
                if y_right < max_draw_y: self._display_trait(y_right, col2_x, "Humanity", self.character.humanity, col_width); y_right += 1
                if y_right < max_draw_y: self._display_trait(y_right, col2_x, "Willpower", self.character.willpower, col_width)
            
            exit_msg = "Press any key to exit the program..."
            self.stdscr.addstr(start_y + container_height - 2, start_x + (container_width - len(exit_msg)) // 2, exit_msg, theme.CLR_BORDER())
            self.stdscr.refresh()
            
            if self.stdscr.getch() != curses.KEY_RESIZE:
                return

    def _display_trait(self, y: int, x: int, name: str, data: Dict, width: int):
        max_name_len = width - 9
        name_part = f"{name[:max_name_len]:<{max_name_len}}"
        if data['base'] == data['new']:
            trait_str = f"{name_part} [{data['new']}]"
            self.stdscr.addstr(y, x, trait_str[:width], theme.CLR_TEXT())
        else:
            trait_str = f"{name_part} [{data['base']}]"
            self.stdscr.addstr(y, x, trait_str, theme.CLR_TEXT())
            self.stdscr.addstr(y, x + len(trait_str), f"{theme.SYM_ARROW}[{data['new']}]", theme.CLR_ACCENT())