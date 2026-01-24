#!/usr/bin/env python3
"""Create a complete 75-scene bedtime story queue."""

import sys
from pathlib import Path
sys.path.append('/mnt/c/Users/jon-d/whisk-automation/whisk')

from rich.console import Console
from src.queue_manager import QueueManager
from src.config import load_config
from src.models import Scene, ImageFormat

console = Console()

# Complete 75-scene story: "Grandmother's Magical Garden Adventure"
# Each scene is 4 seconds = 300 seconds (5 minutes)

STORY_SCENES = [
    # ACT 1: Introduction (Scenes 1-15) - Setting the scene
    {"scene_id": 1, "env": "env_room", "chars": ["grandmother_01"], "prompt": "Cozy bedroom at sunset, warm golden light through window, grandmother sitting in rocking chair, Studio Ghibli style, peaceful atmosphere"},
    {"scene_id": 2, "env": "env_room", "chars": ["grandmother_01"], "prompt": "Grandmother opens a storybook, magical sparkles floating from pages, Studio Ghibli style, whimsical"},
    {"scene_id": 3, "env": "env_room", "chars": ["grandmother_01"], "prompt": "Close-up of grandmother's kind face, gentle smile, wrinkles showing wisdom, Studio Ghibli style, warm lighting"},
    {"scene_id": 4, "env": "garden_01", "chars": [], "prompt": "Magical garden at twilight, glowing flowers, fireflies beginning to appear, Studio Ghibli style, enchanting"},
    {"scene_id": 5, "env": "garden_01", "chars": ["grandmother_01"], "prompt": "Grandmother standing at garden gate, white flowing dress, silver hair glowing in moonlight, Studio Ghibli style"},
    {"scene_id": 6, "env": "garden_01", "chars": [], "prompt": "Garden path lined with luminescent mushrooms, soft blue glow, Studio Ghibli style, magical forest atmosphere"},
    {"scene_id": 7, "env": "garden_01", "chars": ["miso_01"], "prompt": "Tiny curious creature peaking from behind a mushroom, miso the forest spirit, Studio Ghibli style, adorable"},
    {"scene_id": 8, "env": "garden_01", "chars": ["grandmother_01", "miso_01"], "prompt": "Grandmother notices the tiny creature, gentle greeting moment, Studio Ghibli style, heartwarming"},
    {"scene_id": 9, "env": "garden_01", "chars": ["miso_01"], "prompt": "Miso the forest spirit leading the way deeper into the magical garden, Studio Ghibli style, adventurous"},
    {"scene_id": 10, "env": "garden_01", "chars": [], "prompt": "Enormous glowing flowers opening their petals as night falls, Studio Ghibli style, bioluminescent beauty"},
    {"scene_id": 11, "env": "garden_01", "chars": ["cats"], "prompt": "Magical cat with star-patterned fur sleeping on a large mushroom, Studio Ghibli style, peaceful"},
    {"scene_id": 12, "env": "garden_01", "chars": ["grandmother_01"], "prompt": "Grandmother gently petting the star-cat, creature purring with sparkles, Studio Ghibli style, heartwarming"},
    {"scene_id": 13, "env": "env_forest", "chars": [], "prompt": "Path leading from garden into enchanted forest, trees with glowing leaves, Studio Ghibli style, mystical"},
    {"scene_id": 14, "env": "env_forest", "chars": ["grandmother_01", "miso_01"], "prompt": "Grandmother and miso walking into the forest, hand in tiny hand, Studio Ghibli style, tender moment"},
    {"scene_id": 15, "env": "env_forest", "chars": [], "prompt": "Forest canopy with stars visible through magical glowing branches, Studio Ghibli style, dreamlike"},

    # ACT 2: The Forest Journey (Scenes 16-30) - Meeting friends
    {"scene_id": 16, "env": "env_forest", "chars": [], "prompt": "Ancient tree with friendly face in bark, eyes opening with warm light, Studio Ghibli style, magical being"},
    {"scene_id": 17, "env": "env_forest", "chars": ["grandmother_01"], "prompt": "Grandmother speaking to the ancient tree, wisdom exchanged, Studio Ghibli style, reverent"},
    {"scene_id": 18, "env": "env_forest", "chars": ["char_girl"], "prompt": "Lost forest spirit girl appearing from behind tree, shy and curious, Studio Ghibli style, innocent"},
    {"scene_id": 19, "env": "env_forest", "chars": ["grandmother_01", "char_girl"], "prompt": "Grandmother comforting the lost spirit girl, motherly embrace, Studio Ghibli style, emotional"},
    {"scene_id": 20, "env": "env_forest", "chars": ["char_girl", "miso_01"], "prompt": "Spirit girl and miso playing together, magical laughter, Studio Ghibli style, joyful"},
    {"scene_id": 21, "env": "env_forest", "chars": [], "prompt": "Forest clearing with pond reflecting moonlight, lotus flowers blooming, Studio Ghibli style, serene"},
    {"scene_id": 22, "env": "env_forest", "chars": ["cats"], "prompt": "Multiple magical cats gathering around the pond, drinking starlight water, Studio Ghibli style, ethereal"},
    {"scene_id": 23, "env": "env_forest", "chars": ["grandmother_01"], "prompt": "Grandmother scattering magic seeds, flowers instantly blooming, Studio Ghibli style, creation moment"},
    {"scene_id": 24, "env": "env_forest", "chars": [], "prompt": "Butterflies made of pure light emerging from flowers, Studio Ghibli style, magical transformation"},
    {"scene_id": 25, "env": "env_forest", "chars": ["miso_01", "char_girl"], "prompt": "Children chasing light butterflies, laughter filling the forest, Studio Ghibli style, pure joy"},
    {"scene_id": 26, "env": "env_forest", "chars": ["grandmother_01"], "prompt": "Grandmother watching children play, nostalgic smile, remembering her own childhood, Studio Ghibli style, bittersweet"},
    {"scene_id": 27, "env": "env_forest", "chars": [], "prompt": "Fireflies creating magical pathways through the forest, Studio Ghibli style, illumination"},
    {"scene_id": 28, "env": "env_forest", "chars": ["cats"], "prompt": "Cats frolicking in firefly light, pouncing on sparks playfully, Studio Ghibli style, adorable"},
    {"scene_id": 29, "env": "env_forest", "chars": ["grandmother_01", "char_girl"], "prompt": "Spirit girl whispering secret to grandmother, Studio Ghibli style, intimate moment"},
    {"scene_id": 30, "env": "env_forest", "chars": [], "prompt": "Forest revealing hidden pathway of moonbeams, Studio Ghibli style, magical discovery"},

    # ACT 3: The Moonlit Lake (Scenes 31-45) - Middle journey
    {"scene_id": 31, "env": "env_forest", "chars": ["grandmother_01", "miso_01", "char_girl"], "prompt": "Group following moonbeam path together, Studio Ghibli style, journey continuing"},
    {"scene_id": 32, "env": "garden_01", "chars": [], "prompt": "Hidden lake revealed, water like liquid silver, stars perfectly reflected, Studio Ghibli style, mirror world"},
    {"scene_id": 33, "env": "garden_01", "chars": ["grandmother_01"], "prompt": "Grandmother at water's edge, reflection showing younger version of herself, Studio Ghibli style, memory"},
    {"scene_id": 34, "env": "garden_01", "chars": ["miso_01"], "prompt": "Miso skipping stones that create ripples of light, Studio Ghibli style, playful magic"},
    {"scene_id": 35, "env": "garden_01", "chars": ["char_girl"], "prompt": "Spirit girl dancing on water's surface, graceful as moonlight, Studio Ghibli style, ethereal beauty"},
    {"scene_id": 36, "env": "garden_01", "chars": ["cats"], "prompt": "Star-cat watching from shore, eyes wide with wonder, Studio Ghibli style, adorable"},
    {"scene_id": 37, "env": "garden_01", "chars": [], "prompt": "Water lilies glowing and blooming in response to music, Studio Ghibli style, synesthetic magic"},
    {"scene_id": 38, "env": "garden_01", "chars": ["grandmother_01"], "prompt": "Grandmother singing to the lake, water vibrating with harmonious light, Studio Ghibli style, sound visualization"},
    {"scene_id": 39, "env": "garden_01", "chars": [], "prompt": "Musical notes taking form as glowing fish swimming below surface, Studio Ghibli style, magical realism"},
    {"scene_id": 40, "env": "garden_01", "chars": ["miso_01", "char_girl"], "prompt": "Children trying to catch the note-fishes with bare hands, giggling, Studio Ghibli style, innocent play"},
    {"scene_id": 41, "env": "garden_01", "chars": ["cats"], "prompt": "Cats chasing note-fishes excitedly, splashing playfully, Studio Ghibli style, energetic joy"},
    {"scene_id": 42, "env": "garden_01", "chars": ["grandmother_01"], "prompt": "Grandmother laughing at the playful chaos, pure happiness, Studio Ghibli style, infectious joy"},
    {"scene_id": 43, "env": "garden_01", "chars": [], "prompt": "Lotus flowers opening to reveal tiny sleeping fairies inside, Studio Ghibli style, magical revelation"},
    {"scene_id": 44, "env": "garden_01", "chars": ["miso_01"], "prompt": "Miso gently poking a lotus flower, fairy waking up with stretch and yawn, Studio Ghibli style, cute"},
    {"scene_id": 45, "env": "garden_01", "chars": ["grandmother_01", "miso_01", "char_girl"], "prompt": "Fairies joining the group, tiny lights adding to the magical gathering, Studio Ghibli style, wondrous"},

    # ACT 4: The Star Festival (Scenes 46-60) - Climax
    {"scene_id": 46, "env": "env_forest", "chars": [], "prompt": "Forest clearing transforming into festival ground, lanterns appearing, Studio Ghibli style, magical festival"},
    {"scene_id": 47, "env": "env_forest", "chars": ["grandmother_01"], "prompt": "Grandmother greeted by forest spirits as honored guest, Studio Ghibli style, heartwarming welcome"},
    {"scene_id": 48, "env": "env_forest", "chars": ["miso_01", "char_girl"], "prompt": "Children running to festival games, pure excitement, Studio Ghibli style, childhood joy"},
    {"scene_id": 49, "env": "env_forest", "chars": ["cats"], "prompt": "Cats chasing magical lanterns that float just out of reach, Studio Ghibli style, playful chase"},
    {"scene_id": 50, "env": "env_forest", "chars": [], "prompt": "Food tables appearing with magical glowing treats, Studio Ghibli style, feast appearance"},
    {"scene_id": 51, "env": "env_forest", "chars": ["grandmother_01"], "prompt": "Grandmother served by ancient tree spirit, exchange of gifts, Studio Ghibli style, honor and respect"},
    {"scene_id": 52, "env": "env_forest", "chars": ["miso_01"], "prompt": "Miso eating star-shaped cookie, crumbs turning into butterflies, Studio Ghibli style, magical eating"},
    {"scene_id": 53, "env": "env_forest", "chars": ["char_girl"], "prompt": "Spirit girl receiving moonflower crown, becoming festival princess, Studio Ghibli style, coronation moment"},
    {"scene_id": 54, "env": "env_forest", "chars": ["cats"], "prompt": "Cats wearing tiny festival hats, looking dignified and adorable, Studio Ghibli style, cute formal"},
    {"scene_id": 55, "env": "env_forest", "chars": [], "prompt": "Music beginning, instruments made of crystal and starlight, Studio Ghibli style, magical orchestra"},
    {"scene_id": 56, "env": "env_forest", "chars": ["grandmother_01", "miso_01", "char_girl"], "prompt": "Everyone dancing, grandmother teaching traditional steps, Studio Ghibli style, dance celebration"},
    {"scene_id": 57, "env": "env_forest", "chars": [], "prompt": "Fireflies creating light show synchronized to music, Studio Ghibli style, natural fireworks"},
    {"scene_id": 58, "env": "env_forest", "chars": ["cats"], "prompt": "Cats attempting to dance, clumsy but enthusiastic, Studio Ghibli style, adorable chaos"},
    {"scene_id": 59, "env": "env_forest", "chars": ["grandmother_01"], "prompt": "Grandmother receiving gift of woven starlight shawl from forest, Studio Ghibli style, precious gift"},
    {"scene_id": 60, "env": "env_forest", "chars": [], "prompt": "Festival reaching peak, entire forest glowing with celebration, Studio Ghibli style, magical climax"},

    # ACT 5: Return and Bedtime (Scenes 61-75) - Resolution
    {"scene_id": 61, "env": "env_forest", "chars": ["grandmother_01"], "prompt": "Grandmother saying gentle goodbyes, promises to return, Studio Ghibli style, tender farewell"},
    {"scene_id": 62, "env": "env_forest", "chars": ["char_girl"], "prompt": "Spirit girl giving grandmother parting gift, glowing moonflower, Studio Ghibli style, meaningful exchange"},
    {"scene_id": 63, "env": "env_forest", "chars": ["miso_01"], "prompt": "Miso promising to guard the forest until next time, Studio Ghibli style, loyal friend"},
    {"scene_id": 64, "env": "env_forest", "chars": ["cats"], "prompt": "Star-cat rubbing against grandmother's leg one last time, Studio Ghibli style, affectionate goodbye"},
    {"scene_id": 65, "env": "garden_01", "chars": ["grandmother_01"], "prompt": "Grandmother walking back through garden at peace, Studio Ghibli style, serene return"},
    {"scene_id": 66, "env": "garden_01", "chars": [], "prompt": "Garden flowers closing gently for night, Studio Ghibli style, natural cycle"},
    {"scene_id": 67, "env": "env_room", "chars": ["grandmother_01"], "prompt": "Grandmother entering her cozy bedroom, warmth and safety, Studio Ghibli style, home comfort"},
    {"scene_id": 68, "env": "env_room", "chars": ["grandmother_01"], "prompt": "Grandmother placing moonflower in vase, glow illuminating room, Studio Ghibli style, magical keepsake"},
    {"scene_id": 69, "env": "env_room", "chars": ["grandmother_01"], "prompt": "Grandmother writing in her journal about the adventure, Studio Ghibli style, memory preservation"},
    {"scene_id": 70, "env": "env_room", "chars": [], "prompt": "Room transforming to starry night sky inside, Studio Ghibli style, dreamlike bedroom"},
    {"scene_id": 71, "env": "env_room", "chars": ["cats"], "prompt": "Star-cat appearing on windowsill, watching over grandmother, Studio Ghibli style, guardian presence"},
    {"scene_id": 72, "env": "env_room", "chars": ["grandmother_01"], "prompt": "Grandmother climbing into bed, tired but happy, Studio Ghibli style, peaceful rest"},
    {"scene_id": 73, "env": "env_room", "chars": [], "prompt": "Room filling with gentle lullaby music visible as soft colors, Studio Ghibli style, synesthetic sleep"},
    {"scene_id": 74, "env": "env_room", "chars": ["grandmother_01", "cats"], "prompt": "Grandmother falling asleep, star-cat curling up nearby, Studio Ghibli style, cozy sleep"},
    {"scene_id": 75, "env": "env_room", "chars": [], "prompt": "Final shot: bedroom fading to starry night, crescent moon, Studio Ghibli style, peaceful ending"},
]

# Full narration script for the 5-minute video
FULL_NARRATION = """
Once upon a time, in a cozy little house at the edge of the world, there lived a kind grandmother with silver hair that shone like moonlight.

Every evening, as the sun began to set, she would open her beloved storybook, and magical things would happen.

On this particular night, the book led her to a secret magical garden, where flowers glowed with their own inner light.

In this garden lived a tiny forest spirit named Miso, who was curious and full of wonder.

Grandmother and Miso became fast friends, and together they discovered a path into the enchanted forest.

The forest was alive with magic. Ancient trees with friendly faces welcomed them.

They met a lost forest spirit girl who was shy and lonely. Grandmother's warm heart made her feel safe.

The children played together, chasing butterflies made of pure light.

Deep in the forest, they found a hidden lake where the water was like liquid silver, reflecting the stars perfectly.

At the lake, Grandmother sang a beautiful song, and musical notes became glowing fish swimming below the surface.

The children laughed and played, while a little star-cat watched with wide eyes of wonder.

Fairies bloomed from lotus flowers, adding their tiny lights to the magical gathering.

The forest spirits invited everyone to a special star festival under the moonlit sky.

There was music and dancing, magical food that turned into butterflies, and gifts exchanged between friends.

The forest glowed with celebration, fireflies painting the sky with their light.

But all magical adventures must come to their gentle end. Grandmother said her goodbyes with promises to return.

She walked back through her peaceful garden, now quiet for the night.

In her cozy bedroom, she placed a glowing moonflower on her bedside table.

As she climbed into bed, a star-cat appeared on her windowsill, watching over her.

And so, under a sky full of stars, grandmother drifted into peaceful dreams, her heart full of magical memories.

Goodnight, little one. Sweet dreams.
"""


def main():
    """Add all 75 scenes to the queue."""
    config = load_config()
    manager = QueueManager(config)
    manager.load_state()

    # Clear existing pending items for fresh start
    pending = manager.get_pending()
    if pending:
        console.print(f"[yellow]Clearing {len(pending)} old pending items...[/yellow]")
        for item in pending:
            manager.state.items.remove(item)
        manager.save_state()

    console.print(f"[bold cyan]Adding 75 scenes to queue...[/bold cyan]")

    for scene_data in STORY_SCENES:
        scene = Scene(
            scene_id=scene_data["scene_id"],
            environment_id=scene_data["env"],
            character_ids=scene_data.get("chars", []),
            prompt=scene_data["prompt"],
            image_format=ImageFormat.LANDSCAPE,
        )
        manager.add_scene(scene, batches=1)
        console.print(f"[green]Added Scene {scene_data['scene_id']}[/green]")

    manager.show_status()

    # Save narration to file
    narration_path = "data/full_narration.txt"
    Path("data").mkdir(exist_ok=True)
    with open(narration_path, "w") as f:
        f.write(FULL_NARRATION.strip())

    console.print(f"\n[green]Narration saved to: {narration_path}[/green]")
    console.print(f"[yellow]Next: Run 'python run.py process' to generate all images[/yellow]")


if __name__ == "__main__":
    main()
