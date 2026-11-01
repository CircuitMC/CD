"""Wood sets: palettes shared by every block_wood module, planks, logs, stripped logs,
log tops and leaves for the overworld trees (bamboo / nether stems live in their own modules)."""
import numpy as np

from ...engine import pal
from ...registry import register
from .wood_kit import (board_field, canopy, end_grain_rings, fiber_grain, gray, plate_bark,
                       smooth_bark)

# planks: 6 shades (p[0] seams), bark: 5+ shades, stripped: 4, rings: 2 (+ optional heart)
WOODS = {
    "oak": dict(
        planks=pal("5e4628", "7d6038", "8f6f42", "a07e4d", "af8c58", "bd9a64"),
        bark=pal("2f2316", "45341f", "564129", "674f32", "785d3b", "866a45"),
        stripped=pal("a5834f", "b6925a", "c4a065", "d0ad70"),
        rings=pal("9c7c4c", "b6955f"), heart=pal("8a6a3f")[0],
        bark_style=("plates", dict(widths=(2, 4), seglen=(4, 9)))),
    "spruce": dict(
        planks=pal("3c2818", "553a24", "634430", "714f38", "7e5a40", "8a654a"),
        bark=pal("1c130c", "2a1d13", "36261a", "433021", "4f3a28", "5a4430"),
        stripped=pal("6e4c2e", "7e5936", "8d653e", "9a7247"),
        rings=pal("6c4c30", "81603c"), heart=pal("5c3f27")[0],
        bark_style=("plates", dict(widths=(2, 3), seglen=(2, 4), warp=0.5))),
    "birch": dict(
        planks=pal("9a8a5e", "b8a777", "c6b583", "d2c28f", "ddce9b", "e6d9a7"),
        bark=pal("26221e", "bdb8ad", "cfcac0", "dedad1", "ebe8e0", "f5f3ee"),
        stripped=pal("b7a578", "c7b585", "d4c391", "e0cf9d"),
        rings=pal("c5b383", "d7c796"), heart=None,
        bark_style=("smooth", dict(marks="patch", count=9, mark_color=pal("2a2622")[0],
                                   light_color=pal("fbfaf6")[0], streaky=0.25))),
    "jungle": dict(
        planks=pal("6a4530", "8a5f41", "9a6c4a", "a97954", "b6855e", "c19168"),
        bark=pal("2c220d", "3e3115", "4e3e1c", "5d4a22", "6b5629", "786231"),
        stripped=pal("aa7b50", "bc8b5c", "ca9867", "d6a472"),
        rings=pal("a87951", "c09063"), heart=pal("8f6340")[0],
        bark_style=("plates", dict(widths=(1, 3), seglen=(6, 14), tone_amt=0.2, crack=False))),
    "acacia": dict(
        planks=pal("7b3a1f", "a2502c", "b25b33", "c0663b", "cc7144", "d77c4e"),
        bark=pal("2e2b27", "433f39", "524e47", "605b53", "6d685f", "79746a"),
        stripped=pal("aa542f", "be6138", "cd6d41", "d9794b"),
        rings=pal("b35b35", "cc6f44"), heart=pal("9a4a2a")[0],
        bark_style=("plates", dict(widths=(2, 5), seglen=(3, 7), furrow_color=pal("5a2e1e")[0]))),
    "dark_oak": dict(
        planks=pal("251709", "3e2914", "4a321b", "553b21", "604428", "6a4d30"),
        bark=pal("150e07", "22180e", "2d2013", "372818", "41301d", "4a3823"),
        stripped=pal("503921", "5e4328", "6b4d2f", "775736"),
        rings=pal("4d3621", "60462a"), heart=pal("3e2a18")[0],
        bark_style=("plates", dict(widths=(3, 5), seglen=(5, 12), tone_amt=0.08))),
    "mangrove": dict(
        planks=pal("441a17", "632822", "74302a", "843831", "92413a", "9e4a42"),
        bark=pal("231a15", "34281f", "433328", "513e31", "5e493a", "6a5443"),
        stripped=pal("74302a", "853a31", "95443a", "a24e43"),
        rings=pal("7a342d", "90433a"), heart=pal("62261f")[0],
        bark_style=("plates", dict(widths=(1, 2), seglen=(6, 16), crack=False, tone_amt=0.25))),
    "cherry": dict(
        planks=pal("94675f", "bd8c83", "cc9a91", "d8a8a0", "e2b5ad", "eac0b9"),
        bark=pal("1a1014", "2c1c22", "38252b", "443036", "4f3a40", "5a4349"),
        stripped=pal("b97b78", "c98b88", "d69896", "e0a5a2"),
        rings=pal("cc908c", "dfa6a1"), heart=pal("b5736f")[0],
        bark_style=("smooth", dict(marks="dash", count=10, mark_color=pal("1a1014")[0],
                                   light_color=pal("7a6066")[0], streaky=0.35))),
    "pale_oak": dict(
        planks=pal("948d86", "b6b0aa", "c4beb8", "d0cbc5", "dbd6d1", "e5e1dc"),
        bark=pal("332e2b", "4a4440", "59534e", "68625c", "77706a", "857e77"),
        stripped=pal("c9c2bb", "d5cfc8", "e0dad4", "e9e4df"),
        rings=pal("cdc6bf", "ddd8d2"), heart=pal("b9b1a9")[0],
        bark_style=("plates", dict(widths=(2, 4), seglen=(5, 10)))),
    "poplar": dict(
        planks=pal("8d8b6e", "b0ad8d", "bfbc9b", "cbc8a8", "d6d3b4", "dfdcbf"),
        bark=pal("4b4f45", "8d9284", "9da294", "adb2a4", "bcc0b3", "c9cdc0"),
        stripped=pal("cfcbab", "dad6b7", "e3e0c2", "ebe8cd"),
        rings=pal("c9c5a6", "dbd8ba"), heart=pal("b8b394")[0],
        bark_style=("smooth", dict(marks="diamond", count=6, mark_color=pal("4b4f45")[0],
                                   light_color=pal("d3d7ca")[0], streaky=0.3)),
        straight=0.85),
    # palettes used by the bamboo / nether modules (registered there)
    "bamboo": dict(
        planks=pal("7a6a26", "a6933a", "b8a444", "c7b34f", "d3c05a", "dccb66"),
        bark=pal("3d5418", "55721f", "668826", "779b2e", "88ad37", "99bd44"),
        stripped=pal("b5a446", "c6b553", "d3c15d", "dfcd69"),
        rings=pal("c0ad4d", "d4c25e"), heart=None),
    "crimson": dict(
        planks=pal("3e1524", "5c2136", "6d2840", "7c2f49", "8a3652", "963e5b"),
        bark=pal("230c13", "3a1520", "4a1b28", "5a2230", "6a2939", "783142"),
        stripped=pal("7a2a45", "8b3350", "9b3d5a", "a84764"),
        rings=pal("7d2e4a", "973c5c"), heart=None,
        vein=pal("a3243c", "d03a52", "f06a7a")),
    "warped": dict(
        planks=pal("153a37", "235650", "2a645d", "317168", "387d72", "3f887c"),
        bark=pal("151b21", "232d35", "2b3841", "33434c", "3b4e57", "445861"),
        stripped=pal("2f7469", "378276", "408f82", "4a9b8d"),
        rings=pal("327568", "3f8c7d"), heart=None,
        vein=pal("17998a", "2cc9b0", "6af0d8")),
}

OVERWORLD = ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry", "pale_oak",
             "poplar"]

TINTED_LEAVES = {
    "oak": dict(count=14, min_dist=2.4, gap=0.55, holes=0.75),
    "spruce": dict(count=26, min_dist=1.8, gap=0.45, holes=0.6, light=0.18),
    "birch": dict(count=18, min_dist=2.1, gap=0.5, holes=0.7),
    "jungle": dict(count=9, min_dist=3.6, gap=0.6, holes=0.8),
    "acacia": dict(count=12, min_dist=2.6, gap=0.65, holes=0.85, speckle=0.07),
    "dark_oak": dict(count=11, min_dist=3.0, gap=0.5, holes=0.6, speckle=0.03),
    "mangrove": dict(count=16, min_dist=2.2, gap=0.55, holes=0.7),
}
LEAF_GRAY = {"oak": (0.36, 0.86), "spruce": (0.32, 0.74), "birch": (0.42, 0.9), "jungle": (0.36, 0.88),
             "acacia": (0.4, 0.86), "dark_oak": (0.3, 0.78), "mangrove": (0.36, 0.84)}

COLORED_LEAVES = {
    "cherry": (pal("8f3a60", "b5527e", "cc6895", "de82aa", "eb9dbf", "f5b9d2"),
               dict(count=15, min_dist=2.3, gap=0.55, holes=0.7, speckle=0.04)),
    "pale_oak": (pal("454c43", "5b6257", "6f766a", "848a7e", "979d91", "aab0a3"),
                 dict(count=14, min_dist=2.4, gap=0.5, holes=0.7)),
    "azalea": (pal("33501b", "456a23", "557d2b", "659034", "75a23d", "88b34b"),
               dict(count=13, min_dist=2.5, gap=0.55, holes=0.7)),
    "red_poplar": (pal("5c140f", "841f17", "a12c1f", "b93c26", "cc4f2d", "da6638"),
                   dict(count=17, min_dist=2.1, gap=0.5, holes=0.7)),
    "orange_poplar": (pal("7a360d", "a04c12", "bb6017", "d2751d", "e28b27", "eca23a"),
                      dict(count=17, min_dist=2.1, gap=0.5, holes=0.7)),
    "yellow_poplar": (pal("7a5d0f", "a48215", "c09c1c", "d5b326", "e3c634", "ecd64e"),
                      dict(count=17, min_dist=2.1, gap=0.5, holes=0.7)),
}


def _bind(fn, *args):
    return lambda ctx: fn(ctx, *args)


def planks_tex(ctx, w):
    spec = WOODS[w]
    return board_field(ctx, spec["planks"], salt=w, straight=spec.get("straight", 0.0)).tex(wrap=True)


def log_tex(ctx, w):
    spec = WOODS[w]
    style, kw = spec["bark_style"]
    if style == "plates":
        cv = plate_bark(ctx, spec["bark"], salt=w, **kw)
    else:
        cv = smooth_bark(ctx, spec["bark"], salt=w, **kw)
    if w == "jungle":  # a little moss in the furrows
        m = (ctx.texel_noise("jmoss", soft=False) > 0.93) & (cv.height < 0.2)
        cv.put(m, color=pal("4f5a22")[0], sss=0.3)
    return cv.tex(wrap=True)


def log_top_tex(ctx, w, is_stripped):
    spec = WOODS[w]
    st = spec["stripped"]
    rim = st[:3] * 0.88 if is_stripped else spec["bark"][1:5]
    rings = np.stack([st[0] * 0.86, st[2]])
    return end_grain_rings(ctx, rings, rim, salt=w, heart=spec.get("heart")).tex(wrap=True)


def stripped_tex(ctx, w):
    return fiber_grain(ctx, WOODS[w]["stripped"], salt=w).tex(wrap=True)


def tinted_leaves(ctx, w):
    lo, hi = LEAF_GRAY[w]
    t = canopy(ctx, gray(lo, hi), salt=w, **TINTED_LEAVES[w])
    if w == "spruce":  # needle rows: short diagonal strokes
        rows = ((np.floor(ctx.x) - np.floor(ctx.y)) % 3 == 0) & (t.alpha > 0.5)
        rows &= ctx.texel_noise("needle", soft=False) > 0.25
        t.color = np.where(rows[..., None], t.color * 0.82, t.color)
        t.height = np.where(rows, t.height - 0.08, t.height)
    return t


def colored_leaves(ctx, w):
    p, kw = COLORED_LEAVES[w]
    return canopy(ctx, p, salt=w, **kw)


for _w in OVERWORLD:
    register(f"block/{_w}_planks", _bind(planks_tex, _w))
    register(f"block/{_w}_log", _bind(log_tex, _w))
    register(f"block/{_w}_log_top", _bind(log_top_tex, _w, False))
    register(f"block/stripped_{_w}_log", _bind(stripped_tex, _w))
    register(f"block/stripped_{_w}_log_top", _bind(log_top_tex, _w, True))
for _w in TINTED_LEAVES:
    register(f"block/{_w}_leaves", _bind(tinted_leaves, _w))
for _w in COLORED_LEAVES:
    register(f"block/{_w}_leaves", _bind(colored_leaves, _w))
