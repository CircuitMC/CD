"""Food items (a-g): fruit, vegetables, meat & fish (raw/cooked), baked goods,
eggs, soups."""
import numpy as np

from ...engine import GOLD as GOLD_ID, pal
from ...registry import register, texture
from ...sprites import compose
from .common import GOLD, WOOD
from .a_lib import (U, arc_pts, box, circ, curve, dots, ell, inter, line, minus, paint, poly, rod, shades, spr,
                    stroke)

APPLE = pal("4a0a0e", "8a1418", "c42a26", "e8483a", "ff8a6e")
STEM = pal("2e1c0c", "4e3216", "6e4a22")
LEAF = pal("1a4210", "2c6e1a", "44a02a", "76cc46")
CARROT = pal("6a2a08", "b0500e", "e2741c", "f8a03a", "ffcf88")
POTATO_SKIN = pal("4a2c12", "7a4c22", "a06a34", "c4904e", "dcb070")
POTATO_IN = pal("b89a40", "dcc060", "f2dc84", "fff2b8")
RAW_RED = pal("4e0c10", "8c1a1c", "c03432", "e05a50", "f49488")
FAT = pal("b8a49a", "e2d4cc", "f6eee8")
SEARED = pal("2e170a", "4e2a12", "74401e", "9a5e30", "c0844a")
CHICKEN_RAW = pal("8a5a4c", "d29a88", "eebcaa", "fcdccc", "fff2ea")
CHICKEN_COOKED = pal("4e2a0c", "8a4e18", "b8742a", "d89a44", "f2c46e")
BONE = pal("8a8270", "c8c0aa", "e8e2d0", "fbf8ee")
BREAD = pal("5a320e", "8e541c", "bc7c30", "dca452", "f2cc84")
COOKIE = pal("5e3410", "925a22", "b87c38", "d6a058", "ecc47e")
CHOC = pal("1e0e06", "3a1e0e", "56301a")
BEET = pal("3a0618", "6a0e2c", "981c44", "c43a62", "e2708e")
SEEDS = pal("3a2a14", "6a5028", "967444", "bc9a66")
CHORUS = pal("2a1438", "4e2a64", "7a4a94", "a674bc", "d0a8e2")
COCOA = pal("2a140a", "4a2814", "6c4020", "8e5a30", "ac7848")
KELP = pal("0e1a0c", "1e3216", "2e4a20", "42642c", "5a7e3a")
MELON_RIND = pal("1a3a0e", "2e6418", "4c9228", "78b840")
MELON_FLESH = pal("8a1414", "c42a26", "e8483a", "fa7a62")
BERRY = pal("6a2a06", "c45a0e", "f08a1c", "ffbe48", "fff0a0")
EYE = pal("3a060c", "6e0e18", "a4202a", "d04a4a", "f08a80")
MUSHROOM = pal("3a2214", "6a4428", "946240", "ba8a62")
BOWL = pal("3a2210", "5e3a1c", "84562c", "a8763e", "c89656")
SOUP_BEET = pal("4a0610", "7c0e1c", "a8202c", "d0484a", "ec7a70")


def dark_edge(ctx, t, mask, rgb):
    ring = ctx.edge(mask, 1) > 0
    paint(t, ring, rgb)


# --------------------------------------------------------------- fruit

def apple_shape(ctx):
    return minus(U(circ(ctx, 6.2, 9.4, 4.7), circ(ctx, 9.8, 9.4, 4.7), ell(ctx, 8.0, 11.0, 5.6, 4.0)),
                 circ(ctx, 8.0, 3.6, 1.5))


def apple(ctx, golden=False):
    m = apple_shape(ctx)
    p = GOLD if golden else APPLE
    t = spr(ctx, m, p, bevel=3.0, light=0.32, smooth=0.75 if golden else 0.45, sss=0 if golden else 0.1)
    if golden:
        t.set_metal(m, GOLD_ID)
    ring = ctx.edge(m, 1) > 0
    paint(t, dots(ctx, [(4, 7), (5, 6)]) * (~ring), p[4])
    paint(t, dots(ctx, [(11, 12), (10, 13)]) * (~ring), p[1])
    stem = rod(ctx, [(8.0, 6.4), (8.4, 2.4)], 1.2, STEM)
    leaf = spr(ctx, poly(ctx, [(8.6, 3.6), (10.6, 1.6), (13.4, 1.8), (11.6, 4.0)]), LEAF, bevel=1)
    return compose(ctx, t, stem, leaf)


register("item/apple", lambda ctx: apple(ctx))
register("item/golden_apple", lambda ctx: apple(ctx, True))


def carrot(ctx, golden=False):
    p = GOLD if golden else CARROT
    m = poly(ctx, [(1.4, 14.8), (7.6, 5.0), (10.4, 3.8), (12.2, 5.6), (11.2, 8.4)])
    m = U(m, curve(ctx, (2.0, 14.0), (6.6, 9.4), (10.4, 5.6), 1.2, 5.0))
    t = spr(ctx, m, p, bevel=2.0, smooth=0.75 if golden else 0.3)
    if golden:
        t.set_metal(m, GOLD_ID)
    ring = ctx.edge(m, 1) > 0
    for a, b in (((5.0, 10.0), (6.6, 11.4)), ((7.0, 7.6), (8.8, 9.0)), ((3.8, 12.0), (4.6, 12.8))):
        paint(t, line(ctx, [a, b], 0.7) * (~ring), p[1])
    paint(t, line(ctx, [(6.4, 8.0), (8.6, 5.8)], 0.7) * (~ring), p[4])
    lp = LEAF if not golden else pal("4a3a06", "8a6e0e", "c8a82a", "f0d860")
    leaves = spr(ctx, U(line(ctx, [(10.6, 5.2), (13.0, 1.4)], 1.4), line(ctx, [(11.0, 5.6), (14.8, 3.6)], 1.4),
                        line(ctx, [(10.8, 5.4), (15.0, 1.0)], 1.0)), lp, bevel=1)
    return compose(ctx, t, leaves)


register("item/carrot", lambda ctx: carrot(ctx))
register("item/golden_carrot", lambda ctx: carrot(ctx, True))


@texture("item/chorus_fruit")
def chorus_fruit(ctx):
    """Knobbly purple fruit: a round body covered in raised bumps, with a stalk."""
    lobes = [(8.0, 9.2, 5.0), (5.0, 6.6, 2.6), (11.2, 6.4, 2.6), (4.4, 11.6, 2.5), (11.6, 11.8, 2.5),
             (8.0, 4.8, 2.4), (8.0, 13.4, 2.4)]
    m = U(*[circ(ctx, x, y, r) for x, y, r in lobes])
    t = spr(ctx, m, CHORUS, bevel=2.5, sss=0.2)
    ring = ctx.edge(m, 1) > 0
    for x, y, r in lobes:  # each bump: lit top-left, shaded bottom-right
        paint(t, dots(ctx, [(x - r * 0.45 - 0.5, y - r * 0.45 - 0.5)], 0.55) * (~ring), CHORUS[4])
        paint(t, dots(ctx, [(x + r * 0.35 - 0.5, y + r * 0.4 - 0.5)], 0.5) * (~ring), CHORUS[1])
    stalk = spr(ctx, U(line(ctx, [(8.4, 3.0), (9.6, 0.8)], 1.1)), pal("2a1438", "5a3a6a", "8a6a9a"), bevel=1)
    return compose(ctx, stalk, t)


@texture("item/glistering_melon_slice")
def glistering_melon_slice(ctx):
    rind = minus(circ(ctx, 8.0, 3.0, 12.0), circ(ctx, 8.0, 1.6, 10.4), box(ctx, 0, 0, 16, 4.0))
    rind = inter(rind, poly(ctx, [(8, 3.0), (-6, 16), (22, 16)]))
    flesh = minus(inter(circ(ctx, 8.0, 1.6, 10.6), poly(ctx, [(8, 3.0), (-4.6, 14.6), (20.6, 14.6)])), box(ctx, 0, 0, 16, 4.0))
    m = U(rind, flesh)
    tr = spr(ctx, U(rind, flesh), MELON_RIND, bevel=1)
    tf = spr(ctx, flesh, MELON_FLESH, bevel=2, outline=False, sss=0.2)
    t = compose(ctx, tr, tf)
    seeds = dots(ctx, [(6, 8), (9, 9), (7, 11), (11, 11)], 0.5)
    paint(t, seeds, pal("1a1010")[0])
    flecks = dots(ctx, [(5, 10), (8, 7), (10, 10), (12, 12), (4, 12), (8, 12)], 0.5)
    paint(t, flecks, GOLD[3])
    paint(t, dots(ctx, [(8, 7), (12, 12)], 0.4), GOLD[4])
    t.emissive = np.where(flecks > 0.5, 0.35, 0.0)
    t.set_metal(flecks, GOLD_ID)
    return t


@texture("item/glow_berries")
def glow_berries(ctx):
    vine = stroke(ctx, [(9.0, 0.8), (8.4, 3.6), (8.8, 6.0), (7.6, 8.0)], 1.0)
    tv = spr(ctx, vine, pal("1e3a10", "345e1c", "4e8228"), outline=False, bevel=1)
    leaf = spr(ctx, poly(ctx, [(9.0, 3.0), (12.0, 1.6), (13.6, 3.0), (11.0, 4.6)]), LEAF, bevel=1)
    bs = []
    for x, y, r in ((7.4, 9.4, 2.3), (11.6, 11.4, 2.3), (5.0, 13.0, 2.3), (9.4, 14.0, 1.8)):
        b = circ(ctx, x, y, r)
        tb = spr(ctx, b, BERRY, bevel=1.5, sss=0.3, emissive=0.7)
        paint(tb, dots(ctx, [(x - 1.4, y - 1.4)], 0.5) * (~(ctx.edge(b, 1) > 0)), BERRY[4])
        bs.append(tb)
    twig = spr(ctx, U(line(ctx, [(7.6, 8.0), (11.0, 9.6)], 0.9), line(ctx, [(7.4, 8.4), (5.4, 11.0)], 0.9)),
               pal("1e3a10", "345e1c", "4e8228"), outline=False, bevel=1)
    return compose(ctx, tv, leaf, twig, *bs)


# ------------------------------------------------------------- veggies

@texture("item/baked_potato")
def baked_potato(ctx):
    m = ell(ctx, 8.0, 9.0, 6.6, 4.8, -0.35)
    t = spr(ctx, m, POTATO_SKIN, bevel=2.5, porosity=0.4)
    split = ell(ctx, 7.6, 7.6, 3.6, 1.6, -0.35)
    paint(t, split, POTATO_IN[2])
    paint(t, ell(ctx, 7.0, 7.3, 2.2, 0.8, -0.35), POTATO_IN[3])
    paint(t, ctx.edge(split, 1, "br") * split, POTATO_IN[0])
    ring = ctx.edge(m, 1) > 0
    paint(t, dots(ctx, [(4, 11), (9, 12), (12, 9), (11, 12)]) * (~ring), POTATO_SKIN[1])
    return t


@texture("item/beetroot")
def beetroot(ctx):
    bulb = U(circ(ctx, 8.0, 10.0, 4.4), poly(ctx, [(5.0, 12.6), (11.0, 12.6), (8.0, 15.6)]))
    t = spr(ctx, bulb, BEET, bevel=2.5)
    ring = ctx.edge(bulb, 1) > 0
    paint(t, line(ctx, [(5.6, 9.0), (7.0, 7.6)], 0.8) * (~ring), BEET[4])
    paint(t, line(ctx, [(9.6, 12.0), (10.6, 10.6)], 0.8) * (~ring), BEET[1])
    stems = spr(ctx, U(line(ctx, [(7.6, 6.2), (5.0, 1.4)], 1.0), line(ctx, [(8.4, 6.2), (10.6, 1.2)], 1.0)),
                pal("3a0618", "6a0e2c", "981c44"), outline=False, bevel=1)
    leaves = spr(ctx, U(ell(ctx, 4.6, 2.6, 2.2, 1.2, 1.0), ell(ctx, 11.2, 2.4, 2.2, 1.2, -1.0)), LEAF, bevel=1)
    return compose(ctx, stems, leaves, t)


@texture("item/beetroot_seeds")
def beetroot_seeds(ctx):
    layers = []
    for x, y, a in ((4.6, 5.0, 0.5), (10.8, 4.4, -0.7), (6.2, 11.2, -0.2), (11.6, 11.0, 0.9)):
        c, s_ = np.cos(a), np.sin(a)
        m = U(circ(ctx, x, y, 1.9), poly(ctx, [(x - 1.8 * s_, y + 1.8 * c), (x + 3.2 * c, y + 3.2 * s_),
                                               (x + 1.8 * s_, y - 1.8 * c)]))
        t = spr(ctx, m, SEEDS, bevel=1)
        paint(t, dots(ctx, [(x - 1.0, y - 1.0)], 0.45), SEEDS[3])
        layers.append(t)
    return compose(ctx, *layers)


@texture("item/cocoa_beans")
def cocoa_beans(ctx):
    """Three plump oval beans, each split by a lengthwise crease."""
    layers = []
    for x, y, a in ((5.4, 5.6, 0.7), (11.0, 7.0, -0.5), (7.4, 11.6, 0.15)):
        b = ell(ctx, x, y, 3.4, 2.3, a)
        t = spr(ctx, b, COCOA, bevel=1.5, smooth=0.3)
        ring = ctx.edge(b, 1) > 0
        c, s_ = np.cos(a), np.sin(a)
        paint(t, line(ctx, [(x - 2.2 * c, y - 2.2 * s_), (x + 2.2 * c, y + 2.2 * s_)], 0.7) * (~ring), COCOA[0])
        paint(t, dots(ctx, [(x - 1.6 * c + 1.0 * s_ - 0.5, y - 1.6 * s_ - 1.0 * c - 0.5)], 0.5) * (~ring), COCOA[4])
        layers.append(t)
    return compose(ctx, *layers)


@texture("item/dried_kelp")
def dried_kelp(ctx):
    """A dried, crinkled kelp leaf: dark olive blade with a midrib and wrinkles."""
    m = poly(ctx, [(2.4, 14.0), (2.6, 10.0), (4.0, 6.6), (7.0, 3.6), (11.0, 1.8), (14.2, 1.8), (13.6, 5.0),
                   (11.6, 9.0), (8.6, 12.0), (5.0, 13.6)])
    t = spr(ctx, m, KELP, bevel=1.5, porosity=0.3)
    ring = ctx.edge(m, 1) > 0
    paint(t, line(ctx, [(3.0, 13.4), (6.6, 8.6), (13.4, 2.4)], 0.7) * (~ring), KELP[4])
    for (x0, y0), (x1, y1) in (((5.0, 10.6), (3.6, 9.6)), ((7.6, 7.6), (6.4, 5.4)), ((10.0, 5.4), (9.0, 3.4)),
                               ((6.6, 10.2), (8.4, 11.0)), ((9.2, 7.6), (11.2, 8.0)), ((11.6, 4.6), (13.2, 4.6))):
        paint(t, line(ctx, [(x0, y0), (x1, y1)], 0.6) * (~ring), KELP[1])
    return t


# ----------------------------------------------------------------- meat

def steak_shape(ctx):
    return poly(ctx, [(2.0, 7.6), (4.0, 3.6), (8.6, 2.0), (13.0, 3.4), (14.6, 7.0), (13.6, 11.4), (10.0, 14.2),
                      (5.0, 14.0), (2.4, 11.6)])


def beef(ctx, cooked=False):
    m = steak_shape(ctx)
    p = SEARED if cooked else RAW_RED
    t = spr(ctx, m, p, bevel=2.5, sss=0 if cooked else 0.2, smooth=0.35 if not cooked else 0.25)
    ring = ctx.edge(m, 1) > 0
    fat = minus(m, poly(ctx, [(3.2, 8.0), (4.8, 4.6), (8.6, 3.2), (12.4, 4.4), (13.6, 7.4), (12.6, 11.0),
                              (9.6, 13.0), (5.4, 12.8), (3.4, 11.0)]))
    paint(t, fat * (~ring), (pal("8a5a30")[0] if cooked else FAT[1]))
    paint(t, inter(fat, box(ctx, 0, 0, 9, 7)) * (~ring), (pal("b07a44")[0] if cooked else FAT[2]))
    if cooked:
        for i in range(3):
            paint(t, line(ctx, [(4.0 + i * 3, 12.0), (8.0 + i * 3, 5.0)], 0.9) * (~ring), SEARED[0])
    else:
        paint(t, line(ctx, [(6.0, 8.4), (8.0, 7.0), (10.4, 8.6)], 0.7) * (~ring), FAT[0])
        paint(t, line(ctx, [(7.0, 11.0), (9.4, 10.6)], 0.7) * (~ring), FAT[0])
    return t


register("item/beef", lambda ctx: beef(ctx))
register("item/cooked_beef", lambda ctx: beef(ctx, True))


def drumstick(ctx, p, cooked=False):
    meat = U(ell(ctx, 6.6, 6.8, 4.8, 4.0, -0.75), circ(ctx, 9.2, 9.2, 2.6))
    bone = U(line(ctx, [(9.4, 9.4), (13.0, 13.0)], 1.8), circ(ctx, 13.4, 12.4, 1.2), circ(ctx, 12.4, 13.6, 1.2))
    tb = spr(ctx, bone, BONE, bevel=1)
    tm = spr(ctx, meat, p, bevel=2.5, sss=0 if cooked else 0.15)
    ring = ctx.edge(meat, 1) > 0
    paint(tm, dots(ctx, [(4, 4), (5, 4), (3, 6)]) * (~ring), p[4])
    if cooked:
        paint(tm, dots(ctx, [(7, 8), (9, 6), (5, 9)]) * (~ring), p[1])
    else:
        paint(tm, dots(ctx, [(7, 8), (9, 6), (5, 9)], 0.45) * (~ring), p[2] * 0.95)
    return compose(ctx, tb, tm)


register("item/chicken", lambda ctx: drumstick(ctx, CHICKEN_RAW))
register("item/cooked_chicken", lambda ctx: drumstick(ctx, CHICKEN_COOKED, True))


def sear(ctx, t, lines, rgb):
    """Grill marks over the opaque interior of a food sprite."""
    m = t.alpha > 0.5
    ring = ctx.edge(m.astype(np.float32), 1) > 0
    for a, b in lines:
        paint(t, (line(ctx, [a, b], 0.9) > 0.5) & ~ring, rgb)
    return t


def cooked_chop(ctx, p, rim, bone):
    from . import h_food as HF  # same silhouette as raw mutton / porkchop
    t = HF.chop(ctx, p, rim, bone)
    return sear(ctx, t, [((4.4, 10.6), (8.0, 5.0)), ((6.8, 11.6), (10.2, 6.6))], p[0])


register("item/cooked_mutton", lambda ctx: cooked_chop(ctx, pal("3a1a0c", "6a3418", "8e4c26", "b06a38", "cc8a50"),
                                                       pal("d8b080")[0], True))
register("item/cooked_porkchop", lambda ctx: cooked_chop(ctx, pal("4a2410", "7e4422", "aa6436", "cc8650", "e8aa70"),
                                                         pal("eccc94")[0], False))


@texture("item/cooked_rabbit")
def cooked_rabbit(ctx):
    p = pal("3e1e0a", "6e3c18", "9a5a28", "bc7e40", "dca460")
    m = U(ell(ctx, 7.0, 7.6, 5.2, 3.8, -0.6), ell(ctx, 10.4, 11.0, 3.4, 2.4, -0.9))
    t = spr(ctx, m, p, bevel=2.5)
    ring = ctx.edge(m, 1) > 0
    paint(t, line(ctx, [(4.6, 9.4), (8.4, 5.0)], 0.8) * (~ring), p[1])
    paint(t, line(ctx, [(9.2, 10.6), (11.6, 9.4)], 0.8) * (~ring), p[1])
    paint(t, dots(ctx, [(4, 5), (5, 4)]) * (~ring), p[4])
    bone = spr(ctx, U(line(ctx, [(11.6, 12.4), (14.0, 14.4)], 1.5), circ(ctx, 14.2, 14.2, 1.1)), BONE, bevel=1)
    return compose(ctx, bone, t)


# ----------------------------------------------------------------- fish

def fish(ctx, body_p, belly, cooked=False, fin_p=None):
    from . import h_food as HF  # same fish silhouette as raw salmon / tropical fish
    t = HF.fish(ctx, body_p, belly, fin_p)
    if cooked:
        sear(ctx, t, [((5.0, 10.6), (7.0, 6.4)), ((8.6, 10.8), (10.4, 6.6))], body_p[1])
    return t


register("item/cod", lambda ctx: fish(ctx, pal("3e3424", "6e6046", "9a8a68", "bcae8a", "dcd0b0"), pal("e8dcc0")[0],
                                      fin_p=pal("2e281c", "5a4e38", "7e7058")))
register("item/cooked_cod", lambda ctx: fish(ctx, pal("3e2410", "7a4e26", "a8743e", "c89a5e", "e6c288"),
                                              pal("f0d8a8")[0], True, pal("2e1c0c", "5a3a1c", "7e5228")))
register("item/cooked_salmon", lambda ctx: fish(ctx, pal("4a1c0c", "8a3a1c", "bc5a2e", "dc7e48", "f2a46c"),
                                                 pal("f4c090")[0], True, pal("2e1c14", "5a3a2a", "7a5440")))


# ---------------------------------------------------------- baked goods

@texture("item/bread")
def bread(ctx):
    m = U(ell(ctx, 8.0, 8.6, 7.2, 3.8, -0.55))
    t = spr(ctx, m, BREAD, bevel=2.5, porosity=0.5)
    ring = ctx.edge(m, 1) > 0
    for i in range(3):
        cx, cy = 5.0 + i * 3.0, 11.0 - i * 2.4
        paint(t, line(ctx, [(cx - 0.8, cy - 1.4), (cx + 0.9, cy + 0.6)], 0.8) * (~ring), BREAD[1])
        paint(t, line(ctx, [(cx - 1.6, cy - 1.0), (cx - 0.4, cy - 2.0)], 0.6) * (~ring), BREAD[4])
    return t


@texture("item/cookie")
def cookie(ctx):
    m = circ(ctx, 8.0, 8.4, 6.0)
    t = spr(ctx, m, COOKIE, bevel=2.0, porosity=0.5)
    chips = dots(ctx, [(5, 6), (9, 5), (11, 9), (6, 10), (9, 11), (7, 8)], 0.75)
    paint(t, chips, CHOC[1])
    paint(t, dots(ctx, [(5, 6), (9, 5), (7, 8)], 0.35), CHOC[2])
    paint(t, dots(ctx, [(4, 8), (12, 7)], 0.5) * (~(ctx.edge(m, 1) > 0)), COOKIE[4])
    return t


@texture("item/cake")
def cake(ctx):
    body = poly(ctx, [(1.0, 6.6), (8.0, 3.0), (15.0, 6.6), (15.0, 11.0), (8.0, 15.0), (1.0, 11.0)])
    sponge = pal("6a3a1a", "a06030", "c88848", "e2ac6a")
    t = spr(ctx, body, sponge, bevel=1.5)
    top = poly(ctx, [(1.0, 6.6), (8.0, 3.0), (15.0, 6.6), (8.0, 10.2)])
    icing_side = U(top, poly(ctx, [(1, 6.6), (8, 10.2), (15, 6.6), (15, 8.4), (13.4, 9.8), (12.0, 9.2), (10.0, 11.0),
                                   (8.0, 12.0), (6.2, 10.6), (4.4, 10.8), (2.6, 9.2), (1, 8.8)]))
    icing = spr(ctx, icing_side, pal("9a9a9e", "dcdce0", "f2f2f4", "ffffff"), bevel=1.2)
    t = compose(ctx, t, icing)
    paint(t, line(ctx, [(8.0, 11.6), (8.0, 14.4)], 0.8), sponge[1])
    cher = dots(ctx, [(5, 6), (8, 5), (10, 7), (7, 7)], 0.7)
    paint(t, cher, pal("c41e1e")[0])
    paint(t, dots(ctx, [(5, 6), (8, 5)], 0.3), pal("ff7a6a")[0])
    return t


# ---------------------------------------------------------------- eggs

def egg(ctx, p, speck=None):
    k = ctx.w / 16
    x, y = ctx.x / k, ctx.y / k
    yy = (y - 9.0) / 5.6
    rx = 4.2 * (1 + 0.16 * yy)
    m = ((((x - 8.0) / rx) ** 2 + yy ** 2) < 1).astype(np.float32)
    t = spr(ctx, m, p, bevel=2.5, light=0.32, smooth=0.4)
    ring = ctx.edge(m, 1) > 0
    paint(t, dots(ctx, [(6, 6)], 0.6) * (~ring), p[-1])
    if speck is not None:
        paint(t, dots(ctx, [(9, 7), (6, 10), (10, 11), (8, 13), (7, 8)], 0.45) * (~ring), speck)
    return t


register("item/egg", lambda ctx: egg(ctx, pal("8a7a5a", "c8b88e", "e2d6b2", "f4ecd4", "fffaee")))
register("item/blue_egg", lambda ctx: egg(ctx, pal("2e4a6a", "5a82a8", "82a8cc", "aac8e6", "d6e8f8"),
                                          pal("3a5a7e")[0]))
register("item/brown_egg", lambda ctx: egg(ctx, pal("4a2a12", "7e4e26", "a8723e", "c89458", "e2b67a"),
                                           pal("5e3818")[0]))


# --------------------------------------------------------------- bowls

def bowl_layers(ctx, soup=None):
    outer = minus(U(ell(ctx, 8.0, 9.0, 7.0, 5.4)), box(ctx, 0, 0, 16, 8.0))
    rim = ell(ctx, 8.0, 8.4, 7.0, 2.4)
    m = U(outer, rim)
    t = spr(ctx, m, BOWL, bevel=1.5, porosity=0.3)
    inner = ell(ctx, 8.0, 8.4, 5.6, 1.5)
    if soup is None:
        paint(t, inner, BOWL[1])
        paint(t, inter(inner, box(ctx, 0, 6.0, 16, 8.4)), BOWL[0])
    else:
        paint(t, inner, soup[2])
        paint(t, inter(inner, box(ctx, 0, 6.0, 16, 8.2)), soup[1])
        paint(t, dots(ctx, [(5, 8), (9, 8)], 0.5), soup[4])
    ring = ctx.edge(m, 1) > 0
    paint(t, line(ctx, [(3.0, 11.0), (5.0, 12.6)], 0.7) * (~ring), BOWL[4])
    return t


register("item/bowl", lambda ctx: bowl_layers(ctx))
register("item/beetroot_soup", lambda ctx: bowl_layers(ctx, SOUP_BEET))


@texture("item/fermented_spider_eye")
def fermented_spider_eye(ctx):
    eye = circ(ctx, 8.0, 10.0, 4.8)
    t = spr(ctx, eye, EYE, bevel=2.5, sss=0.2, smooth=0.6)
    paint(t, circ(ctx, 7.0, 10.6, 1.8), pal("2a0e2a")[0])
    paint(t, dots(ctx, [(6, 10)], 0.4), pal("c88ac8")[0])
    cap = minus(ell(ctx, 8.6, 5.0, 4.6, 2.8), box(ctx, 0, 5.6, 16, 16))
    tc = spr(ctx, U(cap, box(ctx, 7.6, 5.0, 9.6, 7.0)), MUSHROOM, bevel=1.2)
    paint(tc, dots(ctx, [(7, 3), (10, 3)], 0.5), MUSHROOM[3])
    sugar = spr(ctx, U(circ(ctx, 12.6, 13.0, 0.9), circ(ctx, 3.6, 13.4, 0.8), circ(ctx, 13.4, 9.4, 0.7)),
                pal("a8a8a8", "e8e8e8", "ffffff"), bevel=1)
    return compose(ctx, t, tc, sugar)
