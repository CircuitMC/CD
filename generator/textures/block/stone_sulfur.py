"""Sulfur and cinnabar families (26.x) and sulfur spikes.

Sulfur: pale-to-deep yellow crystalline mineral with powdery bloom.
Cinnabar: vermilion red mercury ore embedded in a gray-brown matrix."""
import numpy as np

from ...engine import Tex, pal
from ...registry import register, texture
from .stone_common import blocks, bond, carve, emboss, frame, mottled, ore_clusters, polished, speckle, spike_tex

SULFUR = pal("7c6a10", "a28e1a", "c2ad26", "d8c535", "e8d850", "f5ea80")
POTENT = pal("6e7a0e", "98a818", "bccb22", "d6e238", "e8f05a", "f6fa98")
CINNABAR = pal("4e1010", "721816", "93211d", "b02c24", "c93d31", "de5a4b")
MATRIX = pal("3e3634", "4c4340", "5a504c", "685d58")


def crystalline(ctx, p, salt, cells=10):
    c = ctx.sub(f"cryst{salt}")
    vo = c.voronoi(cells, f"cr{salt}", min_dist=3.0)
    facet = np.clip(-(vo["dx"] * 0.7 + vo["dy"]) / 4 + 0.5, 0, 1)
    tone = c.rng(f"crt{salt}").uniform(-0.18, 0.18, len(vo["points"])).astype(np.float32)
    v = facet * 0.6 + 0.2 + tone[vo["id"]] + (c.texel_noise(f"crg{salt}") - 0.5) * 0.2
    col = ctx.palette(p[1:], np.clip(v, 0, 1))
    edge = (vo["f2"] - vo["f1"]) < 0.5
    col = np.where(edge[..., None], p[0], col)
    return Tex(ctx, col, height=np.where(edge, 0.25, 0.45 + facet * 0.3), smooth=0.55, f0=0.05,
               porosity=0.2)


def sulfur_base(ctx):
    t = crystalline(ctx, SULFUR, "s")
    speckle(ctx.sub("block/sulfur"), t, pal("f8f2b0")[0], 0.05, "bloom", height=0.6, size=2, smooth=0.1)
    return t


@texture("block/sulfur")
def sulfur(ctx):
    return sulfur_base(ctx)


@texture("block/potent_sulfur")
def potent_sulfur(ctx):
    t = crystalline(ctx, POTENT, "p", cells=8)
    return ore_clusters(ctx, t, pal("a8b01c", "e8f040", "fbff8a", "ffffd8"), salt="pot", count=6,
                        size=(2, 5), min_dist=5, smooth=0.8, glow=0.45, rim=0.7)


@texture("block/polished_sulfur")
def polished_sulfur(ctx):
    return polished(ctx, SULFUR, salt="psu", flecks=SULFUR[-1], fleck_density=0.05, smooth=0.5)


def sulfur_brick_tex(ctx, p, salt):
    fill = mottled(ctx.sub(f"sbf{salt}"), p[1:], cell=4, contrast=0.5, salt=f"sbf{salt}", smooth=0.4)
    rects = [(x, 0, 6, 4) for x in (0, 6)] + [(12, 0, 4, 4)] + [(x, 4, 6, 4) for x in (3, 9)] + [(15, 4, 4, 4)] + \
        [(x, 8, 6, 4) for x in (0, 6)] + [(12, 8, 4, 4)] + [(x, 12, 6, 4) for x in (3, 9)] + [(15, 12, 4, 4)]
    t, _, _ = blocks(ctx, rects, fill, p[0] * 0.75, salt=salt, lit=1.12, dark=0.84)
    return t


@texture("block/sulfur_bricks")
def sulfur_bricks(ctx):
    return sulfur_brick_tex(ctx, SULFUR, "sb")


def chiseled(ctx, p, salt, motif):
    t = polished(ctx, p, salt=salt, smooth=0.45)
    frame(ctx, t, 2, 2, 14, 14, p[0], p[-1])
    if motif == "hex":
        dx, dy = np.abs(ctx.x - 8), np.abs(ctx.y - 8)
        hexd = np.maximum(dx * 0.87 + dy * 0.5, dy)
        carve(ctx, t, ((hexd < 4.6) & (hexd >= 3.4)).astype(np.float32))
        emboss(ctx, t, (hexd < 1.6).astype(np.float32))
    else:
        d = np.abs(ctx.x - 8) + np.abs(ctx.y - 8)
        carve(ctx, t, ((d < 5.2) & (d >= 4.0)).astype(np.float32))
        carve(ctx, t, ((np.abs(ctx.x - 8) < 0.6) | (np.abs(ctx.y - 8) < 0.6)).astype(np.float32) * (d < 3))
    return t


@texture("block/chiseled_sulfur")
def chiseled_sulfur(ctx):
    return chiseled(ctx, SULFUR, "csu", "hex")


# ---------------------------------------------------------------- cinnabar

def cinnabar_base(ctx):
    c = ctx.sub("block/cinnabar")
    n = c.noise(5, 3, 0.55, salt="cin")
    red = ctx.palette(CINNABAR[1:], n * 0.65 + c.texel_noise("cing") * 0.35)
    mat = ctx.palette(MATRIX, c.texel_noise("cinm"))
    m = c.noise(4, 2, 0.5, salt="cinx") < 0.33
    col = np.where(m[..., None], mat, red)
    t = Tex(ctx, col, height=np.where(m, 0.4, 0.55 + n * 0.15), smooth=np.where(m, 0.15, 0.5), f0=0.06,
            porosity=np.where(m, 0.3, 0.05))
    # crystal glints
    speckle(c, t, CINNABAR[-1] * 1.1, 0.04, "cgl", height=0.7, smooth=0.85)
    return t


@texture("block/cinnabar")
def cinnabar(ctx):
    return cinnabar_base(ctx)


@texture("block/polished_cinnabar")
def polished_cinnabar(ctx):
    return polished(ctx, CINNABAR, salt="pci", flecks=MATRIX[2], fleck_density=0.04, smooth=0.55)


@texture("block/cinnabar_bricks")
def cinnabar_bricks(ctx):
    fill = mottled(ctx.sub("cbf"), CINNABAR[1:], cell=4, contrast=0.5, salt="cbf", smooth=0.45)
    t, _, _ = blocks(ctx, bond(4, 4, 8, offset=4), fill, MATRIX[0], salt="cb", lit=1.12, dark=0.84)
    return t


@texture("block/chiseled_cinnabar")
def chiseled_cinnabar(ctx):
    return chiseled(ctx, CINNABAR, "cci", "diamond")


# ---------------------------------------------------------------- sulfur spikes

def sulfur_spike(ctx, piece, up):
    t = spike_tex(ctx, piece, up, SULFUR, salt="sspk", smooth=0.6, f0=0.05, ridges=False)
    # crystal facet line down the middle
    ridge = (np.abs(ctx.x - 7.5) < 0.5) & (t.alpha > 0.5)
    t.color = np.where(ridge[..., None], SULFUR[-1], t.color)
    return t


for _dir in ("down", "up"):
    for _piece in ("base", "frustum", "middle", "tip", "tip_merge"):
        register(f"block/sulfur_spike_{_dir}_{_piece}",
                 (lambda piece, up: lambda ctx: sulfur_spike(ctx, piece, up))(_piece, _dir == "up"))
