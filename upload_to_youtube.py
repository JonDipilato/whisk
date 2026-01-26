#!/usr/bin/env python3
"""Upload video to YouTube with metadata and thumbnail.

Usage:
    python upload_to_youtube.py
"""

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from src.youtube_uploader import YouTubeUploader

console = Console()


def main():
    console.print("[bold cyan]YouTube Video Upload[/bold cyan]\n")

    # Paths
    video_path = Path("output/videos/starfall_valley_music_only.mp4")
    metadata_path = Path("output/videos/starfall_valley_music_only_metadata.json")
    thumbnail_path = Path("output/thumbnails/starfall_valley_music_only_thumbnail.png")

    # Verify files exist
    missing = []
    if not video_path.exists():
        missing.append(f"Video: {video_path}")
    if not metadata_path.exists():
        missing.append(f"Metadata: {metadata_path}")
    if not thumbnail_path.exists():
        missing.append(f"Thumbnail: {thumbnail_path}")

    if missing:
        console.print("[red]Missing files:[/red]")
        for f in missing:
            console.print(f"  - {f}")
        return 1

    # Load metadata
    with open(metadata_path) as f:
        metadata = json.load(f)

    console.print(Panel.fit(
        f"[bold]Title:[/bold] {metadata['title']}\n"
        f"[bold]Video:[/bold] {video_path.name} ({video_path.stat().st_size // 1024 // 1024} MB)\n"
        f"[bold]Thumbnail:[/bold] {thumbnail_path.name}\n"
        f"[bold]Privacy:[/bold] unlisted",
        title="Upload Summary"
    ))

    # Initialize uploader
    uploader = YouTubeUploader()

    # Authenticate
    console.print("\n[yellow]Authenticating with YouTube...[/yellow]")
    if not uploader.authenticate():
        console.print("[red]Authentication failed![/red]")
        return 1

    # Upload
    console.print("\n[bold green]Starting upload...[/bold green]")
    console.print("[dim]This may take several minutes for a 42 MB file[/dim]\n")

    video_id = uploader.upload(
        video_path=str(video_path),
        title=metadata['title'],
        description=metadata['description'],
        tags=metadata['tags'],
        category=metadata.get('category', 'Education'),
        privacy="unlisted",  # Upload as unlisted
        thumbnail_path=str(thumbnail_path),
        made_for_kids=True,
    )

    if video_id:
        console.print(f"\n[bold green]Upload successful![/bold green]")
        console.print(f"[bold cyan]Video ID:[/bold cyan] {video_id}")
        console.print(f"[bold cyan]URL:[/bold cyan] https://www.youtube.com/watch?v={video_id}")
        return 0
    else:
        console.print("\n[red]Upload failed![/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
