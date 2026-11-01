"""Armor trims: palette key, material palettes and the pattern overlays.

The game swaps colors through a palette: every pixel of a trim pattern whose
color equals key[i] (palettes/trim_base) is replaced with material[i]. So the
patterns below are painted with the 8 exact key colors only, at every
resolution (no blending, no micro grain), and the palettes stay 8x1.

Key order used throughout: index 0 = brightest highlight ... 7 = deepest shadow.
"""
import numpy as np

from ...engine import Tex
from ...registry import register
from .common import native

KEY = np.array([0xEC, 0xCE, 0xB2, 0x96, 0x7C, 0x63, 0x4C, 0x36], np.float32) / 255


def _hex(c):
    return np.array([int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def _ramp(*stops):
    """8 colors (light -> dark) interpolated through the given hex stops."""
    s = np.stack([_hex(c) for c in stops])
    t = np.linspace(0, len(s) - 1, 8)
    i0 = np.floor(t).astype(int).clip(0, len(s) - 2)
    f = (t - i0)[:, None]
    return s[i0] * (1 - f) + s[i0 + 1] * f


MATERIALS = {
    "amethyst": _ramp("f4e2ff", "c69cf0", "9a64d4", "6e3ca6", "3e1f66"),
    "copper": _ramp("ffd8bc", "eea078", "cc6e44", "9a4626", "5a2612"),
    "copper_darker": _ramp("e6a582", "c4704a", "9c4c2a", "6e3018", "3e1a0c"),
    "diamond": _ramp("e6fffc", "9af3ea", "48d2c8", "1c968e", "0c524e"),
    "diamond_darker": _ramp("a8eee6", "56c9be", "22988e", "126660", "083a36"),
    "emerald": _ramp("d8ffe6", "78f0a8", "22c264", "128a42", "084c24"),
    "gold": _ramp("fff8c4", "fbe06a", "e8b62c", "b0800e", "6a4806"),
    "gold_darker": _ramp("f6dc78", "dcae2e", "b07e10", "7a540a", "443004"),
    "iron": _ramp("ffffff", "e2e2e8", "bcbcc4", "8c8c94", "50505a"),
    "iron_darker": _ramp("d8d8de", "aeaeb6", "84848c", "5c5c64", "34343c"),
    "lapis": _ramp("c6d6ff", "7a9ef4", "3a66d8", "1e3ca2", "0e1c5e"),
    "netherite": _ramp("8e8084", "665a5e", "4a4044", "322a2e", "1a1517"),
    "netherite_darker": _ramp("6a5e62", "4c4246", "342d30", "221d1f", "120f10"),
    "quartz": _ramp("fffef8", "f2ede4", "ddd4c6", "bdb0a0", "8a7e70"),
    "redstone": _ramp("ffb4a4", "f45040", "c81e1e", "8c0e0e", "4c0606"),
    "resin": _ramp("ffd890", "f8a830", "dc7a10", "a25008", "5c2a04"),
}


def _palette(colors):
    @native
    def gen(ctx):
        c = np.asarray(colors, np.float32)[np.clip(ctx.tx, 0, 7)]
        return Tex(ctx, c, wrap=True, grain=0)
    return gen


register("palettes/trim_base", _palette(np.repeat(KEY[:, None], 3, 1)))
for _name, _cols in MATERIALS.items():
    register(f"palettes/trim/{_name}", _palette(_cols))


# ------------------------------------------------------------------ armor layout
# (part, face, x0, y0, w, h) on the 64x32 humanoid armor sheet.
HEAD = [("head", f, x, y, 8, 8) for f, x, y in
        (("top", 8, 0), ("right", 0, 8), ("front", 8, 8), ("left", 16, 8), ("back", 24, 8))]
BODY = [("body", "top", 20, 16, 8, 4), ("body", "front", 20, 20, 8, 12), ("body", "back", 32, 20, 8, 12),
        ("body", "right", 16, 20, 4, 12), ("body", "left", 28, 20, 4, 12)]
ARM = [("arm", "top", 44, 16, 4, 4), ("arm", "outer", 40, 20, 4, 12), ("arm", "front", 44, 20, 4, 12),
       ("arm", "inner", 48, 20, 4, 12), ("arm", "back", 52, 20, 4, 12)]
LEG = [("leg", "outer", 0, 20, 4, 12), ("leg", "front", 4, 20, 4, 12), ("leg", "inner", 8, 20, 4, 12),
       ("leg", "back", 12, 20, 4, 12)]

# Vertical band of each part a trim may use (keeps trims on the armored area).
LAYER1 = dict(head=(0, 8), body=(0, 12), arm=(0, 6), leg=(7, 12))     # helmet, chestplate, boots
LAYER2 = dict(body=(8, 12), leg=(0, 9))                                 # leggings


def _band(u, v, w, h, a, b):
    return (v >= a) & (v < b)


class F:
    """Face-local float coordinates handed to pattern functions."""

    def __init__(self, ctx, part, face, x0, y0, w, h, lo, hi):
        self.part, self.face, self.w, self.h = part, face, w, h
        self.u = ctx.x - x0
        self.v = ctx.y - y0
        self.inside = (self.u >= 0) & (self.u < w) & (self.v >= 0) & (self.v < h)
        self.lo, self.hi = lo, hi
        self.s = ctx.s

    # helpers in face space
    def rect(self, u0, v0, u1, v1):
        return (self.u >= u0) & (self.u < u1) & (self.v >= v0) & (self.v < v1)

    def hline(self, v0, th=1.0):
        return (self.v >= v0) & (self.v < v0 + th)

    def vline(self, u0, th=1.0):
        return (self.u >= u0) & (self.u < u0 + th)

    def disc(self, cu, cv, r):
        return np.hypot(self.u - cu, self.v - cv) < r

    def seg(self, u1, v1, u2, v2, wd=1.0):
        pu, pv = self.u - u1, self.v - v1
        bu, bv = u2 - u1, v2 - v1
        t = np.clip((pu * bu + pv * bv) / max(1e-6, bu * bu + bv * bv), 0, 1)
        return np.hypot(pu - bu * t, pv - bv * t) < wd / 2

    @property
    def mid(self):
        return self.w / 2

    @property
    def side(self):
        return self.face in ("left", "right", "outer", "inner")


# Each pattern: f(F) -> (mask, tone) where tone is a base key index field/int (1..5).
def p_bolt(f):
    if f.face == "top":
        return f.rect(1, 1, f.w - 1, 2), 2
    lo, hi = f.lo, f.hi
    span = hi - lo
    if f.face in ("front", "back"):
        k = min(1.6, f.w / 4)
        a, b = lo + span * 0.45, lo + span * 0.55
        m = (f.seg(f.mid + k, lo + 0.5, f.mid - k, a, 1.1) | f.seg(f.mid - k, a, f.mid + k, b, 1.1)
             | f.seg(f.mid + k, b, f.mid - k * 0.6, hi - 0.5, 1.1))
    else:
        m = f.hline(lo + 1) | f.seg(0.5, lo + 3, f.w - 0.5, lo + 4.5, 0.9)
    return m, np.where(f.v < lo + span / 2, 2, 3)


def p_coast(f):
    base = f.hi - 3
    wave = base + np.sin(f.u / max(f.w, 1) * np.pi * 2 + (0 if f.face != "back" else 1.5)) * 0.9
    m = (f.v >= wave) & (f.v < wave + 1.2)
    if f.part == "head":
        m |= f.hline(1) & (f.face != "top")
    if f.face == "top":
        m = f.rect(0, 0, f.w, 1) | f.rect(0, f.h - 1, f.w, f.h)
    foam = f.disc(f.w * 0.3, base - 1.5, 0.7) if f.face in ("front", "outer") else np.zeros_like(m)
    return m | foam, np.where(f.v < base, 1, 3)


def p_dune(f):
    m = np.zeros_like(f.inside)
    for k in range(3):
        o = f.lo + 1 + k * 2.6
        m |= (f.v - o >= (f.u * 0.5) - 1) & (f.v - o < (f.u * 0.5)) & (f.v >= f.lo) & (f.v < f.hi)
    if f.face == "top":
        m = f.rect(0, f.h - 1, f.w, f.h)
    return m, 3


def p_eye(f):
    if f.face in ("front",) and f.part in ("head", "body"):
        cv = 4.5 if f.part == "head" else (f.lo + f.hi) / 2 - 1
        r = 2.2 if f.part == "head" else 2.6
        outer = (np.abs(np.hypot((f.u - f.mid) * 0.75, f.v - cv) - r * 0.75) < 0.6)
        pupil = f.disc(f.mid, cv, 0.9)
        return outer | pupil, np.where(pupil, 5, 2)
    if f.part == "head":
        return f.hline(1) & (f.face != "top"), 3
    return f.hline(f.lo + (1 if f.part != "leg" else 0)) | (f.disc(f.mid, f.lo + 3, 0.8) & f.side), 3


def p_flow(f):
    t = (f.v - f.lo)
    curve = f.mid + np.sin(t / 3.2 + (0.8 if f.face == "back" else 0)) * f.w * 0.3
    m = (np.abs(f.u - curve) < 0.65) & (f.v >= f.lo) & (f.v < f.hi)
    if f.face == "top":
        m = f.disc(f.mid, f.h / 2, 1.3) & ~f.disc(f.mid, f.h / 2, 0.5)
    return m, np.where(t % 4 < 2, 2, 3)


def p_host(f):
    """Bordered panels: a frame just inside every face."""
    lo, hi = f.lo, f.hi
    frame = (f.rect(0, lo, f.w, hi) & ~f.rect(1, lo + 1, f.w - 1, hi - 1))
    if f.face == "top":
        frame = f.rect(0, 0, f.w, 1) | f.rect(0, 0, 1, f.h)
    stud = f.disc(f.mid, (lo + hi) / 2, 0.8) & (f.face == "front")
    return frame | stud, np.where(stud, 1, 3)


def p_raiser(f):
    """Upward chevrons."""
    m = np.zeros_like(f.inside)
    for k in range(2):
        tip = f.lo + 1 + k * 3
        m |= (np.abs(f.v - (tip + np.abs(f.u + 0.5 - f.mid) * 0.8)) < 0.6) & (f.v < f.hi)
    if f.face == "top":
        m = f.rect(f.mid - 1, 0, f.mid + 1, f.h)
    return m, 2


def p_rib(f):
    if f.part == "body" and f.face in ("front", "back"):
        m = np.zeros_like(f.inside)
        for k in range(3):
            v0 = f.lo + 2 + k * 2.4
            if v0 + 1 > f.hi:
                break
            m |= f.hline(v0) & ~f.rect(f.mid - 0.5, 0, f.mid + 0.5, 99) & f.rect(1, 0, f.w - 1, 99)
        m |= f.rect(f.mid - 0.5, f.lo + 1, f.mid + 0.5, f.hi - 1)
        return m, np.where(f.rect(f.mid - 0.5, 0, f.mid + 0.5, 99), 2, 3)
    if f.face == "top":
        return f.rect(1, 1, f.w - 1, 2), 2
    m = np.zeros_like(f.inside)
    for k in range(3):
        m |= f.hline(f.lo + 1 + k * 2)
    return m & (f.v < f.hi), 3


def p_sentry(f):
    stripes = (np.floor(f.u) % 3 == 1) & (f.v >= f.lo + 1) & (f.v < f.hi - 1)
    studs = (f.hline(f.lo) | f.hline(f.hi - 1)) & (np.floor(f.u) % 2 == 0)
    if f.face == "top":
        return f.rect(0, 0, f.w, f.h) & ((np.floor(f.u) + np.floor(f.v)) % 4 == 0), 2
    return stripes | studs, np.where(studs, 1, 3)


def p_shaper(f):
    cv = (f.lo + f.hi) / 2
    dia = (np.abs(f.u + 0.0 - f.mid) + np.abs(f.v - cv) * 0.8)
    m = (np.abs(dia - min(f.w / 2 - 0.3, 3.0)) < 0.6)
    if f.face == "top":
        m = f.rect(0, 0, 1, f.h) | f.rect(f.w - 1, 0, f.w, f.h)
    core = (dia < 0.9) & (f.face == "front")
    return (m | core) & (f.v >= f.lo) & (f.v < f.hi), np.where(core, 1, 3)


def p_silence(f):
    """Dotted concentric arcs (sculk-like echo lines)."""
    cu, cv = f.mid, f.hi + 1
    d = np.hypot(f.u - cu, (f.v - cv) * 1.1)
    arcs = (np.abs(d % 3 - 1.2) < 0.55) & (f.v >= f.lo) & (f.v < f.hi)
    dots = arcs & ((np.floor(f.u) + np.floor(f.v)) % 3 != 0)
    if f.face == "top":
        dots = f.disc(f.mid, f.h / 2, 1.0)
    return dots, np.where(d < 4, 2, 4)


def p_snout(f):
    if f.face == "front":
        cv = 5.5 if f.part == "head" else (f.lo + f.hi) / 2
        plate = (np.abs(f.u - f.mid) < min(2.5, f.w / 2 - 0.5)) & (np.abs(f.v - cv) < 1.6)
        holes = (f.disc(f.mid - 1.0, cv, 0.6) | f.disc(f.mid + 1.0, cv, 0.6)) & (f.w > 4)
        return plate, np.where(holes, 6, np.where(f.v < cv, 2, 3))
    if f.face == "top":
        return f.rect(0, f.h - 1, f.w, f.h), 3
    return f.hline(f.lo + 1, 1.0) | (f.vline(0) & (f.v >= f.lo) & (f.v < f.lo + 3)), 3


def p_spire(f):
    m = np.zeros_like(f.inside)
    span = f.hi - f.lo
    for cu in ([f.mid] if f.w <= 4 else [f.w * 0.25, f.w * 0.75]):
        height = span * 0.8
        tri = (np.abs(f.u + 0.0 - cu) * (height / 2.2) < (f.v - (f.hi - height))) & (f.v < f.hi)
        m |= tri
    if f.face == "top":
        m = f.disc(f.mid, f.h / 2, 1.0)
    return m, np.where(f.v < f.hi - span * 0.45, 2, 4)


def p_tide(f):
    c = f.lo + (f.hi - f.lo) * 0.55
    crest = c + np.abs(((f.u / 2.5) % 2) - 1) * 1.8
    m = (f.v >= crest) & (f.v < crest + 1.2) | (f.hline(f.hi - 1) & (np.floor(f.u) % 2 == 0))
    if f.face == "top":
        m = f.rect(0, 0, f.w, 1)
    return m & (f.v >= f.lo) & (f.v < f.hi), np.where(f.v < c + 1, 1, 3)


def p_vex(f):
    """Feathered diagonal strokes (wings)."""
    m = np.zeros_like(f.inside)
    sgn = -1 if f.face in ("right", "outer") else 1
    for k in range(3):
        o = f.lo + 1 + k * 2.2
        m |= f.seg(f.mid, o, f.mid + sgn * (f.w / 2 - 0.5), o + 2.2, 0.9)
        m |= f.seg(f.mid, o, f.mid - sgn * (f.w / 2 - 0.5), o + 2.2, 0.9) & (f.face in ("front", "back"))
    if f.face == "top":
        m = f.rect(f.mid - 0.5, 0, f.mid + 0.5, f.h)
    return m & (f.v >= f.lo) & (f.v < f.hi), np.where(f.u < f.mid, 2, 3)


def p_ward(f):
    if f.face == "front":
        cv = (f.lo + f.hi) / 2 if f.part != "head" else 4
        cross = (f.rect(f.mid - 0.5, cv - 3, f.mid + 0.5, cv + 3) | f.rect(f.mid - 2.5, cv - 1, f.mid + 2.5, cv))
        if f.w <= 4:
            cross = f.rect(f.mid - 0.5, cv - 3, f.mid + 0.5, cv + 3) | f.rect(0.5, cv - 1, f.w - 0.5, cv)
        gem = f.disc(f.mid, cv - 0.5, 0.75)
        return (cross | gem) & (f.v >= f.lo) & (f.v < f.hi), np.where(gem, 1, 3)
    if f.face == "top":
        return f.rect(0, 0, f.w, 1), 3
    return (f.hline(f.lo) | f.hline(f.hi - 1)) & (f.v < f.hi), 4


def p_wayfinder(f):
    if f.face in ("front", "back") and f.w >= 8:
        cv = (f.lo + f.hi) / 2 if f.part != "head" else 4.5
        du, dv = np.abs(f.u - f.mid), np.abs(f.v - cv)
        star = (du * 2.6 + dv < 3.2) | (dv * 2.6 + du < 3.2)
        return star & (f.v >= f.lo) & (f.v < f.hi), np.where(f.v < cv, 1, 3)
    if f.face == "top":
        return f.disc(f.mid, f.h / 2, 0.8), 2
    arrow = f.seg(f.mid, f.lo + 1, f.mid, f.hi - 1, 1.0) | (f.seg(f.mid, f.lo + 0.8, f.mid - 1.4, f.lo + 2.2, 0.9) |
                                                       f.seg(f.mid, f.lo + 0.8, f.mid + 1.4, f.lo + 2.2, 0.9))
    return arrow & (f.v >= f.lo) & (f.v < f.hi), 3


def p_wild(f):
    t = f.v - f.lo
    vine = f.mid + np.sin(t * 0.9 + (1 if f.face in ("left", "inner") else 0)) * (f.w * 0.25)
    m = (np.abs(f.u - vine) < 0.55)
    leaves = np.zeros_like(m)
    for k in range(3):
        lv = f.lo + 1.5 + k * 3
        lu = f.mid + (1.4 if k % 2 else -1.4) * min(1, f.w / 6)
        leaves |= f.disc(lu, lv, 0.85)
    if f.face == "top":
        return f.disc(f.w * 0.3, f.h * 0.4, 0.9) | f.disc(f.w * 0.7, f.h * 0.6, 0.9), 2
    return (m | leaves) & (f.v >= f.lo) & (f.v < f.hi), np.where(leaves, 2, 4)


PATTERNS = dict(bolt=p_bolt, coast=p_coast, dune=p_dune, eye=p_eye, flow=p_flow, host=p_host,
                raiser=p_raiser, rib=p_rib, sentry=p_sentry, shaper=p_shaper, silence=p_silence,
                snout=p_snout, spire=p_spire, tide=p_tide, vex=p_vex, ward=p_ward,
                wayfinder=p_wayfinder, wild=p_wild)


def _to_texel_grid(ctx, mask):
    """At 16x: as is. Above: snap to a finer half-texel grid so lines stay crisp."""
    return mask


def trim_sheet(pattern, layer):
    def gen(ctx):
        idx = np.full((ctx.H, ctx.W), -1, np.int32)
        faces = (HEAD + BODY + ARM + LEG) if layer is LAYER1 else (BODY + LEG)
        for part, face, x0, y0, w, h in faces:
            if part not in layer:
                continue
            lo, hi = layer[part]
            if face == "top" and lo > 0:
                continue          # band starts below the top: the top face is not armored there
            f = F(ctx, part, face, x0, y0, w, h, lo, min(hi, h) if face != "top" else h)
            if face == "top":
                f.lo, f.hi = 0, h
            m, tone = pattern(f)
            band = f.inside if face == "top" else f.inside & (f.v >= lo) & (f.v < hi)
            m = np.asarray(m) & band
            tone = np.broadcast_to(np.asarray(tone, np.int32), m.shape)
            k = ctx.s
            down = np.zeros_like(m); down[k:] = m[:-k]
            right = np.zeros_like(m); right[:, k:] = m[:, :-k]
            shadow = (down | right) & ~m & band
            up = np.zeros_like(m); up[:-k] = m[k:]
            left = np.zeros_like(m); left[:, :-k] = m[:, k:]
            lit = m & ~(down & right)          # top/left rim of each stroke
            stone = np.where(lit, tone - 1, tone)
            # shadow takes the tone of the stroke pixel it comes from
            src = np.where(down, np.roll(tone, k, 0), np.roll(tone, k, 1))
            idx = np.where(m, stone, idx)
            idx = np.where(shadow & (idx < 0), src + 3, idx)
        solid = (idx >= 0).astype(np.float32)
        idx = np.clip(idx, 0, 7)
        color = KEY[idx][..., None].repeat(3, -1)
        alpha = (solid > 0).astype(np.float32)
        color = np.where(alpha[..., None] > 0, color, 0)
        return Tex(ctx, color, alpha=alpha, height=np.where(alpha > 0, 0.6, 0.0), wrap=False, grain=0)
    return gen


for _name, _fn in PATTERNS.items():
    register(f"trims/entity/humanoid/{_name}", trim_sheet(_fn, LAYER1))
    register(f"trims/entity/humanoid_leggings/{_name}", trim_sheet(_fn, LAYER2))


# ------------------------------------------------------------------ item trim overlays
# Small accents placed where an armor icon's plate usually sits; drawn with key colors.
ITEM_TRIMS = {
    "helmet_trim": [
        "................",
        "................",
        "................",
        "................",
        "......1221......",
        ".....1....3.....",
        "....1......3....",
        "...2........4...",
        "...2........4...",
        "...3........5...",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    "chestplate_trim": [
        "................",
        "................",
        "................",
        "................",
        "......1..2......",
        ".......22.......",
        ".......23.......",
        "......2..3......",
        "................",
        "......2223......",
        "................",
        ".......23.......",
        "................",
        "................",
        "................",
        "................",
    ],
    "leggings_trim": [
        "................",
        "................",
        "................",
        "....11222334....",
        "................",
        "....2......4....",
        "................",
        "....2......4....",
        "....3......5....",
        "................",
        "....3......5....",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    "boots_trim": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "...12....12.....",
        "................",
        "...2......2.....",
        "..23......23....",
        "................",
        "................",
        "................",
        "................",
    ],
}


def item_trim(rows):
    def gen(ctx):
        idx = np.full((ctx.H, ctx.W), -1, np.int32)
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != ".":
                    idx[(ctx.tx == i) & (ctx.ty == j)] = int(ch)
        alpha = (idx >= 0).astype(np.float32)
        color = KEY[np.clip(idx, 0, 7)][..., None].repeat(3, -1) * alpha[..., None]
        return Tex(ctx, color, alpha=alpha, wrap=False, grain=0)
    return gen


for _name, _rows in ITEM_TRIMS.items():
    register(f"trims/items/{_name}", item_trim(_rows))
