"""Prepare storyline scenes for video generation - scan images and create prompts."""
from pathlib import Path
import json

def scan_generated_scenes(output_dir: Path = Path("output")) -> dict:
    """Scan all generated scene images and create storyline config."""
    scenes = {}

    # Find all scene batch folders
    scene_folders = sorted(output_dir.glob("scene_*_batch_1"))

    for folder in scene_folders:
        # Extract scene ID from folder name
        scene_id = folder.name.split("_")[1]

        # Find the best/most recent image in this folder
        images = sorted(folder.glob("scene_*.png"), key=lambda p: p.stat().st_mtime, reverse=True)

        if images:
            scenes[scene_id] = {
                "image_path": str(images[0]),  # Use most recent image
                "motion_prompt": ""  # To be filled in
            }

    return scenes


def generate_motion_prompts(scenes: dict) -> dict:
    """Generate motion prompts for each scene based on storyline context."""

    # Example motion prompts - customize these for your story!
    prompt_templates = {
        # Kitchen scenes
        "301": "Camera slowly zooms in slightly on narrator and grandmother sharing tea, warm afternoon light shifts through curtains, intimate peaceful moment",
        "302": "Camera follows grandmother's gentle hand movement as she pours tea, steam rises gracefully from cups, tender nurturing moment",
        "303": "Camera pans left to right as both stand up from table, natural smooth movement toward door, anticipation of outdoor adventure",

        # Garden scenes
        "304": "Camera slowly pulls back to reveal colorful garden surrounding them, gentle breeze makes flowers sway, peaceful outdoor serenity",
        "305": "Camera tracks grandmother bending down to show flower, narrator follows with curiosity, warm connection between generations",
        "306": "Camera tracks from side as they stroll along garden path, trees provide dappled shade, leisurely contemplative pace",

        # Street scenes
        "307": "Camera follows from behind as they walk onto quiet street, suburban houses pass by, neighborhood exploration feeling",
        "308": "Camera circles around grandmother pointing out interesting sights, narrator looks with wonder, shared discovery moment",
        "309": "Camera slowly pulls back as they continue walking into golden hour distance, journey continuing, warm sunset glow",

        # Transition scenes
        "310": "Camera reveals beautiful sunlit garden with colorful flowers and trees, blue sky overhead, sense of peaceful outdoor sanctuary",
        "311": "Camera shows garden gate opening to neighborhood street, new territory visible ahead, sense of adventure beginning",
    }

    for scene_id, scene_data in scenes.items():
        if scene_id in prompt_templates:
            scene_data["motion_prompt"] = prompt_templates[scene_id]
        else:
            # Default prompt for scenes not in template
            scene_data["motion_prompt"] = f"Gentle camera movement showing scene {scene_id}, peaceful storytelling moment"

    return scenes


def save_storyline_config(storyline: dict, output_path: Path = Path("storyline_config.json")):
    """Save storyline configuration to JSON file."""
    with open(output_path, "w") as f:
        json.dump(storyline, f, indent=2)
    print(f"Storyline config saved: {output_path}")


if __name__ == "__main__":
    print("Scanning generated scenes...")
    scenes = scan_generated_scenes()

    print(f"\nFound {len(scenes)} scenes:")
    for scene_id in sorted(scenes.keys()):
        print(f"  Scene {scene_id}: {Path(scenes[scene_id]['image_path']).name}")

    print("\nGenerating motion prompts...")
    storyline = generate_motion_prompts(scenes)

    print("\nMotion prompts:")
    for scene_id in sorted(storyline.keys()):
        print(f"\n  Scene {scene_id}:")
        print(f"    Image: {storyline[scene_id]['image_path']}")
        print(f"    Motion: {storyline[scene_id]['motion_prompt']}")

    save_storyline_config(storyline)

    print("\n" + "="*60)
    print("Next steps:")
    print("1. Review storyline_config.json")
    print("2. Customize motion prompts as needed")
    print("3. Run: python video_automation.py")
    print("   (This will use Grok Imagine to generate 6-second videos)")
    print("\nEstimated total video length: {} seconds ({} scenes × 6s)".format(
        len(scenes) * 6, len(scenes)
    ))
