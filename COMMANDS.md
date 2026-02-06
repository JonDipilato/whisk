# Command Reference

All commands use: `.\venv_win\Scripts\python.exe` (Windows) or `python3` (WSL)

---

## generate_episode.py — Create a new episode

### Full pipeline (generate + images + video + upload)
```
generate_episode.py --ai --target-minutes 6 --run --upload
```

### Generate config only (no pipeline)
```
generate_episode.py --ai --target-minutes 6
```

### With specific theme
```
generate_episode.py --ai --theme ocean --target-minutes 8 --run --upload
```

### With scheduled upload (N hours from now)
```
generate_episode.py --ai --target-minutes 6 --run --schedule 24
```

### Template mode (random characters, no AI)
```
generate_episode.py --template --run
```

### Grandma Rose & Lily profile
```
generate_episode.py --template --profile grandma --run
```

### Add guest character
```
generate_episode.py --ai --new-character --run
```

### List available themes
```
generate_episode.py --list-themes
```

| Flag | What it does |
|------|-------------|
| `--ai` | Use OpenAI to generate story (recommended) |
| `--local` | Use local LM Studio instead of OpenAI |
| `--template` | Use hardcoded story templates (random characters) |
| `--theme X` | Pick theme: starfall, ocean, sky_islands, mushroom, winter, desert, garden, aurora |
| `--target-minutes N` | Narration length in minutes (default: 10) |
| `--episode N` | Override episode number |
| `--seed N` | Reproducible random seed |
| `--run` | Run full pipeline after generating config |
| `--upload` | Upload to YouTube (auto-scheduled) |
| `--schedule N` | Schedule upload N hours from now |
| `--profile X` | friends (default) or grandma |
| `--new-character` | Add guest character in Act 2 |
| `--use-luna-kai` | Fixed Luna & Kai traits (template mode) |
| `--output FILE` | Config output path (default: story_config.json) |
| `--output-dir DIR` | Episode output directory |

---

## run_story.py — Pipeline, video, upload, fixes

### Run full pipeline (images + audio + video)
```
run_story.py --output-dir output/episodes/luna_kai_ep19_20260205_143625
```

### Skip Whisk (use existing images)
```
run_story.py --skip-whisk --output-dir DIR
```

### Rebuild video only (from existing images + audio)
```
run_story.py --video-only --output-dir DIR
```

### Upload only (skip everything, just upload existing video)
```
run_story.py --upload-only --output-dir DIR
```

### Upload + rebuild video
```
run_story.py --video-only --upload --output-dir DIR
```

### Publish immediately (no scheduling)
```
run_story.py --upload-only --upload-now --output-dir DIR
```

---

## Fixing failed scenes

### Regenerate specific scene(s)
```
run_story.py --scene 48 --output-dir DIR
run_story.py --scene 48,52,60 --output-dir DIR
run_story.py --scene 48-55 --output-dir DIR
```

### Fix scene then rebuild + upload
```
run_story.py --scene 48 --output-dir DIR
run_story.py --video-only --upload --output-dir DIR
```

---

## YouTube management

### Check schedule status
```
run_story.py --schedule-status
```

### Set next publish date manually
```
run_story.py --set-schedule 2026-02-25
```

### List recent uploads
```
run_story.py --list-videos
```

### Update title/episode on existing video
```
run_story.py --update-video VIDEO_ID --fix-title "New Title" --fix-episode 15
```

### Regenerate metadata + thumbnail only
```
run_story.py --metadata-only --output-dir DIR
```

### Update metadata on existing YouTube video
```
run_story.py --update-video VIDEO_ID --output-dir DIR
```

---

## Common workflows

### New episode end-to-end
```
generate_episode.py --ai --target-minutes 6 --run --upload
```

### Scene failed during generation — fix it
```
run_story.py --scene 48 --output-dir output/episodes/luna_kai_epN_TIMESTAMP
run_story.py --video-only --upload --output-dir output/episodes/luna_kai_epN_TIMESTAMP
```

### Rebuild video with different music/narration
```
run_story.py --video-only --output-dir DIR
```

### Re-upload with new schedule
```
run_story.py --upload-only --output-dir DIR
```

### Find your latest episode directory
```
ls -dt output/episodes/*/ | head -5
```
