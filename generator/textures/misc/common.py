"""Shared helpers for the misc work area (particles, environment, overlays, paintings...).

Nothing here registers textures.
"""
import numpy as np

from ...engine import Ctx, Tex, hexc, pal, smoothstep  # noqa: F401  (re-exported)


def native(fn):
    """Render at native size (scale 1) at every resolution.

    For lookup tables / cell grids the game reads pixel by pixel (colormaps,
    clouds, trim palettes, dither matrix): upscaling them would change meaning.
    """
    def wrapped(ctx):
        if ctx.s == 1:
            return fn(ctx)
        return fn(Ctx(ctx.name, ctx.w, ctx.h, 1, ctx.frame, ctx.frames))
    wrapped.__name__ = getattr(fn, "__name__", "native")
    return wrapped


class Canvas:
    """Simple RGBA painter: stack masks with colors (top layer last)."""

    def __init__(self, ctx, bg=None, alpha=0.0):
        self.ctx = ctx
        self.color = np.zeros((ctx.H, ctx.W, 3), np.float32)
        if bg is not None:
            self.color[:] = bg
        self.alpha = ctx.full(alpha)

    def put(self, mask, rgb, a=1.0):
        """Paint rgb (RGB or (H,W,3)) where mask > 0.5 with opacity a (scalar or field)."""
        m = np.asarray(mask) > 0.5
        rgb = np.asarray(rgb, np.float32)
        if rgb.ndim == 1:
            rgb = np.broadcast_to(rgb, self.color.shape)
        a = np.broadcast_to(np.asarray(a, np.float32), m.shape)
        self.color[m] = rgb[m]
        self.alpha[m] = a[m]
        return self

    def over(self, mask, rgb, a=1.0):
        """Alpha-composite rgb with coverage a*mask over the canvas (soft layers)."""
        cov = np.clip(np.asarray(mask, np.float32) * a, 0, 1)
        rgb = np.asarray(rgb, np.float32)
        if rgb.ndim == 1:
            rgb = np.broadcast_to(rgb, self.color.shape)
        out_a = cov + self.alpha * (1 - cov)
        safe = np.maximum(out_a, 1e-6)[..., None]
        self.color = (rgb * cov[..., None] + self.color * (self.alpha * (1 - cov))[..., None]) / safe
        self.alpha = out_a
        return self

    def tex(self, wrap=False, emissive=0.0, crisp=False, grain=0.0, height=None):
        a = np.clip(self.alpha, 0, 1)
        if crisp:
            a = (a > 0.5).astype(np.float32)
        h = np.where(a > 0.5, 0.5, 0.0) if height is None else height
        return Tex(self.ctx, np.clip(self.color, 0, 1), alpha=a, height=h, wrap=wrap,
                   grain=grain, emissive=emissive)


def gray(v):
    return np.array([v, v, v], np.float32)


def mix(a, b, t):
    t = np.asarray(t, np.float32)
    a = np.asarray(a, np.float32)
    b = np.asarray(b, np.float32)
    if t.ndim >= 2:
        t = t[..., None]
    return a + (b - a) * t


def ramp(ctx, p, v):
    """ctx.palette with clipping, convenience."""
    return ctx.palette(p, np.clip(v, 0, 1))


def ball_shade(ctx, cx, cy, r, mask=None):
    """0..1 light value on a sphere-ish disc lit from the top-left."""
    dx, dy = (ctx.x - cx) / max(r, 1e-3), (ctx.y - cy) / max(r, 1e-3)
    d2 = np.clip(dx * dx + dy * dy, 0, 1)
    nz = np.sqrt(1 - d2)
    lam = -0.5 * dx - 0.55 * dy + 0.65 * nz
    return np.clip(lam * 0.8 + 0.2, 0, 1)


def rot(x, y, ang, cx=0.0, cy=0.0):
    c, s = np.cos(ang), np.sin(ang)
    x, y = x - cx, y - cy
    return c * x - s * y + cx, s * x + c * y + cy


def ellipse(ctx, cx, cy, rx, ry, ang=0.0):
    x, y = rot(ctx.x, ctx.y, -ang, cx, cy)
    return (((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1).astype(np.float32)


def ring(ctx, cx, cy, r, w):
    d = np.hypot(ctx.x - cx, ctx.y - cy)
    return (np.abs(d - r) < w / 2).astype(np.float32)


def polar(ctx, cx, cy):
    dx, dy = ctx.x - cx, ctx.y - cy
    return np.hypot(dx, dy), np.arctan2(dy, dx)


def lumpy(ctx, cx, cy, r, salt, amount=0.25, lobes=1.6):
    """Irregular puff mask: a disc whose radius wobbles with noise (cell ~ r)."""
    d = np.hypot(ctx.x - cx, ctx.y - cy)
    n = ctx.noise(max(1.0, r * lobes / 2), 2, 0.5, salt=salt, detail=False)
    return (d < r * (1 + (n - 0.5) * 2 * amount)).astype(np.float32)


def outline(ctx, mask):
    """Inner 1-texel ring of a mask."""
    return ctx.edge(mask, 1.0) > 0
