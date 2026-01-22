"""Organize generated scenes into location-based folders for easy access."""
from pathlib import Path
import shutil

def organize_scenes_by_location():
    """Move/copy scenes into location folders (kitchen, garden, street, playground)."""

    output_dir = Path("output")

    # Scene ID ranges for each location
    locations = {
        "kitchen": list(range(301, 304)),      # 301-303
        "garden": list(range(304, 307)),        # 304-306
        "street": list(range(307, 310)),        # 307-309
        "playground": [312, 313, 314],         # 312-314
        "transitions": [310, 311],               # Garden transitions
        "environments": [200, 320, 321, 322],   # Environment-only scenes
    }

    print("Organizing scenes by location...\n")

    for location, scene_ids in locations.items():
        # Create location folder
        loc_folder = output_dir / location
        loc_folder.mkdir(parents=True, exist_ok=True)

        print(f"Location: {location}")

        # Find and copy scenes
        for scene_id in scene_ids:
            # Find the scene folder
            scene_folders = list(output_dir.glob(f"scene_{scene_id}_batch_*"))

            for scene_folder in scene_folders:
                # Copy all images from this scene folder to location folder
                images = list(scene_folder.glob("*.png"))

                for img in images:
                    dest = loc_folder / img.name
                    shutil.copy2(img, dest)
                    print(f"  Copied: {img.name}")

        print(f"  Total in {location}/: {len(list(loc_folder.glob('*.png')))} images\n")

    # Create a summary
    print("\n" + "="*60)
    print("ORGANIZATION COMPLETE!")
    print("="*60)
    print("\nScene locations:")
    for location in locations.keys():
        loc_folder = output_dir / location
        count = len(list(loc_folder.glob("*.png")))
        print(f"  output/{location}/ - {count} images")

    print("\nYou can now easily find scenes by location!")
    print("\nExample:")
    print("  Kitchen scenes: output/kitchen/")
    print("  Garden scenes: output/garden/")
    print("  Street scenes: output/street/")
    print("  Playground scenes: output/playground/")


if __name__ == "__main__":
    organize_scenes_by_location()
