"""Materials & crafting items (a-g): ingots, nuggets, gems, shards, rods,
powders, bottles, books, feather, misc drops."""
import numpy as np

from ...engine import COPPER as COPPER_ID, GOLD as GOLD_ID, pal
from ...registry import register, texture
from ...sprites import compose
from .common import AMETHYST, BONE, COPPER, DIAMOND, EMERALD, GOLD, STRING
from .a_lib import (U, arc_pts, box, circ, curve, dots, ell, inter, line, minus, paint, poly, rod, spr, stroke)

# ---------------------------------------------------------------- ingots

def ingot(ctx, p, metal_id=None, smooth=0.75, porosity=0.0, f0=0.04):
    """Bar seen from above-front: sloped top face, front and end faces."""
    top = poly(ctx, [(2.4, 8.4), (8.6, 4.6), (13.8, 7.0), (7.6, 10.8)])
    front = poly(ctx, [(1.4, 8.6), (7.6, 11.0), (7.6, 13.6), (1.4, 11.0)])
    end = poly(ctx, [(7.6, 11.0), (14.6, 7.0), (14.6, 9.6), (7.6, 13.6)])
    m = U(top, front, end, poly(ctx, [(1.4, 8.6), (8.6, 4.2), (14.6, 7.0), (7.6, 11.0)]))
    t = spr(ctx, m, p, bevel=1, smooth=smooth, porosity=porosity, f0=f0)
    ring = ctx.edge(m, 1) > 0
    paint(t, top * (~ring), p[3])
    paint(t, front * (~ring), p[2])
    paint(t, end * (~ring), p[1])
    paint(t, line(ctx, [(3.4, 8.2), (8.6, 5.2)], 0.8) * (~ring), p[4])
    paint(t, line(ctx, [(2.4, 8.8), (7.4, 10.8)], 0.7) * (~ring), p[4])
    paint(t, dots(ctx, [(9, 6)], 0.5) * (~ring), p[4])
    if metal_id:
        t.set_metal(m, metal_id)
    return t


def nugget(ctx, p, metal_id=None):
    """Three small irregular metal lumps, each with its own highlight."""
    layers = []
    for cx, cy, rx, ry, a in ((6.0, 10.4, 2.8, 2.2, 0.3), (10.6, 9.6, 2.4, 1.9, -0.4), (8.4, 6.4, 2.2, 1.8, 0.1)):
        m = U(ell(ctx, cx, cy, rx, ry, a), ell(ctx, cx + 0.6, cy - 0.5, rx * 0.7, ry * 0.8, a))
        t = spr(ctx, m, p, bevel=1.2, smooth=0.8)
        ring = ctx.edge(m, 1) > 0
        paint(t, dots(ctx, [(cx - 1.4, cy - 1.2)], 0.5) * (~ring), p[4])
        paint(t, dots(ctx, [(cx + 0.6, cy + 0.6)], 0.45) * (~ring), p[1])
        if metal_id:
            t.set_metal(m, metal_id)
        layers.append(t)
    return compose(ctx, *layers)


register("item/gold_ingot", lambda ctx: ingot(ctx, GOLD, GOLD_ID))
register("item/copper_ingot", lambda ctx: ingot(ctx, COPPER, COPPER_ID, 0.65))
register("item/gold_nugget", lambda ctx: nugget(ctx, GOLD, GOLD_ID))
register("item/copper_nugget", lambda ctx: nugget(ctx, COPPER, COPPER_ID))
register("item/brick", lambda ctx: ingot(ctx, pal("4a1e12", "7e3622", "a44c32", "c46646", "da8a66"), None, 0.2, 0.5))

# ------------------------------------------------------------------ gems


def gem_tex(ctx, mask, p, facets, emissive=0.0, smooth=0.9, f0=0.17):
    t = spr(ctx, mask, p, bevel=1, smooth=smooth, f0=f0, emissive=emissive)
    ring = ctx.edge(mask, 1) > 0
    for fm, idx in facets:
        paint(t, fm * (~ring), p[idx])
    t.height = np.where(mask > 0.5, 0.75, 0)
    return t


@texture("item/diamond")
def diamond(ctx):
    m = poly(ctx, [(2.0, 6.0), (5.4, 2.4), (10.6, 2.4), (14.0, 6.0), (8.0, 14.6)])
    p = DIAMOND
    f = [(poly(ctx, [(2, 6), (8, 6), (8, 14.6)]), 2),
         (poly(ctx, [(8, 6), (14, 6), (8, 14.6)]), 1),
         (poly(ctx, [(5.4, 6), (8, 6), (8, 12)]), 3),
         (poly(ctx, [(2, 6), (5.4, 2.4), (6.6, 6)]), 3),
         (poly(ctx, [(5.4, 2.4), (10.6, 2.4), (9.6, 6), (6.6, 6)]), 4),
         (poly(ctx, [(10.6, 2.4), (14, 6), (9.6, 6)]), 2)]
    t = gem_tex(ctx, m, p, f)
    paint(t, dots(ctx, [(6, 3), (5, 4)], 0.5) * (~(ctx.edge(m, 1) > 0)), pal("ffffff")[0])
    return t


@texture("item/emerald")
def emerald(ctx):
    m = poly(ctx, [(8, 1.4), (12.4, 4.6), (12.4, 11.4), (8, 14.6), (3.6, 11.4), (3.6, 4.6)])
    p = EMERALD
    table = poly(ctx, [(8, 4.2), (10.2, 5.8), (10.2, 10.2), (8, 11.8), (5.8, 10.2), (5.8, 5.8)])
    f = [(poly(ctx, [(8, 1.4), (12.4, 4.6), (12.4, 8), (3.6, 8), (3.6, 4.6)]), 3),
         (poly(ctx, [(3.6, 8), (12.4, 8), (12.4, 11.4), (8, 14.6), (3.6, 11.4)]), 1),
         (poly(ctx, [(8, 8), (12.4, 4.6), (12.4, 11.4)]), 2),
         (table, 2), (inter(table, box(ctx, 0, 0, 8, 8)), 4)]
    return gem_tex(ctx, m, p, f)


def shard(ctx, base, tip, w):
    """Pointed prism from base to tip with half-width w."""
    bx, by = base
    tx, ty = tip
    dx, dy = tx - bx, ty - by
    n = np.hypot(dx, dy)
    nx, ny = -dy / n * w, dx / n * w
    return poly(ctx, [(bx + nx, by + ny), (tx - dx * 0.25 + nx, ty - dy * 0.25 + ny), (tx, ty),
                      (tx - dx * 0.25 - nx, ty - dy * 0.25 - ny), (bx - nx, by - ny)]), (nx, ny)


@texture("item/amethyst_shard")
def amethyst_shard(ctx):
    layers = []
    for base, tip, w in (((5.0, 14.4), (2.6, 5.6), 1.5), ((11.0, 14.4), (13.6, 6.4), 1.5), ((8.0, 14.6), (8.4, 1.6), 2.2)):
        m, (nx, ny) = shard(ctx, base, tip, w)
        t = spr(ctx, m, AMETHYST, bevel=1, smooth=0.9, f0=0.1)
        ring = ctx.edge(m, 1) > 0
        half = poly(ctx, [base, tip, (base[0] - nx * 2, base[1] - ny * 2), (tip[0] - nx * 2, tip[1] - ny * 2)])
        paint(t, inter(m, half) * (~ring), AMETHYST[3])
        layers.append(t)
    t = compose(ctx, *layers)
    paint(t, line(ctx, [(7.6, 4.0), (7.6, 9.0)], 0.6), AMETHYST[4])
    return t


@texture("item/echo_shard")
def echo_shard(ctx):
    p = pal("041a1e", "0a3438", "0f5056", "1a7a7c", "4ec2bc")
    m = poly(ctx, [(4.0, 14.0), (2.6, 9.0), (6.0, 4.0), (10.6, 1.6), (13.6, 4.0), (12.0, 9.0), (8.0, 13.6)])
    f = [(poly(ctx, [(6.0, 4.0), (10.6, 1.6), (9.0, 8.0)]), 3),
         (poly(ctx, [(10.6, 1.6), (13.6, 4.0), (12.0, 9.0), (9.0, 8.0)]), 2),
         (poly(ctx, [(2.6, 9.0), (6.0, 4.0), (9.0, 8.0), (4.0, 14.0)]), 2),
         (poly(ctx, [(9.0, 8.0), (12.0, 9.0), (8.0, 13.6), (4.0, 14.0)]), 1)]
    t = gem_tex(ctx, m, p, f, smooth=0.8, f0=0.08)
    core = line(ctx, [(5.6, 11.0), (8.0, 7.0), (10.6, 4.0)], 0.8) * (~(ctx.edge(m, 1) > 0))
    paint(t, core, pal("7ef4ec")[0])
    t.emissive = np.where(core > 0.5, 0.6, 0.0)
    return t


@texture("item/disc_fragment_5")
def disc_fragment_5(ctx):
    p = pal("0e0e12", "1c1c22", "2a2a32", "3a3a44", "50505c")
    m = poly(ctx, [(2.0, 13.6), (4.0, 5.0), (9.0, 2.0), (14.0, 3.0), (10.6, 8.6), (11.4, 12.0), (6.0, 14.6)])
    t = spr(ctx, m, p, bevel=1, smooth=0.7)
    ring = ctx.edge(m, 1) > 0
    for r in (6.0, 9.0):
        paint(t, stroke(ctx, arc_pts(15.0, 15.0, r, 180, 270, 16), 0.6) * (~ring), p[3])
    paint(t, stroke(ctx, arc_pts(15.0, 15.0, 7.6, 190, 260, 16), 1.0) * (~ring), pal("2a8a8e")[0])
    return t


# ------------------------------------------------------------ fuels etc

def lump(ctx, p, salt, smooth=0.3):
    m = poly(ctx, [(2.4, 9.0), (4.0, 4.6), (8.0, 2.6), (12.4, 3.8), (14.0, 8.0), (12.6, 12.6), (8.0, 14.2),
                   (4.0, 13.0)])
    t = spr(ctx, m, p, bevel=2.0, smooth=smooth)
    ring = ctx.edge(m, 1) > 0
    f = [(poly(ctx, [(4.0, 4.6), (8.0, 2.6), (8.6, 7.0), (4.6, 8.6)]), 3),
         (poly(ctx, [(8.0, 2.6), (12.4, 3.8), (11.4, 7.6), (8.6, 7.0)]), 2),
         (poly(ctx, [(8.6, 7.0), (11.4, 7.6), (12.6, 12.6), (8.0, 11.0)]), 1),
         (poly(ctx, [(4.6, 8.6), (8.6, 7.0), (8.0, 11.0), (4.0, 13.0)]), 2)]
    for fm, idx in f:
        paint(t, fm * (~ring), p[idx])
    paint(t, dots(ctx, [(5, 5), (9, 4)], 0.5) * (~ring), p[4])
    return t


@texture("item/coal")
def coal(ctx):
    p = pal("0c0c0e", "24242a", "3a3a42", "5a5a66", "8e8e9c")
    m = poly(ctx, [(2.0, 9.6), (3.6, 4.4), (7.4, 2.0), (11.6, 2.8), (14.2, 6.6), (13.6, 11.6), (9.4, 14.4),
                   (4.4, 13.6)])
    t = spr(ctx, m, p, bevel=1.5, smooth=0.55)
    ring = ctx.edge(m, 1) > 0
    facets = [(poly(ctx, [(3.6, 4.4), (7.4, 2.0), (8.2, 6.4), (4.6, 8.4)]), 3),
              (poly(ctx, [(7.4, 2.0), (11.6, 2.8), (11.0, 6.8), (8.2, 6.4)]), 2),
              (poly(ctx, [(11.6, 2.8), (14.2, 6.6), (11.0, 6.8)]), 1),
              (poly(ctx, [(2.0, 9.6), (4.6, 8.4), (6.6, 12.6), (4.4, 13.6)]), 2),
              (poly(ctx, [(4.6, 8.4), (8.2, 6.4), (11.0, 6.8), (10.4, 10.6), (6.6, 12.6)]), 2),
              (poly(ctx, [(11.0, 6.8), (14.2, 6.6), (13.6, 11.6), (10.4, 10.6)]), 1),
              (poly(ctx, [(6.6, 12.6), (10.4, 10.6), (13.6, 11.6), (9.4, 14.4)]), 0)]
    for fm, idx in facets:
        paint(t, fm * (~ring), p[idx])
    edges = U(line(ctx, [(4.6, 8.4), (8.2, 6.4), (11.0, 6.8)], 0.6), line(ctx, [(7.4, 2.4), (8.2, 6.4)], 0.6))
    paint(t, edges * (~ring), p[4])
    paint(t, dots(ctx, [(5, 4), (9, 3)], 0.45), pal("9a9aa8")[0])
    return t


@texture("item/charcoal")
def charcoal(ctx):
    p = pal("140e0a", "241a12", "36281c", "4a3828", "64503c")
    m = poly(ctx, [(2.0, 11.0), (8.4, 2.6), (14.0, 4.4), (14.0, 6.6), (7.6, 14.0), (2.0, 13.6)])
    t = spr(ctx, m, p, bevel=1.5, porosity=0.6)
    ring = ctx.edge(m, 1) > 0
    for i in range(3):
        paint(t, line(ctx, [(3.6 + i * 2.0, 12.0), (9.6 + i * 1.6, 4.4)], 0.6) * (~ring), p[1 + (i % 2) * 2])
    paint(t, U(line(ctx, [(9.0, 3.6), (13.0, 5.0)], 0.6)) * (~ring), p[4])
    return t


@texture("item/flint")
def flint(ctx):
    p = pal("1c1c20", "323238", "4a4a52", "64646e", "84848e")
    m = poly(ctx, [(3.0, 12.0), (3.4, 6.6), (7.0, 2.6), (11.6, 3.4), (13.4, 8.0), (11.0, 13.0), (6.6, 14.4)])
    t = spr(ctx, m, p, bevel=1.5, smooth=0.5)
    ring = ctx.edge(m, 1) > 0
    paint(t, poly(ctx, [(4.6, 7.0), (7.4, 4.0), (9.6, 5.6), (6.4, 8.8)]) * (~ring), p[4])
    paint(t, stroke(ctx, arc_pts(5.0, 13.0, 4.6, -80, 0, 8), 0.7) * (~ring), p[1])
    paint(t, stroke(ctx, arc_pts(5.0, 13.0, 7.0, -70, -10, 8), 0.7) * (~ring), p[1])
    return t


@texture("item/clay_ball")
def clay_ball(ctx):
    p = pal("4e5260", "7a8090", "9aa0ae", "b4bac6", "ccd2dc")
    m = U(ell(ctx, 8.0, 9.0, 5.6, 4.8), circ(ctx, 6.0, 6.6, 2.6))
    t = spr(ctx, m, p, bevel=3.0, porosity=0.6)
    ring = ctx.edge(m, 1) > 0
    paint(t, dots(ctx, [(5, 6), (6, 5)], 0.5) * (~ring), p[4])
    paint(t, line(ctx, [(9.0, 11.6), (11.6, 10.0)], 0.6) * (~ring), p[1])
    return t


@texture("item/bone")
def bone(ctx):
    p = pal("6e6656", "a8a090", "d4ccb8", "eee8d8", "fcfaf2")
    m = U(line(ctx, [(4.4, 11.6), (11.6, 4.4)], 2.2), circ(ctx, 3.0, 11.4, 1.6), circ(ctx, 4.6, 13.0, 1.6),
          circ(ctx, 11.4, 3.0, 1.6), circ(ctx, 13.0, 4.6, 1.6))
    return spr(ctx, m, p, bevel=1.2, porosity=0.3)


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


register("item/bone_meal", lambda ctx: powder(ctx, pal("8a8678", "c2beb0", "deded2", "f0f0e8", "ffffff"), salt="bm"))
register("item/blaze_powder", lambda ctx: powder(ctx, pal("8a3a04", "d06a0a", "f29a1a", "ffc848", "fff0a0"), 0.6,
                                                 salt="bp"))
register("item/glowstone_dust", lambda ctx: powder(ctx, pal("7a5418", "b88a2a", "e8c050", "fbe486", "fffad0"),
                                                   0.75, pal("ffffe8")[0], salt="gd"))
register("item/gunpowder", lambda ctx: powder(ctx, pal("1e1e20", "3a3a3e", "56565c", "74747a", "96969c"),
                                              salt="gp"))


def magic_rod(ctx, p, emissive, bands=None):
    m = line(ctx, [(3.0, 13.0), (13.0, 3.0)], 2.2)
    t = spr(ctx, m, p, bevel=1.2, emissive=emissive, smooth=0.5)
    ring = ctx.edge(m, 1) > 0
    paint(t, line(ctx, [(4.0, 11.6), (11.6, 4.0)], 0.6) * (~ring), p[4])
    if bands is not None:
        for u in (5.0, 8.0, 11.0):
            paint(t, line(ctx, [(u - 1.8, 16 - u - 0.2), (u - 0.2, 16 - u + 1.6)], 0.9) * (~ring), bands)
    return t


register("item/blaze_rod", lambda ctx: magic_rod(ctx, pal("7a3404", "d0700c", "f6a420", "ffd250", "fff6b0"), 0.75,
                                                 pal("c45a08")[0]))


@texture("item/breeze_rod")
def breeze_rod(ctx):
    p = pal("3c3a6a", "6c68aa", "9a96d4", "c4c2ee", "eeeeff")
    t = magic_rod(ctx, p, 0.0)
    m = t.alpha > 0.5
    wind = U(stroke(ctx, arc_pts(5.6, 10.4, 2.2, 140, 330, 10), 0.7),
             stroke(ctx, arc_pts(10.4, 5.6, 2.2, 140, 330, 10), 0.7))
    paint(t, wind, p[1])
    return t


# --------------------------------------------------------------- bottles

GLASS = pal("4a6a7a", "86a8b8", "b6d2de", "e4f4fa")


def bottle(ctx, liquid=None, emissive=0.0, swirl=None):
    body = circ(ctx, 8.0, 10.6, 4.6)
    neck = box(ctx, 6.6, 3.4, 9.4, 7.0)
    lip = box(ctx, 6.0, 2.0, 10.0, 3.6)
    m = U(body, neck, lip)
    ring = ctx.edge(m, 1) > 0
    color = np.zeros((ctx.H, ctx.W, 3), np.float32)
    t = spr(ctx, m, GLASS, bevel=1, smooth=0.95)
    alpha = ring.astype(np.float32)
    alpha = np.maximum(alpha, lip)
    paint(t, lip * (~ring), GLASS[2])
    inner = (m > 0.5) & ~ring
    if liquid is not None:
        lm = inter(circ(ctx, 8.0, 10.6, 3.6), box(ctx, 0, 8.0, 16, 16)) * inner
        tl = spr(ctx, lm, liquid, outline=False, bevel=2, emissive=emissive, smooth=0.8)
        alpha = np.maximum(alpha, lm)
        t.color = np.where((lm > 0.5)[..., None], tl.color, t.color)
        t.emissive = np.where(lm > 0.5, emissive, 0.0)
        paint(t, inter(lm, box(ctx, 0, 8.0, 16, 9.0)), liquid[-1])
        if swirl is not None:
            sw = stroke(ctx, arc_pts(8.0, 11.0, 2.0, 200, 470, 16), 0.7) * lm
            paint(t, sw, swirl)
    gl = U(line(ctx, [(5.6, 9.6), (5.6, 11.6)], 0.8), dots(ctx, [(6, 8)], 0.45))
    alpha = np.maximum(alpha, gl * inner)
    paint(t, gl * inner, GLASS[3])
    t.alpha = alpha * (m > 0.5)
    return t


def glass_filled(ctx, liquid=None, emissive=0.0, sparkle=None):
    """Bottle in the shared potion geometry (h_liquids). Empty glass is drawn as
    pale tinted glass (opaque, crisp) so the bottle reads as a solid object."""
    from . import h_liquids as HL
    t = HL.bottle(ctx, liquid, emissive)
    body, neck, lip = HL._bottle_masks(ctx)
    m = (U(body, neck) > 0.5)
    ring = ctx.edge(U(body, neck, lip), 1) > 0
    empty = m & (t.alpha < 0.5)
    k = ctx.w / 16
    yy = ctx.y / k
    shade = np.clip((yy - 4) / 11, 0, 1)[..., None]
    pale = GLASS[3] * (1 - shade) + GLASS[2] * shade
    t.color = np.where(empty[..., None], pale, t.color)
    t.alpha = np.where(empty, 1.0, t.alpha)
    t.height = np.where(empty, 0.7, t.height)
    t.smooth = np.where(empty, 0.95, t.smooth)
    # glass shading: darker right side, bright streak on the left
    paint(t, inter(circ(ctx, 9.6, 11.6, 3.2), box(ctx, 9.6, 0, 16, 16)) * empty, GLASS[2] * 0.92)
    paint(t, U(line(ctx, [(5.6, 9.4), (5.6, 11.8)], 0.9), dots(ctx, [(7, 4)], 0.45)) * (~ring), pal("ffffff")[0])
    if sparkle is not None and liquid is not None:
        paint(t, dots(ctx, [(9, 11), (7, 13), (10, 13)], 0.45), sparkle)
    return t


register("item/glass_bottle", lambda ctx: glass_filled(ctx))
register("item/experience_bottle", lambda ctx: glass_filled(
    ctx, pal("2e6a0a", "58a814", "8ad62a", "c4f45a", "f0ffb0"), 0.8, pal("ffffc0")[0]))
register("item/dragon_breath", lambda ctx: glass_filled(
    ctx, pal("5a1a4a", "9a3a80", "cc62ae", "eea2d2", "ffd8f0"), 0.5, pal("fff0fa")[0]))


# ------------------------------------------------------------------ books

def book(ctx, cover, enchanted=False):
    m = poly(ctx, [(2.0, 4.0), (10.6, 2.0), (14.0, 4.6), (14.0, 12.6), (5.4, 14.6), (2.0, 12.0)])
    t = spr(ctx, m, cover, bevel=1.5, porosity=0.3)
    ring = ctx.edge(m, 1) > 0
    pages = poly(ctx, [(5.4, 6.6), (14.0, 4.6), (14.0, 12.6), (5.4, 14.6)])
    front = poly(ctx, [(2.0, 4.0), (10.6, 2.0), (12.6, 3.6), (4.0, 5.6)])
    paint(t, poly(ctx, [(10.6, 2.0), (14.0, 4.6), (14.0, 12.6), (12.4, 11.6), (12.4, 3.6)]) * (~ring),
          pal("f2ead6")[0])
    for y in (5.6, 7.6, 9.6):
        paint(t, line(ctx, [(12.8, y), (13.6, y + 0.6)], 0.5) * (~ring), pal("b8ae96")[0])
    paint(t, line(ctx, [(2.6, 4.6), (2.6, 11.6)], 0.8) * (~ring), cover[1])
    paint(t, line(ctx, [(3.4, 4.6), (10.4, 2.8)], 0.7) * (~ring), cover[4])
    if enchanted:
        gold = GOLD
        paint(t, line(ctx, [(4.0, 6.0), (11.0, 4.4)], 0.7) * (~ring), gold[3])
        paint(t, line(ctx, [(4.0, 12.4), (11.0, 10.8)], 0.7) * (~ring), gold[2])
        paint(t, ell(ctx, 7.6, 8.4, 1.6, 1.2), gold[3])
        paint(t, dots(ctx, [(7, 7)], 0.4), gold[4])
    else:
        paint(t, box(ctx, 5.0, 7.0, 9.6, 9.0) * (~ring), cover[3])
        paint(t, line(ctx, [(5.6, 7.6), (9.0, 7.6)], 0.5) * (~ring), cover[1])
    return t


register("item/book", lambda ctx: book(ctx, pal("3a1e0e", "6a3a1c", "8e5428", "ae703a", "c88e54")))
register("item/enchanted_book", lambda ctx: book(ctx, pal("2a0e3a", "4e1c6a", "7030a0", "9454c8", "b884e6"), True))


# ------------------------------------------------------------ misc drops

@texture("item/feather")
def feather(ctx):
    vane = poly(ctx, [(3.6, 12.4), (5.0, 8.0), (8.4, 4.0), (12.4, 1.6), (14.4, 1.6), (13.6, 4.4), (11.0, 8.4),
                      (7.4, 11.6)])
    t = spr(ctx, vane, pal("7a7a80", "b8b8be", "dcdce2", "f2f2f6", "ffffff"), bevel=1.5)
    ring = ctx.edge(vane, 1) > 0
    for a in ((6.0, 8.6), (8.6, 5.8), (11.0, 3.4)):
        paint(t, line(ctx, [a, (a[0] + 1.6, a[1] + 1.8)], 0.5) * (~ring), pal("a8a8ae")[0])
    quill = rod(ctx, [(1.6, 14.4), (5.0, 11.0), (13.6, 2.4)], 1.0, pal("6e6656", "c8c0a8", "efe8d6"))
    return compose(ctx, t, quill)


@texture("item/ender_pearl")
def ender_pearl(ctx):
    p = pal("041e1c", "0a3a36", "126058", "2a8a7e", "6ac8b8")
    m = circ(ctx, 8.0, 8.0, 5.8)
    t = spr(ctx, m, p, bevel=3.0, light=0.35, smooth=0.85, f0=0.06)
    ring = ctx.edge(m, 1) > 0
    sw = stroke(ctx, arc_pts(8.0, 8.0, 2.8, 160, 420, 18), 0.8)
    paint(t, sw * (~ring), p[1])
    paint(t, dots(ctx, [(5, 5), (6, 4)], 0.5), p[4])
    return t


@texture("item/ender_eye")
def ender_eye(ctx):
    p = pal("06301a", "0e5a30", "1e8a4a", "48bc6e", "9cf0b0")
    m = circ(ctx, 8.0, 8.0, 5.8)
    t = spr(ctx, m, p, bevel=3.0, light=0.35, smooth=0.85, f0=0.06)
    iris = ell(ctx, 8.0, 8.0, 2.6, 3.4)
    paint(t, iris, pal("c8e85a")[0])
    pupil = ell(ctx, 8.0, 8.0, 0.9, 2.6)
    paint(t, pupil, pal("0a140a")[0])
    paint(t, dots(ctx, [(5, 5)], 0.5), p[4])
    t.emissive = np.where(iris * (pupil < 0.5) > 0.5, 0.7, 0.0)
    return t


@texture("item/fire_charge")
def fire_charge(ctx):
    p = pal("140a06", "2a160c", "422414", "5a3420", "74462c")
    m = circ(ctx, 8.0, 8.0, 5.6)
    t = spr(ctx, m, p, bevel=3.0, porosity=0.5)
    ring = ctx.edge(m, 1) > 0
    cracks = U(line(ctx, [(4.0, 6.0), (6.6, 7.6), (7.6, 10.6), (10.6, 12.0)], 0.8),
               line(ctx, [(6.6, 7.6), (10.0, 5.0), (12.0, 6.6)], 0.8),
               line(ctx, [(7.6, 10.6), (5.0, 12.0)], 0.7)) * (~ring)
    paint(t, cracks, pal("f2901a")[0])
    paint(t, dots(ctx, [(6, 7), (9, 5)], 0.4), pal("ffe070")[0])
    t.emissive = np.where(cracks > 0.5, 0.8, 0.0)
    return t


@texture("item/ghast_tear")
def ghast_tear(ctx):
    p = pal("3a6a7a", "7aaebe", "acd8e4", "d8f2f8", "ffffff")
    m = U(circ(ctx, 8.0, 10.4, 3.4), poly(ctx, [(4.9, 9.4), (8.0, 2.4), (11.1, 9.4)]))
    t = spr(ctx, m, p, bevel=2.0, smooth=0.95, emissive=0.15)
    paint(t, dots(ctx, [(6, 9), (7, 7)], 0.5), p[4])
    return t


@texture("item/glow_ink_sac")
def glow_ink_sac(ctx):
    p = pal("06302e", "0e5450", "15807a", "2ab4a8", "7af0e0")
    m = U(ell(ctx, 8.0, 10.0, 5.4, 4.6), poly(ctx, [(6.0, 6.0), (7.2, 2.4), (8.8, 2.4), (10.0, 6.0)]))
    t = spr(ctx, m, p, bevel=2.5, sss=0.3)
    spots = dots(ctx, [(5, 9), (9, 8), (7, 11), (10, 12), (8, 4)], 0.6) * (~(ctx.edge(m, 1) > 0))
    paint(t, spots, pal("b4fff2")[0])
    t.emissive = np.where(spots > 0.5, 0.9, np.where(m > 0.5, 0.25, 0.0))
    tie = spr(ctx, box(ctx, 6.4, 5.0, 9.6, 6.4), pal("042220", "0a3a36", "126058"), bevel=1)
    return compose(ctx, t, tie)


@texture("item/goat_horn")
def goat_horn(ctx):
    p = pal("4a4034", "7e7262", "a89a86", "ccc0ac", "e8e0d0")
    pts = [(2.6, 13.4), (3.2, 8.0), (6.4, 4.6), (10.0, 3.6), (13.0, 4.8)]
    from .a_lib import bez_pts
    pts = bez_pts((2.4, 13.6), (3.0, 3.0), (12.4, 4.6), 16)
    m = U(stroke(ctx, pts, 2.4, 5.2), ell(ctx, 12.6, 5.0, 1.8, 3.0, 0.2))
    t = spr(ctx, m, p, bevel=1.5, porosity=0.3)
    ring = ctx.edge(m, 1) > 0
    for i in (4, 7, 10, 13):
        x, y = pts[i]
        paint(t, circ(ctx, x, y, 0.45 + i * 0.07) * (~ring), p[1])
    paint(t, ell(ctx, 13.0, 4.9, 0.8, 1.8, 0.2), p[0])
    paint(t, line(ctx, [(3.4, 10.0), (4.6, 6.6)], 0.6) * (~ring), p[4])
    return t


@texture("item/armadillo_scute")
def armadillo_scute(ctx):
    """A single shell plate: rounded shield, pink-brown, with overlapping bands."""
    p = pal("4a2420", "7e3e36", "a8584c", "c87a6a", "e2a292")
    m = U(poly(ctx, [(2.0, 4.0), (8.0, 2.0), (14.0, 4.0), (13.4, 10.0), (8.0, 14.6), (2.6, 10.0)]))
    t = spr(ctx, m, p, bevel=2.0, smooth=0.5)
    ring = ctx.edge(m, 1) > 0
    for y0 in (5, 8, 11):
        paint(t, inter(m, box(ctx, 0, y0, 16, y0 + 1)) * (~ring), p[1])
        paint(t, inter(m, box(ctx, 0, y0 + 1, 16, y0 + 2)) * (~ring), p[3])
    paint(t, line(ctx, [(4.0, 4.2), (8.0, 3.0), (12.0, 4.2)], 0.7) * (~ring), p[4])
    paint(t, line(ctx, [(8.0, 3.4), (8.0, 13.0)], 0.6) * (~ring), p[2])
    return t
