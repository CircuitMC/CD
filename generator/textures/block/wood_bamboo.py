"""Bamboo wood set: bundled stalk blocks, planks, mosaic, fences."""
import numpy as np

from ...engine import pal
from ...registry import register
from .wood import WOODS
from .wood_kit import Canvas

GREEN = WOODS["bamboo"]["bark"]
YELLOW = WOODS["bamboo"]["planks"]
STRIPPED = pal("8a7a2c", "b5a446", "c6b553", "d3c15d", "dfcd69", "e8d87a")
PITH = pal("c8b878", "dccd92", "ebe0ad")


def stalks(ctx, p, salt, widths=(4, 4, 4, 4)):
    """Vertical stalks side by side with node rings (tiles)."""
    c = ctx
    bounds = np.cumsum([0, *widths]).astype(np.float32)
    k = np.clip(np.searchsorted(bounds, c.x, side="right") - 1, 0, len(widths) - 1)
    u = c.x - bounds[k]
    wk = np.asarray(widths, np.float32)[k]
    rng = c.rng(f"stalk{salt}")
    offs = rng.integers(0, 16, len(widths))
    period = rng.integers(6, 9, len(widths))
    n = c.noise(2, 2, salt=f"sk{salt}", stretch=(1, 5))
    rel = u / wk
    v = 0.62 - np.abs(rel - 0.4) * 0.5 + (n - 0.5) * 0.25 + (c.texel_noise(f"skt{salt}") - 0.5) * 0.1
    cv = Canvas(c, c.palette(p[1:], np.clip(v, 0, 1)), height=0.75 - np.abs(rel - 0.45) * 0.4, smooth=0.45,
                porosity=0.1)
    cv.put(u < 1, mul=1.12)
    cv.put(wk - u <= 1, color=p[0], height=0.25)
    yy = (c.y + offs[k]) % 16
    pk = period[k]
    node = (np.floor(yy) % pk == 0) & (wk - u > 1)
    cv.put(node, color=p[-1], dh=0.08)
    cv.put((np.floor(yy) % pk == 1) & (wk - u > 1), mul=0.82)
    return cv


def bamboo_block(ctx, stripped):
    p = STRIPPED if stripped else GREEN
    return stalks(ctx, p, "blk", (4, 3, 5, 4)).tex(wrap=True)


def bamboo_top(ctx, stripped):
    c = ctx
    p = STRIPPED if stripped else GREEN
    cv = Canvas(c, p[0] * 0.6, height=0.1, smooth=0.3, porosity=0.2)
    for cx, cy, r in ((4, 4, 3.6), (12, 4, 3.4), (4, 12, 3.4), (12, 12, 3.6), (8, 8, 1.6), (0, 8, 1.4),
                      (8, 0, 1.4)):
        for ox in (-16, 0, 16):
            for oy in (-16, 0, 16):
                d = np.hypot(c.x - cx - ox, c.y - cy - oy)
                outer = d < r
                if not outer.any():
                    continue
                wall = outer & (d >= r - 1.1)
                lit = (c.x - cx - ox + c.y - cy - oy) < 0
                cv.put(outer, color=PITH[1], height=0.4)
                cv.put(outer & (d < r - 1.1) & (d >= r - 2.0), color=PITH[2], height=0.45)
                cv.put(wall, color=np.where(lit[..., None], p[-2], p[1]), height=0.7)
                cv.put(outer & (d < max(0.6, r - 2.6)), color=PITH[0] * 0.7, height=0.2)
    return cv.tex(wrap=True)


def bamboo_planks(ctx):
    c = ctx
    # flattened strips, 2 texels wide, two rows of 8-texel pieces with offset joints
    k = np.floor(c.x / 2)
    u = c.x - k * 2
    n = c.noise(2, 2, salt="bpl", stretch=(1, 4))
    rng = c.rng("bplanks")
    tone = rng.uniform(-0.1, 0.1, 8).astype(np.float32)[k.astype(int) % 8]
    v = 0.6 + tone + (n - 0.5) * 0.3 + (c.texel_noise("bplt") - 0.5) * 0.12
    cv = Canvas(c, c.palette(YELLOW[1:], np.clip(v, 0, 1)), height=0.55, smooth=0.4, porosity=0.15)
    cv.put(u >= 1, mul=0.9)
    cv.put((k % 4 == 3) & (u >= 1), color=YELLOW[0], height=0.15)
    offs = rng.integers(0, 16, 8)
    joint = np.floor((c.y + offs[k.astype(int) % 8]) % 8) == 0
    cv.put(joint, color=YELLOW[0], height=0.15)
    node = np.floor((c.y + offs[k.astype(int) % 8] + 4) % 8) == 0
    cv.put(node & ~joint, color=YELLOW[-1])
    return cv.tex(wrap=True)


def bamboo_mosaic(ctx):
    c = ctx
    q = (np.floor(c.x / 8) + np.floor(c.y / 8)) % 2 == 0
    lx, ly = c.x % 8, c.y % 8
    across = np.where(q, ly, lx)
    along = np.where(q, lx, ly)
    strip = np.floor(across / 2)
    au = across - strip * 2
    n = c.noise(2, 2, salt="mos")
    tone = c.rng("mos").uniform(-0.12, 0.12, 64).astype(np.float32)
    idx = (strip + np.floor(c.x / 8) * 4 + np.floor(c.y / 8) * 8).astype(int) % 64
    v = 0.58 + tone[idx] + (n - 0.5) * 0.2 + (c.texel_noise("most") - 0.5) * 0.1
    cv = Canvas(c, c.palette(YELLOW[1:], np.clip(v, 0, 1)), height=0.55, smooth=0.4, porosity=0.15)
    cv.put(au < 1, mul=1.08)
    cv.put((au >= 1) & (strip == 3), color=YELLOW[0], height=0.2)
    node = np.floor(along) == 3
    cv.put(node & (strip % 2 == 0), color=YELLOW[-1], dh=0.05)
    edge = (lx < 1) | (ly < 1)
    cv.put(edge, color=YELLOW[0] * 0.9, height=0.1)
    return cv.tex(wrap=True)


def bamboo_fence(ctx, gate):
    c = ctx
    cv = stalks(c, YELLOW, "fence" + str(gate), (4, 4, 4, 4))
    if gate:
        rope = pal("5c4a2a", "7d6638", "9c8347")
        for y0 in (3, 11):
            m = c.rect(0, y0, 16, y0 + 2) > 0
            tw = ((np.floor(c.x) + np.floor(c.y)) % 2 == 0)
            cv.put(m, color=np.where(tw[..., None], rope[2], rope[1]), height=0.8)
    return cv.tex(wrap=True)


register("block/bamboo_block", lambda c: bamboo_block(c, False))
register("block/stripped_bamboo_block", lambda c: bamboo_block(c, True))
register("block/bamboo_block_top", lambda c: bamboo_top(c, False))
register("block/stripped_bamboo_block_top", lambda c: bamboo_top(c, True))
register("block/bamboo_planks", bamboo_planks)
register("block/bamboo_mosaic", bamboo_mosaic)
register("block/bamboo_fence", lambda c: bamboo_fence(c, False))
register("block/bamboo_fence_gate", lambda c: bamboo_fence(c, True))
register("block/bamboo_fence_particle", bamboo_planks)
register("block/bamboo_fence_gate_particle", bamboo_planks)
