"""Metal light & hardware: copper bulbs, lanterns, chains, bars, lightning
rods, end rod and sea lantern (with all copper oxidation stages)."""
import math

import numpy as np

from ...engine import IRON, Tex, pal
from .func_common import (COPPER_PREFIXES, COPPER_STAGES, DARK_IRON, FIRE, GREEN_FIRE, IRON_P, REDSTONE,
                          SOUL_FIRE, M, bevel, bind, blank, copper_metal, glyph, paint, rectm, reg, ring,
                          texel_set, tone)

GLOW_BY_STAGE = {"": 1.0, "exposed_": 0.8, "weathered_": 0.55, "oxidized_": 0.3}


def patina(ctx, stage, salt=""):
    """0..1 noise field and a mask where the next oxidation stage shows through."""
    n = ctx.noise(4, 3, 0.55, salt=f"pat{salt}") * 0.8 + ctx.texel_noise(f"pat{salt}") * 0.2
    thr = {"": 2.0, "exposed_": 0.72, "weathered_": 0.62, "oxidized_": 2.0}[stage]
    return n, n > thr


NEXT = {"": "exposed_", "exposed_": "weathered_", "weathered_": "oxidized_", "oxidized_": "oxidized_"}


def copper_paint(ctx, t, mask, stage, v, salt="", h=None):
    """Paint copper (with patina flecks of the next stage) where mask, palette value v (0..1)."""
    p = COPPER_STAGES[stage]
    m = M(mask)
    _, spots = patina(ctx, stage, salt)
    col = np.where(spots[..., None], ctx.palette(COPPER_STAGES[NEXT[stage]], v), ctx.palette(p, v))
    met = copper_metal(stage)
    paint(t, m, col, h=h, alpha=1, metal=met, smooth=0.55 if met else 0.25, f0=0.04)
    paint(t, m & spots, None, metal=copper_metal(NEXT[stage]), smooth=0.25)
    return t


def metal_paint(ctx, t, mask, stage, v, salt="", h=None):
    if stage is None:
        paint(t, mask, ctx.palette(IRON_P, v), h=h, alpha=1, metal=IRON, smooth=0.6)
        return t
    return copper_paint(ctx, t, mask, stage, v, salt, h)


# ------------------------------------------------------------------ copper bulb
def copper_bulb(ctx, stage="", lit=False, powered=False):
    p = COPPER_STAGES[stage]
    n = ctx.noise(6, 2, 0.5, salt="cb")
    t = Tex(ctx, ctx.palette(p, 0.5), height=0.6)
    frame = ring(ctx, 0, 0, 16, 16, 3)
    copper_paint(ctx, t, frame, stage, 0.35 + n * 0.35, "cb", h=0.65)
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16), lit=1.2, dark=0.7)
    bevel(ctx, t, rectm(ctx, 3, 3, 13, 13), raised=False, lit=1.2, dark=0.65)
    # corner bolts
    for cx, cy in ((1, 1), (14, 1), (1, 14), (14, 14)):
        b = rectm(ctx, cx, cy, cx + 1, cy + 1)
        paint(t, b, p[5])
    # glass window with the bulb
    win = rectm(ctx, 3, 3, 13, 13)
    d = np.hypot(ctx.x - 8, ctx.y - 8)
    k = GLOW_BY_STAGE[stage]
    if lit:
        LIT = pal("9a4d14", "d47a22", "f4ac3e", "ffd57a", "fff0bf", "fffcef")
        v = np.clip(1.05 - d / 6.5, 0, 1) * (0.55 + 0.45 * k) + 0.1
        paint(t, win, ctx.palette(LIT, v), h=0.45, smooth=0.85, emissive=np.clip(0.35 + v * 0.65, 0, 1) * k,
              metal=0, alpha=1)
    else:
        DARKG = pal("1e1612", "2a1f19", "3a2b22", "4d3a2c", "5e4a3a")
        v = np.clip(0.8 - d / 9, 0, 1) * 0.7 + ctx.texel_noise("gl") * 0.15
        paint(t, win, ctx.palette(DARKG, v), h=0.45, smooth=0.85, metal=0, alpha=1)
    # filament coil
    coil = glyph(ctx, ["#.#.#.#", ".#.#.#."], 5, 7) | rectm(ctx, 5, 9, 6, 12) | rectm(ctx, 11, 9, 12, 12)
    coil = M(coil)
    if lit:
        paint(t, coil, pal("fffdf2")[0], emissive=1.0 * k + 0.0)
    else:
        paint(t, coil, p[2])
    # glints
    paint(t, texel_set(ctx, [(4, 4), (5, 4), (4, 5)]), pal("fff6e0")[0] if lit else pal("8a7464")[0])
    # powered indicator: small redstone lights in the top/bottom frame
    for cx in (7, 8):
        for cy in (1, 14):
            ind = rectm(ctx, cx, cy, cx + 1, cy + 1)
            if powered:
                paint(t, ind, REDSTONE[5], emissive=0.9, metal=0, h=0.6)
            else:
                paint(t, ind, p[1], h=0.55)
    return t


# ------------------------------------------------------------------ chain
def chain(ctx, stage=None):
    t = blank(ctx)
    pv = 0.5
    for strip, off in ((0, 0), (3, 4)):
        for k in range(-1, 3):
            y0 = off + k * 8
            ringm = (rectm(ctx, strip, y0 + 1, strip + 1, y0 + 6) | rectm(ctx, strip + 2, y0 + 1, strip + 3, y0 + 6) |
                     rectm(ctx, strip + 1, y0, strip + 2, y0 + 1) | rectm(ctx, strip + 1, y0 + 6, strip + 2, y0 + 7))
            edge_link = rectm(ctx, strip + 1, y0 + 6, strip + 2, y0 + 9)
            m = (ringm | edge_link) & rectm(ctx, 0, 0, 16, 16)
            v = ctx.full(pv) + (ctx.tx == strip) * 0.35 - (ctx.tx == strip + 2) * 0.25 - \
                ((ctx.ty - y0) % 8 >= 6) * 0.15
            metal_paint(ctx, t, m, stage, np.clip(v, 0, 1), "ch", h=0.7)
    return t


# ------------------------------------------------------------------ bars
def bars(ctx, stage=None):
    t = blank(ctx)
    vb = rectm(ctx, 7, 0, 9, 16) | rectm(ctx, 0, 0, 1, 16) | rectm(ctx, 15, 0, 16, 16) | \
        rectm(ctx, 3, 0, 4, 16) | rectm(ctx, 12, 0, 13, 16)
    hb = rectm(ctx, 0, 1, 16, 2) | rectm(ctx, 0, 14, 16, 15)
    v = 0.45 + (ctx.tx == 7) * 0.3 - (ctx.tx == 8) * 0.1 + (ctx.tx == 0) * 0.25 + (ctx.tx == 3) * 0.15 \
        - (ctx.tx == 12) * 0.05
    v = v + ctx.texel_noise("bar") * 0.1
    metal_paint(ctx, t, vb, stage, np.clip(v, 0, 1), "bars", h=0.7)
    vh = 0.55 + (ctx.ty == 1) * 0.15 - (ctx.ty == 14) * 0.1 + ctx.texel_noise("hb") * 0.1
    metal_paint(ctx, t, hb, stage, np.clip(vh, 0, 1), "bars", h=0.75)
    # rivets where bars cross
    cross = vb & hb
    tone(t, cross, 1.2)
    return t


# ------------------------------------------------------------------ lightning rod / end rod
def lightning_rod(ctx, stage="", on=False):
    t = blank(ctx)
    rod = rectm(ctx, 0, 4, 2, 16)
    tip = rectm(ctx, 0, 0, 4, 4)
    v = 0.45 + (ctx.tx == 0) * 0.3 - (ctx.tx == 1) * 0.05 + ctx.texel_noise("lr") * 0.12
    copper_paint(ctx, t, rod, stage, np.clip(v, 0, 1), "lr", h=0.7)
    vt = 0.5 + (ctx.tx == 0) * 0.2 + (ctx.ty == 0) * 0.25 - (ctx.tx == 3) * 0.2 - (ctx.ty == 3) * 0.2
    copper_paint(ctx, t, tip, stage, np.clip(vt + ctx.texel_noise("lt") * 0.1, 0, 1), "lr", h=0.8)
    if on:
        ZAP = pal("8fb4ff", "c4d8ff", "eef4ff", "ffffff")
        paint(t, rod | tip, ctx.palette(ZAP, np.clip(v * 1.1, 0, 1)), emissive=1.0, metal=0)
    return t


def end_rod(ctx):
    t = blank(ctx)
    ROD = pal("b9b0c4", "d8d2df", "eeeaf2", "fbfaff")
    BASE = pal("4f3a5c", "6a4f7a", "856795", "a083ae")
    rod = rectm(ctx, 0, 0, 2, 15)
    v = 0.5 + (ctx.tx == 0) * 0.35 - (ctx.ty >= 13) * 0.2
    paint(t, rod, ctx.palette(ROD, np.clip(v, 0, 1)), h=0.75, alpha=1, emissive=0.9, smooth=0.8)
    top = rectm(ctx, 2, 2, 6, 6)
    paint(t, top, ctx.palette(BASE, 0.4 + ctx.texel_noise("eb") * 0.3), h=0.65, alpha=1, smooth=0.5)
    bevel(ctx, t, top)
    paint(t, rectm(ctx, 3, 3, 5, 5), BASE[0])
    side = rectm(ctx, 2, 6, 6, 7)
    paint(t, side, BASE[1], h=0.6, alpha=1)
    return t


# ------------------------------------------------------------------ lanterns
def lantern(ctx, stage=None, flame=FIRE):
    """Layout: cap side (1..5,0..2), body side (0..6,2..9), top/bottom (0..6,9..15),
    handle links (11..14,1..5) and (11..14,10..14)."""
    t = blank(ctx)
    fr = ctx.frame / max(1, ctx.frames)
    # body frame
    body = rectm(ctx, 0, 2, 6, 9)
    frame = body & ~rectm(ctx, 1, 3, 5, 8)
    v = 0.45 + (ctx.tx == 0) * 0.25 + (ctx.ty == 2) * 0.2 - (ctx.tx == 5) * 0.2 - (ctx.ty == 8) * 0.2
    metal_paint(ctx, t, frame, stage, np.clip(v, 0, 1), "lb", h=0.75)
    # glass + flame
    win = rectm(ctx, 1, 3, 5, 8)
    flick = 0.5 + 0.5 * math.sin(fr * 2 * math.pi)
    d = np.hypot((ctx.x - 3) * 1.2, ctx.y - (6.2 - flick * 0.4))
    fv = np.clip(1.15 - d / 2.6, 0, 1)
    col = ctx.palette(flame[1:], fv)
    paint(t, win, col, h=0.5, alpha=1, emissive=0.45 + fv * 0.55, metal=0, smooth=0.8)
    core = texel_set(ctx, [(2, 6), (3, 6), (2 + (ctx.frame % 2), 5)])
    paint(t, core, flame[-1], emissive=1.0)
    # cap side
    cap = rectm(ctx, 1, 0, 5, 2)
    vc = 0.5 + (ctx.ty == 0) * 0.25 - (ctx.tx == 4) * 0.2
    metal_paint(ctx, t, cap, stage, np.clip(vc, 0, 1), "lc", h=0.8)
    # top / bottom plate (0..6, 9..15) with cap top in the middle
    plate = rectm(ctx, 0, 9, 6, 15)
    vp = 0.45 + (ctx.tx == 0) * 0.2 + (ctx.ty == 9) * 0.2 - (ctx.tx == 5) * 0.2 - (ctx.ty == 14) * 0.2
    metal_paint(ctx, t, plate, stage, np.clip(vp + ctx.texel_noise("lp") * 0.1, 0, 1), "lp", h=0.7)
    ctop = rectm(ctx, 1, 10, 5, 14)
    tone(t, ring(ctx, 1, 10, 5, 14) & ctop, 0.8)
    tone(t, rectm(ctx, 2, 11, 4, 13), 1.15)
    # handle links
    for y0 in (1, 10):
        link = ring(ctx, 11, y0, 14, y0 + 4)
        vl = 0.55 + (ctx.tx == 11) * 0.2 - (ctx.tx == 13) * 0.25
        metal_paint(ctx, t, link, stage, np.clip(vl, 0, 1), "lh", h=0.7)
    return t


# ------------------------------------------------------------------ sea lantern
SEA = pal("6f9a90", "8fb8ac", "acd0c4", "c9e4da", "e2f3ec", "f6fffb")


def sea_lantern(ctx):
    ph = ctx.frame / max(1, ctx.frames)
    t = Tex(ctx, ctx.palette(SEA, 0.5), height=0.55, smooth=0.8, emissive=0.6, f0=0.05)
    fr = ring(ctx, 0, 0, 16, 16, 1)
    paint(t, fr, ctx.palette(SEA[:3], ctx.texel_noise("sf") * 0.8 + 0.1), h=0.65, emissive=0.25)
    tone(t, rectm(ctx, 0, 0, 16, 1) | rectm(ctx, 0, 0, 1, 16), 1.15)
    # four glowing orbs whose brightness rotates around the block
    for i, (cx, cy) in enumerate(((4.5, 4.5), (11.5, 4.5), (11.5, 11.5), (4.5, 11.5))):
        d = np.hypot(ctx.x - cx, ctx.y - cy)
        cell = rectm(ctx, cx - 3.5, cy - 3.5, cx + 3.5, cy + 3.5) & ~fr
        b = 0.5 + 0.5 * math.cos(2 * math.pi * (ph - i / 4))
        v = np.clip(1.0 - d / 4.2, 0, 1) * (0.55 + 0.45 * b) + 0.25
        paint(t, cell, ctx.palette(SEA[1:], v), h=0.5 + v * 0.1, emissive=0.55 + v * 0.45)
        rim = cell & (d > 3.0)
        tone(t, rim, 0.9)
    # crossing seams
    seam = (rectm(ctx, 7.5, 1, 8.5, 15) | rectm(ctx, 1, 7.5, 15, 8.5))
    paint(t, seam, SEA[1], h=0.45, emissive=0.3)
    center = rectm(ctx, 7, 7, 9, 9)
    paint(t, center, SEA[-1], emissive=1.0)
    return t


# ------------------------------------------------------------------ registration
for _s in COPPER_PREFIXES:
    reg(f"block/{_s}copper_bulb", bind(copper_bulb, _s))
    reg(f"block/{_s}copper_bulb_lit", bind(copper_bulb, _s, True))
    reg(f"block/{_s}copper_bulb_powered", bind(copper_bulb, _s, False, True))
    reg(f"block/{_s}copper_bulb_lit_powered", bind(copper_bulb, _s, True, True))
    reg(f"block/{_s}copper_chain", bind(chain, _s))
    reg(f"block/{_s}copper_bars", bind(bars, _s))
    reg(f"block/{_s}copper_lantern", bind(lantern, _s, GREEN_FIRE))
    reg(f"block/{_s}lightning_rod", bind(lightning_rod, _s))
reg("block/lightning_rod_on", bind(lightning_rod, "", True))
reg("block/iron_chain", chain)
reg("block/iron_bars", bars)
reg("block/lantern", bind(lantern, None, FIRE))
reg("block/soul_lantern", bind(lantern, None, SOUL_FIRE))
reg("block/end_rod", end_rod)
reg("block/sea_lantern", sea_lantern)
_ = DARK_IRON
