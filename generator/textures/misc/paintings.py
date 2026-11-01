"""Original paintings (16 texels per block) and the painting back.

Every painting is a small scene painted with a shared toolkit: limited
palettes, short horizontal "brush" noise inside each shape, light from the
top-left, and a thin dark wooden frame. At 16x the palettes step hard
(pixel art); at higher resolutions the same shapes get softer gradients and
visible brush texture.

The file paths are the game's painting ids; the pictures are our own themes.
"""
import numpy as np

from ...engine import Tex, pal
from ...registry import texture
from .common import ellipse as _ellipse, hexc, mix, polar


class BoolCtx:
    """Ctx proxy whose shape helpers return boolean masks (so &, |, ~ work)."""

    def __init__(self, ctx):
        self.real = ctx

    def __getattr__(self, k):
        return getattr(self.real, k)

    def rect(self, *a):
        return self.real.rect(*a) > 0.5

    def circle(self, *a):
        return self.real.circle(*a) > 0.5

    def polygon(self, *a):
        return self.real.polygon(*a) > 0.5

    def segment(self, *a):
        return self.real.segment(*a) > 0.5


def ellipse(ctx, *a):
    return _ellipse(ctx, *a) > 0.5


def painting(*paths):
    def deco(fn):
        def run(ctx):
            return fn(BoolCtx(ctx))
        run.__name__ = fn.__name__
        texture(*paths)(run)
        return fn
    return deco


class Paint:
    def __init__(self, ctx, salt=""):
        self.ctx = ctx
        self.salt = salt or ctx.name
        self.color = np.zeros((ctx.H, ctx.W, 3), np.float32)
        self.w, self.h = ctx.w, ctx.h
        self._brush = {}

    def brush(self, stretch=(3, 1), cell=2.0):
        key = (stretch, cell)
        if key not in self._brush:
            n = self.ctx.noise(cell, 2, 0.5, salt=f"brush{stretch}{cell}", stretch=stretch)
            g = self.ctx.texel_noise("bgrain")
            self._brush[key] = n * 0.7 + g * 0.3 - 0.5
        return self._brush[key]

    def fill(self, mask, p, v=0.5, brush=0.3, stretch=(3, 1), cell=2.0):
        m = np.asarray(mask) > 0.5
        if not m.any():
            return self
        vv = np.broadcast_to(np.asarray(v, np.float32), m.shape) + self.brush(stretch, cell) * brush
        col = self.ctx.palette(p, np.clip(vv, 0, 1))
        self.color[m] = col[m]
        return self

    def put(self, mask, rgb):
        m = np.asarray(mask) > 0.5
        rgb = np.broadcast_to(np.asarray(rgb, np.float32), self.color.shape)
        self.color[m] = rgb[m]
        return self

    # common fields -------------------------------------------------------
    def vgrad(self, y0, y1, flip=False):
        t = np.clip((self.ctx.y - y0) / max(1e-3, y1 - y0), 0, 1)
        return 1 - t if flip else t

    def all(self):
        return np.ones((self.ctx.H, self.ctx.W), bool)

    def ridge(self, base, amp, cell, salt, below=True):
        """Mask under (or above) a 1D noisy horizon line y = base + amp * n(x)."""
        rng = self.ctx.rng(f"ridge{salt}")
        k = int(self.w / cell) + 3
        pts = rng.random(k)
        xs = np.arange(k) * cell - cell
        line = np.interp(self.ctx.x, xs, pts)
        # a finer octave
        pts2 = rng.random(k * 3)
        line = line * 0.75 + np.interp(self.ctx.x, np.arange(k * 3) * cell / 3 - cell, pts2) * 0.25
        y = base + (line - 0.5) * 2 * amp
        return (self.ctx.y >= y) if below else (self.ctx.y < y)

    def frame(self, dark="2a1a10", mid="4a3020", light="6e4a30"):
        ctx = self.ctx
        b = 1.0
        outer = ~((ctx.x >= b) & (ctx.x < self.w - b) & (ctx.y >= b) & (ctx.y < self.h - b))
        tl = outer & ((ctx.x < b) | (ctx.y < b)) & ~((ctx.x >= self.w - b) | (ctx.y >= self.h - b))
        self.put(outer, hexc(mid))
        self.put(tl, hexc(light))
        corner = outer & (((ctx.x >= self.w - b) & (ctx.y < b)) | ((ctx.x < b) & (ctx.y >= self.h - b)))
        self.put(corner, hexc(mid))
        br = outer & ((ctx.x >= self.w - b) | (ctx.y >= self.h - b)) & ~corner
        self.put(br, hexc(dark))
        return self

    def tex(self, frame=True):
        if frame:
            self.frame()
        return Tex(getattr(self.ctx, "real", self.ctx), np.clip(self.color, 0, 1), wrap=False, grain=0.03)


def P(*c):
    return pal(*c)


# ------------------------------------------------------------------ shared palettes
SKY_DAY = P("5a8ccf", "6f9fd8", "86b2e0", "a3c6e8", "c4dcf0")
SKY_DUSK = P("3a2a5a", "6a3a6a", "b0506a", "e07a5a", "f4b26a", "fbe0a0")
SKY_NIGHT = P("0c1028", "141a3a", "1e2850", "2c3a66")
GRASS = P("3a5a22", "4a7028", "5c8630", "74a03a", "90b848")
HILL_FAR = P("5a7a8a", "6a8a96", "7c9aa4", "90aab2")
WATER = P("1e3e6a", "2a5282", "3a6a9a", "5288b4", "7aa8cc")
WOOD = P("3a2414", "553620", "6e482a", "8a5e38", "a6764a")
STONE = P("4a4a50", "5e5e66", "74747c", "8c8c94", "a6a6ae")
SKIN = P("8a5236", "b0704a", "cc8c62", "e0a880", "f0c4a0")
SKIN2 = P("4a2a1a", "6a3e26", "8a5636", "a87048", "c48c62")
GOLD = P("6a4a10", "9a7018", "c49a28", "e2c050", "f6e08a")
LEAF = P("1e3a1a", "2a5222", "3a6a2a", "548a36", "74a848")
RED = P("5a1014", "8a1a1e", "b42a2a", "d84a3a", "f07a5a")
CREAM = P("8a7e68", "b0a488", "cec2a4", "e4dac0", "f4eedc")
DARK = P("0e0c12", "1a1620", "262230", "34303e")


def sky(p, paint, y0=0, y1=None, v0=0.0, v1=1.0, flip=False):
    y1 = paint.h if y1 is None else y1
    t = paint.vgrad(y0, y1, flip)
    paint.fill(paint.all(), p, v0 + (v1 - v0) * t, brush=0.12, stretch=(6, 1))


def sun_disc(paint, cx, cy, r, p, halo=None):
    ctx = paint.ctx
    d = np.hypot(ctx.x - cx, ctx.y - cy)
    if halo is not None:
        paint.fill(d < r * 1.9, halo, 0.6 - (d / (r * 1.9)) * 0.4, brush=0.05)
    paint.fill(d < r, p, 0.75 - (d / r) * 0.3, brush=0.08)


def tree(paint, x, base, height, crown, trunk_p=WOOD, leaf_p=LEAF, salt="t"):
    ctx = paint.ctx
    tw = max(1.0, height * 0.12)
    paint.fill(ctx.rect(x - tw / 2, base - height * 0.55, x + tw / 2, base), trunk_p, 0.35 + (ctx.x < x) * 0.25, brush=0.2, stretch=(1, 3))
    cy = base - height * 0.6
    blob = ctx.zeros()
    rng = ctx.rng(f"tree{salt}")
    for k in range(5):
        ox, oy = rng.uniform(-0.6, 0.6) * crown, rng.uniform(-0.5, 0.3) * crown
        blob = np.maximum(blob, ctx.circle(x + ox, cy + oy, crown * rng.uniform(0.55, 0.8)))
    shade = np.clip(0.75 - ((ctx.x - x) + (ctx.y - cy)) / (crown * 2.4), 0, 1)
    paint.fill(blob, leaf_p, shade, brush=0.35, stretch=(1, 1), cell=1.0)
    return blob


def pine(paint, x, base, height, p=LEAF, trunk=WOOD):
    ctx = paint.ctx
    paint.fill(ctx.rect(x - 0.5, base - height * 0.2, x + 0.5, base), trunk, 0.3, brush=0.1)
    wdt = height * 0.32
    tri = ctx.polygon([(x, base - height), (x + wdt, base - height * 0.18), (x - wdt, base - height * 0.18)])
    shade = np.clip(0.55 - (ctx.x - x) / (wdt * 2), 0, 1)
    paint.fill(tri, p, shade, brush=0.3, stretch=(2, 1), cell=1.0)


def figure(paint, x, base, height, cloth, skin=SKIN, hair=None, hat=None, staff=False):
    """Small standing person, facing the viewer, lit from the left."""
    ctx = paint.ctx
    hr = height * 0.13
    hy = base - height + hr
    body = ctx.polygon([(x - height * 0.12, hy + hr * 1.1), (x + height * 0.12, hy + hr * 1.1),
                        (x + height * 0.2, base), (x - height * 0.2, base)])
    paint.fill(body, cloth, 0.62 - (ctx.x > x) * 0.3, brush=0.25, stretch=(1, 2))
    head = ctx.circle(x, hy, hr)
    paint.fill(head, skin, 0.7 - (ctx.x > x) * 0.25, brush=0.1)
    if hair is not None:
        paint.fill(head & (ctx.y < hy - hr * 0.2), hair, 0.5, brush=0.2)
    if hat is not None:
        paint.fill(ctx.rect(x - hr * 1.6, hy - hr * 0.9, x + hr * 1.6, hy - hr * 0.5), hat, 0.4, brush=0.1)
        paint.fill(ctx.rect(x - hr * 0.9, hy - hr * 2.0, x + hr * 0.9, hy - hr * 0.6), hat, 0.55, brush=0.1)
    if staff:
        paint.fill(ctx.segment(x + height * 0.26, base - height * 0.85, x + height * 0.3, base, max(0.8, height * 0.05)),
                   WOOD, 0.6, brush=0.1)


def portrait(paint, cx, cy, s, skin, hair, cloth, bg=None, eyes="1a1414", hat=None, beard=None, mouth="8a3a30"):
    """Bust portrait: head and shoulders, s = head half-width in texels."""
    ctx = paint.ctx
    shoulders = ellipse(ctx, cx, cy + s * 3.4, s * 2.6, s * 1.9) & (ctx.y > cy + s * 1.6)
    paint.fill(shoulders, cloth, 0.6 - (ctx.x - cx) / (s * 6), brush=0.3, stretch=(1, 2))
    paint.fill(ctx.rect(cx - s * 0.4, cy + s * 0.8, cx + s * 0.4, cy + s * 2.0), skin, 0.35, brush=0.1)
    face = ellipse(ctx, cx, cy, s, s * 1.25)
    paint.fill(face, skin, 0.72 - (ctx.x - cx) / (s * 3.2) - (ctx.y - cy) / (s * 8), brush=0.12)
    if hair is not None:
        top = ellipse(ctx, cx, cy - s * 0.35, s * 1.12, s * 1.05) & ~(ellipse(ctx, cx, cy + s * 0.35, s * 0.9, s * 1.05) & (ctx.y > cy - s * 0.45))
        paint.fill(top, hair, 0.55 - (ctx.x - cx) / (s * 3), brush=0.35, stretch=(1, 2), cell=1.0)
    if beard is not None:
        bd = ellipse(ctx, cx, cy + s * 0.75, s * 0.85, s * 0.65) & (ctx.y > cy + s * 0.35)
        paint.fill(bd, beard, 0.5, brush=0.35, stretch=(1, 2), cell=1.0)
    ew = max(0.5, s * 0.16)
    for sx in (-1, 1):
        ex = cx + sx * s * 0.42
        paint.put(ctx.rect(ex - ew, cy - s * 0.1, ex + ew, cy - s * 0.1 + max(1.0, s * 0.2)), hexc(eyes))
    paint.put(ctx.rect(cx - s * 0.3, cy + s * 0.55, cx + s * 0.3, cy + s * 0.55 + max(0.6, s * 0.12)), hexc(mouth))
    if hat is not None:
        paint.fill(ellipse(ctx, cx, cy - s * 1.0, s * 1.9, s * 0.38), hat, 0.4, brush=0.15)
        paint.fill(ellipse(ctx, cx, cy - s * 1.35, s * 1.05, s * 0.75) & (ctx.y < cy - s * 1.0), hat, 0.6, brush=0.15)


def flower(paint, x, y, r, p, center="f2c43a"):
    ctx = paint.ctx
    d, a = polar(ctx, x, y)
    petals = d < r * (0.7 + 0.3 * np.abs(np.cos(a * 2.5)))
    paint.fill(petals, p, 0.75 - (d / r) * 0.35 - (ctx.x - x) / (r * 4), brush=0.15)
    paint.put(d < max(0.55, r * 0.3), hexc(center))


def stars(paint, density, salt, rgb="f4f0d8", mask=None):
    ctx = paint.ctx
    st = ctx.texel_noise(f"stars{salt}", soft=False) > 1 - density
    if not ctx.pixel_art:
        st &= np.hypot(ctx.x % 1 - 0.5, ctx.y % 1 - 0.5) < 0.35
    if mask is not None:
        st &= mask
    paint.put(st, hexc(rgb))


def sea(paint, y0, p=WATER, sparkle="dcecf8", salt="sea"):
    ctx = paint.ctx
    m = ctx.y >= y0
    t = np.clip((ctx.y - y0) / max(1, paint.h - y0), 0, 1)
    paint.fill(m, p, 0.8 - t * 0.6, brush=0.3, stretch=(6, 1))
    sp = (ctx.texel_noise(f"sp{salt}", soft=False) > 0.93) & m & (ctx.y < y0 + (paint.h - y0) * 0.6)
    paint.put(sp, hexc(sparkle))


# ================================================================== 16x16
@painting("painting/alban")
def alban(ctx):
    """Lighthouse on a cliff at dusk."""
    p = Paint(ctx)
    sky(SKY_DUSK, p, 1, 11, 0.05, 0.95)
    sea(p, 11, P("1e2a4a", "2a3a62", "3e527a", "6a6a8a"), "f4b26a")
    cliff = ctx.polygon([(1, 9), (6, 8.5), (8, 10), (9, 15), (1, 15)])
    p.fill(cliff, STONE, 0.45 - (ctx.y - 9) / 14, brush=0.3)
    p.fill(ctx.rect(4, 3, 6, 9), CREAM, 0.8 - (ctx.x >= 5) * 0.35, brush=0.05)
    p.put(ctx.rect(4, 5, 6, 6), hexc("b42a2a"))
    p.put(ctx.rect(4, 2, 6, 3), hexc("fff0a0"))
    p.put(ctx.rect(6, 2, 9, 3) * (ctx.texel_noise("beam", soft=False) > -1), hexc("fbe0a0"))
    return p.tex()


@painting("painting/aztec")
def aztec(ctx):
    """Stepped sunburst in terracotta and turquoise (abstract)."""
    p = Paint(ctx)
    cx, cy = ctx.w / 2, ctx.h / 2
    d = np.maximum(np.abs(ctx.x - cx), np.abs(ctx.y - cy))
    ring_i = np.floor(d / 1.5)
    pals = [P("c86a3a", "e08a4a"), P("2a8a8a", "3aa8a0"), P("e8c88a", "f4dca8"), P("7a3a26", "9a4a30")]
    for k in range(6):
        p.fill(ring_i == k, pals[k % 4], 0.5, brush=0.4)
    diag = np.abs(np.abs(ctx.x - cx) - np.abs(ctx.y - cy)) < 0.6
    p.put(diag & (d > 1.5), hexc("3a1a12"))
    return p.tex()


@painting("painting/aztec2")
def aztec2(ctx):
    """Woven textile: zigzag bands in ochre, indigo and cream."""
    p = Paint(ctx)
    band = np.floor((ctx.y + np.abs((ctx.x % 6) - 3)) / 3) % 3
    p.fill(band == 0, P("b0801e", "d4a032"), 0.5, brush=0.3)
    p.fill(band == 1, P("26305e", "34407a"), 0.5, brush=0.3)
    p.fill(band == 2, CREAM, 0.6, brush=0.3)
    dots = ((ctx.tx % 3) == 1) & ((ctx.ty % 6) == 3)
    p.put(dots, hexc("b42a2a"))
    return p.tex()


@painting("painting/bomb")
def bomb(ctx):
    """Still life: a brass lantern glowing on a dark table."""
    p = Paint(ctx)
    d = np.hypot(ctx.x - 8, ctx.y - 8)
    p.fill(p.all(), P("140e0c", "2a1c14", "4a3020", "7a5030"), np.clip(1 - d / 9, 0, 1), brush=0.15, stretch=(1, 1))
    p.fill(ctx.y >= 12, WOOD, 0.35, brush=0.3, stretch=(6, 1))
    p.fill(ctx.rect(5, 6, 11, 12), GOLD, 0.3 + (ctx.x < 8) * 0.3, brush=0.1)
    p.fill(ctx.rect(6, 7, 10, 11), P("e07a20", "f4b040", "ffe890"), np.clip(1 - np.hypot(ctx.x - 8, ctx.y - 9) / 2.5, 0, 1), brush=0.1)
    p.fill(ctx.rect(6, 4, 10, 6), GOLD, 0.5, brush=0.1)
    p.put(ctx.rect(7.5, 2, 8.5, 4), hexc("6a4a10"))
    return p.tex()


@painting("painting/kebab")
def kebab(ctx):
    """Still life: teapot and cup on a checked cloth."""
    p = Paint(ctx)
    p.fill(p.all(), P("6a4a5a", "7a5a6a", "8a6a7a"), 0.5, brush=0.3)
    cloth = ctx.y >= 10
    check = ((ctx.tx // 2 + ctx.ty // 2) % 2) == 0
    p.fill(cloth & check, RED, 0.55, brush=0.1)
    p.fill(cloth & ~check, CREAM, 0.7, brush=0.1)
    pot = ellipse(ctx, 6, 8, 3.2, 2.8)
    p.fill(pot, P("1e4a5a", "2a6a7a", "3a8a96", "6ab4bc"), 0.75 - (ctx.x - 4) / 7 - (ctx.y - 6) / 10, brush=0.1)
    p.fill(ctx.segment(9, 7.5, 11.5, 6, 1.0), P("1e4a5a", "2a6a7a"), 0.5)
    p.fill(ctx.rect(5, 4.5, 7, 5.5), P("1e4a5a", "3a8a96"), 0.6)
    cup = ctx.rect(11, 9, 14, 11)
    p.fill(cup, CREAM, 0.8 - (ctx.x >= 12.5) * 0.3, brush=0.05)
    return p.tex()


@painting("painting/meditative")
def meditative(ctx):
    """A single candle in the dark, halo of warm light."""
    p = Paint(ctx)
    d = np.hypot(ctx.x - 8, (ctx.y - 6) * 1.1)
    p.fill(p.all(), P("08060a", "160e12", "2a1a16", "4a2e1c", "6a4424"), np.clip(1 - d / 8, 0, 1) ** 1.3, brush=0.1, stretch=(1, 1))
    p.fill(ctx.rect(7, 8, 9, 14), CREAM, 0.75 - (ctx.x >= 8) * 0.35, brush=0.05)
    p.put(ctx.rect(7.5, 7, 8.5, 8), hexc("2a1a10"))
    p.fill(ellipse(ctx, 8, 5.6, 0.9, 1.7), P("e07a20", "f8c040", "fff2b0"), np.clip(1 - np.abs(ctx.y - 6) / 2, 0, 1), brush=0.05)
    p.fill(ctx.rect(4, 14, 12, 15), WOOD, 0.3, brush=0.2)
    return p.tex()


@painting("painting/plant")
def plant(ctx):
    """A little bonsai in a blue glazed pot."""
    p = Paint(ctx)
    sky(P("d8c8a8", "e4d6b8", "f0e4cc"), p, 1, 15, 0.9, 0.2)
    p.fill(ctx.polygon([(4, 11), (12, 11), (11, 14), (5, 14)]), P("1e3a6a", "2a5292", "4a72b2"), 0.7 - (ctx.x - 4) / 10, brush=0.1)
    p.fill(ctx.segment(8, 11, 7, 8, 1.2) | ctx.segment(7, 8, 9.5, 6, 1.0) | ctx.segment(7, 8.5, 5, 7, 0.9), WOOD, 0.4)
    for x, y, r in ((9.5, 5, 2.2), (5, 6.2, 1.8), (7.4, 4, 1.6)):
        p.fill(ellipse(ctx, x, y, r, r * 0.65), LEAF, 0.75 - (ctx.y - (y - 1)) / 3, brush=0.25, stretch=(1, 1), cell=1)
    return p.tex()


@painting("painting/wasteland")
def wasteland(ctx):
    """Dead tree on cracked red earth under a pale sun."""
    p = Paint(ctx)
    sky(P("8a3a2a", "b05a3a", "d08a5a", "e8b48a"), p, 1, 11, 0.9, 0.1, flip=False)
    sun_disc(p, 11, 5, 1.6, P("f4d8a8", "fff0d0"))
    p.fill(ctx.y >= 11, P("4a2014", "6a301c", "8a4226"), 0.6 - (ctx.y - 11) / 8, brush=0.3, stretch=(5, 1))
    cracks = (np.abs(np.sin(ctx.x * 1.7 + ctx.y * 2.3)) < 0.12) & (ctx.y >= 12)
    p.put(cracks, hexc("2a100a"))
    br = (ctx.segment(5, 12, 5, 6, 1.0) | ctx.segment(5, 8, 3, 5.5, 0.8) | ctx.segment(5, 7, 7.5, 4.5, 0.8)
          | ctx.segment(7, 5, 8, 5, 0.7))
    p.put(br, hexc("1e140e"))
    return p.tex()


# ================================================================== 32x16
@painting("painting/courbet")
def courbet(ctx):
    """Two travellers at a fork in a country road."""
    p = Paint(ctx)
    sky(SKY_DAY, p, 1, 9, 0.9, 0.3)
    p.fill(p.ridge(8, 1.2, 6, "c1"), HILL_FAR, 0.5, brush=0.2)
    p.fill(ctx.y >= 9, GRASS, 0.6 - (ctx.y - 9) / 14, brush=0.3, stretch=(4, 1))
    road = (np.abs(ctx.x - 16 - (ctx.y - 9) * 0.0) < (ctx.y - 8) * 1.2) & (ctx.y >= 9)
    fork = (np.abs(ctx.x - 16 - (9 - ctx.y) * 1.5) < 0.6) & (ctx.y > 8) & (ctx.y < 10)
    p.fill(road | fork, P("8a7050", "a68a64", "c4a87e"), 0.5, brush=0.2)
    figure(p, 13.5, 14, 6, RED, hat=WOOD, staff=True)
    figure(p, 18, 14, 5.5, P("26305e", "34407a", "4a5a9a"), hair=WOOD)
    tree(p, 27, 12, 8, 3, salt="cb")
    return p.tex()


@painting("painting/creebet")
def creebet(ctx):
    """Green vines overrunning a ruined stone arch."""
    p = Paint(ctx)
    sky(P("8aa0b0", "a4b8c4", "c0d0d8"), p, 1, 15, 0.9, 0.3)
    p.fill(ctx.y >= 12, GRASS, 0.5, brush=0.3)
    d = np.hypot((ctx.x - 16) / 1.1, ctx.y - 12)
    arch = (d < 9) & (d > 5.5) & (ctx.y < 12) | (ctx.rect(6, 6, 10, 14) > 0) | (ctx.rect(22, 6, 26, 14) > 0)
    arch &= ~(ctx.rect(23, 1, 30, 8) > 0)
    blocks = ((ctx.tx + (ctx.ty // 2) % 2 * 2) % 4 == 0) | (ctx.ty % 2 == 0)
    p.fill(arch, STONE, 0.55 - blocks * 0.1 - (ctx.x - 6) / 60, brush=0.2)
    vine = p.ridge(5, 3, 3, "vine", below=True) & arch & (ctx.noise(2, 2, 0.5, salt="vn") > 0.45)
    p.fill(vine, LEAF, 0.6, brush=0.4, stretch=(1, 1), cell=1)
    return p.tex()


@painting("painting/pool")
def pool(ctx):
    """Lily pond: pads and two pink blossoms on dark green water."""
    p = Paint(ctx)
    p.fill(p.all(), P("12302a", "1a4038", "245248", "34665a"), 0.5 + p.vgrad(0, 16) * 0.2, brush=0.35, stretch=(5, 1))
    rng = ctx.rng("pads")
    for k in range(7):
        x, y, r = rng.uniform(3, 29), rng.uniform(3, 13), rng.uniform(1.4, 2.6)
        d, a = polar(ctx, x, y)
        pad = (d < r) & ~((np.abs(a - rng.uniform(-3, 3)) < 0.4))
        p.fill(pad, LEAF, 0.75 - (ctx.y - y + r) / (r * 3), brush=0.15)
    flower(p, 11, 7, 1.6, P("a8406a", "d8709a", "f4b0c8"), "f8e070")
    flower(p, 23, 11, 1.4, P("a8406a", "d8709a", "f4b0c8"), "f8e070")
    return p.tex()


@painting("painting/sea")
def sea_painting(ctx):
    """A small sailing ship on a choppy grey-green sea."""
    p = Paint(ctx)
    sky(P("6a7480", "828c96", "9ca4ac", "b6bcc2"), p, 1, 9, 0.2, 0.9)
    sea(p, 9, P("1e3a3a", "2a4e4c", "3a6460", "5a827a"), "c8dcd4")
    crest = (np.abs(np.sin(ctx.x * 0.9 + ctx.y * 2.2)) > 0.93) & (ctx.y > 9.5)
    p.put(crest, hexc("dce8e0"))
    p.fill(ctx.polygon([(12, 10), (21, 10), (19.5, 12), (13.5, 12)]), WOOD, 0.45, brush=0.1)
    p.put(ctx.rect(16, 3, 17, 10), hexc("3a2414"))
    p.fill(ctx.polygon([(17, 3.5), (21, 9), (17, 9)]), CREAM, 0.8, brush=0.1)
    p.fill(ctx.polygon([(16, 4.5), (13, 9), (16, 9)]), CREAM, 0.55, brush=0.1)
    return p.tex()


@painting("painting/sunset")
def sunset(ctx):
    """Sun setting over plains, a river catching the light."""
    p = Paint(ctx)
    sky(SKY_DUSK, p, 1, 10, 0.0, 1.0)
    sun_disc(p, 20, 9.5, 2.6, P("f8c060", "ffe8a0"), halo=P("e07a5a", "f4a060"))
    p.fill(p.ridge(10, 0.8, 5, "ss"), P("2a1a2a", "3a2436", "4a2e40"), 0.5, brush=0.2)
    p.fill(ctx.y >= 11, P("2a2a1e", "3a3a24", "4e4a2c"), 0.5 - (ctx.y - 11) / 10, brush=0.3, stretch=(5, 1))
    river = (np.abs(ctx.x - 20 + (ctx.y - 11) * 2.0) < 0.6 + (ctx.y - 11) * 0.6) & (ctx.y >= 11)
    p.fill(river, P("e07a5a", "f4b26a", "fbe0a0"), 0.6 - (ctx.y - 11) / 10, brush=0.3)
    return p.tex()


# ================================================================== 16x32
@painting("painting/graham")
def graham(ctx):
    """Portrait: a tall sage in a starry blue robe."""
    p = Paint(ctx)
    sky(P("3a2a4a", "4a3a5a", "5a4a6a"), p, 1, 31, 0.8, 0.2)
    robe = ctx.polygon([(5, 12), (11, 12), (13, 30), (3, 30)])
    p.fill(robe, P("1a2250", "26306a", "3a4890", "5466b0"), 0.7 - (ctx.x - 4) / 10, brush=0.25, stretch=(1, 3))
    stars(p, 0.08, "robe", "e8d070", robe > 0)
    portrait(p, 8, 9, 2.2, SKIN, None, P("1a2250", "3a4890"), beard=P("a8a8a8", "d0d0d0", "f0f0f0"))
    p.fill(ctx.polygon([(8, 1.5), (11.5, 7.5), (4.5, 7.5)]), P("1a2250", "26306a", "3a4890"), 0.6 - (ctx.x - 6) / 8, brush=0.2)
    p.put(ctx.rect(7.5, 4, 8.5, 5), hexc("e8d070"))
    return p.tex()


@painting("painting/wanderer")
def wanderer(ctx):
    """A walker with a staff on a mountain ridge, looking up at the stars."""
    p = Paint(ctx)
    sky(SKY_NIGHT, p, 1, 22, 0.0, 1.0)
    stars(p, 0.07, "w", mask=ctx.y < 18)
    sun_disc(p, 11, 6, 1.5, P("d8dcf0", "f4f6ff"))
    p.fill(p.ridge(20, 3, 5, "wm"), P("1e2440", "2a3254", "3a4466"), 0.5 - (ctx.x - 8) / 30, brush=0.2)
    p.fill(ctx.polygon([(1, 31), (1, 25), (9, 23), (15, 27), (15, 31)]), P("141828", "1e2438", "2a3248"), 0.5, brush=0.2)
    figure(p, 8, 24, 7, P("4a2a1e", "6a3e2a", "8a5638"), hat=P("2a1a12", "3a2a1e"), staff=True)
    return p.tex()


@painting("painting/prairie_ride")
def prairie_ride(ctx):
    """A windmill standing alone on a golden prairie."""
    p = Paint(ctx)
    sky(SKY_DAY, p, 1, 20, 0.95, 0.35)
    p.fill(ctx.y >= 20, P("8a6a20", "aa8a30", "caa848", "e2c870"), 0.75 - (ctx.y - 20) / 16, brush=0.35, stretch=(1, 2), cell=1)
    p.fill(ctx.polygon([(6.5, 10), (9.5, 10), (10.5, 21), (5.5, 21)]), CREAM, 0.8 - (ctx.x > 8) * 0.35, brush=0.1)
    p.fill(ctx.polygon([(6, 10), (10, 10), (8, 7.5)]), RED, 0.5)
    for ang in (0.5, 2.07, 3.64, 5.21):
        ex, ey = 8 + np.cos(ang) * 6, 9.5 + np.sin(ang) * 6
        p.fill(ctx.segment(8, 9.5, ex, ey, 1.4), WOOD, 0.65, brush=0.1)
    p.put(ctx.rect(7.5, 9, 8.5, 10), hexc("2a1a10"))
    return p.tex()


# ================================================================== 32x32
@painting("painting/baroque")
def baroque(ctx):
    """An oval mirror in an ornate gilt frame reflecting a red rose."""
    p = Paint(ctx)
    p.fill(p.all(), P("2a1418", "3a1c20", "4a2428"), 0.5, brush=0.3, stretch=(1, 2))
    outer = ellipse(ctx, 16, 16, 12, 14)
    inner = ellipse(ctx, 16, 16, 9, 11)
    d, a = polar(ctx, 16, 16)
    scroll = 0.5 + 0.35 * np.sin(a * 10)
    p.fill(outer & ~inner, GOLD, scroll - (ctx.x - 16) / 40 - (ctx.y - 16) / 40, brush=0.2)
    p.fill(inner, P("3a4a52", "4e626a", "687e86", "8aa0a8"), 0.7 - (ctx.x + ctx.y - 20) / 40, brush=0.15, stretch=(1, 1))
    flower(p, 16, 14, 3.4, RED, "5a1014")
    p.fill(ctx.segment(16, 17, 15, 24, 1.0), LEAF, 0.5)
    p.fill(ellipse(ctx, 17.8, 20, 1.6, 0.8, 0.5), LEAF, 0.6)
    return p.tex()


@painting("painting/bust")
def bust(ctx):
    """A marble bust on a pedestal in a niche."""
    p = Paint(ctx)
    p.fill(p.all(), P("3a3040", "4a4052", "5a5066"), 0.4 + p.vgrad(0, 32, True) * 0.3, brush=0.2)
    niche = ellipse(ctx, 16, 12, 9, 10) | ctx.rect(7, 12, 25, 31)
    p.fill(niche, P("1e1a26", "2a2434", "363042"), 0.5, brush=0.15)
    marble = P("8a8a90", "a8a8ae", "c4c4ca", "dcdce0", "f0f0f2")
    p.fill(ctx.rect(11, 24, 21, 31), marble, 0.6 - (ctx.x - 11) / 14, brush=0.15)
    p.fill(ctx.rect(10, 23, 22, 25), marble, 0.8, brush=0.1)
    portrait(p, 16, 12.5, 3.6, marble, marble, marble, eyes="8a8a90", mouth="a8a8ae")
    return p.tex()


@painting("painting/earth")
def earth(ctx):
    """A planet seen from space: blue oceans, green-brown lands, white cloud swirls."""
    p = Paint(ctx)
    p.fill(p.all(), DARK, 0.3, brush=0.1)
    stars(p, 0.04, "e")
    d = np.hypot(ctx.x - 16, ctx.y - 16)
    globe = d < 12
    light = np.clip(0.95 - ((ctx.x - 10) + (ctx.y - 10)) / 26, 0, 1)
    p.fill(globe, WATER, light, brush=0.1)
    land = globe & (ctx.noise(8, 3, 0.5, salt="land") > 0.56)
    p.fill(land, P("2a3a1a", "3e5a24", "5a7a30", "8a8a46", "b0a060"), light, brush=0.2)
    cloud = globe & (ctx.noise(5, 2, 0.5, salt="clouds", stretch=(3, 1)) > 0.68)
    p.fill(cloud, P("8a96a4", "c4ccd6", "f0f4f8"), light, brush=0.1)
    p.fill(globe & (d > 11), P("4a7ac8", "8ab4f0"), 0.5, brush=0.05)
    return p.tex()


@painting("painting/fire")
def fire(ctx):
    """Campfire under a night sky, sparks rising."""
    p = Paint(ctx)
    sky(SKY_NIGHT, p, 1, 24, 0.0, 1.0)
    stars(p, 0.05, "f", mask=ctx.y < 18)
    glow = np.clip(1 - np.hypot(ctx.x - 16, ctx.y - 23) / 13, 0, 1)
    p.fill(glow > 0.3, P("2a1a2a", "4a2a2a", "6a3a26", "8a4a22"), glow, brush=0.2, stretch=(1, 1))
    p.fill(ctx.y >= 25, P("1a1410", "2a2016", "3a2c1e"), 0.3 + glow * 0.8, brush=0.3, stretch=(4, 1))
    for x1, x2 in ((11, 21), (21, 11)):
        p.fill(ctx.segment(x1, 27, x2, 24.5, 1.8), WOOD, 0.35, brush=0.2)
    fl = ctx.polygon([(16, 13), (19.5, 20), (19, 25), (13, 25), (12.5, 20), (14.5, 17)])
    p.fill(fl, P("c43a14", "e86a1a", "f4a030", "fbd860", "fff4c0"), np.clip(1 - np.hypot(ctx.x - 16, (ctx.y - 23) * 0.6) / 6, 0, 1), brush=0.2, stretch=(1, 3))
    rng = ctx.rng("sparks")
    for k in range(9):
        x, y = rng.uniform(10, 22), rng.uniform(4, 14)
        p.put(ctx.rect(np.floor(x), np.floor(y), np.floor(x) + 1, np.floor(y) + 1), hexc("f8c050"))
    return p.tex()


@painting("painting/humble")
def humble(ctx):
    """A small thatched cottage with a smoking chimney in green hills."""
    p = Paint(ctx)
    sky(SKY_DAY, p, 1, 18, 0.95, 0.3)
    p.fill(p.ridge(17, 2, 8, "hh"), P("4a6a3a", "5a7a44", "6a8a50"), 0.5, brush=0.2)
    p.fill(ctx.y >= 21, GRASS, 0.7 - (ctx.y - 21) / 16, brush=0.3, stretch=(4, 1))
    p.fill(ctx.rect(9, 16, 23, 25), CREAM, 0.75 - (ctx.x > 16) * 0.3, brush=0.15)
    p.fill(ctx.polygon([(7, 17), (25, 17), (21, 10), (11, 10)]), P("6a5020", "8a6a2a", "aa8a3c", "c8a850"), 0.7 - (ctx.x - 7) / 26, brush=0.35, stretch=(1, 2))
    p.fill(ctx.rect(19, 7, 21, 11), STONE, 0.5)
    for k, (x, y, r) in enumerate(((20.5, 5, 1.2), (22, 3.5, 1.5), (24.5, 2.5, 1.7))):
        p.fill(ctx.circle(x, y, r), P("a8acb4", "c8ccd2", "e4e6ea"), 0.6, brush=0.1)
    p.fill(ctx.rect(14, 20, 17, 25), WOOD, 0.35, brush=0.1)
    p.fill(ctx.rect(19, 19, 21.5, 21.5), P("f4c050", "fbe090"), 0.6, brush=0.05)
    p.fill(ctx.rect(10.5, 19, 13, 21.5), P("f4c050", "fbe090"), 0.6, brush=0.05)
    return p.tex()


@painting("painting/match")
def match(ctx):
    """A struck match: flame blooming against deep teal."""
    p = Paint(ctx)
    d = np.hypot(ctx.x - 16, ctx.y - 11)
    p.fill(p.all(), P("0a1e22", "12302e", "1a4440", "2a5a50", "4a7a5a"), np.clip(1 - d / 18, 0, 1), brush=0.15, stretch=(1, 1))
    p.fill(ctx.segment(16, 15, 20, 29, 1.6), P("a8844a", "c8a466", "e0c286"), 0.6, brush=0.1)
    p.fill(ellipse(ctx, 16, 15, 1.6, 2.0), P("5a1010", "8a1a14", "b42a1e"), 0.5)
    fl = ellipse(ctx, 16, 10, 3.2, 5.5)
    p.fill(fl, P("c43a14", "e86a1a", "f4a030", "fbd860", "fff8d8"), np.clip(1 - np.hypot((ctx.x - 16) / 3.2, (ctx.y - 12) / 5.5), 0, 1) * 1.2, brush=0.15, stretch=(1, 3))
    p.fill(ellipse(ctx, 16, 12.5, 1.2, 1.8), P("4a6ac8", "8aa8f0"), 0.5, brush=0.05)
    return p.tex()


@painting("painting/skull_and_roses")
def skull_and_roses(ctx):
    """Vanitas still life: roses in a pewter jug, a guttering candle and an hourglass."""
    p = Paint(ctx)
    p.fill(p.all(), P("140e10", "201618", "2e2022", "3e2c2a"), 0.3 + np.clip(1 - np.hypot(ctx.x - 10, ctx.y - 10) / 22, 0, 1) * 0.7, brush=0.15, stretch=(1, 1))
    p.fill(ctx.y >= 25, WOOD, 0.4 - (ctx.y - 25) / 20, brush=0.3, stretch=(6, 1))
    p.fill(ctx.polygon([(6, 25), (14, 25), (13, 16), (7, 16)]), STONE, 0.6 - (ctx.x - 6) / 10, brush=0.1)
    for x, y in ((8, 12), (12, 11), (10, 8), (6, 9)):
        flower(p, x, y, 2.2, RED, "5a1014")
    p.fill(ctx.segment(10, 12, 10, 16, 0.8) | ctx.segment(12, 13, 11, 16, 0.8), LEAF, 0.4)
    p.fill(ctx.rect(19, 15, 21, 25), CREAM, 0.75 - (ctx.x >= 20) * 0.3, brush=0.05)
    p.fill(ellipse(ctx, 20, 13, 0.8, 1.5), P("e07a20", "fff0b0"), 0.6)
    glass = (np.abs(ctx.x - 26) < np.abs(ctx.y - 21) * 0.8 + 0.5) & (ctx.y > 17) & (ctx.y < 25)
    p.fill(glass, P("6a7a80", "a8b8bc"), 0.5, brush=0.05)
    p.fill(glass & (ctx.y > 22), P("b49a5a", "d4ba7a"), 0.5, brush=0.05)
    p.fill(ctx.rect(23, 16, 29, 17) | ctx.rect(23, 25, 29, 26), WOOD, 0.5)
    return p.tex()


@painting("painting/stage")
def stage(ctx):
    """An empty theatre stage, red curtains, a single spotlight."""
    p = Paint(ctx)
    p.fill(p.all(), P("0e0a10", "1a141c", "2a2028"), 0.3, brush=0.15)
    beam = (np.abs(ctx.x - 16 - (ctx.y - 26) * 0.0) < (ctx.y - 2) * 0.28) & (ctx.y < 26)
    p.fill(beam, P("3a3240", "5a5060", "7a7080"), 0.4 + ctx.y / 60, brush=0.1, stretch=(1, 3))
    p.fill(ctx.y >= 24, WOOD, 0.5 - (ctx.y - 24) / 16, brush=0.25, stretch=(6, 1))
    p.fill(ellipse(ctx, 16, 25.5, 6, 1.4), P("c8b47a", "e8d8a0"), 0.6, brush=0.05)
    fold = 0.5 + 0.4 * np.sin(ctx.x * 1.6)
    left = ctx.x < 8 - np.clip(ctx.y - 6, 0, 30) * 0.12
    right = ctx.x > 24 + np.clip(ctx.y - 6, 0, 30) * 0.12
    p.fill(left | right, RED, fold, brush=0.15, stretch=(1, 4))
    p.fill(ctx.y < 5, RED, 0.4 + 0.3 * np.sin(ctx.x * 1.2), brush=0.15)
    p.fill(ctx.rect(1, 4.5, 31, 5.5), GOLD, 0.6)
    return p.tex()


@painting("painting/void")
def void(ctx):
    """A black hole bending the light of a violet nebula."""
    p = Paint(ctx)
    n = ctx.noise(10, 3, 0.55, salt="neb")
    p.fill(p.all(), P("06040c", "140c24", "2a1440", "4a2060", "7a3a8a", "b06ab0"), n ** 1.6 * 1.1, brush=0.15, stretch=(1, 1))
    stars(p, 0.05, "v")
    d, a = polar(ctx, 16, 16)
    disk = (np.abs((ctx.y - 16) - (ctx.x - 16) * 0.25) < 1.4 + 0.08 * np.abs(ctx.x - 16)) & (d < 14)
    p.fill(disk, P("8a3a1a", "c86a2a", "f4a850", "fff0c0"), np.clip(1 - d / 14, 0, 1) * 1.2, brush=0.3, stretch=(4, 1))
    p.fill(d < 6.2, P("f4a850", "fff0c0"), 0.6)
    p.put(d < 5.2, hexc("000000"))
    return p.tex()


@painting("painting/water")
def water(ctx):
    """A waterfall dropping between mossy cliffs into a pool."""
    p = Paint(ctx)
    sky(SKY_DAY, p, 1, 10, 0.9, 0.4)
    p.fill(ctx.x < 11 + np.sin(ctx.y * 0.5) * 1.5, P("2a3a2a", "3a4a34", "4a5e40", "5e7650"), 0.5, brush=0.35, stretch=(1, 2))
    p.fill(ctx.x > 21 + np.sin(ctx.y * 0.4 + 2) * 1.5, P("2a3a2a", "3a4a34", "4a5e40", "5e7650"), 0.35, brush=0.35, stretch=(1, 2))
    fall = (ctx.x >= 11 + np.sin(ctx.y * 0.5) * 1.5) & (ctx.x <= 21 + np.sin(ctx.y * 0.4 + 2) * 1.5) & (ctx.y > 4) & (ctx.y < 25)
    p.fill(fall, P("4a7aa8", "7aa4c8", "a8c8e0", "dcecf8"), 0.6 + np.sin(ctx.x * 2.1) * 0.25, brush=0.3, stretch=(1, 6))
    p.fill(ctx.y >= 25, WATER, 0.6, brush=0.3, stretch=(5, 1))
    foam = ellipse(ctx, 16, 25, 8, 2) > 0
    p.fill(foam, P("b8d4e8", "e4f0f8", "ffffff"), 0.6, brush=0.4, stretch=(1, 1), cell=1)
    return p.tex()


@painting("painting/wind")
def wind(ctx):
    """A red kite flying over windswept grass."""
    p = Paint(ctx)
    sky(SKY_DAY, p, 1, 22, 0.95, 0.2)
    for k, y in enumerate((6, 10, 15)):
        streak = (np.abs(ctx.y - y - np.sin(ctx.x * 0.3 + k) * 1.2) < 0.45) & (ctx.x > 3 + k * 4) & (ctx.x < 20 + k * 3)
        p.put(streak, hexc("e8f0f8"))
    p.fill(ctx.y >= 22, GRASS, 0.5 + np.sin(ctx.x * 1.3 + ctx.y * 0.7) * 0.3, brush=0.3, stretch=(1, 2), cell=1)
    kite = ctx.polygon([(22, 5), (26, 9), (22, 15), (18, 9)])
    p.fill(kite, RED, 0.75 - (ctx.x - 18) / 10, brush=0.1)
    p.put(ctx.segment(22, 5, 22, 15, 0.5) | ctx.segment(18, 9, 26, 9, 0.5), hexc("5a1014"))
    tail = (np.abs(ctx.x - 22 + (ctx.y - 15) * 0.6 - np.sin(ctx.y) * 1.0) < 0.5) & (ctx.y > 15) & (ctx.y < 24)
    p.put(tail, hexc("f4e0a0"))
    return p.tex()


@painting("painting/wither")
def wither(ctx):
    """Eclipse: three dark moons in a line before a blood-red corona."""
    p = Paint(ctx)
    d = np.hypot(ctx.x - 16, ctx.y - 14)
    p.fill(p.all(), P("08060a", "1a0a10", "3a1018", "6a1a1e", "a83a2a", "e8803a"), np.clip(1 - d / 15, 0, 1) ** 1.4 * 1.1, brush=0.2, stretch=(1, 1))
    for x, r in ((8, 3.2), (16, 4.4), (24, 3.2)):
        p.put(np.hypot(ctx.x - x, ctx.y - 14) < r, hexc("0a0808"))
        p.put((np.abs(np.hypot(ctx.x - x, ctx.y - 14) - r) < 0.45), hexc("f4b060"))
    p.fill(p.ridge(26, 2, 4, "wr"), P("060406", "100a0c", "1a1214"), 0.5, brush=0.2)
    return p.tex()


# ================================================================== 48x48
@painting("painting/bouquet")
def bouquet(ctx):
    """A loose bouquet of mixed flowers in a white jug."""
    p = Paint(ctx)
    p.fill(p.all(), P("4a5a6a", "5a6a7a", "6a7a88", "7a8a96"), 0.4 + p.vgrad(0, 48, True) * 0.4, brush=0.3, stretch=(1, 1))
    p.fill(ctx.y >= 38, WOOD, 0.5 - (ctx.y - 38) / 20, brush=0.3, stretch=(6, 1))
    jug = ellipse(ctx, 24, 34, 7, 8) & (ctx.y > 27)
    p.fill(jug, CREAM, 0.85 - (ctx.x - 18) / 16, brush=0.1)
    p.fill(ctx.rect(20, 25, 28, 28), CREAM, 0.6, brush=0.1)
    rng = ctx.rng("bq")
    for k in range(9):
        x, y = rng.uniform(13, 35), rng.uniform(6, 24)
        p.fill(ctx.segment(24, 27, x, y, 0.9), LEAF, 0.4)
    pals = [RED, P("6a3a8a", "8a5ab0", "b48ad8"), P("c89a1a", "e8c030", "f8e070"), P("c86a8a", "e890b0", "f8c0d4"), CREAM]
    for k in range(11):
        x, y = rng.uniform(12, 36), rng.uniform(5, 24)
        flower(p, x, y, rng.uniform(2.2, 3.8), pals[k % len(pals)], ("5a1014", "f8e070", "8a4a10")[k % 3])
    for k in range(5):
        x, y = rng.uniform(14, 34), rng.uniform(10, 26)
        p.fill(ellipse(ctx, x, y, 2.4, 1.1, rng.uniform(-1, 1)), LEAF, 0.6, brush=0.2)
    return p.tex()


@painting("painting/cavebird")
def cavebird(ctx):
    """From inside a cave: a bird flies out across a bright valley."""
    p = Paint(ctx)
    sky(SKY_DAY, p, 1, 30, 0.95, 0.3)
    p.fill(p.ridge(28, 3, 8, "cb1"), HILL_FAR, 0.5, brush=0.2)
    p.fill(p.ridge(33, 2, 6, "cb2"), GRASS, 0.5 - (ctx.y - 33) / 30, brush=0.3)
    d = np.hypot((ctx.x - 24) / 1.2, (ctx.y - 26) / 1.0) + (ctx.noise(5, 2, 0.5, salt="cave") - 0.5) * 6
    rock = d > 16
    p.fill(rock, P("141214", "201c1e", "2e2a2a", "3e3836"), np.clip((d - 16) / -14 + 0.8, 0, 1), brush=0.3, stretch=(1, 1))
    bx, by = 26, 22
    wing = ctx.segment(bx - 4, by - 2, bx, by, 1.0) | ctx.segment(bx, by, bx + 4, by - 2.5, 1.0) | ctx.circle(bx, by + 0.3, 1.0)
    p.put(wing, hexc("1e1a20"))
    return p.tex()


@painting("painting/cotan")
def cotan(ctx):
    """Portrait of a lady in a wide green hat."""
    p = Paint(ctx)
    p.fill(p.all(), P("6a5a3a", "8a7448", "a68e5a", "c0a870"), 0.3 + np.clip(1 - np.hypot(ctx.x - 30, ctx.y - 14) / 30, 0, 1) * 0.6, brush=0.3, stretch=(1, 1))
    portrait(p, 24, 22, 6.5, SKIN, P("3a2010", "5a3018", "7a4422"), P("1e4a3a", "2a6a50", "3a8a66", "5aa882"),
             hat=P("1e3a24", "2a5232", "3a6a40", "548a50"), mouth="a84a40")
    flower(p, 31, 14.5, 2.0, P("c86a8a", "e890b0", "f8c0d4"), "f8e070")
    return p.tex()


@painting("painting/dennis")
def dennis(ctx):
    """Portrait of an old fisherman with a white beard and a knit cap."""
    p = Paint(ctx)
    sky(P("4a5a6a", "5e6e7c", "74828e", "8a96a0"), p, 1, 47, 0.8, 0.2)
    sea(p, 30, P("1e3a4a", "2a4e5e", "3a6272"), "a8c0c8", "dn")
    portrait(p, 24, 22, 6.5, SKIN, P("8a8a8a", "b0b0b0", "d4d4d4"), P("6a5a20", "8a7a2a", "aa9a3a", "c8b450"),
             beard=P("9a9a9a", "c4c4c4", "e8e8e8"), mouth="6a3a30")
    cap = ellipse(ctx, 24, 15.5, 7.2, 4.5) & (ctx.y < 17)
    p.fill(cap, P("5a1414", "8a2020", "b03030"), 0.6 - (ctx.x - 18) / 20 + (ctx.ty % 2) * 0.1, brush=0.15)
    p.fill(ctx.segment(30, 30, 37, 27, 1.2), WOOD, 0.4)
    p.fill(ctx.rect(36, 25, 39, 28), WOOD, 0.55)
    return p.tex()


@painting("painting/endboss")
def endboss(ctx):
    """A great winged serpent circling dark stone pillars under a violet sky."""
    p = Paint(ctx)
    sky(P("0c0814", "1a1028", "2a1a40", "3e2a58"), p, 1, 40, 0.0, 1.0)
    stars(p, 0.03, "eb")
    sun_disc(p, 24, 15, 9, P("8a7aa8", "b0a2c8", "d4c8e4"), halo=P("2a1a40", "4a3a64"))
    for x, h in ((8, 22), (17, 30), (31, 26), (40, 18)):
        p.fill(ctx.rect(x - 2, 47 - h, x + 2, 47), P("0e0a14", "1a1424", "2a2236"), 0.4 + (ctx.x < x) * 0.3, brush=0.2, stretch=(1, 4))
        p.put(ctx.rect(x - 1, 47 - h - 1.5, x + 1, 47 - h), hexc("e0b0ff"))
    p.fill(ctx.y >= 42, P("c8c290", "d8d2a0", "e8e2b4"), 0.5, brush=0.3, stretch=(4, 1))
    t = np.linspace(0, 1, 40)
    body = ctx.zeros()
    for k in range(len(t) - 1):
        x1, y1 = 8 + t[k] * 32, 14 + np.sin(t[k] * 7) * 4
        x2, y2 = 8 + t[k + 1] * 32, 14 + np.sin(t[k + 1] * 7) * 4
        body = np.maximum(body, ctx.segment(x1, y1, x2, y2, 2.6 - t[k] * 1.6))
    for wx in (18, 28):
        p.put(ctx.polygon([(wx, 13), (wx + 6, 4), (wx + 3, 12), (wx + 8, 9), (wx + 3, 15)]), hexc("140e1a"))
    p.put(body > 0, hexc("1a1222"))
    p.put((body > 0) & (ctx.real.edge(body, 1.0, "tl") > 0), hexc("4a3a5a"))
    p.put(ctx.rect(7, 13, 8, 14), hexc("e070ff"))
    return p.tex()


@painting("painting/fern")
def fern(ctx):
    """Botanical study of a fern frond on aged paper."""
    p = Paint(ctx)
    p.fill(p.all(), P("a89a74", "bcae88", "cec09a", "ddd0ac"), 0.6 + (ctx.noise(12, 2, 0.5, salt="paper") - 0.5) * 0.6, brush=0.15, stretch=(1, 1))
    stem = lambda y: 24 + np.sin((y - 6) / 40 * 2.2) * 6
    for y in np.arange(6, 44, 0.5):
        p.put(ctx.circle(stem(y), y, 0.55), hexc("3a4a22"))
    for k, y in enumerate(np.arange(9, 42, 2.6)):
        ln = 9 * np.sin((y - 6) / 38 * np.pi) + 1
        for side in (-1, 1):
            x0 = stem(y)
            for j in np.arange(0.8, ln, 0.9):
                lx, ly = x0 + side * j, y - j * 0.35
                p.fill(ellipse(ctx, lx, ly, 0.6, 1.1, side * 0.5), LEAF, 0.6 - j / ln * 0.3 + (side > 0) * 0.15, brush=0.1)
    p.put(ctx.rect(30, 42, 40, 43), hexc("6a5a40"))
    return p.tex()


@painting("painting/owlemons")
def owlemons(ctx):
    """An owl perched on a branch beside a bowl of lemons."""
    p = Paint(ctx)
    p.fill(p.all(), P("1e2a3a", "2a3a4e", "3a4c62"), 0.4 + p.vgrad(0, 48) * 0.3, brush=0.3, stretch=(1, 1))
    p.fill(ctx.segment(2, 30, 46, 27, 2.4), WOOD, 0.4, brush=0.2)
    owl = ellipse(ctx, 16, 20, 7, 9.5)
    p.fill(owl, P("4a3420", "6a4c2e", "8a6a42", "aa8a5c", "c8a878"), 0.65 - (ctx.x - 10) / 18 + np.sin(ctx.y * 1.4) * 0.08, brush=0.25, stretch=(1, 1), cell=1)
    p.fill(ellipse(ctx, 16, 23, 4.5, 5.5), CREAM, 0.5 + (ctx.ty % 2) * 0.15, brush=0.15)
    for ex in (13, 19):
        p.put(ctx.circle(ex, 16, 2.4), hexc("e8b030"))
        p.put(ctx.circle(ex, 16, 1.1), hexc("140c08"))
    p.put(ctx.polygon([(15, 18), (17, 18), (16, 20.5)]), hexc("c88a2a"))
    p.put(ctx.polygon([(10, 11), (12.5, 13), (10.5, 8)]) | ctx.polygon([(22, 11), (19.5, 13), (21.5, 8)]), hexc("4a3420"))
    p.fill(ellipse(ctx, 34, 38, 9, 4) & (ctx.y > 36), P("6a3a2a", "8a4e36", "aa6448"), 0.5, brush=0.2)
    for x, y in ((30, 34.5), (35, 33.5), (39, 35), (33, 31)):
        p.fill(ellipse(ctx, x, y, 2.8, 2.1, 0.3), P("a88a10", "d4b420", "f0d840", "fbf09a"), 0.7 - (ctx.x - x + ctx.y - y) / 6, brush=0.1)
    return p.tex()


@painting("painting/sunflowers")
def sunflowers(ctx):
    """A field of sunflowers turned toward a summer sky."""
    p = Paint(ctx)
    sky(SKY_DAY, p, 1, 26, 0.95, 0.35)
    p.fill(p.ridge(25, 1.5, 6, "sf"), HILL_FAR, 0.5)
    p.fill(ctx.y >= 26, LEAF, 0.45 + np.sin(ctx.x * 1.1 + ctx.y * 0.8) * 0.2, brush=0.35, stretch=(1, 1), cell=1)
    rng = ctx.rng("sfl")
    heads = sorted([(rng.uniform(3, 45), rng.uniform(22, 44)) for _ in range(13)], key=lambda q: q[1])
    for x, y in heads:
        r = 1.6 + (y - 20) / 9
        p.fill(ctx.rect(x - 0.5, y, x + 0.5, 48), LEAF, 0.35)
        flower(p, x, y, r, P("a87010", "d8a018", "f4c830", "fbe070"), "4a2a10")
    return p.tex()


@painting("painting/tides")
def tides(ctx):
    """Abstract: interlocking rings of tide water, ochre sand and foam."""
    p = Paint(ctx)
    d1 = np.hypot(ctx.x - 14, ctx.y - 16)
    d2 = np.hypot(ctx.x - 34, ctx.y - 34)
    v = np.sin(d1 * 0.8) + np.sin(d2 * 0.8)
    p.fill(v > 0.5, WATER, 0.5 + v * 0.2, brush=0.25, stretch=(1, 1))
    p.fill((v <= 0.5) & (v > -0.6), P("a8885a", "c4a470", "dcc08a", "eedaa8"), 0.6 + v * 0.3, brush=0.25)
    p.fill(v <= -0.6, P("1e2e4a", "26385a"), 0.5, brush=0.25)
    p.put(np.abs(v - 0.5) < 0.12, hexc("f0f4f6"))
    return p.tex()


# ================================================================== 48x64
@painting("painting/backyard")
def backyard(ctx):
    """A garden: picket fence, apple tree, laundry line and a sleeping cat."""
    p = Paint(ctx)
    sky(SKY_DAY, p, 1, 34, 0.95, 0.3)
    p.fill(p.ridge(33, 2, 10, "by"), HILL_FAR, 0.5)
    p.fill(ctx.y >= 36, GRASS, 0.7 - (ctx.y - 36) / 40, brush=0.35, stretch=(1, 1), cell=1)
    crown = tree(p, 14, 46, 32, 10, salt="by")
    rng = ctx.rng("apples")
    for k in range(9):
        ax, ay = rng.uniform(6, 22), rng.uniform(20, 34)
        p.put((ctx.circle(ax, ay, 0.9) > 0) & (crown > 0), hexc("c42a20"))
    fence = ((ctx.tx % 4) < 2) & (ctx.y > 38) & (ctx.y < 46) & ~((ctx.tx % 4 < 2) & (ctx.y < 39 + np.abs((ctx.x % 4) - 1) * 1.0))
    fence |= ctx.rect(1, 40, 47, 41) > 0
    fence |= ctx.rect(1, 44, 47, 45) > 0
    p.fill(fence & (ctx.x > 24), CREAM, 0.8 - ((ctx.tx % 4) == 1) * 0.3, brush=0.05)
    line = np.abs(ctx.y - 22 - ((ctx.x - 30) / 16) ** 2 * 3) < 0.4
    p.put(line & (ctx.x > 26) & (ctx.x < 46), hexc("4a4a4a"))
    for x, pc in ((30, RED), (36, P("2a4a8a", "4a6ab0")), (41, CREAM)):
        p.fill(ctx.rect(x, 23, x + 4, 29), pc, 0.6, brush=0.15)
    p.fill(ellipse(ctx, 34, 52, 4, 2), P("3a3a3a", "5a5a5a", "7a7a7a"), 0.6, brush=0.1)
    p.fill(ctx.circle(37.5, 50.8, 1.6), P("3a3a3a", "6a6a6a"), 0.6)
    return p.tex()


@painting("painting/pond")
def pond(ctx):
    """Koi pond seen from above: orange and white fish among pebbles and pads."""
    p = Paint(ctx)
    p.fill(p.all(), STONE, 0.5, brush=0.4, stretch=(1, 1), cell=1)
    d = np.hypot((ctx.x - 24) / 20, (ctx.y - 32) / 27) + (ctx.noise(8, 2, 0.5, salt="pond") - 0.5) * 0.15
    water = d < 1
    p.fill(water, P("0e2a2a", "143838", "1e4a46", "2a5e56"), 0.3 + (1 - d) * 0.6, brush=0.3, stretch=(1, 1))
    rng = ctx.rng("koi")
    for k in range(6):
        x, y = rng.uniform(10, 38), rng.uniform(10, 54)
        ang = rng.uniform(0, np.pi * 2)
        body = ellipse(ctx, x, y, 3.2, 1.3, ang)
        tx, ty = x - np.cos(ang) * 3.8, y - np.sin(ang) * 3.8
        tail = ellipse(ctx, tx, ty, 1.2, 1.4, ang)
        m = (body | tail) & water
        p.fill(m, P("c84a10", "e8701a", "f49a40", "fbd0a0") if k % 3 else CREAM, 0.6 + (ctx.noise(1, 1, 0.5, salt=f"k{k}") - 0.5) * 0.8, brush=0.1)
    for k in range(5):
        x, y = rng.uniform(6, 42), rng.uniform(6, 58)
        pad = (ctx.circle(x, y, 2.6) > 0) & water
        p.fill(pad, LEAF, 0.6, brush=0.2)
    return p.tex()


# ================================================================== 64x32
@painting("painting/changing")
def changing(ctx):
    """One tree through four seasons, panel by panel."""
    p = Paint(ctx)
    skies = [P("8ab4d8", "a8c8e4", "c8dcf0"), SKY_DAY, P("c89a6a", "d8b48a", "e8cca8"), P("8a94a4", "a4acb8", "c4cad2")]
    grounds = [GRASS, GRASS, P("6a5a2a", "8a7238", "aa8a48"), P("c8d0d8", "dce2e8", "f0f4f8")]
    leaves = [P("6aa040", "8ac060", "f0b0c8"), LEAF, P("8a3010", "c4561a", "e88a2a", "f4c040"), None]
    for i in range(4):
        x0 = i * 16
        m = (ctx.x >= x0) & (ctx.x < x0 + 16)
        t = p.vgrad(1, 22)
        p.fill(m, skies[i], 0.9 - t * 0.6, brush=0.12, stretch=(6, 1))
        p.fill(m & (ctx.y >= 23), grounds[i], 0.5, brush=0.3)
        p.fill(m & (ctx.rect(x0 + 7, 13, x0 + 9, 24) > 0), WOOD, 0.4 + (ctx.x < x0 + 8) * 0.2, brush=0.1)
        p.fill(m & (ctx.segment(x0 + 8, 15, x0 + 4, 10, 1) > 0) | m & (ctx.segment(x0 + 8, 14, x0 + 12, 9, 1) > 0), WOOD, 0.4)
        if leaves[i] is not None:
            cr = ellipse(ctx, x0 + 8, 10, 5.5, 4.5) & (ctx.noise(1.5, 2, 0.5, salt=f"ch{i}") > (0.35 if i < 2 else 0.5))
            p.fill(m & cr, leaves[i], 0.6 - (ctx.y - 6) / 12, brush=0.4, stretch=(1, 1), cell=1)
        else:
            stars(p, 0.08, "snow", "ffffff", m & (ctx.y < 23))
        p.put(m & (np.abs(ctx.x - x0 - 15.5) < 0.5) & (i < 3), hexc("2a1a10"))
    return p.tex()


@painting("painting/fighters")
def fighters(ctx):
    """Two knights crossing swords on a hilltop at sunrise."""
    p = Paint(ctx)
    sky(SKY_DUSK, p, 1, 24, 0.15, 1.0)
    sun_disc(p, 32, 22, 5, P("f8c060", "ffe8a0"), halo=P("e07a5a", "f4a060"))
    p.fill(p.ridge(24, 1.5, 10, "fg"), P("1a1218", "241a22", "30242c"), 0.5, brush=0.2)
    for x, sgn, col in ((26, 1, "201820"), (38, -1, "1a1418")):
        body = ctx.polygon([(x - 2.5, 13), (x + 2.5, 13), (x + 3, 23), (x - 3, 23)])
        p.put(body, hexc(col))
        p.put(ctx.circle(x, 10.5, 2.4), hexc(col))
        p.put(ctx.rect(x - 0.5, 6, x + 0.5, 8.5), hexc("8a1a1a"))
        p.put(ctx.segment(x + sgn * 2, 15, x + sgn * 8, 7, 0.9), hexc("d8dce4"))
        p.put(ctx.polygon([(x - sgn * 2, 14), (x - sgn * 6, 15), (x - sgn * 6, 20), (x - sgn * 3, 22)]), hexc(col))
    return p.tex()


@painting("painting/finding")
def finding(ctx):
    """An explorer with a lantern discovering a glittering gem seam in a cave."""
    p = Paint(ctx)
    lx, ly = 20, 16
    glow = np.clip(1 - np.hypot((ctx.x - lx) / 1.4, ctx.y - ly) / 26, 0, 1)
    p.fill(p.all(), P("0a080a", "16121a", "241e26", "3a3032", "54463e"), glow * 1.1, brush=0.35, stretch=(1, 1), cell=1.5)
    seam = (np.abs(ctx.y - 12 - (ctx.x - 40) * 0.25 - np.sin(ctx.x * 0.4) * 2) < 1.6) & (ctx.x > 34)
    p.fill(seam, P("1a3a5a", "2a6a9a", "4aa8d8", "a8f0ff"), 0.4 + ctx.texel_noise("gems") * 0.6, brush=0.0)
    gems = (ctx.texel_noise("gems2", soft=False) > 0.9) & seam
    p.put(gems, hexc("e8ffff"))
    figure(p, 22, 28, 13, P("4a3a20", "6a5430", "8a6e40"), hat=P("4a2e1a", "6a4428"))
    p.fill(ctx.circle(lx + 6, ly + 2, 1.6), P("f4b040", "fff0b0"), 0.6, brush=0.05)
    p.fill(ctx.y >= 28, P("141014", "221c20", "322a2a"), 0.3 + glow * 0.5, brush=0.3, stretch=(4, 1))
    return p.tex()


@painting("painting/lowmist")
def lowmist(ctx):
    """Pine forest in a valley half-drowned in morning mist."""
    p = Paint(ctx)
    sky(P("a8b8c4", "bcc8d2", "d0d8e0", "e4eaee"), p, 1, 31, 0.3, 1.0)
    p.fill(p.ridge(14, 4, 12, "lm1"), P("6a7a86", "7a8894", "8a96a0"), 0.5, brush=0.2)
    rng = ctx.rng("pines")
    for row, (y0, pc, n) in enumerate(((22, P("4a5a5a", "5a6a6a", "6a7a7a"), 14), (29, P("1e2e26", "2a3e32", "3a5040"), 10))):
        for k in range(n):
            pine(p, rng.uniform(1, 63), y0 + rng.uniform(-1, 2), rng.uniform(7, 11) + row * 3, pc)
        mist = (ctx.y > y0 - 3) & (ctx.noise(6, 2, 0.5, salt=f"mist{row}", stretch=(4, 1)) > 0.45 - (ctx.y - y0 + 3) * 0.05)
        p.fill(mist & (ctx.y < y0 + 2), P("c8d2da", "dce4ea", "eef2f4"), 0.6, brush=0.2, stretch=(6, 1))
    return p.tex()


@painting("painting/passage")
def passage(ctx):
    """A stone archway opening onto a bright meadow beyond a dark corridor."""
    p = Paint(ctx)
    p.fill(p.all(), STONE, 0.35, brush=0.3)
    blocks = ((ctx.tx + (ctx.ty // 3 % 2) * 3) % 6 == 0) | (ctx.ty % 3 == 0)
    p.fill(blocks, STONE, 0.15, brush=0.1)
    d = np.hypot((ctx.x - 32) / 1.0, ctx.y - 16)
    hole = (d < 10) | ((np.abs(ctx.x - 32) < 10) & (ctx.y > 16))
    p.fill(hole, P("0e0c10", "1a161c", "26222a"), 0.4, brush=0.2)
    far = (np.hypot(ctx.x - 32, ctx.y - 20) < 4.5) | ((np.abs(ctx.x - 32) < 4.5) & (ctx.y > 20))
    p.fill(far & (ctx.y < 24), SKY_DAY, 0.8, brush=0.1)
    p.fill(far & (ctx.y >= 24), GRASS, 0.8, brush=0.2)
    floor = hole & (ctx.y > 24) & ~far
    p.fill(floor, P("1a161c", "2a2630", "3e3a44"), (ctx.y - 24) / 8 * 0.6 + 0.2 + (np.abs(ctx.x - 32) < 4) * 0.3, brush=0.2)
    p.fill(np.abs(d - 10.5) < 1.0, STONE, 0.75, brush=0.1)
    return p.tex()


# ================================================================== 64x48
@painting("painting/donkey_kong")
def donkey_kong(ctx):
    """A cliff-top castle at dawn, a winding road and a banner in the wind."""
    p = Paint(ctx)
    sky(SKY_DUSK, p, 1, 34, 0.2, 1.0)
    p.fill(p.ridge(30, 3, 10, "dk1"), P("4a3a5a", "5a4a6a", "6a5a78"), 0.5, brush=0.2)
    cliff = ctx.polygon([(30, 22), (54, 20), (60, 47), (22, 47)])
    p.fill(cliff, STONE, 0.6 - (ctx.x - 30) / 50 - (ctx.y - 22) / 60, brush=0.3, stretch=(1, 2))
    castle = ctx.rect(34, 10, 52, 22) > 0
    for x in (32, 50):
        castle |= ctx.rect(x, 5, x + 5, 22) > 0
    crenel = (ctx.y < 11) & (ctx.y >= 9.5) & (ctx.tx % 2 == 0) & (ctx.x > 34) & (ctx.x < 50)
    p.fill(castle | crenel, P("6a5e6a", "8a7e86", "a89ca2", "c4b8bc"), 0.7 - (ctx.x - 32) / 40, brush=0.15)
    for x in (32, 50):
        p.fill(ctx.polygon([(x - 0.5, 5), (x + 5.5, 5), (x + 2.5, 0.5)]), P("3a2a5a", "5a3a7a"), 0.5)
    for wx, wy in ((38, 14), (44, 14), (34, 9), (52, 9)):
        p.put(ctx.rect(wx, wy, wx + 1.5, wy + 2.5), hexc("f8d070"))
    p.put(ctx.rect(42.5, 1, 43, 10), hexc("2a2a2a"))
    flag = (ctx.x > 43) & (ctx.x < 49) & (np.abs(ctx.y - 3 - np.sin(ctx.x * 0.9) * 0.6) < 1.5)
    p.fill(flag, RED, 0.6)
    p.fill(ctx.y >= 38, GRASS, 0.4, brush=0.3)
    road = np.abs(ctx.x - 20 - np.sin(ctx.y * 0.35) * 6) < 1.2 + (ctx.y - 30) * 0.08
    p.fill(road & (ctx.y > 30), P("8a7050", "a68a64", "c4a87e"), 0.5, brush=0.2)
    return p.tex()


@painting("painting/skeleton")
def skeleton(ctx):
    """A fossil in layered rock: the curled skeleton of a long-necked beast."""
    p = Paint(ctx)
    bands = np.floor((ctx.y + ctx.noise(10, 2, 0.5, salt="strata") * 6) / 6) % 4
    pals = [P("5a4232", "6a4e3a"), P("7a5e44", "8a6c50"), P("4a3628", "5a4232"), P("846a52", "94785e")]
    for k in range(4):
        p.fill(bands == k, pals[k], 0.5, brush=0.4, stretch=(5, 1))
    bone = P("c8bca0", "e0d6bc", "f4eedc")
    d, a = polar(ctx, 32, 26)
    spine_r = 8 + (a + np.pi) * 2.2
    spine = (np.abs(d - spine_r) < 1.0) & (spine_r < 20)
    p.fill(spine, bone, 0.6, brush=0.1)
    ribs = (np.abs(d - spine_r + 2.2) < 2.2) & (np.abs(np.sin(a * 9)) < 0.2) & (a > -0.5) & (a < 1.8)
    p.fill(ribs, bone, 0.45, brush=0.1)
    p.fill(ellipse(ctx, 52, 14, 3.8, 2.2, -0.3), bone, 0.7, brush=0.1)
    p.fill(ctx.segment(48.5, 15.5, 44, 17.5, 1.6), bone, 0.6, brush=0.1)
    p.put(ctx.circle(53, 13.5, 0.8), hexc("4a3a2a"))
    for lx in (26, 36):
        p.fill(ctx.segment(lx, 30, lx - 2, 40, 1.2) | ctx.segment(lx - 2, 40, lx + 1, 43, 1.0), bone, 0.5)
    return p.tex()


# ================================================================== 64x64
@painting("painting/burning_skull")
def burning_skull(ctx):
    """A blazing comet streaking over snowy peaks."""
    p = Paint(ctx)
    sky(SKY_NIGHT, p, 1, 50, 0.0, 1.0)
    stars(p, 0.03, "bs", mask=ctx.y < 36)
    cx, cy = 44, 18
    dx, dy = ctx.x - cx, ctx.y - cy
    along = -(dx * 0.8 + dy * 0.6)
    across = np.abs(dx * 0.6 - dy * 0.8)
    tail = (along > 0) & (across < 1.5 + along * 0.22) & (along < 40)
    p.fill(tail, P("2a3a6a", "4a5aa0", "8a7ad0", "d0a0e0", "fff0f0"), np.clip(1 - along / 40 - across / 12, 0, 1), brush=0.3, stretch=(3, 1))
    p.fill(ctx.circle(cx, cy, 3.6), P("f4a040", "fbd870", "fffbe0"), np.clip(1 - np.hypot(dx, dy) / 3.6, 0, 1) + 0.3, brush=0.05)
    peaks = p.ridge(46, 9, 9, "bsk")
    p.fill(peaks, P("1a2030", "2a3248", "3a4660", "4e5c78"), 0.5 - (ctx.x - 32) / 80, brush=0.25, stretch=(1, 2))
    snow = peaks & ~p.ridge(49, 9, 9, "bsk") & (ctx.y < 44)
    p.fill(snow, P("a8b4c8", "d0dae8", "f0f4fa"), 0.6, brush=0.1)
    p.fill(ctx.y >= 56, P("101420", "1a2030"), 0.5, brush=0.2)
    return p.tex()


@painting("painting/orb")
def orb(ctx):
    """A crystal orb on a brass stand, mist swirling inside."""
    p = Paint(ctx)
    d0 = np.hypot(ctx.x - 32, ctx.y - 28)
    p.fill(p.all(), P("0a0812", "160f22", "241838", "34224e"), np.clip(1 - d0 / 40, 0, 1), brush=0.2, stretch=(1, 1))
    p.fill(ctx.y >= 50, P("2a1420", "3e1c2c", "52263a"), 0.4, brush=0.3, stretch=(5, 1))
    p.fill(ctx.polygon([(22, 52), (42, 52), (38, 44), (26, 44)]), GOLD, 0.6 - (ctx.x - 24) / 30, brush=0.15)
    globe = d0 < 16
    _, a = polar(ctx, 32, 28)
    swirl = 0.5 + 0.5 * np.sin(a * 2 + d0 * 0.5 + ctx.noise(6, 2, 0.5, salt="orbmist") * 4)
    p.fill(globe, P("1e2a5a", "3a4a8a", "6a6ab8", "a890d8", "e0d0f8"), swirl * (1 - d0 / 20) + 0.15, brush=0.2, stretch=(1, 1))
    p.put(np.abs(d0 - 15.6) < 0.5, hexc("8a7ac8"))
    p.fill(ellipse(ctx, 26, 21, 3, 2, -0.6), P("e8e0ff", "ffffff"), 0.6, brush=0.05)
    return p.tex()


@painting("painting/pigscene")
def pigscene(ctx):
    """Farmyard: a red barn, a muddy pen and three pink pigs."""
    p = Paint(ctx)
    sky(SKY_DAY, p, 1, 30, 0.95, 0.3)
    p.fill(p.ridge(28, 3, 12, "pg"), HILL_FAR, 0.5)
    p.fill(ctx.y >= 32, GRASS, 0.65 - (ctx.y - 32) / 50, brush=0.3, stretch=(3, 1))
    p.fill(ctx.rect(36, 16, 60, 34), RED, 0.6 - (ctx.x > 48) * 0.25 + ((ctx.tx % 3) == 0) * -0.1, brush=0.1, stretch=(1, 3))
    p.fill(ctx.polygon([(34, 17), (62, 17), (48, 6)]), P("3a2a2a", "4e3a36", "6a4e48"), 0.5 - (ctx.x - 34) / 60, brush=0.2)
    p.fill(ctx.rect(44, 23, 52, 34), P("3a1a14", "5a2a20"), 0.5)
    p.put(ctx.segment(44, 23, 52, 34, 0.8) | ctx.segment(52, 23, 44, 34, 0.8), hexc("e8dcc4"))
    mud = ellipse(ctx, 22, 50, 18, 7)
    p.fill(mud, P("3a2414", "4e321c", "644226", "7a5232"), 0.5, brush=0.4, stretch=(4, 1))
    pig = P("a85a64", "c87a84", "e09aa2", "f4bcc2")
    for x, y, s in ((14, 46, 1.0), (26, 50, 1.1), (36, 44, 0.85)):
        p.fill(ellipse(ctx, x, y, 4.5 * s, 2.8 * s), pig, 0.7 - (ctx.x - x) / 12 - (ctx.y - y) / 10, brush=0.1)
        p.fill(ctx.circle(x + 4.5 * s, y - 1 * s, 2.0 * s), pig, 0.7, brush=0.1)
        p.put(ctx.rect(x + 5.5 * s, y - 1 * s, x + 6.7 * s, y), hexc("8a4650"))
        for lx in (-2.5, 2.5):
            p.put(ctx.rect(x + lx * s - 0.6, y + 2.4 * s, x + lx * s + 0.6, y + 4 * s), hexc("a85a64"))
    fence = (ctx.y > 38) & (ctx.y < 40) | ((ctx.tx % 6 == 0) & (ctx.y > 36) & (ctx.y < 44))
    p.fill(fence & (ctx.x < 34), WOOD, 0.6, brush=0.1)
    return p.tex()


@painting("painting/pointer")
def pointer(ctx):
    """An old treasure map: coastlines, a dotted trail and a compass rose."""
    p = Paint(ctx)
    paper = P("8a7448", "a68e5a", "c0a870", "d6c08a", "e8d6a6")
    p.fill(p.all(), paper, 0.65 + (ctx.noise(10, 3, 0.5, salt="map") - 0.5) * 0.6, brush=0.2, stretch=(1, 1))
    land = ctx.noise(14, 3, 0.5, salt="island") > 0.52
    coast = land & ~(ctx.noise(14, 3, 0.5, salt="island") > 0.56)
    sea_m = ~land
    p.fill(sea_m, P("5a7a7a", "7a9a90", "9ab4a4"), 0.5, brush=0.3, stretch=(4, 1))
    p.put(coast, hexc("4a3420"))
    trail = ctx.zeros() > 1
    pts = [(10, 50), (20, 44), (28, 46), (34, 36), (44, 30), (50, 22)]
    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        trail |= (ctx.segment(x1, y1, x2, y2, 1.0) > 0)
    trail &= ((ctx.tx + ctx.ty) % 3 != 0)
    p.put(trail, hexc("8a1a14"))
    x0, y0 = 50, 22
    p.put(ctx.segment(x0 - 2, y0 - 2, x0 + 2, y0 + 2, 1.2) | ctx.segment(x0 - 2, y0 + 2, x0 + 2, y0 - 2, 1.2), hexc("b42a1e"))
    cx, cy = 14, 14
    du, dv = np.abs(ctx.x - cx), np.abs(ctx.y - cy)
    rose = (du * 3.5 + dv < 8) | (dv * 3.5 + du < 8)
    p.fill(rose, P("4a3420", "6a4c2e", "8a6a42"), 0.4 + (ctx.x < cx) * 0.3, brush=0.05)
    p.put(np.abs(np.hypot(ctx.x - cx, ctx.y - cy) - 5.5) < 0.4, hexc("4a3420"))
    return p.tex()


@painting("painting/unpacked")
def unpacked(ctx):
    """Still life: an opened crate spilling apples, a bottle, a book and a candle."""
    p = Paint(ctx)
    p.fill(p.all(), P("2a2024", "3a2c2e", "4a3a3a", "5e4a46"), 0.3 + np.clip(1 - np.hypot(ctx.x - 20, ctx.y - 16) / 50, 0, 1) * 0.7, brush=0.2, stretch=(1, 1))
    p.fill(ctx.y >= 44, WOOD, 0.45 - (ctx.y - 44) / 40, brush=0.3, stretch=(6, 1))
    crate = ctx.rect(8, 28, 34, 48) > 0
    p.fill(crate, WOOD, 0.55 - ((ctx.ty % 5) == 0) * 0.3 - (ctx.x - 8) / 60, brush=0.2, stretch=(4, 1))
    p.fill(ctx.polygon([(8, 28), (34, 28), (38, 20), (12, 22)]), WOOD, 0.7, brush=0.2, stretch=(4, 1))
    for x, y in ((14, 26), (19, 25.5), (24, 26.5), (29, 25), (36, 50), (41, 52)):
        p.fill(ctx.circle(x, y, 2.6), RED, 0.75 - ((ctx.x - x) + (ctx.y - y)) / 7, brush=0.1)
    bottle = ctx.rect(42, 26, 48, 46) | ctx.rect(44, 19, 46, 26)
    p.fill(bottle, P("1a3a2a", "2a5a3a", "3a7a4e", "6aa87a"), 0.6 - (ctx.x - 42) / 8, brush=0.1, stretch=(1, 3))
    p.fill(ctx.rect(50, 40, 60, 46), P("2a2a5a", "3a3a7a", "4e4e9a"), 0.5, brush=0.1)
    p.fill(ctx.rect(50, 39, 60, 40), CREAM, 0.8)
    p.fill(ctx.rect(54, 30, 56, 39), CREAM, 0.75 - (ctx.x >= 55) * 0.3, brush=0.05)
    p.fill(ellipse(ctx, 55, 28, 0.9, 1.6), P("e07a20", "fff0b0"), 0.6)
    return p.tex()


# ================================================================== back
@painting("painting/back")
def back(ctx):
    """Back of a canvas: plain boards with a cross brace and nails."""
    p = Paint(ctx)
    board = P("5a4028", "6a4c30", "7a583a", "8a6644", "9a744e")
    v = 0.5 + (ctx.noise(4, 2, 0.5, salt="grain", stretch=(1, 4)) - 0.5) * 0.6
    p.fill(p.all(), board, v + ((ctx.tx % 4) == 3) * -0.35, brush=0.2, stretch=(1, 4))
    p.fill(ctx.rect(0, 7, 16, 9), board, 0.75, brush=0.15, stretch=(4, 1))
    p.put(ctx.rect(0, 9, 16, 10), board[0])
    for x in (2, 13):
        p.put(ctx.rect(x, 7, x + 1, 8), hexc("3a3a40"))
    return p.tex(frame=False)
