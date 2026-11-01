"""Built / dressed stone: quartz, purpur, prismarine, sandstone families, mud, resin."""
import numpy as np

from ...engine import Tex, pal
from ...materials import RED_SAND, layered
from ...registry import register, texture
from .masonry import SANDSTONE
from .stone_common import (blocks, bond, carve, emboss, frame, grid, mottled, pillar_side, pillar_top,
                           polished, speckle)

QUARTZ = pal("b9aea3", "cfc6bd", "ddd6ce", "e7e1da", "efeae4", "f8f5f1")
PURPUR = pal("7a5a7c", "8f6b91", "a07ca2", "ae8aaf", "bb98bc", "c9a8ca")
PRISMARINE = pal("2f6b62", "3d8274", "4c9886", "5daa98", "70bcaa", "8ccfc0")
PRISM_BRICK = pal("3a7c70", "4a917f", "5aa38f", "6ab49f", "7cc3ae", "93d2c0")
DARK_PRISM = pal("1b3a32", "22483d", "2a5548", "336253", "3c6f5f", "4a7f6f")
RED_SANDSTONE = pal("8f4317", "a1501d", "ae5a23", "ba652b", "c57133", "d07e3d")
MUD = pal("2c2a2a", "363333", "3f3b3a", "484342", "514b49", "5b5452")
PACKED_MUD = pal("7a5a40", "8a684b", "977456", "a38060", "ae8b6b", "b99777")
MUD_BRICK = pal("74553f", "86644a", "937055", "9f7c5f", "aa876a", "b59376")
RESIN = pal("7a2e06", "a5410a", "c95a12", "e1761e", "f0952f", "fbb653")
RESIN_BRICK = pal("82340a", "a8470e", "c65d16", "da7320", "ea8d2d", "f6a945")


# ---------------------------------------------------------------- quartz

def quartz_face(ctx, salt="q"):
    n = ctx.noise(8, 2, 0.5, salt=f"qz{salt}")
    v = 0.55 + (n - 0.5) * 0.4 + (ctx.texel_noise(f"qzg{salt}") - 0.5) * 0.25
    return Tex(ctx, ctx.palette(QUARTZ[1:-1], np.clip(v, 0, 1)), height=0.55 + n * 0.03,
               smooth=0.6, f0=0.045, porosity=0.02)


@texture("block/quartz_block_side", "block/quartz_block_top")
def quartz_block(ctx):
    t = quartz_face(ctx.sub("block/quartz_block_side"))
    frame(ctx, t, 0, 0, 16, 16, QUARTZ[-1], QUARTZ[1])
    return t


@texture("block/quartz_block_bottom")
def quartz_block_bottom(ctx):
    t = quartz_face(ctx.sub("block/quartz_block_bottom"), "b")
    speckle(ctx, t, QUARTZ[1], 0.06, "qbb", height=0.4)
    frame(ctx, t, 0, 0, 16, 16, QUARTZ[-1], QUARTZ[1])
    return t


@texture("block/quartz_bricks")
def quartz_bricks(ctx):
    fill = quartz_face(ctx.sub("qbr"), "br")
    t, _, _ = blocks(ctx, bond(4, 4, 8, offset=4), fill, QUARTZ[0], salt="qbr", lit=1.04, dark=0.9,
                     tone=0.02)
    return t


@texture("block/quartz_pillar_side")
def quartz_pillar_side(ctx):
    return pillar_side(ctx, QUARTZ, salt="qp", smooth=0.6)


@texture("block/quartz_pillar_top")
def quartz_pillar_top(ctx):
    return pillar_top(ctx, QUARTZ, salt="qpt", rings=(0, 3), smooth=0.6)


@texture("block/chiseled_quartz_block")
def chiseled_quartz_block(ctx):
    t = quartz_face(ctx.sub("cq"), "cq")
    for y0, y1 in ((0, 3), (3, 13), (13, 16)):
        frame(ctx, t, 0, y0, 16, y1, QUARTZ[-1], QUARTZ[1])
    # carved vertical lozenge chain in the middle band
    d = np.abs(ctx.x - 8) * 1.2 + np.abs(((ctx.y - 3) % 5) - 2.5)
    carve(ctx, t, ((d < 2.6) & (d >= 1.6)).astype(np.float32) * ctx.rect(1, 4, 15, 12), depth=0.86)
    for x in (2, 13):
        carve(ctx, t, ctx.rect(x, 5, x + 1, 11), depth=0.86)
    return t


@texture("block/chiseled_quartz_block_top")
def chiseled_quartz_block_top(ctx):
    t = quartz_face(ctx.sub("cqt"), "cqt")
    frame(ctx, t, 0, 0, 16, 16, QUARTZ[-1], QUARTZ[1])
    frame(ctx, t, 2, 2, 14, 14, QUARTZ[1], QUARTZ[-1])
    d = np.hypot(ctx.x - 8, ctx.y - 8)
    carve(ctx, t, ((d < 4.2) & (d >= 3.0)).astype(np.float32), depth=0.86)
    emboss(ctx, t, (d < 1.6).astype(np.float32))
    return t


# ---------------------------------------------------------------- purpur

@texture("block/purpur_block")
def purpur_block(ctx):
    fill = mottled(ctx.sub("pp"), PURPUR[1:], cell=4, contrast=0.45, salt="pp", smooth=0.3)
    t, _, _ = blocks(ctx, grid(2, 2), fill, PURPUR[0], salt="pp", lit=1.12, dark=0.86, tone=0.04)
    # small corner nicks for a weathered look
    for cx, cy in ((2, 2), (12, 10), (5, 12), (10, 3)):
        m = ctx.rect(cx, cy, cx + 1, cy + 1) > 0
        t.color = np.where(m[..., None], PURPUR[1], t.color)
    return t


@texture("block/purpur_pillar_side")
def purpur_pillar_side(ctx):
    return pillar_side(ctx, PURPUR, salt="ppp", smooth=0.3, groove_x=(3, 7, 11))


@texture("block/purpur_pillar_top")
def purpur_pillar_top(ctx):
    return pillar_top(ctx, PURPUR, salt="pppt", rings=(0, 2), smooth=0.3)


# ---------------------------------------------------------------- prismarine

def prismarine(ctx):
    ph = ctx.frame / max(1, ctx.frames) * 2 * np.pi
    n1 = ctx.noise(6, 3, 0.55, salt="pr1")
    n2 = ctx.noise(5, 2, 0.5, salt="pr2")
    v = n1 * (0.6 + 0.25 * np.cos(ph)) + n2 * (0.4 + 0.25 * np.sin(ph))
    v = ctx.normalize(v) * 0.75 + ctx.texel_noise("prg") * 0.25
    col = ctx.palette(PRISMARINE[1:], v)
    # hue drift between teal and blue-green across frames
    shift = np.array([-0.03 * np.sin(ph), 0.02 * np.cos(ph), 0.05 * np.sin(ph)], np.float32)
    col = np.clip(col + shift * (n2[..., None] * 2 - 0.5), 0, 1)
    t = Tex(ctx, col, height=0.45 + n1 * 0.2, smooth=0.5, f0=0.05, porosity=0.05)
    vo = ctx.voronoi(6, "prv", min_dist=5)
    seam = ((vo["f2"] - vo["f1"]) < 0.5) & (ctx.noise(4, 1, salt="prs") > 0.4)
    t.color = np.where(seam[..., None], PRISMARINE[0], t.color)
    t.height = np.where(seam, 0.2, t.height)
    return t


register("block/prismarine", prismarine, frames=4, frametime=100, interpolate=True)


@texture("block/prismarine_bricks")
def prismarine_bricks(ctx):
    fill = mottled(ctx.sub("prb"), PRISM_BRICK[1:], cell=4, contrast=0.5, salt="prb", smooth=0.5)
    rects = bond(2, 4, 8, offset=4) + [(x, 8, 4, 4) for x in (0, 4, 8, 12)] + bond(1, 4, 8, offset=2, y0=12)
    t, _, _ = blocks(ctx, rects, fill, PRISM_BRICK[0] * 0.85, salt="prb", lit=1.12, dark=0.86)
    return t


@texture("block/dark_prismarine")
def dark_prismarine(ctx):
    fill = mottled(ctx.sub("dpr"), DARK_PRISM[1:], cell=4, contrast=0.5, salt="dpr", smooth=0.5)
    rects = [(0, 0, 8, 8), (8, 0, 8, 4), (8, 4, 8, 4), (0, 8, 4, 8), (4, 8, 4, 8), (8, 8, 8, 8)]
    t, _, _ = blocks(ctx, rects, fill, DARK_PRISM[0] * 0.8, salt="dpr", lit=1.18, dark=0.82)
    speckle(ctx, t, pal("5aa08c")[0], 0.025, "dprs", height=0.6)
    return t


# ---------------------------------------------------------------- sandstone families

def ss_side(ctx, p, salt):
    t = layered(ctx.sub(f"sss{salt}"), p, salt=salt)
    rows = {0: p[-1], 1: p[-2], 3: p[0], 12: p[0], 15: p[1]}
    for y, c in rows.items():
        m = ctx.rect(0, y, 16, y + 1) > 0
        t.color[m] = c
    return t


def ss_cut(ctx, p, salt):
    t = layered(ctx.sub(f"ssc{salt}"), p, stretch=6, salt=f"c{salt}")
    t.smooth = ctx.full(0.2)
    for y0, y1 in ((0, 8), (8, 16)):
        frame(ctx, t, 0, y0, 16, y1, p[-1], p[0])
    return t


def ss_chiseled(ctx, p, salt, emblem):
    t = layered(ctx.sub(f"sscc{salt}"), p, stretch=6, salt=f"cc{salt}")
    for y0, y1 in ((0, 3), (3, 13), (13, 16)):
        frame(ctx, t, 0, y0, 16, y1, p[-1], p[0])
    cx, cy = 7.5, 7.5
    if emblem == "sun":
        d = np.hypot(ctx.x - cx - 0.5, ctx.y - cy - 0.5)
        ang = np.arctan2(ctx.y - cy - 0.5, ctx.x - cx - 0.5)
        rays = (d >= 2.8) & (d < 4.6) & (np.cos(ang * 8) > 0.3)
        carve(ctx, t, (rays | ((d < 2.0) & (d >= 1.0))).astype(np.float32))
    else:  # stylised eye/beetle
        e = ((ctx.x - cx - 0.5) / 4.5) ** 2 + ((ctx.y - cy - 0.5) / 2.6) ** 2
        carve(ctx, t, ((e < 1) & (e >= 0.45)).astype(np.float32))
        carve(ctx, t, ctx.rect(7, 7, 9, 9))
        carve(ctx, t, ctx.rect(2, 4, 3, 12) + ctx.rect(13, 4, 14, 12))
    return t


def ss_top(ctx, p, salt):
    n = ctx.noise(8, 2, 0.6, salt=f"sst{salt}")
    return Tex(ctx, ctx.palette(p[2:], n * 0.75 + ctx.texel_noise(f"sst{salt}") * 0.25),
               height=0.5 + n * 0.1, smooth=0.15, porosity=0.5)


def ss_bottom(ctx, p, salt):
    t = layered(ctx.sub(f"ssb{salt}"), p, salt=f"b{salt}")
    r = ctx.texel_noise(f"ssb_speck{salt}", soft=False) < 0.05
    t.color = np.where(r[..., None], p[0], t.color)
    return t


register("block/cut_sandstone", lambda ctx: ss_cut(ctx, SANDSTONE, "s"))
register("block/chiseled_sandstone", lambda ctx: ss_chiseled(ctx, SANDSTONE, "s", "eye"))
register("block/red_sandstone", lambda ctx: ss_side(ctx, RED_SANDSTONE, "r"))
register("block/red_sandstone_top", lambda ctx: ss_top(ctx, RED_SANDSTONE, "r"))
register("block/red_sandstone_bottom", lambda ctx: ss_bottom(ctx, RED_SANDSTONE, "r"))
register("block/cut_red_sandstone", lambda ctx: ss_cut(ctx, RED_SANDSTONE, "r"))
register("block/chiseled_red_sandstone", lambda ctx: ss_chiseled(ctx, RED_SANDSTONE, "r", "sun"))


# ---------------------------------------------------------------- mud

@texture("block/mud")
def mud(ctx):
    n = ctx.noise(6, 3, 0.55, salt="mud")
    v = n * 0.6 + ctx.texel_noise("mudg") * 0.4
    t = Tex(ctx, ctx.palette(MUD[1:], v), height=0.45 + n * 0.15, smooth=0.55, porosity=0.0, f0=0.03)
    # wet glints
    wet = (n > 0.72) & (ctx.texel_noise("mudw", soft=False) < 0.25)
    t.color = np.where(wet[..., None], pal("6e6664")[0], t.color)
    t.smooth = np.where(wet, 0.85, t.smooth)
    speckle(ctx, t, MUD[0], 0.06, "mudd", height=0.3)
    return t


def packed_mud_base(ctx, p=PACKED_MUD, salt="pm"):
    t = mottled(ctx, p[1:], cell=5, contrast=0.5, salt=salt, smooth=0.12, porosity=0.4)
    rng = ctx.rng(f"straw{salt}")
    straw = pal("c9ad7a", "a88c5c")
    for i in range(9):
        x, y = float(rng.uniform(0, 16)), float(rng.uniform(0, 16))
        L = float(rng.uniform(1.5, 3.5))
        dy = float(rng.choice([-1, 0, 0, 1]))
        m = ctx.segment(x, y, x + L, y + dy * 0.8, 0.9) > 0
        m |= ctx.segment(x - 16, y, x + L - 16, y + dy * 0.8, 0.9) > 0
        t.color = np.where(m[..., None], straw[i % 2], t.color)
        t.height = np.where(m, 0.62, t.height)
    return t


@texture("block/packed_mud")
def packed_mud(ctx):
    return packed_mud_base(ctx)


@texture("block/mud_bricks")
def mud_bricks(ctx):
    fill = packed_mud_base(ctx.sub("mbf"), MUD_BRICK, "mb")
    rects = ([(x, 0, 8, 4) for x in (1, 9)] + [(x, 4, 8, 4) for x in (5, 13)] +
             [(x, 8, 8, 4) for x in (1, 9)] + [(x, 12, 8, 4) for x in (5, 13)])
    t, _, _ = blocks(ctx, rects, fill, pal("5e4634")[0], salt="mb", lit=1.1, dark=0.86)
    return t


# ---------------------------------------------------------------- resin

@texture("block/resin_block")
def resin_block(ctx):
    n = ctx.noise(6, 3, 0.55, salt="res")
    flow = ctx.noise(3, 2, 0.5, salt="resf", stretch=(1, 2.5))
    v = n * 0.5 + flow * 0.35 + ctx.texel_noise("resg") * 0.15
    t = Tex(ctx, ctx.palette(RESIN[1:], v), height=0.45 + n * 0.2, smooth=0.75, f0=0.045, sss=0.5)
    # trapped bubbles: light dot with darker ring below-right
    r = ctx.texel_noise("resb", soft=False) < 0.035
    t.color = np.where(r[..., None], RESIN[-1] * 1.02, t.color)
    sh = (np.roll(r, ctx.s, 0) | np.roll(r, ctx.s, 1)) & ~r
    t.color = np.where(sh[..., None], RESIN[1], t.color)
    return t


def resin_brick_tex(ctx):
    fill = mottled(ctx.sub("rbf"), RESIN_BRICK[1:], cell=4, contrast=0.5, salt="rbf", smooth=0.6)
    fill.sss = ctx.full(0.35)
    t, _, _ = blocks(ctx.sub("block/resin_bricks"), bond(4, 4, 8, offset=4), fill, RESIN_BRICK[0] * 0.75,
                     salt="rb", lit=1.12, dark=0.84)
    return t


@texture("block/resin_bricks")
def resin_bricks(ctx):
    return resin_brick_tex(ctx)


@texture("block/chiseled_resin_bricks")
def chiseled_resin_bricks(ctx):
    fill = mottled(ctx.sub("crbf"), RESIN_BRICK[1:], cell=4, contrast=0.5, salt="crbf", smooth=0.6)
    fill.sss = ctx.full(0.35)
    t, _, _ = blocks(ctx, [(0, 0, 16, 4), (0, 4, 16, 8), (0, 12, 16, 4)], fill, RESIN_BRICK[0] * 0.75,
                     salt="crb", lit=1.12, dark=0.84)
    # carved eye-shaped emblem
    e = ((ctx.x - 8) / 5.0) ** 2 + ((ctx.y - 7.5) / 2.4) ** 2
    carve(ctx, t, ((e < 1) & (e >= 0.5)).astype(np.float32))
    emboss(ctx, t, ctx.rect(7, 7, 9, 9))
    return t
