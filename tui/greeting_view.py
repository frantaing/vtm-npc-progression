# Imports
import curses
from . import utils
from . import theme

class GreetingView:
    def __init__(self, stdscr):
        self.stdscr = stdscr

    def run(self) -> bool:
        """
        Displays the initial mode selection screen.
        Returns:
            bool: True if Free Mode is selected, False for Default Mode.
        Raises:
            utils.QuitApplication: If the user presses Ctrl+X.
        """
        modes = [
            {
                "name": "Default Mode",
                "desc": "Standard character progression. Freebie Points are calculated based on the character's age, limiting improvements."
            },
            {
                "name": "Free Mode",
                "desc": "Build any character you can imagine. Freebie Points are unlimited, allowing for unrestricted character improvement."
            }
        ]
        selected = 0
        
        while True:
            h, w = self.stdscr.getmaxyx()
            self.stdscr.erase() # Changed from clear() to erase()
            
            container_width, container_height = 70, 16
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
            
            utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, "Welcome")
            
            title = "VTM NPC Progression Tool"
            self.stdscr.addstr(start_y + 2, start_x + (container_width - len(title)) // 2, title, theme.CLR_TITLE())
            self.stdscr.addstr(start_y + 4, start_x + 2, "Please select a mode:", theme.CLR_TEXT())
            
            # Draw menu options
            for i, mode in enumerate(modes):
                style = theme.CLR_SELECTED() if i == selected else theme.CLR_TEXT()
                prefix = theme.SYM_POINTER if i == selected else "  "
                self.stdscr.addstr(start_y + 6 + i, start_x + 4, f"{prefix}{mode['name']}  ", style)
            
            desc_box_y = start_y + 9
            self.stdscr.addstr(desc_box_y, start_x + 3, theme.SYM_BORDER_H * (container_width - 6), theme.CLR_BORDER())
            
            utils.draw_wrapped_text(self.stdscr, desc_box_y + 2, start_x + 4, modes[selected]['desc'], container_width - 8, theme.CLR_ACCENT())
            
            # Color is now CLR_ACCENT
            controls = "↑/↓: Navigate | Enter: Select | Ctrl+X: Exit"
            self.stdscr.addstr(h - 1, (w - len(controls)) // 2, controls, theme.CLR_ACCENT())
            
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            if key == 24: raise utils.QuitApplication()
            elif key in (curses.KEY_UP, curses.KEY_LEFT): selected = (selected - 1 + len(modes)) % len(modes)
            elif key in (curses.KEY_DOWN, curses.KEY_RIGHT): selected = (selected + 1) % len(modes)
            elif key in (curses.KEY_ENTER, ord('\n')):
                return selected == 1