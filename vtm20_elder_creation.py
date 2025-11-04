#!/user/bin/env python3

# --- IMPORTS ---
import sys
import math

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
    "Strength", "Dexterity", "Stamina",  # Physical
    "Charisma", "Manipulation", "Appearance",  # Social
    "Perception", "Intelligence", "Wits"  # Mental
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

# --- USER INPUT FUNCTIONS ---
def get_int_input(prompt, min_val=0, max_val=10):
    """Gets a validated integer input from the user."""
    while True:
        try:
            value = int(input(prompt))
            if min_val <= value <= max_val:
                return value
            else:
                print(f"  Please enter a number between {min_val} and {max_val}.")
        except ValueError:
            print("  Invalid input. Please enter a number.")

def get_str_input(prompt):
    """Gets a non-empty string input from the user."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        else:
            print("  This field cannot be empty.")

# --- CHARACTER CLASS ---
class VtMCharacter:
    """Stores and manages a VtM character's progression."""

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

        # Calculate progression values
        self.max_trait_rating = GENERATION_DATA.get(generation, {}).get("max_trait", 5)
        self.total_freebies = self._calculate_total_freebies()
        self.spent_freebies = 0

    def _calculate_total_freebies(self):
        """Calculates freebie points based on character age."""
        for upper_age, points in AGE_FREEBIE_BRACKETS:
            if self.age <= upper_age:
                return points
        return AGE_FREEBIE_BRACKETS[-1][1] # Return max if older than table

    def set_initial_trait(self, category, trait_name, value):
        """Sets the initial value for a trait."""
        trait_dict = getattr(self, category)
        trait_dict[trait_name] = {"base": value, "new": value}

    def set_initial_value(self, category, value):
        """Sets the initial value for a single-value stat like Humanity."""
        stat = getattr(self, category)
        stat["base"] = value
        stat["new"] = value

    def get_trait_data(self, category_name, trait_name):
        """A helper to retrieve the data dictionary for any given trait."""
        if category_name in ["Attribute", "Ability", "Discipline", "Background", "Virtue"]:
            attr_name = "abilities" if category_name == "Ability" else f"{category_name.lower()}s"
            trait_pool = getattr(self, attr_name)
            # If the trait doesn't exist (e.g., a new Discipline), return a default 0-dot dict
            return trait_pool.get(trait_name, {"base": 0, "new": 0})
        else: # For Humanity and Willpower
            return getattr(self, category_name.lower())

    def display_sheet(self):
        """Prints the character sheet with current progression."""
        print("\n" + "="*40)
        print(f" CHARACTER: {self.name} ({self.clan})")
        print(f" AGE: {self.age} | GENERATION: {self.generation}th | MAX TRAIT RATING: {self.max_trait_rating}")
        print("-"*40)
        print(f" FREEBIE POINTS: {self.total_freebies - self.spent_freebies} / {self.total_freebies}")
        print("="*40 + "\n")

        # format and print each trait
        def print_trait(name, data):
            if data['base'] == data['new']:
                print(f"  {name:<15} = [{data['new']}]")
            else:
                print(f"  {name:<15} = [{data['base']}] -> {{{data['new']}}}")

        print("--- Attributes ---")
        for name, data in self.attributes.items():
            print_trait(name, data)

        print("\n--- Abilities ---")
        for name, data in self.abilities.items():
            if data['new'] > 0:
                print_trait(name, data)

        print("\n--- Disciplines ---")
        for name, data in self.disciplines.items():
            print_trait(name, data)

        print("\n--- Backgrounds ---")
        for name, data in self.backgrounds.items():
            print_trait(name, data)

        print("\n--- Virtues & Path ---")
        for name, data in self.virtues.items():
            print_trait(name, data)
        print_trait("Humanity/Path", self.humanity)

        print("\n--- Willpower ---")
        print_trait("Willpower", self.willpower)
        print("\n" + "="*40)

    def improve_trait(self, category_name, trait_name, target_value):
        """Logic to improve a trait to a new target value by spending freebie points."""
        cost_per_dot = FREEBIE_COSTS[category_name]
        remaining_points = self.total_freebies - self.spent_freebies

        # Identify which dictionary to work with
        if category_name in ["Attribute", "Ability", "Discipline", "Background", "Virtue"]:
            trait_pool = getattr(self, "abilities" if category_name == "Ability" else f"{category_name.lower()}s")
            if trait_name not in trait_pool:
                # Add the new trait if it doesn't exist
                trait_pool[trait_name] = {"base": 0, "new": 0}
            trait_data = trait_pool[trait_name]
        else:
            trait_data = getattr(self, category_name.lower())

        current_rating = trait_data["new"]

        # Safeguard check
        if target_value <= current_rating:
            print(f"\n>> Error: New value ({target_value}) must be higher than current value ({current_rating}).")
            return

        dots_to_add = target_value - current_rating
        total_cost = dots_to_add * cost_per_dot

        if remaining_points < total_cost:
            print(f"\n>> Not enough Freebie Points! This upgrade costs {total_cost}, but you only have {remaining_points}.")
            return

        # --- Apply Improvement ---
        trait_data["new"] = target_value
        self.spent_freebies += total_cost
        print(f"\n>> Success! '{trait_name}' raised to {target_value}. You spent {total_cost} freebie points.")

# --- INITIAL CHARACTER SETUP ---
def setup_character():
    """Guides the user through the initial character setup."""
    print("--- Vampire Character Progression Helper ---")
    print("Let's set up your character sheet based on Belladonna's Elder System.")

    name = get_str_input("Enter character name: ")
    clan = get_str_input("Enter character clan: ")
    age = get_int_input("Enter character age (0-5600+): ", min_val=0, max_val=10000)
    generation = get_int_input("Enter character generation (e.g., 8 for 8th): ", min_val=2, max_val=16)
    player_char = VtMCharacter(name, clan, age, generation)

    print(f"\nYour character has {player_char.total_freebies} Freebie Points to spend.")
    print("-" * 20)

    print("\n--- Enter Initial Attributes (1-10) ---")
    for attr in ATTRIBUTES_LIST:
        val = get_int_input(f"  {attr}: ", min_val=1, max_val=10)
        player_char.set_initial_trait("attributes", attr, val)

    print("\n--- Enter Initial Abilities (0-10) ---")
    for abil in ABILITIES_LIST:
        val = get_int_input(f"  {abil}: ", min_val=0, max_val=10)
        player_char.set_initial_trait("abilities", abil, val)

    for category in ["Disciplines", "Backgrounds"]:
        print(f"\n--- Enter Initial {category} (1-10) ---")
        print("(Type 'done' when you have finished entering all of them)")
        while True:
            trait_name = get_str_input(f"  {category[:-1]} Name (or 'done'): ")
            if trait_name.lower() == 'done':
                break
            val = get_int_input(f"    Value for {trait_name}: ", min_val=1, max_val=10)
            player_char.set_initial_trait(f"{category.lower()}", trait_name, val)

    print("\n--- Enter Virtues, Humanity/Path, and Willpower (1-10) ---")
    for virtue in VIRTUES_LIST:
        val = get_int_input(f"  {virtue}: ", min_val=1, max_val=10)
        player_char.set_initial_trait("virtues", virtue, val)

    humanity_val = get_int_input("  Humanity/Path of Enlightenment: ", min_val=1, max_val=10)
    player_char.set_initial_value("humanity", humanity_val)

    willpower_val = get_int_input("  Willpower: ", min_val=1, max_val=10)
    player_char.set_initial_value("willpower", willpower_val)

    return player_char

# --- MAIN LOOP ---
def main_loop(character):
    """The main interactive loop for spending points."""
    while True:
        character.display_sheet()
        print("\n--- Spend Freebie Points ---")
        print("1. Improve Attribute    (Cost: 5 per dot)")
        print("2. Improve Ability      (Cost: 2 per dot)")
        print("3. Improve Discipline   (Cost: 7 per dot)")
        print("4. Improve Background   (Cost: 1 per dot)")
        print("5. Improve Virtue       (Cost: 2 per dot)")
        print("6. Improve Humanity     (Cost: 1 per dot)")
        print("7. Improve Willpower    (Cost: 1 per dot)")
        print("0. Exit")

        choice = get_int_input("Choose a category to improve: ", min_val=0, max_val=7)

        if choice == 0:
            print("\nExiting the character helper. Final sheet:")
            character.display_sheet()
            sys.exit()
        elif choice == 1:
            handle_improvement(character, "Attribute", ATTRIBUTES_LIST)
        elif choice == 2:
            handle_improvement(character, "Ability", ABILITIES_LIST)
        elif choice == 3:
            handle_improvement(character, "Discipline", list(character.disciplines.keys()), can_add_new=True)
        elif choice == 4:
            handle_improvement(character, "Background", list(character.backgrounds.keys()), can_add_new=True)
        elif choice == 5:
            handle_improvement(character, "Virtue", VIRTUES_LIST)
        elif choice == 6:
            handle_improvement(character, "Humanity", ["Humanity/Path"])
        elif choice == 7:
            handle_improvement(character, "Willpower", ["Willpower"])


def handle_improvement(character, category_name, trait_list, can_add_new=False):
    """Generic handler for selecting a trait from a list and improving it to a target value."""
    print(f"\n--- Select {category_name} to Improve ---")

    # Create a dynamic list of traits to show, including ones with 0 dots for abilities
    display_list = []
    if category_name == "Ability":
         display_list = ABILITIES_LIST
    else:
         display_list = trait_list

    for i, trait in enumerate(display_list, 1):
        current_val = character.get_trait_data(category_name, trait)['new']
        print(f"{i}. {trait:<15} [{current_val}]")

    if can_add_new:
        print("0. ** Add a new one **")

    min_choice = 0 if can_add_new else 1
    prompt = f"Enter number (or any other key to go back): " if not can_add_new else f"Enter number to improve or add (or any other key to go back): "

    try:
        choice_str = input(prompt)
        choice = int(choice_str)
        if not (min_choice <= choice <= len(display_list)):
            return # Invalid number, go back
    except ValueError:
        return # Not a number, go back

    trait_to_improve = ""
    if can_add_new and choice == 0:
        trait_to_improve = get_str_input(f"Enter the name of the new {category_name}: ")
    elif choice > 0:
        trait_to_improve = display_list[choice - 1]
    else:
        return # Go back

    # --- Get target value ---
    trait_data = character.get_trait_data(category_name, trait_to_improve)
    current_rating = trait_data["new"]
    max_rating = character.max_trait_rating

    if current_rating >= max_rating:
        print(f"\n>> Cannot improve '{trait_to_improve}'. It's already at the maximum rating ({max_rating}).")
        return

    # For new traits, the prompt starts from 1
    prompt_min_val = current_rating + 1 if current_rating > 0 else 1

    prompt = f"  {trait_to_improve} [{current_rating}] -> Enter a new rating ({prompt_min_val} to {max_rating}): "
    target_value = get_int_input(prompt, min_val=prompt_min_val, max_val=max_rating)

    character.improve_trait(category_name, trait_to_improve, target_value)


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    try:
        my_character = setup_character()
        main_loop(my_character)
    except KeyboardInterrupt:
        print("\n\nExiting program. Goodbye!")
        sys.exit()