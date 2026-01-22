"""Test scene with all 3 characters - v5 create slots first then upload."""
from pathlib import Path
from src.config import load_config
from src.models import Scene, ImageFormat
from src.queue_manager import QueueManager

config = load_config()
manager = QueueManager(config)
manager.load_state()

scene = Scene(
    scene_id=307,
    environment_id="kitchen_01",
    character_ids=["narrator_01", "grandmother_01", "miso_01"],
    prompt="""The narrator and grandmother sit at the kitchen table sharing tea; Miso the cat lounges contentedly on the warm wooden surface nearby; soft afternoon sunlight streaming through fluttering curtains; peaceful quiet family moment; bowl of lemons on table; Ghibli-inspired animated storybook illustration, soft hand-painted digital artwork, clean gentle linework, warm natural hues.""",
    image_format=ImageFormat.LANDSCAPE,
)

manager.add_scene(scene, batches=1)
print("Three-character scene v5 added (create slots first)!")
