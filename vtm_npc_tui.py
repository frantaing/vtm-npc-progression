#!/usr/bin/env python3

"""
vtm_tui.py

This module contains the UI for the tool. It handles all rendering and
user input, and uses on vtm_npc_logic.py for character management.
"""

# --- [IMPORTS] ---
import curses
import sys
import traceback
from tui.utils import QuitApplication
from tui.setup_view import SetupView
from tui.main_view import MainView
from tui.final_view import FinalView

# --- [TUI ORCHESTRATOR] ---
class TUIApp:
    """Manages the overall application flow and views."""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.character = None
        
        # Initialize colors
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        
        curses.curs_set(0)
        self.stdscr.keypad(True)

    def run(self):
        """Main application orchestrator."""
        try:
            # 1: Setup
            setup_view = SetupView(self.stdscr)
            self.character = setup_view.run()
            if not self.character:
                return # User quit during initial setup

            # 2: Main Interaction
            main_view = MainView(self.stdscr, self.character)
            main_view.run()

        except QuitApplication:
            # This will catch Ctrl+X from any view after setup is complete
            pass
        
        # 3: Final Display (only if a character was created)
        if self.character:
            final_view = FinalView(self.stdscr, self.character)
            final_view.show()

# --- [APP] ---
def main(stdscr):
    """The main entry point for the curses application."""
    app = TUIApp(stdscr)
    app.run()

# --- [MAIN] ---
if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except QuitApplication:
        # This catches Ctrl+X only if it's raised during the initial setup
        print("\nExiting program. Goodbye!")
    except KeyboardInterrupt:
        print("\nExiting program. Goodbye!")
    except Exception as e:
        traceback.print_exc()
        input(f"\nAn error occurred: {e}. Press Enter to exit.")