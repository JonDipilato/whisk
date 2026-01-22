"""Test scene with 2 characters: Narrator and Grandmother in kitchen."""
from pathlib import Path
from src.config import load_config
from src.models import Scene, ImageFormat
from src.queue_manager import QueueManager

config = load_config()
manager = QueueManager(config)
manager.load_state()

# Scene: Narrator and Grandmother together in the kitchen
scene = Scene(
    scene_id=302,
    environment_id="kitchen_01",
    character_ids=["narrator_01", "grandmother_01"],  # Both characters!
    prompt="""The narrator and grandmother stand together at the kitchen table; grandmother lovingly teaches her to prepare tea, hands gently guiding; warm afternoon sunlight streaming through the window; dust motes floating; intimate tender moment between generations; Ghibli-inspired animated storybook illustration, soft hand-painted digital artwork, clean gentle linework, warm natural hues.""",
    image_format=ImageFormat.LANDSCAPE,
)

manager.add_scene(scene, batches=1)
print("Two-character scene added: Narrator + Grandmother in Kitchen!")
