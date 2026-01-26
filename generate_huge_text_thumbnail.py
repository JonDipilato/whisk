#!/usr/bin/env python3
"""Generate thumbnail with harmonious but scroll-stopping colors."""

import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table

from PIL import Image, ImageDraw, ImageFont

console = Console()

def generate_color_combo(img_path, text, font, colors, name, out_path):
    """Generate thumbnail with specific color combo."""
    img = Image.open(img_path)
    img = img.resize((1280, 720), Image.Resampling.LANCZOS)

    # Dark overlay
    for _ in range(3):
        overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 50))
        img.paste(overlay, (0, 0), overlay)
    img = img.convert("RGB")

    draw = ImageDraw.Draw(img)

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (1280 - text_width) // 2
    y = 50

    # Apply color combo
    for thickness, color in colors:
        draw.text((x - thickness, y + thickness), text, font=font, fill=color)

    # Save
    img.save(out_path, "PNG")
    return out_path

# Extract frame first
video_path = Path("output/videos/starfall_valley_narrated.mp4")
temp_frame = Path("output/thumbnails/temp_frame.png")

subprocess.run([
    "ffmpeg", "-y", "-ss", "00:00:12", "-i", str(video_path),
    "-vframes", "1", "-q:v", "2", str(temp_frame)
], capture_output=True)

# Load font
font = None
for font_path in ["C:\\Windows\\Fonts\\impact.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"]:
    try:
        font = ImageFont.truetype(font_path, 180)
        break
    except:
        pass

if not font:
    font = ImageFont.load_default()

text = "STARFALL VALLEY"

# Color combos to try
combos = [
    (
        "Classic White",
        [(15, (0, 0, 0)), (8, (50, 50, 50)), (4, (100, 100, 100)), (0, (255, 255, 255))]
    ),
    (
        "Golden Amber",
        [(15, (0, 0, 0)), (10, (100, 50, 0)), (6, (200, 120, 0)), (2, (255, 200, 100)), (0, (255, 255, 220))]
    ),
    (
        "Electric Blue",
        [(15, (0, 0, 0)), (10, (0, 50, 100)), (6, (0, 120, 200)), (2, (100, 200, 255)), (0, (200, 230, 255))]
    ),
    (
        "Bright Yellow",
        [(15, (0, 0, 0)), (10, (80, 60, 0)), (6, (150, 120, 0)), (2, (230, 200, 0)), (0, (255, 255, 200))]
    ),
    (
        "Sunset Orange",
        [(15, (0, 0, 0)), (10, (100, 30, 0)), (6, (200, 80, 0)), (2, (255, 140, 50)), (0, (255, 200, 150))]
    ),
    (
        "Soft Pink",
        [(15, (0, 0, 0)), (10, (80, 20, 40)), (6, (150, 40, 80)), (2, (220, 100, 150)), (0, (255, 180, 220))]
    ),
]

# Generate options
table = Table(title="Color Combo Options")
table.add_column("Option", style="cyan")
table.add_column("Name", style="magenta")
table.add_column("Preview", style="yellow")

console.print("\n[bold]Generating color options...[/bold]\n")

for i, (name, colors) in enumerate(combos, 1):
    out_path = Path(f"output/thumbnails/option_{i}_{name.replace(' ', '_')}.png")
    generate_color_combo(temp_frame, text, font, colors, name, out_path)
    table.add_row(str(i), name, f"output/thumbnails/option_{i}_{name.replace(' ', '_')}.png")

console.print(table)
console.print("\n[bold]Pick one to use as main thumbnail![/bold]")
console.print("[dim]Or tell me which color scheme you prefer and I'll regenerate[/dim]")

temp_frame.unlink()
