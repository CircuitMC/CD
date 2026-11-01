"""Sky and weather: sun, moon phases, end flash, clouds, rain, snow, end sky."""
import numpy as np

from ...engine import Tex, smoothstep
from ...registry import texture
from .common import Canvas, hexc, mix, native


# ------------------------------------------------------------------ sun
@texture("environment/celestial/sun")
def sun(ctx):
    """Blocky sun: a hot square core with stepped, fading corona (drawn additively in game)."""
    c = ctx.w / 2
    dx, dy = np.abs(ctx.x - c), np.abs(ctx.y - c)
    box = np.maximum(dx, dy)                   # square distance
    rnd = np.hypot(dx, dy)
    cv = Canvas(ctx)
    core_r = ctx.w * 0.25
    # corona: square-ish falloff mixed with round so corners stay soft
    d = box * 0.6 + rnd * 0.4
    glow = np.clip(1 - (d - core_r) / (ctx.w * 0.27), 0, 1)
    glow = ctx.quantize(glow, 5) if ctx.pixel_art else glow
    cv.over(np.ones_like(glow), hexc("ffb43c"), glow * 0.55)
    core = box < core_r
    n = ctx.noise(3, 2, 0.5, salt="sunspots")
    inner = np.clip(1 - box / core_r, 0, 1)
    col = mix(hexc("ffd25a"), hexc("fffbe0"), np.clip(inner * 1.6 + (n - 0.5) * 0.4, 0, 1))
    col = np.where((box > core_r - 1)[..., None], hexc("ffc244"), col)
    cv.put(core, col, 1.0)
    return cv.tex(emissive=1.0)


# ------------------------------------------------------------------ moon
PHASES = {  # illuminated fraction sign: + waxing (lit on the right), - waning
    "full_moon": 1.0, "waning_gibbous": -0.7, "third_quarter": -0.5, "waning_crescent": -0.22,
    "new_moon": 0.0, "waxing_crescent": 0.22, "first_quarter": 0.5, "waxing_gibbous": 0.7,
}


def moon(phase):
    def gen(ctx):
        c = ctx.w / 2
        r = ctx.w * 0.25                    # square moon face, half size
        u, v = (ctx.x - c) / r, (ctx.y - c) / r
        face = (np.abs(u) < 1) & (np.abs(v) < 1)
        # surface: pale gray with darker maria and a few craters
        n = ctx.noise(4, 3, 0.5, salt="moon:maria")
        base = mix(hexc("c9cdd8"), hexc("eef0f6"), np.clip(n * 1.3 - 0.1, 0, 1))
        maria = (ctx.noise(6, 2, 0.5, salt="moon:mare") > 0.6)
        base = np.where(maria[..., None], hexc("a9aebd"), base)
        for cx, cy, cr in ((-0.45, -0.35, 0.28), (0.4, 0.3, 0.22), (0.1, -0.55, 0.16), (-0.3, 0.55, 0.18)):
            d = np.hypot(u - cx, v - cy)
            base = np.where((d < cr)[..., None], hexc("9ea3b2"), base)
            rim = (d >= cr) & (d < cr + 0.14) & ((u - cx) + (v - cy) > 0)
            base = np.where(rim[..., None], hexc("f6f7fb"), base)
        base = np.where((ctx.edge(face.astype(np.float32), 1.0) > 0)[..., None], hexc("b4b9c6"), base)
        # terminator: the lit part is bounded by an ellipse-like curve across the square
        if phase == 0:
            lit = np.zeros_like(face)
        elif abs(phase) == 1:
            lit = face
        else:
            k = abs(phase)
            # x position of the terminator for each row of the "sphere"
            half = np.sqrt(np.clip(1 - v * v * 0.35, 0, 1))
            term = (1 - 2 * k) * half
            lit = (u > term) if phase > 0 else (-u > term)
        cv = Canvas(ctx)
        glow = np.clip(1 - np.maximum(np.abs(u), np.abs(v)) / 1.9, 0, 1) * (0.25 if phase else 0.0)
        cv.over(np.ones_like(glow), hexc("9fb4e0"), glow)
        # unlit side: very faint earthshine
        cv.put(face, base * 0.16, 1.0)
        cv.put(face & lit, base, 1.0)
        return cv.tex(emissive=0.6)
    return gen


for _name, _ph in PHASES.items():
    texture(f"environment/celestial/moon/{_name}")(moon(_ph))


@texture("environment/celestial/end_flash")
def end_flash(ctx):
    """Bright starburst flash for the End sky: violet halo, white core, 8 rays."""
    c = ctx.w / 2
    dx, dy = ctx.x - c, ctx.y - c
    d = np.hypot(dx, dy) / c
    ang = np.arctan2(dy, dx)
    rays = np.abs(np.cos(ang * 4)) ** 18 * np.clip(1 - d, 0, 1) * 1.1
    rays2 = np.abs(np.cos(ang * 4 + np.pi / 4)) ** 30 * np.clip(1 - d * 1.5, 0, 1) * 0.7
    halo = np.clip(1 - d, 0, 1) ** 2.2
    core = np.clip(1 - d * 4, 0, 1)
    a = np.clip(halo * 0.75 + rays + rays2 + core, 0, 1)
    if ctx.pixel_art:
        a = ctx.quantize(a, 6)
    col = mix(hexc("a35cff"), hexc("f4e8ff"), np.clip(core * 2 + rays * 0.8 + halo * 0.4, 0, 1))
    return Tex(ctx, col, alpha=a, wrap=False, grain=0, emissive=1.0)


# ------------------------------------------------------------------ clouds
@texture("environment/clouds")
@native
def clouds(ctx):
    """Cloud cell map: each texel is one cloud column. Binary alpha, tiling."""
    big = ctx.noise(48, 3, 0.55, salt="clouds:big")
    mid = ctx.noise(14, 2, 0.5, salt="clouds:mid")
    v = big * 0.82 + mid * 0.18
    v = (v - v.mean()) / (v.std() + 1e-6)
    m = (v > 0.45).astype(np.float32)
    col = np.ones((ctx.H, ctx.W, 3), np.float32)
    return Tex(ctx, col, alpha=m, wrap=True, grain=0)


# ------------------------------------------------------------------ weather
def _streaks(ctx, salt, per_col, length, width, gap_ok=True):
    """Vertical tiling streak layer: list of (mask_value 0..1) per pixel."""
    rng = ctx.rng(salt)
    out = ctx.zeros()
    for col in range(ctx.w):
        for _ in range(per_col):
            if rng.random() < 0.35:
                continue
            y0 = rng.uniform(0, ctx.h)
            ln = rng.uniform(*length)
            yy = (ctx.y - y0) % ctx.h
            t = yy / ln
            m = (ctx.tx == col) & (yy < ln)
            out = np.where(m, np.maximum(out, 1 - t * 0.7), out)
    return out


@texture("environment/rain")
def rain(ctx):
    s = _streaks(ctx, "rain", 3, (10, 26), 1)
    # head of each streak is brightest; fade toward the tail
    a = np.where(s > 0, 0.35 + s * 0.55, 0)
    col = mix(hexc("6f8fd8"), hexc("c8d8ff"), np.clip(s, 0, 1))
    if ctx.pixel_art:
        a = np.round(a * 6) / 6
    return Tex(ctx, col, alpha=a, wrap=True, grain=0)


@texture("environment/snow")
def snow(ctx):
    rng = ctx.rng("snow")
    cv = Canvas(ctx)
    for i in range(150):
        x, y = rng.uniform(0, ctx.w), rng.uniform(0, ctx.h)
        size = rng.choice([1, 1, 1, 2, 2, 3])
        bright = rng.uniform(0.82, 1.0)
        col = np.array([bright, bright, min(1, bright + 0.03)], np.float32)
        x, y = np.floor(x), np.floor(y)
        for ox in (0, -ctx.w, ctx.w):
            for oy in (0, -ctx.h, ctx.h):
                if size == 1:
                    m = ctx.rect(x + ox, y + oy, x + ox + 1, y + oy + 1)
                elif size == 2:
                    m = ctx.rect(x + ox, y + oy, x + ox + 2, y + oy + 2)
                else:   # little plus-shaped flake
                    m = np.maximum(ctx.rect(x + ox - 1, y + oy, x + ox + 2, y + oy + 1),
                                   ctx.rect(x + ox, y + oy - 1, x + ox + 1, y + oy + 2))
                if m.any():
                    cv.put(m, col, 1.0 if size > 1 else 0.85)
                    if size == 3:
                        cv.put(ctx.rect(x + ox, y + oy, x + ox + 1, y + oy + 1), col, 1.0)
    return cv.tex(wrap=True)


@texture("environment/end_sky")
def end_sky(ctx):
    """Light, tiling mottled field (the game multiplies it by a very dark color)."""
    n = ctx.noise(16, 4, 0.55, salt="endsky")
    g = ctx.texel_noise("endsky")
    v = n * 0.75 + g * 0.25
    p = np.stack([hexc(c) for c in ("4a4458", "5e5870", "746d86", "8a839c", "a29bb4")])
    col = ctx.palette(p, v)
    stars = ctx.texel_noise("endstars", soft=False) > 0.985
    col = np.where(stars[..., None], hexc("d8d0f0"), col)
    return Tex(ctx, col, wrap=True, grain=0.05)
