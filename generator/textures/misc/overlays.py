"""Screen overlays and other misc/ textures.

Blend facts used here (game side): vignette / credits_vignette darken the
screen by their brightness (black = no effect); nausea is added on top
(black = no effect); pumpkin blur, powder snow and spyglass use normal alpha.
"""
import numpy as np

from ...engine import Tex, smoothstep
from ...registry import texture
from .common import Canvas, hexc, mix


def _radial(ctx):
    u = (ctx.x / ctx.w) * 2 - 1
    v = (ctx.y / ctx.h) * 2 - 1
    return u, v, np.hypot(u, v)


@texture("misc/vignette")
def vignette(ctx):
    u, v, d = _radial(ctx)
    # slightly squarer than a circle so screen corners get the most
    q = (np.abs(u) ** 3 + np.abs(v) ** 3) ** (1 / 3)
    k = np.clip((d * 0.6 + q * 0.4 - 0.35) / 1.0, 0, 1) ** 1.6
    return Tex(ctx, np.repeat(k[..., None], 3, -1), wrap=False, grain=0)


@texture("misc/credits_vignette")
def credits_vignette(ctx):
    u, v, d = _radial(ctx)
    k = np.clip((d - 0.2) / 1.0, 0, 1) ** 1.3
    return Tex(ctx, np.repeat(k[..., None], 3, -1), wrap=False, grain=0)


@texture("misc/nausea")
def nausea(ctx):
    """Additive swirl: two counter-rotating spiral arms in green and violet, dark center."""
    u, v, d = _radial(ctx)
    ang = np.arctan2(v, u)
    s1 = 0.5 + 0.5 * np.sin(ang * 3 + d * 9)
    s2 = 0.5 + 0.5 * np.sin(-ang * 2 + d * 7 + 1.3)
    wob = ctx.noise(48, 3, 0.5, salt="nausea")
    fade = smoothstep(0.1, 0.9, d) * (0.6 + wob * 0.4)
    col = (hexc("3fb85a")[None, None] * (s1 ** 3)[..., None] +
           hexc("8a42c8")[None, None] * (s2 ** 3)[..., None]) * fade[..., None]
    return Tex(ctx, np.clip(col, 0, 1), wrap=False, grain=0)


@texture("misc/pumpkinblur")
def pumpkinblur(ctx):
    """Looking out through a carved pumpkin: dark rind with two leaf-shaped eye holes."""
    u, v, d = _radial(ctx)
    n = ctx.noise(24, 3, 0.5, salt="pumpkin")
    ribs = 0.5 + 0.5 * np.cos(u * np.pi * 4)          # vertical rib shading
    col = mix(hexc("2a1204"), hexc("6e3510"), np.clip(ribs * 0.6 + n * 0.4, 0, 1))
    holes = np.zeros_like(u, dtype=bool)
    glow = ctx.zeros()
    for sx in (-1, 1):
        cx, cy = sx * 0.42, -0.08
        # almond eye, tilted toward the middle
        ang = -sx * 0.25
        x = (u - cx) * np.cos(ang) - (v - cy) * np.sin(ang)
        y = (u - cx) * np.sin(ang) + (v - cy) * np.cos(ang)
        e = (x / 0.36) ** 2 + (y / (0.22 * (1 - (x / 0.42) ** 2).clip(0.05))) ** 2
        holes |= e < 1
        glow = np.maximum(glow, np.clip(1 - (e - 1) / 1.6, 0, 1))
    # carved edge: bright orange flesh around the cut
    col = mix(col, hexc("e88a1c"), (glow * (~holes)) ** 2 * 0.9)
    alpha = np.where(holes, 0.0, 1.0)
    # soften the inner edge a little (texture is drawn with blur)
    alpha = np.where(~holes & (glow > 0.85), 0.85, alpha)
    return Tex(ctx, col, alpha=alpha, wrap=False, grain=0)


@texture("misc/powder_snow_outline")
def powder_snow_outline(ctx):
    u, v, d = _radial(ctx)
    q = np.maximum(np.abs(u), np.abs(v))
    n = ctx.noise(16, 4, 0.55, salt="frost")
    edge = q * 0.65 + d * 0.35 + (n - 0.5) * 0.35
    a = np.clip((edge - 0.55) / 0.35, 0, 1)
    if ctx.pixel_art:
        a = ctx.quantize(a, 6)
    col = mix(hexc("b8d4ee"), hexc("f4faff"), np.clip(a * 0.8 + n * 0.3, 0, 1))
    # crystalline sparkles near the frozen edge
    sp = (ctx.texel_noise("frostsp", soft=False) > 0.985) & (a > 0.3)
    col = np.where(sp[..., None], hexc("ffffff"), col)
    return Tex(ctx, col, alpha=np.clip(a * 0.95, 0, 1), wrap=False, grain=0)


@texture("misc/spyglass_scope")
def spyglass_scope(ctx):
    u, v, d = _radial(ctx)
    cv = Canvas(ctx, bg=hexc("050506"), alpha=1.0)
    lens = d < 0.98
    cv.put(lens, hexc("000000"), 0.0)
    # brass rim
    rim = (d >= 0.9) & (d < 0.98)
    ang = np.arctan2(v, u)
    shade = 0.5 + 0.5 * np.cos(ang + 2.4)
    cv.put(rim, mix(hexc("3a2410"), hexc("8a6430"), shade), 1.0)
    inner = (d >= 0.86) & (d < 0.9)
    cv.put(inner, hexc("140c06"), 1.0)
    # subtle reticle ticks
    for a0 in (0, np.pi / 2, np.pi, 3 * np.pi / 2):
        tick = (np.abs(((ang - a0 + np.pi) % (2 * np.pi)) - np.pi) < 0.012 * 2) & (d > 0.78) & (d < 0.86)
        cv.put(tick, hexc("1a1a1c"), 0.8)
    # faint vignette inside the lens
    cv.put(lens & ~rim & ~inner & (d > 0.72), hexc("000000"), np.clip((d - 0.72) / 0.14, 0, 1) * 0.6)
    return cv.tex()


@texture("misc/shadow")
def shadow(ctx):
    u, v, d = _radial(ctx)
    a = np.clip(1 - d, 0, 1) ** 0.8
    a = np.where(d < 1, a, 0)
    if ctx.pixel_art:
        a = np.round(a * 8) / 8
    return Tex(ctx, np.zeros((ctx.H, ctx.W, 3), np.float32), alpha=a, wrap=False, grain=0)


@texture("misc/underwater")
def underwater(ctx):
    """Tiling murky water drawn over the view: caustic-like ripples, translucent blue."""
    vo = ctx.voronoi(7, "uw", min_dist=4)
    c = np.clip((vo["f2"] - vo["f1"]) / 2.5, 0, 1)
    n = ctx.noise(8, 2, 0.5, salt="uw")
    v = (1 - c) * 0.6 + n * 0.4
    p = np.stack([hexc(x) for x in ("0e2a52", "153a6a", "1f4c80", "2e6296", "4a80b0")])
    col = ctx.palette(p, v)
    return Tex(ctx, col, alpha=0.55 + v * 0.25, wrap=True, grain=0)


@texture("misc/forcefield")
def forcefield(ctx):
    """World border: tinted by the game -> white diagonal hatching with gaps."""
    k = (ctx.x + ctx.y) % 8
    band = (k < 2.0)
    fine = ((ctx.x - ctx.y) % 8 < 1.0) & ((ctx.ty % 4) == 0)
    a = np.where(band, 0.9, np.where(fine, 0.5, 0.0))
    return Tex(ctx, np.ones((ctx.H, ctx.W, 3), np.float32), alpha=a, wrap=True, grain=0)


def glint(ctx, salt, freq):
    """Tiling purple shimmer: soft diagonal bands broken up by stretched noise.
    freq = (fx, fy) integer band counts across the tile (keeps it seamless)."""
    t = (ctx.x * freq[0] + ctx.y * freq[1]) / ctx.w
    n = ctx.noise(32, 4, 0.55, salt=salt, stretch=(2, 2))
    bands = 0.5 + 0.5 * np.sin(2 * np.pi * (t + n * 1.2))
    sparkle = ctx.noise(4, 2, 0.5, salt=salt + "sp") ** 6
    v = np.clip(bands ** 2 * 0.85 + sparkle * 0.6, 0, 1)
    col = np.stack([0.50 * v + 0.08 * v ** 2, 0.20 * v + 0.12 * v ** 3, 0.85 * v], -1)
    return Tex(ctx, np.clip(col * 1.15, 0, 1), wrap=True, grain=0)


@texture("misc/enchanted_glint_item")
def glint_item(ctx):
    return glint(ctx, "glint_item", (2, 1))


@texture("misc/enchanted_glint_armor")
def glint_armor(ctx):
    return glint(ctx, "glint_armor", (1, 2))


def _icon_bg(ctx, top, bottom):
    t = ctx.y / ctx.h
    return mix(hexc(top), hexc(bottom), t)


@texture("misc/unknown_pack")
def unknown_pack(ctx):
    """Missing pack icon: a closed cardboard box with a question mark on a slate tile."""
    s = ctx.w / 16
    cv = Canvas(ctx, bg=_icon_bg(ctx, "4a4f5c", "2c3038"), alpha=1.0)
    box = ctx.polygon([(3 * s, 5 * s), (13 * s, 5 * s), (13 * s, 13.5 * s), (3 * s, 13.5 * s)])
    lid = ctx.polygon([(2.5 * s, 3.5 * s), (13.5 * s, 3.5 * s), (13.5 * s, 5.5 * s), (2.5 * s, 5.5 * s)])
    n = ctx.noise(2 * s, 2, 0.5, salt="card")
    cv.put(box, mix(hexc("9a6e3c"), hexc("b4844c"), n), 1)
    cv.put(ctx.edge(box, s * 0.5, "br") > 0, hexc("6e4a24"), 1)
    cv.put(lid, mix(hexc("c4945a"), hexc("d8aa6c"), n), 1)
    cv.put(ctx.edge(lid, s * 0.5, "br") > 0, hexc("8a6234"), 1)
    tape = ctx.rect(7.25 * s, 3.5 * s, 8.75 * s, 9 * s)
    cv.put(tape, hexc("e2d2a8"), 1)
    # question mark
    q = np.maximum.reduce([ctx.rect(6.5 * s, 7 * s, 9.5 * s, 8 * s), ctx.rect(9 * s, 7 * s, 10 * s, 10 * s),
                           ctx.rect(8 * s, 9.5 * s, 9.5 * s, 10.5 * s), ctx.rect(7.5 * s, 10 * s, 8.5 * s, 11.5 * s),
                           ctx.rect(7.5 * s, 12 * s, 8.5 * s, 13 * s)])
    cv.put(q, hexc("3a2410"), 1)
    return cv.tex()


@texture("misc/unknown_server")
def unknown_server(ctx):
    """Missing server icon: a small stack of server units with status lights."""
    s = ctx.w / 16
    cv = Canvas(ctx, bg=_icon_bg(ctx, "3c4a5a", "222a34"), alpha=1.0)
    for i, y in enumerate((3, 6.5, 10)):
        unit = ctx.rect(3 * s, y * s, 13 * s, (y + 3) * s)
        cv.put(unit, hexc("5c6470"), 1)
        cv.put(ctx.edge(unit, s * 0.5, "tl") > 0, hexc("8a94a2"), 1)
        cv.put(ctx.edge(unit, s * 0.5, "br") > 0, hexc("383e48"), 1)
        for k in range(3):
            slot = ctx.rect((4.5 + k * 1.6) * s, (y + 1.1) * s, (5.6 + k * 1.6) * s, (y + 1.9) * s)
            cv.put(slot, hexc("2a3038"), 1)
        led = ctx.circle(11.3 * s, (y + 1.5) * s, 0.7 * s)
        cv.put(led, hexc(("5ce06a", "f2c040", "e05a4a")[i]), 1)
    return cv.tex()
