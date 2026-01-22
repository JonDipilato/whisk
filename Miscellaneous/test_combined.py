"""Test combining character + environment in Whisk."""
from pathlib import Path
from src.config import load_config
from src.models import Scene, ImageFormat
from src.queue_manager import QueueManager

config = load_config()
manager = QueueManager(config)
manager.load_state()

# Scene: Narrator in the kitchen
# Character ref goes to SUBJECT slot, Environment goes to SCENE slot
scene = Scene(
    scene_id=301,
    environment_id="kitchen_01",  # Kitchen environment in data/environments/
    character_ids=["narrator_01"],  # Narrator character in data/characters/
    prompt="""The narrator stands at the worn wooden table, gazing thoughtfully out the sunlit window; soft afternoon light catches the dust motes around her; calm serene expression, relaxed posture; Ghibli-inspired animated storybook illustration, soft hand-painted digital artwork, clean gentle linework, warm natural hues.""",
    image_format=ImageFormat.LANDSCAPE,
)

manager.add_scene(scene, batches=1)
print("Combined scene added: Narrator in Kitchen!")
