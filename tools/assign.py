#!/usr/bin/env python3
"""Split vanilla texture paths into work areas (one owner module folder each).

    python3 tools/assign.py            # writes data/assignments.json, prints counts
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = json.loads((ROOT / "data" / "vanilla-26.3.json").read_text())["textures"]

DYES = ("white|orange|magenta|light_blue|yellow|lime|pink|gray|light_gray|cyan|purple|blue|"
        "brown|green|red|black")
WOODS = "oak|spruce|birch|jungle|acacia|dark_oak|mangrove|cherry|pale_oak|bamboo|crimson|warped|poplar"

# Ordered (owner, regex on the path without "block/"). First match wins.
BLOCK_RULES = [
    ("core", r"(.*_)?glass(_pane_top)?$|tinted_glass"),
    ("block_stone", r"_ore$|^grass_block|^mossy_|^(dirt|coarse_dirt|rooted_dirt)$"),
    ("block_color", rf"({DYES})_(wool|concrete|concrete_powder|terracotta|glazed_terracotta|candle|candle_lit|shulker_box|bed_.*)$"
                    r"|^(candle|candle_lit|shulker_box|terracotta|bed_.*)$"),
    ("block_color", r"^(water|lava)_|^fire_[01]$|^soul_fire_|nether_portal|destroy_|^debug|end_portal|campfire_fire|soul_campfire_fire"),
    ("block_plants", r"flower|tulip|orchid|allium|bluet|daisy|poppy|dandelion|cornflower|lily|rose|peony|lilac|"
                     r"sunflower|short_grass|tall_grass|dry_grass|fern|bush|vine|kelp|seagrass|coral|cactus|sugar_cane|"
                     r"dripleaf|moss|lichen|wheat|carrots|potatoes|beetroots|cocoa|nether_wart_stage|melon|pumpkin|"
                     r"propagule|spore|hanging_roots|sweet_berry|pitcher|torchflower|eyeblossom|petals|leaf_litter|"
                     r"wildflowers|chorus|sea_pickle|nether_sprouts|twisting|weeping|dead_bush|shrub|frogspawn|"
                     r"lily_pad|firefly|resin_clump|shelf_mushroom|_mushroom$|fungus|_roots$|_roots_pot|azalea_plant|"
                     r"potted_|bamboo_stage|bamboo_stalk|bamboo_.*leaf|bamboo_.*leaves|mushroom_stem|"
                     r"mushroom_block|nylium|wart_block|sculk_catalyst_.*bloom"),
    ("block_wood", rf"^(stripped_)?({WOODS})_|_(stem|stem_top|hyphae)$|^stripped_|_leaves$|sapling|mushroom|fungus|roots|"
                   r"flower|tulip|orchid|allium|bluet|daisy|poppy|dandelion|cornflower|lily|rose|peony|lilac|sunflower|"
                   r"grass|fern|bush|vine|kelp|seagrass|coral|cactus|sugar_cane|bamboo|azalea|dripleaf|moss|lichen|"
                   r"wheat|carrots|potatoes|beetroots|cocoa|nether_wart_stage|melon|pumpkin|propagule|spore|hanging_roots|"
                   r"sweet_berry|pitcher|torchflower|eyeblossom|petals|leaf_litter|wildflowers|chorus|sea_pickle|"
                   r"nether_sprouts|twisting|weeping|cave_vines|glow_berries|dead_bush|shrub|hay|dried_kelp|frogspawn|"
                   r"lily_pad|firefly|cactus_flower|creaking_heart|resin_clump|shelf_mushroom|straw|mangrove|"
                   r"bee_nest|beehive|honey|ladder|scaffolding|composter|barrel|bookshelf|crafting_table|"
                   r"cartography|fletching|smithing|loom|lectern|chiseled_bookshelf|jukebox|note_block|"
                   r"campfire_log|_door_|_trapdoor|_sign$|_shelf$|_hanging_sign|_planks|_mosaic|_fence"),
    ("block_functional", r"furnace|smoker|dispenser|dropper|observer|piston|redstone|repeater|comparator|"
                         r"rail|lever|tripwire|daylight|target|tnt|command_block|structure_block|jigsaw|test_|"
                         r"trial_spawner|vault|crafter|hopper|cauldron|anvil|grindstone|stonecutter|enchanting|"
                         r"brewing|beacon|conduit|bell|lantern|torch|end_rod|lightning_rod|chain|iron_bars|copper_bars|"
                         r"copper_bulb|spawner|lodestone|respawn_anchor|sculk_|calibrated|item_frame|flower_pot|"
                         r"cake|dragon_egg|heavy_core|turtle_egg|sniffer_egg|dried_ghast|cobweb|lamp|frosted_ice|"
                         r"end_portal_frame|ender|jack_o_lantern|carved_pumpkin|sponge|slime|"
                         r"reinforced_deepslate|farmland|dirt_path|grass_block_snow"),
    ("block_stone", r".*"),
]


ENTITY_OBJECTS = {
    "equipment", "shield", "banner", "decorated_pot", "chest", "boat", "chest_boat", "cushion", "conduit",
    "projectiles", "end_crystal", "end_portal", "trident", "beacon", "bell", "enchantment", "experience",
    "fishing", "lead_knot", "minecart", "armorstand", "signs", "bed", "shulker", "player",
}


def owner(path):
    top = path.split("/")[0]
    if top == "block":
        name = path[len("block/"):]
        for who, rx in BLOCK_RULES:
            if re.search(rx, name):
                return who
    if top == "item":
        return "item_1" if path[len("item/")] <= "g" else "item_2"
    if top == "entity":
        sub = path.split("/")[1] if path.count("/") > 1 else ""
        return "entity_objects" if sub in ENTITY_OBJECTS or not sub else "entity_mobs"
    return { "gui": "gui", "font": "gui", "mob_effect": "gui",
        "map": "gui", "particle": "misc", "environment": "misc", "misc": "misc", "painting": "misc",
        "colormap": "misc", "effect": "misc", "palettes": "misc", "trims": "misc",
    }[top]


def main():
    out = {p: owner(p) for p in sorted(INDEX)}
    (ROOT / "data" / "assignments.json").write_text(json.dumps(out, indent=1))
    for who, n in Counter(out.values()).most_common():
        print(f"{who:18} {n}")


if __name__ == "__main__":
    main()
