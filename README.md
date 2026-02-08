A CLI and TUI tool for creating and progressing Vampire: The Masquerade (V20) characters, specifically for creating NPCs.

This is a personal project for me to happily make characters to use as a foundation or baseline for NPC characters.

<img align="center" alt="image" src="https://github.com/user-attachments/assets/e325c139-2bf4-4bfd-bf03-71cdde6dcf83" />

## Why?
How do I stat out a 500 year old Ministry character who just woke up? Standard character creation is designed for fledglings/neonates, not older and more experienced Kindred.

So this tool solves my problem by using age-based progression systems to generate a pool of freebie points that can be used to progress an existing starting character sheet to reflect the character's age, experience, and power. For me, I use it as a guide that gives me a mechanical basis for what an NPC can do. (You can break it if you want. You're the Storyteller)

> [!NOTE]
> This is specifically built for V20 because I make more V20 characters than V5. 😅

## Features
- **Character Setup:** Creation based on Name, Clan, Age, and Generation.
- **Progression Logic:** Calculates freebie points based on age brackets.
- **Generation Limits:** Enforces max trait ratings (e.g., Gen 8 can have traits up to 5, Gen 7 up to 6, and so on).
- **Interactive TUI:** A fully interactive terminal interface using `curses`.
- **Free Mode:** An optional mode for unlimited building without point restrictions.

## Getting Started

For **Windows**, you might need to install the curses library: `pip install windows-curses`

```bash
# Clone this repository
git clone https://github.com/frantaing/vtm-npc-progression.git
cd vtm-npc-progression

# And just run this script for your terminal!
# Or use python3
python vtm_npc_tui.py
```

## 📝 Disclaimer & Credits

### Acknowledgements and System Credits

The core progression logic in this tool isn't mine! It's a direct implementation of the systems described in this great article: [Elder Creation System by Belladona on KismetRose.com](https://www.kismetrose.com/vtm/sc/character/Character03.html).

This tool is just a way to automate the math described in that article. Full credit for the design of the progression systems goes to the article's original author.

### Disclaimer

This is a fan-made, non-commercial project created for educational and recreational purposes only. All game mechanics, setting terms, and thematic elements from Vampire: The Masquerade belong to their respective copyright holders.

This project is not affiliated with, endorsed, sponsored, or specifically approved by White Wolf Publishing, Paradox Interactive, or any related entity.
