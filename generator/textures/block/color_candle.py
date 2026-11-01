"""Candles: small UV sheet used by the candle block models.

Layout (candle model UVs, block-space texels): wick 1x1 at (0, 5), candle top
2x2 at (0, 6), candle sides 2x6 at (0, 8), bottom 2x2 at (0, 14). The rest of
the texture is unused and left transparent. Lit candles have a glowing wick
and a warm, faintly emissive melt pool on top.
"""
import numpy as np

from ...engine import Tex, hexc
from ...registry import register
from .color_common import DYE, DYE_NAMES, adjust, mix, ramp

PLAIN_WAX = hexc("e6d6ab")
WICK = hexc("3a2c25")
WICK_LIT = [hexc("ffd56a"), hexc("ff9b2e")]


def wax_color(d):
    return np.clip(mix(adjust(d, sat=0.92), np.ones(3), 0.08), 0, 1)


def candle(ctx, wax, lit=False):
    p = ramp(wax, 6, dark=0.62, light=1.18, hue_shift=0.1)
    rgb = np.zeros((ctx.H, ctx.W, 3), np.float32) + p[2]
    alpha = ctx.zeros()
    height = ctx.zeros()
    emis = ctx.zeros()
    sx, sy = ctx.w / 16, ctx.h / 16  # texels per model unit (16 for a 16x16 texture)

    def R(x0, y0, x1, y1):
        return ctx.rect(x0 * sx, y0 * sy, x1 * sx, y1 * sy) > 0

    n = ctx.noise(1, 2, 0.5, salt="wax", stretch=(1, 3))
    # Sides (rows 8..14): left column lit, right column shaded, a drip of melted wax.
    sides = R(0, 8, 2, 14)
    left = R(0, 8, 1, 14)
    v = np.where(left, 0.68, 0.40) + (n - 0.5) * 0.18
    col = ctx.palette(p, np.clip(v, 0, 1))
    drip = R(1, 8, 2, 10) | R(0, 8, 1, 9)
    col = np.where(drip[..., None], p[4], col)
    foot = R(0, 13, 2, 14)
    col = np.where(foot[..., None], p[1] if not lit else p[2], col)
    rgb = np.where(sides[..., None], col, rgb)
    # Top (rows 6..8): rim with a small dimple around the wick.
    top = R(0, 6, 2, 8)
    tcol = np.where(R(0, 6, 1, 7)[..., None], p[5], p[3])
    tcol = np.where(R(1, 7, 2, 8)[..., None], p[2], tcol)
    if lit:  # warm melt pool lit by the flame
        warm = np.array([1.0, 0.86, 0.6], np.float32)
        tcol = np.clip(tcol * 0.55 + warm * 0.5, 0, 1)
        emis = np.where(top, 0.25, emis)
    rgb = np.where(top[..., None], tcol, rgb)
    # Bottom (rows 14..16)
    bot = R(0, 14, 2, 16)
    rgb = np.where(bot[..., None], ctx.palette(p[:3], n), rgb)
    # Wick (row 5)
    wick = R(0, 5, 1, 6)
    if lit:
        wc = WICK_LIT[0]
        emis = np.where(wick, 1.0, emis)
    else:
        wc = WICK
    rgb = np.where(wick[..., None], wc, rgb)
    solid = sides | top | bot | wick
    alpha = np.where(solid, 1.0, alpha)
    height = np.where(solid, 0.5 + n * 0.05, height)
    return Tex(ctx, np.clip(rgb, 0, 1), alpha=alpha, height=height, smooth=0.45, f0=0.035,
               sss=np.where(sides | top | bot, 0.55, 0.0), emissive=emis, wrap=False, grain=0.03)


register("block/candle", lambda ctx: candle(ctx, PLAIN_WAX))
register("block/candle_lit", lambda ctx: candle(ctx, PLAIN_WAX, True))
for _d in DYE_NAMES:
    _w = wax_color(DYE[_d])
    register(f"block/{_d}_candle", lambda ctx, w=_w: candle(ctx, w))
    register(f"block/{_d}_candle_lit", lambda ctx, w=_w: candle(ctx, w, True))
