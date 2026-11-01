"""Small flowers, tall (double) flowers, flower beds."""
import math

import numpy as np

from ...engine import hexc, pal
from ...registry import register, texture
from .plants_common import (LEAF, LEAF_BLUE, STEM, Canvas, bez, curve, dots, ellipse, leaf,
                            leaf_spray, petals, px, radial, shift, stalk, stem_fill, union, vgrad)

RED = pal("4a0a0e", "7a1216", "a51b1c", "c42a22", "dc4430", "ee6a4c")
YELLOW = pal("7a4c06", "a8720c", "d09c16", "eabf22", "f6db42", "fff184")
GOLDEN = pal("5c3a04", "8f620a", "c08f14", "e4b828", "f8d850", "fff3a8")
ORCHID = pal("123f6e", "1d5e98", "2b82c0", "45a6dc", "73c6ee", "aee2f8")
ALLIUM = pal("3c1752", "582275", "763496", "9450b4", "b072cc", "cc9ee2")
WHITE = pal("8c8a86", "aeaca6", "c9c7c0", "dddcd4", "eeede6", "fbfaf4")
BLUE = pal("141d5e", "1f2e8a", "2c46b4", "3f63d4", "5f86ea", "93b2f6")
DARK = pal("120e10", "1c1518", "281d21", "35262a", "453033", "5a3d3c")
ORANGE = pal("6a2306", "993606", "c4500c", "e06c16", "f28c26", "fbb04a")
PINK = pal("6a2440", "93345a", "ba4c78", "d66c96", "eb92b4", "f8bcd2")
MAGENTA = pal("5a1240", "86205c", "b0327a", "d04c96", "e872b0", "f8a6d0")
CENTER = pal("4a2a0a", "6e420e", "93601a", "b88228")
LILAC = pal("4c2a62", "6a3f86", "8a5aa8", "a87ac4", "c49cdc", "dcc2ee")
PEONY = pal("7a3a5c", "a2507a", "c46c98", "dc8eb4", "eeb2cc", "fad6e4")
PALE_STEM = pal("2e3330", "3d4440", "4e5751", "606a63", "737e76", "889389")
PALE_PETAL = pal("6e6a70", "8c8890", "aaa6ae", "c4c0c8", "dcd8e0", "f0eef2")
EYE = pal("6a1e04", "a63a06", "e06410", "fb9a2a", "ffd070")


def base_leaves(c, ctx, specs, p=LEAF, **kw):
    """specs: (bx, by, tx, ty, width, bend)."""
    m = ctx.zeros()
    for bx, by, tx, ty, w, b in specs:
        m = np.maximum(m, leaf(ctx, (bx, by), (tx, ty), w, bend=b))
    c.add(m, p, salt="leaves", **kw)
    return m


def stem_to(c, ctx, x0, x1, top, bend=0.0, width=1.0, p=STEM, y0=16.5):
    c.add(stalk(ctx, x0, y0, x1, top, width, bend), p, light=0.25, salt="stem")


# ---------------------------------------------------------------- small flowers

@texture("block/poppy")
def poppy(ctx):
    c = Canvas(ctx)
    stem_to(c, ctx, 8, 8, 7.5, bend=0.6)
    base_leaves(c, ctx, [(8, 13.5, 4.2, 10.5, 2.2, 0.4), (8.4, 11.5, 12.2, 9.2, 2.0, -0.4)])
    head = union(ellipse(ctx, 8, 5.6, 3.5, 2.6), ctx.circle(6.3, 3.9, 1.9), ctx.circle(9.8, 3.8, 1.9),
                 ctx.circle(8, 3.2, 1.5))
    c.add(head, RED, outline=True, shade=vgrad(ctx, 2, 8, 0.12, -0.1), salt="poppy")
    c.recolor(px(ctx, [(8, 3), (7, 6), (8, 6)]), RED[1])
    c.recolor(px(ctx, [(7, 5), (8, 5)]), hexc("1c1a12"))
    c.recolor(px(ctx, [(6, 3), (10, 3)]), RED[5])
    return c.done()


def puff_head(ctx, cx, cy, r, salt):
    m = ctx.circle(cx, cy, r)
    for i in range(9):
        a = i / 9 * 2 * math.pi + 0.3
        m = np.maximum(m, ctx.circle(cx + math.cos(a) * r * 0.85, cy + math.sin(a) * r * 0.8, r * 0.42))
    return m


def dandelion_like(ctx, p, shine=False):
    c = Canvas(ctx)
    stem_to(c, ctx, 8, 7.5, 9, bend=-0.5)
    # toothed rosette leaves at the base
    m = ctx.zeros()
    for bx, tx, ty in ((8, 3.2, 12.5), (8, 12.8, 12.0), (8, 5.0, 10.5), (8, 11.2, 10.2)):
        lm = leaf(ctx, (bx, 16), (tx, ty), 2.0, fat=0.6)
        m = np.maximum(m, lm)
        # teeth
        for k in (0.35, 0.65):
            m = np.maximum(m, ctx.circle(bx + (tx - bx) * k, 16 + (ty - 16) * k - 0.9, 0.7))
    c.add(m, LEAF, salt="dl")
    c.add(ellipse(ctx, 7.5, 9.2, 1.7, 0.9), STEM, salt="sepal")
    head = puff_head(ctx, 7.5, 6.3, 2.5, "dandelion")
    if shine:
        head = np.maximum(head, petals(ctx, 7.5, 6.3, 10, 3.7, 1.3, rot=0.2, inner=1.5))
        c.add(head, p, outline=True, light=0.45, noise=0.25, smooth=0.75, f0=0.6, salt="gd",
              shade=vgrad(ctx, 3, 9, 0.1, -0.12))
        c.t.set_metal(head, 231)  # LabPBR gold
        c.recolor(px(ctx, [(6, 5), (7, 4), (9, 6)]), p[5])
    else:
        c.add(head, p, outline=True, noise=0.3, shade=vgrad(ctx, 3, 9, 0.12, -0.12), salt="dand")
        c.recolor(px(ctx, [(6, 5), (8, 4)]), p[5])
    return c.done()


register("block/dandelion", lambda ctx: dandelion_like(ctx, YELLOW))
register("block/golden_dandelion", lambda ctx: dandelion_like(ctx, GOLDEN, shine=True))


@texture("block/blue_orchid")
def blue_orchid(ctx):
    c = Canvas(ctx)
    base_leaves(c, ctx, [(8, 16, 3.5, 11.5, 2.6, 0.5), (8, 16, 12.5, 12.0, 2.6, -0.4),
                         (8, 16, 9.5, 10.5, 2.0, -0.3)])
    m = union(stalk(ctx, 8, 16, 5, 6, 1, -1.2), stalk(ctx, 8, 16, 11, 4.5, 1, 1.0),
              stalk(ctx, 8.5, 14, 9.5, 9.5, 1, 0.3))
    c.add(m, STEM, light=0.2, salt="st")
    for cx, cy, r in ((5, 5.2, 2.4), (11, 3.8, 2.3), (9.6, 9.2, 1.9)):
        f = petals(ctx, cx, cy, 5, r, 1.7, rot=-math.pi / 2)
        c.add(f, ORCHID, outline=True, light=0.35, salt=f"or{cx}")
        c.recolor(ctx.rect(round(cx - 0.5), round(cy - 0.5), round(cx - 0.5) + 1, round(cy - 0.5) + 1),
                  ORCHID[5])
    return c.done()


@texture("block/allium")
def allium(ctx):
    c = Canvas(ctx)
    base_leaves(c, ctx, [(8, 16, 4.0, 10.0, 1.5, 0.6), (8, 16, 12.0, 11.0, 1.5, -0.6)])
    stem_to(c, ctx, 8, 8, 7, bend=0.3)
    head = ctx.circle(8, 4.4, 3.4)
    for i in range(10):
        a = i / 10 * 2 * math.pi
        head = np.maximum(head, ctx.circle(8 + math.cos(a) * 3.3, 4.4 + math.sin(a) * 3.2, 0.8))
    c.add(head, ALLIUM, outline=True, noise=0.42, light=0.35, salt="al")
    rng = ctx.rng("allflor")
    c.recolor(px(ctx, [(int(x), int(y)) for x, y in zip(rng.integers(6, 10, 4), rng.integers(2, 6, 4))]),
              ALLIUM[5])
    return c.done()


@texture("block/azure_bluet")
def azure_bluet(ctx):
    c = Canvas(ctx)
    base_leaves(c, ctx, [(7, 16, 3.5, 13.0, 1.8, 0.3), (9, 16, 13.0, 13.2, 1.8, -0.3),
                         (8, 16, 6.0, 12.0, 1.4, 0.2)], p=LEAF_BLUE)
    heads = ((4.5, 8.5), (8, 6.5), (11.5, 8), (6.5, 11), (10.5, 11.5))
    m = ctx.zeros()
    for x, y in heads:
        m = np.maximum(m, stalk(ctx, 8 + (x - 8) * 0.4, 16.5, x, y, 1, (x - 8) * 0.15))
    c.add(m, STEM, light=0.2, salt="st")
    for x, y in heads:
        f = petals(ctx, x, y, 4, 1.6, 1.4, rot=math.pi / 4, inner=0)
        c.add(f, WHITE, light=0.3, noise=0.08, salt=f"b{x}")
        c.recolor(ctx.rect(math.floor(x), math.floor(y), math.floor(x) + 1, math.floor(y) + 1), YELLOW[4])
    return c.done()


def tulip(ctx, p, salt):
    c = Canvas(ctx)
    stem_to(c, ctx, 8, 8, 7.5, bend=-0.3)
    base_leaves(c, ctx, [(8, 16, 4.2, 9.0, 3.2, 0.9), (8, 16, 12.0, 10.5, 3.0, -0.8)], p=LEAF_BLUE)
    cup = union(ellipse(ctx, 8, 5.8, 2.9, 2.4),
                ctx.polygon([(5.1, 6), (5.2, 2.3), (6.9, 4.2), (8, 1.6), (9.1, 4.2), (10.8, 2.3), (10.9, 6)]))
    c.add(cup, p, outline=True, shade=vgrad(ctx, 2, 8, 0.12, -0.12), salt=salt)
    c.recolor(px(ctx, [(7, 4), (7, 5), (9, 4), (9, 5)]), p[1])
    c.recolor(px(ctx, [(8, 3), (8, 4)]), p[5])
    return c.done()


for _name, _p in (("red", RED), ("orange", ORANGE), ("white", WHITE), ("pink", PINK)):
    register(f"block/{_name}_tulip", lambda ctx, p=_p, n=_name: tulip(ctx, p, n))


@texture("block/oxeye_daisy")
def oxeye_daisy(ctx):
    c = Canvas(ctx)
    stem_to(c, ctx, 8, 8, 8, bend=0.5)
    base_leaves(c, ctx, [(8, 15, 4.0, 12.0, 2.0, 0.3), (8, 13, 12.0, 10.5, 1.8, -0.3)])
    f = petals(ctx, 8, 5, 11, 3.9, 1.5, rot=0.15, inner=0.8)
    c.add(f, WHITE, outline=True, light=0.3, salt="dp")
    c.add(ctx.circle(8, 5, 1.55), YELLOW, outline=True, salt="dc", light=0.4)
    return c.done()


@texture("block/cornflower")
def cornflower(ctx):
    c = Canvas(ctx)
    stem_to(c, ctx, 8, 8, 7, bend=-0.4)
    base_leaves(c, ctx, [(8, 15, 4.5, 10.0, 1.4, 0.4), (8, 13, 11.5, 9.5, 1.4, -0.4),
                         (8, 16, 11.0, 13.5, 1.3, 0)], p=LEAF_BLUE)
    c.add(ellipse(ctx, 8, 7.2, 1.6, 1.2), LEAF_BLUE, salt="cal")
    f = ctx.zeros()
    for i in range(7):
        a = -math.pi + 0.25 + i * (math.pi - 0.5) / 6
        tip = (8 + math.cos(a) * 4.0, 5.6 + math.sin(a) * 3.8)
        f = np.maximum(f, leaf(ctx, (8, 5.8), tip, 1.6, fat=0.75))
        f = np.maximum(f, ctx.circle(tip[0], tip[1], 0.7))
    c.add(f, BLUE, outline=True, light=0.35, salt="cf")
    c.add(ctx.circle(8, 5.6, 1.2), pal("1e1250", "2c1a6e", "3f2890"), salt="cc")
    return c.done()


@texture("block/lily_of_the_valley")
def lily_of_the_valley(ctx):
    c = Canvas(ctx)
    base_leaves(c, ctx, [(7, 16, 3.2, 6.5, 3.8, 0.7), (8.5, 16, 11.0, 10.5, 3.0, -0.3)])
    arch = bez((7.5, 16.5), (6.0, 1.0), (13.5, 3.5), 14)
    c.add(curve(ctx, arch, 1.0), STEM, light=0.2, salt="arch")
    bells = ctx.zeros()
    for x, y in ((8.5, 4.6), (10.9, 5.0), (13.2, 6.0)):
        bells = np.maximum(bells, ellipse(ctx, x, y, 1.25, 1.15))
        bells = np.maximum(bells, ctx.rect(round(x) - 2, round(y + 0.6), round(x) + 1, round(y + 0.6) + 1)
                           * ellipse(ctx, x, y + 0.6, 1.6, 1.0))
    c.add(bells, WHITE, outline=True, outline_color=hexc("8e9a88"), salt="bell", light=0.4)
    return c.done()


@texture("block/wither_rose")
def wither_rose(ctx):
    c = Canvas(ctx)
    stem = pal("1a1714", "26211c", "332c25", "41382f", "50463b")
    stem_to(c, ctx, 8, 8, 7.5, bend=0.7, p=stem)
    c.add(px(ctx, [(9, 11), (7, 13), (9, 14)]), stem, salt="thorn")
    base_leaves(c, ctx, [(8, 13.5, 4.0, 11.5, 2.2, 0.5), (8.5, 10.5, 12.0, 9.5, 2.0, -0.5)],
                p=pal("15140f", "1f1d16", "2b281e", "383427", "464031"))
    head = union(ctx.circle(8, 5, 3.2), ctx.circle(5.7, 6.4, 1.4), ctx.circle(10.3, 6.4, 1.4))
    c.add(head, DARK, outline=True, outline_color=hexc("0c0a0a"), light=0.4, salt="wr")
    d, a = radial(ctx, 8, 5)
    swirl = (np.sin(a * 2 + d * 2.6) > 0.55) & (d < 2.6)
    c.recolor(swirl.astype(np.float32), DARK[0])
    c.recolor(px(ctx, [(7, 3), (8, 4), (6, 5)]), hexc("5a2a2a"))
    return c.done()


@texture("block/torchflower")
def torchflower(ctx):
    c = Canvas(ctx)
    stem_to(c, ctx, 8, 8, 9, bend=0.3)
    base_leaves(c, ctx, [(8, 14, 4.0, 11.5, 2.0, 0.4), (8, 12.5, 12.0, 10.5, 2.0, -0.4)])
    c.add(union(leaf(ctx, (8, 10), (5.0, 8.3), 1.8), leaf(ctx, (8, 10), (11, 8.3), 1.8)), LEAF, salt="cal")
    flame = ctx.polygon([(8, 0.8), (9.6, 3.0), (10.9, 5.6), (10.6, 8.2), (8, 9.8), (5.4, 8.2), (5.1, 5.6),
                         (6.4, 3.2)])
    c.add(flame, ORANGE, outline=True, outline_color=RED[1], shade=vgrad(ctx, 1, 10, 0.15, -0.15),
          salt="tf", emissive=0.15)
    core = ctx.polygon([(8, 3.6), (9.2, 6.0), (8.8, 8.0), (7.2, 8.0), (6.8, 6.0)])
    c.recolor(core, pal("fbd24a")[0], emissive=0.6)
    c.recolor(px(ctx, [(8, 6), (8, 7)]), pal("fff2a0")[0], emissive=0.8)
    return c.done()


@texture("block/cactus_flower")
def cactus_flower(ctx):
    c = Canvas(ctx)
    c.add(union(ellipse(ctx, 8, 14.8, 3.2, 1.6), ctx.rect(5.5, 14.5, 10.5, 16)),
          pal("2c4a1c", "3c6224", "4f7a2e", "649238"), salt="base")
    f = ctx.zeros()
    for i, a in enumerate((-165, -130, -105, -75, -50, -15)):
        r = math.radians(a)
        L = 5.6 if i in (2, 3) else 4.7
        f = np.maximum(f, leaf(ctx, (8, 13.2), (8 + math.cos(r) * L, 13.2 + math.sin(r) * L), 2.6, fat=0.6))
    c.add(f, MAGENTA, outline=True, light=0.35, shade=vgrad(ctx, 7, 14, 0.15, -0.1), salt="cfl")
    c.recolor(union(ctx.rect(7, 10, 9, 13), px(ctx, [(8, 9)])), YELLOW[4])
    c.recolor(px(ctx, [(7, 12), (8, 12)]), YELLOW[2])
    return c.done()


def eyeblossom(ctx, is_open, emissive_only=False):
    c = Canvas(ctx)
    stem_to(c, ctx, 8, 8, 8, bend=-0.5, p=PALE_STEM)
    base_leaves(c, ctx, [(8, 16, 3.5, 12.0, 2.4, 0.5), (8, 15, 12.8, 11.5, 2.2, -0.5)], p=PALE_STEM)
    if is_open:
        f = petals(ctx, 8, 5.2, 6, 3.9, 2.4, rot=-math.pi / 2, inner=0.4)
        c.add(f, PALE_PETAL, outline=True, light=0.3, salt="eb")
        d, a = radial(ctx, 8, 5.2)
        c.add(ctx.circle(8, 5.2, 1.9), EYE, outline=True, light=0.3, salt="eye", emissive=0.85)
        vein = (np.abs(np.sin(a * 3)) < 0.18) & (d > 1.9) & (d < 3.1)
        c.recolor(vein.astype(np.float32), EYE[2], emissive=0.6)
        c.recolor(ctx.rect(7.5, 4.7, 8.5, 5.7), pal("3a1404")[0], emissive=0.0)
    else:
        bud = ctx.polygon([(8, 1.8), (9.8, 4.5), (10.2, 7.0), (8, 8.8), (5.8, 7.0), (6.2, 4.5)])
        c.add(bud, pal("2e2a34", "403a48", "554d5e", "6a6274", "807888"), outline=True, salt="bud",
              shade=vgrad(ctx, 2, 9, 0.12, -0.1))
        c.recolor(ctx.segment(8, 3, 8, 7.6, 0.9), pal("2a2430")[0])
    t = c.done()
    if emissive_only:
        glow = t.emissive > 0.01
        t.alpha = glow.astype(np.float32)
        t.emissive = np.where(glow, 1.0, 0.0).astype(np.float32)
        t.color = np.where(glow[..., None], t.color, 0)
    return t


register("block/open_eyeblossom", lambda ctx: eyeblossom(ctx, True))
register("block/open_eyeblossom_emissive", lambda ctx: eyeblossom(ctx, True, True))
register("block/closed_eyeblossom", lambda ctx: eyeblossom(ctx, False))


# ---------------------------------------------------------------- flower beds (top-down)

def bed(ctx, colors, n_petals, size, salt, tiny=False):
    c = Canvas(ctx)
    rng = ctx.rng(salt)
    quads = [(0, 0), (8, 0), (0, 8), (8, 8)]
    leafm = ctx.zeros()
    flowers = []
    for qi, (qx, qy) in enumerate(quads):
        count = 3 if tiny else 1
        for k in range(count):
            if tiny:
                cx, cy = qx + rng.uniform(2, 6), qy + rng.uniform(2, 6)
                if k:
                    cx, cy = qx + 2 + (k * 2.6 + rng.uniform(0, 1.5)) % 4.5, qy + 2 + ((k + qi) * 2.2) % 4.5
            else:
                cx, cy = qx + 4 + rng.uniform(-0.6, 0.6), qy + 4 + rng.uniform(-0.6, 0.6)
            flowers.append((cx, cy, colors[(qi * count + k) % len(colors)]))
            for j in range(2):
                a = rng.uniform(0, 2 * math.pi)
                L = size * 1.1
                leafm = np.maximum(leafm, leaf(ctx, (cx, cy), (cx + math.cos(a) * L, cy + math.sin(a) * L),
                                               1.5 if tiny else 2.0))
    c.add(leafm, LEAF, salt="bedleaf")
    for i, (cx, cy, p) in enumerate(flowers):
        f = petals(ctx, cx, cy, n_petals, size, size * (0.75 if tiny else 0.8), rot=rng.uniform(0, 6.3),
                   inner=0)
        c.add(f, p, light=0.3, noise=0.1, salt=f"bf{i}")
        c.recolor(ctx.rect(math.floor(cx), math.floor(cy), math.floor(cx) + 1, math.floor(cy) + 1),
                  YELLOW[4] if p is not YELLOW else ORANGE[4])
    return c.done()


register("block/pink_petals", lambda ctx: bed(ctx, [PINK, shift(PINK, 0.15)], 5, 2.9, "pinkp"))
register("block/wildflowers", lambda ctx: bed(ctx, [YELLOW, WHITE, ALLIUM, YELLOW, ORCHID, WHITE], 4, 1.4,
                                              "wildf", tiny=True))
register("block/pink_petals_stem", lambda ctx: stem_fill(ctx, STEM, salt="pps"))
register("block/wildflowers_stem", lambda ctx: stem_fill(ctx, LEAF, salt="wfs"))


# ---------------------------------------------------------------- tall flowers

def thick_stem(c, ctx, y0, y1, x=8, width=1.6, bend=0.0, p=STEM):
    c.add(stalk(ctx, x, y0, x + bend * 0.3, y1, width, bend), p, light=0.3, salt="tstem")


@texture("block/sunflower_bottom")
def sunflower_bottom(ctx):
    c = Canvas(ctx)
    thick_stem(c, ctx, 16.5, -0.5, bend=0.4)
    base_leaves(c, ctx, [(8, 11, 2.0, 7.5, 3.2, 0.6), (8, 6, 14.0, 3.0, 3.0, -0.6),
                         (8, 15, 12.5, 12.5, 2.4, -0.3)])
    return c.done()


@texture("block/sunflower_top")
def sunflower_top(ctx):
    c = Canvas(ctx)
    thick_stem(c, ctx, 16.5, 6.5, x=8.1, bend=-0.3)
    base_leaves(c, ctx, [(8, 13, 3.0, 9.5, 2.6, 0.5)])
    return c.done()


@texture("block/sunflower_front")
def sunflower_front(ctx):
    c = Canvas(ctx)
    f = petals(ctx, 8, 8, 14, 7.6, 2.4, rot=0.1, inner=2.5, fat=0.45)
    c.add(f, YELLOW, outline=True, light=0.3, salt="sfp")
    d, a = radial(ctx, 8, 8)
    disc = ctx.circle(8, 8, 4.1)
    seeds = 0.5 + 0.35 * np.sin(a * 13 + d * 3.2) * np.sin(d * 3.6) - d * 0.06
    c.add(disc, CENTER, outline=True, outline_color=hexc("2e1a06"), shade=seeds - 0.5, noise=0.25, salt="sfc")
    return c.done()


@texture("block/sunflower_back")
def sunflower_back(ctx):
    c = Canvas(ctx)
    f = petals(ctx, 8, 8, 14, 7.6, 2.4, rot=0.1, inner=2.5, fat=0.45)
    c.add(f, shift(YELLOW, -0.18), outline=True, light=0.2, salt="sbp")
    sep = union(ctx.circle(8, 8, 4.6), petals(ctx, 8, 8, 9, 5.8, 2.0, rot=0.4, inner=3))
    c.add(sep, LEAF, outline=True, salt="sbs")
    c.add(ctx.circle(8, 8, 1.4), STEM, outline=True, salt="sbm")
    return c.done()


def bush_part(ctx, c, salt, top, n=24, p=LEAF, y1=16.5):
    rng = ctx.rng(salt)
    stems = ctx.zeros()
    for x0, x1, b in ((7.5, 4.5, -0.8), (8.5, 11.5, 0.8), (8, 8.5, 0.2)):
        stems = np.maximum(stems, stalk(ctx, x0, y1, x1, top + 1, 1.0, b))
    c.add(stems, STEM, light=0.2, salt=f"{salt}s")
    c.add(leaf_spray(ctx, rng, n, 3, top + 1, 13, 15.5, length=(2.4, 3.8), width=(1.8, 2.6)), p,
          salt=f"{salt}l", light=0.3)


@texture("block/lilac_bottom", "block/rose_bush_bottom", "block/peony_bottom")
def double_bottom(ctx):
    c = Canvas(ctx)
    p = {"lilac": LEAF, "rose": shift(LEAF, -0.12), "peony": LEAF_BLUE}[ctx.name.split("/")[1].split("_")[0]]
    rng = ctx.rng("dbstem")
    stems = ctx.zeros()
    for x0, x1, b in ((7.5, 5.0, -0.6), (8.5, 11.0, 0.7), (8, 8.0, 0.3)):
        stems = np.maximum(stems, stalk(ctx, x0, 16.5, x1, -0.5, 1.0, b))
    c.add(stems, STEM, light=0.2, salt="dbs")
    c.add(leaf_spray(ctx, rng, 30, 2.5, 0, 13.5, 15, length=(2.6, 4.0), width=(2.0, 2.8)), p, salt="dbl")
    if ctx.name.endswith("rose_bush_bottom"):
        c.add(px(ctx, [(5, 6), (11, 9), (7, 12)]), RED, salt="rb")
    return c.done()


@texture("block/lilac_top")
def lilac_top(ctx):
    c = Canvas(ctx)
    bush_part(ctx, c, "lt", 8, n=14)
    rng = ctx.rng("lilacfl")
    for cx, top, base, w in ((5, 2.5, 10, 2.6), (11, 1.5, 9.5, 2.6), (8, 5.5, 11.5, 2.2)):
        cone = union(ctx.polygon([(cx, top), (cx + w, base - 1.5), (cx, base), (cx - w, base - 1.5)]),
                     ctx.circle(cx, base - 1.8, w * 0.9))
        for _ in range(8):
            cone = np.maximum(cone, ctx.circle(cx + rng.uniform(-w, w) * 0.8, rng.uniform(top + 1, base - 1), 0.9)
                              * ellipse(ctx, cx, (top + base) / 2, w + 0.8, (base - top) / 2 + 0.6))
        c.add(cone, LILAC, outline=True, noise=0.45, light=0.35, salt=f"lc{cx}")
    return c.done()


@texture("block/rose_bush_top")
def rose_bush_top(ctx):
    c = Canvas(ctx)
    bush_part(ctx, c, "rt", 3, n=26, p=shift(LEAF, -0.12))
    for x, y, r in ((5, 5.5, 2.2), (11, 4.5, 2.3), (8.5, 10, 2.1), (3.5, 11.5, 1.6), (13, 10.5, 1.6)):
        c.add(ctx.circle(x, y, r), RED, outline=True, light=0.35, salt=f"rr{x}")
        d, a = radial(ctx, x, y)
        c.recolor(((np.sin(a * 2 + d * 3) > 0.6) & (d < r - 0.8)).astype(np.float32), RED[2])
    return c.done()


@texture("block/peony_top")
def peony_top(ctx):
    c = Canvas(ctx)
    bush_part(ctx, c, "pt", 7, n=16, p=LEAF_BLUE)
    for x, y, r in ((5, 5, 3.4), (11.5, 4, 3.1), (8.5, 9.0, 2.6)):
        m = ctx.circle(x, y, r * 0.75)
        for i in range(8):
            a = i / 8 * 2 * math.pi
            m = np.maximum(m, ctx.circle(x + math.cos(a) * r * 0.62, y + math.sin(a) * r * 0.55, r * 0.42))
        c.add(m, PEONY, outline=True, noise=0.3, light=0.35, salt=f"pe{x}")
        d, a = radial(ctx, x, y)
        c.recolor(((np.cos(a * 5 + d * 2) > 0.7) & (d < r * 0.8)).astype(np.float32), PEONY[2])
    return c.done()
