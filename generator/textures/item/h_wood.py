"""Wood items (h-z woods): boats, chest boats, doors, signs, hanging signs; metal doors."""
import numpy as np

from ...registry import register
from .common import CHAIN, GOLD as GOLD_P
from .h_lib import (COPPER, IRON, cells, compose, metal, minus, paint, pal, rows_mask, seg, spr, union)

PLANKS = {
    "oak": pal("6f5533", "8a6b41", "9a784b", "a98656", "b79461", "c3a06b"),
    "spruce": pal("4b3321", "5c3f28", "6a4a31", "78553b", "856043", "916b4c"),
    "jungle": pal("7b5337", "8f6242", "9f6f4b", "ae7c55", "bb885f", "c69469"),
    "mangrove": pal("4e1e1c", "662824", "78302b", "883a33", "96443c", "a24f45"),
    "pale_oak": pal("9a948c", "b2aca4", "c3beb6", "d1cdc6", "ddd9d3", "e8e5e0"),
    "poplar": pal("7e7450", "968a62", "a89c70", "b8ac7e", "c6bb8c", "d2c89a"),
    "warped": pal("18403f", "235452", "2c6563", "357472", "418580", "4f978f"),
}
BARK = {
    "oak": pal("2e2214", "3b2c1b", "4e3b25", "5f492e", "705737"),
    "spruce": pal("1a120c", "231811", "302117", "3c2b1d", "483424"),
    "jungle": pal("2c220e", "3a2d12", "4c3c1a", "5c4a21", "6b5728"),
    "mangrove": pal("2a1e18", "3a2a22", "4a382e", "5a463a", "6a5446"),
    "pale_oak": pal("3a3632", "4e4a44", "625d56", "77716a", "8a847c"),
    "poplar": pal("2e2c22", "45423a", "8a877a", "b0ad9e", "cfccbe"),
    "warped": pal("1e1428", "3a1e46", "562a62", "4a8a7a", "5ab0a0"),
}
CHEST = pal("3a2410", "6a4420", "94612e", "b8803e", "d09a52")
LATCH = pal("4a4a50", "9a9aa0", "d0d0d6")


def _grain(ctx, t, mask, p, axis="y", step=3, salt=""):
    """Plank seams + grain specks inside a wooden mask."""
    ring = ctx.edge(mask, 1) > 0
    inner = (mask > 0.5) & ~ring
    k = ctx.w / 16
    v = (ctx.x if axis == "y" else ctx.y) / k
    seam = (np.floor(v) % step == step - 1) & inner
    t.color[seam] = p[1]
    n = ctx.texel_noise("grain" + salt)
    t.color[inner & ~seam & (n < 0.12)] = p[2]
    t.color[inner & ~seam & (n > 0.92)] = p[-1]
    return t


# ------------------------------------------------------------------ boats
HULL = [
    "#..............#",
    "##............##",
    "################",
    ".##############.",
    "..############..",
    "...##########...",
]


def boat(ctx, wood, chest=False):
    p = PLANKS[wood]
    hull_m = rows_mask(ctx, HULL, y0=8, round_=0.15)
    hull = spr(ctx, hull_m, p, smooth=0.25, porosity=0.25)
    ring = ctx.edge(hull_m, 1) > 0
    paint(hull, (cells(ctx, [(x, 12) for x in range(2, 14)]) > 0.5) & ~ring, p[1])
    paint(hull, (cells(ctx, [(x, 10) for x in range(1, 15)]) > 0.5) & ~ring, p[-1])
    rim = cells(ctx, [(x, 9) for x in range(2, 14)])
    paint(hull, rim > 0.5, p[0])
    oar = spr(ctx, union(seg(ctx, 3.5, 3.0, 9.5, 9.0, 1.2), seg(ctx, 2.6, 2.0, 4.0, 3.6, 2.2)),
              BARK[wood][1:] if wood != "poplar" else p[:5], smooth=0.2)
    layers = [oar]
    if chest:
        cm = rows_mask(ctx, ["######", "######", "######", "######", "######"], x0=8, y0=4, round_=0.05)
        c = spr(ctx, cm, CHEST, bevel=1.5, smooth=0.25)
        paint(c, cells(ctx, [(x, 6) for x in range(9, 13)]) > 0.5, CHEST[1])
        lt = metal(ctx, cells(ctx, [(10, 6), (11, 6), (10, 7), (11, 7)]), LATCH, IRON, bevel=1, outline=False)
        layers += [c, lt]
    layers.append(hull)
    return compose(ctx, *layers)


# ------------------------------------------------------------------ doors
DOOR = ["########"] * 16

WINDOWS = {  # texels of glass/holes per wood, door spans x 4..11
    "oak": [(x, y) for x in (5, 6, 9, 10) for y in (2, 3, 4)],
    "spruce": [],
    "jungle": [(x, y) for x in (5, 7, 9) for y in (2, 4)] + [(x, y) for x in (6, 8, 10) for y in (3, 5)],
    "mangrove": [(x, y) for x in range(5, 11) for y in (2, 4, 6)],
    "pale_oak": [(x, y) for x in range(5, 11) for y in range(2, 6) if not (x in (7, 8) or y == 4 and False)],
    "poplar": [(6, 2), (7, 2), (8, 2), (9, 2), (5, 3), (6, 3), (9, 3), (10, 3), (5, 4), (10, 4),
               (5, 5), (6, 5), (9, 5), (10, 5), (6, 6), (7, 6), (8, 6), (9, 6)],
    "warped": [(5, 3), (6, 2), (10, 4), (9, 5), (6, 9), (5, 10), (10, 11)],
}
GLASS = pal("6a8a98", "9cbccc", "c8e0ea")


def door(ctx, wood):
    p = PLANKS[wood]
    m = rows_mask(ctx, DOOR, x0=4, y0=0)
    t = spr(ctx, m, p, smooth=0.25, porosity=0.25, bevel=1.5)
    _grain(ctx, t, m, p, "y", 3, wood)
    ring = ctx.edge(m, 1) > 0
    # frame rails
    rails = cells(ctx, [(x, y) for x in range(5, 11) for y in (7, 8)] if wood != "spruce"
                  else [(x, y) for x in range(5, 11) for y in (4, 11)] + [(5 + i, 5 + i) for i in range(6)])
    paint(t, (rails > 0.5) & ~ring, p[2])
    win = cells(ctx, WINDOWS[wood]) > 0.5
    if wood in ("oak", "pale_oak", "poplar"):
        paint(t, win, GLASS[1])
        paint(t, win & (cells(ctx, [(5, 2), (9, 2), (6, 2), (5, 3)]) > 0.5), GLASS[2])
    else:
        t.alpha[win & ~ring] = 0  # cut-outs
    knob = cells(ctx, [(10, 9)])
    paint(t, knob > 0.5, pal("3a3a3a")[0] if wood != "pale_oak" else p[0])
    return t


IRON_DOOR = pal("4a4a50", "7a7a80", "a4a4aa", "c6c6cc", "e4e4e8")
COPPER_W = pal("3a4a3a", "5e7a5a", "6e9a74", "84ae8a", "a0c2a2")  # weathered
COPPER_O = pal("1e4a44", "2e6e64", "3e9080", "52a894", "74c4ae")  # oxidized


def metal_door(ctx, p, mid, salt, patina=None):
    m = rows_mask(ctx, DOOR, x0=4, y0=0)
    t = metal(ctx, m, p, mid, bevel=1.5, smooth=0.6 if patina is None else 0.35)
    ring = ctx.edge(m, 1) > 0
    inner = (m > 0.5) & ~ring
    paint(t, (cells(ctx, [(x, y) for x in range(5, 11) for y in (6, 11)]) > 0.5) & ~ring, p[1])
    paint(t, (cells(ctx, [(5, 1), (10, 1), (5, 14), (10, 14), (5, 7), (10, 7)]) > 0.5) & ~ring, p[-1])
    win = cells(ctx, [(x, y) for x in (6, 7, 8, 9) for y in (2, 3, 4)]) > 0.5
    t.alpha[win] = 0
    if patina is not None:
        n = ctx.texel_noise(salt)
        sp = inner & (n > 0.7)
        t.color[sp] = patina[2]
        t.color[inner & (n < 0.1)] = patina[1]
        t.metal[sp] = 0
    paint(t, cells(ctx, [(10, 9)]) > 0.5, p[0])
    return t


# ------------------------------------------------------------------ signs
SIGN = [
    "##############",
    "##############",
    "##############",
    "##############",
    "##############",
    "##############",
    "##############",
]


def sign(ctx, wood):
    p = PLANKS[wood]
    b = BARK[wood]
    post = rows_mask(ctx, ["##"] * 7, x0=7, y0=9)
    pt = spr(ctx, post, b, bevel=1, smooth=0.2)
    m = rows_mask(ctx, SIGN, x0=1, y0=2)
    t = spr(ctx, m, p, smooth=0.25, porosity=0.25, bevel=1.5)
    _grain(ctx, t, m, p, "x", 3, wood)
    ring = ctx.edge(m, 1) > 0
    # faint "text" lines
    txt = cells(ctx, [(x, y) for y in (4, 6) for x in range(3, 13) if (x * 7 + y) % 5 != 0])
    paint(t, (txt > 0.5) & ~ring, p[1])
    return compose(ctx, pt, t)


def hanging_sign(ctx, wood):
    p = PLANKS[wood]
    b = BARK[wood]
    bar = rows_mask(ctx, ["############"], x0=2, y0=1)
    bt = spr(ctx, union(bar, cells(ctx, [(2, 2), (13, 2)])), b, bevel=1, smooth=0.2)
    chains = metal(ctx, cells(ctx, [(4, 3), (4, 4), (11, 3), (11, 4)]), CHAIN, IRON, outline=False, bevel=1)
    paint(chains, cells(ctx, [(4, 4), (11, 3)]) > 0.5, CHAIN[1])
    m = rows_mask(ctx, ["############"] * 8, x0=2, y0=5, round_=0.05)
    t = spr(ctx, m, p, smooth=0.25, porosity=0.25, bevel=1.5)
    _grain(ctx, t, m, p, "x", 4, wood + "h")
    ring = ctx.edge(m, 1) > 0
    frame = (ctx.edge(m, 2) > 0) & ~ring
    paint(t, frame, p[2])
    paint(t, (cells(ctx, [(x, y) for y in (7, 9, 11) for x in range(4, 12) if (x + y) % 4]) > 0.5) & ~ring, p[1])
    return compose(ctx, bt, chains, t)


for _w in PLANKS:
    register(f"item/{_w}_door", lambda ctx, w=_w: door(ctx, w))
    register(f"item/{_w}_sign", lambda ctx, w=_w: sign(ctx, w))
    register(f"item/{_w}_hanging_sign", lambda ctx, w=_w: hanging_sign(ctx, w))
    if _w != "warped":
        register(f"item/{_w}_boat", lambda ctx, w=_w: boat(ctx, w))
        register(f"item/{_w}_chest_boat", lambda ctx, w=_w: boat(ctx, w, True))

register("item/iron_door", lambda ctx: metal_door(ctx, IRON_DOOR, IRON, "iron"))
register("item/weathered_copper_door",
         lambda ctx: metal_door(ctx, pal("5a3a26", "8a5a3a", "a8744e", "c08e64", "d6a87e"), COPPER, "wc", COPPER_W))
register("item/oxidized_copper_door", lambda ctx: metal_door(ctx, COPPER_O, None, "oc", COPPER_O))
