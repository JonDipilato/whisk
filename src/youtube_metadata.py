"""YouTube metadata generation module for titles, descriptions, and tags."""

import json
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from rich.console import Console

from src.config import AppConfig, load_config
from src.models import VideoMetadata, Chapter


console = Console()


TITLE_TEMPLATES = [
    "{character_name}'s {theme} Adventure | {style} Bedtime Story for Kids",
    "This {style} Story Will Help Your Child Sleep | {character_name}'s {theme} Journey",
    "{number} {theme} Stories for Kids | {style} Animation Bedtime Story",
    "{character_name} and the {theme} | Peaceful {style} Story for Children",
    "Calming {theme} Story | {style} Bedtime Story for Kids",
    "{character_name}'s Magical {theme} Adventure | {style} Animation",
    "Sleep Story: {character_name}'s {theme} Journey | {style} Style",
    "Peaceful {theme} Bedtime Story | {style} Animation for Kids",
]

TITLE_HOOKS = [
    "This Will Help Your Child Sleep",
    "Peaceful Bedtime Story",
    "Calming Animation for Kids",
    "Beautiful {style} Story",
    "Magical Journey",
    "Gentle Bedtime Story",
    "Relaxing Animation",
]

CHARACTER_NAMES = [
    "Grandmother", "Little Fox", "Brave Bunny", "Wise Owl", "Kind Bear",
    "Gentle Deer", "Curious Squirrel", "Friendly Whale", "Happy Dolphin",
    "Loving Mother", "Caring Father", "Sweet Sister", "Kind Brother",
]

THEMES = [
    "Garden", "Forest Adventure", "Ocean Journey", "Mountain Discovery",
    "Magical Kingdom", "Starlight", "Moonlit Path", "Sunny Meadow",
    "Cozy Cottage", "Winter Wonderland", "Spring Bloom", "Autumn Leaves",
    "Beach Day", "Rainy Day", "Snowy Adventure", "Flower Field",
]

STYLE_TAGS = {
    "ghibli": ["ghibli style", "studio ghibli", "ghibli aesthetic", "anime style"],
    "pixar": ["pixar style", "3d animation", "pixar aesthetic", "cgi animation"],
    "watercolor": ["watercolor", "hand drawn", "watercolor illustration", "art style"],
    "storybook": ["storybook", "illustration style", "children's book", "picture book"],
}


@dataclass
class MetadataConfig:
    """Configuration for metadata generation."""
    character_name: str = "Grandmother"
    theme: str = "Garden Adventure"
    style: str = "ghibli"
    number: Optional[int] = None
    summary: Optional[str] = None
    lesson: Optional[str] = None
    schedule: str = "Tuesday & Friday"


@dataclass
class ChapterTimestamp:
    """A chapter with timestamp for YouTube description."""
    title: str
    timestamp: str  # Format: "MM:SS" or "HH:MM:SS"

    def to_dict(self) -> dict:
        return {"title": self.title, "timestamp": self.timestamp}

    def to_line(self) -> str:
        return f"{self.timestamp} - {self.title}"


def format_timestamp(seconds: float) -> str:
    """Convert seconds to YouTube timestamp format.

    Args:
        seconds: Time in seconds.

    Returns:
        Formatted timestamp string (MM:SS or HH:MM:SS).
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def generate_title(
    character_name: str,
    theme: str,
    style: str = "ghibli",
    number: Optional[int] = None,
    custom_template: Optional[str] = None,
) -> str:
    """Generate a YouTube-optimized video title.

    Args:
        character_name: Name of the main character.
        theme: Story theme (e.g., "Garden Adventure").
        style: Visual style (e.g., "ghibli", "pixar").
        number: Optional number for numbered titles.
        custom_template: Optional custom title template.

    Returns:
        Generated video title.
    """
    style_name = style.title() if style else "Animated"

    if custom_template:
        return custom_template.format(
            character_name=character_name,
            theme=theme,
            style=style_name,
            number=number or "",
        )

    # Use a random template for variety
    template = random.choice(TITLE_TEMPLATES)

    title = template.format(
        character_name=character_name,
        theme=theme,
        style=style_name,
        number=number or "",
    )

    # Clean up double spaces
    title = " ".join(title.split())

    return title


def generate_description(
    title: str,
    character_name: str,
    theme: str,
    style: str,
    summary: Optional[str] = None,
    lesson: Optional[str] = None,
    channel_name: str = "Peaceful Stories",
    channel_handle: str = "peacefulstories",
    schedule: str = "Tuesday & Friday",
    chapters: Optional[List[ChapterTimestamp]] = None,
    video_duration: Optional[float] = None,
) -> str:
    """Generate a YouTube-optimized video description.

    Args:
        title: Video title.
        character_name: Main character name.
        theme: Story theme.
        style: Visual style.
        summary: Optional story summary.
        lesson: Optional lesson learned.
        channel_name: Channel name.
        channel_handle: Channel handle (without @).
        schedule: Upload schedule.
        chapters: Optional list of chapter timestamps.
        video_duration: Video duration in seconds.

    Returns:
        Generated video description.
    """
    lines = []

    # Hook (first 2 lines - most important for SEO)
    hook = f"Watch {character_name} learn {theme.lower()} in this beautiful {style} bedtime story for kids."
    lines.append(hook)
    lines.append("")

    # Summary
    if summary:
        lines.append(f"{summary}")
    else:
        lines.append(
            f"A peaceful {style} animated story perfect for bedtime, nap time, "
            f"or any time your child needs to relax."
        )
    lines.append("")

    # Chapter timestamps
    if chapters:
        lines.append("TIMESTAMPS:")
        for chapter in chapters:
            lines.append(f"{chapter.timestamp} - {chapter.title}")
        lines.append("")

    # Lesson learned
    if lesson:
        lines.append(f"STORY SUMMARY:")
        lines.append(f"In this story, {character_name} learns about {lesson.lower()}.")
        lines.append("")

    # Channel info
    lines += [
        f"ABOUT THIS CHANNEL:",
        f"Welcome to {channel_name}! We create beautiful {style} animated "
        f"stories for children. New videos every {schedule}.",
        "",
        f"SUBSCRIBE for more: https://www.youtube.com/@{channel_handle}?sub_confirmation=1",
        "",
    ]

    # Tags section (for reference, not visible)
    lines.append("TAGS:")
    base_tags = [
        f"bedtime stories for kids",
        f"{style} stories",
        f"animated stories",
        f"calming stories for sleep",
        f"children's stories",
        f"kids bedtime stories",
        f"peaceful stories",
    ]
    lines.extend([f"#{tag.replace(' ', '')}" for tag in base_tags])

    return "\n".join(lines)


def generate_tags(
    style: str,
    theme: str,
    character_name: str,
    additional_tags: Optional[List[str]] = None,
) -> List[str]:
    """Generate YouTube tags for the video.

    Args:
        style: Visual style.
        theme: Story theme.
        character_name: Main character.
        additional_tags: Optional additional tags.

    Returns:
        List of tags (comma-separated for YouTube upload).
    """
    # Primary tags
    tags = [
        f"{style} bedtime stories for kids",
        f"{style} stories for children",
        f"animated bedtime stories",
        f"calming stories for kids",
        f"sleep stories for children",
        f"peaceful bedtime stories",
    ]

    # Secondary tags
    tags.extend([
        "children's stories",
        "animated stories",
        "kids stories",
        "bedtime stories",
        "story for kids",
        "calming stories",
    ])

    # Style-specific tags
    if style.lower() in STYLE_TAGS:
        tags.extend(STYLE_TAGS[style.lower()])

    # Character and theme tags
    tags.append(f"{character_name} stories")
    tags.append(f"{theme} story")

    # Additional tags
    if additional_tags:
        tags.extend(additional_tags)

    # Remove duplicates while preserving order
    seen = set()
    unique_tags = []
    for tag in tags:
        lowered = tag.lower()
        if lowered not in seen:
            seen.add(lowered)
            unique_tags.append(tag)

    return unique_tags


def generate_chapters(
    segments: List[Dict],
    duration_per_image: float = 4.0,
    transition_time: float = 0.5,
) -> List[ChapterTimestamp]:
    """Generate chapter timestamps from video segments.

    Args:
        segments: List of segment dictionaries with scene_id and optional title.
        duration_per_image: Duration of each image.
        transition_time: Transition duration between scenes.

    Returns:
        List of chapter timestamps.
    """
    chapters = []
    current_time = 0.0

    for i, segment in enumerate(segments):
        scene_id = segment.get("scene_id", i + 1)
        title = segment.get("title", f"Scene {scene_id}")
        image_count = segment.get("image_count", 1)

        segment_duration = (image_count * duration_per_image) + transition_time

        timestamp = format_timestamp(current_time)
        chapters.append(ChapterTimestamp(title=title, timestamp=timestamp))

        current_time += segment_duration

    return chapters


def generate_chapters_from_scenes(
    scenes: List[Dict],
    scenes_config: Optional[Dict] = None,
) -> List[ChapterTimestamp]:
    """Generate chapter timestamps from scene data.

    Args:
        scenes: List of scene dictionaries.
        scenes_config: Optional config with duration_per_image, etc.

    Returns:
        List of chapter timestamps.
    """
    if scenes_config is None:
        scenes_config = {"duration_per_image": 4.0, "transition_time": 0.5}

    chapters = []
    current_time = 0.0
    duration = scenes_config.get("duration_per_image", 4.0)

    for scene in scenes:
        scene_id = scene.get("scene_id", 0)
        prompt = scene.get("prompt", "")
        image_count = scene.get("image_count", 1)

        # Generate chapter title from prompt
        title = _extract_chapter_title(prompt, scene_id)

        # Create timestamp
        timestamp = format_timestamp(current_time)
        chapters.append(ChapterTimestamp(title=title, timestamp=timestamp))

        # Advance time
        current_time += image_count * duration

    return chapters


def _extract_chapter_title(prompt: str, scene_id: int) -> str:
    """Extract a short chapter title from a prompt.

    Args:
        prompt: Scene prompt text.
        scene_id: Scene number.

    Returns:
        Short chapter title (30 chars max).
    """
    # Take first meaningful words
    words = prompt.strip().split()
    title_words = []

    for word in words[:8]:
        if word.lower() in ["a", "an", "the", "in", "on", "at", "to", "with"]:
            continue
        title_words.append(word)
        if len(" ".join(title_words)) > 25:
            break

    if title_words:
        return " ".join(title_words).capitalize()

    return f"Scene {scene_id}"


class YouTubeMetadataGenerator:
    """Generate complete YouTube metadata packages."""

    def __init__(self, config: Optional[AppConfig] = None):
        """Initialize the metadata generator.

        Args:
            config: Application configuration. Uses default if not provided.
        """
        self.config = config or load_config()
        self.youtube_config = self.config.youtube

    def generate_all_metadata(
        self,
        character_name: str,
        theme: str,
        style: str = "ghibli",
        summary: Optional[str] = None,
        lesson: Optional[str] = None,
        chapters: Optional[List[ChapterTimestamp]] = None,
        number: Optional[int] = None,
        custom_title: Optional[str] = None,
    ) -> VideoMetadata:
        """Generate complete YouTube metadata package.

        Args:
            character_name: Main character name.
            theme: Story theme.
            style: Visual style.
            summary: Story summary.
            lesson: Lesson learned.
            chapters: Chapter timestamps.
            number: Optional number for titles.
            custom_title: Custom title if provided.

        Returns:
            Complete VideoMetadata object.
        """
        # Generate title
        title = custom_title or generate_title(
            character_name=character_name,
            theme=theme,
            style=style,
            number=number,
        )

        # Generate description
        description = generate_description(
            title=title,
            character_name=character_name,
            theme=theme,
            style=style,
            summary=summary,
            lesson=lesson,
            channel_name=self.youtube_config.channel_name,
            channel_handle=self.youtube_config.channel_handle,
            schedule=self.youtube_config.upload_schedule,
            chapters=chapters,
        )

        # Generate tags
        tags = generate_tags(
            style=style,
            theme=theme,
            character_name=character_name,
            additional_tags=self.youtube_config.default_tags,
        )

        # Convert chapters to dict format
        chapter_dict = {}
        if chapters:
            chapter_dict = {c.timestamp: c.title for c in chapters}

        metadata = VideoMetadata(
            title=title,
            description=description,
            tags=tags,
            category=self.youtube_config.default_category,
            privacy_status=self.youtube_config.default_privacy,
            chapter_timestamps=chapter_dict,
        )

        return metadata

    def save_metadata(self, metadata: VideoMetadata, output_path: Path) -> Path:
        """Save metadata to a JSON file.

        Args:
            metadata: VideoMetadata object.
            output_path: Output file path.

        Returns:
            Path to saved metadata file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "title": metadata.title,
            "description": metadata.description,
            "tags": metadata.tags,
            "category": metadata.category,
            "privacy_status": metadata.privacy_status,
            "chapter_timestamps": metadata.chapter_timestamps,
            "generated_at": datetime.now().isoformat(),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        console.print(f"[green]Metadata saved: {output_path}[/green]")
        return output_path

    def load_metadata(self, metadata_path: Path) -> VideoMetadata:
        """Load metadata from a JSON file.

        Args:
            metadata_path: Path to metadata JSON file.

        Returns:
            VideoMetadata object.
        """
        metadata_path = Path(metadata_path)

        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return VideoMetadata(
            title=data.get("title", ""),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            category=data.get("category", "Education"),
            privacy_status=data.get("privacy_status", "public"),
            chapter_timestamps=data.get("chapter_timestamps", {}),
        )

    def print_metadata_preview(self, metadata: VideoMetadata) -> None:
        """Print a preview of the metadata.

        Args:
            metadata: VideoMetadata to preview.
        """
        console.print("\n[bold cyan]=== YouTube Metadata Preview ===[/bold cyan]\n")

        console.print(f"[bold yellow]Title:[/bold yellow] {metadata.title}")
        console.print(f"[bold yellow]Tags:[/bold yellow] {', '.join(metadata.tags[:10])}...")
        console.print(f"[bold yellow]Category:[/bold yellow] {metadata.category}")
        console.print(f"[bold yellow]Privacy:[/bold yellow] {metadata.privacy_status}")

        console.print(f"\n[bold yellow]Description:[/bold yellow]")
        console.print(metadata.description[:500] + "..." if len(metadata.description) > 500 else metadata.description)

        if metadata.chapter_timestamps:
            console.print(f"\n[bold yellow]Chapters:[/bold yellow]")
            for timestamp, title in list(metadata.chapter_timestamps.items())[:5]:
                console.print(f"  {timestamp} - {title}")
            if len(metadata.chapter_timestamps) > 5:
                console.print(f"  ... and {len(metadata.chapter_timestamps) - 5} more")

        console.print()


def generate_metadata_package(
    character_name: str,
    theme: str,
    style: str = "ghibli",
    output_path: Optional[Path] = None,
    config: Optional[AppConfig] = None,
    **kwargs
) -> VideoMetadata:
    """Convenience function to generate and optionally save metadata.

    Args:
        character_name: Main character name.
        theme: Story theme.
        style: Visual style.
        output_path: Optional path to save metadata JSON.
        config: Application configuration.
        **kwargs: Additional arguments for metadata generation.

    Returns:
        VideoMetadata object.
    """
    generator = YouTubeMetadataGenerator(config)
    metadata = generator.generate_all_metadata(
        character_name=character_name,
        theme=theme,
        style=style,
        **kwargs
    )

    if output_path:
        generator.save_metadata(metadata, output_path)

    return metadata
