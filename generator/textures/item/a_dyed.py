"""Dye-colored item families for the a-g colors (black, blue, brown, cyan, gray,
green) plus the undyed bundle and candle.

The family generators live in h_dyed (item_2) so all 16 colors share one design;
this module only registers the a-g colors and the undyed variants."""
from ...registry import register
from . import h_dyed as HD
from .h_lib import pal

COLORS = ["black", "blue", "brown", "cyan", "gray", "green"]

for _c in COLORS:
    for _k, _fn in HD.FAMILY.items():
        register(f"item/{_c}_{_k}", lambda ctx, fn=_fn, c=_c: fn(ctx, c))

# Undyed: tanned leather bundle, beeswax-cream candle.
LEATHER_BAG = pal("4a2c14", "7a4a24", "a06a38", "c08a50", "dcae74")
WAX = pal("8a7448", "c2a670", "dcc48e", "eedcaa", "fbf0cc")


# Undyed variants reuse the shared palette-driven generators from h_dyed.
register("item/bundle", lambda ctx: HD.bundle_with(ctx, LEATHER_BAG))
register("item/bundle_open_back", lambda ctx: HD.bundle_open_back_with(ctx, LEATHER_BAG))
register("item/bundle_open_front", lambda ctx: HD.bundle_open_front_with(ctx, LEATHER_BAG))
register("item/candle", lambda ctx: HD.candle_with(ctx, WAX))
