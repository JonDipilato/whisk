"""Progressive storyline test - each batch uses previous batch's scene as environment."""
from pathlib import Path
from src.config import load_config
from src.models import Scene, ImageFormat
from src.queue_manager import QueueManager

config = load_config()
manager = QueueManager(config)
manager.load_state()

# Storyline: Narrator and grandmother sharing moments together
characters = ["narrator_01", "grandmother_01"]  # 2 characters to stay within Whisk limit

# BATCH 1: Starting with the kitchen scene
print("\n=== BATCH 1: Kitchen Tea Time ===")
batch1_scenes = [
    Scene(
        scene_id=301,
        environment_id="kitchen_01",
        character_ids=characters,
        prompt="""The narrator and grandmother sit at the kitchen table sharing tea on a peaceful afternoon; soft sunlight streaming through curtains; intimate warm conversation; Ghibli-inspired storybook illustration, hand-painted digital art.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
    Scene(
        scene_id=302,
        environment_id="kitchen_01",
        character_ids=characters,
        prompt="""Grandmother pouring tea for the narrator at the kitchen table; steam rising from ceramic cups; gentle loving expression; cozy domestic moment; Ghibli-inspired storybook illustration, warm natural hues.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
    Scene(
        scene_id=303,
        environment_id="kitchen_01",
        character_ids=characters,
        prompt="""The narrator listening intently as grandmother tells stories by the kitchen window; afternoon light creating warm shadows; cherished family bonding time; Ghibli-inspired storybook illustration, soft gentle linework.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
]

for scene in batch1_scenes:
    manager.add_scene(scene, batches=1)

print("\n✅ Batch 1 queued (3 scenes)")
print("📝 After generation, pick the best image and update BATCH 2 environment_id below!")
print("📂 Images will be in: output/scene_30{1,2,3}_batch_1/")
