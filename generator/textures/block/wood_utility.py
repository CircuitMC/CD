"""Wooden utility / workstation blocks: crafting table, bookshelves, barrel, composter,
beehive & bee nest, honey, loom, lectern, smithing/fletching/cartography tables,
note block, jukebox, scaffolding, ladder, hay, straw bed."""
import numpy as np

from ...engine import IRON, pal
from ...registry import register
from .wood import WOODS
from .wood_doors import frame, hole_bevel, iron, nails, panel, rail
from .wood_kit import DARK_IRON, IRON_P, Canvas, board_field, end_grain_rings, fiber_grain

OAK = WOODS["oak"]["planks"]
SPRUCE = WOODS["spruce"]["planks"]
BIRCH = WOODS["birch"]["planks"]
DARK = WOODS["dark_oak"]["planks"]
JUNGLE = WOODS["jungle"]["planks"]
BOOKS = pal("7a2a22", "2f4f7a", "3e6b33", "8a6a2a", "5a3a6a", "8a4a1e", "35605e", "6a2a3a", "a08850")
PAPER = pal("a89a78", "c4b690", "d8cba6", "e8ddbc")
HONEY = pal("8a4a08", "b8680c", "d88a14", "eba724", "f5c242", "fbd96a")
STRAW = pal("8a6a1e", "a8862a", "c09d36", "d2b044", "dfc155", "ead06a")
TWINE = pal("4a3418", "6a4a22", "84602c")


def planks_cv(ctx, p, salt, vertical=False, boards=4, joints=True, **kw):
    return board_field(ctx, p, boards=boards, vertical=vertical, salt=salt, joints=joints, knots=0, **kw)


def rect(c, x0, y0, x1, y1):
    return c.rect(x0, y0, x1, y1) > 0


def border(c, w=1):
    return ~rect(c, w, w, c.w - w, c.h - w)


def dark_frame(cv, p, w=1, wood_mul=0.8):
    """Darker raised outer frame (end grain of the box edges)."""
    c = cv.ctx
    m = border(c, w)
    cv.put(m, mul=wood_mul)
    cv.raised(m, dh=0.05)


def tool_hammer(cv, c, x, y):
    cv.put(rect(c, x + 1, y + 2, x + 2, y + 8), color=JUNGLE[2], height=0.7)
    cv.put(rect(c, x + 1, y + 2, x + 2, y + 8) & (np.floor(c.y) % 3 == 0), color=JUNGLE[1])
    iron(cv, rect(c, x - 1, y, x + 4, y + 2))


def tool_saw(cv, c, x, y):
    blade = c.polygon([(x, y), (x + 3, y), (x + 3, y + 8), (x, y + 6)]) > 0
    iron(cv, blade)
    teeth = blade & (np.floor(c.x) == x) & (np.floor(c.y) % 2 == 0)
    cv.put(teeth, color=IRON_P[1])
    cv.put(rect(c, x, y - 2, x + 3, y), color=JUNGLE[3], height=0.7)
    cv.put(rect(c, x + 1, y - 1, x + 2, y), color=JUNGLE[0])


def tool_square(cv, c, x, y):
    m = rect(c, x, y, x + 1, y + 6) | rect(c, x, y + 5, x + 5, y + 6)
    iron(cv, m)


# ----------------------------------------------------------------- crafting table

def crafting_top(ctx):
    c = ctx
    cv = planks_cv(c, OAK, "ct_top", boards=1, joints=False, seams=False, straight=0.5)
    rim = border(c, 2)
    cv.put(rim, color=c.palette(DARK[2:5], c.texel_noise("ctr")), height=0.6)
    cv.raised(rim, dh=0.04)
    gx, gy = np.floor(c.x), np.floor(c.y)
    inner = rect(c, 2, 2, 14, 14)
    grid = inner & ((gx == 6) | (gx == 10) | (gy == 6) | (gy == 10))
    cv.put(grid, color=OAK[0], height=0.3)
    cv.put(inner & ~grid & ((gx == 7) | (gx == 11) | (gy == 7) | (gy == 11)), mul=0.9)
    cv.put(inner & ~grid & ((gx == 5) | (gx == 9) | (gy == 5) | (gy == 9)), mul=1.06)
    for x, y in ((0, 0), (14, 0), (0, 14), (14, 14)):
        iron(cv, rect(c, x, y, x + 2, y + 2))
    return cv.tex(wrap=True)


def crafting_side(ctx, front):
    c = ctx
    cv = planks_cv(c, OAK, "ct_side", boards=4)
    band = rect(c, 0, 0, 16, 3)
    cv.put(band, color=c.palette(DARK[2:5], c.texel_noise("ctb")), height=0.6)
    cv.raised(band, dh=0.04)
    cv.put(rect(c, 0, 13, 16, 16), mul=0.85)
    for x in (0, 15):
        cv.put(rect(c, x, 3, x + 1, 16), color=DARK[2], height=0.6)
    if front:
        tool_saw(cv, c, 3, 6)
        tool_hammer(cv, c, 10, 4)
    else:
        tool_square(cv, c, 3, 5)
        nails(cv, [(10, 5), (12, 5)])
        cv.put(rect(c, 9, 6, 14, 11), color=PAPER[2], height=0.6)
        cv.put(rect(c, 10, 7, 13, 8) | rect(c, 10, 9, 12, 10), color=PAPER[0])
    return cv.tex(wrap=True)


# ----------------------------------------------------------------- bookshelves

def book_row(cv, c, y0, y1, salt, gap_chance=0.12):
    rng = c.rng(f"books{salt}")
    x = 1
    while x < 15:
        w = int(rng.choice([1, 2, 2, 2, 3]))
        w = min(w, 15 - x)
        if rng.random() < gap_chance:
            x += w
            continue
        h = int(rng.integers(y1 - y0 - 2, y1 - y0 + 1))
        col = BOOKS[int(rng.integers(0, len(BOOKS)))] * rng.uniform(0.85, 1.1)
        m = rect(c, x, y1 - h, x + w, y1)
        cv.put(m, color=np.clip(col, 0, 1), height=0.7, smooth=0.3, porosity=0.1)
        cv.put(m & (np.floor(c.x) == x), mul=1.25)
        cv.put(m & (np.floor(c.x) == x + w - 1) & (w > 1), mul=0.75)
        cv.put(m & (np.floor(c.y) == y1 - h + 1), color=np.clip(col * 1.5 + 0.1, 0, 1))  # label band
        if rng.random() < 0.3 and w >= 2:
            # leaning book
            pass
        x += w


def bookshelf(ctx):
    c = ctx
    cv = planks_cv(c, OAK, "bs", boards=4)
    for y0, y1 in ((1, 7), (9, 15)):
        cv.put(rect(c, 1, y0, 15, y1), color=OAK[0] * 0.6, height=0.15)
        book_row(cv, c, y0, y1, f"{y0}")
        cv.put(rect(c, 1, y0, 15, y0 + 1) & (cv.height < 0.2), mul=0.7)
    return cv.tex(wrap=True)


SLOTS = [(x0, y0, x1, y1) for y0, y1 in ((1, 7), (9, 15)) for x0, x1 in ((1, 5), (6, 10), (11, 15))]


def chiseled(ctx, occupied):
    c = ctx
    cv = planks_cv(c, OAK, "cbs", boards=2)
    dark_frame(cv, OAK, 1, 0.85)
    for i, (x0, y0, x1, y1) in enumerate(SLOTS):
        cv.sunken(rect(c, x0, y0, x1, y1), dh=-0.3, body=0.45)
        if occupied:
            rng = c.rng(f"cslot{i}")
            x = x0
            while x < x1:
                w = min(int(rng.choice([1, 1, 2])), x1 - x)
                h = int(rng.integers(y1 - y0 - 1, y1 - y0 + 1))
                col = BOOKS[int(rng.integers(0, len(BOOKS)))]
                m = rect(c, x, y1 - h, x + w, y1)
                cv.put(m, color=col, height=0.65, smooth=0.3)
                cv.put(m & (np.floor(c.x) == x), mul=1.25)
                cv.put(m & (np.floor(c.y) == y1 - h + 1), color=np.clip(col * 1.5 + 0.1, 0, 1))
                x += w
    return cv.tex(wrap=False)


def chiseled_side(ctx):
    c = ctx
    cv = planks_cv(c, OAK, "cbside", vertical=True, boards=3)
    dark_frame(cv, OAK, 1, 0.85)
    rail(cv, 7, 9, 1, 15)
    return cv.tex(wrap=False)


def chiseled_top(ctx):
    c = ctx
    cv = planks_cv(c, OAK, "cbtop", boards=4)
    dark_frame(cv, OAK, 1, 0.85)
    cv.sunken(rect(c, 3, 3, 13, 13), dh=-0.05, body=0.95)
    return cv.tex(wrap=False)


# ----------------------------------------------------------------- barrel

BARREL = SPRUCE


def barrel_side(ctx):
    c = ctx
    cv = planks_cv(c, BARREL, "barrel", vertical=True, boards=4, joints=False)
    for y0 in (2, 12):
        iron(cv, rect(c, 0, y0, 16, y0 + 2), DARK_IRON)
        nails(cv, [(2, y0), (6, y0), (10, y0), (14, y0)], IRON_P)
    return cv.tex(wrap=True)


def barrel_top(ctx, mode):
    c = ctx
    cv = planks_cv(c, BARREL, f"barrel{mode}", boards=4, joints=False)
    rim = border(c, 2)
    cv.put(rim, color=c.palette(BARREL[1:4], c.texel_noise("br")), height=0.65)
    cv.put(border(c, 1), color=DARK_IRON[2], metal=IRON, smooth=0.5, porosity=0.0)
    cv.raised(rim, dh=0.04)
    if mode == "open":
        inner = rect(c, 2, 2, 14, 14)
        depth = np.clip(np.minimum.reduce([c.x - 2, c.y - 2]) / 4, 0, 1)
        cv.put(inner, color=np.clip(BARREL[0][None, None] * (0.75 - depth[..., None] * 0.45), 0, 1), height=0.0)
        cv.put(inner & ~rect(c, 3, 3, 14, 14), color=BARREL[0] * 0.4)
    elif mode == "top":
        cv.put(rect(c, 7, 6, 9, 10), color=BARREL[0], height=0.3)
        cv.put(rect(c, 5, 7, 11, 9), color=BARREL[0], height=0.3)
        cv.put(rect(c, 7, 7, 9, 9), color=BARREL[2], height=0.5)
    else:
        cv.put(rect(c, 2, 2, 14, 14), mul=0.85)
    return cv.tex(wrap=False)


# ----------------------------------------------------------------- composter

def composter_side(ctx):
    c = ctx
    cv = planks_cv(c, OAK, "comp", vertical=True, boards=4, joints=False)
    m = border(c, 2)
    cv.put(m, color=c.palette(OAK[1:4], c.texel_noise("cmp")), height=0.62)
    cv.raised(m, dh=0.04)
    cv.put(rect(c, 2, 2, 14, 14), mul=0.9)
    rail(cv, 7, 9, 2, 14)
    nails(cv, [(0.5 + 0, 0), (14, 0), (0, 14), (14, 14)])
    return cv.tex(wrap=True)


def composter_top(ctx):
    c = ctx
    cv = planks_cv(c, OAK, "comptop", boards=4, joints=False)
    m = border(c, 2)
    cv.raised(m, dh=0.04)
    cv.cut(rect(c, 2, 2, 14, 14))
    return cv.tex(wrap=False)


def composter_bottom(ctx):
    c = ctx
    cv = planks_cv(c, OAK, "compbot", boards=4)
    cv.put(rect(c, 0, 0, 16, 16), mul=0.82)
    return cv.tex(wrap=True)


def compost(ctx, ready):
    c = ctx
    n = c.noise(4, 2, 0.6, salt="compost")
    g = c.texel_noise("compost")
    v = n * 0.4 + g * 0.6
    p = pal("2a1d12", "3a2918", "4a361f", "5a4427", "6a5230")
    cv = Canvas(c, c.palette(p, v), height=0.4 + v * 0.3, smooth=0.05, porosity=0.8)
    r = c.texel_noise("bits", soft=False)
    cv.put(r > 0.9, color=pal("4c5a22")[0], height=0.7)
    cv.put((r > 0.84) & (r <= 0.9), color=pal("6a4a24")[0], height=0.6)
    if ready:
        r2 = c.texel_noise("meal", soft=False)
        cv.put(r2 > 0.7, color=c.palette(pal("b0aa9a", "cfc9ba", "e6e2d6"), c.texel_noise("ml")), height=0.75,
               porosity=0.6)
    return cv.tex(wrap=True)


# ----------------------------------------------------------------- beehive / bee nest

HIVE = pal("7a5a2c", "a07a3e", "b48b48", "c49a52", "d2a95e", "ddb66a")


def beehive_side(ctx):
    c = ctx
    cv = planks_cv(c, HIVE, "hive", boards=4)
    m = border(c, 1)
    cv.put(rect(c, 0, 0, 1, 16) | rect(c, 15, 0, 16, 16), color=OAK[1], height=0.6)
    cv.put(rect(c, 0, 0, 16, 1) | rect(c, 0, 15, 16, 16), color=OAK[2], height=0.6)
    return cv.tex(wrap=True)


def beehive_end(ctx):
    c = ctx
    cv = planks_cv(c, HIVE, "hiveend", boards=4)
    frame(cv, 0, 0, 16, 16, 1)
    cv.put(rect(c, 6, 3, 10, 13), color=HONEY[3], height=0.6, smooth=0.6)
    cv.raised(rect(c, 6, 3, 10, 13), dh=0.03)
    return cv.tex(wrap=False)


def beehive_front(ctx, honey):
    c = ctx
    cv = planks_cv(c, HIVE, "hivefront", boards=4)
    frame(cv, 0, 0, 16, 16, 1)
    hole = rect(c, 5, 8, 11, 11)
    cv.put(hole, color=pal("1d140a")[0], height=0.05)
    cv.put(rect(c, 5, 8, 11, 9), color=pal("0f0a05")[0])
    cv.raised(rect(c, 3, 11, 13, 13), dh=0.1)
    if honey:
        drip = rect(c, 4, 4, 12, 8) | rect(c, 5, 8, 6, 12) | rect(c, 9, 8, 10, 14) | rect(c, 11, 6, 12, 10)
        lv = np.clip(0.55 + (c.texel_noise("hd") - 0.5) * 0.4 - (c.y - 4) * 0.03, 0, 1)
        cv.put(drip, color=c.palette(HONEY[1:], lv), height=0.7, smooth=0.85, porosity=0.0)
        cv.put(drip & (c.edge(drip.astype(np.float32), 1, "tl") > 0), color=HONEY[-1])
    return cv.tex(wrap=False)


NEST = pal("8a6418", "b08a24", "c89e30", "d8b03c", "e4c04c", "eed060")


def nest_base(c, salt):
    n = c.noise(4, 2, salt=f"nest{salt}", stretch=(3, 1))
    row = np.floor(c.y + c.lattice_noise(4, 16, f"nw{salt}") * 1.5)
    v = 0.55 + (n - 0.5) * 0.4 + (c.texel_noise(f"nt{salt}") - 0.5) * 0.2
    band = row % 3 == 0
    cv = Canvas(c, c.palette(NEST[1:], np.clip(v, 0, 1)), height=0.55, smooth=0.15, porosity=0.4)
    cv.put(band, color=NEST[0], height=0.35)
    cv.put(np.roll(band, c.s, 0) & ~band, mul=1.1)
    return cv


def nest_side(ctx):
    return nest_base(ctx, "side").tex(wrap=True)


def nest_top(ctx, bottom):
    c = ctx
    cv = nest_base(c, "top" + str(bottom))
    cap = rect(c, 2, 2, 14, 14)
    cv.put(cap, color=c.palette(OAK[1:5], c.texel_noise("ncap")), height=0.65)
    cv.raised(cap, dh=0.05)
    cv.put(rect(c, 6, 6, 10, 10), color=OAK[0], height=0.3)
    if bottom:
        cv.put(rect(c, 0, 0, 16, 16), mul=0.85)
    return cv.tex(wrap=True)


def nest_front(ctx, honey):
    c = ctx
    cv = nest_base(c, "front")
    holes = [(4, 4), (10, 6), (6, 10)]
    for x, y in holes:
        cv.put(rect(c, x, y, x + 2, y + 2), color=pal("22180a")[0], height=0.05)
        cv.put(rect(c, x, y + 2, x + 2, y + 3), color=NEST[-1])
    if honey:
        for x, y in holes:
            d = rect(c, x, y + 1, x + 2, y + 2) | rect(c, x, y + 2, x + 1, y + 4)
            cv.put(d, color=HONEY[3], height=0.7, smooth=0.85, porosity=0.0)
            cv.put(rect(c, x, y + 1, x + 1, y + 2), color=HONEY[-1])
    return cv.tex(wrap=True)


def honey_block(ctx, face):
    c = ctx
    n = c.noise(6, 2, salt="honey")
    v = 0.5 + (n - 0.5) * 0.4
    cv = Canvas(c, c.palette(HONEY[2:], v), height=0.5, smooth=0.9, porosity=0.0, alpha=0.62)
    cv.sss[:] = 0.5
    w = {"top": 1, "side": 1, "bottom": 2}[face]
    edge = border(c, w)
    cv.put(edge, color=HONEY[2], alpha=0.85, height=0.7)
    cv.put(edge & (c.edge(np.ones((c.H, c.W), np.float32), 1, "tl") > 0), color=HONEY[4])
    if face == "side":
        cv.put(rect(c, 1, 1, 15, 4), color=HONEY[4], alpha=0.7)
    hl = rect(c, 3, 3, 6, 4) | rect(c, 3, 4, 4, 6)
    cv.put(hl, color=HONEY[-1], alpha=0.75)
    t = cv.tex(wrap=True, grain=0.0)
    return t


def honeycomb_block(ctx):
    c = ctx
    # hex cells on a wrapping lattice: 4 columns x 4 rows (offset rows)
    pts = []
    for j in range(4):
        for i in range(4):
            pts.append(((i + 0.5 * (j % 2)) * 4 + 1, j * 4 + 2))
    vo = c.voronoi(len(pts), points=pts)
    wall = (vo["f2"] - vo["f1"]) < 0.9
    d = np.clip(vo["f1"] / 2.2, 0, 1)
    v = 0.75 - d * 0.35 + np.clip(-(vo["dx"] + vo["dy"]) / 4, -0.3, 0.3)
    cv = Canvas(c, c.palette(HONEY[1:], np.clip(v, 0, 1)), height=0.45 - d * 0.1, smooth=0.7, porosity=0.05)
    cv.put(wall, color=HONEY[3], height=0.8, smooth=0.4)
    cv.put(wall & (c.edge((~wall).astype(np.float32), 1) > 0) & (vo["dy"] > 0), color=HONEY[0])
    return cv.tex(wrap=True)


# ----------------------------------------------------------------- loom

def loom_top(ctx):
    c = ctx
    cv = planks_cv(c, OAK, "loomtop", boards=4)
    frame(cv, 0, 0, 16, 16, 2)
    warp = rect(c, 2, 2, 14, 14) & (np.floor(c.x) % 2 == 0)
    cv.put(rect(c, 2, 2, 14, 14), color=OAK[0] * 0.7, height=0.2)
    cv.put(warp, color=pal("e8e2d2")[0], height=0.55, porosity=0.6)
    cv.raised(rect(c, 2, 7, 14, 9), dh=0.1)
    return cv.tex(wrap=False)


def loom_front(ctx):
    c = ctx
    cv = planks_cv(c, OAK, "loomfront", boards=4)
    frame(cv, 0, 0, 16, 16, 2)
    cloth = rect(c, 3, 3, 13, 10)
    stripe = np.floor(c.y) % 4
    col = np.where((stripe < 2)[..., None], pal("b33a2e")[0], pal("e2d8c0")[0])
    weave = ((np.floor(c.x) + np.floor(c.y)) % 2 == 0)
    cv.put(cloth, color=col * np.where(weave, 1.0, 0.88)[..., None], height=0.6, porosity=0.6)
    threads = rect(c, 3, 10, 13, 13) & (np.floor(c.x) % 2 == 1)
    cv.put(rect(c, 3, 10, 13, 13), color=OAK[0] * 0.7, height=0.2)
    cv.put(threads, color=pal("e8e2d2")[0], height=0.5)
    cv.raised(rect(c, 2, 13, 14, 14), dh=0.1)
    return cv.tex(wrap=False)


def loom_side(ctx):
    c = ctx
    cv = planks_cv(c, OAK, "loomside", boards=4)
    frame(cv, 0, 0, 16, 16, 2)
    spool = c.circle(8, 8, 3.2) > 0
    cv.put(spool, color=pal("d8cfb8")[0], height=0.7, porosity=0.6)
    cv.put(spool & (np.floor(c.y) % 2 == 0), color=pal("bfb59c")[0])
    cv.put(c.circle(8, 8, 1.1) > 0, color=OAK[0], height=0.4)
    return cv.tex(wrap=False)


def loom_bottom(ctx):
    c = ctx
    cv = planks_cv(c, OAK, "loombot", boards=4)
    frame(cv, 0, 0, 16, 16, 1)
    cv.put(rect(c, 1, 1, 15, 15), mul=0.85)
    return cv.tex(wrap=False)


# ----------------------------------------------------------------- lectern

def lectern_base(ctx):
    c = ctx
    cv = planks_cv(c, OAK, "lecbase", boards=4)
    frame(cv, 0, 0, 16, 16, 1)
    return cv.tex(wrap=False)


def lectern_front(ctx):
    c = ctx
    cv = planks_cv(c, OAK, "lecfront", vertical=True, boards=3, joints=False)
    frame(cv, 0, 0, 16, 16, 1)
    cv.sunken(rect(c, 4, 3, 12, 13))
    cv.put(rect(c, 6, 5, 10, 11), color=OAK[4], height=0.55)
    cv.put(rect(c, 7, 6, 9, 10), color=OAK[0])
    return cv.tex(wrap=False)


def lectern_sides(ctx):
    c = ctx
    cv = planks_cv(c, OAK, "lecside", boards=4)
    frame(cv, 0, 0, 16, 16, 1)
    cv.put(rect(c, 0, 0, 16, 4), mul=0.85)
    cv.raised(rect(c, 0, 0, 16, 4), dh=0.05)
    return cv.tex(wrap=False)


def lectern_top(ctx):
    c = ctx
    cv = planks_cv(c, OAK, "lectop", vertical=True, boards=3, joints=False)
    frame(cv, 0, 0, 16, 16, 1)
    cv.raised(rect(c, 1, 13, 15, 15), dh=0.1)
    return cv.tex(wrap=False)


# ----------------------------------------------------------------- smithing table

def smithing(ctx, face):
    c = ctx
    if face == "top":
        cv = Canvas(c, IRON_P[1])
        n = c.noise(4, 2, salt="smt")
        cv.color[:] = c.palette(DARK_IRON[1:4], n * 0.6 + c.texel_noise("smt") * 0.4)
        cv.metal[:] = IRON
        cv.smooth[:] = 0.5
        cv.porosity[:] = 0
        cv.put(border(c, 2), color=c.palette(DARK[1:4], c.texel_noise("smr")), metal=0, smooth=0.2,
               porosity=0.2)
        cv.raised(border(c, 2), dh=0.05)
        cv.raised(rect(c, 4, 4, 12, 12), lit=1.25, dh=0.05)
        return cv.tex(wrap=False)
    cv = planks_cv(c, DARK, f"sm{face}", boards=4)
    if face == "bottom":
        frame(cv, 0, 0, 16, 16, 1)
        return cv.tex(wrap=False)
    iron(cv, rect(c, 0, 0, 16, 2), DARK_IRON)
    iron(cv, rect(c, 0, 14, 16, 16), DARK_IRON)
    nails(cv, [(2, 0), (13, 0), (2, 15), (13, 15)], IRON_P)
    if face == "front":
        # tongs and hammer on the front
        iron(cv, c.segment(3.5, 4, 6.5, 12, 1.1) + c.segment(6.5, 4, 3.5, 12, 1.1) > 0)
        cv.put(rect(c, 11, 6, 12, 13), color=OAK[2], height=0.7)
        iron(cv, rect(c, 9, 4, 14, 6))
    else:
        cv.sunken(rect(c, 3, 4, 13, 12))
        iron(cv, rect(c, 5, 7, 11, 9), IRON_P)
    return cv.tex(wrap=False)


# ----------------------------------------------------------------- fletching table

FEATHER = pal("9a9a92", "c9c9c0", "eeeee6")


def fletching(ctx, face):
    c = ctx
    cv = planks_cv(c, BIRCH, f"fl{face}", boards=4)
    if face == "top":
        frame(cv, 0, 0, 16, 16, 1)
        for x in (4, 8, 12):
            cv.put(rect(c, x, 2, x + 1, 14), color=OAK[1], height=0.7)
            cv.put(rect(c, x - 1, 2, x + 2, 4) & ~rect(c, x, 2, x + 1, 3), color=FEATHER[2], height=0.7)
            iron(cv, rect(c, x, 13, x + 1, 15))
        return cv.tex(wrap=False)
    cv.put(rect(c, 0, 0, 16, 3), color=c.palette(OAK[1:4], c.texel_noise("flb")), height=0.6)
    cv.raised(rect(c, 0, 0, 16, 3), dh=0.04)
    if face == "front":
        # a pinned feather
        f = c.polygon([(5, 13), (9, 4), (11, 5), (8, 13)]) > 0
        cv.put(f, color=c.palette(FEATHER, 1 - (c.y - 4) / 10), height=0.7)
        cv.put(c.segment(5, 14, 10.5, 4.5, 0.8) > 0, color=FEATHER[0])
    else:
        target = (c.circle(8, 9, 4.5) > 0)
        ring = np.floor(np.hypot(c.x - 8, c.y - 9) / 1.5) % 2
        cv.put(target, color=np.where((ring == 0)[..., None], pal("b5352a")[0], pal("e8e0cc")[0]),
               height=0.6, porosity=0.5)
    return cv.tex(wrap=False)


# ----------------------------------------------------------------- cartography table

MAPC = pal("6a8a4a", "8aa868", "c4b07c", "5a7ea8")


def cartography(ctx, face):
    c = ctx
    cv = planks_cv(c, DARK, f"ca{face}", boards=4)
    if face == "top":
        frame(cv, 0, 0, 16, 16, 1)
        paper = rect(c, 2, 2, 14, 14)
        n = c.noise(4, 2, salt="map")
        col = np.where((n < 0.35)[..., None], MAPC[3], np.where((n < 0.65)[..., None], MAPC[1], MAPC[2]))
        cv.put(paper, color=col * (0.95 + c.texel_noise("mp")[..., None] * 0.1), height=0.6, porosity=0.6)
        cv.put(paper & ((np.floor(c.x) % 4 == 1) | (np.floor(c.y) % 4 == 1)), mul=0.85)
        cv.put(border(c, 2) & rect(c, 1, 1, 15, 15), color=PAPER[2], height=0.6)
        return cv.tex(wrap=False)
    cv.put(rect(c, 0, 0, 16, 3), color=c.palette(OAK[1:4], c.texel_noise("cab")), height=0.6)
    cv.raised(rect(c, 0, 0, 16, 3), dh=0.04)
    if face == "side1":
        sheet = rect(c, 3, 5, 13, 13)
        cv.put(sheet, color=PAPER[2], height=0.6, porosity=0.6)
        cv.put(sheet & (np.floor(c.y) % 2 == 0) & rect(c, 4, 6, 12, 12), color=PAPER[0])
    elif face == "side2":
        cv.put(rect(c, 4, 6, 6, 14), color=PAPER[3], height=0.7)
        cv.put(rect(c, 7, 5, 9, 14), color=PAPER[2], height=0.7)
        cv.put(rect(c, 10, 7, 12, 14), color=PAPER[1], height=0.7)
    else:
        iron(cv, c.segment(4, 13, 8, 5, 1.0) + c.segment(12, 13, 8, 5, 1.0) > 0)
        cv.put(c.circle(8, 5, 1.0) > 0, color=pal("c09030")[0], height=0.8)
    return cv.tex(wrap=False)


# ----------------------------------------------------------------- note block / jukebox

NOTE = pal("3c2216", "5a3624", "6a412c", "784b33", "85553b", "906044")


def note_block(ctx):
    c = ctx
    cv = planks_cv(c, NOTE, "note", boards=4)
    frame(cv, 0, 0, 16, 16, 1)
    for x in range(3, 13, 3):
        for y in range(3, 13, 3):
            cv.put(rect(c, x, y, x + 2, y + 2), color=NOTE[0] * 0.5, height=0.1)
            cv.put(rect(c, x, y + 2, x + 2, y + 3), mul=1.15)
    return cv.tex(wrap=False)


def jukebox(ctx, top):
    c = ctx
    cv = planks_cv(c, NOTE, f"juke{top}", boards=4)
    m = border(c, 1)
    cv.put(m, color=c.palette(DARK[1:4], c.texel_noise("jb")), height=0.65)
    cv.raised(m, dh=0.04)
    if top:
        cv.sunken(rect(c, 3, 6, 13, 10), dh=-0.2, body=0.8)
        cv.put(rect(c, 4, 7, 12, 9), color=pal("140c08")[0], height=0.0)
    else:
        cv.sunken(rect(c, 3, 3, 13, 13), dh=-0.05, body=0.95)
        for x, y in ((2, 2), (13, 2), (2, 13), (13, 13)):
            cv.put(rect(c, x, y, x + 1, y + 1), color=pal("c09030")[0], metal=236 - 5, height=0.8)
    return cv.tex(wrap=False)


# ----------------------------------------------------------------- scaffolding / ladder

def bamboo_bar(cv, c, m, vertical):
    p = WOODS["bamboo"]["planks"]
    pos = c.x if vertical else c.y
    fr = pos - np.floor(pos)
    col = c.palette(p[1:], np.clip(0.6 + (c.texel_noise("sb") - 0.5) * 0.2, 0, 1))
    cv.put(m, color=col, alpha=1.0, height=0.7)
    e1 = c.edge(m.astype(np.float32), 1, "tl") > 0
    e2 = c.edge(m.astype(np.float32), 1, "br") > 0
    cv.put(m & e1, color=p[-1])
    cv.put(m & e2 & ~e1, color=p[0])


def scaffolding(ctx, face):
    c = ctx
    cv = Canvas(c, (0, 0, 0), alpha=0.0, height=0.0, porosity=0.2)
    rope = pal("5c4a2a", "7d6638", "9c8347")
    if face == "side":
        bamboo_bar(cv, c, rect(c, 0, 0, 2, 16), True)
        bamboo_bar(cv, c, rect(c, 14, 0, 16, 16), True)
        bamboo_bar(cv, c, rect(c, 2, 0, 14, 2), False)
        diag = (np.abs(np.floor(c.x) - np.floor(c.y)) <= 0.5) | (np.abs(np.floor(c.x) - np.floor(c.y) + 1) <= 0.5)
        diag &= rect(c, 2, 2, 14, 16)
        bamboo_bar(cv, c, diag, True)
        for y in (0, 14):
            cv.put(rect(c, 0, y, 2, y + 2) | rect(c, 14, y, 16, y + 2), color=rope[1], alpha=1.0)
    elif face == "top":
        bamboo_bar(cv, c, border(c, 2) & (rect(c, 0, 0, 16, 2) | rect(c, 0, 14, 16, 16)), False)
        bamboo_bar(cv, c, rect(c, 0, 2, 2, 14) | rect(c, 14, 2, 16, 14), True)
        for x in (4, 7, 10):
            bamboo_bar(cv, c, rect(c, x + 0.0, 2, x + 2, 14), True)
        for xy in ((0, 0), (14, 0), (0, 14), (14, 14)):
            cv.put(rect(c, xy[0], xy[1], xy[0] + 2, xy[1] + 2), color=rope[2], alpha=1.0)
    else:
        bamboo_bar(cv, c, rect(c, 0, 0, 16, 2) | rect(c, 0, 14, 16, 16), False)
        bamboo_bar(cv, c, rect(c, 0, 2, 2, 14) | rect(c, 14, 2, 16, 14), True)
    return cv.tex(wrap=False)


def ladder(ctx):
    c = ctx
    cv = Canvas(c, (0, 0, 0), alpha=0.0, height=0.0, porosity=0.2)
    p = OAK
    rails = rect(c, 2, 0, 4, 16) | rect(c, 12, 0, 14, 16)
    rungs = (rect(c, 4, 0, 12, 16)) & (np.floor(c.y) % 4 == 1)
    col = c.palette(p[2:], c.noise(2, 2, salt="lad", stretch=(1, 4)))
    cv.put(rails, color=col, alpha=1.0, height=0.7)
    cv.put(rails & (np.floor(c.x) % 10 == 2), mul=1.15)
    cv.put(rails & (np.floor(c.x) % 10 == 3), mul=0.82)
    colr = c.palette(p[1:], c.noise(2, 2, salt="rung", stretch=(4, 1)))
    cv.put(rungs, color=colr, alpha=1.0, height=0.65)
    cv.put(rungs & ((np.floor(c.x) == 4) | (np.floor(c.x) == 11)), color=p[0])
    under = np.roll(rungs, c.s, 0) & rails
    cv.put(under, mul=0.8)
    nails(cv, [(3, 1), (12, 1), (3, 5), (12, 5), (3, 9), (12, 9), (3, 13), (12, 13)])
    return cv.tex(wrap=False)


# ----------------------------------------------------------------- hay / straw

def hay_side(ctx):
    c = ctx
    g = c.lattice_noise(1.3, 16, "hay")
    f = c.noise(1, 2, salt="hayf", stretch=(1, 3))
    v = 0.5 + (g - 0.5) * 0.6 + (f - 0.5) * 0.3 + (c.texel_noise("ht") - 0.5) * 0.2
    cv = Canvas(c, c.palette(STRAW, np.clip(v, 0, 1)), height=0.5 + (g - 0.5) * 0.2, smooth=0.12, porosity=0.6)
    cv.put(c.texel_noise("hd", soft=False) > 0.92, color=STRAW[0], height=0.3)
    for y0 in (3, 11):
        band = rect(c, 0, y0, 16, y0 + 2)
        tw = (np.floor(c.x) + np.floor(c.y)) % 2 == 0
        cv.put(band, color=np.where(tw[..., None], TWINE[2], TWINE[1]), height=0.75, porosity=0.4)
        cv.put(rect(c, 0, y0 + 2, 16, y0 + 3), mul=0.8)
    return cv.tex(wrap=True)


def hay_top(ctx):
    c = ctx
    n = c.noise(2, 2, salt="haytop")
    g = c.texel_noise("haytop", soft=False)
    v = n * 0.4 + g * 0.6
    cv = Canvas(c, c.palette(STRAW, v), height=0.4 + v * 0.3, smooth=0.1, porosity=0.6)
    cv.put(g < 0.12, color=STRAW[0] * 0.8, height=0.2)
    cv.put(g > 0.92, color=STRAW[-1], height=0.75)
    for x0 in (3, 11):
        band = rect(c, x0, 0, x0 + 2, 16) & (border(c, 1))
        cv.put(band, color=TWINE[2], height=0.75)
    return cv.tex(wrap=True)


def straw_field(c, salt):
    g = c.lattice_noise(16, 1.3, f"st{salt}")
    f = c.noise(1, 2, salt=f"stf{salt}", stretch=(3, 1))
    v = 0.5 + (g - 0.5) * 0.5 + (f - 0.5) * 0.3 + (c.texel_noise(f"stt{salt}") - 0.5) * 0.25
    cv = Canvas(c, c.palette(STRAW, np.clip(v, 0, 1)), height=0.5 + (g - 0.5) * 0.2, smooth=0.12, porosity=0.6)
    weave = ((np.floor(c.x / 2) + np.floor(c.y / 2)) % 2 == 0) & (np.floor(c.y) % 2 == 0)
    cv.put(weave, mul=0.88, dh=-0.05)
    return cv


def straw_bed(ctx):
    c = ctx
    cv = straw_field(c, "bed")
    # darker woven edging every 16 texels so each bed face gets a rim
    cell = (np.floor(c.x) % 16 == 15) | (np.floor(c.y) % 16 == 15)
    cv.put(cell, color=TWINE[2], dh=-0.05)
    return cv.tex(wrap=False)


def straw_particle(ctx):
    return straw_field(ctx, "p").tex(wrap=True)


R = register
R("block/crafting_table_top", crafting_top)
R("block/crafting_table_front", lambda c: crafting_side(c, True))
R("block/crafting_table_side", lambda c: crafting_side(c, False))
R("block/bookshelf", bookshelf)
R("block/chiseled_bookshelf_empty", lambda c: chiseled(c, False))
R("block/chiseled_bookshelf_occupied", lambda c: chiseled(c, True))
R("block/chiseled_bookshelf_side", chiseled_side)
R("block/chiseled_bookshelf_top", chiseled_top)
R("block/barrel_side", barrel_side)
R("block/barrel_top", lambda c: barrel_top(c, "top"))
R("block/barrel_top_open", lambda c: barrel_top(c, "open"))
R("block/barrel_bottom", lambda c: barrel_top(c, "bottom"))
R("block/composter_side", composter_side)
R("block/composter_top", composter_top)
R("block/composter_bottom", composter_bottom)
R("block/composter_compost", lambda c: compost(c, False))
R("block/composter_ready", lambda c: compost(c, True))
R("block/beehive_side", beehive_side)
R("block/beehive_end", beehive_end)
R("block/beehive_front", lambda c: beehive_front(c, False))
R("block/beehive_front_honey", lambda c: beehive_front(c, True))
R("block/bee_nest_side", nest_side)
R("block/bee_nest_top", lambda c: nest_top(c, False))
R("block/bee_nest_bottom", lambda c: nest_top(c, True))
R("block/bee_nest_front", lambda c: nest_front(c, False))
R("block/bee_nest_front_honey", lambda c: nest_front(c, True))
for _f in ("top", "side", "bottom"):
    R(f"block/honey_block_{_f}", lambda c, f=_f: honey_block(c, f))
R("block/honeycomb_block", honeycomb_block)
R("block/loom_top", loom_top)
R("block/loom_front", loom_front)
R("block/loom_side", loom_side)
R("block/loom_bottom", loom_bottom)
R("block/lectern_base", lectern_base)
R("block/lectern_front", lectern_front)
R("block/lectern_sides", lectern_sides)
R("block/lectern_top", lectern_top)
for _f in ("top", "front", "side", "bottom"):
    R(f"block/smithing_table_{_f}", lambda c, f=_f: smithing(c, f))
for _f in ("top", "front", "side"):
    R(f"block/fletching_table_{_f}", lambda c, f=_f: fletching(c, f))
for _f in ("top", "side1", "side2", "side3"):
    R(f"block/cartography_table_{_f}", lambda c, f=_f: cartography(c, f))
R("block/note_block", note_block)
R("block/jukebox_top", lambda c: jukebox(c, True))
R("block/jukebox_side", lambda c: jukebox(c, False))
for _f in ("top", "side", "bottom"):
    R(f"block/scaffolding_{_f}", lambda c, f=_f: scaffolding(c, f))
R("block/ladder", ladder)
R("block/hay_block_side", hay_side)
R("block/hay_block_top", hay_top)
R("block/straw_bed", straw_bed)
R("block/straw_bed_particle", straw_particle)
