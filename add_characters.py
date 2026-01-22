"""Add character reference scenes to the queue."""
from pathlib import Path
from src.config import load_config
from src.models import Scene, ImageFormat
from src.queue_manager import QueueManager

config = load_config()
manager = QueueManager(config)
manager.load_state()

characters = [
    {
        "id": 101,
        "name": "narrator",
        "prompt": """Full-body character reference of the narrator: a gentle young adult (mid-20s), slim build, average height, warm light-olive skin, soft oval face, calm thoughtful eyes, short wavy dark-brown hair slightly tousled, faint freckles across the nose; wearing a cozy cream knit sweater with slightly loose sleeves, high-waisted muted-brown relaxed trousers, simple socks, indoor house slippers; neutral relaxed posture with arms resting at sides, serene expression; minimal plain background in creamy off-white with a faint warm gradient; Ghibli-inspired animated storybook illustration, soft hand-painted digital artwork, clean gentle linework, warm natural hues, subtle brush texture, eye-level view."""
    },
    {
        "id": 102,
        "name": "grandmother",
        "prompt": """Full-body character reference of Grandmother: elderly woman (late 70s), petite and sturdy, warm rosy-beige skin, gentle wrinkles, kind crescent-shaped eyes, soft smile; gray hair gathered loosely at the nape with a few wisps framing her face; wearing a faded sky-blue long-sleeve dress and a well-worn beige apron with tiny embroidered flowers along the hem, simple house shoes; calm upright posture with hands loosely folded, affectionate steady presence; minimal plain background in creamy off-white with warm gradient; Ghibli-inspired animated storybook illustration, soft hand-painted digital artwork, clean gentle linework, warm natural hues, subtle brush texture, eye-level view."""
    },
    {
        "id": 103,
        "name": "miso_cat",
        "prompt": """Full-body character reference of Miso the cat: medium-sized domestic cat with plush fur the color of toasted bread (warm tan with slightly darker stripes), round cheeks, sleepy half-lidded amber eyes, small pink nose, thick tail with darker tip; seated in a composed loaf posture, calm and dignified; minimal plain background in creamy off-white with warm gradient; Ghibli-inspired animated storybook illustration, soft hand-painted digital artwork, clean gentle linework, warm natural hues, subtle brush texture, eye-level view."""
    }
]

for char in characters:
    scene = Scene(
        scene_id=char["id"],
        environment_id="",  # No environment for character refs
        character_ids=[],   # No character refs needed
        prompt=char["prompt"],
        image_format=ImageFormat.PORTRAIT,  # Portrait for character refs
    )
    manager.add_scene(scene, batches=1)
    print(f"Added: {char['name']} (scene {char['id']})")

print("\n3 character references added to queue!")
