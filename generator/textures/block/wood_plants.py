"""Saplings, azalea bush, mangrove roots (cutout sprites) and muddy mangrove roots."""
import numpy as np

from ...engine import pal
from ...registry import register
from ...sprites import compose, sprite
from .wood import COLORED_LEAVES, WOODS
from .wood_kit import Canvas, canopy

TRUNK = {
    "oak": pal("3a2a18", "5a4228", "6e5232", "84653e"),
    "spruce": pal("24170e", "3a2818", "4b3420", "5c412a"),
    "birch": pal("4a4640", "bdb8ad", "d8d4ca", "efede6"),
    "jungle": pal("33280f", "4e3e1c", "625026", "766230"),
    "acacia": pal("3a3631", "56514a", "6b665d", "807a70"),
    "dark_oak": pal("1c130a", "2f2214", "3d2d1b", "4a3823"),
    "cherry": pal("1f1418", "3a262d", "4b333b", "5c424a"),
    "pale_oak": pal("3a3532", "5b544e", "706962", "857e77"),
    "poplar": pal("4b4f45", "8d9284", "a8ad9e", "c1c5b8"),
}
FOLIAGE = {
    "oak": pal("1f3d12", "2f5a1a", "3f7322", "52892c", "68a03a"),
    "spruce": pal("142a1c", "1f3d29", "2b5035", "386343", "487552"),
    "birch": pal("2e4a16", "46691f", "5c8429", "759c35", "8fb646"),
    "jungle": pal("1c4010", "2b5e16", "3b7a1e", "4e9428", "66ab34"),
    "acacia": pal("3a4212", "56601a", "6c7a22", "84922c", "9aa83a"),
    "dark_oak": pal("10260c", "1a3a12", "254d18", "31601f", "3e7228"),
    "cherry": pal("8f3a60", "b5527e", "cc6895", "de82aa", "f0a6c5"),
    "pale_oak": pal("3e453c", "596055", "6f766a", "878d80", "a3a99c"),
    "poplar": pal("4a5a14", "687c1c", "849826", "9eb032", "b6c444"),
}


def _leafy(ctx, mask, p, salt, speck=0.25):
    t = sprite(ctx, mask, p, bevel=2.0, light=0.3, sss=0.5, smooth=0.3)
    m = mask > 0.5
    inner = m & ~(ctx.edge(mask, 1) > 0)
    r = ctx.texel_noise(f"lf{salt}", soft=False)
    t.color = np.where((inner & (r < speck))[..., None], p[1], t.color)
    t.color = np.where((inner & (r > 1 - speck * 0.6))[..., None], p[-1], t.color)
    return t


def _trunk(ctx, pts, width, p):
    m = ctx.zeros()
    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        m = np.maximum(m, ctx.segment(x1, y1, x2, y2, width))
    return m


def sapling(ctx, w):
    c = ctx
    tp, fp = TRUNK[w], FOLIAGE[w]
    blossom = None
    if w == "oak":
        tr = _trunk(c, [(8, 16), (8, 9), (6.5, 7)], 1.6, tp)
        lv = np.maximum.reduce([c.circle(5.5, 6.5, 3.2), c.circle(10.5, 5.5, 3.4), c.circle(8.5, 10, 2.8),
                                c.circle(8, 3.5, 2.5)])
    elif w == "spruce":
        tr = _trunk(c, [(8, 16), (8, 3)], 1.4, tp)
        lv = np.maximum.reduce([c.polygon([(8, 1), (11, 6), (5, 6)]), c.polygon([(8, 4), (12.5, 10), (3.5, 10)]),
                                c.polygon([(8, 7.5), (14, 14), (2, 14)])])
    elif w == "birch":
        tr = _trunk(c, [(8, 16), (8, 6), (10, 3)], 1.2, tp)
        lv = np.maximum.reduce([c.circle(x, y, r) for x, y, r in
                                ((5, 5, 2.2), (10.5, 3.5, 2.2), (11.5, 8, 2.3), (5.5, 9.5, 2.0), (8.2, 6.5, 2.0))])
    elif w == "jungle":
        tr = _trunk(c, [(8, 16), (8, 9)], 2.0, tp)
        lv = np.maximum.reduce([c.polygon([(8, 9), (2, 6), (1, 3), (5, 3)]),
                                c.polygon([(8, 9), (14, 5), (15, 2), (10, 2.5)]),
                                c.polygon([(8, 9), (6, 2), (8, 0.5), (10, 2)])])
    elif w == "acacia":
        tr = _trunk(c, [(7, 16), (7, 11), (10, 6)], 1.4, tp)
        lv = np.maximum(c.polygon([(2, 6), (5, 3), (12, 2.5), (15, 5), (13, 7), (4, 7.5)]), c.circle(10, 4.5, 2.5))
    elif w == "dark_oak":
        tr = _trunk(c, [(8, 16), (8, 9)], 2.6, tp)
        lv = np.maximum.reduce([c.circle(8, 6, 5.2), c.circle(4, 9, 3.0), c.circle(12, 9, 3.0)])
    elif w == "cherry":
        tr = _trunk(c, [(8, 16), (8, 10), (5, 6)], 1.5, tp)
        tr = np.maximum(tr, _trunk(c, [(8, 11), (11, 7)], 1.2, tp))
        lv = np.maximum.reduce([c.circle(5, 5.5, 3.0), c.circle(11, 6, 3.0), c.circle(8, 3, 2.6)])
        blossom = True
    elif w == "pale_oak":
        tr = _trunk(c, [(8, 16), (8, 8), (10, 5)], 1.6, tp)
        lv = np.maximum.reduce([c.circle(5, 6, 2.6), c.circle(11, 4.5, 2.8), c.circle(9, 8.5, 2.2),
                                c.circle(6, 2.5, 1.8)])
    else:  # poplar: tall narrow column
        tr = _trunk(c, [(8, 16), (8, 4)], 1.2, tp)
        d = ((c.x - 8) / 3.2) ** 2 + ((c.y - 7) / 6.5) ** 2
        lv = (d < 1).astype(np.float32)
    tr = (tr > 0.5) & ~(lv > 0.5)
    trunk = sprite(c, tr.astype(np.float32), tp, bevel=1.0, light=0.3)
    leaves = _leafy(c, lv, fp, w)
    out = compose(c, trunk, leaves)
    if blossom:
        r = c.texel_noise("bl", soft=False)
        m = (lv > 0.5) & (r > 0.8) & ~(c.edge(lv, 1) > 0)
        out.color = np.where(m[..., None], pal("fbe0ec")[0], out.color)
    return out


def azalea_top(ctx):
    p, kw = COLORED_LEAVES["azalea"]
    return canopy(ctx, p, salt="azaleatop", **{**kw, "holes": 0.4, "speckle": 0.02})


def azalea_side(ctx):
    p, kw = COLORED_LEAVES["azalea"]
    t = canopy(ctx, p, salt="azaleaside", **kw)
    rng = ctx.rng("azfringe")
    L = np.array([8 + rng.integers(0, 3) + (2 if rng.random() < 0.2 else 0) for _ in range(ctx.w)], np.float32)
    keep = ctx.y < L[ctx.tx % ctx.w]
    t.alpha = np.where(keep, t.alpha, 0.0)
    t.color = np.where(keep[..., None], t.color, p[0] * 0.55)
    t.wrap = False
    return t


ROOT_P = pal("2a1e16", "45332a", "5a4436", "6e5443", "826553")
MUD = pal("2c2722", "3a332d", "463e37", "524942", "5e554c")


def root_mask(c, salt, mode):
    """Tangled roots; drawn with wrap so the block tiles."""
    rng = c.rng(f"roots{salt}")
    m = c.zeros()
    n = 6 if mode == "side" else 7
    for i in range(n):
        if mode == "side":
            x0 = rng.uniform(0, 16)
            amp, ph, fq = rng.uniform(1.0, 2.5), rng.uniform(0, 6.3), float(rng.choice([1, 2])) * np.pi / 8
            ys = np.linspace(-1, 17, 10)
            pts = [(x0 + amp * np.sin(y * fq + ph), y) for y in ys]
        else:
            ang = rng.uniform(0, np.pi)
            cx, cy = rng.uniform(0, 16), rng.uniform(0, 16)
            dx, dy = np.cos(ang), np.sin(ang)
            pts = [(cx + dx * t + np.sin(t * 0.5 + i) * 1.2 * dy, cy + dy * t - np.sin(t * 0.5 + i) * 1.2 * dx)
                   for t in np.linspace(-11, 11, 10)]
        width = rng.uniform(1.3, 2.1)
        for ox in (-16, 0, 16):
            for oy in ((-16, 0, 16) if mode == "top" else (0,)):
                for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
                    m = np.maximum(m, c.segment(x1 + ox, y1 + oy, x2 + ox, y2 + oy, width))
    return m


def roots(ctx, mode, muddy=False):
    c = ctx
    m = root_mask(c, mode, mode)
    t = sprite(c, m, ROOT_P, bevel=1.0, light=0.3, porosity=0.4)
    grain = c.noise(1, 1, salt="rg", stretch=(1, 3))
    t.color = np.clip(t.color * (0.92 + grain[..., None] * 0.16), 0, 1)
    t.wrap = True
    if not muddy:
        t.color = np.where((t.alpha < 0.5)[..., None], ROOT_P[0] * 0.5, t.color)
        return t
    n = c.noise(4, 2, salt="mud")
    g = c.texel_noise("mud")
    cv = Canvas(c, c.palette(MUD, n * 0.5 + g * 0.5), height=0.35 + n * 0.1, smooth=0.35, porosity=0.9)
    shadow = (np.roll(m, c.s, 0) > 0.5) | (np.roll(m, c.s, 1) > 0.5)
    cv.put(shadow & (m < 0.5), mul=0.7)
    base = cv.tex(wrap=True)
    base.paste(t)
    base.alpha[:] = 1
    return base


for _w in TRUNK:
    register(f"block/{_w}_sapling", lambda c, w=_w: sapling(c, w))
register("block/azalea_top", azalea_top)
register("block/azalea_side", azalea_side)
register("block/mangrove_roots_side", lambda c: roots(c, "side"))
register("block/mangrove_roots_top", lambda c: roots(c, "top"))
register("block/muddy_mangrove_roots_side", lambda c: roots(c, "side", True))
register("block/muddy_mangrove_roots_top", lambda c: roots(c, "top", True))
