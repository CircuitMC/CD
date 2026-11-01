"""Particles, part 2: leaves & petals, souls & sculk, wind, trial/vault/omen,
enchanting glyphs, geysers, gas and misc creature particles."""
import numpy as np

from ...registry import register, texture
from .common import Canvas, ball_shade, ellipse, gray, hexc, lumpy, mix, polar, ring
from .particles_fx import seq


# ------------------------------------------------------------------ leaves & petals
LEAF_SHAPES_5 = [  # 5x5 leaf silhouettes: '#' body, '+' highlight, 'o' dark vein/edge
    [".##..", "#+##.", "##o#.", ".#o##", "...##"],
    ["..#..", ".#+#.", ".#o#.", "##o##", "..#.."],
    ["...##", ".##+#", "#+o#.", "#o##.", "##..."],
    [".....", "##+#.", "#+o##", ".##o#", "...#."],
    ["..##.", ".#+##", "#+o#.", "##o..", ".#..."],
    ["#....", "##+#.", ".#o#.", ".#+o#", "...##"],
]


def leaf5(ctx, i, cols, salt):
    rows = LEAF_SHAPES_5[(i * 5 + 1) % len(LEAF_SHAPES_5)]
    if (i // len(LEAF_SHAPES_5)) % 2:
        rows = [r[::-1] for r in rows]
    if (i // 3) % 2:
        rows = rows[::-1]
    pal = {"#": hexc(cols[1]), "+": hexc(cols[2]), "o": hexc(cols[0])}
    rgb, m = ctx.texels(rows, pal)
    cv = Canvas(ctx)
    cv.put(m, rgb)
    return cv.tex()


def leaf_series(prefix, n, cols, start=0):
    for k in range(n):
        idx = k + start
        register(f"particle/{prefix}{idx}", (lambda k: (lambda ctx: leaf5(ctx, k, cols, prefix)))(k))


leaf_series("leaf_", 12, ("8a8a8a", "b4b4b4", "dadada"))                 # tinted by foliage color
leaf_series("pale_oak_", 12, ("8e9488", "b8bdb2", "dfe2da"))
leaf_series("orange_poplar_", 4, ("a8501a", "e0802a", "f8b250"), start=1)
leaf_series("red_poplar_", 4, ("801a1a", "c43226", "ec6a4a"), start=1)
leaf_series("yellow_poplar_", 4, ("a8861a", "e4c432", "fbe68a"), start=1)

PETALS_3 = [["#+.", "##o", ".o."], [".#.", "#+#", ".o."], ["+#.", "#o#", "..#"], [".+#", "##o", "#.."],
            ["##.", "+#o", ".#."], [".#+", "#o.", "#.."]]


def cherry(ctx, i, n):
    rows = PETALS_3[i % 6]
    if i >= 6:
        rows = [r[::-1] for r in rows[::-1]]
    rgb, m = ctx.texels(rows, {"#": hexc("f0a2c4"), "+": hexc("ffd4e6"), "o": hexc("d0709c")})
    cv = Canvas(ctx)
    cv.put(m, rgb)
    return cv.tex()


seq("cherry_", 12, cherry)


# ------------------------------------------------------------------ souls
def soul_face(ctx, cv, cx, cy, s, body, dark, alpha=1.0):
    """Little wailing ghost: rounded head, wavy tail, two eyes and an open mouth."""
    head = ellipse(ctx, cx, cy, 3.0 * s, 3.2 * s)
    tail = ctx.polygon([(cx - 3 * s, cy), (cx + 3 * s, cy), (cx + 1.5 * s, cy + 5.5 * s),
                        (cx + 0.2 * s, cy + 4 * s), (cx - 1.2 * s, cy + 6 * s)])
    m = np.maximum(head, tail)
    cv.put(m, body, alpha)
    cv.put(m * (ctx.edge(m, 1.0, "br") > 0), dark, alpha)
    for ex in (-1.2, 1.2):
        cv.put(ctx.rect(np.floor(cx + ex * s) - 0.0, np.floor(cy - 0.8 * s),
                        np.floor(cx + ex * s) + 1, np.floor(cy - 0.8 * s) + 1 + (s > 0.9)), dark, alpha)
    cv.put(ellipse(ctx, cx, cy + 1.4 * s, 0.9 * s, 1.1 * s), dark, alpha)


def soul(ctx, i, n):
    """Soul from soul sand/fire: forms, rises and dissolves (11 frames)."""
    t = i / (n - 1)
    cv = Canvas(ctx)
    s = 0.55 + 0.45 * min(1, t * 3)
    cy = 7 - t * 2
    body = mix(hexc("8ae6f0"), hexc("d8fbff"), 0.5)
    soul_face(ctx, cv, 8, cy, s, body, hexc("2a8a9a"))
    if t > 0.55:
        holes = ctx.noise(2, 2, 0.5, salt="soulfade") < (t - 0.55) * 1.7
        cv.alpha = np.where(holes, 0, cv.alpha)
    return cv.tex(emissive=1.0)


def sculk_soul(ctx, i, n):
    t = i / (n - 1)
    cv = Canvas(ctx)
    s = 0.5 + 0.5 * min(1, t * 2.5)
    cy = 7.5 - t * 2.5
    soul_face(ctx, cv, 8, cy, s, hexc("2fd4d8"), hexc("0a4a58"))
    cv.put(ctx.rect(7, cy - 1, 9, cy) * (t < 0.3), hexc("c8ffff"))
    if t > 0.5:
        holes = ctx.noise(2, 2, 0.5, salt="sculkfade") < (t - 0.5) * 1.6
        cv.alpha = np.where(holes, 0, cv.alpha)
    return cv.tex(emissive=1.0)


seq("soul_", 11, soul)
seq("sculk_soul_", 11, sculk_soul)


def sculk_charge(ctx, i, n):
    """Charge travelling over sculk: a cross of teal dashes that spreads, then fades."""
    t = i / (n - 1)
    cv = Canvas(ctx)
    r = 1.5 + t * 5
    d, a = polar(ctx, 8, 8)
    arms = (np.abs(np.sin(a * 2)) < 0.28) & (np.abs(d - r) < 1.2)
    dots = (np.abs(np.cos(a * 2)) < 0.2) & (np.abs(d - r * 0.6) < 0.7)
    col = mix(hexc("0e8a9a"), hexc("6ffbff"), 1 - t)
    cv.put(arms, col)
    cv.put(dots & (t < 0.8), hexc("0a5a6a"))
    cv.put(np.maximum(ctx.rect(7, 6, 9, 10), ctx.rect(6, 7, 10, 9)) * (t < 0.2), hexc("2fd4d8"))
    cv.put(ctx.rect(7, 7, 9, 9) * (t < 0.4), hexc("e0ffff"))
    return cv.tex(emissive=1.0)


def sculk_charge_pop(ctx, i, n):
    cv = Canvas(ctx)
    k = 6
    rad = 2 + i * 1.5
    for j in range(k):
        a = j / k * 2 * np.pi + 0.3
        x, y = np.floor(8 + np.cos(a) * rad), np.floor(8 + np.sin(a) * rad)
        cv.put(ctx.rect(x, y, x + 1 + (i < 2), y + 1 + (i < 2)), hexc("2fd4d8") if j % 2 else hexc("9cffff"))
    return cv.tex(emissive=1.0)


seq("sculk_charge_", 7, sculk_charge)
seq("sculk_charge_pop_", 4, sculk_charge_pop)


@texture("particle/shriek")
def shriek(ctx):
    """13x13: double ring (the game lays it flat and lets it rise)."""
    cv = Canvas(ctx)
    cv.put(ring(ctx, 6.5, 6.5, 5.6, 1.1), hexc("2fd4d8"))
    cv.put(ring(ctx, 6.5, 6.5, 3.4, 1.0), hexc("8ffcff"))
    return cv.tex(emissive=1.0)


def sonic_boom(ctx, i, n):
    """Expanding cyan shock ring with inner ripples, fading to thin arcs."""
    t = i / (n - 1)
    cv = Canvas(ctx)
    r = 3 + t * 11.5
    w = 3.2 - t * 2.0
    d, a = polar(ctx, 16, 16)
    outer = np.abs(d - r) < w / 2
    inner = np.abs(d - r * 0.62) < max(0.6, w * 0.3)
    breaks = ctx.noise(4, 1, 0.5, salt=f"sb", detail=False) < t * 0.7
    cv.put(inner & ~breaks & (t < 0.85), hexc("1a8aa0"))
    cv.put(outer & ~breaks, mix(hexc("bffcff"), hexc("2ac4dc"), t))
    cv.put(outer & ~breaks & (d < r - w * 0.15), hexc("eaffff") if t < 0.5 else hexc("5ae0f0"))
    return cv.tex(emissive=1.0)


seq("sonic_boom_", 16, sonic_boom)


# ------------------------------------------------------------------ wind
def gust(ctx, i, n, size=32):
    """Spiral wind swirl drawn as curling white strokes; it unwinds and fades."""
    t = i / (n - 1)
    c = size / 2
    d, a = polar(ctx, c, c)
    turns = 1.6 - t * 0.8
    sp = (a / (2 * np.pi)) % 1
    # archimedean spiral: radius grows with angle
    k = size * 0.12
    m = ctx.zeros() > 1
    for lap in range(3):
        rr = (sp + lap) * k * (1 + t * 0.6)
        m |= (np.abs(d - rr) < 0.75 * size / 32 + 0.25) & (sp + lap < turns + 1.2)
    m &= d > size * 0.06
    m &= ~(ctx.noise(size / 6, 2, 0.5, salt="gustcut") < t * 0.65)
    cv = Canvas(ctx)
    cv.put(m, gray(0.96), 0.95)
    cv.put(m & (ctx.edge(m.astype(np.float32), 1.0, "br") > 0), gray(0.78), 0.95)
    return cv.tex()


seq("gust_", 12, gust)
seq("small_gust_", 7, lambda ctx, i, n: gust(ctx, i, n, size=8))


# ------------------------------------------------------------------ trial / vault / omen
def detection(ctx, i, n, cols):
    """Little flickering wisp: a teardrop flame that shrinks to an ember."""
    cv = Canvas(ctx)
    s = 1 - i * 0.17
    body = ctx.polygon([(4, 4 - 3.4 * s), (4 + 2.4 * s, 5), (4, 7.4), (4 - 2.4 * s, 5)])
    core = ctx.circle(4, 5.4, 1.2 * s)
    cv.put(body, hexc(cols[0]))
    cv.put(body * (ctx.y > 4), hexc(cols[1]))
    cv.put(core, hexc(cols[2]))
    return cv.tex(emissive=1.0)


seq("trial_spawner_detection_", 5, lambda c, i, n: detection(c, i, n, ("c4501c", "f29a30", "ffe9a0")))
seq("trial_spawner_detection_ominous_", 5, lambda c, i, n: detection(c, i, n, ("1e6aa0", "3cb6e0", "d6f6ff")))


@texture("particle/vault_connection")
def vault_connection(ctx):
    cv = Canvas(ctx)
    du, dv = np.abs(ctx.x - 4), np.abs(ctx.y - 4)
    cv.put(du + dv < 3.2, hexc("c47c1c"))
    cv.put(du + dv < 2.0, hexc("f6c04a"))
    cv.put((du < 0.5) & (dv < 0.5), hexc("fff4c8"))
    return cv.tex(emissive=1.0)


@texture("particle/raid_omen")
def raid_omen(ctx):
    rows = ["#...#", ".#o#.", "..o..", ".#o#.", "#...#"]
    rgb, m = ctx.texels(rows, {"#": hexc("b8262a"), "o": hexc("3a3a40")})
    return Canvas(ctx).put(m, rgb).tex()


@texture("particle/trial_omen")
def trial_omen(ctx):
    rows = [".#.#.", "#o.o#", "..#..", "#o.o#", ".#.#."]
    rgb, m = ctx.texels(rows, {"#": hexc("2a9ab8"), "o": hexc("c8f4ff")})
    return Canvas(ctx).put(m, rgb).tex(emissive=1.0)


@texture("particle/ominous_spawning")
def ominous_spawning(ctx):
    """16x16 spiral sigil in deep blue and violet."""
    d, a = polar(ctx, 8, 8)
    sp = np.abs(((a / (2 * np.pi) * 2 + d / 3.0) % 1) - 0.5) < 0.16
    cv = Canvas(ctx)
    cv.put(sp & (d < 7) & (d > 1.5), hexc("3a5ad8"))
    cv.put(sp & (d < 4) & (d > 1.5), hexc("9a7cf4"))
    cv.put(d < 1.5, hexc("e6dcff"))
    return cv.tex(emissive=1.0)


@texture("particle/infested")
def infested(ctx):
    """Stone chip flicked off an infested block."""
    cv = Canvas(ctx)
    m = ctx.polygon([(2, 2.5), (5.5, 1.5), (6.5, 4.5), (4.5, 6.5), (1.5, 5.5)])
    v = ball_shade(ctx, 4, 4, 3.4)
    col = mix(hexc("5c5c62"), hexc("a8a8ae"), np.floor(v * 3) / 2 if ctx.pixel_art else v)
    cv.put(m, col)
    cv.put(m * (ctx.edge(m, 1.0, "br") > 0), hexc("46464c"))
    return cv.tex()


@texture("particle/nautilus")
def nautilus(ctx):
    """Spiral shell with banded stripes."""
    d, a = polar(ctx, 4.2, 4.2)
    r_sp = 1.0 + ((a + np.pi) / (2 * np.pi)) * 2.6
    m = (d < r_sp + 0.4).astype(np.float32)
    band = (np.floor((a + np.pi) / (np.pi / 3)) % 2 == 0)
    cv = Canvas(ctx)
    cv.put(m, np.where(band[..., None], hexc("e8dcc4"), hexc("c4744a")))
    cv.put(m * (ctx.edge(m, 1.0) > 0), hexc("7a4a2c"))
    cv.put(ctx.circle(4.2, 4.2, 0.9), hexc("4a2a18"))
    return cv.tex()


@texture("particle/firefly")
def firefly(ctx):
    d = np.hypot(ctx.x - 4, ctx.y - 4)
    cv = Canvas(ctx)
    cv.put(d < 3.5, hexc("d8f060"), 0.3)
    cv.put(d < 2.4, hexc("e8fa7a"), 0.65)
    cv.put(d < 1.3, hexc("fbffd0"))
    return cv.tex(emissive=1.0)


# ------------------------------------------------------------------ enchanting glyphs (original runes)
def glyph_strokes(letter):
    """Deterministic original rune for a letter: 2-4 strokes on a 3x4 node grid."""
    k = ord(letter) - ord("a")
    rng = np.random.default_rng(1000 + k * 7919)
    nodes = [(x, y) for y in range(4) for x in range(3)]
    strokes = [((1, 0), (1, 3))] if k % 3 == 0 else [((0, 0), (0, 3))] if k % 3 == 1 else [((0, 0), (2, 0))]
    while len(strokes) < 2 + k % 3:
        a = nodes[rng.integers(len(nodes))]
        b = nodes[rng.integers(len(nodes))]
        if a == b or (abs(a[0] - b[0]) > 0 and abs(a[1] - b[1]) > 0 and abs(a[0] - b[0]) != abs(a[1] - b[1])):
            continue
        strokes.append((a, b))
    return strokes


def sga(ctx):
    letter = ctx.name[-1]
    cv = Canvas(ctx)
    m = ctx.zeros()
    for (x1, y1), (x2, y2) in glyph_strokes(letter):
        px = lambda gx: 1.5 + gx * 2.5
        py = lambda gy: 0.5 + gy * 2.0 + 0.5
        m = np.maximum(m, ctx.segment(px(x1), py(y1), px(x2), py(y2), 1.05))
    if ctx.pixel_art:
        m = (m > 0.5).astype(np.float32)
    cv.put(m, gray(0.96))
    return cv.tex()


for _c in "abcdefghijklmnopqrstuvwxyz":
    register(f"particle/sga_{_c}", sga)


# ------------------------------------------------------------------ vibration (animated 18x18, 7 frames)
@texture("particle/vibration")
def vibration(ctx):
    """Travelling signal: a diamond pulse whose rings breathe across the frames."""
    t = ctx.frame / max(1, ctx.frames)
    du, dv = np.abs(ctx.x - 9), np.abs(ctx.y - 9)
    dia = du + dv
    cv = Canvas(ctx)
    r1 = 2 + 5 * t
    r2 = 2 + 5 * ((t + 0.5) % 1)
    for r in (r1, r2):
        cv.put((np.abs(dia - r) < 0.75), mix(hexc("6ffbff"), hexc("1a8aa0"), (r - 2) / 5))
    cv.put(dia < 1.6, hexc("d8ffff"))
    return cv.tex(emissive=1.0)


# ------------------------------------------------------------------ geysers, gas, goo
def geyser_base(ctx, i, n):
    """Bubbling ground vent: churning steam bulges at the bottom."""
    cv = Canvas(ctx)
    rng = ctx.rng("gbase")
    total = ctx.zeros()
    for k in range(5):
        cx = rng.uniform(3, 13)
        ph = rng.uniform(0, 1)
        h = 2.5 + 2.5 * np.sin(2 * np.pi * (i / n + ph)) ** 2
        total = np.maximum(total, ellipse(ctx, cx, 15 - h * 0.5, 2.6, h))
    v = np.clip((ctx.y - 8) / 8, 0, 1)
    col = mix(hexc("f2f0e4"), hexc("c8c2a0"), v)
    cv.put(total, col)
    cv.put(total * (ctx.edge(total, 1.0, "br") > 0), hexc("a8a080"))
    return cv.tex()


def geyser_plume(ctx, i, n):
    """Rising column of steam; puffs scroll upward through the frames."""
    cv = Canvas(ctx)
    total = ctx.zeros()
    for k in range(5):
        y = 16 - ((k * 4 + i * 2) % 20)
        r = 2.4 + 0.25 * k
        cx = 8 + np.sin(k * 1.7 + i * 0.4) * 1.2
        total = np.maximum(total, lumpy(ctx, cx, y, r, f"plume{k}", 0.15))
    light = ball_shade(ctx, 8, 8, 9)
    col = mix(hexc("d6d2c0"), hexc("ffffff"), np.floor(light * 3) / 2 if ctx.pixel_art else light)
    cv.put(total, col)
    return cv.tex()


def geyser_poof(ctx, i, n):
    t = i / (n - 1)
    cv = Canvas(ctx)
    r = 2 + t * 5
    m = lumpy(ctx, 8, 8, r, "gpoof", 0.22)
    if t > 0.4:
        m = m * (ctx.noise(3, 2, 0.5, salt="gpoofh") > (t - 0.4) * 1.4)
    v = ball_shade(ctx, 8, 8, r * 1.1)
    col = mix(hexc("cfc9b0"), hexc("ffffff"), np.floor(v * 3) / 2 if ctx.pixel_art else v)
    cv.put(m, col)
    return cv.tex()


def noxious_gas(ctx, i, n):
    """Sickly yellow-green cloud that swells and thins out."""
    t = i / (n - 1)
    cv = Canvas(ctx)
    r = 3 + t * 4
    m = lumpy(ctx, 8, 8.5 - t, r, "nox", 0.25)
    if t > 0.35:
        m = m * (ctx.noise(3, 2, 0.5, salt="noxh") > (t - 0.35) * 1.3)
    v = ball_shade(ctx, 8, 8, r * 1.1)
    if ctx.pixel_art:
        v = np.floor(v * 3) / 2
    col = mix(hexc("7a8a24"), hexc("d4e060"), v)
    cv.put(m, col, 0.85)
    return cv.tex()


seq("geyser_base_", 8, geyser_base, start=1, width=2)
seq("geyser_plume_", 8, geyser_plume, start=1, width=2)
seq("geyser_poof_", 8, geyser_poof, start=1, width=2)
seq("noxious_gas_", 8, noxious_gas, start=1, width=2)


@texture("particle/sulfur_cube_goo")
def sulfur_cube_goo(ctx):
    """Blob of yellow goo with a drip."""
    cv = Canvas(ctx)
    m = np.maximum(lumpy(ctx, 8, 7, 4.5, "goo", 0.15), ellipse(ctx, 9.5, 12.5, 1.4, 2.4))
    v = ball_shade(ctx, 8, 7, 5)
    if ctx.pixel_art:
        v = np.floor(v * 4) / 3
    col = mix(hexc("a88a10"), hexc("f4e04a"), v)
    cv.put(m, col)
    cv.put(m * (ctx.edge(m, 1.0, "br") > 0), hexc("7a620a"))
    cv.put(ctx.rect(5, 4, 7, 5) * m, hexc("fffbc8"))
    return cv.tex()
