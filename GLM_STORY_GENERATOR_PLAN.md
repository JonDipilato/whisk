# GLM Story Generator Plan

## Goal
Call Zhipu AI GLM-4 API to generate unique Luna & Kai episodes with the same quality structure as the grandma Excel sheet.

## API Setup
- Endpoint: `https://api.z.ai/api/paas/v4/chat/completions`
- Model: `glm-4.7` (or `glm-4.7-flash` for free)
- Key: `.env` file → `GLM_API_KEY`
- Can use OpenAI SDK with `base_url="https://api.z.ai/api/paas/v4/"`

## Output Format (matches grandma Excel)
```
image | prompt | character_code | environment_code
1     | Luna ref: silver hair, blue eyes... | C1 | E1
2     | Kai ref: brown hair, fox companion... | C2 | E1
3     | Fox companion ref... | C3 | E1
4-80  | Scene prompts with Ghibli style suffix | varies | varies
```

## Characters (fixed for consistency)
- C1 = Luna (silver hair, blue eyes, lantern, gentle)
- C2 = Kai (brown hair, amber eyes, fox companion, adventurous)
- C3 = Fox companion (tiny orange fox)

## Environments (UNIQUE per episode)
GLM generates a new set each time, examples:
- Episode A: village → forest path → crystal caves → underground lake → glowing cavern
- Episode B: village → mountain trail → cloud bridges → floating islands → sky temple
- Episode C: village → river path → waterfall → hidden valley → ancient garden

## Story Structure (77 scenes across 5 acts)
- Act 1 (15): Discovery - village life, noticing something, setting out
- Act 2 (15): Journey - traveling through environments, wonder
- Act 3 (15): Challenge - problem discovered, working to solve
- Act 4 (15): Resolution - success, celebration, gratitude
- Act 5 (17): Return - farewell, journey home, settling in, sleep

## Scene Variety per Act
Each act has mix of:
- C0 (establishing/environment shots) ~30-40%
- C1 (Luna solo moments) ~15%
- C2 (Kai solo moments) ~15%
- C1|2 (both together) ~30-40%
- C3 appears in ~10% of scenes with others

## Prompt Style
Every scene prompt ends with:
`"Ghibli-inspired animated storybook illustration, soft hand-painted digital artwork, clean gentle linework, warm natural hues."`

## File to Create
`glm_story_generator.py` with:
1. `load_api_key()` - from .env
2. `generate_story(theme_hint=None)` - calls GLM, returns structured data
3. `build_config(story_data)` - converts to story_config.json format
4. CLI: `python glm_story_generator.py --run` (generate + run pipeline)

## Integration
Works alongside existing system:
- `generate_episode.py` - template-based (still works, just repetitive)
- `excel_to_config.py` - grandma Excel (still works)
- `glm_story_generator.py` - NEW: unique LLM-generated Luna/Kai episodes
