"""
tui/save_manager.py

Handles all save/load file I/O for VtMCharacter objects.
Views call these functions directly — no JSON logic leaks into the UI layer.
"""

import json
import os
from vtm_npc_logic import VtMCharacter

# --- [CONSTANTS] ---
SAVES_DIR = "saves"

# --- [HELPERS] ---
def _ensure_saves_dir():
    """Creates the saves/ directory if it doesn't exist."""
    os.makedirs(SAVES_DIR, exist_ok=True)

def _build_path(filename: str) -> str:
    """Returns a full path inside saves/ for a given filename."""
    if not filename.endswith(".json"):
        filename += ".json"
    return os.path.join(SAVES_DIR, filename)

# --- [PUBLIC API] ---
def save_character(character: VtMCharacter, filename: str) -> tuple[bool, str]:
    """
    Saves a character to saves/{filename}.json.
    Returns (success, message).
    """
    try:
        _ensure_saves_dir()
        path = _build_path(filename)
        with open(path, 'w') as f:
            json.dump(character.to_dict(), f, indent=2)
        return True, f"Character saved to {path}"
    except Exception as e:
        return False, f"Failed to save: {str(e)}"

def load_character(filename: str) -> tuple[bool, str | VtMCharacter]:
    """
    Loads a character from saves/{filename}.json.
    Returns (success, VtMCharacter) on success.
    Returns (False, error_message) on failure.
    """
    try:
        path = _build_path(filename)
        with open(path, 'r') as f:
            data = json.load(f)
        character = VtMCharacter.from_dict(data)
        return True, character
    except FileNotFoundError:
        return False, f"Save file '{filename}' not found."
    except (json.JSONDecodeError, KeyError) as e:
        return False, f"Save file is corrupted or invalid: {str(e)}"
    except Exception as e:
        return False, f"Failed to load: {str(e)}"

def list_saves() -> list[str]:
    """
    Returns a list of save filenames (without extension) found in saves/.
    Returns an empty list if the directory doesn't exist or is empty.
    """
    if not os.path.exists(SAVES_DIR):
        return []
    return [
        f[:-5] for f in os.listdir(SAVES_DIR)
        if f.endswith(".json")
    ]

def default_save_name(character: VtMCharacter) -> str:
    """Returns a sanitized default filename for a character."""
    return character.name.replace(" ", "_").lower()