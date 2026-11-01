"""In-game HUD: hearts, food, armor, air, hotbar, bars, crosshair, locator bar, boss bars."""
import numpy as np

from ...registry import register
from .common import BLACK, C, Canvas, WHITE, mix

OUT = C("1a0f0f")

HEART = [".###.###.",
         "#########",
         "#########",
         "#########",
         ".#######.",
         "..#####..",
         "...###...",
         "....#...."]


def _sil(rows):
    return {(i, j) for j, r in enumerate(rows) for i, ch in enumerate(r) if ch == "#"}


def _outline(sil):
    return {(x, y) for (x, y) in sil
            if any((x + dx, y + dy) not in sil for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


def shade_cells(c, cells, base, hi, sh, ox=0, oy=0, light=None):
    """Fill cells with base, top-left inner edge highlight and bottom-right inner shade."""
    for (x, y) in cells:
        col = base
        if (x - 1, y) not in cells or (x, y - 1) not in cells:
            col = hi
        elif (x + 1, y) not in cells or (x, y + 1) not in cells:
            col = sh
        c.px(ox + x, oy + y, col)
    if light:
        for p in light:
            if p in cells:
                c.px(ox + p[0], oy + p[1], WHITE)


HEART_SIL = _sil(HEART)
HEART_IN = HEART_SIL - _outline(HEART_SIL)

HEART_COLORS = {
    "": ("d4302a", "ff7a68", "8c1414"),
    "poisoned": ("86a52a", "c8e05a", "4a6312"),
    "withered": ("3d3638", "6e6467", "1d1a1b"),
    "frozen": ("7cc6ea", "d4f1ff", "3c86b0"),
    "absorbing": ("e3b72f", "fff09a", "a2740e"),
    "vehicle": ("e0782e", "ffbd80", "9c4512"),
}


def heart(kind, half=False, hardcore=False, blink=False):
    def fn(ctx):
        c = Canvas(ctx)
        b, h, s = (C(v) for v in HEART_COLORS[kind])
        if blink:
            b, h, s = mix(b, WHITE, 0.35), mix(h, WHITE, 0.5), mix(s, WHITE, 0.25)
        cells = {p for p in HEART_IN if not half or p[0] <= 4}
        shade_cells(c, cells, b, h, s, light=[(2, 2)] if not hardcore else None)
        if hardcore:
            # hardcore: a darker spiked crown band across the top lobes
            for p in ((1, 1), (3, 1), (5, 1), (7, 1), (2, 2), (6, 2), (4, 3)):
                if p in cells:
                    c.px(*p, mix(s, BLACK, 0.35))
            for p in ((2, 1), (6, 1)):
                if p in cells:
                    c.px(*p, WHITE)
        return c.tex()
    return fn


def heart_container(hardcore=False, blink=False, vehicle=False):
    def fn(ctx):
        c = Canvas(ctx)
        ink = C("f4f4f4") if blink else OUT
        for p in _outline(HEART_SIL):
            c.px(*p, ink)
        for p in HEART_IN:
            c.px(*p, C("3b2424") if not vehicle else C("3b2c20"))
        if hardcore:
            for p in ((1, 0), (2, 0), (3, 0), (5, 0), (6, 0), (7, 0)):
                c.px(p[0], p[1], ink)
            c.px(4, 0, ink)
        return c.tex()
    return fn


H = "gui/sprites/hud/heart/"
register(H + "container", heart_container())
register(H + "container_blinking", heart_container(blink=True))
register(H + "container_hardcore", heart_container(True))
register(H + "container_hardcore_blinking", heart_container(True, True))
register(H + "vehicle_container", heart_container(vehicle=True))
for _k in ("", "poisoned", "withered", "frozen", "absorbing"):
    for _hc in (False, True):
        for _half in (False, True):
            for _bl in (False, True):
                name = "_".join(p for p in (_k, "hardcore" if _hc else "", "half" if _half else "full",
                                            "blinking" if _bl else "") if p)
                register(H + name, heart(_k, _half, _hc, _bl))
register(H + "vehicle_full", heart("vehicle"))
register(H + "vehicle_half", heart("vehicle", True))

# ----------------------------------------------------------------- food (apple)
APPLE = ["....##...",
         "...#..##.",
         ".##.#.#..",
         "#########",
         "#########",
         "#########",
         "#########",
         ".#######.",
         "..##.##.."]
APPLE_SIL = _sil(APPLE[3:]) | {(x, y + 0) for (x, y) in set()}
APPLE_SIL = {(x, y + 3) for (x, y) in _sil(APPLE[3:])} | {(1, 2), (2, 2), (6, 2), (7, 2)}
STEM = {(4, 0), (4, 1), (4, 2)}
LEAF = {(5, 1), (6, 0), (7, 0), (6, 1)}


def food(state, hunger=False):
    def fn(ctx):
        c = Canvas(ctx)
        out = _outline(APPLE_SIL)
        inner = APPLE_SIL - out
        if state == "empty":
            for p in out:
                c.px(*p, OUT)
            for p in inner:
                c.px(*p, C("3a2a22"))
            for p in STEM:
                c.px(*p, OUT)
            return c.tex()
        if hunger:
            b, h, s = C("8aa53a"), C("c6dc72"), C("4f6620")
        else:
            b, h, s = C("cf3b2b"), C("ff8a6a"), C("86190f")
        cells = APPLE_SIL if state == "full" else {p for p in APPLE_SIL if p[0] >= 4}
        for p in out & cells:
            c.px(*p, mix(s, BLACK, 0.45))
        shade_cells(c, inner & cells, b, h, s, light=[(2, 4)])
        if state == "full" or True:
            for p in STEM:
                c.px(*p, C("5a3a1e"))
            for p in LEAF:
                c.px(*p, C("5fae3a") if not hunger else C("7c8a3a"))
        return c.tex()
    return fn


for _st in ("empty", "full", "half"):
    register(f"gui/sprites/hud/food_{_st}", food(_st))
    register(f"gui/sprites/hud/food_{_st}_hunger", food(_st, True))

# ----------------------------------------------------------------- armor (chestplate)
ARMOR = ["##.....##",
         "###...###",
         "#########",
         ".#######.",
         "..#####..",
         "..#####..",
         "..#####..",
         "..#####..",
         "........."]
ARMOR_SIL = _sil(ARMOR)


def armor(state):
    def fn(ctx):
        c = Canvas(ctx)
        out = _outline(ARMOR_SIL)
        inner = ARMOR_SIL - out
        if state == "empty":
            for p in out:
                c.px(*p, C("26282c"))
            for p in inner:
                c.px(*p, C("4a4d54"), 0.85)
            return c.tex()
        cells = ARMOR_SIL if state == "full" else {p for p in ARMOR_SIL if p[0] <= 4}
        for p in out & cells:
            c.px(*p, C("2c2e33"))
        shade_cells(c, inner & cells, C("b9bec8"), C("eef2f8"), C("7a7f8a"))
        if state == "half":
            for p in ARMOR_SIL - cells:
                c.px(*p, C("26282c") if p in out else C("4a4d54"))
        for y in range(3, 8):
            if (4, y) in cells and (4, y) in inner:
                c.px(4, y, C("8e939e"))
        return c.tex()
    return fn


for _st in ("empty", "full", "half"):
    register(f"gui/sprites/hud/armor_{_st}", armor(_st))


# ----------------------------------------------------------------- air bubbles
def bubble(state):
    def fn(ctx):
        c = Canvas(ctx)
        ring = C("2d6fb5")
        if state == "empty":
            c.ring(4.5, 4.5, 4.0, 1.0, C("1d3550"), 0.6)
            return c.tex()
        if state == "bursting":
            for (x, y) in ((1, 1), (7, 1), (1, 7), (7, 7), (4, 0), (0, 4), (8, 4), (4, 8),
                           (2, 2), (6, 2), (2, 6), (6, 6)):
                c.px(x, y, C("9fd4ff"))
            return c.tex()
        c.circle(4.5, 4.5, 4.0, C("8cc8f5"), 0.75)
        c.ring(4.5, 4.5, 4.0, 1.0, ring)
        c.px(2, 2, WHITE)
        c.px(3, 2, WHITE)
        c.px(2, 3, WHITE)
        return c.tex()
    return fn


register("gui/sprites/hud/air", bubble("full"))
register("gui/sprites/hud/air_bursting", bubble("bursting"))
register("gui/sprites/hud/air_empty", bubble("empty"))


# ----------------------------------------------------------------- crosshair & attack indicator
def _crosshair(ctx):
    c = Canvas(ctx)
    col = C("ffffff")
    c.vline(7, 1, 5, col)
    c.vline(7, 9, 13, col)
    c.hline(1, 5, 7, col)
    c.hline(9, 13, 7, col)
    c.px(7, 7, col)
    return c.tex()


register("gui/sprites/hud/crosshair", _crosshair)


def _ind_bar(fill):
    def fn(ctx):
        c = Canvas(ctx)
        if fill:
            c.rect(0, 0, 16, 4, C("ffffff"))
            c.hline(1, 14, 1, C("d6dce8"))
        else:
            c.frame(0, 0, 16, 4, C("bfc4cc"))
            c.rect(1, 1, 14, 2, C("2a2b30"), 0.8)
        return c.tex()
    return fn


register("gui/sprites/hud/crosshair_attack_indicator_background", _ind_bar(False))
register("gui/sprites/hud/crosshair_attack_indicator_progress", _ind_bar(True))

SWORD = ["..........##",
         ".........#.#",
         "........#.#.",
         ".......#.#..",
         "......#.#...",
         ".#...#.#....",
         "..#.#.#.....",
         "...#.#......",
         "..#.#.......",
         ".#...#......",
         "#...........",
         ]


def _ind_full(ctx):
    c = Canvas(ctx)
    for j, r in enumerate(SWORD):
        for i, ch in enumerate(r):
            if ch == "#":
                c.px(2 + i, 2 + j, C("ffffff"))
    return c.tex()


register("gui/sprites/hud/crosshair_attack_indicator_full", _ind_full)


def _hb_indicator(progress):
    def fn(ctx):
        c = Canvas(ctx)
        if progress:
            c.rect(1, 1, 16, 16, C("f2f4f8"))
            c.rect(2, 2, 14, 14, C("c9d4ea"))
        else:
            c.rect(0, 0, 18, 18, C("16171a"), 0.9)
            c.rect(1, 1, 16, 16, C("3a3c43"))
            c.rect(2, 2, 14, 14, C("26272c"))
        for j, r in enumerate(SWORD):
            for i, ch in enumerate(r):
                if ch == "#":
                    c.px(3 + i, 3 + j, C("6d7079") if not progress else C("4a5672"))
        return c.tex()
    return fn


register("gui/sprites/hud/hotbar_attack_indicator_background", _hb_indicator(False))
register("gui/sprites/hud/hotbar_attack_indicator_progress", _hb_indicator(True))


# ----------------------------------------------------------------- hotbar
def hotbar_slot(c, x, y):
    c.rect(x, y, 20, 20, C("34363c"), 0.92)
    c.hline(x, x + 19, y, C("1c1d21"))
    c.vline(x, y, y + 19, C("1c1d21"))
    c.hline(x + 1, x + 19, y + 19, C("5a5d66"))
    c.vline(x + 19, y + 1, y + 19, C("5a5d66"))
    c.rect(x + 2, y + 2, 16, 16, C("2a2c31"), 0.9)


def _hotbar(ctx):
    c = Canvas(ctx)
    c.rect(1, 0, 180, 22, C("0e0f11"))
    c.rect(0, 1, 182, 20, C("0e0f11"))
    for i in range(9):
        hotbar_slot(c, 1 + i * 20, 1)
    return c.tex()


def _selection(ctx):
    c = Canvas(ctx)
    a, b = C("f6f7fa"), C("9aa6be")
    c.frame(0, 0, 24, 23, C("0e0f11"))
    c.frame(1, 1, 22, 21, a)
    c.frame(2, 2, 20, 19, b)
    for p in ((1, 1), (22, 1), (1, 21), (22, 21)):
        c.px(*p, C("0e0f11"))
    return c.tex()


def _offhand(left):
    def fn(ctx):
        c = Canvas(ctx)
        x = 0 if left else 7
        c.rect(x + 1, 1, 20, 23, C("0e0f11"))
        c.rect(x, 2, 22, 21, C("0e0f11"))
        hotbar_slot(c, x + 1, 2)
        return c.tex()
    return fn


register("gui/sprites/hud/hotbar", _hotbar)
register("gui/sprites/hud/hotbar_selection", _selection)
register("gui/sprites/hud/hotbar_offhand_left", _offhand(True))
register("gui/sprites/hud/hotbar_offhand_right", _offhand(False))


# ----------------------------------------------------------------- bars (182x5)
def bar(fill, hi, dark, notch=None, segments=0, empty=False):
    def fn(ctx):
        c = Canvas(ctx)
        w, h = ctx.w, ctx.h
        if empty:
            c.rect(0, 0, w, h, C("101114"))
            c.rect(1, 1, w - 2, h - 2, dark)
            c.hline(1, w - 2, 1, mix(dark, BLACK, 0.3))
        else:
            c.rect(0, 0, w, h, mix(fill, BLACK, 0.6))
            c.rect(1, 1, w - 2, h - 2, fill)
            c.hline(1, w - 2, 1, hi)
            c.hline(1, w - 2, h - 2, mix(fill, BLACK, 0.2))
        if segments:
            for k in range(1, segments):
                x = round(k * (w - 1) / segments)
                c.vline(x, 1, h - 2, notch if notch is not None else C("101114"))
        return c.tex()
    return fn


def notch_overlay(segments):
    def fn(ctx):
        c = Canvas(ctx)
        for k in range(1, segments):
            x = round(k * (ctx.w - 1) / segments)
            c.vline(x, 1, ctx.h - 2, C("101114"), 0.8)
        return c.tex()
    return fn


XP = C("6ad640")
register("gui/sprites/hud/experience_bar_background", bar(XP, XP, C("2c3a26"), empty=True, segments=18))
register("gui/sprites/hud/experience_bar_progress", bar(XP, C("b8f590"), None, segments=18, notch=C("3f8c22")))
register("gui/sprites/hud/jump_bar_background", bar(None, None, C("2b2e3a"), empty=True))
register("gui/sprites/hud/jump_bar_progress", bar(C("4f9be8"), C("a8d4ff"), None))
register("gui/sprites/hud/jump_bar_cooldown", bar(C("6d7079"), C("9a9da6"), None))

BOSS = {"pink": "e45fb2", "blue": "3f8ee8", "red": "e0403a", "green": "4cc844", "yellow": "e8cf3a",
        "purple": "9a52e0", "white": "e8eaee"}
for _n, _hex in BOSS.items():
    _c = C(_hex)
    register(f"gui/sprites/boss_bar/{_n}_background", bar(None, None, mix(_c, BLACK, 0.72), empty=True))
    register(f"gui/sprites/boss_bar/{_n}_progress", bar(_c, mix(_c, WHITE, 0.45), None))
for _seg in (6, 10, 12, 20):
    register(f"gui/sprites/boss_bar/notched_{_seg}_background", notch_overlay(_seg))
    register(f"gui/sprites/boss_bar/notched_{_seg}_progress", notch_overlay(_seg))


# ----------------------------------------------------------------- locator bar
def _loc_bg(ctx):
    c = Canvas(ctx)
    c.rect(0, 0, 12, 5, C("101114"), 0.8)
    c.rect(1, 1, 10, 3, C("2b2d33"), 0.8)
    c.vline(0, 0, 4, C("6d7079"))
    c.vline(11, 0, 4, C("6d7079"))
    return c.tex()


def _loc_arrow(up):
    def fn(ctx):
        c = Canvas(ctx)
        dy = ctx.frame  # frame 1 nudges the arrow
        rows = ["...#...", "..###..", ".#####.", "#######"]
        if not up:
            rows = rows[::-1]
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch == "#":
                    c.px(i, j + (dy if up else 1 - dy), C("f4f5f7"))
        return c.tex()
    return fn


register("gui/sprites/hud/locator_bar_background", _loc_bg)
register("gui/sprites/hud/locator_bar_arrow_up", _loc_arrow(True), size=(7, 5), frames=2, frametime=7)
register("gui/sprites/hud/locator_bar_arrow_down", _loc_arrow(False), size=(7, 5), frames=2, frametime=7)


def _dot(shape):
    def fn(ctx):
        c = Canvas(ctx)
        col, ink = C("ffffff"), C("1a1b1f")
        if shape == "bowtie":
            rows = ["#.......#", "##.....##", "###...###", "####.####", "#########",
                    "####.####", "###...###", "##.....##", "#.......#"]
            for j, r in enumerate(rows):
                for i, ch in enumerate(r):
                    if ch == "#":
                        c.px(i, j, col)
            return c.tex()
        r = {"default_0": 4.4, "default_1": 3.6, "default_2": 2.8, "default_3": 2.0}[shape]
        c.circle(4.5, 4.5, r + 0.6, ink)
        c.circle(4.5, 4.5, r - 0.4, col)
        return c.tex()
    return fn


for _d in ("bowtie", "default_0", "default_1", "default_2", "default_3"):
    register(f"gui/sprites/hud/locator_bar_dot/{_d}", _dot(_d))


# ----------------------------------------------------------------- effect backgrounds
def _effect_bg(ambient, size, border):
    def fn(ctx):
        c = Canvas(ctx)
        w = h = size
        edge = C("8fd3ef") if ambient else C("16171a")
        face = C("2f3b4a") if ambient else C("383a41")
        c.rect(1, 0, w - 2, h, edge)
        c.rect(0, 1, w, h - 2, edge)
        c.rect(1, 1, w - 2, h - 2, mix(face, WHITE, 0.25))
        c.rect(2, 2, w - 3, h - 3, mix(face, BLACK, 0.3))
        c.rect(2, 2, w - 4, h - 4, face)
        return c.tex()
    return fn


register("gui/sprites/hud/effect_background", _effect_bg(False, 24, 0))
register("gui/sprites/hud/effect_background_ambient", _effect_bg(True, 24, 0))
register("gui/sprites/container/inventory/effect_background", _effect_bg(False, 32, 4))
register("gui/sprites/container/inventory/effect_background_ambient", _effect_bg(True, 32, 4))
