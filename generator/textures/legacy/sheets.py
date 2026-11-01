"""Old atlas sheets assembled from the modern single sprites: explosion / sweep
strips, moon phases, painting atlas, particle sheet, map icon atlas."""
import numpy as np

from ...engine import Tex, hexc
from ...registry import TEXTURES
from ..block.color_common import DYE, DYE_NAMES
from .kit import blank, fit, place, reg, render


def _adopt_meta(out, t):
    out.normal_strength, out.grain = t.normal_strength, t.grain
    return out


# ------------------------------------------------------------------ explosion / sweep

def explosion_sheet(ctx):
    out = blank(ctx)
    for i in range(16):
        t = render(f"particle/explosion_{i}", ctx.s, 32, 32)
        place(out, t, (i % 4) * 32, (i // 4) * 32)
    return _adopt_meta(out, t)


def sweep_sheet(ctx):
    out = blank(ctx)
    for i in range(8):
        t = render(f"particle/sweep_{i}", ctx.s, 32, 32)
        x, y = (i % 4) * 32, (i // 4) * 16
        fit(out, t, (x, y, x + 32, y + 16))   # drawn on a square quad: squeeze 2:1
    return _adopt_meta(out, t)


reg("entity/explosion", explosion_sheet, pbr=False)
reg("entity/sweep", sweep_sheet, pbr=False)


# ------------------------------------------------------------------ moon phases

MOON_ORDER = ["full_moon", "waning_gibbous", "third_quarter", "waning_crescent",
              "new_moon", "waxing_crescent", "first_quarter", "waxing_gibbous"]


def moon_phases(ctx):
    out = blank(ctx)
    for i, n in enumerate(MOON_ORDER):
        t = render(f"environment/celestial/moon/{n}", ctx.s, 32, 32)
        place(out, t, (i % 4) * 32, (i // 4) * 32)
    return _adopt_meta(out, t)


reg("environment/moon_phases", moon_phases, pbr=False)


# ------------------------------------------------------------------ painting atlas (1.7-1.13)

PAINTINGS = [
    ("kebab", 0, 0), ("aztec", 16, 0), ("alban", 32, 0), ("aztec2", 48, 0), ("bomb", 64, 0), ("plant", 80, 0),
    ("wasteland", 96, 0),
    ("pool", 0, 32), ("courbet", 32, 32), ("sea", 64, 32), ("sunset", 96, 32), ("creebet", 128, 32),
    ("wanderer", 0, 64), ("graham", 16, 64),
    ("fighters", 0, 96),
    ("match", 0, 128), ("bust", 32, 128), ("stage", 64, 128), ("void", 96, 128), ("skull_and_roses", 128, 128),
    ("wither", 160, 128),
    ("pointer", 0, 192), ("pigscene", 64, 192), ("burning_skull", 128, 192),
    ("skeleton", 192, 64), ("donkey_kong", 192, 112),
]


def painting_atlas(ctx):
    out = blank(ctx)
    t = None
    for name, x, y in PAINTINGS:
        t = render(f"painting/{name}", ctx.s)
        place(out, t, x, y)
    back = render("painting/back", ctx.s)
    for i in range(4):
        for j in range(4):
            place(out, back, 192 + i * 16, j * 16)
    return _adopt_meta(out, t)


reg("painting/paintings_kristoffer_zetterstrand", painting_atlas)


# ------------------------------------------------------------------ particle sheet

def particle_cells():
    """(col, row) -> modern sprite key, on the 16x16 cell grid."""
    cells = {}
    for i in range(8):
        cells[(i, 0)] = f"particle/generic_{i}"
        cells[(i, 8)] = f"particle/effect_{i}"
        cells[(i, 9)] = f"particle/spell_{i}"
        cells[(i, 10)] = f"particle/spark_{i}"
        cells[(i, 11)] = f"particle/glitter_{i}"
    for i in range(4):
        cells[(3 + i, 1)] = f"particle/splash_{i}"
    cells.update({
        (0, 2): "particle/bubble", (1, 2): "entity/fishing/fishing_hook",
        (0, 3): "particle/flame", (1, 3): "particle/lava",
        (0, 4): "particle/note", (1, 4): "particle/critical_hit", (2, 4): "particle/enchanted_hit",
        (3, 4): "particle/damage",
        (0, 5): "particle/heart", (1, 5): "particle/angry", (2, 5): "particle/glint",
        (0, 7): "particle/drip_hang", (1, 7): "particle/drip_fall", (2, 7): "particle/drip_land",
    })
    for i in range(26):
        n = 225 + i
        cells[(n % 16, n // 16)] = f"particle/sga_{chr(97 + i)}"
    return cells


def particle_sheet(ctx):
    out = blank(ctx)
    cell = ctx.w / 16          # 8 texels at 128x128, 16 at 256x256
    for (cx, cy), key in particle_cells().items():
        if key not in TEXTURES:
            continue
        t = render(key, ctx.s * int(cell // 8) if cell >= 8 else ctx.s, 8, 8)
        fit(out, t, (cx * cell, cy * cell, (cx + 1) * cell, (cy + 1) * cell))
    # firework flash: one 4x4-cell sprite at cells (4..8, 2..6)
    fl = render("particle/flash", ctx.s * max(1, int(cell // 8)), 32, 32)
    fit(out, fl, (4 * cell, 2 * cell, 8 * cell, 6 * cell))
    return out


reg("particle/particles", particle_sheet, pbr=False)
reg("particle/particles@128x128", particle_sheet, pbr=False, size=(128, 128))


# ------------------------------------------------------------------ map icon atlas

ICON_ORDER = (["player", "frame", "red_marker", "blue_marker", "target_x", "target_point", "player_off_map",
               "player_off_limits", "woodland_mansion", "ocean_monument"]
              + [f"{d}_banner" for d in DYE_NAMES]
              + ["red_x", "desert_village", "plains_village", "savanna_village", "snowy_village",
                 "taiga_village", "jungle_temple", "swamp_hut", "trial_chambers"])

ARROWS = {"player": "f4f4ee", "frame": "3aa83a", "red_marker": "d83a2e", "blue_marker": "3a5ad8"}
HOUSES = {"desert_village": ("d8bc7a", "a8783a"), "plains_village": ("b08a54", "8a3a2a"),
          "savanna_village": ("c08a4a", "a8582a"), "snowy_village": ("e8eef2", "6a4a2a"),
          "taiga_village": ("7a5a3a", "3a4a2a"), "swamp_hut": ("5a4a32", "3a4a2a"),
          "woodland_mansion": ("5a3a22", "2e1e12")}


def _sprite(ctx, rows, colors, outline="141414"):
    """8x8 icon from a texel map; '#' body, 'o' auto outline around it."""
    rgb = np.zeros((ctx.H, ctx.W, 3), np.float32)
    a = ctx.zeros()
    s = ctx.s
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in colors:
                rgb[j * s:(j + 1) * s, i * s:(i + 1) * s] = hexc(colors[ch])
                a[j * s:(j + 1) * s, i * s:(i + 1) * s] = 1
    return Tex(ctx, rgb, alpha=a, height=0.5, wrap=False, grain=0)


def draw_icon(ctx, name):
    if name in ARROWS:
        c = ARROWS[name]
        rows = ["...o....", "..o#o...", "..o#o...", ".o###o..", ".o###o..", "o##o##o.", "oo.o.oo.", "........"]
        return _sprite(ctx, rows, {"#": c, "o": "1c1c1c"})
    if name == "target_x" or name == "red_x":
        c = "f0f0f0" if name == "target_x" else "d02a20"
        rows = ["oo...oo.", "o#o.o#o.", ".o#o#o..", "..o#o...", ".o#o#o..", "o#o.o#o.", "oo...oo.", "........"]
        return _sprite(ctx, rows, {"#": c, "o": "2a1a14"})
    if name == "target_point":
        rows = ["........", "...o....", "..o#o...", ".o###o..", "o#####o.", ".ooooo..", "........", "........"]
        return _sprite(ctx, rows, {"#": "d83a2e", "o": "3a1010"})
    if name in ("player_off_map", "player_off_limits"):
        big = name == "player_off_map"
        rows = (["..ooo...", ".o###o..", "o#####o.", "o#####o.", "o#####o.", ".o###o..", "..ooo...", "........"]
                if big else ["........", "........", "..ooo...", ".o###o..", ".o###o..", "..ooo...", "........", "........"])
        return _sprite(ctx, rows, {"#": "f4f4ee", "o": "1c1c1c"})
    if name.endswith("_banner"):
        c = DYE[name[:-7]]
        hexs = "%02x%02x%02x" % tuple(int(v * 255) for v in np.clip(c, 0, 1))
        rows = ["oooooo..", "o####o..", "o####o..", "o####o..", "o####o..", "o#oo#o..", "oo..oo..", "..o....."]
        t = _sprite(ctx, rows, {"#": hexs, "o": "2a2018"})
        return t
    if name == "ocean_monument" or name == "jungle_temple":
        c, d = ("3aa898", "1e5a52") if name == "ocean_monument" else ("6a8a3a", "3a4a22")
        rows = ["...o....", "..o#o...", "..o#o...", ".o###o..", ".o#d#o..", "o#####o.", "ooooooo.", "........"]
        return _sprite(ctx, rows, {"#": c, "d": d, "o": "141c18"})
    if name == "trial_chambers":
        rows = ["........", ".oooooo.", ".o#dd#o.", ".o####o.", ".o#dd#o.", ".o####o.", ".oooooo.", "........"]
        return _sprite(ctx, rows, {"#": "c8703c", "d": "4aa28a", "o": "2a1810"})
    wall, roof = HOUSES[name]
    rows = ["...o....", "..oro...", ".orrro..", "orrrrro.", ".o###o..", ".o#d#o..", ".ooooo..", "........"]
    return _sprite(ctx, rows, {"#": wall, "r": roof, "d": "2a1a10", "o": "141010"})


def map_icon(ctx, name):
    key = f"map/decorations/{name}"
    if key in TEXTURES:
        return render(key, ctx.s, 8, 8)
    from ...engine import Ctx
    return draw_icon(Ctx(key, 8, 8, ctx.s), name)


def map_icons(ctx):
    out = blank(ctx)
    cols = ctx.w // 8
    for i, name in enumerate(ICON_ORDER):
        if i >= cols * (ctx.h // 8):
            break
        place(out, map_icon(ctx, name), (i % cols) * 8, (i // cols) * 8)
    return out


reg("map/map_icons", map_icons, pbr=False)
reg("map/map_icons@32x32", map_icons, pbr=False, size=(32, 32))
