"""
=================================================================
  EPISODE GENERATOR

  Generates a unique story_config.json for each run.
  Every episode has different characters, settings, and storylines
  to comply with YouTube monetization (unique content).

  HOW TO USE:
  1. Run: python generate_episode.py
  2. It creates a fresh story_config.json
  3. Then run: python run_story.py

  OR one command:
     python generate_episode.py --run
     (generates episode AND runs the full pipeline)

  OPTIONS:
     python generate_episode.py --theme ocean
     python generate_episode.py --episode 5
     python generate_episode.py --list-themes
=================================================================
"""

import json
import random
import sys
from pathlib import Path
from datetime import datetime

# =============================================================================
# STORY BUILDING BLOCKS
# =============================================================================

THEMES = {
    "starfall": {
        "setting_name": "Starfall Valley",
        "setting_desc": "magical valley at twilight, crystal trees glowing blue and purple, floating lily pads, stars falling like rain, waterfall of starlight, fireflies, bioluminescent flowers",
        "mood": "mystical twilight",
        "elements": ["crystal trees", "falling stars", "glowing flowers", "starlight streams", "luminous creatures"],
        "conflict": "heart_stone",
        "color_palette": "blue, purple, silver",
    },
    "ocean": {
        "setting_name": "Coral Dream Cove",
        "setting_desc": "underwater cove with bioluminescent coral, gentle currents carrying glowing jellyfish, ancient sea turtle shells forming bridges, pearl gardens, sunlight filtering through crystal-clear water",
        "mood": "deep ocean wonder",
        "elements": ["glowing coral", "sea turtles", "pearl gardens", "jellyfish lanterns", "singing whales"],
        "conflict": "fading_reef",
        "color_palette": "turquoise, coral pink, deep blue",
    },
    "sky_islands": {
        "setting_name": "Cloud Blossom Isles",
        "setting_desc": "floating islands connected by rainbow bridges, clouds shaped like animals, trees growing upside down with roots in the sky, waterfalls falling upward, birds made of paper and light",
        "mood": "airy and weightless",
        "elements": ["floating islands", "rainbow bridges", "cloud animals", "sky waterfalls", "paper birds"],
        "conflict": "broken_bridge",
        "color_palette": "white, gold, soft pink",
    },
    "mushroom": {
        "setting_name": "Spore Hollow",
        "setting_desc": "vast underground cavern filled with giant luminescent mushrooms, mycelium networks pulsing with light, spore clouds creating aurora-like displays, moss-covered stone paths, underground lake reflecting mushroom glow",
        "mood": "warm underground glow",
        "elements": ["giant mushrooms", "glowing mycelium", "spore auroras", "moss paths", "crystal caves"],
        "conflict": "dying_network",
        "color_palette": "warm orange, teal, amber",
    },
    "winter": {
        "setting_name": "Frost Whisper Peaks",
        "setting_desc": "mountain peaks where aurora borealis touches the snow, ice caves with frozen music, snow foxes with glowing fur, hot springs surrounded by crystal ice formations, pine forests dusted with starlight",
        "mood": "cold but cozy",
        "elements": ["aurora borealis", "ice caves", "snow foxes", "hot springs", "frozen waterfalls"],
        "conflict": "eternal_winter",
        "color_palette": "ice blue, aurora green, warm amber",
    },
    "desert": {
        "setting_name": "Sandglass Oasis",
        "setting_desc": "desert oasis where sand flows like water, glass flowers that chime in the wind, ancient stone guardians that move at sunset, mirage pools showing other worlds, dunes that shift colors with the moon",
        "mood": "warm golden mystery",
        "elements": ["glass flowers", "sand rivers", "stone guardians", "mirage pools", "color-shifting dunes"],
        "conflict": "dried_spring",
        "color_palette": "gold, deep red, turquoise",
    },
    "garden": {
        "setting_name": "Everbloom Sanctuary",
        "setting_desc": "enormous walled garden where seasons change in different sections, flowers that sing at dawn, butterflies that carry messages, ancient greenhouse with impossible plants, sundial that controls time",
        "mood": "lush and timeless",
        "elements": ["singing flowers", "message butterflies", "season zones", "ancient greenhouse", "time sundial"],
        "conflict": "stopped_seasons",
        "color_palette": "green, rose, lavender",
    },
    "aurora": {
        "setting_name": "Northern Light Falls",
        "setting_desc": "frozen lake where aurora lights dance on the surface, ice sculptures that come alive at night, snow owls that guide travelers, crystal geysers erupting color, northern lights forming stories in the sky",
        "mood": "magical arctic night",
        "elements": ["aurora dancers", "living ice sculptures", "snow owls", "crystal geysers", "light stories"],
        "conflict": "fading_aurora",
        "color_palette": "aurora green, violet, ice white",
    },
}

CHARACTER_TRAITS = {
    "hair_colors": ["silver", "golden", "dark brown", "copper red", "midnight blue", "soft pink", "white", "chestnut"],
    "hair_styles": ["long flowing", "short messy", "braided", "curly", "tied in a ponytail", "wild and windswept"],
    "eye_colors": ["bright blue", "warm amber", "deep green", "violet", "golden", "dark brown", "silver-grey"],
    "clothing_styles": [
        "a flowing dress with embroidered patterns",
        "a cozy knit sweater over shorts",
        "an adventurer's jacket with many pockets",
        "a hooded cloak with star patterns",
        "overalls over a striped shirt",
        "a tunic with leaf patterns",
    ],
    "accessories": [
        "a small glowing lantern",
        "a worn leather satchel",
        "a flower crown that never wilts",
        "a compass that points to magic",
        "a scarf that changes color with mood",
        "a wooden flute",
    ],
    "companions": [
        "a tiny orange fox",
        "a small blue bird",
        "a floating light orb",
        "a baby cloud that follows them",
        "a friendly firefly swarm",
        "a miniature dragon",
        "a glowing moth",
        "a crystal butterfly",
    ],
    "personalities": ["curious and brave", "gentle and kind", "clever and resourceful", "dreamy and imaginative", "bold and determined"],
}

NAMES_POOL = {
    "female": ["Luna", "Aria", "Ivy", "Mira", "Sage", "Wren", "Fern", "Coral", "Iris", "Dove", "Lyra", "Nova", "Ember", "Willow", "Hazel", "Aurora", "Stella", "Maple"],
    "male": ["Kai", "Finn", "Ash", "Reed", "Sol", "Jasper", "Robin", "Elm", "Fox", "Lark", "Rowan", "Alder", "Cedar", "Flint", "Otto", "Leo", "Hugo", "Miles"],
}

CONFLICT_TEMPLATES = {
    "heart_stone": {
        "problem": "the {setting}'s heart stone is cracked and fading, threatening all magic",
        "solution": "gather {elements} to restore the heart stone's power",
        "climax": "place the final piece and watch magic surge back to life",
    },
    "fading_reef": {
        "problem": "the {setting}'s colors are fading as its life source dims",
        "solution": "find the ancient source and reawaken it with help from local creatures",
        "climax": "the source erupts with renewed energy, color flooding back everywhere",
    },
    "broken_bridge": {
        "problem": "the connections between the {setting}'s parts have broken, isolating everyone",
        "solution": "rebuild the bridges by finding missing pieces scattered throughout",
        "climax": "the final bridge connects and all parts light up in celebration",
    },
    "dying_network": {
        "problem": "the {setting}'s communication network is going dark, silencing all voices",
        "solution": "trace the network to its core and find what's blocking the signal",
        "climax": "clear the blockage and watch as light pulses through every connection",
    },
    "eternal_winter": {
        "problem": "the {setting} is stuck in endless cold, unable to feel warmth",
        "solution": "find the hidden warmth source and carry it back to the frozen heart",
        "climax": "warmth spreads out from the center, ice transforming into spring",
    },
    "dried_spring": {
        "problem": "the {setting}'s water source has mysteriously stopped flowing",
        "solution": "journey upstream to find and remove what's blocking the water",
        "climax": "water rushes back, bringing life and color to everything it touches",
    },
    "stopped_seasons": {
        "problem": "the {setting}'s seasons have frozen in place, nothing grows or changes",
        "solution": "repair the ancient mechanism that keeps the cycle turning",
        "climax": "seasons begin flowing again, each section bursting with its proper beauty",
    },
    "fading_aurora": {
        "problem": "the {setting}'s lights are growing dim, the sky losing its stories",
        "solution": "collect fragments of old stories and return them to the sky",
        "climax": "the aurora blazes back brighter than ever, new stories joining the old",
    },
}


# =============================================================================
# STORY GENERATOR
# =============================================================================

class EpisodeGenerator:
    def __init__(self, theme=None, episode_num=None, seed=None):
        if seed is None:
            seed = int(datetime.now().timestamp() * 1000) % 2**32
        self.rng = random.Random(seed)
        self.seed = seed

        if theme and theme in THEMES:
            self.theme_key = theme
        else:
            self.theme_key = self.rng.choice(list(THEMES.keys()))

        self.theme = THEMES[self.theme_key]
        self.episode_num = episode_num or self.rng.randint(1, 999)

    def generate_character(self, gender="female"):
        name = self.rng.choice(NAMES_POOL[gender])
        hair_color = self.rng.choice(CHARACTER_TRAITS["hair_colors"])
        hair_style = self.rng.choice(CHARACTER_TRAITS["hair_styles"])
        eye_color = self.rng.choice(CHARACTER_TRAITS["eye_colors"])
        clothing = self.rng.choice(CHARACTER_TRAITS["clothing_styles"])
        accessory = self.rng.choice(CHARACTER_TRAITS["accessories"])
        companion = self.rng.choice(CHARACTER_TRAITS["companions"])
        personality = self.rng.choice(CHARACTER_TRAITS["personalities"])

        description = (
            f"Anime character, {hair_style} {hair_color} hair, {eye_color} eyes, "
            f"wearing {clothing}, carrying {accessory}, "
            f"{companion} nearby, {personality} expression, "
            f"Ghibli style, white background"
        )

        return {
            "name": name,
            "description": description,
            "hair": f"{hair_style} {hair_color}",
            "eyes": eye_color,
            "clothing": clothing,
            "accessory": accessory,
            "companion": companion,
            "personality": personality,
        }

    def generate_story_arc(self, char1, char2):
        setting = self.theme["setting_name"]
        elements = self.theme["elements"]
        mood = self.theme["mood"]
        conflict_key = self.theme["conflict"]
        conflict = CONFLICT_TEMPLATES[conflict_key]

        problem = conflict["problem"].format(setting=setting, elements=", ".join(elements[:3]))
        solution = conflict["solution"].format(setting=setting, elements=", ".join(elements[:2]))

        style = "Studio Ghibli anime style"
        c1 = char1["name"]
        c2 = char2["name"]
        c1_desc = f"character with {char1['hair']} hair"
        c2_desc = f"character with {char2['hair']} hair and {char2['companion']}"

        scenes = []

        # ACT 1: Discovery (15 scenes)
        act1 = [
            f"Peaceful evening in a small village, warm lights in windows, {mood} sky above, {style}",
            f"{c1_desc} looking out window at something magical in the distance, wonder in their eyes, {style}",
            f"{c2_desc} running excitedly through the village toward the magical sight, {style}",
            f"Two friends meeting at the village edge at dusk, ready for adventure, {style}",
            f"Two children walking along a winding path at night, one carrying {char1['accessory']}, {style}",
            f"Path opening to reveal {setting} for the first time, {self.theme['setting_desc'][:80]}, children gasping in awe, {style}",
            f"Children carefully entering {setting}, surrounded by {elements[0]}, magical atmosphere, {style}",
            f"Close-up of {elements[0]}, beautiful and ethereal, child reaching out to touch, {style}",
            f"{char2['companion']} playfully exploring {elements[1]}, curious and delighted, {style}",
            f"Children discovering {elements[2]} up close, kneeling in wonder, soft light, {style}",
            f"Child gently interacting with {elements[2]}, it responds with light, magical connection, {style}",
            f"{elements[3]} stretching across the landscape, beautiful and inviting, {style}",
            f"Children following {elements[3]}, adventurous expressions, magical landscape around, {style}",
            f"Both children exploring together, laughing, {elements[4]} around them, {style}",
            f"Arriving at the heart of {setting}, most beautiful spot, ancient and powerful, {style}",
        ]

        # ACT 2: Exploration (15 scenes)
        act2 = [
            f"The heart of {setting} revealed in full glory, breathtaking vista, {style}",
            f"Local magical creatures appearing, curious about the children, friendly and glowing, {style}",
            f"Creatures interacting with {c1_desc}, landing on outstretched hands, trusting, {style}",
            f"{char2['companion']} playing with local creatures, creating light trails together, {style}",
            f"Children discovering a hidden garden of {elements[1]}, each one unique and beautiful, {style}",
            f"Children helping to tend {elements[2]}, gentle and careful, rewarding work, {style}",
            f"New growth appearing where children helped, small miracle of nature, {style}",
            f"Local creatures celebrating the new growth, dancing with joy, festive, {style}",
            f"Child climbing to a high viewpoint, looking out over all of {setting}, panoramic, {style}",
            f"Beautiful panoramic view of {setting} from above, all {elements[0]} visible, breathtaking, {style}",
            f"Children following a hidden path deeper into {setting}, determined expressions, {style}",
            f"Crossing a natural bridge over a gap, brave moment, {elements[4]} below, {style}",
            f"Arriving at the most ancient part of {setting}, powerful and awe-inspiring, {style}",
            f"Children noticing something is wrong, {elements[0]} dimming, worry on faces, {style}",
            f"Hidden entrance to the source of {setting}'s power, ancient symbols glowing faintly, {style}",
        ]

        # ACT 3: Challenge (15 scenes)
        act3 = [
            f"Children entering the ancient chamber at {setting}'s core, walls with glowing symbols, {style}",
            f"Inside a vast space, the source of power visible but clearly damaged, {style}",
            f"The damaged power source shown in detail, cracks and fading light, something is very wrong, {style}",
            f"Children looking worried, creatures gathered around looking sad, the problem is clear, {style}",
            f"Ancient images on walls showing {setting} in its full glory, understanding the history, {style}",
            f"Images showing how the power source connects to everything in {setting}, {style}",
            f"Child placing a found element near the damaged source, first attempt to help, {style}",
            f"Power source responding to the offering, tiny spark of healing light, hope, {style}",
            f"{char2['companion']} rushing out to gather more helpful elements, determined, {style}",
            f"Creatures joining the effort, bringing pieces of {elements[1]} to help, teamwork, {style}",
            f"Power source growing stronger with each offering, healing visible, {style}",
            f"Everyone working together, children and creatures united, beautiful cooperation, {style}",
            f"Final big effort, children lifting something important together, straining but hopeful, {style}",
            f"Placing the final piece, massive surge of brilliant light, everyone shielding eyes, {style}",
            f"Wave of restored magic bursting outward from the source, spreading everywhere, {style}",
        ]

        # ACT 4: Renewal (15 scenes)
        act4 = [
            f"Children emerging to see {setting} transformed, brighter and more magical than ever, {style}",
            f"{elements[0]} growing more vibrant and numerous, spreading across the landscape, {style}",
            f"{elements[4]} more beautiful now, moving in graceful patterns, renewed energy, {style}",
            f"New growth everywhere, {elements[2]} blooming in every color, carpet of beauty, {style}",
            f"The centerpiece of {setting} now twice as magnificent, restored to full power, {style}",
            f"Hundreds of creatures filling the air in celebration, creating patterns of light, {style}",
            f"{char2['companion']} dancing joyfully among the renewed {elements[1]}, pure happiness, {style}",
            f"Children sitting together peacefully, watching the celebration, content smiles, {style}",
            f"Creatures showing gratitude to the children, gentle gifts of light, {style}",
            f"Child receiving a small keepsake from {setting}, a crystal seed or glowing token, {style}",
            f"Grand celebration, all creatures dancing in synchronized beauty, spectacular, {style}",
            f"Children joining the celebration, carried by magic, floating slightly, pure joy, {style}",
            f"The ancient center at its brightest, sending light into the sky, connecting everything, {style}",
            f"New elements being born from the renewed power, floating upward, beautiful cycle, {style}",
            f"Dawn beginning to lighten the horizon, celebration becoming softer, golden hour, {style}",
        ]

        # ACT 5: Return (15 scenes)
        act5 = [
            f"First light touching {elements[0]}, colors shifting to warm golden tones, transition, {style}",
            f"Creatures gently guiding children toward the path home, bittersweet farewell, {style}",
            f"Children hugging creatures goodbye, {char2['companion']} looking back, farewell, {style}",
            f"Children climbing back up the path, looking back at {setting} one more time, {style}",
            f"{setting} growing smaller behind them but still glowing softly in dawn light, {style}",
            f"Walking back through the approach path, sunrise filtering through, world feels different, {style}",
            f"{char2['companion']} sleepy and content, riding on shoulder, tired from adventure, {style}",
            f"Child's {char1['accessory']} now glowing with {setting}'s magic, a piece kept forever, {style}",
            f"Village appearing ahead as morning sun rises fully, familiar and welcoming, {style}",
            f"Children walking through quiet morning village, everyone asleep, their secret, {style}",
            f"Child planting the keepsake in their garden, bringing magic home, {style}",
            f"Other child placing glowing token on windowsill, room lit with soft magical light, {style}",
            f"Both children waving to each other from windows, smiling, friendship, {style}",
            f"Garden keepsake already sprouting tiny magical growth, magic spreading, {style}",
            f"Final wide shot: village at sunrise, one tiny magical glow in a garden, stars fading, promise of return, {style}",
        ]

        scenes = act1 + act2 + act3 + act4 + act5
        return scenes

    def generate_narration(self, char1, char2):
        setting = self.theme["setting_name"]
        elements = self.theme["elements"]
        c1 = char1["name"]
        c2 = char2["name"]

        narration = f"""In a quiet village where the days were gentle and the nights were full of wonder, two friends shared a bond stronger than anything the world could offer.

{c1}, with {char1['hair']} hair and {char1['eyes']} eyes, always carried {char1['accessory']}. {c1.split()[0] if ' ' in c1 else c1} was {char1['personality']}, always looking beyond the horizon for something magical.

{c2} was different but perfectly matched. With {char2['companion']} always nearby and a heart full of adventure, {c2} was {char2['personality']}, ready for whatever the world would bring.

One evening, something extraordinary appeared in the distance. Without hesitation, they set out together, following the mystery beyond the village and into the unknown.

The path led them through shadows and silence, until suddenly the world opened up before them. {setting} stretched out in all its glory, a place where {elements[0]} shimmered with inner light, and {elements[1]} drifted through the air like living dreams.

They explored with wide eyes and open hearts. {elements[2]} responded to their gentle touch, and {elements[4]} seemed to welcome them as old friends.

Deeper they ventured, discovering wonders at every turn. Local creatures, shy at first, grew bold enough to approach, sensing the children's kind spirits. {c2}'s {char2['companion']} made friends instantly, and soon they were all exploring together.

But beauty sometimes hides sorrow. At the heart of {setting}, they found its power source damaged and fading. The magic that sustained everything was slowly dying.

Without hesitation, they knew what to do. Working alongside the creatures of {setting}, they gathered what was needed. Every small offering of {elements[1]} brought a little more light back. Every act of care healed another crack.

It was not easy. It required patience, courage, and trust in each other. But together, with the help of every creature who called this place home, they restored what was broken.

The moment the power returned, {setting} erupted in renewed beauty. {elements[0].capitalize()} blazed brighter than ever. {elements[4].capitalize()} danced in celebration. The very air seemed to sing with gratitude.

The creatures thanked them with gifts of light and crystal, small pieces of this magical place to carry forever.

As dawn painted the sky in gold and rose, {c1} and {c2} said their gentle goodbyes. The path home was shorter than the journey there, as paths home always are.

Back in their village, the world looked the same but felt different. {c1}'s {char1['accessory']} now held a permanent glow, and {c2} planted a crystal keepsake in the garden behind their house.

From their windows, they waved goodnight to each other. And in the garden, already, something small and magical had begun to grow.

{setting} would always be there, waiting for their return. And perhaps, on the quietest nights, its magic still reaches their village, carried on the wind.

Goodnight. May your dreams carry you to magical places."""

        return narration

    def generate_config(self):
        char1 = self.generate_character("female")
        char2 = self.generate_character("male")

        # Ensure unique names
        while char2["name"] == char1["name"]:
            char2["name"] = self.rng.choice(NAMES_POOL["male"])

        scenes = self.generate_story_arc(char1, char2)
        narration = self.generate_narration(char1, char2)

        config = {
            "title": f"{self.theme['setting_name']} - Episode {self.episode_num}",
            "description": f"Two friends discover {self.theme['setting_name']} and help restore its fading magic",
            "episode": self.episode_num,
            "theme": self.theme_key,
            "seed": self.seed,
            "characters": [
                {"name": char1["name"], "description": char1["description"]},
                {"name": char2["name"], "description": char2["description"]},
            ],
            "scene": {
                "name": self.theme["setting_name"],
                "description": f"Wide landscape of {self.theme['setting_desc']}, Ghibli style",
            },
            "style": "Studio Ghibli anime style",
            "scenes": scenes,
            "narration": narration,
            "settings": {
                "voice": "en-US-AriaNeural",
                "narration_speed": "-15%",
                "music_volume": 0.18,
                "narration_volume": 1.2,
                "resolution": "1920x1080",
                "fps": 24,
                "video_quality": 18,
                "output_versions": ["narrated", "music_only"],
            },
        }

        return config


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a unique story episode")
    parser.add_argument("--theme", choices=list(THEMES.keys()),
                        help=f"Choose a theme ({', '.join(THEMES.keys())})")
    parser.add_argument("--episode", type=int, help="Episode number")
    parser.add_argument("--seed", type=int, help="Random seed (for reproducibility)")
    parser.add_argument("--output", default="story_config.json", help="Output config file")
    parser.add_argument("--run", action="store_true", help="Also run the full pipeline after generating")
    parser.add_argument("--list-themes", action="store_true", help="List all available themes")

    args = parser.parse_args()

    if args.list_themes:
        print("\nAvailable Themes:")
        print("-" * 50)
        for key, theme in THEMES.items():
            print(f"  {key:15s} - {theme['setting_name']}")
            print(f"  {'':15s}   {theme['mood']}")
            print(f"  {'':15s}   Elements: {', '.join(theme['elements'][:3])}")
            print()
        sys.exit(0)

    generator = EpisodeGenerator(
        theme=args.theme,
        episode_num=args.episode,
        seed=args.seed,
    )

    config = generator.generate_config()

    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\n  Episode Generated!")
    print(f"  Title:      {config['title']}")
    print(f"  Theme:      {generator.theme_key} ({generator.theme['setting_name']})")
    print(f"  Characters: {config['characters'][0]['name']} & {config['characters'][1]['name']}")
    print(f"  Scenes:     {len(config['scenes'])}")
    print(f"  Seed:       {generator.seed}")
    print(f"  Saved to:   {output_path}")
    print()

    if args.run:
        print("  Starting pipeline...")
        import subprocess
        subprocess.run([sys.executable, "run_story.py", "--config", str(output_path)])
