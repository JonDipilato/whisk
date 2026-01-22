"""Queue Ghibli-style scenes from Excel prompts file."""
import pandas as pd
from pathlib import Path
from src.config import load_config
from src.models import Scene, ImageFormat
from src.queue_manager import QueueManager

# Load Excel file
excel_path = Path("/mnt/c/Users/jon-d/Desktop/MISC/story_prompts_grouped_with_blank_lines_and_suffix.xlsx")

# Read and filter valid rows (skip NaN prompts)
df = pd.read_excel(excel_path)
df = df.dropna(subset=['prompt'])

print(f"\n=== Ghibli Kitchen Scenes ===")
print(f"Found {len(df)} prompts in Excel file\n")

# Map codes to your asset IDs
character_map = {0.0: "narrator_01"}
environment_map = {2.0: "kitchen_01"}

config = load_config()
manager = QueueManager(config)
manager.load_state()

# Create scenes from Excel
scenes_created = 0
for idx, row in df.iterrows():
    scene_num = int(row['image']) if pd.notna(row['image']) else idx
    char_code = row['character_code']
    env_code = row['environment_code']
    prompt = row['prompt']

    # Clean prompt - remove the suffix part that's for video/audio
    # Keep only the visual description
    if "No background music" in prompt:
        prompt = prompt.split("No background music")[0].strip().rstrip('.,;')

    # Map codes to asset IDs
    char_id = character_map.get(char_code, "narrator_01")
    env_id = environment_map.get(env_code, "kitchen_01")

    scene = Scene(
        scene_id=scene_num + 1000,  # Offset to avoid conflicts with existing scenes
        environment_id=env_id,
        character_ids=[char_id] if pd.notna(char_code) else [],
        prompt=prompt,
        image_format=ImageFormat.LANDSCAPE,
    )

    manager.add_scene(scene, batches=1)
    scenes_created += 1
    print(f"[OK] Scene {scene_num + 1000}: {prompt[:60]}...")

print(f"\n[OK] Queued {scenes_created} Ghibli kitchen scenes")
print("Run: python run.py process")
