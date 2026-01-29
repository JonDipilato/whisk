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
import re
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

FIXED_CHARACTERS = {
    "luna": {
        "name": "Luna",
        "description": (
            "Anime girl, long silver hair, blue eyes, light blue dress with star patterns, "
            "holding a small lantern, barefoot, gentle smile, Studio Ghibli anime style, white background"
        ),
        "hair": "long silver",
        "eyes": "blue",
        "clothing": "light blue dress with star patterns",
        "accessory": "a small lantern",
        "companion": "",
        "personality": "gentle and kind",
    },
    "kai": {
        "name": "Kai",
        "description": (
            "Anime boy, messy dark brown hair, warm amber-brown eyes, wearing an earthy green jacket with "
            "sewn patches over a cream shirt, brown shorts, leather boots, a tiny orange fox on his shoulder, "
            "adventurous confident smile, Studio Ghibli anime style, white background"
        ),
        "hair": "messy dark brown",
        "eyes": "warm amber-brown",
        "clothing": "earthy green jacket with sewn patches over a cream shirt, brown shorts, leather boots",
        "accessory": "",
        "companion": "a tiny orange fox",
        "personality": "bold and determined",
    },
    "grandma_rose": {
        "name": "Grandma Rose",
        "description": (
            "Elderly woman, silver hair in a bun, rosy cheeks, warm brown eyes, wearing a blue dress "
            "with a cream apron with floral embroidery, gentle wise smile, Studio Ghibli anime style, white background"
        ),
        "hair": "silver in a bun",
        "eyes": "warm brown",
        "clothing": "blue dress with a cream apron with floral embroidery",
        "accessory": "a worn leather satchel of herbs and keepsakes",
        "companion": "",
        "personality": "wise and nurturing",
    },
    "lily": {
        "name": "Lily",
        "description": (
            "Young girl, curly dark brown hair, bright brown eyes, wearing a white cable-knit sweater "
            "and brown pants, curious excited expression, Studio Ghibli anime style, white background"
        ),
        "hair": "curly dark brown",
        "eyes": "bright brown",
        "clothing": "white cable-knit sweater and brown pants",
        "accessory": "a small hand-knit scarf from Grandma",
        "companion": "",
        "personality": "curious and brave",
    },
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


GUEST_ROLES = {
    "guardian": {
        "role_desc": "a wise protector who watches over the {setting}",
        "intro": "emerging from the shadows of {elements}, a gentle figure with ancient knowing eyes",
        "help": "shields the children with a barrier of light, buying them time to complete the restoration",
        "farewell": "fades back into the landscape, becoming one with {setting} once more",
        "personality_pool": ["wise and serene", "quiet but powerful", "ancient and kind"],
    },
    "trickster": {
        "role_desc": "a playful spirit who tests travelers with riddles",
        "intro": "appearing with a mischievous grin, dancing between {elements}",
        "help": "reveals a hidden shortcut through a clever riddle, making the impossible task achievable",
        "farewell": "disappears in a burst of sparkles, laughter echoing as the children wave goodbye",
        "personality_pool": ["mischievous and clever", "playful and quick", "witty and energetic"],
    },
    "lost_one": {
        "role_desc": "a wanderer searching for their way home",
        "intro": "sitting alone near {elements}, looking lost but hopeful",
        "help": "remembers an old path from their wandering that leads directly to the power source",
        "farewell": "finally finds their way home as the magic restores, waving with tears of joy",
        "personality_pool": ["gentle and uncertain", "hopeful and wandering", "shy but warm"],
    },
    "healer": {
        "role_desc": "a gentle soul who mends what is broken",
        "intro": "kneeling beside a wounded {elements}, hands glowing with soft healing light",
        "help": "channels healing energy into the damaged source, amplifying the children's efforts tenfold",
        "farewell": "places a blessing on each child before dissolving into warm golden light",
        "personality_pool": ["compassionate and steady", "warm and nurturing", "calm and focused"],
    },
}

HOOK_TEMPLATES = [
    "On the night the sky first shimmered over {setting}, {c1} and {c2} felt a quiet pull toward the unknown.",
    "Before the stars fully woke, {c1} and {c2} noticed {elements1} drifting through the air, like a soft invitation.",
    "When the world grew still and {elements0} began to glow, {c1} and {c2} knew this night would be different.",
    "A hush fell over the village as {elements2} flickered in the distance, and {c1} and {c2} followed the feeling in their hearts.",
]

HOOK_TEMPLATES_GRANDMA = [
    "On the evening {c2} came to visit, {c1} had a story waiting — but this time, the story was real.",
    "The kettle had just finished singing when {c1} took {c2}'s hand and said, 'Tonight, I want to show you something special.'",
    "As the last light faded from the kitchen window, {c1} wrapped a shawl around {c2}'s shoulders and whispered, 'Come with me.'",
    "The fireflies had barely begun to glow when {c1} and {c2} stepped outside, following {elements0} toward something wonderful.",
]

PAUSE_LINES = [
    "For a moment, everything was still and calm.",
    "They paused to breathe, letting the quiet settle around them.",
    "A gentle hush drifted through the air, soft and unhurried.",
    "The light lingered, and time seemed to slow.",
    "They listened to the silence, warm and safe.",
    "The world held its breath, peaceful and steady.",
    "Softly, the night whispered and carried them onward.",
    "A quiet calm wrapped around them like a blanket.",
]

TRANSITION_LINES = [
    "The night grew deeper, and the path opened gently ahead.",
    "With each step, the world felt softer and more magical.",
    "They moved on together, guided by the quiet glow around them.",
    "The journey continued, slow and steady, like a lullaby.",
]


# =============================================================================
# STORY GENERATOR
# =============================================================================

class EpisodeGenerator:
    def __init__(
        self,
        theme=None,
        episode_num=None,
        seed=None,
        new_character=False,
        use_luna_kai=False,
        avoid_theme=None,
        target_minutes=10,
        profile="friends",
    ):
        if seed is None:
            seed = int(datetime.now().timestamp() * 1000) % 2**32
        self.rng = random.Random(seed)
        self.seed = seed
        self.new_character = new_character
        self.use_luna_kai = use_luna_kai
        self.target_minutes = target_minutes
        self.profile = profile

        if theme and theme in THEMES:
            self.theme_key = theme
        else:
            theme_keys = list(THEMES.keys())
            if avoid_theme in theme_keys and len(theme_keys) > 1:
                theme_keys.remove(avoid_theme)
            self.theme_key = self.rng.choice(theme_keys)

        self.theme = THEMES[self.theme_key]
        self.episode_num = episode_num or self.rng.randint(1, 999)

    def _get_fixed_character(self, key):
        data = FIXED_CHARACTERS[key]
        return dict(data)

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

    def generate_guest_character(self):
        """Generate a third guest character with a specific role archetype."""
        role_key = self.rng.choice(list(GUEST_ROLES.keys()))
        role = GUEST_ROLES[role_key]

        gender = self.rng.choice(["female", "male"])
        name = self.rng.choice(NAMES_POOL[gender])
        hair_color = self.rng.choice(CHARACTER_TRAITS["hair_colors"])
        hair_style = self.rng.choice(CHARACTER_TRAITS["hair_styles"])
        eye_color = self.rng.choice(CHARACTER_TRAITS["eye_colors"])
        clothing = self.rng.choice(CHARACTER_TRAITS["clothing_styles"])
        personality = self.rng.choice(role["personality_pool"])

        description = (
            f"Anime character, {hair_style} {hair_color} hair, {eye_color} eyes, "
            f"wearing {clothing}, {personality} expression, "
            f"mysterious and ethereal aura, Ghibli style, white background"
        )

        return {
            "name": name,
            "description": description,
            "hair": f"{hair_style} {hair_color}",
            "eyes": eye_color,
            "clothing": clothing,
            "personality": personality,
            "role": role_key,
            "role_data": role,
        }

    def generate_story_arc(self, char1, char2, char3=None):
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

        # ACT 2: Exploration (15 scenes) - guest character appears here
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

        if char3:
            role_data = char3["role_data"]
            c3_desc = f"mysterious character with {char3['hair']} hair"
            intro_scene = role_data["intro"].format(setting=setting, elements=elements[0])
            # Insert guest character appearance at scene 8-9 of Act 2
            act2[7] = f"{c3_desc} {intro_scene}, {style}"
            act2[8] = f"Children cautiously approaching the mysterious figure, {char2['companion']} curious, {style}"
            act2[9] = f"The mysterious character smiling warmly at the children, {char3['personality']} demeanor, trust forming, {style}"

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

        if char3:
            role_data = char3["role_data"]
            c3_desc = f"mysterious character with {char3['hair']} hair"
            help_scene = role_data["help"]
            # Guest character helps during the critical moment in Act 3
            act3[8] = f"{c3_desc} stepping forward with determination, ready to help, {style}"
            act3[9] = f"{char3['name']} {help_scene}, magical energy flowing, {style}"
            act3[10] = f"Children and {char3['name']} working together, power source responding to their combined effort, {style}"

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

        if char3:
            role_data = char3["role_data"]
            c3_desc = f"mysterious character with {char3['hair']} hair"
            farewell_scene = role_data["farewell"].format(setting=setting, elements=elements[0])
            # Guest character farewell in Act 5
            act5[3] = f"{char3['name']} standing at the boundary of {setting}, {farewell_scene}, {style}"
            act5[4] = f"Children hugging {char3['name']} goodbye, {c3_desc} smiling peacefully, heartfelt farewell, {style}"

        scenes = act1 + act2 + act3 + act4 + act5
        return scenes

    def _estimate_minutes(self, text: str, words_per_minute: int = 130) -> float:
        words = re.findall(r"[A-Za-z0-9']+", text)
        return len(words) / max(words_per_minute, 1)

    def _make_hook(self, char1, char2, setting, elements):
        template = self.rng.choice(HOOK_TEMPLATES)
        return template.format(
            c1=char1["name"],
            c2=char2["name"],
            setting=setting,
            elements0=elements[0],
            elements1=elements[1],
            elements2=elements[2],
        )

    def _insert_pause_lines(self, paragraphs, max_lines=None):
        if not paragraphs:
            return paragraphs
        available = list(PAUSE_LINES)
        self.rng.shuffle(available)
        pause_lines = available[:max_lines] if max_lines else available

        enriched = []
        for idx, para in enumerate(paragraphs):
            enriched.append(para)
            if idx < len(paragraphs) - 1 and pause_lines:
                if idx % 2 == 1:
                    enriched.append(pause_lines.pop(0))
        return enriched

    def _pad_narration_to_target(self, narration: str) -> str:
        if not self.target_minutes:
            return narration

        target = float(self.target_minutes)
        estimate = self._estimate_minutes(narration)
        if estimate >= target:
            return narration

        paragraphs = [p.strip() for p in narration.split("\n\n") if p.strip()]
        paragraphs = self._insert_pause_lines(paragraphs, max_lines=6)
        narration = "\n\n".join(paragraphs)

        estimate = self._estimate_minutes(narration)
        if estimate >= target:
            return narration

        extra_lines = list(TRANSITION_LINES) + list(PAUSE_LINES)
        self.rng.shuffle(extra_lines)
        while estimate < target and extra_lines:
            insert_at = self.rng.randint(1, max(1, len(paragraphs) - 1))
            paragraphs.insert(insert_at, extra_lines.pop(0))
            narration = "\n\n".join(paragraphs)
            estimate = self._estimate_minutes(narration)

        return narration

    def generate_narration(self, char1, char2, char3=None):
        setting = self.theme["setting_name"]
        elements = self.theme["elements"]
        c1 = char1["name"]
        c2 = char2["name"]

        # Guest character narration segments
        guest_intro = ""
        guest_help = ""
        guest_farewell = ""
        if char3:
            c3 = char3["name"]
            role_data = char3["role_data"]
            guest_intro = (
                f"\n\nDeeper into {setting}, they encountered someone unexpected. "
                f"{c3}, {role_data['role_desc'].format(setting=setting)}, appeared before them. "
                f"{c3} was {char3['personality']}, and something about their presence felt both ancient and warm. "
                f"Though strangers, trust formed quickly between them.\n"
            )
            guest_help = (
                f" And then {c3} stepped forward. {role_data['help'].capitalize()}. "
                f"With {c3}'s aid, what seemed impossible became real.\n"
            )
            guest_farewell = (
                f"\n\nBefore leaving {setting}, they found {c3} one last time. "
                f"{c3} {role_data['farewell'].format(setting=setting, elements=elements[0])}. "
                f"{c1} and {c2} knew they would never forget {c3}.\n"
            )

        hook = self._make_hook(char1, char2, setting, elements)

        narration = f"""{hook}

In a quiet village where the days were gentle and the nights were full of wonder, two friends shared a bond stronger than anything the world could offer.

{c1}, with {char1['hair']} hair and {char1['eyes']} eyes, always carried {char1['accessory']}. {c1.split()[0] if ' ' in c1 else c1} was {char1['personality']}, always looking beyond the horizon for something magical.

{c2} was different but perfectly matched. With {char2['companion']} always nearby and a heart full of adventure, {c2} was {char2['personality']}, ready for whatever the world would bring.

One evening, something extraordinary appeared in the distance. Without hesitation, they set out together, following the mystery beyond the village and into the unknown.

The path led them through shadows and silence, until suddenly the world opened up before them. {setting} stretched out in all its glory, a place where {elements[0]} shimmered with inner light, and {elements[1]} drifted through the air like living dreams.

They explored with wide eyes and open hearts. {elements[2]} responded to their gentle touch, and {elements[4]} seemed to welcome them as old friends.{guest_intro}

Deeper they ventured, discovering wonders at every turn. Local creatures, shy at first, grew bold enough to approach, sensing the children's kind spirits. {c2}'s {char2['companion']} made friends instantly, and soon they were all exploring together.

But beauty sometimes hides sorrow. At the heart of {setting}, they found its power source damaged and fading. The magic that sustained everything was slowly dying.

Without hesitation, they knew what to do. Working alongside the creatures of {setting}, they gathered what was needed. Every small offering of {elements[1]} brought a little more light back. Every act of care healed another crack.

It was not easy. It required patience, courage, and trust in each other.{guest_help} But together, with the help of every creature who called this place home, they restored what was broken.

The moment the power returned, {setting} erupted in renewed beauty. {elements[0].capitalize()} blazed brighter than ever. {elements[4].capitalize()} danced in celebration. The very air seemed to sing with gratitude.

The creatures thanked them with gifts of light and crystal, small pieces of this magical place to carry forever.{guest_farewell}

As dawn painted the sky in gold and rose, {c1} and {c2} said their gentle goodbyes. The path home was shorter than the journey there, as paths home always are.

Back in their village, the world looked the same but felt different. {c1}'s {char1['accessory']} now held a permanent glow, and {c2} planted a crystal keepsake in the garden behind their house.

From their windows, they waved goodnight to each other. And in the garden, already, something small and magical had begun to grow.

{setting} would always be there, waiting for their return. And perhaps, on the quietest nights, its magic still reaches their village, carried on the wind.

Goodnight. May your dreams carry you to peaceful, magical places."""

        narration = self._pad_narration_to_target(narration)
        return narration

    def _make_hook_grandma(self, char1, char2, setting, elements):
        template = self.rng.choice(HOOK_TEMPLATES_GRANDMA)
        return template.format(
            c1=char1["name"],
            c2=char2["name"],
            setting=setting,
            elements0=elements[0],
            elements1=elements[1],
            elements2=elements[2],
        )

    def generate_story_arc_grandma(self, char1, char2, char3=None):
        setting = self.theme["setting_name"]
        elements = self.theme["elements"]
        mood = self.theme["mood"]
        conflict_key = self.theme["conflict"]
        conflict = CONFLICT_TEMPLATES[conflict_key]

        style = "Studio Ghibli anime style"
        g = char1["name"]  # Grandma Rose
        l = char2["name"]  # Lily
        g_desc = "elderly woman with silver hair in a bun"
        l_desc = "young girl with curly brown hair"

        scenes = []

        # ACT 1: A Quiet Beginning (15 scenes)
        act1 = [
            f"Cozy cottage kitchen at evening, warm lamplight, teacups on table, grandmother and granddaughter together, {style}",
            f"{g_desc} pouring tea, smiling warmly at {l_desc} sitting across the table, cozy interior, {style}",
            f"{l_desc} leaning forward eagerly, listening to {g_desc} tell a story, firelight on their faces, {style}",
            f"{g_desc} gesturing toward the window where {elements[0]} shimmer faintly in the distance, {style}",
            f"{l_desc} pressing her face to the window, eyes wide with wonder, {mood} sky outside, {style}",
            f"{g_desc} wrapping a shawl around {l_desc}'s shoulders, getting ready to go outside, {style}",
            f"Grandmother and granddaughter stepping out the front door into the {mood} evening, hand in hand, {style}",
            f"Two figures walking along a quiet country path at dusk, {g_desc} and {l_desc}, lantern light, {style}",
            f"{l_desc} pointing excitedly at {elements[1]} appearing along the path, {g_desc} smiling knowingly, {style}",
            f"Path winding through soft twilight, {elements[0]} growing brighter ahead, anticipation, {style}",
            f"The path opening up to reveal {setting}, {self.theme['setting_desc'][:80]}, both figures gasping, {style}",
            f"{g_desc} and {l_desc} entering {setting} together, surrounded by {elements[0]}, magical atmosphere, {style}",
            f"{l_desc} reaching out to touch {elements[0]}, {g_desc} watching with gentle pride, {style}",
            f"{g_desc} kneeling beside {l_desc} to examine {elements[2]} up close, teaching moment, {style}",
            f"Grandmother and granddaughter standing at the heart of {setting}, taking it all in, hand in hand, {style}",
        ]

        # ACT 2: Discovering Together (15 scenes) — guest character appears here
        act2 = [
            f"The heart of {setting} in full beauty, {g_desc} and {l_desc} exploring side by side, {style}",
            f"{g_desc} pointing out details of {elements[1]} to {l_desc}, sharing old knowledge, {style}",
            f"{l_desc} discovering a hidden patch of {elements[2]}, calling grandmother over excitedly, {style}",
            f"{g_desc} telling a story about {setting}, {l_desc} sitting on a mossy rock listening, {style}",
            f"Local magical creatures appearing, curious about the pair, gentle and glowing, {style}",
            f"{l_desc} befriending a small creature, {g_desc} watching with warm eyes, {style}",
            f"Grandmother showing granddaughter how to care for {elements[2]}, gentle hands working together, {style}",
            f"New growth appearing where they helped, {l_desc} clapping with delight, {g_desc} nodding wisely, {style}",
            f"{l_desc} running ahead on the path, looking back to make sure {g_desc} is following, {style}",
            f"{g_desc} and {l_desc} climbing a gentle hill to look out over {setting}, panoramic view, {style}",
            f"Beautiful panoramic view of {setting} from above, all {elements[0]} visible, breathtaking, {style}",
            f"{g_desc} sitting on a bench while {l_desc} explores nearby, peaceful watching, {style}",
            f"Grandmother and granddaughter following a hidden trail deeper into {setting}, {style}",
            f"{l_desc} noticing something is wrong, {elements[0]} dimming, tugging grandmother's sleeve, worried, {style}",
            f"Hidden entrance to the source of {setting}'s power, ancient symbols glowing faintly, {style}",
        ]

        if char3:
            role_data = char3["role_data"]
            c3_desc = f"mysterious character with {char3['hair']} hair"
            intro_scene = role_data["intro"].format(setting=setting, elements=elements[0])
            act2[7] = f"{c3_desc} {intro_scene}, {style}"
            act2[8] = f"{l_desc} hiding behind {g_desc}, peeking out at the mysterious figure, {style}"
            act2[9] = f"{g_desc} greeting the mysterious character warmly, {char3['personality']} demeanor, trust forming, {style}"

        # ACT 3: A Gentle Challenge (15 scenes)
        act3 = [
            f"Grandmother and granddaughter entering the ancient chamber at {setting}'s core, glowing symbols, {style}",
            f"Inside a vast space, the power source visible but damaged, {g_desc} looking concerned, {style}",
            f"The damaged power source in detail, cracks and fading light, {l_desc} looking up at {g_desc} for guidance, {style}",
            f"{g_desc} studying the ancient symbols on the walls, remembering something, {style}",
            f"{g_desc} explaining to {l_desc} what needs to be done, kneeling to her level, gentle instruction, {style}",
            f"{l_desc} gathering pieces of {elements[1]} with determination, small hands working carefully, {style}",
            f"{g_desc} guiding {l_desc}'s hands to place an offering near the source, patient teaching, {style}",
            f"Power source responding to the offering, tiny spark of healing light, both smiling, {style}",
            f"{l_desc} running to gather more, energetic and determined, {g_desc} directing her gently, {style}",
            f"Creatures joining the effort, bringing pieces to help, {l_desc} working alongside them, {style}",
            f"{g_desc} humming an old song, the sound itself seeming to help the healing, magical, {style}",
            f"Power source growing stronger, {l_desc} and {g_desc} working side by side, {style}",
            f"{l_desc} lifting the final piece, {g_desc}'s steady hands helping her reach, together, {style}",
            f"Placing the final piece, massive surge of brilliant light, grandmother shielding granddaughter's eyes, {style}",
            f"Wave of restored magic bursting outward from the source, spreading everywhere, {style}",
        ]

        if char3:
            role_data = char3["role_data"]
            c3_desc = f"mysterious character with {char3['hair']} hair"
            help_scene = role_data["help"]
            act3[8] = f"{c3_desc} stepping forward with determination, ready to help, {style}"
            act3[9] = f"{char3['name']} {help_scene}, magical energy flowing, {style}"
            act3[10] = f"Grandmother, granddaughter, and {char3['name']} working together, combined effort, {style}"

        # ACT 4: Renewed Wonder (15 scenes)
        act4 = [
            f"Grandmother and granddaughter emerging to see {setting} transformed, brighter than ever, {style}",
            f"{elements[0]} growing more vibrant, {l_desc} spinning with arms wide in delight, {style}",
            f"{elements[4]} more beautiful now, moving in graceful patterns, renewed energy, {style}",
            f"New growth everywhere, {elements[2]} blooming in every color, carpet of beauty, {style}",
            f"The centerpiece of {setting} now magnificent, restored to full power, golden light, {style}",
            f"Hundreds of creatures filling the air in celebration, {l_desc} laughing, {style}",
            f"{g_desc} sitting on a mossy stone, {l_desc} resting her head on grandmother's lap, peaceful, {style}",
            f"Grandmother stroking granddaughter's hair as they watch the celebration together, content, {style}",
            f"Creatures showing gratitude, a small one landing on {l_desc}'s outstretched finger, {style}",
            f"{g_desc} receiving a small crystal keepsake from a grateful creature, {style}",
            f"Grand celebration, all creatures dancing, {l_desc} dancing among them, {g_desc} clapping along, {style}",
            f"{l_desc} pulling {g_desc} up to dance, grandmother laughing, dancing slowly together, {style}",
            f"The ancient center at its brightest, sending light into the sky, connecting everything, {style}",
            f"New elements born from renewed power, floating upward, beautiful cycle, {style}",
            f"Dawn beginning to lighten the horizon, celebration becoming softer, golden hour, {style}",
        ]

        # ACT 5: Walking Home (15 scenes)
        act5 = [
            f"First light touching {elements[0]}, colors shifting to warm golden tones, {style}",
            f"Creatures gently guiding grandmother and granddaughter toward the path home, {style}",
            f"{l_desc} hugging a small creature goodbye, {g_desc} waving warmly to the others, {style}",
            f"Grandmother and granddaughter walking slowly back, {l_desc} holding {g_desc}'s hand tightly, {style}",
            f"{setting} growing smaller behind them but still glowing softly in dawn light, {style}",
            f"{l_desc} yawning, leaning against {g_desc}'s arm as they walk, sleepy after the adventure, {style}",
            f"{g_desc} wrapping her arm around {l_desc}'s shoulders, steady and warm, sunrise path, {style}",
            f"Country path in early morning light, two figures walking slowly home, peaceful, {style}",
            f"Cottage appearing ahead, smoke from chimney, welcoming and familiar, {style}",
            f"Grandmother opening the cottage door, {l_desc} stumbling in sleepily, warm inside, {style}",
            f"{g_desc} tucking {l_desc} into bed, pulling the quilt up gently, {style}",
            f"{g_desc} placing the crystal keepsake on the nightstand beside sleeping {l_desc}, soft glow, {style}",
            f"{l_desc} already asleep, small smile on her face, grandmother kissing her forehead, {style}",
            f"The keepsake glowing softly on the nightstand, tiny sparkles drifting, {style}",
            f"Final wide shot: cottage at sunrise, one tiny magical glow in the window, stars fading, peaceful, {style}",
        ]

        if char3:
            role_data = char3["role_data"]
            c3_desc = f"mysterious character with {char3['hair']} hair"
            farewell_scene = role_data["farewell"].format(setting=setting, elements=elements[0])
            act5[3] = f"{char3['name']} standing at the boundary of {setting}, {farewell_scene}, {style}"
            act5[4] = f"{l_desc} hugging {char3['name']} goodbye, {g_desc} placing a hand on {char3['name']}'s shoulder, {style}"

        scenes = act1 + act2 + act3 + act4 + act5
        return scenes

    def generate_narration_grandma(self, char1, char2, char3=None):
        setting = self.theme["setting_name"]
        elements = self.theme["elements"]
        g = char1["name"]  # Grandma Rose
        l = char2["name"]  # Lily

        guest_intro = ""
        guest_help = ""
        guest_farewell = ""
        if char3:
            c3 = char3["name"]
            role_data = char3["role_data"]
            guest_intro = (
                f"\n\nDeeper into {setting}, they met someone unexpected. "
                f"{c3}, {role_data['role_desc'].format(setting=setting)}, appeared before them. "
                f"{g} greeted {c3} warmly, and {l} peeked out from behind her grandmother with curious eyes. "
                f"Trust came easily — {c3} was {char3['personality']}, and {g} seemed to know their kind.\n"
            )
            guest_help = (
                f" Then {c3} stepped forward. {role_data['help'].capitalize()}. "
                f"With {c3}'s help, and {g}'s steady guidance, {l} found the courage to finish what they had started.\n"
            )
            guest_farewell = (
                f"\n\nBefore leaving {setting}, they found {c3} one last time. "
                f"{c3} {role_data['farewell'].format(setting=setting, elements=elements[0])}. "
                f"{l} waved until {c3} was out of sight, and {g} whispered, 'Some friends are only meant for one night, but they stay with you forever.'\n"
            )

        hook = self._make_hook_grandma(char1, char2, setting, elements)

        narration = f"""{hook}

{g} had always been the kind of grandmother who kept magic in her pockets. Not the storybook kind — the real kind. The kind you feel when someone who loves you takes your hand and says, 'Let me show you something.'

{l}, with her {char2['hair']} hair and {char2['eyes']} eyes, adored her grandmother more than anyone in the world. Every visit to {g}'s cottage meant stories by the fire, warm tea with honey, and the feeling that anything was possible.

Tonight was different, though. {g} had that look in her eyes — the one that meant an adventure was coming.

'Put on your sweater, dear,' {g} said, wrapping a shawl around her own shoulders. 'There's something I've been waiting to show you, and tonight is the night.'

{l} didn't need to be told twice. She pulled on her white cable-knit sweater and took her grandmother's hand, and together they stepped into the cool evening air.

The path was one {g} seemed to know by heart, though {l} had never seen it before. It wound past the garden, through a grove of old trees, and then — quite suddenly — the world opened up before them.

{setting} stretched out in all its glory, a place where {elements[0]} shimmered with inner light, and {elements[1]} drifted through the air like living dreams.

'Oh, Grandma,' {l} breathed. 'It's beautiful.'

'It is,' {g} said softly, squeezing her hand. 'I came here once, a long time ago. I've been waiting for the right person to share it with.'

They explored together, hand in hand. {g} pointed out the hidden details — how {elements[2]} responded to a gentle touch, how {elements[4]} moved in patterns if you watched long enough. {l} listened to every word, her eyes wide, storing it all away like treasure.{guest_intro}

'Grandma, how do you know so much about this place?' {l} asked.

{g} smiled. 'Some things you learn from books, and some things you learn by paying attention. The best things, though — those you learn by loving the world enough to notice.'

But beauty sometimes carries sorrow with it. At the heart of {setting}, they found its power source damaged and fading. The magic that sustained everything was slowly dimming.

{l} looked up at her grandmother with worried eyes. 'Can we fix it?'

{g} knelt beside her and placed both hands on {l}'s shoulders. 'We can try. Together. I'll show you what to do, and you'll do the hard part — because young hands carry the most hope.'

And so they worked. {g} guided and {l} gathered, her small hands careful with every piece of {elements[1]}. Each offering brought a little more light back. Each act of care healed another crack.

It was not easy. It required patience, and trust, and the kind of quiet courage that doesn't shout but simply keeps going.{guest_help} But together, piece by piece, they mended what was broken.

The moment the power returned, {setting} erupted in renewed beauty. {elements[0].capitalize()} blazed brighter than ever. {elements[4].capitalize()} danced in celebration. The very air seemed to hum a song of gratitude.

{l} threw her arms around her grandmother. 'We did it!'

{g} held her tight and whispered, 'You did it, my darling. I just showed you the way.'

The creatures of {setting} thanked them with small gifts — a crystal that caught the light, a flower that would never wilt. {g} tucked the crystal into her apron pocket and gave the flower to {l}.{guest_farewell}

As dawn painted the sky in gold and rose, they began the walk home. {l}'s steps grew slower and her eyelids grew heavy. She leaned against her grandmother's arm, letting {g}'s steady pace carry them both.

'Grandma?' {l} murmured. 'Will we come back?'

'Whenever you need to, sweetheart. It will always be here.'

Back at the cottage, {g} carried {l} the last few steps to bed, pulling the quilt up to her chin and placing the crystal keepsake on the nightstand. It glowed softly, filling the room with the faintest shimmer of {setting}'s magic.

{g} kissed {l}'s forehead and whispered, 'Goodnight, my brave girl. May your dreams carry you back to all the beautiful places.'

And in the soft glow of that tiny crystal, {l} smiled in her sleep, already dreaming of the next adventure with her grandmother.

Goodnight. May your dreams be warm, and may someone who loves you always be near."""

        narration = self._pad_narration_to_target(narration)
        return narration

    def _build_scene_refs_friends(self, has_char3=False):
        """Build per-scene character assignments for friends/Luna-Kai profile.

        Maps each of the 75 scenes to which characters should appear,
        based on the story arc structure. Gives Whisk better results
        by only uploading relevant character refs per scene.
        """
        B = []             # No characters (establishing/environment shot)
        C1 = ["C1"]        # First character solo
        C2 = ["C2"]        # Second character solo
        BOTH = ["C1", "C2"]
        C3 = ["C3"]
        ALL3 = ["C1", "C2", "C3"]

        act1 = [
            B,     # 1: Peaceful evening village
            C1,    # 2: c1 looking out window
            C2,    # 3: c2 running excitedly
            BOTH,  # 4: Two friends meeting
            BOTH,  # 5: Two children walking
            B,     # 6: Path opening to reveal setting
            BOTH,  # 7: Children entering setting
            C1,    # 8: Close-up, child reaching
            C2,    # 9: Companion exploring
            BOTH,  # 10: Children discovering
            C1,    # 11: Child interacting
            B,     # 12: Elements stretching
            BOTH,  # 13: Children following
            BOTH,  # 14: Both exploring, laughing
            BOTH,  # 15: Arriving at heart
        ]

        act2 = [
            B,     # 1: Heart revealed
            B,     # 2: Creatures appearing
            C1,    # 3: Creatures with c1
            C2,    # 4: Companion playing
            BOTH,  # 5: Hidden garden discovery
            BOTH,  # 6: Helping tend
            B,     # 7: New growth appearing
            B,     # 8: Creatures celebrating
            C1,    # 9: Child climbing viewpoint
            B,     # 10: Panoramic view
            BOTH,  # 11: Following hidden path
            BOTH,  # 12: Crossing bridge
            BOTH,  # 13: Ancient part
            BOTH,  # 14: Noticing something wrong
            B,     # 15: Hidden entrance
        ]

        act3 = [
            BOTH,  # 1: Entering chamber
            B,     # 2: Inside vast space
            B,     # 3: Damaged source detail
            BOTH,  # 4: Children looking worried
            B,     # 5: Ancient images on walls
            B,     # 6: Images showing connections
            C1,    # 7: Child placing element
            B,     # 8: Source responding
            C2,    # 9: Companion rushing to gather
            B,     # 10: Creatures joining effort
            B,     # 11: Source growing stronger
            BOTH,  # 12: Everyone working together
            BOTH,  # 13: Final big effort
            BOTH,  # 14: Placing final piece
            B,     # 15: Wave of restored magic
        ]

        act4 = [
            BOTH,  # 1: Children emerging
            B,     # 2: Elements vibrant
            B,     # 3: Creatures beautiful
            B,     # 4: New growth everywhere
            B,     # 5: Centerpiece magnificent
            B,     # 6: Creatures celebration
            C2,    # 7: Companion dancing
            BOTH,  # 8: Children sitting peacefully
            BOTH,  # 9: Creatures showing gratitude
            C1,    # 10: Child receiving keepsake
            B,     # 11: Grand celebration
            BOTH,  # 12: Children joining celebration
            B,     # 13: Ancient center brightest
            B,     # 14: New elements born
            B,     # 15: Dawn beginning
        ]

        act5 = [
            B,     # 1: First light
            BOTH,  # 2: Creatures guiding children
            BOTH,  # 3: Children hugging creatures goodbye
            BOTH,  # 4: Children climbing path
            B,     # 5: Setting growing smaller
            BOTH,  # 6: Walking back through path
            C2,    # 7: Companion sleepy
            C1,    # 8: Child's accessory glowing
            B,     # 9: Village appearing
            BOTH,  # 10: Children walking village
            C1,    # 11: Child planting keepsake
            C2,    # 12: Other child placing token
            BOTH,  # 13: Both waving from windows
            B,     # 14: Garden keepsake sprouting
            B,     # 15: Final wide shot
        ]

        if has_char3:
            act2[7] = C3
            act2[8] = ALL3
            act2[9] = ALL3
            act3[8] = C3
            act3[9] = ALL3
            act3[10] = ALL3
            act5[3] = ALL3
            act5[4] = ALL3

        all_refs = act1 + act2 + act3 + act4 + act5
        return [{"character_codes": codes} for codes in all_refs]

    def generate_config(self):
        if self.profile == "grandma":
            char1 = self._get_fixed_character("grandma_rose")
            char2 = self._get_fixed_character("lily")
        elif self.use_luna_kai:
            char1 = self._get_fixed_character("luna")
            char2 = self._get_fixed_character("kai")
        else:
            char1 = self.generate_character("female")
            char2 = self.generate_character("male")

            # Ensure unique names
            while char2["name"] == char1["name"]:
                char2["name"] = self.rng.choice(NAMES_POOL["male"])

        # Generate optional guest character
        char3 = None
        if self.new_character:
            char3 = self.generate_guest_character()
            while char3["name"] in (char1["name"], char2["name"]):
                char3["name"] = self.rng.choice(
                    NAMES_POOL["female"] + NAMES_POOL["male"]
                )

        if self.profile == "grandma":
            scenes = self.generate_story_arc_grandma(char1, char2, char3)
            narration = self.generate_narration_grandma(char1, char2, char3)
        else:
            scenes = self.generate_story_arc(char1, char2, char3)
            narration = self.generate_narration(char1, char2, char3)

        characters_list = [
            {"name": char1["name"], "description": char1["description"], "code": "C1"},
            {"name": char2["name"], "description": char2["description"], "code": "C2"},
        ]
        if char3:
            characters_list.append({
                "name": char3["name"],
                "description": char3["description"],
                "code": "C3",
                "role": char3["role"],
                "appears_from_scene": 22,  # Act 2, scene 8
            })

        if self.profile == "grandma":
            description = f"Grandma Rose and Lily discover {self.theme['setting_name']} and help restore its magic"
        else:
            description = f"Two friends discover {self.theme['setting_name']} and help restore its fading magic"

        # Build scene_refs for friends/Luna-Kai profile
        scene_refs = None
        if self.profile != "grandma":
            scene_refs = self._build_scene_refs_friends(has_char3=char3 is not None)

        config = {
            "title": f"{self.theme['setting_name']} - Episode {self.episode_num}",
            "description": description,
            "episode": self.episode_num,
            "theme": self.theme_key,
            "seed": self.seed,
            "characters": characters_list,
            "scene": {
                "name": self.theme["setting_name"],
                "description": f"Wide landscape of {self.theme['setting_desc']}, Ghibli style",
            },
            "style": "Studio Ghibli anime style",
            "scenes": scenes,
            "scene_refs": scene_refs,
            "narration": narration,
            "settings": {
                "voice": "en-US-AriaNeural",
                "narration_speed": "-20%",
                "music_volume": 0.18,
                "narration_volume": 1.2,
                "resolution": "1920x1080",
                "fps": 24,
                "video_quality": 18,
                "output_versions": ["narrated", "music_only"],
                "target_minutes": self.target_minutes,
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
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube after pipeline completes")
    parser.add_argument("--schedule", type=int, default=None,
                        help="Schedule upload N hours from now (implies --upload)")
    parser.add_argument("--profile", choices=["friends", "grandma"], default="friends",
                        help="Story profile: friends (default) or grandma (Lily & Grandma Rose)")
    parser.add_argument("--new-character", action="store_true",
                        help="Add a guest character (guardian/trickster/lost_one/healer) who appears in Act 2")
    parser.add_argument("--use-luna-kai", action="store_true",
                        help="Use fixed Luna & Kai character traits aligned to reference images")
    parser.add_argument("--target-minutes", type=float, default=10,
                        help="Target narration length in minutes (default: 10)")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory for the episode (default: output/episodes/episode_<num>_<theme>_<timestamp>)")
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

    previous_theme = None
    output_path = Path(args.output)
    if args.theme is None and output_path.exists():
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing_config = json.load(f)
                previous_theme = existing_config.get("theme")
        except Exception:
            previous_theme = None

    def _load_episode_counter() -> int | None:
        counter_path = Path("data") / "episode_counter.json"
        if counter_path.exists():
            try:
                with open(counter_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                last_episode = data.get("last_episode")
                if isinstance(last_episode, int) and last_episode >= 0:
                    return last_episode
            except Exception:
                return None
        return None

    def _count_episodes_in_folders() -> int:
        episodes_dir = Path("output") / "episodes"
        count = 0
        if episodes_dir.exists():
            for entry in episodes_dir.iterdir():
                if not entry.is_dir():
                    continue
                if entry.name.startswith("episode_"):
                    count += 1
        return count

    episode_num = args.episode
    if episode_num is None:
        counter_episode = _load_episode_counter()
        folder_count = _count_episodes_in_folders()
        if isinstance(counter_episode, int):
            # If the counter looks out of sync with actual episodes, trust the folder count.
            last_episode = folder_count if folder_count > 0 and counter_episode > folder_count else counter_episode
        else:
            last_episode = folder_count
        episode_num = last_episode + 1

    generator = EpisodeGenerator(
        theme=args.theme,
        episode_num=episode_num,
        seed=args.seed,
        new_character=args.new_character,
        use_luna_kai=args.use_luna_kai,
        avoid_theme=previous_theme,
        target_minutes=args.target_minutes,
        profile=args.profile,
    )

    config = generator.generate_config()

    output_dir = args.output_dir
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("output") / "episodes" / f"episode_{config['episode']}_{generator.theme_key}_{timestamp}"
    else:
        output_dir = Path(output_dir)

    if args.profile == "grandma" and len(config["characters"]) >= 2:
        config["characters"][0]["image_path"] = "data/characters/grandmother_01.png"
        config["characters"][1]["image_path"] = "data/characters/lily_01.png"
    elif args.use_luna_kai and len(config["characters"]) >= 2:
        config["characters"][0]["image_path"] = "data/characters/luna_01.png"
        config["characters"][1]["image_path"] = "data/characters/kai_01.png"

    scene_slug = config["scene"]["name"].lower().replace(" ", "_")
    config["scene"]["image_path"] = str(output_dir / "refs" / f"{scene_slug}.png")

    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    counter_path = Path("data") / "episode_counter.json"
    counter_path.parent.mkdir(parents=True, exist_ok=True)
    with open(counter_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "last_episode": config["episode"],
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            },
            f,
            indent=2,
        )

    print(f"\n  Episode Generated!")
    print(f"  Title:      {config['title']}")
    print(f"  Theme:      {generator.theme_key} ({generator.theme['setting_name']})")
    char_names = f"{config['characters'][0]['name']} & {config['characters'][1]['name']}"
    if len(config['characters']) > 2:
        char3_info = config['characters'][2]
        char_names += f" + {char3_info['name']} ({char3_info['role']})"
    print(f"  Characters: {char_names}")
    print(f"  Scenes:     {len(config['scenes'])}")
    print(f"  Seed:       {generator.seed}")
    print(f"  Saved to:   {output_path}")
    print()

    if args.run:
        print("  Starting pipeline...")
        import subprocess
        upload = args.upload or args.schedule is not None
        subprocess.run([
            sys.executable,
            "run_story.py",
            "--config",
            str(output_path),
            "--output-dir",
            str(output_dir),
            *(
                ["--upload"] if upload else []
            ),
            *(
                ["--schedule", str(args.schedule)]
                if args.schedule is not None
                else []
            ),
        ])
