"""
=================================================================
  AI STORY GENERATOR (Luna & Kai)

  Uses OpenAI API to generate unique episodes featuring Luna & Kai
  with unique environments per episode.

  HOW TO USE:
     python glm_story_generator.py              # Generate config only
     python glm_story_generator.py --run        # Generate + run pipeline
     python glm_story_generator.py --dry-run    # Preview without API call

  REQUIRES:
     .env file with OPENAI_API_KEY=your_key_here
=================================================================
"""

import json
import os
import sys
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

# =============================================================================
# CONFIGURATION
# =============================================================================

# Remote API (Z.AI GLM)
GLM_API_ENDPOINT = "https://api.z.ai/api/paas/v4/chat/completions"
GLM_MODEL = "glm-4.7-flash"

# OpenAI API
OPENAI_API_ENDPOINT = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-5.2"  # Latest model

# Local API (LM Studio) - no API key needed
LOCAL_API_ENDPOINT = "http://100.114.81.52:1234/v1/chat/completions"
LOCAL_MODEL = "qwen/qwen3-14b"

# Default to local
USE_LOCAL = True

# Fixed character definitions (consistent across all episodes)
CHARACTERS = {
    "C1": {
        "name": "Luna",
        "description": (
            "Young girl with flowing silver hair and bright blue eyes, wearing a soft lavender dress "
            "with a small glowing lantern, gentle curious expression, Studio Ghibli anime style, white background"
        ),
        "image_path": "data/characters/luna_01.png",
    },
    "C2": {
        "name": "Kai",
        "description": (
            "Young boy with messy brown hair and warm amber eyes, wearing a forest green tunic "
            "with a tiny orange fox companion on his shoulder, adventurous friendly smile, "
            "Studio Ghibli anime style, white background"
        ),
        "image_path": "data/characters/kai_01.png",
    },
    "C3": {
        "name": "Fox",
        "description": (
            "Tiny orange fox with fluffy tail and bright curious eyes, playful expression, "
            "soft fur with white chest patch, Studio Ghibli anime style, white background"
        ),
        "image_path": "data/characters/fox_01.png",
    },
}

# Story structure: 77 scenes across 5 acts
SCENE_STRUCTURE = {
    "act_1": {"name": "Discovery", "scenes": 15, "desc": "Village life, noticing something, setting out"},
    "act_2": {"name": "Journey", "scenes": 15, "desc": "Traveling through environments, wonder"},
    "act_3": {"name": "Challenge", "scenes": 15, "desc": "Problem discovered, working to solve"},
    "act_4": {"name": "Resolution", "scenes": 15, "desc": "Success, celebration, gratitude"},
    "act_5": {"name": "Return", "scenes": 17, "desc": "Farewell, journey home, settling in, sleep"},
}

# Ghibli style suffix for all prompts
GHIBLI_SUFFIX = (
    "Ghibli-inspired animated storybook illustration, soft hand-painted digital artwork, "
    "clean gentle linework, warm natural hues."
)

# History file for uniqueness tracking
HISTORY_FILE = Path(__file__).parent / "data" / "glm_episode_history.jsonl"
COUNTER_FILE = Path(__file__).parent / "data" / "episode_counter.json"


# =============================================================================
# API FUNCTIONS
# =============================================================================

def load_api_key() -> str:
    """Load GLM API key from .env file."""
    env_path = Path(__file__).parent / ".env"

    # Try loading with dotenv first
    if HAS_DOTENV and env_path.exists():
        load_dotenv(env_path, override=True)

    key = os.environ.get("GLM_API_KEY", "")

    # Fallback: read .env file directly if dotenv didn't work
    if not key and env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GLM_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break

    if not key:
        print("ERROR: GLM_API_KEY not found in .env file")
        print("Create a .env file with: GLM_API_KEY=your_key_here")
        sys.exit(1)

    return key


def load_all_titles() -> list[str]:
    """Load ALL episode titles from history for uniqueness checking."""
    if not HISTORY_FILE.exists():
        return []

    titles = []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entry = json.loads(line)
                    title = entry.get("title", "").strip()
                    if title:
                        titles.append(title)
                except json.JSONDecodeError:
                    continue
    return titles


def is_title_unique(title: str, existing_titles: list[str]) -> bool:
    """Check if a title is sufficiently unique vs existing titles.

    Returns False if:
    - Exact match (case-insensitive)
    - Near-duplicate (SequenceMatcher >= 0.85)
    - 80%+ word overlap
    """
    import difflib

    title_lower = title.lower().strip()
    title_words = set(title_lower.split())

    for existing in existing_titles:
        existing_lower = existing.lower().strip()

        # Exact match
        if title_lower == existing_lower:
            return False

        # Near-duplicate via SequenceMatcher
        ratio = difflib.SequenceMatcher(None, title_lower, existing_lower).ratio()
        if ratio >= 0.85:
            return False

        # Word overlap check
        existing_words = set(existing_lower.split())
        if title_words and existing_words:
            overlap = len(title_words & existing_words)
            max_len = max(len(title_words), len(existing_words))
            if max_len > 0 and overlap / max_len >= 0.80:
                return False

    return True


def load_recent_episodes(n: int = 3) -> list[dict]:
    """Load the last N episodes from history for uniqueness checking."""
    if not HISTORY_FILE.exists():
        return []

    episodes = []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    episodes.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return episodes[-n:] if len(episodes) >= n else episodes


def build_glm_prompt(recent_episodes: list[dict], theme_hint: Optional[str] = None, target_minutes: float = 10, all_titles: list[str] = None) -> str:
    """Build the system prompt for GLM to generate a unique story."""

    # List recent environments to avoid
    avoid_envs = []
    for ep in recent_episodes:
        avoid_envs.extend(ep.get("environments", []))
    avoid_str = ", ".join(avoid_envs) if avoid_envs else "none"

    # Build titles-to-avoid string
    titles_to_avoid = all_titles or []
    if titles_to_avoid:
        titles_str = ", ".join(f'"{t}"' for t in titles_to_avoid[-20:])  # Last 20 to fit context
    else:
        titles_str = ""

    theme_str = f"Theme hint: {theme_hint}" if theme_hint else "Choose a unique adventure theme"

    # Calculate narration word count from target minutes (130 wpm reading pace)
    min_words = int(target_minutes * 130 * 0.9)
    max_words = int(target_minutes * 130 * 1.1)

    # Calculate scene count based on target minutes (~8 seconds per scene)
    total_scenes = int(target_minutes * 60 / 8)
    scenes_per_act = total_scenes // 5
    final_act_scenes = total_scenes - (scenes_per_act * 4)  # Remainder goes to Act 5

    prompt = f'''You are a master storyteller creating a bedtime story for children aged 3-7.
Generate a complete Luna & Kai adventure episode in JSON format.

CHARACTERS (fixed, do not change):
- C1 = Luna: silver-haired girl with lantern, gentle and curious
- C2 = Kai: brown-haired boy with fox companion, adventurous
- C3 = Fox: tiny orange fox (Kai's companion)

CHARACTER USAGE RULES:
- C0 = No characters (establishing/environment shots)
- C1 = Luna solo
- C2 = Kai solo (fox may appear with him)
- C1|C2 = Both together (no fox when together)
- C3 only appears with C2, never with C1 alone, never all three together

ENVIRONMENT RULES:
- Create 5-7 UNIQUE environments for this episode
- E1 = Starting village (always first)
- E2-E7 = Journey locations (forest, caves, mountains, rivers, etc.)
- Each environment should flow naturally to the next
- AVOID these recently used environments: {avoid_str}

TIME-OF-DAY PROGRESSION (critical for continuity):
- Act 1: MORNING - soft dawn light, golden sunrise, dew on grass
- Act 2: LATE MORNING to EARLY AFTERNOON - bright daylight, warm sun
- Act 3: AFTERNOON - golden hour approaching, longer shadows
- Act 4: LATE AFTERNOON to SUNSET - warm orange/pink light, golden glow
- Act 5: EVENING to NIGHT - twilight, stars appearing, moonlight, cozy indoor warmth
- NEVER jump backwards in time (no night→morning within same act)
- Lighting must be consistent within each environment segment

SCENE-TO-SCENE CONTINUITY:
- Each scene should connect logically to the previous one
- If a character picks something up, show them still holding it
- Weather/sky should progress naturally (clear→cloudy or stay consistent)
- Actions have consequences in following scenes
- Use transitional moments: walking, looking, reaching, discovering

CRITICAL: You MUST generate EXACTLY {total_scenes} scenes for this {target_minutes}-minute video.

STORY STRUCTURE ({total_scenes} scenes total - THIS IS MANDATORY):
- Act 1 (scenes 1-{scenes_per_act}): Discovery - village morning, noticing something magical, deciding to explore [{scenes_per_act} scenes]
- Act 2 (scenes {scenes_per_act+1}-{scenes_per_act*2}): Journey - traveling through environments, wonder and discovery [{scenes_per_act} scenes]
- Act 3 (scenes {scenes_per_act*2+1}-{scenes_per_act*3}): Challenge - problem discovered, working together to solve [{scenes_per_act} scenes]
- Act 4 (scenes {scenes_per_act*3+1}-{scenes_per_act*4}): Resolution - success, celebration, gratitude [{scenes_per_act} scenes]
- Act 5 (scenes {scenes_per_act*4+1}-{total_scenes}): Return - farewell, journey home, cozy evening, falling asleep [{final_act_scenes} scenes]

Count your scenes as you generate them. You MUST reach scene {total_scenes}.

SCENE VARIETY (per act):
- 30-40% C0 (establishing shots, environment beauty, atmosphere)
- 15% C1 (Luna solo moments - curious, gentle, observing)
- 15% C2 (Kai solo moments - adventurous, playful, with fox)
- 30-40% C1|C2 (both together - friendship, teamwork, shared wonder)

ENVIRONMENT TRANSITIONS:
When switching environments, always include this sequence:
1. Departure scene: characters leaving/walking away from current location
2. Travel moment: path, bridge, or transitional space between areas
3. Arrival C0 shot: wide establishing shot of new environment (no characters)
4. Entry scene: characters entering/discovering the new space

{theme_str}

PROMPT FORMAT (match this style exactly):
- 25-50 words per prompt (concise, visual, specific)
- Focus on: camera angle, lighting, specific details, textures, mood
- Use phrases like: "close-up of", "wide shot of", "soft morning light", "warm golden glow"
- Include sensory details: steam rising, leaves rustling, water sparkling
- End each prompt with the Ghibli suffix (I'll add it automatically)
- NO dialogue, NO character thoughts, ONLY visual descriptions

EXAMPLE PROMPTS (follow this style):
- "Wide establishing shot of a cozy village at dawn, thatched cottages with chimney smoke, flower gardens with morning dew, soft pink sky"
- "Close-up of Luna's hands reaching toward a glowing butterfly, silver hair catching sunlight, curious expression, meadow flowers in background"
- "Kai and fox companion crossing a mossy stone bridge, afternoon light filtering through ancient trees, stream sparkling below"
- "Quiet interior of tree hollow home, warm lantern light, Luna and Kai sharing bread, tired happy expressions, night sky visible through window"

TITLE REQUIREMENTS (YouTube-optimized, NO episode numbers):
- Create a captivating title like: "The Starlight Lantern", "Journey to Crystal Falls", "The Secret Garden Path"
- Keep it short (3-6 words), magical, and intriguing
- NO "Episode X" or numbers in the title
- Focus on the adventure/destination, not "Luna and Kai go to..."
- Vary your title structure — do NOT start multiple titles with the same word
{'- AVOID these recently used titles (do NOT reuse or closely resemble): ' + titles_str if titles_str else ''}

OUTPUT FORMAT (strict JSON only, no markdown):
{{
  "episode_title": "The Starlight Lantern",
  "episode_description": "Brief 1-2 sentence summary",
  "environments": [
    {{"code": "E1", "name": "Meadow Village", "description": "Cozy village with thatched cottages at the edge of rolling hills, flower gardens and winding stone paths"}},
    {{"code": "E2", "name": "Whispering Woods", "description": "Ancient forest with towering trees, soft moss carpet, shafts of golden light, gentle mist"}},
    ...
  ],
  "scenes": [
    {{"prompt": "Wide establishing shot of a cozy village at dawn, thatched cottages with chimney smoke rising, flower gardens glistening with dew, soft pink and gold sky", "character_codes": [], "environment_code": "E1", "narration": "In a quiet little village, the sun was just beginning to rise."}},
    {{"prompt": "Luna standing by her cottage window, silver hair glowing in morning light, curious expression as she notices something in the distance", "character_codes": ["C1"], "environment_code": "E1", "narration": "Luna looked out her window, her silver hair catching the golden light. Something sparkled in the distance."}},
    ...continue for ALL {total_scenes} scenes, each with its own narration...
  ]
}}

PER-SCENE NARRATION REQUIREMENTS:
- Each scene MUST have a "narration" field with 1-3 sentences
- Total narration should be {min_words}-{max_words} words ({target_minutes} minutes)
- Narration must match what's shown in the scene's visual prompt
- Use gentle, soothing bedtime story tone
- Simple vocabulary for young children (ages 3-7)
- Include soft sensory details (sounds, textures, warmth)
- C0 scenes (no characters): describe the environment, mood, atmosphere
- Character scenes: describe what they see, feel, do
- Pacing: calm beginning, gentle wonder in middle, peaceful sleepy ending
- Final scenes must describe settling down, eyes closing, drifting to sleep

Return ONLY the JSON object, no explanations or markdown.'''

    return prompt


def call_llm_api(prompt: str, provider: str = "openai", api_key: str = "", max_retries: int = 3) -> dict:
    """Call LLM API and return parsed JSON response.

    Args:
        provider: "openai", "local", or "glm"
    """

    if provider == "local":
        endpoint = LOCAL_API_ENDPOINT
        model = LOCAL_MODEL
        headers = {"Content-Type": "application/json"}
        api_name = f"Local LM Studio ({model})"
        timeout = 600
        max_tok = 32000
    elif provider == "openai":
        endpoint = OPENAI_API_ENDPOINT
        model = OPENAI_MODEL
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        api_name = f"OpenAI ({model})"
        timeout = 300
        max_tok = 16384  # gpt-4o max output tokens
    else:  # glm
        endpoint = GLM_API_ENDPOINT
        model = GLM_MODEL
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        api_name = f"Z.AI GLM ({model})"
        timeout = 120
        max_tok = 16000

    # Build payload - OpenAI uses max_completion_tokens, others use max_tokens
    token_param = "max_completion_tokens" if provider == "openai" else "max_tokens"
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        token_param: max_tok,
    }

    for attempt in range(max_retries):
        try:
            print(f"  Calling {api_name} (attempt {attempt + 1}/{max_retries})...")

            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=timeout,
            )

            if response.status_code != 200:
                print(f"  API error: {response.status_code} - {response.text[:200]}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                continue

            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Parse JSON from response (handle potential markdown wrapping)
            content = content.strip()

            # Strip Qwen3 <think> tags if present
            if "<think>" in content:
                content = re.sub(r"<think>.*?</think>\s*", "", content, flags=re.DOTALL)

            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\s*", "", content)
                content = re.sub(r"\s*```$", "", content)

            story_data = json.loads(content)
            print("  API call successful!")
            return story_data

        except json.JSONDecodeError as e:
            print(f"  JSON parse error: {e}")
            # Show partial response for debugging
            if 'content' in dir():
                print(f"  Response preview: {content[:500] if content else 'empty'}...")
            if attempt < max_retries - 1:
                time.sleep(3)
        except requests.RequestException as e:
            print(f"  Request error: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)

    print("ERROR: Failed to get valid response after retries")
    sys.exit(1)


# =============================================================================
# VALIDATION
# =============================================================================

def validate_story(story_data: dict, history_titles: list[str] = None) -> tuple[bool, list[str]]:
    """Validate the generated story meets requirements."""
    errors = []

    # Check required fields (narration can be top-level OR per-scene)
    required = ["episode_title", "environments", "scenes"]
    for field in required:
        if field not in story_data:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    # Check scene count (flexible - at least 20 for any video)
    scene_count = len(story_data["scenes"])
    if scene_count < 20:
        errors.append(f"Scene count {scene_count} too low (need at least 20)")

    # Check environment codes exist
    env_codes = {e["code"] for e in story_data["environments"]}
    for i, scene in enumerate(story_data["scenes"]):
        env_code = scene.get("environment_code", "")
        if env_code and env_code not in env_codes:
            errors.append(f"Scene {i+1} uses undefined environment: {env_code}")

    # Check character codes are valid (normalize pipe-delimited strings from LLM)
    valid_char_codes = {"C0", "C1", "C2", "C3"}
    for i, scene in enumerate(story_data["scenes"]):
        raw_codes = scene.get("character_codes", [])
        # LLM sometimes returns "C1|C2" as a string or ["C1|C2"] instead of ["C1", "C2"]
        if isinstance(raw_codes, str):
            raw_codes = [c.strip() for c in raw_codes.split("|") if c.strip()]
        else:
            expanded = []
            for code in raw_codes:
                code = str(code)
                if "|" in code:
                    expanded.extend(c.strip() for c in code.split("|") if c.strip())
                else:
                    expanded.append(code)
            raw_codes = expanded
        for code in raw_codes:
            if code not in valid_char_codes:
                errors.append(f"Scene {i+1} has invalid character code: {code}")
        # Check no triple characters (C0 doesn't count)
        real_chars = [c for c in raw_codes if c != "C0"]
        if len(real_chars) > 2:
            errors.append(f"Scene {i+1} has more than 2 characters")

    # Check narration exists - either top-level OR per-scene
    top_level_narration = story_data.get("narration", "")
    per_scene_narrations = [s.get("narration", "") for s in story_data.get("scenes", [])]
    combined_per_scene = " ".join(n for n in per_scene_narrations if n)

    narration_text = top_level_narration or combined_per_scene
    word_count = len(narration_text.split())
    if word_count < 100:
        errors.append(f"Narration too short: {word_count} words (need at least 100)")

    # Title uniqueness warning (non-fatal)
    if history_titles:
        title = story_data.get("episode_title", "")
        if title and not is_title_unique(title, history_titles):
            print(f"  WARNING: Title '{title}' is similar to an existing title (will retry)")

    return len(errors) == 0, errors


# =============================================================================
# CONFIG BUILDER
# =============================================================================

def build_config(story_data: dict, episode_num: int, output_dir: str) -> dict:
    """Convert GLM story data to story_config.json format."""

    # Build characters array
    characters = []
    for code, char_data in CHARACTERS.items():
        characters.append({
            "name": char_data["name"],
            "description": char_data["description"],
            "code": code,
            "image_path": char_data["image_path"],
        })

    # Build environments dict
    environments = {}
    for env in story_data["environments"]:
        code = env["code"]
        if code == "E1":
            continue  # Skip plain background
        name = env["name"].lower().replace(" ", "_")
        environments[code] = {
            "name": name,
            "description": env["description"],
            "image_path": f"{output_dir}/refs/env_{name}.png",
        }

    # Build scenes, scene_refs, and scene_narrations arrays
    scenes = []
    scene_refs = []
    scene_narrations = []
    # Pattern to strip leading character codes from prompt text (e.g. "C0 wide shot..." or "C1|C2 children walking...")
    _code_prefix_re = re.compile(r'^(?:C[0-3](?:\|C[0-3])*)\s+', re.IGNORECASE)

    for scene in story_data["scenes"]:
        # Strip any leading character code prefix the LLM may have embedded in the prompt
        prompt = _code_prefix_re.sub('', scene["prompt"])
        scenes.append(prompt)

        # Extract per-scene narration
        scene_narrations.append(scene.get("narration", ""))

        # Convert character codes to list format
        char_codes = scene.get("character_codes", [])
        if isinstance(char_codes, str):
            char_codes = [c.strip() for c in char_codes.split("|") if c.strip()]
        else:
            # Expand pipe-joined entries inside a list (e.g. ["C1|C2"] -> ["C1", "C2"])
            expanded = []
            for code in char_codes:
                if "|" in str(code):
                    expanded.extend(c.strip() for c in code.split("|") if c.strip())
                else:
                    expanded.append(code)
            char_codes = expanded

        # C0 means "no characters" — normalize to empty list
        char_codes = [c for c in char_codes if c.upper() != "C0"]

        scene_refs.append({
            "character_codes": char_codes,
            "environment_code": scene.get("environment_code", "E1"),
        })

    # Combine all scene narrations for backwards compatibility
    combined_narration = story_data.get("narration", "")
    if not combined_narration and scene_narrations:
        combined_narration = " ".join(n for n in scene_narrations if n)

    # Default scene (first non-E1 environment)
    first_env = story_data["environments"][1] if len(story_data["environments"]) > 1 else story_data["environments"][0]
    first_env_name = first_env["name"].lower().replace(" ", "_")
    default_scene = {
        "name": first_env_name,
        "description": first_env["description"],
        "image_path": f"{output_dir}/refs/env_{first_env_name}.png",
    }

    # YouTube-optimized title (no episode numbers - hurts clicks)
    title = story_data.get("episode_title", "A Magical Adventure")
    # Remove any "Episode X" that GLM might have added
    title = re.sub(r'\s*-?\s*[Ee]pisode\s*\d*', '', title).strip()

    config = {
        "title": title,
        "description": story_data.get("episode_description", ""),
        "profile": "glm_generated",
        "episode": episode_num,
        "characters": characters,
        "environments": environments,
        "scene": default_scene,
        "scenes": scenes,
        "scene_refs": scene_refs,
        "scene_narrations": scene_narrations,
        "narration": combined_narration,
        "style": "",  # Prompts already include Ghibli suffix
        "settings": {
            "voice": "en-US-AriaNeural",
            "narration_speed": "-15%",
            "music_volume": 0.18,
            "narration_volume": 1.2,
            "resolution": "1920x1080",
            "fps": 24,
            "video_quality": 18,
            "output_versions": ["narrated", "music_only"],
        },
    }

    return config


# =============================================================================
# EPISODE COUNTER
# =============================================================================

def load_episode_counter() -> int:
    """Load the current episode counter."""
    if COUNTER_FILE.exists():
        try:
            with open(COUNTER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("last_episode", 0)
        except Exception:
            pass
    return 0


def save_episode_counter(episode_num: int):
    """Save the episode counter."""
    COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(COUNTER_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "last_episode": episode_num,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }, f, indent=2)


def save_to_history(story_data: dict, episode_num: int):
    """Append episode summary to history for uniqueness tracking."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    env_names = [e["name"] for e in story_data.get("environments", [])]
    sample_scenes = [s["prompt"][:100] for s in story_data.get("scenes", [])[:5]]

    entry = {
        "episode": episode_num,
        "title": story_data.get("episode_title", ""),
        "environments": env_names,
        "sample_scenes": sample_scenes,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# =============================================================================
# MAIN GENERATOR
# =============================================================================

def generate_story(
    theme_hint: Optional[str] = None,
    target_minutes: float = 10,
    dry_run: bool = False,
    quiet: bool = False,
    provider: str = "openai",
) -> dict:
    """Generate a complete story using LLM API.

    Args:
        theme_hint: Optional theme like "crystal caves" or "sky islands"
        target_minutes: Target narration length in minutes
        dry_run: If True, don't call API, just show what would happen
        quiet: If True, minimal output (for integration with generate_episode.py)
        provider: "openai", "local", or "glm"

    Returns:
        Story data dict with episode_title, environments, scenes, narration
    """
    model_names = {
        "local": f"Local LM Studio",
        "openai": f"OpenAI ({OPENAI_MODEL})",
        "glm": f"Z.AI GLM ({GLM_MODEL})",
    }
    model_name = model_names.get(provider, provider)

    if not quiet:
        print(f"\n  Story Generator (Luna & Kai) - {model_name}")
        print("  " + "=" * 40)

    # Load recent episodes for uniqueness
    recent = load_recent_episodes(3)
    if recent and not quiet:
        print(f"  Loaded {len(recent)} recent episodes for uniqueness check")

    # Load all titles for uniqueness gate
    all_titles = load_all_titles()
    if all_titles and not quiet:
        print(f"  Loaded {len(all_titles)} existing titles for uniqueness check")

    # Build prompt
    prompt = build_glm_prompt(recent, theme_hint, target_minutes, all_titles=all_titles)

    if dry_run:
        print(f"\n  [DRY RUN] Would send prompt to {model_name}:")
        print(f"  Prompt length: {len(prompt)} characters")
        print(f"  Theme hint: {theme_hint or 'auto'}")
        print(f"  Target: {target_minutes} minutes")
        if all_titles:
            print(f"  Avoiding {len(all_titles)} existing titles")
        return {}

    # Load API key (only needed for remote providers)
    api_key = ""
    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            # Try loading from .env
            env_path = Path(__file__).parent / ".env"
            if env_path.exists():
                for line in env_path.read_text().splitlines():
                    if line.startswith("OPENAI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        if not api_key:
            print("ERROR: OPENAI_API_KEY not found in environment or .env file")
            sys.exit(1)
        if not quiet:
            print(f"  OpenAI API key loaded: {api_key[:8]}...")
    elif provider == "glm":
        api_key = load_api_key()
        if not quiet:
            print(f"  GLM API key loaded: {api_key[:8]}...")
    elif not quiet:
        print(f"  Using local LM Studio at {LOCAL_API_ENDPOINT}")

    # Call API with title uniqueness retry loop
    rejected_titles = []
    max_title_retries = 3

    for title_attempt in range(max_title_retries):
        # Rebuild prompt with rejected titles added to avoid list
        if rejected_titles:
            retry_titles = all_titles + rejected_titles
            prompt = build_glm_prompt(recent, theme_hint, target_minutes, all_titles=retry_titles)

        story_data = call_llm_api(prompt, provider=provider, api_key=api_key)

        # Validate structure
        valid, errors = validate_story(story_data, history_titles=all_titles)
        if not valid:
            print("\n  ERROR: Story validation failed:")
            for err in errors:
                print(f"    - {err}")
            print("\n  The AI generated an invalid story structure.")
            print("  Try running again or check the API response.")
            sys.exit(1)

        # Check title uniqueness
        generated_title = story_data.get("episode_title", "")
        if is_title_unique(generated_title, all_titles + rejected_titles):
            if title_attempt > 0 and not quiet:
                print(f"  Title accepted on attempt {title_attempt + 1}: {generated_title}")
            return story_data

        # Title is a duplicate — retry
        rejected_titles.append(generated_title)
        if not quiet:
            print(f"  Title '{generated_title}' too similar to existing — retrying ({title_attempt + 1}/{max_title_retries})")

    # All retries exhausted — force uniqueness by appending environment name
    generated_title = story_data.get("episode_title", "A Magical Adventure")
    envs = story_data.get("environments", [])
    primary_env = envs[1]["name"] if len(envs) > 1 else (envs[0]["name"] if envs else "Adventure")
    story_data["episode_title"] = f"{generated_title} of {primary_env}"
    if not quiet:
        print(f"  Forced unique title: {story_data['episode_title']}")

    return story_data


# =============================================================================
# PUBLIC API (for integration with generate_episode.py)
# =============================================================================

def generate_glm_config(
    episode_num: int,
    output_dir: str,
    theme_hint: Optional[str] = None,
    target_minutes: float = 10,
    provider: str = "openai",
) -> dict:
    """Generate a complete story config using LLM API.

    This is the main entry point for generate_episode.py --use-glm.

    Args:
        episode_num: Episode number
        output_dir: Output directory for episode assets
        theme_hint: Optional theme like "crystal caves"
        target_minutes: Target narration length in minutes
        provider: "openai", "local", or "glm"

    Returns:
        Complete story_config dict ready for pipeline
    """
    model_names = {
        "local": "Local LM Studio",
        "openai": f"OpenAI ({OPENAI_MODEL})",
        "glm": f"Z.AI GLM",
    }
    model_name = model_names.get(provider, provider)
    print(f"\n  Generating unique story with {model_name}...")
    print(f"  Target: {target_minutes} minutes, Theme: {theme_hint or 'auto'}")

    # Generate story
    story_data = generate_story(
        theme_hint=theme_hint,
        target_minutes=target_minutes,
        quiet=True,
        provider=provider,
    )

    if not story_data:
        raise RuntimeError("GLM API returned empty response")

    # Build config
    config = build_config(story_data, episode_num, output_dir)

    # Save to history
    save_to_history(story_data, episode_num)

    # Print summary
    print(f"  Title: {config['title']}")
    print(f"  Scenes: {len(config['scenes'])}")
    print(f"  Environments: {len(config['environments'])}")
    narr_words = len(config['narration'].split())
    print(f"  Narration: {narr_words} words (~{narr_words // 130} min)")

    return config


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate unique Luna & Kai episodes using GLM-4.7 AI"
    )
    parser.add_argument("--theme", default=None,
                        help="Optional theme hint (e.g., 'underwater caves', 'sky islands')")
    parser.add_argument("--episode", type=int, default=None,
                        help="Override episode number")
    parser.add_argument("--output", default="story_config.json",
                        help="Output config file path")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory for episode assets")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview what would be generated without calling API")
    parser.add_argument("--run", action="store_true",
                        help="Run the full pipeline after generating config")
    parser.add_argument("--skip-whisk", action="store_true",
                        help="Skip Whisk image generation")
    parser.add_argument("--upload", action="store_true",
                        help="Upload to YouTube after pipeline")

    args = parser.parse_args()

    # Determine episode number
    if args.episode is not None:
        episode_num = args.episode
    else:
        episode_num = load_episode_counter() + 1

    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"output/episodes/luna_kai_ep{episode_num}_{timestamp}"

    # Generate story
    story_data = generate_story(theme_hint=args.theme, dry_run=args.dry_run)

    if args.dry_run:
        print("\n  [DRY RUN] No config generated")
        sys.exit(0)

    # Build config
    config = build_config(story_data, episode_num, output_dir)

    # Write config
    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    # Save counter and history
    save_episode_counter(episode_num)
    save_to_history(story_data, episode_num)

    # Print summary
    print(f"\n  Story Generated!")
    print(f"  Title:        {config['title']}")
    print(f"  Episode:      {episode_num}")
    print(f"  Scenes:       {len(config['scenes'])}")
    print(f"  Environments: {len(config['environments'])}")
    narr_words = len(config['narration'].split())
    print(f"  Narration:    {narr_words} words (~{narr_words // 130} minutes)")
    print(f"  Output dir:   {output_dir}")
    print(f"  Saved to:     {output_path}")
    print()

    # Run pipeline if requested
    if args.run:
        print("  Starting pipeline...")
        import subprocess
        cmd = [
            sys.executable,
            "run_story.py",
            "--config", str(output_path),
            "--output-dir", output_dir,
        ]
        if args.skip_whisk:
            cmd.append("--skip-whisk")
        if args.upload:
            cmd.append("--upload")
        subprocess.run(cmd)
