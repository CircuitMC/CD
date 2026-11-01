"""1.12-1.21.8 bed entity sheets and pre-1.15 double chest sheets.

Bed sheet (64x64): head slab box uv(0,0) 16x16x6 and foot slab uv(0,22),
both rotated so the 16x16 "front" face is the sleeping surface (texture top =
head end) and the "back" face the underside; the head piece's "top" face is
the head end, the foot piece's "bottom" face the foot end; legs 3x3x3 at
(50,0), (50,6), (50,12), (50,18). The block-model faces of 26.3 beds supply
the top and bottom; the thin slab sides are woven with the same fabric code
and kept symmetric across their thickness (orientation independent).

Double chest (128x64): lid 30x5x14 uv(0,0), base 30x10x14 uv(0,19), latch
2x4x1 uv(0,0). Built by joining the 1.15+ left/right half sheets so that the
halves' open (seam) edges meet in the middle of every face.
"""
import numpy as np

from ..block.color_bed import FOLD_Z, SHEET, WOOD, fabric, wood
from ..block.color_common import DYE, DYE_NAMES, ramp
from ..block.color_dyed import wool_color
from .kit import blank, blit, faces, place, reg, render


def _fill(t, r, rgb, height=0.55, sss=0.1, porosity=0.55, smooth=0.06):
    s = t.ctx.s
    sl = np.s_[int(r[1] * s):int(r[3] * s), int(r[0] * s):int(r[2] * s)]
    t.color[sl] = rgb[sl] if np.ndim(rgb) == 3 else rgb
    t.alpha[sl] = 1
    t.height[sl] = height
    t.sss[sl] = sss
    t.porosity[sl] = porosity
    t.smooth[sl] = smooth


def _hem(t, r, color, vertical):
    """Darker piping on both long edges of a thin strip (symmetric)."""
    x0, y0, x1, y1 = r
    if vertical:
        edges = [(x0, y0, x0 + 1, y1), (x1 - 1, y0, x1, y1)]
    else:
        edges = [(x0, y0, x1, y0 + 1), (x0, y1 - 1, x1, y1)]
    for e in edges:
        _fill(t, e, color, height=0.45)


def bed_sheet(ctx, dye):
    t = blank(ctx)
    p = ramp(wool_color(DYE[dye]), 6, dark=0.66, light=1.15)
    blanket, _ = fabric(ctx, p, f"{dye}ent", quilt=False)
    sheet, _ = fabric(ctx, SHEET, "entsheet", quilt=False)
    head, foot = faces(0, 0, 16, 16, 6), faces(0, 22, 16, 16, 6)
    # sleeping surface and underside from the 26.3 block faces
    up_h = render(f"block/{dye}_bed_head_up", ctx.s, 16, 16)
    up_f = render(f"block/{dye}_bed_foot_up", ctx.s, 16, 16)
    down = render("block/bed_down", ctx.s, 16, 16)
    place(t, up_h, *head["front"][:2])
    place(t, up_f, *foot["front"][:2])
    place(t, down, *head["back"][:2])
    place(t, down, *foot["back"][:2])
    # slab sides: sheet near the head end (top of the strip), blanket elsewhere
    for name in ("right", "left"):
        r = head[name]
        _fill(t, r, blanket)
        _fill(t, (r[0], r[1], r[2], r[1] + FOLD_Z - 2), sheet)
        _fill(t, (r[0], r[1] + FOLD_Z - 2, r[2], r[1] + FOLD_Z), SHEET[3])
        _hem(t, (r[0], r[1] + FOLD_Z, r[2], r[3]), p[1], vertical=True)
        r = foot[name]
        _fill(t, r, blanket)
        _hem(t, r, p[1], vertical=True)
        _fill(t, (r[0], r[3] - 1, r[2], r[3]), p[1], height=0.45)   # blanket hem at the foot end
    # end faces
    _fill(t, head["top"], sheet)
    _hem(t, head["top"], SHEET[1], vertical=False)
    _fill(t, head["bottom"], blanket)
    _fill(t, foot["top"], blanket)
    _fill(t, foot["bottom"], blanket)
    _hem(t, foot["bottom"], p[1], vertical=False)
    # legs
    wc, g = wood(ctx, "entlegs")
    for v in (0, 6, 12, 18):
        for name, r in faces(50, v, 3, 3, 3).items():
            _fill(t, r, wc, height=0.55, sss=0.0, porosity=0.3, smooth=0.2)
            if name in ("right", "front", "left", "back"):
                _fill(t, (r[0], r[3] - 1, r[2], r[3]), WOOD[0], height=0.5, sss=0.0, porosity=0.3)
                _fill(t, (r[0], r[1], r[0] + 1, r[3] - 1), WOOD[3], height=0.55, sss=0.0, porosity=0.3)
            elif name == "bottom":
                _fill(t, r, WOOD[1], height=0.5, sss=0.0, porosity=0.3)
    t.grain = 0.06
    return t


for _d in DYE_NAMES:
    reg(f"entity/bed/{_d}", lambda ctx, d=_d: bed_sheet(ctx, d))
reg("entity/bed/silver", lambda ctx: bed_sheet(ctx, "light_gray"))


# ------------------------------------------------------------------ double chests

def _join(out, R, L, sbox, dbox):
    """Join the two 15-wide half boxes into one 30-wide box."""
    sf, df = faces(*sbox), faces(*dbox)
    hw = sbox[2]
    for name, (a, b) in (("top", (R, L)), ("bottom", (R, L)), ("front", (R, L)), ("back", (L, R))):
        x0, y0, x1, y1 = df[name]
        sr = sf[name]
        blit(out, a, sr, (x0, y0))
        blit(out, b, sr, (x0 + hw, y0))
    blit(out, R, sf["right"], df["right"][:2])
    blit(out, L, sf["left"], df["left"][:2])


def double_chest(ctx, style):
    R = render(f"entity/chest/{style}_right", ctx.s, 64, 64)
    L = render(f"entity/chest/{style}_left", ctx.s, 64, 64)
    out = blank(ctx)
    _join(out, R, L, (0, 19, 15, 10, 14), (0, 19, 30, 10, 14))
    _join(out, R, L, (0, 0, 15, 5, 14), (0, 0, 30, 5, 14))
    _join(out, R, L, (0, 0, 1, 4, 1), (0, 0, 2, 4, 1))      # latch
    out.normal_strength, out.grain = R.normal_strength, R.grain
    return out


for _s in ("normal", "trapped", "christmas"):
    reg(f"entity/chest/{_s}_double", lambda ctx, s=_s: double_chest(ctx, s))
