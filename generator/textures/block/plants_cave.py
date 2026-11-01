"""Lush / pale garden / deep dark plants: dripleaves, moss, pale moss, glow lichen, cave vines,
spore blossom, hanging roots, resin clump, sculk catalyst bloom, shelf mushroom."""
import math

import numpy as np

from ...engine import Tex, hexc, pal
from ...registry import register
from .plants_common import (LEAF, Canvas, borrowed, curve, dots, ellipse, leaf, petals, phase, px, radial,
                            shift, stalk, union, vgrad)

DRIP = pal("2a5a18", "36701e", "448626", "529c2e", "64b038", "7ac446")
DRIP_STEM = pal("2c4a16", "3a5e1c", "4a7424", "5a8a2c", "6ca034")
MOSS = pal("33501c", "3f6222", "4c7428", "5a862f", "689638", "78a642")
PALE_MOSS = pal("5a6058", "6c7469", "7f877b", "929a8d", "a4ac9f", "b6bdb0")
LICHEN = pal("3a5a4e", "4a6e5e", "5c8470", "709a82", "88b294")
VINE = pal("2a4a16", "34601a", "427422", "52882a", "64a034")
BERRY = pal("8a3a06", "c45a0a", "ec8418", "fbb03a", "ffdc78")
SPORE = pal("8a2a5a", "b03c78", "d05a96", "e682b4", "f4aed0")
ROOT = pal("4a3020", "60402a", "765236", "8c6644", "a07a54")
RESIN = pal("6a2a04", "9a4206", "c8620c", "e8841a", "f8aa36", "ffd27a")
SHELF = pal("4a3020", "634026", "7c5430", "96683c", "ae7e4c", "c4965e")


# ---------------------------------------------------------------- dripleaves

def leaf_top(ctx, p, rounded, vein_from, salt):
    sq = np.maximum(np.abs(ctx.x - 8), np.abs(ctx.y - 8))
    corner = np.hypot(np.maximum(np.abs(ctx.x - 8) - (8 - rounded), 0), np.maximum(np.abs(ctx.y - 8) - (8 - rounded), 0))
    m = (corner < rounded).astype(np.float32)
    d, a = radial(ctx, *vein_from)
    vein = (np.abs(np.sin(a * 4)) < 0.12) & (d > 1) | (np.abs(ctx.x - vein_from[0]) < 0.5) & (ctx.y < vein_from[1])
    c = Canvas(ctx)
    c.add(m, p, outline=True, light=0.15, noise=0.18, bevel=3, shade=-np.clip(sq / 8, 0, 1) * 0.1, salt=salt)
    c.recolor(vein.astype(np.float32) * (sq < 7), p[2])
    return c.done()


register("block/big_dripleaf_top", lambda ctx: leaf_top(ctx, DRIP, 3.0, (8, 8), "bdt"))
register("block/small_dripleaf_top", lambda ctx: leaf_top(ctx, shift(DRIP, 0.05), 5.0, (8, 15), "sdt"))


def leaf_side(ctx, p, rows):
    c = Canvas(ctx)
    c.add(ctx.rect(0, 0, 16, rows), p, light=0.2, noise=0.25, bevel=1, salt="ls")
    return c.done()


register("block/big_dripleaf_side", lambda ctx: leaf_side(ctx, DRIP, 3))
register("block/small_dripleaf_side", lambda ctx: leaf_side(ctx, shift(DRIP, 0.05), 2))


def drip_stem(ctx, top_flare=False, width=2.0):
    c = Canvas(ctx)
    c.add(ctx.rect(8 - width / 2, 0 if not top_flare else 2, 8 + width / 2, 16), DRIP_STEM, light=0.3, bevel=1, salt="ds")
    if top_flare:
        c.add(ctx.polygon([(8 - width / 2, 6), (3.5, 0), (12.5, 0), (8 + width / 2, 6)]), DRIP, light=0.3, salt="dsf")
    c.recolor(ctx.rect(8 - width / 2, 0, 8 - width / 2 + 1, 16) * (ctx.texel_noise("dsn") > 0.6), DRIP_STEM[4])
    return c.done()


register("block/big_dripleaf_stem", lambda ctx: drip_stem(ctx))
register("block/big_dripleaf_tip", lambda ctx: drip_stem(ctx, True))


def small_drip_stem(ctx, top):
    c = Canvas(ctx)
    m = union(stalk(ctx, 6, 16.5, 5, -0.5 if not top else 6, 1, -0.4), stalk(ctx, 10, 16.5, 11, -0.5 if not top else 4, 1, 0.4))
    if top:
        m = np.maximum(m, union(stalk(ctx, 5, 6.5, 3, 0, 1, -0.5), stalk(ctx, 11, 4.5, 13, 0, 1, 0.5)))
    c.add(m, DRIP_STEM, light=0.2, salt="sds")
    return c.done()


register("block/small_dripleaf_stem_bottom", lambda ctx: small_drip_stem(ctx, False))
register("block/small_dripleaf_stem_top", lambda ctx: small_drip_stem(ctx, True))


# ---------------------------------------------------------------- moss

def moss(ctx, p, salt):
    n = ctx.noise(5, 3, 0.55, salt=salt)
    g = ctx.texel_noise(salt)
    clump = ctx.voronoi(9, salt, min_dist=3.2)
    puff = np.clip(1 - clump["f1"] / 3.2, 0, 1)
    v = puff * 0.45 + n * 0.3 + g * 0.3 - 0.05
    v = np.where((clump["f2"] - clump["f1"]) < 0.5, v - 0.25, v)
    return Tex(ctx, ctx.palette(p, np.clip(v, 0, 1)), height=0.3 + puff * 0.5 + g * 0.1, smooth=0.05, sss=0.35,
               porosity=0.4)


register("block/moss_block", lambda ctx: moss(ctx, MOSS, "moss"))
register("block/pale_moss_block", lambda ctx: moss(ctx, PALE_MOSS, "palemoss"))
register("block/pale_moss_carpet", lambda ctx: moss(ctx.sub("block/pale_moss_block"), PALE_MOSS, "palemoss"))


def moss_fringe(ctx, length):
    rng = ctx.rng("pmf")
    L = np.array([length * rng.uniform(0.45, 1.0) for _ in range(16)], np.float32)
    L = np.maximum(L, np.roll(L, 1) * 0.7)
    Lx = L[ctx.tx % 16]
    m = (ctx.y < Lx).astype(np.float32)
    c = Canvas(ctx)
    c.add(m, PALE_MOSS, noise=0.3, light=0.15, shade=-np.clip(ctx.y / max(1, length), 0, 1) * 0.2, bevel=1, salt="pmf")
    return c.done()


register("block/pale_moss_carpet_side_small", lambda ctx: moss_fringe(ctx, 5))
register("block/pale_moss_carpet_side_tall", lambda ctx: moss_fringe(ctx, 13))


def hanging_moss(ctx, tip):
    c = Canvas(ctx)
    m = ctx.zeros()
    rng = ctx.rng("phm")
    for x in (3.5, 6.5, 9.0, 12.0):
        end = rng.uniform(7, 15) if tip else 16.6
        pts = [(x + math.sin(y * 0.6 + x) * 0.7, y) for y in np.linspace(-0.5, end, 10)]
        m = np.maximum(m, curve(ctx, pts, 1.6, 0.9 if tip else 1.6))
        if tip:  # tassel
            m = np.maximum(m, ellipse(ctx, pts[-1][0], end - 1.2, 1.0, 1.6))
    for i in range(6):
        x, y = rng.uniform(3, 13), rng.uniform(1, 12)
        m = np.maximum(m, leaf(ctx, (x, y), (x + rng.choice([-1.6, 1.6]), y + 2.2), 1.2))
    c.add(m, PALE_MOSS, noise=0.25, light=0.25, salt="phm")
    return c.done()


register("block/pale_hanging_moss", lambda ctx: hanging_moss(ctx, False))
register("block/pale_hanging_moss_tip", lambda ctx: hanging_moss(ctx, True))


# ---------------------------------------------------------------- glow lichen & resin clump

def glow_lichen(ctx):
    n = ctx.noise(6, 2, 0.5, salt="lichen")
    m = (n > 0.42).astype(np.float32)
    c = Canvas(ctx)
    c.add(m, LICHEN, noise=0.35, light=0.2, bevel=2, salt="gl", sss=0.3)
    glow = (ctx.texel_noise("glow", soft=True) > 0.8) & (m > 0.5) & (n > 0.5)
    c.recolor(glow.astype(np.float32), hexc("d8f4c8"), emissive=0.9)
    return c.done()


register("block/glow_lichen", glow_lichen)


def resin_clump(ctx):
    rng = ctx.rng("resin")
    c = Canvas(ctx)
    m = ctx.zeros()
    for _ in range(16):
        x, y = rng.uniform(2, 14), rng.uniform(2, 14)
        m = np.maximum(m, ellipse(ctx, x, y, rng.uniform(1.2, 2.4), rng.uniform(1.0, 2.0), rng.uniform(0, 3)))
    c.add(m, RESIN, outline=True, light=0.5, noise=0.15, bevel=2, smooth=0.8, sss=0.6, salt="rc")
    c.recolor(((ctx.distance(m, 2) > 1.0) & (ctx.texel_noise("rs", soft=True) > 0.85)).astype(np.float32), RESIN[5])
    return c.done()


register("block/resin_clump", resin_clump)


# ---------------------------------------------------------------- cave vines

def cave_vine(ctx, tip, lit):
    c = Canvas(ctx)
    end = 11 if tip else 16.6
    pts = [(8 + math.sin(y / 16 * 2 * math.pi) * 1.2, y) for y in np.linspace(-0.5, end, 12)]
    c.add(curve(ctx, pts, 1.2), VINE, light=0.2, salt="cvs")
    lm = ctx.zeros()
    spots = ((2, -1), (6, 1), (10, -1), (14, 1)) if not tip else ((2, -1), (6, 1), (9.5, -1))
    for y, s in spots:
        x = 8 + math.sin(y / 16 * 2 * math.pi) * 1.2
        lm = np.maximum(lm, leaf(ctx, (x, y), (x + s * 4.0, y + 1.6), 2.2, bend=s * 0.5))
    if tip:
        lm = np.maximum(lm, leaf(ctx, (8, 10), (7.5, 14.5), 2.0))
    c.add(lm, VINE, outline=True, light=0.3, salt="cvl")
    if lit:
        pos = ((4.5, 4.5), (11.5, 8.5), (5.0, 12.5)) if not tip else ((4.5, 4.5), (10.5, 9.0), (7.5, 14.0))
        for i, (x, y) in enumerate(pos):
            c.add(ctx.circle(x, y, 1.6), BERRY, outline=True, light=0.45, emissive=0.9, smooth=0.5, salt=f"cb{i}")
    return c.done()


register("block/cave_vines", lambda ctx: cave_vine(ctx, True, False))
register("block/cave_vines_lit", lambda ctx: cave_vine(ctx, True, True))
register("block/cave_vines_plant", lambda ctx: cave_vine(ctx, False, False))
register("block/cave_vines_plant_lit", lambda ctx: cave_vine(ctx, False, True))


# ---------------------------------------------------------------- spore blossom

def spore_blossom(ctx):
    c = Canvas(ctx)
    f = petals(ctx, 8, 8, 4, 7.6, 6.0, rot=math.pi / 4, inner=0.5, fat=0.55)
    d, a = radial(ctx, 8, 8)
    c.add(f, SPORE, outline=True, light=0.15, shade=-np.clip(d / 8, 0, 1) * 0.2 + 0.1, bevel=3, salt="sb",
          emissive=0.0)
    c.recolor(((np.abs(np.sin(a * 2)) < 0.12) & (d > 1.5) & (d < 6)).astype(np.float32), SPORE[1])
    c.add(ctx.circle(8, 8, 1.6), pal("5a1e3e", "8a2c5a", "b84a80"), salt="sbc", emissive=0.3)
    return c.done()


def spore_base(ctx):
    c = Canvas(ctx)
    f = petals(ctx, 8, 8, 6, 7.0, 3.6, rot=0.3, inner=0.5)
    c.add(f, LEAF, outline=True, light=0.25, salt="sbb")
    return c.done()


register("block/spore_blossom", spore_blossom)
register("block/spore_blossom_base", spore_base)


# ---------------------------------------------------------------- hanging roots

def hanging_roots(ctx):
    rng = ctx.rng("roots")
    c = Canvas(ctx)
    m = ctx.zeros()
    for x in (3, 5.5, 8, 10.5, 13):
        end = rng.uniform(8, 15.5)
        pts = [(x + math.sin(y * 0.7 + x) * 0.8, y) for y in np.linspace(-0.5, end, 10)]
        m = np.maximum(m, curve(ctx, pts, 1.3, 0.8))
        if rng.random() < 0.7:
            y0 = rng.uniform(2, end - 2)
            x0 = pts[int(y0 / end * 9)][0]
            m = np.maximum(m, ctx.segment(x0, y0, x0 + rng.choice([-2, 2]), y0 + 2.5, 0.9))
    c.add(m, ROOT, light=0.25, noise=0.2, salt="hr", sss=0.2)
    return c.done()


register("block/hanging_roots", hanging_roots)


# ---------------------------------------------------------------- sculk catalyst bloom (animated)

SCULK = pal("061a20", "0a2830", "0e3640", "124650", "185862")
SOUL = pal("1c8c94", "3ac0c4", "7ae8e4", "c6fff8")


def _sculk_fallback(ctx):
    n = ctx.noise(4, 2, 0.5, salt="sk")
    return Tex(ctx, ctx.palette(SCULK, n * 0.7 + ctx.texel_noise("sk") * 0.3), height=0.4 + n * 0.2, smooth=0.3)


def catalyst_bloom(ctx, face):
    base_path = f"block/sculk_catalyst_{face}"
    t = borrowed(ctx, base_path, _sculk_fallback)
    t = t.copy()
    t.wrap = True
    k = ctx.frame / max(1, ctx.frames)  # 0..1 through the bloom
    if face == "top":
        d, _ = radial(ctx, 8, 8)
    else:
        d = np.hypot((ctx.x - 8) * 0.8, ctx.y - 3.0)
    ring = np.abs(d - k * 9.0) < 0.9 + k * 0.6
    veins = (ctx.noise(3, 2, 0.5, salt="bloomv") > 0.55) & (d < k * 9.0 + 0.5)
    strength = 1 - k * 0.7
    glow = ring | veins
    lvl = np.where(ring, 0.85, 0.45) * strength + (ctx.texel_noise("bl") - 0.5) * 0.2
    col = ctx.palette(SOUL, np.clip(lvl, 0, 1))
    t.color = np.where(glow[..., None], col, t.color)
    t.emissive = np.where(glow, np.clip(lvl, 0.2, 1), t.emissive).astype(np.float32)
    return t


register("block/sculk_catalyst_side_bloom", lambda ctx: catalyst_bloom(ctx, "side"))
register("block/sculk_catalyst_top_bloom", lambda ctx: catalyst_bloom(ctx, "top"))


# ---------------------------------------------------------------- shelf mushroom

def shelf_surface(ctx):
    n = ctx.noise(4, 2, 0.5, salt="shelf")
    rings = np.sin(ctx.y * 1.6 + n * 3)
    v = 0.45 + rings * 0.2 + (ctx.texel_noise("sh") - 0.5) * 0.25
    return Tex(ctx, ctx.palette(SHELF, np.clip(v, 0, 1)), height=0.45 + rings * 0.1, smooth=0.15, porosity=0.5)


def shelf_mushroom(ctx, stage):
    c = Canvas(ctx)
    W = ctx.w / 16  # 32x32 texture -> 2 texels per 16x unit
    specs = [(16, 18, 11, 6)] if stage == 0 else [(16, 12, 13, 7), (11, 22, 8, 4.5), (22, 24, 8, 4.5)]
    for i, (cx, cy, rx, ry) in enumerate(specs):
        m = ellipse(ctx, cx, cy, rx, ry) * (ctx.y < cy + ry * 0.35)
        d, a = radial(ctx, cx, cy)
        rings = np.sin(np.hypot((ctx.x - cx) / rx, (ctx.y - cy) / ry) * 12)
        c.add(m, SHELF, outline=True, light=0.3, shade=rings * 0.12, noise=0.15, bevel=3, sss=0.2, salt=f"sm{i}")
        rim = m * (ctx.y >= cy + ry * 0.35 - 1.5)
        c.recolor(rim, SHELF[5])
    return c.done()


register("block/shelf_mushroom_stage0", lambda ctx: shelf_mushroom(ctx, 0))
register("block/shelf_mushroom_stage1", lambda ctx: shelf_mushroom(ctx, 1))
register("block/shelf_mushroom_particle", shelf_surface)
