"""Armor items (h-z): iron, netherite, leather (tinted + overlay), turtle helmet,
horse armor, nautilus armor, wolf armor."""
import numpy as np

from ...registry import register
from .common import GRAY, CHAIN
from .h_lib import (IRON, NETH, blank, cells, compose, metal, minus, paint, pal, ramp, rows_mask, spr, union)

IRON_P = pal("44444a", "76767c", "a2a2a8", "c4c4ca", "e8e8ec")
NETH_P = pal("161214", "2a2326", "3f3639", "564b4f", "73676b")
NETH_TRIM = pal("3a2a1a", "6b4a22", "a07438", "c9a060")
LEATHER_G = pal("4a4a4a", "7a7a7a", "a2a2a2", "c4c4c4", "e2e2e2")  # tinted base
BUCKLE = pal("3a3a40", "77777f", "b4b4bc", "e2e2e8")
LACE = pal("4a3a28", "7a6448", "a88e6a")

SHAPES = {
    "helmet": [
        "................",
        "................",
        ".....######.....",
        "...##########...",
        "..############..",
        "..############..",
        "..############..",
        "..#####..#####..",
        "..###......###..",
        "..###......###..",
        "..###......###..",
        "...#........#...",
    ],
    "chestplate": [
        "................",
        "..####....####..",
        ".######..######.",
        ".##############.",
        ".##############.",
        ".##.########.##.",
        ".##.########.##.",
        "....########....",
        "....########....",
        "....########....",
        "....########....",
        "....########....",
        ".....######.....",
    ],
    "leggings": [
        "................",
        "................",
        "...##########...",
        "...##########...",
        "...##########...",
        "...####..####...",
        "...###....###...",
        "...###....###...",
        "...###....###...",
        "...###....###...",
        "...###....###...",
        "...###....###...",
        "...###....###...",
    ],
    "boots": [
        "................",
        "................",
        "................",
        "................",
        "..####...####...",
        "..####...####...",
        "..####...####...",
        "..####...####...",
        "..####...####...",
        ".#####..#####...",
        "######.######...",
        "######.######...",
    ],
}
# leather pieces: softer cap, tunic, trousers, shoes
LEATHER_SHAPES = {
    "helmet": [
        "................",
        "................",
        "................",
        ".....######.....",
        "...##########...",
        "..############..",
        "..############..",
        ".##############.",
        ".####......####.",
        "..##........##..",
    ],
    "chestplate": [
        "................",
        "................",
        "..####....####..",
        ".#####....#####.",
        ".##############.",
        ".##############.",
        ".##.########.##.",
        ".##.########.##.",
        "....########....",
        "....########....",
        "....########....",
        "....########....",
        "....########....",
    ],
    "leggings": SHAPES["leggings"],
    "boots": SHAPES["boots"],
}

# detail texels per piece, in 16x16 design coordinates
SEAMS = {  # darker plate seams
    "helmet": [(x, 6) for x in range(3, 13)] + [(7, 3), (8, 3), (7, 4), (8, 4)],
    "chestplate": [(7, y) for y in range(4, 12)] + [(8, y) for y in range(4, 12)],
    "leggings": [(x, 4) for x in range(4, 13)],
    "boots": [(x, 8) for x in (3, 4, 5, 10, 11, 12)],
}
RIVETS = {
    "helmet": [(4, 5), (11, 5), (7, 4)],
    "chestplate": [(3, 3), (12, 3), (5, 8), (10, 8)],
    "leggings": [(5, 3), (10, 3), (4, 8), (11, 8)],
    "boots": [(3, 5), (10, 5)],
}


def armor_piece(ctx, piece, p, mid, smooth=0.7, netherite=False):
    m = rows_mask(ctx, SHAPES[piece], round_=0.12)
    t = metal(ctx, m, p, mid, smooth=smooth)
    ring = ctx.edge(m, 1) > 0
    paint(t, (cells(ctx, SEAMS[piece]) > 0.5) & ~ring, p[1])
    paint(t, (cells(ctx, RIVETS[piece]) > 0.5) & ~ring, p[-1])
    if netherite:  # dark gold-bronze trim on the lower rim (netherite heritage: gold)
        lower = rows_mask(ctx, _lower_rim(SHAPES[piece]))
        paint(t, (lower > 0.5) & ~ring, NETH_TRIM[1])
    return t


def _lower_rim(rows):
    """Texels whose lower neighbour is outside the shape (bottom rim, one row up)."""
    out = []
    for j, row in enumerate(rows):
        r = ""
        for i, ch in enumerate(row):
            below = rows[j + 1][i] if j + 1 < len(rows) else "."
            below2 = rows[j + 2][i] if j + 2 < len(rows) else "."
            r += "#" if ch == "#" and below == "#" and below2 != "#" else "."
        out.append(r)
    return out


def leather(ctx, piece, overlay=False):
    rows = LEATHER_SHAPES[piece]
    m = rows_mask(ctx, rows, round_=0.2)
    if not overlay:
        t = spr(ctx, m, LEATHER_G, smooth=0.25, porosity=0.4)
        ring = ctx.edge(m, 1) > 0
        n = ctx.texel_noise("leather")
        inner = (m > 0.5) & ~ring
        t.color[inner & (n < 0.15)] *= 0.92
        # stitch lines (tinted too)
        st = {"helmet": [(x, 6) for x in range(3, 13, 2)],
              "chestplate": [(x, 12) for x in range(4, 12, 2)],
              "leggings": [(x, 4) for x in range(4, 13, 2)],
              "boots": [(x, 8) for x in (3, 5, 10, 12)]}[piece]
        paint(t, (cells(ctx, st) > 0.5) & ~ring, LEATHER_G[1])
        return t
    # overlay: untinted buckles, laces, soles
    parts = []
    if piece == "helmet":
        parts.append(spr(ctx, cells(ctx, [(2, 8), (2, 9), (13, 8), (13, 9)]), BUCKLE, outline=False, bevel=1))
    elif piece == "chestplate":
        parts.append(spr(ctx, cells(ctx, [(7, 4), (8, 5), (7, 6), (8, 7)]), LACE, outline=False, bevel=1))
        parts.append(spr(ctx, cells(ctx, [(7, 11), (8, 11)]), BUCKLE, outline=False, bevel=1))
    elif piece == "leggings":
        parts.append(spr(ctx, cells(ctx, [(7, 3), (8, 3)]), BUCKLE, outline=False, bevel=1))
    elif piece == "boots":
        parts.append(spr(ctx, union(rows_mask(ctx, ["######.######"], x0=0, y0=11)), LACE, outline=False, bevel=1))
    return compose(ctx, *parts)


# ---------------------------------------------------------------- horse armor
HORSE = [
    "................",
    "..........#.....",
    ".........###....",
    "........#####...",
    "......#######...",
    "....#########...",
    "..###########...",
    ".############...",
    ".#####.#######..",
    "..###...#######.",
    "........#######.",
    "........########",
    ".......#########",
    ".......#########",
    "................",
]


def horse_armor(ctx, p, mid=None, smooth=0.7, tinted=False, overlay=False):
    m = rows_mask(ctx, HORSE, round_=0.15)
    if overlay:  # untinted buckles / straps of the leather horse armor
        straps = cells(ctx, [(9, 4), (9, 5), (9, 6), (12, 10), (12, 11), (12, 12)])
        return spr(ctx, straps, BUCKLE, outline=False, bevel=1)
    t = metal(ctx, m, p, mid, smooth=smooth) if mid else spr(ctx, m, p, smooth=smooth, porosity=0.3)
    ring = ctx.edge(m, 1) > 0
    eye = cells(ctx, [(6, 8)])
    paint(t, eye > 0.5, p[0])
    paint(t, (cells(ctx, [(x, 9 - (x - 8) // 2) for x in range(8, 12)]) > 0.5) & ~ring, p[1])  # cheek seam
    paint(t, (cells(ctx, [(4, 6), (10, 11), (13, 12)]) > 0.5) & ~ring, p[-1])
    return t


# ------------------------------------------------------------- nautilus armor
NAUT = [
    "................",
    "................",
    "................",
    "......#####.....",
    "....#########...",
    "...###########..",
    "..#############.",
    "..#############.",
    ".##############.",
    ".#############..",
    ".####......###..",
    ".##.............",
]


def nautilus_armor(ctx, p, mid, smooth=0.7, accent=None):
    m = rows_mask(ctx, NAUT, round_=0.25)
    t = metal(ctx, m, p, mid, smooth=smooth)
    ring = ctx.edge(m, 1) > 0
    # spiral emblem and ribs
    spiral = cells(ctx, [(8, 6), (9, 6), (10, 7), (10, 8), (9, 9), (8, 9), (7, 8), (7, 7)])
    paint(t, (spiral > 0.5) & ~ring, p[1])
    paint(t, cells(ctx, [(8, 7), (9, 8)]) > 0.5, accent if accent is not None else p[-1])
    ribs = cells(ctx, [(4, 6), (3, 8), (5, 5), (12, 6), (13, 8)])
    paint(t, (ribs > 0.5) & ~ring, p[-1])
    return t


# --------------------------------------------------------------- wolf armor
WOLF = [
    "................",
    "................",
    "................",
    "................",
    "....########....",
    "..############..",
    ".##############.",
    ".##############.",
    ".##############.",
    ".###.######.###.",
    ".##..######..##.",
    ".....######.....",
    "......####......",
]
SCUTE = pal("4a2a26", "7a4440", "a8625a", "c88478", "e6aa9a")


def wolf_armor(ctx, overlay=False):
    m = rows_mask(ctx, WOLF, round_=0.2)
    ring = ctx.edge(m, 1) > 0
    if not overlay:
        t = spr(ctx, m, SCUTE, smooth=0.55, f0=0.05)
        bands = cells(ctx, [(x, 7) for x in range(2, 14)] + [(x, 10) for x in range(6, 10)])
        paint(t, (bands > 0.5) & ~ring, SCUTE[1])
        return t
    # dyed cloth band (grayscale, tinted by dye; invisible when undyed)
    band = rows_mask(ctx, ["############", ".##########."], x0=2, y0=5)
    band = band * (m > 0.5)
    return spr(ctx, band, GRAY[1:], outline=False, bevel=1, smooth=0.15, porosity=0.4)


# -------------------------------------------------------------- turtle helmet
TURTLE = pal("1a3a12", "2c5e1e", "3f8030", "5ca044", "86c464")


def turtle_helmet(ctx):
    m = rows_mask(ctx, SHAPES["helmet"], round_=0.2)
    t = spr(ctx, m, TURTLE, smooth=0.5, f0=0.05)
    ring = ctx.edge(m, 1) > 0
    plates = cells(ctx, [(5, 4), (6, 5), (9, 5), (10, 4), (7, 6), (8, 6), (4, 7), (11, 7)])
    paint(t, (plates > 0.5) & ~ring, TURTLE[1])
    paint(t, (cells(ctx, [(6, 3), (7, 4), (8, 4), (9, 3), (3, 5)]) > 0.5) & ~ring, TURTLE[4])
    return t


for _piece in SHAPES:
    register(f"item/iron_{_piece}", lambda ctx, pc=_piece: armor_piece(ctx, pc, IRON_P, IRON))
    register(f"item/netherite_{_piece}", lambda ctx, pc=_piece: armor_piece(ctx, pc, NETH_P, NETH, 0.62, True))
    register(f"item/leather_{_piece}", lambda ctx, pc=_piece: leather(ctx, pc))
    register(f"item/leather_{_piece}_overlay", lambda ctx, pc=_piece: leather(ctx, pc, True))

register("item/iron_horse_armor", lambda ctx: horse_armor(ctx, IRON_P, IRON))
register("item/netherite_horse_armor", lambda ctx: horse_armor(ctx, NETH_P, NETH, 0.62))
register("item/leather_horse_armor", lambda ctx: horse_armor(ctx, LEATHER_G, None, 0.25))
register("item/leather_horse_armor_overlay", lambda ctx: horse_armor(ctx, LEATHER_G, overlay=True))
register("item/iron_nautilus_armor", lambda ctx: nautilus_armor(ctx, IRON_P, IRON))
register("item/netherite_nautilus_armor", lambda ctx: nautilus_armor(ctx, NETH_P, NETH, 0.62, NETH_TRIM[2]))
register("item/wolf_armor", lambda ctx: wolf_armor(ctx))
register("item/wolf_armor_overlay", lambda ctx: wolf_armor(ctx, True))
register("item/turtle_helmet", turtle_helmet)
