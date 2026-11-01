"""Shared helpers for the block_color area (dyed families, fluids, fire, overlays).

Only used by generator/textures/block/color_*.py modules.
"""
import colorsys
import math

import numpy as np

from ...engine import hexc
from .glass import DYES as GLASS_DYES

# Dye order (vanilla color order) and base colors shared with stained glass.
DYE_NAMES = ["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray",
             "light_gray", "cyan", "purple", "blue", "brown", "green", "red", "black"]
DYE = {k: hexc(GLASS_DYES[k]) for k in DYE_NAMES}


# ------------------------------------------------------------------ color math

def to_hsv(rgb):
    return np.array(colorsys.rgb_to_hsv(*[float(c) for c in rgb]), np.float32)


def from_hsv(h, s, v):
    return np.array(colorsys.hsv_to_rgb(h % 1.0, min(max(s, 0), 1), min(max(v, 0), 1)), np.float32)


def adjust(rgb, sat=1.0, val=1.0, add=0.0):
    """Scale saturation / value of an RGB color."""
    h, s, v = to_hsv(rgb)
    return np.clip(from_hsv(h, s * sat, v * val) + add, 0, 1)


def mix(a, b, t):
    return np.asarray(a, np.float32) * (1 - t) + np.asarray(b, np.float32) * t


WARM = np.array([1.0, 0.93, 0.80], np.float32)
COOL = np.array([0.20, 0.24, 0.40], np.float32)


def ramp(rgb, n=5, dark=0.70, light=1.22, hue_shift=0.12):
    """Dark -> light palette around `rgb` with cool shadows and warm highlights."""
    rgb = np.asarray(rgb, np.float32)
    out = []
    for t in np.linspace(-1, 1, n):
        if t < 0:
            c = rgb * (1 + t * (1 - dark))
            c = mix(c, COOL * float(np.mean(c)) * 1.6, hue_shift * -t)
            c = c - 0.03 * -t * (float(np.mean(rgb)) < 0.12)
        else:
            c = rgb * (1 + t * (light - 1)) + 0.05 * t
            c = mix(c, WARM * float(np.max(c)), hue_shift * t * 0.7)
        out.append(np.clip(c, 0, 1))
    return np.stack(out).astype(np.float32)


# ------------------------------------------------------------------ noise helpers

def fbm(ctx, x, y, cell, octaves=3, salt="", persistence=0.5, stretch=(1, 1), detail=True):
    """Tileable fBm sampled at arbitrary texel coordinates (x, y arrays). 0..1 (not normalized)."""
    total = np.zeros_like(x, dtype=np.float32)
    amp, amp_sum, k, c = 1.0, 0.0, 0, float(cell)
    while True:
        fine = k >= octaves
        if fine and (not detail or c * ctx.s < 2 or c < 1 / 16):
            break
        total += ctx.lattice_noise(c * stretch[0], c * stretch[1], f"{salt}:{k}", x=x, y=y) * amp
        amp_sum += amp
        amp *= persistence
        c /= 2
        k += 1
    return total / amp_sum


def loop_phase(ctx):
    """Animation phase 0..1 (frame / frames); frame N-1 -> 0 continues seamlessly."""
    return ctx.frame / max(1, ctx.frames)


def drift(ctx, cell, octaves, salt, vx=0, vy=0, persistence=0.5, stretch=(1, 1), warp=None):
    """Tileable noise translated by (vx*w, vy*h) texels over one animation loop.

    vx, vy must be integers so the last frame wraps exactly onto the first.
    """
    t = loop_phase(ctx)
    x = ctx.x - vx * ctx.w * t
    y = ctx.y - vy * ctx.h * t
    if warp is not None:
        x = x + warp[0]
        y = y + warp[1]
    return fbm(ctx, x, y, cell, octaves, salt, persistence, stretch)


def circle_blend(ctx, a, b):
    """Periodic morph between two zero-mean fields; keeps variance constant."""
    ph = 2 * math.pi * loop_phase(ctx)
    return (a - 0.5) * math.cos(ph) + (b - 0.5) * math.sin(ph) + 0.5


def stepped(ctx, v, levels):
    """Quantize 0..1 to `levels` values at 16x, keep smooth (slightly) at high res."""
    return ctx.quantize(np.clip(v, 0, 1), levels)
