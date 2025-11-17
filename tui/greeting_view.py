# tui/greeting_view.py

import curses
from . import utils

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
            self.stdscr.clear()
            
            container_width, container_height = 70, 16
            start_x, start_y = (w - container_width) // 2, (h - container_height) // 2
            
            utils.draw_box(self.stdscr, start_y, start_x, container_height, container_width, "Welcome")
            
            title = "VTM NPC Progression Tool"
            self.stdscr.addstr(start_y + 2, start_x + (container_width - len(title)) // 2, title, curses.color_pair(utils.COLOR_MAGENTA) | curses.A_BOLD)
            self.stdscr.addstr(start_y + 4, start_x + 2, "Please select a mode:")
            
            # Draw menu options
            for i, mode in enumerate(modes):
                style = curses.A_REVERSE if i == selected else curses.A_NORMAL
                self.stdscr.addstr(start_y + 6 + i, start_x + 4, f"  {mode['name']}  ", style)
            
            # Draw description box at the bottom
            desc_box_y = start_y + 9
            desc_box_height = container_height - 10
            self.stdscr.addstr(desc_box_y, start_x + 3, "─" * (container_width - 6))
            
            # Draw the description of the selected mode
            utils.draw_wrapped_text(self.stdscr, desc_box_y + 2, start_x + 4, modes[selected]['desc'], container_width - 8, utils.COLOR_YELLOW)
            
            controls = "↑/↓: Navigate | Enter: Select | Ctrl+X: Exit"
            self.stdscr.addstr(h - 1, (w - len(controls)) // 2, controls, curses.color_pair(utils.COLOR_YELLOW))
            
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            if key == 24: raise utils.QuitApplication()
            elif key in (curses.KEY_UP, curses.KEY_LEFT): selected = (selected - 1 + len(modes)) % len(modes)
            elif key in (curses.KEY_DOWN, curses.KEY_RIGHT): selected = (selected + 1) % len(modes)
            elif key in (curses.KEY_ENTER, ord('\n')):
                return selected == 1 # Returns True if Free Mode (index 1) is selected