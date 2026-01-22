"""Generate environment-only scenes (no characters) to use as backgrounds."""
from pathlib import Path
from src.config import load_config
from src.models import Scene, ImageFormat
from src.queue_manager import QueueManager

config = load_config()
manager = QueueManager(config)
manager.load_state()

# Environment-only scenes (NO characters)
print("\n=== GENERATING ENVIRONMENT BACKGROUNDS ===")

environments = [
    Scene(
        scene_id=320,  # Garden environment
        environment_id="kitchen_01",  # Start with kitchen
        character_ids=[],  # NO CHARACTERS - just environment!
        prompt="""A beautiful sunlit garden with colorful flowers blooming in vibrant reds, yellows, and purples; lush green trees providing dappled shade; a winding garden path made of stone; peaceful serene outdoor sanctuary; blue sky with soft white clouds; Ghibli-inspired storybook illustration, vibrant natural colors, detailed background art.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
    Scene(
        scene_id=321,  # Street environment
        environment_id="kitchen_01",
        character_ids=[],  # NO CHARACTERS
        prompt="""A quiet suburban neighborhood street with small charming houses; tree-lined sidewalk with autumn leaves; warm afternoon sunlight; peaceful residential setting; houses with white picket fences and manicured lawns; Ghibli-inspired storybook illustration, detailed background art.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
    Scene(
        scene_id=322,  # Playground environment
        environment_id="kitchen_01",
        character_ids=[],  # NO CHARACTERS
        prompt="""A charming children's playground with colorful equipment; swings, slide, and sandbox; soft green grass surrounding; bright sunny day with fluffy clouds; whimsical and joyful atmosphere; Ghibli-inspired storybook illustration, vibrant playful colors.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
]

for scene in environments:
    manager.add_scene(scene, batches=1)

print("\n[OK] Queued 3 environment-only scenes")
print("After generation:")
print("  scene 320 → garden_01.png")
print("  scene 321 → street_01.png")
print("  scene 322 → playground_01.png")
print("\nThen run: run.bat process")
