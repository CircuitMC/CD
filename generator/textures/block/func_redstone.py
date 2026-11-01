"""Redstone components: dust, rails, repeater, comparator, lever, tripwire,
daylight detector, target, lamp, redstone block and torches."""
import math

import numpy as np

from ...engine import GOLD, IRON, Tex, pal
from ...materials import planks
from .func_common import (DARK_IRON, DARK_WOOD, FIRE, GOLD_P, GREEN_FIRE, IRON_P, OAK, REDSTONE,
                          REDSTONE_OFF, SMOOTH, SOUL_FIRE, M, bevel, bind, blank, cast_shadow, glyph,
                          paint, rectm, reg, ring, surface, texel_set, tone)

TIE = pal("3e2a17", "533a21", "684a2b", "7a5935", "8a673e")
RAIL_IRON = pal("3a3a40", "5a5a62", "84848c", "a8a8b0", "cdcdd3")


# ------------------------------------------------------------------ dust (grayscale, tinted)
def dust_field(ctx):
    """Shared brightness field so the dot and both lines match where they overlap."""
    g = ctx.sub("block/redstone_dust").texel_noise("dust")
    return 0.8 + ctx.quantize(g, 3) * 0.16


def dust_tex(ctx, m):
    t = blank(ctx)
    v = dust_field(ctx)
    paint(t, m, np.repeat(v[..., None], 3, -1), h=0.6, alpha=1, smooth=0.35)
    return t


def dust_dot(ctx):
    # round 4x4 blob centred on the block, overlapping the 2-texel lines
    if ctx.pixel_art:
        m = glyph(ctx, [".##.", "####", "####", ".##."], 6, 6)
    else:
        m = M(ctx.circle(8, 8, 2.15)) | M(ctx.rect(7, 6, 9, 10)) | M(ctx.rect(6, 7, 10, 9))
    return dust_tex(ctx, m)


def dust_line(ctx, vertical=True):
    a = ctx.x if vertical else ctx.y
    return dust_tex(ctx, (a >= 7) & (a < 9))


def dust_overlay(ctx):
    t = blank(ctx)
    sp = texel_set(ctx, [(7, 7), (8, 8)])
    paint(t, sp, pal("ffd2c8")[0], h=0.7, alpha=1, smooth=0.6)
    return t


# ------------------------------------------------------------------ rails
# One design for every rail: bars at x [2,4) and [12,14) (outer column lit,
# inner column shaded), 2-texel sleepers every 4 texels, lit on their upper /
# counter-clockwise half.  rail_corner bends the same track around the
# bottom-right corner, so it meets the straight pieces without a step.
RAIL_BARS = ((2, 4), (12, 14))
SLEEPER_ROWS = (1, 5, 9, 13)


def paint_ties(ctx, t, tie, tie_dark):
    g = ctx.sub("block/rail").texel_noise("tie")
    paint(t, tie, ctx.palette(TIE[1:], 0.2 + g * 0.6), h=0.45, alpha=1, porosity=0.2)
    tone(t, tie & tie_dark, 0.78)
    return t


def paint_track(ctx, t, tie, tie_dark, bars, rp=RAIL_IRON, metal=IRON, ties=True):
    """tie / tie_dark: sleeper masks; bars: list of (lit_half, dark_half) masks."""
    if ties:
        paint_ties(ctx, t, tie, tie_dark)
    for lit, dark in bars:
        paint(t, lit, rp[3], h=0.8, alpha=1, metal=metal, smooth=0.7)
        paint(t, dark, rp[1], h=0.75, alpha=1, metal=metal, smooth=0.6)
        paint(t, dark & tie & tie_dark, rp[0])  # spike heads
        if not ctx.pixel_art:
            paint(t, lit & (ctx.sub("block/rail").texel_noise("sheen") > 0.7), rp[4])
    return t


def straight_track(ctx, t, kind="rail"):
    tie = np.zeros((ctx.H, ctx.W), bool)
    for y0 in SLEEPER_ROWS:
        tie |= rectm(ctx, 1, y0, 15, y0 + 2)
    tie_dark = M(np.isin(ctx.ty, [y + 1 for y in SLEEPER_ROWS]))
    bars = [(rectm(ctx, a, 0, a + 1, 16), rectm(ctx, a + 1, 0, b, 16)) for a, b in RAIL_BARS]
    gold = kind == "powered"
    return tie, tie_dark, bars, (GOLD_P if gold else RAIL_IRON), (GOLD if gold else IRON)


def rail_base(ctx, kind="rail", on=False):
    t = blank(ctx)
    tie, tie_dark, bars, rp, metal = straight_track(ctx, t, kind)
    paint_ties(ctx, t, tie, tie_dark)
    if kind == "powered":
        paint(t, rectm(ctx, 7, 0, 9, 16), (REDSTONE[4] if on else REDSTONE_OFF[2]), h=0.55, alpha=1,
              emissive=0.8 if on else 0)
        paint(t, rectm(ctx, 7, 0, 8, 16), (REDSTONE[5] if on else REDSTONE_OFF[3]))
    elif kind == "detector":
        plate = rectm(ctx, 5, 4, 11, 12)
        paint(t, plate, ctx.palette(SMOOTH[1:5], ctx.texel_noise("pl")), h=0.65, alpha=1)
        bevel(ctx, t, plate)
        dot = rectm(ctx, 7, 7, 9, 9)
        paint(t, dot, REDSTONE[5] if on else REDSTONE_OFF[3], emissive=0.8 if on else 0)
    elif kind == "activator":
        strip = rectm(ctx, 7, 0, 9, 16)
        paint(t, strip, ctx.palette(RAIL_IRON[1:3], ctx.texel_noise("as")), h=0.5, alpha=1, metal=IRON)
        for y0 in (3, 7, 11, 15):
            nub = rectm(ctx, 7, y0, 9, y0 + 1)
            paint(t, nub, REDSTONE[5] if on else REDSTONE_OFF[3], h=0.6, emissive=0.8 if on else 0, metal=0)
    return paint_track(ctx, t, tie, tie_dark, bars, rp, metal, ties=False)


def rail_corner(ctx):
    """Curve joining the south (bottom) and east (right) edges."""
    t = blank(ctx)
    d = np.hypot(16 - ctx.x, 16 - ctx.y)
    ang = np.arctan2(16 - ctx.y, 16 - ctx.x)  # 0 = toward west, pi/2 = toward north
    tie = np.zeros((ctx.H, ctx.W), bool)
    tie_dark = np.zeros_like(tie)
    for k in range(4):
        a0 = (k + 0.5) / 4 * (math.pi / 2)
        off = np.sin(ang - a0) * d          # signed distance from the sleeper's centre line
        band = (np.abs(off) < 1.0) & (np.cos(ang - a0) > 0) & (d >= 1.0) & (d < 15.0)
        tie |= band
        tie_dark |= band & (off < 0)        # clockwise half is the shaded one
    bars = []
    for a, b in RAIL_BARS:                  # straight bar [a,b) -> radii (16-b, 16-a]
        r_in, r_out = 16 - b, 16 - a
        mid = (r_in + r_out) / 2
        bars.append(((d > mid) & (d <= r_out), (d > r_in) & (d <= mid)))
    return paint_track(ctx, t, tie, tie_dark, bars)

# ------------------------------------------------------------------ repeater / comparator
def slab_top(ctx, salt="slab"):
    t = surface(ctx.sub("block/redstone_slab"), SMOOTH, salt=salt, cell=8, lo=0.3, hi=0.8, smooth=0.3)
    top = rectm(ctx, 0, 0, 16, 1) | rectm(ctx, 0, 0, 1, 16)
    bot = (rectm(ctx, 0, 15, 16, 16) | rectm(ctx, 15, 0, 16, 16)) & ~top
    paint(t, top, SMOOTH[-1], h=0.6)
    paint(t, bot, SMOOTH[0], h=0.35)
    return t


def groove(ctx, t, mask, on):
    p = REDSTONE if on else REDSTONE_OFF
    g = ctx.texel_noise("groove")
    paint(t, mask, ctx.palette(p[2:] if on else p[1:], 0.25 + g * 0.6), h=0.35,
          emissive=(0.55 + g * 0.3) if on else 0.0, smooth=0.4)
    edge = M(ctx.edge(mask, 1, "tl"))
    tone(t, edge, 0.8)
    return t


def repeater(ctx, on=False):
    t = slab_top(ctx, "rep")
    groove(ctx, t, rectm(ctx, 7, 1, 9, 15), on)
    # torch sockets and the delay rail
    for y0 in (2, 6):
        s = rectm(ctx, 6, y0, 10, y0 + 3)
        bevel(ctx, t, s, raised=False, dh=0.05)
    rail = rectm(ctx, 3, 9, 13, 10)
    paint(t, rail, SMOOTH[1], h=0.4)
    for x in (3, 12):
        paint(t, rectm(ctx, x, 9, x + 1, 10), SMOOTH[0])
    tri = glyph(ctx, ["#.#", ".#."], 7, 12) if False else glyph(ctx, ["####", ".##."], 6, 12)
    groove(ctx, t, tri, on)
    return t


def comparator(ctx, on=False):
    t = slab_top(ctx, "cmp")
    m = (M(ctx.segment(4.5, 12.5, 8, 4, 1.4)) | M(ctx.segment(11.5, 12.5, 8, 4, 1.4)) |
         rectm(ctx, 4, 12, 12, 14))
    if ctx.pixel_art:
        m = glyph(ctx, [
            "....##....",
            "....##....",
            "...#..#...",
            "...#..#...",
            "..#....#..",
            "..#....#..",
            ".#......#.",
            ".#......#.",
            "##########",
            "##########"], 3, 4)
    groove(ctx, t, m, on)
    for cx, cy in ((4, 11), (11, 11), (7, 2)):
        s = rectm(ctx, cx, cy, cx + 2, cy + 2)
        bevel(ctx, t, s, raised=False, dh=0.05)
    return t


# ------------------------------------------------------------------ torches, lever, hook
def stick(ctx, t, x0, y0, y1, p=OAK):
    paint(t, rectm(ctx, x0, y0, x0 + 1, y1), p[4], h=0.7, alpha=1, porosity=0.2)
    paint(t, rectm(ctx, x0 + 1, y0, x0 + 2, y1), p[2], h=0.65, alpha=1, porosity=0.2)
    paint(t, texel_set(ctx, [(x0, y0 + 3), (x0 + 1, y0 + 6)]), p[1])
    return t


def torch(ctx, flame=FIRE, kind="fire"):
    t = blank(ctx)
    stick(ctx, t, 7, 8, 16)
    head = rectm(ctx, 7, 6, 9, 8)
    if kind == "redstone_on" or kind == "redstone_off":
        on = kind == "redstone_on"
        p = REDSTONE if on else REDSTONE_OFF
        paint(t, head, p[4] if on else p[3], h=0.85, alpha=1, emissive=1.0 if on else 0)
        paint(t, texel_set(ctx, [(7, 6)]), p[-1] if on else p[-1])
        paint(t, rectm(ctx, 7, 5, 9, 6), p[3] if on else p[2], h=0.8, alpha=1, emissive=0.8 if on else 0)
        if on:
            halo = texel_set(ctx, [(6, 5), (9, 6), (6, 7), (9, 4), (8, 4)])
            paint(t, halo, REDSTONE[5], h=0.6, alpha=1, emissive=0.7)
        return t
    # flame head: ember cup + tongue
    paint(t, head, flame[3], h=0.85, alpha=1, emissive=1.0)
    paint(t, texel_set(ctx, [(7, 6)]), flame[5], emissive=1.0)
    paint(t, texel_set(ctx, [(8, 7)]), flame[2], emissive=0.9)
    tip = texel_set(ctx, [(7, 5), (8, 5), (8, 4)])
    paint(t, tip, flame[4], h=0.8, alpha=1, emissive=1.0)
    paint(t, texel_set(ctx, [(7, 5)]), flame[6] if len(flame) > 6 else flame[5])
    # sooty wrap just below the head
    paint(t, rectm(ctx, 7, 8, 9, 9), pal("3a2a1c")[0])
    return t


def lever(ctx):
    t = blank(ctx)
    stick(ctx, t, 7, 8, 16)
    knob = rectm(ctx, 7, 6, 9, 8)
    paint(t, knob, IRON_P[4], h=0.8, alpha=1, metal=IRON, smooth=0.6)
    paint(t, texel_set(ctx, [(8, 7)]), IRON_P[2])
    paint(t, texel_set(ctx, [(7, 6)]), IRON_P[6])
    return t


def tripwire_hook(ctx):
    t = blank(ctx)
    stick(ctx, t, 7, 9, 16)
    d = np.hypot(ctx.x - 8, ctx.y - 4.5)
    loop = (d < 3.2) & (d >= 1.9) if not ctx.pixel_art else glyph(ctx, [
        ".##.", "#..#", "#..#", "#..#", ".##."], 6, 2)
    loop = M(loop)
    paint(t, loop, IRON_P[4], h=0.8, alpha=1, metal=IRON, smooth=0.6)
    paint(t, loop & (ctx.x > 8) & (ctx.y > 4.5), IRON_P[2])
    paint(t, rectm(ctx, 7, 7, 9, 9), IRON_P[3], h=0.75, alpha=1, metal=IRON)
    return t


def tripwire(ctx):
    """Every row identical (models sample different 2-texel strips); period 4 along x."""
    STR = pal("8e8e94", "b4b4ba", "d6d6dc", "ececf0")
    idx = np.array([3, 2, 1, 2], np.int32)[ctx.tx % 4]
    t = Tex(ctx, STR[idx], alpha=1.0, height=0.6, smooth=0.2, wrap=False, grain=0)
    return t


# ------------------------------------------------------------------ daylight detector, target, lamp
def daylight_top(ctx, inverted=False):
    w = planks(ctx.sub("block/daylight_frame"), OAK, boards=4, knots=0)
    t = w
    glass = pal("2b3f55", "3c5a78", "4f7698", "6a96b8", "9cc3dc") if not inverted else \
        pal("1b1530", "28204a", "372e66", "4a3f84", "6a5ca8")
    for gx in range(3):
        cell = rectm(ctx, 1 + gx * 5, 1, 5 + gx * 5, 15) if gx < 2 else rectm(ctx, 11, 1, 15, 15)
        n = ctx.noise(4, 2, 0.5, salt=f"dl{gx}")
        v = 0.25 + n * 0.35 + np.clip(1 - (ctx.y - 1) / 14, 0, 1) * 0.25
        paint(t, cell, ctx.palette(glass, v), h=0.4, smooth=0.9, f0=0.04, porosity=0)
        tone(t, cell & rectm(ctx, 0, 1, 16, 2), 0.7)
        for y in (5, 10):
            paint(t, cell & rectm(ctx, 0, y, 16, y + 1), glass[0])
        sp = cell & texel_set(ctx, [(2 + gx * 5, 3), (3 + gx * 5, 2), (2 + gx * 5, 7)])
        paint(t, sp, glass[-1])
    tone(t, rectm(ctx, 0, 0, 16, 1) | rectm(ctx, 0, 0, 1, 16), 1.15)
    tone(t, rectm(ctx, 0, 15, 16, 16) | rectm(ctx, 15, 0, 16, 16), 0.75)
    return t


def daylight_side(ctx):
    t = planks(ctx.sub("block/daylight_frame"), OAK, boards=4, knots=0)
    trim = rectm(ctx, 0, 10, 16, 11)
    paint(t, trim, OAK[5], h=0.6)
    paint(t, rectm(ctx, 0, 15, 16, 16), OAK[0], h=0.3)
    return t


STRAW = pal("a4936a", "bcab7f", "cfbf93", "ddcfa6", "e8dcb8", "f1e9cf")
TARGET_RED = pal("6e1010", "8f1717", "b0201d", "c93128")


def target(ctx, top=False):
    n = ctx.noise(2, 2, 0.5, salt="straw", stretch=(1, 3) if not top else (3, 1))
    g = ctx.texel_noise("straw")
    t = Tex(ctx, ctx.palette(STRAW, n * 0.5 + g * 0.5), height=0.45 + n * 0.2, smooth=0.1, porosity=0.6)
    d = np.maximum(np.abs(ctx.x - 8), np.abs(ctx.y - 8)) * 0.4 + np.hypot(ctx.x - 8, ctx.y - 8) * 0.6
    ring_m = (d >= 4.4) & (d < 6.3)
    bull = d < 2.2
    rv = ctx.palette(TARGET_RED, n * 0.6 + g * 0.4)
    paint(t, ring_m | bull, rv, h=0.5)
    tone(t, M(ctx.edge(ring_m | bull, 1, "br")), 0.8)
    return t


LAMP_FRAME = pal("3a2b1d", "4c3826", "5e4630", "6f553b", "806446")
LAMP_OFF = pal("2e2016", "3f2c1d", "533b26", "684b31", "7a5a3c")
LAMP_ON = pal("b0601a", "d88a2a", "f2b648", "ffd877", "fff0b8", "fffbe8")


def redstone_lamp(ctx, on=False):
    n = ctx.noise(3, 2, 0.5, salt="lamp")
    vo = ctx.voronoi(9, "lampcell", min_dist=3.6)
    border = vo["f2"] - vo["f1"]
    cellv = np.clip(1 - vo["f1"] / 3.2, 0, 1)
    if on:
        v = 0.25 + cellv * 0.6 + (n - 0.5) * 0.2
        col = ctx.palette(LAMP_ON, v)
        t = Tex(ctx, col, height=0.5 + cellv * 0.1, smooth=0.75, emissive=0.6 + cellv * 0.4, f0=0.04)
        crack = border < 0.6
        paint(t, crack, LAMP_ON[0], h=0.35, emissive=0.35)
    else:
        v = 0.2 + cellv * 0.55 + (n - 0.5) * 0.2
        t = Tex(ctx, ctx.palette(LAMP_OFF, v), height=0.5 + cellv * 0.1, smooth=0.55)
        crack = border < 0.6
        paint(t, crack, LAMP_OFF[0], h=0.35)
    fr = ring(ctx, 0, 0, 16, 16, 2)
    paint(t, fr, ctx.palette(LAMP_FRAME, ctx.texel_noise("lf") * 0.6 + 0.2), h=0.7, emissive=0.0, smooth=0.3)
    tone(t, rectm(ctx, 0, 0, 16, 1) | rectm(ctx, 0, 0, 1, 16), 1.25)
    tone(t, (rectm(ctx, 0, 15, 16, 16) | rectm(ctx, 15, 0, 16, 16)), 0.7)
    inner_edge = ring(ctx, 2, 2, 14, 14, 1)
    tone(t, inner_edge & (rectm(ctx, 2, 2, 14, 3) | rectm(ctx, 2, 2, 3, 14)), 0.7 if not on else 0.85)
    for cx, cy in ((0, 0), (14, 0), (0, 14), (14, 14)):
        c = rectm(ctx, cx, cy, cx + 2, cy + 2)
        paint(t, c, REDSTONE[3] if on else REDSTONE_OFF[3], emissive=0.5 if on else 0)
        paint(t, c & texel_set(ctx, [(cx, cy)]), REDSTONE[5] if on else REDSTONE_OFF[4])
    return t


def redstone_block(ctx):
    n = ctx.noise(6, 2, 0.5, salt="rb")
    g = ctx.texel_noise("rb")
    t = Tex(ctx, ctx.palette(REDSTONE[1:5], n * 0.5 + g * 0.5), height=0.5 + n * 0.1, smooth=0.55, f0=0.05)
    # crystalline facets
    vo = ctx.voronoi(8, "rbf", min_dist=4)
    facet = np.clip(-(vo["dx"] * 0.6 + vo["dy"]) / 4 + 0.5, 0, 1)
    t.color = ctx.palette(REDSTONE[2:6], facet * 0.65 + n * 0.25 + g * 0.1)
    edges = (vo["f2"] - vo["f1"]) < 0.5
    paint(t, edges, REDSTONE[1], h=0.35)
    fr = ring(ctx, 0, 0, 16, 16, 1)
    paint(t, fr & (rectm(ctx, 0, 0, 16, 1) | rectm(ctx, 0, 0, 1, 16)), REDSTONE[5], h=0.65)
    paint(t, fr & ~(rectm(ctx, 0, 0, 16, 1) | rectm(ctx, 0, 0, 1, 16)), REDSTONE[0], h=0.3)
    sp = (ctx.texel_noise("rbs", soft=False) > 0.97) & ~fr
    paint(t, sp, REDSTONE[6], emissive=0.3)
    t.emissive = np.maximum(t.emissive, np.where(facet > 0.8, 0.12, 0))
    return t


# ------------------------------------------------------------------ registration
reg("block/redstone_dust_dot", dust_dot)
reg("block/redstone_dust_line0", bind(dust_line, True))
reg("block/redstone_dust_line1", bind(dust_line, False))
reg("block/redstone_dust_overlay", dust_overlay)
reg("block/rail", rail_base)
reg("block/rail_corner", rail_corner)
reg("block/powered_rail", bind(rail_base, "powered"))
reg("block/powered_rail_on", bind(rail_base, "powered", True))
reg("block/detector_rail", bind(rail_base, "detector"))
reg("block/detector_rail_on", bind(rail_base, "detector", True))
reg("block/activator_rail", bind(rail_base, "activator"))
reg("block/activator_rail_on", bind(rail_base, "activator", True))
reg("block/repeater", repeater)
reg("block/repeater_on", bind(repeater, True))
reg("block/comparator", comparator)
reg("block/comparator_on", bind(comparator, True))
reg("block/torch", torch)
reg("block/soul_torch", bind(torch, SOUL_FIRE))
reg("block/copper_torch", bind(torch, GREEN_FIRE))
reg("block/redstone_torch", bind(torch, kind="redstone_on"))
reg("block/redstone_torch_off", bind(torch, kind="redstone_off"))
reg("block/lever", lever)
reg("block/tripwire_hook", tripwire_hook)
reg("block/tripwire", tripwire)
reg("block/daylight_detector_top", daylight_top)
reg("block/daylight_detector_inverted_top", bind(daylight_top, True))
reg("block/daylight_detector_side", daylight_side)
reg("block/target_side", target)
reg("block/target_top", bind(target, top=True))
reg("block/redstone_lamp", redstone_lamp)
reg("block/redstone_lamp_on", bind(redstone_lamp, True))
reg("block/redstone_block", redstone_block)
_ = (DARK_IRON, cast_shadow)
