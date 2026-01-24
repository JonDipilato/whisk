"""Music library management module for background music sourcing and organization."""

import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn

from src.config import AppConfig, load_config


console = Console()


class MusicCategory(str, Enum):
    """Music categories for different moods."""
    AMBIENT = "ambient"
    CALM = "calm"
    UPBEAT = "upbeat"
    DRAMATIC = "dramatic"
    NATURE = "nature"
    PIANO = "piano"
    ORCHESTRAL = "orchestral"
    LULLABY = "lullaby"


@dataclass
class MusicTrack:
    """A music track in the library."""
    path: Path
    name: str
    category: MusicCategory
    duration: float = 0.0
    artist: str = ""
    url: str = ""
    tags: List[str] = field(default_factory=list)

    @property
    def exists(self) -> bool:
        return self.path.exists()

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "name": self.name,
            "category": self.category.value,
            "duration": self.duration,
            "artist": self.artist,
            "url": self.url,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MusicTrack":
        return cls(
            path=Path(data["path"]),
            name=data["name"],
            category=MusicCategory(data["category"]),
            duration=data.get("duration", 0.0),
            artist=data.get("artist", ""),
            url=data.get("url", ""),
            tags=data.get("tags", []),
        )


class MusicLibrary:
    """Manage local music library for video backgrounds."""

    def __init__(self, config: Optional[AppConfig] = None):
        """Initialize the music library.

        Args:
            config: Application configuration. Uses default if not provided.
        """
        self.config = config or load_config()
        self.library_path = Path(self.config.music_sources.local_library)
        self.index_path = self.library_path / "index.json"
        self.tracks: Dict[str, MusicTrack] = {}

        self._load_index()

    def _load_index(self) -> None:
        """Load track index from disk."""
        if self.index_path.exists():
            try:
                with open(self.index_path, "r") as f:
                    data = json.load(f)
                    for name, track_data in data.get("tracks", {}).items():
                        self.tracks[name] = MusicTrack.from_dict(track_data)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load music index: {e}[/yellow]")
        else:
            self._scan_library()

    def _save_index(self) -> None:
        """Save track index to disk."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "1.0",
            "tracks": {name: track.to_dict() for name, track in self.tracks.items()},
        }

        with open(self.index_path, "w") as f:
            json.dump(data, f, indent=2)

    def _scan_library(self) -> int:
        """Scan library directory for music files.

        Returns:
            Number of tracks found.
        """
        if not self.library_path.exists():
            return 0

        audio_extensions = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
        found = 0

        for category in MusicCategory:
            category_dir = self.library_path / category.value
            if not category_dir.exists():
                continue

            for file_path in category_dir.glob("*"):
                if file_path.suffix.lower() not in audio_extensions:
                    continue

                name = file_path.stem
                if name not in self.tracks:
                    self.tracks[name] = MusicTrack(
                        path=file_path,
                        name=name,
                        category=category,
                    )
                    found += 1

        # Also scan root library for uncategorized tracks
        for file_path in self.library_path.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                name = file_path.stem
                if name not in self.tracks:
                    self.tracks[name] = MusicTrack(
                        path=file_path,
                        name=name,
                        category=MusicCategory.AMBIENT,
                    )
                    found += 1

        if found > 0:
            self._save_index()

        return found

    def get_track(self, name: str) -> Optional[MusicTrack]:
        """Get a track by name.

        Args:
            name: Track name.

        Returns:
            MusicTrack if found, None otherwise.
        """
        return self.tracks.get(name)

    def find_tracks(
        self,
        category: Optional[MusicCategory] = None,
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
        tags: Optional[List[str]] = None,
    ) -> List[MusicTrack]:
        """Find tracks matching criteria.

        Args:
            category: Filter by category.
            min_duration: Minimum duration in seconds.
            max_duration: Maximum duration in seconds.
            tags: Filter by tags.

        Returns:
            List of matching tracks.
        """
        results = []

        for track in self.tracks.values():
            if not track.exists:
                continue

            if category and track.category != category:
                continue

            if min_duration and track.duration < min_duration:
                continue

            if max_duration and track.duration > max_duration:
                continue

            if tags:
                if not any(tag in track.tags for tag in tags):
                    continue

            results.append(track)

        return results

    def get_random_track(self, category: Optional[MusicCategory] = None) -> Optional[MusicTrack]:
        """Get a random track from the library.

        Args:
            category: Optional category filter.

        Returns:
            Random track or None if library is empty.
        """
        import random

        tracks = self.find_tracks(category=category)
        return random.choice(tracks) if tracks else None

    def get_best_track(
        self,
        category: Optional[MusicCategory] = None,
        target_duration: Optional[float] = None,
    ) -> Optional[MusicTrack]:
        """Get the best matching track for a video.

        Args:
            category: Desired category.
            target_duration: Target video duration.

        Returns:
            Best matching track or None.
        """
        tracks = self.find_tracks(category=category)

        if not tracks:
            return None

        if target_duration is None:
            return tracks[0]

        # Find track closest to target duration (at or above)
        suitable = [t for t in tracks if t.duration >= target_duration]
        if suitable:
            return min(suitable, key=lambda t: t.duration)

        # Fallback: longest track
        return max(tracks, key=lambda t: t.duration)

    def add_track(
        self,
        path: Path,
        name: Optional[str] = None,
        category: MusicCategory = MusicCategory.AMBIENT,
        artist: str = "",
        tags: Optional[List[str]] = None,
    ) -> MusicTrack:
        """Add a track to the library.

        Args:
            path: Path to the audio file.
            name: Track name (defaults to filename).
            category: Music category.
            artist: Artist name.
            tags: Optional tags.

        Returns:
            Added MusicTrack.
        """
        path = Path(path)
        name = name or path.stem

        track = MusicTrack(
            path=path,
            name=name,
            category=category,
            artist=artist,
            tags=tags or [],
        )

        self.tracks[name] = track
        self._save_index()

        console.print(f"[green]Added track: {name} ({category.value})[/green]")
        return track

    def remove_track(self, name: str) -> bool:
        """Remove a track from the library index.

        Args:
            name: Track name.

        Returns:
            True if removed, False if not found.
        """
        if name in self.tracks:
            del self.tracks[name]
            self._save_index()
            return True
        return False

    def list_tracks(self, category: Optional[MusicCategory] = None) -> List[MusicTrack]:
        """List all tracks in the library.

        Args:
            category: Optional category filter.

        Returns:
            List of tracks.
        """
        if category:
            return self.find_tracks(category=category)
        return list(self.tracks.values())

    def print_library_status(self) -> None:
        """Print a summary of the library."""
        console.print("\n[bold cyan]Music Library Status[/bold cyan]\n")

        if not self.tracks:
            console.print("[yellow]No tracks in library[/yellow]")
            console.print(f"\nLibrary path: {self.library_path}")
            return

        # Count by category
        category_counts = {}
        total_duration = 0

        for track in self.tracks.values():
            category_counts[track.category.value] = category_counts.get(track.category.value, 0) + 1
            total_duration += track.duration

        console.print(f"Total tracks: {len(self.tracks)}")
        console.print(f"Total duration: {total_duration / 60:.1f} minutes")
        console.print(f"Library path: {self.library_path}\n")

        console.print("[bold]Tracks by category:[/bold]")
        for category, count in sorted(category_counts.items()):
            console.print(f"  {category}: {count}")

    def ensure_directories(self) -> None:
        """Create library directory structure."""
        self.library_path.mkdir(parents=True, exist_ok=True)

        for category in MusicCategory:
            category_dir = self.library_path / category.value
            category_dir.mkdir(exist_ok=True)

        console.print(f"[green]Library directories created at: {self.library_path}[/green]")


class PixabayMusicClient:
    """Client for downloading royalty-free music from Pixabay."""

    BASE_URL = "https://pixabay.com/api/"
    MUSIC_URL = "https://pixabay.com/music/search/"

    def __init__(self, api_key: str = ""):
        """Initialize the Pixabay client.

        Args:
            api_key: Pixabay API key (optional for browsing).
        """
        self.api_key = api_key

        if not REQUESTS_AVAILABLE:
            console.print("[yellow]Warning: requests not installed. Install with: pip install requests[/yellow]")

    def search_music(
        self,
        query: str = "ambient",
        category: Optional[str] = None,
        duration_min: Optional[int] = None,
        duration_max: Optional[int] = None,
    ) -> List[Dict]:
        """Search for music on Pixabay.

        Note: This requires a browser scraper as Pixabay doesn't have a public API for music.
        This is a placeholder for future implementation.

        Args:
            query: Search query.
            category: Music category.
            duration_min: Minimum duration in seconds.
            duration_max: Maximum duration in seconds.

        Returns:
            List of track metadata.
        """
        console.print("[yellow]Pixabay music search requires web scraping.[/yellow]")
        console.print("[yellow]Please download music manually from: https://pixabay.com/music/[/yellow]")
        return []

    def get_download_url(self, track_id: str) -> Optional[str]:
        """Get download URL for a track (placeholder).

        Args:
            track_id: Pixabay track ID.

        Returns:
            Download URL or None.
        """
        return None


class SunoAIClient:
    """Client for AI-generated music via Suno AI."""

    def __init__(self, api_key: str = ""):
        """Initialize the Suno AI client.

        Args:
            api_key: Suno AI API key.
        """
        self.api_key = api_key
        self.base_url = "https://api.suno.ai/v1"

        if not REQUESTS_AVAILABLE:
            console.print("[yellow]Warning: requests not installed. Install with: pip install requests[/yellow]")

    def generate_music(
        self,
        prompt: str,
        duration: int = 120,
        style: str = "ambient",
    ) -> Optional[str]:
        """Generate AI music using Suno (placeholder).

        Args:
            prompt: Description of desired music.
            duration: Duration in seconds.
            style: Music style.

        Returns:
            URL to generated audio or None.
        """
        console.print("[yellow]Suno AI integration requires API access.[/yellow]")
        console.print("[yellow]Visit: https://suno.ai/ for AI music generation[/yellow]")
        return None


def setup_music_library(
    library_path: Optional[Path] = None,
    config: Optional[AppConfig] = None,
) -> MusicLibrary:
    """Set up and initialize the music library.

    Args:
        library_path: Custom library path.
        config: Application configuration.

    Returns:
        Initialized MusicLibrary instance.
    """
    library = MusicLibrary(config)

    if library_path:
        library.library_path = Path(library_path)

    library.ensure_directories()
    return library


def download_free_music(
    output_dir: Path,
    category: MusicCategory = MusicCategory.AMBIENT,
) -> List[Path]:
    """Download free royalty-free music (placeholder for future implementation).

    Args:
        output_dir: Output directory for downloads.
        category: Music category to download.

    Returns:
        List of downloaded file paths.
    """
    console.print("[yellow]Automatic music download requires API integration.[/yellow]")
    console.print(f"[cyan]Recommended free sources:[/cyan]")
    console.print("  - Pixabay: https://pixabay.com/music/")
    console.print("  - Freesound: https://freesound.org/")
    console.print("  - incompetech: https://incompetech.com/music/royalty-free/")
    console.print("  - Bensound: https://www.bensound.com/")

    return []
