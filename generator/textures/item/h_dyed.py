"""Dye-colored item families (h-z colors): bundle (+ open back/front), candle,
cushion, dye, harness."""
import numpy as np

from ...registry import register
from .common import STRING
from .h_lib import DYES, cells, compose, ellipse, metal, IRON, paint, pal, ramp, rows_mask, spr, union

COLORS = ["light_blue", "light_gray", "lime", "magenta", "orange", "pink", "purple", "red", "white", "yellow"]
TIE = pal("4a3a26", "7a6446", "a88e6a", "cdb894")
BUCKLE = pal("3a3a40", "77777f", "b4b4bc", "e2e2e8")
WICK = pal("1c1a18", "3a3430", "5a524a")


def dye_pal(color, n=5):
    base = DYES[color]
    if color == "white":
        return pal("8a9298", "b4bcc2", "d6dce0", "eef1f3", "ffffff")
    return ramp(base, n, lo=0.45, lift=0.5)


BUNDLE = [
    "................",
    "................",
    ".....######.....",
    "....########....",
    "......####......",
    ".....######.....",
    "....########....",
    "...##########...",
    "..############..",
    "..############..",
    "..############..",
    "..############..",
    "...##########...",
    "....########....",
]


def bundle(ctx, color):
    p = dye_pal(color)
    m = rows_mask(ctx, BUNDLE, round_=0.25)
    t = spr(ctx, m, p, smooth=0.2, porosity=0.4)
    ring = ctx.edge(m, 1) > 0
    # cinch folds and seam
    paint(t, (cells(ctx, [(5, 6), (10, 6), (4, 8), (11, 8), (7, 10), (8, 12)]) > 0.5) & ~ring, p[1])
    paint(t, (cells(ctx, [(5, 3), (6, 3), (4, 9), (5, 8)]) > 0.5) & ~ring, p[-1])
    tie = spr(ctx, rows_mask(ctx, ["######"], x0=5, y0=4), TIE, bevel=1)
    knot = spr(ctx, cells(ctx, [(11, 4), (11, 5), (12, 6)]), TIE, outline=False, bevel=1)
    return compose(ctx, t, tie, knot)


OPEN_BACK = [
    "................",
    "................",
    "................",
    "..############..",
    ".##############.",
    ".##############.",
    "..############..",
    "..############..",
    "..############..",
    "..############..",
    "..############..",
    "..############..",
    "...##########...",
    "....########....",
]


def bundle_open_back(ctx, color):
    p = dye_pal(color)
    m = rows_mask(ctx, OPEN_BACK, round_=0.25)
    t = spr(ctx, m, p, smooth=0.2, porosity=0.4)
    inner = rows_mask(ctx, ["############", "############", "##########"], x0=2, y0=4)
    paint(t, (inner > 0.5), p[0] * 0.7)
    paint(t, cells(ctx, [(x, 4) for x in range(3, 13)]) > 0.5, p[0] * 0.5)
    return t


OPEN_FRONT = [
    "..############..",
    ".##############.",
    "..############..",
    "..############..",
    "..############..",
    "..############..",
    "...##########...",
    "....########....",
]


def bundle_open_front(ctx, color):
    p = dye_pal(color)
    m = rows_mask(ctx, OPEN_FRONT, y0=6, round_=0.25)
    t = spr(ctx, m, p, smooth=0.2, porosity=0.4)
    ring = ctx.edge(m, 1) > 0
    paint(t, (cells(ctx, [(x, 7) for x in range(3, 13)]) > 0.5) & ~ring, p[-1])  # rolled lip
    paint(t, (cells(ctx, [(4, 10), (11, 10), (7, 12)]) > 0.5) & ~ring, p[1])
    tie = spr(ctx, rows_mask(ctx, ["##", "##"], x0=12, y0=7), TIE, bevel=1)
    return compose(ctx, t, tie)


def candle(ctx, color):
    p = dye_pal(color)
    body = rows_mask(ctx, ["####"] * 9, x0=6, y0=6)
    drip = cells(ctx, [(5, 7), (5, 8), (10, 6)])
    t = spr(ctx, union(body, drip), p, smooth=0.45, sss=0.35, bevel=1.5)
    ring = ctx.edge(union(body, drip), 1) > 0
    paint(t, (cells(ctx, [(7, 6), (8, 6)]) > 0.5) & ~ring, p[-1])
    paint(t, (cells(ctx, [(9, 9), (9, 11), (9, 13)]) > 0.5) & ~ring, p[1])
    wick = spr(ctx, cells(ctx, [(7, 4), (7, 5)]), WICK, outline=False, bevel=1)
    return compose(ctx, t, wick)


def cushion(ctx, color):
    p = dye_pal(color)
    m = rows_mask(ctx, [
        ".##..........##.",
        "################",
        ".##############.",
        ".##############.",
        ".##############.",
        ".##############.",
        ".##############.",
        ".##############.",
        "################",
        ".##..........##.",
    ], y0=3, round_=0.35)
    t = spr(ctx, m, p, smooth=0.2, porosity=0.5, sss=0.1, bevel=3)
    ring = ctx.edge(m, 1) > 0
    tuft = cells(ctx, [(7, 7), (8, 8), (4, 6), (11, 6), (4, 10), (11, 10)])
    paint(t, (tuft > 0.5) & ~ring, p[1])
    paint(t, cells(ctx, [(7, 8), (8, 7)]) > 0.5, p[2])
    paint(t, (cells(ctx, [(3, 5), (4, 5), (3, 6)]) > 0.5) & ~ring, p[-1])
    return t


def dye(ctx, color):
    """Pigment heap: a soft mound of powder with a few loose grains."""
    p = dye_pal(color)
    m = rows_mask(ctx, [
        "......###.......",
        "....#######.....",
        "...#########....",
        "..###########...",
        ".#############..",
        ".##############.",
        "..############..",
    ], y0=6, round_=0.4)
    t = spr(ctx, m, p, smooth=0.1, porosity=0.9, bevel=2.5)
    ring = ctx.edge(m, 1) > 0
    n = ctx.texel_noise("dye")
    inner = (m > 0.5) & ~ring
    t.color[inner & (n < 0.15)] = p[1]
    t.color[inner & (n > 0.9)] = p[-1]
    grains = spr(ctx, cells(ctx, [(12, 9), (13, 11), (3, 10), (11, 6)]), p[1:], outline=False, bevel=1)
    return compose(ctx, t, grains)


def harness(ctx, color):
    """Ghast harness: a padded strap frame with goggles-like buckles."""
    p = dye_pal(color)
    frame = rows_mask(ctx, [
        "..############..",
        ".##############.",
        "###..........###",
        "##............##",
        "##............##",
        "##............##",
        "###..........###",
        ".##############.",
        "..############..",
    ], y0=3, round_=0.3)
    cross = rows_mask(ctx, ["##"] * 5, x0=7, y0=5)
    m = union(frame, cross)
    t = spr(ctx, m, p, smooth=0.25, porosity=0.4)
    ring = ctx.edge(m, 1) > 0
    paint(t, (cells(ctx, [(x, 4) for x in range(3, 13, 2)] + [(x, 10) for x in range(3, 13, 2)]) > 0.5) & ~ring, p[1])
    buckles = metal(ctx, union(rows_mask(ctx, ["###", "###", "###"], x0=1, y0=6),
                               rows_mask(ctx, ["###", "###", "###"], x0=12, y0=6)), BUCKLE, IRON, bevel=1)
    paint(buckles, cells(ctx, [(2, 7), (13, 7)]) > 0.5, BUCKLE[0])
    return compose(ctx, t, buckles)


FAMILY = dict(bundle=bundle, bundle_open_back=bundle_open_back, bundle_open_front=bundle_open_front,
              candle=candle, cushion=cushion, dye=dye, harness=harness)

for _c in COLORS:
    for _k, _fn in FAMILY.items():
        register(f"item/{_c}_{_k}", lambda ctx, fn=_fn, c=_c: fn(ctx, c))
