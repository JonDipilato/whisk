"""Queue playground scenes (final chapter) for progressive storyline."""
from pathlib import Path
from src.config import load_config
from src.models import Scene, ImageFormat
from src.queue_manager import QueueManager

config = load_config()
manager = QueueManager(config)
manager.load_state()

characters = ["narrator_01", "grandmother_01"]

print("\n=== BATCH 4: PLAYGROUND SCENES (FINAL CHAPTER) ===")

batch4 = [
    Scene(
        scene_id=312,
        environment_id="playground_01",  # Playground environment (already generated)
        character_ids=characters,
        prompt="""The narrator and grandmother arriving at a charming playground; colorful swings and slide visible; excitement and joy on their faces; bright sunny day; Ghibli-inspired storybook illustration, vibrant playful colors.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
    Scene(
        scene_id=313,
        environment_id="playground_01",
        character_ids=characters,
        prompt="""Grandmother pushing the narrator on a swing; laughter and happiness; gentle loving moment; playground background with colorful equipment; Ghibli-inspired storybook illustration, warm joyful tones.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
    Scene(
        scene_id=314,
        environment_id="playground_01",
        character_ids=characters,
        prompt="""The narrator and grandmother sitting together on a bench near the playground; peaceful moment watching children play; warm golden hour light; sense of contentment and cherished memory; Ghibli-inspired storybook illustration, soft gentle hues.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
]

for scene in batch4:
    manager.add_scene(scene, batches=1)

print("\n[OK] Queued 3 playground scenes")
print("Run: run.bat process")
print("\nFinal storyline: 12 scenes = 72 seconds (1:12 of video)")
