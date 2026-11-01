"""Built blocks: bricks, stone bricks, smooth stone, sandstone."""
import numpy as np

from ...engine import Tex, pal
from ...materials import (SAND, STONE, bordered_panel, layered, masonry, overgrow, rock,
                          running_bond)
from ...registry import texture

BRICK = pal("7f3a2b", "924333", "a14d3b", "ae5844", "bb634e", "c66e58")
MORTAR = pal("8f887d", "a39c90", "b2ab9f")
SMOOTH = pal("8c8c8f", "98989b", "a3a3a6", "aeaeb1", "b9b9bc")
SANDSTONE = pal("bba672", "c8b37e", "d3bf8a", "dcc995", "e4d2a0")


@texture("block/bricks")
def bricks(ctx):
    fill = rock(ctx, BRICK, cell=4, contrast=0.5, streaks=0, salt="brick", porosity=0.3)
    t, _ = masonry(ctx, running_bond(4, 4, 8), fill, MORTAR, salt="brick")
    return t


def stone_brick_layout(ctx):
    fill = rock(ctx.sub("block/stone_bricks_fill"), STONE, streaks=1)
    t, _ = masonry(ctx, [(8, [0]), (8, [8])], fill, STONE[0])
    return t


@texture("block/stone_bricks")
def stone_bricks(ctx):
    return stone_brick_layout(ctx.sub("block/stone_bricks"))


@texture("block/cracked_stone_bricks")
def cracked_stone_bricks(ctx):
    t = stone_brick_layout(ctx.sub("block/stone_bricks"))
    rng = ctx.rng("crack")
    for _ in range(3):
        x, y = float(rng.integers(0, 16)), float(rng.integers(0, 16))
        for _ in range(int(rng.integers(5, 9))):
            nx, ny = x + rng.choice([-1, 0, 1]), y + rng.choice([0, 1, 1])
            m = ctx.segment(x + 0.5, y + 0.5, nx + 0.5, ny + 0.5, 0.8) > 0
            t.color[m] = STONE[0] * 0.7
            t.height[m] = 0.05
            x, y = nx, ny
    return t


@texture("block/mossy_stone_bricks")
def mossy_stone_bricks(ctx):
    return overgrow(ctx, stone_brick_layout(ctx.sub("block/stone_bricks")), 0.68)


@texture("block/smooth_stone")
def smooth_stone(ctx):
    return bordered_panel(ctx, SMOOTH)


@texture("block/smooth_stone_slab_side")
def smooth_stone_slab_side(ctx):
    top = bordered_panel(ctx.sub("slab_top"), SMOOTH)
    # Two half-height panels stacked: redo the frame for each half.
    for y0 in (0, 8):
        hi = (ctx.rect(0, y0, 16, y0 + 1) + ctx.rect(0, y0, 1, y0 + 8)) > 0
        lo = (ctx.rect(0, y0 + 7, 16, y0 + 8) + ctx.rect(15, y0, 16, y0 + 8)) > 0
        top.color[hi] = SMOOTH[-1]
        top.color[lo & ~hi] = SMOOTH[0]
        top.height[hi] = 0.65
        top.height[lo & ~hi] = 0.25
    return top


@texture("block/sandstone")
def sandstone(ctx):
    t = layered(ctx, SANDSTONE, salt="ss")
    rows = {0: SANDSTONE[-1], 1: SANDSTONE[-2], 3: SANDSTONE[0], 12: SANDSTONE[0], 15: SANDSTONE[1]}
    for y, c in rows.items():
        m = ctx.rect(0, y, 16, y + 1) > 0
        t.color[m] = c
        t.height[m] = 0.2 if c is SANDSTONE[0] else 0.65
    return t


@texture("block/sandstone_top")
def sandstone_top(ctx):
    n = ctx.noise(8, 2, 0.6, salt="sst")
    return Tex(ctx, ctx.palette(SANDSTONE[2:], n * 0.75 + ctx.texel_noise("sst") * 0.25),
               height=0.5 + n * 0.1, smooth=0.15, porosity=0.5)


@texture("block/sandstone_bottom")
def sandstone_bottom(ctx):
    t = layered(ctx, SANDSTONE, salt="ssb")
    r = ctx.texel_noise("ssb_speck", soft=False) < 0.04
    t.color = np.where(r[..., None], SAND[0], t.color)
    return t
