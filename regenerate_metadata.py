#!/usr/bin/env python3
"""Regenerate metadata with proper format and re-upload video.

Based on analysis of successful channels like Sleepytime Corner:
- ~10 meaningful chapters (not 75!)
- ~50-60 second intervals
- Full descriptive chapter titles
- Rich description with emojis
- NO "made for kids" setting
"""

import json
import subprocess
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from src.youtube_metadata import (
    YouTubeMetadataGenerator,
    generate_description,
    generate_chapters_from_scenes,
    generate_story_chapters,
)
from src.youtube_uploader import YouTubeUploader

console = Console()


def extract_frame_from_video(video_path: Path, output_path: Path, timestamp: str = "00:00:10"):
    """Extract a frame from video using ffmpeg."""
    cmd = ["ffmpeg", "-y", "-ss", timestamp, "-i", str(video_path),
           "-vframes", "1", "-q:v", "2", str(output_path)]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0 and output_path.exists()


def generate_thumbnail_with_text(image_path: Path, title: str, output_path: Path):
    """Generate YouTube thumbnail with large centered text at top."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        console.print("[red]PIL required for thumbnail[/red]")
        return None

    img = Image.open(image_path)
    img_resized = img.resize((1280, 720), Image.Resampling.LANCZOS)
    thumb = img_resized.copy()
    draw = ImageDraw.Draw(thumb, "RGBA")

    # Dark overlay at top
    for y in range(200):
        alpha = int(200 * (1 - y / 200))
        draw.rectangle([(0, y), (1280, y + 1)], fill=(0, 0, 0, alpha))

    # Load font
    title_font = None
    for font_name, size in [("Impact", 130), ("Arial Black", 120), ("Arial-Bold", 120)]:
        try:
            title_font = ImageFont.truetype(font_name, size)
            break
        except:
            continue
    if not title_font:
        title_font = ImageFont.load_default()

    # Clean title - remove style tag and shorten
    title_clean = title.upper()
    for phrase in [" FOR KIDS", " FOR CHILDREN", "| GHIBLI STYLE", "| PIXAR STYLE"]:
        title_clean = title_clean.replace(phrase, "")
    if len(title_clean) > 28:
        title_clean = title_clean[:26] + "..."

    # Center and draw
    text_bbox = draw.textbbox((0, 0), title_clean, font=title_font)
    text_x = (1280 - (text_bbox[2] - text_bbox[0])) // 2
    text_y = 30

    # Shadow layers
    for ox, oy in [(8, 8), (5, 5), (3, 3)]:
        draw.text((text_x + ox, text_y + oy), title_clean, font=title_font, fill=(0, 0, 0, 255))
    draw.text((text_x, text_y), title_clean, font=title_font, fill=(255, 255, 255))

    # Bottom gradient
    for y in range(720 - 80, 720):
        alpha = int(80 * (y - (720 - 80)) / 80)
        draw.rectangle([(0, y), (1280, y + 1)], fill=(0, 0, 0, alpha))

    # White border
    from PIL import Image as PILImage
    border = PILImage.new("RGB", (1296, 736), (255, 255, 255))
    border.paste(thumb, (8, 8))
    border.save(output_path, "PNG", optimize=True)
    return output_path


def main():
    console.print("[bold cyan]Regenerating Metadata & Re-uploading[/bold cyan]\n")

    # Load story config
    with open("story_config.json") as f:
        story_config = json.load(f)

    characters = story_config.get("characters", [])
    main_character = characters[0]["name"] if characters else "Luna"
    scene_info = story_config.get("scene", {})
    theme = scene_info.get("name", "Starfall Valley")
    style = story_config.get("style", "Studio Ghibli")

    # Style tag
    if "ghibli" in style.lower():
        style_tag = "ghibli"
    elif "pixar" in style.lower():
        style_tag = "pixar"
    else:
        style_tag = "ghibli"

    # Video duration (42 MB file ~ 5 minutes typically)
    # Calculate from scenes: 75 scenes × 4.26 seconds = ~320 seconds = ~5:20
    total_duration = 75 * 4.26

    # Generate proper story-based chapters (~10 chapters, not 75!)
    console.print("[yellow]Generating story-based chapters (~10 meaningful chapters)...[/yellow]")
    chapters = generate_story_chapters(
        total_duration_seconds=total_duration,
        story_title=story_config.get("title", "Starfall Valley"),
        character_name=main_character,
        setting_name=theme,
        target_chapter_count=10,
    )

    console.print(f"[green]Generated {len(chapters)} chapters:[/green]")
    for ch in chapters:
        console.print(f"  {ch.timestamp} - {ch.title}")

    # Generate description
    console.print("\n[yellow]Generating rich description...[/yellow]")
    description = generate_description(
        title=f"{main_character}'s {theme} Adventure | {style_tag.title()} Bedtime Story",
        character_name=main_character,
        theme=theme,
        style=style_tag,
        summary=f"In this peaceful {style_tag} bedtime story, {main_character} discovers the magical {theme}, "
                f"a place where fallen stars come to rest. Join {main_character} and friends on this gentle "
                f"journey of friendship, courage, and wonder—perfect for helping little ones relax and drift "
                f"into peaceful dreams.",
        lesson="friendship, courage, and the magic of the stars",
        chapters=chapters,
        channel_name="Cozy Storytime",
        channel_handle="cozystorytime",
    )

    # Save metadata
    metadata = {
        "title": f"{main_character}'s {theme} Adventure | {style_tag.title()} Bedtime Story",
        "description": description,
        "tags": [
            f"{style_tag} bedtime stories",
            "bedtime stories for kids",
            "calming stories for sleep",
            "sleep stories for children",
            "peaceful bedtime stories",
            "animated stories",
            "kids stories",
            "bedtime stories",
            f"{main_character} stories",
            f"{theme} story",
        ],
        "category": "Education",
        "privacy_status": "unlisted",
        "chapter_timestamps": {c.timestamp: c.title for c in chapters},
        "made_for_kids": False,  # IMPORTANT: Not set to True
    }

    metadata_path = Path("output/videos/starfall_valley_music_only_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    console.print(f"[green]Metadata saved: {metadata_path}[/green]")

    # Generate thumbnail
    console.print("\n[yellow]Generating thumbnail...[/yellow]")
    video_path = Path("output/videos/starfall_valley_narrated.mp4")
    temp_frame = Path("output/thumbnails/temp_frame.png")
    thumbnail_path = Path("output/thumbnails/starfall_valley_music_only_thumbnail.png")

    if extract_frame_from_video(video_path, temp_frame, "00:00:15"):
        generate_thumbnail_with_text(temp_frame, metadata["title"], thumbnail_path)
        temp_frame.unlink()
        console.print(f"[green]Thumbnail saved: {thumbnail_path}[/green]")
    else:
        console.print("[red]Failed to extract frame[/red]")

    # Show preview
    console.print(Panel.fit(
        f"[bold]Title:[/bold] {metadata['title']}\n"
        f"[bold]Chapters:[/bold] {len(chapters)} (was 75!)\n"
        f"[bold]Made for Kids:[/bold] {metadata['made_for_kids']}\n"
        f"[bold]Privacy:[/bold] {metadata['privacy_status']}",
        title="Updated Metadata"
    ))

    # Upload
    console.print("\n[yellow]Upload to YouTube? (y/n)[/yellow] ", end="")
    # For automation, just proceed

    uploader = YouTubeUploader()
    if not uploader.authenticate():
        console.print("[red]Authentication failed[/red]")
        return 1

    console.print("\n[bold green]Uploading...[/bold green]")
    video_id = uploader.upload(
        video_path="output/videos/starfall_valley_music_only.mp4",
        title=metadata["title"],
        description=metadata["description"],
        tags=metadata["tags"],
        category=metadata["category"],
        privacy="unlisted",
        thumbnail_path=str(thumbnail_path),
        made_for_kids=False,  # NOT set to True
    )

    if video_id:
        console.print(f"\n[bold green]Uploaded![/bold green]")
        console.print(f"URL: https://www.youtube.com/watch?v={video_id}")
    else:
        console.print("[red]Upload failed[/red]")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
