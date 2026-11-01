"""Bitmap font sheets (CircuitMC typeface) + a provider override that only lists
characters this pack actually draws (everything else falls back to the unifont)."""
import functools
import json
import unicodedata
from pathlib import Path

import numpy as np

from ...registry import register, static_file
from . import glyphs
from .common import Canvas, WHITE

FONTS = Path(__file__).resolve().parents[3] / "data" / "fonts"
DEFAULT = json.loads((FONTS / "include__default.json").read_text())
ALT = json.loads((FONTS / "alt.json").read_text())
ILLAGER = json.loads((FONTS / "illageralt.json").read_text())


def _provider(cfg, name):
    for p in cfg["providers"]:
        if p.get("file") == f"minecraft:font/{name}.png":
            return p
    raise KeyError(name)


def _fits(cells, cw, ch, yoff):
    return all(0 <= x < cw and 0 <= y + yoff < ch for x, y in cells)


def _sheet(ctx, chars, lookup, yoff):
    c = Canvas(ctx)
    rows, cols = len(chars), len(chars[0])
    cw, chh = ctx.w // cols, ctx.h // rows
    for r, line in enumerate(chars):
        for i, ch in enumerate(line):
            if ch == "\0":
                continue
            g = lookup(ch)
            if not g:
                continue
            for (x, y) in g:
                if 0 <= x < cw and 0 <= y + yoff < chh:
                    c.px(i * cw + x, r * chh + y + yoff, WHITE)
    return c.tex()


def _main(ch):
    return glyphs.glyph(ch)


@functools.lru_cache(maxsize=None)
def fit8(ch):
    """Glyph that fits an 8-tall cell (em rows 0..7): accented capitals use a small-cap base with
    the marks directly on top, accented lowercase drop the gap between letter and mark."""
    g = glyphs.glyph(ch)
    if not g:
        return None
    ys = [y for _, y in g]
    if min(ys) >= 0 and max(ys) <= 7:
        return g
    nfd = unicodedata.normalize("NFD", ch)
    above = [m for m in nfd[1:] if m in glyphs.MARKS_ABOVE]
    if len(nfd) > 1 and above and len(above) + sum(m in glyphs.MARKS_BELOW for m in nfd[1:]) == len(nfd) - 1:
        base = nfd[0]
        if base.isupper():
            bg = glyphs._small_cap(base)
        else:
            bg = glyphs.glyph({"i": "ı", "j": "ȷ"}.get(base, base))
        if bg:
            cells = set(bg)
            x0, x1, top, y1 = glyphs._bounds(cells)
            cx = (x0 + x1) / 2
            y = top
            for m in above:
                spec = glyphs.MARKS_ABOVE[m]
                w, h = glyphs._mark_size(spec)
                if h == 3:
                    spec = " ".join(spec.split()[:2])
                    h = 2
                y -= h
                cells = glyphs._stamp(cells, spec, int(round(cx - (w - 1) / 2)), y)
            yb = max(y1, 6) + 1
            for m in nfd[1:]:
                if m in glyphs.MARKS_BELOW:
                    spec = glyphs.MARKS_BELOW[m].split()[0]
                    cells = glyphs._stamp(cells, spec, int(round(cx)) if m != "\u0328" else x1 - 1, yb)
            g = frozenset(cells)
            ys = [y for _, y in g]
    if min(ys) < 0:
        g = frozenset((x, y - min(ys)) for x, y in g)
    return g


def _yoff(p):
    return 3 if p.get("height", 8) == 12 else 0


def _lookup(p):
    return _main if _yoff(p) else fit8


OLD = {}
for _f in sorted((FONTS / "old").glob("*__default.json")):
    OLD[_f.name.split("__")[0]] = {q["file"].split("/")[-1][:-4]: q for q in json.loads(_f.read_text())["providers"]
                                   if "chars" in q}


def _union_chars(name):
    """Modern grid, with cells that are empty in 26.3 filled from older grids of the same size
    (pre-1.17 ascii.png also held accented letters and Greek in its upper/lower rows)."""
    rows = [list(r) for r in _provider(DEFAULT, name)["chars"]]
    for ver in ("1.16.5", "1.14.4", "1.13.2"):
        q = OLD.get(ver, {}).get(name)
        if not q or len(q["chars"]) != len(rows):
            continue
        for j, r in enumerate(q["chars"]):
            for i, ch in enumerate(r):
                if rows[j][i] == "\0" and ch != "\0":
                    rows[j][i] = ch
    return ["".join(r) for r in rows]


for _name in ("ascii", "nonlatin_european", "accented"):
    _p = _provider(DEFAULT, _name)
    register(f"font/{_name}", lambda ctx, p=_p, n=_name: _sheet(ctx, _union_chars(n), _lookup(p), _yoff(p)))

# older font sheet sizes (1.13 - 1.16): their own char grids from that version's font/default.json
for _ver, _name in (("1.13.2", "nonlatin_european"), ("1.14.4", "nonlatin_european"), ("1.16.5", "nonlatin_european"),
                    ("1.13.2", "accented"), ("1.14.4", "accented")):
    _q = OLD[_ver][_name]
    _cw = 9 if _q.get("height") == 12 else 8
    _ch = 12 if _q.get("height") == 12 else 8
    _size = (16 * _cw, len(_q["chars"]) * _ch)
    register(f"font/{_name}@{_size[0]}x{_size[1]}",
             lambda ctx, q=_q: _sheet(ctx, q["chars"], _lookup(q), _yoff(q)), size=_size)


def _filtered_default():
    out = {"providers": []}
    for p in DEFAULT["providers"]:
        q = dict(p)
        if p.get("type") == "bitmap" and "chars" in p:
            q["chars"] = ["".join(c if c != "\0" and glyphs.glyph(c) else "\0" for c in row) for row in p["chars"]]
        out["providers"].append(q)
    return json.dumps(out, ensure_ascii=True, indent=1)


static_file("minecraft/font/include/default.json", _filtered_default())


# ----------------------------------------------------------------- rune alphabets
def _rune_set(strokes, count, seed, w, h, top, min_strokes=2, max_strokes=3):
    """Deterministic set of distinct, connected rune glyphs assembled from stroke primitives."""
    import itertools
    cands = []
    for k in range(min_strokes, max_strokes + 1):
        for idx in itertools.combinations(range(len(strokes)), k):
            cells = frozenset().union(*[strokes[i] for i in idx])
            if len(cells) < 6 or any(cells == strokes[i] for i in idx):
                continue
            todo, comp = [next(iter(cells))], set()
            while todo:
                p = todo.pop()
                if p in comp:
                    continue
                comp.add(p)
                x, y = p
                todo += [q for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1),
                                     (x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1)) if q in cells]
            if len(comp) == len(cells):
                cands.append(cells)
    cands = sorted(set(cands), key=lambda c: sorted(c))
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(cands))
    out = []
    for i in order[:count]:
        cells = cands[i]
        x0 = min(x for x, _ in cells)
        out.append(frozenset((x - x0, y + top) for x, y in cells))
    return out


def _cells(rows):
    return frozenset((i, j) for j, r in enumerate(rows.split()) for i, ch in enumerate(r) if ch == "#")


# enchanting runes: blocky, orthogonal strokes on a 5x6 grid
SGA_STROKES = [_cells(s) for s in (
    "#.... #.... #.... #.... #.... #....",  # left stem
    "....# ....# ....# ....# ....# ....#",  # right stem
    "..#.. ..#.. ..#.. ..#.. ..#.. ..#..",  # mid stem
    "##### ..... ..... ..... ..... .....",  # top bar
    "..... ..... ..... ..... ..... #####",  # bottom bar
    "..... ..... ##### ..... ..... .....",  # mid bar
    "#.... #.... ###.. ..... ..... .....",  # upper hook
    "..... ..... ..... ..### ....# ....#",  # lower hook
    "..... ..#.. ..#.. ..#.. ..... .....",  # short mid
    "###.. ..#.. ..#.. ..... ..... .....",  # corner
    "..... ..... ..... #.... #.... ###..",  # foot
    "....# ...## ....# ..... ..... .....",  # flag
    "..... .###. ..... ..... ..... .....",  # short top bar
    "..... ..... ..... .###. ..... .....",  # short low bar
)]
# illager runes: angular, with diagonals, 5x7
ILL_STROKES = [_cells(s) for s in (
    "#.... #.... #.... #.... #.... #.... #....",
    "....# ....# ....# ....# ....# ....# ....#",
    "..#.. ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    "#.... .#... ..#.. ...#. ....# ..... .....",
    "....# ...#. ..#.. .#... #.... ..... .....",
    "..... ..... #.... .#... ..#.. ...#. ....#",
    "..... ..... ....# ...#. ..#.. .#... #....",
    "##### ..... ..... ..... ..... ..... .....",
    "..... ..... ..... ##### ..... ..... .....",
    "..... ..... ..... ..... ..... ..... #####",
    "..#.. .#.#. #...# ..... ..... ..... .....",
    "..... ..... ..... ..... #...# .#.#. ..#..",
)]

@functools.lru_cache(maxsize=None)
def _runes(kind):
    if kind == "sga":
        return _rune_set(SGA_STROKES, 26, 1337, 5, 6, 1)
    return _rune_set(ILL_STROKES, 36, 4242, 5, 7, 0, 2, 3)


def _sga(ch):
    if ch.isascii() and ch.isalpha():
        return _runes("sga")[ord(ch.upper()) - 65]
    return None


_ILL_ORDER = "abcdefghijklmnopqrstuvwxyz0123456789"


def _ill(ch):
    if ch in "!,-.?":
        return glyphs.glyph(ch)
    k = ch.lower()
    if k in _ILL_ORDER:
        return _runes("ill")[_ILL_ORDER.index(k)]
    return None


register("font/ascii_sga", lambda ctx: _sheet(ctx, _provider(ALT, "ascii_sga")["chars"], _sga, 0))
register("font/asciillager", lambda ctx: _sheet(ctx, _provider(ILLAGER, "asciillager")["chars"], _ill, 0))
