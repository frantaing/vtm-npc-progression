#!/usr/bin/env python3

"""
vtm_npc_Tui.py

This module contains the UI for the tool. It handles all rendering and
user input, and uses on vtm_npc_logic.py for character management.
"""

# --- [IMPORTS] ---
import curses
import sys
import traceback
from tui.utils import QuitApplication
from tui.greeting_view import GreetingView
from tui.setup_view import SetupView
from tui.main_view import MainView
from tui.final_view import FinalView
from tui import theme # Theme import here!

# --- [TUI ORCHESTRATOR] ---
class TUIApp:
    """Manages the overall application flow and views."""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.character = None
        
        # Hide cursor and enable keypad
        curses.curs_set(0)
        self.stdscr.keypad(True)
        
        # Initialize the Theme
        theme.init_colors()

    def run(self):
        """Main application orchestrator."""
        is_free_mode = False
        try:
            # 0. Greeting
            greeting_view = GreetingView(self.stdscr)
            is_free_mode = greeting_view.run()

            # 1. Setup
            setup_view = SetupView(self.stdscr)
            self.character = setup_view.run(is_free_mode=is_free_mode)
            if not self.character:
                return 

            # 2. Main Interaction
            main_view = MainView(self.stdscr, self.character)
            main_view.run()

        except QuitApplication:
            pass
        
        # 3. Final Display
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
        print("\nExiting program. Goodbye!")
    except KeyboardInterrupt:
        print("\nExiting program. Goodbye!")
    except Exception as e:
        traceback.print_exc()
        input(f"\nAn error occurred: {e}. Press Enter to exit.")