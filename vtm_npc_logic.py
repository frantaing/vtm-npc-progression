#!/usr/bin/env python3

"""
vtm_logic.py

This module contains the character data and business logic for the tool. It is independent of the
user interface.
"""

# --- [IMPORTS] ---
import sys
from typing import Dict, List, Tuple

# --- [DATA] ---
GENERATION_DATA: Dict[int, Dict[str, int]] = {
    2: {"max_trait": 10}, 3: {"max_trait": 10}, 4: {"max_trait": 9},
    5: {"max_trait": 8}, 6: {"max_trait": 7}, 7: {"max_trait": 6},
    8: {"max_trait": 5}, 9: {"max_trait": 5}, 10: {"max_trait": 5},
    11: {"max_trait": 5}, 12: {"max_trait": 5}, 13: {"max_trait": 5},
    14: {"max_trait": 5}, 15: {"max_trait": 5}, 16: {"max_trait": 5}
}

AGE_FREEBIE_BRACKETS: List[Tuple[int, int]] = [
    (50, 45), (100, 90), (200, 150), (350, 225), (550, 315),
    (800, 390), (1100, 465), (1450, 525), (1850, 585), (2300, 630),
    (2800, 675), (3350, 705), (3950, 735), (5600, 750)
]

FREEBIE_COSTS: Dict[str, int] = {
    "Attribute": 5, "Ability": 2, "Discipline": 7,
    "Background": 1, "Virtue": 2, "Humanity": 1, "Willpower": 1
}

ATTRIBUTES_LIST: List[str] = [
    "Strength", "Dexterity", "Stamina",
    "Charisma", "Manipulation", "Appearance",
    "Perception", "Intelligence", "Wits"
]

ABILITIES_LIST: List[str] = [
    "Alertness", "Athletics", "Awareness", "Brawl", "Empathy",
    "Expression", "Intimidation", "Leadership", "Streetwise", "Subterfuge",
    "Animal Ken", "Crafts", "Drive", "Etiquette", "Firearms",
    "Larceny", "Melee", "Performance", "Stealth", "Survival",
    "Academics", "Computer", "Finance", "Investigation", "Law",
    "Medicine", "Occult", "Politics", "Science", "Technology"
]

VIRTUES_LIST: List[str] = ["Conscience", "Self-Control", "Courage"]

# --- [CHARACTER CLASS] ---
class VtMCharacter:
    """Stores and manages a VtM character's progression."""

    def __init__(self, name: str, clan: str, age: int, generation: int, is_free_mode: bool = False):
        self.name = name
        self.clan = clan
        self.age = age
        self.generation = generation
        self.is_free_mode = is_free_mode

        self.attributes: Dict[str, Dict[str, int]] = {}
        self.abilities: Dict[str, Dict[str, int]] = {}
        self.disciplines: Dict[str, Dict[str, int]] = {}
        self.backgrounds: Dict[str, Dict[str, int]] = {}
        self.virtues: Dict[str, Dict[str, int]] = {}
        self.humanity: Dict[str, int] = {"base": 0, "new": 0}
        self.willpower: Dict[str, int] = {"base": 0, "new": 0}

        self.max_trait_rating = GENERATION_DATA.get(generation, {}).get("max_trait", 5)
        
        self.total_freebies = sys.maxsize if self.is_free_mode else self._calculate_total_freebies()
        self.spent_freebies = 0

    def _calculate_total_freebies(self) -> int:
        """Calculates total freebies based on character's age."""
        for upper_age, points in AGE_FREEBIE_BRACKETS:
            if self.age <= upper_age:
                return points
        return AGE_FREEBIE_BRACKETS[-1][1]

    def set_initial_trait(self, category: str, trait_name: str, value: int):
        """Sets the initial base and new value for a named trait."""
        trait_dict = getattr(self, category)
        trait_dict[trait_name] = {"base": value, "new": value}

    def set_initial_value(self, category: str, value: int):
        """Sets the initial base and new value for a single-value stat."""
        stat = getattr(self, category)
        stat["base"] = value
        stat["new"] = value

    def get_trait_data(self, category_name: str, trait_name: str) -> Dict[str, int]:
        """Gets the data dictionary for a specific trait."""
        if category_name in ["Attribute", "Ability", "Discipline", "Background", "Virtue"]:
            attr_name = "abilities" if category_name == "Ability" else f"{category_name.lower()}s"
            trait_pool = getattr(self, attr_name)
            return trait_pool.get(trait_name, {"base": 0, "new": 0})
        else:
            return getattr(self, category_name.lower())

    def improve_trait(self, category_name: str, trait_name: str, target_value: int) -> Tuple[bool, str]:
        """Attempts to improve a trait by spending freebie points."""
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

        if not self.is_free_mode and remaining_points < total_cost:
            return False, f"Not enough points! Cost: {total_cost}, Available: {remaining_points}"

        trait_data["new"] = target_value
        
        # Always track spent points
        self.spent_freebies += total_cost
        
        return True, f"'{trait_name}' raised to {target_value}. Cost: {total_cost} points"