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
import click
from rich.console import Console
from selenium.webdriver.common.by import By

from src.config import load_config, save_config, AppConfig
from src.models import Scene, ImageFormat
from src.queue_manager import QueueManager, create_sample_csv
from src.whisk_controller import test_whisk_connection, WhiskController

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


if __name__ == "__main__":
    cli()
