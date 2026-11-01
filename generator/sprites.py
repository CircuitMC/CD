"""Helpers for non-tiling sprites: items, plants, entities, GUI, particles.

Draw shapes as texel-space vector masks (ctx.polygon / circle / segment / rect)
so they stay crisp at 16x and get smooth edges at 64x+. Then turn masks into
shaded, outlined Tex layers with `sprite()` and stack them with `compose()`.
"""
import numpy as np

from .engine import Tex


def outline_of(ctx, mask, width=1.0):
    """Ring of pixels just *inside* the mask edge (vanilla-style item outline)."""
    return ctx.edge(mask, width) > 0


def sprite(ctx, mask, p, outline=True, bevel=2.0, light=0.28, smooth=0.25, f0=0.04, metal=None,
           emissive=0.0, sss=0.0, porosity=0.0, outline_color=None, crisp=True):
    """Shade a mask with palette p (dark->light) as a slightly domed, top-left lit shape.

    outline: darkest shade (or outline_color) on the 1-texel border.
    crisp:   binary alpha (needed for cutout blocks; items look best crisp too).
    """
    m = mask > 0.5
    d = ctx.distance(m.astype(np.float32), max_texels=bevel + 1)
    dome = np.clip(d / bevel, 0, 1)
    # Distance grows toward the interior: on top/left edges the gradient points
    # down/right, so (gx + gy) > 0 means "faces the light".
    gy, gx = np.gradient(d)
    facing = np.clip((gx + gy) * ctx.s, -1.5, 1.5)
    v = 0.48 + facing * light * 1.2 + (dome - 0.5) * 0.2
    color = ctx.palette(p[1:] if outline else p, np.clip(v, 0, 1))
    if outline:
        ring = outline_of(ctx, m)
        oc = p[0] if outline_color is None else outline_color
        color = np.where(ring[..., None], oc, color)
    alpha = m.astype(np.float32) if crisp else np.clip(mask, 0, 1)
    t = Tex(ctx, color, alpha=alpha, height=np.where(m, 0.35 + dome * 0.45, 0.0), smooth=smooth,
            f0=f0, emissive=np.where(m, emissive, 0.0), sss=sss, porosity=porosity, wrap=False, grain=0.04)
    if metal:
        t.set_metal(m.astype(np.float32), metal)
    return t


def blank(ctx):
    """Fully transparent sprite canvas to paste layers onto."""
    return Tex(ctx, np.zeros((ctx.H, ctx.W, 3), np.float32), alpha=0.0, height=0.0, wrap=False, grain=0)


def compose(ctx, *layers):
    """Paste layers bottom to top (each layer's alpha is its mask)."""
    out = blank(ctx)
    for layer in layers:
        out.paste(layer)
    return out


def flat(ctx, mask, rgb, alpha=1.0, **kw):
    """Unshaded fill (GUI panels, fonts, simple icons)."""
    m = mask > 0.5
    return Tex(ctx, np.broadcast_to(np.asarray(rgb, np.float32), (ctx.H, ctx.W, 3)).copy(),
               alpha=np.where(m, alpha, 0.0), height=np.where(m, 0.5, 0.0), wrap=False, grain=0, **kw)


def stem(ctx, points, width, p, **kw):
    """Polyline (plant stems, sticks, wires) as one shaded sprite."""
    m = ctx.zeros()
    for (x1, y1), (x2, y2) in zip(points[:-1], points[1:]):
        m = np.maximum(m, ctx.segment(x1, y1, x2, y2, width))
    return sprite(ctx, m, p, **kw)
