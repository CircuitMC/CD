"""Dye-colored item families for the a-g colors (black, blue, brown, cyan, gray,
green) plus the undyed bundle and candle.

The family generators live in h_dyed (item_2) so all 16 colors share one design;
this module only registers the a-g colors and the undyed variants."""
from ...registry import register
from ...sprites import compose
from . import h_dyed as HD
from .a_lib import paint
from .h_lib import cells, pal, rows_mask, spr, union

COLORS = ["black", "blue", "brown", "cyan", "gray", "green"]

for _c in COLORS:
    for _k, _fn in HD.FAMILY.items():
        register(f"item/{_c}_{_k}", lambda ctx, fn=_fn, c=_c: fn(ctx, c))

# Undyed: tanned leather bundle, beeswax-cream candle.
LEATHER_BAG = pal("4a2c14", "7a4a24", "a06a38", "c08a50", "dcae74")
WAX = pal("8a7448", "c2a670", "dcc48e", "eedcaa", "fbf0cc")


def bundle(ctx):
    p = LEATHER_BAG
    m = rows_mask(ctx, HD.BUNDLE, round_=0.25)
    t = spr(ctx, m, p, smooth=0.2, porosity=0.4)
    ring = ctx.edge(m, 1) > 0
    paint(t, (cells(ctx, [(5, 6), (10, 6), (4, 8), (11, 8), (7, 10), (8, 12)]) > 0.5) & ~ring, p[1])
    paint(t, (cells(ctx, [(5, 3), (6, 3), (4, 9), (5, 8)]) > 0.5) & ~ring, p[-1])
    paint(t, (cells(ctx, [(9, 9), (9, 10), (6, 11)]) > 0.5) & ~ring, p[2])  # stitches
    tie = spr(ctx, rows_mask(ctx, ["######"], x0=5, y0=4), HD.TIE, bevel=1)
    knot = spr(ctx, cells(ctx, [(11, 4), (11, 5), (12, 6)]), HD.TIE, outline=False, bevel=1)
    return compose(ctx, t, tie, knot)


def bundle_open_back(ctx):
    p = LEATHER_BAG
    m = rows_mask(ctx, HD.OPEN_BACK, round_=0.25)
    t = spr(ctx, m, p, smooth=0.2, porosity=0.4)
    inner = rows_mask(ctx, ["############", "############", "##########"], x0=2, y0=4)
    paint(t, inner > 0.5, p[0] * 0.7)
    paint(t, cells(ctx, [(x, 4) for x in range(3, 13)]) > 0.5, p[0] * 0.5)
    return t


def bundle_open_front(ctx):
    p = LEATHER_BAG
    m = rows_mask(ctx, HD.OPEN_FRONT, y0=6, round_=0.25)
    t = spr(ctx, m, p, smooth=0.2, porosity=0.4)
    ring = ctx.edge(m, 1) > 0
    paint(t, (cells(ctx, [(x, 7) for x in range(3, 13)]) > 0.5) & ~ring, p[-1])
    paint(t, (cells(ctx, [(4, 10), (11, 10), (7, 12)]) > 0.5) & ~ring, p[1])
    tie = spr(ctx, rows_mask(ctx, ["##", "##"], x0=12, y0=7), HD.TIE, bevel=1)
    return compose(ctx, t, tie)


def candle(ctx):
    p = WAX
    body = rows_mask(ctx, ["####"] * 9, x0=6, y0=6)
    drip = cells(ctx, [(5, 7), (5, 8), (10, 6)])
    m = union(body, drip)
    t = spr(ctx, m, p, smooth=0.45, sss=0.35, bevel=1.5)
    ring = ctx.edge(m, 1) > 0
    paint(t, (cells(ctx, [(7, 6), (8, 6)]) > 0.5) & ~ring, p[-1])
    paint(t, (cells(ctx, [(9, 9), (9, 11), (9, 13)]) > 0.5) & ~ring, p[1])
    wick = spr(ctx, cells(ctx, [(7, 4), (7, 5)]), HD.WICK, outline=False, bevel=1)
    return compose(ctx, t, wick)


register("item/bundle", bundle)
register("item/bundle_open_back", bundle_open_back)
register("item/bundle_open_front", bundle_open_front)
register("item/candle", candle)
