"""Nether stone: netherrack, nether bricks family, nether ores, ancient debris, magma,
glowstone, shroomlight, soul sand / soil."""
import numpy as np

from ...engine import GOLD, Tex, pal, smoothstep
from ...materials import granular
from ...registry import register, texture
from .stone_common import blocks, bond, carve, cracks, emboss, mottled, ore_clusters, pits, speckle

NETHERRACK = pal("4a1515", "5e1c1c", "6f2424", "7f2c2b", "903734", "a2443f")
NETHER_BRICK = pal("1f0d10", "2b1216", "36171c", "421d22", "4f2329", "5c2a31")
RED_NETHER_BRICK = pal("3d0507", "50090b", "620d10", "731316", "84191c", "952124")
DEBRIS = pal("2c201d", "3d2c27", "4f3a32", "61483d", "755747", "8a6a58")
MAGMA = pal("3a160c", "4f1e10", "642813", "7a3116")
LAVA_GLOW = pal("a8300a", "e05a10", "ff9423", "ffd466")
GLOW = pal("7a4a1c", "b07a2c", "d9a443", "f2cb68", "ffe9a6")
SHROOM = pal("9c3d1e", "c45a28", "e07c33", "f2a246", "ffd27a")
SOUL_SAND = pal("2f2219", "3e2d22", "4c382b", "594234", "674d3d", "765a48")
SOUL_SOIL = pal("281d16", "33261d", "3d2e24", "48362b", "534033", "5f4a3b")


def netherrack_base(ctx):
    c = ctx.sub("block/netherrack")
    t = mottled(c, NETHERRACK[1:], cell=4, contrast=0.55, salt="nr")
    vo = c.voronoi(10, "nrv", min_dist=3.2)
    crev = ((vo["f2"] - vo["f1"]) < 0.55) & (c.noise(3, 1, salt="nrc") > 0.4)
    t.color = np.where(crev[..., None], NETHERRACK[0], t.color)
    t.height = np.where(crev, 0.15, t.height)
    lip = np.roll(crev, c.s, 0) & ~crev
    t.color = np.where(lip[..., None], NETHERRACK[-1], t.color)
    speckle(c, t, pal("b45a50")[0], 0.025, "nrl", height=0.65)
    t.porosity = c.full(0.3)
    return t


@texture("block/netherrack")
def netherrack(ctx):
    return netherrack_base(ctx)


@texture("block/nether_gold_ore")
def nether_gold_ore(ctx):
    gold = pal("9c6a0e", "e0ad25", "f8d54a", "fff3a0")
    return ore_clusters(ctx, netherrack_base(ctx), gold, salt="ngo", count=9, size=(2, 5), min_dist=4.0,
                        smooth=0.7, metal_id=GOLD, rim=0.7)


@texture("block/nether_quartz_ore")
def nether_quartz_ore(ctx):
    quartz = pal("a89c94", "d9d0c8", "eee8e1", "ffffff")
    return ore_clusters(ctx, netherrack_base(ctx), quartz, salt="nqo", count=8, size=(3, 6), min_dist=4.2,
                        smooth=0.8, f0=0.05, rim=0.62)


def nbricks(ctx, p, salt):
    fill = mottled(ctx.sub(f"nbf{salt}"), p[1:], cell=4, contrast=0.5, salt=f"nb{salt}")
    rects = bond(4, 4, 8, offset=4)
    t, _, _ = blocks(ctx.sub(f"nb{salt}"), rects, fill, p[0] * 0.6, salt=salt, lit=1.22, dark=0.8,
                     tone=0.08)
    t.porosity = ctx.full(0.15)
    return t


@texture("block/nether_bricks")
def nether_bricks(ctx):
    return nbricks(ctx, NETHER_BRICK, "nb")


@texture("block/cracked_nether_bricks")
def cracked_nether_bricks(ctx):
    t = nbricks(ctx, NETHER_BRICK, "nb")
    cracks(ctx, t, 4, NETHER_BRICK[0] * 0.5, "cnb")
    return t


@texture("block/red_nether_bricks")
def red_nether_bricks(ctx):
    return nbricks(ctx, RED_NETHER_BRICK, "rnb")


@texture("block/chiseled_nether_bricks")
def chiseled_nether_bricks(ctx):
    p = NETHER_BRICK
    fill = mottled(ctx.sub("cnbf"), p[1:], cell=4, contrast=0.5, salt="cnbf")
    rects = [(0, 0, 8, 4), (8, 0, 8, 4), (0, 4, 16, 8), (4, 12, 8, 4), (12, 12, 8, 4)]
    t, _, _ = blocks(ctx, rects, fill, p[0] * 0.6, salt="cnb", lit=1.22, dark=0.8)
    # raised diamond ring emblem with a sunken heart, lighter stone so it reads on dark brick
    d = np.abs(ctx.x - 8) + np.abs(ctx.y - 8) * 1.4
    ring = (d < 5.2) & (d >= 3.2) & (ctx.y > 4) & (ctx.y < 12)
    t.color = np.where(ring[..., None], np.clip(t.color * 1.35, 0, 1), t.color)
    emboss(ctx, t, ring.astype(np.float32), lit=1.3, dark=0.65)
    carve(ctx, t, ctx.rect(7, 7, 9, 9), depth=0.6)
    for x in (2, 13):
        emboss(ctx, t, ctx.rect(x, 7, x + 1, 9), lit=1.4)
    return t


# ---------------------------------------------------------------- ancient debris

@texture("block/ancient_debris_side")
def ancient_debris_side(ctx):
    warp = ctx.noise(6, 2, 0.5, salt="adw")
    band = (ctx.y + warp * 6) / 2.6
    idx = np.floor(band) % 4
    v = 0.2 + idx * 0.18 + (ctx.texel_noise("adg") - 0.5) * 0.18
    col = ctx.palette(DEBRIS, np.clip(v, 0, 1))
    t = Tex(ctx, col, height=0.4 + idx * 0.08, smooth=0.3, porosity=0.05)
    lines = (band - np.floor(band)) < 0.18
    t.color = np.where((lines & (idx == 0))[..., None], DEBRIS[0] * 0.8, t.color)
    # metallic glints of the hidden scrap
    m = ore_clusters(ctx, t, pal("4a3a36", "7a6660", "a8948a", "d6c6bc"), salt="adm", count=4,
                     size=(2, 4), min_dist=6, smooth=0.7, rim=0.75)
    return m


@texture("block/ancient_debris_top")
def ancient_debris_top(ctx):
    dx, dy = ctx.x - 8, ctx.y - 8
    r = np.maximum(np.abs(dx), np.abs(dy)) * 0.6 + np.hypot(dx, dy) * 0.4
    r = r + (ctx.noise(5, 2, salt="adt") - 0.5) * 2.2
    idx = np.floor(r / 1.6) % 4
    v = 0.2 + idx * 0.18 + (ctx.texel_noise("adtg") - 0.5) * 0.18
    col = ctx.palette(DEBRIS, np.clip(v, 0, 1))
    t = Tex(ctx, col, height=0.4 + idx * 0.08, smooth=0.3, porosity=0.05)
    core = r < 1.4
    t.color = np.where(core[..., None], pal("a8948a")[0], t.color)
    t.height = np.where(core, 0.8, t.height)
    return t


# ---------------------------------------------------------------- magma

def magma(ctx):
    vo = ctx.voronoi(8, "mag", min_dist=4)
    border = vo["f2"] - vo["f1"]
    phase = ctx.frame / max(1, ctx.frames)
    pulse = 0.5 + 0.5 * np.sin(2 * np.pi * (phase + ctx.noise(8, 1, salt="mph")))
    crack_w = 0.7 + pulse * 0.25
    crack = border < crack_w
    lit = np.clip(-(vo["dx"] + vo["dy"]) / 6, -0.5, 0.5)
    v = 0.45 + lit * 0.7 + (ctx.texel_noise("mg") - 0.5) * 0.3
    rock = ctx.palette(MAGMA, np.clip(v, 0, 1))
    heat = np.clip(1 - border / np.maximum(crack_w, 1e-3), 0, 1)
    glow = ctx.palette(LAVA_GLOW, np.clip(heat * 0.6 + pulse * 0.4, 0, 1))
    col = np.where(crack[..., None], glow, rock)
    # warm rim around cracks
    rim = (border < crack_w + 0.7) & ~crack
    col = np.where(rim[..., None], np.clip(col * np.array([1.35, 1.0, 0.8]), 0, 1), col)
    # glowing pores in the rock
    pore = (ctx.texel_noise("mgp", soft=False) < 0.04) & ~crack
    col = np.where(pore[..., None], LAVA_GLOW[1], col)
    em = np.where(crack, 0.55 + heat * 0.4, np.where(pore, 0.5, 0.0))
    return Tex(ctx, col, height=np.where(crack, 0.15, 0.55 + np.clip(border / 4, 0, 0.3)), smooth=0.3,
               emissive=em, porosity=0.1)


register("block/magma", magma, frames=3, frametime=12, interpolate=True)


# ---------------------------------------------------------------- glowstone / shroomlight

@texture("block/glowstone")
def glowstone(ctx):
    vo = ctx.voronoi(12, "gls", min_dist=3.0)
    border = vo["f2"] - vo["f1"]
    tone = ctx.rng("glt").uniform(0.3, 0.9, len(vo["points"])).astype(np.float32)
    lit = np.clip(-(vo["dx"] + vo["dy"]) / 3, -0.4, 0.4)
    v = tone[vo["id"]] + lit * 0.5 + (ctx.texel_noise("glg") - 0.5) * 0.2
    col = ctx.palette(GLOW[1:], np.clip(v, 0, 1))
    gap = border < 0.75
    col = np.where(gap[..., None], GLOW[0], col)
    em = np.where(gap, 0.35, 0.75 + np.clip(v, 0, 1) * 0.25)
    return Tex(ctx, col, height=np.where(gap, 0.2, 0.5 + np.clip(border / 3, 0, 0.35)), smooth=0.55,
               f0=0.05, emissive=em)


@texture("block/shroomlight")
def shroomlight(ctx):
    n = ctx.noise(5, 3, 0.55, salt="shr")
    v = n * 0.55 + ctx.texel_noise("shrg") * 0.25
    col = ctx.palette(SHROOM[:4], np.clip(v, 0, 1))
    t = Tex(ctx, col, height=0.45 + n * 0.2, smooth=0.25, sss=0.4, emissive=0.35)
    # bright glowing bulbs
    t = ore_clusters(ctx, t, pal("e8902e", "ffc457", "ffe08a", "fff6d0"), salt="bulb", count=7,
                     size=(2, 5), min_dist=4.3, smooth=0.4, glow=1.0, rim=0.8)
    return t


# ---------------------------------------------------------------- soul sand / soil

@texture("block/soul_sand")
def soul_sand(ctx):
    t = granular(ctx, SOUL_SAND, salt="ss", dark=SOUL_SAND[0], light=SOUL_SAND[-1], porosity=0.9)
    # hollow pockets: pairs of oval pits above a wider one (trapped souls, stylised)
    rng = ctx.rng("ssp")
    for i in range(4):
        cx, cy = float(rng.uniform(0, 16)), float(rng.uniform(0, 16))
        for ox, oy, rx, ry in ((-1.5, 0, 0.8, 1.1), (1.5, 0, 0.8, 1.1), (0, 3, 1.6, 0.9)):
            for wx in (-16, 0, 16):
                for wy in (-16, 0, 16):
                    e = (((ctx.x - (cx + ox + wx)) / rx) ** 2 + ((ctx.y - (cy + oy + wy)) / ry) ** 2) < 1
                    if not e.any():
                        continue
                    lip = np.roll(e, ctx.s, 0) & ~e
                    t.color = np.where(e[..., None], SOUL_SAND[0] * 0.7, t.color)
                    t.color = np.where(lip[..., None], SOUL_SAND[-1], t.color)
                    t.height = np.where(e, 0.1, t.height)
    return t


@texture("block/soul_soil")
def soul_soil(ctx):
    t = mottled(ctx, SOUL_SOIL[1:], cell=4, contrast=0.45, salt="soil", smooth=0.05, porosity=0.8)
    pits(ctx, t, 0.08, "soilp", dark_f=0.6, lit_f=1.12)
    speckle(ctx, t, pal("6e5a4a")[0], 0.04, "soill", height=0.6)
    return t
