#!/usr/bin/env python3

# --- IMPORTS ---
import curses
import sys
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
        """Setup initial trait values with list display."""
        h, w = self.stdscr.getmaxyx()
        
        # Attributes
        entered_attrs = {}
        for i, attr in enumerate(ATTRIBUTES_LIST):
            self.stdscr.clear()
            
            # Calculate centered container
            container_width = 60
            container_height = 20
            start_x = (w - container_width) // 2
            start_y = (h - container_height) // 2
            
            self.draw_box(start_y, start_x, container_height, container_width, "Initial Attributes")
            self.stdscr.addstr(start_y + 2, start_x + 2, "Set initial attribute values (1-10)", curses.color_pair(3))
            
            # Display already entered attributes
            list_y = start_y + 4
            for name, value in entered_attrs.items():
                self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(1))
                list_y += 1
            
            # Prompt for current attribute
            val = self.get_number_input(f"{attr}: ", list_y, start_x + 2, 1, 10)
            if val is None:
                return False
            entered_attrs[attr] = val
            self.character.set_initial_trait("attributes", attr, val)
        
        # Abilities
        entered_abils = {}
        for i, abil in enumerate(ABILITIES_LIST):
            self.stdscr.clear()
            
            container_width = 60
            container_height = min(40, h - 4)
            start_x = (w - container_width) // 2
            start_y = (h - container_height) // 2
            
            self.draw_box(start_y, start_x, container_height, container_width, "Initial Abilities")
            self.stdscr.addstr(start_y + 2, start_x + 2, "Set initial ability values (0-10)", curses.color_pair(3))
            
            # Display already entered abilities (scrollable)
            list_y = start_y + 4
            max_display = container_height - 8
            start_idx = max(0, len(entered_abils) - max_display + 1)
            
            for name, value in list(entered_abils.items())[start_idx:]:
                if list_y >= start_y + container_height - 4:
                    break
                self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(1))
                list_y += 1
            
            val = self.get_number_input(f"{abil}: ", list_y, start_x + 2, 0, 10)
            if val is None:
                return False
            entered_abils[abil] = val
            self.character.set_initial_trait("abilities", abil, val)
        
        # Disciplines
        entered_discs = {}
        while True:
            self.stdscr.clear()
            
            container_width = 60
            container_height = 25
            start_x = (w - container_width) // 2
            start_y = (h - container_height) // 2
            
            self.draw_box(start_y, start_x, container_height, container_width, "Initial Disciplines")
            self.stdscr.addstr(start_y + 2, start_x + 2, 
                             "Enter disciplines (empty name when done)", curses.color_pair(3))
            
            list_y = start_y + 4
            for name, value in entered_discs.items():
                self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(1))
                list_y += 1
            
            disc_name = self.get_string_input("Discipline Name: ", list_y, start_x + 2)
            if not disc_name:
                break
            
            val = self.get_number_input(f"  Value: ", list_y + 1, start_x + 2, 1, 10)
            if val is None:
                continue
            entered_discs[disc_name] = val
            self.character.set_initial_trait("disciplines", disc_name, val)
        
        # Backgrounds
        entered_bgs = {}
        while True:
            self.stdscr.clear()
            
            container_width = 60
            container_height = 25
            start_x = (w - container_width) // 2
            start_y = (h - container_height) // 2
            
            self.draw_box(start_y, start_x, container_height, container_width, "Initial Backgrounds")
            self.stdscr.addstr(start_y + 2, start_x + 2, 
                             "Enter backgrounds (empty name when done)", curses.color_pair(3))
            
            list_y = start_y + 4
            for name, value in entered_bgs.items():
                self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(1))
                list_y += 1
            
            bg_name = self.get_string_input("Background Name: ", list_y, start_x + 2)
            if not bg_name:
                break
            
            val = self.get_number_input(f"  Value: ", list_y + 1, start_x + 2, 1, 10)
            if val is None:
                continue
            entered_bgs[bg_name] = val
            self.character.set_initial_trait("backgrounds", bg_name, val)
        
        # Virtues
        entered_virtues = {}
        for virtue in VIRTUES_LIST:
            self.stdscr.clear()
            
            container_width = 60
            container_height = 15
            start_x = (w - container_width) // 2
            start_y = (h - container_height) // 2
            
            self.draw_box(start_y, start_x, container_height, container_width, "Virtues & Path")
            self.stdscr.addstr(start_y + 2, start_x + 2, "Set virtue values (1-10)", curses.color_pair(3))
            
            list_y = start_y + 4
            for name, value in entered_virtues.items():
                self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(1))
                list_y += 1
            
            val = self.get_number_input(f"{virtue}: ", list_y, start_x + 2, 1, 10)
            if val is None:
                return False
            entered_virtues[virtue] = val
            self.character.set_initial_trait("virtues", virtue, val)
        
        # Humanity and Willpower
        self.stdscr.clear()
        
        container_width = 60
        container_height = 15
        start_x = (w - container_width) // 2
        start_y = (h - container_height) // 2
        
        self.draw_box(start_y, start_x, container_height, container_width, "Final Values")
        
        list_y = start_y + 2
        for name, value in entered_virtues.items():
            self.stdscr.addstr(list_y, start_x + 2, f"{name}: {value}", curses.color_pair(1))
            list_y += 1
        
        list_y += 1
        humanity = self.get_number_input("Humanity/Path: ", list_y, start_x + 2, 1, 10)
        if humanity is None:
            return False
        self.character.set_initial_value("humanity", humanity)
        
        willpower = self.get_number_input("Willpower: ", list_y + 1, start_x + 2, 1, 10)
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

    def display_trait(self, y: int, x: int, name: str, data: Dict, width: int = 30):
        """Display a single trait with progression."""
        if data['base'] == data['new']:
            trait_str = f"{name[:15]:<15} [{data['new']}]"
            self.stdscr.addstr(y, x, trait_str[:width])
        else:
            trait_str = f"{name[:15]:<15} [{data['base']}] -> {{{data['new']}}}"
            self.stdscr.addstr(y, x, trait_str[:width], curses.color_pair(1))

    def main_menu(self):
        """Main menu for spending freebie points with split view."""
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
            
            # Calculate centered container dimensions
            container_width = min(100, w - 10)
            container_height = min(50, h - 6)
            start_x = (w - container_width) // 2
            start_y = (h - container_height) // 2
            
            # Split container into left (character sheet) and right (menu)
            left_width = 35
            right_width = container_width - left_width - 3
            
            # Draw main container
            self.draw_box(start_y, start_x, container_height, container_width, "VTM Elder Creator")
            
            # Draw left panel (character sheet)
            left_x = start_x + 2
            self.display_character_sheet(start_y + 2, left_x, left_width)
            
            # Draw vertical separator
            for i in range(1, container_height - 1):
                self.stdscr.addstr(start_y + i, start_x + left_width + 2, "│", curses.color_pair(4))
            
            # Draw right panel (menu)
            right_x = start_x + left_width + 4
            menu_y = start_y + 2
            
            self.stdscr.addstr(menu_y, right_x, "SPEND FREEBIE POINTS", curses.color_pair(3) | curses.A_BOLD)
            menu_y += 2
            
            for i, (label, _, cost) in enumerate(menu_items):
                if menu_y >= start_y + container_height - 2:
                    break
                    
                prefix = "► " if i == selected else "  "
                if cost > 0:
                    menu_str = f"{prefix}{label} (Cost: {cost}/dot)"
                else:
                    menu_str = f"{prefix}{label}"
                
                attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
                self.stdscr.addstr(menu_y + i, right_x, menu_str[:right_width], attr)
            
            # Display message at bottom of container
            if self.message:
                msg_y = start_y + container_height - 2
                self.stdscr.addstr(msg_y, start_x + 2, self.message[:container_width-4], 
                                 curses.color_pair(self.message_color))
            
            # Controls outside container
            controls = "↑/↓: Navigate | Enter: Select | Q: Quit"
            self.stdscr.addstr(h - 1, (w - len(controls)) // 2, controls, curses.color_pair(3))
            
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
        """Handle improvement of a specific category with split view."""
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
            
            # Calculate centered container dimensions
            container_width = min(100, w - 10)
            container_height = min(50, h - 6)
            start_x = (w - container_width) // 2
            start_y = (h - container_height) // 2
            
            # Split container
            left_width = 35
            right_width = container_width - left_width - 3
            
            # Draw main container
            title = f"Improve {label}"
            self.draw_box(start_y, start_x, container_height, container_width, title)
            
            # Draw left panel (character sheet)
            left_x = start_x + 2
            self.display_character_sheet(start_y + 2, left_x, left_width)
            
            # Draw vertical separator
            for i in range(1, container_height - 1):
                self.stdscr.addstr(start_y + i, start_x + left_width + 2, "│", curses.color_pair(4))
            
            # Draw right panel (trait selection)
            right_x = start_x + left_width + 4
            menu_y = start_y + 2
            
            # Show available points
            remaining = self.character.total_freebies - self.character.spent_freebies
            points_str = f"Available: {remaining} points"
            self.stdscr.addstr(menu_y, right_x, points_str, curses.color_pair(1) | curses.A_BOLD)
            menu_y += 2
            
            # Show traits
            display_list = trait_list if category != "Ability" else ABILITIES_LIST
            max_display = min(len(display_list), container_height - 10)
            
            for i in range(max_display):
                trait = display_list[i]
                current = self.character.get_trait_data(category, trait)['new']
                prefix = "► " if i == selected else "  "
                trait_str = f"{prefix}{trait[:18]:<18} [{current}]"
                
                attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
                self.stdscr.addstr(menu_y + i, right_x, trait_str[:right_width], attr)
            
            if can_add:
                add_idx = len(display_list)
                if add_idx < container_height - 10:
                    prefix = "► " if selected == add_idx else "  "
                    attr = curses.A_REVERSE if selected == add_idx else curses.A_NORMAL
                    self.stdscr.addstr(menu_y + add_idx, right_x, f"{prefix}** Add New **"[:right_width], attr)
            
            # Display message
            if self.message:
                msg_y = start_y + container_height - 2
                self.stdscr.addstr(msg_y, start_x + 2, self.message[:container_width-4], 
                                 curses.color_pair(self.message_color))
            
            # Controls
            controls = "↑/↓: Navigate | Enter: Improve | Esc: Back"
            self.stdscr.addstr(h - 1, (w - len(controls)) // 2, controls, curses.color_pair(3))
            
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
                    new_name = self.get_string_input("New name: ", start_y + container_height - 3, start_x + 2)
                    if new_name:
                        self.improve_single_trait(category, new_name)
                elif selected < len(display_list):
                    self.improve_single_trait(category, display_list[selected])
            elif key == 27:  # Escape
                self.message = ""
                return

    def improve_single_trait(self, category: str, trait_name: str):
        """Improve a single trait with centered input dialog."""
        trait_data = self.character.get_trait_data(category, trait_name)
        current = trait_data['new']
        max_val = self.character.max_trait_rating
        
        if current >= max_val:
            self.show_message(f"{trait_name} is already at maximum ({max_val})", 2)
            return
        
        h, w = self.stdscr.getmaxyx()
        
        # Create a centered input dialog
        dialog_width = 50
        dialog_height = 8
        dialog_x = (w - dialog_width) // 2
        dialog_y = (h - dialog_height) // 2
        
        # Draw dialog box
        self.draw_box(dialog_y, dialog_x, dialog_height, dialog_width, "Improve Trait")
        
        # Show current value and prompt
        self.stdscr.addstr(dialog_y + 2, dialog_x + 2, f"Trait: {trait_name}", curses.color_pair(3))
        self.stdscr.addstr(dialog_y + 3, dialog_x + 2, f"Current: [{current}]", curses.color_pair(1))
        self.stdscr.addstr(dialog_y + 4, dialog_x + 2, f"Max: {max_val}", curses.color_pair(3))
        
        prompt = f"New value ({current+1}-{max_val}): "
        target = self.get_number_input(prompt, dialog_y + 5, dialog_x + 2, current + 1, max_val)
        
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

# --- MAIN APP ---
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