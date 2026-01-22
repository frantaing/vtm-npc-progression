# tui/main_view.py

import curses
from typing import Dict, Any, Optional, List, Tuple
from . import utils
from . import theme
from vtm_npc_logic import VtMCharacter, ATTRIBUTES_LIST, ABILITIES_LIST, VIRTUES_LIST, FREEBIE_COSTS

class MainView:
    def __init__(self, stdscr, character: VtMCharacter):
        self.stdscr = stdscr
        self.character = character
        self.message = ""
        self.message_color = theme.CLR_ACCENT()
        
        # --- [NAVIGATION STATE] ---
        # 0=Attributes, 1=Abilities, 2=Other
        self.active_col = 0 
        self.active_row = 0
        
        # To track list sizes for boundary checking
        self.col_counts = [0, 0, 0]

    def run(self):
        """Main interaction loop using direct navigation."""
        while True:
            # 1. Build Data Lists for this Frame
            col1_items = self._get_col1_items()
            col2_items = self._get_col2_items()
            col3_items = self._get_col3_items()
            
            # Update counts to prevent out-of-bounds errors
            self.col_counts = [len(col1_items), len(col2_items), len(col3_items)]
            
            # Clamp cursor if list shrank or if user switched columns
            if self.active_row >= self.col_counts[self.active_col]:
                self.active_row = max(0, self.col_counts[self.active_col] - 1)

            # 2. Draw Screen
            self._draw_screen(col1_items, col2_items, col3_items)
            self.stdscr.refresh()
            
            # 3. Handle input
            key = self.stdscr.getch()
            
            if key == 24: return # Ctrl+X
            elif key == curses.KEY_RESIZE: 
                self.stdscr.erase()
            
            # --- Navigation ---
            elif key == curses.KEY_UP:
                self.active_row = max(0, self.active_row - 1)
                self.message = ""
            elif key == curses.KEY_DOWN:
                self.active_row = min(self.col_counts[self.active_col] - 1, self.active_row + 1)
                self.message = ""
            elif key == ord(' ') or key == 9: # Space or Tab switches columns
                self.active_col = (self.active_col + 1) % 3
                self.active_row = 0 # Reset to top of new column
                self.message = ""
            
            # --- Incremental modification (Arrows) ---
            elif key == curses.KEY_LEFT:
                self._handle_modification(col1_items, col2_items, col3_items, -1)
            elif key == curses.KEY_RIGHT:
                self._handle_modification(col1_items, col2_items, col3_items, 1)
            
            # --- Direct numeric input (0-9) ---
            elif 48 <= key <= 57:
                val = key - 48
                if val == 0: val = 10 # Shortcut: 0 sets value to 10
                self._handle_numeric_input(col1_items, col2_items, col3_items, val)

            # --- Special Actions ---
            elif key == ord('\n'):
                self._handle_enter(col1_items, col2_items, col3_items)

    # --- [DATA HELPERS] ---
    # These generate the lists of (Category, Name) tuples for each column.
    
    def _get_col1_items(self) -> List[Tuple[str, str]]:
        return [("Attribute", attr) for attr in ATTRIBUTES_LIST]

    def _get_col2_items(self) -> List[Tuple[str, str]]:
        # List ALL abilities so user can buy them from 0
        return [("Ability", abil) for abil in ABILITIES_LIST]

    def _get_col3_items(self) -> List[Tuple[str, str]]:
        items = []
        # Disciplines
        for disc in self.character.disciplines: items.append(("Discipline", disc))
        items.append(("System", "Add Discipline"))
        # Backgrounds
        for bg in self.character.backgrounds: items.append(("Background", bg))
        items.append(("System", "Add Background"))
        # Virtues
        for virt in VIRTUES_LIST: items.append(("Virtue", virt))
        items.append(("Humanity", "Humanity/Path"))
        items.append(("Willpower", "Willpower"))
        return items

    # --- [LOGIC HANDLERS] ---
    def _handle_modification(self, c1, c2, c3, delta):
        """Handles Left/Right arrow keys to modify stats."""
        current_list = [c1, c2, c3][self.active_col]
        category, name = current_list[self.active_row]
        
        # Can't modify "Add New" buttons with arrows
        if category == "System": return

        # Get current data
        trait_data = self.character.get_trait_data(category, name)
        current_val = trait_data['new']
        target_val = current_val + delta
        
        # Attempt improvement (logic handles bounds and cost)
        success, msg = self.character.improve_trait(category, name, target_val)
        
        if success:
            self.message = msg
            self.message_color = theme.CLR_ACCENT()
        else:
            # Show errors (like "Not enough points" or "Min value reached")
            # For silent bounds checking, check if msg contains "limit" logic
            if "Not enough points" in msg:
                self.message = msg
                self.message_color = theme.CLR_ERROR()
            else:
                self.message = ""

    # --- Helper for Number Keys ---
    def _handle_numeric_input(self, c1, c2, c3, value):
        """Handles pressing keys 0-9 to jump directly to a value."""
        current_list = [c1, c2, c3][self.active_col]
        category, name = current_list[self.active_row]
        
        if category == "System": return

        # Attempt to set the trait directly to 'value'
        success, msg = self.character.improve_trait(category, name, value)
        
        if success:
            self.message = msg
            self.message_color = theme.CLR_ACCENT()
        else:
            # Sshow errors for bounds (e.g. trying to set 9 when max is 5)
            # Or cost issues
            self.message = msg
            self.message_color = theme.CLR_ERROR()

    def _handle_enter(self, c1, c2, c3):
        """Handles Enter key for System buttons."""
        current_list = [c1, c2, c3][self.active_col]
        category, name = current_list[self.active_row]
        
        if category == "System":
            new_cat = "Discipline" if "Discipline" in name else "Background"
            self._add_new_trait(new_cat)

    def _add_new_trait(self, category):
        h, w = self.stdscr.getmaxyx()
        prompt_y = h - 3
        def dummy_redraw(): pass
        
        try:
            name = utils.get_string_input(self.stdscr, f"New {category} Name: ", prompt_y, 2, dummy_redraw)
            if name:
                # Add with base 0
                self.character.set_initial_trait(category.lower() + 's', name, 0)
                self.message = f"Added {name}"
                self.message_color = theme.CLR_ACCENT()
        except utils.InputCancelled:
            self.message = "Cancelled"

    # --- [DRAWING] ---
    def _draw_screen(self, col1, col2, col3):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.erase()
        
        # Maximized width
        container_width = min(130, w - 2)
        container_height = min(50, h - 2)
        start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
        
        utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, "VTM Elder Creator")
        
        # Header Info
        header_y = start_y + 1
        info_str = f"{self.character.name} ({self.character.clan}) | Age: {self.character.age} | Gen: {self.character.generation}th"
        self.stdscr.addstr(header_y, start_x + 2, info_str, theme.CLR_TITLE())
        
        # Freebie Points
        header_y += 1
        if self.character.is_free_mode:
            spent_str = f"Freebie Points Spent: {self.character.spent_freebies}"
            color = theme.CLR_ACCENT()
        else:
            remaining = self.character.total_freebies - self.character.spent_freebies
            spent_str = f"Freebie: {remaining}/{self.character.total_freebies}"
            color = theme.CLR_ACCENT() if remaining > 0 else theme.CLR_ERROR()
        self.stdscr.addstr(header_y, start_x + 2, spent_str, color)

        # 3-Column Calculations
        col_width = (container_width - 4) // 3
        cx1 = start_x + 2
        cx2 = cx1 + col_width + 1
        cx3 = cx2 + col_width + 1
        
        content_y = header_y + 2
        
        # Draw Headers
        self.stdscr.addstr(content_y, cx1, f"{theme.SYM_HEADER_L}ATTRIBUTES{theme.SYM_HEADER_R}"[:col_width], theme.CLR_BORDER())
        self.stdscr.addstr(content_y, cx2, f"{theme.SYM_HEADER_L}ABILITIES{theme.SYM_HEADER_R}"[:col_width], theme.CLR_BORDER())
        self.stdscr.addstr(content_y, cx3, f"{theme.SYM_HEADER_L}OTHERS{theme.SYM_HEADER_R}"[:col_width], theme.CLR_BORDER())
        
        # Draw Separators
        for i in range(content_y + 1, start_y + container_height - 1):
            self.stdscr.addstr(i, cx2 - 1, theme.SYM_BORDER_V, theme.CLR_BORDER())
            self.stdscr.addstr(i, cx3 - 1, theme.SYM_BORDER_V, theme.CLR_BORDER())

        # Draw Columns
        list_start_y = content_y + 1
        max_rows = container_height - 8
        
        self._draw_column(list_start_y, cx1, col_width, col1, 0, max_rows)
        self._draw_column(list_start_y, cx2, col_width, col2, 1, max_rows)
        self._draw_column(list_start_y, cx3, col_width, col3, 2, max_rows)

        # Footer
        if self.message:
            utils.draw_wrapped_text(self.stdscr, start_y + container_height - 2, start_x + 2, self.message, container_width - 4, self.message_color)
        else:
            # --- [MODIFIED] Help text to indicate numeric input
            controls = "Arrows/0-9: Modify | Space: Next Col | Enter: Add | Ctrl+X: Done"
            self.stdscr.addstr(start_y + container_height - 2, start_x + (container_width - len(controls))//2, controls, theme.CLR_ACCENT())

    def _draw_column(self, start_y, start_x, width, items, col_idx, max_rows):
        # Calculate scroll offset
        scroll_offset = 0
        if self.active_col == col_idx:
            if self.active_row >= max_rows:
                scroll_offset = self.active_row - max_rows + 1
        
        for i in range(max_rows):
            idx = scroll_offset + i
            if idx >= len(items): break
            
            cat, name = items[idx]
            is_selected = (self.active_col == col_idx and self.active_row == idx)
            
            # Format text
            if cat == "System":
                text = f"[ {name} ]"
                val_str = ""
            else:
                data = self.character.get_trait_data(cat, name)
                text = name
                # Standard display: [5]
                val_str = f"[{data['new']}]"
            
            # Calculate Colors & Padding
            # Shift 'x' by 2 for padding, reduce Width by 4 (2 for padding, 2 for safety)
            draw_x = start_x + 2
            max_text_w = width - 8
            
            if is_selected:
                style = theme.CLR_HIGHLIGHT()
                # Draw with Gold Selection Indicators < ... >
                display_str = f"{theme.SYM_SELECTED_L}{text:<{max_text_w}}{val_str}{theme.SYM_SELECTED_R}"
                # If selected, draw slightly to the left to fit the arrows
                self.stdscr.addstr(start_y + i, draw_x - 2, display_str, style)
            else:
                # Check modifications for Color
                is_modified = False
                if cat != "System":
                    data = self.character.get_trait_data(cat, name)
                    if data['base'] != data['new']:
                        is_modified = True
                
                style = theme.CLR_ACCENT() if is_modified else theme.CLR_TEXT()
                display_str = f"{text:<{max_text_w}}{val_str}"
                self.stdscr.addstr(start_y + i, draw_x, display_str, style)