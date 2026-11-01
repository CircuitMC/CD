"""Coral (plants, fans, blocks; alive and dead), kelp, seagrass, sea pickle, dried kelp, frogspawn."""
import math

import numpy as np

from ...engine import Tex, hexc, pal
from ...registry import register
from .plants_common import (Canvas, curve, desat, dots, ellipse, leaf, phase, px, radial, shift, stalk,
                            sway_ctx, union, vgrad)

CORALS = {
    "tube": pal("0c2470", "143494", "1e4ab8", "2e62d2", "4480e6", "64a0f4"),
    "brain": pal("761c4a", "9c2862", "be387c", "d65496", "e876ae", "f49ec8"),
    "bubble": pal("520c64", "721488", "9220a8", "ac38c0", "c25ad2", "d886e4"),
    "fire": pal("640a0e", "8a1216", "ae1c1c", "ca3028", "de4a38", "ee6e4e"),
    "horn": pal("74540a", "9a740e", "be9416", "d8ae24", "eac83c", "f6de6c"),
}
DEAD_TONE = {"tube": (0.5, 0.5, 0.52), "brain": (0.52, 0.5, 0.5), "bubble": (0.51, 0.49, 0.52),
             "fire": (0.53, 0.5, 0.48), "horn": (0.52, 0.51, 0.47)}


def coral_pal(kind, dead):
    p = CORALS[kind]
    if dead:
        return desat(shift(p, 0.12), 0.92, DEAD_TONE[kind], 0.9)
    return p


# ---------------------------------------------------------------- coral plants (cross)

def branches(ctx, rng, x, y, ang, length, width, depth, spread, out, tips):
    x2, y2 = x + math.cos(ang) * length, y + math.sin(ang) * length
    out.append(ctx.segment(x, y, x2, y2, width))
    if depth == 0:
        tips.append((x2, y2, ang))
        return
    for s in (-1, 1):
        branches(ctx, rng, x2, y2, ang + s * spread * rng.uniform(0.7, 1.2), length * rng.uniform(0.6, 0.8),
                 max(1.0, width * 0.8), depth - 1, spread, out, tips)


def coral_plant(ctx, kind, dead):
    p = coral_pal(kind, dead)
    rng = ctx.rng("cp" + kind)
    c = Canvas(ctx)
    kw = dict(sss=0.4 if not dead else 0.0, smooth=0.2, porosity=0.3 if dead else 0.0)
    if kind == "tube":
        tubes = [(3.5, 8.0), (6.5, 4.0), (9.8, 2.5), (12.8, 6.5), (8.2, 9.5)]
        for i, (x, top) in enumerate(tubes):
            bend = (x - 8) * 0.15
            m = stalk(ctx, 8 + (x - 8) * 0.4, 16.6, x, top, 2.2, bend)
            c.add(m, p, outline=True, light=0.3, salt=f"t{i}", **kw)
            c.recolor(ellipse(ctx, x, top + 0.4, 0.9, 0.55), p[0])
            c.recolor(px(ctx, [(math.floor(x - 1), math.floor(top))]), p[5])
    elif kind == "brain":
        out, tips = [], []
        for a in (-2.1, -1.57, -1.0):
            branches(ctx, rng, 8, 16.5, a, 4.2, 2.0, 2, 0.5, out, tips)
        m = union(*out, *[ctx.circle(x, y, 1.3) for x, y, _ in tips])
        c.add(m, p, outline=True, light=0.3, noise=0.2, salt="br", **kw)
    elif kind == "bubble":
        out, tips = [], []
        for a in (-2.0, -1.5, -1.1):
            branches(ctx, rng, 8, 16.5, a, 4.5, 1.2, 1, 0.55, out, tips)
        c.add(union(*out), shift(p, -0.15), light=0.2, salt="bs", **kw)
        for i, (x, y, _) in enumerate(tips):
            r = 1.5 + (i % 3) * 0.35
            c.add(ctx.circle(x, y - 0.6, r), p, outline=True, light=0.45, salt=f"bb{i}", **kw)
            c.recolor(px(ctx, [(math.floor(x - r * 0.4), math.floor(y - 0.6 - r * 0.4))]), p[5])
    elif kind == "fire":
        m = ctx.zeros()
        for i, (bx, tx, ty) in enumerate(((7, 2.5, 3.5), (8, 7.5, 0.8), (9, 13.0, 3.0), (8, 4.5, 9.0),
                                          (8, 11.5, 8.0))):
            m = np.maximum(m, ctx.polygon([(bx - 1.6, 16.5), (tx, ty), (bx + 1.6, 16.5)]))
            for k in (0.35, 0.6):
                sx, sy = bx + (tx - bx) * k, 16.5 + (ty - 16.5) * k
                s = 1 if i % 2 else -1
                m = np.maximum(m, ctx.polygon([(sx - 0.7, sy + 0.8), (sx + s * 2.6, sy - 2.2), (sx + 0.7, sy - 0.4)]))
        c.add(m, p, outline=True, light=0.3, shade=vgrad(ctx, 1, 16, 0.12, -0.12), salt="fi", **kw)
    else:  # horn: flattened antler forks
        out, tips = [], []
        for a in (-2.2, -1.55, -0.95):
            branches(ctx, rng, 8, 16.5, a, 4.8, 2.2, 2, 0.6, out, tips)
        m = union(*out, *[leaf(ctx, (x, y), (x + math.cos(a) * 1.6, y + math.sin(a) * 1.6), 1.6) for x, y, a in tips])
        c.add(m, p, outline=True, light=0.3, salt="ho", **kw)
    return c.done()


# ---------------------------------------------------------------- coral fans

def coral_fan(ctx, kind, dead):
    p = coral_pal(kind, dead)
    c = Canvas(ctx)
    kw = dict(sss=0.4 if not dead else 0.0, smooth=0.2, porosity=0.3 if dead else 0.0)
    pts = [(7.0, 16.5)]
    for th in np.linspace(-0.9, 0.9, 41):
        R = 9.5 + 3.5 * math.cos(th * 1.4) ** 2
        if kind == "brain":
            R += abs(math.sin(th * 6)) * 1.4 - 0.8
        elif kind == "fire":
            R += (abs(((th * 9 / math.pi) % 1) - 0.5) * 2) ** 2 * 3 - 1.5
        elif kind == "horn":
            R += (1.6 if math.cos(th * 11) > 0.2 else -0.6)
        elif kind == "tube":
            R += math.cos(th * 8) * 0.7
        pts.append((8 + math.sin(th) * R, 16.2 - math.cos(th) * R))
    pts.append((9.0, 16.5))
    m = ctx.polygon(pts)
    dx, dy = ctx.x - 8, ctx.y - 16.2
    d, up = np.hypot(dx, dy), np.arctan2(dx, -dy)
    ribs = (np.abs(np.sin(up * 7)) < 0.16) & (d > 1.5) & (d < 10.5)
    c.add(m, p, outline=True, light=0.25, shade=-np.clip(1 - d / 11, 0, 1) * 0.18, salt="fan" + kind, **kw)
    c.recolor(ribs.astype(np.float32), p[2])
    if kind == "bubble":
        for i, th in enumerate(np.linspace(-0.8, 0.8, 5)):
            R = 9.5 + 3.5 * math.cos(th * 1.4) ** 2
            x, y = 8 + math.sin(th) * R, 16.2 - math.cos(th) * R
            c.add(ctx.circle(x, y, 1.3), p, outline=True, light=0.45, salt=f"fb{i}", **kw)
    if kind == "tube":
        holes = (np.abs(np.sin(up * 5.5 + 0.28)) < 0.2) & (np.abs(np.sin(d * 1.1)) < 0.25) & (d > 2)
        c.recolor(holes.astype(np.float32) * m, p[1])
    return c.done()


# ---------------------------------------------------------------- coral blocks (tiling)

def coral_block(ctx, kind, dead):
    p = coral_pal(kind, dead)
    g = ctx.texel_noise("cb" + kind)
    n = ctx.noise(8, 2, 0.5, salt="cb" + kind)
    if kind == "tube":
        vo = ctx.voronoi(12, "tubes", min_dist=3.4)
        f1 = vo["f1"]
        hole = f1 < 1.0
        rim = (f1 >= 1.0) & (f1 < 1.6)
        v = 0.45 + n * 0.25 + (g - 0.5) * 0.2 - np.clip((vo["f2"] - vo["f1"]) < 0.6, 0, 1) * 0.2
        v = np.where(rim, 0.85 + (vo["dy"] > 0) * -0.25, v)
        v = np.where(hole, 0.05 + (vo["dy"] < 0) * 0.1, v)
        h = np.where(hole, 0.1, np.where(rim, 0.8, 0.55))
    elif kind == "brain":
        w = ctx.noise(6, 2, 0.3, salt="brainw", detail=False)
        bands = np.abs(np.sin(w * 8 + ctx.noise(5, 1, salt="bw2", detail=False) * 1.5))
        groove = bands < 0.22
        v = 0.3 + bands * 0.5 + (g - 0.5) * 0.08
        v = np.where(groove, 0.08, v)
        h = np.where(groove, 0.15, 0.4 + bands * 0.4)
    elif kind == "bubble":
        vo = ctx.voronoi(14, "bubbles", min_dist=2.6)
        r = 1.0 + (ctx.rng("bsz").random(len(vo["points"]))[vo["id"]]) * 0.8
        inside = vo["f1"] < r
        shade = -(vo["dx"] + vo["dy"]) / r
        v = np.where(inside, 0.55 + shade * 0.22, 0.2 + n * 0.15 + (g - 0.5) * 0.15)
        v = np.where(inside & (vo["f1"] > r - 0.6), v - 0.15, v)
        h = np.where(inside, 0.8 - vo["f1"] / r * 0.3, 0.3)
    elif kind == "fire":
        vo = ctx.voronoi(10, "fire", min_dist=3)
        ridge = vo["f2"] - vo["f1"]
        spike = np.abs(np.sin(np.arctan2(vo["dy"], vo["dx"]) * 3)) * np.clip(vo["f1"] / 2.5, 0, 1)
        v = 0.3 + np.clip(ridge / 2.5, 0, 1) * 0.4 + spike * 0.2 + (g - 0.5) * 0.2
        v = np.where(ridge < 0.5, 0.06, v)
        h = 0.3 + np.clip(ridge / 2.5, 0, 1) * 0.5
    else:  # horn: porous
        pits = (ctx.noise(2, 1, salt="hpit") > 0.68) & (g > 0.3)
        v = 0.4 + n * 0.35 + (g - 0.5) * 0.25
        v = np.where(pits, 0.08, v)
        v = np.where(~pits & np.roll(pits, -ctx.s, 0), v - 0.2, v)
        h = np.where(pits, 0.15, 0.45 + n * 0.3)
    return Tex(ctx, ctx.palette(p, np.clip(v, 0, 1)), height=h, smooth=0.2 if not dead else 0.08,
               porosity=0.4 if dead else 0.2, sss=0.0 if dead else 0.2)


for _kind in CORALS:
    for _dead in (False, True):
        _pre = "dead_" if _dead else ""
        register(f"block/{_pre}{_kind}_coral", lambda ctx, k=_kind, d=_dead: coral_plant(ctx, k, d))
        register(f"block/{_pre}{_kind}_coral_fan", lambda ctx, k=_kind, d=_dead: coral_fan(ctx, k, d))
        register(f"block/{_pre}{_kind}_coral_block", lambda ctx, k=_kind, d=_dead: coral_block(ctx, k, d))


# ---------------------------------------------------------------- kelp & seagrass (animated)

KELP = pal("2a4a10", "38601a", "487822", "5a902a", "6ea634", "86bc42")
SEAGRASS = pal("1c4a14", "26601a", "327822", "40902a", "52a634", "6abc44")


def kelp_draw(ctx, tip):
    ph = phase(ctx)
    sw = sway_ctx(ctx, lambda y: np.sin(ph + y / 16 * 2 * math.pi) * 0.9 + np.sin(ph * 2 + y / 8 * 2 * math.pi) * 0.3)
    c = Canvas(sw)
    stem_pts = [(7.8 + math.sin(k / 8 * 2 * math.pi) * 0.6, k * 2 - 0.5) for k in range(10)]
    top = 4 if tip else -1
    pts = [(x, y) for x, y in stem_pts if y >= top]
    c.add(curve(sw, pts, 1.8), shift(KELP, -0.15), light=0.2, salt="ks")
    lm = sw.zeros()
    bladders = sw.zeros()
    spots = ((14, -1), (11, 1), (8, -1), (5, 1), (2, -1), (-1, 1), (17, 1)) if not tip else ((14, -1), (11, 1), (8.5, -1))
    for y, s in spots:
        bx = 7.8 + math.sin(y / 8 * 2 * math.pi) * 0.6
        L = 4.2
        lm = np.maximum(lm, leaf(sw, (bx, y), (bx + s * L, y - 4.0), 3.2, bend=-s * 0.7, fat=0.4))
        bladders = np.maximum(bladders, sw.circle(bx + s * 0.9, y + 0.6, 0.85))
    if tip:
        lm = np.maximum(lm, leaf(sw, (7.8, 6.0), (8.6, 0.2), 2.6, bend=0.4))
    c.add(lm, KELP, light=0.3, noise=0.18, salt="kl")
    c.add(bladders, shift(KELP, 0.15), outline=True, light=0.45, salt="kb")
    t = c.done()
    t.ctx = ctx
    return t


register("block/kelp", lambda ctx: kelp_draw(ctx, True))
register("block/kelp_plant", lambda ctx: kelp_draw(ctx, False))


def seagrass_draw(ctx, part):
    ph = phase(ctx)
    base = {"short": 16.0, "bottom": 32.0, "top": 32.0}[part]
    yoff = {"short": 0, "bottom": 16, "top": 0}[part]  # top sits above bottom: shared 32-tall field

    def amount(y):
        yw = y + yoff
        hgt = np.clip((base - yw) / base, 0, 1)
        return np.sin(ph + yw * 0.2) * (0.3 + hgt * 1.2)
    sw = sway_ctx(ctx, amount)
    c = Canvas(sw)
    rng = ctx.rng("sea" + part)
    m = sw.zeros()
    if part == "short":
        blades = [(3, 4.5, 2.0), (6, 1.5, 2.0), (9, 3.0, 2.2), (12.5, 5.5, 2.0), (7.5, 8, 1.8)]
        for x, top, w in blades:
            m = np.maximum(m, ribbon(sw, x, 16.6, top, w, rng.uniform(-1, 1)))
    elif part == "bottom":
        for x in (3.0, 7.0, 11.0, 14.0):
            m = np.maximum(m, ribbon(sw, x, 16.6, -0.6, 2.2, 0.0, taper=False))
        for x, top in ((5.0, 6.0), (12.5, 9.0)):
            m = np.maximum(m, ribbon(sw, x, 16.6, top, 1.8, rng.uniform(-1, 1)))
    else:
        for x, top in ((3.0, 4.0), (7.0, 1.0), (11.0, 3.0), (14.0, 8.0)):
            m = np.maximum(m, ribbon(sw, x, 16.6, top, 2.2, rng.uniform(-1, 1)))
    c.add(m, SEAGRASS, light=0.25, noise=0.2, shade=vgrad(ctx, 0, 16, 0.1, -0.12), sss=0.6, salt="sg")
    t = c.done()
    t.ctx = ctx
    return t


def ribbon(ctx, x, y0, top, width, bend, taper=True):
    pts = [(x + bend * math.sin(t * math.pi), y0 + (top - y0) * t) for t in np.linspace(0, 1, 9)]
    if taper:
        return curve(ctx, pts, width, 0.9)
    return curve(ctx, pts, width)


register("block/seagrass", lambda ctx: seagrass_draw(ctx, "short"))
register("block/tall_seagrass_bottom", lambda ctx: seagrass_draw(ctx, "bottom"))
register("block/tall_seagrass_top", lambda ctx: seagrass_draw(ctx, "top"))


# ---------------------------------------------------------------- sea pickle

PICKLE = pal("2a3a10", "3c5016", "50681e", "66822a", "7e9a36", "98b246")


def sea_pickle(ctx):
    """Skin over the upper part (body/top boxes sample it), a small tuft at the bottom."""
    n = ctx.texel_noise("pick")
    v = 0.45 + (n - 0.5) * 0.35 + (ctx.noise(3, 1, salt="pk") - 0.5) * 0.25
    spots = (ctx.texel_noise("pks", soft=True) > 0.82)
    v = np.where(spots, 0.9, v)
    t = Tex(ctx, ctx.palette(PICKLE, np.clip(v, 0, 1)), height=0.5 + spots * 0.2, smooth=0.5, sss=0.5,
            wrap=False)
    top = ctx.rect(0, 0, 16, 5) > 0
    t.emissive = np.where(top & spots, 0.6, 0.0).astype(np.float32)
    t.color[top & spots] = hexc("d8f080")
    tuft = ctx.rect(0, 11, 16, 16) > 0
    c = Canvas(ctx)
    c.add(union(leaf(ctx, (8, 16.5), (5.5, 11.2), 1.6), leaf(ctx, (8, 16.5), (10.5, 11.2), 1.6),
                ctx.rect(7.5, 11, 8.5, 16)), PICKLE, salt="tuft")
    tf = c.done()
    for attr in ("color", "alpha", "height", "emissive", "sss"):
        a, b = getattr(t, attr), getattr(tf, attr)
        m = tuft if a.ndim == 2 else tuft[..., None]
        setattr(t, attr, np.where(m, b, a).astype(np.float32))
    return t


register("block/sea_pickle", sea_pickle)


# ---------------------------------------------------------------- dried kelp block

DRIED = pal("1a1e10", "232a14", "2e3618", "3a421e", "464e24", "545c2c")


def dried_kelp_end(ctx):
    d, a = radial(ctx, 8, 8)
    spiral = np.sin(d * 2.1 - a * 1.0)
    v = 0.45 + spiral * 0.25 + (ctx.texel_noise("dke") - 0.5) * 0.25
    sq = np.maximum(np.abs(ctx.x - 8), np.abs(ctx.y - 8))
    v = v - (sq > 7) * 0.25
    return Tex(ctx, ctx.palette(DRIED, np.clip(v, 0, 1)), height=0.45 + spiral * 0.15, smooth=0.15, porosity=0.5,
               wrap=False)


def dried_kelp_side(ctx):
    wav = ctx.y + np.sin(ctx.x * 0.8) * 0.6 + (ctx.noise(4, 1, salt="dks") - 0.5) * 2
    layer = (wav % 3) / 3
    v = 0.3 + layer * 0.45 + (ctx.texel_noise("dks") - 0.5) * 0.2
    band = (ctx.ty == 3) | (ctx.ty == 12)
    color = ctx.palette(DRIED, np.clip(v, 0, 1))
    color = np.where(band[..., None], ctx.palette(pal("4a3a20", "5e4a2a", "74603a"), ctx.texel_noise("bd")), color)
    return Tex(ctx, color, height=0.4 + layer * 0.2 + band * 0.2, smooth=0.15, porosity=0.5)


register("block/dried_kelp_top", dried_kelp_end)
register("block/dried_kelp_bottom", dried_kelp_end)
register("block/dried_kelp_side", dried_kelp_side)


# ---------------------------------------------------------------- frogspawn

def frogspawn(ctx):
    rng = ctx.rng("spawn")
    pts = []
    for _ in range(400):
        if len(pts) >= 22:
            break
        x, y = rng.uniform(2, 14), rng.uniform(2, 14)
        if math.hypot(x - 8, y - 8) < 6.5 and all(math.hypot(x - a, y - b) > 2.1 for a, b in pts):
            pts.append((x, y))
    c = Canvas(ctx)
    jelly = union(*[ctx.circle(x, y, 1.25) for x, y in pts])
    c.add(jelly, pal("4e5e5c", "667876", "7e9290", "96aaa6"), light=0.3, smooth=0.8, sss=0.5, salt="jelly")
    c.add(px(ctx, [(math.floor(x), math.floor(y)) for x, y in pts]), pal("141614", "222622", "323632"), smooth=0.7,
          salt="egg", sss=0.0)
    return c.done()


register("block/frogspawn", frogspawn)
