#!/usr/bin/env python3
"""
Whisk Automation CLI - Batch image generation using Google Whisk.

Usage:
    python run.py --help
    python run.py test           # Test connection to Whisk
    python run.py add-scene ...  # Add a single scene to queue
    python run.py load-csv ...   # Load scenes from CSV
    python run.py status         # Show queue status
    python run.py process        # Process the queue
"""

from pathlib import Path
from datetime import datetime
import click
from rich.console import Console
from rich.panel import Panel
from selenium.webdriver.common.by import By

from src.config import load_config, save_config, AppConfig
from src.models import Scene, ImageFormat
from src.queue_manager import QueueManager, create_sample_csv
from src.whisk_controller import test_whisk_connection, WhiskController

# Video pipeline imports
from src.video_assembler import VideoAssembler, create_video_from_output, create_video_from_scenes
from src.audio_generator import AudioGenerator, list_available_voices
from src.youtube_metadata import YouTubeMetadataGenerator, generate_metadata_package
from src.pipeline import VideoPipeline, PipelineConfig, run_pipeline_from_output
from src.music_library import MusicLibrary, setup_music_library, MusicCategory

console = Console()


@click.group()
@click.pass_context
def cli(ctx):
    """Whisk Automation - Batch image generation using Google Whisk."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config()


@cli.command()
@click.pass_context
def test(ctx):
    """Test connection to Whisk."""
    config = ctx.obj["config"]
    console.print("[bold cyan]Testing Whisk connection...[/bold cyan]")
    test_whisk_connection(config)


@cli.command()
@click.pass_context
def status(ctx):
    """Show queue status."""
    config = ctx.obj["config"]
    manager = QueueManager(config)
    manager.load_state()
    manager.show_status()


@cli.command("add-scene")
@click.option("--scene-id", "-s", required=True, type=int, help="Scene ID number")
@click.option("--env", "-e", required=True, help="Environment image ID")
@click.option("--chars", "-c", default="", help="Character IDs (comma-separated)")
@click.option("--prompt", "-p", required=True, help="Generation prompt")
@click.option("--format", "-f", type=click.Choice(["landscape", "portrait", "square"]), default="landscape")
@click.option("--batches", "-b", type=int, default=None, help="Number of batches (default from config)")
@click.pass_context
def add_scene(ctx, scene_id, env, chars, prompt, format, batches):
    """Add a single scene to the queue."""
    config = ctx.obj["config"]

    char_list = [c.strip() for c in chars.split(",") if c.strip()] if chars else []

    scene = Scene(
        scene_id=scene_id,
        environment_id=env,
        character_ids=char_list,
        prompt=prompt,
        image_format=ImageFormat(format),
    )

    manager = QueueManager(config)
    manager.load_state()
    manager.add_scene(scene, batches=batches)


@cli.command("load-csv")
@click.argument("csv_path", type=click.Path(exists=True))
@click.pass_context
def load_csv(ctx, csv_path):
    """Load scenes from a CSV file and add to queue."""
    config = ctx.obj["config"]
    manager = QueueManager(config)
    manager.load_state()
    manager.add_scenes_from_csv(Path(csv_path))


@cli.command()
@click.pass_context
def process(ctx):
    """Process all pending items in the queue."""
    config = ctx.obj["config"]
    manager = QueueManager(config)
    manager.load_state()
    manager.process_queue()


@cli.command("process-one")
@click.pass_context
def process_one(ctx):
    """Process a single item from the queue (for testing)."""
    config = ctx.obj["config"]
    manager = QueueManager(config)
    manager.load_state()
    manager.process_one()


@cli.command("debug-page")
@click.pass_context
def debug_page(ctx):
    """Debug the page structure to find elements."""
    from src.whisk_controller import WhiskController
    config = ctx.obj["config"]
    controller = WhiskController(config)

    try:
        controller.start()
        console.print("\n[bold cyan]Page Structure Debug[/bold cyan]")

        # Get page HTML for inspection
        page_source = controller.driver.page_source
        console.print(f"Page source length: {len(page_source)} characters")

        # Look for file-related keywords in HTML
        keywords = ["input type=\"file\"", "accept=\"image", "upload", "dropzone", "drag-drop"]
        console.print("\n[bold]File upload related HTML:[/bold]")
        for keyword in keywords:
            count = page_source.count(keyword)
            if count > 0:
                console.print(f"  '{keyword}': {count} occurrences")

        # Look for all elements that might be clickable for upload
        console.print("\n[bold]Potential upload elements:[/bold]")
        all_elements = controller.driver.find_elements(By.XPATH, "//*[@onclick or @role='button' or contains(@class, 'upload') or contains(@class, 'drop')]")
        console.print(f"Found {len(all_elements)} potential upload elements")

        # Look for shadow DOM
        console.print("\n[bold]Checking for Shadow DOM:[/bold]")
        shadow_hosts = controller.driver.execute_script("""
            return Array.from(document.querySelectorAll('*')).filter(el => el.shadowRoot);
        """)
        console.print(f"Found {len(shadow_hosts)} shadow hosts")

        console.print("\n[bold]All button classes:[/bold]")
        buttons = controller.driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons[:5]:
            btn_class = btn.get_attribute("class") or ""
            btn_text = btn.text or ""
            console.print(f"  class='{btn_class}' text='{btn_text[:30]}'")

        console.print("\n[yellow]Browser will stay open for 10 seconds for inspection...[/yellow]")
        import time
        time.sleep(10)

    finally:
        controller.stop()


@cli.command("clear")
@click.option("--all", "clear_all", is_flag=True, help="Clear entire queue")
@click.option("--completed", is_flag=True, help="Clear only completed items")
@click.pass_context
def clear(ctx, clear_all, completed):
    """Clear items from the queue."""
    config = ctx.obj["config"]
    manager = QueueManager(config)
    manager.load_state()

    if clear_all:
        manager.clear_queue()
    elif completed:
        manager.clear_completed()
    else:
        console.print("[yellow]Use --all or --completed flag[/yellow]")


@cli.command("retry-failed")
@click.pass_context
def retry_failed(ctx):
    """Reset failed items to pending for retry."""
    config = ctx.obj["config"]
    manager = QueueManager(config)
    manager.load_state()
    manager.reset_failed()


@cli.command("create-sample")
@click.pass_context
def create_sample(ctx):
    """Create sample CSV and folder structure."""
    config = ctx.obj["config"]

    # Create directories
    Path(config.paths.environments).mkdir(parents=True, exist_ok=True)
    Path(config.paths.characters).mkdir(parents=True, exist_ok=True)
    Path(config.paths.output).mkdir(parents=True, exist_ok=True)

    # Create sample CSV
    csv_path = Path(config.paths.scenes_file)
    create_sample_csv(csv_path)

    console.print("\n[bold green]Sample structure created![/bold green]")
    console.print(f"""
[cyan]Next steps:[/cyan]
1. Add environment images to: {config.paths.environments}/
2. Add character images to: {config.paths.characters}/
3. Edit the scenes file: {config.paths.scenes_file}
4. Run: [bold]python run.py load-csv {config.paths.scenes_file}[/bold]
5. Run: [bold]python run.py process[/bold]
""")


@cli.command("config")
@click.option("--show", is_flag=True, help="Show current config")
@click.option("--set-headless/--no-headless", default=None, help="Run browser in headless mode")
@click.option("--images-per-prompt", type=int, help="Images to generate per prompt")
@click.option("--batches", type=int, help="Batches per scene")
@click.pass_context
def config_cmd(ctx, show, set_headless, images_per_prompt, batches):
    """View or modify configuration."""
    config = ctx.obj["config"]

    if show or (set_headless is None and images_per_prompt is None and batches is None):
        console.print("[bold]Current Configuration:[/bold]")
        console.print(f"  Whisk URL: {config.whisk_url}")
        console.print(f"  Headless: {config.browser.headless}")
        console.print(f"  Images per prompt: {config.generation.images_per_prompt}")
        console.print(f"  Batches per scene: {config.generation.batches_per_scene}")
        console.print(f"  Environments path: {config.paths.environments}")
        console.print(f"  Characters path: {config.paths.characters}")
        console.print(f"  Output path: {config.paths.output}")
        return

    modified = False

    if set_headless is not None:
        config.browser.headless = set_headless
        modified = True

    if images_per_prompt is not None:
        config.generation.images_per_prompt = images_per_prompt
        modified = True

    if batches is not None:
        config.generation.batches_per_scene = batches
        modified = True

    if modified:
        save_config(config)
        console.print("[green]Configuration updated![/green]")


@cli.command("interactive")
@click.pass_context
def interactive(ctx):
    """Launch interactive mode with live browser control."""
    config = ctx.obj["config"]

    console.print("[bold cyan]Interactive Mode[/bold cyan]")
    console.print("This will open Whisk in a browser. You can then manually interact or use commands.")
    console.print("\nCommands during interactive mode:")
    console.print("  upload-env <path>  - Upload environment image")
    console.print("  upload-char <path> - Upload character image")
    console.print("  prompt <text>      - Set prompt")
    console.print("  generate           - Generate images")
    console.print("  download <folder>  - Download generated images")
    console.print("  quit               - Exit\n")

    _interactive_mode(config)


def _interactive_mode(config: AppConfig):
    """Run interactive mode."""
    controller = WhiskController(config)

    try:
        controller.start()
        console.print("[green]Browser ready! Whisk is loaded.[/green]")
        console.print("[yellow]The browser will stay open. Type commands or 'quit' to exit.[/yellow]\n")

        while True:
            try:
                cmd = input("> ")
                cmd = cmd.strip()

                if not cmd:
                    continue

                if cmd.lower() == "quit":
                    break

                parts = cmd.split(maxsplit=1)
                action = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""

                if action == "upload-env":
                    controller.upload_environment(Path(arg))
                elif action == "upload-char":
                    controller.upload_character(Path(arg))
                elif action == "prompt":
                    controller.set_prompt(arg)
                elif action == "generate":
                    controller.generate()
                    controller.wait_for_generation()
                elif action == "download":
                    folder = Path(config.paths.output) / (arg or "interactive")
                    controller.download_images(folder)
                elif action == "screenshot":
                    path = Path(config.paths.output) / "screenshot.png"
                    controller.driver.save_screenshot(str(path))
                    console.print(f"[green]Screenshot saved: {path}[/green]")
                elif action == "help":
                    console.print("Commands: upload-env, upload-char, prompt, generate, download, screenshot, quit")
                else:
                    console.print(f"[yellow]Unknown command: {action}[/yellow]")

            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    finally:
        controller.stop()


# ============================================
# Video Generation Commands
# ============================================

@cli.command("create-video")
@click.option("--scenes", required=True, help="Scene folder path or 'all' for output directory")
@click.option("--output", "-o", help="Output video path")
@click.option("--duration", "-d", type=float, default=4.0, help="Seconds per image")
@click.option("--images", "-i", type=int, default=1, help="Images per scene")
@click.option("--no-transitions", is_flag=True, help="Disable fade transitions")
@click.pass_context
def create_video(ctx, scenes, output, duration, images, no_transitions):
    """Assemble images into video."""
    config = ctx.obj["config"]

    console.print("[bold cyan]Creating video from images...[/bold cyan]")

    # Determine source path
    if scenes.lower() == "all":
        source_dir = Path(config.paths.output)
    else:
        source_dir = Path(scenes)

    if not source_dir.exists():
        console.print(f"[red]Error: Source directory not found: {source_dir}[/red]")
        return

    # Determine output path
    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = Path(config.paths.videos) / f"video_{timestamp}.mp4"
    else:
        output = Path(output)

    try:
        assembler = VideoAssembler(config)

        if scenes.lower() == "all":
            video_path, segments = assembler.create_video_from_output_directory(
                output_dir=source_dir,
                output_path=output,
                images_per_scene=images,
                duration_per_image=duration,
                add_transitions=not no_transitions,
            )
        else:
            # Single scene or directory
            video_path, segments = assembler.create_video_from_scenes(
                scene_folders=[source_dir],
                output_path=output,
                images_per_scene=images,
                duration_per_image=duration,
                add_transitions=not no_transitions,
            )

        # Show video info
        info = assembler.get_video_info(video_path)
        console.print(f"\n[green]Video created successfully![/green]")
        console.print(f"  Path: {video_path}")
        console.print(f"  Duration: {info['duration']:.1f}s")
        console.print(f"  Size: {info['size'][0]}x{info['size'][1]}")
        console.print(f"  Scenes: {len(segments)}")

    except Exception as e:
        console.print(f"[red]Error creating video: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())


@cli.command("full-pipeline")
@click.option("--scenes", required=True, help="Scene folder path or 'all' for output directory")
@click.option("--character", default="Grandmother", help="Main character name")
@click.option("--theme", default="Garden Adventure", help="Story theme")
@click.option("--style", default="ghibli", help="Visual style (ghibli, pixar, watercolor, storybook)")
@click.option("--narration", "-n", help="Full narration text for TTS")
@click.option("--narration-file", type=click.Path(exists=True), help="File containing narration text")
@click.option("--music", "-m", type=click.Path(exists=True), help="Background music file path")
@click.option("--music-category", default="calm", help="Music category (ambient, calm, upbeat, dramatic)")
@click.option("--voice", default="aria", help="TTS voice (aria, guy, jenny, etc.)")
@click.option("--images", "-i", type=int, default=1, help="Images per scene")
@click.option("--duration", "-d", type=float, default=4.0, help="Seconds per image")
@click.option("--title", help="Custom video title")
@click.option("--summary", help="Story summary for metadata")
@click.option("--lesson", help="Lesson learned for metadata")
@click.option("--project-id", help="Custom project ID")
@click.option("--asmr-only", is_flag=True, help="Generate only ASMR version (no narration)")
@click.option("--narrated-only", is_flag=True, help="Generate only narrated version")
@click.pass_context
def full_pipeline(ctx, scenes, character, theme, style, narration, narration_file,
                  music, music_category, voice, images, duration, title, summary,
                  lesson, project_id, asmr_only, narrated_only):
    """Run complete video generation pipeline."""
    config = ctx.obj["config"]

    console.print("[bold cyan]Running Full Video Pipeline[/bold cyan]")

    # Load narration from file if provided
    if narration_file:
        with open(narration_file, "r") as f:
            narration = f.read()

    # Determine source path
    if scenes.lower() == "all":
        source_dir = Path(config.paths.output)
    else:
        source_dir = Path(scenes)

    if not source_dir.exists():
        console.print(f"[red]Error: Source directory not found: {source_dir}[/red]")
        return

    # Get scene folders
    scene_folders = sorted([
        f for f in source_dir.iterdir()
        if f.is_dir() and f.name.startswith("scene_")
    ])
    if not scene_folders and source_dir.is_dir():
        # If no scene_* subdirs found, use the directory itself
        scene_folders = [source_dir]

    if not scene_folders:
        console.print(f"[red]Error: No scene folders found[/red]")
        return

    console.print(f"Found {len(scene_folders)} scene folders")

    # Create pipeline config
    pipeline_config = PipelineConfig(
        character_name=character,
        theme=theme,
        style=style,
        narration_text=narration,
        music_path=Path(music) if music else None,
        music_category=music_category,
        voice=voice,
        images_per_scene=images,
        duration_per_image=duration,
        custom_title=title,
        summary=summary,
        lesson=lesson,
        generate_both_versions=not (asmr_only or narrated_only),
    )

    # Run pipeline
    pipeline = VideoPipeline(config)
    result = pipeline.run_full_pipeline(
        image_folders=scene_folders,
        pipeline_config=pipeline_config,
        project_id=project_id,
    )

    # Print final status
    if result.success:
        console.print(f"\n[bold green]Pipeline Complete![/bold green]")
        console.print(f"Project ID: {result.project_id}")
        console.print(f"Video duration: {result.duration:.1f}s")
        console.print(f"Generation time: {result.generation_time_seconds / 60:.1f} minutes")
    else:
        console.print(f"\n[red]Pipeline Failed:[/red] {result.error_message}")


@cli.command("generate-audio")
@click.option("--text", "-t", required=True, help="Text to convert to speech")
@click.option("--output", "-o", required=True, help="Output audio file path")
@click.option("--voice", default="aria", help="TTS voice (aria, guy, jenny, etc.)")
@click.option("--list-voices", is_flag=True, help="List available voices")
@click.pass_context
def generate_audio(ctx, text, output, voice, list_voices):
    """Generate text-to-speech audio."""
    if list_voices:
        console.print("[bold cyan]Available TTS Voices:[/bold cyan]")
        for name, voice_id in list_available_voices().items():
            console.print(f"  {name}: {voice_id}")
        return

    config = ctx.obj["config"]
    generator = AudioGenerator(config)

    console.print(f"[cyan]Generating TTS audio...[/cyan]")

    try:
        result = generator.text_to_speech(
            text=text,
            output_path=Path(output),
            voice=voice,
        )
        console.print(f"[green]Audio saved: {result}[/green]")
    except Exception as e:
        console.print(f"[red]Error generating audio: {e}[/red]")


@cli.command("mix-audio")
@click.option("--narration", "-n", type=click.Path(exists=True), help="Narration audio file")
@click.option("--music", "-m", type=click.Path(exists=True), required=True, help="Background music file")
@click.option("--output", "-o", required=True, help="Output audio file path")
@click.option("--music-volume", type=float, default=0.25, help="Music volume (0-1)")
@click.option("--fade-in", type=float, default=0.5, help="Fade in duration (seconds)")
@click.option("--fade-out", type=float, default=1.0, help="Fade out duration (seconds)")
@click.pass_context
def mix_audio(ctx, narration, music, output, music_volume, fade_in, fade_out):
    """Mix narration and background music."""
    config = ctx.obj["config"]
    generator = AudioGenerator(config)

    console.print(f"[cyan]Mixing audio...[/cyan]")

    try:
        result = generator.create_audio_mix(
            narration_path=Path(narration) if narration else None,
            music_path=Path(music),
            output_path=Path(output),
            music_volume=music_volume,
            fade_in=fade_in,
            fade_out=fade_out,
        )
        console.print(f"[green]Audio mix saved: {result}[/green]")
    except Exception as e:
        console.print(f"[red]Error mixing audio: {e}[/red]")


@cli.command("generate-metadata")
@click.option("--character", default="Grandmother", help="Main character name")
@click.option("--theme", default="Garden Adventure", help="Story theme")
@click.option("--style", default="ghibli", help="Visual style")
@click.option("--title", help="Custom video title")
@click.option("--summary", help="Story summary")
@click.option("--lesson", help="Lesson learned")
@click.option("--output", "-o", help="Output metadata file path")
@click.pass_context
def generate_metadata_cmd(ctx, character, theme, style, title, summary, lesson, output):
    """Generate YouTube metadata (title, description, tags)."""
    config = ctx.obj["config"]
    generator = YouTubeMetadataGenerator(config)

    console.print("[cyan]Generating YouTube metadata...[/cyan]")

    metadata = generator.generate_all_metadata(
        character_name=character,
        theme=theme,
        style=style,
        custom_title=title,
        summary=summary,
        lesson=lesson,
    )

    generator.print_metadata_preview(metadata)

    if output:
        generator.save_metadata(metadata, Path(output))
        console.print(f"\n[green]Metadata saved to: {output}[/green]")


@cli.command("music-library")
@click.option("--scan", is_flag=True, help="Scan library for new tracks")
@click.option("--list", "list_category", help="List tracks in category")
@click.option("--setup", is_flag=True, help="Create library directory structure")
@click.pass_context
def music_library_cmd(ctx, scan, list_category, setup):
    """Manage music library."""
    config = ctx.obj["config"]
    library = setup_music_library(config=config)

    if setup:
        library.ensure_directories()
        console.print(f"[green]Library ready at: {library.library_path}[/green]")
        return

    if scan:
        count = library._scan_library()
        console.print(f"[green]Found {count} new tracks[/green]")

    if list_category:
        tracks = library.list_tracks(MusicCategory(list_category) if list_category != "all" else None)
        console.print(f"\n[bold]Tracks ({len(tracks)}):[/bold]")
        for track in tracks:
            console.print(f"  {track.name} ({track.category.value}) - {track.duration:.1f}s")

    library.print_library_status()


@cli.command("video-info")
@click.argument("video_path", type=click.Path(exists=True))
@click.pass_context
def video_info_cmd(ctx, video_path):
    """Get information about a video file."""
    config = ctx.obj["config"]
    assembler = VideoAssembler(config)

    try:
        info = assembler.get_video_info(Path(video_path))

        console.print(f"\n[bold cyan]Video Information[/bold cyan]\n")
        console.print(f"Path: {info['path']}")
        console.print(f"Duration: {info['duration']:.1f} seconds ({info['duration']/60:.1f} minutes)")
        console.print(f"Size: {info['size'][0]}x{info['size'][1]}")
        console.print(f"FPS: {info['fps']}")
        console.print(f"Has Audio: {info['has_audio']}")

    except Exception as e:
        console.print(f"[red]Error reading video: {e}[/red]")


@cli.command("export-youtube")
@click.argument("video_path", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output path (default: adds _youtube suffix)")
@click.pass_context
def export_youtube_cmd(ctx, video_path, output):
    """Export video with YouTube-optimized settings."""
    config = ctx.obj["config"]
    assembler = VideoAssembler(config)

    console.print("[cyan]Exporting for YouTube...[/cyan]")

    try:
        result = assembler.export_for_youtube(
            video_path=Path(video_path),
            output_path=Path(output) if output else None,
        )
        console.print(f"[green]YouTube-ready video: {result}[/green]")
    except Exception as e:
        console.print(f"[red]Error exporting video: {e}[/red]")


@cli.command("master")
@click.option("--story", default="grandmother_garden", help="Story name to create")
@click.option("--project-id", help="Custom project ID")
@click.option("--skip-generation", is_flag=True, help="Skip image generation (use existing images)")
@click.pass_context
def master_cmd(ctx, story, project_id, skip_generation):
    """MASTER AUTOMATION - One command for everything.

    This single command does the ENTIRE pipeline:
      1. Queues all story scenes
      2. Generates images via Whisk
      3. Creates video from images
      4. Generates TTS narration
      5. Mixes with background music
      6. Generates YouTube metadata
      7. Exports final video

    Example:
        python run.py master
    """
    config = ctx.obj["config"]

    console.print(Panel(
        "[bold magenta]🎬 MASTER AUTOMATION[/bold magenta]\n"
        "One command to create a complete YouTube-ready video",
        title="Full Pipeline"
    ))

    import subprocess
    import sys

    # Run the master automation script
    cmd = [sys.executable, "master_automation.py"]
    if story:
        cmd.extend(["--story", story])
    if project_id:
        cmd.extend(["--project-id", project_id])
    if skip_generation:
        cmd.extend(["--only", "video"])

    console.print(f"[cyan]Running: {' '.join(cmd)}[/cyan]")
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    cli()
