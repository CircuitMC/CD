"""Shared helpers for the entity_objects work area (chests, boats, equipment, ...).

A `Sheet` is a transparent canvas for unwrapped model textures. Model UV
boxes are given in *model* texels (texture offset + box size, as listed in the
OptiFine CEM template .jem files of github.com/ewanhowell5195/cemTemplateModels);
`k` scales them when the image is larger than the template's textureSize (e.g.
the end crystal template is 64x32 but its texture is 128x64 -> k = 2).

Face naming follows entity/common.py:
    top    = DOWN face region (u+d, v)      bottom = UP face region (u+d+w, v)
    right  = WEST face (u, v+d)              front  = NORTH face (u+d, v+d)
    left   = EAST face (u+d+w, v+d)          back   = SOUTH face (u+2d+w, v+d)
Designs that depend on which way a side face is shown are kept vertically
symmetric where the orientation is not certain (chests).
"""
import numpy as np

from ...engine import Tex, pal
from ...materials import lerp
from .common import box_faces

# 16 dye colors (dark-ish fabric base tones; dark -> light palettes are derived).
DYES = {
    "white": "e9ecec", "orange": "f07613", "magenta": "bd44b3", "light_blue": "3aafd9",
    "yellow": "f8c527", "lime": "70b919", "pink": "ed8dac", "gray": "3e4447",
    "light_gray": "8e8e86", "cyan": "158991", "purple": "792aac", "blue": "35399d",
    "brown": "724728", "green": "546d1b", "red": "a12722", "black": "1d1d21",
}
DYE_ORDER = ["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray",
             "light_gray", "cyan", "purple", "blue", "brown", "green", "red", "black"]


def ramp(hex_mid, n=5, spread=0.42, warm=0.04):
    """Dark -> light palette around one color, highlights warmer, shadows cooler."""
    c = pal(hex_mid)[0]
    out = []
    for i in range(n):
        t = (i / (n - 1)) * 2 - 1  # -1 .. 1
        if t < 0:
            col = c * (1 + t * spread) + np.array([-warm, -warm * 0.3, warm]) * (-t)
        else:
            col = c + (1 - c) * t * spread * 0.8 + np.array([warm, warm * 0.4, -warm]) * t
        out.append(np.clip(col, 0, 1))
    return np.stack(out).astype(np.float32)


class Sheet:
    """Transparent canvas with per-pixel PBR attributes for model unwraps."""

    def __init__(self, ctx, k=1):
        self.ctx, self.k = ctx, k
        z = ctx.zeros
        self.color = np.zeros((ctx.H, ctx.W, 3), np.float32)
        self.alpha, self.height = z(), z()
        self.smooth, self.f0 = z() + 0.15, z() + 0.04
        self.metal, self.porosity, self.sss, self.emissive = z(), z(), z(), z()

    # ---------------------------------------------------------- geometry
    def faces(self, u, v, w, h, d):
        k = self.k
        return {n: tuple(c * k for c in r) for n, r in box_faces(u, v, w, h, d).items()}

    def rect(self, r):
        return self.ctx.rect(*r) > 0.5

    def box_mask(self, u, v, w, h, d, which=None):
        m = np.zeros((self.ctx.H, self.ctx.W), bool)
        for n, r in self.faces(u, v, w, h, d).items():
            if which is None or n in which:
                m |= self.rect(r)
        return m

    def local(self, r):
        """Face-local texel coordinates (lx, ly) and size (w, h) of rect r."""
        return self.ctx.x - r[0], self.ctx.y - r[1], r[2] - r[0], r[3] - r[1]

    # ---------------------------------------------------------- painting
    def put(self, mask, color, alpha=1.0, height=0.5, smooth=None, f0=None, metal=None,
            emissive=None, porosity=None, sss=None):
        m = np.asarray(mask) > 0.5
        if not m.any():
            return self
        col = np.asarray(color, np.float32)
        if col.ndim == 1:
            self.color[m] = col
        else:
            self.color[m] = col[m]
        for name, val in (("alpha", alpha), ("height", height), ("smooth", smooth), ("f0", f0),
                          ("emissive", emissive), ("porosity", porosity), ("sss", sss)):
            if val is None:
                continue
            arr = getattr(self, name)
            v = np.asarray(val, np.float32)
            arr[m] = v[m] if v.ndim == 2 else v
        if metal is not None:
            self.metal[m] = metal
        elif f0 is not None or smooth is not None:
            pass
        return self

    def shade(self, mask, factor):
        """Multiply color inside mask (lighting / edge accents)."""
        m = np.asarray(mask) > 0.5
        f = np.asarray(factor, np.float32)
        self.color[m] = np.clip(self.color[m] * (f[m][..., None] if f.ndim == 2 else f), 0, 1)
        return self

    def tint(self, mask, rgb, t):
        m = np.asarray(mask) > 0.5
        self.color[m] = lerp(self.color[m], np.asarray(rgb, np.float32), t)
        return self

    def unmetal(self, mask):
        self.metal[np.asarray(mask) > 0.5] = 0
        return self

    def bevel(self, r, lit=1.12, dark=0.82, width=1, sides="tlbr"):
        """Lighter top/left, darker bottom/right edge ring inside rect r."""
        x0, y0, x1, y1 = r
        wd = width
        c = self.ctx
        if "t" in sides:
            self.shade(c.rect(x0, y0, x1, y0 + wd), lit)
        if "l" in sides:
            self.shade(c.rect(x0, y0 + wd, x0 + wd, y1), lit)
        if "b" in sides:
            self.shade(c.rect(x0, y1 - wd, x1, y1), dark)
        if "r" in sides:
            self.shade(c.rect(x1 - wd, y0, x1, y1 - wd), dark)
        return self

    def tex(self, grain=0.05, normal_strength=1.0):
        t = Tex(self.ctx, np.clip(self.color, 0, 1), alpha=self.alpha, height=self.height,
                smooth=self.smooth, f0=self.f0, porosity=self.porosity, sss=self.sss,
                emissive=self.emissive, wrap=False, grain=grain, normal_strength=normal_strength)
        t.metal = np.where(self.alpha > 0.5, self.metal, 0).astype(np.float32)
        return t


def frame(ctx, r, w=1, sides="tblr"):
    """Border ring of rect r (texels), on the chosen sides."""
    x0, y0, x1, y1 = r
    m = ctx.zeros()
    if "t" in sides:
        m = np.maximum(m, ctx.rect(x0, y0, x1, y0 + w))
    if "b" in sides:
        m = np.maximum(m, ctx.rect(x0, y1 - w, x1, y1))
    if "l" in sides:
        m = np.maximum(m, ctx.rect(x0, y0, x0 + w, y1))
    if "r" in sides:
        m = np.maximum(m, ctx.rect(x1 - w, y0, x1, y1))
    return m > 0.5


# ------------------------------------------------------------- material fields

def wood_field(ctx, p, salt="", along="x", boards=None, board_px=4, seam=True, origin=(0, 0)):
    """Plank-grain color + height over the whole canvas.

    along: grain direction ('x' horizontal boards, 'y' vertical).
    board_px: board width in texels; seams drawn in the darkest shade.
    """
    sx, sy = (6, 1) if along == "x" else (1, 6)
    g = ctx.noise(4, 3, 0.55, salt=f"wg{salt}", stretch=(sx, sy), norm=False)
    f = ctx.noise(1, 1, 0.5, salt=f"wf{salt}", stretch=(sx * 2, sy * 2), norm=False)
    t = ctx.texel_noise(f"wt{salt}")
    coord = (ctx.y - origin[1]) if along == "x" else (ctx.x - origin[0])
    idx = np.floor(coord / board_px).astype(np.int32)
    rng = ctx.rng(f"wb{salt}")
    tone = rng.uniform(-0.12, 0.12, 64).astype(np.float32)[idx % 64]
    v = np.clip(g * 0.75 + f * 0.25 - 0.15 + 0.15 + tone + (t - 0.5) * 0.15, 0, 1)
    color = ctx.palette(p[1:], v)
    height = 0.5 + (g - 0.5) * 0.2
    if seam:
        line = (np.floor(coord).astype(np.int32) - 0) % board_px == board_px - 1
        line = line & (coord >= 0)
        color = np.where(line[..., None], lerp(p[0], p[1], 0.35), color)
        height = np.where(line, 0.25, height)
    return color, height


def metal_field(ctx, p, salt="", stretch=(6, 1)):
    """Brushed metal color + height."""
    b = ctx.noise(1, 2, 0.5, salt=f"mb{salt}", stretch=stretch)
    n = ctx.noise(6, 2, 0.5, salt=f"mn{salt}")
    v = np.clip(0.5 + (b - 0.5) * 0.35 + (n - 0.5) * 0.5, 0, 1)
    return ctx.palette(p[1:-1], v), 0.55 + (b - 0.5) * 0.06


def cloth_field(ctx, lo=0.62, hi=0.9, salt=""):
    """Grayscale woven fabric value field (0..1 gray), for dye-tinted layers."""
    n = ctx.noise(6, 2, 0.5, salt=f"cl{salt}")
    t = ctx.texel_noise(f"ct{salt}")
    weave = ((ctx.tx + ctx.ty) % 2 == 0).astype(np.float32)
    v = n * 0.5 + t * 0.3 + weave * 0.2
    v = ctx.quantize(v, 4)
    return lo + (hi - lo) * v


def mottle(ctx, p, cell=4, salt="", grain=0.35):
    n = ctx.noise(cell, 2, 0.55, salt=f"mo{salt}")
    t = ctx.texel_noise(f"mt{salt}")
    v = n * (1 - grain) + t * grain
    return ctx.palette(p, v), 0.45 + n * 0.2


def gray(v):
    v = np.asarray(v, np.float32)
    return np.repeat(v[..., None], 3, -1)
