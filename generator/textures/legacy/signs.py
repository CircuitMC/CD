"""Sign entity sheets used before 26.x (64x32).

Standing/wall sign: board 24x12x2 uv(0,0), post 2x14x2 uv(0,14).
Hanging sign: board 14x10x2 uv(0,12), top plank 16x2x4 uv(0,0), chains 3x6 planes
at uv(0,6) and uv(6,6) (front + back), V-chains 12x6 plane at uv(14,6).
Wood surfaces come from the same board / grain builders and palettes as the
26.3 sign and plank textures.
"""
import numpy as np

from ...engine import IRON, pal
from ..block.wood import WOODS
from ..block.wood_kit import board_field, fiber_grain
from .kit import blank, blit, faces, reg

SIGN_WOODS = ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry", "pale_oak",
              "bamboo", "crimson", "warped"]
CHAIN = pal("1e2026", "34373f", "4e525c", "6c717c")


def _shade_faces(t, fs, names, f):
    s = t.ctx.s
    for n in names:
        x0, y0, x1, y1 = fs[n]
        t.color[int(y0 * s):int(y1 * s), int(x0 * s):int(x1 * s)] *= f


def _border(t, r, f):
    s = t.ctx.s
    x0, y0, x1, y1 = [int(v * s) for v in r]
    for sl in (np.s_[y0:y0 + s, x0:x1], np.s_[y1 - s:y1, x0:x1], np.s_[y0:y1, x0:x0 + s], np.s_[y0:y1, x1 - s:x1]):
        t.color[sl] *= f


def sign_sheet(ctx, w):
    spec = WOODS[w]
    boards = board_field(ctx, spec["planks"], boards=8, offset=2, salt=f"esign{w}", joints=False, knots=0,
                         straight=0.3).tex(wrap=False)
    post = fiber_grain(ctx, spec["planks"][1:5] * 0.92, salt=f"epost{w}", vertical=True).tex(wrap=False)
    out = blank(ctx)
    board = faces(0, 0, 24, 12, 2)
    for r in board.values():
        blit(out, boards, r)
    _shade_faces(out, board, ("top",), 1.06)
    _shade_faces(out, board, ("bottom", "right", "left"), 0.86)
    for n in ("front", "back"):
        _border(out, board[n], 0.9)
    stick = faces(0, 14, 2, 14, 2)
    for r in stick.values():
        blit(out, post, r)
    _shade_faces(out, stick, ("right", "back"), 0.88)
    _shade_faces(out, stick, ("top", "bottom"), 0.8)
    out.color = np.clip(out.color, 0, 1)
    out.grain = boards.grain
    return out


def _chain(out, ctx, r, rows):
    """Stamp a chain texel map into rect r (other texels stay transparent)."""
    s = ctx.s
    x0, y0 = int(r[0]), int(r[1])
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            c = CHAIN[{"#": 2, "d": 1, "l": 3}[ch]]
            sl = np.s_[(y0 + j) * s:(y0 + j + 1) * s, (x0 + i) * s:(x0 + i + 1) * s]
            out.color[sl] = c
            out.alpha[sl] = 1
            out.height[sl] = 0.6
            out.smooth[sl] = 0.55
            out.metal[sl] = IRON


LINK = [".l.", "l.d", "#.d", ".d.", ".#.", ".d."]


def hanging_sheet(ctx, w):
    spec = WOODS[w]
    p = spec["stripped"]
    board_t = fiber_grain(ctx, p, salt=f"hsb{w}", vertical=False).tex(wrap=False)
    bar_t = fiber_grain(ctx, np.clip(p * 0.86, 0, 1), salt=f"hsp{w}", vertical=False).tex(wrap=False)
    out = blank(ctx)
    plank = faces(0, 0, 16, 2, 4)
    for r in plank.values():
        blit(out, bar_t, r)
    _shade_faces(out, plank, ("bottom", "right", "left"), 0.84)
    _shade_faces(out, plank, ("top",), 1.05)
    board = faces(0, 12, 14, 10, 2)
    for r in board.values():
        blit(out, board_t, r)
    _shade_faces(out, board, ("bottom", "right", "left"), 0.86)
    for n in ("front", "back"):
        _border(out, board[n], 0.88)
    out.color = np.clip(out.color, 0, 1)
    for x in (0, 3, 6, 9):
        _chain(out, ctx, (x, 6), LINK)
    v = [".....##.....", "....d..d....", "...l....l...", "..d......d..", ".#........#.", "d..........d"]
    for x in (14, 26):
        _chain(out, ctx, (x, 6), v)
    out.grain = board_t.grain
    return out


reg("entity/sign", lambda ctx: sign_sheet(ctx, "oak"))
for _w in SIGN_WOODS:
    reg(f"entity/signs/{_w}", lambda ctx, w=_w: sign_sheet(ctx, w))
    reg(f"entity/signs/hanging/{_w}", lambda ctx, w=_w: hanging_sheet(ctx, w))


# ------------------------------------------------------------------ 1.7-1.8 boat (64x32)

def boat_old(ctx):
    """Single oak boat: hull bottom 24x16x4 uv(0,8), side walls 20x6x2 / 16x6x2 uv(0,0)."""
    spec = WOODS["oak"]
    hull = board_field(ctx, spec["planks"], boards=8, offset=0, salt="oldboat", joints=True, knots=1,
                       straight=0.4).tex(wrap=False)
    out = blank(ctx)
    walls = faces(0, 0, 20, 6, 2)
    bottom = faces(0, 8, 24, 16, 4)
    for r in list(walls.values()) + list(bottom.values()):
        blit(out, hull, r)
    _shade_faces(out, walls, ("top",), 1.08)
    _shade_faces(out, walls, ("back",), 0.8)            # inner side of the walls
    _shade_faces(out, bottom, ("front",), 0.78)         # inside floor
    _shade_faces(out, bottom, ("right", "left", "top", "bottom"), 0.88)
    out.color = np.clip(out.color, 0, 1)
    out.grain = hull.grain
    return out


reg("entity/boat", boat_old)
