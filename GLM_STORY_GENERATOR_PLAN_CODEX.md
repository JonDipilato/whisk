# Codex Plan of Attack - GLM Story Generator (Luna & Kai, Grandma-Style Schema)

## Goal
Generate monetization-safe, unique episodes using Z.ai **GLM-4.7** while preserving the **grandma Excel flow** (multi-environment switching, cohesive 5-act narrative, per-scene refs) but with **Luna & Kai** as the fixed characters. Target **10–12 minutes** narration.

## Hard Constraints (Pipeline Compatibility)
- Output must match `run_story.py` schema:
  - `title`, `description`, `episode`
  - `characters` (with `name`, `description`, `code`, `image_path`)
  - `environments` (E2+ map: `name`, `description`, `image_path`)
  - `scene` (default env entry)
  - `scenes` (list of prompts)
  - `scene_refs` (parallel list of `{character_codes, environment_code}`)
  - `narration` (full text)
  - `settings` (copied from grandma Excel defaults)
  - `style` (empty string if prompts already include suffix)
- **Two characters max per scene**:
  - C1 = Luna
  - C2 = Kai
  - C3 = Fox (only appear **with Kai alone**, never with Luna)
- Multi-environment switching required, with smooth transitions like grandma Excel.

## Scene/Narration Targets
- **Narration length**: 10–12 minutes (~1,300–1,800 words at 130–150 wpm).
- **Scene count**: 75–85 total, recommended **77** to match grandma pipeline.
- **Structure**: 5 acts with coherent flow:
  - Act 1 (Discovery): 15 scenes
  - Act 2 (Journey): 15 scenes
  - Act 3 (Challenge): 15 scenes
  - Act 4 (Resolution): 15 scenes
  - Act 5 (Return): 17 scenes

## Environment Switching Rules (Grandma-Style Transitions)
When switching environments, enforce a transition pair:
1) **Departure scene** in old environment (C1|C2 or C2 with C3).
2) **Arrival/establishing scene** in new environment (C0 or C1|C2).
Also ensure **1–2 establishing C0 shots** at the start of each new environment segment.

## Character Usage Rules (Scene Refs)
- C0 scenes: `character_codes: []`
- Luna solo: `["C1"]`
- Kai solo (with fox): `["C2", "C3"]`
- Together: `["C1", "C2"]` (no fox)
- Never `["C1","C2","C3"]`

## GLM Output Contract (Strict JSON)
GLM must return **JSON only** with:
```
{
  "episode_title": "...",
  "episode_description": "...",
  "characters": [
    {"code":"C1","name":"Luna","description":"..."},
    {"code":"C2","name":"Kai","description":"..."},
    {"code":"C3","name":"Fox","description":"..."}
  ],
  "environments": [
    {"code":"E2","name":"Village Dawn","description":"..."},
    {"code":"E3","name":"Forest Path","description":"..."},
    ...
  ],
  "scenes": [
    {"prompt":"...", "character_codes":["C1"], "environment_code":"E2"},
    ...
  ],
  "narration":"..."
}
```
Validation will reject any non-JSON output.

## Uniqueness Guardrails
- Maintain a local history file (JSONL) with episode title + environment list + 5–10 scene snippets.
- Include last 3–5 episodes in the GLM prompt to reduce overlap.
- Post-validate:
  - No repeated environment name from last N episodes.
  - Prompt overlap under threshold (e.g., <25% similar lines).
  - If overlap too high, regenerate.

## Implementation Steps (glm_story_generator.py)
1) **Load API key** from `.env` (GLM_API_KEY).
2) **Build GLM prompt** enforcing the JSON schema and transition rules.
3) **Call GLM-4.7** via `requests` to Z.ai endpoint.
4) **Validate output**:
   - `len(scenes) == len(scene_refs)` and equals target (77).
   - All `environment_code` exist in environments map.
   - Character codes only in allowed sets.
   - Narration word count in target range.
5) **Build story_config.json**:
   - Use fixed `characters` with stable `image_path`:
     - `data/characters/luna_01.png`
     - `data/characters/kai_01.png`
     - `data/characters/fox_01.png` (confirm/prepare if missing)
   - Map environments to per-episode refs:
     - `output/episodes/grandma_glm_ep{N}_{timestamp}/refs/grandma_{env_name}.png`
   - Set `scene` to the first environment.
   - Copy `settings` defaults from `excel_to_config.py`.
6) **Write outputs**:
   - `story_config.json`
   - Update `data/episode_counter_grandma.json`
   - Append to `data/glm_episode_history.jsonl`
7) **Run pipeline** (optional CLI):
   - `python glm_story_generator.py --run --output-dir "output/episodes/grandma_glm_ep..."`

## Verification Checklist
- `python glm_story_generator.py --dry-run` prints:
  - Episode title
  - Scene count
  - Environments list
  - Narration word count
- `python run_story.py --config story_config.json --output-dir ...` runs cleanly
- Scene refs never include 3 characters

## Risk & Mitigation
- **Risk**: GLM returns malformed JSON → strict parser + retry.
- **Risk**: Short narration → enforce min word count and regenerate.
- **Risk**: Overlap with prior episodes → similarity checks + regenerate.
- **Risk**: Missing fox image ref → add once in `data/characters/fox_01.png`.
