"""Crimson & warped stems (animated glowing veins), stripped stems, tops and planks."""
import math

import numpy as np

from ...registry import register
from .wood import WOODS
from .wood_kit import board_field, end_grain_rings, fiber_grain, plate_bark


def veins(c, salt, count=4):
    """Wavy vertical vein mask (tiles: one or two sine periods over the block height).
    Returns (mask, vein index)."""
    rng = c.rng(f"veins{salt}")
    m = np.zeros((c.H, c.W), bool)
    vid = np.zeros((c.H, c.W), np.int32)
    xs = (np.arange(count) + rng.uniform(0.1, 0.9, count)) * c.w / count
    for i, x0 in enumerate(xs):
        k = int(rng.choice([1, 2]))
        amp, ph = rng.uniform(0.8, 1.8), rng.uniform(0, 6.3)
        cx = x0 + amp * np.sin(c.y * 2 * math.pi * k / c.h + ph)
        d = np.abs(((c.x - cx + c.w / 2) % c.w) - c.w / 2)
        if c.pixel_art:
            mm = np.floor(c.x) == np.floor(cx) % c.w
        else:
            mm = d < 0.5
        # side twigs
        for _ in range(2):
            ty = rng.uniform(0, c.h)
            dirx = rng.choice([-1, 1])
            twig = c.segment(x0 + amp * math.sin(ty * 2 * math.pi * k / c.h + ph), ty,
                             x0 + amp * math.sin(ty * 2 * math.pi * k / c.h + ph) + dirx * 2, ty - 1.5, 1.0) > 0
            mm |= twig
        m |= mm
        vid = np.where(mm, i, vid)
    return m, vid


def stem(ctx, w):
    c = ctx
    spec = WOODS[w]
    cv = plate_bark(c.sub(f"block/{w}_stem_base"), spec["bark"], widths=(1, 3), seglen=(5, 12), salt=w,
                    crack=False, tone_amt=0.25)
    cv.ctx = c
    m, vid = veins(c.sub(f"block/{w}_stem_base"), w)
    ph = c.rng(f"vph{w}").uniform(0, 1, 8).astype(np.float32)
    t = c.frame / max(1, c.frames)
    b = 0.5 + 0.5 * np.cos(2 * math.pi * (c.y / c.h - t + ph[vid]))
    vcol = c.palette(spec["vein"], b)
    glow_edge = (np.roll(m, c.s, 1) | np.roll(m, -c.s, 1)) & ~m
    cv.put(glow_edge, mul=1.25)
    cv.put(m, color=vcol, height=0.45, emissive=0.15 + 0.45 * b, smooth=0.4)
    return cv.tex(wrap=True)


def stem_top(ctx, w, stripped):
    c = ctx
    spec = WOODS[w]
    st = spec["stripped"]
    rings = np.stack([st[0] * 0.8, st[2]])
    rim = st[:3] * 0.85 if stripped else spec["bark"][1:5]
    cv = end_grain_rings(c, rings, rim, salt=w)
    if not stripped:
        r = c.texel_noise("rimv", soft=False)
        edge = (c.x < 1) | (c.x >= c.w - 1) | (c.y < 1) | (c.y >= c.h - 1)
        cv.put(edge & (r > 0.8), color=spec["vein"][1], emissive=0.4)
    return cv.tex(wrap=True)


def stripped_stem(ctx, w):
    c = ctx
    spec = WOODS[w]
    cv = fiber_grain(c, spec["stripped"], salt=w)
    m, _ = veins(c, f"s{w}", 3)
    cv.put(m, mul=0.82, dh=-0.05)
    return cv.tex(wrap=True)


def nether_planks(ctx, w):
    c = ctx
    spec = WOODS[w]
    cv = board_field(c, spec["planks"], salt=w, straight=0.3)
    r = c.texel_noise("np", soft=False)
    cv.put(r > 0.965, color=spec["planks"][-1] * 1.08)
    return cv.tex(wrap=True)


for _w in ("crimson", "warped"):
    register(f"block/{_w}_stem", lambda c, w=_w: stem(c, w), frametime=10, interpolate=True)
    register(f"block/{_w}_stem_top", lambda c, w=_w: stem_top(c, w, False))
    register(f"block/stripped_{_w}_stem", lambda c, w=_w: stripped_stem(c, w))
    register(f"block/stripped_{_w}_stem_top", lambda c, w=_w: stem_top(c, w, True))
    register(f"block/{_w}_planks", lambda c, w=_w: nether_planks(c, w))
