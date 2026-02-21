#!/usr/bin/env python3

""" This module contains the character data and business logic for the tool. It is independent of the user interface. """

# --- [IMPORTS] ---
import sys
from typing import Dict, List, Tuple

# Import all data from the new 'vtm_data.py'
from vtm_data import (
    GENERATION_DATA, AGE_FREEBIE_BRACKETS, FREEBIE_COSTS,
    ATTRIBUTES_LIST, ABILITIES_LIST, VIRTUES_LIST,
    CLAN_DATA, BACKGROUNDS_LIST, DISCIPLINES_LIST
)

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

        # Automatically populate disciplines based on Clan (Case insensitive check)
        self._apply_clan_disciplines()

    def _apply_clan_disciplines(self):

        """Checks if the chosen clan exists in data and adds its disciplines."""

        # Normalize input to Title Case for lookup (e.g. "brujah" -> "Brujah")
        formatted_clan = self.clan.title()
        
        if formatted_clan in CLAN_DATA:
            for disc in CLAN_DATA[formatted_clan]:
                # Initialize with 0 dots
                self.disciplines[disc] = {"base": 0, "new": 0}

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

    # Trait modification
    def improve_trait(self, category_name: str, trait_name: str, target_value: int) -> Tuple[bool, str]:

        """ Attempts to modify a trait by spending or refunding freebie points. Returns (Success, Message). """
        
        cost_per_dot = FREEBIE_COSTS[category_name]
        remaining_points = self.total_freebies - self.spent_freebies

        # Fetch trait data
        if category_name in ["Attribute", "Ability", "Discipline", "Background", "Virtue"]:
            trait_pool = getattr(self, "abilities" if category_name == "Ability" else f"{category_name.lower()}s")
            if trait_name not in trait_pool:
                trait_pool[trait_name] = {"base": 0, "new": 0}
            trait_data = trait_pool[trait_name]
        else:
            trait_data = getattr(self, category_name.lower())

        current_rating = trait_data["new"]
        base_rating = trait_data["base"]

        # Basic Validation
        if target_value == current_rating:
            return False, f"Value unchanged."
        
        if target_value < base_rating:
            return False, f"Cannot lower below initial base value ({base_rating})."

        # --- Generation Limit Check  ---
        # Do not increase stats above gen cap
        limit = 10 if category_name in ["Humanity", "Willpower"] else self.max_trait_rating        
        if target_value > limit:
            return False, f"Cannot raise above generation limit ({limit})."

        # Calculate cost (positive) or refund (negative)
        dots_diff = target_value - current_rating
        total_cost = dots_diff * cost_per_dot

        # If increasing, check affordability
        if total_cost > 0 and not self.is_free_mode and remaining_points < total_cost:
            return False, f"Not enough points! Cost: {total_cost}, Available: {remaining_points}"

        # Apply changes
        trait_data["new"] = target_value
        
        # Update spent pool (refunds automatically subtract because total_cost is negative)
        if not self.is_free_mode:
            self.spent_freebies += total_cost
        elif total_cost > 0: 
            # In free mode, spent freebie points, but refunds just lower the counter
            self.spent_freebies += total_cost
        else:
            # Free mode refund logic
            # Also keeps coutner accurate
            self.spent_freebies += total_cost

        action = "raised" if dots_diff > 0 else "lowered"
        points_label = "Cost" if dots_diff > 0 else "Refund"
        
        return True, f"'{trait_name}' {action} to {target_value}. {points_label}: {abs(total_cost)} points"

    def remove_trait(self, category_name: str, trait_name: str) -> Tuple[bool, str]:

        """Removes a trait and refunds the points spent on it."""
        
        # Only allow removing Disciplines and Backgrounds for now
        if category_name == "Discipline":
            target_dict = self.disciplines
        elif category_name == "Background":
            target_dict = self.backgrounds
        else:
            return False, f"Cannot delete {category_name}s."

        if trait_name not in target_dict:
            return False, "Trait not found."

        # Calculate refund (Base + Dots)
        data = target_dict[trait_name]
        # Calculate how many dots were purchased (New - Base). 
        # For added traits, Base is usually 0, so it refunds everything.
        dots_purchased = data['new'] - data['base']
        cost_per_dot = FREEBIE_COSTS.get(category_name, 0)
        refund = dots_purchased * cost_per_dot

        self.spent_freebies -= refund
        del target_dict[trait_name]
        return True, f"Removed {trait_name}. Refunded {refund} points."

    def get_text_sheet(self) -> str:

        """Generates a plain text representation of the character sheet."""
        
        lines = []
        lines.append("="*40)
        lines.append(f"NAME: {self.name} ({self.clan})")
        lines.append(f"Age: {self.age} | Generation: {self.generation}th")
        lines.append(f"Freebie Points Spent: {self.spent_freebies}")
        lines.append("="*40 + "\n")

        def format_section(title, data_dict):
            if not data_dict: return
            lines.append(f"--- {title} ---")
            for name, val in data_dict.items():
                val_str = f"[{val['new']}]" if val['base'] == val['new'] else f"[{val['base']}->{val['new']}]"
                lines.append(f"{name:<20} {val_str}")
            lines.append("")

        format_section("ATTRIBUTES", self.attributes)
        active_abilities = {k: v for k, v in self.abilities.items() if v['new'] > 0}
        format_section("ABILITIES", active_abilities)
        format_section("DISCIPLINES", self.disciplines)
        format_section("BACKGROUNDS", self.backgrounds)
        format_section("VIRTUES", self.virtues)

        lines.append("--- OTHER ---")
        lines.append(f"{'Humanity/Path':<20} [{self.humanity['new']}]")
        lines.append(f"{'Willpower':<20} [{self.willpower['new']}]")
        
        return "\n".join(lines)