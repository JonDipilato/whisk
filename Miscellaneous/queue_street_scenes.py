"""Queue street scenes (Batch 3) for progressive storyline."""
from pathlib import Path
from src.config import load_config
from src.models import Scene, ImageFormat
from src.queue_manager import QueueManager

config = load_config()
manager = QueueManager(config)
manager.load_state()

characters = ["narrator_01", "grandmother_01"]

print("\n=== BATCH 3: STREET SCENES ===")

batch3 = [
    Scene(
        scene_id=307,
        environment_id="street_01",  # Street environment (already generated)
        character_ids=characters,
        prompt="""The narrator and grandmother walking together along a quiet suburban street; small charming houses with white picket fences lining the road; trees providing shade; peaceful neighborhood exploration; Ghibli-inspired storybook illustration.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
    Scene(
        scene_id=308,
        environment_id="street_01",
        character_ids=characters,
        prompt="""Grandmother pointing out interesting things along the street to the narrator; narrator looking with curiosity and wonder; shared discovery moment; warm connection between generations; Ghibli-inspired storybook illustration.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
    Scene(
        scene_id=309,
        environment_id="street_01",
        character_ids=characters,
        prompt="""The narrator and grandmother continuing their leisurely walk down the street; warm golden hour sunlight illuminating their path; journey continuing into the distance; peaceful sense of adventure; Ghibli-inspired storybook illustration.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
]

for scene in batch3:
    manager.add_scene(scene, batches=1)

print("\n[OK] Queued 3 street scenes")
print("Run: run.bat process")
