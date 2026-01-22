"""Progressive storyline test - characters journey through different locations."""
from pathlib import Path
from src.config import load_config
from src.models import Scene, ImageFormat
from src.queue_manager import QueueManager

config = load_config()
manager = QueueManager(config)
manager.load_state()

characters = ["narrator_01", "grandmother_01"]  # Only 2 characters - no cat

# ===== BATCH 1: KITCHEN (starting location) =====
print("\n=== BATCH 1: KITCHEN SCENES ===")

batch1 = [
    Scene(
        scene_id=301,
        environment_id="kitchen_01",
        character_ids=characters,
        prompt="""The narrator and grandmother sitting together at the cozy kitchen table sharing afternoon tea; warm sunlight streaming through fluttering curtains; intimate peaceful moment between grandchild and grandmother; Ghibli-inspired storybook illustration, soft hand-painted digital art, gentle linework.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
    Scene(
        scene_id=302,
        environment_id="kitchen_01",
        character_ids=characters,
        prompt="""Grandmother tenderly pouring more tea for the narrator at the kitchen table; steam rising delicately from ceramic cups; grandmother's loving hands and warm smile; nurturing moment of care; Ghibli-inspired storybook illustration, warm natural hues.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
    Scene(
        scene_id=303,
        environment_id="kitchen_01",
        character_ids=characters,
        prompt="""The narrator and grandmother rising from their chairs at the kitchen table; grandmother affectionately touching the narrator's shoulder; both smiling as they prepare to step outside together; natural continuation of their tea time; Ghibli-inspired storybook illustration, soft gentle linework.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
]

# ===== TRANSITION: KITCHEN TO GARDEN =====
print("\n=== TRANSITION: FULLY OUTSIDE IN GARDEN ===")

transition_1 = Scene(
    scene_id=310,  # Transition scene - NEW GARDEN ENVIRONMENT
    environment_id="kitchen_01",  # Will be replaced with generated garden scene
    character_ids=characters,
    prompt="""The narrator and grandmother standing together in a beautiful sunlit garden; colorful flowers blooming all around them; trees with green leaves providing shade; blue sky above; they have just stepped outside and are marveling at the garden; peaceful outdoor setting; Ghibli-inspired storybook illustration, vibrant natural colors.""",
    image_format=ImageFormat.LANDSCAPE,
)

# ===== BATCH 2: GARDEN (will use generated scene 310 as environment) =====
print("\n=== BATCH 2: GARDEN SCENES (uses scene 310 as environment) ===")
print("WARNING:  IMPORTANT: After generating scene 310, run:")
print("   py prepare_next_batch.py output/scene_310_batch_1/<best_image> garden_01")
print("   Then update environment_id below to 'garden_01'")

batch2 = [
    Scene(
        scene_id=304,
        environment_id="garden_01",  # Garden environment
        character_ids=characters,
        prompt="""The narrator and grandmother standing together in the beautiful sunlit garden; colorful flowers blooming all around them; warm smile between them as they enjoy the peaceful outdoor setting; Ghibli-inspired storybook illustration, vibrant natural colors.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
    Scene(
        scene_id=305,
        environment_id="garden_01",  # Garden environment
        character_ids=characters,
        prompt="""Grandmother bending down tenderly to show the narrator a blooming flower in the garden; narrator leaning in with curiosity and wonder; warm intergenerational teaching moment; Ghibli-inspired storybook illustration, soft natural light.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
    Scene(
        scene_id=306,
        environment_id="garden_01",  # Garden environment
        character_ids=characters,
        prompt="""The narrator and grandmother strolling slowly along the garden path together; trees providing dappled shade; peaceful conversation as they enjoy the garden; natural movement toward garden gate; Ghibli-inspired storybook illustration.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
]

# ===== TRANSITION: GARDEN TO STREET =====
print("\n=== TRANSITION: GARDEN -> STREET ===")

transition_2 = Scene(
    scene_id=311,  # Transition scene
    environment_id="garden_01",  # Starting from garden
    character_ids=characters,
    prompt="""The narrator and grandmother walking through an open garden gate leaving the garden behind; quiet neighborhood street visible ahead; new adventure beginning beyond the garden; Ghibli-inspired storybook illustration.""",
    image_format=ImageFormat.LANDSCAPE,
)

# ===== BATCH 3: STREET (will use generated scene 311 as environment) =====
print("\n=== BATCH 3: STREET SCENES (uses scene 311 as environment) ===")
print("WARNING:  After generating scene 311, run:")
print("   py prepare_next_batch.py output/scene_311_batch_1/<best_image> street_01")
print("   Then update environment_id below to 'street_01'")

batch3 = [
    Scene(
        scene_id=307,
        environment_id="kitchen_01",  # UPDATE TO: "street_01"
        character_ids=characters,
        prompt="""The narrator and grandmother walking along a quiet neighborhood street; small houses and trees lining the road; peaceful afternoon stroll; Ghibli-inspired storybook illustration.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
    Scene(
        scene_id=308,
        environment_id="kitchen_01",  # UPDATE TO: "street_01"
        character_ids=characters,
        prompt="""Grandmother pointing out interesting things along the street; narrator looking with curiosity; exploring the neighborhood together; Ghibli-inspired storybook illustration.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
    Scene(
        scene_id=309,
        environment_id="kitchen_01",  # UPDATE TO: "street_01"
        character_ids=characters,
        prompt="""The narrator and grandmother continuing their walk down the street; journey continuing into the distance; warm golden hour light; Ghibli-inspired storybook illustration.""",
        image_format=ImageFormat.LANDSCAPE,
    ),
]

# Queue all scenes
print("\n" + "="*60)
print("QUEUEING SCENES...")
print("="*60)

# Queue Batch 2 (Garden) + Transition 2 (Garden to Street)
for scene in batch2 + [transition_2]:
    manager.add_scene(scene, batches=1)

print("\n[OK] Queued: Batch 2 (garden) + Transition to street")
print("NOTE: Workflow:")
print("   1. Make sure you've copied scene 310 as garden_01 environment")
print("   2. Run: run.bat process")
print("   3. Pick best image from scene_311_batch_1/")
print("   4. Run: py prepare_next_batch.py output/scene_311_batch_1/<image> street_01")
print("   5. Re-run this file to queue Batch 3 (street)")
