"""Map item backgrounds and map decoration markers (8x8)."""
import numpy as np

from ...registry import register
from .common import BLACK, C, Canvas, WHITE, mix

INK = C("1e1a14")
DYES = {"white": "f2f2f2", "orange": "f08a1e", "magenta": "c64fbd", "light_blue": "4fb8e6", "yellow": "f5d23a",
        "lime": "80c71f", "pink": "f2a0bd", "gray": "4a4f55", "light_gray": "9d9d97", "cyan": "169c9c",
        "purple": "8932b8", "blue": "3c44aa", "brown": "835432", "green": "5e7c16", "red": "b02e26",
        "black": "1d1d21"}


def _paper(ctx, checker=False):
    c = Canvas(ctx)
    w, h = ctx.w, ctx.h
    if checker:
        k = w // 16
        light = ((ctx.tx // k + ctx.ty // k) % 2) == 0
        c.mask(ctx.full(1), C("d7c79c"))
        c.mask(light, C("e4d6ae"))
        return c.tex()
    n = ctx.noise(8, 3, 0.5, salt="paper")
    g = ctx.texel_noise("pg")
    base = mix(C("cdb98a"), C("e6d7ae"), 1.0)
    col = base[None, None, :] * (0.93 + 0.08 * n[..., None] + 0.03 * g[..., None])
    c.mask(ctx.full(1), col)
    b = max(2, w // 16)
    edge = (ctx.x < b) | (ctx.x > w - b) | (ctx.y < b) | (ctx.y > h - b)
    c.mask(edge, mix(C("8a7048"), C("6b5434"), 0.3))
    c.mask(ctx.edge(ctx.full(1), 1.0), C("4a3a24"))
    return c.tex()


register("map/map_background", lambda ctx: _paper(ctx))
register("map/map_background_checkerboard", lambda ctx: _paper(ctx, True))


def _deco(rows, pal):
    def fn(ctx):
        c = Canvas(ctx)
        c.art(rows, pal)
        return c.tex()
    return fn


ARROW = ["...##...",
         "..#ww#..",
         "..#ww#..",
         ".#wwww#.",
         ".#wwww#.",
         "#ww##ww#",
         "#w#..#w#",
         "##....##"]


def arrow(col):
    return _deco(ARROW, {"#": mix(C(col), BLACK, 0.6), "w": C(col)})


register("map/decorations/player", arrow("ffffff"))
register("map/decorations/frame", arrow("4fc84a"))
register("map/decorations/red_marker", arrow("e0403a"))
register("map/decorations/blue_marker", arrow("3f7fe0"))
register("map/decorations/target_point", arrow("e8c24a"))

DOT = ["........", "..####..", ".#wwww#.", ".#wwww#.", ".#wwww#.", ".#wwww#.", "..####..", "........"]
SMALL = ["........", "........", "...##...", "..#ww#..", "..#ww#..", "...##...", "........", "........"]
register("map/decorations/player_off_map", _deco(DOT, {"#": C("3a3a3a"), "w": C("ffffff")}))
register("map/decorations/player_off_limits", _deco(SMALL, {"#": C("3a3a3a"), "w": C("ffffff")}))

X = ["##....##", "#w#..#w#", ".#w##w#.", "..#ww#..", "..#ww#..", ".#w##w#.", "#w#..#w#", "##....##"]
register("map/decorations/red_x", _deco(X, {"#": C("5a0f0a"), "w": C("e0403a")}))
register("map/decorations/target_x", _deco(X, {"#": C("3a3a3a"), "w": C("ffffff")}))

BANNER = ["########", "#cccccc#", "#cccccc#", "#cccccc#", "#cccccc#", "#ccssccs", "#cs##sc#", "##....##"]
for _n, _hex in DYES.items():
    col = C(_hex)
    register(f"map/decorations/{_n}_banner",
             _deco(BANNER, {"#": mix(col, BLACK, 0.6), "c": col, "s": mix(col, BLACK, 0.25)}))

HOUSE = ["...##...", "..#rr#..", ".#rrrr#.", "#rrrrrr#", ".#wwww#.", ".#wddw#.", ".#wddw#.", ".######."]
VILLAGES = {"plains": ("b8844e", "e8d8b0"), "desert": ("d8b06a", "f2e2b4"), "savanna": ("c8642e", "e0c08a"),
            "snowy": ("f2f6fa", "b8c4d0"), "taiga": ("4f3a22", "a8845a")}
for _v, (_roof, _wall) in VILLAGES.items():
    register(f"map/decorations/{_v}_village",
             _deco(HOUSE, {"#": INK, "r": C(_roof), "w": C(_wall), "d": C("4a3418")}))

STRUCT = {
    "woodland_mansion": (["..####..", ".#rrrr#.", "#rrrrrr#", "#wwwwww#", "#wdwwdw#", "#wwwwww#", "#wdwwdw#", "########"],
                         {"r": "4a2e18", "w": "8a6a4a", "d": "1e1a14"}),
    "ocean_monument": (["...##...", "..#pp#..", ".#pppp#.", "#pplppp#", "#pppppl#", "#pplppp#", "#pppppp#", "########"],
                       {"p": "4fa8a0", "l": "8fe0d8"}),
    "desert_pyramid": (["...##...", "..#ss#..", "..#ss#..", ".#ssss#.", ".#sdds#.", "#ssssss#", "#ssssss#", "########"],
                       {"s": "e0c27a", "d": "c25a2e"}),
    "jungle_temple": (["........", "..####..", ".#mmmm#.", ".#mddm#.", "#mmmmmm#", "#mmddmm#", "#mmddmm#", "########"],
                      {"m": "6a8a5a", "d": "2a3a22"}),
    "swamp_hut": (["...##...", "..#rr#..", ".#rrrr#.", "#rrrrrr#", ".#wwww#.", ".#wddw#.", ".#.##.#.", ".#....#."],
                  {"r": "3a4a2a", "w": "6b4a2e", "d": "1e1a14"}),
    "abandoned_camp": (["...#....", "..#t#...", ".#ttt#..", "#ttttt#.", "#tt#tt#.", "#######.", "....ff..", "...ffff."],
                       {"t": "c8b48a", "f": "f08a1e"}),
    "ancient_city": (["#......#", "#d....d#", "#dd##dd#", "#dddddd#", "#dcddcd#", "#dddddd#", "#dddddd#", "########"],
                     {"d": "34363d", "c": "4ad6e0"}),
    "trial_chambers": (["########", "#cccccc#", "#cbbbbc#", "#cb##bc#", "#cb##bc#", "#cbbbbc#", "#cccccc#", "########"],
                       {"c": "c87a3a", "b": "6a8aa0"}),
    "warm_ocean_ruins": (["........", "#......#", "#s.##.s#", "#ss##ss#", "#ssssss#", "#sdssds#", "#ssssss#", "########"],
                         {"s": "d8b88a", "d": "4fa8a0"}),
    "mineshaft": (["########", "#wwwwww#", "#w#..#w#", "#w#..#w#", "#w#..#w#", "#w#..#w#", "#w#..#w#", "##....##"],
                  {"w": "a07a4a"}),
}
for _n, (_rows, _p) in STRUCT.items():
    register(f"map/decorations/{_n}", _deco(_rows, {"#": INK, **{k: C(v) for k, v in _p.items()}}))
