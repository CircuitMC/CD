"""Animated fluids and flames: water, lava, fire, soul fire, campfire fire, nether portal.

All animations loop seamlessly: motion is either a translation by whole tile
periods over the loop (tileable noise wraps exactly) or a periodic "churn"
where every point orbits a small circle with a spatially varying phase.

fire_1 / water_flow / nether_portal register explicit size and frame counts
(their vanilla mcmeta has an empty `"animation": {}` section, which older
build.py versions treated as "not animated").
"""
import math

import numpy as np

from ...engine import Tex, pal
from ...registry import register
from .color_common import fbm, loop_phase


def churn(ctx, amp, salt, cell=8, speed=1):
    """Periodic domain warp: each point circles with radius ~amp texels."""
    ph = 2 * math.pi * loop_phase(ctx) * speed
    p1 = ctx.noise(cell, 1, 0.5, salt=f"{salt}p1", detail=False) * 2 * math.pi * 0.7
    a1 = 0.5 + ctx.noise(cell, 2, 0.5, salt=f"{salt}a1", detail=False)
    return ctx.x + np.cos(ph + p1) * amp * a1, ctx.y + np.sin(ph + p1) * amp * a1


def moving(ctx, x, y, vx, vy):
    """Translate coordinates by whole tiles over the loop (vx, vy integers)."""
    t = loop_phase(ctx)
    return x - vx * ctx.w * t, y - vy * ctx.h * t


# ------------------------------------------------------------------ water (grayscale, biome tinted)

WATER = pal("9a9a9a", "aeaeae", "bebebe", "cecece", "e0e0e0", "f0f0f0")  # grayscale: biome water color tints it


def water(ctx, flow=False, salt="water"):
    """Gentle swell with thin bright ripple crests (contour lines of a drifting field)."""
    if flow:
        x, y = churn(ctx, 0.6, f"{salt}c", cell=16)
        x1, y1 = moving(ctx, x, y, 0, 1)
        a = fbm(ctx, x1, y1, 16, 3, f"{salt}a", stretch=(0.6, 1.6), persistence=0.45)
        x2, y2 = moving(ctx, x, y, 0, 2)
        b = fbm(ctx, x2, y2, 8, 2, f"{salt}b", stretch=(1, 2))
    else:
        x, y = churn(ctx, 1.0, f"{salt}c", cell=16)
        x1, y1 = moving(ctx, x, y, 1, 0)
        x2, y2 = moving(ctx, x, y, 0, -1)
        a = fbm(ctx, x1, y1, 8, 2, f"{salt}a", persistence=0.4)
        b = fbm(ctx, x2, y2, 8, 2, f"{salt}b", persistence=0.4)
    # Caustic web: ridges (mid-level lines) of two drifting fields, brightest where they cross.
    r1 = np.clip(1 - np.abs(a - 0.5) * 2 * 3.2, 0, 1)
    r2 = np.clip(1 - np.abs(b - 0.5) * 2 * 3.2, 0, 1)
    web = np.maximum(r1, r2) ** 2 + r1 * r2 * 0.6
    swell = 0.5 + (a + b - 1) * 1.2
    v = np.clip(0.3 + swell * 0.25 + web * 0.5, 0, 1)
    color = ctx.palette(WATER, v)
    alpha = 0.66 + v * 0.12
    if ctx.pixel_art:
        alpha = np.round(alpha * 20) / 20
    height = 0.45 + v * 0.1
    return Tex(ctx, color, alpha=alpha, height=height, smooth=0.95, f0=0.02, porosity=0.0,
               normal_strength=0.5, grain=0)


def water_overlay(ctx):
    t = water(ctx.sub("block/water_still"), salt="water")
    # Slightly framed so glass-adjacent water reads as a surface
    n = ctx.noise(4, 2, 0.5, salt="ov")
    t.color = ctx.palette(WATER, np.clip(0.35 + n * 0.4, 0, 1))
    t.alpha = ctx.full(0.62) + n * 0.1
    return t


# ------------------------------------------------------------------ lava (emissive)

LAVA = pal("4a1206", "7d2209", "b23a0d", "d9561a", "ef7a22", "f9a434", "ffcf55", "fff19a")


def lava(ctx, flow=False, salt="lava"):
    """Bright melt with slowly churning darker crust islands and glowing seams."""
    x, y = churn(ctx, 1.4 if not flow else 0.8, f"{salt}c", cell=16)
    if flow:
        x, y = moving(ctx, x, y, 0, 1)
        st = (1, 2)
    else:
        st = (1, 1)
    crust = fbm(ctx, x, y, 8, 2, f"{salt}k", stretch=st, persistence=0.45)
    heat = fbm(ctx, x, y, 4, 2, f"{salt}h", stretch=st)
    c = 0.5 + (crust - 0.5) * (1.7 if flow else 2.4)
    heat = 0.5 + (heat - 0.5) * 1.8
    seam = np.clip(1 - np.abs(c - 0.58) * 9, 0, 1)
    v = 0.5 + (heat - 0.5) * 0.55 + seam * 0.35 - np.clip(c - 0.6, 0, 1) * 2.2 \
        + np.clip(0.42 - c, 0, 1) * 0.6
    v = np.clip(v, 0, 1)
    color = ctx.palette(LAVA, v)
    height = 0.4 + np.clip(c - 0.6, 0, 1) * 1.0 + v * 0.05
    em = np.clip(0.55 + v * 0.45, 0, 1)
    return Tex(ctx, color, height=height, smooth=0.55, f0=0.03, porosity=0.0, emissive=em,
               normal_strength=0.7, grain=0.04)


# ------------------------------------------------------------------ fire (cutout, emissive)

FIRE = pal("8e1f08", "c23a0c", "e8611a", "f78f26", "fbbb3c", "ffe27a", "fff6c6")
SOUL = pal("0b3b55", "10638a", "1694b7", "33c3d8", "7ee7ea", "c4fbf6", "f0fffd")


def wrap_edge(m, s):
    """Mask pixels whose left/right/top neighbor is outside (sides wrap, bottom never counts)."""
    out = m & ~np.roll(m, s, 1) | m & ~np.roll(m, -s, 1)
    above = np.roll(m, s, 0)
    above[:s] = True
    return out | (m & ~above)


def flames(ctx, p, salt, rise=2, tall=1.0, base_frac=0.0):
    """Rising flame tongues.

    Column heights (1D noise, ~5 tongues per block) breathe between two random
    sets; rising noise sways the tongues sideways and nibbles their edges.
    rise = tiles traveled upward per loop (integer) by the sway/flicker noise.
    """
    up = 1 - ctx.y / ctx.h                      # 0 at the bottom, 1 at the top
    ph = 2 * math.pi * loop_phase(ctx)
    x, y = moving(ctx, ctx.x, ctx.y, 0, -rise)
    sway = fbm(ctx, x, y, 8, 2, f"{salt}s", stretch=(1, 1.5))
    flick = fbm(ctx, x, y, 2, 2, f"{salt}f", stretch=(1, 2))
    xw = ctx.x + (sway - 0.5) * 3.0 * up
    w1 = 0.5 + 0.5 * math.cos(ph)
    w2 = 0.5 + 0.5 * math.cos(ph + 2 * math.pi / 3)
    w3 = 0.5 + 0.5 * math.cos(ph + 4 * math.pi / 3)
    hs = [ctx.lattice_noise(2.6, 64, f"{salt}h{k}", x=xw, y=ctx.y * 0) for k in range(3)]
    h = (hs[0] * w1 + hs[1] * w2 + hs[2] * w3) / (w1 + w2 + w3)
    h = ctx.normalize(h) if h.max() > h.min() else h
    H = (0.36 + 0.62 * h ** 1.8) * tall + (flick - 0.5) * 0.18
    rel = up / np.maximum(H, 0.05)
    mask = rel < 1.0
    if base_frac:
        mask |= up < base_frac
    if not ctx.pixel_art:
        mask = ctx.organic(mask.astype(np.float32), 0.2, salt)
    # Inner hot tongue: a narrower, shorter copy.
    inner = rel < 0.55 + (flick - 0.5) * 0.3
    v = np.clip(0.6 - rel * 0.5 + (flick - 0.5) * 0.25, 0, 1)
    v = np.where(inner, np.clip(v + 0.2 + (rel < 0.25) * 0.1, 0, 1), v)
    color = ctx.palette(p[1:], v)
    edge = wrap_edge(mask, ctx.s)
    color = np.where(edge[..., None], p[1] * 0.6 + color * 0.4, color)
    return Tex(ctx, color, alpha=mask.astype(np.float32), height=np.where(mask, 0.5, 0.0),
               smooth=0.0, emissive=np.where(mask, 1.0, 0.0), wrap=False, grain=0.03)


# ------------------------------------------------------------------ nether portal

PORTAL = pal("1d0638", "34096a", "4f1499", "6e25c4", "9348e6", "b97ff5", "e0c2ff")


def nether_portal(ctx):
    """Swirling translucent wisps: two counter-rotating fields; bright where they meet."""
    x, y = churn(ctx, 1.6, "portal", cell=16)
    ph = 2 * math.pi * loop_phase(ctx)
    a = fbm(ctx, x + 3 * math.cos(ph), y + 3 * math.sin(ph), 8, 2, "pa", persistence=0.45)
    b = fbm(ctx, x - 3 * math.sin(ph), y - 3 * math.cos(ph), 8, 2, "pb", persistence=0.45)
    filament = np.clip(1 - np.abs(a - b) * 7, 0, 1)
    glow = fbm(ctx, x, y, 16, 1, "pg")
    v = np.clip(0.28 + (glow - 0.5) * 0.6 + filament * 0.62, 0, 1)
    color = ctx.palette(PORTAL, v)
    alpha = 0.62 + v * 0.3
    if ctx.pixel_art:
        alpha = np.round(alpha * 20) / 20
    return Tex(ctx, color, alpha=alpha, height=0.5, smooth=0.9, f0=0.04, emissive=0.6 + v * 0.4,
               normal_strength=0.3, grain=0)


# ------------------------------------------------------------------ registration

register("block/water_still", lambda ctx: water(ctx), frametime=2)
register("block/water_flow", lambda ctx: water(ctx, flow=True, salt="waterf"),
         size=(32, 32), frames=32, frametime=2)
register("block/water_overlay", water_overlay)
register("block/lava_still", lambda ctx: lava(ctx), frames=40, frametime=3)
register("block/lava_flow", lambda ctx: lava(ctx, flow=True, salt="lavaf"), frames=32, frametime=3)
register("block/fire_0", lambda ctx: flames(ctx, FIRE, "fire0"), frametime=1)
register("block/fire_1", lambda ctx: flames(ctx, FIRE, "fire1", tall=0.9), size=(16, 16), frames=32,
         frametime=1)
register("block/soul_fire_0", lambda ctx: flames(ctx, SOUL, "sfire0"), frametime=1)
register("block/soul_fire_1", lambda ctx: flames(ctx, SOUL, "sfire1", tall=0.9), size=(16, 16),
         frames=32, frametime=1)
register("block/campfire_fire", lambda ctx: flames(ctx, FIRE, "camp", rise=1, tall=1.1, base_frac=0.15),
         frametime=2)
register("block/soul_campfire_fire", lambda ctx: flames(ctx, SOUL, "scamp", rise=1, tall=1.1,
                                                         base_frac=0.15), frametime=2)
register("block/nether_portal", nether_portal, size=(16, 16), frames=32, frametime=2)
