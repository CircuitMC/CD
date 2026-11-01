"""Large GUI pictures: title wordmarks, panorama cubemap, realms/preset illustrations,
book, recipe book, advancement window and backgrounds, sign edit textures."""
import math

import numpy as np

from ...engine import Tex, pal
from ...materials import planks, rock
from ...registry import register
from . import glyphs
from .legacy_embed import embed
from .common import (BLACK, C, Canvas, FACE, HI, INK, SHADE, WHITE, inset, mix, panel)


# ----------------------------------------------------------------- wordmark
def word_cells(text, gap=1):
    """Glyph cells for a word using the CircuitMC font (caps)."""
    cells, x = set(), 0
    for ch in text:
        if ch == " ":
            x += 3
            continue
        g = glyphs.glyph(ch)
        w = max(px for px, _ in g) + 1
        cells |= {(x + px, py) for px, py in g}
        x += w + gap
    return cells, x - gap


def wordmark(ctx, text, px, x0, y0, depth=3, face=None, side=None, edge=None, trace=True, flat_white=False):
    """Blocky extruded logo: each glyph texel becomes a px x px block (in texture texels)."""
    c = Canvas(ctx)
    cells, w = word_cells(text)
    if flat_white:
        for (gx, gy) in cells:
            c.rect(x0 + gx * px, y0 + gy * px, px, px, WHITE)
        return c
    face = (C("8e939c"), C("c3c8d0")) if face is None else face
    side = C("3e4148") if side is None else side
    edge = C("17181c") if edge is None else edge
    # outline + extrusion
    for d in range(depth, 0, -1):
        for (gx, gy) in cells:
            c.rect(x0 + gx * px + d * px // 3 - 2, y0 + gy * px + d * px // 3 - 2, px + 4, px + 4, edge)
    for d in range(depth, 0, -1):
        for (gx, gy) in cells:
            c.rect(x0 + gx * px + d * px // 3, y0 + gy * px + d * px // 3, px, px, mix(side, BLACK, d / (depth * 3)))
    for (gx, gy) in cells:
        c.rect(x0 + gx * px - 2, y0 + gy * px - 2, px + 4, px + 4, edge)
    n = ctx.noise(px * 1.5, 2, 0.5, salt="logo")
    grain = ctx.texel_noise("logog")
    face_col = mix(face[0], face[1], 1.0)[None, None, :] * 0 + \
        face[0][None, None, :] * (1 - n[..., None]) + face[1][None, None, :] * n[..., None]
    face_col = face_col * (0.94 + 0.08 * grain[..., None])
    fm = ctx.zeros()
    for (gx, gy) in cells:
        fm = np.maximum(fm, ctx.rect(x0 + gx * px, y0 + gy * px, x0 + (gx + 1) * px, y0 + (gy + 1) * px))
    c.mask(fm, face_col)
    # bevel: light top-left, dark bottom-right per letter block edge
    c.mask(ctx.edge(fm, px / 4, "tl"), mix(face[1], WHITE, 0.45))
    c.mask(ctx.edge(fm, px / 4, "br"), mix(face[0], BLACK, 0.35))
    if trace:  # copper circuit traces etched in the letter faces
        rng = np.random.default_rng(7)
        cl = sorted(cells)
        for k in range(len(cl) // 3):
            gx, gy = cl[rng.integers(len(cl))]
            if (gx + 1, gy) in cells:
                yy = y0 + gy * px + px // 2
                c.rect(x0 + gx * px + px // 2, yy - 1, px, 2, C("d0803e"))
                c.circle(x0 + gx * px + px // 2 + 0.5, yy, 2.4, C("f0b070"))
            elif (gx, gy + 1) in cells:
                xx = x0 + gx * px + px // 2
                c.rect(xx - 1, y0 + gy * px + px // 2, 2, px, C("d0803e"))
                c.circle(xx, y0 + gy * px + px // 2 + 0.5, 2.4, C("f0b070"))
    return c


def _title(text):
    def fn(ctx):
        cells, w = word_cells(text)
        px = min((ctx.w - 60) // (w + 2), (ctx.h - 40) // 9)
        x0 = (ctx.w - w * px) // 2 - px // 2
        y0 = (ctx.h - 7 * px) // 2 - px // 2
        return wordmark(ctx, text, px, x0, y0, depth=2).tex()
    return fn


register("gui/title/minecraft", _title("CircuitMC".upper()))
register("gui/title/minceraft", _title("CricuitMC".upper()))


def _edition(ctx):
    text = "DEFAULT EDITION"
    cells, w = word_cells(text)
    px = min((ctx.w - 16) // w, (ctx.h - 12) // 8)
    x0 = (ctx.w - w * px) // 2
    c = Canvas(ctx)
    for (gx, gy) in cells:
        c.rect(x0 + gx * px + px // 2, 6 + gy * px + px // 2, px, px, C("5a3a0a"))
    for (gx, gy) in cells:
        c.rect(x0 + gx * px, 6 + gy * px, px, px, C("f2c33a"))
        c.rect(x0 + gx * px, 6 + gy * px, px, px // 4, C("ffe58a"))
    return c.tex()


register("gui/title/edition", _edition)


def _realms_logo(ctx):
    cells, w = word_cells("REALMS")
    px = min((ctx.w - 40) // (w + 2), (ctx.h - 40) // 9)
    x0 = (ctx.w - w * px) // 2
    y0 = (ctx.h - 7 * px) // 2
    return wordmark(ctx, "REALMS", px, x0, y0, face=(C("3f8f4a"), C("7ad070")), side=C("1f4a24"),
                    trace=False).tex()


register("gui/title/realms", _realms_logo)


def _studio(ctx):
    """Loading-screen wordmark: left half in the top half of the sheet, right half below (white).
    The game shows the two halves side by side, so the split falls between letters."""
    c = Canvas(ctx)
    H = ctx.h // 2
    left, lw = word_cells("CIRCU")
    right, rw = word_cells("ITMC")
    px = min((ctx.w - 40) // max(lw, rw), (H - 60) // 7)
    gap = px // 2
    y0 = (H - 7 * px) // 2
    for (gx, gy) in left:
        c.rect(ctx.w - gap - lw * px + gx * px, y0 + gy * px, px, px, WHITE)
    for (gx, gy) in right:
        c.rect(gap + gx * px, H + y0 + gy * px, px, px, WHITE)
    return c.tex()


register("gui/title/mojangstudios", _studio)


# ----------------------------------------------------------------- panorama cubemap
def _periodic(phi, terms, seed):
    rng = np.random.default_rng(int(seed * 10))
    out = np.zeros_like(phi)
    for f, a in terms:
        out += a * np.sin(f * phi + rng.uniform(0, 2 * math.pi))
    return out


def sky_scene(phi, elev, dist_fog=1.0, seed=3):
    """Colour for view direction (azimuth phi, elevation elev) -> (H, W, 3)."""
    t = np.clip(elev / (math.pi / 2), -1, 1)
    sky = mix(C("bfe0ff"), C("3f7fd6"), 0)[None, None] * 0 + \
        (C("cfe6ff")[None, None] * (1 - np.clip(t * 1.2, 0, 1)[..., None]) +
         C("4a86d8")[None, None] * np.clip(t * 1.2, 0, 1)[..., None])
    # clouds in a band above the horizon (fade out toward the zenith)
    cl = _periodic(phi, [(3, 0.5), (7, 0.35), (13, 0.25), (23, 0.15)], seed + 1)
    band = np.exp(-((elev - 0.22) / 0.09) ** 2)
    cloud = np.clip((cl + 0.2) * 2.5, 0, 1) * band
    sky = sky * (1 - cloud[..., None] * 0.8) + WHITE[None, None] * (cloud[..., None] * 0.8)
    # far mountains / near hills (periodic in phi -> seamless)
    far = 0.06 + 0.05 * _periodic(phi, [(4, 0.6), (9, 0.3), (17, 0.15)], seed + 2)
    near = 0.015 + 0.04 * _periodic(phi, [(5, 0.5), (11, 0.35), (29, 0.12)], seed + 3)
    col = sky
    m_far = elev < far
    col = np.where(m_far[..., None], mix(C("6f86a8"), C("9fb4cc"), 0.4)[None, None], col)
    snow = m_far & (elev > far - 0.015) & (far > 0.09)
    col = np.where(snow[..., None], C("eef4fa")[None, None], col)
    m_near = elev < near
    col = np.where(m_near[..., None], C("4f8a3a")[None, None], col)
    # trees along the near ridge
    tree = (elev < near + 0.02 + 0.012 * np.sin(phi * 160)) & (elev > near - 0.01) & (np.sin(phi * 40 + 1) > 0.2)
    col = np.where(tree[..., None], C("2f5a26")[None, None], col)
    # ground below horizon: grass with faint field stripes, fading to uniform at steep angles
    g = elev < -0.0
    stripes = 0.5 + 0.5 * np.sin(phi * 24 + 3 * np.sin(phi * 5))
    fade = np.clip((-elev - 0.0) / 0.5, 0, 1)
    grass = (C("5fa040")[None, None] * (1 - stripes[..., None] * 0.12 * (1 - fade[..., None])))
    grass = grass * (1 - fade[..., None]) + C("4f8f36")[None, None] * fade[..., None]
    col = np.where(g[..., None] & ~m_near[..., None], grass, col)
    # water patch to the "south"
    lake = g & (np.cos(phi - math.pi) > 0.85) & (elev > -0.12)
    col = np.where(lake[..., None], C("3f76c4")[None, None], col)
    return col


def _cube_dir(ctx, face):
    u = (ctx.x / ctx.w) * 2 - 1
    v = (ctx.y / ctx.h) * 2 - 1
    if face < 4:
        a = face * math.pi / 2
        f = np.array([math.sin(a), 0, -math.cos(a)])
        r = np.array([math.cos(a), 0, math.sin(a)])
        d = f[None, None] + u[..., None] * r[None, None] - v[..., None] * np.array([0, 1, 0])[None, None]
    elif face == 4:
        d = np.stack([u, np.ones_like(u), v], -1)
    else:
        d = np.stack([u, -np.ones_like(u), -v], -1)
    x, y, z = d[..., 0], d[..., 1], d[..., 2]
    phi = np.arctan2(x, -z)
    elev = np.arctan2(y, np.hypot(x, z))
    return phi, elev


def _panorama(face):
    def fn(ctx):
        from .panorama import render_face
        return render_face(ctx, face)
    return fn


for _i in range(6):
    register(f"gui/title/background/panorama_{_i}", _panorama(_i), size=(512, 512))


def _overlay(ctx):
    t = ctx.y / ctx.h
    a = np.clip(np.abs(t - 0.5) * 2, 0, 1) ** 2 * 0.55
    return Tex(ctx, np.zeros((ctx.H, ctx.W, 3), np.float32), alpha=a, wrap=False, grain=0)


register("gui/title/background/panorama_overlay", _overlay, size=(16, 128))


# ----------------------------------------------------------------- illustrations
def landscape(ctx, seed, horizon=0.55, tint=None):
    """Flat 2D scene: azimuth spans the width once, elevation from the vertical."""
    phi = ctx.x / ctx.w * 2 * math.pi * 0.5 + seed
    elev = (horizon - ctx.y / ctx.h) * 1.2
    col = sky_scene(phi, elev, seed=seed)
    if tint is not None:
        col = col * (1 - tint[1]) + C(tint[0])[None, None] * tint[1]
    return col


def framed(ctx, col, border=True):
    c = Canvas(ctx)
    c.mask(ctx.full(1), col)
    if border:
        c.frame(0, 0, ctx.w, ctx.h, C("16171a"))
        c.frame(1, 1, ctx.w - 2, ctx.h - 2, C("6d7079"))
    return c


def _scene(seed, extra=None, tint=None, horizon=0.55):
    def fn(ctx):
        c = framed(ctx, landscape(ctx, seed, horizon, tint))
        if extra:
            extra(c, ctx)
        return c.tex()
    return fn


def _house(c, ctx, x, y, s):
    c.rect(x, y, 10 * s, 7 * s, C("a8784a"))
    c.poly([(x - s, y), (x + 5 * s, y - 5 * s), (x + 11 * s, y)], C("8c3a2a"))
    c.rect(x + 4 * s, y + 3 * s, 2 * s, 4 * s, C("4a3018"))


def _tower(c, ctx, x, y, s):
    c.rect(x, y, 6 * s, 16 * s, C("8a8d95"))
    for k in range(3):
        c.rect(x + k * 2 * s, y - 2 * s, s, 2 * s, C("8a8d95"))
    c.rect(x + 2 * s, y + 5 * s, 2 * s, 3 * s, C("2a2b30"))


def _orb(c, ctx, x, y, r):
    c.circle(x, y, r + 2, C("2f6b1e"))
    c.circle(x, y, r, C("86e050"))
    c.circle(x - r / 3, y - r / 3, r / 3, C("d8ffb0"))


def _arrow_up(c, ctx, x, y, s):
    c.poly([(x - 6 * s, y), (x, y - 7 * s), (x + 6 * s, y)], WHITE)
    c.rect(x - 2 * s, y, 4 * s, 7 * s, WHITE)


def _bulb(c, ctx, x, y, r):
    c.circle(x, y, r, C("f2d23a"))
    c.circle(x - r / 3, y - r / 3, r / 3, C("fff6c0"))
    c.rect(x - r / 2, y + r * 0.8, r, r / 2, C("8a8d95"))


def _plus(c, ctx, x, y, s):
    c.rect(x - s, y - 4 * s, 2 * s, 8 * s, WHITE)
    c.rect(x - 4 * s, y - s, 8 * s, 2 * s, WHITE)


register("gui/realms/adventure", _scene(1.0, lambda c, ctx: _tower(c, ctx, 150, 100, 4)))
register("gui/realms/experience", _scene(2.0, lambda c, ctx: _orb(c, ctx, 128, 90, 26)))
register("gui/realms/inspiration", _scene(3.0, lambda c, ctx: _bulb(c, ctx, 128, 90, 28)))
register("gui/realms/new_world", _scene(4.0, lambda c, ctx: _plus(c, ctx, 128, 90, 6)))
register("gui/realms/survival_spawn", _scene(5.0, lambda c, ctx: _house(c, ctx, 100, 120, 6)))
register("gui/realms/upload", _scene(6.0, lambda c, ctx: _arrow_up(c, ctx, 128, 100, 6)))
register("gui/presets/isles", _scene(7.0, None, tint=("3f76c4", 0.0), horizon=0.75))
register("gui/realms/friends", _scene(8.0, lambda c, ctx: (_house(c, ctx, 14, 24, 1), _house(c, ctx, 36, 22, 1))))
register("gui/realms/minigames", _scene(9.0, lambda c, ctx: _orb(c, ctx, 32, 16, 7)))
register("gui/realms/private_server", _scene(10.0, lambda c, ctx: _tower(c, ctx, 28, 12, 1)))
register("gui/realms/no_realms", _scene(11.0, lambda c, ctx: _plus(c, ctx, 65, 30, 3)))
register("gui/realms/snapshot_realms", _scene(12.0, lambda c, ctx: _bulb(c, ctx, 65, 30, 12)))


def _empty_frame(ctx):
    c = Canvas(ctx)
    c.rect(0, 0, 16, 16, C("16171a"))
    c.rect(1, 1, 14, 14, C("6d7079"))
    c.rect(2, 2, 12, 12, C("2a2b30"))
    return c.tex()


register("gui/realms/empty_frame", _empty_frame)


# ----------------------------------------------------------------- book / recipe book / advancement window
def _book(ctx):
    c = Canvas(ctx)
    x, y, w, h = 20, 1, 146, 180
    n = ctx.noise(6, 2, 0.5, salt="page")
    paper = C("efe4c8")[None, None] * (0.95 + 0.06 * n[..., None])
    c.rect(x - 2, y, w + 4, h, C("5a3a1e"))       # cover edge
    c.rect(x - 1, y + 1, w + 2, h - 2, C("8a5a2e"))
    m = ctx.rect(x + 1, y + 2, x + w - 1, y + h - 3)
    c.mask(m, paper)
    c.vline(x + 2, y + 2, y + h - 4, C("d8caa4"))   # spine shadow
    c.vline(x + 3, y + 2, y + h - 4, C("e2d6b4"))
    c.hline(x + 1, x + w - 2, y + h - 3, C("cbbd96"))
    embed(c, ctx, "book")
    return c.tex()


register("gui/book", _book)


def _recipe_book(ctx):
    c = Canvas(ctx)
    panel(c, 1, 1, 147, 166)
    inset(c, 10, 30, 129, 104, face=C("9a9da6"))
    embed(c, ctx, "recipe_book")
    return c.tex()


register("gui/recipe_book", _recipe_book)


def _adv_window(ctx):
    c = Canvas(ctx)
    panel(c, 0, 0, 252, 140)
    c.rect(8, 17, 236, 116, C("16171a"))
    c.clear(9, 18, 234, 114)
    return c.tex()


register("gui/advancements/window", _adv_window)


def _adv_bg(p, kind):
    def fn(ctx):
        t = rock(ctx, p, cell=4, salt=kind)
        t.grain = 0
        if kind == "husbandry":  # hay-like streaks
            s = (np.sin(ctx.x * 2.2 + ctx.noise(4, 1, salt="hay") * 3) > 0.6)
            t.color = np.where(s[..., None], t.color * 0.8, t.color)
        return t
    return fn


register("gui/advancements/backgrounds/stone", _adv_bg(pal("5a5b60", "6a6b70", "76777c", "828388", "8e8f94"), "stone"))
register("gui/advancements/backgrounds/adventure", _adv_bg(pal("8a5a2e", "9e6a38", "ae7a44", "bc8850", "c8965c"), "adventure"))
register("gui/advancements/backgrounds/end", _adv_bg(pal("c8c48a", "d4d098", "dedaa4", "e6e2b0", "eeeabc"), "end"))
register("gui/advancements/backgrounds/husbandry", _adv_bg(pal("8a7a2a", "a08e34", "b4a03e", "c4b04a", "d2be58"), "husbandry"))
register("gui/advancements/backgrounds/nether", _adv_bg(pal("4a1414", "5e1a1a", "6e2222", "7e2a28", "8c3430"), "nether"))


# ----------------------------------------------------------------- signs
WOODS = {
    "oak": ("6f5533", "a98656", "c3a06b"), "spruce": ("4b3321", "6a4a31", "856043"),
    "birch": ("a99a6b", "d5c691", "e7daa8"), "jungle": ("7b5337", "ae7c55", "c69469"),
    "acacia": ("8f4526", "c6683c", "dc804f"), "dark_oak": ("2e1e0e", "4d341c", "634629"),
    "mangrove": ("5a221e", "7e3530", "984640"), "cherry": ("b07a74", "e2b0a8", "f2c8c0"),
    "bamboo": ("9a8a34", "c8b450", "e0cc64"), "crimson": ("4a1a30", "7a2e4c", "94405e"),
    "warped": ("1e4a48", "2e7470", "3f8c86"), "pale_oak": ("b8b0a8", "dcd6d0", "eeeae4"),
    "poplar": ("8a7a5a", "b8a67e", "cfbe96"),
}


def _plank_rows(c, ctx, x, y, w, h, wood, board=4):
    lo, mid, hi = (C(v) for v in WOODS[wood])
    n = ctx.noise(3, 2, 0.5, salt=wood, stretch=(4, 0.5))
    col = mid[None, None] * (0.9 + 0.2 * n[..., None])
    m = ctx.rect(x, y, x + w, y + h)
    c.mask(m, col)
    for yy in range(y + board - 1, y + h - 1, board):
        c.hline(x, x + w - 1, yy, mix(lo, mid, 0.3))
    c.frame(x, y, w, h, lo)
    c.hline(x + 1, x + w - 2, y + 1, hi)


def _sign(wood):
    def fn(ctx):
        c = Canvas(ctx)
        lo = C(WOODS[wood][0])
        c.rect(11, 12, 2, 14, mix(lo, BLACK, 0.2))
        c.vline(11, 12, 25, lo)
        _plank_rows(c, ctx, 0, 0, 24, 13, wood, 4)
        return c.tex()
    return fn


def _hanging(wood):
    def fn(ctx):
        c = Canvas(ctx)
        _plank_rows(c, ctx, 0, 0, 16, 16, wood, 5)
        c.frame(1, 1, 14, 14, mix(C(WOODS[wood][0]), C(WOODS[wood][1]), 0.5))
        return c.tex()
    return fn


for _w in WOODS:
    register(f"gui/signs/{_w}", _sign(_w))
    register(f"gui/hanging_signs/{_w}", _hanging(_w))
