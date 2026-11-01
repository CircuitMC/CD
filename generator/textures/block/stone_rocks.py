"""Natural rock variants and their cut forms: granite / diorite / andesite, tuff, calcite,
basalt, dripstone, end stone, obsidian, bone block, blackstone and deepslate families."""
import numpy as np

from ...engine import GOLD, Tex, pal, smoothstep
from ...materials import DEEPSLATE, STONE, layered, pebbles
from ...registry import register, texture
from .stone_common import (blocks, bond, carve, cracks, emboss, frame, grid, mottled, ore_clusters,
                           pits, polished, speckle, spike_tex)

GRANITE = pal("6e4234", "86523f", "985e4b", "a76b57", "b47864", "c38874")
DIORITE = pal("8e8e8c", "a9a9a7", "bbbbb8", "c9c9c6", "d7d7d4", "e6e6e3")
ANDESITE = pal("5a5a5c", "6a6a6c", "77777a", "838386", "8f8f92", "9d9d9f")
TUFF = pal("464842", "53564f", "5f625a", "6b6e65", "777a70", "85887d")
CALCITE = pal("c4c6c3", "d3d5d2", "dddfdc", "e7e8e5", "f0f1ee", "f9f9f7")
BASALT = pal("2a2a2f", "36363b", "414147", "4d4d53", "5a5a61", "68686f")
BLACKSTONE = pal("19161b", "211d24", "2a252d", "332d36", "3d3741", "4a434e")
END_STONE = pal("b3b67f", "c5c890", "d3d69d", "dddfa8", "e6e8b3", "f0f2c2")
OBSIDIAN = pal("0b0911", "120e1b", "1a1427", "241b35", "312447", "463562")
BONE = pal("aea78c", "c3bca0", "d2ccb1", "ddd8bf", "e7e3cc", "f2efdd")
DRIPSTONE = pal("634e40", "735b4b", "816757", "8e7362", "9c806e", "ab8f7c")


# ---------------------------------------------------------------- granite / diorite / andesite

@texture("block/granite")
def granite(ctx):
    t = mottled(ctx, GRANITE[1:], cell=4, contrast=0.55, salt="granite")
    speckle(ctx, t, pal("5a3428")[0], 0.07, "gd", height=0.35, size=2)
    speckle(ctx, t, pal("d6ae9c")[0], 0.05, "gl", height=0.65)
    speckle(ctx, t, pal("c08a76")[0], 0.06, "gf", height=0.6, size=2)
    return t


@texture("block/polished_granite")
def polished_granite(ctx):
    return polished(ctx, GRANITE, salt="pgr", flecks=pal("c69480")[0], fleck_density=0.07)


@texture("block/diorite")
def diorite(ctx):
    t = mottled(ctx, DIORITE[1:], cell=4, contrast=0.5, salt="diorite")
    speckle(ctx, t, pal("78787a")[0], 0.06, "dm", height=0.4, size=2)
    speckle(ctx, t, pal("505052")[0], 0.035, "dd", height=0.3)
    speckle(ctx, t, DIORITE[-1], 0.05, "dl", height=0.65)
    return t


@texture("block/polished_diorite")
def polished_diorite(ctx):
    return polished(ctx, DIORITE, salt="pdi", flecks=pal("8a8a8c")[0], fleck_density=0.06)


@texture("block/andesite")
def andesite(ctx):
    t = mottled(ctx, ANDESITE[1:], cell=3, contrast=0.55, salt="andesite", streaks=2)
    speckle(ctx, t, ANDESITE[-1] * 1.05, 0.06, "al", height=0.62)
    speckle(ctx, t, ANDESITE[0], 0.06, "ad", height=0.35)
    return t


@texture("block/polished_andesite")
def polished_andesite(ctx):
    return polished(ctx, ANDESITE, salt="pan", flecks=ANDESITE[-1], fleck_density=0.06)


# ---------------------------------------------------------------- tuff

def tuff_base(ctx):
    t = mottled(ctx.sub("block/tuff"), TUFF[1:], cell=5, contrast=0.55, salt="tuff")
    pits(ctx.sub("block/tuff"), t, 0.06, "tuff", dark_f=0.68)
    speckle(ctx.sub("block/tuff"), t, pal("9a9c8e")[0], 0.04, "ash", height=0.6)
    return t


@texture("block/tuff")
def tuff(ctx):
    return tuff_base(ctx)


@texture("block/polished_tuff")
def polished_tuff(ctx):
    return polished(ctx, TUFF, salt="ptuff", flecks=TUFF[0], fleck_density=0.04)


TUFF_BRICKS = [(2, 0, 8, 5), (10, 0, 8, 5), (0, 5, 4, 3), (4, 5, 4, 3), (8, 5, 4, 3), (12, 5, 4, 3),
               (6, 8, 8, 5), (14, 8, 8, 5), (2, 13, 4, 3), (6, 13, 4, 3), (10, 13, 4, 3), (14, 13, 4, 3)]


@texture("block/tuff_bricks")
def tuff_bricks(ctx):
    fill = mottled(ctx.sub("tb_fill"), TUFF[1:], cell=6, contrast=0.5, salt="tbf")
    t, _, _ = blocks(ctx, TUFF_BRICKS, fill, TUFF[0] * 0.85, salt="tb")
    return t


def _chiseled_tuff_side(ctx, bricks):
    if bricks:
        fill = mottled(ctx.sub("ctb_fill"), TUFF[1:], cell=6, contrast=0.5, salt="ctbf")
        rects = [(0, 0, 4, 4), (4, 0, 4, 4), (8, 0, 4, 4), (12, 0, 4, 4), (0, 4, 16, 8),
                 (2, 12, 4, 4), (6, 12, 4, 4), (10, 12, 4, 4), (14, 12, 4, 4)]
        t, _, _ = blocks(ctx, rects, fill, TUFF[0] * 0.85, salt="ctb")
        # embossed diamond emblem on the big block
        d = np.abs(ctx.x - 7.5) + np.abs(ctx.y - 7.5) * 1.6
        emboss(ctx, t, (d < 4.5) & ~(d < 2.2), lit=1.2)
        carve(ctx, t, (d < 1.2).astype(np.float32))
        return t
    t = polished(ctx.sub("ct"), TUFF, salt="ct")
    for y0, y1 in ((0, 4), (4, 12), (12, 16)):
        frame(ctx, t, 0, y0, 16, y1, TUFF[-1], TUFF[0])
    # carved band with a row of square sockets
    carve(ctx, t, ctx.rect(2, 7, 14, 9))
    for x in (3, 7, 11):
        carve(ctx, t, ctx.rect(x, 5, x + 2, 6) + ctx.rect(x, 10, x + 2, 11))
    return t


def _chiseled_tuff_top(ctx, bricks):
    t = polished(ctx.sub("ctt"), TUFF, salt="ctt")
    ring = ctx.rect(3, 3, 13, 13) * (1 - ctx.rect(4, 4, 12, 12))
    carve(ctx, t, ring)
    if bricks:
        carve(ctx, t, ctx.rect(7, 5, 9, 11) + ctx.rect(5, 7, 11, 9))
    else:
        carve(ctx, t, ctx.rect(7, 7, 9, 9))
    return t


register("block/chiseled_tuff", lambda ctx: _chiseled_tuff_side(ctx, False))
register("block/chiseled_tuff_top", lambda ctx: _chiseled_tuff_top(ctx, False))
register("block/chiseled_tuff_bricks", lambda ctx: _chiseled_tuff_side(ctx, True))
register("block/chiseled_tuff_bricks_top", lambda ctx: _chiseled_tuff_top(ctx, True))


# ---------------------------------------------------------------- calcite

@texture("block/calcite")
def calcite(ctx):
    t = mottled(ctx, CALCITE[1:], cell=8, contrast=0.65, salt="calcite", smooth=0.3)
    n = ctx.noise(6, 2, 0.5, salt="cvein")
    vein = np.abs(n - 0.5) < (0.035 if ctx.pixel_art else 0.025)
    vein = ctx.organic(vein.astype(np.float32), 0.2, "cv")
    t.color = np.where(vein[..., None], pal("b9bfc2")[0], t.color)
    t.height = np.where(vein, 0.38, t.height)
    speckle(ctx, t, CALCITE[0], 0.03, "cs")
    return t


# ---------------------------------------------------------------- basalt

def _columns(ctx, salt, widths=(3, 4, 5)):
    """Vertical column boundaries: returns (column index per pixel, seam mask, x-in-column)."""
    rng = ctx.rng(f"col{salt}")
    xs, x = [], 0
    while x < ctx.w:
        xs.append(x)
        x += int(rng.choice(widths))
    xs = np.array(xs + [ctx.w], np.float32)
    if xs[-1] - xs[-2] < 2:
        xs = np.delete(xs, -2)
    idx = np.searchsorted(xs, ctx.x, side="right") - 1
    local = ctx.x - xs[idx]
    width = (xs[idx + 1] - xs[idx])
    return idx, local, width


@texture("block/basalt_side")
def basalt_side(ctx):
    idx, local, width = _columns(ctx, "bs")
    g = ctx.noise(3, 2, 0.5, salt="bss", stretch=(0.7, 4))
    tone = ctx.rng("bst").uniform(-0.12, 0.12, 16).astype(np.float32)[idx]
    v = 0.5 + tone + (g - 0.5) * 0.45 + (ctx.texel_noise("bsg") - 0.5) * 0.2
    v = v + np.where(local < 1, 0.18, 0) - np.where(local >= width - 1, 0.22, 0)
    seam = (local < 1) & (ctx.noise(2, 2, salt="bsb", stretch=(1, 3)) > 0.35)
    seam = (np.roll(seam, -ctx.s, 1) if False else seam)
    col = ctx.palette(BASALT[1:], np.clip(v, 0, 1))
    col = np.where(seam[..., None], BASALT[0], col)
    h = np.where(seam, 0.1, 0.45 + g * 0.2 - (local >= width - 1) * 0.1)
    # occasional horizontal fractures
    fr = (ctx.texel_noise("bsf", soft=False) < 0.05) & ~seam
    col = np.where(fr[..., None], BASALT[0], col)
    return Tex(ctx, col, height=h, smooth=0.15, porosity=0.1)


@texture("block/basalt_top")
def basalt_top(ctx):
    vo = ctx.voronoi(5, "btop", min_dist=5.5)
    tone = ctx.rng("btt").uniform(0.35, 0.65, len(vo["points"])).astype(np.float32)
    lit = np.clip(-(vo["dx"] + vo["dy"]) / 8, -0.4, 0.4)
    v = tone[vo["id"]] + lit * 0.6 + (ctx.texel_noise("btg") - 0.5) * 0.18
    border = vo["f2"] - vo["f1"]
    joint = border < 0.9
    col = ctx.palette(BASALT[1:], np.clip(v, 0, 1))
    col = np.where(joint[..., None], BASALT[0], col)
    # radial cooling cracks inside each cell
    ring = np.abs((vo["f1"] % 2.6) - 1.3) < 0.18
    col = np.where((ring & ~joint & (vo["f1"] > 1.5))[..., None], col * 0.86, col)
    return Tex(ctx, col, height=np.where(joint, 0.1, 0.5 + np.clip(border / 4, 0, 0.3)), smooth=0.15)


@texture("block/polished_basalt_side")
def polished_basalt_side(ctx):
    g = ctx.noise(2, 2, 0.5, salt="pbs", stretch=(1, 6))
    lx = ctx.x % 4
    v = 0.5 + (g - 0.5) * 0.35 + (ctx.texel_noise("pbg") - 0.5) * 0.12
    v = v + np.where(lx < 1, 0.22, 0) - np.where(lx >= 3, 0.2, 0)
    col = ctx.palette(BASALT[1:], np.clip(v, 0, 1))
    return Tex(ctx, col, height=0.5 + (lx < 1) * 0.1 - (lx >= 3) * 0.12, smooth=0.4, porosity=0.04)


@texture("block/polished_basalt_top")
def polished_basalt_top(ctx):
    dx, dy = ctx.x - ctx.w / 2, ctx.y - ctx.h / 2
    r = np.maximum(np.abs(dx), np.abs(dy)) * 0.7 + np.hypot(dx, dy) * 0.3
    ang = np.arctan2(dy, dx) / (2 * np.pi)
    s = (r / 2.2 + ang) % 1.0
    v = 0.35 + s * 0.45 + (ctx.texel_noise("pbt") - 0.5) * 0.12
    col = ctx.palette(BASALT[1:], np.clip(v, 0, 1))
    t = Tex(ctx, col, height=0.45 + s * 0.15, smooth=0.4, porosity=0.04)
    frame(ctx, t, 0, 0, 16, 16, BASALT[-1], BASALT[0])
    return t


@texture("block/smooth_basalt")
def smooth_basalt(ctx):
    t = mottled(ctx, BASALT[1:5], cell=8, contrast=0.6, salt="sb", smooth=0.3)
    speckle(ctx, t, BASALT[-1], 0.03, "sbl", height=0.6)
    speckle(ctx, t, BASALT[0], 0.04, "sbd", height=0.35)
    return t


# ---------------------------------------------------------------- dripstone

@texture("block/dripstone_block")
def dripstone_block(ctx):
    g = ctx.noise(3, 3, 0.5, salt="drip", stretch=(0.6, 3))
    b = ctx.noise(8, 2, 0.5, salt="dripb", stretch=(3, 0.6))
    v = g * 0.55 + b * 0.25 + ctx.texel_noise("dripg") * 0.2
    col = ctx.palette(DRIPSTONE[1:], v)
    t = Tex(ctx, col, height=0.4 + g * 0.3, smooth=0.25, porosity=0.15)
    # vertical flow grooves
    gro = (np.abs(ctx.noise(2, 1, salt="dripg2", stretch=(0.5, 5)) - 0.5) < 0.05)
    t.color = np.where(gro[..., None], DRIPSTONE[0], t.color)
    t.height = np.where(gro, 0.15, t.height)
    return t


for _dir in ("down", "up"):
    for _piece in ("base", "frustum", "middle", "tip", "tip_merge"):
        register(f"block/pointed_dripstone_{_dir}_{_piece}",
                 (lambda piece, up: lambda ctx: spike_tex(ctx, piece, up, DRIPSTONE, salt="drip"))(_piece, _dir == "up"))


# ---------------------------------------------------------------- end stone

def end_stone_base(ctx):
    c = ctx.sub("block/end_stone")
    t = mottled(c, END_STONE[1:], cell=5, contrast=0.55, salt="end")
    pits(c, t, 0.07, "endpit", dark_f=0.78, lit_f=1.06)
    speckle(c, t, END_STONE[0] * 0.95, 0.04, "endd", height=0.35)
    return t


@texture("block/end_stone")
def end_stone(ctx):
    return end_stone_base(ctx)


@texture("block/end_stone_bricks")
def end_stone_bricks(ctx):
    fill = mottled(ctx.sub("esb"), END_STONE[1:], cell=6, contrast=0.5, salt="esb")
    rects = bond(2, 4, 8, offset=4) + bond(2, 4, 8, offset=4, y0=8)
    t, _, _ = blocks(ctx, rects, fill, END_STONE[0] * 0.8, salt="esb", lit=1.06, dark=0.88)
    return t


# ---------------------------------------------------------------- obsidian

def obsidian_base(ctx):
    c = ctx.sub("block/obsidian")
    n = c.noise(6, 3, 0.55, salt="obs")
    vo = c.voronoi(7, "obsv", min_dist=4)
    facet = np.clip(-(vo["dx"] * 0.6 + vo["dy"]) / 6 + 0.5, 0, 1)
    v = n * 0.45 + facet * 0.35 + c.texel_noise("obsg") * 0.2
    col = c.palette(OBSIDIAN[:-1], v)
    ridge = (vo["f2"] - vo["f1"]) < 0.5
    col = np.where(ridge[..., None] & (vo["dy"] < 0)[..., None], OBSIDIAN[-1], col)
    t = Tex(ctx, col, height=0.5 + facet * 0.2, smooth=0.85, f0=0.05)
    return t


@texture("block/obsidian")
def obsidian(ctx):
    return obsidian_base(ctx)


@texture("block/crying_obsidian")
def crying_obsidian(ctx):
    t = obsidian_base(ctx)
    tears = pal("4a1680", "7a24c8", "a64cf0", "dc9cff")
    t = ore_clusters(ctx, t, tears, salt="tear", count=6, size=(2, 5), min_dist=5, smooth=0.95,
                     glow=0.75, rim=0.8)
    # drips running down from some tears
    rng = ctx.rng("drips")
    for i in range(5):
        x, y = int(rng.integers(0, 16)), int(rng.integers(0, 16))
        L = int(rng.integers(2, 5))
        m = (ctx.rect(x, y, x + 1, y + L) + ctx.rect(x, y - 16, x + 1, y + L - 16)) > 0
        t.color = np.where(m[..., None], tears[1], t.color)
        t.emissive = np.where(m, 0.6, t.emissive)
        tip = (ctx.rect(x, y + L - 1, x + 1, y + L) + ctx.rect(x, y + L - 17, x + 1, y + L - 16)) > 0
        t.color = np.where(tip[..., None], tears[2], t.color)
    return t


# ---------------------------------------------------------------- bone block

@texture("block/bone_block_side")
def bone_block_side(ctx):
    g = ctx.noise(2, 2, 0.5, salt="bone", stretch=(0.6, 6))
    v = 0.5 + (g - 0.5) * 0.6 + (ctx.texel_noise("boneg") - 0.5) * 0.15
    col = ctx.palette(BONE[1:], np.clip(v, 0, 1))
    fib = np.abs(ctx.noise(1.5, 1, salt="bonef", stretch=(0.5, 6)) - 0.5) < 0.06
    col = np.where(fib[..., None], BONE[1], col)
    t = Tex(ctx, col, height=0.5 + g * 0.15 - fib * 0.1, smooth=0.3, porosity=0.2)
    edge_t = ctx.rect(0, 0, 16, 1) > 0
    edge_b = ctx.rect(0, 15, 16, 16) > 0
    t.color = np.where(edge_t[..., None], BONE[-1], t.color)
    t.color = np.where(edge_b[..., None], BONE[0], t.color)
    return t


@texture("block/bone_block_top")
def bone_block_top(ctx):
    dx, dy = ctx.x - 8, ctx.y - 8
    d = np.maximum(np.abs(dx), np.abs(dy)) * 0.55 + np.hypot(dx, dy) * 0.45
    n = ctx.noise(4, 2, 0.5, salt="bt")
    col = ctx.palette(BONE[2:], n * 0.6 + ctx.texel_noise("btg") * 0.4)
    t = Tex(ctx, col, height=0.55, smooth=0.3, porosity=0.2)
    spongy = d < 4.6 + (n - 0.5) * 1.2
    sc = ctx.palette(BONE[:3], ctx.texel_noise("bsp") * 0.8 + n * 0.2)
    t.color = np.where(spongy[..., None], sc, t.color)
    t.height = np.where(spongy, 0.3, t.height)
    pores = spongy & (ctx.texel_noise("bpo", soft=False) < 0.3)
    t.color = np.where(pores[..., None], BONE[0] * 0.8, t.color)
    t.porosity = np.where(spongy, 0.7, t.porosity)
    ring = (d >= 4.6 + (n - 0.5) * 1.2) & (d < 5.6 + (n - 0.5) * 1.2)
    t.color = np.where(ring[..., None], BONE[1], t.color)
    frame(ctx, t, 0, 0, 16, 16, BONE[-1], BONE[1])
    return t


# ---------------------------------------------------------------- chiseled stone bricks

@texture("block/chiseled_stone_bricks")
def chiseled_stone_bricks(ctx):
    fill = mottled(ctx.sub("csb"), STONE[1:5], cell=6, contrast=0.5, salt="csb")
    t, _, _ = blocks(ctx, [(0, 0, 16, 4), (0, 4, 16, 8), (0, 12, 16, 4)], fill, STONE[0] * 0.85,
                     salt="csb")
    d = np.hypot(ctx.x - 8, ctx.y - 7.5)
    carve(ctx, t, ((d < 3.4) & (d >= 2.2)).astype(np.float32))
    carve(ctx, t, (d < 1.0).astype(np.float32))
    for x in (2, 13):
        carve(ctx, t, ctx.rect(x, 7, x + 1, 9))
    return t


# ---------------------------------------------------------------- blackstone

def blackstone_base(ctx):
    c = ctx.sub("block/blackstone")
    t = mottled(c, BLACKSTONE[1:], cell=4, contrast=0.6, salt="bls")
    vo = c.voronoi(9, "blsv", min_dist=3.5)
    crev = ((vo["f2"] - vo["f1"]) < 0.6) & (c.noise(4, 1, salt="blc") > 0.45)
    t.color = np.where(crev[..., None], BLACKSTONE[0], t.color)
    t.height = np.where(crev, 0.12, t.height)
    lip = np.roll(crev, c.s, 0) & ~crev
    t.color = np.where(lip[..., None], BLACKSTONE[-1], t.color)
    speckle(c, t, pal("5a5260")[0], 0.03, "blsl", height=0.65)
    return t


@texture("block/blackstone")
def blackstone(ctx):
    return blackstone_base(ctx)


@texture("block/blackstone_top")
def blackstone_top(ctx):
    vo = ctx.voronoi(3, "bltop", min_dist=7)
    bands = np.floor(vo["f1"] / 1.6 + ctx.noise(4, 2, salt="blb") * 1.4) % 3
    v = 0.3 + bands * 0.2 + (ctx.texel_noise("bltg") - 0.5) * 0.25
    col = ctx.palette(BLACKSTONE[1:], np.clip(v, 0, 1))
    t = Tex(ctx, col, height=0.4 + bands * 0.1, smooth=0.15, porosity=0.1)
    speckle(ctx, t, BLACKSTONE[0], 0.06, "bltd", height=0.2)
    return t


@texture("block/polished_blackstone")
def polished_blackstone(ctx):
    return polished(ctx, BLACKSTONE, salt="pbl", flecks=BLACKSTONE[-1] * 1.1, fleck_density=0.03, smooth=0.5)


BLACKSTONE_BRICKS = bond(4, 4, 8, offset=3)


def blackstone_bricks(ctx):
    fill = mottled(ctx.sub("pbb"), BLACKSTONE[1:], cell=6, contrast=0.5, salt="pbb", smooth=0.4)
    t, _, _ = blocks(ctx.sub("block/polished_blackstone_bricks"), BLACKSTONE_BRICKS, fill,
                     BLACKSTONE[0] * 0.7, salt="pbb", lit=1.25, dark=0.82)
    return t


@texture("block/polished_blackstone_bricks")
def polished_blackstone_bricks(ctx):
    return blackstone_bricks(ctx)


@texture("block/cracked_polished_blackstone_bricks")
def cracked_polished_blackstone_bricks(ctx):
    t = blackstone_bricks(ctx)
    cracks(ctx, t, 4, BLACKSTONE[0] * 0.6, "cpbb")
    return t


@texture("block/chiseled_polished_blackstone")
def chiseled_polished_blackstone(ctx):
    t = polished(ctx, BLACKSTONE, salt="cpb", smooth=0.5)
    frame(ctx, t, 2, 2, 14, 14, BLACKSTONE[0], BLACKSTONE[-1])
    d = np.abs(ctx.x - 8) + np.abs(ctx.y - 8)
    carve(ctx, t, ((d < 5) & (d >= 3.8)).astype(np.float32))
    emboss(ctx, t, (np.maximum(np.abs(ctx.x - 8), np.abs(ctx.y - 8)) < 1.5).astype(np.float32))
    for cx, cy in ((4, 4), (11, 4), (4, 11), (11, 11)):
        carve(ctx, t, ctx.rect(cx, cy, cx + 1, cy + 1))
    return t


@texture("block/gilded_blackstone")
def gilded_blackstone(ctx):
    base = blackstone_base(ctx)
    gold = pal("8f6410", "d9a823", "f5d44a", "fff1a0")
    return ore_clusters(ctx, base, gold, salt="gild", count=6, size=(3, 7), smooth=0.75, metal_id=GOLD,
                        rim=0.7)


# ---------------------------------------------------------------- deepslate family

@texture("block/cobbled_deepslate")
def cobbled_deepslate(ctx):
    return pebbles(ctx, DEEPSLATE[1:5], 11, 3.8, DEEPSLATE[0] * 0.75, salt="cds", bevel=0.4)


@texture("block/polished_deepslate")
def polished_deepslate(ctx):
    t = polished(ctx, DEEPSLATE, salt="pds", smooth=0.45)
    lay = layered(ctx.sub("pdsl"), DEEPSLATE, stretch=5)
    inner = ctx.rect(1, 1, 15, 15) > 0
    t.color = np.where(inner[..., None], t.color * 0.6 + lay.color * 0.4, t.color)
    return t


DS_BRICKS = [(x, 0, 8, 4) for x in (0, 8)] + [(x, 4, 8, 4) for x in (4, 12)] + \
    [(x, 8, 8, 4) for x in (2, 10)] + [(x, 12, 8, 4) for x in (6, 14)]


def ds_bricks(ctx):
    fill = layered(ctx.sub("dsb"), DEEPSLATE, stretch=3, salt="dsb")
    t, _, _ = blocks(ctx.sub("block/deepslate_bricks"), DS_BRICKS, fill, DEEPSLATE[0] * 0.75, salt="dsb",
                     lit=1.18, dark=0.82)
    return t


def ds_tiles(ctx):
    fill = mottled(ctx.sub("dst"), DEEPSLATE[1:], cell=4, contrast=0.5, salt="dst")
    t, _, _ = blocks(ctx.sub("block/deepslate_tiles"), grid(4, 4), fill, DEEPSLATE[0] * 0.7, salt="dst",
                     lit=1.2, dark=0.8, tone=0.1)
    return t


@texture("block/deepslate_bricks")
def deepslate_bricks(ctx):
    return ds_bricks(ctx)


@texture("block/cracked_deepslate_bricks")
def cracked_deepslate_bricks(ctx):
    t = ds_bricks(ctx)
    cracks(ctx, t, 4, DEEPSLATE[0] * 0.55, "cdsb")
    return t


@texture("block/deepslate_tiles")
def deepslate_tiles(ctx):
    return ds_tiles(ctx)


@texture("block/cracked_deepslate_tiles")
def cracked_deepslate_tiles(ctx):
    t = ds_tiles(ctx)
    cracks(ctx, t, 4, DEEPSLATE[0] * 0.55, "cdst")
    return t


@texture("block/chiseled_deepslate")
def chiseled_deepslate(ctx):
    t = polished(ctx, DEEPSLATE, salt="chds", smooth=0.4)
    d = np.abs(ctx.x - 8) + np.abs(ctx.y - 8)
    for lo, hi in ((6, 7.2), (2.5, 3.7)):
        carve(ctx, t, ((d >= lo) & (d < hi)).astype(np.float32))
    sq = np.maximum(np.abs(ctx.x - 8), np.abs(ctx.y - 8))
    carve(ctx, t, ((sq >= 6) & (sq < 7)).astype(np.float32) * (d >= 7.2))
    return t
