"""Metal & mineral blocks: copper (4 oxidation stages x block/cut/chiseled/grate),
storage blocks, raw ore blocks, amethyst."""
import numpy as np

from ...engine import COPPER, GOLD, IRON, Tex, pal
from ...materials import pebbles
from ...registry import register, texture
from .stone_common import blocks, carve, crystal_cross, emboss, frame, grid, mottled, ore_clusters, speckle

# ---------------------------------------------------------------- copper

COPPER_P = pal("74371f", "954629", "b05834", "c56a40", "d6804f", "e89b6a")
EXPOSED_P = pal("6e4536", "8a5a47", "a06d57", "b07f66", "bf9279", "cfa68e")
PATINA_W = pal("3e6a57", "4d7f67", "5c9276", "69a283", "77b290", "8bc3a1")
PATINA_O = pal("2f6458", "3b7766", "478873", "53997f", "62a88d", "79bba2")
STAGES = {"": 0, "exposed_": 1, "weathered_": 2, "oxidized_": 3}


def patina_map(ctx, stage):
    """True where the surface has turned green. Same blotch shapes for every stage so the
    green spreads consistently from copper -> oxidized."""
    if stage == 0:
        return np.zeros((ctx.H, ctx.W), bool)
    if stage == 3:
        return np.ones((ctx.H, ctx.W), bool)
    c = ctx.sub("copper_patina")
    n = c.noise(5, 3, 0.55, salt="pat") * 0.8 + c.texel_noise("patg") * 0.2
    thr = {1: 0.74, 2: 0.36}[stage]
    return n > thr


def copper_surface(ctx, stage, salt="cu"):
    c = ctx.sub(f"copper_surface{salt}")
    brush = c.noise(1, 2, 0.5, salt="cub", stretch=(6, 1))
    n = c.noise(6, 2, 0.5, salt="cun")
    v = 0.5 + (brush - 0.5) * 0.3 + (n - 0.5) * 0.4 + (c.texel_noise("cug") - 0.5) * 0.15
    metal_p = COPPER_P if stage == 0 else EXPOSED_P
    col = ctx.palette(metal_p[1:-1], np.clip(v, 0, 1))
    pm = patina_map(ctx, stage)
    pat_p = PATINA_O if stage == 3 else PATINA_W
    pn = c.noise(3, 2, 0.5, salt="cupn") * 0.6 + c.texel_noise("cupg") * 0.4
    pcol = ctx.palette(pat_p[1:-1], pn)
    col = np.where(pm[..., None], pcol, col)
    t = Tex(ctx, col, height=0.55 + brush * 0.03 + pm * 0.04, smooth=np.where(pm, 0.25, 0.7 - brush * 0.1),
            porosity=np.where(pm, 0.3, 0.0))
    t.set_metal((~pm).astype(np.float32), COPPER)
    return t, pm, metal_p, pat_p


def _edge_cols(stage, pm_any, metal_p, pat_p):
    p = pat_p if stage >= 2 else metal_p
    return p[-1], p[0]


def copper_block(ctx, stage):
    t, pm, mp, pp = copper_surface(ctx, stage)
    hi, lo = _edge_cols(stage, pm, mp, pp)
    frame(ctx, t, 0, 0, 16, 16, hi, lo)
    for cx, cy in ((2, 2), (13, 2), (2, 13), (13, 13)):
        emboss(ctx, t, ctx.rect(cx, cy, cx + 1, cy + 1), lit=1.3)
    return t


def cut_copper(ctx, stage):
    t, pm, mp, pp = copper_surface(ctx, stage, "cut")
    p = pp if stage >= 2 else mp
    t, _, _ = blocks(ctx, grid(2, 2), t, p[0] * 0.8, lit=1.18, dark=0.8, tone=0.03, salt="cut")
    t.set_metal(((~pm) & (t.height > 0.2)).astype(np.float32), COPPER)
    return t


def chiseled_copper(ctx, stage):
    t, pm, mp, pp = copper_surface(ctx, stage, "chis")
    hi, lo = _edge_cols(stage, pm, mp, pp)
    frame(ctx, t, 0, 0, 16, 16, hi, lo)
    frame(ctx, t, 2, 2, 14, 14, lo, hi)
    ring = ctx.rect(4, 4, 12, 12) * (1 - ctx.rect(5, 5, 11, 11))
    carve(ctx, t, ring)
    emboss(ctx, t, ctx.rect(7, 7, 9, 9), lit=1.3)
    return t


def copper_grate(ctx, stage):
    t, pm, mp, pp = copper_surface(ctx, stage, "grate")
    p = pp if stage >= 2 else mp
    bars = ((ctx.tx % 5) == 0) | ((ctx.ty % 5) == 0)
    hole = ~bars
    # bevel each bar: lit just below/right of holes' top-left? light from top-left: bar texel
    # with a hole to its right/below catches light on that face -> darker; texel with a hole
    # above/left is lit.
    hole_above = np.roll(hole, ctx.s, 0)
    hole_left = np.roll(hole, ctx.s, 1)
    hole_below = np.roll(hole, -ctx.s, 0)
    hole_right = np.roll(hole, -ctx.s, 1)
    lit = bars & (hole_above | hole_left)
    dark = bars & (hole_below | hole_right) & ~lit
    t.color = np.where(lit[..., None], np.clip(t.color * 1.18, 0, 1), t.color)
    t.color = np.where(dark[..., None], t.color * 0.78, t.color)
    t.alpha = np.where(hole, 0.0, 1.0).astype(np.float32)
    t.color = np.where(hole[..., None], p[0] * 0.5, t.color)
    t.height = np.where(hole, 0.0, t.height)
    return t


for _pre, _st in STAGES.items():
    register(f"block/{_pre}copper" if _pre else "block/copper_block",
             (lambda s: lambda ctx: copper_block(ctx, s))(_st))
    register(f"block/{_pre}cut_copper", (lambda s: lambda ctx: cut_copper(ctx, s))(_st))
    register(f"block/{_pre}chiseled_copper", (lambda s: lambda ctx: chiseled_copper(ctx, s))(_st))
    register(f"block/{_pre}copper_grate", (lambda s: lambda ctx: copper_grate(ctx, s))(_st))


# ---------------------------------------------------------------- storage blocks

IRON_P = pal("8e8e92", "aaaaae", "bdbdc1", "cdcdd1", "dcdce0", "ececef")
GOLD_P = pal("a8730e", "cf9a1c", "e3b52c", "f0cb40", "f8de5e", "fff09a")
DIAMOND_P = pal("1d7e7a", "2ea8a2", "4ccbc3", "74e2da", "a4f2ec", "dafffb")
EMERALD_P = pal("0b5a2a", "14803d", "1ea44e", "35c066", "62d88a", "a6f2c0")
LAPIS_P = pal("142168", "1b2d8a", "233aa6", "2d4abe", "3d5ed2", "5a7ce4")
NETHERITE_P = pal("2a2526", "352f31", "40393b", "4b4446", "585052", "6a6163")


def metal_plate(ctx, p, metal_id, salt, grooves=(), smooth=0.75):
    c = ctx.sub(f"plate{salt}")
    brush = c.noise(1, 2, 0.5, salt="br", stretch=(8, 1))
    n = c.noise(8, 2, 0.5, salt="mn")
    v = 0.55 + (brush - 0.5) * 0.25 + (n - 0.5) * 0.35 + (c.texel_noise("mg") - 0.5) * 0.08
    t = Tex(ctx, ctx.palette(p[1:-1], np.clip(v, 0, 1)), height=0.55 + brush * 0.03,
            smooth=smooth - brush * 0.08, porosity=0.0)
    for gy in grooves:
        g = ctx.rect(1, gy, 15, gy + 1) > 0
        lip = ctx.rect(1, gy + 1, 15, gy + 2) > 0
        t.color = np.where(g[..., None], p[0], t.color)
        t.color = np.where(lip[..., None], p[-1], t.color)
        t.height = np.where(g, 0.25, t.height)
    frame(ctx, t, 0, 0, 16, 16, p[-1], p[0])
    if metal_id:
        t.set_metal(ctx.full(1), metal_id)
    return t


@texture("block/iron_block")
def iron_block(ctx):
    t = metal_plate(ctx, IRON_P, IRON, "iron", grooves=(5, 10))
    for cx in (2, 13):
        for cy in (2, 7, 12):
            emboss(ctx, t, ctx.rect(cx, cy, cx + 1, cy + 1), lit=1.12, dark=0.8)
    return t


@texture("block/gold_block")
def gold_block(ctx):
    t = metal_plate(ctx, GOLD_P, GOLD, "gold", smooth=0.85)
    frame(ctx, t, 2, 2, 14, 14, GOLD_P[1], GOLD_P[-1])
    sheen = (np.abs((ctx.x + ctx.y) - 10) < 1.0) | (np.abs((ctx.x + ctx.y) - 13) < 0.5)
    inner = ctx.rect(3, 3, 13, 13) > 0
    t.color = np.where((sheen & inner)[..., None], GOLD_P[-2], t.color)
    return t


def gem_tiles(ctx, p, salt, smooth=0.9, f0=0.17):
    """Cut gem block: a 2x2 grid of faceted pyramids (light from top-left)."""
    lx, ly = ctx.x % 8 - 4, ctx.y % 8 - 4
    face = np.where(np.abs(lx) > np.abs(ly), np.where(lx < 0, 0.85, 0.3), np.where(ly < 0, 1.0, 0.15))
    table = (np.abs(lx) < 1.2) & (np.abs(ly) < 1.2)
    face = np.where(table, 0.65, face)
    v = face * 0.85 + ctx.texel_noise(f"gt{salt}") * 0.15
    col = ctx.palette(p[1:], np.clip(v, 0, 1))
    seam = (np.abs(np.abs(lx) - np.abs(ly)) < 0.5) & ~table & (np.maximum(np.abs(lx), np.abs(ly)) < 3.5)
    col = np.where(seam[..., None], col * 0.92, col)
    border = (np.maximum(np.abs(lx + 0.5), np.abs(ly + 0.5)) > 3.5)
    col = np.where(border[..., None], p[0], col)
    t = Tex(ctx, col, height=np.where(border, 0.2, 0.5 + (4 - np.maximum(np.abs(lx), np.abs(ly))) * 0.08),
            smooth=smooth, f0=f0)
    # sparkle
    spark = ((ctx.tx % 8) == 2) & ((ctx.ty % 8) == 2)
    t.color = np.where(spark[..., None], p[-1], t.color)
    return t


@texture("block/diamond_block")
def diamond_block(ctx):
    return gem_tiles(ctx, DIAMOND_P, "dia")


@texture("block/emerald_block")
def emerald_block(ctx):
    t = gem_tiles(ctx, EMERALD_P, "em", f0=0.16)
    return t


@texture("block/lapis_block")
def lapis_block(ctx):
    t = mottled(ctx, LAPIS_P[1:], cell=4, contrast=0.6, salt="lap", smooth=0.5)
    t.f0 = ctx.full(0.06)
    speckle(ctx, t, pal("d8c060")[0], 0.035, "pyr", height=0.65, smooth=0.8)  # pyrite flecks
    speckle(ctx, t, pal("e6eaf2")[0], 0.02, "calc", height=0.6)               # calcite flecks
    frame(ctx, t, 0, 0, 16, 16, LAPIS_P[-1], LAPIS_P[0])
    return t


@texture("block/netherite_block")
def netherite_block(ctx):
    t = metal_plate(ctx, NETHERITE_P, None, "neth", smooth=0.7)
    t, _, _ = blocks(ctx, [(0, 0, 16, 8), (0, 8, 8, 8), (8, 8, 8, 8)], t, NETHERITE_P[0] * 0.7, lit=1.25,
                     dark=0.78, tone=0.03, salt="neth")
    t.f0 = ctx.full(0.6)  # dark custom metal: high reflectance, albedo kept
    t.smooth = ctx.full(0.7)
    return t


@texture("block/coal_block")
def coal_block(ctx):
    coal = pal("19191c", "212125", "2a2a2e", "333338")
    t = pebbles(ctx, coal, 12, 3.4, pal("0e0e10")[0], salt="coal", bevel=0.5, smooth=0.5)
    r = ctx.texel_noise("cgl", soft=False) < 0.05
    t.color = np.where(r[..., None], pal("55555c")[0], t.color)
    t.smooth = np.where(r, 0.8, t.smooth)
    return t


# ---------------------------------------------------------------- raw ore blocks

RAW = {
    "iron": (pal("5e4232", "8a6650", "a8826a", "c49e84", "dcbca2"), IRON),
    "gold": (pal("7a5410", "b48420", "d6a42c", "ecc244", "fde27a"), GOLD),
    "copper": (pal("5a2c18", "8a4528", "ac5a36", "c87048", "e28e62"), COPPER),
}


def raw_block(ctx, kind):
    p, mid = RAW[kind]
    t = pebbles(ctx, p[1:4], 11, 3.2, p[0], salt=f"raw{kind}", bevel=0.55, smooth=0.45)
    # grainy surface with bright flecks
    speckle(ctx, t, p[-1], 0.06, f"rf{kind}", height=0.8)
    lumps = t.height > 0.4
    t.set_metal(lumps.astype(np.float32) * (ctx.texel_noise(f"rm{kind}", soft=False) < 0.35), mid)
    t.porosity = np.where(lumps, 0.1, 0.4)
    return t


for _k in RAW:
    register(f"block/raw_{_k}_block", (lambda k: lambda ctx: raw_block(ctx, k))(_k))


# ---------------------------------------------------------------- amethyst

AMETHYST = pal("3e2266", "53308a", "6a43a6", "8259bd", "9d76d2", "bd9be6", "dcc6f6")


def amethyst_base(ctx):
    c = ctx.sub("block/amethyst_block")
    vo = c.voronoi(9, "am", min_dist=3.6)
    facet = np.clip(-(vo["dx"] * 0.8 + vo["dy"]) / 4.5 + 0.5, 0, 1)
    tone = c.rng("amt").uniform(-0.15, 0.15, len(vo["points"])).astype(np.float32)
    v = facet * 0.7 + tone[vo["id"]] + c.texel_noise("amg") * 0.15
    col = ctx.palette(AMETHYST[1:-1], np.clip(v, 0, 1))
    edge = (vo["f2"] - vo["f1"]) < 0.5
    col = np.where(edge[..., None] & (vo["dy"] < 0)[..., None], AMETHYST[-2], col)
    col = np.where(edge[..., None] & (vo["dy"] >= 0)[..., None], AMETHYST[0], col)
    return Tex(ctx, col, height=0.45 + facet * 0.3, smooth=0.8, f0=0.07, sss=0.15)


@texture("block/amethyst_block")
def amethyst_block(ctx):
    return amethyst_base(ctx)


@texture("block/budding_amethyst")
def budding_amethyst(ctx):
    t = amethyst_base(ctx)
    buds = pal("2a1448", "a07ad8", "d2b8f4", "fbf2ff")
    return ore_clusters(ctx, t, buds, salt="bud", count=6, size=(2, 4), min_dist=5, smooth=0.9, f0=0.08,
                        rim=0.5, glow=0.1)


BUDS = {
    "small_amethyst_bud": [(8, 2.2, 4, 0), (5.5, 1.2, 3, -0.6), (10.5, 1.2, 3, 0.6)],
    "medium_amethyst_bud": [(8, 2.6, 8, 0), (5, 1.6, 5, -1.2), (11, 1.6, 5.5, 1.2)],
    "large_amethyst_bud": [(8, 2.8, 11, 0), (4.5, 1.8, 7, -1.6), (11.5, 1.8, 8, 1.6), (7, 1.2, 4, -0.5)],
    "amethyst_cluster": [(8, 2.6, 14, 0.3), (4, 1.8, 9, -2), (12, 1.8, 10, 2), (6, 1.4, 6, -1),
                         (10.5, 1.4, 6, 1.2), (2, 1.2, 4, -1.2), (14, 1.2, 4, 1.0)],
}


def bud(ctx, name):
    return crystal_cross(ctx, AMETHYST, BUDS[name], smooth=0.85, f0=0.07, glow=0.1 if "cluster" in name else 0.05,
                         sss=0.2)


for _b in BUDS:
    register(f"block/{_b}", (lambda b: lambda ctx: bud(ctx, b))(_b))
