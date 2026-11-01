"""Shared helpers for the functional-block modules (func_*.py).

Everything here works in texel space so 16x stays crisp pixel art and higher
resolutions get the same design with more detail.
"""
import json
import math
from pathlib import Path

import numpy as np

from ...engine import COPPER, GOLD, IRON, Tex, pal
from ...materials import STONE, lerp
from ...registry import register

_INDEX = json.loads((Path(__file__).resolve().parents[3] / "data" / "vanilla-26.3.json").read_text())["textures"]

# ------------------------------------------------------------------ palettes
IRON_P = pal("3c3c42", "55555c", "6f6f77", "8d8d95", "acacb3", "c9c9cf", "e4e4e8")
DARK_IRON = pal("1f1f24", "2b2b31", "393940", "48484f", "585860", "6a6a72")
GOLD_P = pal("7a4f0c", "a26d12", "c99019", "e3b02a", "f4cd4a", "fde77f")
REDSTONE = pal("3b0303", "5f0606", "8c0b0b", "b81414", "e0261c", "ff5a3c", "ff9a78")
REDSTONE_OFF = pal("2a0606", "3e0a0a", "561010", "6e1717", "86201e")
MSTONE = pal("4a4a4e", "58585c", "656569", "727276", "808084", "8e8e92", "9d9da1")  # machine stone
SMOOTH = pal("7c7c80", "8a8a8e", "97979b", "a3a3a7", "afafb3", "bcbcc0")
OBSIDIAN = pal("0d0a14", "150f20", "1e152e", "2a1d40", "3a2955", "4e3a6e")
OAK = pal("5c4426", "6f5533", "8a6b41", "9a784b", "a98656", "b79461")
DARK_WOOD = pal("2a1d10", "38281a", "463322", "54402b", "634c33")
SCULK = pal("05121a", "0a1d27", "0f2a36", "153646", "1c4457", "255a6e")
SCULK_GLOW = pal("0f6e7a", "1ba2ad", "35d1d6", "7ff1ee", "c8fffb")
BONE = pal("8f8a73", "aaa48a", "c0ba9f", "d3cdb3", "e2ddc5", "efeadb")
FIRE = pal("7a1f02", "b83a05", "e46a0c", "f79a1c", "ffc53d", "ffe98a", "fff8d0")
SOUL_FIRE = pal("06334a", "0a5f78", "13a0b4", "35d4dc", "8ff4f2", "e6fffd")
GREEN_FIRE = pal("1d4a0c", "2f7a14", "4cab1e", "79d433", "b4ee6a", "e8ffc0")

COPPER_STAGES = {
    "": pal("5e2a17", "7f3d23", "a1532f", "bc6a3f", "d38351", "e8a26e", "f6c49a"),
    "exposed_": pal("5a3e33", "785645", "95705a", "a8826b", "b9957d", "c9a991", "dbc0aa"),
    "weathered_": pal("2f5444", "3e6b57", "4d8269", "5b9677", "6ca886", "86bd9b", "a6d2b5"),
    "oxidized_": pal("24584c", "2f6f60", "3b8775", "4a9e88", "5cb39b", "7bc8b1", "a1dcc9"),
}
COPPER_PREFIXES = list(COPPER_STAGES)


def copper_metal(stage):
    """LabPBR metal id for a copper oxidation stage (patina is dielectric)."""
    return COPPER if stage in ("", "exposed_") else None


# ------------------------------------------------------------------ registry
def reg(path, fn, **kw):
    """register() with vanilla frametime/interpolate unless given."""
    anim = _INDEX.get(path, {}).get("mcmeta", {}).get("animation")
    if anim is not None:
        kw.setdefault("frametime", anim.get("frametime", 1))
        kw.setdefault("interpolate", bool(anim.get("interpolate", False)))
    register(path, fn, **kw)


def bind(fn, *args, **kw):
    return lambda ctx: fn(ctx, *args, **kw)


# ------------------------------------------------------------------ painting
def M(m):
    return np.asarray(m) > 0.5


def paint(t, mask, color=None, h=None, **attrs):
    """Set color/height/other layers where mask is set. color: RGB or (H,W,3)."""
    m = M(mask)
    if color is not None:
        c = np.asarray(color, np.float32)
        if c.ndim == 1:
            t.color[m] = c
        else:
            t.color[m] = c[m]
    if h is not None:
        hv = np.asarray(h, np.float32)
        t.height[m] = hv if hv.ndim == 0 else hv[m]
    for k, v in attrs.items():
        if k == "metal":
            t.metal[m] = v if v else 0
            continue
        arr = getattr(t, k)
        vv = np.asarray(v, np.float32)
        arr[m] = vv if vv.ndim == 0 else vv[m]
    return t


def tone(t, mask, f):
    """Multiply color by f where mask."""
    m = M(mask)
    t.color[m] = np.clip(t.color[m] * f, 0, 1)
    return t


def bevel(ctx, t, mask, lit=1.18, dark=0.72, dh=0.1, width=1.0, raised=True):
    """Raise (or sink) a region: lit/shadow edges + height."""
    m = M(mask)
    e_tl = M(ctx.edge(m, width, "tl"))
    e_br = M(ctx.edge(m, width, "br")) & ~e_tl
    if raised:
        tone(t, e_tl, lit)
        tone(t, e_br, dark)
        t.height[m] = np.clip(t.height[m] + dh, 0, 1)
        t.height[e_br] = np.clip(t.height[e_br] - dh * 0.5, 0, 1)
    else:
        tone(t, e_tl, dark)
        tone(t, e_br, lit)
        t.height[m] = np.clip(t.height[m] - dh, 0, 1)
    return t


def cast_shadow(ctx, t, mask, f=0.7, dist=1):
    """Darken pixels just below-right of a raised mask."""
    m = M(mask)
    s = max(1, int(dist * ctx.s))
    sh = np.zeros_like(m)
    sh[s:, s:] |= m[:-s, :-s]
    sh[s:, :] |= m[:-s, :]
    sh &= ~m
    tone(t, sh, f)
    t.height[sh] *= 0.85
    return t


def rectm(ctx, x0, y0, x1, y1):
    return M(ctx.rect(x0, y0, x1, y1))


def ring(ctx, x0, y0, x1, y1, w=1):
    return rectm(ctx, x0, y0, x1, y1) & ~rectm(ctx, x0 + w, y0 + w, x1 - w, y1 - w)


def texel_set(ctx, cells):
    m = np.zeros((ctx.h, ctx.w), bool)
    for x, y in cells:
        if 0 <= x < ctx.w and 0 <= y < ctx.h:
            m[y, x] = True
    return m[np.clip(ctx.ty, 0, ctx.h - 1), np.clip(ctx.tx, 0, ctx.w - 1)]


def glyph(ctx, rows, x0, y0, ch="#"):
    """Mask of texels marked `ch` in a list of strings placed at (x0, y0)."""
    cells = {(x0 + i, y0 + j) for j, r in enumerate(rows) for i, c in enumerate(r) if c in ch}
    return texel_set(ctx, cells)


def surface(ctx, p, salt="", cell=6, contrast=0.6, lo=0.0, hi=1.0, h=0.5, hamp=0.12, **kw):
    """Low-noise base material using palette range lo..hi."""
    n = ctx.noise(cell, 3, 0.55, salt=f"sf{salt}")
    g = ctx.texel_noise(f"sf{salt}")
    v = lo + (hi - lo) * (n * contrast + g * (1 - contrast))
    kw.setdefault("smooth", 0.2)
    return Tex(ctx, ctx.palette(p, v), height=h + (n - 0.5) * hamp + (g - 0.5) * hamp * 0.4, **kw)


def metal_surface(ctx, p, salt="", metal=IRON, lo=0.25, hi=0.75, brushed=True, smooth=0.6):
    """Brushed or cast metal plate."""
    if brushed:
        b = ctx.noise(1, 2, 0.5, salt=f"brush{salt}", stretch=(6, 1))
    else:
        b = ctx.texel_noise(f"cast{salt}")
    n = ctx.noise(6, 2, 0.5, salt=f"msf{salt}")
    v = lo + (hi - lo) * (n * 0.55 + b * 0.45)
    t = Tex(ctx, ctx.palette(p, v), height=0.5 + (b - 0.5) * 0.04, smooth=smooth - b * 0.1, porosity=0.0)
    if metal:
        t.set_metal(ctx.full(1), metal)
    return t


def stone_surface(ctx, p=MSTONE, salt="", lo=0.2, hi=0.85):
    """Rough machine stone (furnace bodies etc.)."""
    n = ctx.noise(4, 3, 0.55, salt=f"ms{salt}")
    g = ctx.texel_noise(f"ms{salt}")
    v = lo + (hi - lo) * (n * 0.55 + g * 0.45)
    t = Tex(ctx, ctx.palette(p, v), height=0.45 + n * 0.2 + g * 0.08, smooth=0.15, porosity=0.15)
    # few chips
    chip = ctx.texel_noise(f"chip{salt}", soft=False) > 0.94
    chip = ctx.organic(chip, 0.3, f"chip{salt}")
    paint(t, chip, p[0], h=0.2)
    return t


def rivet(ctx, t, cx, cy, p, r=0.75, metal=IRON):
    m = M(ctx.circle(cx, cy, r)) if not ctx.pixel_art else rectm(ctx, math.floor(cx), math.floor(cy),
                                                                   math.floor(cx) + 1, math.floor(cy) + 1)
    paint(t, m, p[-3], h=0.85, metal=metal, smooth=0.6)
    hi_m = m & M(ctx.circle(cx - 0.25, cy - 0.25, r * 0.5))
    if not ctx.pixel_art:
        paint(t, hi_m, p[-1])
    cast_shadow(ctx, t, m, 0.7)
    return t


def flame_field(ctx, cx, base_y, height, width, salt="", frame=0, frames=1, speed=1.0):
    """0..1 flame intensity: tall teardrop with flickering noise (texel space)."""
    ph = (frame / max(1, frames)) * 2 * math.pi * speed
    dy = (base_y - ctx.y) / max(0.5, height)   # 0 at base -> 1 at tip
    wob = ctx.noise(2, 2, 0.5, salt=f"fl{salt}{frame}", detail=False) - 0.5
    sway = math.sin(ph) * 0.35 + wob * 0.8 * dy
    halfw = width * 0.5 * np.clip(1 - dy, 0, 1) ** 0.7 * np.clip(dy * 4 + 0.6, 0, 1.4)
    d = np.abs(ctx.x - cx - sway)
    f = np.clip(1 - d / np.maximum(halfw, 1e-3), 0, 1) * (dy >= -0.05) * (dy <= 1)
    return f * np.clip(1.15 - dy * 0.5, 0, 1)


def emissive_from(t, mask, amount):
    m = M(mask)
    a = np.asarray(amount, np.float32)
    t.emissive[m] = a if a.ndim == 0 else a[m]
    return t


def cutout(ctx, t, mask):
    """Binary alpha; transparent texels keep a dark color."""
    m = M(mask)
    t.alpha = m.astype(np.float32)
    t.color[~m] = t.color[~m] * 0.3
    t.height[~m] = 0
    t.wrap = False
    return t


def blank(ctx, rgb=(0, 0, 0)):
    return Tex(ctx, np.broadcast_to(np.asarray(rgb, np.float32), (ctx.H, ctx.W, 3)).copy(), alpha=0.0,
               height=0.0, wrap=False, grain=0.04)


def shade_v(ctx, p, mask, light=0.3, bevel_w=2.0, base=0.5):
    """Dome-shaded palette lookup for a mask (lit top-left)."""
    m = M(mask)
    d = ctx.distance(m.astype(np.float32), max_texels=bevel_w + 1)
    gy, gx = np.gradient(d)
    facing = np.clip((gx + gy) * ctx.s, -1.5, 1.5)
    dome = np.clip(d / bevel_w, 0, 1)
    v = np.clip(base + facing * light + (dome - 0.5) * 0.15, 0, 1)
    return ctx.palette(p, v), dome


def outline(ctx, mask, w=1.0):
    return M(ctx.edge(M(mask), w))


__all__ = [n for n in dir() if not n.startswith("__")]
_ = (GOLD, STONE, lerp)
