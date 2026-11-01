"""Nether flora (fungi, roots, sprouts, nylium, wart blocks, twisting / weeping vines),
overworld mushrooms and mushroom blocks, chorus plant / flower."""
import math

import numpy as np

from ...engine import Tex, hexc, pal
from ...registry import register
from .plants_common import (Canvas, blade, borrowed, curve, dots, ellipse, leaf, px, radial, shift, stalk,
                            union, vgrad)

CRIMSON = pal("4a0a12", "6c1018", "8e1a20", "ae2828", "c83a32", "dc5240")
WARPED = pal("0a3a38", "0e524c", "146a60", "1c8474", "2a9e88", "40b89c")
WARPED_SPOT = pal("a8480a", "d06a14", "f09028")
FUNGUS_STEM = pal("6a5a48", "86745e", "a08e76", "b8a68e", "ccbca4")
NETHERRACK = pal("3a1212", "4e1818", "621e1e", "742626", "862e2c")
BROWN_CAP = pal("4a3224", "5e402e", "745038", "8a6244", "a07650", "b48a60")
RED_CAP = pal("5a0c0c", "800e10", "a41616", "c42020", "dc3a30", "ec5a48")
MUSH_STEM = pal("a49a88", "b8ae9c", "c8bfad", "d6cebd", "e2dbcc", "ede7da")
INSIDE = pal("a8907c", "bca28c", "ccb49e", "dac4b0", "e6d4c2")
CHORUS = pal("3e2a42", "543a58", "6a4c6e", "805e84", "967298", "aa88ac")
CHORUS_FLOWER = pal("6a4c7a", "8a6a9c", "a888b8", "c2a6d0", "d8c2e2", "ece0f2")
CHORUS_DEAD = pal("4a3a3c", "5e4a4c", "72605e", "867470", "988882", "aa9c94")


# ---------------------------------------------------------------- fungi & mushrooms (cross sprites)

def fungus(ctx, cap_p, warped):
    c = Canvas(ctx)
    c.add(stalk(ctx, 8, 16.6, 8.2, 8, 2.0, 0.6, 1.6), FUNGUS_STEM, light=0.3, salt="fs")
    if warped:
        cap = union(ellipse(ctx, 8, 7.2, 5.6, 2.2), ellipse(ctx, 8, 5.8, 3.6, 2.0))
    else:
        cap = union(ellipse(ctx, 8, 6.8, 4.6, 3.2) * (ctx.y < 9), ellipse(ctx, 8, 4.6, 2.6, 2.0))
    c.add(cap, cap_p, outline=True, light=0.35, shade=vgrad(ctx, 2, 9, 0.12, -0.12), salt="fc", sss=0.3)
    spots = px(ctx, [(5, 6), (10, 5), (8, 7), (12, 7)] if warped else [(6, 5), (9, 4), (10, 7), (5, 7)])
    c.recolor(spots, WARPED_SPOT[2] if warped else hexc("f0a02a"))
    if not warped:  # hanging vine tendrils under the cap
        c.add(union(ctx.rect(4, 8, 5, 11), ctx.rect(11, 8, 12, 10)), CRIMSON, salt="ft")
    return c.done()


register("block/crimson_fungus", lambda ctx: fungus(ctx, CRIMSON, False))
register("block/warped_fungus", lambda ctx: fungus(ctx, WARPED, True))


def mushroom(ctx, red):
    c = Canvas(ctx)
    c.add(ctx.polygon([(7.0, 16.5), (7.2, 10), (8.8, 10), (9.0, 16.5)]), MUSH_STEM, light=0.3, salt="ms")
    if red:
        cap = ellipse(ctx, 8, 10.2, 4.0, 3.8) * (ctx.y < 11)
        c.add(cap, RED_CAP, outline=True, light=0.4, salt="mc")
        c.recolor(px(ctx, [(6, 8), (9, 7), (10, 9), (7, 10)]), hexc("f0ece4"))
    else:
        cap = ellipse(ctx, 8, 10.8, 5.4, 2.8) * (ctx.y < 11.4)
        c.add(cap, BROWN_CAP, outline=True, light=0.35, salt="mc")
    return c.done()


register("block/red_mushroom", lambda ctx: mushroom(ctx, True))
register("block/brown_mushroom", lambda ctx: mushroom(ctx, False))


# ---------------------------------------------------------------- roots & sprouts

def roots(ctx, p, potted):
    rng = ctx.rng("roots")
    c = Canvas(ctx)
    m = ctx.zeros()
    lo, hi = (6, 11) if potted else (1.5, 9)
    xs = (4, 6.5, 9, 11.5) if potted else (2, 4.5, 6.5, 8.5, 10.5, 13, 14.5)
    for x in xs:
        top = rng.uniform(lo, hi)
        tx = x + (x - 8) * 0.3 + rng.uniform(-1, 1)
        m = np.maximum(m, blade(ctx, (x, 16.6), (tx, top), rng.uniform(1.4, 2.0), bend=rng.uniform(-0.8, 0.8)))
        if rng.random() < 0.5:
            m = np.maximum(m, ctx.circle(tx, top + 0.8, 0.9))
    c.add(m, p, shade=vgrad(ctx, 2, 16, 0.12, -0.15), noise=0.2, light=0.25, salt="r", sss=0.4)
    return c.done()


register("block/crimson_roots", lambda ctx: roots(ctx, CRIMSON, False))
register("block/warped_roots", lambda ctx: roots(ctx, WARPED, False))
register("block/crimson_roots_pot", lambda ctx: roots(ctx, CRIMSON, True))
register("block/warped_roots_pot", lambda ctx: roots(ctx, WARPED, True))


def nether_sprouts(ctx):
    rng = ctx.rng("sprout")
    c = Canvas(ctx)
    m = ctx.zeros()
    for x in (2.5, 5, 7.5, 10, 12.5, 14):
        top = rng.uniform(10, 13.5)
        m = np.maximum(m, blade(ctx, (x, 16.6), (x + rng.uniform(-1.2, 1.2), top), 1.6, bend=rng.uniform(-0.5, 0.5)))
    c.add(m, shift(WARPED, 0.1), shade=vgrad(ctx, 10, 16, 0.12, -0.15), light=0.25, salt="ns", sss=0.4)
    return c.done()


register("block/nether_sprouts", nether_sprouts)


# ---------------------------------------------------------------- nylium & wart blocks

def _netherrack_fallback(ctx):
    n = ctx.noise(4, 2, 0.5, salt="nr")
    return Tex(ctx, ctx.palette(NETHERRACK, n * 0.6 + ctx.texel_noise("nr") * 0.4), height=0.4 + n * 0.2,
               smooth=0.15, porosity=0.3)


def fleshy(ctx, p, salt, pits=True):
    vo = ctx.voronoi(14, salt, min_dist=2.6)
    bump = np.clip(1 - vo["f1"] / 2.6, 0, 1)
    n = ctx.noise(6, 2, 0.5, salt=salt)
    lit = np.clip(-(vo["dx"] + vo["dy"]) / 2.6, -1, 1)
    v = 0.3 + bump * 0.35 + lit * 0.15 + n * 0.15 + (ctx.texel_noise(salt) - 0.5) * 0.18
    if pits:
        v = np.where((vo["f2"] - vo["f1"]) < 0.45, 0.04, v)
    return v, bump


def nylium_top(ctx, p):
    v, bump = fleshy(ctx, p, "nyl" + ctx.name)
    return Tex(ctx, ctx.palette(p, np.clip(v, 0, 1)), height=0.35 + bump * 0.45, smooth=0.25, sss=0.3, porosity=0.2)


def nylium_side(ctx, p):
    t = borrowed(ctx, "block/netherrack", _netherrack_fallback).copy()
    t.wrap = True
    rng = ctx.rng("nyside")
    L = np.array([3 + round(rng.uniform(0, 2.5)) + (rng.random() < 0.2) * 2 for _ in range(16)], np.float32)
    Lx = L[ctx.tx % 16]
    if not ctx.pixel_art:
        Lx = Lx + (ctx.noise(0.5, 1, salt="nyt", stretch=(1, 2)) - 0.5) * 0.8 * ctx.smooth_t
    m = ctx.y < Lx
    v, bump = fleshy(ctx, p, "nys", pits=False)
    v = v - np.clip(ctx.y / np.maximum(Lx, 1), 0, 1) * 0.2
    t.color = np.where(m[..., None], ctx.palette(p, np.clip(v, 0, 1)), t.color)
    t.height = np.where(m, 0.6 + bump * 0.2, t.height)
    t.sss = np.where(m, 0.3, t.sss).astype(np.float32)
    shadow = (~m) & np.roll(m, ctx.s, 0)
    t.color = np.where(shadow[..., None], t.color * 0.7, t.color)
    return t


register("block/crimson_nylium", lambda ctx: nylium_top(ctx, CRIMSON))
register("block/warped_nylium", lambda ctx: nylium_top(ctx, WARPED))
register("block/crimson_nylium_side", lambda ctx: nylium_side(ctx, CRIMSON))
register("block/warped_nylium_side", lambda ctx: nylium_side(ctx, WARPED))


def wart_block(ctx, p):
    vo = ctx.voronoi(18, "wart" + ctx.name, min_dist=2.2)
    bump = np.clip(1 - vo["f1"] / 2.4, 0, 1)
    lit = np.clip(-(vo["dx"] + vo["dy"]) / 2.4, -1, 1)
    n = ctx.noise(8, 2, 0.5, salt="wb")
    v = 0.25 + bump * 0.4 + lit * 0.18 + (n - 0.5) * 0.25 + (ctx.texel_noise("wb") - 0.5) * 0.15
    v = np.where((vo["f2"] - vo["f1"]) < 0.4, v - 0.25, v)
    return Tex(ctx, ctx.palette(p, np.clip(v, 0, 1)), height=0.3 + bump * 0.5, smooth=0.3, sss=0.35, porosity=0.1)


register("block/nether_wart_block", lambda ctx: wart_block(ctx, shift(CRIMSON, -0.08)))
register("block/warped_wart_block", lambda ctx: wart_block(ctx, shift(WARPED, -0.05)))


# ---------------------------------------------------------------- twisting / weeping vines

def nether_vine(ctx, p, up, tip):
    """up=True grows from the bottom (twisting), else hangs from the top (weeping)."""
    c = Canvas(ctx)
    m = ctx.zeros()
    strands = ((5.0, 0.0), (10.5, 2.5)) if up else ((5.5, 1.0), (10.0, 3.0))
    for i, (x, ph) in enumerate(strands):
        if tip:
            y0, y1 = (16.6, 3 + i * 3) if up else (-0.6, 12 - i * 3)
        else:
            y0, y1 = (16.6, -0.6)
        ys = np.linspace(y0, y1, 14)
        pts = [(x + math.sin(y / 16 * 4 * math.pi + ph) * 1.6, y) for y in ys]
        m = np.maximum(m, curve(ctx, pts, 1.8, 1.1 if tip else 1.8))
        for y in ys[2:-1:3]:
            xx = x + math.sin(y / 16 * 4 * math.pi + ph) * 1.6
            s = 1 if (int(y) // 3 + i) % 2 else -1
            dy = -1.8 if up else 1.8
            m = np.maximum(m, leaf(ctx, (xx, y), (xx + s * 3.0, y + dy), 1.9))
    c.add(m, p, light=0.3, noise=0.2, salt="nv", sss=0.4)
    return c.done()


register("block/twisting_vines", lambda ctx: nether_vine(ctx, WARPED, True, True))
register("block/twisting_vines_plant", lambda ctx: nether_vine(ctx, WARPED, True, False))
register("block/weeping_vines", lambda ctx: nether_vine(ctx, CRIMSON, False, True))
register("block/weeping_vines_plant", lambda ctx: nether_vine(ctx, CRIMSON, False, False))


# ---------------------------------------------------------------- mushroom blocks

def mushroom_cap_block(ctx, red):
    n = ctx.noise(6, 2, 0.5, salt="cap")
    g = ctx.texel_noise("cap")
    p = RED_CAP if red else BROWN_CAP
    v = 0.35 + n * 0.4 + (g - 0.5) * 0.25
    color = ctx.palette(p, np.clip(v, 0, 1))
    t = Tex(ctx, color, height=0.45 + n * 0.15, smooth=0.25, sss=0.2, porosity=0.2)
    if red:
        vo = ctx.voronoi(5, "spots", min_dist=6)
        spot = vo["f1"] < 1.9
        t.color = np.where(spot[..., None], ctx.palette(MUSH_STEM[2:], 0.6 + (-(vo["dx"] + vo["dy"]) / 4)), t.color)
        t.height = np.where(spot, 0.65, t.height)
    else:
        speck = ctx.texel_noise("speck", soft=True) > 0.88
        t.color = np.where(speck[..., None], p[5], t.color)
    return t


register("block/red_mushroom_block", lambda ctx: mushroom_cap_block(ctx, True))
register("block/brown_mushroom_block", lambda ctx: mushroom_cap_block(ctx, False))


def mushroom_stem(ctx):
    fib = ctx.noise(2, 2, 0.5, salt="fib", stretch=(0.5, 6))
    v = 0.3 + fib * 0.5 + (ctx.texel_noise("ms") - 0.5) * 0.2
    return Tex(ctx, ctx.palette(MUSH_STEM, np.clip(v, 0, 1)), height=0.45 + fib * 0.15, smooth=0.2, porosity=0.4,
               sss=0.2)


def mushroom_inside(ctx):
    n = ctx.noise(4, 2, 0.5, salt="ins")
    pores = (ctx.texel_noise("pore", soft=True) > 0.82) & (((ctx.tx + ctx.ty) % 2 == 0) | (not ctx.pixel_art))
    v = 0.5 + (n - 0.5) * 0.4 + (ctx.texel_noise("in") - 0.5) * 0.2
    v = np.where(pores, 0.08, v)
    return Tex(ctx, ctx.palette(INSIDE, np.clip(v, 0, 1)), height=np.where(pores, 0.25, 0.5), smooth=0.15,
               porosity=0.6, sss=0.2)


register("block/mushroom_stem", mushroom_stem)
register("block/mushroom_block_inside", mushroom_inside)


# ---------------------------------------------------------------- chorus

def chorus_plant(ctx):
    w = ctx.noise(5, 2, 0.5, salt="cho", stretch=(1, 2))
    veins = np.abs(np.sin(w * 10)) < 0.25
    v = 0.4 + w * 0.35 + (ctx.texel_noise("cho") - 0.5) * 0.2
    v = np.where(veins, v - 0.3, v)
    return Tex(ctx, ctx.palette(CHORUS, np.clip(v, 0, 1)), height=np.where(veins, 0.3, 0.5 + w * 0.15), smooth=0.2,
               porosity=0.3)


def chorus_flower(ctx, p):
    sq = np.maximum(np.abs(ctx.x - 7.5), np.abs(ctx.y - 7.5))
    d, a = radial(ctx, 7.5, 7.5)
    seg = (np.abs(ctx.x - 7.5) < 0.6) | (np.abs(ctx.y - 7.5) < 0.6)
    v = 0.75 - sq / 8 * 0.5 + (ctx.texel_noise("cf") - 0.5) * 0.15
    v = np.where(seg & (d > 1.5), v - 0.35, v)
    v = np.where(sq > 6.5, 0.12, v)
    v = np.where(d < 1.6, 0.95, v)
    return Tex(ctx, ctx.palette(p, np.clip(v, 0, 1)), height=0.4 + v * 0.3, smooth=0.25, sss=0.4, porosity=0.1,
               wrap=False)


register("block/chorus_plant", chorus_plant)
register("block/chorus_flower", lambda ctx: chorus_flower(ctx, CHORUS_FLOWER))
register("block/chorus_flower_dead", lambda ctx: chorus_flower(ctx, CHORUS_DEAD))
