"""Food items (h-z). Shapes follow the item_1 food designs (raw/cooked pairs,
bowls, fish) so pairs split across both work areas match."""
import numpy as np

from ...registry import register, texture
from .h_lib import (U, arc_pts, box, cells, circ, compose, dots, ell, inter, line, minus, paint, pal, poly, rgb,
                    spr, stroke)

BONE = pal("8a8270", "c8c0aa", "e8e2d0", "fbf8ee")
POTATO_SKIN = pal("5a3a16", "8a6028", "b48a44", "d2ae62", "e8cc88")
POISON_SKIN = pal("3a4a12", "5e7220", "849a34", "a8bc50", "cadc7a")
MELON_RIND = pal("1a3a0e", "2e6418", "4c9228", "78b840")
MELON_FLESH = pal("8a1414", "c42a26", "e8483a", "fa7a62")
EYE = pal("3a060c", "6e0e18", "a4202a", "d04a4a", "f08a80")
BOWL = pal("3a2210", "5e3a1c", "84562c", "a8763e", "c89656")
LEAF = pal("1a4210", "2c6e1a", "44a02a", "76cc46")


def chop(ctx, p, rim, bone=True, marbling=None):
    """bone=True: lamb rib chop (round eye of meat, fat rim, long rib bone).
    bone=False: pork chop (broad slab with a thick fat cap along the top and a small bone eye).
    Signature kept stable: item_1's cooked variants call this and sear the result."""
    layers = []
    if bone:
        meat = poly(ctx, [(1.6, 10.0), (2.4, 6.0), (5.0, 3.6), (8.6, 3.6), (11.0, 5.6), (11.6, 9.0), (9.6, 12.6),
                          (6.0, 14.2), (3.0, 13.4)])
        eye = ell(ctx, 6.4, 8.8, 3.4, 3.2)
        b = U(line(ctx, [(9.6, 6.6), (13.6, 2.6)], 2.0), circ(ctx, 14.0, 2.2, 1.4))
        layers.append(spr(ctx, b, BONE, bevel=1))
    else:
        meat = poly(ctx, [(1.4, 6.0), (4.0, 3.0), (9.0, 2.4), (13.6, 3.6), (14.8, 7.4), (13.4, 12.0), (9.0, 13.8),
                          (4.0, 13.6), (1.6, 11.0)])
        eye = poly(ctx, [(2.6, 7.6), (5.0, 6.0), (10.0, 5.6), (13.4, 7.0), (13.0, 10.8), (9.0, 12.8), (4.4, 12.6),
                         (2.6, 10.6)])
    tm = spr(ctx, meat, p, bevel=2.5, sss=0.15)
    ring = ctx.edge(meat, 1) > 0
    paint(tm, (minus(meat, eye) > 0.5) & ~ring, rim)                       # fat rim / cap
    paint(tm, (ctx.edge(eye, 1, "tl") > 0) & (meat > 0.5) & ~ring, p[-1])  # moist highlight on the cut
    if marbling is not None:
        pts = [(5, 7), (7, 9), (5, 10), (8, 7)] if bone else [(5, 8), (8, 7), (10, 9), (6, 10), (11, 7)]
        paint(tm, (dots(ctx, pts, 0.45) > 0.5) & (eye > 0.5) & ~ring, marbling)
    if not bone:  # small round bone eye in the corner of the pork chop
        paint(tm, circ(ctx, 11.6, 9.6, 1.1) > 0.5, BONE[2])
        paint(tm, cells(ctx, [(11, 9)]) > 0.5, BONE[3])
    return compose(ctx, *layers, tm)


register("item/mutton", lambda ctx: chop(ctx, pal("4e0c14", "8a1e24", "b8383a", "d65a56", "ee8a80"),
                                         rgb("f0dcd0"), True, rgb("e8b0a8")))
register("item/porkchop", lambda ctx: chop(ctx, pal("5e1e26", "9e4048", "c8646a", "e08888", "f4aca8"),
                                           rgb("fbeee6"), False, rgb("f8c8c4")))


@texture("item/rabbit")
def rabbit(ctx):
    p = pal("4e1418", "903a3c", "c06060", "dc8682", "f2b0a8")
    m = U(ell(ctx, 7.0, 7.6, 5.2, 3.8, -0.6), ell(ctx, 10.4, 11.0, 3.4, 2.4, -0.9))
    t = spr(ctx, m, p, bevel=2.5, sss=0.15)
    ring = ctx.edge(m, 1) > 0
    paint(t, (line(ctx, [(4.6, 9.4), (8.4, 5.0)], 0.8) > 0.5) & ~ring, rgb("f2dcd4"))
    paint(t, (dots(ctx, [(4, 5), (5, 4)]) > 0.5) & ~ring, p[4])
    bone = spr(ctx, U(line(ctx, [(11.6, 12.4), (14.0, 14.4)], 1.5), circ(ctx, 14.2, 14.2, 1.1)), BONE, bevel=1)
    return compose(ctx, bone, t)


def fish(ctx, body_p, belly, fin_p=None, stripes=None):
    body = U(ell(ctx, 7.0, 8.4, 6.0, 4.4), poly(ctx, [(11.0, 7.0), (14.2, 3.8), (15.4, 4.4), (13.6, 8.4),
                                                       (15.4, 12.4), (14.2, 13.0), (11.0, 9.8)]))
    t = spr(ctx, body, body_p, bevel=2.0, smooth=0.5)
    ring = ctx.edge(body, 1) > 0
    paint(t, (inter(ell(ctx, 6.6, 11.0, 4.6, 1.8), body) > 0.5) & ~ring, belly)
    if stripes is not None:
        for x in (6.4, 9.6):
            paint(t, (box(ctx, x, 0, x + 1.2, 16) > 0.5) & (body > 0.5) & ~ring, stripes)
    paint(t, dots(ctx, [(3, 7)], 0.6), rgb("101010"))
    paint(t, (line(ctx, [(5.0, 6.6), (5.6, 10.0)], 0.6) > 0.5) & ~ring, body_p[1])
    fin = spr(ctx, poly(ctx, [(5.0, 4.8), (8.6, 2.6), (10.0, 5.2)]), fin_p if fin_p is not None else body_p, bevel=1)
    return compose(ctx, fin, t)


register("item/salmon", lambda ctx: fish(ctx, pal("3a1010", "7a2622", "a84038", "cc6450", "e88e76"),
                                         rgb("e8a890"), pal("1e3a2e", "3a6a54", "5a8a70")))
register("item/tropical_fish", lambda ctx: fish(ctx, pal("6a2406", "c04e12", "ec7a22", "f8a446", "ffd08a"),
                                                rgb("fff2e0"), pal("8a6a06", "d8b020", "f8e060"), rgb("f8f4ee")))


@texture("item/pufferfish")
def pufferfish(ctx):
    p = pal("6a4a06", "b08410", "e2b828", "f6da5c", "fff2a8")
    body = circ(ctx, 8.0, 8.6, 5.0)
    t = spr(ctx, body, p, bevel=2.5, smooth=0.5)
    ring = ctx.edge(body, 1) > 0
    paint(t, (inter(ell(ctx, 8.0, 11.0, 4.0, 2.0), body) > 0.5) & ~ring, rgb("f4eed4"))
    paint(t, cells(ctx, [(5, 7), (10, 7)]), rgb("101010"))
    paint(t, (cells(ctx, [(6, 10), (9, 10), (7, 5), (11, 9), (4, 9)]) > 0.5) & ~ring, rgb("3a8a96"))
    spikes = spr(ctx, cells(ctx, [(8, 2), (2, 8), (13, 6), (3, 4), (12, 3), (14, 10), (2, 12)]),
                 pal("8a8460", "d8d2a8", "f4f0d8"), outline=False, bevel=1)
    fins = spr(ctx, poly(ctx, [(12.6, 11.0), (15.0, 13.0), (12.0, 13.4)]), p, bevel=1)
    return compose(ctx, spikes, fins, t)


def potato(ctx, skin, eyes, spots=None):
    m = ell(ctx, 8.0, 9.0, 6.0, 4.6, -0.35)
    t = spr(ctx, m, skin, bevel=2.5, porosity=0.4)
    ring = ctx.edge(m, 1) > 0
    paint(t, (dots(ctx, [(5, 8), (9, 11), (11, 7)]) > 0.5) & ~ring, eyes)
    paint(t, (dots(ctx, [(5, 6), (6, 5)], 0.5) > 0.5) & ~ring, skin[4])
    if spots is not None:
        paint(t, (dots(ctx, [(7, 9), (10, 9), (4, 10), (8, 12)], 0.5) > 0.5) & ~ring, spots)
    return t


register("item/potato", lambda ctx: potato(ctx, POTATO_SKIN, POTATO_SKIN[1]))
register("item/poisonous_potato", lambda ctx: potato(ctx, POISON_SKIN, POISON_SKIN[1], rgb("6a8a1e")))


@texture("item/spider_eye")
def spider_eye(ctx):
    eye = circ(ctx, 8.0, 8.6, 5.0)
    t = spr(ctx, eye, EYE, bevel=2.5, sss=0.2, smooth=0.7)
    paint(t, circ(ctx, 7.0, 9.2, 2.0), rgb("1a0a0e"))
    paint(t, dots(ctx, [(6, 8)], 0.45), rgb("e8b0b0"))
    paint(t, cells(ctx, [(5, 5), (6, 4)]), EYE[4])
    return t


@texture("item/melon_slice")
def melon_slice(ctx):
    rind = minus(circ(ctx, 8.0, 3.0, 12.0), circ(ctx, 8.0, 1.6, 10.4), box(ctx, 0, 0, 16, 4.0))
    rind = inter(rind, poly(ctx, [(8, 3.0), (-6, 16), (22, 16)]))
    flesh = minus(inter(circ(ctx, 8.0, 1.6, 10.6), poly(ctx, [(8, 3.0), (-4.6, 14.6), (20.6, 14.6)])),
                  box(ctx, 0, 0, 16, 4.0))
    tr = spr(ctx, U(rind, flesh), MELON_RIND, bevel=1)
    tf = spr(ctx, flesh, MELON_FLESH, bevel=2, outline=False, sss=0.2)
    t = compose(ctx, tr, tf)
    paint(t, dots(ctx, [(6, 8), (9, 9), (7, 11), (11, 11), (4, 12)], 0.5), rgb("1a1010"))
    return t


def bowl(ctx, soup, chunks=()):
    outer = minus(U(ell(ctx, 8.0, 9.0, 7.0, 5.4)), box(ctx, 0, 0, 16, 8.0))
    rim = ell(ctx, 8.0, 8.4, 7.0, 2.4)
    m = U(outer, rim)
    t = spr(ctx, m, BOWL, bevel=1.5, porosity=0.3)
    inner = ell(ctx, 8.0, 8.4, 5.6, 1.5)
    paint(t, inner, soup[2])
    paint(t, inter(inner, box(ctx, 0, 6.0, 16, 8.2)), soup[1])
    paint(t, dots(ctx, [(5, 8), (9, 8)], 0.5), soup[4])
    for pts, c in chunks:
        paint(t, inter(dots(ctx, pts, 0.55), inner), c)
    ring = ctx.edge(m, 1) > 0
    paint(t, (line(ctx, [(3.0, 11.0), (5.0, 12.6)], 0.7) > 0.5) & ~ring, BOWL[4])
    return t


STEW = pal("4a2e1a", "7a5232", "a87a4e", "c89e6e", "e6c494")
register("item/mushroom_stew", lambda ctx: bowl(ctx, STEW, [([(6, 8), (10, 7)], rgb("c43a2a")), ([(8, 8)], rgb("e6d6c0"))]))
register("item/rabbit_stew", lambda ctx: bowl(ctx, pal("4a2a10", "7a4818", "a8682a", "c88a44", "e6b06a"),
                                              [([(5, 7)], rgb("f08a1a")), ([(10, 8)], rgb("e8cc78")),
                                               ([(8, 7)], rgb("8a5a3a"))]))
register("item/suspicious_stew", lambda ctx: bowl(ctx, pal("3a3a1a", "6a6a2e", "92924a", "b4b46a", "d8d890"),
                                                  [([(6, 8)], rgb("e8d040")), ([(10, 7)], rgb("4a8ae0"))]))


@texture("item/pumpkin_pie")
def pumpkin_pie(ctx):
    crust = pal("5a320e", "8e541c", "bc7c30", "dca452", "f2cc84")
    filling = pal("7a3206", "b85a10", "e08424", "f4a844", "fcd08a")
    m = U(poly(ctx, [(1.6, 9.0), (8.0, 5.0), (14.4, 9.0), (14.4, 11.6), (8.0, 14.6), (1.6, 11.6)]))
    t = spr(ctx, m, crust, bevel=1.5, porosity=0.4)
    top = poly(ctx, [(3.2, 9.0), (8.0, 6.2), (12.8, 9.0), (8.0, 11.8)])
    tf = spr(ctx, top, filling, bevel=1.5, outline=False)
    out = compose(ctx, t, tf)
    ring = ctx.edge(m, 1) > 0
    paint(out, (line(ctx, [(2.0, 11.0), (8.0, 14.0), (14.0, 11.0)], 0.7) > 0.5) & ~ring, crust[1])
    paint(out, dots(ctx, [(6, 8), (9, 9)], 0.45), filling[4])
    return out


@texture("item/rotten_flesh")
def rotten_flesh(ctx):
    p = pal("3a2a14", "6a4a22", "946a32", "b88c4a", "d4ac6a")
    m = poly(ctx, [(2.4, 6.0), (5.0, 3.0), (9.0, 3.6), (12.6, 2.6), (14.0, 6.6), (12.0, 9.4), (13.0, 13.0),
                   (8.0, 13.6), (4.4, 12.6), (3.0, 9.6)])
    t = spr(ctx, m, p, bevel=2, porosity=0.5)
    ring = ctx.edge(m, 1) > 0
    paint(t, (dots(ctx, [(5, 6), (9, 8), (7, 11), (11, 5)], 0.6) > 0.5) & ~ring, rgb("6a7a2a"))
    paint(t, (dots(ctx, [(8, 6), (10, 11)], 0.5) > 0.5) & ~ring, rgb("8a2a1e"))
    return t


@texture("item/sweet_berries")
def sweet_berries(ctx):
    bp = pal("3a0610", "7a0e1e", "b0222e", "d84a4a", "f48a80")
    stem = spr(ctx, U(line(ctx, [(8.0, 1.6), (8.0, 5.0)], 1.0), line(ctx, [(8.0, 4.0), (5.0, 6.6)], 0.9),
                      line(ctx, [(8.0, 4.0), (11.0, 7.0)], 0.9)), pal("2e1c0c", "4e3216", "6e4a22"),
               outline=False, bevel=1)
    leaf = spr(ctx, ell(ctx, 10.4, 2.6, 2.2, 1.1, -0.4), LEAF, bevel=1)
    berries = []
    for x, y, r in ((5.0, 9.0, 2.6), (11.0, 9.6, 2.6), (8.0, 12.0, 2.8)):
        b = spr(ctx, circ(ctx, x, y, r), bp, bevel=1.5, smooth=0.7)
        paint(b, cells(ctx, [(int(x - 1), int(y - 1))]), bp[4])
        berries.append(b)
    return compose(ctx, stem, leaf, *berries)


@texture("item/popped_chorus_fruit")
def popped_chorus_fruit(ctx):
    p = pal("4a2a5a", "7a508a", "a67ab8", "caa4da", "ead2f4")
    m = U(circ(ctx, 8.0, 8.4, 4.6), circ(ctx, 4.6, 6.0, 2.2), circ(ctx, 11.6, 5.4, 2.0), circ(ctx, 11.4, 12.0, 2.2),
          circ(ctx, 4.6, 12.0, 2.0))
    t = spr(ctx, m, p, bevel=2.5, porosity=0.4)
    ring = ctx.edge(m, 1) > 0
    paint(t, (dots(ctx, [(7, 7), (9, 9), (6, 10)], 0.5) > 0.5) & ~ring, p[1])
    paint(t, (dots(ctx, [(4, 5), (11, 4)], 0.5) > 0.5) & ~ring, p[4])
    return t
