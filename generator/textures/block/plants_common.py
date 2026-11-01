"""Shared helpers for the block_plants work area (flowers, crops, coral, vines...).

Plants are drawn as texel-space vector shapes (leaf / blade / petal polygons, curves)
and shaded part by part with `part()`: top-left lit, slightly domed, per-texel grain,
no anti-aliasing at 16x and smooth outlines above. Alpha is always binary (cutout).
"""
import math

import numpy as np

from ...engine import Tex, hexc, pal
from ...registry import TEXTURES
from ...sprites import blank

# ------------------------------------------------------------------ palettes (dark -> light)
STEM = pal("23461a", "2f5c20", "3d7228", "4d8832", "62a03e", "7ab84f")
LEAF = pal("1f4417", "2a5a1d", "377024", "46862d", "589c38", "6db246")
LEAF_BLUE = pal("1d4a33", "275e40", "33724c", "418858", "529c66", "68b277")   # cooler foliage
LEAF_YELLOW = pal("3f5a17", "52721d", "668a25", "7ba02f", "92b63c", "a8c84d")
GRAY = pal("4a4a4a", "5e5e5e", "727272", "868686", "9a9a9a", "b0b0b0", "c6c6c6", "dcdcdc")
WOODY = pal("2f2216", "41301f", "533e28", "664d32", "785c3c", "8a6c48")
DRY = pal("5a4126", "73562f", "8c6a3a", "a47f46", "ba9455", "cfab67")


def gray_of(p, lo=0.45, hi=0.9):
    """Turn a colored palette into a grayscale (tint-ready) one spanning lo..hi."""
    p = np.asarray(p, np.float32)
    lum = p @ np.array([0.3, 0.59, 0.11], np.float32)
    lum = (lum - lum.min()) / max(1e-6, float(lum.max() - lum.min()))
    v = lo + (hi - lo) * lum
    return np.repeat(v[:, None], 3, 1)


def grays(n=6, lo=0.45, hi=0.9):
    v = np.linspace(lo, hi, n, dtype=np.float32)
    return np.repeat(v[:, None], 3, 1)


def desat(p, amount=0.85, tone=(0.52, 0.5, 0.48), dark=0.95):
    """Desaturate a palette toward gray (dead coral, withered plants)."""
    p = np.asarray(p, np.float32)
    lum = p @ np.array([0.3, 0.59, 0.11], np.float32)
    g = lum[:, None] * np.asarray(tone, np.float32) / 0.5
    return np.clip((p * (1 - amount) + g * amount) * dark, 0, 1)


def ramp(c0, c1, n=6):
    a, b = hexc(c0), hexc(c1)
    return np.stack([a + (b - a) * t for t in np.linspace(0, 1, n)]).astype(np.float32)


def shift(p, k):
    """Brighten (k>0) / darken (k<0) a palette."""
    p = np.asarray(p, np.float32)
    return np.clip(p * (1 + k) if k < 0 else p + (1 - p) * k, 0, 1)


# ------------------------------------------------------------------ shading

def part(ctx, mask, p, light=0.32, noise=0.12, shade=0.0, outline=False, outline_color=None,
         sss=0.6, smooth=0.12, emissive=0.0, bevel=1.5, f0=0.03, salt="", height=0.55, porosity=0.0):
    """Shade one plant part (mask) with palette p as a softly domed, top-left lit shape.

    shade: extra value offset (scalar or array, e.g. a vertical gradient).
    outline: darkest palette entry (or outline_color) on the 1-texel inner border.
    """
    m = mask > 0.5
    p = np.asarray(p, np.float32)
    d = ctx.distance(m.astype(np.float32), max_texels=bevel + 1)
    dome = np.clip(d / bevel, 0, 1)
    gy, gx = np.gradient(d)
    facing = np.clip((gx + gy) * ctx.s, -1.5, 1.5)
    n = ctx.texel_noise(f"part{salt}") - 0.5
    v = 0.5 + facing * light + (dome - 0.5) * 0.18 + n * noise + shade
    body = p[1:] if outline and outline_color is None else p
    color = ctx.palette(body, np.clip(v, 0, 1))
    if outline:
        ring = ctx.edge(m.astype(np.float32), 1.0) > 0
        oc = p[0] if outline_color is None else np.asarray(outline_color, np.float32)
        color = np.where(ring[..., None], oc, color)
    em = emissive if np.ndim(emissive) == 0 else np.asarray(emissive, np.float32)
    t = Tex(ctx, color, alpha=m.astype(np.float32), height=np.where(m, height - 0.15 + dome * 0.3, 0.0),
            smooth=smooth, f0=f0, sss=sss, porosity=porosity, emissive=np.where(m, em, 0.0),
            wrap=False, grain=0.04)
    return t


class Canvas:
    """Stack of shaded parts (bottom to top) on a transparent sprite canvas."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.t = blank(ctx)

    def add(self, mask, p, **kw):
        if np.any(np.asarray(mask) > 0.5):
            self.t.paste(part(self.ctx, mask, p, **kw))
        return self

    def tex(self, tex):
        self.t.paste(tex)
        return self

    def recolor(self, mask, rgb, emissive=None):
        m = (mask > 0.5) & (self.t.alpha > 0.5)
        self.t.color[m] = rgb if np.ndim(rgb) == 1 else np.asarray(rgb)[m]
        if emissive is not None:
            self.t.emissive[m] = emissive
        return self

    @property
    def mask(self):
        return self.t.alpha > 0.5

    def done(self):
        return self.t


# ------------------------------------------------------------------ shapes

def union(*masks):
    out = masks[0].astype(np.float32)
    for m in masks[1:]:
        out = np.maximum(out, m)
    return out


def minus(a, b):
    return np.where(b > 0.5, 0.0, a).astype(np.float32)


def bez(p0, p1, p2, n=12):
    """Quadratic Bezier as a list of points."""
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
    return out


def curve(ctx, pts, width=1.0, w_end=None):
    """Polyline as a thick line; width tapers linearly to w_end."""
    m = ctx.zeros()
    w_end = width if w_end is None else w_end
    k = max(1, len(pts) - 1)
    for i, ((x1, y1), (x2, y2)) in enumerate(zip(pts[:-1], pts[1:])):
        w = width + (w_end - width) * (i + 0.5) / k
        m = np.maximum(m, ctx.segment(x1, y1, x2, y2, w))
    return m


def stalk(ctx, x0, y0, x1, y1, width=1.0, bend=0.0, w_end=None):
    """Curved stem from (x0, y0) to (x1, y1); bend pushes the middle sideways (texels)."""
    mx, my = (x0 + x1) / 2 + bend, (y0 + y1) / 2
    return curve(ctx, bez((x0, y0), (mx, my), (x1, y1), 10), width, w_end)


def _axis_poly(base, tip, halfw, bend=0.0, n=14):
    """Polygon around a (curved) axis with half-width function halfw(t)."""
    bx, by = base
    tx, ty = tip
    L = math.hypot(tx - bx, ty - by) or 1.0
    ux, uy = (tx - bx) / L, (ty - by) / L
    nx, ny = -uy, ux
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        off = bend * 4 * t * (1 - t)
        cx = bx + (tx - bx) * t + nx * off
        cy = by + (ty - by) * t + ny * off
        h = halfw(t)
        left.append((cx + nx * h, cy + ny * h))
        right.append((cx - nx * h, cy - ny * h))
    return left + right[::-1]


def leaf(ctx, base, tip, width=3.0, bend=0.0, fat=0.4):
    """Lens / lanceolate leaf from base to tip; widest at fraction `fat`."""
    def hw(t):
        if t <= fat:
            return width / 2 * math.sin(t / fat * math.pi / 2) ** 0.8
        return width / 2 * math.cos((t - fat) / (1 - fat) * math.pi / 2) ** 0.9
    m = ctx.polygon(_axis_poly(base, tip, hw, bend))
    return np.maximum(m, curve(ctx, bez(base, _mid(base, tip, bend), tip, 6), 0.9) * (width >= 1.2))


def blade(ctx, base, tip, width=2.0, bend=0.0):
    """Grass blade: full width at the base tapering to a point."""
    m = ctx.polygon(_axis_poly(base, tip, lambda t: width / 2 * (1 - t) ** 0.85, bend))
    pts = bez(base, _mid(base, tip, bend), tip, 8)
    return np.maximum(m, curve(ctx, pts[:-1], min(1.0, width)))


def _mid(a, b, bend):
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
    return ((a[0] + b[0]) / 2 + nx * bend * 2, (a[1] + b[1]) / 2 + ny * bend * 2)


def ellipse(ctx, cx, cy, rx, ry, angle=0.0):
    c, s = math.cos(angle), math.sin(angle)
    dx, dy = ctx.x - cx, ctx.y - cy
    u, v = dx * c + dy * s, -dx * s + dy * c
    return ((u / rx) ** 2 + (v / ry) ** 2 < 1).astype(np.float32)


def petals(ctx, cx, cy, n, length, width, rot=0.0, inner=0.3, fat=0.5):
    """n petals radiating from (cx, cy)."""
    m = ctx.zeros()
    for i in range(n):
        a = rot + i * 2 * math.pi / n
        b = (cx + math.cos(a) * inner, cy + math.sin(a) * inner)
        t = (cx + math.cos(a) * length, cy + math.sin(a) * length)
        m = np.maximum(m, leaf(ctx, b, t, width, fat=fat))
    return m


def radial(ctx, cx, cy):
    """(distance, angle) fields around a point."""
    dx, dy = ctx.x - cx, ctx.y - cy
    return np.hypot(dx, dy), np.arctan2(dy, dx)


def vgrad(ctx, y0, y1, a=-0.15, b=0.15):
    """Vertical value offset from a (at y0) to b (at y1)."""
    t = np.clip((ctx.y - y0) / max(1e-6, (y1 - y0)), 0, 1)
    return a + (b - a) * t


def dots(ctx, pts, r=0.6):
    m = ctx.zeros()
    for x, y in pts:
        m = np.maximum(m, ctx.circle(x, y, r))
    return m


def px(ctx, cells):
    """Exact texel cells -> mask (hand placed details)."""
    m = ctx.zeros()
    for x, y in cells:
        if ctx.pixel_art:
            m = np.maximum(m, ctx.rect(x, y, x + 1, y + 1))
        else:  # same spot, rounded at high resolution
            m = np.maximum(m, ctx.circle(x + 0.5, y + 0.5, 0.62))
    return m


def phase(ctx):
    """Looping animation phase in radians."""
    return 2 * math.pi * ctx.frame / max(1, ctx.frames)


def sway_ctx(ctx, amount_fn):
    """Return a copy of ctx whose x coordinates are displaced by amount_fn(y) (texels).

    Lets any static drawing code wave like underwater plants.
    """
    from ...engine import Ctx
    c = Ctx(ctx.name, ctx.w, ctx.h, ctx.s, ctx.frame, ctx.frames)
    c.x = (ctx.x - amount_fn(ctx.y)).astype(np.float32)
    return c


# ------------------------------------------------------------------ cross-area reuse

def borrowed(ctx, path, fallback):
    """Render another area's texture (same seed) if it is registered, else fallback(ctx)."""
    spec = TEXTURES.get(path)
    if spec is not None:
        try:
            out = spec.fn(ctx.sub(path))
            if isinstance(out, list):
                out = out[0]
            out.ctx = ctx
            return out
        except Exception:  # other area still in progress: keep our own look
            pass
    return fallback(ctx)


def opaque_tex(ctx, color, height=0.5, **kw):
    return Tex(ctx, color, height=height, **kw)


def bind(fn, *args, **kw):
    return lambda ctx: fn(ctx, *args, **kw)


def leaf_spray(ctx, rng, n, x0, y0, x1, y1, length=(2.5, 4.0), width=(1.6, 2.4), up=0.6, cx=None):
    """Random leaves inside a box, pointing away from the box's vertical axis (bushes)."""
    cx = (x0 + x1) / 2 if cx is None else cx
    m = ctx.zeros()
    for _ in range(n):
        bx, by = rng.uniform(x0, x1), rng.uniform(y0, y1)
        side = 1 if bx > cx else -1
        if abs(bx - cx) < 0.6:
            side = rng.choice([-1, 1])
        ang = math.atan2(-up - rng.uniform(0, 0.6), side * (0.5 + rng.uniform(0, 0.6)))
        L = rng.uniform(*length)
        tip = (bx + math.cos(ang) * L, by + math.sin(ang) * L)
        m = np.maximum(m, leaf(ctx, (bx, by), tip, rng.uniform(*width), bend=rng.uniform(-0.5, 0.5)))
    return m


def stem_fill(ctx, p=STEM, period=4, salt="stemfill"):
    """Fully opaque stem texture (for model elements that sample small UV boxes)."""
    col = (ctx.x % period) / period
    v = 0.25 + 0.5 * (1 - np.abs(col - 0.45) * 2) + (ctx.texel_noise(salt) - 0.5) * 0.25
    v = v + (ctx.noise(4, 1, salt=salt, stretch=(1, 3)) - 0.5) * 0.2
    return Tex(ctx, ctx.palette(p, np.clip(v, 0, 1)), height=0.4 + v * 0.3, smooth=0.12, sss=0.55,
               wrap=False)
