"""Generate storyline videos using Grok's Imagine feature, then stitch together."""
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

class GrokVideoGenerator:
    """Automate Grok Imagine to generate 6-second videos from scene images."""

    GROK_URL = "https://grok.x.ai"  # Or whatever the actual URL is

    def __init__(self, user_data_dir: str = None):
        self.driver = None

        # Configure Chrome options
        options = Options()

        if user_data_dir:
            options.add_argument(f"--user-data-dir={user_data_dir}")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")

        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        self.options = options

    def start(self):
        """Start browser and navigate to Grok."""
        print("Starting browser for Grok Imagine...")
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.get(self.GROK_URL)
        time.sleep(5)
        print("Connected to Grok!")

    def stop(self):
        """Close browser."""
        if self.driver:
            self.driver.quit()
            print("Browser closed.")

    def generate_video_from_image(self, image_path: Path, motion_prompt: str, output_folder: Path):
        """
        Generate a 6-second video from an image using Grok Imagine.

        Args:
            image_path: Path to the scene image
            motion_prompt: Description of the motion/action (e.g., "camera slowly pans right as characters walk toward garden")
            output_folder: Where to save the generated video
        """
        print(f"\nGenerating video for: {image_path.name}")
        print(f"Motion prompt: {motion_prompt}")

        try:
            # TODO: Implement the actual automation steps:
            # 1. Find the Imagine/video generation interface
            # 2. Upload the image
            # 3. Enter the motion prompt
            # 4. Click generate
            # 5. Wait for generation (6-second video)
            # 6. Download the video

            # This will require inspecting Grok's web interface
            # and adding the specific selectors

            print("Video generation started...")
            time.sleep(10)  # Wait for generation
            print(f"Video saved to: {output_folder}")

            return True

        except Exception as e:
            print(f"Error generating video: {e}")
            return False

    def process_storyline(self, scenes_config: dict, output_folder: Path):
        """
        Process entire storyline: generate videos for all scenes, then combine.

        Args:
            scenes_config: Dictionary mapping scene_id to {image_path, motion_prompt}
            output_folder: Where to save final video and individual clips
        """
        output_folder.mkdir(parents=True, exist_ok=True)
        video_clips = []

        for scene_id, scene_data in scenes_config.items():
            image_path = Path(scene_data["image_path"])
            motion_prompt = scene_data["motion_prompt"]

            # Generate video for this scene
            video_path = output_folder / f"scene_{scene_id}_video.mp4"

            success = self.generate_video_from_image(
                image_path=image_path,
                motion_prompt=motion_prompt,
                output_folder=output_folder
            )

            if success:
                video_clips.append(video_path)

        # Stitch all videos together
        if video_clips:
            self.stitch_videos(video_clips, output_folder / "full_storyline.mp4")

    def stitch_videos(self, clip_paths: list[Path], output_path: Path):
        """
        Use FFmpeg to stitch video clips together.

        Args:
            clip_paths: List of video clip paths (in order)
            output_path: Final output video path
        """
        print(f"\nStitching {len(clip_paths)} clips into full video...")

        # Create file list for FFmpeg
        list_file = Path("video_list.txt")
        with open(list_file, "w") as f:
            for clip in clip_paths:
                f.write(f"file '{clip.absolute()}'\n")

        # FFmpeg command to concatenate
        import subprocess
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(output_path)
        ]

        try:
            subprocess.run(cmd, check=True)
            print(f"Full video saved: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error stitching videos: {e}")
        finally:
            list_file.unlink()


# Example usage configuration
EXAMPLE_STORYLINE = {
    301: {
        "image_path": "output/scene_301_batch_1/scene_301_xxx_1.png",
        "motion_prompt": "Gentle camera slowly zooms in on narrator and grandmother at kitchen table, warm light shifts through curtains"
    },
    302: {
        "image_path": "output/scene_302_batch_1/scene_302_xxx_1.png",
        "motion_prompt": "Camera follows grandmother's hand as she pours tea, steam rises gracefully, warm intimate feel"
    },
    303: {
        "image_path": "output/scene_303_batch_1/scene_303_xxx_1.png",
        "motion_prompt": "Camera pans left as both stand up, natural movement toward the back door, sense of transition"
    },
    # Add more scenes...
}


if __name__ == "__main__":
    print("Grok Video Generator")
    print("=" * 50)
    print("\nNOTE: This script needs Grok's web interface to be inspected first.")
    print("Once you have Grok open in browser, we can add the specific selectors.")
    print("\nSteps:")
    print("1. Open Grok in browser with Chrome DevTools")
    print("2. Go to the Imagine/video feature")
    print("3. Inspect elements for: upload button, prompt input, generate button")
    print("4. Update the generate_video_from_image() method with correct selectors")
    print("\nThen run: python video_automation.py")
