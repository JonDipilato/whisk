"""Add a Ghibli scene to the queue."""
from pathlib import Path
from src.config import load_config
from src.models import Scene, ImageFormat
from src.queue_manager import QueueManager

config = load_config()
manager = QueueManager(config)
manager.load_state()

# Ghibli kitchen scene prompt
prompt = """Wide interior establishing scene of a rustic countryside kitchen in warm afternoon daylight: worn wooden table at center, pale fluttering curtain by a sunlit window, bowl of lemons glowing softly, pantry with a small ticking clock above it, simple stove with a quiet kettle; outside the window, a small garden with a pear tree gently moving in the breeze; atmosphere hushed and safe, dust motes floating in the sunbeam; Ghibli-inspired animated storybook illustration, soft hand-painted digital artwork, clean gentle linework, warm natural hues, dreamy daylight glow."""

scene = Scene(
    scene_id=4,
    environment_id="2",
    character_ids=[],
    prompt=prompt,
    image_format=ImageFormat.LANDSCAPE,
)

manager.add_scene(scene, batches=1)
print("Ghibli scene added to queue!")
