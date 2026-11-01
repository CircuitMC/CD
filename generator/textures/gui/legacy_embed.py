"""Sprites that pre-1.20.2 versions read from inside the container/book/recipe-book sheets.

The 26.3 backgrounds only use their top-left window area, so the old sprite strips are drawn into
the otherwise unused parts of the same 256x256 images: one texture serves every version.
Coordinates follow the old screens' blit() source rectangles.
"""
from .legacy_common import put

S = "gui/sprites/container/"
FURNACE = lambda k: [(f"{S}{k}/lit_progress", 176, 0), (f"{S}{k}/burn_progress", 176, 14)]
SCROLL = lambda k, x: [(f"{S}{k}/scroller", x, 0), (f"{S}{k}/scroller_disabled", x + 12, 0)]
RB = "gui/sprites/recipe_book/"

EMBED = {
    "furnace": FURNACE("furnace"),
    "smoker": FURNACE("smoker"),
    "blast_furnace": FURNACE("blast_furnace"),
    "brewing_stand": [(S + "brewing_stand/brew_progress", 176, 0), (S + "brewing_stand/bubbles", 185, 0),
                      (S + "brewing_stand/fuel_length", 176, 29)],
    "anvil": [(S + "anvil/text_field", 0, 166), (S + "anvil/text_field_disabled", 0, 182),
              (S + "anvil/error", 176, 0)],
    "grindstone": [(S + "grindstone/error", 176, 0)],
    "smithing": [(S + "smithing/error", 176, 0)],
    "cartography_table": [(S + "cartography_table/map", 176, 0), (S + "cartography_table/scaled_map", 176, 66),
                          (S + "cartography_table/duplicated_map", 176, 132),
                          (S + "cartography_table/error", 226, 132), (S + "cartography_table/locked", 226, 153)],
    "enchanting_table": [(S + "enchanting_table/enchantment_slot", 0, 166),
                         (S + "enchanting_table/enchantment_slot_disabled", 0, 185),
                         (S + "enchanting_table/enchantment_slot_highlighted", 0, 204)]
    + [(S + f"enchanting_table/level_{n}", 16 * (n - 1), 223) for n in (1, 2, 3)]
    + [(S + f"enchanting_table/level_{n}_disabled", 16 * (n - 1), 239) for n in (1, 2, 3)],
    "beacon": [(S + "beacon/button", 0, 219), (S + "beacon/button_selected", 22, 219),
               (S + "beacon/button_disabled", 44, 219), (S + "beacon/button_highlighted", 66, 219),
               (S + "beacon/confirm", 90, 220), (S + "beacon/cancel", 112, 220)],
    "creative_items": SCROLL("creative_inventory", 232),
    "gamemode_switcher": [("gui/sprites/gamemode_switcher/slot", 0, 75),
                          ("gui/sprites/gamemode_switcher/selection", 26, 75)],
    "horse": [(S + "horse/chest_slots", 0, 166), (S + "horse/armor_slot", 0, 220),
              (S + "horse/saddle_slot", 18, 220), (S + "horse/llama_armor_slot", 36, 220)],
    "inventory": [(S + "inventory/effect_background_large", 0, 166),
                  (S + "inventory/effect_background", 0, 198)],
    "loom": [(S + "loom/pattern", 0, 166), (S + "loom/pattern_selected", 0, 180),
             (S + "loom/pattern_highlighted", 0, 194), (S + "slot/banner", 176, 0), (S + "slot/dye", 192, 0),
             (S + "slot/banner_pattern", 208, 0)] + SCROLL("loom", 232),
    "stonecutter": SCROLL("stonecutter", 176)
    + [(S + "stonecutter/recipe", 0, 166), (S + "stonecutter/recipe_selected", 0, 184),
       (S + "stonecutter/recipe_highlighted", 0, 202)],
    "book": [("gui/sprites/widget/page_forward", 0, 192), ("gui/sprites/widget/page_forward_highlighted", 23, 192),
             ("gui/sprites/widget/page_backward", 0, 205), ("gui/sprites/widget/page_backward_highlighted", 23, 205)],
    "recipe_book": [
        (RB + "filter_disabled", 152, 41), (RB + "filter_enabled", 180, 41),
        (RB + "filter_disabled_highlighted", 152, 59), (RB + "filter_enabled_highlighted", 180, 59),
        (RB + "furnace_filter_disabled", 152, 182), (RB + "furnace_filter_enabled", 180, 182),
        (RB + "furnace_filter_disabled_highlighted", 152, 200), (RB + "furnace_filter_enabled_highlighted", 180, 200),
        (RB + "page_forward", 1, 208), (RB + "page_forward_highlighted", 1, 226),
        (RB + "page_backward", 14, 208), (RB + "page_backward_highlighted", 14, 226),
        (RB + "tab", 153, 2), (RB + "tab_selected", 188, 2),
        (RB + "slot_craftable", 29, 206), (RB + "slot_uncraftable", 54, 206),
        (RB + "slot_many_craftable", 29, 231), (RB + "slot_many_uncraftable", 54, 231),
        (RB + "overlay_recipe", 82, 208),
        (RB + "crafting_overlay", 152, 78), (RB + "crafting_overlay_highlighted", 152, 104),
        (RB + "crafting_overlay_disabled", 178, 78), (RB + "crafting_overlay_disabled_highlighted", 178, 104),
        (RB + "furnace_overlay", 152, 130), (RB + "furnace_overlay_highlighted", 152, 156),
        (RB + "furnace_overlay_disabled", 178, 130), (RB + "furnace_overlay_disabled_highlighted", 178, 156),
    ],
}


def embed(c, ctx, name):
    for item in EMBED.get(name, ()):
        put(c, ctx, *item)
    return c
