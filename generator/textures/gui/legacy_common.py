"""Helpers to compose pre-1.20.2 GUI sheets from the modern sprite generators.

`sprite(ctx, path, w, h)` renders a registered 26.3 sprite (frame 0) at the sheet's scale into a
Canvas; nine-sliced sprites are resized with their own gui.scaling borders. `put` pastes it at
old-sheet texel coordinates.
"""
import json
from pathlib import Path

import numpy as np

from ...engine import Ctx
from ...registry import TEXTURES
from .common import Canvas

_INDEX = None


def _index():
    """26.3 index, completed with entries only found in older version indexes."""
    global _INDEX
    if _INDEX is None:
        root = Path(__file__).resolve().parents[3] / "data"
        _INDEX = {}
        files = sorted(root.glob("vanilla-*.json"), key=lambda f: [int(x) for x in f.stem[8:].split(".")])
        for f in files:  # oldest first, newer entries win
            _INDEX.update(json.loads(f.read_text())["textures"])
    return _INDEX


def native_size(path):
    spec = TEXTURES[path]
    if spec.size:
        return spec.size
    e = _index().get(path, {})
    anim = e.get("mcmeta", {}).get("animation")
    if anim:
        w = anim.get("width", e["w"])
        return w, anim.get("height", w)
    return e["w"], e["h"]


def borders(path):
    sc = _index().get(path, {}).get("mcmeta", {}).get("gui", {}).get("scaling", {})
    if sc.get("type") != "nine_slice":
        return None
    b = sc["border"]
    if isinstance(b, int):
        return b, b, b, b
    return b.get("left", 0), b.get("top", 0), b.get("right", 0), b.get("bottom", 0)


def render(ctx, path, w=None, h=None):
    """Render a registered generator at its own size (or w x h) -> Canvas at ctx.s."""
    nw, nh = native_size(path)
    w, h = w or nw, h or nh
    spec = TEXTURES[path]
    frames = spec.frames or 1
    sub = Ctx(path, w, h, ctx.s, frame=0, frames=frames)
    out = spec.fn(sub)
    if isinstance(out, list):
        out = out[0]
    c = Canvas(sub)
    c.rgb = np.asarray(out.color, np.float32).copy()
    c.a = np.asarray(out.alpha, np.float32).copy()
    return c


def _axis_map(nt, ns, b0, b1, s):
    px = np.arange(nt * s)
    t = (px + 0.5) / s
    src = px.copy()
    right = t >= nt - b1
    src[right] = px[right] - (nt - ns) * s
    mid = (t >= b0) & ~right
    if nt - b0 - b1 > 0:
        tc = (t[mid] - b0) / (nt - b0 - b1) * (ns - b0 - b1) + b0
        src[mid] = np.floor(tc * s).astype(int)
    return np.clip(src, 0, ns * s - 1)


def sprite(ctx, path, w=None, h=None):
    """Sprite at size w x h: nine-slice resize when the sprite has gui scaling, else re-render."""
    nw, nh = native_size(path)
    w, h = w or nw, h or nh
    b = borders(path)
    if (w, h) == (nw, nh) or b is None:
        return render(ctx, path, w, h) if b is None else render(ctx, path)
    src = render(ctx, path)
    sub = Ctx(path, w, h, ctx.s)
    out = Canvas(sub)
    xs = _axis_map(w, nw, b[0], b[2], ctx.s)
    ys = _axis_map(h, nh, b[1], b[3], ctx.s)
    out.rgb = src.rgb[ys][:, xs]
    out.a = src.a[ys][:, xs]
    return out


def put(c, ctx, path, x, y, w=None, h=None):
    c.paste(sprite(ctx, path, w, h), x, y)
    return c


def put_canvas(c, other, x, y, crop=None):
    """Paste another canvas, optionally a texel crop (x0, y0, x1, y1) of it."""
    if crop is not None:
        s = c.s
        x0, y0, x1, y1 = crop
        sub = Canvas.__new__(Canvas)
        sub.ctx, sub.s = other.ctx, s
        sub.rgb = other.rgb[y0 * s:y1 * s, x0 * s:x1 * s]
        sub.a = other.a[y0 * s:y1 * s, x0 * s:x1 * s]
        sub.w, sub.h = x1 - x0, y1 - y0
        other = sub
    c.paste(other, x, y)
    return c


def icon_button(c, ctx, x, y, icon, state="", w=20, h=20, iw=None, ih=None):
    """Old-style icon button: widget/button nine-sliced to w x h plus a centred icon sprite."""
    base = {"": "gui/sprites/widget/button", "_highlighted": "gui/sprites/widget/button_highlighted",
            "_disabled": "gui/sprites/widget/button_disabled"}[state]
    put(c, ctx, base, x, y, w, h)
    if icon:
        iw0, ih0 = native_size(icon)
        put(c, ctx, icon, x + (w - iw0) // 2, y + (h - ih0) // 2)
    return c
