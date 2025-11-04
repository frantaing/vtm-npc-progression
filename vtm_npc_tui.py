#!/usr/bin/env python3

# --- IMPORTS ---
import curses
import sys
import math
from typing import Dict, List, Tuple, Optional

# --- DATA ---
GENERATION_DATA = {
    2: {"max_trait": 10}, 3: {"max_trait": 10}, 4: {"max_trait": 9},
    5: {"max_trait": 8}, 6: {"max_trait": 7}, 7: {"max_trait": 6},
    8: {"max_trait": 5}, 9: {"max_trait": 5}, 10: {"max_trait": 5},
    11: {"max_trait": 5}, 12: {"max_trait": 5}, 13: {"max_trait": 5},
    14: {"max_trait": 5}, 15: {"max_trait": 5}, 16: {"max_trait": 5}
}

AGE_FREEBIE_BRACKETS = [
    (50, 45), (100, 90), (200, 150), (350, 225), (550, 315),
    (800, 390), (1100, 465), (1450, 525), (1850, 585), (2300, 630),
    (2800, 675), (3350, 705), (3950, 735), (5600, 750)
]

FREEBIE_COSTS = {
    "Attribute": 5, "Ability": 2, "Discipline": 7,
    "Background": 1, "Virtue": 2, "Humanity": 1, "Willpower": 1
}

ATTRIBUTES_LIST = [
    "Strength", "Dexterity", "Stamina",                 # Physical
    "Charisma", "Manipulation", "Appearance",           # Social
    "Perception", "Intelligence", "Wits"                # Mental
]

ABILITIES_LIST = [
    # Talents
    "Alertness", "Athletics", "Awareness", "Brawl", "Empathy",
    "Expression", "Intimidation", "Leadership", "Streetwise", "Subterfuge",
    # Skills
    "Animal Ken", "Crafts", "Drive", "Etiquette", "Firearms",
    "Larceny", "Melee", "Performance", "Stealth", "Survival",
    # Knowledges
    "Academics", "Computer", "Finance", "Investigation", "Law",
    "Medicine", "Occult", "Politics", "Science", "Technology"
]

VIRTUES_LIST = ["Conscience", "Self-Control", "Courage"]

# --- CHARACTER CLASS ---
class VtMCharacter:
    """Stores and manages a VtM character's progression."""

    def __init__(self, name, clan, age, generation):
        self.name = name
        self.clan = clan
        self.age = age
        self.generation = generation

        self.attributes = {}
        self.abilities = {}
        self.disciplines = {}
        self.backgrounds = {}
        self.virtues = {}
        self.humanity = {"base": 0, "new": 0}
        self.willpower = {"base": 0, "new": 0}

        self.max_trait_rating = GENERATION_DATA.get(generation, {}).get("max_trait", 5)
        self.total_freebies = self._calculate_total_freebies()
        self.spent_freebies = 0

    def _calculate_total_freebies(self):
        for upper_age, points in AGE_FREEBIE_BRACKETS:
            if self.age <= upper_age:
                return points
        return AGE_FREEBIE_BRACKETS[-1][1]

    def set_initial_trait(self, category, trait_name, value):
        trait_dict = getattr(self, category)
        trait_dict[trait_name] = {"base": value, "new": value}

    def set_initial_value(self, category, value):
        stat = getattr(self, category)
        stat["base"] = value
        stat["new"] = value

    def get_trait_data(self, category_name, trait_name):
        if category_name in ["Attribute", "Ability", "Discipline", "Background", "Virtue"]:
            attr_name = "abilities" if category_name == "Ability" else f"{category_name.lower()}s"
            trait_pool = getattr(self, attr_name)
            return trait_pool.get(trait_name, {"base": 0, "new": 0})
        else:
            return getattr(self, category_name.lower())

    def improve_trait(self, category_name, trait_name, target_value):
        cost_per_dot = FREEBIE_COSTS[category_name]
        remaining_points = self.total_freebies - self.spent_freebies

        if category_name in ["Attribute", "Ability", "Discipline", "Background", "Virtue"]:
            trait_pool = getattr(self, "abilities" if category_name == "Ability" else f"{category_name.lower()}s")
            if trait_name not in trait_pool:
                trait_pool[trait_name] = {"base": 0, "new": 0}
            trait_data = trait_pool[trait_name]
        else:
            trait_data = getattr(self, category_name.lower())

        current_rating = trait_data["new"]

        if target_value <= current_rating:
            return False, f"New value must be higher than current ({current_rating})"

        dots_to_add = target_value - current_rating
        total_cost = dots_to_add * cost_per_dot

        if remaining_points < total_cost:
            return False, f"Not enough points! Cost: {total_cost}, Available: {remaining_points}"

        trait_data["new"] = target_value
        self.spent_freebies += total_cost
        return True, f"'{trait_name}' raised to {target_value}. Cost: {total_cost} points"
    """Stores and manages a VtM character's progression."""

    # Initialize character values
    def __init__(self, name, clan, age, generation):
        self.name = name
        self.clan = clan
        self.age = age
        self.generation = generation

        # Dictionaries to hold traits. Format: { "Trait Name": {"base": X, "new": Y} }
        self.attributes = {}
        self.abilities = {}
        self.disciplines = {}
        self.backgrounds = {}
        self.virtues = {}
        self.humanity = {"base": 0, "new": 0}
        self.willpower = {"base": 0, "new": 0}

        # Calculate progression values/ability
        self.max_trait_rating = GENERATION_DATA.get(generation, {}).get("max_trait", 5)
        self.total_freebies = self._calculate_total_freebies()
        self.spent_freebies = 0

    def _calculate_total_freebies(self):
        for upper_age, points in AGE_FREEBIE_BRACKETS:
            if self.age <= upper_age:
                return points
        return AGE_FREEBIE_BRACKETS[-1][1] # Return max if older than table

    def set_initial_trait(self, category, trait_name, value):
        trait_dict = getattr(self, category)
        trait_dict[trait_name] = {"base": value, "new": value}

    def set_initial_value(self, category, value):
        stat = getattr(self, category)
        stat["base"] = value
        stat["new"] = value

    def get_trait_data(self, category_name, trait_name):
        if category_name in ["Attribute", "Ability", "Discipline", "Background", "Virtue"]:
            attr_name = "abilities" if category_name == "Ability" else f"{category_name.lower()}s"
            trait_pool = getattr(self, attr_name)
            # If the trait doesn't exist (e.g., a new Discipline), return a default 0-dot dict
            return trait_pool.get(trait_name, {"base": 0, "new": 0})
        else: # For Humanity and Willpower
            return getattr(self, category_name.lower())

    def improve_trait(self, category_name, trait_name, target_value):
        cost_per_dot = FREEBIE_COSTS[category_name]
        remaining_points = self.total_freebies - self.spent_freebies

        # Identify which dictionary to work with
        if category_name in ["Attribute", "Ability", "Discipline", "Background", "Virtue"]:
            trait_pool = getattr(self, "abilities" if category_name == "Ability" else f"{category_name.lower()}s")
            if trait_name not in trait_pool:
                trait_pool[trait_name] = {"base": 0, "new": 0}
            trait_data = trait_pool[trait_name]
        else:
            trait_data = getattr(self, category_name.lower())

        current_rating = trait_data["new"]

        # Safeguard check
        if target_value <= current_rating:
            return False, f"New value must be higher than current ({current_rating})"

        dots_to_add = target_value - current_rating
        total_cost = dots_to_add * cost_per_dot

        if remaining_points < total_cost:
            return False, f"Not enough points! Cost: {total_cost}, Available: {remaining_points}"

        # Apply improvement
        trait_data["new"] = target_value
        self.spent_freebies += total_cost
        return True, f"'{trait_name}' raised to {target_value}. Cost: {total_cost} points"

# --- TUI ---
class TUIApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.character: Optional[VtMCharacter] = None
        self.message = ""
        self.message_color = 1
        
        # Initialize colors
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        
        curses.curs_set(0)  # Hide cursor
        self.stdscr.keypad(True)

    def show_message(self, msg: str, color: int = 1):
        """Store a message to display at the bottom of the screen."""
        self.message = msg
        self.message_color = color

    def draw_box(self, y, x, height, width, title=""):
        """Draw a box with optional title."""
        self.stdscr.attron(curses.color_pair(4))
        for i in range(height):
            if i == 0:
                self.stdscr.addstr(y + i, x, "┌" + "─" * (width - 2) + "┐")
            elif i == height - 1:
                self.stdscr.addstr(y + i, x, "└" + "─" * (width - 2) + "┘")
            else:
                self.stdscr.addstr(y + i, x, "│" + " " * (width - 2) + "│")
        
        if title:
            title_str = f" {title} "
            self.stdscr.addstr(y, x + 2, title_str, curses.color_pair(3) | curses.A_BOLD)
        self.stdscr.attroff(curses.color_pair(4))

    def get_string_input(self, prompt: str, y: int, x: int) -> str:
        """Get string input from user."""
        curses.echo()
        curses.curs_set(1)
        self.stdscr.addstr(y, x, prompt, curses.color_pair(3))
        self.stdscr.refresh()
        result = self.stdscr.getstr(y, x + len(prompt), 30).decode('utf-8').strip()
        curses.noecho()
        curses.curs_set(0)
        return result

    def get_number_input(self, prompt: str, y: int, x: int, min_val: int, max_val: int) -> Optional[int]:
        """Get validated number input from user."""
        while True:
            try:
                val_str = self.get_string_input(prompt, y, x)
                if not val_str:
                    return None
                val = int(val_str)
                if min_val <= val <= max_val:
                    return val
                self.show_message(f"Please enter a number between {min_val} and {max_val}", 2)
                self.stdscr.refresh()
                curses.napms(1500)
            except ValueError:
                self.show_message("Invalid input. Please enter a number.", 2)
                self.stdscr.refresh()
                curses.napms(1500)

    def setup_character(self) -> bool:
        """Initial character setup screen."""
        while True:
            self.stdscr.clear()
            h, w = self.stdscr.getmaxyx()
            
            # Title
            title = "VAMPIRE: THE MASQUERADE - ELDER CHARACTER CREATOR"
            self.stdscr.addstr(1, (w - len(title)) // 2, title, curses.color_pair(5) | curses.A_BOLD)
            
            self.draw_box(3, 2, 15, w - 4, "Character Setup")
            
            # Get character info
            name = self.get_string_input("Character Name: ", 5, 5)
            if not name:
                return False
            
            clan = self.get_string_input("Clan: ", 7, 5)
            if not clan:
                return False
            
            age = self.get_number_input("Age (0-5600+): ", 9, 5, 0, 10000)
            if age is None:
                return False
            
            generation = self.get_number_input("Generation (2-16): ", 11, 5, 2, 16)
            if generation is None:
                return False
            
            self.character = VtMCharacter(name, clan, age, generation)
            
            self.stdscr.clear()
            self.stdscr.addstr(5, 5, f"Character created with {self.character.total_freebies} Freebie Points!", 
                             curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(7, 5, "Press any key to set initial traits...")
            self.stdscr.refresh()
            self.stdscr.getch()
            
            # Set initial traits
            if not self.setup_initial_traits():
                return False
            
            return True

    def setup_initial_traits(self) -> bool:
        """Setup initial trait values."""
        # Attributes
        for attr in ATTRIBUTES_LIST:
            self.stdscr.clear()
            self.draw_box(2, 2, 8, 60, "Initial Attributes")
            self.stdscr.addstr(4, 5, "Set initial attribute values (1-10)", curses.color_pair(3))
            val = self.get_number_input(f"{attr}: ", 6, 5, 1, 10)
            if val is None:
                return False
            self.character.set_initial_trait("attributes", attr, val)
        
        # Abilities
        for abil in ABILITIES_LIST:
            self.stdscr.clear()
            self.draw_box(2, 2, 8, 60, "Initial Abilities")
            self.stdscr.addstr(4, 5, "Set initial ability values (0-10)", curses.color_pair(3))
            val = self.get_number_input(f"{abil}: ", 6, 5, 0, 10)
            if val is None:
                return False
            self.character.set_initial_trait("abilities", abil, val)
        
        # Disciplines
        self.stdscr.clear()
        self.draw_box(2, 2, 10, 60, "Initial Disciplines")
        self.stdscr.addstr(4, 5, "Enter disciplines (press Enter with empty name when done)", curses.color_pair(3))
        y = 6
        while True:
            disc_name = self.get_string_input("Discipline Name: ", y, 5)
            if not disc_name:
                break
            val = self.get_number_input(f"  Value for {disc_name}: ", y + 1, 5, 1, 10)
            if val is None:
                continue
            self.character.set_initial_trait("disciplines", disc_name, val)
            y += 2
        
        # Backgrounds
        self.stdscr.clear()
        self.draw_box(2, 2, 10, 60, "Initial Backgrounds")
        self.stdscr.addstr(4, 5, "Enter backgrounds (press Enter with empty name when done)", curses.color_pair(3))
        y = 6
        while True:
            bg_name = self.get_string_input("Background Name: ", y, 5)
            if not bg_name:
                break
            val = self.get_number_input(f"  Value for {bg_name}: ", y + 1, 5, 1, 10)
            if val is None:
                continue
            self.character.set_initial_trait("backgrounds", bg_name, val)
            y += 2
        
        # Virtues
        for virtue in VIRTUES_LIST:
            self.stdscr.clear()
            self.draw_box(2, 2, 8, 60, "Virtues & Path")
            val = self.get_number_input(f"{virtue}: ", 4, 5, 1, 10)
            if val is None:
                return False
            self.character.set_initial_trait("virtues", virtue, val)
        
        humanity = self.get_number_input("Humanity/Path: ", 6, 5, 1, 10)
        if humanity is None:
            return False
        self.character.set_initial_value("humanity", humanity)
        
        willpower = self.get_number_input("Willpower: ", 7, 5, 1, 10)
        if willpower is None:
            return False
        self.character.set_initial_value("willpower", willpower)
        
        return True

    def display_character_sheet(self, y: int, x: int, width: int):
        """Display the character sheet in a container."""
        start_y = y
        
        # Header
        header = f"{self.character.name} ({self.character.clan})"
        self.stdscr.addstr(y, x, header[:width], curses.color_pair(5) | curses.A_BOLD)
        y += 1
        
        info = f"Age: {self.character.age} | Gen: {self.character.generation}th | Max: {self.character.max_trait_rating}"
        self.stdscr.addstr(y, x, info[:width], curses.color_pair(3))
        y += 1
        
        remaining = self.character.total_freebies - self.character.spent_freebies
        freebie_str = f"Freebie: {remaining}/{self.character.total_freebies}"
        color = curses.color_pair(1) if remaining > 0 else curses.color_pair(2)
        self.stdscr.addstr(y, x, freebie_str, color | curses.A_BOLD)
        y += 2
        
        # Attributes
        self.stdscr.addstr(y, x, "═══ ATTRIBUTES ═══", curses.color_pair(4) | curses.A_BOLD)
        y += 1
        for name, data in self.character.attributes.items():
            if y >= start_y + 40:  # Don't overflow
                break
            self.display_trait(y, x, name, data, width)
            y += 1
        y += 1
        
        # Abilities (show only non-zero)
        self.stdscr.addstr(y, x, "═══ ABILITIES ═══", curses.color_pair(4) | curses.A_BOLD)
        y += 1
        abilities_shown = [(name, data) for name, data in self.character.abilities.items() if data['new'] > 0]
        for name, data in abilities_shown[:8]:  # Limit display
            if y >= start_y + 40:
                break
            self.display_trait(y, x, name, data, width)
            y += 1
        y += 1
        
        # Disciplines
        if self.character.disciplines:
            self.stdscr.addstr(y, x, "═══ DISCIPLINES ═══", curses.color_pair(4) | curses.A_BOLD)
            y += 1
            for name, data in self.character.disciplines.items():
                if y >= start_y + 40:
                    break
                self.display_trait(y, x, name, data, width)
                y += 1
            y += 1
        
        # Backgrounds
        if self.character.backgrounds:
            self.stdscr.addstr(y, x, "═══ BACKGROUNDS ═══", curses.color_pair(4) | curses.A_BOLD)
            y += 1
            for name, data in self.character.backgrounds.items():
                if y >= start_y + 40:
                    break
                self.display_trait(y, x, name, data, width)
                y += 1
            y += 1
        
        # Virtues
        self.stdscr.addstr(y, x, "═══ VIRTUES & PATH ═══", curses.color_pair(4) | curses.A_BOLD)
        y += 1
        for name, data in self.character.virtues.items():
            self.display_trait(y, x, name, data, width)
            y += 1
        self.display_trait(y, x, "Humanity", self.character.humanity, width)
        y += 1
        self.display_trait(y, x, "Willpower", self.character.willpower, width)
        
        return y

    def display_trait(self, y: int, x: int, name: str, data: Dict):
        """Display a single trait with progression."""
        if data['base'] == data['new']:
            trait_str = f"{name[:12]:<12} [{data['new']}]"
            self.stdscr.addstr(y, x, trait_str)
        else:
            trait_str = f"{name[:12]:<12} [{data['base']}]→{{{data['new']}}}"
            self.stdscr.addstr(y, x, trait_str, curses.color_pair(1))

    def main_menu(self):
        """Main menu for spending freebie points."""
        selected = 0
        menu_items = [
            ("Attributes", "Attribute", 5),
            ("Abilities", "Ability", 2),
            ("Disciplines", "Discipline", 7),
            ("Backgrounds", "Background", 1),
            ("Virtues", "Virtue", 2),
            ("Humanity/Path", "Humanity", 1),
            ("Willpower", "Willpower", 1),
            ("Exit", None, 0)
        ]
        
        while True:
            self.stdscr.clear()
            h, w = self.stdscr.getmaxyx()
            
            # Display character sheet
            bottom_y = self.display_character_sheet()
            
            # Menu
            menu_y = min(bottom_y + 1, h - 12)
            self.stdscr.addstr(menu_y, 2, "═══ SPEND FREEBIE POINTS ═══", curses.color_pair(3) | curses.A_BOLD)
            menu_y += 1
            
            for i, (label, _, cost) in enumerate(menu_items):
                prefix = "► " if i == selected else "  "
                if cost > 0:
                    menu_str = f"{prefix}{label} (Cost: {cost} per dot)"
                else:
                    menu_str = f"{prefix}{label}"
                
                attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
                self.stdscr.addstr(menu_y + i, 4, menu_str, attr)
            
            # Display message
            if self.message:
                msg_y = h - 2
                self.stdscr.addstr(msg_y, 2, self.message[:w-4], curses.color_pair(self.message_color))
            
            # Controls
            controls = "↑/↓: Navigate | Enter: Select | Q: Quit"
            self.stdscr.addstr(h - 1, 2, controls, curses.color_pair(3))
            
            self.stdscr.refresh()
            
            # Handle input
            key = self.stdscr.getch()
            
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(menu_items)
                self.message = ""
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(menu_items)
                self.message = ""
            elif key == ord('\n'):
                if selected == len(menu_items) - 1:  # Exit
                    return
                else:
                    self.handle_improvement_menu(menu_items[selected][0], menu_items[selected][1])
            elif key == ord('q') or key == ord('Q'):
                return

    def handle_improvement_menu(self, label: str, category: str):
        """Handle improvement of a specific category."""
        # Determine trait list
        if category == "Attribute":
            trait_list = ATTRIBUTES_LIST
            trait_dict = self.character.attributes
        elif category == "Ability":
            trait_list = ABILITIES_LIST
            trait_dict = self.character.abilities
        elif category == "Discipline":
            trait_list = list(self.character.disciplines.keys())
            trait_dict = self.character.disciplines
        elif category == "Background":
            trait_list = list(self.character.backgrounds.keys())
            trait_dict = self.character.backgrounds
        elif category == "Virtue":
            trait_list = VIRTUES_LIST
            trait_dict = self.character.virtues
        elif category == "Humanity":
            self.improve_single_trait(category, "Humanity/Path")
            return
        elif category == "Willpower":
            self.improve_single_trait(category, "Willpower")
            return
        else:
            return
        
        selected = 0
        can_add = category in ["Discipline", "Background"]
        
        while True:
            self.stdscr.clear()
            h, w = self.stdscr.getmaxyx()
            
            title = f"Improve {label}"
            self.stdscr.addstr(1, 2, title, curses.color_pair(5) | curses.A_BOLD)
            
            # Show remaining points
            remaining = self.character.total_freebies - self.character.spent_freebies
            self.stdscr.addstr(2, 2, f"Available Points: {remaining}", curses.color_pair(1))
            
            y = 4
            display_list = trait_list if category != "Ability" else ABILITIES_LIST
            
            for i, trait in enumerate(display_list):
                if i >= h - 8:  # Don't overflow screen
                    break
                
                current = self.character.get_trait_data(category, trait)['new']
                prefix = "► " if i == selected else "  "
                trait_str = f"{prefix}{trait:<20} [{current}]"
                
                attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
                self.stdscr.addstr(y + i, 4, trait_str, attr)
            
            if can_add:
                add_idx = len(display_list)
                prefix = "► " if selected == add_idx else "  "
                attr = curses.A_REVERSE if selected == add_idx else curses.A_NORMAL
                self.stdscr.addstr(y + add_idx, 4, f"{prefix}** Add New **", attr)
            
            # Controls
            controls = "↑/↓: Navigate | Enter: Improve | Esc: Back"
            self.stdscr.addstr(h - 1, 2, controls, curses.color_pair(3))
            
            if self.message:
                self.stdscr.addstr(h - 2, 2, self.message[:w-4], curses.color_pair(self.message_color))
            
            self.stdscr.refresh()
            
            # Handle input
            key = self.stdscr.getch()
            
            if key == curses.KEY_UP:
                max_idx = len(display_list) + (1 if can_add else 0) - 1
                selected = (selected - 1) % (max_idx + 1)
                self.message = ""
            elif key == curses.KEY_DOWN:
                max_idx = len(display_list) + (1 if can_add else 0) - 1
                selected = (selected + 1) % (max_idx + 1)
                self.message = ""
            elif key == ord('\n'):
                if can_add and selected == len(display_list):
                    # Add new
                    new_name = self.get_string_input("New name: ", h - 3, 2)
                    if new_name:
                        self.improve_single_trait(category, new_name)
                elif selected < len(display_list):
                    self.improve_single_trait(category, display_list[selected])
            elif key == 27:  # Escape
                self.message = ""
                return

    def improve_single_trait(self, category: str, trait_name: str):
        """Improve a single trait."""
        trait_data = self.character.get_trait_data(category, trait_name)
        current = trait_data['new']
        max_val = self.character.max_trait_rating
        
        if current >= max_val:
            self.show_message(f"{trait_name} is already at maximum ({max_val})", 2)
            return
        
        h, w = self.stdscr.getmaxyx()
        prompt = f"New value for {trait_name} ({current+1}-{max_val}): "
        target = self.get_number_input(prompt, h - 3, 2, current + 1, max_val)
        
        if target is not None:
            success, msg = self.character.improve_trait(category, trait_name, target)
            self.show_message(msg, 1 if success else 2)

    def run(self):
        """Main application loop."""
        if not self.setup_character():
            return
        
        self.main_menu()
        
        # Final display
        self.stdscr.clear()
        self.display_character_sheet()
        self.stdscr.addstr(self.stdscr.getmaxyx()[0] - 2, 2, "Character creation complete! Press any key to exit...", 
                          curses.color_pair(1) | curses.A_BOLD)
        self.stdscr.refresh()
        self.stdscr.getch()
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.character: Optional[VtMCharacter] = None
        self.message = ""
        self.message_color = 1
        
        # Initialize colors
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        
        curses.curs_set(0)  # Hide cursor
        self.stdscr.keypad(True)

    def show_message(self, msg: str, color: int = 1):
        """Store a message to display at the bottom of the screen."""
        self.message = msg
        self.message_color = color

    def draw_box(self, y, x, height, width, title=""):
        """Draw a box with optional title."""
        self.stdscr.attron(curses.color_pair(4))
        for i in range(height):
            if i == 0:
                self.stdscr.addstr(y + i, x, "┌" + "─" * (width - 2) + "┐")
            elif i == height - 1:
                self.stdscr.addstr(y + i, x, "└" + "─" * (width - 2) + "┘")
            else:
                self.stdscr.addstr(y + i, x, "│" + " " * (width - 2) + "│")
        
        if title:
            title_str = f" {title} "
            self.stdscr.addstr(y, x + 2, title_str, curses.color_pair(3) | curses.A_BOLD)
        self.stdscr.attroff(curses.color_pair(4))

    def get_string_input(self, prompt: str, y: int, x: int) -> str:
        """Get string input from user."""
        curses.echo()
        curses.curs_set(1)
        self.stdscr.addstr(y, x, prompt, curses.color_pair(3))
        self.stdscr.refresh()
        result = self.stdscr.getstr(y, x + len(prompt), 30).decode('utf-8').strip()
        curses.noecho()
        curses.curs_set(0)
        return result

    def get_number_input(self, prompt: str, y: int, x: int, min_val: int, max_val: int) -> Optional[int]:
        """Get validated number input from user."""
        while True:
            try:
                val_str = self.get_string_input(prompt, y, x)
                if not val_str:
                    return None
                val = int(val_str)
                if min_val <= val <= max_val:
                    return val
                self.show_message(f"Please enter a number between {min_val} and {max_val}", 2)
                self.stdscr.refresh()
                curses.napms(1500)
            except ValueError:
                self.show_message("Invalid input. Please enter a number.", 2)
                self.stdscr.refresh()
                curses.napms(1500)

    def setup_character(self) -> bool:
        """Initial character setup screen."""
        while True:
            self.stdscr.clear()
            h, w = self.stdscr.getmaxyx()
            
            # Title
            title = "VAMPIRE: THE MASQUERADE - ELDER CHARACTER CREATOR"
            self.stdscr.addstr(1, (w - len(title)) // 2, title, curses.color_pair(5) | curses.A_BOLD)
            
            self.draw_box(3, 2, 15, w - 4, "Character Setup")
            
            # Get character info
            name = self.get_string_input("Character Name: ", 5, 5)
            if not name:
                return False
            
            clan = self.get_string_input("Clan: ", 7, 5)
            if not clan:
                return False
            
            age = self.get_number_input("Age (0-5600+): ", 9, 5, 0, 10000)
            if age is None:
                return False
            
            generation = self.get_number_input("Generation (2-16): ", 11, 5, 2, 16)
            if generation is None:
                return False
            
            self.character = VtMCharacter(name, clan, age, generation)
            
            self.stdscr.clear()
            self.stdscr.addstr(5, 5, f"Character created with {self.character.total_freebies} Freebie Points!", 
                             curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(7, 5, "Press any key to set initial traits...")
            self.stdscr.refresh()
            self.stdscr.getch()
            
            # Set initial traits
            if not self.setup_initial_traits():
                return False
            
            return True

    def setup_initial_traits(self) -> bool:
        """Setup initial trait values."""
        # Attributes
        for attr in ATTRIBUTES_LIST:
            self.stdscr.clear()
            self.draw_box(2, 2, 8, 60, "Initial Attributes")
            self.stdscr.addstr(4, 5, "Set initial attribute values (1-10)", curses.color_pair(3))
            val = self.get_number_input(f"{attr}: ", 6, 5, 1, 10)
            if val is None:
                return False
            self.character.set_initial_trait("attributes", attr, val)
        
        # Abilities
        for abil in ABILITIES_LIST:
            self.stdscr.clear()
            self.draw_box(2, 2, 8, 60, "Initial Abilities")
            self.stdscr.addstr(4, 5, "Set initial ability values (0-10)", curses.color_pair(3))
            val = self.get_number_input(f"{abil}: ", 6, 5, 0, 10)
            if val is None:
                return False
            self.character.set_initial_trait("abilities", abil, val)
        
        # Disciplines
        self.stdscr.clear()
        self.draw_box(2, 2, 10, 60, "Initial Disciplines")
        self.stdscr.addstr(4, 5, "Enter disciplines (press Enter with empty name when done)", curses.color_pair(3))
        y = 6
        while True:
            disc_name = self.get_string_input("Discipline Name: ", y, 5)
            if not disc_name:
                break
            val = self.get_number_input(f"  Value for {disc_name}: ", y + 1, 5, 1, 10)
            if val is None:
                continue
            self.character.set_initial_trait("disciplines", disc_name, val)
            y += 2
        
        # Backgrounds
        self.stdscr.clear()
        self.draw_box(2, 2, 10, 60, "Initial Backgrounds")
        self.stdscr.addstr(4, 5, "Enter backgrounds (press Enter with empty name when done)", curses.color_pair(3))
        y = 6
        while True:
            bg_name = self.get_string_input("Background Name: ", y, 5)
            if not bg_name:
                break
            val = self.get_number_input(f"  Value for {bg_name}: ", y + 1, 5, 1, 10)
            if val is None:
                continue
            self.character.set_initial_trait("backgrounds", bg_name, val)
            y += 2
        
        # Virtues
        for virtue in VIRTUES_LIST:
            self.stdscr.clear()
            self.draw_box(2, 2, 8, 60, "Virtues & Path")
            val = self.get_number_input(f"{virtue}: ", 4, 5, 1, 10)
            if val is None:
                return False
            self.character.set_initial_trait("virtues", virtue, val)
        
        humanity = self.get_number_input("Humanity/Path: ", 6, 5, 1, 10)
        if humanity is None:
            return False
        self.character.set_initial_value("humanity", humanity)
        
        willpower = self.get_number_input("Willpower: ", 7, 5, 1, 10)
        if willpower is None:
            return False
        self.character.set_initial_value("willpower", willpower)
        
        return True

    def display_character_sheet(self, start_y: int = 2):
        """Display the character sheet."""
        y = start_y
        x = 2
        
        # Header
        header = f"{self.character.name} ({self.character.clan})"
        self.stdscr.addstr(y, x, header, curses.color_pair(5) | curses.A_BOLD)
        y += 1
        
        info = f"Age: {self.character.age} | Gen: {self.character.generation}th | Max Trait: {self.character.max_trait_rating}"
        self.stdscr.addstr(y, x, info, curses.color_pair(3))
        y += 1
        
        remaining = self.character.total_freebies - self.character.spent_freebies
        freebie_str = f"Freebie Points: {remaining} / {self.character.total_freebies}"
        color = curses.color_pair(1) if remaining > 0 else curses.color_pair(2)
        self.stdscr.addstr(y, x, freebie_str, color | curses.A_BOLD)
        y += 2
        
        # Attributes (in columns)
        self.stdscr.addstr(y, x, "═══ ATTRIBUTES ═══", curses.color_pair(4) | curses.A_BOLD)
        y += 1
        for i, (name, data) in enumerate(self.character.attributes.items()):
            col = (i // 3) * 25
            row = y + (i % 3)
            self.display_trait(row, x + col, name, data)
        y += 4
        
        # Abilities (show only non-zero)
        self.stdscr.addstr(y, x, "═══ ABILITIES ═══", curses.color_pair(4) | curses.A_BOLD)
        y += 1
        abilities_shown = [(name, data) for name, data in self.character.abilities.items() if data['new'] > 0]
        for i, (name, data) in enumerate(abilities_shown[:12]):  # Show first 12
            col = (i // 6) * 25
            row = y + (i % 6)
            self.display_trait(row, x + col, name, data)
        y += 7
        
        return y

    def display_trait(self, y: int, x: int, name: str, data: Dict):
        """Display a single trait with progression."""
        if data['base'] == data['new']:
            trait_str = f"{name[:12]:<12} [{data['new']}]"
            self.stdscr.addstr(y, x, trait_str)
        else:
            trait_str = f"{name[:12]:<12} [{data['base']}]→{{{data['new']}}}"
            self.stdscr.addstr(y, x, trait_str, curses.color_pair(1))

    # Main menu
    def main_menu(self):
        """Main menu for spending freebie points."""
        selected = 0
        menu_items = [
            ("Attributes", "Attribute", 5),
            ("Abilities", "Ability", 2),
            ("Disciplines", "Discipline", 7),
            ("Backgrounds", "Background", 1),
            ("Virtues", "Virtue", 2),
            ("Humanity/Path", "Humanity", 1),
            ("Willpower", "Willpower", 1),
            ("Exit", None, 0)
        ]
        
        while True:
            self.stdscr.clear()
            h, w = self.stdscr.getmaxyx()
            
            # Display character sheet
            bottom_y = self.display_character_sheet()
            
            # Menu
            menu_y = min(bottom_y + 1, h - 12)
            self.stdscr.addstr(menu_y, 2, "═══ SPEND FREEBIE POINTS ═══", curses.color_pair(3) | curses.A_BOLD)
            menu_y += 1
            
            for i, (label, _, cost) in enumerate(menu_items):
                prefix = "► " if i == selected else "  "
                if cost > 0:
                    menu_str = f"{prefix}{label} (Cost: {cost} per dot)"
                else:
                    menu_str = f"{prefix}{label}"
                
                attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
                self.stdscr.addstr(menu_y + i, 4, menu_str, attr)
            
            # Display message
            if self.message:
                msg_y = h - 2
                self.stdscr.addstr(msg_y, 2, self.message[:w-4], curses.color_pair(self.message_color))
            
            # Controls
            controls = "↑/↓: Navigate | Enter: Select | Q: Quit"
            self.stdscr.addstr(h - 1, 2, controls, curses.color_pair(3))
            
            self.stdscr.refresh()
            
            # Handle input
            key = self.stdscr.getch()
            
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(menu_items)
                self.message = ""
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(menu_items)
                self.message = ""
            elif key == ord('\n'):
                if selected == len(menu_items) - 1:  # Exit
                    return
                else:
                    self.handle_improvement_menu(menu_items[selected][0], menu_items[selected][1])
            elif key == ord('q') or key == ord('Q'):
                return

    def handle_improvement_menu(self, label: str, category: str):
        """Handle improvement of a specific category."""
        # Determine trait list
        if category == "Attribute":
            trait_list = ATTRIBUTES_LIST
            trait_dict = self.character.attributes
        elif category == "Ability":
            trait_list = ABILITIES_LIST
            trait_dict = self.character.abilities
        elif category == "Discipline":
            trait_list = list(self.character.disciplines.keys())
            trait_dict = self.character.disciplines
        elif category == "Background":
            trait_list = list(self.character.backgrounds.keys())
            trait_dict = self.character.backgrounds
        elif category == "Virtue":
            trait_list = VIRTUES_LIST
            trait_dict = self.character.virtues
        elif category == "Humanity":
            self.improve_single_trait(category, "Humanity/Path")
            return
        elif category == "Willpower":
            self.improve_single_trait(category, "Willpower")
            return
        else:
            return
        
        selected = 0
        can_add = category in ["Discipline", "Background"]
        
        while True:
            self.stdscr.clear()
            h, w = self.stdscr.getmaxyx()
            
            title = f"Improve {label}"
            self.stdscr.addstr(1, 2, title, curses.color_pair(5) | curses.A_BOLD)
            
            # Show remaining points
            remaining = self.character.total_freebies - self.character.spent_freebies
            self.stdscr.addstr(2, 2, f"Available Points: {remaining}", curses.color_pair(1))
            
            y = 4
            display_list = trait_list if category != "Ability" else ABILITIES_LIST
            
            for i, trait in enumerate(display_list):
                if i >= h - 8:  # Don't overflow screen
                    break
                
                current = self.character.get_trait_data(category, trait)['new']
                prefix = "► " if i == selected else "  "
                trait_str = f"{prefix}{trait:<20} [{current}]"
                
                attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
                self.stdscr.addstr(y + i, 4, trait_str, attr)
            
            if can_add:
                add_idx = len(display_list)
                prefix = "► " if selected == add_idx else "  "
                attr = curses.A_REVERSE if selected == add_idx else curses.A_NORMAL
                self.stdscr.addstr(y + add_idx, 4, f"{prefix}** Add New **", attr)
            
            # Controls
            controls = "↑/↓: Navigate | Enter: Improve | Esc: Back"
            self.stdscr.addstr(h - 1, 2, controls, curses.color_pair(3))
            
            if self.message:
                self.stdscr.addstr(h - 2, 2, self.message[:w-4], curses.color_pair(self.message_color))
            
            self.stdscr.refresh()
            
            # Handle input
            key = self.stdscr.getch()
            
            if key == curses.KEY_UP:
                max_idx = len(display_list) + (1 if can_add else 0) - 1
                selected = (selected - 1) % (max_idx + 1)
                self.message = ""
            elif key == curses.KEY_DOWN:
                max_idx = len(display_list) + (1 if can_add else 0) - 1
                selected = (selected + 1) % (max_idx + 1)
                self.message = ""
            elif key == ord('\n'):
                if can_add and selected == len(display_list):
                    # Add new
                    new_name = self.get_string_input("New name: ", h - 3, 2)
                    if new_name:
                        self.improve_single_trait(category, new_name)
                elif selected < len(display_list):
                    self.improve_single_trait(category, display_list[selected])
            elif key == 27:  # Escape
                self.message = ""
                return

    def improve_single_trait(self, category: str, trait_name: str):
        """Improve a single trait."""
        trait_data = self.character.get_trait_data(category, trait_name)
        current = trait_data['new']
        max_val = self.character.max_trait_rating
        
        if current >= max_val:
            self.show_message(f"{trait_name} is already at maximum ({max_val})", 2)
            return
        
        h, w = self.stdscr.getmaxyx()
        prompt = f"New value for {trait_name} ({current+1}-{max_val}): "
        target = self.get_number_input(prompt, h - 3, 2, current + 1, max_val)
        
        if target is not None:
            success, msg = self.character.improve_trait(category, trait_name, target)
            self.show_message(msg, 1 if success else 2)

    def run(self):
        """Main application loop."""
        if not self.setup_character():
            return
        
        self.main_menu()
        
        # Final display
        self.stdscr.clear()
        self.display_character_sheet()
        self.stdscr.addstr(self.stdscr.getmaxyx()[0] - 2, 2, "Character creation complete! Press any key to exit...", 
                          curses.color_pair(1) | curses.A_BOLD)
        self.stdscr.refresh()
        self.stdscr.getch()

# --- APP ---
def main(stdscr):
    app = TUIApp(stdscr)
    app.run()

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nExiting program. Goodbye!")
        sys.exit(0)