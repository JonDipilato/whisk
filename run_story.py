"""
=================================================================
  STORY VIDEO MAKER

  Creates an animated story video from a simple config file.

  HOW TO USE:
  1. Edit 'story_config.json' with your story details
  2. Run: python run_story.py
  3. Find your videos in the 'output/videos/' folder

  REQUIREMENTS:
  - Google Chrome installed
  - Python packages: selenium, edge-tts, rich
  - ffmpeg installed
  - Be logged into Google Whisk in Chrome
=================================================================
"""

import os
import sys
import json
import time
import shutil
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

if HAS_RICH:
    console = Console()
    def status(msg, style="cyan"):
        console.print(f"[{style}]{msg}[/{style}]")
    def error(msg):
        console.print(f"[bold red]ERROR: {msg}[/bold red]")
    def success(msg):
        console.print(f"[bold green]{msg}[/bold green]")
    def header(msg):
        console.print(Panel(f"[bold magenta]{msg}[/bold magenta]"))
else:
    def status(msg, style=None): print(f"  {msg}")
    def error(msg): print(f"  ERROR: {msg}")
    def success(msg): print(f"  OK: {msg}")
    def header(msg): print(f"\n{'='*60}\n  {msg}\n{'='*60}")


class StoryVideoMaker:
    def __init__(self, config_path="story_config.json"):
        self.root = Path(__file__).parent
        self.config_path = self.root / config_path
        self.config = self._load_config()
        self.output_dir = self.root / "output"
        self.chars_dir = self.root / "data" / "characters"
        self.envs_dir = self.root / "data" / "environments"
        self.audio_dir = self.output_dir / "audio"
        self.videos_dir = self.output_dir / "videos"

        # Create directories
        for d in [self.output_dir, self.chars_dir, self.envs_dir, self.audio_dir, self.videos_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        if not self.config_path.exists():
            error(f"Config file not found: {self.config_path}")
            error("Create a 'story_config.json' file. See the example template.")
            sys.exit(1)

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Validate required fields
        required = ["title", "characters", "scene", "scenes", "narration"]
        missing = [r for r in required if r not in config]
        if missing:
            error(f"Missing required fields in config: {', '.join(missing)}")
            sys.exit(1)

        if len(config["characters"]) == 0:
            error("At least one character is required")
            sys.exit(1)

        if len(config["scenes"]) == 0:
            error("At least one scene is required")
            sys.exit(1)

        return config

    def _get_settings(self, key, default=None):
        return self.config.get("settings", {}).get(key, default)

    # =========================================================================
    # STEP 1: Generate character & scene reference images via Whisk
    # =========================================================================
    def generate_references(self):
        header("STEP 1: Generating Reference Images via Whisk")

        from src.config import load_config
        from src.whisk_controller import WhiskController

        app_config = load_config()
        refs_needed = []

        # Check characters
        for char in self.config["characters"]:
            name = char["name"].lower().replace(" ", "_")
            filepath = self.chars_dir / f"{name}_01.png"
            if filepath.exists() and filepath.stat().st_size > 10000:
                status(f"Character '{char['name']}' already exists ({filepath.stat().st_size // 1024}KB)")
            else:
                refs_needed.append(("character", name, char["description"], filepath))

        # Check scene
        scene = self.config["scene"]
        scene_name = scene["name"].lower().replace(" ", "_")
        scene_path = self.envs_dir / f"{scene_name}.png"
        if scene_path.exists() and scene_path.stat().st_size > 10000:
            status(f"Scene '{scene['name']}' already exists ({scene_path.stat().st_size // 1024}KB)")
        else:
            refs_needed.append(("scene", scene_name, scene["description"], scene_path))

        if not refs_needed:
            success("All reference images already exist!")
            return True

        status(f"Need to generate {len(refs_needed)} reference(s)...")

        controller = WhiskController(app_config)
        for ref_type, ref_id, prompt, save_path in refs_needed:
            status(f"Generating {ref_type}: {ref_id}...")

            try:
                controller.start()
                time.sleep(3)

                controller.clear_inputs()
                time.sleep(2)
                controller.set_prompt(prompt)
                time.sleep(1)
                controller.generate()
                controller.wait_for_generation(timeout=90)

                temp_dir = self.output_dir / f"_ref_{ref_id}"
                temp_dir.mkdir(parents=True, exist_ok=True)
                downloaded = controller.download_images(temp_dir, prefix=f"ref_{ref_id}", crop=False)

                if downloaded:
                    best = max(downloaded, key=lambda p: p.stat().st_size)
                    shutil.copy2(best, save_path)
                    success(f"Saved: {save_path.name} ({save_path.stat().st_size // 1024}KB)")
                else:
                    error(f"Failed to generate {ref_id}. Try running again.")

            except Exception as e:
                error(f"Error generating {ref_id}: {e}")
            finally:
                controller.stop()
                time.sleep(2)

        return True

    # =========================================================================
    # STEP 2: Generate scene images using references
    # =========================================================================
    def generate_scenes(self):
        header(f"STEP 2: Generating {len(self.config['scenes'])} Scene Images")

        from src.config import load_config
        from src.whisk_controller import WhiskController

        app_config = load_config()
        style = self.config.get("style", "")
        scenes = self.config["scenes"]

        # Get character file paths
        char_files = []
        for char in self.config["characters"]:
            name = char["name"].lower().replace(" ", "_")
            filepath = self.chars_dir / f"{name}_01.png"
            if filepath.exists():
                char_files.append(filepath)
            else:
                error(f"Character reference missing: {filepath}")
                error("Run step 1 first (reference generation)")
                return False

        # Get scene file path
        scene = self.config["scene"]
        scene_name = scene["name"].lower().replace(" ", "_")
        scene_path = self.envs_dir / f"{scene_name}.png"
        if not scene_path.exists():
            error(f"Scene reference missing: {scene_path}")
            return False

        # Check which scenes already have images
        scenes_to_generate = []
        for i, scene_prompt in enumerate(scenes, 1):
            scene_dir = self.output_dir / f"scene_{i:03d}_batch_1"
            if scene_dir.exists():
                images = list(scene_dir.glob("*.png")) + list(scene_dir.glob("*.webp"))
                if images and max(img.stat().st_size for img in images) > 30000:
                    continue  # Already has good images
            scenes_to_generate.append((i, scene_prompt))

        if not scenes_to_generate:
            success("All scene images already generated!")
            return True

        status(f"{len(scenes_to_generate)} scenes need generation (skipping {len(scenes) - len(scenes_to_generate)} already done)")

        controller = WhiskController(app_config)

        for scene_idx, scene_prompt in scenes_to_generate:
            scene_dir = self.output_dir / f"scene_{scene_idx:03d}_batch_1"
            scene_dir.mkdir(parents=True, exist_ok=True)

            full_prompt = f"{scene_prompt}, {style}" if style else scene_prompt
            status(f"Scene {scene_idx}/{len(scenes)}: {scene_prompt[:60]}...")

            try:
                controller.start()
                time.sleep(3)

                # Upload references
                controller.upload_references(
                    character_paths=char_files,
                    environment_path=scene_path,
                )
                time.sleep(2)

                # Set prompt and generate
                controller.set_prompt(full_prompt)
                time.sleep(1)
                controller.generate()
                controller.wait_for_generation(timeout=60)

                # Download results
                downloaded = controller.download_images(scene_dir, prefix=f"scene_{scene_idx:03d}")
                if downloaded:
                    success(f"Scene {scene_idx}: {len(downloaded)} images saved")
                else:
                    error(f"Scene {scene_idx}: No images downloaded")

            except Exception as e:
                error(f"Scene {scene_idx} error: {e}")
            finally:
                controller.stop()
                time.sleep(2)

        return True

    # =========================================================================
    # STEP 3: Generate narration audio
    # =========================================================================
    def generate_narration(self):
        header("STEP 3: Generating Narration Audio")

        narration_path = self.audio_dir / "narration.mp3"
        if narration_path.exists() and narration_path.stat().st_size > 50000:
            status(f"Narration already exists ({narration_path.stat().st_size // 1024}KB)")
            return narration_path

        try:
            import edge_tts
        except ImportError:
            error("edge-tts not installed. Run: pip install edge-tts")
            return None

        voice = self._get_settings("voice", "en-US-AriaNeural")
        rate = self._get_settings("narration_speed", "-15%")
        text = self.config["narration"]

        status(f"Generating narration with voice: {voice}, rate: {rate}")

        async def _generate():
            communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
            await communicate.save(str(narration_path))

        asyncio.run(_generate())

        if narration_path.exists() and narration_path.stat().st_size > 10000:
            success(f"Narration saved: {narration_path.stat().st_size // 1024}KB")
            return narration_path
        else:
            error("Narration generation failed")
            return None

    # =========================================================================
    # STEP 4: Find or set music
    # =========================================================================
    def get_music_path(self):
        music_dir = self.root / "assets" / "music" / "calm"
        candidates = [
            music_dir / "relaxing_ambient.mp3",
            music_dir / "ambient_5min.wav",
            music_dir / "ambient_bedtime.wav",
        ]
        for c in candidates:
            if c.exists() and c.stat().st_size > 100000:
                status(f"Using music: {c.name}")
                return c

        status("No music file found. Videos will have narration only.", "yellow")
        return None

    # =========================================================================
    # STEP 5: Assemble final videos
    # =========================================================================
    def assemble_videos(self, narration_path, music_path):
        header("STEP 4: Assembling Final Videos")

        # Check ffmpeg
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            error("ffmpeg not found. Install ffmpeg first.")
            return False

        scenes = self.config["scenes"]
        resolution = self._get_settings("resolution", "1920x1080")
        width, height = resolution.split("x")
        fps = self._get_settings("fps", 24)
        crf = self._get_settings("video_quality", 18)
        music_vol = self._get_settings("music_volume", 0.18)
        narr_vol = self._get_settings("narration_volume", 1.2)

        # Get narration duration to calculate scene timing
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0",
             str(narration_path)],
            capture_output=True, text=True
        )
        narr_duration = float(result.stdout.strip()) if result.stdout.strip() else 300
        secs_per_scene = narr_duration / len(scenes)
        status(f"Narration: {narr_duration:.0f}s, {secs_per_scene:.2f}s per scene")

        # Build concat file
        concat_file = self.output_dir / "ffmpeg_concat.txt"
        lines = []
        for i in range(1, len(scenes) + 1):
            scene_dir = self.output_dir / f"scene_{i:03d}_batch_1"
            if not scene_dir.exists():
                continue
            images = list(scene_dir.glob("*.png")) + list(scene_dir.glob("*.jpg")) + list(scene_dir.glob("*.webp"))
            if not images:
                continue
            best = max(images, key=lambda p: p.stat().st_size)
            lines.append(f"file '{best}'")
            lines.append(f"duration {secs_per_scene:.3f}")

        if not lines:
            error("No scene images found!")
            return False

        # Add last frame hold
        lines.append(lines[-2])
        lines.append("duration 0.1")

        with open(concat_file, "w") as f:
            f.write("\n".join(lines))

        total_duration = narr_duration + 1
        title_safe = self.config["title"].lower().replace(" ", "_").replace("-", "")[:30]
        versions = self._get_settings("output_versions", ["narrated", "music_only"])

        # Build narrated version (narration + music)
        if "narrated" in versions and narration_path:
            status("Building narrated version...")
            output_path = self.videos_dir / f"{title_safe}_narrated.mp4"

            if music_path:
                # Pre-mix audio
                mixed_audio = self.audio_dir / "mixed_audio.wav"
                mix_cmd = [
                    "ffmpeg", "-y",
                    "-i", str(narration_path),
                    "-i", str(music_path),
                    "-filter_complex",
                    f"[0:a]volume={narr_vol},apad=whole_dur={total_duration}[narr];"
                    f"[1:a]volume={music_vol},apad=whole_dur={total_duration},"
                    f"afade=t=out:st={narr_duration - 8}:d=8[mus];"
                    f"[narr][mus]amerge=inputs=2,pan=mono|c0=0.5*c0+0.5*c1[aout]",
                    "-map", "[aout]",
                    "-t", str(total_duration),
                    "-c:a", "pcm_s16le",
                    str(mixed_audio)
                ]
                subprocess.run(mix_cmd, capture_output=True)
                audio_input = mixed_audio
            else:
                audio_input = narration_path

            video_cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_file),
                "-i", str(audio_input),
                "-filter_complex",
                f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
                f"setsar=1,fps={fps}[vid]",
                "-map", "[vid]", "-map", "1:a",
                "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(output_path)
            ]
            subprocess.run(video_cmd, capture_output=True)

            if output_path.exists() and output_path.stat().st_size > 100000:
                success(f"Narrated video: {output_path.name} ({output_path.stat().st_size // 1024 // 1024}MB)")
            else:
                error("Failed to create narrated video")

        # Build music-only version
        if "music_only" in versions and music_path:
            status("Building music-only version...")
            output_path = self.videos_dir / f"{title_safe}_music_only.mp4"

            video_cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_file),
                "-i", str(music_path),
                "-filter_complex",
                f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
                f"setsar=1,fps={fps}[vid];"
                f"[1:a]volume=0.7,afade=t=in:st=0:d=3,"
                f"afade=t=out:st={narr_duration - 8}:d=8[mus]",
                "-map", "[vid]", "-map", "[mus]",
                "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(output_path)
            ]
            subprocess.run(video_cmd, capture_output=True)

            if output_path.exists() and output_path.stat().st_size > 100000:
                success(f"Music-only video: {output_path.name} ({output_path.stat().st_size // 1024 // 1024}MB)")
            else:
                error("Failed to create music-only video")

        return True

    # =========================================================================
    # MAIN RUN
    # =========================================================================
    def run(self, skip_whisk=False):
        header(f"STORY VIDEO MAKER: {self.config['title']}")
        status(f"Characters: {', '.join(c['name'] for c in self.config['characters'])}")
        status(f"Scene: {self.config['scene']['name']}")
        status(f"Total scenes: {len(self.config['scenes'])}")
        print()

        start = datetime.now()

        if not skip_whisk:
            # Step 1: Generate references
            self.generate_references()
            print()

            # Step 2: Generate scene images
            self.generate_scenes()
            print()
        else:
            status("Skipping Whisk generation (using existing images)")
            print()

        # Step 3: Generate narration
        narration_path = self.generate_narration()
        print()

        # Step 4: Get music
        music_path = self.get_music_path()
        print()

        # Step 5: Assemble videos
        if narration_path:
            self.assemble_videos(narration_path, music_path)

        elapsed = (datetime.now() - start).total_seconds()
        print()
        header("COMPLETE!")
        status(f"Time: {int(elapsed // 60)}m {int(elapsed % 60)}s")
        status(f"Videos saved to: {self.videos_dir}")


# =============================================================================
# CLI
# =============================================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Story Video Maker - Create animated story videos from a config file"
    )
    parser.add_argument("--config", default="story_config.json",
                        help="Path to story config JSON (default: story_config.json)")
    parser.add_argument("--skip-whisk", action="store_true",
                        help="Skip image generation (use existing images)")
    parser.add_argument("--video-only", action="store_true",
                        help="Only rebuild videos from existing images + audio")

    args = parser.parse_args()
    maker = StoryVideoMaker(config_path=args.config)

    if args.video_only:
        narration = maker.generate_narration()
        music = maker.get_music_path()
        if narration:
            maker.assemble_videos(narration, music)
    else:
        maker.run(skip_whisk=args.skip_whisk)
