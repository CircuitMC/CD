"""Creatures & food blocks: dragon egg, cake, turtle eggs, sniffer eggs and
the dried ghast (hydration stages 0-3)."""
import math

import numpy as np

from ...engine import Tex, pal
from .func_common import M, bevel, bind, paint, rectm, reg, ring, texel_set, tone

# ------------------------------------------------------------------ dragon egg
DRAGON = pal("08050c", "120b1a", "1d1228", "2a1a3a", "3c2752", "5a3c78")


def dragon_egg(ctx):
    n = ctx.noise(5, 3, 0.55, salt="de")
    g = ctx.texel_noise("de")
    t = Tex(ctx, ctx.palette(DRAGON[:5], n * 0.65 + g * 0.35), height=0.5 + n * 0.12, smooth=0.7, f0=0.05)
    sp = (g > 0.9) & (n > 0.4)
    paint(t, sp, DRAGON[5], h=0.6, emissive=0.1)
    scale = (ctx.voronoi(14, "scale", min_dist=2.5)["f2"] - ctx.voronoi(14, "scale", min_dist=2.5)["f1"]) < 0.4
    tone(t, scale, 0.75)
    return t


# ------------------------------------------------------------------ cake
FROST = pal("c9c0b4", "ddd6cc", "ece7df", "f7f4ef", "fffdfa")
SPONGE = pal("8a5a2a", "a8703a", "c08848", "d4a05e", "e2b674")
BERRY = pal("7a0f18", "b01e26", "e04040")


def cake_top(ctx):
    n = ctx.noise(4, 2, 0.5, salt="ct")
    t = Tex(ctx, ctx.palette(FROST, 0.4 + n * 0.4 + ctx.texel_noise("ct") * 0.15), height=0.6 + n * 0.08,
            smooth=0.5, sss=0.3)
    crust = ring(ctx, 1, 1, 15, 15)
    paint(t, crust, FROST[1])
    tone(t, crust & (rectm(ctx, 1, 14, 16, 15) | rectm(ctx, 14, 1, 15, 16)), 0.9)
    for (x, y) in ((4, 4), (10, 3), (7, 7), (12, 9), (3, 10), (8, 12), (11, 13)):
        b = rectm(ctx, x, y, x + 1, y + 1)
        paint(t, b, BERRY[1], h=0.75, smooth=0.7)
        paint(t, rectm(ctx, x + 1, y, x + 2, y + 1), BERRY[0], h=0.65)
    paint(t, texel_set(ctx, [(7, 7)]), BERRY[2])
    return t


def cake_side(ctx):
    n = ctx.noise(2, 2, 0.5, salt="cs")
    t = Tex(ctx, ctx.palette(SPONGE, 0.35 + n * 0.4 + ctx.texel_noise("cs") * 0.2), height=0.5, smooth=0.1,
            porosity=0.6)
    holes = ctx.texel_noise("ch", soft=False) > 0.88
    paint(t, holes, SPONGE[0], h=0.3)
    drip = ctx.y < 10 + (ctx.lattice_noise(2, 16, "drip") > 0.55) * 1 + (ctx.lattice_noise(3, 16, "drip2") > 0.7)
    paint(t, drip, ctx.palette(FROST, 0.5 + ctx.texel_noise("fd") * 0.4), h=0.65, sss=0.3, smooth=0.5,
          porosity=0)
    tone(t, M(ctx.edge(drip, 1, "br")) & drip, 0.85)
    jam = rectm(ctx, 0, 12, 16, 13)
    paint(t, jam, BERRY[1], h=0.45)
    paint(t, rectm(ctx, 0, 0, 16, 8), ctx.palette(FROST, 0.6 + ctx.texel_noise("tp") * 0.3))
    return t


def cake_inner(ctx):
    t = cake_side(ctx.sub("block/cake_side"))
    sp = ctx.texel_noise("ci", soft=False) > 0.8
    paint(t, sp & (ctx.y > 10), SPONGE[4])
    return t


def cake_bottom(ctx):
    n = ctx.noise(3, 2, 0.5, salt="cb")
    t = Tex(ctx, ctx.palette(SPONGE[:4], 0.2 + n * 0.5 + ctx.texel_noise("cb") * 0.2), height=0.5, smooth=0.1,
            porosity=0.6)
    tone(t, ctx.texel_noise("cbh", soft=False) > 0.85, 0.8)
    return t


# ------------------------------------------------------------------ turtle egg
SHELL = pal("b8b098", "cfc8b0", "e2dcc6", "f0ebda", "faf7ee")
SPOT = pal("3e6a3a", "52844c", "68a060")


def cracks(ctx, t, level, color, salt="cr", region=(0, 0, 16, 16)):
    rng = ctx.rng(f"{salt}{level}")
    x0r, y0r, x1r, y1r = region
    for _ in range(level * 2):
        x, y = float(rng.integers(x0r + 1, x1r - 1)), float(rng.integers(y0r + 1, y1r - 1))
        for _ in range(int(rng.integers(3, 6))):
            nx, ny = x + rng.choice([-1, 0, 1]), y + rng.choice([-1, 1])
            m = M(ctx.segment(x + 0.5, y + 0.5, nx + 0.5, ny + 0.5, 0.8)) & rectm(ctx, *region)
            paint(t, m, color, h=0.2)
            x, y = nx, ny
    return t


def turtle_egg(ctx, crack=0):
    n = ctx.noise(4, 2, 0.5, salt="te")
    t = Tex(ctx, ctx.palette(SHELL, 0.35 + n * 0.4 + ctx.texel_noise("te") * 0.2), height=0.55, smooth=0.4,
            f0=0.04)
    spots = (ctx.noise(2, 2, 0.5, salt="tes") > 0.68)
    spots = ctx.organic(spots, 0.2, "tes")
    paint(t, spots, ctx.palette(SPOT, ctx.texel_noise("sp")), h=0.5)
    cracks(ctx, t, crack, SHELL[0] * 0.6)
    return t


# ------------------------------------------------------------------ sniffer egg
SNIFF = pal("4a1414", "641c1a", "7e2620", "983228", "b04232", "c25a42")
SNIFF_SPOT = pal("1f5a52", "2c7a6c", "3e9a88", "5cb8a2")
FACE_LIGHT = {"top": 1.12, "north": 1.0, "south": 0.95, "east": 0.98, "west": 1.03, "bottom": 0.82}


def sniffer_egg(ctx, crack=0, face="north"):
    n = ctx.noise(5, 3, 0.55, salt=f"se{face}")
    g = ctx.texel_noise(f"se{face}")
    v = 0.3 + n * 0.45 + g * 0.2
    if face not in ("top", "bottom"):
        v = v + (8 - np.abs(ctx.y - 8)) * 0.01
    t = Tex(ctx, ctx.palette(SNIFF, v), height=0.5 + n * 0.15, smooth=0.45, f0=0.04)
    sp = ctx.noise(3, 2, 0.5, salt=f"ses{face}") > 0.7
    sp = ctx.organic(sp, 0.25, f"ses{face}")
    paint(t, sp, ctx.palette(SNIFF_SPOT, ctx.texel_noise(f"ss{face}") * 0.7 + 0.2), h=0.55)
    t.color = np.clip(t.color * FACE_LIGHT[face], 0, 1)
    # soft rim shading toward the egg's edges
    rim = ring(ctx, 0, 0, 16, 16, 1)
    tone(t, rim & (rectm(ctx, 0, 15, 16, 16) | rectm(ctx, 15, 0, 16, 16)), 0.8)
    tone(t, rim & (rectm(ctx, 0, 0, 16, 1) | rectm(ctx, 0, 0, 1, 16)), 1.1)
    if crack:
        cracks(ctx, t, crack * (1 if face != "bottom" else 0) + (crack > 1), pal("f2d488")[0], f"sc{face}")
        if crack > 1:
            glow = (ctx.texel_noise(f"gl{face}", soft=False) > 0.97)
            paint(t, glow, pal("ffe9a8")[0], emissive=0.3)
    return t


# ------------------------------------------------------------------ dried ghast
GHAST = {
    0: pal("4e4238", "62554a", "76685b", "8a7c6e", "9c8f81", "aea294"),
    1: pal("6a6460", "817a75", "98918b", "aca6a0", "bfb9b3", "d0cbc6"),
    2: pal("8e8e94", "a6a6ac", "bcbcc2", "cfcfd4", "dfdfe4", "ececf0"),
    3: pal("a4a8b4", "bcc0ca", "d0d4dc", "e0e3ea", "eceff4", "f8f9fc"),
}


def ghast_skin(ctx, stage, salt):
    p = GHAST[stage]
    n = ctx.noise(4, 2, 0.5, salt=f"gs{salt}")
    g = ctx.texel_noise(f"gs{salt}")
    t = Tex(ctx, ctx.palette(p, 0.35 + n * 0.35 + g * 0.2), height=0.5 + n * 0.1, smooth=0.15 + stage * 0.08,
            sss=0.1 + stage * 0.1, porosity=0.4 - stage * 0.1)
    # wrinkles: fewer and fainter as it rehydrates
    count = (4 - stage) * 2
    rng = ctx.rng(f"wr{salt}")
    for _ in range(count):
        x, y = int(rng.integers(0, 14)), int(rng.integers(1, 15))
        L = int(rng.integers(3, 7))
        w = rectm(ctx, x, y, x + L, y + 1)
        wob = rectm(ctx, x + L // 2, y + 1, x + L, y + 2) if rng.random() < 0.5 else rectm(ctx, x, y - 1, x + 2, y)
        paint(t, w | wob, p[1], h=0.3)
        tone(t, rectm(ctx, x, y + 1, x + L, y + 2) & ~(w | wob), 1.08)
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16), lit=1.1, dark=0.8)
    return t


def ghast_face(ctx, stage, face):
    t = ghast_skin(ctx, stage, face)
    p = GHAST[stage]
    if face == "north":
        dark = pal("1e1a1a")[0]
        # eyes: shut slits when dry, opening as hydration rises
        rows = {0: 1, 1: 1, 2: 2, 3: 3}[stage]
        for x0 in (3, 10):
            eye = rectm(ctx, x0, 6, x0 + 3, 6 + rows)
            paint(t, eye, dark, h=0.15)
            tone(t, rectm(ctx, x0, 5, x0 + 3, 6), 0.8)
            if stage == 3:
                paint(t, texel_set(ctx, [(x0 + 1, 7)]), pal("f6f6ff")[0])
        mouth_w = {0: 2, 1: 2, 2: 3, 3: 4}[stage]
        mx = 8 - mouth_w // 2
        paint(t, rectm(ctx, mx, 11, mx + mouth_w, 12 + (stage >= 2)), dark, h=0.15)
        if stage == 3:
            tear = texel_set(ctx, [(4, 9), (4, 10)])
            paint(t, tear, pal("9ec8f0")[0], smooth=0.9)
    elif face == "bottom":
        for x in range(2, 15, 4):
            for y in range(2, 15, 4):
                paint(t, rectm(ctx, x, y, x + 2, y + 2), p[1], h=0.3)
    elif face == "top":
        tone(t, rectm(ctx, 4, 4, 12, 12), 1.04)
    return t


def ghast_tentacles(ctx, stage):
    p = GHAST[stage]
    t = Tex(ctx, ctx.palette(p, 0.5), height=0.5, smooth=0.15 + stage * 0.08, sss=0.1 + stage * 0.1)
    for i in range(ctx.w // 4):
        x0 = i * 4
        col = rectm(ctx, x0, 0, x0 + 4, ctx.h)
        lx = (ctx.x - x0) / 4
        v = 0.75 - lx * 0.5 + ctx.texel_noise(f"tc{i}") * 0.15
        seg = ((ctx.ty + i * 3) % 5 == 0) & (stage < 3)
        v = np.where(seg, v - 0.25, v)
        paint(t, col, ctx.palette(p, np.clip(v, 0, 1)), h=0.5 + (0.5 - np.abs(lx - 0.45)) * 0.4)
        paint(t, rectm(ctx, x0 + 3, 0, x0 + 4, ctx.h), p[1])
    return t


# ------------------------------------------------------------------ registration
reg("block/dragon_egg", dragon_egg)
reg("block/cake_top", cake_top)
reg("block/cake_side", cake_side)
reg("block/cake_inner", cake_inner)
reg("block/cake_bottom", cake_bottom)
reg("block/turtle_egg", turtle_egg)
reg("block/turtle_egg_slightly_cracked", bind(turtle_egg, 1))
reg("block/turtle_egg_very_cracked", bind(turtle_egg, 3))
for _ci, _cn in enumerate(("not_cracked", "slightly_cracked", "very_cracked")):
    for _f in ("top", "bottom", "north", "south", "east", "west"):
        reg(f"block/sniffer_egg_{_cn}_{_f}", bind(sniffer_egg, _ci, _f))
for _s in range(4):
    for _f in ("top", "bottom", "north", "south", "east", "west"):
        reg(f"block/dried_ghast_hydration_{_s}_{_f}", bind(ghast_face, _s, _f))
    reg(f"block/dried_ghast_hydration_{_s}_tentacles", bind(ghast_tentacles, _s))
_ = math
