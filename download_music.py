"""
=================================================================
  MUSIC LIBRARY DOWNLOADER

  Downloads royalty-free ambient music tracks for video backgrounds.
  Uses Pixabay API to search and download calm/ambient tracks.

  SETUP:
  1. Get a free API key at: https://pixabay.com/api/docs/
  2. Set it in config.json under music_sources.pixabay_api_key
     OR pass via --api-key flag

  USAGE:
     python download_music.py
     python download_music.py --query "ambient nature calm"
     python download_music.py --count 10
     python download_music.py --api-key YOUR_KEY
     python download_music.py --from-url "https://cdn.pixabay.com/audio/..."
=================================================================
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_config
from src.music_library import (
    MusicLibrary, MusicCategory, PixabayMusicClient, setup_music_library
)

try:
    from rich.console import Console
    console = Console()
except ImportError:
    class Console:
        def print(self, msg): print(msg)
    console = Console()


def download_from_pixabay(api_key: str, query: str, count: int, output_dir: Path):
    """Search Pixabay and download ambient tracks."""
    client = PixabayMusicClient(api_key=api_key)

    console.print(f"\n[cyan]Searching Pixabay for: '{query}' (up to {count} tracks)...[/cyan]")
    downloaded = client.download_batch(
        query=query,
        output_dir=output_dir,
        category=MusicCategory.CALM,
        count=count,
    )

    if downloaded:
        console.print(f"\n[green]Downloaded {len(downloaded)} tracks to {output_dir}/calm/[/green]")
    else:
        console.print("\n[yellow]No tracks downloaded. Try a different query or check your API key.[/yellow]")
        console.print("[cyan]You can also manually download from:[/cyan]")
        console.print("  https://pixabay.com/music/search/ambient%20calm/")
        console.print(f"  Place MP3/WAV files in: {output_dir}/calm/")

    return downloaded


def download_from_url(url: str, output_dir: Path, name: str = ""):
    """Download a single track from a direct URL."""
    client = PixabayMusicClient()

    calm_dir = output_dir / "calm"
    calm_dir.mkdir(parents=True, exist_ok=True)

    if not name:
        name = Path(url).stem[:40] or "track"
    ext = Path(url).suffix or ".mp3"
    output_path = calm_dir / f"{name}{ext}"

    console.print(f"\n[cyan]Downloading: {url}[/cyan]")
    if client.download_track(url, output_path):
        console.print(f"[green]Saved: {output_path}[/green]")
        return output_path
    return None


def main():
    parser = argparse.ArgumentParser(description="Download royalty-free music for video backgrounds")
    parser.add_argument("--api-key", help="Pixabay API key (overrides config.json)")
    parser.add_argument("--query", default="ambient calm relaxing meditation",
                        help="Search query for Pixabay (default: ambient calm relaxing meditation)")
    parser.add_argument("--count", type=int, default=10,
                        help="Number of tracks to download (default: 10)")
    parser.add_argument("--from-url", help="Download a single track from a direct URL")
    parser.add_argument("--name", default="", help="Name for the downloaded track (with --from-url)")
    parser.add_argument("--status", action="store_true", help="Show current music library status")

    args = parser.parse_args()

    config = load_config()
    output_dir = Path(config.music_sources.local_library)

    # Ensure directory structure exists
    library = setup_music_library(config=config)

    if args.status:
        library.print_library_status()
        return

    if args.from_url:
        download_from_url(args.from_url, output_dir, name=args.name)
        # Rescan library
        library._scan_library()
        library.print_library_status()
        return

    # Get API key
    api_key = args.api_key or config.music_sources.pixabay_api_key
    if not api_key:
        console.print("[red]Pixabay API key required.[/red]")
        console.print("[cyan]Get a free key at: https://pixabay.com/api/docs/[/cyan]")
        console.print("[cyan]Then either:[/cyan]")
        console.print("  1. Set in config.json: music_sources.pixabay_api_key")
        console.print("  2. Pass via: python download_music.py --api-key YOUR_KEY")
        console.print("\n[cyan]Or download manually:[/cyan]")
        console.print("  1. Visit: https://pixabay.com/music/search/ambient%20calm/")
        console.print(f"  2. Place MP3/WAV files in: {output_dir}/calm/")
        console.print("  3. Run: python download_music.py --status")
        return

    download_from_pixabay(api_key, args.query, args.count, output_dir)

    # Rescan library after downloads
    library._scan_library()
    library.print_library_status()


if __name__ == "__main__":
    main()
