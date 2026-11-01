"""Campfire logs, creaking heart, and the 32x32 sign / hanging sign / shelf textures.

The 32x32 sign, hanging sign and shelf sheets are UV-mapped by their block models.
Without a verified UV layout they are filled edge to edge with a surface that reads
well wherever a face samples it (board grain for signs and shelves, stripped wood for
hanging signs)."""
import math

import numpy as np

from ...engine import pal
from ...registry import register
from .wood import WOODS, log_tex
from .wood_kit import Canvas, board_field, end_grain_rings, fiber_grain

CHAR = pal("120e0c", "1e1814", "2a221c", "362c24", "443830")
EMBER = pal("7a1e06", "c2410c", "f07818", "ffb040", "ffe08a")
SOUL = pal("06404a", "0c7a86", "18b8c4", "50e4ea", "b0fcff")


def campfire(ctx, lit, soul=False):
    c = ctx
    bark = WOODS["oak"]["bark"]
    rings = WOODS["oak"]["stripped"]
    strip = np.floor(c.y / 4)
    v_in = c.y - strip * 4
    n = c.noise(4, 2, salt="cfn", stretch=(4, 1))
    g = c.texel_noise("cfg")
    v = 0.5 + (n - 0.5) * 0.5 + (g - 0.5) * 0.25 + np.where(v_in < 1, 0.2, np.where(v_in >= 3, -0.2, 0))
    cv = Canvas(c, c.palette(bark[1:], np.clip(v, 0, 1)), height=0.6 - np.abs(v_in - 1.5) * 0.08,
                smooth=0.08, porosity=0.35)
    rng = c.rng("cffur")
    fur = np.zeros((c.H, c.W), bool)
    for _ in range(9):
        x, y = int(rng.integers(0, 14)), int(rng.integers(0, 3)) * 4 + int(rng.integers(1, 3))
        fur |= c.rect(x, y, x + int(rng.integers(2, 5)), y + 1) > 0
    logs = c.y < 12
    cv.put(fur & logs, color=bark[0], height=0.2)
    # end grain squares in the last row
    ends = c.y >= 12
    ex, ey = c.x % 4, c.y - 12
    d = np.maximum(np.abs(ex - 2), np.abs(ey - 2))
    ring = np.where((d < 0.9)[..., None], rings[0] * 0.8, np.where((d < 1.5)[..., None], rings[2], rings[1]))
    ring = np.where((d >= 1.5)[..., None], c.palette(bark[1:4], g), ring)
    cv.put(ends, color=ring, height=np.where(d < 1.5, 0.55, 0.65))
    if not lit:
        return cv.tex(wrap=False)
    p = SOUL if soul else EMBER
    cv.put(logs, color=c.palette(CHAR, np.clip(v, 0, 1)))
    cv.put(ends & (d >= 1.5), color=c.palette(CHAR, g))
    t = c.frame / max(1, c.frames)
    flick = c.noise(3, 2, salt="flk", stretch=(2, 1))
    b = 0.5 + 0.5 * np.sin(2 * math.pi * (t + flick * 1.5))
    hot = (fur | (c.texel_noise("hotspots", soft=False) > 0.86)) & logs & (v_in >= 1)
    hot |= (np.floor(c.y) % 4 == 3) & (flick > 0.55) & logs
    cv.put(hot, color=c.palette(p, np.clip(0.25 + b * 0.75, 0, 1)), emissive=0.4 + 0.6 * b, height=0.3)
    core = ends & (d < 1.5)
    cv.put(core, color=c.palette(p, np.clip(0.4 + b * 0.6 - d * 0.15, 0, 1)), emissive=0.5 + 0.5 * b)
    return cv.tex(wrap=False)


def creaking(ctx, state, top):
    c = ctx
    if top:
        spec = WOODS["pale_oak"]
        st = spec["stripped"]
        cv = end_grain_rings(c, np.stack([st[0] * 0.86, st[2]]), spec["bark"][1:5], salt="creak")
        core = c.circle(8, 8, 3.2) > 0
        inner = c.circle(8, 8, 1.8) > 0
    else:
        t = log_tex(c.sub("block/pale_oak_log"), "pale_oak")
        cv = Canvas(c, t.color, height=t.height, smooth=0.08, porosity=0.35)
        core = c.polygon([(8, 1.5), (11.2, 6), (11.2, 10), (8, 14.5), (4.8, 10), (4.8, 6)]) > 0
        inner = c.polygon([(8, 4), (9.8, 7), (9.8, 9), (8, 12), (6.2, 9), (6.2, 7)]) > 0
    rim = core & ~inner
    cv.put(rim, color=pal("2a2422")[0], height=0.2)
    cv.put(rim & (c.edge(core.astype(np.float32), 1, "br") > 0), color=pal("6a625c")[0])
    if state == "awake":
        p, em = pal("8a2a06", "d0560e", "ff8a1e", "ffc04a", "ffe9a0"), 1.0
    elif state == "dormant":
        p, em = pal("4a2410", "6e3a18", "8a4e22", "a0622c", "b8783a"), 0.25
    else:
        p, em = pal("1c1816", "2a2420", "38302a", "463c34", "52473e"), 0.0
    d = np.hypot(c.x - 8, (c.y - 8) * (0.55 if not top else 1))
    col = c.palette(p, np.clip(1 - d / 3.2 + (c.texel_noise("ch") - 0.5) * 0.2, 0, 1))
    cv.put(inner, color=col, height=0.35, emissive=em * np.clip(1.1 - d / 3.5, 0.3, 1))
    # crack veins running out of the heart
    if state != "inactive":
        rng = c.rng("creakveins")
        for _ in range(4):
            x0, y0 = (8, rng.uniform(4, 12)) if not top else (8 + rng.uniform(-2, 2), 8 + rng.uniform(-2, 2))
            ang = rng.uniform(0, 2 * math.pi)
            seg = c.segment(x0, y0, x0 + math.cos(ang) * 6, y0 + math.sin(ang) * 6, 0.9) > 0
            seg &= ~core
            cv.put(seg, color=p[2] if state == "awake" else p[1], emissive=em * 0.5, height=0.3)
    return cv.tex(wrap=not top)


def sign_sheet(ctx, w, hanging):
    c = ctx
    spec = WOODS[w]
    if w == "bamboo" and not hanging:
        from .wood_bamboo import bamboo_planks
        return bamboo_planks(c)
    if hanging:
        cv = fiber_grain(c, spec["stripped"], salt=f"hs{w}", vertical=False)
    else:
        cv = board_field(c, spec["planks"], boards=4, salt=f"sign{w}", seams=False, joints=False, knots=0,
                         straight=0.3)
    return cv.tex(wrap=True)


def shelf_sheet(ctx, w):
    c = ctx
    spec = WOODS[w]
    cv = board_field(c, spec["planks"], boards=8, salt=f"shelf{w}", knots=0, straight=0.4)
    return cv.tex(wrap=True)


register("block/campfire_log", lambda c: campfire(c, False))
register("block/campfire_log_lit", lambda c: campfire(c, True), frametime=20, interpolate=True)
register("block/soul_campfire_log_lit", lambda c: campfire(c, True, True), frametime=20, interpolate=True)
for _st, _suf in (("inactive", ""), ("awake", "_awake"), ("dormant", "_dormant")):
    register(f"block/creaking_heart{_suf}", lambda c, s=_st: creaking(c, s, False))
    register(f"block/creaking_heart_top{_suf}", lambda c, s=_st: creaking(c, s, True))
for _w in ("oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry", "pale_oak", "poplar",
           "bamboo", "crimson", "warped"):
    register(f"block/{_w}_sign", lambda c, w=_w: sign_sheet(c, w, False))
    register(f"block/{_w}_hanging_sign", lambda c, w=_w: sign_sheet(c, w, True))
    register(f"block/{_w}_shelf", lambda c, w=_w: shelf_sheet(c, w))
