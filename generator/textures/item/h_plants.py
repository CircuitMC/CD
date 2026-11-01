"""Plant and growth items (h-z): seeds, crops, aquatic plants, flowers, spikes."""
import math

import numpy as np

from ...registry import register, texture
from .h_lib import (U, arc_pts, box, cells, circ, compose, curve, dots, ell, inter, line, minus, paint, pal, poly,
                    rgb, spr, stroke)

LEAF = pal("1a4210", "2c6e1a", "44a02a", "76cc46", "a8e270")
STALK = pal("2e4a14", "4a7020", "6a9a30", "8ec048")


def seeds(ctx, p, spots, shape=(2.3, 1.6), hi=None):
    layers = []
    for x, y, a in spots:
        layers.append(spr(ctx, ell(ctx, x, y, shape[0], shape[1], a), p, bevel=1, smooth=0.3))
    t = compose(ctx, *layers)
    paint(t, dots(ctx, [(int(x - 1), int(y - 1)) for x, y, _ in spots], 0.45), p[-1] if hi is None else hi)
    return t


SPOTS = ((5.0, 6.0, 0.4), (10.4, 5.4, -0.6), (7.4, 10.6, 1.2), (11.4, 11.0, 0.2), (4.6, 12.0, -0.3))
register("item/wheat_seeds", lambda ctx: seeds(ctx, pal("1e3a10", "36601c", "54862c", "7cae44"), SPOTS))
register("item/melon_seeds", lambda ctx: seeds(ctx, pal("140e0a", "2a1e14", "443222", "604a34"),
                                               ((5.0, 5.6, 0.8), (10.6, 6.4, -0.4), (6.4, 11.0, 0.2), (11.6, 11.6, 1.0))))
register("item/pumpkin_seeds", lambda ctx: seeds(ctx, pal("8a7a50", "c4b484", "e2d6aa", "f6eed2"),
                                                 ((5.0, 5.6, 0.8), (10.6, 6.4, -0.4), (6.4, 11.0, 0.2), (11.6, 11.6, 1.0)),
                                                 (2.4, 1.5)))
register("item/torchflower_seeds", lambda ctx: seeds(ctx, pal("3a1a0a", "6a3414", "9a5422", "c47a3a"),
                                                     ((5.6, 6.0, 0.0), (10.0, 6.8, 0.0), (7.6, 11.0, 0.0)), (1.8, 1.8),
                                                     rgb("f0a03a")))


@texture("item/wheat")
def wheat(ctx):
    gp = pal("5a4210", "8e6c20", "c4a038", "e2c45a", "f4e090")
    stems = U(line(ctx, [(3.0, 14.0), (9.0, 6.0)], 0.9), line(ctx, [(5.0, 14.6), (11.6, 7.0)], 0.9),
              line(ctx, [(2.0, 12.4), (6.6, 4.6)], 0.9))
    ts = spr(ctx, stems, gp[:4], outline=False, bevel=1)
    heads = U(ell(ctx, 10.6, 4.6, 2.0, 3.4, 0.7), ell(ctx, 13.0, 5.6, 1.8, 3.0, 0.8), ell(ctx, 7.6, 3.0, 1.8, 2.8, 0.5))
    th = spr(ctx, heads, gp, bevel=1.5, porosity=0.3)
    ring = ctx.edge(heads, 1) > 0
    paint(th, (dots(ctx, [(10, 3), (12, 5), (7, 2), (10, 5)], 0.45) > 0.5) & ~ring, gp[1])
    return compose(ctx, ts, th)


KELP = pal("102a10", "1e4a1a", "2e6a24", "468e32", "68b048")


@texture("item/kelp")
def kelp(ctx):
    stem = stroke(ctx, [(8.0, 15.0), (7.0, 11.0), (9.0, 7.0), (7.6, 3.0), (8.6, 0.8)], 1.2)
    leaves = U(ell(ctx, 5.6, 10.0, 2.6, 1.2, 0.6), ell(ctx, 10.6, 7.6, 2.6, 1.2, -0.6), ell(ctx, 5.6, 4.6, 2.4, 1.1, 0.5),
               ell(ctx, 10.4, 12.4, 2.2, 1.0, -0.5))
    t = spr(ctx, U(stem, leaves), KELP, bevel=1.2, sss=0.4)
    paint(t, cells(ctx, [(9, 4), (8, 9), (12, 11)]), rgb("a8a030"))  # air bladders
    return t


@texture("item/seagrass")
def seagrass(ctx):
    p = pal("143a14", "246024", "3a8a30", "5aae44", "86d066")
    m = U(curve(ctx, (5.0, 15.0), (3.4, 9.0), (5.0, 3.0), 1.4, 0.6), curve(ctx, (8.0, 15.0), (9.6, 8.0), (7.6, 1.4), 1.6, 0.6),
          curve(ctx, (11.0, 15.0), (12.6, 10.0), (11.0, 5.0), 1.4, 0.6))
    return spr(ctx, m, p, outline=False, bevel=1, sss=0.4)


@texture("item/sugar_cane")
def sugar_cane(ctx):
    p = pal("3a5a1e", "5e8a30", "86b448", "aed46a", "d4f094")
    layers = []
    for x0, y0, y1 in ((4.0, 3.0, 15.0), (8.0, 1.0, 15.0), (11.6, 5.0, 15.0)):
        m = box(ctx, x0, y0, x0 + 2.0, y1)
        t = spr(ctx, m, p, bevel=1)
        for y in np.arange(y0 + 3, y1, 4):
            paint(t, box(ctx, x0, y, x0 + 2.0, y + 1), p[1])
        layers.append(t)
    lv = spr(ctx, U(line(ctx, [(10.0, 8.0), (13.6, 2.4)], 0.9), line(ctx, [(6.0, 10.0), (2.4, 6.0)], 0.9)), p, outline=False,
             bevel=1)
    return compose(ctx, lv, *layers)


@texture("item/nether_sprouts")
def nether_sprouts(ctx):
    p = pal("0e3a34", "1a5e54", "2a8a78", "46b49c", "7adcc4")
    m = U(line(ctx, [(4.0, 14.0), (3.0, 8.0)], 1.0), line(ctx, [(7.0, 14.0), (7.6, 6.0)], 1.0),
          line(ctx, [(10.0, 14.0), (12.0, 7.6)], 1.0), line(ctx, [(12.6, 14.0), (13.6, 11.0)], 1.0),
          line(ctx, [(5.6, 14.0), (5.0, 11.0)], 1.0))
    return spr(ctx, m, p, outline=False, bevel=1)


@texture("item/nether_wart")
def nether_wart(ctx):
    p = pal("3a060c", "6e0e18", "9a1c26", "c4343a", "e06060")
    layers = []
    for x, y, r in ((6.0, 8.0, 3.0), (10.6, 7.0, 2.6), (8.4, 11.4, 3.0)):
        t = spr(ctx, circ(ctx, x, y, r), p, bevel=2, porosity=0.3)
        paint(t, dots(ctx, [(int(x - 1), int(y - 1)), (int(x + 1), int(y))], 0.45), p[1])
        layers.append(t)
    stem = spr(ctx, line(ctx, [(8.0, 3.0), (8.6, 6.0)], 1.0), pal("3a060c", "6e0e18", "9a1c26"), outline=False, bevel=1)
    return compose(ctx, stem, *layers)


def petals(ctx, colors, centers, leaf=True):
    layers = []
    if leaf:
        layers.append(spr(ctx, U(line(ctx, [(8.0, 15.0), (8.0, 9.0)], 0.9), ell(ctx, 5.0, 13.0, 2.4, 1.0, 0.5),
                                 ell(ctx, 11.0, 12.6, 2.4, 1.0, -0.5)), LEAF, outline=False, bevel=1))
    for (x, y), c in zip(centers, colors):
        pp = pal(*c) if isinstance(c, tuple) else c
        m = U(circ(ctx, x - 1.0, y, 1.2), circ(ctx, x + 1.0, y, 1.2), circ(ctx, x, y - 1.0, 1.2), circ(ctx, x, y + 1.0, 1.2))
        t = spr(ctx, m, pp, bevel=1, sss=0.3)
        paint(t, cells(ctx, [(int(x), int(y))]), rgb("f4d040"))
        layers.append(t)
    return compose(ctx, *layers)


PINK = ("8a3a5a", "c46a8e", "eaa0be", "fcd0e2")
register("item/pink_petals", lambda ctx: petals(ctx, [PINK] * 4, [(5.0, 5.0), (10.6, 4.4), (4.6, 10.0), (10.6, 9.6)]))
register("item/wildflowers", lambda ctx: petals(ctx, [("8a7a0a", "c8b020", "f0d840", "fff48a"),
                                                      ("8a8a8a", "c4c4c4", "eeeeee", "ffffff"),
                                                      ("6a3a8a", "9a62b8", "c494e0", "e8c8f8"),
                                                      ("8a7a0a", "c8b020", "f0d840", "fff48a")],
                                                [(5.0, 5.0), (11.0, 4.0), (4.6, 10.4), (11.4, 9.6)]))


@texture("item/leaf_litter")
def leaf_litter(ctx):
    layers = []
    cols = [pal("4a2a0a", "7a4a16", "a86a26", "c88e40"), pal("5a3a0a", "8a6018", "b48a2a", "d2ae4a"),
            pal("3a1e0a", "6a3414", "8e4e22", "b06e36")]
    for i, (x, y, a) in enumerate(((5.0, 5.0, 0.6), (11.0, 6.0, -0.4), (6.0, 11.0, -0.8), (11.0, 11.6, 0.3))):
        m = ell(ctx, x, y, 3.0, 1.8, a)
        t = spr(ctx, m, cols[i % 3], bevel=1, porosity=0.4)
        c, s = math.cos(a), math.sin(a)
        paint(t, (line(ctx, [(x - 2 * c, y - 2 * s), (x + 2 * c, y + 2 * s)], 0.5) > 0.5) & ~(ctx.edge(m, 1) > 0),
              cols[i % 3][1])
        layers.append(t)
    return compose(ctx, *layers)


@texture("item/mangrove_propagule")
def mangrove_propagule(ctx):
    pod = pal("2a3a10", "4a6a1a", "6a9228", "92b844")
    m = U(ell(ctx, 8.0, 10.0, 1.6, 4.6), poly(ctx, [(6.8, 13.0), (9.2, 13.0), (8.0, 15.6)]))
    t = spr(ctx, m, pod, bevel=1, sss=0.2)
    top = spr(ctx, U(ell(ctx, 6.0, 4.0, 2.4, 1.2, 0.5), ell(ctx, 10.0, 4.0, 2.4, 1.2, -0.5), box(ctx, 7.4, 3.0, 8.6, 6.0)),
              LEAF, bevel=1)
    return compose(ctx, top, t)


@texture("item/pitcher_pod")
def pitcher_pod(ctx):
    p = pal("2a3a14", "46602a", "6a8a3e", "92b45a", "bcd884")
    m = U(ell(ctx, 8.0, 9.6, 3.6, 4.6), poly(ctx, [(6.0, 6.0), (10.0, 6.0), (8.0, 2.0)]))
    t = spr(ctx, m, p, bevel=2, porosity=0.3)
    ring = ctx.edge(m, 1) > 0
    paint(t, (line(ctx, [(8.0, 5.0), (8.0, 13.0)], 0.6) > 0.5) & ~ring, p[1])
    paint(t, (cells(ctx, [(6, 8), (6, 9)]) > 0.5) & ~ring, p[4])
    paint(t, cells(ctx, [(7, 14), (8, 14)]), rgb("6a3a8a"))
    return t


@texture("item/pitcher_plant")
def pitcher_plant(ctx):
    leaf = U(curve(ctx, (8.0, 15.0), (3.0, 11.0), (3.4, 5.0), 1.6, 0.8), curve(ctx, (8.0, 15.0), (13.0, 11.0), (12.6, 5.0), 1.6, 0.8))
    tl = spr(ctx, leaf, LEAF, bevel=1)
    cup = U(poly(ctx, [(5.4, 3.0), (10.6, 3.0), (10.0, 11.0), (8.0, 13.0), (6.0, 11.0)]))
    cp = pal("2a1a4a", "4a2e7a", "6e4aa8", "9a76cc", "c4a8ec")
    tc = spr(ctx, cup, cp, bevel=1.5, sss=0.3)
    paint(tc, box(ctx, 6.0, 3.0, 10.0, 4.0), cp[0])
    paint(tc, (cells(ctx, [(6, 6), (6, 7), (9, 9)]) > 0.5) & ~(ctx.edge(cup, 1) > 0), rgb("4ab4a0"))
    return compose(ctx, tl, tc)


@texture("item/sea_pickle")
def sea_pickle(ctx):
    p = pal("2e4a14", "4a6e20", "6a9430", "8eb84a", "b8dc78")
    layers = []
    for x, y0, h in ((5.0, 7.0, 7.0), (10.0, 5.0, 9.0)):
        m = U(box(ctx, x, y0 + 1, x + 3, y0 + h), box(ctx, x + 0.5, y0, x + 2.5, y0 + h + 0.5))
        t = spr(ctx, m, p, bevel=1.2, sss=0.4)
        paint(t, cells(ctx, [(int(x) + 1, int(y0) + 2), (int(x) + 1, int(y0) + 4)]), p[4])
        glow = spr(ctx, box(ctx, x + 1, y0 - 1.6, x + 2, y0), pal("8a9a40", "d0e070", "f8ffb0"), outline=False, bevel=1,
                   emissive=0.8)
        layers += [t, glow]
    return compose(ctx, *layers)


def spike(ctx, p, extra=None, emissive=0.0):
    m = poly(ctx, [(5.2, 1.0), (10.8, 1.0), (10.0, 5.0), (8.8, 10.0), (8.0, 15.4), (7.2, 10.0), (6.0, 5.0)])
    t = spr(ctx, m, p, bevel=1.5, porosity=0.4, emissive=emissive)
    ring = ctx.edge(m, 1) > 0
    for y in (4.0, 7.0, 10.0):
        paint(t, (box(ctx, 0, y, 16, y + 0.8) > 0.5) & (m > 0.5) & ~ring, p[1])
    paint(t, (line(ctx, [(6.6, 3.0), (7.4, 9.0)], 0.6) > 0.5) & ~ring, p[-1])
    return t


register("item/pointed_dripstone", lambda ctx: spike(ctx, pal("3a2a20", "5e4636", "80624c", "a08068", "bca088")))
register("item/sulfur_spike", lambda ctx: spike(ctx, pal("5a5010", "908220", "c0b03a", "dcd060", "f0e898")))
