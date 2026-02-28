# --- [IMPORTS] ---
import curses
from typing import List, Tuple
from . import utils
from . import theme
from vtm_npc_logic import VtMCharacter, ATTRIBUTES_LIST, ABILITIES_LIST, VIRTUES_LIST, FREEBIE_COSTS, DISCIPLINES_LIST, BACKGROUNDS_LIST
from .utils import QuitApplication

class MainView:
    def __init__(self, stdscr, character: VtMCharacter):
        self.stdscr = stdscr
        self.character = character
        self.message = ""
        self.message_color = theme.CLR_ACCENT()
        
        # --- [NAVIGATION STATE] ---
        # 0=Attributes, 1=Abilities, 2=Everything else
        self.active_col = 0 
        self.active_row = 0
        
        # To track list sizes for boundary checking
        self.col_counts = [0, 0, 0]
        
        # Input State (for in-place editing Disciplines/Backgrounds)
        self.is_inputting = False
        self.input_buffer = ""

    def run(self):
        """Main interaction loop using direct navigation."""
        while True:
            # Build data lists
            col1_items = self._get_col1_items()
            col2_items = self._get_col2_items()
            col3_items = self._get_col3_items()
            
            self.col_counts = [len(col1_items), len(col2_items), len(col3_items)]
            if self.active_row >= self.col_counts[self.active_col]:
                self.active_row = max(0, self.col_counts[self.active_col] - 1)
            
            # INITIAL CHECK: If user somehow landed on a header/spacer, move down
            current_list = [col1_items, col2_items, col3_items][self.active_col]
            if current_list:
                item_type = current_list[self.active_row][0]
                if item_type in ["Header", "Spacer"]:
                    self._move_cursor(1, current_list)

            self._draw_screen(col1_items, col2_items, col3_items)
            self.stdscr.refresh()
            key = self.stdscr.getch()
            
            if key == 24: return # Ctrl+X
            elif key == curses.KEY_RESIZE: 
                self.stdscr.erase()
            
            # --- Navigation ---
            elif key == curses.KEY_UP:
                current_list = [col1_items, col2_items, col3_items][self.active_col]
                self._move_cursor(-1, current_list)
                self.message = ""
            elif key == curses.KEY_DOWN:
                current_list = [col1_items, col2_items, col3_items][self.active_col]
                self._move_cursor(1, current_list)
                self.message = ""
            elif key == ord(' ') or key == 9: # Space or Tab switches columns
                self.active_col = (self.active_col + 1) % 3
                self.active_row = 0 # Reset to top of new column
                # Ensure the user doesn't land on a header after switching
                new_list = [col1_items, col2_items, col3_items][self.active_col]
                if new_list:
                    item_type = new_list[0][0]
                    if item_type in ["Header", "Spacer"]:
                        self._move_cursor(1, new_list)
                self.message = ""
            
            # --- Modification ---
            # Arrow keys ('<' & '>')
            elif key == curses.KEY_LEFT:
                self._handle_modification(col1_items, col2_items, col3_items, -1)
            elif key == curses.KEY_RIGHT:
                self._handle_modification(col1_items, col2_items, col3_items, 1)
            # Direct numeric input (0-9)
            elif 48 <= key <= 57:
                val = key - 48
                if val == 0: val = 10 # Shortcut: 0 sets value to 10
                self._handle_numeric_input(col1_items, col2_items, col3_items, val)
            
            # --- Deletion key ---
            elif key == curses.KEY_DC or key == ord('x'):
                self._handle_deletion(col1_items, col2_items, col3_items)

            # --- Special Actions ---
            elif key == ord('\n'):
                self._handle_enter(col1_items, col2_items, col3_items)

    # --- [DATA HELPERS] ---
    # These generate the lists of (Category, Name) tuples for each column.
    def _move_cursor(self, delta, items):
        """Moves cursor, skipping over 'Header' and 'Spacer' items."""
        new_row = self.active_row + delta
        max_idx = len(items) - 1
        
        # Simple bounds check first
        if new_row < 0: return
        if new_row > max_idx: return
        
        # Check if target is a Header/Spacer. 
        while 0 <= new_row <= max_idx and items[new_row][0] in ["Header", "Spacer"]:
            new_row += delta
        
        # Re-check bounds after skipping
        if 0 <= new_row <= max_idx:
            self.active_row = new_row

    def _get_col1_items(self) -> List[Tuple[str, str]]:
        # Added Header to list for auto-centering/alignment
        return [("Header", "ATTRIBUTES")] + [("Attribute", attr) for attr in ATTRIBUTES_LIST]

    def _get_col2_items(self) -> List[Tuple[str, str]]:
        # List ALL abilities so user can buy them from 0
        # Added Header to list for auto-centering/alignment
        return [("Header", "ABILITIES")] + [("Ability", abil) for abil in ABILITIES_LIST]

    def _get_col3_items(self) -> List[Tuple[str, str]]:
        items = []
        
        # Disciplines
        items.append(("Header", "DISCIPLINES"))
        for disc in self.character.disciplines: items.append(("Discipline", disc))
        items.append(("System", "Add Discipline"))
        # Backgrounds
        items.append(("Spacer", ""))
        items.append(("Header", "BACKGROUNDS"))
        for bg in self.character.backgrounds: items.append(("Background", bg))
        items.append(("System", "Add Background"))
        # Virtues
        items.append(("Spacer", ""))
        items.append(("Header", "VIRTUES"))
        for virt in VIRTUES_LIST: items.append(("Virtue", virt))
        # Path/Willpower
        items.append(("Spacer", ""))
        items.append(("Header", "PATH/WILLPOWER"))
        items.append(("Humanity", "Humanity/Path"))
        items.append(("Willpower", "Willpower"))
        
        return items

    # --- [LOGIC HANDLERS] ---
    def _handle_modification(self, c1, c2, c3, delta):
        """Handles Left/Right arrow keys to modify stats."""
        current_list = [c1, c2, c3][self.active_col]
        category, name = current_list[self.active_row]
        
         # Can't modify "Add New" buttons with arrows
        if category in ["System", "Header", "Spacer"]: return

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
        
        if category in ["System", "Header", "Spacer"]: return

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
        current_list = [c1, c2, c3][self.active_col]
        category, name = current_list[self.active_row]
        
        if category == "System":
            new_cat = "Discipline" if "Discipline" in name else "Background"
            self._add_new_trait(new_cat, c1, c2, c3)

    def _add_new_trait(self, category, c1, c2, c3):
        self.is_inputting = True
        curses.curs_set(1)
        
        # Prepare the list (exclude existing traits)
        if category == "Discipline":
            options = sorted([d for d in DISCIPLINES_LIST if d not in self.character.disciplines])
        elif category == "Background":
            options = sorted([b for b in BACKGROUNDS_LIST if b not in self.character.backgrounds])
        else:
            options = []

        # 2. Calculate coordinates for in-line inputs
        h, w = self.stdscr.getmaxyx()
        
        # Re-calculate layout (must match _draw_screen logic!!)
        container_width = min(130, w - 2)
        container_height = min(50, h - 2)
        start_x = (w - container_width) // 2
        start_y = (h - container_height) // 2
        
        col_width = (container_width - 4) // 3
        # Calculate X for col3
        col3_x = start_x + 2 + (col_width + 1) * 2
        
        # Calculate Y for the Active Row
        # Logic: Header (1) + Points (1) + Headers (2) + List Start (1) = +5 offset from start_y?
        # Verify _draw_screen: 
        # header_y = start_y + 1
        # content_y = header_y + 2 (so start_y + 3)
        # list_start_y = content_y + 1 (so start_y + 4)
        list_start_y = start_y + 4
        max_rows = container_height - 8
        
        # Calculate scroll offset for Col 3
        scroll_offset = 0
        if self.active_col == 2: # Column 3
            if self.active_row >= max_rows:
                scroll_offset = self.active_row - max_rows + 1
        
        # The visual row index (0 to max_rows)
        visual_row_index = self.active_row - scroll_offset
        
        # Final screen coordinates
        prompt_y = list_start_y + visual_row_index
        prompt_x = col3_x

        def redraw_func():
            self._draw_screen(c1, c2, c3)

        try:
            # Pass prompt="" so it looks like typing is *in* the cell
            # The get_selection_input will handle the dropdown/typing logic
            name = utils.get_selection_input(self.stdscr, "", prompt_y, prompt_x, options, redraw_func)
            
            if name:
                self.character.set_initial_trait(category.lower() + 's', name, 0)
                self.message = f"Added {name}"
                self.message_color = theme.CLR_ACCENT()
                
        except utils.InputCancelled:
            self.message = "Cancelled"
        finally:
            self.is_inputting = False
            curses.curs_set(0)

    def _handle_deletion(self, c1, c2, c3):
        current_list = [c1, c2, c3][self.active_col]
        if not current_list: return
        
        category, name = current_list[self.active_row]
        
        # Validation
        if category not in ["Discipline", "Background"] or name == "System" or category in ["Header", "Spacer"]:
            self.message = "Can only remove added Disciplines or Backgrounds."
            self.message_color = theme.CLR_ERROR()
            return

        # Prepare Data
        trait_data = self.character.get_trait_data(category, name)
        refund = (trait_data['new'] - trait_data['base']) * FREEBIE_COSTS.get(category, 0)
        
        # Draw the screen first so the pop-up layers over it properly
        self._draw_screen(c1, c2, c3)
        
        # Call the confirmation pop-up
        msg = f"Are you sure you want to completely remove {name}?\n\nThis will refund {refund} Freebie Points."
        confirm = utils.show_confirmation_popup(self.stdscr, "Confirm Deletion", msg, theme.CLR_ACCENT())
        
        if confirm:
            success, msg = self.character.remove_trait(category, name)
            self.message = msg
            self.message_color = theme.CLR_ACCENT()
            # Move cursor up one to avoid landing on a potentially shifted index or out of bounds
            if self.active_row > 0: self.active_row -= 1
        else:
            self.message = "Deletion cancelled."
            self.message_color = theme.CLR_TEXT()

    # --- [DRAWING] ---
    def _draw_screen(self, col1, col2, col3):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.erase()
        
        # Maximized width
        container_width = min(130, w - 2)
        container_height = min(50, h - 2)
        start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
        
        utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, "VTM NPC Progression Tool")
        
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
        
        # ---------------------------------------------------------------------------------
        # ! Headers removed from here because they are now part of the data lists.
        # This makes sure they scroll and align exactly like the rest of the content.
        # ---------------------------------------------------------------------------------
        
        # Draw Separators
        for i in range(content_y + 1, start_y + container_height - 1):
            self.stdscr.addstr(i, cx2 - 1, theme.SYM_BORDER_V, theme.CLR_BORDER())
            self.stdscr.addstr(i, cx3 - 1, theme.SYM_BORDER_V, theme.CLR_BORDER())

        # Draw columns
        # ! Start list drawing immediately at content_y
        list_start_y = content_y
        max_rows = container_height - 7
        
        self._draw_column(list_start_y, cx1, col_width, col1, 0, max_rows)
        self._draw_column(list_start_y, cx2, col_width, col2, 1, max_rows)
        self._draw_column(list_start_y, cx3, col_width, col3, 2, max_rows)

        # Footer
        if self.message:
            utils.draw_wrapped_text(self.stdscr, start_y + container_height - 2, start_x + 2, self.message, container_width - 4, self.message_color)
        else:
            # Controls
            controls = "Arrows/0-9: Modify | Space: Next Col | Enter: Add/Select | Ctrl+X: Done"
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
            
            if cat == "Header":
                header_text = f"{theme.SYM_HEADER_L}{name}{theme.SYM_HEADER_R}"
                pad = (width - len(header_text)) // 2
                self.stdscr.addstr(start_y + i, start_x + max(0, pad), header_text[:width], theme.CLR_BORDER())
                continue
            
            if cat == "Spacer":
                continue 

            is_selected = (self.active_col == col_idx and self.active_row == idx)
            
            draw_x = start_x + 2
            max_text_w = width - 8
            
            # --- In-place input rendering ---
            if is_selected:
                style = theme.CLR_HIGHLIGHT()
                # Draw the input box logic: < Poten_ >
                # Note: append '_' to show the cursor position clearly
                if cat == "System":
                    text = f"[ {name} ]"
                    val_str = ""
                else:
                    data = self.character.get_trait_data(cat, name)
                    text = name
                    val_str = f"[{data['new']}]"
                display_str = f"{theme.SYM_SELECTED_L}{text:<{max_text_w}}{val_str}{theme.SYM_SELECTED_R}"
                
                self.stdscr.addstr(start_y + i, draw_x - 2, display_str, style)
            else:
                # Check modifications for Color
                # Standard unselected behavior
                if cat == "System":
                    text = f"[ {name} ]"
                    val_str = ""
                else:
                    data = self.character.get_trait_data(cat, name)
                    text = name
                    val_str = f"[{data['new']}]"

                is_modified = False
                if cat != "System":
                    data = self.character.get_trait_data(cat, name)
                    # Traits are red if value changed OR if they are dynamic additions (Disciplines/Backgrounds)
                    if data['base'] != data['new'] or cat in ["Discipline", "Background"]:
                        is_modified = True
                
                style = theme.CLR_ACCENT() if is_modified else theme.CLR_TEXT()
                display_str = f"{text:<{max_text_w}}{val_str}"
                self.stdscr.addstr(start_y + i, draw_x, display_str, style)