"""Bed block-model faces (26.x beds are block models, one texture per face).

Assumed geometry (model for a bed whose head points north, rotated by the
blockstate; faces use automatic block-space UVs): mattress y 3..9 -> texture
rows 7..12, legs y 0..3 -> rows 13..15 at the outer end of each half, rows
0..6 unused (transparent). Up faces show the whole top: pillow at the north
end of the head half, a folded sheet strip, then the blanket down to the foot.

Shared faces (bed_down, bed_head_north) are undyed: wood and white sheet.
"""
import numpy as np

from ...engine import Tex, pal
from ...registry import register
from .color_common import DYE, DYE_NAMES, ramp
from .color_dyed import wool_color

WOOD = pal("4a3020", "6a4630", "7f5638", "946743", "a6784f", "b88a5c")
SHEET = pal("8f8a86", "b9b4ae", "d6d2cc", "e8e5e0", "f6f4f1")
FOLD_Z = 9          # blanket starts this many texels from the head end
TOP_ROW = 7         # first texture row of the mattress on side faces
RAIL = (11, 13)     # wooden side rail rows
LEG = (13, 16)


def _blank(ctx):
    rgb = np.broadcast_to(WOOD[2], (ctx.H, ctx.W, 3)).copy()
    return rgb, ctx.zeros(), ctx.full(0.0)


def fabric(ctx, p, salt, quilt=True):
    """Soft blanket weave in palette p (5+ shades)."""
    n = ctx.noise(4, 2, 0.5, salt=f"{salt}n")
    weave = ((ctx.tx + ctx.ty) % 2) * 0.06 if ctx.pixel_art else \
        (np.sin(ctx.x * np.pi * 2) * np.sin(ctx.y * np.pi * 2)) * 0.03
    v = 0.55 + (n - 0.5) * 0.35 + weave + (ctx.texel_noise(salt) - 0.5) * 0.12
    if quilt:  # diagonal stitched diamonds, every 8 texels
        s = np.mod(ctx.x + ctx.y, 8)
        t = np.mod(ctx.x - ctx.y, 8)
        st = (np.minimum(s, 8 - s) < 0.5) | (np.minimum(t, 8 - t) < 0.5)
        v = np.where(st, v - 0.22, v)
    return ctx.palette(p, np.clip(v, 0, 1)), v


def wood(ctx, salt):
    g = ctx.noise(4, 2, 0.5, salt=f"{salt}w", stretch=(4, 1))
    v = 0.5 + (g - 0.5) * 0.6 + (ctx.texel_noise(f"{salt}wt") - 0.5) * 0.2
    return ctx.palette(WOOD[1:], np.clip(v, 0, 1)), g


def side(ctx, blanket_p, sheet_cols, leg_cols, legs_both=False, hem=True, salt="side"):
    """Side face: mattress band (blanket / sheet columns), wooden rail and legs."""
    rgb, alpha, height = _blank(ctx)
    band = ctx.rect(0, TOP_ROW, ctx.w, RAIL[0]) > 0
    bl, _ = fabric(ctx, blanket_p, f"{salt}b", quilt=False)
    sh, _ = fabric(ctx, SHEET, f"{salt}s", quilt=False)
    sheet_m = band & sheet_cols
    rgb = np.where(band[..., None], bl, rgb)
    rgb = np.where(sheet_m[..., None], sh, rgb)
    top = ctx.rect(0, TOP_ROW, ctx.w, TOP_ROW + 1) > 0
    rgb = np.where((top & ~sheet_m)[..., None], blanket_p[-1], rgb)
    rgb = np.where((top & sheet_m)[..., None], SHEET[-1], rgb)
    if hem:
        hm = (ctx.rect(0, RAIL[0] - 1, ctx.w, RAIL[0]) > 0) & ~sheet_m
        rgb = np.where(hm[..., None], blanket_p[1], rgb)
    alpha = np.where(band, 1.0, alpha)
    height = np.where(band, 0.6, height)
    # Rail
    rail = ctx.rect(0, RAIL[0], ctx.w, RAIL[1]) > 0
    wc, g = wood(ctx, salt)
    rgb = np.where(rail[..., None], wc, rgb)
    rgb = np.where((rail & (ctx.rect(0, RAIL[0], ctx.w, RAIL[0] + 1) > 0))[..., None], WOOD[-1], rgb)
    rgb = np.where((rail & (ctx.rect(0, RAIL[1] - 1, ctx.w, RAIL[1]) > 0))[..., None], WOOD[1], rgb)
    alpha = np.where(rail, 1.0, alpha)
    height = np.where(rail, 0.55 + g * 0.05, height)
    # Legs
    for x0 in leg_cols:
        leg = ctx.rect(x0, LEG[0], x0 + 3, LEG[1]) > 0
        lt = ctx.rect(x0, LEG[0], x0 + 1, LEG[1]) > 0
        rt = ctx.rect(x0 + 2, LEG[0], x0 + 3, LEG[1]) > 0
        rgb = np.where(leg[..., None], WOOD[2], rgb)
        rgb = np.where((leg & lt)[..., None], WOOD[3], rgb)
        rgb = np.where((leg & rt)[..., None], WOOD[1], rgb)
        bottom = leg & (ctx.rect(0, LEG[1] - 1, ctx.w, LEG[1]) > 0)
        rgb = np.where(bottom[..., None], WOOD[0], rgb)
        alpha = np.where(leg, 1.0, alpha)
        height = np.where(leg, 0.5, height)
    return Tex(ctx, np.clip(rgb, 0, 1), alpha=alpha, height=height, smooth=0.08, porosity=0.5,
               sss=np.where(band, 0.1, 0.0), wrap=False, grain=0.06)


def bed_side(ctx, dye, part, face):
    p = ramp(wool_color(DYE[dye]), 6, dark=0.66, light=1.15)
    if part == "head":
        # u axis runs south->north on east faces, north->south on west faces
        z = (ctx.w - ctx.x) if face == "east" else ctx.x
        sheet_cols = z < FOLD_Z
        leg = [ctx.w - 3] if face == "east" else [0]
    else:
        sheet_cols = np.zeros((ctx.H, ctx.W), bool)
        leg = [0] if face == "east" else [ctx.w - 3]
    return side(ctx, p, sheet_cols, leg, salt=f"{dye}{part}")


def bed_foot_south(ctx, dye):
    p = ramp(wool_color(DYE[dye]), 6, dark=0.66, light=1.15)
    return side(ctx, p, np.zeros((ctx.H, ctx.W), bool), [0, ctx.w - 3], salt=f"{dye}south")


def bed_head_north(ctx):
    return side(ctx, SHEET, np.ones((ctx.H, ctx.W), bool), [0, ctx.w - 3], hem=False, salt="north")


def bed_top(ctx, dye, part):
    p = ramp(wool_color(DYE[dye]), 6, dark=0.66, light=1.15)
    rgb, v = fabric(ctx, p, f"{dye}top")
    height = 0.55 + v * 0.1
    sss = ctx.full(0.1)
    # Blanket hangs over the sides: outermost columns a shade darker.
    sides = (ctx.rect(0, 0, 1, ctx.h) + ctx.rect(ctx.w - 1, 0, ctx.w, ctx.h)) > 0
    if part == "foot":
        hem = ctx.rect(0, ctx.h - 1, ctx.w, ctx.h) > 0
        rgb = np.where(sides[..., None], rgb * 0.88, rgb)
        rgb = np.where(hem[..., None], p[1], rgb)
        height = np.where(hem, 0.5, height)
    else:
        sh, _ = fabric(ctx, SHEET, "headsheet", quilt=False)
        sheet = ctx.rect(0, 0, ctx.w, FOLD_Z) > 0
        rgb = np.where(sheet[..., None], sh, rgb)
        rgb = np.where((sides & ~sheet)[..., None], rgb * 0.88, rgb)
        # Folded-back sheet over the blanket edge
        fold = ctx.rect(0, FOLD_Z - 2, ctx.w, FOLD_Z) > 0
        rgb = np.where(fold[..., None], SHEET[3], rgb)
        rgb = np.where((ctx.rect(0, FOLD_Z - 2, ctx.w, FOLD_Z - 1) > 0)[..., None], SHEET[-1], rgb)
        rgb = np.where((ctx.rect(0, FOLD_Z, ctx.w, FOLD_Z + 1) > 0)[..., None], p[1], rgb)
        height = np.where(fold, 0.7, np.where(sheet, 0.55, height))
        # Pillow: soft rounded cushion
        pm = ctx.rect(2, 1, ctx.w - 2, 6)
        pm = np.maximum(pm, ctx.rect(3, 0.5, ctx.w - 3, 6.5)) if not ctx.pixel_art else pm
        pm = ctx.organic(pm, 0.1, "pillow")
        d = ctx.distance(pm.astype(np.float32), 3)
        gy, gx = np.gradient(d)
        lit = np.clip((gx + gy) * ctx.s, -1, 1)
        pv = 0.55 + np.clip(d / 2, 0, 1) * 0.25 + lit * 0.25 + (ctx.texel_noise("pil") - 0.5) * 0.08
        pc = ctx.palette(SHEET[1:], np.clip(pv, 0, 1))
        ring = (ctx.edge(pm.astype(np.float32), 1) > 0) & pm
        pc = np.where(ring[..., None], SHEET[1], pc)
        rgb = np.where(pm[..., None], pc, rgb)
        shadow = (np.roll(np.roll(pm, ctx.s, 0), ctx.s, 1)) & ~pm
        rgb = np.where(shadow[..., None], rgb * 0.82, rgb)
        height = np.where(pm, 0.65 + np.clip(d / 2, 0, 1) * 0.3, height)
    return Tex(ctx, np.clip(rgb, 0, 1), height=height, smooth=0.06, porosity=0.6, sss=sss, grain=0.08)


def bed_down(ctx):
    rgb, g = wood(ctx, "down")
    height = 0.5 + g * 0.08
    seams = np.zeros((ctx.H, ctx.W), bool)
    for y in (4, 8, 12):
        seams |= ctx.rect(1, y - 1, ctx.w - 1, y) > 0
    rgb = np.where(seams[..., None], WOOD[0], rgb)
    frame_l = (ctx.rect(0, 0, ctx.w, 1) + ctx.rect(0, 0, 1, ctx.h)) > 0
    frame_d = (ctx.rect(0, ctx.h - 1, ctx.w, ctx.h) + ctx.rect(ctx.w - 1, 0, ctx.w, ctx.h)) > 0
    rgb = np.where(frame_d[..., None], WOOD[1], rgb)
    rgb = np.where(frame_l[..., None], WOOD[4], rgb)
    for x0, y0 in ((0, 0), (ctx.w - 3, 0), (0, ctx.h - 3), (ctx.w - 3, ctx.h - 3)):
        leg = ctx.rect(x0, y0, x0 + 3, y0 + 3) > 0
        core = ctx.rect(x0 + 1, y0 + 1, x0 + 2, y0 + 2) > 0
        rgb = np.where(leg[..., None], WOOD[2], rgb)
        rgb = np.where(core[..., None], WOOD[1], rgb)
        height = np.where(leg, 0.6, height)
    height = np.where(seams, 0.3, height)
    return Tex(ctx, np.clip(rgb, 0, 1), height=height, smooth=0.22, porosity=0.25)


register("block/bed_down", bed_down)
register("block/bed_head_north", bed_head_north)
for _d in DYE_NAMES:
    for _face in ("east", "west"):
        register(f"block/{_d}_bed_head_{_face}", lambda ctx, d=_d, f=_face: bed_side(ctx, d, "head", f))
        register(f"block/{_d}_bed_foot_{_face}", lambda ctx, d=_d, f=_face: bed_side(ctx, d, "foot", f))
    register(f"block/{_d}_bed_foot_south", lambda ctx, d=_d: bed_foot_south(ctx, d))
    register(f"block/{_d}_bed_head_up", lambda ctx, d=_d: bed_top(ctx, d, "head"))
    register(f"block/{_d}_bed_foot_up", lambda ctx, d=_d: bed_top(ctx, d, "foot"))
