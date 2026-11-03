"""Dial / readout items: recovery compass frames, light block levels, explorer maps."""
import math

import numpy as np

from ...registry import register
from .h_lib import (U, box, cells, compose, ellipse, metal, paint, pal, ramp, rgb, ring, rows_mask, seg, spr, union, IRON)
from ...sprites import flat

# ------------------------------------------------------------ recovery compass
CASE = pal("0a1418", "16262c", "24383e", "345058", "4a6a72")
FACE = pal("06282e", "0c3a42", "145058")
NEEDLE = pal("0e6a70", "26b8b8", "6af0e8", "c8fff8")


def recovery_compass(ctx, i):
    k = ctx.w / 16
    body = ellipse(ctx, 8, 8, 6.6, 6.6)
    t = spr(ctx, body, CASE, smooth=0.55, bevel=1.5)
    face = ellipse(ctx, 8, 8, 4.6, 4.6)
    paint(t, face, FACE[1])
    paint(t, ring(ctx, 8, 8, 4.0, 4.6), FACE[0])
    # sculk-ish catalyst dots on the case
    paint(t, cells(ctx, [(8, 1), (14, 8), (8, 14), (1, 8)]), NEEDLE[1], emissive=0.4)
    paint(t, cells(ctx, [(4, 3), (3, 4)]), CASE[4])
    a = (i / 32 + 0.5) * 2 * math.pi  # frame 16: needle up (target ahead), 00: down; clockwise
    dx, dy = math.sin(a), -math.cos(a)
    cx, cy = 8.0, 8.0
    tip = seg(ctx, cx, cy, cx + dx * 3.9, cy + dy * 3.9, 1.3)
    tail = seg(ctx, cx, cy, cx - dx * 2.4, cy - dy * 2.4, 1.1)
    paint(t, tail, CASE[4])
    paint(t, tip, NEEDLE[2], emissive=0.7)
    paint(t, seg(ctx, cx + dx * 2.0, cy + dy * 2.0, cx + dx * 3.9, cy + dy * 3.9, 1.0), NEEDLE[3], emissive=0.9)
    if ctx.s > 1:
        paint(t, seg(ctx, cx, cy, cx + dx * 3.5, cy + dy * 3.5, 0.5), NEEDLE[3], emissive=0.9)
    hub = ellipse(ctx, 8, 8, 0.7, 0.7) if ctx.s > 1 else cells(ctx, [(int(cx - 0.5 + 0.5), int(cy - 0.5 + 0.5))])
    paint(t, hub, CASE[3])
    return t


for _i in range(32):
    register(f"item/recovery_compass_{_i:02d}", lambda ctx, i=_i: recovery_compass(ctx, i))

# ------------------------------------------------------------------ light
DIGITS = {
    "0": ["###", "#.#", "#.#", "#.#", "###"], "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["###", "..#", "###", "#..", "###"], "3": ["###", "..#", ".##", "..#", "###"],
    "4": ["#.#", "#.#", "###", "..#", "..#"], "5": ["###", "#..", "###", "..#", "###"],
    "6": ["###", "#..", "###", "#.#", "###"], "7": ["###", "..#", ".#.", ".#.", ".#."],
    "8": ["###", "#.#", "###", "#.#", "###"], "9": ["###", "#.#", "###", "..#", "###"],
}


def digits_mask(ctx, text, x0, y0):
    m = ctx.zeros()
    x = x0
    for ch in text:
        m = np.maximum(m, rows_mask(ctx, DIGITS[ch], x0=x, y0=y0))
        x += 4
    return m


def light(ctx, level):
    """Glowing light bulb (brightness grows with the level) plus the level number."""
    f = level / 15
    core = mix_pal(f)
    cx, cy, r = 6.6, 5.8, 4.4
    k = ctx.w / 16
    # halo rays for bright levels
    rays = ctx.zeros()
    for j in range(min(8, (level + 1) // 2)):
        a = math.pi + j / 8 * 2 * math.pi
        rays = np.maximum(rays, seg(ctx, cx + math.cos(a) * (r + 0.7), cy + math.sin(a) * (r + 0.7),
                                    cx + math.cos(a) * (r + 1.5), cy + math.sin(a) * (r + 1.5), 0.9))
    rays = rays * (1 - box(ctx, 9.0, 9.0, 16, 16))
    rt = flat(ctx, rays, core[-2], emissive=f)
    bulb = U(ellipse(ctx, cx, cy, r, r), box(ctx, cx - 2.0, cy + 2.0, cx + 2.0, cy + 5.0))
    glass = pal("3a3a40", "6a6a72")
    t = spr(ctx, bulb, np.concatenate([glass[:1], core]), smooth=0.9, bevel=3, emissive=0.1 + 0.9 * f)
    ring = ctx.edge(bulb, 1) > 0
    inner = (bulb > 0.5) & ~ring
    # filament (visible when dim), highlight
    fil = U(seg(ctx, cx - 1.4, cy + 1.6, cx - 1.0, cy - 0.6, 0.6), seg(ctx, cx + 1.4, cy + 1.6, cx + 1.0, cy - 0.6, 0.6),
            seg(ctx, cx - 1.0, cy - 0.6, cx + 1.0, cy - 0.6, 0.6))
    paint(t, (fil > 0.5) & inner, mix_pal(1.0)[3] if level else rgb("8a6a4a"), emissive=0.4 + 0.6 * f)
    paint(t, (cells(ctx, [(4, 3), (3, 4), (4, 4)]) > 0.5) & inner, rgb("ffffff") * (0.75 + 0.25 * f))
    base_m = box(ctx, cx - 2.0, cy + 5.0, cx + 2.0, cy + 8.0)
    tb = metal(ctx, base_m, pal("3a3a40", "6e6e76", "9a9aa2", "c4c4cc"), IRON, bevel=1)
    paint(tb, box(ctx, 0, cy + 6.0, 16, cy + 7.0), rgb("4e4e56"))
    txt = str(level)
    w = 4 * len(txt) - 1
    dm = digits_mask(ctx, txt, 16 - w - (0 if level >= 10 else 1), 10)
    g = dm > 0.5
    s1 = ctx.s * int(k)
    shadow = np.zeros_like(g)
    for oy in (-s1, 0, s1):
        for ox in (-s1, 0, s1):
            shadow |= np.roll(np.roll(g, oy, 0), ox, 1)
    shadow &= ~g
    sh = flat(ctx, shadow, rgb("1e1a12"))
    dg = flat(ctx, dm, rgb("fff6d0") if level else rgb("b0aca0"), emissive=0.3 + 0.5 * f)
    return compose(ctx, rt, t, tb, sh, dg)


def mix_pal(f):
    dim = np.stack([rgb(c) for c in ("2a2a30", "4a4a52", "6a6a74", "8a8a94", "aaaab4")])
    hot = np.stack([rgb(c) for c in ("8a5a10", "e0a020", "f8d040", "fff08a", "fffbe0")])
    return (dim * (1 - f) + hot * f).astype(np.float32)


for _l in range(16):
    register(f"item/light_{_l:02d}", lambda ctx, l=_l: light(ctx, l))

# ------------------------------------------------------------------ maps
PAPER = pal("6a5a3e", "a89470", "cdbb92", "e2d4ae", "f2e8cc")
LAND = rgb("a8b46a")
WATER = rgb("6a90b4")
INK = rgb("4a3a26")


def map_base(ctx, inner=True):
    m = rows_mask(ctx, ["############"] * 12, x0=2, y0=2, round_=0.05)
    t = spr(ctx, m, PAPER, smooth=0.15, porosity=0.6, bevel=1)
    edge = ctx.edge(m, 1) > 0
    inr = (m > 0.5) & ~(ctx.edge(m, 2) > 0)
    paint(t, (ctx.edge(m, 2) > 0) & ~edge, PAPER[3])
    return t, inr, edge


def empty_map(ctx):
    t, inr, edge = map_base(ctx)
    paint(t, inr, PAPER[2])
    grid = cells(ctx, [(x, y) for x in range(4, 12) for y in range(4, 12) if (x % 3 == 1 or y % 3 == 1) and (x + y) % 2])
    paint(t, (grid > 0.5) & inr, PAPER[1])
    return t


# explorer maps: (land color, water fraction style, marker rows 5x5, marker color)
MARKERS = {
    "jungle_pyramid": ("5a9a3a", "land", ["..#..", ".###.", "#####", ".###.", "#####"], "8a8a6a"),
    "ocean_monument": ("4a7aa4", "sea", ["#.#.#", "#####", "#.#.#", "#####", "#####"], "4ab0a0"),
    "plains_village": ("8ab454", "land", ["..#..", ".###.", "#####", ".#.#.", ".###."], "9a6a3a"),
    "savanna_village": ("b4a85a", "land", ["..#..", ".###.", "#####", ".#.#.", ".###."], "b0582a"),
    "snowy_village": ("e6eef0", "land", ["..#..", ".###.", "#####", ".#.#.", ".###."], "6a4a2a"),
    "swamp_hut": ("5a6a3a", "marsh", ["..#..", ".###.", "#####", ".###.", "#.#.#"], "4a3a2a"),
    "taiga_village": ("4a7a4a", "land", ["..#..", ".###.", "#####", ".#.#.", ".###."], "5a3a22"),
    "warm_ocean_ruins": ("3a9ab4", "sea", ["#...#", "#.#.#", "#####", "#.#.#", "#####"], "c4a070"),
    "woodland_mansion": ("2e5a2a", "land", ["#.#.#", "#####", "#.#.#", "#####", "#.#.#"], "3a2414"),
}


def explorer_map(ctx, name):
    land, style, rows, mc = MARKERS[name]
    t, inr, edge = map_base(ctx)
    n = ctx.noise(5, 2, 0.5, salt="map" + name)
    lc, wc = rgb(land), WATER
    if style == "land":
        water = n < 0.3
    elif style == "sea":
        water = n < 0.72
    else:
        water = (n < 0.4) | (ctx.texel_noise("marsh") < 0.2)
    col = np.where(water[..., None], wc, lc)
    q = ctx.quantize(n, 4)
    col = col * (0.88 + 0.12 * q[..., None])
    t.color = np.where(inr[..., None], col, t.color)
    mm = rows_mask(ctx, rows, x0=6, y0=5)
    s = ctx.s * int(ctx.w / 16)
    shadow = np.roll(np.roll(mm > 0.5, s, 0), s, 1) & ~(mm > 0.5)
    paint(t, shadow & inr, INK)
    paint(t, mm, rgb(mc))
    paint(t, (mm > 0.5) & (cells(ctx, [(8, 5), (7, 6), (6, 7)]) > 0.5), np.clip(rgb(mc) * 1.3 + 0.1, 0, 1))
    # red X near the marker
    paint(t, cells(ctx, [(11, 11), (12, 12), (12, 11), (11, 12)]) > 0.5, rgb("b42a1e"))
    return t


register("item/map", empty_map)
for _n in MARKERS:
    register(f"item/{_n}_map", lambda ctx, n=_n: explorer_map(ctx, n))
