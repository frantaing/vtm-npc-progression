# --- [IMPORTS] ---
import curses
from typing import List, Tuple
from . import utils
from . import theme
from vtm_npc_logic import VtMCharacter, ATTRIBUTES_LIST, ABILITIES_LIST, VIRTUES_LIST, FREEBIE_COSTS, DISCIPLINES_LIST, BACKGROUNDS_LIST
from .utils import QuitApplication
from .renderer import draw_character_sheet_columns, draw_sheet_container, SheetItem

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

    def move_selection(self, delta: int, items: list):
        """Moves cursor by delta, skipping Header and Spacer items."""
        new_row = self.active_row + delta
        max_idx = len(items) - 1

        if new_row < 0 or new_row > max_idx:
            return

        while 0 <= new_row <= max_idx and items[new_row].category in ("Header", "Spacer"):
            new_row += delta

        if 0 <= new_row <= max_idx:
            self.active_row = new_row

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

    def _get_col1_items(self) -> list:
        items = [SheetItem("Header", "ATTRIBUTES")]
        for attr in ATTRIBUTES_LIST:
            data = self.character.get_trait_data("Attribute", attr)
            items.append(SheetItem("Attribute", attr, data))
        return items

    def _get_col2_items(self) -> list:
        items = [SheetItem("Header", "ABILITIES")]
        for abil in ABILITIES_LIST:
            data = self.character.get_trait_data("Ability", abil)
            items.append(SheetItem("Ability", abil, data))
        return items

    def _get_col3_items(self) -> list:
        items = []

        items.append(SheetItem("Header", "DISCIPLINES"))
        for disc in self.character.disciplines:
            data = self.character.get_trait_data("Discipline", disc)
            items.append(SheetItem("Discipline", disc, data))
        items.append(SheetItem("System", "Add Discipline"))

        items.append(SheetItem("Spacer", ""))
        items.append(SheetItem("Header", "BACKGROUNDS"))
        for bg in self.character.backgrounds:
            data = self.character.get_trait_data("Background", bg)
            items.append(SheetItem("Background", bg, data))
        items.append(SheetItem("System", "Add Background"))

        items.append(SheetItem("Spacer", ""))
        items.append(SheetItem("Header", "VIRTUES"))
        for virt in VIRTUES_LIST:
            data = self.character.get_trait_data("Virtue", virt)
            items.append(SheetItem("Virtue", virt, data))

        items.append(SheetItem("Spacer", ""))
        items.append(SheetItem("Header", "PATH/WILLPOWER"))
        items.append(SheetItem("Humanity", "Humanity/Path", self.character.get_trait_data("Humanity", "Humanity/Path")))
        items.append(SheetItem("Willpower", "Willpower", self.character.get_trait_data("Willpower", "Willpower")))

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

        if category == "Discipline":
            options = sorted([d for d in DISCIPLINES_LIST if d not in self.character.disciplines])
        elif category == "Background":
            options = sorted([b for b in BACKGROUNDS_LIST if b not in self.character.backgrounds])
        else:
            options = []

        h, w = self.stdscr.getmaxyx()
        container_width = min(130, w - 2)
        container_height = min(50, h - 2)

        # Build freebie string (needed to call draw_sheet_container to get accurate layout)
        if self.character.is_free_mode:
            freebie_str = f"Freebie Points Spent: {self.character.spent_freebies}"
            freebie_color = theme.CLR_ACCENT()
        else:
            remaining = self.character.total_freebies - self.character.spent_freebies
            freebie_str = f"Freebie: {remaining}/{self.character.total_freebies}"
            freebie_color = theme.CLR_ACCENT() if remaining > 0 else theme.CLR_ERROR()

        # Get the same layout dict _draw_screen uses so coordinates match exactly
        layout = draw_sheet_container(
            self.stdscr, self.character,
            "VTM NPC Progression Tool",
            freebie_str, freebie_color,
            container_width, container_height
        )
        layout["start_y"] = layout["content_y"]
        layout["max_rows"] = container_height - 7

        list_start_y = layout["content_y"]
        col3_x = layout["cx3"]
        max_rows = layout["max_rows"]

        scroll_offset = 0
        if self.active_col == 2:
            if self.active_row >= max_rows:
                scroll_offset = self.active_row - max_rows + 1

        visual_row_index = self.active_row - scroll_offset
        prompt_y = list_start_y + visual_row_index
        prompt_x = col3_x

        def redraw_func():
            self._draw_screen(c1, c2, c3)

        try:
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

        container_width = min(130, w - 2)
        container_height = min(50, h - 2)

        # Format freebie string
        if self.character.is_free_mode:
            freebie_str = f"Freebie Points Spent: {self.character.spent_freebies}"
            freebie_color = theme.CLR_ACCENT()
        else:
            remaining = self.character.total_freebies - self.character.spent_freebies
            freebie_str = f"Freebie: {remaining}/{self.character.total_freebies}"
            freebie_color = theme.CLR_ACCENT() if remaining > 0 else theme.CLR_ERROR()

        layout = draw_sheet_container(
            self.stdscr, self.character,
            "VTM NPC Progression Tool",
            freebie_str, freebie_color,
            container_width, container_height
        )

        # Remap content_y -> start_y for draw_character_sheet_columns
        layout["start_y"] = layout["content_y"]
        layout["max_rows"] = container_height - 7

        draw_character_sheet_columns(
            self.stdscr, self.character,
            col1, col2, col3,
            layout,
            active_col=self.active_col,
            active_row=self.active_row,
            is_interactive=True
        )

        # Footer
        start_y = layout["container_start_y"]
        start_x = layout["start_x"]
        if self.message:
            utils.draw_wrapped_text(self.stdscr, start_y + container_height - 2, start_x + 2, self.message, container_width - 4, self.message_color)
        else:
            controls = "Arrows/0-9: Modify | Space: Next Col | Enter: Add/Select | Ctrl+X: Done"
            self.stdscr.addstr(start_y + container_height - 2, start_x + (container_width - len(controls)) // 2, controls, theme.CLR_ACCENT())