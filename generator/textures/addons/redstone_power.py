"""Add-on pack: shows the signal strength (0-15) on every piece of redstone dust.

Works in plain vanilla (no mods): the pack ships its own redstone_wire
blockstate with original wire models plus one overlay model per power level.
"""
import json

import numpy as np

from ...engine import Tex
from ...registry import register, static_file

PACK = "redstone_power"
NS = "circuitmc"

# 3x5 digit glyphs
DIGITS = {
    "0": ["###", "#.#", "#.#", "#.#", "###"],
    "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["###", "..#", "###", "#..", "###"],
    "3": ["###", "..#", ".##", "..#", "###"],
    "4": ["#.#", "#.#", "###", "..#", "..#"],
    "5": ["###", "#..", "###", "..#", "###"],
    "6": ["###", "#..", "###", "#.#", "###"],
    "7": ["###", "..#", ".#.", ".#.", ".#."],
    "8": ["###", "#.#", "###", "#.#", "###"],
    "9": ["###", "#.#", "###", "..#", "###"],
}


def glyph_cells(text):
    cells, x = set(), 0
    for ch in text:
        for j, row in enumerate(DIGITS[ch]):
            for i, c in enumerate(row):
                if c == "#":
                    cells.add((x + i, j))
        x += 4
    return cells, x - 1


def power_digits(ctx, level):
    cells, width = glyph_cells(str(level))
    ox, oy = (16 - width) // 2, 5
    glyph = np.zeros((ctx.H, ctx.W), bool)
    for i, j in cells:
        glyph |= ctx.rect(ox + i, oy + j, ox + i + 1, oy + j + 1) > 0
    s = ctx.s
    outline = np.zeros_like(glyph)
    for dy in (-s, 0, s):
        for dx in (-s, 0, s):
            outline |= np.roll(np.roll(glyph, dy, 0), dx, 1)
    outline &= ~glyph
    t = level / 15
    fg = np.array([0.55, 0.55, 0.58]) if level == 0 else np.array([1.0, 0.75 + 0.25 * t, 0.45 + 0.55 * t])
    color = np.where(glyph[..., None], fg, np.array([0.08, 0.02, 0.02]))
    alpha = (glyph | outline).astype(np.float32)
    em = np.where(glyph, 0.6 if level else 0.0, 0.0)
    return Tex(ctx, color, alpha=alpha, height=np.where(glyph, 0.8, 0.6), emissive=em, wrap=False, grain=0)


def dust_dot(ctx):
    """Round blob centered on the block; same width/brightness as the line core."""
    d = np.hypot(ctx.x - 8, ctx.y - 8)
    m = d < 3.0
    v = np.where(d < 2.0, 0.95, 0.72) - ctx.texel_noise("dot") * 0.08
    return Tex(ctx, np.repeat(v[..., None], 3, -1), alpha=m.astype(np.float32),
               height=np.where(m, 0.7, 0.5), smooth=0.4, wrap=False, grain=0)


def dust_line(ctx):
    """Straight line exactly centered on the block (4 texels: bright 2-texel core,
    darker edges), uniform along its length so pieces join without steps."""
    dx = np.abs(ctx.x - 8)
    m = dx < 2.0
    v = np.where(dx < 1.0, 0.95, 0.72) - ctx.texel_noise("line") * 0.08
    return Tex(ctx, np.repeat(v[..., None], 3, -1), alpha=m.astype(np.float32),
               height=np.where(m, 0.7, 0.5), smooth=0.4, grain=0)


register(f"/{NS}/textures/block/redstone/dot", dust_dot, size=(16, 16), pack=PACK)
register(f"/{NS}/textures/block/redstone/line", dust_line, size=(16, 16), pack=PACK)
for _lvl in range(16):
    register(f"/{NS}/textures/block/redstone_power/{_lvl}",
             lambda ctx, l=_lvl: power_digits(ctx, l), size=(16, 16), pack=PACK)


def model(textures, elements):
    return json.dumps({"ambientocclusion": False, "textures": textures, "elements": elements}, indent=1)


def flat(frm, to, face, uv, tex, tint=True, shade=True):
    f = {"uv": uv, "texture": tex}
    if tint:
        f["tintindex"] = 0
    return {"from": frm, "to": to, "shade": shade, "faces": {face: f}}


T = {"particle": f"{NS}:block/redstone/dot", "dot": f"{NS}:block/redstone/dot",
     "line": f"{NS}:block/redstone/line"}
MODELS = f"{NS}/models/block/redstone"
static_file(f"{MODELS}/dot.json", model(T, [flat([0, 0.25, 0], [16, 0.25, 16], "up", [0, 0, 16, 16], "#dot")]), PACK)
static_file(f"{MODELS}/side.json", model(T, [flat([0, 0.25, 0], [16, 0.25, 8], "up", [0, 0, 16, 8], "#line")]), PACK)
static_file(f"{MODELS}/up.json", model(T, [flat([0, 0, 0.25], [16, 16, 0.25], "south", [0, 0, 16, 16], "#line")]), PACK)
for _lvl in range(16):
    tex = f"{NS}:block/redstone_power/{_lvl}"
    static_file(f"{MODELS}/power_{_lvl}.json",
                model({"particle": tex, "digit": tex},
                      [flat([0, 0.5, 0], [16, 0.5, 16], "up", [0, 0, 16, 16], "#digit", tint=False, shade=False)]),
                PACK)

SIDE = "side|up"
ROT = {"north": 0, "east": 90, "south": 180, "west": 270}


def apply(name, y=0):
    a = {"model": f"{NS}:block/redstone/{name}"}
    if y:
        a["y"] = y
    return a


parts = [{
    "when": {"OR": [
        {"north": "none", "east": "none", "south": "none", "west": "none"},
        {"north": SIDE, "east": SIDE}, {"east": SIDE, "south": SIDE},
        {"south": SIDE, "west": SIDE}, {"west": SIDE, "north": SIDE},
    ]},
    "apply": apply("dot"),
}]
parts += [{"when": {d: SIDE}, "apply": apply("side", y)} for d, y in ROT.items()]
parts += [{"when": {d: "up"}, "apply": apply("up", y)} for d, y in ROT.items()]
# Unpowered dust (0) shows no number, so idle wiring stays clean.
parts += [{"when": {"power": str(l)}, "apply": apply(f"power_{l}")} for l in range(1, 16)]
static_file("minecraft/blockstates/redstone_wire.json", json.dumps({"multipart": parts}, indent=1), PACK)
