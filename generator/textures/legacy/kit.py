"""Composition helpers: render 26.3 generators and re-arrange them on old sheets.

All rectangles are in texels of the respective Tex (x0, y0, x1, y1); pixel
scale is the context's `s`, so the same code works at every resolution.
Registry lookups happen at render time (other work areas may be imported
after this package).
"""
import json
from pathlib import Path

import numpy as np

from ...engine import Ctx, Tex
from ...registry import TEXTURES, register

CHANNELS = ("alpha", "height", "smooth", "f0", "metal", "porosity", "sss", "emissive")
_INDEX = json.loads((Path(__file__).resolve().parents[3] / "data" / "vanilla-26.3.json").read_text())["textures"]


def native(key):
    """(w, h, frames) of a registry entry in texels (26.3 interface data)."""
    spec = TEXTURES[key]
    if spec.size:
        return spec.size[0], spec.size[1], spec.frames or 1
    e = _INDEX.get(key.split("@")[0])
    if not e:
        return 16, 16, spec.frames or 1
    anim = e.get("mcmeta", {}).get("animation")
    if anim is None:
        return e["w"], e["h"], spec.frames or 1
    w = anim.get("width", e["w"])
    h = anim.get("height", w)
    return w, h, spec.frames or max(1, e["h"] // h)


def render(key, s, w=None, h=None, frame=0, frames=None, name=None):
    """Render registry entry `key` at scale s (optionally at another native size)."""
    nw, nh, nf = native(key)
    w, h = w or nw, h or nh
    frames = frames or nf
    ctx = Ctx(name or key.split("@")[0], w, h, s, frame=min(frame, frames - 1), frames=frames)
    out = TEXTURES[key].fn(ctx)
    if isinstance(out, list):
        out = out[min(frame, len(out) - 1)]
    return out


def blank(ctx):
    return Tex(ctx, np.zeros((ctx.H, ctx.W, 3), np.float32), alpha=0.0, height=0.0, wrap=False, grain=0.05)


def _px(t, r):
    s = t.ctx.s
    return [int(round(v * s)) for v in r]


def crop(t, r):
    """Sub-image of a Tex as a dict of channel arrays (pixels)."""
    x0, y0, x1, y1 = _px(t, r)
    d = {"color": t.color[y0:y1, x0:x1].copy()}
    for c in CHANNELS:
        d[c] = getattr(t, c)[y0:y1, x0:x1].copy()
    return d


def _transform(a, rot=0, fx=False, fy=False):
    if fx:
        a = a[:, ::-1]
    if fy:
        a = a[::-1]
    if rot:
        a = np.rot90(a, rot // 90 % 4)
    return a


def _resize(a, h, w):
    sh, sw = a.shape[:2]
    if (sh, sw) == (h, w):
        return a
    iy = np.minimum((np.arange(h) * sh) // max(h, 1), sh - 1) if h else np.zeros(0, int)
    ix = np.minimum((np.arange(w) * sw) // max(w, 1), sw - 1) if w else np.zeros(0, int)
    return a[iy][:, ix]


def put(dst, piece, r, rot=0, fx=False, fy=False, over=False):
    """Write a crop()'d piece into dst rect r (nearest resampling, optional
    flips then rotation by rot degrees counter-clockwise). over=True keeps dst
    where the piece is transparent."""
    x0, y0, x1, y1 = _px(dst, r)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(dst.ctx.W, x1), min(dst.ctx.H, y1)
    if x1 <= x0 or y1 <= y0:
        return
    h, w = y1 - y0, x1 - x0
    arrs = {k: _resize(_transform(v, rot, fx, fy), h, w) for k, v in piece.items()}
    m = arrs["alpha"] > 0.5 if over else np.ones((h, w), bool)
    dst.color[y0:y1, x0:x1][m] = arrs["color"][m]
    for c in CHANNELS:
        getattr(dst, c)[y0:y1, x0:x1][m] = arrs[c][m]


def blit(dst, src, sr, dr=None, **kw):
    """Copy src rect sr to dst rect dr (default: same place, same size)."""
    if dr is None:
        dr = sr
    elif len(dr) == 2:
        dr = (dr[0], dr[1], dr[0] + sr[2] - sr[0], dr[1] + sr[3] - sr[1])
    put(dst, crop(src, sr), dr, **kw)


def place(dst, src, x, y, **kw):
    """Paste a whole Tex at texel (x, y) of dst."""
    blit(dst, src, (0, 0, src.ctx.w, src.ctx.h), (x, y), **kw)


def fit(dst, src, r, **kw):
    """Paste a whole Tex scaled into rect r of dst."""
    put(dst, crop(src, (0, 0, src.ctx.w, src.ctx.h)), r, **kw)


def faces(u, v, w, h, d):
    return {
        "top": (u + d, v, u + d + w, v + d),
        "bottom": (u + d + w, v, u + d + 2 * w, v + d),
        "right": (u, v + d, u + d, v + d + h),
        "front": (u + d, v + d, u + d + w, v + d + h),
        "left": (u + d + w, v + d, u + 2 * d + w, v + d + h),
        "back": (u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h),
    }


def remap_box(dst, src, sbox, dbox, rows=None, over=False):
    """Copy every face of box sbox=(u, v, w, h, d) in src onto box dbox in dst,
    resampling faces of different size. rows=(a, b): only use the fraction a..b
    of the side faces' height (e.g. to split one leg into leg/shin/hoof)."""
    sf, df = faces(*sbox), faces(*dbox)
    for name in sf:
        s, d = sf[name], df[name]
        if s[2] <= s[0] or s[3] <= s[1] or d[2] <= d[0] or d[3] <= d[1]:
            continue
        if rows and name in ("right", "front", "left", "back"):
            hgt = s[3] - s[1]
            s = (s[0], s[1] + hgt * rows[0], s[2], s[1] + hgt * rows[1])
        put(dst, crop_f(src, s), d, over=over)


def crop_f(t, r):
    """crop() for fractional texel rects (rounded to whole pixels, >= 1 px)."""
    s = t.ctx.s
    x0, y0, x1, y1 = (int(np.floor(r[0] * s + 1e-6)), int(np.floor(r[1] * s + 1e-6)),
                      int(np.ceil(r[2] * s - 1e-6)), int(np.ceil(r[3] * s - 1e-6)))
    x1, y1 = max(x1, x0 + 1), max(y1, y0 + 1)
    d = {"color": t.color[y0:y1, x0:x1].copy()}
    for c in CHANNELS:
        d[c] = getattr(t, c)[y0:y1, x0:x1].copy()
    return d


def layered(ctx, keys, w=None, h=None):
    """Stack several same-layout textures (bottom to top) into one Tex."""
    out = None
    for k in keys:
        t = render(k, ctx.s, w or ctx.w, h or ctx.h)
        if out is None:
            out = blank(ctx)
            out.normal_strength, out.wrap, out.grain = t.normal_strength, False, t.grain
        out.paste(t)
    return out


def adopt(ctx, t):
    """Rebind a Tex rendered with another (same-sized) Ctx to ctx."""
    out = blank(ctx)
    out.paste(t, np.ones((ctx.H, ctx.W), np.float32))
    out.normal_strength, out.wrap, out.grain = t.normal_strength, t.wrap, t.grain
    return out


def top_part(ctx, key, h_full=None):
    """Render key at its 26.3 size and keep the top ctx.h rows (old sheets whose
    UVs equal the upper part of a taller modern sheet)."""
    t = render(key, ctx.s)
    out = blank(ctx)
    blit(out, t, (0, 0, ctx.w, ctx.h))
    out.normal_strength, out.grain = t.normal_strength, t.grain
    return out


def reg(path, fn, **kw):
    register(path, fn, **kw)
