"""Materials and drops (h-z): ingots, nuggets, raw ores, gems, powders, mob drops.

Ingot / nugget / lump / powder geometry matches the item_1 materials so the
families line up across both work areas.
"""
import numpy as np

from ...registry import register, texture
from .common import IRON as IRON_P, LAPIS, QUARTZ, REDSTONE, WOOD, STRING, LEATHER
from .h_lib import (IRON, GOLD, COPPER, NETH, U, arc_pts, box, cells, circ, compose, dots, ell, flat_layer, grow,
                    inter, line, minus, paint, pal, poly, rgb, rod, rows_mask, spr, stroke)


def ingot(ctx, p, metal_id=None, smooth=0.75, porosity=0.0):
    top = poly(ctx, [(2.4, 8.4), (8.6, 4.6), (13.8, 7.0), (7.6, 10.8)])
    front = poly(ctx, [(1.4, 8.6), (7.6, 11.0), (7.6, 13.6), (1.4, 11.0)])
    end = poly(ctx, [(7.6, 11.0), (14.6, 7.0), (14.6, 9.6), (7.6, 13.6)])
    m = U(top, front, end, poly(ctx, [(1.4, 8.6), (8.6, 4.2), (14.6, 7.0), (7.6, 11.0)]))
    t = spr(ctx, m, p, bevel=1, smooth=smooth, porosity=porosity)
    ring = ctx.edge(m, 1) > 0
    paint(t, (top > 0.5) & ~ring, p[3])
    paint(t, (front > 0.5) & ~ring, p[2])
    paint(t, (end > 0.5) & ~ring, p[1])
    paint(t, (line(ctx, [(3.4, 8.2), (8.6, 5.2)], 0.8) > 0.5) & ~ring, p[4])
    paint(t, (line(ctx, [(2.4, 8.8), (7.4, 10.8)], 0.7) > 0.5) & ~ring, p[4])
    paint(t, (dots(ctx, [(9, 6)], 0.5) > 0.5) & ~ring, p[4])
    if metal_id:
        t.set_metal(m, metal_id)
    return t, m, ring


def nugget(ctx, p, metal_id=None):
    m = U(ell(ctx, 7.0, 9.0, 3.4, 2.6, 0.3), ell(ctx, 10.0, 8.0, 2.4, 2.0), ell(ctx, 8.4, 11.0, 2.6, 1.8))
    t = spr(ctx, m, p, bevel=1.5, smooth=0.75)
    ring = ctx.edge(m, 1) > 0
    paint(t, (dots(ctx, [(5, 7), (9, 6)], 0.5) > 0.5) & ~ring, p[4])
    paint(t, (dots(ctx, [(9, 11)], 0.5) > 0.5) & ~ring, p[1])
    if metal_id:
        t.set_metal(m, metal_id)
    return t


def lump(ctx, p, smooth=0.3, pts=None):
    pts = pts or [(2.4, 9.0), (4.0, 4.6), (8.0, 2.6), (12.4, 3.8), (14.0, 8.0), (12.6, 12.6), (8.0, 14.2), (4.0, 13.0)]
    m = poly(ctx, pts)
    t = spr(ctx, m, p, bevel=2.0, smooth=smooth)
    ring = ctx.edge(m, 1) > 0
    f = [(poly(ctx, [(4.0, 4.6), (8.0, 2.6), (8.6, 7.0), (4.6, 8.6)]), 3),
         (poly(ctx, [(8.0, 2.6), (12.4, 3.8), (11.4, 7.6), (8.6, 7.0)]), 2),
         (poly(ctx, [(8.6, 7.0), (11.4, 7.6), (12.6, 12.6), (8.0, 11.0)]), 1),
         (poly(ctx, [(4.6, 8.6), (8.6, 7.0), (8.0, 11.0), (4.0, 13.0)]), 2)]
    for fm, idx in f:
        paint(t, (fm > 0.5) & ~ring & (m > 0.5), p[idx])
    paint(t, (dots(ctx, [(5, 5), (9, 4)], 0.5) > 0.5) & ~ring, p[4])
    return t, m, ring


def powder(ctx, p, emissive=0.0, sparkle=None, salt="p"):
    m = U(ell(ctx, 8.0, 11.6, 6.4, 2.8), ell(ctx, 8.0, 9.6, 4.0, 3.0), ell(ctx, 7.4, 8.0, 2.0, 1.8))
    t = spr(ctx, m, p, bevel=2.5, porosity=0.9, emissive=emissive)
    ring = ctx.edge(m, 1) > 0
    n = ctx.texel_noise(salt)
    inner = (m > 0.5) & ~ring
    t.color[inner & (n < 0.15)] = p[1]
    t.color[inner & (n > 0.88)] = p[-1]
    grains = spr(ctx, dots(ctx, [(13, 7), (2, 9), (12, 4), (4, 6)], 0.55), p[1:], outline=False, bevel=1,
                 emissive=emissive)
    t = compose(ctx, t, grains)
    if sparkle is not None:
        paint(t, dots(ctx, [(6, 9), (9, 11), (8, 7)], 0.4), sparkle)
    return t


def shard(ctx, base, tip, w):
    bx, by = base
    tx, ty = tip
    dx, dy = tx - bx, ty - by
    n = np.hypot(dx, dy)
    nx, ny = -dy / n * w, dx / n * w
    return poly(ctx, [(bx + nx, by + ny), (tx - dx * 0.25 + nx, ty - dy * 0.25 + ny), (tx, ty),
                      (tx - dx * 0.25 - nx, ty - dy * 0.25 - ny), (bx - nx, by - ny)])


NETH_P = pal("161214", "2a2326", "3f3639", "564b4f", "73676b")
register("item/iron_ingot", lambda ctx: ingot(ctx, IRON_P, IRON)[0])
register("item/netherite_ingot", lambda ctx: ingot(ctx, NETH_P, NETH, 0.65)[0])
register("item/iron_nugget", lambda ctx: nugget(ctx, IRON_P, IRON))
register("item/nether_brick", lambda ctx: ingot(ctx, pal("1e0a0e", "341418", "4a1e22", "60282c", "7a363a"), None, 0.2, 0.5)[0])
register("item/resin_brick", lambda ctx: ingot(ctx, pal("6a2a06", "a8480e", "d06a1a", "e8902e", "f8b860"), None, 0.35, 0.2)[0])


def raw(ctx, p, spot, mid):
    t, m, ring = lump(ctx, p, 0.35, [(2.4, 10.0), (3.4, 5.6), (6.6, 3.0), (11.0, 3.2), (13.8, 6.4), (13.6, 11.0),
                                     (10.4, 13.8), (5.4, 13.6)])
    sp = (cells(ctx, [(5, 9), (6, 9), (10, 6), (9, 11), (10, 11), (7, 5)]) > 0.5) & ~ring
    paint(t, sp, rgb(spot))
    paint(t, (cells(ctx, [(5, 8), (10, 5), (9, 10)]) > 0.5) & ~ring, np.clip(rgb(spot) * 1.25, 0, 1))
    t.set_metal(sp.astype(np.float32), mid)
    return t


register("item/raw_iron", lambda ctx: raw(ctx, pal("4a3a2e", "7a6250", "a68a72", "c8ae94", "e2ccb4"), "d8d0c8", IRON))
register("item/raw_gold", lambda ctx: raw(ctx, pal("6a4a06", "a8780e", "d8a420", "f0c84a", "fbe48a"), "fff4a0", GOLD))
register("item/raw_copper", lambda ctx: raw(ctx, pal("5a2a14", "94482a", "c06a42", "dc8e64", "f0b48e"), "6ac0a0", COPPER))


@texture("item/netherite_scrap")
def netherite_scrap(ctx):
    p = pal("1a1210", "2e2220", "46342e", "5e4840", "7a6458")
    t, m, ring = lump(ctx, p, 0.45, [(2.4, 11.0), (3.6, 5.4), (8.4, 3.0), (13.0, 4.4), (13.8, 9.6), (11.4, 13.4),
                                     (5.6, 13.8)])
    for y0 in (6.0, 9.0, 12.0):
        paint(t, (line(ctx, [(3.6, y0 + 1.0), (12.6, y0 - 2.0)], 0.6) > 0.5) & ~ring, p[1])
    paint(t, (cells(ctx, [(6, 5), (10, 7), (7, 10)]) > 0.5) & ~ring, rgb("8a7a6e"))
    t.set_metal(m, NETH)
    return t


@texture("item/lapis_lazuli")
def lapis(ctx):
    p = LAPIS
    m = poly(ctx, [(3.0, 10.4), (4.4, 5.0), (8.6, 2.6), (12.6, 4.4), (13.6, 9.0), (11.0, 13.4), (6.0, 13.8)])
    t = spr(ctx, m, p, bevel=1.5, smooth=0.6, f0=0.06)
    ring = ctx.edge(m, 1) > 0
    paint(t, (poly(ctx, [(4.4, 5.0), (8.6, 2.6), (9.4, 6.4), (5.4, 8.6)]) > 0.5) & ~ring, p[3])
    paint(t, (poly(ctx, [(9.4, 6.4), (13.6, 9.0), (11.0, 13.4), (8.4, 10.6)]) > 0.5) & ~ring, p[1])
    paint(t, (cells(ctx, [(6, 10), (10, 5), (11, 10)]) > 0.5) & ~ring, rgb("e8c84a"))
    paint(t, (cells(ctx, [(6, 4), (5, 5)]) > 0.5) & ~ring, p[4])
    return t


@texture("item/quartz")
def quartz(ctx):
    p = QUARTZ
    big = poly(ctx, [(3.0, 12.0), (3.4, 6.0), (8.0, 2.0), (12.0, 3.0), (12.6, 7.4), (8.6, 13.6), (5.0, 14.0)])
    t = spr(ctx, big, p, bevel=1, smooth=0.85, f0=0.06)
    ring = ctx.edge(big, 1) > 0
    paint(t, (poly(ctx, [(3.4, 6.0), (8.0, 2.0), (9.0, 6.0), (5.4, 9.0)]) > 0.5) & ~ring, p[4])
    paint(t, (poly(ctx, [(9.0, 6.0), (12.6, 7.4), (8.6, 13.6), (7.6, 9.6)]) > 0.5) & ~ring, p[1])
    paint(t, (poly(ctx, [(5.4, 9.0), (9.0, 6.0), (7.6, 9.6), (5.0, 14.0)]) > 0.5) & ~ring, p[2])
    paint(t, (cells(ctx, [(5, 6), (6, 5)]) > 0.5) & ~ring, rgb("ffffff"))
    return t


PRIS = pal("1e4a44", "3a7a6e", "5aa494", "8acab8", "c4ece0")


@texture("item/prismarine_shard")
def prismarine_shard(ctx):
    m = poly(ctx, [(3.0, 13.0), (4.0, 7.6), (9.0, 2.4), (13.0, 2.6), (12.4, 6.4), (8.0, 11.4)])
    t = spr(ctx, m, PRIS, bevel=1.2, smooth=0.6)
    ring = ctx.edge(m, 1) > 0
    paint(t, (poly(ctx, [(4.0, 7.6), (9.0, 2.4), (10.0, 4.0), (5.6, 9.0)]) > 0.5) & ~ring, PRIS[3])
    paint(t, (line(ctx, [(5.0, 11.6), (11.6, 4.0)], 0.7) > 0.5) & ~ring, PRIS[1])
    return t


@texture("item/prismarine_crystals")
def prismarine_crystals(ctx):
    p = pal("2a5a5a", "5a9a92", "92d0c4", "c8f4e8", "f4fffc")
    layers = []
    for cx, cy, r in ((5.4, 5.6, 2.8), (11.0, 5.0, 2.4), (8.4, 10.6, 3.2), (3.6, 12.0, 1.8), (13.0, 11.4, 2.0)):
        m = poly(ctx, [(cx, cy - r), (cx + r * 0.8, cy), (cx, cy + r), (cx - r * 0.8, cy)])
        t = spr(ctx, m, p, bevel=1, smooth=0.9, f0=0.1, emissive=0.45)
        ring = ctx.edge(m, 1) > 0
        paint(t, (poly(ctx, [(cx, cy - r), (cx, cy), (cx - r * 0.8, cy)]) > 0.5) & ~ring, p[3])
        paint(t, (poly(ctx, [(cx, cy + r), (cx, cy), (cx + r * 0.8, cy)]) > 0.5) & ~ring, p[1])
        layers.append(t)
    out = compose(ctx, *layers)
    paint(out, cells(ctx, [(5, 4), (8, 9)]), p[4], emissive=0.8)
    return out


register("item/redstone", lambda ctx: powder(ctx, REDSTONE, 0.35, salt="rs"))
register("item/sugar", lambda ctx: powder(ctx, pal("9aa0aa", "ccd0d8", "e8eaee", "f6f7f8", "ffffff"),
                                          sparkle=rgb("ffffff"), salt="sg"))


@texture("item/heart_of_the_sea")
def heart_of_the_sea(ctx):
    shell = pal("0e2a2e", "1e4a4e", "2e6a6a", "4a8a84", "6aaaa0")
    core = pal("0a2a6a", "1a4ab0", "2a7ae0", "6ab4ff", "d0ecff")
    m = circ(ctx, 8, 8, 6.4)
    t = spr(ctx, m, shell, bevel=2, smooth=0.5)
    ring = ctx.edge(m, 1) > 0
    n = ctx.texel_noise("hots")
    paint(t, (m > 0.5) & ~ring & (n > 0.8), shell[3])
    cm = circ(ctx, 8, 8, 3.6)
    ct = spr(ctx, cm, core, bevel=2, smooth=0.95, f0=0.17, emissive=0.6, outline=False)
    out = compose(ctx, t, ct)
    paint(out, stroke(ctx, arc_pts(8, 8, 2.0, 180, 450, 12), 0.7), core[4], emissive=0.8)
    return out


@texture("item/nether_star")
def nether_star(ctx):
    p = pal("8a8aa0", "c4c4d8", "e6e6f4", "f8f8ff", "ffffff")
    pts = []
    import math
    for i in range(8):
        a = math.radians(-90 + i * 45)
        r = 7.2 if i % 2 == 0 else 2.6
        pts.append((8 + math.cos(a) * r, 8 + math.sin(a) * r))
    m = poly(ctx, pts)
    t = spr(ctx, m, p, bevel=1.5, smooth=0.8, emissive=0.7)
    paint(t, circ(ctx, 8, 8, 1.6), rgb("fffff0"), emissive=1.0)
    paint(t, cells(ctx, [(6, 6), (7, 4)]) * (1 - ctx.edge(m, 1)), p[4])
    return t


@texture("item/honeycomb")
def honeycomb(ctx):
    p = pal("7a4206", "c07410", "e89e1e", "f8c440", "fde68a")
    import math
    cents = [(5.0, 6.0), (9.6, 4.4), (8.0, 9.4), (12.4, 8.6), (4.6, 11.4), (10.4, 13.0)]
    hexes = []
    for cx, cy in cents:
        hexes.append(poly(ctx, [(cx + 2.6 * math.cos(math.radians(a)), cy + 2.6 * math.sin(math.radians(a)))
                                for a in range(0, 360, 60)]))
    m = U(*hexes)
    t = spr(ctx, m, p, bevel=1.5, smooth=0.6, sss=0.3)
    ring = ctx.edge(m, 1) > 0
    for h in hexes:
        paint(t, (ctx.edge(h, 1) > 0) & ~ring, p[1])
    paint(t, dots(ctx, [(4, 5), (9, 3), (7, 8)], 0.5) * (1 - ring), p[4])
    return t


@texture("item/ink_sac")
def ink_sac(ctx):
    p = pal("0e0e18", "1e1e2e", "2e2e44", "44445e", "62627e")
    m = U(ell(ctx, 8.0, 9.4, 5.0, 4.4), ell(ctx, 6.4, 5.6, 2.4, 2.4), line(ctx, [(10.6, 12.4), (12.4, 14.4)], 1.4))
    t = spr(ctx, m, p, bevel=2.5, smooth=0.6, sss=0.2)
    paint(t, cells(ctx, [(5, 7), (6, 6), (5, 4)]) * (1 - ctx.edge(m, 1)), p[4])
    return t


@texture("item/leather")
def leather(ctx):
    p = LEATHER
    m = poly(ctx, [(2.0, 4.0), (5.0, 2.6), (8.0, 3.6), (11.4, 2.4), (14.0, 4.4), (13.0, 8.0), (14.2, 12.0),
                   (11.0, 13.6), (8.0, 12.6), (4.6, 14.0), (2.0, 12.0), (3.0, 8.0)])
    t = spr(ctx, m, p, bevel=2, smooth=0.25, porosity=0.4)
    ring = ctx.edge(m, 1) > 0
    n = ctx.texel_noise("lea")
    paint(t, (m > 0.5) & ~ring & (n < 0.15), p[1])
    paint(t, (m > 0.5) & ~ring & (n > 0.9), p[4])
    return t


@texture("item/rabbit_hide")
def rabbit_hide(ctx):
    p = pal("5a4026", "8a6a44", "b0906a", "ccb08a", "e4ceae")
    m = poly(ctx, [(3.0, 5.0), (6.0, 3.6), (10.4, 3.6), (13.0, 5.4), (12.4, 9.0), (13.0, 12.4), (9.0, 13.0),
                   (6.0, 12.4), (3.0, 12.6), (3.6, 9.0)])
    t = spr(ctx, m, p, bevel=2, smooth=0.15, porosity=0.6)
    ring = ctx.edge(m, 1) > 0
    n = ctx.texel_noise("rh")
    paint(t, (m > 0.5) & ~ring & (n < 0.25), p[1])
    paint(t, (m > 0.5) & ~ring & (n > 0.8), p[4])
    return t


@texture("item/magma_cream")
def magma_cream(ctx):
    p = pal("4a1006", "8a2a0a", "d05a12", "f4962a", "ffd060")
    m = U(circ(ctx, 8, 9, 5.0), circ(ctx, 6.4, 6.6, 2.6))
    t = spr(ctx, m, p, bevel=3, smooth=0.6, emissive=0.3)
    ring = ctx.edge(m, 1) > 0
    cr = cells(ctx, [(7, 8), (8, 9), (9, 9), (10, 10), (6, 11), (5, 10), (10, 7)])
    paint(t, (cr > 0.5) & ~ring, p[1], emissive=0.0)
    paint(t, (cells(ctx, [(8, 8), (9, 10), (6, 10)]) > 0.5) & ~ring, p[4], emissive=0.9)
    return t


@texture("item/slime_ball")
def slime_ball(ctx):
    p = pal("2a6a1e", "4a9a32", "6ac44a", "9ae278", "d0ffb8")
    m = circ(ctx, 8, 8.6, 5.4)
    t = spr(ctx, m, p, bevel=3, smooth=0.85, sss=0.5)
    paint(t, circ(ctx, 8.6, 9.4, 2.4) * (1 - ctx.edge(m, 1)), p[1])
    paint(t, cells(ctx, [(5, 5), (6, 5), (5, 6)]), p[4])
    return t


@texture("item/snowball")
def snowball(ctx):
    p = pal("8aa0b4", "c4d4e4", "e2ecf4", "f4f8fc", "ffffff")
    m = circ(ctx, 8, 8.4, 5.4)
    t = spr(ctx, m, p, bevel=3, smooth=0.2, sss=0.5)
    n = ctx.texel_noise("snow")
    paint(t, (m > 0.5) & ~(ctx.edge(m, 1) > 0) & (n < 0.12), p[1])
    return t


@texture("item/nautilus_shell")
def nautilus_shell(ctx):
    p = pal("7a6a54", "b4a488", "d8ccb4", "eee6d4", "fcf8ee")
    m = U(circ(ctx, 8.6, 8.6, 5.6), ell(ctx, 4.4, 11.4, 2.4, 2.8))
    t = spr(ctx, m, p, bevel=2.5, smooth=0.7, f0=0.06)
    ring = ctx.edge(m, 1) > 0
    sp = stroke(ctx, arc_pts(8.6, 8.6, 3.4, -90, 220, 18), 0.8)
    paint(t, (sp > 0.5) & ~ring, p[1])
    stripes = U(*[line(ctx, [(8.6 + 5 * np.cos(a), 8.6 + 5 * np.sin(a)), (8.6 + 3.8 * np.cos(a), 8.6 + 3.8 * np.sin(a))], 0.8)
                  for a in np.radians([-60, -20, 20, 60, 100])])
    paint(t, (stripes > 0.5) & ~ring, rgb("a8603a"))
    paint(t, ell(ctx, 4.4, 11.6, 1.2, 1.6), p[0])
    return t


@texture("item/paper")
def paper(ctx):
    p = pal("8a8476", "c8c2b2", "e4dfd2", "f2eee4", "fcfaf4")
    m = poly(ctx, [(3.0, 3.0), (12.6, 2.0), (13.4, 12.6), (4.0, 14.0)])
    t = spr(ctx, m, p, bevel=1, smooth=0.1, porosity=0.7)
    ring = ctx.edge(m, 1) > 0
    paint(t, (poly(ctx, [(10.6, 13.0), (13.4, 12.6), (13.0, 10.0)]) > 0.5) & ~ring, p[1])
    for y in (5.6, 7.6, 9.6):
        paint(t, (line(ctx, [(5.0, y + 0.4), (11.0, y - 0.4)], 0.5) > 0.5) & ~ring, p[2])
    return t


@texture("item/phantom_membrane")
def phantom_membrane(ctx):
    p = pal("4a4a5a", "7a7a8e", "a8a8ba", "c8c8d8", "e6e6f0")
    m = poly(ctx, [(2.0, 4.0), (8.0, 2.4), (14.0, 3.6), (12.0, 7.0), (13.6, 12.0), (9.0, 11.0), (6.0, 14.0),
                   (5.0, 10.0), (2.4, 9.6), (4.0, 6.6)])
    t = spr(ctx, m, p, bevel=2, smooth=0.5, sss=0.6)
    ring = ctx.edge(m, 1) > 0
    veins = U(line(ctx, [(4.0, 5.0), (9.0, 8.0), (12.0, 11.0)], 0.6), line(ctx, [(9.0, 8.0), (12.0, 4.6)], 0.6),
              line(ctx, [(9.0, 8.0), (6.6, 12.4)], 0.6))
    paint(t, (veins > 0.5) & ~ring, p[1])
    t.color = np.where(((m > 0.5) & ~ring & ~(veins > 0.5))[..., None], t.color * np.array([0.92, 1.0, 0.95]), t.color)
    return t


@texture("item/rabbit_foot")
def rabbit_foot(ctx):
    p = pal("5a4026", "8a6a44", "b0906a", "ccb08a", "e4ceae")
    m = U(ell(ctx, 9.0, 7.0, 3.4, 4.6, 0.5), ell(ctx, 6.0, 11.6, 3.6, 2.4, 0.3))
    t = spr(ctx, m, p, bevel=2.5, smooth=0.15, porosity=0.6)
    claws = spr(ctx, cells(ctx, [(2, 12), (3, 13), (2, 10)]), pal("4a4440", "8a847a", "c8c2b4"), outline=False, bevel=1)
    paint(t, cells(ctx, [(9, 4), (8, 5)]), p[4])
    return compose(ctx, t, claws)


@texture("item/resin_clump")
def resin_clump(ctx):
    p = pal("6a2a06", "aa4a0e", "d8701a", "f09a34", "fcc870")
    m = U(circ(ctx, 6.6, 9.4, 3.6), circ(ctx, 10.0, 7.4, 3.2), circ(ctx, 9.4, 11.4, 2.6))
    t = spr(ctx, m, p, bevel=2.5, smooth=0.8, sss=0.3)
    paint(t, cells(ctx, [(5, 7), (9, 5), (10, 5)]), p[4])
    return t


@texture("item/shulker_shell")
def shulker_shell(ctx):
    p = pal("3a1e44", "6a3a78", "946296", "b688b4", "d8b0d4")
    m = rows_mask(ctx, ["....########....", "..############..", ".##############.", ".##############.",
                        ".##############.", "################", "################", "#####......#####",
                        "###..........###"], y0=3, round_=0.2)
    t = spr(ctx, m, p, bevel=2, smooth=0.55)
    ring = ctx.edge(m, 1) > 0
    paint(t, (box(ctx, 0.0, 8.0, 16.0, 9.0) > 0.5) & ~ring, p[1])
    paint(t, (box(ctx, 1.0, 9.0, 15.0, 10.0) > 0.5) & ~ring, p[4])
    paint(t, (cells(ctx, [(5, 5), (6, 5), (4, 6), (10, 6), (11, 7)]) > 0.5) & ~ring, p[4])
    return t


register("item/stick", lambda ctx: rod(ctx, [(3.4, 13.0), (13.0, 3.4)], 1.6, WOOD, porosity=0.2))


@texture("item/string")
def string(ctx):
    """A small hank of string: looped coil with a loose tail."""
    loops = U(stroke(ctx, arc_pts(8.0, 7.6, 4.6, 0, 360, 28), 1.1), stroke(ctx, arc_pts(8.4, 8.2, 3.2, 20, 380, 22), 1.0),
              stroke(ctx, arc_pts(7.6, 7.0, 3.8, 200, 520, 24), 0.9))
    tail = stroke(ctx, [(10.6, 11.4), (12.0, 13.0), (11.0, 14.4), (12.6, 15.2)], 1.0)
    t = spr(ctx, U(loops, tail), STRING, outline=False, bevel=1, smooth=0.2)
    paint(t, ctx.edge(U(loops, tail), 1, "br") > 0, STRING[0])
    return t


@texture("item/turtle_scute")
def turtle_scute(ctx):
    p = pal("1e4a14", "2e6e20", "46942e", "6ab448", "9ad470")
    import math
    m = poly(ctx, [(8 + 6 * math.cos(math.radians(a)), 8.4 + 5.2 * math.sin(math.radians(a))) for a in range(-90, 270, 60)])
    t = spr(ctx, m, p, bevel=2, smooth=0.55)
    ring = ctx.edge(m, 1) > 0
    inner = poly(ctx, [(8 + 3 * math.cos(math.radians(a)), 8.4 + 2.6 * math.sin(math.radians(a))) for a in range(-90, 270, 60)])
    paint(t, (ctx.edge(inner, 1) > 0) & ~ring, p[1])
    paint(t, cells(ctx, [(6, 5), (5, 6)]), p[4])
    return t


@texture("item/wind_charge")
def wind_charge(ctx):
    p = pal("4a5a8a", "7a8ac4", "a8b8e8", "d0dcff", "f4f8ff")
    m = circ(ctx, 8, 8, 5.2)
    t = spr(ctx, m, p, bevel=2.5, smooth=0.6, sss=0.3)
    sw = U(stroke(ctx, arc_pts(8, 8, 3.4, 200, 380, 12), 0.8), stroke(ctx, arc_pts(8, 8, 1.8, 20, 220, 10), 0.8))
    paint(t, sw * (1 - ctx.edge(m, 1)), p[4])
    tails = U(stroke(ctx, arc_pts(8, 8, 6.4, 120, 170, 6), 0.8), stroke(ctx, arc_pts(8, 8, 6.4, 300, 350, 6), 0.8))
    tt = spr(ctx, tails, p[1:], outline=False, bevel=1)
    return compose(ctx, tt, t)


EGG_SHELL = pal("8a8a6a", "c4c4a4", "e2e2c8", "f2f2e2", "fcfcf4")


@texture("item/turtle_egg")
def turtle_egg(ctx):
    a = ell(ctx, 6.0, 10.0, 3.0, 3.8)
    b = ell(ctx, 11.0, 9.4, 2.6, 3.4)
    ta = spr(ctx, a, EGG_SHELL, bevel=2, smooth=0.4)
    tb = spr(ctx, b, EGG_SHELL, bevel=2, smooth=0.4)
    for t, sp in ((ta, [(5, 8), (7, 11), (4, 11)]), (tb, [(11, 8), (10, 10), (12, 11)])):
        paint(t, cells(ctx, sp), rgb("5a9a3a"))
    return compose(ctx, tb, ta)


@texture("item/sniffer_egg")
def sniffer_egg(ctx):
    p = pal("4a1a10", "7a2e1e", "a8442e", "c8664a", "e08e6e")
    m = ell(ctx, 8.0, 8.8, 5.0, 6.2)
    t = spr(ctx, m, p, bevel=3, smooth=0.4)
    ring = ctx.edge(m, 1) > 0
    sp = cells(ctx, [(6, 5), (9, 7), (7, 10), (10, 11), (5, 8), (8, 13)])
    paint(t, (sp > 0.5) & ~ring, rgb("3a8a5a"))
    paint(t, cells(ctx, [(6, 4), (5, 5)]), p[4])
    return t
