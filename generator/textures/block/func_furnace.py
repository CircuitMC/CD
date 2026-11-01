"""Stone machines: furnace, smoker, blast furnace, dispenser, dropper,
observer, piston and crafter."""
import math

import numpy as np

from ...engine import IRON, Tex, pal
from ...materials import planks
from .func_common import (DARK_IRON, DARK_WOOD, FIRE, IRON_P, MSTONE, OAK, REDSTONE, REDSTONE_OFF,
                          SMOOTH, M, bevel, bind, cast_shadow, flame_field, glyph, metal_surface,
                          paint, rectm, reg, ring, rivet, stone_surface, surface, tone)

DSTONE = pal("26262b", "303036", "3a3a41", "45454c", "505058", "5c5c64", "6a6a72")  # observer / crafter


# ------------------------------------------------------------------ shared bodies
def framed(ctx, t, p, x0=0, y0=0, x1=None, y1=None, w=1):
    """Lit top/left, dark bottom/right border."""
    x1 = ctx.w if x1 is None else x1
    y1 = ctx.h if y1 is None else y1
    top = rectm(ctx, x0, y0, x1, y0 + w) | rectm(ctx, x0, y0, x0 + w, y1)
    bot = (rectm(ctx, x0, y1 - w, x1, y1) | rectm(ctx, x1 - w, y0, x1, y1)) & ~top
    paint(t, top, ctx.palette(p[-3:], ctx.texel_noise("frt")), h=0.62)
    paint(t, bot, ctx.palette(p[:2], ctx.texel_noise("frb")), h=0.3)
    return t


def stone_body(ctx, salt="body"):
    t = stone_surface(ctx.sub("block/furnace_body"), MSTONE, salt=salt)
    framed(ctx, t, MSTONE)
    return t


def smooth_top(ctx, p=SMOOTH, salt="top"):
    t = surface(ctx.sub("block/furnace_top"), p, salt=salt, cell=8, contrast=0.7, lo=0.25, hi=0.8, smooth=0.3)
    framed(ctx, t, p)
    return t


def fire_in(ctx, t, x0, y0, x1, y1, salt="", p=FIRE, tongues=3, glow=1.0, height=1.0):
    box = rectm(ctx, x0, y0, x1, y1)
    f = ctx.zeros()
    w = (x1 - x0) / tongues
    rng = ctx.rng(f"fire{salt}")
    ph = ctx.frame / max(1, ctx.frames)
    for i in range(tongues):
        cx = x0 + w * (i + 0.5) + rng.uniform(-0.4, 0.4)
        k = rng.random()
        hgt = (y1 - y0) * height * rng.uniform(0.65, 1.0) * (0.8 + 0.2 * math.sin(2 * math.pi * (ph + k)))
        f = np.maximum(f, flame_field(ctx, cx, y1, hgt, w * 1.5, salt=f"{salt}{i}",
                                      frame=ctx.frame, frames=ctx.frames))
    n = ctx.noise(2, 2, 0.5, salt=f"fn{salt}{ctx.frame}")
    f = np.clip(f * (0.75 + n * 0.5), 0, 1)
    embers = box & rectm(ctx, x0, y1 - 1, x1, y1)
    lit = box & ((f > 0.15) | embers)
    v = np.where(embers & (f < 0.3), 0.35 + n * 0.3, f)
    paint(t, lit, ctx.palette(p, v), h=0.3, smooth=0.0, f0=0.02)
    t.emissive[lit] = (0.55 + 0.45 * v[lit]) * glow
    # warm glow on the dark interior around the fire
    near = box & ~lit
    t.color[near] = np.clip(t.color[near] + np.array([0.14, 0.05, 0.0]) * glow, 0, 1)
    return t


def mouth(ctx, t, x0, y0, x1, y1, depth=0.12):
    """Dark recessed opening with a lip."""
    hole = rectm(ctx, x0, y0, x1, y1)
    g = ctx.texel_noise("mouth")
    paint(t, hole, ctx.palette(pal("0b0b0d", "141416", "1c1c20"), g * 0.6 + (ctx.y - y0) / (y1 - y0) * 0.4),
          h=depth, smooth=0.05)
    # inner shadow from the lintel
    tone(t, hole & rectm(ctx, x0, y0, x1, y0 + 1), 0.6)
    lip_t = ring(ctx, x0 - 1, y0 - 1, x1 + 1, y1 + 1) & rectm(ctx, x0 - 1, y0 - 1, x1 + 1, y0)
    lip_b = rectm(ctx, x0 - 1, y1, x1 + 1, y1 + 1)
    tone(t, lip_t, 0.75)
    tone(t, lip_b, 1.22)
    return hole


# ------------------------------------------------------------------ furnace
def furnace_side(ctx):
    t = stone_body(ctx)
    band = rectm(ctx, 1, 3, 15, 4)
    tone(t, band, 0.72)
    tone(t, rectm(ctx, 1, 4, 15, 5), 1.12)
    return t


def furnace_front(ctx, on=False):
    t = furnace_side(ctx)
    # lintel block above the mouth
    lin = rectm(ctx, 3, 5, 13, 7)
    paint(t, lin, ctx.palette(SMOOTH[1:4], ctx.texel_noise("lin")), h=0.62)
    bevel(ctx, t, lin)
    hole = mouth(ctx, t, 3, 8, 13, 14)
    # grate bars
    for x in (5, 8, 10):
        bar = rectm(ctx, x, 8, x + 1, 14) if not on else rectm(ctx, x, 8, x + 1, 9)
        paint(t, bar & hole, IRON_P[1], h=0.3, metal=IRON)
    if on:
        fire_in(ctx, t, 3, 8, 13, 14, salt="furnace")
        glow = rectm(ctx, 2, 7, 14, 15) & ~hole
        t.color[glow] = np.clip(t.color[glow] * np.array([1.18, 1.0, 0.85]), 0, 1)
    else:
        ash = hole & rectm(ctx, 3, 13, 13, 14)
        paint(t, ash, ctx.palette(pal("242322", "33302d", "45403a"), ctx.texel_noise("ash")))
    return t


def furnace_top(ctx):
    t = smooth_top(ctx)
    vent = rectm(ctx, 5, 5, 11, 11)
    bevel(ctx, t, vent, raised=False)
    for y in (6, 8):
        paint(t, rectm(ctx, 6, y + 0.0, 10, y + 1), SMOOTH[0], h=0.2)
    return t


# ------------------------------------------------------------------ smoker
SMOKE_IRON = pal("1c1b1d", "262528", "312f33", "3d3b40", "4a484e", "59575d")


def smoker_hood(ctx, t):
    hood = rectm(ctx, 0, 0, 16, 7)
    m = metal_surface(ctx.sub("block/smoker_hood"), SMOKE_IRON, salt="hood", lo=0.3, hi=0.8)
    paint(t, hood, m.color, h=0.6, metal=IRON, smooth=0.45)
    tone(t, rectm(ctx, 0, 0, 16, 1), 1.25)
    tone(t, rectm(ctx, 0, 6, 16, 7), 0.6)
    for x in (2.5, 13.5):
        rivet(ctx, t, x, 3.5, IRON_P)
    return t


def smoker_side(ctx):
    t = stone_body(ctx, salt="smk")
    smoker_hood(ctx, t)
    # wooden slats across the middle
    slats = rectm(ctx, 1, 8, 15, 10)
    paint(t, slats, ctx.palette(DARK_WOOD[1:], ctx.noise(1, 1, salt="sl", stretch=(5, 1))), h=0.6)
    bevel(ctx, t, slats)
    return t


def smoker_front(ctx, on=False):
    t = smoker_side(ctx)
    hole = mouth(ctx, t, 4, 11, 12, 15)
    for x in (6, 9):
        paint(t, rectm(ctx, x, 11, x + 1, 15) & hole, IRON_P[1], h=0.3, metal=IRON)
    vent = rectm(ctx, 4, 2, 12, 5)
    for x in range(4, 12, 2):
        paint(t, rectm(ctx, x, 2, x + 1, 5), SMOKE_IRON[0], h=0.3)
    _ = vent
    if on:
        fire_in(ctx, t, 4, 11, 12, 15, salt="smoker", tongues=3, height=0.9)
        for x in (6, 9):
            paint(t, rectm(ctx, x, 11, x + 1, 12), IRON_P[1])
        glow = rectm(ctx, 4, 2, 12, 5) & ~M(np.isin(ctx.tx, [4, 6, 8, 10]))
        n = 0.5 + 0.5 * math.sin(ctx.frame / max(1, ctx.frames) * 2 * math.pi)
        paint(t, glow, ctx.palette(FIRE[1:4], ctx.texel_noise("sg") * 0.5 + n * 0.5), emissive=0.4)
    return t


def smoker_top(ctx):
    t = metal_surface(ctx.sub("block/smoker_top"), SMOKE_IRON, salt="st", lo=0.3, hi=0.85, brushed=False)
    framed(ctx, t, SMOKE_IRON)
    chim = rectm(ctx, 4, 4, 12, 12)
    bevel(ctx, t, chim, lit=1.3)
    hole = rectm(ctx, 6, 6, 10, 10)
    paint(t, hole, pal("0c0b0c")[0], h=0.05)
    tone(t, rectm(ctx, 6, 6, 10, 7), 0.6)
    for cx, cy in ((2, 2), (13, 2), (2, 13), (13, 13)):
        rivet(ctx, t, cx + 0.5, cy + 0.5, IRON_P)
    return t


def smoker_bottom(ctx):
    t = stone_body(ctx, salt="smb")
    tone(t, ring(ctx, 3, 3, 13, 13), 0.85)
    return t


# ------------------------------------------------------------------ blast furnace
BF_IRON = pal("3a3b40", "4b4c52", "5e5f66", "72737a", "88898f", "a2a3a8", "c0c1c5")


def bf_side(ctx):
    t = surface(ctx.sub("block/blast_furnace_side"), SMOOTH, salt="bfs", cell=8, lo=0.15, hi=0.75, smooth=0.3)
    plate_t = rectm(ctx, 0, 0, 16, 3)
    plate_b = rectm(ctx, 0, 13, 16, 16)
    m = metal_surface(ctx.sub("block/bf_plate"), BF_IRON, salt="bf")
    for p in (plate_t, plate_b):
        paint(t, p, m.color, h=0.62, metal=IRON, smooth=0.55)
        bevel(ctx, t, p)
    for x in (2.5, 8.5, 13.5):
        rivet(ctx, t, x, 1.5, BF_IRON)
        rivet(ctx, t, x, 14.5, BF_IRON)
    # stone courses
    tone(t, rectm(ctx, 0, 8, 16, 9), 0.75)
    tone(t, rectm(ctx, 7, 3, 8, 8) | rectm(ctx, 11, 9, 12, 13) | rectm(ctx, 3, 9, 4, 13), 0.78)
    return t


def bf_front(ctx, on=False):
    t = bf_side(ctx)
    hole = mouth(ctx, t, 3, 5, 13, 12)
    if on:
        g = ctx.noise(3, 2, 0.5, salt=f"bfg{ctx.frame}")
        v = 0.45 + g * 0.4 + (ctx.y - 5) / 7 * 0.25
        paint(t, hole, ctx.palette(FIRE[1:6], v), emissive=0.6 + g * 0.3, h=0.2)
    for y in (6, 8, 10):
        bar = rectm(ctx, 3, y, 13, y + 1)
        paint(t, bar, ctx.palette(BF_IRON[1:4], ctx.texel_noise("bar")), h=0.45, metal=IRON, emissive=0.0)
        tone(t, rectm(ctx, 3, y + 1, 13, y + 1.0 + 1) & hole & ~M(np.isin(ctx.ty, [6, 8, 10])), 0.9)
    return t


def bf_top(ctx):
    t = metal_surface(ctx.sub("block/blast_furnace_top"), BF_IRON, salt="bft", brushed=False)
    framed(ctx, t, BF_IRON)
    for gx in range(3):
        for gy in range(3):
            x0, y0 = 2 + gx * 4.5, 2 + gy * 4.5
            h = rectm(ctx, round(x0), round(y0), round(x0) + 3, round(y0) + 3)
            paint(t, h, pal("141417")[0], h=0.1)
            tone(t, h & rectm(ctx, 0, round(y0), 16, round(y0) + 1), 0.6)
    return t


# ------------------------------------------------------------------ dispenser / dropper
def disp_face(ctx, vertical, kind):
    t = smooth_top(ctx) if vertical else furnace_side(ctx.sub("block/furnace_side"))
    if kind == "dispenser":
        r = 4.0
        rim = M(ctx.circle(8, 8, r + 1.2)) if not ctx.pixel_art else glyph(ctx, [
            "..####..", ".######.", "########", "########", "########", "########", ".######.", "..####.."], 4, 4)
        hole = M(ctx.circle(8, 8, r - 0.6)) if not ctx.pixel_art else glyph(ctx, [
            ".##.", "####", "####", ".##."], 6, 6)
        paint(t, rim, ctx.palette(SMOOTH[1:5], ctx.texel_noise("rim")), h=0.65)
        bevel(ctx, t, rim)
        paint(t, hole, pal("0d0d0f")[0], h=0.05)
        tone(t, hole & rectm(ctx, 0, 6, 16, 7), 1.0)
        tone(t, hole & rectm(ctx, 0, 9, 16, 10), 1.6)
    else:
        box = rectm(ctx, 4, 4, 12, 12)
        paint(t, box, ctx.palette(SMOOTH[1:5], ctx.texel_noise("rim")), h=0.65)
        bevel(ctx, t, box)
        hole = rectm(ctx, 6, 7, 10, 9)
        paint(t, hole, pal("0d0d0f")[0], h=0.05)
        paint(t, rectm(ctx, 6, 9, 10, 10), SMOOTH[0], h=0.3)
        paint(t, rectm(ctx, 7, 6, 9, 7), SMOOTH[0], h=0.3)
    return t


# ------------------------------------------------------------------ observer
def dark_body(ctx, salt="ob"):
    t = surface(ctx.sub("block/observer_body"), DSTONE, salt=salt, cell=5, lo=0.25, hi=0.75, smooth=0.25)
    framed(ctx, t, DSTONE)
    return t


def observer_front(ctx):
    t = dark_body(ctx)
    face = rectm(ctx, 2, 3, 14, 13)
    bevel(ctx, t, face, raised=False)
    for x0 in (3, 9):
        eye = rectm(ctx, x0, 5, x0 + 4, 8)
        paint(t, eye, pal("101012")[0], h=0.1)
        paint(t, rectm(ctx, x0 + 1, 6, x0 + 3, 7), pal("4b4f58")[0], h=0.2)
        tone(t, rectm(ctx, x0, 8, x0 + 4, 9), 1.25)
    for x in range(4, 13, 2):
        paint(t, rectm(ctx, x, 10, x + 1, 12), pal("121214")[0], h=0.1)
    return t


def observer_back(ctx, on=False):
    t = dark_body(ctx, "obb")
    plate = rectm(ctx, 4, 4, 12, 12)
    paint(t, plate, ctx.palette(DSTONE[3:], ctx.texel_noise("pl")), h=0.6)
    bevel(ctx, t, plate)
    port = rectm(ctx, 6, 6, 10, 10)
    if on:
        paint(t, port, ctx.palette(REDSTONE[3:], 0.3 + 0.7 * ctx.texel_noise("pt")), h=0.55, emissive=0.9)
        paint(t, rectm(ctx, 7, 7, 8, 8), REDSTONE[-1])
    else:
        paint(t, port, ctx.palette(REDSTONE_OFF[1:4], ctx.texel_noise("pt")), h=0.4)
    tone(t, ring(ctx, 5, 5, 11, 11) & ~port, 0.6)
    return t


def observer_side(ctx):
    t = dark_body(ctx, "obs")
    shaft = rectm(ctx, 2, 7, 14, 9)
    paint(t, shaft, ctx.palette(IRON_P[2:5], ctx.texel_noise("sh")), h=0.6, metal=IRON)
    bevel(ctx, t, shaft)
    paint(t, rectm(ctx, 6, 7, 10, 9), REDSTONE_OFF[3], h=0.6, metal=0)
    return t


def observer_top(ctx):
    t = dark_body(ctx, "obt")
    arrow = glyph(ctx, ["...##...", "..####..", ".######.", "...##...", "...##...", "...##...",
                        "...##..."], 4, 3)
    paint(t, arrow, ctx.palette(IRON_P[3:6], ctx.texel_noise("ar")), h=0.65, metal=IRON, smooth=0.5)
    bevel(ctx, t, arrow, width=1)
    cast_shadow(ctx, t, arrow, 0.75)
    return t


# ------------------------------------------------------------------ piston
def head_wood(ctx, salt="ph"):
    return planks(ctx.sub("block/piston_head_wood"), OAK, boards=4, salt=salt, knots=0)


def piston_side(ctx):
    t = stone_surface(ctx.sub("block/piston_body"), MSTONE, salt="ps")
    framed(ctx, t, MSTONE, y0=4)
    wood = head_wood(ctx)
    head = rectm(ctx, 0, 0, 16, 4)
    paint(t, head, wood.color, h=wood.height)
    tone(t, rectm(ctx, 0, 0, 16, 1), 1.12)
    paint(t, rectm(ctx, 0, 3, 16, 4), OAK[0], h=0.25)
    band = rectm(ctx, 0, 9, 16, 11)
    paint(t, band, ctx.palette(IRON_P[2:6], ctx.noise(1, 1, salt="pb", stretch=(6, 1))), h=0.65, metal=IRON,
          smooth=0.55)
    bevel(ctx, t, band)
    for x in (3.5, 12.5):
        rivet(ctx, t, x, 9.5, IRON_P)
    return t


def piston_top(ctx, sticky=False):
    t = head_wood(ctx)
    framed(ctx, t, OAK)
    boss = M(ctx.circle(8, 8, 3.6)) if not ctx.pixel_art else glyph(ctx, [
        ".####.", "######", "######", "######", "######", ".####."], 5, 5)
    paint(t, boss, ctx.palette(IRON_P[2:6], ctx.texel_noise("boss") * 0.5 + 0.25), h=0.7, metal=IRON, smooth=0.6)
    bevel(ctx, t, boss)
    cast_shadow(ctx, t, boss)
    for cx, cy in ((2.5, 2.5), (13.5, 2.5), (2.5, 13.5), (13.5, 13.5)):
        rivet(ctx, t, cx, cy, IRON_P)
    if sticky:
        n = ctx.noise(4, 2, 0.5, salt="slime")
        d = np.hypot(ctx.x - 8, ctx.y - 7.5) + (n - 0.5) * 3
        drip = M(np.isin(ctx.tx, [4, 9, 12])) & (ctx.y < 12.5 + (ctx.tx % 3)) & (ctx.y > 8)
        sl = ((d < 5.8) | drip) & rectm(ctx, 1, 1, 15, 15)
        sl = ctx.organic(sl, 0.2, "sl")
        SL = pal("3d7a2a", "54a03a", "6cbf4c", "8ad968", "b3ef94")
        v = 0.55 + (n - 0.5) * 0.5 - (ctx.y - 7.5) / 20
        paint(t, sl, ctx.palette(SL, v), h=0.8, smooth=0.75, sss=0.5, metal=0)
        t.metal[sl] = 0
        bevel(ctx, t, sl, lit=1.15)
        paint(t, sl & glyph(ctx, ["#.", ".#"], 5, 4), SL[-1])
    return t


def piston_bottom(ctx):
    t = stone_body(ctx, salt="pbt")
    plate = rectm(ctx, 3, 3, 13, 13)
    paint(t, plate, ctx.palette(IRON_P[2:5], ctx.texel_noise("pp")), h=0.62, metal=IRON, smooth=0.5)
    bevel(ctx, t, plate)
    hole = rectm(ctx, 6, 6, 10, 10)
    paint(t, hole, pal("141416")[0], h=0.1, metal=0)
    t.metal[hole] = 0
    tone(t, rectm(ctx, 6, 6, 10, 7), 0.6)
    return t


def piston_inner(ctx):
    t = stone_body(ctx, salt="pin")
    tone(t, ring(ctx, 1, 1, 15, 15, 1), 0.85)
    hole = rectm(ctx, 5, 5, 11, 11)
    paint(t, hole, ctx.palette(IRON_P[1:4], ctx.texel_noise("ph")), h=0.35, metal=IRON)
    bevel(ctx, t, hole, raised=False)
    core = rectm(ctx, 6, 6, 10, 10)
    paint(t, core, pal("101012")[0], h=0.05)
    t.metal[core] = 0
    return t


# ------------------------------------------------------------------ crafter
def crafter_body(ctx, salt="cb"):
    t = surface(ctx.sub("block/crafter_body"), DSTONE, salt=salt, cell=5, lo=0.35, hi=0.85, smooth=0.25)
    framed(ctx, t, DSTONE)
    # iron corner brackets
    for x0, y0 in ((0, 0), (13, 0), (0, 13), (13, 13)):
        c = rectm(ctx, x0, y0, x0 + 3, y0 + 3)
        paint(t, c, ctx.palette(IRON_P[2:5], ctx.texel_noise("cr")), h=0.68, metal=IRON, smooth=0.5)
        bevel(ctx, t, c)
    return t


def crafter_top(ctx, state=""):
    t = crafter_body(ctx, "ct")
    grid = rectm(ctx, 1, 1, 15, 15)
    paint(t, grid, ctx.palette(IRON_P[1:4], ctx.texel_noise("gr")), h=0.6, metal=IRON, smooth=0.45)
    rng = ctx.rng("cells")
    for gx in range(3):
        for gy in range(3):
            x0, y0 = 1 + gx * 5, 1 + gy * 5
            cell = rectm(ctx, x0 + (gx > 0), y0 + (gy > 0), x0 + 4 + (gx > 0), y0 + 4 + (gy > 0))
            g = ctx.texel_noise("cg")
            if state == "crafting":
                paint(t, cell, ctx.palette(pal("5a3c12", "8a5c1c", "c48a2c", "f0c060"), 0.3 + g * 0.5),
                      h=0.25, emissive=0.35, metal=0)
            elif state == "triggered" and rng.random() < 0.55:
                paint(t, cell, ctx.palette(REDSTONE[2:6], 0.2 + g * 0.6), h=0.25, emissive=0.5, metal=0)
            else:
                paint(t, cell, ctx.palette(pal("141416", "1d1d21", "26262b"), g), h=0.2, metal=0)
                if state == "triggered":
                    rng.random()
            t.metal[cell] = 0
            tone(t, cell & rectm(ctx, 0, y0 + (gy > 0), 16, y0 + 1 + (gy > 0)), 0.7)
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16) & ~rectm(ctx, 1, 1, 15, 15))
    return t


def crafter_north(ctx, state=""):
    t = crafter_body(ctx, "cn")
    hole = mouth(ctx, t, 4, 6, 12, 11)
    if state == "crafting":
        g = ctx.texel_noise("ng")
        paint(t, hole, ctx.palette(pal("4a3010", "8a5c1c", "d09838", "ffe08a"), 0.2 + g * 0.4 + (ctx.y - 6) / 10),
              emissive=0.5)
    paint(t, rectm(ctx, 3, 12, 13, 13), IRON_P[3], h=0.6, metal=IRON)
    return t


def crafter_south(ctx, state=""):
    t = crafter_body(ctx, "cs")
    sock = rectm(ctx, 5, 5, 11, 11)
    paint(t, sock, ctx.palette(IRON_P[1:4], ctx.texel_noise("so")), h=0.4, metal=IRON)
    bevel(ctx, t, sock, raised=False)
    pins = rectm(ctx, 7, 6, 9, 10)
    on = state == "triggered"
    paint(t, pins, ctx.palette((REDSTONE[3:] if on else REDSTONE_OFF[1:]), ctx.texel_noise("pn")), h=0.5,
          emissive=0.85 if on else 0.0, metal=0)
    t.metal[pins] = 0
    return t


def crafter_side(ctx, state="", mirror=False):
    t = crafter_body(ctx, "cw" if mirror else "ce")
    slot = rectm(ctx, 3, 6, 13, 10)
    paint(t, slot, pal("17171a")[0], h=0.15)
    tone(t, rectm(ctx, 3, 6, 13, 7), 0.7)
    arm_len = 9 if state == "crafting" else 5
    x0 = 3 if not mirror else 13 - arm_len
    arm = rectm(ctx, x0, 7, x0 + arm_len, 9)
    paint(t, arm, ctx.palette(IRON_P[2:6], ctx.texel_noise("arm")), h=0.6, metal=IRON)
    bevel(ctx, t, arm)
    lamp = rectm(ctx, 7, 12, 9, 14)
    on = state == "triggered"
    paint(t, lamp, REDSTONE[5] if on else REDSTONE_OFF[2], h=0.6, emissive=0.9 if on else 0, metal=0)
    t.metal[lamp] = 0
    bevel(ctx, t, lamp)
    if state == "crafting":
        paint(t, rectm(ctx, 7, 12, 9, 14), pal("e6a33a")[0], emissive=0.6)
    return t


def crafter_bottom(ctx):
    t = crafter_body(ctx, "cbt")
    tone(t, ring(ctx, 4, 4, 12, 12), 0.8)
    return t


# ------------------------------------------------------------------ registration
reg("block/furnace_side", furnace_side)
reg("block/furnace_front", furnace_front)
reg("block/furnace_front_on", bind(furnace_front, on=True))
reg("block/furnace_top", furnace_top)
reg("block/smoker_side", smoker_side)
reg("block/smoker_front", smoker_front)
reg("block/smoker_front_on", bind(smoker_front, on=True))
reg("block/smoker_top", smoker_top)
reg("block/smoker_bottom", smoker_bottom)
reg("block/blast_furnace_side", bf_side)
reg("block/blast_furnace_front", bf_front)
reg("block/blast_furnace_front_on", bind(bf_front, on=True))
reg("block/blast_furnace_top", bf_top)
reg("block/dispenser_front", bind(disp_face, False, "dispenser"))
reg("block/dispenser_front_vertical", bind(disp_face, True, "dispenser"))
reg("block/dropper_front", bind(disp_face, False, "dropper"))
reg("block/dropper_front_vertical", bind(disp_face, True, "dropper"))
reg("block/observer_front", observer_front)
reg("block/observer_back", observer_back)
reg("block/observer_back_on", bind(observer_back, on=True))
reg("block/observer_side", observer_side)
reg("block/observer_top", observer_top)
reg("block/piston_side", piston_side)
reg("block/piston_top", piston_top)
reg("block/piston_top_sticky", bind(piston_top, sticky=True))
reg("block/piston_bottom", piston_bottom)
reg("block/piston_inner", piston_inner)
reg("block/crafter_top", crafter_top)
reg("block/crafter_top_crafting", bind(crafter_top, "crafting"))
reg("block/crafter_top_triggered", bind(crafter_top, "triggered"))
reg("block/crafter_north", crafter_north)
reg("block/crafter_north_crafting", bind(crafter_north, "crafting"))
reg("block/crafter_south", crafter_south)
reg("block/crafter_south_triggered", bind(crafter_south, "triggered"))
reg("block/crafter_east", crafter_side)
reg("block/crafter_east_crafting", bind(crafter_side, "crafting"))
reg("block/crafter_east_triggered", bind(crafter_side, "triggered"))
reg("block/crafter_west", bind(crafter_side, mirror=True))
reg("block/crafter_west_crafting", bind(crafter_side, "crafting", mirror=True))
reg("block/crafter_west_triggered", bind(crafter_side, "triggered", mirror=True))
reg("block/crafter_bottom", crafter_bottom)
_ = (Tex, DARK_IRON)
