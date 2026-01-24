#!/usr/bin/env python3
"""
Master Automation - Single file, full pipeline.

Phase 0: Generate character/scene reference images via Whisk (prompt-only)
Phase 1: Queue 75 scenes
Phase 2: Generate all scene images using character/scene references
Phase 3: Assemble into YouTube-ready video

Usage:
    python master_automation.py                    # Full pipeline
    python master_automation.py --only setup       # Only generate reference images
    python master_automation.py --only generate    # Only scene image generation
    python master_automation.py --only video       # Only video assembly
"""

import os
import sys
import time
import shutil
from pathlib import Path
from datetime import datetime
import argparse

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.config import load_config, AppConfig
from src.queue_manager import QueueManager
from src.models import Scene, ImageFormat, QueueState
from src.pipeline import VideoPipeline, PipelineConfig
from src.audio_generator import AudioGenerator
from src.video_assembler import VideoAssembler
from src.whisk_controller import WhiskController

console = Console()

# ============================================================================
# CHARACTERS & SCENE DESIGN
# ============================================================================

CHARACTERS = {
    "luna": {
        "name": "Luna",
        "prompt": (
            "Anime girl with long silver hair, blue eyes, light blue dress with star patterns, "
            "holding a small lantern, barefoot, gentle smile, Ghibli style, white background"
        ),
        "file": "luna_01.png",
    },
    "kai": {
        "name": "Kai",
        "prompt": (
            "Full body character design sheet, young boy age 13, messy dark brown hair, "
            "warm amber-brown eyes, wearing an earthy green jacket with sewn patches over "
            "a cream shirt, brown shorts, leather boots, a tiny orange fox sitting on his shoulder, "
            "adventurous confident smile, Studio Ghibli anime style, clean white background, "
            "soft lighting, detailed character reference sheet"
        ),
        "file": "kai_01.png",
    },
}

SCENE_ENV = {
    "name": "Starfall Valley",
    "prompt": (
        "Wide landscape panorama of a magical valley at twilight, crystal trees glowing "
        "with soft blue and purple light, floating lily pads hovering above a gentle stream, "
        "stars beginning to fall like slow rain from the sky, distant waterfall of starlight, "
        "fireflies everywhere, lush green grass with bioluminescent flowers, "
        "Studio Ghibli anime style, breathtaking environment, no characters"
    ),
    "file": "starfall_valley.png",
}

# ============================================================================
# 75-SCENE STORY: Luna & Kai in Starfall Valley
# ============================================================================

STORY = {
    "title": "Starfall Valley - Where Stars Come to Rest",
    "style": "ghibli",
    "scenes": [
        # ACT 1: Discovery (scenes 1-15)
        {"id": 1, "prompt": "Twilight sky over a quiet village, first star falling in the distance, warm cottages with glowing windows, Studio Ghibli style"},
        {"id": 2, "prompt": "Young girl with silver hair looking out her bedroom window at the falling star, wonder in her eyes, lantern on her desk, Studio Ghibli style"},
        {"id": 3, "prompt": "Boy with dark hair and fox on shoulder running through village street toward the falling star, excited expression, Studio Ghibli style"},
        {"id": 4, "prompt": "Two young friends meeting at the village gate at dusk, silver-haired girl with lantern and dark-haired boy with fox, Studio Ghibli style"},
        {"id": 5, "prompt": "Two children walking along a forest path at night, lantern lighting the way, fireflies around them, Studio Ghibli style"},
        {"id": 6, "prompt": "Forest path opening up to reveal a hidden valley below, crystal trees glowing blue, stars falling gently, children gasping in awe, Studio Ghibli style"},
        {"id": 7, "prompt": "Children carefully descending a mossy hillside into the glowing valley, stars drifting past them like snow, Studio Ghibli style"},
        {"id": 8, "prompt": "First crystal tree up close, transparent trunk with light pulsing inside, girl reaching out to touch it gently, Studio Ghibli style"},
        {"id": 9, "prompt": "Fox jumping off boy's shoulder to chase a falling star, playful and curious, crystal forest background, Studio Ghibli style"},
        {"id": 10, "prompt": "A fallen star resting in the grass like a small glowing orb, children kneeling beside it in wonder, soft blue light, Studio Ghibli style"},
        {"id": 11, "prompt": "Girl gently picking up the star orb, it pulses warmly in her hands, her face lit with soft blue glow, Studio Ghibli style"},
        {"id": 12, "prompt": "Stream of liquid starlight flowing through the valley, floating lily pads hovering above it, magical atmosphere, Studio Ghibli style"},
        {"id": 13, "prompt": "Boy stepping onto a floating lily pad, balancing carefully, girl watching with amused smile, Studio Ghibli style"},
        {"id": 14, "prompt": "Both children riding floating lily pads down the starlight stream, laughing together, magical journey, Studio Ghibli style"},
        {"id": 15, "prompt": "Lily pads bringing them to a clearing with a massive ancient crystal tree, the heart of the valley, Studio Ghibli style"},

        # ACT 2: The Valley's Magic (scenes 16-30)
        {"id": 16, "prompt": "Enormous ancient crystal tree in center of valley, roots spreading like rivers of light, branches touching the sky, Studio Ghibli style"},
        {"id": 17, "prompt": "Tiny luminous creatures emerging from crystal flowers, curious about the children, moth-like wings glowing, Studio Ghibli style"},
        {"id": 18, "prompt": "Luminous creatures landing on girl's outstretched hands, gentle and trusting, boy watching with soft smile, Studio Ghibli style"},
        {"id": 19, "prompt": "Fox playing with luminous creatures, jumping and twirling, creating trails of light, children laughing, Studio Ghibli style"},
        {"id": 20, "prompt": "Children discovering a garden of star flowers that bloom only at night, each petal a tiny constellation, Studio Ghibli style"},
        {"id": 21, "prompt": "Girl and boy planting a fallen star in the earth, star taking root and beginning to grow, magical moment, Studio Ghibli style"},
        {"id": 22, "prompt": "Small crystal sapling growing from planted star, leaves unfurling with inner light, children watching in amazement, Studio Ghibli style"},
        {"id": 23, "prompt": "Valley creatures gathering around the new sapling, celebrating with swirling light dances, festive atmosphere, Studio Ghibli style"},
        {"id": 24, "prompt": "Boy climbing a crystal tree to get a better view of the valley, girl calling up to him, starlit panorama, Studio Ghibli style"},
        {"id": 25, "prompt": "View from crystal tree top showing entire valley spread below, starfall waterfall in distance, breathtaking vista, Studio Ghibli style"},
        {"id": 26, "prompt": "Children following a path of embedded stars in the ground, leading toward the waterfall, determined expressions, Studio Ghibli style"},
        {"id": 27, "prompt": "Crossing a bridge made of woven crystal vines over a deep ravine, stars falling around them, brave moment, Studio Ghibli style"},
        {"id": 28, "prompt": "Arriving at the base of the starfall waterfall, cascading light instead of water, mist of sparkles, Studio Ghibli style"},
        {"id": 29, "prompt": "Girl holding her lantern up to the waterfall, it responds by glowing brighter, connection between them, Studio Ghibli style"},
        {"id": 30, "prompt": "Behind the waterfall a hidden cave entrance glows with ancient symbols, children exchanging excited glances, Studio Ghibli style"},

        # ACT 3: The Heart of the Valley (scenes 31-45)
        {"id": 31, "prompt": "Children entering the cave behind the waterfall, walls covered in glowing constellation maps, Studio Ghibli style"},
        {"id": 32, "prompt": "Cave opening into a vast underground chamber, ceiling like a private sky full of trapped stars, Studio Ghibli style"},
        {"id": 33, "prompt": "Ancient stone pedestal in center of chamber, a large dim crystal resting on it, the valley's heart stone, Studio Ghibli style"},
        {"id": 34, "prompt": "Girl noticing the heart stone is cracked and fading, valley creatures looking worried, something is wrong, Studio Ghibli style"},
        {"id": 35, "prompt": "Boy finding ancient murals on cave walls showing the valley in full bloom, understanding the history, Studio Ghibli style"},
        {"id": 36, "prompt": "Murals showing how the heart stone powers the entire valley's magic, stars flowing from it like a fountain, Studio Ghibli style"},
        {"id": 37, "prompt": "Girl placing her fallen star orb near the cracked heart stone, blue light reaching toward it, Studio Ghibli style"},
        {"id": 38, "prompt": "Heart stone beginning to absorb the star's energy, crack starting to heal with golden light, Studio Ghibli style"},
        {"id": 39, "prompt": "Boy encouraging the fox to bring more fallen stars from outside, fox running eagerly through cave entrance, Studio Ghibli style"},
        {"id": 40, "prompt": "Luminous creatures joining in, carrying tiny fallen stars in their wings toward the heart stone, teamwork, Studio Ghibli style"},
        {"id": 41, "prompt": "Heart stone glowing stronger as more stars are placed around it, cracks healing one by one, Studio Ghibli style"},
        {"id": 42, "prompt": "Children working together to lift a large fallen star, straining but determined, creatures helping push, Studio Ghibli style"},
        {"id": 43, "prompt": "Large star placed on pedestal next to heart stone, massive surge of light, everyone shielding eyes, Studio Ghibli style"},
        {"id": 44, "prompt": "Heart stone fully restored, brilliant white-blue light flooding the chamber, symbols on walls glowing, Studio Ghibli style"},
        {"id": 45, "prompt": "Wave of magic energy bursting from cave, spreading across entire valley, restoring everything, Studio Ghibli style"},

        # ACT 4: Valley Reborn (scenes 46-60)
        {"id": 46, "prompt": "Children emerging from cave to see valley transformed, brighter than ever, new crystal trees sprouting, Studio Ghibli style"},
        {"id": 47, "prompt": "Crystal trees growing taller and more vibrant, branches reaching toward sky, light flowing through them, Studio Ghibli style"},
        {"id": 48, "prompt": "Stars falling more beautifully now, spiraling down in graceful patterns instead of random drops, Studio Ghibli style"},
        {"id": 49, "prompt": "New flowers blooming across the valley floor, each one a different color of starlight, carpet of light, Studio Ghibli style"},
        {"id": 50, "prompt": "The starfall waterfall now twice as magnificent, rainbow of light cascading down cliff face, Studio Ghibli style"},
        {"id": 51, "prompt": "Hundreds of luminous creatures filling the sky in celebration, creating living constellation patterns, Studio Ghibli style"},
        {"id": 52, "prompt": "Fox dancing with joy among the new star flowers, little orange figure among blue and purple blooms, Studio Ghibli style"},
        {"id": 53, "prompt": "Children sitting together on a crystal root, watching the valley celebrate, peaceful smiles, Studio Ghibli style"},
        {"id": 54, "prompt": "Luminous creatures forming a crown of light above the girl's head in gratitude, she laughs surprised, Studio Ghibli style"},
        {"id": 55, "prompt": "Boy receiving a small crystal seed from the ancient tree as a thank you gift, holding it carefully, Studio Ghibli style"},
        {"id": 56, "prompt": "Valley creatures performing a synchronized light dance, spiraling upward like a tornado of stars, Studio Ghibli style"},
        {"id": 57, "prompt": "Children joining the dance, floating slightly off the ground carried by magic, pure joy, Studio Ghibli style"},
        {"id": 58, "prompt": "Ancient crystal tree at its brightest, sending beams of light into the sky, connecting earth to stars, Studio Ghibli style"},
        {"id": 59, "prompt": "New stars being born from the ancient tree's branches, floating upward to join the sky, beautiful cycle, Studio Ghibli style"},
        {"id": 60, "prompt": "Dawn beginning to lighten the horizon, valley magic becoming softer, golden hour approaching, Studio Ghibli style"},

        # ACT 5: Return Home (scenes 61-75)
        {"id": 61, "prompt": "First light of dawn touching the crystal trees, they shift from blue to warm amber glow, transition, Studio Ghibli style"},
        {"id": 62, "prompt": "Valley creatures gently guiding children back toward the path home, bittersweet farewell beginning, Studio Ghibli style"},
        {"id": 63, "prompt": "Girl hugging a luminous creature goodbye, boy waving to the ancient tree, fox looking back, Studio Ghibli style"},
        {"id": 64, "prompt": "Children climbing back up the hillside, looking back at the valley one more time, memories forming, Studio Ghibli style"},
        {"id": 65, "prompt": "Valley growing smaller behind them but still glowing softly in the early dawn, path ahead lit by lantern, Studio Ghibli style"},
        {"id": 66, "prompt": "Walking back through the forest, sunrise filtering through leaves, world feeling different now, magical, Studio Ghibli style"},
        {"id": 67, "prompt": "Fox curling up sleepily on boy's shoulder, tired from the adventure, peaceful, Studio Ghibli style"},
        {"id": 68, "prompt": "Girl's lantern now permanently glowing with soft starlight from the valley, a piece of magic kept, Studio Ghibli style"},
        {"id": 69, "prompt": "Village gate appearing ahead as morning sun rises fully, familiar and welcoming, Studio Ghibli style"},
        {"id": 70, "prompt": "Children walking through quiet morning village streets, everyone still asleep, their secret adventure, Studio Ghibli style"},
        {"id": 71, "prompt": "Boy planting the crystal seed in his backyard garden, small act of bringing magic home, Studio Ghibli style"},
        {"id": 72, "prompt": "Girl placing her glowing lantern on her windowsill, it illuminates her room with soft starlight, Studio Ghibli style"},
        {"id": 73, "prompt": "Both children waving goodbye to each other from their windows across the street, smiling, Studio Ghibli style"},
        {"id": 74, "prompt": "Crystal seed in garden already beginning to sprout a tiny glowing leaf, magic spreading, Studio Ghibli style"},
        {"id": 75, "prompt": "Final wide shot: village at sunrise with one tiny crystal sapling glowing in a garden, stars fading from sky, promise of return, Studio Ghibli style"},
    ],
    "narration": (
        "In a quiet village at the edge of the world, where the sky seemed close enough to touch, "
        "two friends shared a secret that no one else knew.\n\n"

        "Luna had silver hair that shimmered like moonlight, and she carried a small lantern "
        "wherever she went. She had always felt drawn to the stars, watching them from her window "
        "each night, wondering where they went when they fell.\n\n"

        "Kai was her best friend, a boy with messy dark hair and a tiny orange fox who rode on his shoulder. "
        "He was always ready to follow wherever curiosity led, and tonight, curiosity was calling.\n\n"

        "A single star streaked across the twilight sky and disappeared beyond the forest. "
        "Luna grabbed her lantern. Kai whistled for his fox. They met at the village gate "
        "without a word, both knowing exactly where they needed to go.\n\n"

        "The forest path was dark, but Luna's lantern lit the way. Fireflies danced around them "
        "as they walked deeper and deeper into the trees. And then, the path opened up, "
        "and they both gasped.\n\n"

        "Below them lay Starfall Valley. Crystal trees glowed with soft blue and purple light. "
        "Stars drifted down from the sky like gentle snow, coming to rest among glowing flowers. "
        "A waterfall of pure starlight cascaded down distant cliffs, "
        "and streams of liquid light flowed through meadows of bioluminescent grass.\n\n"

        "They descended carefully into the valley, reaching out to touch the crystal trees. "
        "The fox leaped from Kai's shoulder to chase a falling star, and Luna knelt beside one "
        "resting in the grass. It was warm, and it pulsed gently, like a tiny heartbeat.\n\n"

        "Floating lily pads hovered above a starlight stream, and the children climbed aboard, "
        "riding them like boats through the magical landscape. The lily pads carried them "
        "to the heart of the valley, where an enormous ancient crystal tree stood, "
        "its roots spreading like rivers of light.\n\n"

        "Tiny luminous creatures emerged from the flowers, moth-like beings with glowing wings. "
        "They landed on Luna's hands, trusting and gentle. The fox danced among them, "
        "creating swirling trails of light.\n\n"

        "But as the children explored deeper, they found something troubling. "
        "Behind the starfall waterfall, a hidden cave held the valley's heart stone, "
        "a great crystal on a stone pedestal. It was cracked, and its light was fading. "
        "Without it, all the magic of the valley would slowly disappear.\n\n"

        "Luna placed the fallen star she had found near the heart stone, "
        "and watched as blue light reached out from it, beginning to heal the cracks. "
        "Kai sent his fox to gather more fallen stars, and the luminous creatures joined in, "
        "carrying tiny stars in their wings.\n\n"

        "Together, they all worked through the night. Star after star was brought to the heart stone, "
        "each one healing it a little more. Finally, Luna and Kai lifted one last great star together, "
        "and placed it on the pedestal.\n\n"

        "A brilliant wave of light burst from the cave and swept across the entire valley. "
        "Crystal trees grew taller and brighter. New flowers bloomed in every color of starlight. "
        "The waterfall became twice as magnificent, and stars began falling in beautiful spirals "
        "instead of random drops.\n\n"

        "The valley was reborn, more magical than ever before. "
        "The luminous creatures celebrated, forming living constellation patterns in the sky. "
        "They placed a crown of light on Luna's head, and gave Kai a crystal seed as thanks.\n\n"

        "As the first light of dawn appeared on the horizon, the valley creatures gently guided "
        "the children back toward home. Luna hugged her new friends goodbye. "
        "Kai waved to the ancient tree. The fox looked back one last time.\n\n"

        "They walked home through the sunrise forest, changed forever by what they had seen. "
        "Luna's lantern now glowed with permanent starlight, a piece of the valley she would always carry. "
        "Kai planted his crystal seed in the garden behind his house.\n\n"

        "From their windows across the street, they waved to each other, smiling. "
        "And in Kai's garden, the crystal seed had already begun to sprout, "
        "one tiny glowing leaf reaching toward the fading stars.\n\n"

        "The magic of Starfall Valley would always be with them. "
        "And perhaps, on quiet nights when the stars fall just right, "
        "they will return again.\n\n"

        "Goodnight. May your dreams be full of falling stars."
    ),
}


# ============================================================================
# MASTER PIPELINE
# ============================================================================

class MasterPipeline:
    """Handles the entire workflow: reference generation, scene generation, video assembly."""

    def __init__(self):
        self.config = load_config()
        self.output_dir = Path(self.config.paths.output)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.char_dir = Path(self.config.paths.characters)
        self.env_dir = Path(self.config.paths.environments)
        self.char_dir.mkdir(parents=True, exist_ok=True)
        self.env_dir.mkdir(parents=True, exist_ok=True)

    def setup_references(self):
        """Phase 0: Generate character and scene reference images via Whisk (prompt-only).

        Opens Whisk, generates reference images using detailed prompts,
        and saves them for use in all subsequent scene generations.
        """
        console.print(Panel(
            "[bold magenta]PHASE 0: Generating Reference Images[/bold magenta]\n"
            "Creating character and scene references via Whisk\n"
            "These will be used as consistent references for all 75 scenes",
            title="Setup"
        ))

        # Check which references already exist
        refs_needed = []
        for char_id, char_data in CHARACTERS.items():
            char_file = self.char_dir / char_data["file"]
            if char_file.exists() and char_file.stat().st_size > 10000:
                console.print(f"[green]Character '{char_data['name']}' reference already exists ({char_file.stat().st_size // 1024}KB)[/green]")
            else:
                refs_needed.append(("character", char_id, char_data))

        env_file = self.env_dir / SCENE_ENV["file"]
        if env_file.exists() and env_file.stat().st_size > 10000:
            console.print(f"[green]Scene '{SCENE_ENV['name']}' reference already exists ({env_file.stat().st_size // 1024}KB)[/green]")
        else:
            refs_needed.append(("scene", "env", SCENE_ENV))

        if not refs_needed:
            console.print("[green]All reference images already exist. Skipping setup.[/green]")
            return True

        console.print(f"[cyan]Need to generate {len(refs_needed)} reference image(s)[/cyan]")

        # Start browser for reference generation
        controller = WhiskController(self.config)
        try:
            controller.start()
            time.sleep(3)

            for ref_type, ref_id, ref_data in refs_needed:
                console.print(f"\n[bold cyan]Generating {ref_type}: {ref_data.get('name', ref_id)}[/bold cyan]")

                # Clear any previous inputs
                controller.clear_inputs()
                time.sleep(2)

                # Set prompt (no reference images - prompt only)
                controller.set_prompt(ref_data["prompt"])
                time.sleep(1)

                # Generate
                controller.generate()

                # Wait for generation
                controller.wait_for_generation(timeout=90)

                # Download result
                if ref_type == "character":
                    save_dir = self.char_dir
                    save_name = ref_data["file"]
                else:
                    save_dir = self.env_dir
                    save_name = ref_data["file"]

                # Create temp folder for download
                temp_dir = self.output_dir / f"_ref_{ref_id}"
                temp_dir.mkdir(parents=True, exist_ok=True)

                downloaded = controller.download_images(temp_dir, prefix=f"ref_{ref_id}", crop=False)

                if downloaded:
                    # Use the first downloaded image as the reference
                    best = downloaded[0]
                    dest = save_dir / save_name
                    shutil.copy2(best, dest)
                    console.print(f"[green]Saved reference: {dest} ({dest.stat().st_size // 1024}KB)[/green]")
                else:
                    console.print(f"[red]Failed to generate reference for {ref_data.get('name', ref_id)}[/red]")

                # Restart browser between references for clean state
                controller.stop()
                time.sleep(2)
                controller.start()
                time.sleep(3)

        except Exception as e:
            console.print(f"[red]Setup error: {e}[/red]")
            return False
        finally:
            controller.stop()

        return True

    def reset_queue(self):
        """Clear the queue for a fresh run."""
        queue_path = self.output_dir / "queue_state.json"
        if queue_path.exists():
            queue_path.unlink()
        console.print("[cyan]Queue reset[/cyan]")

    def queue_scenes(self):
        """Queue all 75 scenes for Whisk generation."""
        console.print(Panel(
            f"[bold cyan]PHASE 1: Queuing {len(STORY['scenes'])} scenes[/bold cyan]",
            title="Queue"
        ))

        manager = QueueManager(self.config)
        manager.load_state()

        # Use both characters as references for every scene
        chars = list(CHARACTERS.keys())
        char_files = [CHARACTERS[c]["file"].replace(".png", "").replace("_01", "_01") for c in chars]

        for scene_data in STORY["scenes"]:
            scene = Scene(
                scene_id=scene_data["id"],
                environment_id=SCENE_ENV["file"].replace(".png", ""),
                character_ids=[CHARACTERS[c]["file"].replace(".png", "") for c in chars],
                prompt=scene_data["prompt"],
                image_format=ImageFormat.LANDSCAPE,
            )
            manager.add_scene(scene, batches=1)

        console.print(f"[green]{len(STORY['scenes'])} scenes queued[/green]")

    def generate_images(self):
        """Phase 2: Generate all scene images using character/scene references."""
        console.print(Panel(
            "[bold yellow]PHASE 2: Generating scene images via Whisk[/bold yellow]\n"
            f"Scenes: {len(STORY['scenes'])}\n"
            "Using character + scene references for consistency",
            title="Whisk Generation"
        ))

        manager = QueueManager(self.config)
        manager.load_state()

        pending = manager.state.get_pending()
        if not pending:
            console.print("[yellow]No pending scenes. All may be completed already.[/yellow]")
            return

        console.print(f"[cyan]Processing {len(pending)} pending scenes...[/cyan]")
        results = manager.process_queue()

        console.print(f"\n[bold]Generation results:[/bold]")
        console.print(f"  Processed: {results['processed']}")
        console.print(f"  Succeeded: {results['succeeded']}")
        console.print(f"  Failed: {results['failed']}")

    def assemble_video(self, project_id: str):
        """Phase 3: Assemble video from generated images + audio + metadata."""
        console.print(Panel(
            "[bold cyan]PHASE 3: Assembling final video[/bold cyan]",
            title="Video Pipeline"
        ))

        # Find all scene folders with images
        scene_folders = sorted([
            f for f in self.output_dir.iterdir()
            if f.is_dir() and f.name.startswith("scene_") and not f.name.startswith("scene__")
        ])

        # Filter to only folders that contain images
        image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        valid_folders = []
        for folder in scene_folders:
            has_images = any(
                f.suffix.lower() in image_extensions
                for f in folder.iterdir()
                if f.is_file()
            )
            if has_images:
                valid_folders.append(folder)

        if not valid_folders:
            # Also check generated_images folder
            gen_dir = Path("generated_images")
            if gen_dir.exists():
                scene_folders = sorted([
                    f for f in gen_dir.iterdir()
                    if f.is_dir() and f.name.startswith("scene_")
                ])
                for folder in scene_folders:
                    has_images = any(
                        f.suffix.lower() in image_extensions
                        for f in folder.iterdir()
                        if f.is_file()
                    )
                    if has_images:
                        valid_folders.append(folder)

        if not valid_folders:
            console.print("[red]No scene folders with images found[/red]")
            return None

        console.print(f"[cyan]Found {len(valid_folders)} scenes with images[/cyan]")

        # Find music file
        music_path = Path("assets/music/calm/ambient_5min.wav")
        if not music_path.exists():
            music_path = Path("assets/music/calm/ambient_bedtime.wav")
        if not music_path.exists():
            console.print("[yellow]No music file found. Video will have narration only.[/yellow]")
            music_path = None

        pipeline_config = PipelineConfig(
            character_name="Luna and Kai",
            theme="Starfall Valley Adventure",
            style=STORY["style"],
            narration_text=STORY["narration"].strip(),
            music_path=music_path,
            music_category="calm",
            voice="aria",
            images_per_scene=1,
            duration_per_image=4.0,
            generate_both_versions=True,
            export_youtube_ready=True,
            summary="Two friends discover a magical valley where stars come to rest, and work together to restore its fading magic.",
            lesson="True magic happens when friends work together with courage and kindness.",
        )

        pipeline = VideoPipeline(self.config)
        result = pipeline.run_full_pipeline(
            image_folders=valid_folders,
            pipeline_config=pipeline_config,
            project_id=project_id,
        )

        return result

    def run(self, only: str = None, project_id: str = None, fresh: bool = True):
        """Run the full pipeline or a specific phase."""
        if project_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_id = f"starfall_valley_{timestamp}"

        start_time = datetime.now()

        console.print(Panel(
            f"[bold magenta]MASTER AUTOMATION[/bold magenta]\n"
            f"Story: {STORY['title']}\n"
            f"Characters: {', '.join(c['name'] for c in CHARACTERS.values())}\n"
            f"Scene: {SCENE_ENV['name']}\n"
            f"Project: {project_id}\n"
            f"Total Scenes: {len(STORY['scenes'])}",
            title="Pipeline"
        ))

        if only == "setup":
            self.setup_references()
            return

        if only == "generate":
            self.generate_images()
            return

        if only == "video":
            result = self.assemble_video(project_id)
            if result and result.success:
                self._print_summary(result, start_time)
            return

        # Full pipeline
        if fresh:
            self.reset_queue()

        # Phase 0: Generate references if needed
        if not self.setup_references():
            console.print("[red]Failed to generate reference images. Cannot continue.[/red]")
            return

        # Phase 1: Queue scenes
        self.queue_scenes()

        # Phase 2: Generate scene images
        self.generate_images()

        # Phase 3: Assemble video
        result = self.assemble_video(project_id)

        if result and result.success:
            self._print_summary(result, start_time)
        elif result:
            console.print(f"\n[red]Pipeline failed: {result.error_message}[/red]")
        else:
            console.print("\n[red]No images available for video assembly[/red]")

    def _print_summary(self, result, start_time):
        """Print final pipeline summary."""
        elapsed = (datetime.now() - start_time).total_seconds() / 60

        table = Table(title="Pipeline Complete")
        table.add_column("Output", style="cyan")
        table.add_column("Path", style="green")

        for name, path in result.video_paths.items():
            table.add_row(f"Video ({name})", str(path))
        if result.metadata_path:
            table.add_row("Metadata", str(result.metadata_path))
        if result.thumbnail_path:
            table.add_row("Thumbnail", str(result.thumbnail_path))

        console.print(table)
        console.print(f"\nScenes: {result.scenes_processed} | "
                      f"Images: {result.total_images_used} | "
                      f"Time: {elapsed:.1f} min")


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master Automation - Full Video Pipeline")
    parser.add_argument("--only", choices=["setup", "generate", "video"],
                        help="Run only a specific phase")
    parser.add_argument("--project-id", help="Custom project ID")
    parser.add_argument("--no-reset", action="store_true",
                        help="Don't reset queue (continue from where we left off)")

    args = parser.parse_args()

    pipeline = MasterPipeline()
    pipeline.run(
        only=args.only,
        project_id=args.project_id,
        fresh=not args.no_reset,
    )
