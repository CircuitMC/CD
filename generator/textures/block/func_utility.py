"""Utility blocks: anvils, cauldron, hopper, grindstone, stonecutter,
enchanting table, brewing stand, beacon, conduit, bell, lodestone, respawn
anchor, TNT, item frames, jack o'lantern, farmland, dirt path, frosted ice,
cobweb, sponges and slime block."""
import math

import numpy as np

from ...engine import GOLD, IRON, Tex, pal
from ...materials import DIRT, STONE, lerp, rock, soil
from .func_common import (DARK_IRON, DARK_WOOD, GOLD_P, IRON_P, MSTONE, OAK, OBSIDIAN, SMOOTH, M,
                          bevel, bind, blank, cast_shadow, glyph, metal_surface, paint, rectm, reg, ring,
                          rivet, stone_surface, surface, texel_set, tone)

ANVIL = pal("1f1f23", "2a2a2f", "36363c", "434349", "515158", "616168", "75757c")


# ------------------------------------------------------------------ anvil
def anvil_side(ctx):
    t = metal_surface(ctx.sub("block/anvil"), ANVIL, salt="an", lo=0.25, hi=0.7, brushed=False, smooth=0.45)
    ham = ctx.voronoi(10, "ham", min_dist=3.5)
    dent = np.clip(ham["f1"] / 3, 0, 1)
    t.color = np.clip(t.color * (0.92 + dent[..., None] * 0.12), 0, 1)
    t.height = 0.45 + dent * 0.1
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16), lit=1.25, dark=0.7)
    return t


def anvil_top(ctx, damage=0):
    t = anvil_side(ctx.sub("block/anvil"))
    face = rectm(ctx, 3, 0, 13, 16)
    n = ctx.noise(1, 2, 0.5, salt="face", stretch=(1, 5))
    paint(t, face, ctx.palette(ANVIL[2:], 0.35 + n * 0.4), h=0.55, smooth=0.6)
    worn = rectm(ctx, 5, 2, 11, 14)
    tone(t, worn, 1.12)
    paint(t, rectm(ctx, 3, 0, 4, 16), ANVIL[5])
    paint(t, rectm(ctx, 12, 0, 13, 16), ANVIL[1])
    rng = ctx.rng(f"crack{damage}")
    for _ in range(damage * 3):
        x, y = float(rng.integers(4, 12)), float(rng.integers(0, 14))
        for _ in range(int(rng.integers(3, 6))):
            nx, ny = x + rng.choice([-1, 0, 1]), y + 1
            m = M(ctx.segment(x + 0.5, y + 0.5, nx + 0.5, ny + 0.5, 0.8)) & face
            paint(t, m, ANVIL[0], h=0.15)
            x, y = nx, ny
    for _ in range(damage * 2):
        x, y = int(rng.integers(3, 12)), int(rng.integers(0, 15))
        chip = rectm(ctx, x, y, x + 2, y + 1)
        paint(t, chip, ANVIL[1], h=0.3)
    return t


# ------------------------------------------------------------------ cauldron & hopper
CAUL = pal("1f1f24", "2c2c32", "3a3a41", "4a4a52", "5c5c65", "70707a", "878791")


def cauldron_side(ctx):
    t = metal_surface(ctx.sub("block/cauldron"), CAUL, salt="cs", lo=0.3, hi=0.7, brushed=False, smooth=0.4)
    rim = rectm(ctx, 0, 0, 16, 2)
    paint(t, rim, ctx.palette(CAUL[3:], ctx.texel_noise("rim")), h=0.7)
    bevel(ctx, t, rim)
    band = rectm(ctx, 0, 9, 16, 10)
    paint(t, band, CAUL[2], h=0.4)
    tone(t, rectm(ctx, 0, 10, 16, 11), 1.15)
    gap = rectm(ctx, 4, 13, 12, 16)
    paint(t, gap, CAUL[0], h=0.1)
    for x0 in (0, 12):
        leg = rectm(ctx, x0, 13, x0 + 4, 16)
        bevel(ctx, t, leg)
    return t


def cauldron_top(ctx):
    t = metal_surface(ctx.sub("block/cauldron_t"), CAUL, salt="ct", lo=0.35, hi=0.8, brushed=False)
    inner = rectm(ctx, 2, 2, 14, 14)
    paint(t, inner, CAUL[0], h=0.1)
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16))
    tone(t, ring(ctx, 2, 2, 14, 14) & (rectm(ctx, 2, 2, 14, 3) | rectm(ctx, 2, 2, 3, 14)), 0.7)
    return t


def cauldron_inner(ctx):
    t = metal_surface(ctx.sub("block/cauldron_i"), CAUL, salt="ci", lo=0.15, hi=0.55, brushed=False, smooth=0.35)
    rust = ctx.noise(4, 2, 0.5, salt="rust") > 0.72
    paint(t, rust, ctx.palette(pal("3a2a22", "4c3528", "5b4030"), ctx.texel_noise("rs")), smooth=0.1, metal=0)
    return t


def cauldron_bottom(ctx):
    t = metal_surface(ctx.sub("block/cauldron_b"), CAUL, salt="cb", lo=0.2, hi=0.6, brushed=False)
    for cx, cy in ((0, 0), (12, 0), (0, 12), (12, 12)):
        leg = rectm(ctx, cx, cy, cx + 4, cy + 4)
        paint(t, leg, ctx.palette(CAUL[3:], ctx.texel_noise("lg")), h=0.7)
        bevel(ctx, t, leg)
    return t


HOP = pal("26262b", "333339", "414148", "505058", "61616a", "75757e")


def hopper_outside(ctx):
    t = metal_surface(ctx.sub("block/hopper"), HOP, salt="ho", lo=0.3, hi=0.75)
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16))
    for y in (5, 11):
        tone(t, rectm(ctx, 0, y, 16, y + 1), 0.7)
        tone(t, rectm(ctx, 0, y + 1, 16, y + 2), 1.12)
    for x, y in ((2, 2), (13, 2), (2, 8), (13, 8), (2, 13), (13, 13)):
        rivet(ctx, t, x + 0.5, y + 0.5, HOP)
    return t


def hopper_top(ctx):
    t = metal_surface(ctx.sub("block/hopper_t"), HOP, salt="htp", lo=0.4, hi=0.85)
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16))
    inner = rectm(ctx, 2, 2, 14, 14)
    paint(t, inner, HOP[0], h=0.1)
    tone(t, rectm(ctx, 2, 2, 14, 3) | rectm(ctx, 2, 2, 3, 14), 0.75)
    return t


def hopper_inside(ctx):
    t = metal_surface(ctx.sub("block/hopper_i"), HOP, salt="hi", lo=0.1, hi=0.5)
    funnel = rectm(ctx, 6, 6, 10, 10)
    paint(t, funnel, pal("0e0e10")[0], h=0.05)
    for k in range(1, 5):
        tone(t, ring(ctx, 6 - k, 6 - k, 10 + k, 10 + k), 0.75 + k * 0.06)
    return t


# ------------------------------------------------------------------ grindstone & stonecutter
GRIND = pal("6e6a63", "807b73", "928d84", "a39e95", "b4afa6", "c4c0b8")


def grindstone_round(ctx):
    n = ctx.noise(2, 2, 0.5, salt="gr")
    g = ctx.texel_noise("gr")
    t = Tex(ctx, ctx.palette(GRIND, n * 0.4 + g * 0.6), height=0.45 + g * 0.2, smooth=0.1, porosity=0.4)
    for x in range(0, 16, 4):
        tone(t, rectm(ctx, x, 0, x + 1, 16), 0.9)
    return t


def grindstone_side(ctx):
    t = grindstone_round(ctx.sub("block/grindstone_round"))
    d = np.hypot(ctx.x - 6, ctx.y - 6)
    disc = d < 6.2
    paint(t, ~disc & rectm(ctx, 0, 0, 12, 12), GRIND[0])
    for r, f in ((5.0, 0.85), (3.2, 0.9)):
        tone(t, (np.abs(d - r) < 0.5), f)
    hub = d < 1.6
    paint(t, hub, ctx.palette(IRON_P[2:5], ctx.texel_noise("hub")), h=0.7, metal=IRON)
    tone(t, M(ctx.edge(disc, 1, "tl")), 1.12)
    tone(t, M(ctx.edge(disc, 1, "br")), 0.75)
    return t


def grindstone_pivot(ctx):
    t = surface(ctx.sub("block/grindstone_pivot"), DARK_WOOD, salt="gp", cell=3, lo=0.2, hi=0.9, smooth=0.2)
    n = ctx.noise(1, 2, 0.5, salt="gpg", stretch=(1, 5))
    t.color = ctx.palette(DARK_WOOD, 0.2 + n * 0.6)
    cap = rectm(ctx, 0, 0, 16, 4)
    paint(t, cap, ctx.palette(IRON_P[2:5], ctx.texel_noise("pc")), h=0.7, metal=IRON, smooth=0.55)
    bevel(ctx, t, cap)
    for x in (2, 6, 10, 14):
        rivet(ctx, t, x + 0.5, 1.5, IRON_P)
    return t


def stonecutter_side(ctx):
    t = stone_surface(ctx.sub("block/stonecutter_body"), MSTONE, salt="scs")
    trim = rectm(ctx, 0, 7, 16, 9)
    paint(t, trim, ctx.palette(IRON_P[2:5], ctx.noise(1, 1, salt="tr", stretch=(5, 1))), h=0.7, metal=IRON)
    bevel(ctx, t, trim)
    bevel(ctx, t, rectm(ctx, 0, 9, 16, 16))
    return t


def stonecutter_top(ctx):
    t = surface(ctx.sub("block/stonecutter_top"), SMOOTH, salt="sct", cell=8, lo=0.3, hi=0.8, smooth=0.35)
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16))
    slot = rectm(ctx, 1, 7, 15, 9)
    paint(t, slot, pal("141416")[0], h=0.05)
    tone(t, rectm(ctx, 1, 6, 15, 7), 0.8)
    tone(t, rectm(ctx, 1, 9, 15, 10), 1.15)
    return t


def stonecutter_bottom(ctx):
    t = stone_surface(ctx.sub("block/stonecutter_body"), MSTONE, salt="scb")
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16))
    return t


def stonecutter_saw(ctx):
    t = blank(ctx)
    SAW = pal("4a4a52", "6e6e78", "9a9aa4", "c4c4cc", "e8e8ee")
    ang = np.arctan2(ctx.y - 16, ctx.x - 8)
    d = np.hypot(ctx.x - 8, ctx.y - 16)
    rot = ctx.frame / max(1, ctx.frames) * (2 * math.pi / 12)
    teeth = (((ang - rot) % (2 * math.pi / 12)) / (2 * math.pi / 12))
    edge_r = 6.2 + teeth * 1.2
    blade = (d < edge_r) & (ctx.y >= 9)
    paint(t, blade, ctx.palette(SAW, np.clip(0.45 + (6 - d) * 0.05 + ctx.texel_noise("sw") * 0.15, 0, 1)),
          h=0.7, alpha=1, metal=IRON, smooth=0.75)
    paint(t, blade & (d > 5.3), SAW[4] if ctx.frame % 2 == 0 else SAW[3])
    for k in range(3):
        a = rot * 3 + k * 2 * math.pi / 3 - math.pi / 2
        hole = M(ctx.circle(8 + math.cos(a) * 3.3, 16 + math.sin(a) * 3.3, 0.9))
        paint(t, hole & blade, SAW[1])
    hub = d < 2.0
    paint(t, hub & blade, SAW[0])
    t.alpha = (t.alpha > 0.5).astype(np.float32)
    return t


# ------------------------------------------------------------------ enchanting table
CLOTH = pal("4a0a12", "6a1019", "8a1822", "a8222c", "c23a3c")
DIAMOND = pal("1c8a86", "3fd1c9", "a4f7f0")


def obsidian(ctx, salt="ob"):
    n = ctx.noise(4, 3, 0.55, salt=f"obs{salt}")
    g = ctx.texel_noise(f"obs{salt}")
    t = Tex(ctx, ctx.palette(OBSIDIAN, n * 0.6 + g * 0.4), height=0.5 + n * 0.15, smooth=0.75, f0=0.05)
    hi_m = (g > 0.93)
    paint(t, hi_m, OBSIDIAN[-1])
    return t


def ench_top(ctx):
    t = obsidian(ctx.sub("block/ench_obsidian"), "top")
    cloth = rectm(ctx, 2, 2, 14, 14)
    n = ctx.noise(2, 2, 0.5, salt="cl")
    paint(t, cloth, ctx.palette(CLOTH, 0.3 + n * 0.5), h=0.6, smooth=0.1, sss=0.2, f0=0.03)
    bevel(ctx, t, cloth)
    trim = ring(ctx, 3, 3, 13, 13)
    paint(t, trim, GOLD_P[3], h=0.65, metal=GOLD, smooth=0.6)
    for cx, cy in ((0, 0), (13, 0), (0, 13), (13, 13)):
        gem = glyph(ctx, [".#.", "###", ".#."], cx, cy)
        paint(t, gem, DIAMOND[1], h=0.8, smooth=0.9, f0=0.17)
        paint(t, gem & texel_set(ctx, [(cx + 1, cy), (cx, cy + 1)]), DIAMOND[2])
        paint(t, gem & texel_set(ctx, [(cx + 2, cy + 1), (cx + 1, cy + 2)]), DIAMOND[0])
    sigil = glyph(ctx, ["..#..", ".#.#.", "#.#.#", ".#.#.", "..#.."], 6, 6)
    paint(t, sigil, GOLD_P[4], metal=GOLD, emissive=0.15)
    return t


def ench_side(ctx):
    t = obsidian(ctx.sub("block/ench_obsidian"), "side")
    cloth = rectm(ctx, 0, 4, 16, 8)
    n = ctx.noise(1, 2, 0.5, salt="cs", stretch=(1, 3))
    paint(t, cloth, ctx.palette(CLOTH, 0.25 + n * 0.55), h=0.6, smooth=0.1, sss=0.2, f0=0.03)
    for x in range(1, 16, 3):
        tassel = rectm(ctx, x, 8, x + 1, 10 + (x % 2))
        paint(t, tassel, CLOTH[2], h=0.6, sss=0.2)
    paint(t, rectm(ctx, 0, 4, 16, 5), GOLD_P[3], metal=GOLD, smooth=0.6, h=0.65)
    for x in (2, 8, 14):
        gem = rectm(ctx, x - 1, 12, x + 1, 14)
        paint(t, gem, DIAMOND[1], smooth=0.9, f0=0.17, h=0.75)
        paint(t, texel_set(ctx, [(x - 1, 12)]), DIAMOND[2])
    return t


def ench_bottom(ctx):
    return obsidian(ctx.sub("block/ench_obsidian"), "bot")


# ------------------------------------------------------------------ brewing stand
BLAZE = pal("7a4a0c", "b0720f", "e0a020", "f8d050", "fff0a0")


def brewing_stand(ctx):
    t = blank(ctx)
    rod = rectm(ctx, 7, 1, 9, 16)
    v = 0.45 + (ctx.tx == 7) * 0.35 + ctx.texel_noise("rod") * 0.15
    paint(t, rod, ctx.palette(BLAZE, np.clip(v, 0, 1)), h=0.75, alpha=1, emissive=0.15)
    paint(t, rectm(ctx, 7, 0, 9, 1), BLAZE[1], h=0.7, alpha=1)
    # arms
    for side in (0, 1):
        pts = [(1.5, 6.5), (6.5, 3.5)] if side == 0 else [(14.5, 6.5), (9.5, 3.5)]
        arm = M(ctx.segment(*pts[0], *pts[1], 1.0))
        paint(t, arm, IRON_P[3], h=0.65, alpha=1, metal=IRON)
        hook_x = 1 if side == 0 else 14
        paint(t, rectm(ctx, hook_x, 6, hook_x + 1, 9), IRON_P[2], h=0.6, alpha=1, metal=IRON)
    # bottle on the left half
    bottle = glyph(ctx, [".##.", ".##.", "####", "####", "####", ".##."], 0, 10)
    GL = pal("6f8fa0", "9cc0d0", "d6eef6")
    paint(t, bottle, GL[1], h=0.6, alpha=1, smooth=0.9)
    paint(t, bottle & texel_set(ctx, [(0, 12), (0, 13), (1, 10)]), GL[2])
    paint(t, bottle & texel_set(ctx, [(3, 13), (3, 14), (2, 15)]), GL[0])
    return t


def brewing_base(ctx):
    t = stone_surface(ctx.sub("block/brewing_base"), MSTONE, salt="bb", lo=0.3, hi=0.9)
    for cx, cy in ((1, 9), (9, 1), (9, 9)):
        c = rectm(ctx, cx, cy, cx + 6, cy + 6)
        bevel(ctx, t, c)
    return t


# ------------------------------------------------------------------ beacon, conduit, bell, lodestone
def beacon(ctx):
    BC = pal("2a8a92", "4fd0d6", "8ff2f2", "d0fffd", "ffffff")
    d = np.maximum(np.abs(ctx.x - 8), np.abs(ctx.y - 8))
    dr = np.hypot(ctx.x - 8, ctx.y - 8)
    v = np.clip(1.1 - dr / 9, 0, 1) * 0.8 + ctx.texel_noise("bc") * 0.15
    t = Tex(ctx, ctx.palette(BC, v), height=0.55, smooth=0.9, f0=0.17, emissive=0.85 + v * 0.15)
    fr = d >= 6.5
    paint(t, fr, ctx.palette(BC[:3], 0.3 + ctx.texel_noise("bf") * 0.5), h=0.6, emissive=0.6)
    tone(t, rectm(ctx, 0, 0, 16, 1) | rectm(ctx, 0, 0, 1, 16), 1.2)
    star = glyph(ctx, ["..#..", "..#..", "#####", "..#..", "..#.."], 6, 6)
    paint(t, star, BC[4], emissive=1.0)
    return t


PRIS = pal("2c5650", "3c7068", "4f8a7e", "66a394", "82bba9")


def conduit(ctx):
    n = ctx.noise(3, 2, 0.5, salt="cd")
    t = Tex(ctx, ctx.palette(PRIS, n * 0.6 + ctx.texel_noise("cd") * 0.4), height=0.5 + n * 0.1, smooth=0.5)
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16))
    for x0 in (0, 8):
        for y0 in (0, 8):
            tone(t, ring(ctx, x0 + 1, y0 + 1, x0 + 7, y0 + 7), 0.85)
    eye = M(ctx.circle(8, 8, 3.3)) if not ctx.pixel_art else glyph(ctx, [".##.", "####", "####", ".##."], 6, 6)
    HEART = pal("1a3a6a", "2a64b0", "4ea0e8", "a8e0ff")
    paint(t, eye, ctx.palette(HEART, 0.4 + ctx.texel_noise("eye") * 0.4), h=0.7, emissive=0.7, smooth=0.9)
    paint(t, texel_set(ctx, [(7, 7)]), HEART[3], emissive=1.0)
    return t


def bell(ctx, face="side"):
    t = metal_surface(ctx.sub("block/bell"), GOLD_P, salt="bell", metal=GOLD, lo=0.3, hi=0.75, smooth=0.75)
    if face == "side":
        v = np.clip(0.75 - np.abs(ctx.x - 5) / 14, 0, 1)
        t.color = ctx.palette(GOLD_P, v * 0.7 + ctx.texel_noise("bs") * 0.15 + 0.1)
        for y in (2, 12):
            paint(t, rectm(ctx, 0, y, 16, y + 1), GOLD_P[5])
            paint(t, rectm(ctx, 0, y + 1, 16, y + 2), GOLD_P[1])
    elif face == "top":
        d = np.hypot(ctx.x - 8, ctx.y - 8)
        tone(t, np.abs(d - 5) < 0.6, 0.75)
        lug = rectm(ctx, 6, 6, 10, 10)
        paint(t, lug, GOLD_P[4], h=0.7)
        bevel(ctx, t, lug)
    else:
        d = np.hypot(ctx.x - 8, ctx.y - 8)
        paint(t, d < 6, ctx.palette(pal("2e1e06", "4a320c", "6a4a14"), np.clip(d / 6, 0, 1)), h=0.1,
              smooth=0.4)
        clapper = d < 1.6
        paint(t, clapper, GOLD_P[2])
    return t


def lodestone(ctx, top=False):
    t = rock(ctx.sub("block/lodestone_stone"), STONE, cell=6, streaks=1)
    if top:
        fr = ring(ctx, 0, 0, 16, 16, 2)
        bevel(ctx, t, rectm(ctx, 0, 0, 16, 16))
        tone(t, fr, 1.05)
        core = rectm(ctx, 4, 4, 12, 12)
        paint(t, core, ctx.palette(IRON_P[1:5], ctx.texel_noise("lc")), h=0.65, metal=IRON, smooth=0.6)
        bevel(ctx, t, core)
        needle = glyph(ctx, ["...#", "..#.", ".#..", "#..."], 6, 6)
        paint(t, needle, pal("b52020")[0], metal=0)
        paint(t, texel_set(ctx, [(6, 9)]), IRON_P[6])
        return t
    # side: chiseled block with an iron band
    t2, _ = t, None
    for y0 in (0, 10):
        blk = rectm(ctx, 0, y0, 16, y0 + 6)
        bevel(ctx, t2, blk)
    band = rectm(ctx, 0, 6, 16, 10)
    paint(t2, band, ctx.palette(IRON_P[1:5], ctx.noise(1, 1, salt="lb", stretch=(6, 1))), h=0.7, metal=IRON)
    bevel(ctx, t2, band)
    for x in (2, 7, 13):
        rivet(ctx, t2, x + 0.5, 7.5, IRON_P)
    return t2


# ------------------------------------------------------------------ respawn anchor
GLOWSTONE = pal("7a4a12", "b8761c", "e8a834", "ffd56a", "fff2b0")
ANCHOR_GLOW = pal("3a0a6a", "6a18b8", "a43ef0", "d48aff", "ffd0ff")


def anchor_body(ctx, salt="ab"):
    t = obsidian(ctx.sub("block/anchor_obsidian"), salt)
    # crying veins
    vein = ctx.noise(3, 2, 0.5, salt="cry") > 0.8
    paint(t, vein & (ctx.texel_noise("cv", soft=False) > 0.55), ANCHOR_GLOW[1], emissive=0.3)
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16))
    return t


def anchor_side(ctx, charge=0):
    t = anchor_body(ctx, "as")
    frame = rectm(ctx, 5, 1, 11, 15)
    paint(t, frame, ctx.palette(OBSIDIAN[2:], ctx.texel_noise("af")), h=0.65)
    bevel(ctx, t, frame)
    for i in range(4):
        y0 = 11 - i * 3
        cell = rectm(ctx, 6, y0, 10, y0 + 3) & ~rectm(ctx, 6, y0 + 2, 10, y0 + 3)
        if i < charge:
            paint(t, cell, ctx.palette(GLOWSTONE[2:], ctx.texel_noise(f"g{i}")), h=0.55, emissive=0.9)
        else:
            paint(t, cell, OBSIDIAN[0], h=0.3)
    return t


def anchor_top(ctx, on=True):
    t = anchor_body(ctx, "at")
    for cx, cy in ((0, 0), (12, 0), (0, 12), (12, 12)):
        c = rectm(ctx, cx + 1, cy + 1, cx + 3, cy + 3)
        paint(t, c, GLOWSTONE[3] if on else GLOWSTONE[0], emissive=0.7 if on else 0, h=0.6)
    well = rectm(ctx, 3, 3, 13, 13)
    bevel(ctx, t, well, raised=False)
    if on:
        ph = ctx.frame / max(1, ctx.frames) * 2 * math.pi
        dx, dy = ctx.x - 8, ctx.y - 8
        r = np.hypot(dx, dy)
        a = np.arctan2(dy, dx)
        n = ctx.noise(2, 2, 0.5, salt="swirl")
        sw = 0.5 + 0.5 * np.sin(r * 1.5 + (n - 0.5) * 3 + np.sin(a + ph) * 0.6 + ph)
        v = np.clip(sw * 0.55 + n * 0.25 + np.clip(1 - r / 6, 0, 1) * 0.3, 0, 1)
        paint(t, rectm(ctx, 4, 4, 12, 12), ctx.palette(ANCHOR_GLOW, v), h=0.4, emissive=0.6 + v * 0.4, smooth=0.9)
    else:
        paint(t, rectm(ctx, 4, 4, 12, 12), ctx.palette(OBSIDIAN[:3], ctx.texel_noise("off")), h=0.3)
    return t


def anchor_bottom(ctx):
    t = anchor_body(ctx, "abt")
    tone(t, ring(ctx, 4, 4, 12, 12), 0.7)
    return t


# ------------------------------------------------------------------ TNT
TNT_RED = pal("6a1410", "8e1d16", "b02a1e", "cc3a26", "e2563a")
PAPER = pal("a49c86", "c4bca4", "ddd6c0", "efe9d8")


def tnt_side(ctx):
    n = ctx.noise(1, 2, 0.5, salt="tnt", stretch=(1, 4))
    t = Tex(ctx, ctx.palette(TNT_RED, 0.5), height=0.55, smooth=0.25, porosity=0.3)
    for i in range(4):
        x0 = i * 4
        stick = rectm(ctx, x0, 0, x0 + 4, 16)
        lx = (ctx.x - x0) / 4
        v = np.clip(0.85 - lx * 0.6 + (n - 0.5) * 0.25, 0, 1)
        paint(t, stick, ctx.palette(TNT_RED, v), h=0.55 + (0.5 - np.abs(lx - 0.4)) * 0.3)
        paint(t, rectm(ctx, x0 + 3, 0, x0 + 4, 16), TNT_RED[0], h=0.2)
    band = rectm(ctx, 0, 5, 16, 11)
    paint(t, band, ctx.palette(PAPER, 0.4 + ctx.texel_noise("pp") * 0.5), h=0.65, porosity=0.4)
    paint(t, rectm(ctx, 0, 5, 16, 6), PAPER[3])
    paint(t, rectm(ctx, 0, 10, 16, 11), PAPER[0])
    # hazard burst emblem
    burst = glyph(ctx, ["#..#..#", ".#.#.#.", "..###..", ".#.#.#."], 5, 6)
    paint(t, burst, pal("2a1a14")[0], h=0.6)
    paint(t, texel_set(ctx, [(8, 8)]), TNT_RED[3])
    for x in (1, 13):
        paint(t, rectm(ctx, x, 7, x + 2, 9), pal("2a1a14")[0])
    return t


def tnt_end(ctx, fuse=True):
    t = Tex(ctx, ctx.palette(PAPER, 0.3), height=0.4, smooth=0.2, porosity=0.4)
    POWDER = pal("2c2a28", "3e3a36", "524c46")
    for gx in range(4):
        for gy in range(4):
            x0, y0 = gx * 4, gy * 4
            rim = glyph(ctx, [".##.", "#..#", "#..#", ".##."], x0, y0)
            core = rectm(ctx, x0 + 1, y0 + 1, x0 + 3, y0 + 3)
            corner = rectm(ctx, x0, y0, x0 + 4, y0 + 4) & ~rim & ~core
            paint(t, rim, TNT_RED[3], h=0.6)
            paint(t, rim & (rectm(ctx, x0 + 3, y0, x0 + 4, y0 + 4) | rectm(ctx, x0, y0 + 3, x0 + 4, y0 + 4)),
                  TNT_RED[1])
            paint(t, rim & texel_set(ctx, [(x0 + 1, y0), (x0, y0 + 1)]), TNT_RED[4])
            paint(t, core, ctx.palette(PAPER[1:], ctx.texel_noise("pw")), h=0.5)
            paint(t, core & texel_set(ctx, [(x0 + 2, y0 + 2)]), POWDER[1])
            paint(t, corner, TNT_RED[0], h=0.2)
    if fuse:
        f = rectm(ctx, 7, 7, 9, 9)
        paint(t, f, pal("8a7a5a")[0], h=0.85)
        paint(t, texel_set(ctx, [(7, 7)]), pal("c4b48c")[0])
        paint(t, texel_set(ctx, [(8, 8)]), pal("4a3e2c")[0])
    return t


# ------------------------------------------------------------------ item frames, jack o'lantern
LEATHER = pal("4a2e1a", "5e3c22", "73492b", "865735", "966540")


def item_frame(ctx, glow=False):
    p = LEATHER if not glow else pal("1d4a4a", "26605c", "33786f", "4a9585", "6cb4a0")
    n = ctx.noise(3, 2, 0.5, salt="lf")
    t = Tex(ctx, ctx.palette(p, 0.3 + n * 0.4 + ctx.texel_noise("lf") * 0.2), height=0.5 + n * 0.08,
            smooth=0.3, porosity=0.2)
    stitch = ring(ctx, 2, 2, 14, 14) & (((ctx.tx + ctx.ty) % 2) == 0)
    paint(t, stitch, p[4] if not glow else pal("bff0d8")[0], h=0.6, emissive=0.6 if glow else 0)
    tone(t, ring(ctx, 0, 0, 16, 16, 2), 0.8)
    if glow:
        t.emissive = np.maximum(t.emissive, 0.25)
    return t


PUMPKIN = pal("8a3e08", "a8520c", "c46812", "da7e1c", "e8942a", "f2aa42")


def jack_o_lantern(ctx):
    n = ctx.noise(2, 2, 0.5, salt="pk", stretch=(1, 4))
    rib = (np.cos((ctx.x + 1) / 16 * 2 * math.pi * 4) + 1) / 2
    v = 0.25 + rib * 0.45 + (n - 0.5) * 0.25
    t = Tex(ctx, ctx.palette(PUMPKIN, v), height=0.4 + rib * 0.25, smooth=0.3, porosity=0.1)
    paint(t, M(np.isin(ctx.tx, [3, 7, 11, 15])) & (ctx.texel_noise("rb", soft=False) > 0.5), PUMPKIN[1],
          h=0.25)
    GL = pal("f0b030", "ffd860", "fff0a0", "fffbe0")
    face = glyph(ctx, [
        "..###......###..",
        ".#####....#####.",
        ".#####....#####.",
        "..###......###..",
        "................",
        ".......##.......",
        "................",
        ".##############.",
        ".#.##########.#.",
        "..####.##.####..",
        "....##....##...."], 0, 4)
    d = np.hypot(ctx.x - 8, ctx.y - 9)
    paint(t, face, ctx.palette(GL, np.clip(1.15 - d / 8, 0, 1)), h=0.2, emissive=0.95, smooth=0.1)
    flesh = M(ctx.edge(face, 1, "tl")) & face
    paint(t, flesh, pal("d88a28")[0], emissive=0.6)
    s1 = ctx.s
    around = np.zeros_like(face)
    for dy in (-s1, 0, s1):
        for dx in (-s1, 0, s1):
            around |= np.roll(np.roll(face, dy, 0), dx, 1)
    rind = around & ~face
    paint(t, rind, PUMPKIN[0], h=0.35)
    return t


# ------------------------------------------------------------------ farmland, dirt path
def farmland(ctx, moist=False):
    t = soil(ctx.sub("block/farmland_soil"), DIRT, salt="fm", pebbles=3)
    if moist:
        t.color = np.clip(t.color * np.array([0.62, 0.55, 0.5]), 0, 1)
        t.smooth = np.full_like(t.smooth, 0.45)
    for k in range(4):
        y0 = k * 4
        ridge = rectm(ctx, 0, y0, 16, y0 + 2)
        furrow = rectm(ctx, 0, y0 + 3, 16, y0 + 4)
        tone(t, ridge & rectm(ctx, 0, y0, 16, y0 + 1), 1.15)
        tone(t, furrow, 0.62)
        t.height[M(ridge)] += 0.15
        t.height[M(furrow)] = 0.12
    if moist:
        wet = (ctx.texel_noise("wet", soft=False) > 0.9) & M(np.isin(ctx.ty % 4, [3]))
        paint(t, wet, pal("2c1e14")[0], smooth=0.8)
    return t


PATH = pal("6e5634", "806640", "92764b", "a08356", "ae9162", "bc9f6e")


def dirt_path_top(ctx):
    n = ctx.noise(5, 2, 0.5, salt="path")
    g = ctx.texel_noise("path")
    t = Tex(ctx, ctx.palette(PATH, n * 0.55 + g * 0.45), height=0.5 + n * 0.08, smooth=0.12, porosity=0.6)
    peb = ctx.texel_noise("pb", soft=False) > 0.95
    paint(t, peb, PATH[-1], h=0.65)
    tread = (ctx.noise(2, 1, 0.5, salt="trd", stretch=(1, 4)) > 0.7)
    tone(t, tread, 0.9)
    return t


def dirt_path_side(ctx):
    t = soil(ctx.sub("block/dirt"), DIRT)
    top = dirt_path_top(ctx.sub("block/dirt_path_top"))
    lip_depth = 3 + (ctx.lattice_noise(4, 16, "lip") > 0.5)
    lip = ctx.y < lip_depth
    paint(t, lip, top.color, h=0.6)
    tone(t, rectm(ctx, 0, 1, 16, 2), 1.08)
    edge = M(ctx.edge(lip, 1, "br"))
    tone(t, edge, 0.75)
    return t


# ------------------------------------------------------------------ frosted ice, cobweb, sponges, slime
ICE = pal("6f9ad8", "8cb2e6", "a8c8f0", "c4dcf8", "e2eeff")


def frosted_ice(ctx, stage=0):
    n = ctx.noise(6, 2, 0.5, salt="ice")
    t = Tex(ctx, ctx.palette(ICE, 0.35 + n * 0.4), alpha=0.72 + n * 0.08, height=0.55, smooth=0.9, f0=0.02,
            wrap=True, grain=0.02)
    frost = ctx.noise(3, 2, 0.5, salt="frost")
    paint(t, frost > 0.7, ICE[-1], alpha=0.85)
    vo = ctx.voronoi(4 + stage * 4, f"fi{stage}", min_dist=3)
    crack = (vo["f2"] - vo["f1"]) < (0.25 + stage * 0.18)
    if stage == 0:
        crack &= False
    paint(t, crack, ICE[-1], alpha=0.95, h=0.3)
    paint(t, crack & (vo["f1"] < 1.0 + stage * 0.6), pal("f6fbff")[0])
    paint(t, texel_set(ctx, [(3, 3), (4, 3), (3, 4), (11, 10), (12, 10)]), ICE[-1], alpha=0.9)
    return t


def cobweb(ctx):
    t = blank(ctx)
    WEB = pal("b4b4ba", "d6d6dc", "f2f2f6")
    c = (7.5, 7.5)
    m = np.zeros((ctx.H, ctx.W), bool)
    rng = ctx.rng("web")
    angs = [k * math.pi / 4 + rng.uniform(-0.12, 0.12) for k in range(8)]
    for a in angs:
        m |= M(ctx.segment(c[0], c[1], c[0] + math.cos(a) * 11, c[1] + math.sin(a) * 11, 0.72))
    for r in (3.7, 6.7):
        pts = [(c[0] + math.cos(a) * r, c[1] + math.sin(a) * r) for a in angs]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            sag = 0.35 * r / 5
            mx, my = mx + (c[0] - mx) * sag / r * 2, my + (c[1] - my) * sag / r * 2
            m |= M(ctx.segment(x1, y1, mx, my, 0.72)) | M(ctx.segment(mx, my, x2, y2, 0.72))
    m &= rectm(ctx, 0, 0, 16, 16)
    m &= ~(ctx.texel_noise("gap", soft=False) > 0.9)
    v = ctx.texel_noise("wb") * 0.6 + 0.3
    paint(t, m, ctx.palette(WEB, v), h=0.6, alpha=1, smooth=0.3)
    return t


SPONGE = pal("8a7a1e", "a8962a", "c2b03a", "d6c64c", "e4d662", "efe280")
WET = pal("5e5a18", "746e20", "8a842a", "9c9636", "aea842", "c2bc58")


def sponge(ctx, wet=False):
    p = WET if wet else SPONGE
    vo = ctx.voronoi(16, "pores", min_dist=2.6)
    n = ctx.noise(4, 2, 0.5, salt="spg")
    t = Tex(ctx, ctx.palette(p, 0.4 + n * 0.35 + ctx.texel_noise("sp") * 0.15), height=0.55 + n * 0.1,
            smooth=0.1, porosity=1.0 if not wet else 0.6)
    pore = vo["f1"] < 0.95
    paint(t, pore, p[0], h=0.1)
    lip = (vo["f1"] >= 0.95) & (vo["f1"] < 1.6) & (vo["dy"] > 0.3)
    tone(t, lip, 1.12)
    if wet:
        drops = ctx.texel_noise("drop", soft=False) > 0.94
        paint(t, drops, pal("cfe0c0")[0], smooth=0.9)
        t.smooth = np.maximum(t.smooth, 0.5)
    return t


def slime_block(ctx):
    SL = pal("3e8a2e", "52a83c", "68c04e", "84d468", "a8e88c", "d0f8bc")
    n = ctx.noise(5, 2, 0.5, salt="slb")
    t = Tex(ctx, ctx.palette(SL, 0.35 + n * 0.3), alpha=0.55, height=0.55, smooth=0.85, sss=0.6, f0=0.03,
            grain=0.02)
    fr = ring(ctx, 0, 0, 16, 16, 1)
    paint(t, fr, SL[1], alpha=0.85)
    paint(t, fr & (rectm(ctx, 0, 0, 16, 1) | rectm(ctx, 0, 0, 1, 16)), SL[4])
    core = rectm(ctx, 3, 3, 13, 13)
    paint(t, core, ctx.palette(SL[:4], 0.35 + n * 0.45), alpha=0.9, h=0.5)
    paint(t, ring(ctx, 3, 3, 13, 13), SL[0], alpha=0.95)
    paint(t, texel_set(ctx, [(4, 4), (5, 4), (4, 5), (2, 2)]), SL[5], alpha=0.95)
    paint(t, texel_set(ctx, [(11, 11), (10, 11)]), SL[3], alpha=0.95)
    return t


# ------------------------------------------------------------------ registration
reg("block/anvil", anvil_side)
reg("block/anvil_top", anvil_top)
reg("block/chipped_anvil_top", bind(anvil_top, 1))
reg("block/damaged_anvil_top", bind(anvil_top, 2))
reg("block/cauldron_side", cauldron_side)
reg("block/cauldron_top", cauldron_top)
reg("block/cauldron_inner", cauldron_inner)
reg("block/cauldron_bottom", cauldron_bottom)
reg("block/hopper_outside", hopper_outside)
reg("block/hopper_top", hopper_top)
reg("block/hopper_inside", hopper_inside)
reg("block/grindstone_round", grindstone_round)
reg("block/grindstone_side", grindstone_side)
reg("block/grindstone_pivot", grindstone_pivot)
reg("block/stonecutter_side", stonecutter_side)
reg("block/stonecutter_top", stonecutter_top)
reg("block/stonecutter_bottom", stonecutter_bottom)
reg("block/stonecutter_saw", stonecutter_saw)
reg("block/enchanting_table_top", ench_top)
reg("block/enchanting_table_side", ench_side)
reg("block/enchanting_table_bottom", ench_bottom)
reg("block/brewing_stand", brewing_stand)
reg("block/brewing_stand_base", brewing_base)
reg("block/beacon", beacon)
reg("block/conduit", conduit)
reg("block/bell_side", bell)
reg("block/bell_top", bind(bell, "top"))
reg("block/bell_bottom", bind(bell, "bottom"))
reg("block/lodestone_side", lodestone)
reg("block/lodestone_top", bind(lodestone, True))
for _c in range(5):
    reg(f"block/respawn_anchor_side{_c}", bind(anchor_side, _c))
reg("block/respawn_anchor_top", anchor_top, frametime=2)
reg("block/respawn_anchor_top_off", bind(anchor_top, False))
reg("block/respawn_anchor_bottom", anchor_bottom)
reg("block/tnt_side", tnt_side)
reg("block/tnt_top", tnt_end)
reg("block/tnt_bottom", bind(tnt_end, False))
reg("block/item_frame", item_frame)
reg("block/glow_item_frame", bind(item_frame, True))
reg("block/jack_o_lantern", jack_o_lantern)
reg("block/farmland", farmland)
reg("block/farmland_moist", bind(farmland, True))
reg("block/dirt_path_top", dirt_path_top)
reg("block/dirt_path_side", dirt_path_side)
for _i in range(4):
    reg(f"block/frosted_ice_{_i}", bind(frosted_ice, _i))
reg("block/cobweb", cobweb)
reg("block/sponge", sponge)
reg("block/wet_sponge", bind(sponge, True))
reg("block/slime_block", slime_block)
_ = (DARK_IRON, OAK, lerp, cast_shadow, surface)
