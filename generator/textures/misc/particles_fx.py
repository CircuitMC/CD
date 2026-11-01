"""Particles, part 1: smoke, puffs, magic, sparks, explosions, flames, liquids.

Sequences: a higher index means a later/larger stage unless noted. Particles
the game tints (generic smoke, spell/effect, glitter, spark, flash, note,
drip, sweep, glow...) are painted in white/light gray.
"""
import numpy as np

from ...registry import register, texture
from .common import Canvas, ball_shade, ellipse, gray, hexc, lumpy, mix, polar, ring


def seq(prefix, n, fn, start=0, width=0):
    for i in range(n):
        k = i + start
        name = f"particle/{prefix}{k:0{width}d}" if width else f"particle/{prefix}{k}"
        register(name, (lambda i: (lambda ctx: fn(ctx, i, n)))(i))


def shade_puff(ctx, mask, cx, cy, r, lo=0.62, hi=1.0, steps=4):
    """Light gray value on a puff, lit from the top-left, stepped at 16x."""
    v = ball_shade(ctx, cx, cy, r * 1.1)
    if ctx.pixel_art:
        v = np.floor(v * steps) / max(1, steps - 1)
    v = lo + (hi - lo) * np.clip(v, 0, 1)
    rim = ctx.edge(mask, 1.0, "br") > 0
    return np.where(rim, lo - 0.06, v)


# ------------------------------------------------------------------ generic smoke (tinted)
def generic(ctx, i, n):
    c = ctx.w / 2
    r = [0.55, 1.0, 1.45, 1.85, 2.3, 2.75, 3.2, 3.75][i]
    if i == 0:
        m = ctx.rect(3.5, 3.5, 4.5, 4.5)
    elif i == 1:
        m = np.maximum(ctx.rect(3, 3.5, 5, 4.5), ctx.rect(3.5, 3, 4.5, 5))
    else:
        m = lumpy(ctx, c, c, r, f"gen{i}", amount=0.12 + 0.02 * i)
    cv = Canvas(ctx)
    cv.put(m, np.repeat(shade_puff(ctx, m, c, c, r)[..., None], 3, -1))
    return cv.tex()


seq("generic_", 8, generic)


# ------------------------------------------------------------------ campfire smoke (random variants)
def big_smoke(ctx, i, n):
    rng = ctx.rng(f"bs{i}")
    cv = Canvas(ctx)
    total = ctx.zeros()
    blobs = []
    for k in range(rng.integers(3, 6)):
        cx, cy = rng.uniform(4.5, 11.5), rng.uniform(4.5, 11.5)
        r = rng.uniform(2.2, 4.2)
        blobs.append((cx, cy, r))
        total = np.maximum(total, lumpy(ctx, cx, cy, r, f"bs{i}:{k}", 0.18))
    light = ctx.zeros()
    for cx, cy, r in blobs:
        inside = np.hypot(ctx.x - cx, ctx.y - cy) < r
        light = np.where(inside, np.maximum(light, ball_shade(ctx, cx, cy, r * 1.1)), light)
    if ctx.pixel_art:
        light = np.floor(light * 4) / 3
    v = 0.55 + 0.4 * np.clip(light, 0, 1)
    rim = ctx.edge(total, 1.0, "br") > 0
    v = np.where(rim, 0.5, v)
    cv.put(total, np.stack([v, v, v * 1.02], -1))
    return cv.tex()


seq("big_smoke_", 12, big_smoke)


# ------------------------------------------------------------------ spell / effect / glitter / spark (tinted)
def spell(ctx, i, n):
    """Twinkling 4-point star that grows."""
    c = 4
    arm = 0.8 + i * 0.42
    cv = Canvas(ctx)
    d1 = np.abs(ctx.x - c) + 0.0
    d2 = np.abs(ctx.y - c)
    star = ((d1 * 3.2 + d2 < arm * 1.2 + 0.9) | (d2 * 3.2 + d1 < arm * 1.2 + 0.9)) & (np.maximum(d1, d2) < arm + 0.3)
    core = np.maximum(d1, d2) < 0.6 + i * 0.12
    cv.put(star, gray(0.78))
    cv.put(core & star, gray(1.0))
    return cv.tex()


def effect(ctx, i, n):
    """Small swirling ring with a sparkle: ring opens up as it grows."""
    c = 4
    r = 0.9 + i * 0.36
    d, a = polar(ctx, c, c)
    m = (np.abs(d - r) < 0.62) & (((a + i * 0.6) % (2 * np.pi)) > 1.2 + i * 0.1)
    if i < 2:
        m = d < 1.0 + i * 0.5
    cv = Canvas(ctx)
    cv.put(m, gray(0.82))
    cv.put(m & (ctx.y < c), gray(1.0))
    cv.put(ctx.rect(c - 0.5, c - 0.5, c + 0.5, c + 0.5) * (i >= 2), gray(0.92))
    return cv.tex()


def glitter(ctx, i, n):
    """Sparkle: big 4-arm star at index 7, shrinking to a dot at 0."""
    c = 4
    arm = 0.6 + i * 0.45
    d1, d2 = np.abs(ctx.x - c), np.abs(ctx.y - c)
    cross = ((d1 < 0.5) & (d2 < arm)) | ((d2 < 0.5) & (d1 < arm))
    diag = (np.abs(d1 - d2) < 0.5) & (d1 < arm * 0.45) & (i > 3)
    cv = Canvas(ctx)
    cv.put(cross | diag, gray(0.85))
    cv.put((d1 < 0.6) & (d2 < 0.6), gray(1.0))
    return cv.tex()


def spark(ctx, i, n):
    """Firework spark: bright dot with a soft halo ring, later frames bigger."""
    c = 4
    d, a = polar(ctx, c - 0.0, c - 0.0)
    r = 0.7 + i * 0.4
    cv = Canvas(ctx)
    halo = d < r + 0.6
    cv.put(halo & (ctx.texel_noise(f"sp{i}", soft=False) > 0.25) & (d > r - 0.5), gray(0.7))
    cv.put(d < max(0.7, r * 0.55), gray(1.0))
    rays = (np.abs(np.cos(a * 2)) > 0.97) & (d < r + 1.0) & (i >= 4)
    cv.put(rays, gray(0.9))
    return cv.tex()


seq("spell_", 8, spell)
seq("effect_", 8, effect)
seq("glitter_", 8, glitter)
seq("spark_", 8, spark)


@texture("particle/flash")
def flash(ctx):
    c = ctx.w / 2
    d = np.hypot(ctx.x - c, ctx.y - c) / c
    a = np.clip(1 - d, 0, 1) ** 1.5
    if ctx.pixel_art:
        a = np.round(a * 6) / 6
    cv = Canvas(ctx)
    cv.over(np.ones_like(a), gray(1.0), a)
    return cv.tex()


# ------------------------------------------------------------------ explosion (16 frames, 32x32)
def explosion(ctx, i, n):
    """Fireball: blooms white-yellow, cools to orange and gray, then breaks apart."""
    t = i / (n - 1)
    rng = ctx.rng("expl")
    pts = [(rng.uniform(9, 23), rng.uniform(9, 23), rng.uniform(4, 8)) for _ in range(7)]
    grow = 0.45 + 0.75 * min(1, t * 2.2)
    total = ctx.zeros()
    light = ctx.zeros()
    for k, (cx, cy, r) in enumerate(pts):
        cx = 16 + (cx - 16) * (0.6 + t * 0.6)
        cy = 16 + (cy - 16) * (0.6 + t * 0.6) - t * 2
        rr = r * grow
        m = lumpy(ctx, cx, cy, rr, f"ex{k}", 0.2)
        total = np.maximum(total, m)
        light = np.where(m > 0, np.maximum(light, ball_shade(ctx, cx, cy, rr * 1.1)), light)
    # late frames: holes eat the cloud
    if t > 0.45:
        holes = ctx.noise(5, 2, 0.5, salt="exholes") < (t - 0.45) * 1.6
        total = total * (~holes)
    heat = np.clip(1.25 - t * 1.4 + (light - 0.5) * 0.4, 0, 1)
    if ctx.pixel_art:
        heat = np.floor(heat * 5) / 4
        light = np.floor(light * 4) / 3
    fire = np.where((heat < 0.5)[..., None], mix(hexc("b8300e"), hexc("f27a18"), heat * 2),
                    mix(hexc("f27a18"), hexc("ffe890"), heat * 2 - 1))
    fire = mix(fire, hexc("fffdf0"), np.clip(heat - 0.8, 0, 1) * 4)
    smoke = mix(hexc("4e4a48"), hexc("a8a29c"), light)
    col = mix(fire, smoke, np.clip((t - 0.45) * 2.5 - heat * 0.3, 0, 1))
    rim = ctx.edge(total, 1.0, "br") > 0
    col = np.where(rim[..., None], col * 0.75, col)
    cv = Canvas(ctx)
    cv.put(total, col)
    return cv.tex(emissive=float(max(0, 1 - t * 1.5)))


seq("explosion_", 16, explosion)


# ------------------------------------------------------------------ flames
def flame(ctx, body, core, tip):
    cv = Canvas(ctx)
    c = 4
    outer = ctx.polygon([(4, 0.5), (5.5, 3), (6.5, 5.5), (6, 7), (4.6, 7.8), (3.4, 7.8), (2, 7), (1.5, 5.5), (2.5, 3)])
    inner = ctx.polygon([(4, 3), (5.2, 5.4), (4.8, 7.2), (3.2, 7.2), (2.8, 5.4)])
    cv.put(outer, hexc(tip))
    cv.put(outer * (ctx.y > 2.6), hexc(body))
    cv.put(inner, hexc(core))
    cv.put(ctx.rect(3.5, 6, 4.5, 7.5) * inner, mix(hexc(core), gray(1.0), 0.6))
    return cv.tex(emissive=1.0)


texture("particle/flame")(lambda ctx: flame(ctx, "f2901e", "ffe27a", "d8461a"))
texture("particle/soul_fire_flame")(lambda ctx: flame(ctx, "3cc8d8", "c6fbff", "1a7a9a"))
texture("particle/copper_fire_flame")(lambda ctx: flame(ctx, "4fd690", "d6ffe0", "1e8a62"))


@texture("particle/lava")
def lava(ctx):
    cv = Canvas(ctx)
    m = lumpy(ctx, 4, 4, 2.6, "lava", 0.18)
    v = ball_shade(ctx, 4, 4, 2.9)
    if ctx.pixel_art:
        v = np.floor(v * 3) / 2
    col = mix(hexc("b8320c"), hexc("ffd040"), v)
    col = np.where((ctx.edge(m, 1.0, "br") > 0)[..., None], hexc("7a1c08"), col)
    cv.put(m, col)
    return cv.tex(emissive=1.0)


# ------------------------------------------------------------------ drips & splashes (tinted)
@texture("particle/drip_hang")
def drip_hang(ctx):
    cv = Canvas(ctx)
    m = np.maximum(ctx.rect(3, 0, 5, 2), ellipse(ctx, 4, 3.6, 1.45, 1.9))
    cv.put(m, gray(0.82))
    cv.put(ctx.rect(3, 2.5, 4, 3.5) * m, gray(1.0))
    return cv.tex()


@texture("particle/drip_fall")
def drip_fall(ctx):
    cv = Canvas(ctx)
    m = np.maximum(ctx.polygon([(4, 1.5), (5.4, 4.5), (2.6, 4.5)]), ctx.circle(4, 5, 1.6))
    cv.put(m, gray(0.82))
    cv.put(ctx.rect(3, 4, 4, 5) * m, gray(1.0))
    return cv.tex()


@texture("particle/drip_land")
def drip_land(ctx):
    cv = Canvas(ctx)
    m = np.maximum(ellipse(ctx, 4, 6.4, 3.4, 1.1), ctx.rect(1, 4.5, 2, 5.5) + ctx.rect(6, 4.5, 7, 5.5))
    cv.put(m, gray(0.8))
    cv.put(ctx.rect(2, 5.5, 5, 6.5) * m, gray(0.98))
    return cv.tex()


def splash(ctx, i, n):
    """Rain splash: droplets thrown up and outwards, crown widening."""
    cv = Canvas(ctx)
    col_hi, col = hexc("e4f0ff"), hexc("a8c4ec")
    spread = 1.0 + i * 0.8
    rise = [5.5, 3.8, 2.8, 3.5][i]
    pts = [(4 - spread, rise + 1), (4 + spread, rise + 1), (4 - spread * 0.4, rise), (4 + spread * 0.4, rise - 0.6)]
    for k, (x, y) in enumerate(pts):
        if i == 0 and k > 1:
            continue
        cv.put(ctx.rect(np.floor(x), np.floor(y), np.floor(x) + 1, np.floor(y) + 1 + (k < 2) * (i < 3)), col)
        cv.put(ctx.rect(np.floor(x), np.floor(y), np.floor(x) + 1, np.floor(y) + 1), col_hi)
    cv.put(ctx.rect(4 - spread * 0.7, 7, 4 + spread * 0.7, 8) * (i < 3), col)
    return cv.tex()


seq("splash_", 4, splash)


# ------------------------------------------------------------------ bubbles
def bubble_img(ctx, rim, hi, r=2.6, c=4):
    cv = Canvas(ctx)
    d = np.hypot(ctx.x - c, ctx.y - c)
    m = d < r + 0.5
    edge = ctx.edge(m.astype(np.float32), 1.0) > 0
    cv.put(m, rim, 0.25)
    cv.put(edge, rim, 1.0)
    cv.put(ctx.rect(c - 1.5, c - 1.5, c - 0.5, c - 0.5) * m, hi)
    cv.put(ctx.rect(c - 0.5, c - 2.5, c + 0.5, c - 1.5) * m * (r > 2), hi)
    return cv.tex()


texture("particle/bubble")(lambda ctx: bubble_img(ctx, hexc("9ad0f0"), hexc("f4fcff")))
texture("particle/bubble_white")(lambda ctx: bubble_img(ctx, hexc("e8eef4"), hexc("ffffff")))


def bubble_pop(ctx, i, n):
    """16x16: the bubble stretches, bursts into a ring of droplets that fly apart."""
    c = 8
    cv = Canvas(ctx)
    col, hi = hexc("9ad0f0"), hexc("f4fcff")
    if i == 0:
        r = 3.2
        d = np.hypot(ctx.x - c, ctx.y - c)
        m = (d < r + 0.5).astype(np.float32)
        cv.put(ctx.edge(m, 1.0) > 0, col)
        cv.put(ctx.rect(6, 6, 7, 7), hi)
        return cv.tex()
    k = 6 + i
    rad = 2.5 + i * 1.3
    for j in range(k):
        a = j / k * 2 * np.pi + i * 0.2
        x, y = c + np.cos(a) * rad, c + np.sin(a) * rad
        sz = 1 if i > 2 else 2 - (j % 2)
        x0, y0 = np.floor(x), np.floor(y)
        cv.put(ctx.rect(x0, y0, x0 + sz, y0 + sz), col if (j + i) % 3 else hi)
    return cv.tex()


seq("bubble_pop_", 5, bubble_pop)


# ------------------------------------------------------------------ hits / damage
@texture("particle/critical_hit")
def critical_hit(ctx):
    """Tinted: jagged 6-point burst."""
    d, a = polar(ctx, 4, 4)
    r = 1.4 + 2.4 * (np.abs(np.cos(a * 3)) ** 3)
    cv = Canvas(ctx)
    m = d < r
    cv.put(m, gray(0.75))
    cv.put(d < 1.2, gray(1.0))
    return cv.tex()


@texture("particle/enchanted_hit")
def enchanted_hit(ctx):
    """Tinted: hollow diamond with a sparkle core."""
    du, dv = np.abs(ctx.x - 4), np.abs(ctx.y - 4)
    dia = du + dv
    cv = Canvas(ctx)
    cv.put((dia > 2.2) & (dia < 3.6), gray(0.78))
    cv.put(((du < 0.5) & (dv < 1.5)) | ((dv < 0.5) & (du < 1.5)), gray(1.0))
    return cv.tex()


@texture("particle/sweep_0", "particle/sweep_1", "particle/sweep_2", "particle/sweep_3",
         "particle/sweep_4", "particle/sweep_5", "particle/sweep_6", "particle/sweep_7")
def sweep(ctx):
    """Tinted crescent slash: grows from a thin sliver to a wide arc, then thins out."""
    i = int(ctx.name.rsplit("_", 1)[1])
    t = i / 7
    d, a = polar(ctx, 16, 25)
    r_out = 17
    thick = 2 + 5 * np.sin(np.pi * min(1, t * 1.15))
    span = 0.7 + 1.9 * min(1, t * 1.6)
    ang = (a + np.pi / 2)            # 0 = straight up
    m = (d < r_out) & (d > r_out - thick * (1 - np.abs(ang) / span * 0.6)) & (np.abs(ang) < span / 2 + 0.1)
    m &= ~((t > 0.7) & (ctx.noise(3, 2, 0.5, salt="swp") < (t - 0.7) * 2.5))
    v = 0.7 + 0.3 * np.clip((d - (r_out - thick)) / max(thick, 1), 0, 1)
    if ctx.pixel_art:
        v = np.floor(v * 4) / 4
    cv = Canvas(ctx)
    cv.put(m, np.repeat(v[..., None], 3, -1))
    return cv.tex()


HEART = ["........",
         ".oo..oo.",
         "o++oo##o",
         "o+#####o",
         "o######o",
         ".o####o.",
         "..o##o..",
         "...oo..."]


def heart_img(ctx, rows, outline, body, hi, crack=None):
    cv = Canvas(ctx)
    pal = {"o": hexc(outline), "#": hexc(body), "+": hexc(hi)}
    rgb, m = ctx.texels(rows, pal)
    if not ctx.pixel_art:   # round the stair steps at high res, keep colors
        full = ctx.organic(m).astype(np.float32)
        inner = ctx.organic(m * (rgb != hexc(outline)).any(-1)).astype(np.float32)
        rgb = np.where((full > 0)[..., None] & (inner == 0)[..., None], hexc(outline), rgb)
        rgb = np.where((inner > 0)[..., None] & (m == 0)[..., None], hexc(body), rgb)
        m = full
    cv.put(m, rgb)
    if crack is not None:
        cv.put(crack * (m > 0), hexc(outline))
    return cv.tex()


@texture("particle/damage")
def damage(ctx):
    """Dark red cracked heart."""
    crack = ((np.abs(ctx.x - 4 - np.where(ctx.ty % 2 == 0, 0.5, -0.5)) < 0.5) & (ctx.y > 1.5) & (ctx.y < 6.5))
    return heart_img(ctx, HEART, "3a0406", "8a1418", "b8302c", crack)


@texture("particle/heart")
def heart(ctx):
    return heart_img(ctx, HEART, "7a0c1a", "dc2a3a", "ff9ca2")


def goldheart(ctx, i, n):
    """8x7: golden heart that glints across its three frames."""
    rows = [r for r in HEART[1:]]
    if i == 1:
        rows[1] = "o#+oo##o"; rows[2] = "o#+####o"
    if i == 2:
        rows[1] = "o##oo+#o"; rows[2] = "o####+#o"
    t = heart_img(ctx, rows, "8a5206", "f0b42a", "fff2a8")
    return t


seq("goldheart_", 3, goldheart)


@texture("particle/angry")
def angry(ctx):
    """Anger mark: four red curved brackets around a point."""
    cv = Canvas(ctx)
    d1, d2 = ctx.x - 4, ctx.y - 4
    m = ctx.zeros()
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = (np.sign(d1) == sx) & (np.sign(d2) == sy)
            dd = np.hypot(d1 - sx * 3.2, d2 - sy * 3.2)
            m = np.maximum(m, (q & (dd < 2.6) & (dd > 1.3)).astype(np.float32))
    cv.put(m, hexc("d8202a"))
    cv.put(m * (ctx.edge(m, 1.0, "br") > 0), hexc("7a0a12"))
    return cv.tex()


@texture("particle/note")
def note(ctx):
    """Tinted eighth note."""
    cv = Canvas(ctx)
    head = ellipse(ctx, 2.9, 6.0, 1.9, 1.35, -0.4)
    stem = ctx.rect(4, 1, 5, 6)
    flag = np.maximum(ctx.rect(5, 1, 6, 2), ctx.rect(6, 2, 7, 4))
    m = np.maximum.reduce([head, stem, flag])
    cv.put(m, gray(0.85))
    cv.put(ctx.rect(2, 5, 3, 6) * head, gray(1.0))
    return cv.tex()


@texture("particle/glint")
def glint(ctx):
    cv = Canvas(ctx)
    du, dv = np.abs(ctx.x - 4), np.abs(ctx.y - 4)
    star = ((du < 0.5) & (dv < 3.5)) | ((dv < 0.5) & (du < 3.5)) | ((du < 1.5) & (dv < 1.5) & (du + dv < 2))
    cv.put(star, gray(0.86))
    cv.put((du < 0.5) & (dv < 0.5), gray(1.0))
    return cv.tex()


@texture("particle/glow")
def glow(ctx):
    cv = Canvas(ctx)
    d = np.hypot(ctx.x - 4, ctx.y - 4)
    cv.put(d < 3.3, gray(0.7), 0.55)
    cv.put(d < 2.3, gray(0.88))
    cv.put(d < 1.2, gray(1.0))
    return cv.tex()
