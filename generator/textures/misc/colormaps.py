"""Biome colormaps and the ordered-dither matrix.

Colormap lookup convention (game side): x = (1 - temperature) * 255,
y = (1 - downfall * temperature) * 255, so the used area is the lower-left
triangle (y >= x). The upper-right part is filled by clamped extrapolation so
modded biomes outside the triangle still get sensible colors.
"""
import numpy as np

from ...engine import Tex
from ...registry import texture
from .common import native


def _climate(ctx):
    x = (ctx.tx + 0.5) / ctx.w
    y = (ctx.ty + 0.5) / ctx.h
    temp = np.clip(1 - x, 0, 1)
    wet = np.clip((1 - y) / np.maximum(temp, 1e-3), 0, 1)
    return temp, wet


def _field(ctx, anchors):
    """anchors: {temp: (dry_rgb, wet_rgb)} -> bilinear blend over (temperature, humidity)."""
    temp, wet = _climate(ctx)
    keys = sorted(anchors)
    cols = {k: [np.array([int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
                for c in anchors[k]] for k in keys}
    out = np.zeros((ctx.H, ctx.W, 3), np.float32)
    # humidity response is not linear: most of the change happens at the dry end
    w = (1 - (1 - wet) ** 1.6)[..., None]
    for a, b in zip(keys[:-1], keys[1:]):
        sel = (temp >= a) & (temp <= b)
        t = ((temp - a) / (b - a))[..., None]
        ca = cols[a][0] * (1 - w) + cols[a][1] * w
        cb = cols[b][0] * (1 - w) + cols[b][1] * w
        c = ca * (1 - t) + cb * t
        out[sel] = c[sel]
    return np.clip(out, 0, 1)


GRASS = {
    0.0: ("86ad98", "6fa894"),    # frozen: cool, blue-green, muted
    0.3: ("8db77a", "5fa86a"),    # taiga-ish
    0.6: ("9cbb5a", "5cab3e"),    # temperate meadow
    0.85: ("b4b552", "4ea52e"),   # warm
    1.0: ("c4b05a", "3f9e22"),    # hot: dry olive-yellow .. lush jungle
}
FOLIAGE = {
    0.0: ("6e9a86", "4f8e78"),
    0.3: ("72a05c", "3f8c46"),
    0.6: ("82a53e", "3a922a"),
    0.85: ("a2a338", "2f8f1c"),
    1.0: ("b29c3c", "248a14"),
}
DRY_FOLIAGE = {
    0.0: ("8f857a", "7a6f66"),    # grey-brown
    0.3: ("9c8a6c", "7d6448"),
    0.6: ("b0905e", "86603a"),
    0.85: ("c09a5a", "8a5c30"),
    1.0: ("cfa860", "7e5028"),    # sun-baked tan .. dark wet brown
}


def colormap(anchors):
    @native
    def gen(ctx):
        return Tex(ctx, _field(ctx, anchors), wrap=False, grain=0)
    return gen


texture("colormap/grass")(colormap(GRASS))
texture("colormap/foliage")(colormap(FOLIAGE))
texture("colormap/dry_foliage")(colormap(DRY_FOLIAGE))


BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32)


@texture("effect/dither")
@native
def dither(ctx):
    v = (BAYER4[ctx.ty % 4, ctx.tx % 4] + 0.5) / 16
    return Tex(ctx, np.repeat(v[..., None], 3, -1), wrap=True, grain=0)
