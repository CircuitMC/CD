"""Music discs, smithing templates, pottery sherds and banner patterns (h-z)."""
import numpy as np

from ...registry import register
from .common import DIAMOND, NETHERITE
from .h_lib import (cells, compose, ellipse, gem, paint, pal, ramp, rgb, ring, rows_mask, spr, union)

# ------------------------------------------------------------------ discs
VINYL = pal("101012", "1e1e22", "2c2c32", "3c3c44", "565662")
DISCS = {  # label, accent
    "11": ("e8e8e8", "3a3a3a"), "13": ("f0d030", "f8f0b0"), "5": ("3a8a8a", "9ad0d0"),
    "blocks": ("e06a1a", "f8c08a"), "bounce": ("e86aa8", "f8c8e0"), "cat": ("6ac82a", "c8f0a0"),
    "chirp": ("c42a2a", "f08a7a"), "creator": ("e8b82a", "fff0a0"), "creator_music_box": ("b07a46", "e8c08a"),
    "far": ("9ad02a", "e0f8a0"), "lava_chicken": ("f08a1a", "f8e04a"), "mall": ("6a5ac8", "b8b0f0"),
    "mellohi": ("a85ac8", "e0c0f0"), "otherside": ("2a8ac8", "9ae0d0"), "pigstep": ("c4302a", "f0c040"),
    "precipice": ("a8603a", "e8b08a"), "relic": ("2aa8a0", "a8f0e0"), "stal": ("2a2a2e", "8a8a96"),
    "strad": ("f4f4f0", "c8c8c0"), "tears": ("d8e8f4", "6aa8e0"), "wait": ("2a5ac8", "8ab0f0"),
    "ward": ("2a7a3a", "9ad08a"),
}


def disc(ctx, name):
    lab, acc = DISCS[name]
    k = ctx.w / 16
    m = ellipse(ctx, 8, 8, 7.0, 7.0)
    t = spr(ctx, m, VINYL, smooth=0.8, f0=0.05, bevel=1.5)
    edge = ctx.edge(m, 1) > 0
    paint(t, (m > 0.5) & ~edge, VINYL[2])
    paint(t, (ctx.edge(m, 2, "br") > 0) & ~edge, VINYL[1])
    for r in (4.4, 6.0):
        paint(t, (ring(ctx, 8, 8, r - 0.75, r) > 0.5) & ~edge, VINYL[1])
    # sheen arcs top-left and bottom-right
    d = np.hypot(ctx.x / k - 8, ctx.y / k - 8)
    ang = np.arctan2(ctx.y / k - 8, ctx.x / k - 8)
    sheen = (d > 3.2) & (d < 6.2) & (np.abs(ang + 2.35) < 0.32)
    paint(t, sheen & ~edge, VINYL[4])
    paint(t, (d > 4.2) & (d < 6.0) & (np.abs(ang - 0.8) < 0.18) & ~edge, VINYL[3])
    lp = ramp(lab, 4, lo=0.55, lift=0.4)
    lm = ellipse(ctx, 8, 8, 2.6, 2.6)
    lt = spr(ctx, lm, lp, smooth=0.3, bevel=1)
    paint(lt, cells(ctx, [(7, 6), (9, 9)]) > 0.5, rgb(acc))
    hole = ellipse(ctx, 8, 8, 0.75, 0.75) if ctx.s > 1 else cells(ctx, [(7, 7)])
    out = compose(ctx, t, lt)
    paint(out, hole, VINYL[0])
    if name == "11":  # cracked disc
        cr = cells(ctx, [(3, 4), (4, 5), (5, 5), (6, 6), (10, 9), (11, 10), (11, 11), (12, 12)])
        out.alpha[(cr > 0.5)] = 0
        paint(out, cells(ctx, [(4, 4), (5, 6), (10, 10), (12, 11)]) > 0.5, VINYL[0])
    return out


for _d in DISCS:
    register(f"item/music_disc_{_d}", lambda ctx, d=_d: disc(ctx, d))

# -------------------------------------------------------- smithing templates
TEMPLATE = [
    "..##########..",
    ".############.",
    "##############",
    "##############",
    "##############",
    "##############",
    "##############",
    "##############",
    "##############",
    "##############",
    ".############.",
    "..##########..",
]
# trim: (plate base color, glyph color, glyph rows 8x8)
TRIMS = {
    "host": ("b8a888", "6a5a40", ["..####..", ".#....#.", "#..##..#", "#.####.#", "#..##..#", ".#....#.", "..####..", "........"]),
    "raiser": ("c4a888", "7a5a3a", ["...##...", "..####..", ".#.##.#.", "...##...", "...##...", ".######.", "........", "........"]),
    "rib": ("4a2a2a", "c4a888", ["#.#.#.#.", "#.#.#.#.", "#######.", "#.#.#.#.", "#.#.#.#.", "#######.", "#.#.#.#.", "........"]),
    "sentry": ("6a7a6a", "2a3a2a", ["########", "#......#", "#.#..#.#", "#......#", "#..##..#", "#......#", "########", "........"]),
    "shaper": ("c49a6a", "6a4a2a", ["#......#", ".#....#.", "..#..#..", "...##...", "...##...", "..#..#..", ".#....#.", "#......#"]),
    "silence": ("1e3a44", "4ad0d4", ["..####..", ".##..##.", "##.##.##", "#.#..#.#", "##.##.##", ".##..##.", "..####..", "........"]),
    "snout": ("3a2a2a", "e8c040", ["..####..", ".######.", "##.##.##", "########", ".#.##.#.", ".######.", "..#..#..", "........"]),
    "spire": ("8a6a9a", "e0d0a0", ["...##...", "...##...", "..####..", "..####..", ".######.", ".######.", "########", "........"]),
    "tide": ("2a6a7a", "9ae0e0", ["........", ".##..##.", "#..##..#", "........", ".##..##.", "#..##..#", "........", "........"]),
    "vex": ("8a9aa8", "2a3a4a", ["#......#", "##....##", ".##..##.", "..####..", "...##...", "..#..#..", ".#....#.", "........"]),
    "ward": ("1e2e3a", "4ad0d4", ["...##...", ".#.##.#.", "#.####.#", "########", "#.####.#", ".#.##.#.", "...##...", "........"]),
    "wayfinder": ("b89a6a", "4a3a2a", ["...#....", "..###...", ".#.#.#..", "...#....", "...#....", ".#####..", "...#....", "........"]),
    "wild": ("5a7a3a", "c8e08a", [".#....#.", "#.#..#.#", "..####..", ".##..##.", "..####..", "#.#..#.#", ".#....#.", "........"]),
}


def template(ctx, base, glyph_c, glyph, upgrade=False):
    bp = ramp(base, 5, lo=0.42, lift=0.45)
    m = rows_mask(ctx, TEMPLATE, x0=1, y0=2, round_=0.1)
    t = spr(ctx, m, bp, smooth=0.35, bevel=2)
    edge = ctx.edge(m, 1) > 0
    inner = (m > 0.5) & ~edge
    n = ctx.texel_noise("tpl")
    t.color[inner & (n < 0.12)] = bp[1]
    gm = rows_mask(ctx, glyph, x0=4, y0=4)
    gc = ramp(glyph_c, 4, lo=0.6, lift=0.4)
    paint(t, gm > 0.5, gc[2])
    # engraved shadow down-right of glyph
    s = ctx.s * max(1, round(ctx.w / 16))
    sh = np.roll(np.roll(gm > 0.5, s, 0), s, 1) & ~(gm > 0.5) & inner
    t.color[sh] *= 0.75
    if upgrade:
        paint(t, gm > 0.5, NETHERITE[4] * 1.25)
        paint(t, cells(ctx, [(7, 6), (8, 7)]) > 0.5, pal("c8a060")[0])
    return t


for _tr, (_b, _g, _gl) in TRIMS.items():
    register(f"item/{_tr}_armor_trim_smithing_template", lambda ctx, b=_b, g=_g, gl=_gl: template(ctx, b, g, gl))
register("item/netherite_upgrade_smithing_template",
         lambda ctx: template(ctx, "5a3a3a", "2a2226",
                              ["..####..", ".######.", "##.##.##", "########", "########", ".######.", "..####..",
                               "........"], upgrade=True))

# ----------------------------------------------------------- pottery sherds
CLAY = pal("5a2e1c", "7e4028", "985034", "ae6040", "c4744e")
SHERD = [
    "....#######.....",
    "..##########....",
    ".############...",
    ".#############..",
    ".##############.",
    "..#############.",
    "..############..",
    "...###########..",
    "...##########...",
    "....#######.....",
]
SHERDS = {
    "heart": [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."],
    "heartbreak": [".##.##.", "###.###", "##.####", ".##.##.", "..#.#..", "...#..."],
    "howl": ["#...#..", "##.##..", "#####..", "#.#.###", "######.", "..#.#.."],
    "miner": ["######.", "...#...", "...#...", "...#...", "...#...", "...#..."],
    "mourner": [".###...", "#.#.#..", "#####..", ".#.#...", "#####..", "#...#.."],
    "plenty": ["#######", "#.#.#.#", "#######", "#######", ".#####.", "..###.."],
    "prize": ["...#...", "..###..", ".#####.", "##.#.##", ".#####.", "..###.."],
    "scrape": ["#..#..#", ".#..#..", "..#..#.", "#..#..#", ".#..#..", "..#..#."],
    "sheaf": ["#.#.#..", "#.#.#..", ".###...", "..#....", ".###...", "#.#.#.."],
    "shelter": ["...#...", "..###..", ".#####.", "#######", ".#...#.", ".#...#."],
    "skull": [".#####.", "#######", "#.#.#.#", "#######", ".#.#.#.", ".#####."],
    "snort": ["..###..", ".#####.", "##.#.##", "#######", "#.#.#.#", ".#####."],
}


def sherd(ctx, name):
    m = rows_mask(ctx, SHERD, y0=3, round_=0.2)
    t = spr(ctx, m, CLAY, smooth=0.25, porosity=0.6, bevel=2)
    edge = ctx.edge(m, 1) > 0
    inner = (m > 0.5) & ~edge
    n = ctx.texel_noise("sherd")
    t.color[inner & (n < 0.12)] = CLAY[2]
    t.color[inner & (n > 0.92)] = CLAY[4]
    g = rows_mask(ctx, SHERDS[name], x0=4, y0=5)
    paint(t, (g > 0.5) & inner, pal("3a1e12")[0])
    return t


for _s in SHERDS:
    register(f"item/{_s}_pottery_sherd", lambda ctx, s=_s: sherd(ctx, s))

# ------------------------------------------------------------ banner patterns
PAPER = pal("8a7e66", "c4b898", "ddd2b4", "ece4ca", "f8f2e0")
PATTERNS = {
    "mojang": ["..####..", ".#....#.", "#.##.#.#", "#.#..#.#", "#..##..#", ".#....#.", "..####.."],
    "piglin": [".######.", "########", "#.####.#", "########", ".#.##.#.", ".######.", "..#..#.."],
    "skull": [".######.", "#.####.#", "#..##..#", "########", ".#.##.#.", ".######.", ".#.#.#.."],
}


def banner_pattern(ctx, name):
    m = rows_mask(ctx, ["##########"] * 12, x0=3, y0=2, round_=0.05)
    t = spr(ctx, m, PAPER, smooth=0.15, porosity=0.6, bevel=1.5)
    edge = ctx.edge(m, 1) > 0
    paint(t, (cells(ctx, [(x, 3) for x in range(4, 12)]) > 0.5) & ~edge, PAPER[1])
    paint(t, (cells(ctx, [(x, 12) for x in range(4, 12)]) > 0.5) & ~edge, PAPER[1])
    g = rows_mask(ctx, PATTERNS[name], x0=4, y0=4)
    paint(t, g > 0.5, pal("4a3a2a")[0])
    return t


for _p in PATTERNS:
    register(f"item/{_p}_banner_pattern", lambda ctx, p=_p: banner_pattern(ctx, p))
