# --- [IMPORTS] ---
import curses
from . import utils
from . import theme
from vtm_npc_logic import VtMCharacter
from .renderer import draw_character_sheet_columns

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
            cx1 = sheet_x
            cx2 = sheet_x + col_width + 2
            cx3 = sheet_x + (col_width * 2) + 4
            content_y = sheet_y

            # Build item lists (same structure as MainView)
            from vtm_npc_logic import ATTRIBUTES_LIST, ABILITIES_LIST, VIRTUES_LIST

            col1_items = [("Header", "ATTRIBUTES")] + [("Attribute", a) for a in ATTRIBUTES_LIST]
            col2_items = [("Header", "ABILITIES")] + [("Ability", a) for a in ABILITIES_LIST]

            col3_items = []
            col3_items.append(("Header", "DISCIPLINES"))
            for disc in self.character.disciplines:
                col3_items.append(("Discipline", disc))
            col3_items.append(("Spacer", ""))
            col3_items.append(("Header", "BACKGROUNDS"))
            for bg in self.character.backgrounds:
                col3_items.append(("Background", bg))
            col3_items.append(("Spacer", ""))
            col3_items.append(("Header", "VIRTUES"))
            for virt in VIRTUES_LIST:
                col3_items.append(("Virtue", virt))
            col3_items.append(("Spacer", ""))
            col3_items.append(("Header", "PATH/WILLPOWER"))
            col3_items.append(("Humanity", "Humanity/Path"))
            col3_items.append(("Willpower", "Willpower"))

            layout = {
                "start_y":           content_y,
                "cx1":               cx1,
                "cx2":               cx2,
                "cx3":               cx3,
                "col_width":         col_width,
                "max_rows":          container_height - 8,
                "container_height":  container_height,
                "container_start_y": start_y,
            }

            draw_character_sheet_columns(
                self.stdscr, self.character,
                col1_items, col2_items, col3_items,
                layout,
                is_interactive=False
            )
            
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