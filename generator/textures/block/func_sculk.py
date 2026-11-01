"""Sculk family: sensor (and calibrated), shrieker, catalyst, vein."""
import math

import numpy as np

from ...engine import Tex, pal
from .func_common import (BONE, SCULK, SCULK_GLOW, M, bevel, bind, blank, glyph, paint, rectm, reg, ring,
                          texel_set, tone)

AMETHYST = pal("3e2470", "5a3598", "7c50c0", "a27ae0", "cfb0ff")


def sculk_ground(ctx, salt="sg", glow=0.6):
    n = ctx.noise(4, 3, 0.55, salt=f"sk{salt}")
    g = ctx.texel_noise(f"sk{salt}")
    v = n * 0.6 + g * 0.4
    t = Tex(ctx, ctx.palette(SCULK, v), height=0.45 + n * 0.2, smooth=0.35, sss=0.2, f0=0.03)
    # soul specks
    sp = (g > 0.93) & (n > 0.5)
    paint(t, sp, SCULK_GLOW[0], emissive=0.3 * glow)
    hot = (ctx.texel_noise(f"hot{salt}", soft=False) > 0.985) & (n > 0.4)
    paint(t, hot, SCULK_GLOW[3], emissive=0.8 * glow)
    return t


def bone_surface(ctx, salt="bn"):
    n = ctx.noise(4, 2, 0.5, salt=f"bn{salt}", stretch=(3, 1))
    g = ctx.texel_noise(f"bn{salt}")
    return Tex(ctx, ctx.palette(BONE, n * 0.55 + g * 0.45), height=0.5 + n * 0.15, smooth=0.3, porosity=0.2)


# ------------------------------------------------------------------ sensor
def sensor_side(ctx, calibrated=False):
    t = sculk_ground(ctx.sub("block/sculk_sensor_body"), "ss")
    rim = rectm(ctx, 0, 8, 16, 10)
    b = bone_surface(ctx, "rim")
    paint(t, rim, b.color, h=0.7, emissive=0, sss=0)
    tone(t, rectm(ctx, 0, 9, 16, 10), 0.8)
    tone(t, rectm(ctx, 0, 10, 16, 11), 0.7)
    if calibrated:
        port = rectm(ctx, 5, 11, 11, 15)
        paint(t, port, ctx.palette(AMETHYST, 0.3 + ctx.texel_noise("pt") * 0.5), h=0.6, emissive=0.3, smooth=0.8)
        bevel(ctx, t, port)
        paint(t, rectm(ctx, 7, 12, 9, 14), AMETHYST[4], emissive=0.7)
    return t


def sensor_top(ctx, calibrated=False):
    t = sculk_ground(ctx.sub("block/sculk_sensor_top"), "st")
    rim = ring(ctx, 0, 0, 16, 16, 2)
    b = bone_surface(ctx, "trim")
    paint(t, rim, b.color, h=0.7, emissive=0)
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16))
    bevel(ctx, t, rectm(ctx, 2, 2, 14, 14), raised=False)
    if calibrated:
        for cx, cy in ((3, 3), (11, 3), (3, 11), (11, 11)):
            gem = rectm(ctx, cx, cy, cx + 2, cy + 2)
            paint(t, gem, AMETHYST[3], h=0.75, smooth=0.85, emissive=0.3)
            paint(t, texel_set(ctx, [(cx, cy)]), AMETHYST[4])
    vein = glyph(ctx, ["..#..", ".###.", "#####", ".###.", "..#.."], 6, 6)
    paint(t, vein, SCULK_GLOW[2], emissive=0.6)
    return t


def sensor_bottom(ctx):
    return sculk_ground(ctx.sub("block/sculk_sensor_bottom"), "sb", glow=0.3)


def tendril(ctx, active=False):
    t = blank(ctx)
    ph = ctx.frame / max(1, ctx.frames)
    m = np.zeros((ctx.H, ctx.W), bool)
    along = ctx.zeros()
    for side, x0 in ((0, 4.5), (1, 11.5)):
        for k in range(10):
            yy = 16 - k
            curl = math.sin(k / 9 * math.pi * 0.9) * (1.5 if side == 0 else -1.5)
            cx = x0 + curl
            w = 2.2 - k * 0.12
            seg = M(ctx.rect(round(cx - w / 2), yy - 1, round(cx - w / 2) + max(1, round(w)), yy))
            m |= seg
            along[seg] = k / 9
        tip = (round(x0 + (1.0 if side == 0 else -1.0)), 6)
        m |= texel_set(ctx, [tip])
        along[texel_set(ctx, [tip])] = 1.0
    wave = 0.5 + 0.5 * np.sin((along - ph * (2 if active else 1)) * 2 * math.pi)
    base = 0.35 if not active else 0.55
    v = np.clip(base + wave * (0.35 if not active else 0.45), 0, 1)
    col = ctx.palette(SCULK_GLOW if active else np.concatenate([SCULK[3:], SCULK_GLOW[:3]]), v)
    paint(t, m, col, h=0.7, alpha=1, emissive=(0.25 + wave * 0.55) if active else wave * 0.3, sss=0.3)
    edge = M(ctx.edge(m, 1, "br")) & m
    tone(t, edge, 0.75)
    return t


def amethyst_sprite(ctx):
    t = blank(ctx)
    shards = [((8, 15), (7.5, 3), 2.6), ((4.5, 15), (2.5, 8), 1.8), ((11.5, 15), (13.5, 7), 1.9)]
    for (bx, by), (tx, ty), w in shards:
        m = M(ctx.polygon([(bx - w, by + 1), (tx - 0.6, ty), (tx + 0.6, ty - 0.6), (bx + w, by + 1)]))
        lit = ctx.x < (bx + tx) / 2 + (ctx.y - by) * (tx - bx) / max(1e-3, ty - by) * 0 + 0.0
        v = np.where(lit, 0.75, 0.4) + ctx.texel_noise("am") * 0.15
        paint(t, m, ctx.palette(AMETHYST, v), h=0.7, alpha=1, smooth=0.85, f0=0.06, emissive=0.15)
        paint(t, M(ctx.edge(m, 1, "br")) & m, AMETHYST[1])
    return t


# ------------------------------------------------------------------ shrieker
def shrieker_side(ctx):
    t = sculk_ground(ctx.sub("block/shrieker_body"), "shs")
    b = bone_surface(ctx, "shs")
    band = rectm(ctx, 0, 8, 16, 11)
    paint(t, band, b.color, h=0.7, emissive=0)
    for x in range(1, 16, 3):
        tooth = rectm(ctx, x, 11, x + 2, 12 + (x % 2))
        paint(t, tooth, BONE[3], h=0.65, emissive=0)
    tone(t, rectm(ctx, 0, 8, 16, 9), 1.1)
    tone(t, rectm(ctx, 0, 10, 16, 11), 0.8)
    paint(t, rectm(ctx, 0, 0, 16, 8), b.color)
    return t


def shrieker_top(ctx):
    t = bone_surface(ctx.sub("block/shrieker_top"), "sht")
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16))
    hole = rectm(ctx, 3, 3, 13, 13)
    paint(t, hole, SCULK[0], h=0.1)
    for x in range(4, 13, 3):
        paint(t, rectm(ctx, x, 3, x + 1, 5) | rectm(ctx, x + 1, 11, x + 2, 13), BONE[2], h=0.6)
    tone(t, ring(ctx, 2, 2, 14, 14), 0.8)
    return t


def shrieker_inner(ctx, summon=False):
    ph = ctx.frame / max(1, ctx.frames) * 2 * math.pi
    dx, dy = ctx.x - 8, ctx.y - 8
    r = np.hypot(dx, dy)
    a = np.arctan2(dy, dx)
    sw = 0.5 + 0.5 * np.sin(a * 2 - r * 0.9 + ph)
    n = ctx.noise(3, 2, 0.5, salt="shi")
    k = 1.0 if summon else 0.6
    v = np.clip((sw * 0.5 + n * 0.3) * k + np.clip(1 - r / 7, 0, 1) * 0.35, 0, 1)
    P = np.concatenate([SCULK[:3], SCULK_GLOW])
    return Tex(ctx, ctx.palette(P, v), height=0.4 + v * 0.1, smooth=0.6, emissive=np.clip(v - 0.25, 0, 1) * k)


def shrieker_bottom(ctx):
    return sculk_ground(ctx.sub("block/shrieker_bottom"), "shb", glow=0.3)


# ------------------------------------------------------------------ catalyst
def catalyst_side(ctx):
    t = bone_surface(ctx.sub("block/catalyst_side"), "cs")
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16))
    # sculk creeping down from the top
    depth = 4 + ctx.lattice_noise(3, 16, "creep") * 5
    creep = ctx.y < depth
    sk = sculk_ground(ctx.sub("block/sculk_creep"), "cr")
    paint(t, creep, sk.color, h=0.55, emissive=sk.emissive)
    tone(t, M(ctx.edge(creep, 1, "br")) & creep, 0.7)
    # glowing soul eyes in the bone
    for cx, cy in ((4, 11), (11, 12)):
        e = rectm(ctx, cx, cy, cx + 2, cy + 2)
        paint(t, e, SCULK_GLOW[3], emissive=0.8, h=0.4)
        tone(t, ring(ctx, cx - 1, cy - 1, cx + 3, cy + 3), 0.75)
    return t


def catalyst_top(ctx):
    t = sculk_ground(ctx.sub("block/catalyst_top"), "ct")
    b = bone_surface(ctx, "ctb")
    d = np.maximum(np.abs(ctx.x - 7.5), np.abs(ctx.y - 7.5))
    plate = (d < 5)
    paint(t, plate, b.color, h=0.7, emissive=0)
    bevel(ctx, t, plate)
    eye = d < 2
    paint(t, eye, ctx.palette(SCULK_GLOW, 0.4 + ctx.texel_noise("ey") * 0.5), emissive=0.9, h=0.4)
    tone(t, (d >= 2) & (d < 3), 0.75)
    return t


def catalyst_bottom(ctx):
    t = bone_surface(ctx.sub("block/catalyst_bottom"), "cb")
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16))
    tone(t, ring(ctx, 3, 3, 13, 13), 0.8)
    return t


# ------------------------------------------------------------------ vein
def sculk_vein(ctx):
    t = blank(ctx)
    ph = ctx.frame / max(1, ctx.frames)
    rng = ctx.rng("veins")
    m = np.zeros((ctx.H, ctx.W), bool)
    nodes = []
    for _ in range(7):
        x, y = float(rng.integers(0, 16)), float(rng.integers(0, 16))
        for _ in range(int(rng.integers(4, 8))):
            nx = x + rng.choice([-2, -1, 0, 1, 2])
            ny = y + rng.choice([-2, -1, 1, 2])
            m |= M(ctx.segment(x + 0.5, y + 0.5, nx + 0.5, ny + 0.5, 1.0))
            x, y = nx % 16, ny % 16
        nodes.append((int(x), int(y)))
    paint(t, m, ctx.palette(SCULK[2:], ctx.texel_noise("vn")), h=0.6, alpha=1, sss=0.2)
    for i, (x, y) in enumerate(nodes):
        b = 0.5 + 0.5 * math.cos(2 * math.pi * (ph + i / 7))
        dot = texel_set(ctx, [(x, y)])
        paint(t, dot, ctx.palette(SCULK_GLOW, 0.3 + b * 0.6), alpha=1, emissive=0.3 + b * 0.6, h=0.7)
    return t


# ------------------------------------------------------------------ registration
reg("block/sculk_sensor_side", sensor_side)
reg("block/sculk_sensor_top", sensor_top)
reg("block/sculk_sensor_bottom", sensor_bottom)
reg("block/sculk_sensor_tendril_inactive", tendril)
reg("block/sculk_sensor_tendril_active", bind(tendril, True))
reg("block/calibrated_sculk_sensor_top", bind(sensor_top, True))
reg("block/calibrated_sculk_sensor_input_side", bind(sensor_side, True))
reg("block/calibrated_sculk_sensor_amethyst", amethyst_sprite)
reg("block/sculk_shrieker_side", shrieker_side)
reg("block/sculk_shrieker_top", shrieker_top)
reg("block/sculk_shrieker_bottom", shrieker_bottom)
reg("block/sculk_shrieker_inner_top", shrieker_inner)
reg("block/sculk_shrieker_can_summon_inner_top", bind(shrieker_inner, True))
reg("block/sculk_catalyst_side", catalyst_side)
reg("block/sculk_catalyst_top", catalyst_top)
reg("block/sculk_catalyst_bottom", catalyst_bottom)
reg("block/sculk_vein", sculk_vein)
