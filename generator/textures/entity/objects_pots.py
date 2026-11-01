"""Decorated pot: base (neck + top/bottom plates) and side textures with original
engraved motifs for every pottery sherd.

Layout from the CEM template decorated_pot.jem. Base (32x32): neck (0,0) 8x3x8, rim (0,5) 6x1x6, top/bottom plates (0,13)-(14,27) and
(14,13)-(28,27). Sides (16x16): the visible plane is (1,0)-(15,16).
"""
import numpy as np

from ...engine import pal
from ...registry import register
from .objects_common import Sheet, frame

CLAY = pal("5a2c1c", "7a3c26", "934a2e", "a85a38", "ba6a44", "c97c52")

# 10 x 10 motif grids: '#' engraved line, '+' raised highlight (inlay), '.' empty.
MOTIFS = {
    "angler": [
        "..........",
        "...####...",
        ".##....#.#",
        "#...#...##",
        "#........#",
        "#........#",
        ".##....#.#",
        "...####...",
        "..........",
        "..........",
    ],
    "archer": [
        "##........",
        "#.#.......",
        "#..#......",
        "#...#....+",
        "#....#..+.",
        "#....#.+..",
        "#...#.+...",
        "#..#.+....",
        "#.#.+.....",
        "##.#......",
    ],
    "arms_up": [
        "#...##...#",
        ".#.#..#.#.",
        "..#.##.#..",
        "...####...",
        "....##....",
        "....##....",
        "...#..#...",
        "..#....#..",
        "..#....#..",
        ".##....##.",
    ],
    "blade": [
        "........##",
        ".......#.#",
        "......#.#.",
        ".....#.#..",
        "....#.#...",
        ".#.#.#....",
        "..#.#.....",
        ".#.#......",
        "#.#.#.....",
        "##........",
    ],
    "brewer": [
        "...####...",
        "....##....",
        "....##....",
        "...#..#...",
        "..#....#..",
        ".#.++++.#.",
        "#.++++++.#",
        "#.++++++.#",
        ".#......#.",
        "..######..",
    ],
    "burn": [
        "....#.....",
        "...##.....",
        "...#.#..#.",
        "..#..#.##.",
        "..#...#.#.",
        ".#..+...#.",
        ".#.+++..#.",
        "#..+++...#",
        "#...+....#",
        ".########.",
    ],
    "danger": [
        "##########",
        "#........#",
        "#.##..##.#",
        "#.##..##.#",
        "#...##...#",
        "#..####..#",
        "#..#..#..#",
        "#........#",
        "##########",
        "..........",
    ],
    "explorer": [
        "##########",
        "#....#...#",
        "#..+.#...#",
        "#.+++#.#.#",
        "#..+..#..#",
        "#....#.#.#",
        "#.##.....#",
        "#...##...#",
        "##########",
        "..........",
    ],
    "flow": [
        "..######..",
        ".#......#.",
        "#..####..#",
        "#.#....#.#",
        "#.#.##.#.#",
        "#.#..#.#.#",
        "#..##..#.#",
        ".#....#..#",
        "..####..#.",
        "......##..",
    ],
    "friend": [
        "..######..",
        ".#......#.",
        "#..#..#..#",
        "#..#..#..#",
        "#........#",
        "#.#....#.#",
        "#..####..#",
        ".#......#.",
        "..######..",
        "..........",
    ],
    "guster": [
        "...####...",
        "..#....#..",
        ".#.#..#.#.",
        ".#......#.",
        "..#.##.#..",
        "...####...",
        ".######...",
        "...#####..",
        "..####....",
        "....###...",
    ],
    "heart": [
        "..........",
        ".##....##.",
        "#..#..#..#",
        "#...##...#",
        "#.++.....#",
        ".#.+....#.",
        "..#....#..",
        "...#..#...",
        "....##....",
        "..........",
    ],
    "heartbreak": [
        "..........",
        ".##...###.",
        "#..#.#...#",
        "#...#....#",
        "#...#....#",
        ".#.#....#.",
        "..#.#..#..",
        "...#..#...",
        "....##....",
        "..........",
    ],
    "howl": [
        "......#...",
        ".....##...",
        "....#.#...",
        "...#..##..",
        "..#.+...#.",
        ".#.......#",
        "#......##.",
        "#.....#...",
        ".#...#....",
        "..###.....",
    ],
    "miner": [
        "..######..",
        ".#..##..#.",
        "#...##...#",
        "....##....",
        "....##....",
        "....##....",
        "....##....",
        "....##....",
        "....##....",
        "....##....",
    ],
    "mourner": [
        "#........#",
        "##......##",
        "#.######.#",
        "#.#....#.#",
        "#.#+..+#.#",
        "#.#....#.#",
        "#.#.##.#.#",
        "#.#....#.#",
        "..######..",
        "..........",
    ],
    "plenty": [
        "##########",
        "#........#",
        "##########",
        "#...##...#",
        "#...++...#",
        "#........#",
        "#........#",
        "##########",
        "..........",
        "..........",
    ],
    "prize": [
        "..........",
        "..######..",
        ".#.+..+.#.",
        "##########",
        ".#.+..+.#.",
        "..#.++.#..",
        "...#..#...",
        "....##....",
        "..........",
        "..........",
    ],
    "scrape": [
        "...####...",
        "..#....#..",
        ".#..##..#.",
        "...#..#...",
        "....##....",
        "....##....",
        "....##....",
        "....##....",
        "....##....",
        "...####...",
    ],
    "sheaf": [
        "#...#...#.",
        ".#..#..#..",
        "#.#.#.#.#.",
        ".#.###.#..",
        "..#####...",
        "...###....",
        "..#####...",
        "....#.....",
        "...#.#....",
        "..#...#...",
    ],
    "shelter": [
        "....##....",
        "...####...",
        "..######..",
        ".########.",
        "....##....",
        "..######..",
        ".#......#.",
        "##..##..##",
        "....##....",
        "....##....",
    ],
    "skull": [
        "..######..",
        ".#......#.",
        "#........#",
        "#.##..##.#",
        "#.##..##.#",
        "#...##...#",
        ".#......#.",
        "..#.##.#..",
        "..######..",
        "..........",
    ],
    "snort": [
        "..........",
        ".########.",
        "#........#",
        "#.#....#.#",
        "#........#",
        "#..####..#",
        "#..#..#..#",
        ".#.####.#.",
        "..#....#..",
        "..#....#..",
    ],
}


def _clay(ctx, salt):
    n = ctx.noise(4, 2, 0.5, salt=f"clay{salt}")
    t = ctx.texel_noise(f"ct{salt}")
    return ctx.palette(CLAY[2:], n * 0.6 + t * 0.3), 0.5 + n * 0.06


def pot_side(ctx, motif=None):
    sh = Sheet(ctx)
    c, h = _clay(ctx, "side")
    x0, y0, x1, y1 = 1, 0, 15, 16
    r = (x0, y0, x1, y1)
    m = sh.rect(r)
    sh.put(m, c, height=h, smooth=0.25, porosity=0.4)
    # Rim bands top and bottom.
    sh.put(m & (ctx.y < 1), CLAY[1], height=0.45)
    sh.put(m & (ctx.y >= 1) & (ctx.y < 2), CLAY[5], height=0.6)
    sh.put(m & (ctx.y >= 15), CLAY[1], height=0.45)
    sh.put(m & (ctx.y >= 14) & (ctx.y < 15), CLAY[4], height=0.55)
    # Shading: curved sides darker at the edges.
    sh.shade(m & (ctx.x < x0 + 1), 0.85)
    sh.shade(m & (ctx.x >= x1 - 1), 0.78)
    if motif is None:
        # Plain pot: one wavy incised line across the belly.
        wave = m & (np.floor(ctx.y) == np.floor(7.5 + np.sin(ctx.x * 0.9) * 1.2)) & (ctx.x >= x0 + 1) & (ctx.x < x1 - 1)
        sh.put(wave, CLAY[0], height=0.3)
        return sh.tex(grain=0.03)
    rows = MOTIFS[motif]
    ox, oy = x0 + 2, y0 + 3
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            cell = ctx.rect(ox + i, oy + j, ox + i + 1, oy + j + 1) > 0.5
            if ch == "#":
                sh.put(cell, CLAY[0], height=0.25)
                below = ctx.rect(ox + i + 1, oy + j + 1, ox + i + 2, oy + j + 2) > 0.5
                if rows_get(rows, i + 1, j + 1) == ".":
                    sh.shade(below & m, 1.12)
            else:
                sh.put(cell, CLAY[5] * 1.05, height=0.65)
    return sh.tex(grain=0.03)


def rows_get(rows, i, j):
    if 0 <= j < len(rows) and 0 <= i < len(rows[j]):
        return rows[j][i]
    return "."


def pot_base(ctx):
    sh = Sheet(ctx)
    c, h = _clay(ctx, "base")
    neck = sh.faces(0, 0, 8, 3, 8)
    rim = sh.faces(0, 5, 6, 1, 6)
    for n, r in neck.items():
        m = sh.rect(r)
        sh.put(m, c, height=h, smooth=0.25, porosity=0.4)
        if n in ("right", "front", "left", "back"):
            sh.shade(m & (ctx.y < r[1] + 1), 1.12)
            sh.shade(m & (ctx.y >= r[3] - 1), 0.82)
        elif n == "top":
            sh.put(ctx.rect(r[0] + 2, r[1] + 2, r[2] - 2, r[3] - 2) > 0.5, CLAY[0], height=0.1)
    for n, r in rim.items():
        m = sh.rect(r)
        sh.put(m, CLAY[4], height=0.6, smooth=0.25)
        if n == "top":
            sh.put(ctx.rect(r[0] + 1, r[1] + 1, r[2] - 1, r[3] - 1) > 0.5, CLAY[0] * 0.8, height=0.05)
    for r, dark in (((0, 13, 14, 27), False), ((14, 13, 28, 27), True)):
        m = sh.rect(r)
        sh.put(m, c * (0.85 if dark else 1.0), height=h, smooth=0.25, porosity=0.4)
        sh.put(frame(ctx, r, 1) & m, CLAY[1], height=0.45)
        ring = frame(ctx, (r[0] + 3, r[1] + 3, r[2] - 3, r[3] - 3), 1) & m
        sh.put(ring, CLAY[1] if not dark else CLAY[0], height=0.4)
    return sh.tex(grain=0.03)


register("entity/decorated_pot/decorated_pot_base", pot_base)
register("entity/decorated_pot/decorated_pot_side", lambda ctx: pot_side(ctx))
for _m in MOTIFS:
    register(f"entity/decorated_pot/{_m}_pottery_pattern", (lambda m: lambda ctx: pot_side(ctx, m))(_m))
