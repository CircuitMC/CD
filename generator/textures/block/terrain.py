"""Natural terrain: stone, deepslate, dirt, grass, sand, gravel, snow, bedrock."""
import numpy as np

from ...engine import Tex, pal
from ...materials import (DEEPSLATE, DIRT, GRASS_SIDE, RED_SAND, SAND, SNOW, STONE, granular,
                          layered, overgrow, pebbles, rock, soil)
from ...registry import texture

BEDROCK = pal("17171a", "29292c", "3d3d41", "545458", "6d6d72", "8a8a8f")
CLAY = pal("868c9a", "8f96a3", "979eab", "a0a7b3", "a9b0bb")
GRAVEL = pal("6d6a68", "7b7876", "8a8784", "958d82", "a19c96", "776d63")


@texture("block/stone")
def stone(ctx):
    t = rock(ctx, STONE, cell=6, contrast=0.55, streaks=4)
    # sparse 1-2 texel flecks of lighter and darker mineral grains
    r = ctx.texel_noise("stfl", soft=False)
    lite = ctx.organic((r > 0.955).astype(np.float32), 0.3, "stl")
    dark = ctx.organic((r < 0.04).astype(np.float32), 0.3, "std")
    t.color = np.where(lite[..., None], STONE[-1], t.color)
    t.color = np.where(dark[..., None], STONE[1], t.color)
    t.height = np.where(lite, t.height + 0.1, np.where(dark, t.height - 0.1, t.height))
    return t


@texture("block/deepslate")
def deepslate(ctx):
    return layered(ctx, DEEPSLATE, stretch=4, bands=5)


@texture("block/deepslate_top")
def deepslate_top(ctx):
    t = rock(ctx, DEEPSLATE, cell=8, contrast=0.6, streaks=0, salt="top")
    vo = ctx.voronoi(6, "dtop", min_dist=5)
    crack = (vo["f2"] - vo["f1"]) < 0.55
    t.color = np.where(crack[..., None], DEEPSLATE[0], t.color)
    t.height = np.where(crack, 0.1, t.height)
    return t


@texture("block/dirt")
def dirt(ctx):
    return soil(ctx.sub("block/dirt"), DIRT)


def grass_field(ctx):
    """Grayscale grass surface (multiplied by the biome color in game)."""
    n = ctx.noise(4, 2, 0.5, salt="grass")
    g = ctx.texel_noise("grass")
    v = ctx.quantize(n * 0.45 + g * 0.55, 5)
    return 0.56 + v * 0.3, v


@texture("block/grass_block_top")
def grass_block_top(ctx):
    lv, v = grass_field(ctx)
    return Tex(ctx, np.repeat(lv[..., None], 3, -1), height=0.4 + v * 0.4, smooth=0.1, sss=0.4,
               porosity=0.3)


def fringe(ctx, salt):
    """Hanging edge for grass/snow/mycelium sides. Returns (mask, depth 0..1)."""
    rng = ctx.rng(f"fringe{salt}")
    lengths = []
    smooth_n = rng.random(ctx.w // 4 + 1)
    for x in range(ctx.w):
        t = x / 4
        i = int(t)
        f = t - i
        b = smooth_n[i % len(smooth_n)] * (1 - f) + smooth_n[(i + 1) % len(smooth_n)] * f
        length = 2 + round(b * 2 + rng.random() * 1.2)
        if rng.random() < 0.18:
            length += int(rng.integers(1, 3))
        lengths.append(length)
    L = np.array(lengths, np.float32)[ctx.tx % ctx.w]
    if not ctx.pixel_art:  # ragged blade tips at high res
        L = L + (ctx.noise(0.5, 1, salt=f"tip{salt}", stretch=(1, 2)) - 0.5) * 0.8 * ctx.smooth_t
    mask = ctx.y < L
    depth = np.clip(ctx.y / np.maximum(L, 1), 0, 1)
    return mask, depth


def grass_overlay_level(ctx, depth):
    return 0.84 - depth * 0.24 + (ctx.texel_noise("gol") - 0.5) * 0.12


@texture("block/grass_block_side_overlay")
def grass_block_side_overlay(ctx):
    m, depth = fringe(ctx, "grass")
    lv = grass_overlay_level(ctx, depth)
    return Tex(ctx, np.repeat(lv[..., None], 3, -1), alpha=m.astype(np.float32),
               height=0.75 - depth * 0.2, sss=0.4, wrap=False)


@texture("block/grass_block_side")
def grass_block_side(ctx):
    t = soil(ctx.sub("block/dirt"), DIRT)
    m, depth = fringe(ctx, "grass")
    lv = grass_overlay_level(ctx, depth)
    t.color = np.where(m[..., None], lv[..., None] * GRASS_SIDE, t.color)
    t.height = np.where(m, 0.75 - depth * 0.2, t.height)
    return t


@texture("block/grass_block_snow")
def grass_block_snow(ctx):
    t = soil(ctx.sub("block/dirt"), DIRT)
    m, depth = fringe(ctx, "snow")
    col = ctx.palette(SNOW, 1 - depth * 0.6 - ctx.texel_noise("sn") * 0.3)
    t.color = np.where(m[..., None], col, t.color)
    t.height = np.where(m, 0.8, t.height)
    t.smooth = np.where(m, 0.4, t.smooth)
    return t


@texture("block/snow")
def snow(ctx):
    n = ctx.noise(8, 2, 0.5, salt="snow")
    return Tex(ctx, ctx.palette(SNOW, n * 0.6 + ctx.texel_noise("snow") * 0.4),
               height=0.5 + n * 0.15, smooth=0.45, sss=0.5, f0=0.02)


@texture("block/sand")
def sand(ctx):
    return granular(ctx, SAND, dark=pal("b6a274")[0], light=SAND[-1])


@texture("block/red_sand")
def red_sand(ctx):
    return granular(ctx, RED_SAND, dark=pal("8b431a")[0], light=RED_SAND[-1])


@texture("block/clay")
def clay(ctx):
    n = ctx.noise(8, 2, 0.6, salt="clay")
    t = Tex(ctx, ctx.palette(CLAY, n * 0.8 + ctx.texel_noise("clay") * 0.2), height=0.5 + n * 0.1,
            smooth=0.35, porosity=0.4)
    rng = ctx.rng("clayspot")
    for _ in range(4):
        x, y = rng.integers(0, 15), rng.integers(0, 16)
        m = ctx.rect(x, y, x + 2, y + 1) > 0
        t.color[m] = pal("b5bbc6")[0]
    return t


@texture("block/gravel")
def gravel(ctx):
    return pebbles(ctx, GRAVEL, 15, 3.0, pal("4e4a47")[0], edge=0.7)


@texture("block/cobblestone")
def cobblestone(ctx):
    return pebbles(ctx.sub("block/cobblestone"), STONE[2:5], 9, 4.6, pal("434346")[0], bevel=0.35)


@texture("block/mossy_cobblestone")
def mossy_cobblestone(ctx):
    return overgrow(ctx, cobblestone(ctx), 0.55)


@texture("block/bedrock")
def bedrock(ctx):
    vo = ctx.voronoi(10, "bed", min_dist=3.5)
    tone = ctx.rng("bedtone").random(len(vo["points"])).astype(np.float32)
    v = tone[vo["id"]] * 0.6 + ctx.texel_noise("bed") * 0.4
    gap = (vo["f2"] - vo["f1"]) < 0.8
    v = np.where(gap, v * 0.3, v)
    return Tex(ctx, ctx.palette(BEDROCK, v), height=np.where(gap, 0.1, 0.4 + v * 0.5), smooth=0.2)
