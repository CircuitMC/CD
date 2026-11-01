"""Drawing helpers for the item_1 work area (items a-g).

All coordinates are given in a 16-unit design space and scaled by K(ctx) =
ctx.w / 16, so a 32x32 item uses the same design with twice the detail.
Shapes are vector masks: crisp texel art at 16x, smooth edges above.
"""
import math

import numpy as np

from ...engine import Tex, hexc, pal
from ...sprites import blank, compose, sprite

SQ2 = math.sqrt(2.0)


def K(ctx):
    return ctx.w / 16.0


# ------------------------------------------------------------------ masks

def poly(ctx, pts):
    k = K(ctx)
    return ctx.polygon([(x * k, y * k) for x, y in pts])


def circ(ctx, cx, cy, r):
    k = K(ctx)
    return ctx.circle(cx * k, cy * k, r * k)


def ell(ctx, cx, cy, rx, ry, rot=0.0):
    k = K(ctx)
    x, y = ctx.x / k - cx, ctx.y / k - cy
    c, s = math.cos(rot), math.sin(rot)
    u, v = x * c + y * s, -x * s + y * c
    return ((u / rx) ** 2 + (v / ry) ** 2 < 1).astype(np.float32)


def box(ctx, x0, y0, x1, y1):
    k = K(ctx)
    return ctx.rect(x0 * k, y0 * k, x1 * k, y1 * k)


def line(ctx, pts, w):
    k = K(ctx)
    m = ctx.zeros()
    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        m = np.maximum(m, ctx.segment(x1 * k, y1 * k, x2 * k, y2 * k, w * k))
    return m


def bez_pts(p0, p1, p2, n=20):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c = (1 - t) ** 2, 2 * t * (1 - t), t * t
        out.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))
    return out


def stroke(ctx, pts, w0, w1=None):
    """Polyline with width interpolated from w0 to w1."""
    w1 = w0 if w1 is None else w1
    k = K(ctx)
    m = ctx.zeros()
    n = max(1, len(pts) - 1)
    for i, ((x1, y1), (x2, y2)) in enumerate(zip(pts[:-1], pts[1:])):
        w = w0 + (w1 - w0) * (i + 0.5) / n
        m = np.maximum(m, ctx.segment(x1 * k, y1 * k, x2 * k, y2 * k, w * k))
    return m


def curve(ctx, p0, p1, p2, w0, w1=None, n=20):
    return stroke(ctx, bez_pts(p0, p1, p2, n), w0, w1)


def U(*ms):
    out = ms[0]
    for m in ms[1:]:
        out = np.maximum(out, m)
    return out


def minus(a, *bs):
    out = a.copy()
    for b in bs:
        out = out * (b < 0.5)
    return out


def inter(a, b):
    return np.minimum(a, b)


def grow(ctx, m, texels=1):
    """Dilate a mask by `texels` (square)."""
    sh = max(1, round(texels * ctx.s))
    b = m > 0.5
    out = b.copy()
    for dy in range(-sh, sh + 1):
        for dx in range(-sh, sh + 1):
            out |= np.roll(np.roll(b, dy, 0), dx, 1)
    return out.astype(np.float32)


def shift(ctx, m, dx, dy):
    k = K(ctx)
    return np.roll(np.roll(m, round(dy * k * ctx.s), 0), round(dx * k * ctx.s), 1)


# ---------------------------------------------------------- diagonal frame

class Diag:
    """Rotated design frame: u runs along (1, -1)/sqrt2 (toward top-right), v
    along (1, 1)/sqrt2 (toward bottom-right). origin in 16-unit coords."""

    def __init__(self, ox, oy, ang=-45.0):
        self.ox, self.oy = ox, oy
        a = math.radians(ang)
        self.ux, self.uy = math.cos(a), math.sin(a)
        self.vx, self.vy = -self.uy, self.ux

    def p(self, u, v):
        return (self.ox + u * self.ux + v * self.vx, self.oy + u * self.uy + v * self.vy)

    def pts(self, uvs):
        return [self.p(u, v) for u, v in uvs]

    def poly(self, ctx, uvs):
        return poly(ctx, self.pts(uvs))

    def seg(self, ctx, u0, u1, w, v=0.0):
        return line(ctx, [self.p(u0, v), self.p(u1, v)], w)

    def rect(self, ctx, u0, v0, u1, v1):
        return self.poly(ctx, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    def curve(self, ctx, a, b, c, w0, w1=None):
        return curve(ctx, self.p(*a), self.p(*b), self.p(*c), w0, w1)


# ---------------------------------------------------------------- shading

def rod(ctx, pts, width, p, outline=False, light=1.0, **kw):
    """Round bar along a polyline, lit from the top-left by its offset from the
    centre line (sticks, handles, shafts). p dark->light."""
    k = K(ctx)
    best = np.full((ctx.H, ctx.W), 1e9, np.float32)
    ox = ctx.zeros()
    oy = ctx.zeros()
    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        x1, y1, x2, y2 = x1 * k, y1 * k, x2 * k, y2 * k
        bx, by = x2 - x1, y2 - y1
        t = np.clip(((ctx.x - x1) * bx + (ctx.y - y1) * by) / max(1e-6, bx * bx + by * by), 0, 1)
        dx, dy = ctx.x - (x1 + bx * t), ctx.y - (y1 + by * t)
        d = dx * dx + dy * dy
        sel = d < best
        best = np.where(sel, d, best)
        ox = np.where(sel, dx, ox)
        oy = np.where(sel, dy, oy)
    m = (np.sqrt(best) < width * k / 2).astype(np.float32)
    off = -(ox + oy) / SQ2 / (width * k / 2 + 1e-6)
    v = np.clip(0.5 + off * 0.55 * light, 0, 1)
    pp = p[1:] if outline else p
    color = ctx.palette(pp, v)
    if outline:
        ring = ctx.edge(m, 1) > 0
        color = np.where(ring[..., None], p[0], color)
    t = Tex(ctx, color, alpha=m, height=np.where(m > 0.5, 0.45 + 0.3 * (1 - np.sqrt(best) / (width * k / 2 + 1e-6)), 0),
            wrap=False, grain=0.04, **kw)
    return t


def spr(ctx, mask, p, **kw):
    """sprite() with item defaults."""
    kw.setdefault("bevel", 2.0)
    return sprite(ctx, mask, p, **kw)


def paint(tex, mask, rgb, inside=True):
    m = mask > 0.5
    if inside:
        m &= tex.alpha > 0.5
    tex.color[m] = np.asarray(rgb, np.float32)
    return tex


def paint_v(tex, mask, rgb_arr, inside=True):
    """Paint with a per-pixel color array."""
    m = mask > 0.5
    if inside:
        m &= tex.alpha > 0.5
    tex.color = np.where(m[..., None], rgb_arr, tex.color)
    return tex


def dots(ctx, pts, r=0.55):
    """Small round dots at texel centres (16-unit coords of the texel's top-left)."""
    m = ctx.zeros()
    for x, y in pts:
        m = np.maximum(m, circ(ctx, x + 0.5, y + 0.5, r))
    return m


def cells(ctx, pts):
    m = ctx.zeros()
    for x, y in pts:
        m = np.maximum(m, box(ctx, x, y, x + 1, y + 1))
    return m


def glyph(ctx, rows, x0, y0, chars="#"):
    """Hand-drawn texel glyph (list of strings), rounded above 16x."""
    k = K(ctx)
    m = ctx.zeros()
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in chars:
                m = np.maximum(m, ctx.rect((x0 + i) * k, (y0 + j) * k, (x0 + i + 1) * k, (y0 + j + 1) * k))
    if ctx.s > 1 or k > 1:
        return ctx.organic(m, 0.15).astype(np.float32) if ctx.s > 1 else m
    return m


def lit_edges(ctx, tex, mask, light, dark, width=1.0):
    """Inner highlight on top-left edge and shade on bottom-right edge of a region,
    just inside its outline."""
    m = mask > 0.5
    k = K(ctx)
    inner = ctx.edge(m.astype(np.float32), width * k) > 0
    ring = ctx.edge(m.astype(np.float32), width * k * 2) > 0
    sec = ring & ~inner
    tl = ctx.edge(m.astype(np.float32), width * k * 2, "tl") > 0
    br = ctx.edge(m.astype(np.float32), width * k * 2, "br") > 0
    if light is not None:
        paint(tex, sec & tl & ~br, light)
    if dark is not None:
        paint(tex, sec & br & ~tl, dark)
    return tex


def gem(ctx, mask, p, facets, smooth=0.9, f0=0.17, emissive=0.0, sss=0.0):
    """Faceted gem: outline p[0]; facets = [(mask, palette index), ...] painted in order."""
    t = sprite(ctx, mask, p, bevel=1.5, smooth=smooth, f0=f0, emissive=emissive, sss=sss)
    ring = ctx.edge(mask, 1) > 0
    for fm, idx in facets:
        paint(t, (fm > 0.5) & ~ring, p[idx])
    t.height = np.where(mask > 0.5, 0.75, 0)
    return t


def metal(tex, mask, metal_id):
    if metal_id:
        tex.set_metal(mask, metal_id)
    tex.smooth = np.where(mask > 0.5, np.maximum(tex.smooth, 0.7), tex.smooth)
    return tex


def outline_layer(ctx, mask, rgb):
    """1-texel outline ring placed *outside* a mask (for parts drawn without outline)."""
    g = grow(ctx, mask, K(ctx))
    ring = (g > 0.5) & ~(mask > 0.5)
    t = Tex(ctx, np.broadcast_to(np.asarray(rgb, np.float32), (ctx.H, ctx.W, 3)).copy(),
            alpha=ring.astype(np.float32), height=np.where(ring, 0.3, 0), wrap=False, grain=0)
    return t


def mix(a, b, t):
    return np.asarray(a, np.float32) * (1 - t) + np.asarray(b, np.float32) * t


def shades(base_hex, n=5, lo=0.42, hi=1.35, warm=0.04):
    """Dark->light palette around a base color with a slight cool->warm hue shift."""
    c = hexc(base_hex) if isinstance(base_hex, str) else np.asarray(base_hex, np.float32)
    out = []
    for i in range(n):
        t = i / (n - 1)
        f = lo + (hi - lo) * t
        col = c * f
        if f > 1:
            col = col + (1 - col) * (f - 1) * 0.35
        col = col + np.array([warm, warm * 0.4, -warm]) * (t - 0.5)
        out.append(np.clip(col, 0, 1))
    return np.stack(out).astype(np.float32)


def tex_mask(t):
    return (t.alpha > 0.5).astype(np.float32)





def arc_pts(cx, cy, r, a0, a1, n=24):
    """Points on a circle arc, angles in degrees (0 = +x, 90 = +y / down)."""
    out = []
    for i in range(n + 1):
        a = np.radians(a0 + (a1 - a0) * i / n)
        out.append((cx + r * np.cos(a), cy + r * np.sin(a)))
    return out


def darker(p, n=1):
    """Shift a palette n steps darker (repeating the darkest)."""
    return np.concatenate([np.repeat(p[:1], n, 0), p[:-n]]) if n else p
