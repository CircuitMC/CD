"""Remaining h-z items: minecarts, hopper, chains, lanterns, frames, books, gear,
weapons, keys, arrows and odds and ends."""
import math

import numpy as np

from ...registry import register, texture
from .common import CHAIN, GOLD as GOLD_P, IRON as IRON_P, LEATHER, STRING, WOOD, EMERALD, REDSTONE, STONE
from .h_lib import (COPPER, GOLD, IRON, NETH, Diag, U, arc_pts, box, cells, circ, compose, curve, dots, ell,
                    flat_layer, inter, line, metal, minus, paint, pal, poly, rgb, rod, rows_mask, spr, stroke, union)

CART = pal("3a3a40", "60606a", "86868e", "aaaab2", "cfcfd6")
WHEEL = pal("1a1a1e", "2e2e34", "46464e")
FLINT = pal("1f1f22", "38383d", "55555b", "727279", "8e8e96")
FEATHER = pal("8a8a8a", "c4c4c4", "e6e6e6", "fafafa")


# ------------------------------------------------------------------ minecarts
def cart(ctx, content=None):
    body = poly(ctx, [(1.0, 7.0), (15.0, 7.0), (14.0, 12.6), (2.0, 12.6)])
    t = metal(ctx, body, CART, IRON, bevel=1.5, smooth=0.55)
    ring = ctx.edge(body, 1) > 0
    paint(t, (box(ctx, 0, 7.0, 16, 8.0) > 0.5) & (body > 0.5), CART[0])
    paint(t, (box(ctx, 2.0, 8.0, 14.0, 9.0) > 0.5) & ~ring & (body > 0.5), CART[4])
    paint(t, (box(ctx, 2.0, 10.6, 14.0, 11.4) > 0.5) & ~ring & (body > 0.5), CART[1])
    paint(t, (cells(ctx, [(3, 9), (12, 9), (3, 11), (12, 11)]) > 0.5) & ~ring, CART[4])
    wheels = U(circ(ctx, 4.6, 13.0, 1.8), circ(ctx, 11.4, 13.0, 1.8))
    tw = metal(ctx, wheels, WHEEL, IRON, bevel=1)
    paint(tw, cells(ctx, [(4, 12), (11, 12)]), WHEEL[2])
    layers = [tw, t]
    if content is not None:
        layers.insert(0, content(ctx))
    return compose(ctx, *layers)


def hopper_in_cart(ctx):
    m = U(poly(ctx, [(3.0, 3.6), (13.0, 3.6), (11.0, 7.4), (5.0, 7.4)]))
    t = metal(ctx, m, pal("1e1e22", "38383e", "54545c", "72727a", "92929a"), IRON, bevel=1)
    paint(t, box(ctx, 4.0, 4.6, 12.0, 5.6), rgb("16161a"))
    return t


def tnt_in_cart(ctx):
    m = box(ctx, 4.0, 2.0, 12.0, 7.6)
    t = spr(ctx, m, pal("5a0e0a", "9a1e16", "c83228", "e85a48", "f68a78"), bevel=1)
    paint(t, box(ctx, 5.0, 4.0, 11.0, 5.6), rgb("ece8e0"))
    paint(t, cells(ctx, [(6, 4), (8, 4), (10, 4)]), rgb("2a2a2a"))
    return t


register("item/minecart", lambda ctx: cart(ctx))
register("item/hopper_minecart", lambda ctx: cart(ctx, hopper_in_cart))
register("item/tnt_minecart", lambda ctx: cart(ctx, tnt_in_cart))

HOPPER = pal("1e1e22", "38383e", "54545c", "72727a", "92929a")


@texture("item/hopper")
def hopper(ctx):
    top = box(ctx, 1.0, 2.0, 15.0, 7.0)
    mid = poly(ctx, [(3.0, 7.0), (13.0, 7.0), (10.6, 11.0), (5.4, 11.0)])
    spout = box(ctx, 6.6, 10.6, 9.4, 14.6)
    m = U(top, mid, spout)
    t = metal(ctx, m, HOPPER, IRON, bevel=1.5, smooth=0.5)
    ring = ctx.edge(m, 1) > 0
    paint(t, box(ctx, 3.0, 3.0, 13.0, 4.6), HOPPER[0])
    paint(t, (box(ctx, 1.0, 6.0, 15.0, 7.0) > 0.5) & ~ring, HOPPER[1])
    paint(t, (cells(ctx, [(2, 5), (13, 5)]) > 0.5) & ~ring, HOPPER[4])
    return t


# ------------------------------------------------------------------ chains
def chain(ctx, p, mid=IRON, patina=None):
    layers = []
    for i, y in enumerate((1.0, 5.6, 10.2)):
        oval = minus(ell(ctx, 8.0, y + 2.4, 3.0, 2.9), ell(ctx, 8.0, y + 2.4, 1.0, 1.1))
        lt = metal(ctx, oval, p, mid, bevel=1, smooth=0.6, outline=False)
        paint(lt, ctx.edge(oval, 1, "br"), p[0])
        paint(lt, ctx.edge(oval, 1, "tl") * (ell(ctx, 8.0, y + 2.4, 2.0, 2.0) < 0.5), p[-1])
        layers.append(lt)
    for y in (4.2, 8.8):
        bar = box(ctx, 7.0, y, 9.0, y + 2.8)
        layers.append(metal(ctx, bar, p, mid, bevel=1, smooth=0.6))
    t = compose(ctx, *layers)
    if patina is not None:
        n = ctx.texel_noise("pat")
        sp = (t.alpha > 0.5) & (n > 0.72)
        t.color[sp] = patina
        t.metal[sp] = 0
    return t


COP_W = pal("3a3a2e", "6a7058", "8a9a74", "a4b68e", "c4d2ae")
COP_O = pal("1e4a44", "2e6e64", "3e9080", "52a894", "74c4ae")
register("item/iron_chain", lambda ctx: chain(ctx, pal("2e2e34", "5a5a62", "84848c", "acacb4", "d4d4dc")))
register("item/weathered_copper_chain", lambda ctx: chain(ctx, pal("4a2e1e", "84543a", "a87054", "c28c6e", "dcae90"),
                                                          COPPER, rgb("6aa88a")))
register("item/oxidized_copper_chain", lambda ctx: chain(ctx, COP_O, None))


# ------------------------------------------------------------------ lanterns
def lantern(ctx, frame_p, flame, mid=IRON):
    handle = stroke(ctx, arc_pts(8.0, 3.6, 2.2, 180, 360, 10), 0.9)
    th = metal(ctx, handle, frame_p, mid, outline=False, bevel=1)
    paint(th, handle, frame_p[1])
    cap = U(box(ctx, 4.0, 3.6, 12.0, 5.6), box(ctx, 5.0, 2.8, 11.0, 4.0))
    base = box(ctx, 4.0, 12.4, 12.0, 14.4)
    cage = box(ctx, 4.6, 5.6, 11.4, 12.4)
    body = U(cap, base, cage)
    t = metal(ctx, body, frame_p, mid, bevel=1, smooth=0.55)
    ring = ctx.edge(body, 1) > 0
    glass = (box(ctx, 5.6, 6.0, 10.4, 12.0) > 0.5)
    fp = pal(*flame)
    paint(t, glass, fp[1], emissive=0.6, metal=0)
    core = (box(ctx, 6.6, 7.6, 9.4, 11.0) > 0.5)
    paint(t, core, fp[2], emissive=0.9)
    paint(t, cells(ctx, [(7, 8), (8, 9)]), fp[3], emissive=1.0)
    paint(t, (box(ctx, 7.6, 6.0, 8.4, 12.0) > 0.5) & ~ring, frame_p[1], emissive=0.0)
    paint(t, (cells(ctx, [(5, 4), (6, 4)]) > 0.5) & ~ring, frame_p[-1])
    return compose(ctx, th, t)


LANTERN_FRAME = pal("1e1e24", "3a3a44", "565662", "74747e", "94949e")
register("item/lantern", lambda ctx: lantern(ctx, LANTERN_FRAME, ("8a4a0a", "e89a2a", "fbd060", "fff6c0")))
register("item/soul_lantern", lambda ctx: lantern(ctx, LANTERN_FRAME, ("0a4a5a", "2aa8c0", "6ae8f0", "d0ffff")))
register("item/weathered_copper_lantern", lambda ctx: lantern(ctx, COP_W, ("2a5a1a", "6ac83a", "a8f070", "e8ffd0"), None))
register("item/oxidized_copper_lantern", lambda ctx: lantern(ctx, COP_O, ("2a5a1a", "6ac83a", "a8f070", "e8ffd0"), None))


# ------------------------------------------------------------------ frames
FRAME_WOOD = pal("3a2410", "5e3c1c", "84572b", "a8773e", "c79a5a")


@texture("item/item_frame")
def item_frame(ctx):
    outer = box(ctx, 1.0, 1.0, 15.0, 15.0)
    t = spr(ctx, outer, FRAME_WOOD, bevel=1.5, porosity=0.3)
    inner = box(ctx, 3.0, 3.0, 13.0, 13.0)
    lp = LEATHER
    paint(t, inner, lp[2])
    paint(t, box(ctx, 3.0, 3.0, 13.0, 4.0), lp[1])
    paint(t, box(ctx, 3.0, 3.0, 4.0, 13.0), lp[1])
    n = ctx.texel_noise("ifr")
    paint(t, (inner > 0.5) & (n > 0.85), lp[3])
    paint(t, (box(ctx, 2.0, 2.0, 14.0, 3.0) > 0.5), FRAME_WOOD[4])
    return t


@texture("item/painting")
def painting(ctx):
    outer = box(ctx, 0.0, 2.0, 16.0, 14.0)
    t = spr(ctx, outer, FRAME_WOOD, bevel=1.5, porosity=0.3)
    inner = box(ctx, 1.0, 3.0, 15.0, 13.0) > 0.5
    k = ctx.w / 16
    y = ctx.y / k
    x = ctx.x / k
    sky = np.where((y < 7.0)[..., None], rgb("8ac4e8"), rgb("aad8f0"))
    hills = (y > 9.0 - 1.6 * np.sin(x * 0.7)) & inner
    col = np.where(hills[..., None], rgb("5a9a3a"), sky)
    col = np.where(((y > 11.0))[..., None] & inner[..., None], rgb("3e7a2a"), col)
    t.color = np.where(inner[..., None], col, t.color)
    paint(t, circ(ctx, 11.6, 5.6, 1.4), rgb("f8e070"))
    paint(t, cells(ctx, [(4, 8), (4, 9), (3, 8), (5, 8), (4, 7)]), rgb("2e5a22"))
    return t


# ------------------------------------------------------------------ books
def book(ctx, cover, deco=None):
    m = poly(ctx, [(2.0, 4.0), (10.6, 2.0), (14.0, 4.6), (14.0, 12.6), (5.4, 14.6), (2.0, 12.0)])
    t = spr(ctx, m, cover, bevel=1.5, porosity=0.3)
    ring = ctx.edge(m, 1) > 0
    paint(t, (poly(ctx, [(10.6, 2.0), (14.0, 4.6), (14.0, 12.6), (12.4, 11.6), (12.4, 3.6)]) > 0.5) & ~ring,
          rgb("f2ead6"))
    for yy in (5.6, 7.6, 9.6):
        paint(t, (line(ctx, [(12.8, yy), (13.6, yy + 0.6)], 0.5) > 0.5) & ~ring, rgb("b8ae96"))
    paint(t, (line(ctx, [(2.6, 4.6), (2.6, 11.6)], 0.8) > 0.5) & ~ring, cover[1])
    paint(t, (line(ctx, [(3.4, 4.6), (10.4, 2.8)], 0.7) > 0.5) & ~ring, cover[4])
    if deco:
        deco(ctx, t, ring, cover)
    return t


def _knowledge(ctx, t, ring, c):
    paint(t, (line(ctx, [(4.0, 6.0), (11.0, 4.4)], 0.7) > 0.5) & ~ring, GOLD_P[3])
    paint(t, (line(ctx, [(4.0, 12.4), (11.0, 10.8)], 0.7) > 0.5) & ~ring, GOLD_P[2])
    paint(t, ell(ctx, 7.6, 8.4, 1.8, 1.4), GOLD_P[3])
    paint(t, cells(ctx, [(7, 8)]), EMERALD[3])


def _written(ctx, t, ring, c):
    paint(t, (box(ctx, 5.0, 7.0, 9.6, 9.0) > 0.5) & ~ring, c[3])
    paint(t, (line(ctx, [(5.6, 7.6), (9.0, 7.6)], 0.5) > 0.5) & ~ring, c[1])
    paint(t, (line(ctx, [(9.6, 12.6), (9.6, 15.4)], 0.9) > 0.5), rgb("c42a2a"))  # ribbon
    t.alpha = np.maximum(t.alpha, line(ctx, [(9.6, 12.6), (9.6, 15.0)], 0.9))


register("item/knowledge_book", lambda ctx: book(ctx, pal("3a0a0a", "6a1414", "962424", "b83a32", "d4604a"), _knowledge))
register("item/written_book", lambda ctx: book(ctx, pal("3a1e0e", "6a3a1c", "8e5428", "ae703a", "c88e54"), _written))


@texture("item/writable_book")
def writable_book(ctx):
    b = book(ctx, pal("3a1e0e", "6a3a1c", "8e5428", "ae703a", "c88e54"))
    paint(b, box(ctx, 5.0, 7.0, 9.6, 9.0) * (1 - ctx.edge(b.alpha, 1)), rgb("ae703a"))
    quill = U(poly(ctx, [(9.0, 9.0), (12.0, 4.0), (15.0, 0.8), (14.6, 3.0), (12.6, 6.6), (10.0, 9.6)]))
    tq = spr(ctx, quill, FEATHER, bevel=1)
    paint(tq, line(ctx, [(9.4, 9.4), (14.4, 1.6)], 0.5), FEATHER[0])
    nib = spr(ctx, line(ctx, [(8.0, 11.4), (9.4, 9.4)], 0.9), pal("101010", "2a2a2a", "4a4a4a"), outline=False, bevel=1)
    return compose(ctx, b, tq, nib)


# ------------------------------------------------------------------ gear
@texture("item/name_tag")
def name_tag(ctx):
    p = pal("6a5a3e", "a89470", "cdbb92", "e2d4ae", "f2e8cc")
    tag = poly(ctx, [(5.0, 4.0), (14.0, 8.0), (11.0, 14.4), (2.0, 10.4), (2.6, 6.0)])
    t = spr(ctx, tag, p, bevel=1.5, porosity=0.4)
    paint(t, circ(ctx, 4.8, 7.0, 0.9), p[0])
    ring = ctx.edge(tag, 1) > 0
    for i in range(3):
        paint(t, (line(ctx, [(6.0 + i * 1.0, 9.0 + i * 1.4), (11.0 + i * 0.6, 11.0 + i * 1.0)], 0.5) > 0.5) & ~ring, p[1])
    s = spr(ctx, stroke(ctx, [(4.6, 7.0), (3.4, 4.0), (5.0, 1.4), (7.6, 1.6)], 0.9), STRING, outline=False, bevel=1)
    return compose(ctx, s, t)


@texture("item/lead")
def lead(ctx):
    p = pal("3a2a1a", "6a5232", "947650", "b89a70", "d6bc94")
    loop = stroke(ctx, arc_pts(9.0, 6.6, 4.4, 0, 360, 28), 1.4)
    tail = stroke(ctx, [(6.0, 10.0), (4.4, 12.6), (2.6, 14.4)], 1.4)
    t = spr(ctx, U(loop, tail), p, bevel=1)
    knot = spr(ctx, circ(ctx, 6.0, 10.0, 1.6), p, bevel=1)
    paint(t, U(*[dots(ctx, [(int(9 + 4.4 * math.cos(a)), int(6.6 + 4.4 * math.sin(a)))], 0.4)
                 for a in np.linspace(0, 2 * math.pi, 9)[:-1]]), p[1])
    return compose(ctx, t, knot)


@texture("item/saddle")
def saddle(ctx):
    p = pal("3a1e0c", "6a3a18", "925428", "b4703a", "d29254")
    seat = poly(ctx, [(1.4, 6.0), (4.0, 3.6), (7.0, 5.4), (10.0, 5.0), (13.4, 3.0), (15.0, 5.6), (13.0, 9.0),
                      (8.0, 10.0), (3.0, 9.4)])
    t = spr(ctx, seat, p, bevel=2, smooth=0.35, porosity=0.3)
    ring = ctx.edge(seat, 1) > 0
    paint(t, (line(ctx, [(3.0, 7.0), (8.0, 8.0), (13.0, 7.0)], 0.6) > 0.5) & ~ring, p[1])
    strap = spr(ctx, box(ctx, 7.0, 9.0, 9.0, 12.4), p, bevel=1)
    stirrup = metal(ctx, minus(ell(ctx, 8.0, 13.6, 2.2, 1.8), ell(ctx, 8.0, 13.8, 1.0, 0.8)), IRON_P, IRON, bevel=1)
    return compose(ctx, strap, t, stirrup)


MACE_HEAD = pal("1e1e24", "3e3e48", "60606c", "84848e", "aaaab4")
ROD = pal("3c3a6a", "6c68aa", "9a96d4", "c4c2ee", "eeeeff")


@texture("item/mace")
def mace(ctx):
    d = Diag(1.5, 14.5)
    handle = rod(ctx, [d.p(0.4, 0), d.p(11.0, 0)], 1.7, ROD)
    paint(handle, U(*[d.seg(ctx, u, u + 0.6, 2.0) for u in (2.0, 5.0, 8.0)]), ROD[1])
    head = U(d.poly(ctx, [(10.4, -2.6), (15.6, -2.6), (16.4, 0), (15.6, 2.6), (10.4, 2.6), (9.6, 0)]),
             d.rect(ctx, 11.8, -4.0, 14.2, 4.0), d.rect(ctx, 16.0, -1.0, 17.6, 1.0))
    th = metal(ctx, head, MACE_HEAD, IRON, bevel=1.5, smooth=0.55)
    ring = ctx.edge(head, 1) > 0
    paint(th, (d.rect(ctx, 11.0, -1.0, 15.0, -0.2) > 0.5) & ~ring, MACE_HEAD[4])
    paint(th, (cells(ctx, [(int(d.p(13, 0)[0]), int(d.p(13, 0)[1]))]) > 0.5), rgb("c8a040"))
    return compose(ctx, handle, th)


@texture("item/shears")
def shears(ctx):
    blade_a = poly(ctx, [(7.0, 9.0), (12.6, 2.0), (14.0, 2.4), (9.0, 10.0)])
    blade_b = poly(ctx, [(7.0, 7.0), (14.0, 3.6), (14.4, 5.0), (8.6, 9.4)])
    ta = metal(ctx, U(blade_a, blade_b), IRON_P, IRON, bevel=1)
    hp = pal("3a1e0c", "6a3a18", "925428", "b4703a")
    handles = U(minus(circ(ctx, 4.4, 11.6, 2.6), circ(ctx, 4.4, 11.6, 1.2)), minus(circ(ctx, 8.4, 12.6, 2.4), circ(ctx, 8.4, 12.6, 1.1)),
                line(ctx, [(5.4, 10.0), (7.6, 8.6)], 1.4))
    th = spr(ctx, handles, hp, bevel=1)
    rivet = spr(ctx, cells(ctx, [(7, 8)]), pal("3a3a40", "9a9aa0", "e0e0e6"), outline=False, bevel=1)
    return compose(ctx, ta, th, rivet)


TRIDENT = pal("12403a", "1e6a5e", "34927e", "5ab8a0", "9ae0cc")


@texture("item/trident")
def trident(ctx):
    d = Diag(1.0, 15.0)
    shaft = rod(ctx, [d.p(0.0, 0), d.p(13.0, 0)], 1.4, TRIDENT)
    head = U(d.rect(ctx, 12.0, -3.4, 13.4, 3.4), d.poly(ctx, [(12.6, -0.8), (19.0, -0.6), (20.4, 0), (19.0, 0.6), (12.6, 0.8)]),
             d.poly(ctx, [(12.6, -3.4), (16.6, -3.0), (17.6, -2.6), (16.6, -2.2), (12.6, -2.0)]),
             d.poly(ctx, [(12.6, 3.4), (16.6, 3.0), (17.6, 2.6), (16.6, 2.2), (12.6, 2.0)]))
    th = metal(ctx, head, TRIDENT, None, bevel=1, smooth=0.7)
    th.f0[th.alpha > 0.5] = 0.1
    grip = spr(ctx, d.rect(ctx, 1.6, -0.9, 4.0, 0.9), pal("1e2a2a", "34484a", "4e6a6a", "6a8a8a"), bevel=1)
    return compose(ctx, shaft, grip, th)


BRASS = pal("5a3a0a", "9a6a14", "c8962a", "e8c04a", "fae48a")


@texture("item/spyglass")
def spyglass(ctx):
    d = Diag(2.0, 14.0)
    body = U(d.rect(ctx, 0.0, -1.6, 8.0, 1.6), d.rect(ctx, 7.6, -1.2, 15.6, 1.2))
    t = metal(ctx, body, BRASS, COPPER, bevel=1, smooth=0.7)
    ring = ctx.edge(body, 1) > 0
    paint(t, (d.rect(ctx, 2.0, -1.6, 5.0, 1.6) > 0.5) & ~ring, pal("3a1e0c", "6a3a18")[1], metal=0)
    paint(t, (d.rect(ctx, 15.0, -1.2, 15.8, 1.2) > 0.5), rgb("8ad0e8"), metal=0)
    return t


@texture("item/spyglass_model")
def spyglass_model(ctx):
    """UV sheet for the held spyglass model: brass tube strips with leather band and lens."""
    t = metal(ctx, box(ctx, 0, 0, 16, 16), BRASS, COPPER, outline=False, bevel=1, smooth=0.7)
    k = ctx.w / 16
    y = ctx.y / k
    t.color = ctx.palette(BRASS[1:], 0.35 + 0.4 * ((np.floor(y) % 4) < 2))
    paint(t, box(ctx, 0, 6.0, 16, 9.0), rgb("6a3a18"), metal=0)
    paint(t, box(ctx, 0, 6.0, 16, 7.0), rgb("8a5228"), metal=0)
    paint(t, box(ctx, 0, 0, 4, 4), rgb("8ad0e8"), metal=0, smooth=0.95)
    paint(t, box(ctx, 0, 0, 2, 2), rgb("d0f4ff"), metal=0)
    paint(t, box(ctx, 12, 12, 16, 16), BRASS[0])
    return t


# ------------------------------------------------------------------ arrows
# Same geometry as item_1's arrow (a_tools.arrow): frame Diag(2.0, 14.0), nock u0=0.6, tip u1=16.9.
ARROW_D = (2.0, 14.0)
ARROW_U0, ARROW_U1 = 0.6, 16.9
ARROWHEAD = pal("26262a", "44444a", "66666e", "8e8e98")
TINT_HEAD = pal("bfbfbf", "cfcfcf", "dfdfdf", "efefef", "f4f4f4")  # tinted by the potion color
SPECTRAL_HEAD = pal("8a5a06", "e0a820", "f8d850", "fff09a", "fffbe0")
SPECTRAL_FEATHER = pal("a8902a", "e0c850", "f4e486", "fff6c8")


def _arrow_parts(ctx):
    d = Diag(*ARROW_D)
    u0, u1 = ARROW_U0, ARROW_U1
    head_m = d.poly(ctx, [(u1 - 3.4, -2.1), (u1, 0), (u1 - 3.4, 2.1), (u1 - 2.6, 0)])
    fl_m = d.poly(ctx, [(u0, -2.6), (u0 + 2.6, -2.6), (u0 + 5.0, 0), (u0 + 2.6, 2.6), (u0, 2.6), (u0 + 2.4, 0)])
    return d, u0, u1, head_m, fl_m


def _head_layer(ctx, hm, p, emissive=0.0):
    t = spr(ctx, hm, p, bevel=1, outline=False, emissive=emissive)
    paint(t, ctx.edge(hm, 1, "br") > 0, p[0])
    return t


def arrow_variant(ctx, kind):
    """kind: spectral | base (tipped arrow without its head) | head (tinted overlay only)."""
    d, u0, u1, hm, flm = _arrow_parts(ctx)
    band_u0 = u1 - 5.4  # tinted band of shaft right behind the head
    if kind == "head":
        band = rod(ctx, [d.p(band_u0, 0), d.p(u1 - 2.4, 0)], 1.5, TINT_HEAD[1:])
        return compose(ctx, band, _head_layer(ctx, hm, TINT_HEAD))
    if kind == "base":
        shaft = rod(ctx, [d.p(u0 + 0.6, 0), d.p(band_u0 - 0.2, 0)], 1.5, WOOD)
        fl = spr(ctx, flm, FEATHER, bevel=1, outline=False)
        return compose(ctx, fl, shaft)
    # spectral: glowing gold head, golden fletching, a glowing band behind the head
    shaft = rod(ctx, [d.p(u0 + 0.6, 0), d.p(u1 - 2.0, 0)], 1.5, WOOD)
    glow = rod(ctx, [d.p(band_u0, 0), d.p(u1 - 2.4, 0)], 1.5, SPECTRAL_HEAD[1:], emissive=0.5)
    fl = spr(ctx, flm, SPECTRAL_FEATHER, bevel=1, outline=False, emissive=0.3)
    return compose(ctx, fl, shaft, glow, _head_layer(ctx, hm, SPECTRAL_HEAD, 0.8))


register("item/spectral_arrow", lambda ctx: arrow_variant(ctx, "spectral"))
register("item/tipped_arrow_base", lambda ctx: arrow_variant(ctx, "base"))
register("item/tipped_arrow_head", lambda ctx: arrow_variant(ctx, "head"))


# ------------------------------------------------------------------ redstone etc
PLATE = pal("5a5a5e", "8a8a8e", "a6a6aa", "bcbcc0", "d2d2d6")


@texture("item/repeater")
def repeater(ctx):
    """Top-down icon: stone plate, redstone line along the centre, two torches on it."""
    plate = box(ctx, 2.0, 2.0, 14.0, 14.0)
    t = spr(ctx, plate, PLATE, bevel=1.5, porosity=0.2)
    ring = ctx.edge(plate, 1) > 0
    inner = (plate > 0.5) & ~ring
    paint(t, inner & (ctx.edge(plate, 2, "tl") > 0), PLATE[4])
    paint(t, inner & (ctx.edge(plate, 2, "br") > 0), PLATE[1])
    n = ctx.texel_noise("rep")
    paint(t, inner & ~(ctx.edge(plate, 2) > 0) & (n < 0.12), PLATE[2])
    paint(t, (box(ctx, 7.0, 3.6, 9.0, 12.6) > 0.5) & inner, PLATE[1])          # groove
    paint(t, (box(ctx, 7.4, 4.0, 8.6, 12.2) > 0.5) & inner, REDSTONE[2], emissive=0.4)  # dust line
    paint(t, cells(ctx, [(8, 12)]), REDSTONE[3], emissive=0.6)
    layers = [t]
    for y in (6.0, 12.4):
        stick = rod(ctx, [(8.0, y), (8.0, y - 1.6)], 1.4, WOOD)
        tm = box(ctx, 7.0, y - 3.6, 9.0, y - 1.6)
        tip = spr(ctx, tm, REDSTONE[1:], bevel=1, outline=False, emissive=0.9)
        paint(tip, ctx.edge(tm, 1, "br") > 0, REDSTONE[1])
        paint(tip, cells(ctx, [(7, int(y - 3.6))]), REDSTONE[4])
        layers += [stick, tip]
    return compose(ctx, *layers)


@texture("item/soul_campfire")
def soul_campfire(ctx):
    logs = pal("1e140a", "3a2814", "54401e", "6e5428", "8a6a36")
    l1 = line(ctx, [(1.6, 14.0), (14.4, 10.4)], 2.4)
    l2 = line(ctx, [(1.6, 10.4), (14.4, 14.0)], 2.4)
    t1 = spr(ctx, l1, logs, bevel=1)
    t2 = spr(ctx, l2, logs, bevel=1)
    fp = pal("0a3a4a", "1a8aa8", "4ad0e8", "a8f4ff", "f0ffff")
    flame = U(ell(ctx, 8.0, 8.6, 3.4, 4.0), poly(ctx, [(5.4, 7.0), (8.0, 1.0), (10.6, 7.0)]),
              poly(ctx, [(4.0, 10.0), (4.4, 4.0), (6.4, 8.0)]), poly(ctx, [(12.0, 10.0), (11.6, 4.6), (9.6, 8.0)]))
    tf = spr(ctx, flame, fp, bevel=2, emissive=0.9, outline=False)
    paint(tf, ell(ctx, 8.0, 9.4, 1.6, 2.2), fp[4], emissive=1.0)
    return compose(ctx, t2, tf, t1)


@texture("item/structure_void")
def structure_void(ctx):
    c = rgb("c8d8f0")
    m = U(ctx.edge(box(ctx, 4.0, 4.0, 12.0, 12.0), 1), line(ctx, [(6.0, 6.0), (10.0, 10.0)], 0.9),
          line(ctx, [(10.0, 6.0), (6.0, 10.0)], 0.9))
    return flat_layer(ctx, m, c)


TOTEM = pal("6a4a06", "b07d0d", "e2b52c", "f7dc5c", "fff6b0")


@texture("item/totem_of_undying")
def totem(ctx):
    body = U(box(ctx, 5.0, 1.6, 11.0, 7.0), box(ctx, 4.0, 7.0, 12.0, 11.0), box(ctx, 1.0, 7.4, 15.0, 9.6),
             box(ctx, 5.4, 11.0, 7.4, 14.6), box(ctx, 8.6, 11.0, 10.6, 14.6))
    t = metal(ctx, body, TOTEM, GOLD, bevel=1.5, smooth=0.7)
    ring = ctx.edge(body, 1) > 0
    paint(t, cells(ctx, [(6, 4), (9, 4)]), EMERALD[3], metal=0, smooth=0.9, f0=0.17)
    paint(t, (box(ctx, 6.0, 5.6, 10.0, 6.4) > 0.5) & ~ring, TOTEM[1])
    paint(t, (box(ctx, 5.0, 9.6, 11.0, 10.4) > 0.5) & ~ring, TOTEM[1])
    paint(t, (cells(ctx, [(2, 8), (13, 8)]) > 0.5) & ~ring, TOTEM[4])
    return t


def key(ctx, p, mid, gem_c, accent=None):
    d = Diag(2.0, 14.0)
    bit = U(d.rect(ctx, 0.0, -0.8, 9.6, 0.8), d.rect(ctx, 0.6, 0.4, 2.0, 2.6), d.rect(ctx, 2.8, 0.4, 3.8, 2.0))
    bow = minus(U(circ(ctx, *d.p(12.0, 0), 3.4)), circ(ctx, *d.p(12.0, 0), 1.4))
    m = U(bit, bow)
    t = metal(ctx, m, p, mid, bevel=1, smooth=0.6)
    gx, gy = d.p(12.0, 0)
    gm = circ(ctx, gx, gy, 1.4)
    tg = spr(ctx, gm, gem_c, outline=False, bevel=1, smooth=0.9, f0=0.17, emissive=0.5)
    out = compose(ctx, t, tg)
    if accent is not None:
        paint(out, U(*[dots(ctx, [(int(gx + 3 * math.cos(a)), int(gy + 3 * math.sin(a)))], 0.45)
                       for a in (0.8, 2.4, 4.0, 5.6)]), accent)
    return out


register("item/trial_key", lambda ctx: key(ctx, pal("4a2a14", "8a5230", "b47448", "d29a68", "ecc29a"), COPPER,
                                           pal("1e5a6a", "3a96a8", "7ad4e0", "c8f8ff")))
register("item/ominous_trial_key", lambda ctx: key(ctx, pal("14181c", "2a3036", "424a52", "5c666e", "7a868e"), None,
                                                   pal("3a0a14", "8a1a2a", "d03a4a", "ff8a8a"), rgb("4ad0c4")))


@texture("item/warped_fungus_on_a_stick")
def warped_fungus_on_a_stick(ctx):
    pts = [(2.0, 14.6), (5.0, 11.0), (8.4, 7.2), (11.6, 4.0), (14.0, 1.8)]
    r = rod(ctx, pts, 1.5, WOOD, porosity=0.2)
    grip = rod(ctx, pts[:2], 1.9, pal("2a1a10", "4a3020", "6a4630", "835b3e"))
    reel = metal(ctx, circ(ctx, 5.6, 11.6, 1.3), IRON_P, IRON, bevel=1)
    s = rod(ctx, [(14.2, 2.0), (14.3, 8.0)], 0.8, STRING)
    cap_p = pal("0e3a3a", "1a5e5a", "2a8a80", "4ab4a4", "7adcc8")
    cap = spr(ctx, minus(ell(ctx, 13.6, 10.6, 2.4, 1.8), box(ctx, 0, 11.4, 16, 16)), cap_p, bevel=1)
    paint(cap, cells(ctx, [(13, 9)]), rgb("f08a3a"))
    stem = spr(ctx, box(ctx, 13.0, 11.0, 14.4, 14.6), pal("4a2a3a", "8a5a6a", "c49aa8"), bevel=1)
    return compose(ctx, r, grip, reel, s, stem, cap)
