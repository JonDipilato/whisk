# Whisk Automation - Project Context

## What This Is
YouTube bedtime story video automation. Generates Studio Ghibli-style animated videos from story configs using Google Whisk (AI image gen), Edge TTS (narration), and FFmpeg (video assembly).

## Architecture

```
generate_episode.py  → Creates story_config.json (theme, characters, 75 scenes, narration)
run_story.py         → Main pipeline: Whisk images → TTS audio → FFmpeg video
src/
├── whisk_controller.py  → Selenium browser automation for Google Whisk
├── audio_generator.py   → Edge TTS + audio mixing
├── video_assembler.py   → MoviePy/FFmpeg video composition
├── youtube_metadata.py  → Title/description/tags/chapters generation
├── pipeline.py          → Full pipeline orchestrator
├── music_library.py     → Music track management
├── config.py            → Pydantic config models
└── models.py            → Data models (Scene, VideoProject, VideoMetadata)
```

## Pipeline Flow (run_story.py)
1. **Reference Gen** — Generate character + environment images via Whisk (skips if exist)
2. **Scene Gen** — 75 scenes via Whisk (~2-3hrs), saves to `output/scene_XXX_batch_1/`
3. **Narration** — Edge TTS, voice: en-US-AriaNeural, rate: -15%
4. **Music** — Looks in `assets/music/calm/` for background track
5. **Video Assembly** — FFmpeg concat images → mix audio → output MP4

## Key Config: story_config.json
```json
{
  "title": "...",
  "characters": [{"name": "Luna", "description": "...whisk prompt..."}, ...],
  "scene": {"name": "Starfall Valley", "description": "...environment prompt..."},
  "style": "Studio Ghibli anime style",
  "scenes": ["...75 scene prompts..."],
  "narration": "...full narration text...",
  "settings": {"voice": "...", "fps": 24, "resolution": "1920x1080", ...}
}
```

## Character Assets
- `data/characters/luna_01.png` — Silver hair girl (main)
- `data/characters/kai_01.png` — Boy with fox (secondary)
- `data/environments/starfall_valley.png` — Current environment ref

## Output Structure
```
output/
├── scene_001_batch_1/ through scene_075_batch_1/ (2 PNGs each)
├── audio/ (narration mp3, mixed wav)
└── videos/ (narrated.mp4, music_only.mp4, youtube.mp4)
```

## generate_episode.py Details
- 8 themes: starfall, ocean, sky_islands, mushroom, winter, desert, garden, aurora
- Generates 2 characters (female+male) from trait pools
- 5-act story arc (discovery, exploration, challenge, renewal, return) × 15 scenes each
- ~1000 word narration
- CLI: `--theme`, `--episode`, `--seed`, `--output`, `--run`, `--list-themes`

## run_story.py FFmpeg Commands
- Video filter (currently letterboxes): `scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black`
- Audio mix: uses amix with volume adjustment
- Output: libx264, CRF 18, fps 24, yuv420p

## Current State (Jan 2026)
- Starfall Valley episode fully generated (75 scenes, narrated video complete)
- youtube_metadata.py exists but NOT hooked into run_story.py
- No thumbnail generation with text overlay
- Music library directories exist but are empty
- No --new-character flag yet
- Videos have black bar letterboxing (not cropped to fill)

---

## PENDING IMPLEMENTATION (Plan: elegant-rolling-peacock.md)

### Feature 1: YouTube Metadata + Thumbnail in run_story.py
- Add `generate_metadata_and_thumbnail()` method after video assembly
- Uses YouTubeMetadataGenerator from src/youtube_metadata.py
- Thumbnail: PIL text overlay on first scene image
- Hook as Step 6 in run() and in --video-only path

### Feature 3: --new-character Flag in generate_episode.py
- Add `--new-character` CLI flag
- GUEST_ROLES constant with guardian/trickster/lost_one/healer archetypes
- Third character appears in Act 2, helps in Act 3, farewell in Act 5
- Modify generate_story_arc() and generate_narration() to accept char3
- Config gets third entry in characters array with "role" and "appears_from_scene"

### Feature 8: Crop-to-Fill (16:9) in run_story.py
- Replace `force_original_aspect_ratio=decrease` + `pad` with
- `force_original_aspect_ratio=increase` + `crop=1920:1080:(iw-1920)/2:(ih-1080)/2`
- Apply to both narrated and music_only FFmpeg commands

## Tech Stack
Python 3, Selenium, edge-tts, MoviePy, FFmpeg, PIL/Pillow, Rich, Pydantic
