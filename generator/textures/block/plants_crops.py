"""Crops (wheat, carrots, potatoes, beetroots, cocoa, nether wart, sweet berries, torchflower,
pitcher), gourd stems and melon / pumpkin blocks."""
import math

import numpy as np

from ...engine import Tex, hexc, pal
from ...registry import register
from .plants_common import (LEAF, STEM, Canvas, blade, ellipse, grays, leaf, leaf_spray, px, radial,
                            shift, stalk, union, vgrad)

WHEAT_GREEN = pal("22461a", "2e5c1e", "3c7424", "4e8a2c", "62a034", "7ab640")
WHEAT_GOLD = pal("6a4a14", "8c641c", "b08424", "cca234", "e0bc4c", "f0d470")
CARROT = pal("7a2c06", "a8420a", "d06212", "ea8222", "f8a444")
POTATO = pal("6a4a22", "8a6630", "a8823e", "c29e52", "d8b86a")
BEET = pal("3a0a1a", "5c1028", "84183a", "a8264c", "c43e62")
NETHER_WART = pal("3c0808", "5e0e0e", "821a16", "a42a1e", "c03e28", "d85a36")
BERRY = pal("4a0610", "780c1a", "a41426", "cc2834", "ea5450")
BERRY_LEAF = pal("163a24", "1f4c2e", "2a6038", "367444", "448852")
PITCHER = pal("1a3c4a", "22546a", "2c6e88", "3c8aa4", "58a6bc", "80c2d2")
PITCHER_RIM = pal("4a1a3a", "6e2656", "943a74", "b85690", "d47aac")


def stage_of(ctx):
    digits = "".join(ch for ch in ctx.name.split("stage")[-1] if ch.isdigit())
    return int(digits or 0)


def crop_rows(ctx, rng, n, top, width=1.4, spread=1.0):
    """n upright stalks across the texture reaching y=top (jittered)."""
    out = []
    for i in range(n):
        bx = (i + 0.5) * 16 / n + rng.uniform(-0.5, 0.5)
        t = top + rng.uniform(-1.2, 1.2)
        tx = bx + rng.uniform(-1.2, 1.2) * spread
        out.append((bx, t, tx))
    return out


# ---------------------------------------------------------------- wheat

def wheat(ctx):
    k = stage_of(ctx)
    t = k / 7
    rng = ctx.rng("wheat")
    c = Canvas(ctx)
    top = 14.0 - 12.0 * t
    ripe = max(0.0, (k - 4) / 3)
    p = WHEAT_GREEN * (1 - ripe) + WHEAT_GOLD * ripe
    stalks = ctx.zeros()
    heads = ctx.zeros()
    for bx, tt, tx in crop_rows(ctx, rng, 5, top, spread=1.0):
        tt = min(15.0, tt)
        if k < 3:
            stalks = np.maximum(stalks, blade(ctx, (bx, 16.6), (tx, tt), 1.8, bend=rng.uniform(-0.6, 0.6)))
            stalks = np.maximum(stalks, blade(ctx, (bx, 16.6), (bx + (tx - bx) * -1.5 + 0.5, tt + 2.5), 1.5))
        else:
            stalks = np.maximum(stalks, stalk(ctx, bx, 16.6, tx, tt + (2.5 if k >= 4 else 0), 1.0,
                                              rng.uniform(-0.4, 0.4)))
            stalks = np.maximum(stalks, blade(ctx, (bx, 15), (bx + rng.choice([-1, 1]) * 3, 15 - 6 * t), 1.6, 0.4))
            if k >= 4:
                hh = 1.6 + ripe * 1.4
                heads = np.maximum(heads, ellipse(ctx, tx, tt + hh * 0.7, 1.15, hh))
    c.add(stalks, p, shade=vgrad(ctx, top, 16, 0.12, -0.18), noise=0.2, light=0.2, salt="ws")
    if k >= 4:
        hp = WHEAT_GREEN * (1 - ripe) + shift(WHEAT_GOLD, 0.08) * ripe
        c.add(heads, hp, outline=True, noise=0.3, light=0.3, salt="wh")
        grain = ((ctx.ty + ctx.tx) % 2 == 0).astype(np.float32) * heads
        c.recolor(grain * (ctx.texel_noise("gr", soft=True) > 0.5), hp[4])
    return c.done()


for _k in range(8):
    register(f"block/wheat_stage{_k}", wheat)


# ---------------------------------------------------------------- root crops

def leafy_crop(ctx, kind):
    k = stage_of(ctx)
    t = (k + 1) / 4
    rng = ctx.rng(kind)
    c = Canvas(ctx)
    plants = (3.5, 8.0, 12.5) if k else (4.5, 11.5)
    leafm = ctx.zeros()
    ribs = ctx.zeros()
    for i, x in enumerate(plants):
        h = 4.5 + 9 * t + rng.uniform(-1, 1)
        n = 2 + k
        for j in range(n):
            a = -math.pi / 2 + (j - (n - 1) / 2) * (0.55 if kind != "potato" else 0.75) + rng.uniform(-0.15, 0.15)
            L = h * rng.uniform(0.75, 1.0)
            tip = (x + math.cos(a) * L, 16.2 + math.sin(a) * L)
            if kind == "carrot":
                lm = blade(ctx, (x, 16.4), tip, 1.6, bend=rng.uniform(-0.6, 0.6))
                for f in (0.45, 0.7):  # feathery side leaflets
                    bx, by = x + (tip[0] - x) * f, 16.4 + (tip[1] - 16.4) * f
                    s = rng.choice([-1, 1])
                    lm = np.maximum(lm, leaf(ctx, (bx, by), (bx + s * 1.8, by - 1.2), 1.1))
            else:
                w = {"potato": 2.6, "beet": 3.0}[kind] * (0.6 + 0.4 * t)
                lm = leaf(ctx, (x, 16.4), tip, w, bend=rng.uniform(-0.6, 0.6), fat=0.6)
                if kind == "beet":
                    ribs = np.maximum(ribs, ctx.segment(x, 16.4, x + (tip[0] - x) * 0.4, 16.4 + (tip[1] - 16.4) * 0.4, 0.6) * lm)
            leafm = np.maximum(leafm, lm)
    p = {"carrot": STEM, "potato": LEAF, "beet": shift(LEAF, -0.05)}[kind]
    c.add(leafm, p, shade=vgrad(ctx, 4, 16, 0.12, -0.15), noise=0.2, light=0.3, salt=f"{kind}l")
    if kind == "beet" and k >= 2:
        c.recolor(ribs, BEET[2])
    if k == 3:
        if kind == "carrot":
            for x in plants:
                c.add(ctx.polygon([(x - 1.3, 13.6), (x + 1.3, 13.6), (x + 0.9, 16.5), (x - 0.9, 16.5)]), CARROT,
                      outline=True, salt=f"cr{x}")
        elif kind == "potato":
            for x, y in ((3.0, 14.6), (8.6, 15.0), (12.8, 14.4)):
                c.add(ellipse(ctx, x, y, 1.9, 1.4), POTATO, outline=True, salt=f"pt{x}")
                c.recolor(px(ctx, [(int(x), int(y))]), POTATO[1])
        else:
            for x in plants:
                c.add(ellipse(ctx, x, 15.2, 2.0, 1.7), BEET, outline=True, salt=f"bt{x}")
    return c.done()


for _k in range(4):
    register(f"block/carrots_stage{_k}", lambda ctx: leafy_crop(ctx, "carrot"))
    register(f"block/potatoes_stage{_k}", lambda ctx: leafy_crop(ctx, "potato"))
    register(f"block/beetroots_stage{_k}", lambda ctx: leafy_crop(ctx, "beet"))


# ---------------------------------------------------------------- cocoa

COCOA = [pal("3a5014", "50681a", "668024", "7e9a2e", "98b43c"),      # young: green
         pal("6a4a10", "8a6418", "aa7e22", "c49a30", "d8b448"),      # yellow-tan
         pal("4a2410", "642f16", "7e3e1e", "985028", "b06434")]      # ripe: brown


def cocoa(ctx):
    """Pod skin everywhere (the model samples several boxes) plus a stem in the top-right."""
    p = COCOA[stage_of(ctx)]
    rib = np.cos(ctx.x / 3 * 2 * math.pi)
    v = 0.5 + rib * 0.25 + (ctx.texel_noise("cocoa") - 0.5) * 0.2 + (ctx.noise(4, 1, salt="cc") - 0.5) * 0.15
    color = ctx.palette(p, np.clip(v, 0, 1))
    t = Tex(ctx, color, height=0.45 + rib * 0.15, smooth=0.25, sss=0.3, wrap=False)
    stem = ctx.rect(12, 0, 16, 4) > 0
    t.color[stem] = ctx.palette(WHEAT_GREEN if stage_of(ctx) == 0 else pal("4a3a1a", "6a5426", "8a6e34"),
                                ctx.texel_noise("cst") * 0.6 + 0.2)[stem]
    t.alpha = np.where(stem & ~((ctx.ty == ctx.tx - 12) | (ctx.ty == ctx.tx - 11)), 0.0, 1.0).astype(np.float32)
    return t


for _k in range(3):
    register(f"block/cocoa_stage{_k}", cocoa)


# ---------------------------------------------------------------- nether wart

def nether_wart(ctx):
    k = stage_of(ctx)
    rng = ctx.rng("wart")
    c = Canvas(ctx)
    m = ctx.zeros()
    bulbs = ctx.zeros()
    xs = (3, 8, 13) if k else (4.5, 11.5)
    for x in xs:
        h = (5, 8, 11)[k] + rng.uniform(-1, 1)
        tx = x + rng.uniform(-1.5, 1.5)
        m = np.maximum(m, stalk(ctx, x, 16.6, tx, 16 - h, 1.2 if k else 1.0, rng.uniform(-1, 1)))
        for j in range(k + 1):
            yy = 16 - h + j * 2.5
            bulbs = np.maximum(bulbs, ctx.circle(tx + (j % 2 * 2 - 1) * (0.8 if j else 0), yy, (1.2, 1.5, 1.8)[k]))
    c.add(m, NETHER_WART, light=0.2, noise=0.2, salt="nws")
    c.add(bulbs, NETHER_WART, outline=True, light=0.35, noise=0.2, salt="nwb", sss=0.4)
    return c.done()


for _k in range(3):
    register(f"block/nether_wart_stage{_k}", nether_wart)


# ---------------------------------------------------------------- sweet berry bush

def sweet_berry(ctx):
    k = stage_of(ctx)
    rng = ctx.rng("sbb")
    c = Canvas(ctx)
    if k == 0:
        lm = union(leaf(ctx, (8, 16.5), (5, 10.5), 2.4, 0.4), leaf(ctx, (8, 16.5), (11, 11), 2.4, -0.4),
                   leaf(ctx, (8, 16.5), (8.5, 9), 2.0))
    else:
        top = (7, 3, 2)[k - 1]
        lm = leaf_spray(ctx, rng, 14 + k * 8, 2.5, top + 2, 13.5, 15.5, length=(2.2, 3.4), width=(1.8, 2.4), up=0.5)
    c.add(lm, BERRY_LEAF, shade=vgrad(ctx, 2, 16, 0.12, -0.15), noise=0.2, outline=k > 1, salt="sbl")
    if k >= 2:
        bp = BERRY if k == 3 else pal("3a5a1a", "50721e", "6c8e28", "88a834", "a4c044")
        pts = [(4, 6), (11, 5), (7, 9), (12, 11), (3.5, 12), (9, 13)][: 4 + (k - 2) * 2]
        for x, y in pts:
            c.add(ctx.circle(x + 0.5, y + 0.5, 1.15), bp, outline=True, light=0.45, salt=f"be{x}", smooth=0.5)
            c.recolor(px(ctx, [(int(x), int(y))]), bp[4])
    return c.done()


for _k in range(4):
    register(f"block/sweet_berry_bush_stage{_k}", sweet_berry)


# ---------------------------------------------------------------- torchflower crop

TORCH_BUD = pal("6a2306", "993606", "c4500c", "e06c16", "f28c26")


def torchflower_crop(ctx):
    k = stage_of(ctx)
    c = Canvas(ctx)
    top = 10 if k == 0 else 6
    c.add(stalk(ctx, 8, 16.6, 8, top, 1.0, 0.3), STEM, salt="tcs")
    c.add(union(leaf(ctx, (8, 14), (4.5, 11.5), 2.0, 0.3), leaf(ctx, (8, 13), (11.5, 10.5), 2.0, -0.3)), LEAF,
          salt="tcl")
    if k == 0:
        c.add(ellipse(ctx, 8, top - 0.5, 1.4, 1.6), pal("3c5a1a", "507420", "6a8e2a", "86a836"), outline=True, salt="tcb")
    else:
        c.add(union(leaf(ctx, (8, top + 1.5), (5.8, top - 1), 1.6), leaf(ctx, (8, top + 1.5), (10.2, top - 1), 1.6)),
              LEAF, salt="tcc")
        c.add(ellipse(ctx, 8, top - 1.5, 1.5, 2.4), TORCH_BUD, outline=True, salt="tcbud", emissive=0.1)
    return c.done()


register("block/torchflower_crop_stage0", torchflower_crop)
register("block/torchflower_crop_stage1", torchflower_crop)


# ---------------------------------------------------------------- pitcher crop

POD = pal("2e3a1a", "3e4e22", "52642c", "687c38", "809444")


def pitcher_pod_face(ctx, face):
    n = ctx.texel_noise("pod" + face)
    if face == "side":
        v = 0.5 + np.cos(ctx.x / 4 * 2 * math.pi) * 0.2 + (n - 0.5) * 0.25 + vgrad(ctx, 0, 16, 0.15, -0.15)
    elif face == "top":
        d, a = radial(ctx, 8, 8)
        v = 0.55 + np.cos(a * 5) * 0.15 * (d > 1.5) + (n - 0.5) * 0.2 - (d < 1.5) * 0.3
    else:
        v = 0.3 + (n - 0.5) * 0.25
    return Tex(ctx, ctx.palette(POD, np.clip(v, 0, 1)), height=0.5 + (v - 0.5) * 0.3, smooth=0.2, sss=0.3,
               wrap=False)


register("block/pitcher_crop_side", lambda ctx: pitcher_pod_face(ctx, "side"))
register("block/pitcher_crop_top", lambda ctx: pitcher_pod_face(ctx, "top"))
register("block/pitcher_crop_bottom", lambda ctx: pitcher_pod_face(ctx, "bottom"))

PITCHER_LEAF = pal("1e3e3a", "28524a", "33685a", "40806a", "50967a")


def pitcher_stage(ctx, part, k):
    c = Canvas(ctx)
    if part == "bottom":
        n = k + 1
        lm = ctx.zeros()
        for j in range(n):
            a = -math.pi / 2 + (j - (n - 1) / 2) * 0.7
            L = 3 + k * 2.4
            lm = np.maximum(lm, leaf(ctx, (8, 16.5), (8 + math.cos(a) * L * 1.1, 16.5 + math.sin(a) * L), 2.2 + k * 0.4,
                                     bend=(j - (n - 1) / 2) * 0.6, fat=0.55))
        if k >= 3:
            c.add(stalk(ctx, 8, 16.6, 8, -0.5, 1.6, 0.3), PITCHER_LEAF, salt="pst")
        c.add(lm, PITCHER_LEAF, outline=True, light=0.3, salt="pbl")
        if k <= 2:
            c.add(ellipse(ctx, 8, 15.2, 2.2, 1.5), POD, outline=True, salt="ppod")
    else:  # top stage 3 / 4
        c.add(stalk(ctx, 8, 16.6, 8, 9, 1.6, 0.2), PITCHER_LEAF, salt="pts")
        c.add(union(leaf(ctx, (8, 15), (3.0, 10.5), 2.6, 0.4), leaf(ctx, (8, 14), (13.0, 10.0), 2.6, -0.4)),
              PITCHER_LEAF, outline=True, salt="ptl")
        if k == 3:
            c.add(ellipse(ctx, 8, 7, 2.0, 3.0), PITCHER, outline=True, salt="pbud")
            c.recolor(ctx.rect(7, 4, 9, 5), PITCHER_RIM[3])
        else:
            cup = ctx.polygon([(5.5, 2.5), (10.5, 2.5), (10.2, 6), (9.6, 10.5), (6.4, 10.5), (5.8, 6)])
            c.add(cup, PITCHER, outline=True, light=0.35, shade=vgrad(ctx, 2, 11, 0.1, -0.1), salt="pcup")
            c.add(union(ellipse(ctx, 8, 2.5, 3.2, 1.3), leaf(ctx, (9, 2.2), (12.5, 0.6), 1.6)), PITCHER_RIM,
                  outline=True, salt="prim")
            c.recolor(ellipse(ctx, 8, 2.6, 2.0, 0.6), PITCHER_RIM[0])
            vein = (np.abs(ctx.x - 8) < 0.5) & (ctx.y > 4) & (ctx.y < 10)
            c.recolor(vein.astype(np.float32), PITCHER[4])
    return c.done()


for _k in range(1, 5):
    register(f"block/pitcher_crop_bottom_stage_{_k}", lambda ctx, k=_k: pitcher_stage(ctx, "bottom", k))
register("block/pitcher_crop_top_stage_3", lambda ctx: pitcher_stage(ctx, "top", 3))
register("block/pitcher_crop_top_stage_4", lambda ctx: pitcher_stage(ctx, "top", 4))


# ---------------------------------------------------------------- gourd stems (tinted)

SG = grays(6, 0.45, 0.88)


def gourd_stem(ctx):
    c = Canvas(ctx)
    c.add(stalk(ctx, 8, 16.6, 8.0, -0.5, 1.2, 0.8), SG, light=0.25, salt="gs")
    c.add(union(leaf(ctx, (8.3, 12), (12.5, 9.0), 2.0, -0.3), leaf(ctx, (7.8, 7), (3.5, 4.5), 2.0, 0.3),
                leaf(ctx, (8.2, 3), (11.5, 0.5), 1.6, -0.2)), SG, light=0.3, salt="gl")
    return c.done()


def attached_stem(ctx):
    c = Canvas(ctx)
    pts = [(8, 16.6), (8.4, 12), (9.5, 9.5), (12, 8.5), (16.5, 8.5)]
    from .plants_common import curve
    c.add(curve(ctx, pts, 1.2), SG, light=0.25, salt="as")
    c.add(union(leaf(ctx, (8.3, 13), (4.0, 10.5), 2.0, 0.3), leaf(ctx, (11.5, 8.8), (13.0, 4.5), 1.8, -0.3)), SG,
          light=0.3, salt="al")
    return c.done()


register("block/melon_stem", gourd_stem)
register("block/pumpkin_stem", gourd_stem)
register("block/attached_melon_stem", attached_stem)
register("block/attached_pumpkin_stem", attached_stem)


# ---------------------------------------------------------------- melon & pumpkin blocks

MELON = pal("2a4a12", "365e16", "44741c", "548a22", "66a02a", "7cb434")
MELON_STRIPE = pal("1c3a0c", "244a10", "2e5c14")
PUMPKIN = pal("6a2e04", "8e4206", "b05a0a", "cc7212", "e08a1e", "eea232")
PUMPKIN_TOP = pal("4a2a10", "6a4218", "8a5a22")


def melon_side(ctx):
    n = ctx.noise(4, 2, 0.5, salt="melon")
    stripe_x = ctx.x + (ctx.noise(8, 1, salt="mst", stretch=(1, 3)) - 0.5) * 3
    stripe = (np.cos(stripe_x / 4 * 2 * math.pi) > 0.55)
    v = 0.25 + n * 0.5 + (ctx.texel_noise("ml") - 0.5) * 0.3
    color = np.where(stripe[..., None], ctx.palette(MELON_STRIPE, np.clip(v, 0, 1)), ctx.palette(MELON[2:], v))
    return Tex(ctx, color, height=0.5 + n * 0.1, smooth=0.45, sss=0.2)


def melon_top(ctx):
    d, a = radial(ctx, 8, 8)
    n = ctx.noise(4, 2, 0.5, salt="mtop")
    stripe = (np.cos(a * 8 + d * 0.15 + (n - 0.5) * 1.5) > 0.6) & (d > 1.6)
    v = 0.25 + n * 0.5 + (ctx.texel_noise("mt") - 0.5) * 0.3
    color = np.where(stripe[..., None], ctx.palette(MELON_STRIPE, np.clip(v, 0, 1)), ctx.palette(MELON[2:], v))
    scar = d < 1.4
    color = np.where(scar[..., None], pal("5e5a2a")[0], color)
    return Tex(ctx, color, height=0.5 + n * 0.1 - scar * 0.1, smooth=0.45, sss=0.2, wrap=False)


def pumpkin_side(ctx):
    rib = (ctx.x % 4) / 4
    v = 0.25 + np.sin(rib * math.pi) * 0.55 + (ctx.texel_noise("pk") - 0.5) * 0.18
    v = v + (ctx.noise(4, 1, salt="pk", stretch=(1, 3)) - 0.5) * 0.15
    groove = (ctx.tx % 4) == 0
    v = np.where(groove, 0.08, v)
    return Tex(ctx, ctx.palette(PUMPKIN, np.clip(v, 0, 1)), height=np.where(groove, 0.3, 0.5 + np.sin(rib * math.pi) * 0.2),
               smooth=0.35, sss=0.1)


def pumpkin_top(ctx):
    d, a = radial(ctx, 8, 8)
    rib = np.cos(a * 8)
    v = 0.45 + rib * 0.25 * np.clip(d / 4, 0, 1) + (ctx.texel_noise("pt") - 0.5) * 0.18 - np.clip((d - 6.5) / 2, 0, 1) * 0.2
    color = ctx.palette(PUMPKIN, np.clip(v, 0, 1))
    stem = ctx.rect(6.5, 6.5, 9.5, 9.5) > 0
    color[stem] = ctx.palette(pal("3a3410", "4e461a", "665c24", "7c7030"), 0.3 + (ctx.x[stem] < 8) * 0.5 - (ctx.y[stem] > 8) * 0.2)
    ring = (ctx.edge(stem.astype(np.float32), 1) > 0) & False
    return Tex(ctx, color, height=0.5 + rib * 0.1 + stem * 0.3 + ring, smooth=0.35, sss=0.1, wrap=False)


def carved_pumpkin(ctx):
    t = pumpkin_side(ctx.sub("block/pumpkin_side"))
    t.ctx = ctx
    face = union(
        ctx.polygon([(3, 4), (6.5, 5.5), (6, 7.5), (3.5, 7.5)]),          # left eye (slanted)
        ctx.polygon([(13, 4), (9.5, 5.5), (10, 7.5), (12.5, 7.5)]),       # right eye
        ctx.rect(7.5, 8, 8.5, 9),                                          # nose dot
        ctx.polygon([(2.5, 10), (13.5, 10), (12.5, 13.0), (10, 13.5), (6, 13.5), (3.5, 13)]),  # mouth
    )
    teeth = union(ctx.rect(5, 10, 6, 11), ctx.rect(10, 10, 11, 11), ctx.rect(7.5, 13, 8.5, 14))
    face = np.where(teeth > 0.5, 0, face) > 0.5
    inner = face & ~(ctx.edge(face.astype(np.float32), 1, "tl") > 0)
    t.color[face] = hexc("3a1a06")
    t.color[inner] = hexc("1e0e04")
    t.height[face] = 0.1
    return t


register("block/melon_side", melon_side)
register("block/melon_top", melon_top)
register("block/pumpkin_side", pumpkin_side)
register("block/pumpkin_top", pumpkin_top)
register("block/carved_pumpkin", carved_pumpkin)
