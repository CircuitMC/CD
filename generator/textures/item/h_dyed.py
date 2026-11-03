"""Dye-colored item families (h-z colors): bundle (+ open back/front), candle,
cushion, dye, harness.

Every design has a palette-based builder (`*_with(ctx, p)`) so undyed variants
(item_1's plain bundle / candle) can share exactly the same drawing; FAMILY maps
names to color-name wrappers (kept stable: item_1 imports it).
"""
import numpy as np

from ...registry import register
from .common import STRING, WOOD
from .h_lib import (DYES, IRON, U, box, cells, circ, compose, ell, ellipse, line, metal, minus, paint, pal, ramp,
                    rgb, rows_mask, spr, stroke, union)

COLORS = ["light_blue", "light_gray", "lime", "magenta", "orange", "pink", "purple", "red", "white", "yellow"]
TIE = pal("4a3a26", "7a6446", "a88e6a", "cdb894")
BUCKLE = pal("3a3a40", "77777f", "b4b4bc", "e2e2e8")
WICK = pal("1c1a18", "3a3430", "5a524a")
SCOOP = pal("3a2410", "5e3c1c", "84572b", "a8773e", "c79a5a")


def dye_pal(color, n=5):
    base = DYES[color]
    if color == "white":
        return pal("8a9298", "b4bcc2", "d6dce0", "eef1f3", "ffffff")
    if color == "black":
        return pal("08080a", "1a1a20", "2c2c34", "42424c", "5c5c68")
    return ramp(base, n, lo=0.45, lift=0.5)


# ------------------------------------------------------------------ bundle
BUNDLE = [  # cloth sack, gathered neck at row 4 (drawstring), flared mouth above
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


def bundle_with(ctx, p):
    m = rows_mask(ctx, BUNDLE, round_=0.25)
    t = spr(ctx, m, p, smooth=0.2, porosity=0.4, bevel=3)
    ring = ctx.edge(m, 1) > 0
    inner = (m > 0.5) & ~ring
    # gathered folds radiating from the neck, light on the left bulge
    folds = U(line(ctx, [(7.0, 5.6), (5.0, 9.0)], 0.6), line(ctx, [(9.0, 5.6), (10.6, 9.4)], 0.6),
              line(ctx, [(8.0, 6.0), (8.0, 8.4)], 0.6))
    paint(t, (folds > 0.5) & inner, p[1])
    paint(t, (cells(ctx, [(4, 8), (4, 9), (5, 7), (6, 3), (7, 3)]) > 0.5) & inner, p[-1])
    paint(t, (cells(ctx, [(5, 2), (6, 2), (9, 2), (10, 2)]) > 0.5) & inner, p[1])  # ruffled mouth
    # drawstring around the neck with hanging cord ends
    tie = spr(ctx, rows_mask(ctx, ["######"], x0=5, y0=4), TIE, bevel=1)
    cord = spr(ctx, U(stroke(ctx, [(10.6, 4.6), (12.0, 6.0), (12.4, 8.0)], 0.9),
                      stroke(ctx, [(10.6, 4.6), (11.0, 6.6), (10.8, 8.4)], 0.9)), TIE, outline=False, bevel=1)
    tassel = spr(ctx, cells(ctx, [(12, 8), (10, 8)]), TIE[1:], outline=False, bevel=1)
    return compose(ctx, t, tie, cord, tassel)


OPEN_BACK = [  # opened sack: back wall + dark interior (drawn behind contents)
    "................",
    "................",
    "................",
    "..############..",
    ".##############.",
    ".##############.",
    "..############..",
    "..############..",
    ".##############.",
    ".##############.",
    ".##############.",
    ".##############.",
    "..############..",
    "...##########...",
    "....########....",
]


def bundle_open_back_with(ctx, p):
    m = rows_mask(ctx, OPEN_BACK, round_=0.25)
    t = spr(ctx, m, p, smooth=0.2, porosity=0.4, bevel=2)
    ring = ctx.edge(m, 1) > 0
    mouth = ell(ctx, 8.0, 6.0, 6.0, 2.2)
    inside = (minus(m, ell(ctx, 8.0, 3.6, 7.0, 0.9)) > 0.5) & ~ring & (box(ctx, 0, 4.0, 16, 16) > 0.5)
    paint(t, inside, p[0] * 0.75)  # dark inside of the sack
    paint(t, (mouth > 0.5) & ~ring & (box(ctx, 0, 4.0, 16, 5.0) > 0.5), p[0] * 0.4)
    paint(t, (cells(ctx, [(x, 3) for x in range(3, 13)]) > 0.5), p[-2])  # back rim
    return t


OPEN_FRONT = [  # front half of the opened sack (drawn over contents), starts at row 6
    "..############..",
    ".##############.",
    ".##############.",
    ".##############.",
    ".##############.",
    ".##############.",
    "..############..",
    "...##########...",
    "....########....",
]


def bundle_open_front_with(ctx, p):
    m = rows_mask(ctx, OPEN_FRONT, y0=6, round_=0.25)
    t = spr(ctx, m, p, smooth=0.2, porosity=0.4, bevel=2.5)
    ring = ctx.edge(m, 1) > 0
    inner = (m > 0.5) & ~ring
    paint(t, (cells(ctx, [(x, 7) for x in range(2, 14)]) > 0.5) & inner, p[-1])  # rolled lip
    paint(t, (cells(ctx, [(x, 8) for x in range(3, 13)]) > 0.5) & inner, p[1])
    paint(t, (U(line(ctx, [(5.0, 9.4), (4.4, 12.0)], 0.6), line(ctx, [(10.6, 9.4), (11.4, 12.0)], 0.6)) > 0.5)
          & inner, p[1])
    tie = spr(ctx, rows_mask(ctx, ["##", "##"], x0=12, y0=7), TIE, bevel=1)
    cord = spr(ctx, stroke(ctx, [(13.4, 8.6), (14.2, 10.6), (13.8, 12.4)], 0.9), TIE, outline=False, bevel=1)
    return compose(ctx, t, tie, cord)


# ------------------------------------------------------------------ candle
def candle_with(ctx, p):
    """Thick wax pillar (5 wide) with a melted top rim, drips and a black wick."""
    body = box(ctx, 5.0, 6.0, 10.0, 15.0)
    drip = U(box(ctx, 4.0, 6.0, 5.0, 9.0), box(ctx, 10.0, 6.0, 11.0, 7.6))
    m = union(body, drip)
    t = spr(ctx, m, p, smooth=0.45, sss=0.4, bevel=2)
    ring = ctx.edge(m, 1) > 0
    inner = (m > 0.5) & ~ring
    paint(t, (box(ctx, 5.0, 6.0, 10.0, 7.0) > 0.5) & inner, p[-1])   # lit top surface
    paint(t, (box(ctx, 6.0, 7.0, 7.0, 13.0) > 0.5) & inner, p[-2])   # sheen stripe
    paint(t, (box(ctx, 9.0, 8.0, 10.0, 14.0) > 0.5) & inner, p[1])   # shaded side
    paint(t, (cells(ctx, [(8, 8), (8, 9), (6, 13)]) > 0.5) & inner, p[2])
    wick = spr(ctx, cells(ctx, [(7, 4), (7, 5)]), WICK, outline=False, bevel=1)
    return compose(ctx, t, wick)


# ------------------------------------------------------------------ cushion
CUSHION = [
    "................",
    "................",
    ".##..........##.",
    ".##############.",
    "..############..",
    "..############..",
    "..############..",
    "..############..",
    "..############..",
    "..############..",
    "..############..",
    "..############..",
    ".##############.",
    ".##..........##.",
    "................",
]


def cushion_with(ctx, p):
    m = rows_mask(ctx, CUSHION, round_=0.35)
    t = spr(ctx, m, p, smooth=0.2, porosity=0.5, sss=0.1, bevel=2)
    ring = ctx.edge(m, 1) > 0
    inner = (m > 0.5) & ~ring
    # pillow dome shading (smooth, round) instead of bevelled facets
    k = ctx.w / 16
    dx, dy = (ctx.x / k - 8.0) / 6.4, (ctx.y / k - 8.0) / 6.0
    z = np.sqrt(np.clip(1 - dx * dx - dy * dy, 0, 1))
    lam = np.clip(-0.5 * dx - 0.6 * dy + 0.62 * z, 0, 1)
    shade = ctx.palette(p[1:], np.clip(lam * 1.15 - 0.05, 0, 1))
    t.color = np.where(inner[..., None], shade, t.color)
    t.height = np.where(m > 0.5, 0.3 + 0.6 * z, 0.0)
    # puffy top-left highlight, dimpled centre button, little corner tassels
    paint(t, (ell(ctx, 8.0, 8.0, 1.6, 1.4) > 0.5) & inner, p[2])
    paint(t, cells(ctx, [(7, 8), (8, 8)]) > 0.5, p[1])
    paint(t, cells(ctx, [(7, 7)]) > 0.5, p[-1])
    return t


# ------------------------------------------------------------------ dye
def dye_with(ctx, p):
    """A heaped wooden scoop of powdered pigment."""
    handle = stroke(ctx, [(10.6, 11.0), (14.6, 7.0)], 1.6)
    th = spr(ctx, handle, SCOOP, bevel=1)
    bowl = minus(ell(ctx, 7.0, 10.6, 5.4, 3.4), box(ctx, 0, 0, 16, 10.0))
    rim = ell(ctx, 7.0, 10.0, 5.4, 1.2)
    tb = spr(ctx, U(bowl, rim), SCOOP, bevel=1.5)
    heap = U(ell(ctx, 7.0, 9.4, 5.0, 1.8), ell(ctx, 7.0, 8.2, 3.8, 2.4), ell(ctx, 6.6, 6.8, 2.2, 1.6))
    th2 = spr(ctx, heap, p, smooth=0.1, porosity=0.9, bevel=2.5)
    ring = ctx.edge(heap, 1) > 0
    inner = (heap > 0.5) & ~ring
    n = ctx.texel_noise("dye")
    th2.color[inner & (n < 0.15)] = p[1]
    th2.color[inner & (n > 0.88)] = p[-1]
    paint(th2, (cells(ctx, [(5, 6), (4, 7), (6, 6)]) > 0.5) & inner, p[-1])
    spill = spr(ctx, cells(ctx, [(2, 13), (12, 13), (3, 14)]), p[1:], outline=False, bevel=1)
    return compose(ctx, th, tb, th2, spill)


# ------------------------------------------------------------------ harness
def harness_with(ctx, p):
    """Ghast harness: a padded saddle seat with a girth strap looping underneath and a buckle."""
    from .h_lib import arc_pts
    seat = rows_mask(ctx, [
        "...##########...",
        ".##############.",
        "################",
        "################",
        ".##############.",
        "..############..",
    ], y0=3, round_=0.3)
    girth = stroke(ctx, arc_pts(8.0, 7.6, 5.6, 10, 170, 18), 1.8)
    tg = spr(ctx, girth, p[:4], smooth=0.25, porosity=0.4, bevel=1)
    t = spr(ctx, seat, p, smooth=0.25, porosity=0.4, bevel=2.5)
    ring = ctx.edge(seat, 1) > 0
    inner = (seat > 0.5) & ~ring
    paint(t, (cells(ctx, [(x, 6) for x in range(2, 14, 2)]) > 0.5) & inner, p[1])      # quilting
    paint(t, (cells(ctx, [(x, 5) for x in range(3, 13, 2)]) > 0.5) & inner, p[-1])
    paint(t, (box(ctx, 1.0, 4.0, 15.0, 5.0) > 0.5) & inner, p[-1])                     # padded roll
    bm = minus(box(ctx, 6.4, 11.8, 9.6, 14.4), box(ctx, 7.4, 12.6, 8.6, 13.6))
    buckle = metal(ctx, bm, BUCKLE, IRON, bevel=1)
    rings = metal(ctx, U(cells(ctx, [(1, 8), (14, 8)])), BUCKLE, IRON, bevel=1, outline=False)
    return compose(ctx, tg, t, rings, buckle)


def _by_color(fn):
    return lambda ctx, color: fn(ctx, dye_pal(color))


bundle = _by_color(bundle_with)
bundle_open_back = _by_color(bundle_open_back_with)
bundle_open_front = _by_color(bundle_open_front_with)
candle = _by_color(candle_with)
cushion = _by_color(cushion_with)
dye = _by_color(dye_with)
harness = _by_color(harness_with)

FAMILY = dict(bundle=bundle, bundle_open_back=bundle_open_back, bundle_open_front=bundle_open_front,
              candle=candle, cushion=cushion, dye=dye, harness=harness)

for _c in COLORS:
    for _k, _fn in FAMILY.items():
        register(f"item/{_c}_{_k}", lambda ctx, fn=_fn, c=_c: fn(ctx, c))
