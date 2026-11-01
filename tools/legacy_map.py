#!/usr/bin/env python3
"""Map legacy (1.7.10 - 1.21.8) texture paths onto the 26.3 paths our generators produce.

Writes
  data/aliases.json   {"aliases": {old: new}, "by_version": {old: {"target": new, "versions": [...]}}}
  data/old_only.json  {"compose_from_modern": {...}, "old_layout": {...}, "no_equivalent": {...}, "skip": {...}}

Every legacy path (present in some indexed version but not in 26.3) lands in exactly one of
aliases / compose_from_modern / old_layout / no_equivalent / skip.  Same-named 26.3 paths whose
size or UV layout differed in older versions are additionally listed under old_layout.
"by_version" holds partial aliases for old_layout entries that match the modern layout in some
versions only (e.g. entity/bat is 32x32 = entity/bat/bat from 1.20.3 on).

Only paths, image sizes and .mcmeta data from data/vanilla-*.json are used (no images).

    python3 tools/legacy_map.py          # write both files + summary
    python3 tools/legacy_map.py --check  # summary only
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
VERSIONS = ["1.7.10", "1.8.9", "1.12.2", "1.13.2", "1.14.4", "1.16.5", "1.17.1", "1.19.2",
            "1.20.1", "1.20.4", "1.21.1", "1.21.4", "1.21.8", "26.3"]
OLD_VERSIONS = VERSIONS[:-1]
IDX = {v: json.loads((DATA / f"vanilla-{v}.json").read_text())["textures"] for v in VERSIONS}
MODERN = IDX["26.3"]

COLORS = ["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray", "silver",
          "cyan", "purple", "blue", "brown", "green", "red", "black"]


def col(c):
    return "light_gray" if c == "silver" else c


WOOD = {"oak": "oak", "spruce": "spruce", "birch": "birch", "jungle": "jungle", "acacia": "acacia",
        "big_oak": "dark_oak", "roofed_oak": "dark_oak", "dark_oak": "dark_oak", "darkoak": "dark_oak",
        "wood": "oak"}

# --------------------------------------------------------------------------------------------
# explicit alias tables
# --------------------------------------------------------------------------------------------
BLOCKS = {  # 1.7-1.12 blocks/<name>  ->  block/<name>
    "anvil_base": "anvil", "anvil_top_damaged_0": "anvil_top", "anvil_top_damaged_1": "chipped_anvil_top",
    "anvil_top_damaged_2": "damaged_anvil_top",
    "bed_feet_end": "red_bed_foot_south", "bed_feet_side": "red_bed_foot_east", "bed_feet_top": "red_bed_foot_up",
    "bed_head_end": "bed_head_north", "bed_head_side": "red_bed_head_east", "bed_head_top": "red_bed_head_up",
    "glass_pane_top": "glass_pane_top",
    "brick": "bricks", "cobblestone_mossy": "mossy_cobblestone",
    "command_block": "command_block_side",
    "comparator_off": "comparator", "deadbush": "dead_bush",
    "dirt_podzol_side": "podzol_side", "dirt_podzol_top": "podzol_top",
    "dispenser_front_horizontal": "dispenser_front", "dropper_front_horizontal": "dropper_front",
    "door_iron_lower": "iron_door_bottom", "door_iron_upper": "iron_door_top",
    "double_plant_fern_bottom": "large_fern_bottom", "double_plant_fern_top": "large_fern_top",
    "double_plant_grass_bottom": "tall_grass_bottom", "double_plant_grass_top": "tall_grass_top",
    "double_plant_paeonia_bottom": "peony_bottom", "double_plant_paeonia_top": "peony_top",
    "double_plant_rose_bottom": "rose_bush_bottom", "double_plant_rose_top": "rose_bush_top",
    "double_plant_sunflower_back": "sunflower_back", "double_plant_sunflower_bottom": "sunflower_bottom",
    "double_plant_sunflower_front": "sunflower_front", "double_plant_sunflower_top": "sunflower_top",
    "double_plant_syringa_bottom": "lilac_bottom", "double_plant_syringa_top": "lilac_top",
    "end_bricks": "end_stone_bricks",
    "endframe_eye": "end_portal_frame_eye", "endframe_side": "end_portal_frame_side",
    "endframe_top": "end_portal_frame_top",
    "farmland_dry": "farmland", "farmland_wet": "farmland_moist",
    "fire_layer_0": "fire_0", "fire_layer_1": "fire_1",
    "flower_allium": "allium", "flower_blue_orchid": "blue_orchid", "flower_dandelion": "dandelion",
    "flower_houstonia": "azure_bluet", "flower_oxeye_daisy": "oxeye_daisy", "flower_rose": "poppy",
    "flower_tulip_orange": "orange_tulip", "flower_tulip_pink": "pink_tulip", "flower_tulip_red": "red_tulip",
    "flower_tulip_white": "white_tulip",
    "furnace_front_off": "furnace_front",
    "grass_path_side": "dirt_path_side", "grass_path_top": "dirt_path_top",
    "grass_side": "grass_block_side", "grass_side_overlay": "grass_block_side_overlay",
    "grass_side_snowed": "grass_block_snow", "grass_top": "grass_block_top",
    "hardened_clay": "terracotta", "ice_packed": "packed_ice", "itemframe_background": "item_frame",
    "melon_stem_connected": "attached_melon_stem", "melon_stem_disconnected": "melon_stem",
    "mob_spawner": "spawner",
    "mushroom_block_skin_brown": "brown_mushroom_block", "mushroom_block_skin_red": "red_mushroom_block",
    "mushroom_block_skin_stem": "mushroom_stem",
    "mushroom_brown": "brown_mushroom", "mushroom_red": "red_mushroom",
    "nether_brick": "nether_bricks", "noteblock": "note_block", "observer_back_lit": "observer_back_on",
    "piston_top_normal": "piston_top", "portal": "nether_portal",
    "prismarine_dark": "dark_prismarine", "prismarine_rough": "prismarine",
    "pumpkin_face_off": "carved_pumpkin", "pumpkin_face_on": "jack_o_lantern",
    "pumpkin_stem_connected": "attached_pumpkin_stem", "pumpkin_stem_disconnected": "pumpkin_stem",
    "purpur_pillar": "purpur_pillar_side",
    "quartz_block_chiseled": "chiseled_quartz_block", "quartz_block_chiseled_top": "chiseled_quartz_block_top",
    "quartz_block_lines": "quartz_pillar_side", "quartz_block_lines_top": "quartz_pillar_top",
    "quartz_ore": "nether_quartz_ore",
    "rail_activator": "activator_rail", "rail_activator_powered": "activator_rail_on",
    "rail_detector": "detector_rail", "rail_detector_powered": "detector_rail_on",
    "rail_golden": "powered_rail", "rail_golden_powered": "powered_rail_on",
    "rail_normal": "rail", "rail_normal_turned": "rail_corner",
    "red_nether_brick": "red_nether_bricks",
    "red_sandstone_carved": "chiseled_red_sandstone", "red_sandstone_normal": "red_sandstone",
    "red_sandstone_smooth": "cut_red_sandstone",
    "redstone_dust_line": "redstone_dust_line0",
    "redstone_dust_cross_overlay": "redstone_dust_overlay", "redstone_dust_line_overlay": "redstone_dust_overlay",
    "redstone_lamp_off": "redstone_lamp", "redstone_torch_on": "redstone_torch",
    "reeds": "sugar_cane", "repeater_off": "repeater",
    "sandstone_carved": "chiseled_sandstone", "sandstone_normal": "sandstone", "sandstone_smooth": "cut_sandstone",
    "slime": "slime_block", "sponge_wet": "wet_sponge",
    "stone_andesite": "andesite", "stone_andesite_smooth": "polished_andesite",
    "stone_diorite": "diorite", "stone_diorite_smooth": "polished_diorite",
    "stone_granite": "granite", "stone_granite_smooth": "polished_granite",
    "stone_slab_side": "smooth_stone_slab_side", "stone_slab_top": "smooth_stone",
    "stonebrick": "stone_bricks", "stonebrick_carved": "chiseled_stone_bricks",
    "stonebrick_cracked": "cracked_stone_bricks", "stonebrick_mossy": "mossy_stone_bricks",
    "tallgrass": "short_grass", "torch_on": "torch", "trapdoor": "oak_trapdoor",
    "trip_wire": "tripwire", "trip_wire_source": "tripwire_hook",
    "waterlily": "lily_pad", "web": "cobweb",
}
BLOCK_RULES = [  # (regex on legacy name, replacement producing modern name)
    (r"^(beetroots|carrots|cocoa|nether_wart|potatoes|wheat)_stage_(\d)$", r"\1_stage\2"),
    (r"^door_(\w+?)_lower$", lambda m: f"{WOOD[m[1]]}_door_bottom"),
    (r"^door_(\w+?)_upper$", lambda m: f"{WOOD[m[1]]}_door_top"),
    (r"^planks_(\w+)$", lambda m: f"{WOOD[m[1]]}_planks"),
    (r"^log_(\w+?)_top$", lambda m: f"{WOOD[m[1]]}_log_top"),
    (r"^log_(\w+)$", lambda m: f"{WOOD[m[1]]}_log"),
    (r"^leaves_(\w+?)$", lambda m: f"{WOOD[m[1]]}_leaves"),
    (r"^sapling_(\w+)$", lambda m: f"{WOOD[m[1]]}_sapling"),
    (r"^wool_colored_(\w+)$", lambda m: f"{col(m[1])}_wool"),
    (r"^hardened_clay_stained_(\w+)$", lambda m: f"{col(m[1])}_terracotta"),
    (r"^glazed_terracotta_(\w+)$", lambda m: f"{col(m[1])}_glazed_terracotta"),
    (r"^concrete_powder_(\w+)$", lambda m: f"{col(m[1])}_concrete_powder"),
    (r"^concrete_(\w+)$", lambda m: f"{col(m[1])}_concrete"),
    (r"^glass_pane_top_(\w+)$", lambda m: f"{col(m[1])}_stained_glass_pane_top"),
    (r"^glass_(\w+)$", lambda m: f"{col(m[1])}_stained_glass"),
    (r"^shulker_top_(\w+)$", lambda m: f"{col(m[1])}_shulker_box"),
]

DYE = {"black": "ink_sac", "blue": "lapis_lazuli", "brown": "cocoa_beans", "white": "bone_meal"}
ITEMS = {  # 1.7-1.12 items/<name>  ->  item/<name>
    "apple_golden": "golden_apple", "boat": "oak_boat",
    "beef_cooked": "cooked_beef", "beef_raw": "beef",
    "book_enchanted": "enchanted_book", "book_normal": "book", "book_writable": "writable_book",
    "book_written": "written_book", "bow_standby": "bow", "broken_elytra": "elytra_broken",
    "bucket_empty": "bucket", "bucket_lava": "lava_bucket", "bucket_milk": "milk_bucket",
    "bucket_water": "water_bucket", "carrot_golden": "golden_carrot",
    "chicken_cooked": "cooked_chicken", "chicken_raw": "chicken", "chorus_fruit_popped": "popped_chorus_fruit",
    "door_iron": "iron_door", "fireball": "fire_charge", "fireworks": "firework_rocket",
    "fireworks_charge": "firework_star", "fireworks_charge_overlay": "firework_star_overlay",
    "fish_clownfish_raw": "tropical_fish", "fish_cod_cooked": "cooked_cod", "fish_cod_raw": "cod",
    "fish_pufferfish_raw": "pufferfish", "fish_salmon_cooked": "cooked_salmon", "fish_salmon_raw": "salmon",
    "fishing_rod_uncast": "fishing_rod",
    "map_empty": "map", "map_filled": "filled_map",
    "melon": "melon_slice", "melon_speckled": "glistering_melon_slice",
    "minecart_chest": "chest_minecart", "minecart_command_block": "command_block_minecart",
    "minecart_furnace": "furnace_minecart", "minecart_hopper": "hopper_minecart",
    "minecart_normal": "minecart", "minecart_tnt": "tnt_minecart",
    "mutton_cooked": "cooked_mutton", "mutton_raw": "mutton", "netherbrick": "nether_brick",
    "porkchop_cooked": "cooked_porkchop", "porkchop_raw": "porkchop",
    "potato_baked": "baked_potato", "potato_poisonous": "poisonous_potato",
    "potion_bottle_drinkable": "potion", "potion_bottle_empty": "glass_bottle",
    "potion_bottle_lingering": "lingering_potion", "potion_bottle_splash": "splash_potion",
    "rabbit_cooked": "cooked_rabbit", "rabbit_raw": "rabbit",
    "redstone_dust": "redstone", "reeds": "sugar_cane",
    "seeds_melon": "melon_seeds", "seeds_pumpkin": "pumpkin_seeds", "seeds_wheat": "wheat_seeds",
    "sign": "oak_sign", "slimeball": "slime_ball", "spider_eye_fermented": "fermented_spider_eye",
    "totem": "totem_of_undying", "wooden_armorstand": "armor_stand",
    "empty_armor_slot_boots": "../gui/sprites/container/slot/boots",
    "empty_armor_slot_chestplate": "../gui/sprites/container/slot/chestplate",
    "empty_armor_slot_helmet": "../gui/sprites/container/slot/helmet",
    "empty_armor_slot_leggings": "../gui/sprites/container/slot/leggings",
    "empty_armor_slot_shield": "../gui/sprites/container/slot/shield",
}
ITEM_RULES = [
    (r"^gold_(axe|boots|chestplate|helmet|hoe|horse_armor|leggings|pickaxe|shovel|sword)$", r"golden_\1"),
    (r"^wood_(axe|hoe|pickaxe|shovel|sword)$", r"wooden_\1"),
    (r"^record_(\w+)$", r"music_disc_\1"),
    (r"^door_(\w+)$", lambda m: f"{WOOD[m[1]]}_door"),
    (r"^dye_powder_(\w+)$", lambda m: DYE.get(m[1], f"{col(m[1])}_dye")),
]

FULL = {  # full-path aliases (1.13+ renames, entity / gui / misc moves)
    "block/chain": "block/iron_chain", "item/chain": "item/iron_chain",
    "block/creaking_heart_active": "block/creaking_heart_awake",
    "block/creaking_heart_top_active": "block/creaking_heart_top_awake",
    "block/grass": "block/short_grass",
    "block/grass_path_side": "block/dirt_path_side", "block/grass_path_top": "block/dirt_path_top",
    "block/purpur_pillar": "block/purpur_pillar_side", "block/quartz_pillar": "block/quartz_pillar_side",
    "block/stone_slab_side": "block/smooth_stone_slab_side", "block/stone_slab_top": "block/smooth_stone",
    "item/broken_elytra": "item/elytra_broken",
    "item/cactus_green": "item/green_dye", "item/dandelion_yellow": "item/yellow_dye", "item/rose_red": "item/red_dye",
    "item/light": "item/light_15", "item/scute": "item/turtle_scute", "item/sign": "item/oak_sign",
    "item/empty_armor_slot_boots": "gui/sprites/container/slot/boots",
    "item/empty_armor_slot_chestplate": "gui/sprites/container/slot/chestplate",
    "item/empty_armor_slot_helmet": "gui/sprites/container/slot/helmet",
    "item/empty_armor_slot_leggings": "gui/sprites/container/slot/leggings",
    "item/empty_armor_slot_shield": "gui/sprites/container/slot/shield",
    # entity
    "entity/alex": "entity/player/slim/alex",
    "entity/armadillo": "entity/armadillo/armadillo",
    "entity/armorstand/wood": "entity/armorstand/armorstand",
    "entity/arrow": "entity/projectiles/arrow",
    "entity/banner_base": "entity/banner/banner_base",
    "entity/beacon_beam": "entity/beacon/beacon_beam",
    "entity/blaze": "entity/blaze/blaze",
    "entity/chicken": "entity/chicken/chicken_temperate",
    "entity/chicken/cold_chicken": "entity/chicken/chicken_cold",
    "entity/chicken/temperate_chicken": "entity/chicken/chicken_temperate",
    "entity/chicken/warm_chicken": "entity/chicken/chicken_warm",
    "entity/cow/cold_cow": "entity/cow/cow_cold", "entity/cow/temperate_cow": "entity/cow/cow_temperate",
    "entity/cow/warm_cow": "entity/cow/cow_warm",
    "entity/dolphin": "entity/dolphin/dolphin",
    "entity/elytra": "entity/equipment/wings/elytra",
    "entity/enchanting_table_book": "entity/enchantment/enchanting_table_book",
    "entity/end_gateway_beam": "entity/end_portal/end_gateway_beam",
    "entity/end_portal": "entity/end_portal/end_portal",
    "entity/endercrystal/endercrystal": "entity/end_crystal/end_crystal",
    "entity/endercrystal/endercrystal_beam": "entity/end_crystal/end_crystal_beam",
    "entity/endermite": "entity/endermite/endermite",
    "entity/experience_orb": "entity/experience/experience_orb",
    "entity/fishing_hook": "entity/fishing/fishing_hook",
    "entity/fox/snow_fox": "entity/fox/fox_snow", "entity/fox/snow_fox_sleep": "entity/fox/fox_snow_sleep",
    "entity/frog/cold_frog": "entity/frog/frog_cold", "entity/frog/temperate_frog": "entity/frog/frog_temperate",
    "entity/frog/warm_frog": "entity/frog/frog_warm",
    "entity/guardian": "entity/guardian/guardian", "entity/guardian_beam": "entity/guardian/guardian_beam",
    "entity/guardian_elder": "entity/guardian/guardian_elder",
    "entity/horse/armor/horse_armor_leather": "entity/equipment/horse_body/leather",
    "entity/illager/fangs": "entity/illager/evoker_fangs",
    "entity/illager/illusionist": "entity/illager/illusioner",
    "entity/iron_golem": "entity/iron_golem/iron_golem",
    "entity/lead_knot": "entity/lead_knot/lead_knot",
    "entity/llama/spit": "entity/llama/llama_spit",
    "entity/llama/decor/trader_llama": "entity/equipment/llama_body/trader_llama",
    "entity/minecart": "entity/minecart/minecart",
    "entity/phantom": "entity/phantom/phantom", "entity/phantom_eyes": "entity/phantom/phantom_eyes",
    "entity/pig/cold_pig": "entity/pig/pig_cold", "entity/pig/temperate_pig": "entity/pig/pig_temperate",
    "entity/pig/warm_pig": "entity/pig/pig_warm",
    "entity/projectiles/spectral_arrow": "entity/projectiles/arrow_spectral",
    "entity/projectiles/tipped_arrow": "entity/projectiles/arrow_tipped",
    "entity/sheep/sheep_fur": "entity/sheep/sheep_wool",
    "entity/shield_base": "entity/shield/shield_base",
    "entity/shield_base_nopattern": "entity/shield/shield_base_nopattern",
    "entity/shulker/shulker_silver": "entity/shulker/shulker_light_gray",
    "entity/silverfish": "entity/silverfish/silverfish",
    "entity/snow_golem": "entity/snow_golem/snow_golem", "entity/snowman": "entity/snow_golem/snow_golem",
    "entity/spider_eyes": "entity/spider/spider_eyes",
    "entity/squid": "entity/squid/squid",
    "entity/strider/strider_saddle": "entity/equipment/strider_saddle/saddle",
    "entity/trident": "entity/trident/trident", "entity/trident_riptide": "entity/trident/trident_riptide",
    "entity/turtle/big_sea_turtle": "entity/turtle/turtle",
    "entity/wandering_trader": "entity/wandering_trader/wandering_trader",
    "entity/witch": "entity/witch/witch",
    "entity/wolf/wolf_armor": "entity/equipment/wolf_body/armadillo_scute",
    "entity/wolf/wolf_armor_overlay": "entity/equipment/wolf_body/armadillo_scute_overlay",
    "environment/sun": "environment/celestial/sun",
    # gui
    "gui/checkmark": "gui/sprites/icon/checkmark",
    "gui/info_icon": "gui/sprites/icon/info",
    "gui/unseen_notification": "gui/sprites/icon/unseen_notification",
    "gui/sprites/container/inventory/effect_background_small": "gui/sprites/container/inventory/effect_background",
    "gui/sprites/container/loom/banner_slot": "gui/sprites/container/slot/banner",
    "gui/sprites/container/loom/dye_slot": "gui/sprites/container/slot/dye",
    "gui/sprites/container/loom/pattern_slot": "gui/sprites/container/slot/banner_pattern",
    # misc (glints are tiling textures sampled with a texture matrix: resolution is free)
    "misc/enchanted_item_glint": "misc/enchanted_glint_item",
    "misc/enchanted_glint_entity": "misc/enchanted_glint_armor",
    # armor models (1.21.2 equipment move)
    "models/armor/leather_layer_1_overlay": "entity/equipment/humanoid/leather_overlay",
    "models/armor/leather_layer_2_overlay": "entity/equipment/humanoid_leggings/leather_overlay",
    "models/armor/turtle_layer_1": "entity/equipment/humanoid/turtle_scute",
    "trims/color_palettes/trim_palette": "palettes/trim_base",
}
TILING = {"misc/enchanted_item_glint"}  # size may differ: resolution-independent tiling texture

FULL_RULES = [
    (r"^entity/boat/boat_(\w+)$", lambda m: f"entity/boat/{WOOD[m[1]]}"),
    (r"^entity/cat/(all_black|black|british_shorthair|calico|jellie|persian|ragdoll|red|siamese|tabby|white)$",
     r"entity/cat/cat_\1"),
    (r"^entity/llama/(brown|creamy|gray|white)$", r"entity/llama/llama_\1"),
    (r"^entity/llama/decor/decor_(\w+)$", lambda m: f"entity/equipment/llama_body/{col(m[1])}"),
    (r"^entity/llama/decor/(\w+)$", r"entity/equipment/llama_body/\1"),
    (r"^entity/panda/(\w+)_panda$", r"entity/panda/panda_\1"),
    (r"^entity/rabbit/(\w+)$", r"entity/rabbit/rabbit_\1"),  # validated -> fails (layout change)
    (r"^models/armor/(\w+)_layer_1$", lambda m: f"entity/equipment/humanoid/{m[1]}"),
    (r"^models/armor/(\w+)_layer_2$", lambda m: f"entity/equipment/humanoid_leggings/{m[1]}"),
    (r"^item/empty_slot_(\w+)$", r"gui/sprites/container/slot/\1"),
    (r"^trims/color_palettes/(\w+)$", r"palettes/trim/\1"),
    (r"^trims/models/armor/(\w+)_leggings$", r"trims/entity/humanoid_leggings/\1"),
    (r"^trims/models/armor/(\w+)$", r"trims/entity/humanoid/\1"),
]

# --------------------------------------------------------------------------------------------
# non-alias classifications (notes are guidance for the compose/legacy generators)
# --------------------------------------------------------------------------------------------
BED_NOTE = ("1.12-1.21.8 bed entity sheet 64x64: head slab box texOffs(0,0) 16x16x6 -> top/sleeping face "
            "(6,6) 16x16, underside (28,6) 16x16, sides (0,6) and (22,6) 6x16, head end (6,0) 16x6; foot slab "
            "texOffs(0,22): top (6,28), underside (28,28), sides (0,28)/(22,28), foot end (22,22) 16x6; legs 3x3x3 "
            "at (50,0),(50,6),(50,12),(50,18). Compose from block/{c}_bed_head_up/_foot_up (tops), "
            "block/{c}_bed_head_east/_west and _foot_east/_west (6-px slab band of the side faces, rotated 90deg), "
            "block/{c}_bed_foot_south + block/bed_head_north (end bands), block/bed_down (undersides, legs).")
CHEST_DOUBLE = ("pre-1.15 double chest 128x64 (lid box 30x5x14 texOffs(0,0), bottom 30x10x14 texOffs(0,19), latch "
                "2x4x1 texOffs(0,0)). Compose from entity/chest/{k}_left + {k}_right (64x64 halves, 1.15+ layout): "
                "left half -> x 0..14 + 44..58 columns, right half -> the mirrored columns; i.e. rebuild each box's "
                "faces by concatenating the matching half-faces (front/back/top/bottom widths 15+15, sides from the "
                "outer half).")
VILLAGER_COMPOSE = ("pre-1.14 full villager texture (64x64, same UV as 1.14 villager base + robe). Compose: "
                    "entity/villager/villager (base) + entity/villager/type/plains + entity/villager/profession/{p} "
                    "layered in that order (all 64x64, same UV).")
ZVILLAGER_COMPOSE = ("1.11-1.13 full zombie-villager texture (64x64). Compose: entity/zombie_villager/zombie_villager + "
                     "entity/zombie_villager/type/plains + entity/zombie_villager/profession/{p} (same 64x64 UV).")
PARTICLES = ("legacy particle sheet, 16x16 grid (cell = width/16: 8 px at 128x128; 1.13.2's 256x256 is assumed to "
             "be the same 16x16 grid at 16 px cells - verify). Cell (col,row): row0 c0-7 particle/generic_7..0 "
             "(index 7-age), row1 c3-6 splash_0..3, row2 c0 bubble, c1 fishing hook (entity/fishing/fishing_hook, "
             "pre-1.14), row3 c0 flame, c1 lava, row4 c0 note, c1 critical_hit, c2 enchanted_hit, c3 damage (1.9+), "
             "row5 c0 heart, c1 angry, c2 glint (happy villager), row7 c0-2 drip_hang/drip_fall/drip_land, row8 c0-7 "
             "effect_7..0, row9 c0-7 spell_7..0 (witch), row10 c0-7 spark_0..7 (firework), row11 c0-7 glitter_0..7 "
             "(end rod, 1.9+), rows14-15 c1-26 (indices 225-250) sga_a..z; firework flash 16x16 at (32,16)-px of "
             "128 sheet = particle/flash downscaled. Unlisted cells transparent.")
MAP_ICONS = ("8x8 icons in a grid of width/8 columns (4 cols at 32x32 for 1.7-1.12, 16 cols at 128x128 for "
             "1.13-1.20.4); icon i at ((i%cols)*8,(i//cols)*8). Order from map/decorations/: 0 player, 1 frame, "
             "2 red_marker, 3 blue_marker, 4 target_x, 5 target_point, 6 player_off_map, 7 player_off_limits, "
             "8 woodland_mansion, 9 ocean_monument, 10-25 {white,orange,magenta,light_blue,yellow,lime,pink,gray,"
             "light_gray,cyan,purple,blue,brown,green,red,black}_banner, 26 red_x, 27 desert_village, "
             "28 plains_village, 29 savanna_village, 30 snowy_village, 31 taiga_village, 32 jungle_temple, "
             "33 swamp_hut, 34 trial_chambers (1.20.5+).")
KZ = ("1.7-1.13 painting atlas 256x256 (16 px per block). From painting/*: kebab(0,0) aztec(16,0) alban(32,0) "
      "aztec2(48,0) bomb(64,0) plant(80,0) wasteland(96,0) [16x16]; pool(0,32) courbet(32,32) sea(64,32) "
      "sunset(96,32) creebet(128,32) [32x16]; wanderer(0,64) graham(16,64) [16x32]; fighters(0,96) [64x32]; "
      "match(0,128) bust(32,128) stage(64,128) void(96,128) skull_and_roses(128,128) wither(160,128) [32x32]; "
      "pointer(0,192) pigscene(64,192) burning_skull(128,192) [64x64]; skeleton(192,64) donkey_kong(192,112) "
      "[64x48]; back: painting/back tiled 4x4 at (192,0) 64x64.")

COMPOSE = {
    "items/bed": "1.7-1.8 flat red bed item icon 16x16 (26.3 has no bed item sprite): draw a small isometric/"
                 "side view from block/red_bed_head_up, red_bed_foot_up and the side faces",
    "blocks/redstone_dust_cross": "1.7-1.8 four-way dust: union of block/redstone_dust_line0, line1 (or line0 "
                                  "rotated 90deg) and block/redstone_dust_dot",
    "items/clock": "1.7-1.8 animated strip 16x1024 = item/clock_00..63 stacked vertically (frame i at y=16*i), "
                   "frame order driven by the game (keep the .mcmeta without frametime)",
    "items/compass": "1.7-1.8 animated strip 16x512 = item/compass_00..31 stacked vertically (frame i at y=16*i)",
    "entity/explosion": "1.7-1.13 explosion sheet 128x128 = particle/explosion_0..15 (32x32) in a 4x4 grid, "
                        "frame i at ((i%4)*32,(i//4)*32)",
    "entity/sweep": "1.9-1.13 sweep sheet 128x32: 8 frames in a 4x2 grid of 32x16 cells (frame i at "
                    "((i%4)*32,(i//4)*16)); from particle/sweep_0..7 (32x32) squeezed 2:1 vertically (verify)",
    "environment/moon_phases": "128x64 = 4x2 grid of 32x32 from environment/celestial/moon/: (0,0) full_moon, "
                               "(32,0) waning_gibbous, (64,0) third_quarter, (96,0) waning_crescent, (0,32) new_moon, "
                               "(32,32) waxing_crescent, (64,32) first_quarter, (96,32) waxing_gibbous",
    "map/map_icons": MAP_ICONS,
    "painting/paintings_kristoffer_zetterstrand": KZ,
    "particle/particles": PARTICLES,
    # gui sheets (pre-1.20.2 sprite atlases)
    "gui/widgets": "256x256: hud/hotbar (0,0) 182x22; hud/hotbar_selection (0,22) 24x24 (sprite is 24x23 - pad "
                   "last row); hud/hotbar_offhand_left (24,22) 29x24, hud/hotbar_offhand_right (53,22) 29x24 (1.9+); "
                   "widget/button_disabled (0,46), widget/button (0,66), widget/button_highlighted (0,86) 200x20; "
                   "language button (0,106) normal / (0,126) highlighted 20x20 = widget/button(_highlighted) "
                   "nine-sliced to 20x20 + icon/language centered; lock button 20x20 (1.14+): "
                   "widget/locked_button (0,146), _highlighted (0,166), _disabled (0,186), unlocked_button(_..) at "
                   "x=20 same rows",
    "gui/icons": "256x256: hud/crosshair (0,0) 15x15; hearts row y=0 (hardcore row y=45), 9x9: heart/container "
                 "(16), container_blinking (25), full (52), half (61), full_blinking (70), half_blinking (79), "
                 "poisoned_full (88), poisoned_half (97), poisoned_*_blinking (106,115), withered_full (124), "
                 "withered_half (133), withered_*_blinking (142,151), absorbing_full (160), absorbing_half (169), "
                 "frozen_full (178), frozen_half (187) [1.17+]; vehicle hearts y=9: vehicle_container (52), "
                 "vehicle_full (88), vehicle_half (97); armor y=9: armor_empty (16), armor_half (25), armor_full (34); "
                 "air y=18: air (16), air_bursting (25); food y=27: food_empty (16), food_empty_hunger (133), "
                 "food_full (52), food_half (61), food_full_hunger (88), food_half_hunger (97); "
                 "experience_bar_background (0,64) / _progress (0,69) 182x5; jump_bar_background (0,84) / "
                 "_progress (0,89) 182x5; attack indicator (1.9+) y=94: hotbar_attack_indicator_background (0) / "
                 "_progress (18) 18x18, crosshair_attack_indicator_background (36) / _progress (52) 16x4, "
                 "crosshair_attack_indicator_full (68) 16x16; ping (0,176+8*k) 10x8: k=0 ping_5 .. k=4 ping_1, "
                 "k=5 unreachable; pinging_1..5 at x=10 same rows (from server_list/*)",
    "gui/bars": "256x256 boss bars from boss_bar/*, 182x5 each: colour c (pink,blue,red,green,yellow,purple,white "
                "= 0..6) background at (0,10c), progress at (0,10c+5); overlays notched_6,10,12,20 (k=0..3) "
                "background at (0,80+10k), progress at (0,85+10k)",
    "gui/accessibility": "1.14-1.20.1 32x64: accessibility button 20x20 at (0,0) normal, (0,20) highlighted "
                         "(texture 32x64) = widget/button(_highlighted) nine-sliced to 20x20 + icon/accessibility "
                         "centered",
    "gui/advancements/tabs": "256x256 from advancements/tab_*: above (28x32) left/middle/right at x=0,28,56, "
                             "y=0 unselected / 32 selected; below (28x32) at x=84,112,140, y=0/32; left (32x28) "
                             "top/middle/bottom at x=0,32,64, y=64/92; right (32x28) at x=96,128,160, y=64/92",
    "gui/advancements/widgets": "256x256: title box obtained (0,0) / unobtained (0,26) 200x26 (advancements/"
                                "box_obtained, box_unobtained); description box (0,52) 200x26 (title_box); frames "
                                "26x26 at y=128 obtained / y=154 unobtained, x=0 task, 26 challenge, 52 goal",
    "gui/chat_tags": "1.19-1.20.1 32x32: icon/chat_modified 9x9 at (0,0)",
    "gui/checkbox": "1.14.4 32x64: checkbox (0,0), checkbox_selected (0,20); 1.15-1.20.1 64x64: u=20 if "
                    "highlighted, v=20 if selected -> checkbox (0,0), _highlighted (20,0), _selected (0,20), "
                    "_selected_highlighted (20,20) (widget/checkbox*)",
    "gui/container/bundle": "1.17-1.20.1 128x128 bundle tooltip: slot 18x20 at (0,0), blocked slot at (0,40), "
                            "1-px border strips at (0,18)/(0,20)/(0,60). Build from container/slot (18x18 + 2 px "
                            "bottom extension) and crafter/disabled_slot",
    "gui/container/creative_inventory/tabs": "256x256 from container/creative_inventory/tab_*_N (26x32): column c "
                                             "(0..5, 0..6 in 1.19.3+) at x=28c; y=0 top_unselected, 32 "
                                             "top_selected, 64 bottom_unselected, 96 bottom_selected; N=c+1",
    "gui/container/recipe_background": "1.12 recipe-book overlay sheet (uncertain layout): overlay popup from "
                                       "recipe_book/overlay_recipe nine-slice, slot buttons from recipe_book/"
                                       "crafting_overlay*",
    "gui/container/stats_icons": "128x128 from statistics/* (18x18): slot (container/slot) (0,0), sort_down (18,0), "
                                 "sort_up (36,0), header (0,18); icons y=18: item_crafted (18), item_used (36), "
                                 "block_mined (54), item_broken (72), item_picked_up (90), item_dropped (108) "
                                 "(verify order)",
    "gui/container/villager2": "1.14-1.20.1 512x256 = gui/container/villager background (0,0 276x166) + "
                               "villager/out_of_stock 28x21 at (311,0), discount_strikethrough 9x2 at (0,176), "
                               "trade_arrow 10x9 at (15,171), trade_arrow_out_of_stock (25,171), "
                               "experience_bar_background 102x5 (0,186), experience_bar_current (0,191), "
                               "experience_bar_result (0,181), scroller 6x27 (0,199), scroller_disabled (6,199) "
                               "(verify coordinates)",
    "gui/demo_background": "248x166 plain window panel at (0,0): standard GUI frame (same style as the "
                           "gui/container/* backgrounds); 26.3 has no demo sheet",
    "gui/light_dirt_background": "1.20 tiled lighter dirt (16x16): block/dirt brightened (game draws it untinted)",
    "gui/options_background": "1.7-1.20.4 tiled menu background 16x16 = block/dirt (the game darkens it); "
                              "26.3 gui/menu_background is a translucent tile, not a substitute",
    "gui/recipe_button": "1.13-1.20.1 256x256: recipe_book/button 20x18 at (0,0), button_highlighted at (0,19)",
    "gui/report_button": "1.19-1.20.1 64x64: social_interactions/report_button (0,0), _highlighted (0,20), "
                         "_disabled (0,40), 20x20",
    "gui/resource_packs": "256x256 from transferable_list/* (32x32): select (0,0) / select_highlighted (0,32), "
                          "unselect (32,0)/(32,32), move_down (64,0)/(64,32), move_up (96,0)/(96,32) "
                          "(up/down arrows use the top/bottom 16 px halves)",
    "gui/server_selection": "256x256 from server_list/* (32x32): join (0,0)/join_highlighted (0,32), "
                            "move_down (64,0)/(64,32), move_up (96,0)/(96,32)",
    "gui/slider": "1.20.1 256x256: widget/slider (0,0), slider_highlighted (0,20) 200x20; slider_handle (0,40), "
                  "slider_handle_highlighted (0,60) (handle 8x20 nine-sliced to 200x20 in the sheet)",
    "gui/social_interactions": "1.16-1.20.1 256x256: social_interactions/background (nine-slice) top-left, "
                               "mute/unmute buttons 20x20 with highlighted state below, report button; exact "
                               "coordinates unverified",
    "gui/spectator_widgets": "256x256 16x16 icons at y=0 from spectator/*: teleport_to_player (0), "
                             "teleport_to_team (16), close (128), scroll_left (144), scroll_right (160)",
    "gui/tab_button": "1.20.1 256x256 from widget/tab* (130x24) stacked at x=0: tab_selected (0), "
                      "tab_selected_highlighted (24), tab (48), tab_highlighted (72) (verify order)",
    "gui/toasts": "256x256 from toast/* : advancement (0,0), recipe (0,32), system (0,64; 26.3 sprite is "
                  "160x64 - take the nine-slice ends), tutorial (0,96), 160x32; tutorial icons 20x20 at "
                  "(176+20x,20y): movement_keys (0,0), mouse (1,0), tree (2,0), recipe_book (0,1), wooden_planks "
                  "(1,1), social_interactions (2,1), right_click (3,1)",
    "gui/world_selection": "256x256 from world_list/* (32x32): join (0,0), marked_join (32,0), warning (64,0), "
                           "error (96,0); _highlighted variants at y=32",
    "gui/achievement/achievement_background": "1.7-1.8 achievements window 256x202 at (0,0) (frame like "
                                              "gui/advancements/window) + achievement frames 26x26 at (0,202) "
                                              "normal and (26,202) special (advancements/task_frame_obtained, "
                                              "challenge_frame_obtained) + toast 160x32 at (96,202) (toast/"
                                              "advancement)",
    "gui/sprites/container/bundle/slot": "1.20.2-1.21.1 18x20 bundle tooltip slot: container/slot (18x18) + "
                                         "2-px bottom extension",
    "gui/sprites/container/bundle/blocked_slot": "1.20.2-1.21.1 18x20: bundle slot + crafter/disabled_slot",
    "gui/sprites/container/horse/armor_slot": "1.20.2-1.21.1 18x18 = container/slot + slot/horse_armor at (1,1)",
    "gui/sprites/container/horse/llama_armor_slot": "1.20.2-1.21.1 18x18 = container/slot + slot/llama_armor "
                                                    "at (1,1)",
    "gui/sprites/container/horse/saddle_slot": "1.20.2-1.21.1 18x18 = container/slot + slot/saddle at (1,1)",
    "gui/sprites/container/inventory/effect_background_large": "1.20.2-1.21.8 120x32: container/inventory/"
                                                               "effect_background (32x32) nine-sliced to 120x32",
    "gui/sprites/player_list/make_operator_highlighted": "1.20.4 8x7: player_list/make_operator brightened",
    "gui/sprites/player_list/remove_operator_highlighted": "1.20.4 8x7: player_list/remove_operator brightened",
    "gui/sprites/player_list/remove_player_highlighted": "1.20.4 8x7: player_list/remove_player brightened",
}
for c in COLORS + ["light_gray"]:
    COMPOSE[f"entity/bed/{c}"] = BED_NOTE.replace("{c}", col(c))
for k in ["normal", "trapped", "christmas"]:
    COMPOSE[f"entity/chest/{k}_double"] = CHEST_DOUBLE.replace("{k}", k)
for old, new in {"butcher": "butcher", "farmer": "farmer", "librarian": "librarian", "priest": "cleric",
                 "smith": "weaponsmith"}.items():
    COMPOSE[f"entity/villager/{old}"] = VILLAGER_COMPOSE.replace("{p}", new)
    COMPOSE[f"entity/zombie_villager/zombie_{old}"] = ZVILLAGER_COMPOSE.replace("{p}", new)
for w in ["oak", "spruce", "birch", "jungle", "acacia", "big_oak"]:
    COMPOSE[f"blocks/leaves_{w}_opaque"] = (f"1.7.10 fast-graphics leaves: block/{WOOD[w]}_leaves with transparent "
                                            "texels filled by a dark (shadowed) leaf colour, fully opaque, still "
                                            "grey for biome tint")

OLD_LAYOUT = {
    "entity/bat": "1.7.10-1.20.2: 64x64 pre-1.20.3 bat model; 1.20.3+ 32x32 = entity/bat/bat (see by_version)",
    "entity/steve": "1.7.10: 64x32 legacy skin layout (no overlay layers, shared limbs); 1.8+ 64x64 = "
                    "entity/player/wide/steve (see by_version)",
    "entity/boat": "1.7.10-1.8.9: 64x32 pre-1.9 single boat model",
    "entity/cow/cow": "1.7.10-1.21.4: 64x32 pre-1.21.5 cow model",
    "entity/cow/mooshroom": "1.7.10-1.13.2: 64x32 pre-1.21.5 cow model (red mooshroom)",
    "entity/cow/red_mooshroom": "1.14-1.21.4: 64x32 old cow model; 1.21.5+ 64x64 = entity/cow/mooshroom_red "
                                "(see by_version)",
    "entity/cow/brown_mooshroom": "1.14-1.21.4: 64x32 old cow model; 1.21.5+ 64x64 = entity/cow/mooshroom_brown "
                                  "(see by_version)",
    "entity/pig/pig": "1.7.10-1.21.4: 64x32 pre-1.21.5 pig layout",
    "entity/pig/pig_saddle": "1.7.10-1.21.4: 64x32 pig saddle overlay on the old pig layout "
                             "(26.3 entity/equipment/pig_saddle/saddle is 64x64)",
    "entity/rabbit/black": "", "entity/rabbit/brown": "", "entity/rabbit/caerbannog": "",
    "entity/rabbit/gold": "", "entity/rabbit/salt": "", "entity/rabbit/toast": "", "entity/rabbit/white": "",
    "entity/rabbit/white_splotched": "",
    "entity/sign": "1.7.10-1.13.2: 64x32 sign entity sheet (board 24x12x2 texOffs(0,0), stick 2x14x2 "
                   "texOffs(0,14)); 26.3 uses block/oak_sign 32x32 with a different layout",
    "entity/zombie_pigman": "1.7.10-1.14.4: 64x64 biped zombie layout; entity/piglin/zombified_piglin uses the "
                            "piglin head (10x8x8 + ears + snout), so the UV differs",
    "entity/zombie/zombie_villager": "1.7.10-1.13.2: 64x64 pre-1.14 zombie villager (zombie arms, villager head "
                                     "region at y=32); still shipped unused until 1.16.5",
    "entity/illager/vex": "", "entity/illager/vex_charging": "",
    "entity/llama/llama": "",
    "gui/title/mojang": "1.7.10-1.13.2: 256x256, 1.14.4: 512x512 loading splash with the whole logo centred; "
                        "gui/title/mojangstudios (1.16+) is a two-half strip layout",
    "gui/presets/isles": "",
    "entity/villager/villager": "1.7.10-1.13.2: same 64x64 UV but a complete generic (nitwit-style) villager, "
                                "1.14+ it is the bald base layer -> compose base + type/plains + profession/nitwit",
    "entity/zombie_villager/zombie_villager": "1.12.2-1.13.2: complete generic zombie villager; 1.14+ base layer "
                                              "-> compose base + type/plains",
}
for c in ["black", "brown", "caerbannog", "gold", "salt", "toast", "white", "white_splotched"]:
    OLD_LAYOUT[f"entity/rabbit/{c}"] = (f"1.8.9-1.21.8: 64x32 pre-26.x rabbit model; 26.3 entity/rabbit/rabbit_{c} "
                                        "is 64x64 (new model)")
for k in ["acacia", "bamboo", "birch", "cherry", "crimson", "dark_oak", "jungle", "mangrove", "oak", "pale_oak",
          "spruce", "warped"]:
    OLD_LAYOUT[f"entity/signs/{k}"] = (f"1.14-1.21.8: 64x32 sign entity sheet; 26.3 block/{k}_sign is 32x32 "
                                       "(different layout) - could be composed from block/{k}_sign + planks")
    OLD_LAYOUT[f"entity/signs/hanging/{k}"] = (f"1.19.3-1.21.8: 64x32 hanging-sign entity sheet; 26.3 "
                                               f"block/{k}_hanging_sign is 32x32 (different layout)")
for m in ["diamond", "gold", "iron"]:
    OLD_LAYOUT[f"entity/horse/armor/horse_armor_{m}"] = (f"1.7.10-1.12.2: 128x128 pre-1.13 horse model; 1.13+ "
                                                         f"64x64 = entity/equipment/horse_body/{m} (see by_version)")
OLD_LAYOUT["entity/illager/vex"] = "1.11-1.19.2: 64x64 pre-1.19.3 vex (biped) model"
OLD_LAYOUT["entity/illager/vex_charging"] = "1.11-1.19.2: 64x64 pre-1.19.3 vex (biped) model"
OLD_LAYOUT["entity/llama/llama"] = "1.11-1.12.2: 128x64 generic llama sheet, unused by the renderer"
del OLD_LAYOUT["gui/presets/isles"]

BY_VERSION = {  # old_layout paths that match a modern texture in some versions
    "entity/bat": ("entity/bat/bat", ["1.20.4", "1.21.1", "1.21.4", "1.21.8"]),
    "entity/steve": ("entity/player/wide/steve", ["1.8.9", "1.12.2", "1.13.2", "1.14.4", "1.16.5", "1.17.1",
                                                   "1.19.2"]),
    "entity/cow/red_mooshroom": ("entity/cow/mooshroom_red", ["1.21.8"]),
    "entity/cow/brown_mooshroom": ("entity/cow/mooshroom_brown", ["1.21.8"]),
}
for m in ["diamond", "gold", "iron"]:
    BY_VERSION[f"entity/horse/armor/horse_armor_{m}"] = (
        f"entity/equipment/horse_body/{m}", [v for v in OLD_VERSIONS if v not in ("1.7.10", "1.8.9", "1.12.2")
                                             and f"entity/horse/armor/horse_armor_{m}" in IDX[v]])

# same-named 26.3 paths whose layout changed (sizes are detected automatically, these are same-size changes)
SPRITE_SHEETS = {  # pre-1.20.2 container backgrounds carried their sprites on the right/bottom
    "gui/container/inventory": "effect backgrounds + status-effect icons (0,166)/(0,198), recipe button",
    "gui/container/furnace": "lit_progress 14x14 at (176,0), burn_progress 24x17 at (176,14)",
    "gui/container/blast_furnace": "lit_progress (176,0), burn_progress (176,14)",
    "gui/container/smoker": "lit_progress (176,0), burn_progress (176,14)",
    "gui/container/brewing_stand": "brew_progress (176,0), bubbles (185,0), fuel_length (176,29)",
    "gui/container/beacon": "buttons 22x22 at (0..88,219), confirm/cancel icons at (90..112,220)",
    "gui/container/anvil": "text_field (0,166/182), error cross (176,0)",
    "gui/container/enchanting_table": "enchantment_slot rows (0,166/185/204), level icons (0..32,223/239)",
    "gui/container/horse": "saddle/armor slots and chest slot grid (0,166)",
    "gui/container/loom": "pattern buttons, scroller, banner/dye/pattern slot icons below 166",
    "gui/container/stonecutter": "scroller (176,0), recipe buttons (0,166)",
    "gui/container/cartography_table": "map previews, lock, error icons right of 176",
    "gui/container/smithing": "error icon (176,0) (1.20)",
    "gui/container/grindstone": "error cross (176,0)",
    "gui/container/gamemode_switcher": "slot/selection 26x26 at (0,75)/(26,75)",
    "gui/container/creative_inventory/tab_items": "scroller 12x15 at (232,0) / disabled (244,0)",
    "gui/container/creative_inventory/tab_item_search": "scroller 12x15 at (232,0) / disabled (244,0)",
    "gui/book": "page_forward/page_backward arrows 23x13 at (0..23,192/205)",
    "gui/recipe_book": "filter buttons, page arrows, tabs, slot frames, overlay pieces right of 147 / below 166",
}


def versions_of(p):
    return [v for v in OLD_VERSIONS if p in IDX[v]]


def vrange(vs):
    return f"{vs[0]}-{vs[-1]}" if len(vs) > 1 else vs[0]


def frame(info):
    w, h = info["w"], info["h"]
    anim = (info.get("mcmeta") or {}).get("animation")
    if anim is not None:
        fw = anim.get("width")
        fh = anim.get("height")
        if fw or fh:
            return (fw or min(w, h), fh or min(w, h))
        return (w, w) if h >= w else (h, h)
    return (w, h)


def frame_any(info):
    """Frame size of an old texture; static vertical strips of square frames count as frames too."""
    return frame(info)


def apply_rules(name, rules):
    for pat, rep in rules:
        m = re.match(pat, name)
        if m:
            return rep(m) if callable(rep) else m.expand(rep)
    return None


def candidate(p):
    if p in FULL:
        return FULL[p]
    top, _, name = p.partition("/")
    if top == "blocks":
        n = BLOCKS.get(name) or apply_rules(name, BLOCK_RULES) or name
        return "block/" + n
    if top == "items":
        n = ITEMS.get(name) or apply_rules(name, ITEM_RULES) or name
        if n.startswith("../"):
            return n[3:]
        return "item/" + n
    return apply_rules(p, FULL_RULES)


NO_EQUIVALENT = {
    "blocks/debug": "1.12 debug-world placeholder texture", "blocks/debug2": "1.12 debug-world placeholder texture",
    "blocks/flower_paeonia": "unused single-block peony flower (1.7-1.12)",
    "items/banner_base": "1.8 flat banner item base (banners render as 3D items since)",
    "items/banner_overlay": "1.8-1.12 flat banner item overlay (unused by the 3D banner item)",
    "items/ruby": "unused ruby item (pre-emerald leftover)", "item/ruby": "unused ruby item (1.13-1.16)",
    "items/quiver": "unused quiver item (1.7-1.8)",
    "items/skull_creeper": "1.7.10 flat creeper head item icon (heads are 3D since 1.8)",
    "items/skull_skeleton": "1.7.10 flat skeleton skull item icon",
    "items/skull_steve": "1.7.10 flat player head item icon",
    "items/skull_wither": "1.7.10 flat wither skeleton skull item icon",
    "items/skull_zombie": "1.7.10 flat zombie head item icon",
    "items/spawn_egg": "grey tinted spawn-egg base (template; per-mob eggs since 1.21.5)",
    "items/spawn_egg_overlay": "grey tinted spawn-egg spots overlay (template)",
    "item/spawn_egg": "1.13-1.21.4 grey tinted spawn-egg base (template; per-mob eggs since 1.21.5)",
    "item/spawn_egg_overlay": "1.13-1.21.4 grey tinted spawn-egg spots overlay (template)",
    "items/map_filled_markings": "1.12 tinted markings overlay of the filled map (26.3 has none)",
    "item/filled_map_markings": "1.13-1.21.8 tinted markings overlay of the filled map (dropped in 26.x)",
    "item/bundle_filled": "1.17-1.21.1 bulging bundle icon shown when it holds items (could fall back to item/bundle)",
    "particle/footprint": "1.7-1.16 footstep particle (removed)",
    "misc/white": "1.17-1.21.8 plain 4x4 white texture (trivial: solid #FFFFFF)",
    "gui/achievement/achievement_icons": "1.7-1.8 achievement GUI icon sheet (no modern counterpart)",
    "gui/container/legacy_smithing": "1.20 legacy 2-slot smithing table background (pre-1.20 layout)",
    "gui/stream_indicator": "1.7-1.8 Twitch broadcast indicator (shipped unused until 1.20.1)",
    "gui/sprites/backup/changes": "1.20.2-1.20.4 Realms backup 'changes' icon",
    "gui/sprites/backup/changes_highlighted": "1.20.2-1.20.4 Realms backup 'changes' icon, highlighted",
    "gui/sprites/backup/restore": "1.20.2-1.20.4 Realms backup 'restore' icon",
    "gui/sprites/backup/restore_highlighted": "1.20.2-1.20.4 Realms backup 'restore' icon, highlighted",
    "gui/sprites/container/bundle/background": "1.20.2-1.21.1 nine-slice bundle tooltip background (32x32 + "
                                               "scaling mcmeta); 1.21.2 bundle UI has no background",
}
for k in ["chaos", "delight", "drought", "luck", "madness", "water"]:
    NO_EQUIVALENT[f"gui/presets/{k}"] = "1.8-1.14 customized-world preset thumbnail (feature removed)"

SKIP = {
    "models/armor/piglin_leather_layer_1": "1.16 unused piglin leather armor leftover",
    "models/armor/piglin_leather_layer_1_overlay": "1.16 unused piglin leather armor leftover",
}


def build():
    old_paths = sorted({p for v in OLD_VERSIONS for p in IDX[v] if p not in MODERN})
    aliases, compose, old_layout, no_eq, skip, by_version = {}, {}, {}, {}, {}, {}
    problems, unclassified = [], []

    for p in old_paths:
        vs = versions_of(p)
        if re.match(r"^font/(unicode_page_|glyph_sizes)", p):
            skip[p] = "legacy unicode glyph pages, out of scope"
            continue
        for table, out in ((SKIP, skip), (NO_EQUIVALENT, no_eq), (COMPOSE, compose), (OLD_LAYOUT, old_layout)):
            if p in table:
                out[p] = table[p]
                break
        else:
            tgt = candidate(p)
            if tgt is None:
                unclassified.append(p)
                continue
            if tgt not in MODERN:
                problems.append(f"{p} -> {tgt}: target missing in 26.3")
                continue
            bad = [f"{v}:{IDX[v][p]['w']}x{IDX[v][p]['h']}" for v in vs
                   if frame_any(IDX[v][p]) != frame(MODERN[tgt]) and p not in TILING]
            if bad:
                problems.append(f"{p} -> {tgt} ({MODERN[tgt]['w']}x{MODERN[tgt]['h']}): frame mismatch {bad}")
                continue
            aliases[p] = tgt
        if p in BY_VERSION:
            tgt, bvs = BY_VERSION[p]
            assert tgt in MODERN, tgt
            for v in bvs:
                assert frame(IDX[v][p]) == frame(MODERN[tgt]), (p, v)
            by_version[p] = {"target": tgt, "versions": bvs}

    # same-named 26.3 paths whose layout changed
    for p, info in sorted(MODERN.items()):
        diffs = [v for v in OLD_VERSIONS if p in IDX[v] and frame(IDX[v][p]) != frame(info)]
        if diffs:
            sizes = sorted({f"{IDX[v][p]['w']}x{IDX[v][p]['h']}" for v in diffs})
            note = f"{vrange(diffs)}: {'/'.join(sizes)} (26.3: {info['w']}x{info['h']})"
            if p == "gui/title/background/panorama_overlay":
                note += " - vertical vignette gradient strip; stretch/resample"
            elif p.startswith("gui/title/background/panorama"):
                note += " - cube face, only the resolution differs; render at the old size"
            elif p == "entity/conduit/wind" or p == "entity/conduit/wind_vertical":
                note += " - 16 frames of 64x64 (no .mcmeta before 1.16) vs 11 frames"
            elif p in ("font/accented", "font/nonlatin_european"):
                note += " - glyph grid with fewer rows; needs that version's font provider order"
            elif p == "gui/title/minecraft":
                note += " - pre-1.20 logo split in two halves stacked in a 256x256 sheet"
            elif p == "gui/container/villager":
                note += " - pre-1.14 trading GUI (176x166 window + arrows/buttons)"
            elif p == "gui/title/edition":
                note += " - same picture at 1/4 resolution; downscale"
            old_layout[p] = note
        if p in SPRITE_SHEETS:
            vs = [v for v in versions_of(p) if VERSIONS.index(v) <= VERSIONS.index("1.20.1")]
            if vs and p not in old_layout:
                old_layout[p] = (f"{vrange(vs)}: {info['w']}x{info['h']} background that also embeds its sprites "
                                 f"(pre-1.20.2): {SPRITE_SHEETS[p]} - compose from gui/sprites/*")
    for p in ("entity/villager/villager", "entity/zombie_villager/zombie_villager"):
        old_layout[p] = OLD_LAYOUT[p]

    return dict(aliases=aliases, compose=compose, old_layout=old_layout, no_eq=no_eq, skip=skip,
                by_version=by_version, problems=problems, unclassified=unclassified, old_paths=old_paths)


def main():
    r = build()
    cats = {"aliases": r["aliases"], "compose_from_modern": r["compose"], "old_layout": r["old_layout"],
            "no_equivalent": r["no_eq"], "skip": r["skip"]}
    seen = {}
    for name, d in cats.items():
        for p in d:
            if p in seen and p in r["old_paths"]:
                r["problems"].append(f"{p} in both {seen[p]} and {name}")
            seen[p] = name
    missing = [p for p in r["old_paths"] if p not in seen]
    print(f"legacy paths: {len(r['old_paths'])}")
    for name, d in cats.items():
        legacy = sum(1 for p in d if p not in MODERN)
        same = len(d) - legacy
        print(f"  {name:20s} {len(d):5d}" + (f"  ({same} same-named 26.3 paths)" if same else ""))
    print(f"  by_version partial aliases: {len(r['by_version'])}")
    for p in r["problems"]:
        print("PROBLEM:", p)
    for p in r["unclassified"]:
        print("UNCLASSIFIED:", p)
    for p in missing:
        if p not in r["unclassified"]:
            print("MISSING:", p)
    if "--check" in sys.argv:
        return
    (DATA / "aliases.json").write_text(json.dumps(
        {"aliases": dict(sorted(r["aliases"].items())), "by_version": dict(sorted(r["by_version"].items()))},
        indent=1) + "\n")
    (DATA / "old_only.json").write_text(json.dumps(
        {k: dict(sorted(v.items())) for k, v in cats.items() if k != "aliases"}, indent=1) + "\n")
    print("wrote data/aliases.json, data/old_only.json")


if __name__ == "__main__":
    main()
