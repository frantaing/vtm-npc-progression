import curses
from typing import NamedTuple, Optional
from . import utils
from . import theme
from .save_manager import list_saves, load_character, default_save_name
from vtm_npc_logic import VtMCharacter

# --- [RESULT TYPE] ---
class GreetingResult(NamedTuple):
    mode: str  # "default", "free", "load"
    character: Optional[VtMCharacter] = None

class GreetingView:
    def __init__(self, stdscr):
        self.stdscr = stdscr

    def run(self) -> GreetingResult:
        """
        Displays the mode selection screen.
        Returns a GreetingResult with mode and optionally a loaded character.
        Raises utils.QuitApplication if the user presses Ctrl+X.
        """
        modes = [
            {
                "name": "Default Mode",
                "desc": "Standard character progression. Freebie Points are calculated based on the character's age, limiting improvements."
            },
            {
                "name": "Free Mode",
                "desc": "Build any character you can imagine. Freebie Points are unlimited, allowing for unrestricted character improvement."
            },
            {
                "name": "Load Character",
                "desc": "Load a previously saved character from a JSON save file and continue editing."
            }
        ]
        selected = 0

        while True:
            h, w = self.stdscr.getmaxyx()
            self.stdscr.erase()

            container_width, container_height = 70, 17
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2

            utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, "Welcome")

            title = "VTM NPC Progression Tool"
            self.stdscr.addstr(start_y + 2, start_x + (container_width - len(title)) // 2, title, theme.CLR_TITLE())
            self.stdscr.addstr(start_y + 4, start_x + 2, "Please select a mode:", theme.CLR_TEXT())

            for i, mode in enumerate(modes):
                style = theme.CLR_SELECTED() if i == selected else theme.CLR_TEXT()
                prefix = theme.SYM_POINTER if i == selected else "  "
                self.stdscr.addstr(start_y + 6 + i, start_x + 4, f"{prefix}{mode['name']}  ", style)

            desc_box_y = start_y + 10
            self.stdscr.addstr(desc_box_y, start_x + 3, theme.SYM_BORDER_H * (container_width - 6), theme.CLR_BORDER())
            utils.draw_wrapped_text(self.stdscr, desc_box_y + 2, start_x + 4, modes[selected]['desc'], container_width - 8, theme.CLR_ACCENT())

            controls = "↑/↓: Navigate | Enter: Select | Ctrl+X: Exit"
            self.stdscr.addstr(h - 1, (w - len(controls)) // 2, controls, theme.CLR_ACCENT())

            self.stdscr.refresh()

            key = self.stdscr.getch()
            if key == 24:
                raise utils.QuitApplication()
            elif key in (curses.KEY_UP, curses.KEY_LEFT):
                selected = (selected - 1 + len(modes)) % len(modes)
            elif key in (curses.KEY_DOWN, curses.KEY_RIGHT):
                selected = (selected + 1) % len(modes)
            elif key in (curses.KEY_ENTER, ord('\n')):
                if selected == 0:
                    return GreetingResult(mode="default")
                elif selected == 1:
                    return GreetingResult(mode="free")
                elif selected == 2:
                    result = self._load_character_flow()
                    if result is not None:
                        return result
                    # If load was cancelled, stay on greeting screen

    def _load_character_flow(self) -> Optional[GreetingResult]:
        """
        Handles the load character sub-flow.
        Returns a GreetingResult on success, or None if cancelled.
        """
        saves = list_saves()

        def draw_load_screen():
            h, w = self.stdscr.getmaxyx()
            self.stdscr.erase()
            container_width, container_height = 70, 14
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
            utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, "Load Character")
            if saves:
                self.stdscr.addstr(start_y + 2, start_x + 2, "Select a save file or type a filename:", theme.CLR_TEXT())
            else:
                self.stdscr.addstr(start_y + 2, start_x + 2, "No saves found. Type a filename to load:", theme.CLR_TEXT())
            return start_y, start_x, start_y + 4

        try:
            start_y, start_x, input_y = draw_load_screen()
            filename = utils.get_file_selection_input(
                self.stdscr, "File: ", input_y, start_x + 2,
                saves, draw_load_screen
            )
        except utils.InputCancelled:
            return None

        success, result = load_character(filename)

        if success:
            utils.show_popup(self.stdscr, "Loaded", f"Loaded '{result.name}' successfully!", theme.CLR_ACCENT())
            return GreetingResult(mode="load", character=result)
        else:
            utils.show_popup(self.stdscr, "Error", result, theme.CLR_ERROR())
            return None