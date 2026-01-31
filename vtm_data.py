""" This is the centralized repository for all static VtM:V20 data. """

# --- [GAME RULES & COSTS] ---
# Generation
GENERATION_DATA = {
    2: {"max_trait": 10}, 3: {"max_trait": 10}, 4: {"max_trait": 9},
    5: {"max_trait": 8}, 6: {"max_trait": 7}, 7: {"max_trait": 6},
    8: {"max_trait": 5}, 9: {"max_trait": 5}, 10: {"max_trait": 5},
    11: {"max_trait": 5}, 12: {"max_trait": 5}, 13: {"max_trait": 5},
    14: {"max_trait": 5}, 15: {"max_trait": 5}, 16: {"max_trait": 5}
}
# Age to Freebie ratio
AGE_FREEBIE_BRACKETS = [
    (50, 45), (100, 90), (200, 150), (350, 225), (550, 315),
    (800, 390), (1100, 465), (1450, 525), (1850, 585), (2300, 630),
    (2800, 675), (3350, 705), (3950, 735), (5600, 750)
]
# Freebie costs
FREEBIE_COSTS = {
    "Attribute": 5, "Ability": 2, "Discipline": 7,
    "Background": 1, "Virtue": 2, "Humanity": 1, "Willpower": 1
}

# --- [CHARACTER SHEETS LISTS] ---
# Attributes
ATTRIBUTES_LIST = [
    "Strength", "Dexterity", "Stamina",
    "Charisma", "Manipulation", "Appearance",
    "Perception", "Intelligence", "Wits"
]
# Abilities
ABILITIES_LIST = [
    "Alertness", "Athletics", "Awareness", "Brawl", "Empathy",
    "Expression", "Intimidation", "Leadership", "Streetwise", "Subterfuge",
    "Animal Ken", "Crafts", "Drive", "Etiquette", "Firearms",
    "Larceny", "Melee", "Performance", "Stealth", "Survival",
    "Academics", "Computer", "Finance", "Investigation", "Law",
    "Medicine", "Occult", "Politics", "Science", "Technology"
]
# Virtues
VIRTUES_LIST = ["Conscience", "Self-Control", "Courage"]

# --- [SELECTION MENUS DATA] ---
# Standard V20 Backgrounds
BACKGROUNDS_LIST = [
    "Allies", "Arsenal", "Contacts", "Fame", "Generation", "Herd",
    "Influence", "Mentor", "Resources", "Retainers", "Status"
]
# V20 Disciplines (Common + Clan Specifics + Bloodline)
DISCIPLINES_LIST = [
    "Abombwe", "Animalism", "Auspex", "Bardo", "Celerity", "Chimerstry",
    "Daimonion", "Deimos", "Dementation", "Dominate", "Fortitude", "Koldunic Sorcery", 
    "Melpominee", "Mortis", "Mytherceria", "Necromancy", "Obeah", "Obfuscate",
    "Obtenebration", "Ogham", "Potence", "Presence", "Protean", "Quietus",
    "Sanguinus", "Serpentis", "Spiritus", "Temporis", "Thaumaturgy", "Thanatosis",
    "Valeren", "Vicissitude", "Visceratika"
]
# Clan Definitions (Name -> In-Clan Disciplines)
CLAN_DATA = {
    "Assamite": ["Celerity", "Obfuscate", "Quietus"],
    "Brujah": ["Celerity", "Potence", "Presence"],
    "Followers Of Set": ["Obfuscate", "Presence", "Serpentis"],
    "Gangrel": ["Animalism", "Fortitude", "Protean"],
    "Giovanni": ["Dominate", "Necromancy", "Potence"],
    "Lasombra": ["Dominate", "Obtenebration", "Potence"],
    "Malkavian": ["Auspex", "Dementation", "Obfuscate"],
    "Nosferatu": ["Animalism", "Obfuscate", "Potence"],
    "Ravnos": ["Animalism", "Chimerstry", "Fortitude"],
    "Toreador": ["Auspex", "Celerity", "Presence"],
    "Tremere": ["Auspex", "Dominate", "Thaumaturgy"],
    "Tzimisce": ["Animalism", "Auspex", "Vicissitude"],
    "Ventrue": ["Dominate", "Fortitude", "Presence"],
    "Cappadocian": ["Auspex", "Fortitude", "Mortis"],
    "Ahrimanes": ["Animalism", "Protean", "Spiritus"],
    "Akunanse": ["Abombwe", "Animalism", "Fortitude"],
    "Baali": ["Daimonion", "Obfuscate", "Presence"],
    "Blood Brothers": ["Fortitude", "Potence", "Sanguinus"],
    "Children Of Osiris": ["Bardo", "Dominate", "Potence"],
    "City Gangrel": ["Celerity", "Obfuscate", "Protean"],
    "Daughters Of Cacophony": ["Fortitude", "Melpominee", "Presence"],
    "Gargoyles": ["Fortitude", "Potence", "Visceratika"],
    "Harbingers Of Skulls": ["Auspex", "Fortitude", "Necromancy"],
    "Kiasyd": ["Dominate", "Mytherceria", "Obtenebration"],
    "Lamia": ["Fortitude", "Mortis", "Potence"],
    "Lhiannan": ["Animalism", "Ogham", "Presence"],
    "Maeghar": ["Mytherceria", "Necromancy"],
    "Nagaraja": ["Auspex", "Dominate", "Necromancy"],
    "Salubri": ["Auspex", "Fortitude", "Valeren"],
    "Samedi": ["Fortitude", "Obfuscate", "Thanatosis"],
    "True Brujah": ["Fortitude", "Potence", "Temporis"],
    "Caitiff": [], # No In-Clan Disciplines
    "Pander": [], # No In-Clan Disciplines
    "Thin Blood": [] # No In-Clan Disciplines
}