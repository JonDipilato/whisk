"""Prepare next batch using a generated scene as the new environment."""
import shutil
from pathlib import Path
import sys

# Copy a generated scene to use as the environment for the next batch
# Usage: py prepare_next_batch.py <source_scene_image> <new_environment_name>

if len(sys.argv) < 3:
    print("Usage: py prepare_next_batch.py <source_image_path> <new_env_name>")
    print("Example: py prepare_next_batch.py output/scene_301_batch_1/scene_301_xxx_1.png kitchen_02")
    sys.exit(1)

source_path = Path(sys.argv[1])
env_name = sys.argv[2]
env_dir = Path("data/environments")

if not source_path.exists():
    print(f"❌ Source image not found: {source_path}")
    sys.exit(1)

# Copy to environments folder
dest_path = env_dir / f"{env_name}.png"
dest_path.parent.mkdir(parents=True, exist_ok=True)

shutil.copy(source_path, dest_path)
print(f"✅ Copied {source_path.name} → {env_name}.png")
print(f"📂 Environment ready: data/environments/{env_name}.png")
print(f"\nNow update your test file to use environment_id='{env_name}'")
