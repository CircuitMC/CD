"""Grasses, ferns, bushes, shrubs, sugar cane, lily pad, vine, leaf litter, bamboo, cactus,
azalea, mangrove propagules, flower pot."""
import math

import numpy as np

from ...engine import Tex, hexc, pal
from ...materials import leaves as leaves_mat
from ...registry import register, texture
from .plants_common import (DRY, LEAF, STEM, WOODY, Canvas, blade, borrowed, curve, ellipse, gray_of,
                            grays, leaf, leaf_spray, petals, px, radial, shift, stalk, union, vgrad)

G = grays(6, 0.45, 0.9)          # tinted foliage
GD = grays(6, 0.40, 0.82)
PINK_FLOWER = pal("7a2e5e", "a2447e", "c45e9c", "de82b8", "f0aad2")
CACTUS = pal("1c3a14", "27501a", "336620", "407c28", "4f9232", "62a83e")
CACTUS_FLESH = pal("6e8a3a", "86a24a", "9eb85c", "b4cc70")
TERRACOTTA = pal("5a2c1a", "6e3720", "824228", "954e30", "a65b38", "b66a44")


# ---------------------------------------------------------------- grasses

def tuft(ctx, rng, n, x0, x1, top_range, width=(1.6, 2.4), y0=16.6, lean=1.0):
    m = ctx.zeros()
    for i in range(n):
        bx = x0 + (x1 - x0) * (i + rng.uniform(0.1, 0.9)) / n
        top = rng.uniform(*top_range)
        tx = bx + (bx - 8) * 0.35 * lean + rng.uniform(-1.5, 1.5)
        m = np.maximum(m, blade(ctx, (bx, y0), (tx, top), rng.uniform(*width), bend=rng.uniform(-0.7, 0.7)))
    return m


def grass_canvas(ctx, mask, p, salt, top=0, sss=0.55):
    c = Canvas(ctx)
    c.add(mask, p, shade=vgrad(ctx, top, 16, 0.14, -0.18), noise=0.22, light=0.22, sss=sss, salt=salt)
    return c.done()


@texture("block/short_grass")
def short_grass(ctx):
    rng = ctx.rng("sg")
    m = union(tuft(ctx, rng, 7, 1.5, 14.5, (2.5, 9), (1.5, 2.2)), tuft(ctx, rng, 4, 4, 12, (6, 11), (1.4, 2.0)))
    return grass_canvas(ctx, m, G, "sg", 3)


@texture("block/tall_grass_bottom")
def tall_grass_bottom(ctx):
    rng = ctx.rng("tgb")
    m = ctx.zeros()
    for i in range(7):
        bx = 1.5 + i * 2.1 + rng.uniform(-0.4, 0.4)
        tx = bx + (bx - 8) * 0.25 + rng.uniform(-0.8, 0.8)
        m = np.maximum(m, stalk(ctx, bx, 16.6, tx, -0.6, rng.uniform(1.4, 2.0), rng.uniform(-0.8, 0.8)))
    m = np.maximum(m, tuft(ctx, rng, 5, 2, 14, (5, 10)))
    return grass_canvas(ctx, m, G, "tgb", -2)


@texture("block/tall_grass_top")
def tall_grass_top(ctx):
    rng = ctx.rng("tgb")  # continue the same stems
    m = ctx.zeros()
    for i in range(7):
        bx = 1.5 + i * 2.1 + rng.uniform(-0.4, 0.4)
        tx0 = bx + (bx - 8) * 0.25 + rng.uniform(-0.8, 0.8)
        rng.uniform(1.4, 2.0), rng.uniform(-0.8, 0.8)
        top = rng.uniform(1.5, 9)
        m = np.maximum(m, blade(ctx, (tx0, 16.8), (tx0 + (tx0 - 8) * 0.3 + rng.uniform(-1, 1), top), 1.9,
                                bend=rng.uniform(-0.8, 0.8)))
    return grass_canvas(ctx, m, G, "tgt", 2)


def frond(ctx, base, tip, bend, leaflet=2.2, width=1.2, n=6):
    """Fern frond: curved rachis with alternating leaflets shrinking toward the tip."""
    bx, by = base
    tx, ty = tip
    mx, my = (bx + tx) / 2 + bend, (by + ty) / 2 - abs(bend) * 0.3
    pts = [((1 - t) ** 2 * bx + 2 * (1 - t) * t * mx + t * t * tx,
            (1 - t) ** 2 * by + 2 * (1 - t) * t * my + t * t * ty) for t in np.linspace(0, 1, 13)]
    m = curve(ctx, pts, 1.0, 0.8)
    for i in range(1, n + 1):
        t = i / (n + 1)
        k = int(t * 12)
        (x1, y1), (x2, y2) = pts[k], pts[min(12, k + 1)]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        size = leaflet * (1 - t * 0.6)
        for s in (1, -1):
            off = 0.3 if s == 1 else -0.3
            tipx = x1 + (nx * s * 0.85 + dx / L * 0.5) * size
            tipy = y1 + (ny * s * 0.85 + dy / L * 0.5) * size
            m = np.maximum(m, leaf(ctx, (x1 + dx / L * off, y1 + dy / L * off), (tipx, tipy), width, fat=0.35))
    return m


@texture("block/fern")
def fern(ctx):
    m = union(frond(ctx, (8, 16.5), (2.0, 4.0), -1.5, 2.6), frond(ctx, (8, 16.5), (14.2, 5.0), 1.5, 2.6),
              frond(ctx, (8, 16.5), (8.5, 1.5), 0.6, 2.4, n=7), frond(ctx, (8, 16.5), (3, 13), -0.5, 1.6, n=3),
              frond(ctx, (8, 16.5), (13.5, 12.5), 0.5, 1.6, n=3))
    return grass_canvas(ctx, m, G, "fern", 2)


@texture("block/large_fern_bottom")
def large_fern_bottom(ctx):
    m = union(frond(ctx, (8, 16.5), (1.0, 2.0), -1.2, 3.0, 1.4, 7), frond(ctx, (8, 16.5), (15.0, 3.0), 1.2, 3.0, 1.4, 7),
              frond(ctx, (8, 16.5), (7.0, -2.0), 0.8, 2.8, 1.3, 8), frond(ctx, (8, 16.5), (2.5, 12.5), -0.6, 1.9, 1.2, 3),
              frond(ctx, (8, 16.5), (13.5, 12.0), 0.6, 1.9, 1.2, 3))
    return grass_canvas(ctx, m, G, "lfb", 0)


@texture("block/large_fern_top")
def large_fern_top(ctx):
    m = union(frond(ctx, (7.0, 17.0), (4.5, 1.5), -0.8, 2.7, 1.3, 7), frond(ctx, (9.5, 17.0), (13.5, 4.0), 1.0, 2.6, 1.3, 6),
              frond(ctx, (2.0, 17.0), (0.5, 10), -0.3, 1.8, 1.2, 3), frond(ctx, (14.0, 17.0), (15.5, 10.5), 0.3, 1.8, 1.2, 3))
    return grass_canvas(ctx, m, G, "lft", 1)


@texture("block/bush")
def bush(ctx):
    c = Canvas(ctx)
    rng = ctx.rng("bush")
    c.add(union(stalk(ctx, 7.5, 16.5, 5, 9, 1, -0.5), stalk(ctx, 8.5, 16.5, 11, 8, 1, 0.5)), GD, light=0.2, salt="bs")
    m = leaf_spray(ctx, rng, 34, 2.5, 3.5, 13.5, 15.5, length=(2.4, 3.6), width=(1.9, 2.6), up=0.4)
    c.add(m, G, shade=vgrad(ctx, 2, 16, 0.12, -0.15), noise=0.2, salt="bl")
    return c.done()


def twigs(ctx, rng, x, y, ang, length, width, depth, out):
    x2, y2 = x + math.cos(ang) * length, y + math.sin(ang) * length
    out.append(ctx.segment(x, y, x2, y2, width))
    if depth > 0:
        for s in (-1, 1):
            if rng.random() < 0.88:
                twigs(ctx, rng, x2, y2, ang + s * rng.uniform(0.35, 0.75), length * rng.uniform(0.55, 0.78),
                      max(0.9, width * 0.75), depth - 1, out)


def shrub(ctx, p, salt, n=3, spread=1.0, top_len=5.0):
    rng = ctx.rng(salt)
    out = []
    for i in range(n):
        a = -math.pi / 2 + (i - (n - 1) / 2) * 0.55 * spread + rng.uniform(-0.15, 0.15)
        twigs(ctx, rng, 8 + (i - (n - 1) / 2) * 0.8, 16.5, a, top_len * rng.uniform(0.8, 1.1), 1.4, 3, out)
    m = union(*out)
    c = Canvas(ctx)
    c.add(m, p, light=0.25, noise=0.2, shade=vgrad(ctx, 2, 16, 0.12, -0.12), sss=0.2, salt=salt)
    return c.done()


register("block/dead_bush", lambda ctx: shrub(ctx, DRY, "deadbush", 3, 1.1))
register("block/red_shrub", lambda ctx: shrub(ctx, pal("3a1810", "4e2216", "642d1c", "7a3a24", "90482c"),
                                              "redshrub", 4, 0.9, 4.4))


def dry_grass(ctx, tall):
    rng = ctx.rng("dry" + str(tall))
    if tall:
        m = union(tuft(ctx, rng, 8, 1, 15, (0.5, 6), (1.4, 2.0)), tuft(ctx, rng, 4, 3, 13, (5, 10), (1.3, 1.8)))
    else:
        m = tuft(ctx, rng, 7, 2, 14, (7, 12), (1.4, 2.0), lean=1.5)
    c = Canvas(ctx)
    c.add(m, DRY, shade=vgrad(ctx, 0 if tall else 6, 16, 0.18, -0.15), noise=0.25, light=0.2, sss=0.35, salt="dg")
    if tall:  # seed heads
        heads = ctx.zeros()
        for x, y in ((3.5, 2.0), (10.5, 1.0), (13.5, 4.0)):
            heads = np.maximum(heads, ellipse(ctx, x, y, 0.8, 1.6, 0.2))
        c.add(heads * (ctx.y < 6), shift(DRY, 0.15), salt="dgh")
    return c.done()


register("block/short_dry_grass", lambda ctx: dry_grass(ctx, False))
register("block/tall_dry_grass", lambda ctx: dry_grass(ctx, True))


# ---------------------------------------------------------------- sugar cane, lily pad, vine, leaf litter

@texture("block/sugar_cane")
def sugar_cane(ctx):
    c = Canvas(ctx)
    stalks = ((3.0, 2, 0), (8.5, 2, 5), (13.0, 2, 10))
    for x, w, node in stalks:
        m = ctx.rect(x - w / 2, 0, x + w / 2, 16)
        ny = ((ctx.y - node) % 6 < 1).astype(np.float32)
        c.add(m, G, light=0.25, noise=0.12, shade=-0.0, sss=0.5, salt=f"sc{x}", bevel=1)
        c.recolor(m * ny, G[1])
        c.recolor(m * ((ctx.y - node) % 6 >= 5) * ctx.rect(x - w / 2, 0, x - w / 2 + 1, 16), G[5])
    lv = union(leaf(ctx, (3.5, 6.5), (6.5, 2.5), 1.4, bend=0.4), leaf(ctx, (9.5, 11.5), (11.5, 8.0), 1.3),
               leaf(ctx, (12.5, 16.0), (10.5, 13.0), 1.3), leaf(ctx, (2.5, 13), (0.3, 9.5), 1.3))
    c.add(lv, G, light=0.2, salt="scl")
    return c.done()


@texture("block/lily_pad")
def lily_pad(ctx):
    d, a = radial(ctx, 8, 8)
    notch = (np.abs(((a - 0.6) + math.pi) % (2 * math.pi) - math.pi) < 0.3) & (d > 0.8)
    pad = ((d < 7.4) & ~notch).astype(np.float32)
    vein = (np.abs(np.sin(a * 3.5 + 0.4)) < 0.16) & (d > 1.5) & (d < 6.5)
    c = Canvas(ctx)
    c.add(pad, G, outline=True, light=0.15, noise=0.15, shade=(d / 7.4) * -0.12 + 0.06, sss=0.4, bevel=3, salt="lp")
    c.recolor(vein.astype(np.float32), G[2])
    c.recolor(ctx.rect(7.5, 7.5, 8.5, 8.5), G[2])
    return c.done()


def _wrap_union(ctx, fn):
    m = ctx.zeros()
    for oy in (-16, 0, 16):
        for ox in (-16, 0, 16):
            m = np.maximum(m, fn(ox, oy))
    return m


@texture("block/vine")
def vine(ctx):
    rng = ctx.rng("vine")
    paths = []
    for i, x in enumerate((2.5, 9.0, 13.5)):
        pts = []
        for k in range(9):
            y = k * 2
            pts.append((x + math.sin(k * 0.9 + i * 2) * 1.6, y))
        paths.append(pts)
    stems = _wrap_union(ctx, lambda ox, oy: union(*[curve(ctx, [(px_ + ox, py + oy) for px_, py in p], 1.0)
                                                   for p in paths]))
    leaves_at = []
    for i, p in enumerate(paths):
        for k in range(0, 8, 2):
            x, y = p[k]
            s = 1 if (k + i) % 4 < 2 else -1
            leaves_at.append((x, y, s, rng.uniform(1.8, 2.5)))

    def lv(ox, oy):
        m = ctx.zeros()
        for x, y, s, L in leaves_at:
            m = np.maximum(m, leaf(ctx, (x + ox, y + oy), (x + s * L * 1.5 + ox, y + 1.2 + oy), L * 1.1, fat=0.5))
        return m
    leafm = _wrap_union(ctx, lv)
    c = Canvas(ctx)
    c.add(stems, GD, light=0.2, salt="vs")
    c.add(leafm, G, light=0.3, noise=0.18, salt="vl")
    t = c.done()
    t.wrap = True
    return t


@texture("block/leaf_litter")
def leaf_litter(ctx):
    rng = ctx.rng("litter")
    c = Canvas(ctx)
    for qi, (qx, qy) in enumerate(((0, 0), (8, 0), (0, 8), (8, 8))):
        for k in range(4):
            cx, cy = qx + rng.uniform(2, 6), qy + rng.uniform(2, 6)
            a = rng.uniform(0, 2 * math.pi)
            L = rng.uniform(3.6, 5.0)
            b = (cx - math.cos(a) * L / 2, cy - math.sin(a) * L / 2)
            t = (cx + math.cos(a) * L / 2, cy + math.sin(a) * L / 2)
            m = leaf(ctx, b, t, L * 0.62, fat=0.45) * ctx.rect(qx, qy, qx + 8, qy + 8)
            p = grays(6, 0.42 + k * 0.04, 0.82 + k * 0.03)
            c.add(m, p, outline=True, light=0.3, noise=0.2, sss=0.3, salt=f"ll{qi}{k}")
            c.recolor(ctx.segment(*b, *t, 0.7) * m, p[1])
    return c.done()


# ---------------------------------------------------------------- firefly bush

FIREFLY_BUSH = pal("1b2c16", "243a1c", "2e4a22", "3a5c29", "486e31", "58823a")
FIREFLIES = [(3.5, 3.5), (12.5, 2.5), (6.5, 7.5), (13.5, 9.5), (2.5, 10.5), (9.5, 4.5), (10.5, 12.5)]


@texture("block/firefly_bush")
def firefly_bush(ctx):
    rng = ctx.rng("ffb")
    c = Canvas(ctx)
    out = []
    for i in range(3):
        twigs(ctx, rng, 7 + i, 16.5, -math.pi / 2 + (i - 1) * 0.5, 5, 1.2, 2, out)
    c.add(union(*out), WOODY, light=0.2, salt="ffs")
    c.add(leaf_spray(ctx, rng, 30, 2, 3, 14, 15, length=(2.2, 3.4), width=(1.6, 2.3), up=0.3), FIREFLY_BUSH,
          shade=vgrad(ctx, 2, 16, 0.12, -0.12), noise=0.2, salt="ffl")
    return c.done()


@texture("block/firefly_bush_emissive")
def firefly_bush_emissive(ctx):
    c = Canvas(ctx)
    f = ctx.frame
    m = ctx.zeros()
    for i, (x, y) in enumerate(FIREFLIES):
        on = ((f + i * 3) % 10) < 4 + (i % 2)
        if on:
            dx = round(math.sin((f + i) * 0.9) * 0.6)
            dy = round(math.cos((f * 0.7 + i)) * 0.6)
            m = np.maximum(m, ctx.rect(math.floor(x) + dx, math.floor(y) + dy, math.floor(x) + dx + 1,
                                       math.floor(y) + dy + 1))
    c.add(m, pal("c8e040", "e8f870", "fbffb0"), noise=0, light=0, emissive=1.0, sss=0, salt="ff")
    return c.done()


# ---------------------------------------------------------------- bamboo

BAMBOO = pal("2c4a12", "3a6018", "4c7a1e", "5e9226", "74a832", "8cbc44")
BAMBOO_LEAF = pal("244a14", "2f601a", "3c7822", "4c902a", "60a636")


@texture("block/bamboo_stalk")
def bamboo_stalk(ctx):
    col = ctx.x % 4
    edge = np.where(col < 1, 0.85, np.where(col >= 3, 0.15, 0.55))
    node = (ctx.y % 8) < 1
    v = edge + (ctx.texel_noise("bam") - 0.5) * 0.15 + (ctx.noise(4, 1, salt="bam", stretch=(1, 4)) - 0.5) * 0.15
    color = ctx.palette(BAMBOO, np.clip(v, 0, 1))
    color = np.where(node[..., None], ctx.palette(shift(BAMBOO, -0.2), np.clip(v, 0, 1)), color)
    return Tex(ctx, color, height=np.where(node, 0.7, 0.4 + edge * 0.2), smooth=0.35, sss=0.3)


@texture("block/bamboo_stage0")
def bamboo_stage0(ctx):
    c = Canvas(ctx)
    c.add(ctx.polygon([(7, 16.5), (7.2, 9), (8, 5), (8.8, 9), (9, 16.5)]), BAMBOO, light=0.3, salt="sh")
    c.add(union(leaf(ctx, (8, 9), (4.5, 5.5), 1.6, bend=0.4), leaf(ctx, (8, 7.5), (11.5, 4.0), 1.6, bend=-0.4)),
          BAMBOO_LEAF, salt="shl")
    c.recolor(ctx.rect(7, 12, 9, 13), BAMBOO[1])
    return c.done()


def bamboo_leaves(ctx, specs):
    c = Canvas(ctx)
    m = ctx.zeros()
    for bx, by, tx, ty, w, b in specs:
        m = np.maximum(m, leaf(ctx, (bx, by), (tx, ty), w * 1.35, bend=b, fat=0.35))
    c.add(m, BAMBOO_LEAF, outline=True, light=0.3, salt="bl")
    return c.done()


register("block/bamboo_singleleaf", lambda ctx: bamboo_leaves(ctx, [(8, 15, 3.0, 4.0, 2.6, 1.0)]))
register("block/bamboo_small_leaves", lambda ctx: bamboo_leaves(ctx, [
    (8, 14, 2.0, 6.0, 2.4, 0.8), (8, 12, 13.5, 3.0, 2.4, -0.8), (8, 16, 12.5, 12.0, 2.0, -0.5)]))
register("block/bamboo_large_leaves", lambda ctx: bamboo_leaves(ctx, [
    (8, 15, 1.0, 9.0, 2.8, 1.0), (8, 13, 3.5, 1.0, 2.8, 0.8), (8, 12, 12.5, 0.5, 2.8, -0.8),
    (8, 14, 15.0, 8.0, 2.8, -1.0), (8, 16, 11.5, 15.5, 2.0, 0.3)]))


# ---------------------------------------------------------------- cactus

def spines(ctx, cells):
    return px(ctx, cells)


@texture("block/cactus_side")
def cactus_side(ctx):
    rib = np.cos((ctx.x - 1.0) / 4 * 2 * math.pi)
    v = 0.5 + rib * 0.28 + (ctx.texel_noise("cs") - 0.5) * 0.18 + (ctx.noise(4, 1, salt="cs", stretch=(1, 3)) - 0.5) * 0.12
    v = np.where((ctx.tx == 0) | (ctx.tx == 15), 0.08, v)
    color = ctx.palette(CACTUS, np.clip(v, 0, 1))
    t = Tex(ctx, color, height=0.45 + rib * 0.2, smooth=0.3, sss=0.25, porosity=0.1, wrap=False)
    sp = [(x + ((y // 4) % 2) * 0, y) for x in (3, 7, 11) for y in (2, 6, 10, 14)]
    sp = [(x + (1 if (y // 4) % 2 else 0) * (1 if x < 11 else 0), y) for x, y in sp]
    m = spines(ctx, sp) > 0
    t.color[m] = hexc("e8e2b8")
    t.color[(px(ctx, [(x + 1, y + 1) for x, y in sp]) > 0) & ~m] = CACTUS[0]
    t.height[m] = 0.9
    return t


def cactus_cap(ctx, top):
    d, a = radial(ctx, 8, 8)
    sq = np.maximum(np.abs(ctx.x - 8), np.abs(ctx.y - 8))
    rib = np.cos(a * 8) * (d > 2.5)
    v = 0.55 + rib * 0.15 * top + (ctx.texel_noise("ct") - 0.5) * 0.2 - (sq > 7) * 0.45 - (sq > 6) * (sq <= 7) * 0.12
    color = ctx.palette(CACTUS, np.clip(v, 0, 1))
    inner = d < 2.6
    color = np.where(inner[..., None], ctx.palette(CACTUS_FLESH, np.clip(0.5 + (ctx.texel_noise("cf") - 0.5) * 0.6, 0, 1)),
                     color)
    t = Tex(ctx, color, height=0.5 + rib * 0.1, smooth=0.3, sss=0.25, wrap=False)
    if top:
        sp = px(ctx, [(4, 4), (11, 4), (4, 11), (11, 11), (8, 2), (2, 7), (13, 8), (7, 13)]) > 0
        t.color[sp] = hexc("e8e2b8")
    return t


register("block/cactus_top", lambda ctx: cactus_cap(ctx, 1))
register("block/cactus_bottom", lambda ctx: cactus_cap(ctx, 0))


# ---------------------------------------------------------------- azalea

AZ_LEAF = pal("2e4a1a", "3b5e20", "4a7228", "5a8630", "6c9a3a", "80ae48")


def _az_side_fallback(ctx):
    rng = ctx.rng("azs")
    edge = 9 + np.array([rng.uniform(-1.5, 1.5) for _ in range(16)])
    m = (ctx.y < edge[ctx.tx % 16]).astype(np.float32)
    c = Canvas(ctx)
    c.add(m, AZ_LEAF, noise=0.35, light=0.15, salt="azs", bevel=2)
    return c.done()


def _az_top_fallback(ctx):
    t = leaves_mat(ctx, count=16, holes=0.0, tint=False, color=AZ_LEAF[3], salt="aztop")
    t.alpha[:] = 1
    return t


def add_blossoms(ctx, tex, salt, count=7, only_opaque=True, size=1.0):
    rng = ctx.rng(f"bloss{salt}")
    pts = []
    for _ in range(count * 30):
        if len(pts) >= count:
            break
        x, y = rng.uniform(1, 15), rng.uniform(1, 15)
        if all(math.hypot(x - a, y - b) > 3.4 for a, b in pts):
            pts.append((x, y))
    c = Canvas(ctx)
    for i, (x, y) in enumerate(pts):
        f = petals(ctx, x, y, 4, 1.6 * size, 1.5 * size, rot=rng.uniform(0, 1.5), inner=0)
        c.add(f, PINK_FLOWER, light=0.3, noise=0.1, salt=f"b{i}")
        c.recolor(ctx.rect(math.floor(x), math.floor(y), math.floor(x) + 1, math.floor(y) + 1), hexc("f4d260"))
    fl = c.done()
    m = fl.alpha > 0.5
    if only_opaque:
        m &= tex.alpha > 0.5
    tex.paste(fl, m.astype(np.float32))
    return tex


def flowering(ctx, base_path, fallback, salt, count=7):
    t = borrowed(ctx, base_path, fallback)
    t.wrap = False
    return add_blossoms(ctx, t, salt, count)


register("block/flowering_azalea_side", lambda ctx: flowering(ctx, "block/azalea_side", _az_side_fallback, "fs", 6))
register("block/flowering_azalea_top", lambda ctx: flowering(ctx, "block/azalea_top", _az_top_fallback, "ft", 7))
register("block/potted_azalea_bush_side", lambda ctx: borrowed(ctx, "block/azalea_side", _az_side_fallback))
register("block/potted_azalea_bush_top", lambda ctx: borrowed(ctx, "block/azalea_top", _az_top_fallback))
register("block/potted_flowering_azalea_bush_side",
         lambda ctx: flowering(ctx, "block/azalea_side", _az_side_fallback, "pfs", 6))
register("block/potted_flowering_azalea_bush_top",
         lambda ctx: flowering(ctx, "block/azalea_top", _az_top_fallback, "pft", 7))


def _az_leaves_fallback(ctx):
    return leaves_mat(ctx, count=14, tint=False, color=AZ_LEAF[3], salt="azl")


@texture("block/flowering_azalea_leaves")
def flowering_azalea_leaves(ctx):
    t = borrowed(ctx, "block/azalea_leaves", _az_leaves_fallback)
    return add_blossoms(ctx, t, "fal", 6)


@texture("block/azalea_plant", "block/potted_azalea_bush_plant", "block/potted_flowering_azalea_bush_plant")
def azalea_plant(ctx):
    rng = ctx.rng("azp")
    out = []
    for x, a in ((7.0, -1.85), (8.5, -1.25), (8.0, -1.6)):
        twigs(ctx, rng, x, 16.5, a, 6, 1.8, 2, out)
    c = Canvas(ctx)
    c.add(union(*out), WOODY, light=0.3, noise=0.2, sss=0.1, salt="azp")
    return c.done()


# ---------------------------------------------------------------- mangrove propagule

PROP_POD = pal("2c3a14", "3c4e1a", "4f6422", "647a2c", "7a9036")


@texture("block/mangrove_propagule")
def mangrove_propagule(ctx):
    c = Canvas(ctx)
    c.add(ctx.polygon([(7.3, 16.5), (7.0, 11), (7.6, 7), (8.4, 7), (9.0, 11), (8.7, 16.5)]), PROP_POD,
          light=0.3, salt="pod")
    lv = union(leaf(ctx, (8, 7.5), (3.0, 3.5), 2.8, bend=0.3), leaf(ctx, (8, 7.5), (13.0, 3.0), 2.8, bend=-0.3),
               leaf(ctx, (8, 7.5), (8.6, 1.0), 2.4))
    c.add(lv, LEAF, outline=True, light=0.3, salt="pl")
    return c.done()


@texture("block/mangrove_propagule_hanging")
def mangrove_propagule_hanging(ctx):
    c = Canvas(ctx)
    c.add(stalk(ctx, 8, -0.5, 8, 4.5, 1.0, 0.2), STEM, salt="hs")
    c.add(union(leaf(ctx, (8, 4.5), (3.5, 2.0), 2.4, bend=-0.3), leaf(ctx, (8, 4.5), (12.5, 2.0), 2.4, bend=0.3)),
          LEAF, outline=True, salt="hl")
    c.add(ellipse(ctx, 8, 6.0, 1.6, 1.4), pal("4a5a1a", "60721e", "788c28", "90a634"), salt="cap")
    c.add(ctx.polygon([(7.1, 6.5), (8.9, 6.5), (8.7, 13.5), (8, 15.5), (7.3, 13.5)]), PROP_POD, light=0.3,
          salt="hpod")
    return c.done()


# ---------------------------------------------------------------- flower pot

@texture("block/flower_pot")
def flower_pot(ctx):
    n = ctx.noise(4, 2, 0.5, salt="pot")
    v = 0.45 + (n - 0.5) * 0.3 + (ctx.texel_noise("pot") - 0.5) * 0.2
    v = v + np.where(ctx.ty == 10, 0.25, 0) + np.where(ctx.ty == 11, -0.15, 0) + np.where(ctx.ty >= 15, -0.15, 0)
    return Tex(ctx, ctx.palette(TERRACOTTA, np.clip(v, 0, 1)), height=0.5 + (ctx.ty == 10) * 0.2,
               smooth=0.25, porosity=0.5, wrap=False)
