"""Doors (16x32 drawn once, cut into top/bottom) and trapdoors for every wood, iron and copper.

Each wood has its own design. Windows are cutout holes (alpha 0/1 only).
"""
import numpy as np

from ...engine import COPPER, IRON, pal
from ...registry import register
from .wood import WOODS
from .wood_kit import DARK_IRON, IRON_P, Canvas, board_field, crop_tex, tall_ctx

COPPER_STAGES = {
    "copper": dict(p=pal("6e3424", "9a4a30", "b8613f", "cf7a52", "e09468", "eeb087"), patina=0.0),
    "exposed_copper": dict(p=pal("6a4a3e", "8f6450", "a6765e", "b5856d", "c49882", "d0ab97"), patina=0.25),
    "weathered_copper": dict(p=pal("3e5f4c", "56785f", "6a8c6f", "6f9b7e", "86ad8f", "9cc0a3"), patina=0.65),
    "oxidized_copper": dict(p=pal("2b5f53", "3a7a6a", "4a9180", "57a291", "6db5a3", "8ac8b8"), patina=1.0),
}
PATINA = pal("2f6e60", "3f8a78", "52a08c", "6bb7a2", "8ccab8")


# ----------------------------------------------------------------- drawing helpers

def hole_bevel(cv, hole):
    """Shade the wood around a cutout: shadow above/left, light below/right."""
    c = cv.ctx
    h = np.asarray(hole) > 0.5
    s = c.s
    below = np.roll(h, -s, 0) & ~h  # pixel above a hole -> its lower neighbour is hole
    right = np.roll(h, -s, 1) & ~h
    above = np.roll(h, s, 0) & ~h
    left = np.roll(h, s, 1) & ~h
    cv.put(below | right, mul=0.72, dh=-0.05)
    cv.put((above | left) & ~(below | right), mul=1.1)
    cv.cut(h)


def frame(cv, x0, y0, x1, y1, w=2):
    """Raised border of width w around rect, interior left alone."""
    c = cv.ctx
    outer = c.rect(x0, y0, x1, y1) > 0
    inner = c.rect(x0 + w, y0 + w, x1 - w, y1 - w) > 0
    cv.raised(outer & ~inner, dh=0.06)
    return inner


def panel(cv, x0, y0, x1, y1, raised=True):
    m = cv.ctx.rect(x0, y0, x1, y1)
    if raised:
        cv.raised(m, dh=0.08)
    else:
        cv.sunken(m)
    return m > 0


def rail(cv, y0, y1, x0=0, x1=16):
    cv.raised(cv.ctx.rect(x0, y0, x1, y1), dh=0.05)


def iron(cv, mask, p=IRON_P, metal_id=IRON):
    cv.metal_part(np.asarray(mask) > 0.5, p, metal_id)


def nails(cv, pts, p=DARK_IRON):
    c = cv.ctx
    m = np.zeros((c.H, c.W), bool)
    for x, y in pts:
        m |= c.rect(x, y, x + 1, y + 1) > 0
    cv.put(m, color=p[3], height=0.8, porosity=0.0, metal=IRON)


def handle(cv, x, y, p=IRON_P):
    c = cv.ctx
    iron(cv, c.rect(x, y, x + 1, y + 2), p)
    cv.put(c.rect(x, y + 2, x + 1, y + 3) > 0, mul=0.7)


def lattice(c, x0, y0, x1, y1, period=4, diag=True):
    inside = c.rect(x0, y0, x1, y1) > 0
    if diag:
        a = np.floor(c.x) + np.floor(c.y)
        b = np.floor(c.x) - np.floor(c.y)
        bars = (a % period == 0) | (b % period == 0)
    else:
        bars = (np.floor(c.x) % period == 0) | (np.floor(c.y) % period == 0)
    return inside & ~bars


def wood_base(c, w, vertical=True, boards=3, salt="door"):
    spec = WOODS[w]
    span = c.w if vertical else c.h
    return board_field(c, spec["planks"], boards=boards, vertical=vertical, salt=f"{salt}{w}",
                       straight=0.6, span=span, joints=False, knots=0)


# ----------------------------------------------------------------- door designs (16x32)

def door_oak(cv, c):
    inner = frame(cv, 0, 0, 16, 32, 2)
    rail(cv, 15, 17, 2, 14)
    for x0 in (3, 9):
        for y0 in (3, 9):
            hole_bevel(cv, c.rect(x0, y0, x0 + 4, y0 + 4))
    panel(cv, 3, 19, 13, 23)
    panel(cv, 3, 25, 13, 30)
    handle(cv, 12, 17)


def door_spruce(cv, c):
    for y0 in (2, 14, 27):
        rail(cv, y0, y0 + 3)
    brace = c.segment(2.5, 25.5, 13.5, 17.5, 2.0) * (c.rect(0, 17, 16, 27))
    cv.raised(brace, dh=0.05)
    win = c.rect(5, 6, 11, 11) * (1 - c.rect(7.5, 6, 8.5, 11))
    hole_bevel(cv, win)
    for y0 in (2, 14, 27):
        iron(cv, c.rect(0, y0, 6, y0 + 3), DARK_IRON)
        nails(cv, [(9, y0 + 1), (13, y0 + 1)])
    handle(cv, 13, 18, DARK_IRON)


def door_birch(cv, c):
    frame(cv, 0, 0, 16, 32, 2)
    rail(cv, 15, 17, 2, 14)
    arch = np.maximum(c.rect(3, 7, 13, 14), c.circle(8, 7.5, 5.0) * c.rect(3, 2, 13, 8))
    bars = np.maximum(c.rect(7.5, 0, 8.5, 32), c.rect(0, 9, 16, 10))
    hole_bevel(cv, arch * (1 - bars))
    m = panel(cv, 3, 19, 13, 30)
    cv.sunken(c.rect(5, 21, 11, 28))
    handle(cv, 12, 17)


def door_jungle(cv, c):
    frame(cv, 0, 0, 16, 32, 2)
    rail(cv, 15, 17, 2, 14)
    hole_bevel(cv, lattice(c, 3, 3, 13, 14, 4))
    for x0 in (3, 9):
        panel(cv, x0, 19, x0 + 4, 30)
        cv.sunken(c.rect(x0 + 1.5, 21, x0 + 2.5, 28))
    handle(cv, 12, 17)


def door_acacia(cv, c):
    frame(cv, 0, 0, 16, 32, 2)
    rail(cv, 16, 18, 2, 14)
    for x0 in (4, 9):
        win = np.maximum(c.rect(x0, 5, x0 + 3, 14), c.circle(x0 + 1.5, 5, 1.6) * c.rect(x0, 3, x0 + 3, 6))
        hole_bevel(cv, win)
    inner = c.rect(3, 19, 13, 30) > 0
    chev = ((np.floor(c.y) + np.abs(np.floor(c.x) - 7.5)) % 3 < 1) & inner
    cv.sunken(inner, dh=-0.06, body=0.96)
    cv.put(chev, mul=0.78, dh=-0.05)
    handle(cv, 12, 18)


def door_dark_oak(cv, c):
    for y0 in (2, 15, 27):
        iron(cv, c.rect(0, y0, 16, y0 + 2), DARK_IRON)
        nails(cv, [(3, y0), (8, y0), (13, y0)])
    grate = c.rect(5, 6, 11, 12)
    hole_bevel(cv, grate)
    iron(cv, np.maximum(c.rect(7.5, 6, 8.5, 12), c.rect(5, 8.5, 11, 9.5)) * 1.0, DARK_IRON)
    ring = (c.circle(12.5, 20, 1.6) > 0) & ~(c.circle(12.5, 20, 0.7) > 0)
    iron(cv, ring, DARK_IRON)


def door_mangrove(cv, c):
    frame(cv, 0, 0, 16, 32, 2)
    rail(cv, 15, 17, 2, 14)
    for x0 in (3, 7, 11):
        for y0 in (3, 7, 11):
            hole_bevel(cv, c.rect(x0, y0, x0 + 2, y0 + 3))
    cv.sunken(c.rect(2, 17, 14, 30), dh=-0.05, body=0.95)
    for x in (5, 8, 11):
        cv.put(c.rect(x, 17, x + 1, 30) > 0, mul=0.8, dh=-0.04)
    rail(cv, 22, 24, 2, 14)
    handle(cv, 12, 18)


def door_cherry(cv, c):
    frame(cv, 0, 0, 16, 32, 2)
    rail(cv, 15, 17, 2, 14)
    win = c.circle(8, 8, 4.8)
    bars = np.maximum(c.rect(7.5, 0, 8.5, 16), c.rect(0, 7.5, 16, 8.5))
    hole_bevel(cv, win * (1 - bars) * (1 - c.circle(8, 8, 1.3)))
    for x0 in (3, 9):
        arch = np.maximum(c.rect(x0, 21, x0 + 4, 30), c.circle(x0 + 2, 21, 2.1) * c.rect(x0, 18, x0 + 4, 22))
        cv.raised(arch, dh=0.07)
    handle(cv, 12, 17)


def door_pale_oak(cv, c):
    frame(cv, 0, 0, 16, 32, 2)
    rail(cv, 16, 17, 2, 14)
    arch = c.polygon([(4, 14), (4, 7), (8, 2.5), (12, 7), (12, 14)])
    hole_bevel(cv, arch * (1 - c.rect(7.5, 0, 8.5, 16)))
    cv.sunken(c.rect(4, 19, 12, 24))
    cv.sunken(c.rect(4, 25, 12, 30))
    handle(cv, 13, 18)


def door_poplar(cv, c):
    frame(cv, 0, 0, 16, 32, 1)
    rail(cv, 15, 17, 1, 15)
    inner = c.rect(2, 2, 14, 14) > 0
    gaps = inner & (np.floor(c.y) % 2 == 1)
    hole_bevel(cv, gaps)
    slat_top = inner & (np.floor(c.y) % 2 == 0)
    cv.put(slat_top & (c.y - np.floor(c.y) < 1.0) & (np.floor(c.y) % 2 == 0), mul=1.06)
    line = (c.rect(3, 19, 13, 30) > 0) & ~(c.rect(4, 20, 12, 29) > 0)
    cv.put(line, mul=0.76, dh=-0.08)
    handle(cv, 12, 18)


def door_crimson(cv, c, vein):
    frame(cv, 0, 0, 16, 32, 2)
    rail(cv, 15, 17, 2, 14)
    win = np.maximum(c.rect(4, 4, 12, 13), c.rect(3, 5, 13, 12))
    bars = np.maximum(c.rect(6, 0, 7, 16), c.rect(9, 0, 10, 16))
    hole_bevel(cv, win * (1 - bars))
    panel(cv, 3, 19, 13, 30)
    v = (np.abs((c.x - 8) - np.sin(c.y * 0.9) * 2.0) < 0.6) & (c.rect(4, 20, 12, 29) > 0)
    cv.put(v, color=vein[0], dh=-0.05)
    handle(cv, 12, 17)


def door_warped(cv, c, vein):
    frame(cv, 0, 0, 16, 32, 2)
    rail(cv, 15, 17, 2, 14)
    win = c.rect(3, 3, 13, 14) > 0
    waves = np.abs(((c.y + np.sin(c.x * 0.8) * 1.2) % 4) - 2) < 0.55
    hole_bevel(cv, win & ~waves)
    panel(cv, 3, 19, 13, 30)
    ring = (c.circle(8, 24.5, 3.2) > 0) & ~(c.circle(8, 24.5, 2.0) > 0)
    cv.put(ring, color=vein[0], dh=-0.05)
    handle(cv, 12, 17)


def door_bamboo(cv, c):
    _bamboo_poles(cv, c, gap_rows=(3, 13))
    for y0 in (2, 14, 28):
        _lashing(cv, c, y0)


def _bamboo_poles(cv, c, gap_rows=None, vertical=True):
    p = WOODS["bamboo"]["planks"]
    pos = c.x if vertical else c.y
    along = c.y if vertical else c.x
    pw = 4
    k = np.floor(pos / pw)
    u = pos - k * pw
    n = c.noise(2, 2, salt="bpole", stretch=(1, 4) if vertical else (4, 1))
    v = 0.6 + (n - 0.5) * 0.3 + (c.texel_noise("bp") - 0.5) * 0.1
    v = np.where(u < 1, v + 0.25, np.where(u >= 2, v - 0.2, v))
    cv.color[:] = c.palette(p[1:], np.clip(v, 0, 1))
    cv.height[:] = 0.6 - np.abs(u - 1.5) * 0.1
    gap = u >= 3
    cv.put(gap, color=p[0], height=0.2)
    rng = c.rng("nodes")
    offs = rng.integers(0, 8, 8)
    node = (np.floor(along) % 8 == offs[k.astype(int) % 8]) & ~gap
    cv.put(node, color=p[-1], dh=0.05)
    cv.put(np.roll(node, c.s, 0 if vertical else 1) & ~gap, mul=0.8)
    if gap_rows:
        g = gap & (along >= gap_rows[0]) & (along < gap_rows[1])
        cv.cut(g)


def _lashing(cv, c, y0, vertical=False):
    rope = pal("5c4a2a", "7d6638", "9c8347")
    m = c.rect(0, y0, 16, y0 + 2) > 0 if not vertical else c.rect(y0, 0, y0 + 2, 16) > 0
    tw = ((np.floor(c.x) + np.floor(c.y)) % 2 == 0)
    cv.put(m, color=np.where(tw[..., None], rope[2], rope[1]), height=0.75, porosity=0.4)
    cv.put(c.edge(m.astype(np.float32), 1, "br") > 0, color=rope[0])


def door_metal(cv, c, p, metal_id, patina=0.0):
    _metal_base(cv, c, p, metal_id, patina)
    inner = frame(cv, 0, 0, 16, 32, 1)
    for x0 in (3, 9):
        hole_bevel(cv, c.rect(x0, 3, x0 + 4, 10))
    if metal_id == IRON:
        for y in (19, 23, 27):
            cv.raised(c.rect(3, y, 13, y + 2), dh=0.06)
    else:
        cv.raised(c.rect(3, 13, 13, 30), dh=0.06)
        diag = (np.abs(((c.x + c.y) % 6) - 3) < 0.5) & (c.rect(4, 14, 12, 29) > 0)
        cv.put(diag, mul=0.8, dh=-0.04)
    rv = [(1, 1), (14, 1), (1, 30), (14, 30), (1, 15), (14, 15)]
    for x, y in rv:
        cv.put(c.rect(x, y, x + 1, y + 1) > 0, color=p[-1], dh=0.1)
    cv.put(c.rect(12, 16, 13, 19) > 0, color=p[1], dh=0.1)


def _metal_base(cv, c, p, metal_id, patina):
    brush = c.noise(1, 2, salt="mb", stretch=(1, 6))
    n = c.noise(6, 2, salt="mn")
    cv.color[:] = c.palette(p[1:-1], np.clip(0.5 + (brush - 0.5) * 0.3 + (n - 0.5) * 0.4, 0, 1))
    cv.height[:] = 0.55
    cv.smooth[:] = 0.65
    cv.porosity[:] = 0.0
    cv.f0[:] = 0.0
    cv.metal[:] = metal_id
    if patina > 0:
        pn = c.noise(5, 3, 0.55, salt="pat") * 0.7 + c.texel_noise("pat") * 0.3
        pm = pn < patina * 1.05 - 0.05 if patina < 1 else pn >= 0
        cv.color[pm] = c.palette(PATINA, n)[pm]
        cv.metal[pm] = 0
        cv.f0[pm] = 0.04
        cv.smooth[pm] = 0.3
        cv.porosity[pm] = 0.3


DOOR_DESIGNS = {
    "oak": door_oak, "spruce": door_spruce, "birch": door_birch, "jungle": door_jungle,
    "acacia": door_acacia, "dark_oak": door_dark_oak, "mangrove": door_mangrove, "cherry": door_cherry,
    "pale_oak": door_pale_oak, "poplar": door_poplar, "bamboo": door_bamboo,
    "crimson": lambda cv, c: door_crimson(cv, c, WOODS["crimson"]["vein"]),
    "warped": lambda cv, c: door_warped(cv, c, WOODS["warped"]["vein"]),
}
BOARDS = {"spruce": 4, "dark_oak": 4, "mangrove": 3, "poplar": 2}


def door_full(ctx, key):
    c = tall_ctx(ctx, f"door:{key}", 32)
    if key == "iron":
        cv = Canvas(c, IRON_P[2])
        door_metal(cv, c, IRON_P, IRON)
    elif key in COPPER_STAGES:
        st = COPPER_STAGES[key]
        cv = Canvas(c, st["p"][2])
        door_metal(cv, c, st["p"], COPPER, st["patina"])
    else:
        cv = wood_base(c, key, vertical=True, boards=BOARDS.get(key, 3))
        DOOR_DESIGNS[key](cv, c)
    return cv.tex(wrap=False)


def door_half(ctx, key, top):
    return crop_tex(door_full(ctx, key), ctx, 0 if top else 16)


# ----------------------------------------------------------------- trapdoors (16x16)

def trap_wood(cv, c, key):
    if key == "oak":
        frame(cv, 0, 0, 16, 16, 2)
        rail(cv, 7, 9, 2, 14)
        cv.raised(c.rect(7, 2, 9, 14), dh=0.05)
        for x0 in (3, 10):
            for y0 in (3, 10):
                hole_bevel(cv, c.rect(x0, y0, x0 + 3, y0 + 3))
    elif key == "spruce":
        for x0 in (2, 11):
            cv.raised(c.rect(x0, 0, x0 + 3, 16), dh=0.05)
            nails(cv, [(x0 + 1, 2), (x0 + 1, 7), (x0 + 1, 13)])
        hole_bevel(cv, c.rect(7, 6, 9, 10))
    elif key == "birch":
        frame(cv, 0, 0, 16, 16, 1)
        for x0 in (3, 9):
            for y0 in (3, 7, 11):
                hole_bevel(cv, c.rect(x0, y0, x0 + 4, y0 + 2))
    elif key == "jungle":
        frame(cv, 0, 0, 16, 16, 2)
        hole_bevel(cv, lattice(c, 2, 2, 14, 14, 4))
    elif key == "acacia":
        frame(cv, 0, 0, 16, 16, 2)
        for x0 in (4, 9):
            hole_bevel(cv, c.rect(x0, 3, x0 + 3, 13))
    elif key == "dark_oak":
        for y0 in (2, 12):
            iron(cv, c.rect(0, y0, 16, y0 + 2), DARK_IRON)
            nails(cv, [(4, y0), (11, y0)])
        hole_bevel(cv, c.rect(5, 5, 11, 11))
        iron(cv, np.maximum(c.rect(7.5, 5, 8.5, 11), c.rect(5, 7.5, 11, 8.5)), DARK_IRON)
    elif key == "mangrove":
        frame(cv, 0, 0, 16, 16, 2)
        for x0 in (3, 7, 11):
            for y0 in (3, 7, 11):
                hole_bevel(cv, c.rect(x0, y0, x0 + 2, y0 + 2))
    elif key == "cherry":
        frame(cv, 0, 0, 16, 16, 2)
        win = c.circle(8, 8, 5.0)
        bars = np.maximum(c.rect(7.5, 0, 8.5, 16), c.rect(0, 7.5, 16, 8.5))
        hole_bevel(cv, win * (1 - bars) * (1 - c.circle(8, 8, 1.3)))
    elif key == "pale_oak":
        frame(cv, 0, 0, 16, 16, 2)
        rail(cv, 7, 9, 2, 14)
        for y0 in (3, 10):
            hole_bevel(cv, c.polygon([(4, y0 + 3), (4, y0 + 1), (8, y0 - 0.5), (12, y0 + 1), (12, y0 + 3)]))
    elif key == "poplar":
        frame(cv, 0, 0, 16, 16, 1)
        inner = c.rect(2, 2, 14, 14) > 0
        hole_bevel(cv, inner & (np.floor(c.y) % 2 == 1))
    elif key == "bamboo":
        _bamboo_poles(cv, c, gap_rows=(4, 12), vertical=False)
        for x0 in (2, 12):
            _lashing(cv, c, x0, vertical=True)
    elif key in ("crimson", "warped"):
        vein = WOODS[key]["vein"]
        frame(cv, 0, 0, 16, 16, 2)
        win = c.rect(3, 3, 13, 13) > 0
        if key == "crimson":
            bars = (c.rect(5, 0, 6, 16) + c.rect(10, 0, 11, 16)) > 0
            cv.put(c.rect(0, 0, 16, 16) > 0, mul=1.0)
        else:
            bars = np.abs(((c.y + np.sin(c.x * 0.8) * 1.2) % 4) - 2) < 0.55
        hole_bevel(cv, win & ~bars)
        cv.put(win & bars & (c.texel_noise("tv", soft=False) > 0.8), color=vein[0])


def trapdoor(ctx, key):
    c = ctx.sub(f"trap:{key}")
    if key == "iron" or key in COPPER_STAGES:
        p, mid, pat = (IRON_P, IRON, 0.0) if key == "iron" else (COPPER_STAGES[key]["p"], COPPER,
                                                                COPPER_STAGES[key]["patina"])
        cv = Canvas(c, p[2])
        _metal_base(cv, c, p, mid, pat)
        frame(cv, 0, 0, 16, 16, 1)
        if key == "iron":
            for x0 in (3, 9):
                for y0 in (3, 9):
                    hole_bevel(cv, c.rect(x0, y0, x0 + 4, y0 + 4))
        else:
            hole_bevel(cv, lattice(c, 2, 2, 14, 14, 4, diag=False) & (c.rect(3, 3, 13, 13) > 0))
        for x, y in ((1, 1), (14, 1), (1, 14), (14, 14)):
            cv.put(c.rect(x, y, x + 1, y + 1) > 0, color=p[-1], dh=0.1)
    else:
        horiz = key in ("spruce", "dark_oak")
        cv = wood_base(c, key, vertical=not horiz, boards=4 if horiz else 3, salt="trap")
        trap_wood(cv, c, key)
    return cv.tex(wrap=False)


_KEYS = ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry", "pale_oak",
         "poplar", "bamboo", "crimson", "warped", "iron", *COPPER_STAGES]
for _k in _KEYS:
    register(f"block/{_k}_door_top", lambda ctx, k=_k: door_half(ctx, k, True))
    register(f"block/{_k}_door_bottom", lambda ctx, k=_k: door_half(ctx, k, False))
    register(f"block/{_k}_trapdoor", lambda ctx, k=_k: trapdoor(ctx, k))
