"""Shared GUI drawing kit: a texel canvas, the CircuitMC panel/slot/button look and text.

All drawing happens in texel coordinates on a pixel buffer of ctx.s x ctx.s pixels per
texel, so 16x output is exact pixel art and higher resolutions get the same design with
smooth vector shapes (circles, polygons) and crisp texel-aligned text.
"""
import numpy as np

from ...engine import Tex
from . import glyphs

# ----------------------------------------------------------------- palette
def C(v):
    """'#rrggbb' / 'rrggbb' / (r, g, b) floats -> float RGB array."""
    if isinstance(v, str):
        v = v.lstrip("#")
        return np.array([int(v[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
    return np.asarray(v, np.float32)


def mix(a, b, t):
    return C(a) * (1 - t) + C(b) * t


INK = C("1c1d21")        # outlines
HI = C("f4f5f7")         # bevel highlight
FACE = C("c2c4ca")       # panel face
SHADE = C("6c6f78")      # bevel shadow
SLOT = C("8a8d95")       # slot interior
SLOT_DK = C("383a41")    # slot top-left edge
TEXT = C("3d3f46")       # label gray
WHITE = C("ffffff")
BLACK = C("0b0b0d")
GREEN = C("5fd35a")
RED = C("e0453a")
GOLD = C("f2c33a")
BLUE = C("4a8fe0")


# ----------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, ctx, bg=None, alpha=0.0):
        self.ctx, self.s = ctx, ctx.s
        self.w, self.h = ctx.w, ctx.h
        self.rgb = np.zeros((ctx.H, ctx.W, 3), np.float32)
        self.a = np.full((ctx.H, ctx.W), alpha, np.float32)
        if bg is not None:
            self.rgb[:] = C(bg)
            self.a[:] = 1.0 if alpha == 0.0 else alpha

    # -- primitives
    def _sl(self, x0, y0, x1, y1):
        s = self.s
        x0, x1 = max(0, int(round(x0 * s))), min(self.ctx.W, int(round(x1 * s)))
        y0, y1 = max(0, int(round(y0 * s))), min(self.ctx.H, int(round(y1 * s)))
        return slice(y0, max(y0, y1)), slice(x0, max(x0, x1))

    def fill(self, x0, y0, x1, y1, col, a=1.0):
        """Fill texel rect [x0, x1) x [y0, y1)."""
        sy, sx = self._sl(x0, y0, x1, y1)
        if a >= 1:
            self.rgb[sy, sx] = C(col)
            self.a[sy, sx] = 1.0
        elif a > 0:
            ia = self.a[sy, sx]
            na = a + ia * (1 - a)
            self.rgb[sy, sx] = (C(col) * a + self.rgb[sy, sx] * (ia * (1 - a))[..., None]) / np.maximum(na, 1e-6)[..., None]
            self.a[sy, sx] = na
        return self

    def rect(self, x, y, w, h, col, a=1.0):
        return self.fill(x, y, x + w, y + h, col, a)

    def clear(self, x, y, w, h):
        sy, sx = self._sl(x, y, x + w, y + h)
        self.a[sy, sx] = 0
        return self

    def px(self, x, y, col, a=1.0):
        return self.fill(x, y, x + 1, y + 1, col, a)

    def hline(self, x0, x1, y, col, a=1.0):
        return self.fill(x0, y, x1 + 1, y + 1, col, a)

    def vline(self, x, y0, y1, col, a=1.0):
        return self.fill(x, y0, x + 1, y1 + 1, col, a)

    def frame(self, x, y, w, h, col, a=1.0):
        self.hline(x, x + w - 1, y, col, a)
        self.hline(x, x + w - 1, y + h - 1, col, a)
        self.vline(x, y, y + h - 1, col, a)
        self.vline(x + w - 1, y, y + h - 1, col, a)
        return self

    def mask(self, m, col, a=1.0):
        m = m > 0.5
        if not m.any():
            return self
        col = np.asarray(C(col) if not isinstance(col, np.ndarray) or col.ndim == 1 else col, np.float32)
        if col.ndim == 3:
            col = col[m]
        if a >= 1:
            self.rgb[m] = col
            self.a[m] = 1.0
        else:
            ia = self.a[m]
            na = a + ia * (1 - a)
            self.rgb[m] = (col * a + self.rgb[m] * (ia * (1 - a))[..., None]) / np.maximum(na, 1e-6)[..., None]
            self.a[m] = na
        return self

    def erase(self, m):
        self.a[m > 0.5] = 0
        return self

    def cells(self, cells, x0, y0, col, a=1.0):
        for (x, y) in cells:
            self.px(x0 + x, y0 + y, col, a)
        return self

    def art(self, rows, colors, x0=0, y0=0):
        """Stamp a texel map: rows of chars, colors maps char -> color ('.'/' ' skip)."""
        if isinstance(rows, str):
            rows = rows.split()
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                c = colors.get(ch)
                if c is not None:
                    self.px(x0 + i, y0 + j, c)
        return self

    # -- vector shapes (texel space)
    def circle(self, cx, cy, r, col, a=1.0):
        return self.mask(self.ctx.circle(cx, cy, r), col, a)

    def poly(self, pts, col, a=1.0):
        return self.mask(self.ctx.polygon(pts), col, a)

    def line(self, x1, y1, x2, y2, col, width=1.0, a=1.0):
        """Texel-stepped line at 16x (Bresenham on texel centers), capsule above."""
        if self.s == 1:
            for (x, y) in bresenham(x1, y1, x2, y2):
                self.px(x, y, col, a)
            return self
        return self.mask(self.ctx.segment(x1 + 0.5, y1 + 0.5, x2 + 0.5, y2 + 0.5, width), col, a)

    def ring(self, cx, cy, r, width, col, a=1.0):
        m = self.ctx.circle(cx, cy, r) * (1 - self.ctx.circle(cx, cy, r - width))
        return self.mask(m, col, a)

    # -- composition
    def paste(self, other, x=0, y=0):
        """Alpha-over another canvas (same scale) at texel offset."""
        s = self.s
        oh, ow = other.a.shape
        X, Y = int(x * s), int(y * s)
        x0, y0 = max(0, X), max(0, Y)
        x1, y1 = min(self.ctx.W, X + ow), min(self.ctx.H, Y + oh)
        if x1 <= x0 or y1 <= y0:
            return self
        src_a = other.a[y0 - Y:y1 - Y, x0 - X:x1 - X]
        src = other.rgb[y0 - Y:y1 - Y, x0 - X:x1 - X]
        da = self.a[y0:y1, x0:x1]
        na = src_a + da * (1 - src_a)
        self.rgb[y0:y1, x0:x1] = (src * src_a[..., None] + self.rgb[y0:y1, x0:x1] * (da * (1 - src_a))[..., None]) \
            / np.maximum(na, 1e-6)[..., None]
        self.a[y0:y1, x0:x1] = na
        return self

    def shift_color(self, fn):
        self.rgb = fn(self.rgb)
        return self

    def tex(self):
        return Tex(self.ctx, np.clip(self.rgb, 0, 1), alpha=np.clip(self.a, 0, 1),
                   height=np.where(self.a > 0, 0.5, 0.0), wrap=False, grain=0)

    # -- text
    def text(self, s, x, y, col=TEXT, shadow=None, font="main"):
        """Draw text with the CircuitMC font; y = cap top. Returns the advance width."""
        cx = x
        for ch in s:
            if ch == " ":
                cx += 4 if font == "main" else 2
                continue
            g = glyphs.glyph(ch) if font == "main" else glyphs.tiny(ch)
            if not g:
                cx += 2
                continue
            if shadow is not None:
                self.cells(g, cx + 1, y + 1, shadow)
            self.cells(g, cx, y, col)
            cx += max(px for px, _ in g) + 2
        return cx - x - 1


def text_width(s, font="main"):
    w = 0
    for ch in s:
        if ch == " ":
            w += 4 if font == "main" else 2
            continue
        g = glyphs.glyph(ch) if font == "main" else glyphs.tiny(ch)
        w += (max(px for px, _ in g) + 2) if g else 2
    return max(0, w - 1)


def bresenham(x0, y0, x1, y1):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    out = []
    while True:
        out.append((x0, y0))
        if x0 == x1 and y0 == y1:
            return out
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


# ----------------------------------------------------------------- CircuitMC widgets
def bevel(c, x, y, w, h, hi=HI, sh=SHADE, face=FACE, width=1):
    """Raised rectangle: light top/left, dark bottom/right."""
    c.rect(x, y, w, h, face)
    for i in range(width):
        c.hline(x + i, x + w - 2 - i, y + i, hi)
        c.vline(x + i, y + i, y + h - 2 - i, hi)
        c.hline(x + 1 + i, x + w - 1 - i, y + h - 1 - i, sh)
        c.vline(x + w - 1 - i, y + 1 + i, y + h - 1 - i, sh)
    return c


def inset(c, x, y, w, h, face=SLOT, dk=SLOT_DK, hi=HI):
    """Recessed rectangle (slot look): dark top/left, light bottom/right."""
    c.rect(x, y, w, h, face)
    c.hline(x, x + w - 2, y, dk)
    c.vline(x, y, y + h - 2, dk)
    c.hline(x + 1, x + w - 1, y + h - 1, hi)
    c.vline(x + w - 1, y + 1, y + h - 1, hi)
    c.px(x + w - 1, y, mix(dk, hi, 0.5))
    c.px(x, y + h - 1, mix(dk, hi, 0.5))
    return c


def panel(c, x, y, w, h, face=FACE, ink=INK, hi=HI, sh=SHADE):
    """Main container panel: dark outline with clipped corners and a 2-texel bevel."""
    c.rect(x + 1, y + 1, w - 2, h - 2, face)
    # outline with 1-texel diagonal corners
    c.hline(x + 2, x + w - 3, y, ink)
    c.hline(x + 2, x + w - 3, y + h - 1, ink)
    c.vline(x, y + 2, y + h - 3, ink)
    c.vline(x + w - 1, y + 2, y + h - 3, ink)
    for (px_, py_) in ((x + 1, y + 1), (x + w - 2, y + 1), (x + 1, y + h - 2), (x + w - 2, y + h - 2)):
        c.px(px_, py_, ink)
    # bevel
    c.hline(x + 2, x + w - 4, y + 1, hi)
    c.hline(x + 2, x + w - 5, y + 2, hi)
    c.vline(x + 1, y + 2, y + h - 4, hi)
    c.vline(x + 2, y + 2, y + h - 5, hi)
    c.hline(x + 3, x + w - 3, y + h - 2, sh)
    c.hline(x + 4, x + w - 3, y + h - 3, sh)
    c.vline(x + w - 2, y + 3, y + h - 3, sh)
    c.vline(x + w - 3, y + 4, y + h - 3, sh)
    c.px(x + w - 3, y + 2, face)
    c.px(x + 2, y + h - 3, face)
    return c


def slot(c, x, y, size=18):
    """Slot frame; (x, y) is the top-left of the frame (item drawn at x+1, y+1 for 18)."""
    return inset(c, x, y, size, size)


def item_slot(c, ix, iy):
    """Slot frame around an item position (the game's slot x/y)."""
    return slot(c, ix - 1, iy - 1)


def big_slot(c, ix, iy):
    """26x26 output slot around a 16x16 item at (ix, iy)."""
    inset(c, ix - 5, iy - 5, 26, 26, face=C("7f828a"))
    c.frame(ix - 4, iy - 4, 24, 24, C("767880"))
    return c


def player_inventory(c, x, y):
    """3 rows of 9 slots at item position (x, y) plus the hotbar 58 texels below."""
    for r in range(3):
        for i in range(9):
            item_slot(c, x + i * 18, y + r * 18)
    for i in range(9):
        item_slot(c, x + i * 18, y + 58)
    return c


def grid(c, x, y, cols, rows):
    for r in range(rows):
        for i in range(cols):
            item_slot(c, x + i * 18, y + r * 18)
    return c


def arrow(c, x, y, col=SHADE, w=22, h=15):
    """Empty progress arrow (pointing right) drawn into a background; box 24x16 at (x, y)."""
    mid = y + 7
    c.rect(x + 1, mid - 2, 14, 5, col)
    for i in range(8):
        c.vline(x + 15 + i, mid - 7 + i, mid + 7 - i, col)
    return c


def arrow_mask_cells(w=24, h=16):
    """Cells of the arrow used for both the empty slot and the progress sprite."""
    cells = set()
    mid = 7
    for xx in range(1, 15):
        for yy in range(mid - 2, mid + 3):
            cells.add((xx, yy))
    for i in range(8):
        for yy in range(mid - 7 + i, mid + 8 - i):
            cells.add((15 + i, yy))
    return cells


def flame_cells():
    """14x14 flame silhouette (original), returns set of (x, y)."""
    rows = [
        "......#.......",
        "......##......",
        ".....###......",
        ".....####.....",
        "....#####..#..",
        "..#.######.#..",
        "..##########..",
        ".###########..",
        ".############.",
        "#############.",
        "##############",
        "##############",
        ".############.",
        "..##########..",
    ]
    return {(i, j) for j, r in enumerate(rows) for i, ch in enumerate(r) if ch == "#"}


def label(c, s, x, y, col=TEXT):
    return c.text(s, x, y, col)
