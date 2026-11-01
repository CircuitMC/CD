"""Shared helpers for the item_2 modules (h_*.py): palettes, masks, local frames.

Everything works in texel space of a 16x16 design; `k = ctx.w / 16` scales
designs onto larger canvases (e.g. 32x32 in-hand textures).
"""
import math

import numpy as np

from ...engine import ALBEDO_METAL, GOLD, IRON, COPPER, Tex, hexc, pal
from ...sprites import blank, compose, outline_of, sprite

__all__ = ["ramp", "mix", "rows_mask", "Frame", "ellipse", "poly", "seg", "paint", "spr", "metal",
           "gem", "union", "minus", "cells", "blank", "compose", "sprite", "hexc", "pal", "rgb",
           "NETH", "IRON", "GOLD", "COPPER", "ALBEDO_METAL", "Tex", "outline_of", "gray_of",
           "ring", "shadow_under", "lines_mask", "DYES"]

NETH = ALBEDO_METAL  # netherite: albedo-driven metal in LabPBR

# Dye colors (same values as the block area uses for stained glass).
DYES = {
    "white": "f2f4f5", "orange": "f07d1f", "magenta": "c24fbe", "light_blue": "3cb2e0",
    "yellow": "f8d22e", "lime": "79c51d", "pink": "ef8fad", "gray": "4a5054",
    "light_gray": "9c9d97", "cyan": "169c9c", "purple": "7b2fb0", "blue": "3a43a8",
    "brown": "7a4e2c", "green": "556e1c", "red": "a52a24", "black": "1c1c21",
}


def rgb(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def mix(a, b, t):
    return rgb(a) * (1 - t) + rgb(b) * t


def ramp(base, n=5, lo=0.42, hi=1.0, lift=0.45):
    """Dark->light palette around a base color with cool shadows and warm highlights.

    lo: brightness factor of the darkest entry; the base sits a bit above the middle;
    the lightest entry blends `lift` toward warm white.
    """
    b = rgb(base)
    out = []
    for i in range(n):
        t = i / (n - 1)
        if t < 0.62:
            f = lo + (1 - lo) * (t / 0.62)
            c = b * f
            c = c + np.array([-0.02, 0.0, 0.035]) * (1 - t / 0.62)  # cool shadow
        else:
            u = (t - 0.62) / 0.38
            c = b + (np.array([1.0, 0.97, 0.88]) - b) * lift * u * hi
        out.append(np.clip(c, 0, 1))
    return np.stack(out).astype(np.float32)


def gray_of(p):
    """Grayscale version of a palette (for tinted bases)."""
    p = np.asarray(p, np.float32)
    g = p @ np.array([0.3, 0.59, 0.11], np.float32)
    return np.repeat(g[:, None], 3, 1)


def rows_mask(ctx, rows, chars="#", x0=0, y0=0, k=None, round_=0.0):
    """Mask from a texel map (list of strings). Cells whose char is in `chars` are set.

    k scales the map (default ctx.w / 16). round_ > 0 rounds stair steps above 16x.
    """
    k = ctx.w / 16 if k is None else k
    m = np.zeros((ctx.H, ctx.W), bool)
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in chars:
                m |= (ctx.x >= (x0 + i) * k) & (ctx.x < (x0 + i + 1) * k) & \
                     (ctx.y >= (y0 + j) * k) & (ctx.y < (y0 + j + 1) * k)
    if round_ and not ctx.pixel_art and m.any():
        m = ctx.organic(m.astype(np.float32), rough=round_, salt=str(len(rows)))
    return m.astype(np.float32)


def cells(ctx, pts, k=None):
    """Mask of individual texels [(x, y), ...] in 16-design space."""
    k = ctx.w / 16 if k is None else k
    m = np.zeros((ctx.H, ctx.W), bool)
    fx, fy = np.floor(ctx.x / k).astype(int), np.floor(ctx.y / k).astype(int)
    for x, y in pts:
        m |= (fx == x) & (fy == y)
    return m.astype(np.float32)


def lines_mask(ctx, mask, step, offset=0.0, axis="y", width=1.0):
    """Every `step` texels a line (inside mask), e.g. stitch rows, planks."""
    v = ctx.y if axis == "y" else ctx.x
    k = ctx.w / 16
    ln = ((v / k - offset) % step) < width
    return (ln & (mask > 0.5)).astype(np.float32)


class Frame:
    """Local coordinates: origin o, axis u at `angle` degrees (screen space, y down)."""

    def __init__(self, ctx, o, angle=-45, k=None):
        self.ctx = ctx
        self.k = ctx.w / 16 if k is None else k
        a = math.radians(angle)
        self.o = np.array(o, np.float32) * self.k
        self.u = np.array([math.cos(a), math.sin(a)], np.float32)
        self.n = np.array([math.sin(a), -math.cos(a)], np.float32)  # left of u (up-left for -45)

    def p(self, t, s=0.0):
        q = self.o + (self.u * t + self.n * s) * self.k
        return float(q[0]), float(q[1])

    def poly(self, pts):
        return self.ctx.polygon([self.p(t, s) for t, s in pts])

    def seg(self, t0, t1, width, s=0.0):
        x0, y0 = self.p(t0, s)
        x1, y1 = self.p(t1, s)
        return self.ctx.segment(x0, y0, x1, y1, width * self.k)

    def ellipse(self, t, s, rt, rs):
        cx, cy = self.p(t, s)
        dx, dy = self.ctx.x - cx, self.ctx.y - cy
        a = dx * self.u[0] + dy * self.u[1]
        b = dx * self.n[0] + dy * self.n[1]
        return ((a / (rt * self.k)) ** 2 + (b / (rs * self.k)) ** 2 < 1).astype(np.float32)

    def coords(self):
        """(t, s) of every pixel."""
        dx, dy = self.ctx.x - self.o[0], self.ctx.y - self.o[1]
        return ((dx * self.u[0] + dy * self.u[1]) / self.k, (dx * self.n[0] + dy * self.n[1]) / self.k)


def ellipse(ctx, cx, cy, rx, ry, k=None):
    k = ctx.w / 16 if k is None else k
    return ((((ctx.x - cx * k) / (rx * k)) ** 2 + ((ctx.y - cy * k) / (ry * k)) ** 2) < 1).astype(np.float32)


def ring(ctx, cx, cy, r0, r1, k=None):
    k = ctx.w / 16 if k is None else k
    d = np.hypot(ctx.x - cx * k, ctx.y - cy * k) / k
    return ((d >= r0) & (d < r1)).astype(np.float32)


def poly(ctx, pts, k=None):
    k = ctx.w / 16 if k is None else k
    return ctx.polygon([(x * k, y * k) for x, y in pts])


def seg(ctx, x0, y0, x1, y1, width, k=None):
    k = ctx.w / 16 if k is None else k
    return ctx.segment(x0 * k, y0 * k, x1 * k, y1 * k, width * k)


def union(*ms):
    out = np.zeros_like(ms[0])
    for m in ms:
        out = np.maximum(out, m)
    return out


def minus(a, *bs):
    out = a.copy()
    for b in bs:
        out = np.where(b > 0.5, 0.0, out)
    return out.astype(np.float32)


def paint(t, mask, color, height=None, inside=True, **attrs):
    """Recolor texels of a Tex where mask (and alpha, if inside) is set."""
    m = mask > 0.5
    if inside:
        m &= t.alpha > 0.5
    c = rgb(color)
    if c.ndim == 1:
        t.color[m] = c
    else:
        t.color[m] = c[m]
    if height is not None:
        t.height[m] = height
    for k, v in attrs.items():
        getattr(t, k)[m] = v
    return t


def spr(ctx, mask, p, **kw):
    return sprite(ctx, mask, np.asarray(p, np.float32), **kw)


def metal(ctx, mask, p, mid=IRON, smooth=0.72, **kw):
    return sprite(ctx, mask, np.asarray(p, np.float32), smooth=smooth, metal=mid, **kw)


def gem(ctx, mask, p, smooth=0.88, **kw):
    return sprite(ctx, mask, np.asarray(p, np.float32), smooth=smooth, f0=0.17, **kw)


def shadow_under(ctx, t, mask, amount=0.7):
    """Darken t where `mask` would cast a 1-texel shadow down-right."""
    s = ctx.s * max(1, round(ctx.w / 16))
    m = mask > 0.5
    cast = (np.roll(m, s, 0) | np.roll(np.roll(m, s, 0), s, 1)) & ~m & (t.alpha > 0.5)
    t.color[cast] *= amount
    return t


# ------------------------------------------------------------ shared tool geometry
# Same diagonal convention as the item_1 area (a_lib.Diag), so tool families of
# both work areas line up: u toward top-right, v toward bottom-right.

class Diag:
    def __init__(self, ox, oy, ang=-45.0):
        self.ox, self.oy = ox, oy
        a = math.radians(ang)
        self.ux, self.uy = math.cos(a), math.sin(a)
        self.vx, self.vy = -self.uy, self.ux

    def p(self, u, v):
        return (self.ox + u * self.ux + v * self.vx, self.oy + u * self.uy + v * self.vy)

    def poly(self, ctx, uvs):
        return poly(ctx, [self.p(u, v) for u, v in uvs])

    def seg(self, ctx, u0, u1, w, v=0.0):
        return seg(ctx, *self.p(u0, v), *self.p(u1, v), w)

    def rect(self, ctx, u0, v0, u1, v1):
        return self.poly(ctx, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    def curve(self, ctx, a, b, c, w0, w1=None):
        return curve(ctx, self.p(*a), self.p(*b), self.p(*c), w0, w1)


def bez(p0, p1, p2, n=20):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c = (1 - t) ** 2, 2 * t * (1 - t), t * t
        out.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))
    return out


def stroke(ctx, pts, w0, w1=None):
    """Polyline with width tapering from w0 to w1."""
    w1 = w0 if w1 is None else w1
    m = ctx.zeros()
    n = max(1, len(pts) - 1)
    for i, ((x1, y1), (x2, y2)) in enumerate(zip(pts[:-1], pts[1:])):
        w = w0 + (w1 - w0) * (i + 0.5) / n
        m = np.maximum(m, seg(ctx, x1, y1, x2, y2, w))
    return m


def curve(ctx, p0, p1, p2, w0, w1=None, n=20):
    return stroke(ctx, bez(p0, p1, p2, n), w0, w1)


def rod(ctx, pts, width, p, outline=False, light=1.0, **kw):
    """Round bar along a polyline lit from the top-left (sticks, handles, shafts)."""
    k = ctx.w / 16
    best = np.full((ctx.H, ctx.W), 1e9, np.float32)
    ox, oy = ctx.zeros(), ctx.zeros()
    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        x1, y1, x2, y2 = x1 * k, y1 * k, x2 * k, y2 * k
        bx, by = x2 - x1, y2 - y1
        t = np.clip(((ctx.x - x1) * bx + (ctx.y - y1) * by) / max(1e-6, bx * bx + by * by), 0, 1)
        dx, dy = ctx.x - (x1 + bx * t), ctx.y - (y1 + by * t)
        d = dx * dx + dy * dy
        sel = d < best
        best, ox, oy = np.where(sel, d, best), np.where(sel, dx, ox), np.where(sel, dy, oy)
    r = width * k / 2
    m = (np.sqrt(best) < r).astype(np.float32)
    off = -(ox + oy) / math.sqrt(2) / (r + 1e-6)
    v = np.clip(0.5 + off * 0.55 * light, 0, 1)
    p = np.asarray(p, np.float32)
    color = ctx.palette(p[1:] if outline else p, v)
    if outline:
        color = np.where((ctx.edge(m, 1) > 0)[..., None], p[0], color)
    return Tex(ctx, color, alpha=m, height=np.where(m > 0.5, 0.45 + 0.3 * (1 - np.sqrt(best) / (r + 1e-6)), 0),
               wrap=False, grain=0.04, **kw)


__all__ += ["Diag", "bez", "stroke", "curve", "rod"]


def U(*ms):
    return union(*ms)


def line_paint(ctx, t, pts, color, w=0.8):
    """Paint a thin polyline (glints, seams) onto a sprite, inside its alpha."""
    m = ctx.zeros()
    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        m = np.maximum(m, seg(ctx, x1, y1, x2, y2, w))
    ring = ctx.edge(t.alpha, 1) > 0
    return paint(t, (m > 0.5) & ~ring, color)


__all__ += ["U", "line_paint"]


# ------------------------------------------------------------ more shape helpers
def circ(ctx, cx, cy, r):
    k = ctx.w / 16
    return ctx.circle(cx * k, cy * k, r * k)


def box(ctx, x0, y0, x1, y1):
    k = ctx.w / 16
    return ctx.rect(x0 * k, y0 * k, x1 * k, y1 * k)


def ell(ctx, cx, cy, rx, ry, rot=0.0):
    k = ctx.w / 16
    x, y = ctx.x / k - cx, ctx.y / k - cy
    c, s = math.cos(rot), math.sin(rot)
    u, v = x * c + y * s, -x * s + y * c
    return ((u / rx) ** 2 + (v / ry) ** 2 < 1).astype(np.float32)


def inter(a, b):
    return np.minimum(a, b)


def line(ctx, pts, w):
    return stroke(ctx, pts, w)


def dots(ctx, pts, r=0.55):
    m = ctx.zeros()
    for x, y in pts:
        m = np.maximum(m, circ(ctx, x + 0.5, y + 0.5, r))
    return m


def arc_pts(cx, cy, r, a0, a1, n=24):
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def grow(ctx, m, texels=1):
    s = max(1, round(texels * ctx.s * ctx.w / 16))
    g = m > 0.5
    out = g.copy()
    for dy in range(-s, s + 1):
        for dx in range(-s, s + 1):
            if dx * dx + dy * dy <= s * s:
                out |= np.roll(np.roll(g, dy, 0), dx, 1)
    return out.astype(np.float32)


def flat_layer(ctx, mask, color, **kw):
    from ...sprites import flat
    return flat(ctx, mask, rgb(color), **kw)


__all__ += ["circ", "box", "ell", "inter", "line", "dots", "arc_pts", "grow", "flat_layer"]
