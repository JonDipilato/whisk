#!/usr/bin/env python3
"""Test script for YouTube metadata generation and thumbnail creation.

Tests:
1. YouTube metadata generation (title, description, tags, chapters)
2. Thumbnail generation with text overlay
3. Metadata saving to JSON
4. Preview of what would be uploaded

Usage:
    python test_youtube_upload.py
"""

import json
import subprocess
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("[yellow]PIL/Pillow not available. Install with: pip install Pillow[/yellow]")

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from src.youtube_metadata import (
    YouTubeMetadataGenerator,
    generate_title,
    generate_description,
    generate_tags,
    generate_chapters_from_scenes,
    ChapterTimestamp,
)
from src.youtube_uploader import YouTubeUploader
from src.config import load_config

console = Console()


def extract_frame_from_video(video_path: Path, output_path: Path, timestamp: str = "00:00:05") -> Optional[Path]:
    """Extract a frame from video using ffmpeg.

    Args:
        video_path: Path to video file.
        output_path: Where to save the extracted frame.
        timestamp: Timestamp to extract (default 5 seconds in).

    Returns:
        Path to extracted image or None.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use ffmpeg to extract frame at timestamp
    cmd = [
        "ffmpeg", "-y",
        "-ss", timestamp,
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "2",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and output_path.exists():
        console.print(f"[green]Extracted frame from: {video_path.name} @ {timestamp}[/green]")
        return output_path
    else:
        console.print(f"[red]Failed to extract frame: {result.stderr}[/red]")
        return None


def generate_thumbnail_with_text(
    image_path: Path,
    title: str,
    output_path: Path,
    subtitle: Optional[str] = None,
) -> Optional[Path]:
    """Generate a YouTube thumbnail with large centered text overlay at top.

    Args:
        image_path: Source image path.
        title: Main title text (large, centered at top).
        output_path: Output thumbnail path.
        subtitle: Optional subtitle text (smaller, below title).

    Returns:
        Path to generated thumbnail.
    """
    if not HAS_PIL:
        console.print("[red]PIL/Pillow required for thumbnail generation[/red]")
        return None

    # Open and resize image to YouTube thumbnail size (1280x720)
    img = Image.open(image_path)

    # Resize to 1280x720 (YouTube thumbnail resolution)
    img_resized = img.resize((1280, 720), Image.Resampling.LANCZOS)

    # Create a copy for editing
    thumb = img_resized.copy()
    draw = ImageDraw.Draw(thumb, "RGBA")

    # Add semi-transparent dark overlay at top for text readability
    overlay_height = 200
    for y in range(overlay_height):
        alpha = int(200 * (1 - y / overlay_height))
        draw.rectangle([(0, y), (1280, y + 1)], fill=(0, 0, 0, alpha))

    # Load large bold font for title - try multiple options
    title_font = None
    try:
        font_candidates = [
            ("Impact", 130),
            ("Arial Black", 120),
            ("Arial-Bold", 120),
            ("Helvetica-Bold", 120),
            ("DejaVuSans-Bold", 120),
            ("NotoSans-Bold", 120),
        ]
        for font_name, size in font_candidates:
            try:
                title_font = ImageFont.truetype(font_name, size)
                console.print(f"[dim]Using font: {font_name}[/dim]")
                break
            except:
                continue
        if title_font is None:
            title_font = ImageFont.load_default()
            console.print("[yellow]Using default font[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Font loading error: {e}[/yellow]")
        title_font = ImageFont.load_default()

    # Load medium font for subtitle
    subtitle_font = None
    try:
        subtitle_font = ImageFont.truetype("Arial", 55)
    except:
        subtitle_font = title_font

    # Clean up title - remove "for kids" references and make it concise
    title_clean = title.upper()
    for phrase in [" FOR KIDS", " FOR CHILDREN", " FOR TODDLERS", "| GHIBLI STYLE", "| PIXAR STYLE"]:
        title_clean = title_clean.replace(phrase, "")

    # Shorten if too long
    if len(title_clean) > 30:
        title_clean = title_clean[:28] + "..."

    # Calculate text position (centered at top)
    text_bbox = draw.textbbox((0, 0), title_clean, font=title_font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (1280 - text_width) // 2
    text_y = 30  # Near the top

    # Draw title with multiple shadow layers for depth and readability
    shadow_offsets = [(8, 8), (5, 5), (3, 3)]
    for offset_x, offset_y in shadow_offsets:
        draw.text(
            (text_x + offset_x, text_y + offset_y),
            title_clean,
            font=title_font,
            fill=(0, 0, 0, 255)
        )

    # Main text (bright white)
    draw.text((text_x, text_y), title_clean, font=title_font, fill=(255, 255, 255))

    # Draw subtitle if provided
    if subtitle:
        sub_clean = subtitle.upper()
        # Remove "for kids" from subtitle too
        for phrase in [" FOR KIDS", " FOR CHILDREN", " FOR TODDLERS"]:
            sub_clean = sub_clean.replace(phrase, "")

        if sub_clean.strip():
            sub_bbox = draw.textbbox((0, 0), sub_clean, font=subtitle_font)
            sub_width = sub_bbox[2] - sub_bbox[0]
            sub_x = (1280 - sub_width) // 2
            sub_y = text_y + 125

            # Subtitle shadow
            draw.text((sub_x + 4, sub_y + 4), sub_clean, font=subtitle_font, fill=(0, 0, 0, 255))
            # Subtitle main (gold/amber color)
            draw.text((sub_x, sub_y), sub_clean, font=subtitle_font, fill=(255, 200, 80))

    # Add subtle gradient overlay at bottom
    for y in range(720 - 80, 720):
        alpha = int(80 * (y - (720 - 80)) / 80)
        draw.rectangle([(0, y), (1280, y + 1)], fill=(0, 0, 0, alpha))

    # Add subtle white border for definition
    from PIL import Image as PILImage
    border = PILImage.new("RGB", (1280 + 16, 720 + 16), (255, 255, 255))
    border.paste(thumb, (8, 8))
    thumb = border

    # Save thumbnail
    output_path.parent.mkdir(parents=True, exist_ok=True)
    thumb.save(output_path, "PNG", optimize=True)

    console.print(f"[green]Thumbnail saved: {output_path}[/green]")
    return output_path


def test_metadata_generation(story_config: dict) -> dict:
    """Test metadata generation from story config.

    Args:
        story_config: Story configuration dictionary.

    Returns:
        Dictionary with generated metadata and paths.
    """
    console.print("\n[bold cyan]=== Testing Metadata Generation ===[/bold cyan]\n")

    # Extract info from config
    title = story_config.get("title", "Starfall Valley")
    characters = story_config.get("characters", [])
    main_character = characters[0]["name"] if characters else "Luna"
    scene_info = story_config.get("scene", {})
    theme = scene_info.get("name", "Starfall Valley")
    style = story_config.get("style", "Studio Ghibli")

    # Normalize style
    if "ghibli" in style.lower():
        style_tag = "ghibli"
    elif "pixar" in style.lower():
        style_tag = "pixar"
    elif "watercolor" in style.lower():
        style_tag = "watercolor"
    else:
        style_tag = "ghibli"

    # Initialize metadata generator
    generator = YouTubeMetadataGenerator()

    # Generate title options
    console.print("[yellow]Title Options:[/yellow]")
    title_options = []
    for i in range(3):
        generated_title = generate_title(
            character_name=main_character,
            theme=theme,
            style=style_tag,
        )
        title_options.append(generated_title)
        console.print(f"  {i + 1}. {generated_title}")

    selected_title = title_options[0]

    # Generate chapters from scenes
    scenes = story_config.get("scenes", [])
    console.print(f"\n[yellow]Generating chapters from {len(scenes)} scenes...[/yellow]")

    # Create scene data structure
    scene_data = []
    for i, scene_prompt in enumerate(scenes):
        scene_data.append({
            "scene_id": i + 1,
            "prompt": scene_prompt,
            "image_count": 1,
        })

    chapters = generate_chapters_from_scenes(scene_data)
    console.print(f"[green]Generated {len(chapters)} chapter timestamps[/green]")

    # Show first few chapters
    console.print("\n[yellow]Chapter Preview (first 5):[/yellow]")
    for chapter in chapters[:5]:
        console.print(f"  {chapter.timestamp} - {chapter.title}")

    # Generate tags
    tags = generate_tags(
        style=style_tag,
        theme=theme,
        character_name=main_character,
    )
    console.print(f"\n[yellow]Generated {len(tags)} tags[/yellow]")
    console.print(f"  [dim]{', '.join(tags[:10])}...[/dim]")

    # Generate full metadata package
    metadata = generator.generate_all_metadata(
        character_name=main_character,
        theme=theme,
        style=style_tag,
        summary=f"In this peaceful {style_tag} bedtime story, {main_character} discovers the magical {theme}.",
        lesson="friendship, courage, and the magic of the stars",
        chapters=chapters,
        custom_title=selected_title,
    )

    # Print preview
    generator.print_metadata_preview(metadata)

    # Save metadata to file
    output_dir = Path("output/videos")
    metadata_path = output_dir / "starfall_valley_music_only_metadata.json"
    generator.save_metadata(metadata, metadata_path)

    return {
        "metadata": metadata,
        "metadata_path": metadata_path,
        "title": selected_title,
        "chapters": chapters,
        "tags": tags,
    }


def test_thumbnail_generation(story_config: dict, metadata: dict) -> Optional[Path]:
    """Test thumbnail generation from video frame.

    Args:
        story_config: Story configuration.
        metadata: Generated metadata.

    Returns:
        Path to generated thumbnail.
    """
    console.print("\n[bold cyan]=== Testing Thumbnail Generation ===[/bold cyan]\n")

    # Use the narrated video to extract a frame
    video_path = Path("output/videos/starfall_valley_narrated.mp4")

    if not video_path.exists():
        console.print(f"[red]Video not found: {video_path}[/red]")
        return None

    console.print(f"[green]Using video: {video_path}[/green]")

    # Extract frame from video (at 10 seconds for a good scene)
    temp_frame = Path("output/thumbnails/temp_frame.png")
    extracted_frame = extract_frame_from_video(video_path, temp_frame, timestamp="00:00:10")

    if not extracted_frame:
        console.print("[red]Failed to extract frame from video[/red]")
        return None

    # Generate thumbnail with text - extract just the story name from title
    # Title format: "Sleep Story: Luna's Starfall Valley Journey | Ghibli Style"
    # We want: "Luna's Starfall Valley Journey"
    title_text = metadata["title"].split("|")[0].strip()
    # Remove prefix like "Sleep Story: "
    if ":" in title_text:
        title_text = title_text.split(":", 1)[1].strip()

    output_dir = Path("output/thumbnails")
    output_dir.mkdir(parents=True, exist_ok=True)
    thumbnail_path = output_dir / "starfall_valley_music_only_thumbnail.png"

    # No "for kids" subtitle - just the title
    thumbnail_path = generate_thumbnail_with_text(
        image_path=extracted_frame,
        title=title_text,
        subtitle=None,  # No subtitle
        output_path=thumbnail_path,
    )

    # Clean up temp frame
    if temp_frame.exists():
        temp_frame.unlink()

    return thumbnail_path


def test_uploader_connection(video_path: Path, metadata_path: Path, thumbnail_path: Path):
    """Test YouTube uploader (auth check only, no upload).

    Args:
        video_path: Path to video file.
        metadata_path: Path to metadata JSON.
        thumbnail_path: Path to thumbnail image.
    """
    console.print("\n[bold cyan]=== Testing YouTube Upload Connection ===[/bold cyan]\n")

    uploader = YouTubeUploader()

    # Check if dependencies are available
    try:
        from googleapiclient.discovery import build
        console.print("[green]YouTube API dependencies installed[/green]")
    except ImportError:
        console.print("[red]YouTube API dependencies missing![/red]")
        console.print("[yellow]Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib[/yellow]")
        return

    # Check for client secret
    if Path("youtube_client_secret.json").exists():
        console.print("[green]Client secret file found[/green]")

        # Try authentication (opens browser)
        console.print("\n[yellow]Attempting authentication (will open browser)...[/yellow]")
        if uploader.authenticate():
            console.print("[green]Authentication successful![/green]")

            # Load metadata
            with open(metadata_path) as f:
                meta = json.load(f)

            # Show what would be uploaded
            console.print("\n[bold green]Ready to upload with:[/bold green]")
            console.print(f"  Video: {video_path.name} ({video_path.stat().st_size // 1024 // 1024} MB)")
            console.print(f"  Title: {meta['title']}")
            console.print(f"  Thumbnail: {thumbnail_path}")
            console.print("\n[dim]To actually upload, call uploader.upload() with the above parameters[/dim]")
        else:
            console.print("[red]Authentication failed[/red]")
    else:
        console.print("[yellow]No client secret file found[/yellow]")
        console.print("[dim]To enable uploads, download OAuth2 credentials from Google Cloud Console[/dim]")


def display_summary(results: dict):
    """Display a summary of the test results.

    Args:
        results: Dictionary with test results.
    """
    console.print("\n[bold cyan]=== Test Summary ===[/bold cyan]\n")

    table = Table(title="Generated Files", show_header=True, header_style="bold magenta")
    table.add_column("Type", style="cyan")
    table.add_column("Path", style="green")
    table.add_column("Status", style="yellow")

    table.add_row(
        "Metadata",
        str(results.get("metadata_path", "N/A")),
        "[green]Created[/green]" if results.get("metadata_path") else "[red]Failed[/red]"
    )
    table.add_row(
        "Thumbnail",
        str(results.get("thumbnail_path", "N/A")),
        "[green]Created[/green]" if results.get("thumbnail_path") else "[red]Failed[/red]"
    )
    table.add_row(
        "Video",
        "output/videos/starfall_valley_music_only.mp4",
        "[green]Exists[/green]" if Path("output/videos/starfall_valley_music_only.mp4").exists() else "[red]Missing[/red]"
    )

    console.print(table)

    # Display upload command preview
    if results.get("metadata_path") and results.get("thumbnail_path"):
        console.print("\n[bold yellow]Upload Command Preview:[/bold yellow]")
        console.print(Panel(
            f"""from src.youtube_uploader import YouTubeUploader

uploader = YouTubeUploader()
video_id = uploader.upload_with_metadata_file(
    video_path="output/videos/starfall_valley_music_only.mp4",
    metadata_path="{results['metadata_path']}",
    thumbnail_path="{results['thumbnail_path']}",
    schedule_hours=24,  # Schedule for 24 hours from now
)""",
            title="Python Code",
            border_style="dim"
        ))


def main():
    """Run all tests."""
    console.print("[bold cyan]YouTube Upload Test Suite[/bold cyan]")
    console.print("[dim]Testing metadata generation and thumbnail creation[/dim]\n")

    # Load story config
    config_path = Path("story_config.json")
    if not config_path.exists():
        console.print(f"[red]Config not found: {config_path}[/red]")
        return

    with open(config_path) as f:
        story_config = json.load(f)

    results = {}

    # Test 1: Metadata generation
    try:
        metadata_results = test_metadata_generation(story_config)
        results.update(metadata_results)
    except Exception as e:
        console.print(f"[red]Metadata generation failed: {e}[/red]")
        import traceback
        traceback.print_exc()

    # Test 2: Thumbnail generation
    try:
        thumbnail_path = test_thumbnail_generation(story_config, metadata_results)
        results["thumbnail_path"] = thumbnail_path
    except Exception as e:
        console.print(f"[red]Thumbnail generation failed: {e}[/red]")
        import traceback
        traceback.print_exc()

    # Test 3: Uploader connection (auth check)
    try:
        video_path = Path("output/videos/starfall_valley_music_only.mp4")
        if video_path.exists():
            test_uploader_connection(
                video_path,
                results.get("metadata_path"),
                results.get("thumbnail_path"),
            )
        else:
            console.print(f"[yellow]Video not found: {video_path}[/yellow]")
    except Exception as e:
        console.print(f"[red]Uploader test failed: {e}[/red]")
        import traceback
        traceback.print_exc()

    # Display summary
    display_summary(results)


if __name__ == "__main__":
    main()
