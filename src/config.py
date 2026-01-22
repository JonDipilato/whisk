"""Configuration management for Whisk Automation."""

import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class BrowserConfig(BaseModel):
    """Browser configuration."""
    headless: bool = False
    slow_mo: int = 100
    user_data_dir: Optional[str] = None


class PathsConfig(BaseModel):
    """File paths configuration."""
    environments: str = "./data/environments"
    characters: str = "./data/characters"
    output: str = "./output"
    scenes_file: str = "./data/scenes.csv"


class GenerationConfig(BaseModel):
    """Image generation settings."""
    images_per_prompt: int = 4
    batches_per_scene: int = 2
    image_format: str = "landscape"
    download_timeout: int = 60


class QueueConfig(BaseModel):
    """Queue behavior settings."""
    retry_on_failure: bool = True
    max_retries: int = 3
    delay_between_scenes: int = 5


class AppConfig(BaseModel):
    """Main application configuration."""
    whisk_url: str = "https://labs.google.com/fx/tools/whisk"
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    queue: QueueConfig = Field(default_factory=QueueConfig)


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """Load configuration from JSON file."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.json"

    if not config_path.exists():
        config = AppConfig()
        save_config(config, config_path)
        return config

    with open(config_path, "r") as f:
        data = json.load(f)

    return AppConfig(**data)


def save_config(config: AppConfig, config_path: Optional[Path] = None) -> None:
    """Save configuration to JSON file."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.json"

    with open(config_path, "w") as f:
        json.dump(config.model_dump(), f, indent=2)
