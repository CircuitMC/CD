"""Pre-1.13 horse family sheets (128x128 image, model UVs in texels of 128).

Old horse model boxes (u, v, w, h, d):
  head 5x5x7 (0,0); upper mouth 4x3x6 (24,18); lower mouth 4x2x5 (24,27);
  horse ears 2x3x1 (0,0); donkey/mule ears 2x7x1 (0,12); neck 4x14x8 (0,12);
  mane 2x16x4 (58,0); body 10x10x24 (0,34); tail base 2x2x3 (44,0), tail middle
  3x4x7 (38,7), tail tip 3x4x7 (24,3); back legs 4x9x5 (78,29)/(96,29), shins
  3x5x3 (78,43)/(96,43), hooves 4x3x4 (78,51)/(96,51); front legs 3x8x4
  (44,29)/(60,29), shins 3x5x3 (44,41)/(60,41), hooves 4x3x4 (44,51)/(60,51);
  chests 8x8x3 (0,34)/(0,47); saddle 10x1x8 (80,0), front 3x1x2 (106,9),
  back 8x1x2 (80,9), stirrup metal 1x2x2 (74,0)/(74,4), stirrup ropes 1x6x1
  (70,0)/(80,0), bit 1x2x2 (74,13), reins 0x3x16 (44,10)/(44,5).
Every part is filled from the matching 26.3 box (64x64 sheet), resampled.
"""
import numpy as np

from ..entity.mobs_layouts import LAYOUTS
from ..entity.objects_common import Sheet
from ..entity.objects_equipment import IRON_P, _strap
from .kit import blank, faces, reg, remap_box, render

ANIMALS = ["horse_black", "horse_brown", "horse_chestnut", "horse_creamy", "horse_darkbrown", "horse_gray",
           "horse_white", "horse_skeleton", "horse_zombie", "donkey", "mule"]
MARKINGS = ["horse_markings_blackdots", "horse_markings_white", "horse_markings_whitedots",
            "horse_markings_whitefield"]
ARMOR = {"diamond": "diamond", "gold": "gold", "iron": "iron"}


def _boxes(model):
    return {b[0]: b[1:6] for b in reversed(LAYOUTS[model][1])}


def body_parts(out, src, model, ears=True):
    b = _boxes(model)
    remap_box(out, src, b["body"], (0, 34, 10, 10, 24))
    remap_box(out, src, b["neck"], (0, 12, 4, 14, 8))
    remap_box(out, src, b["head"], (0, 0, 5, 5, 7))
    remap_box(out, src, b["mouth"], (24, 18, 4, 3, 6), rows=(0, 0.6))
    remap_box(out, src, b["mouth"], (24, 27, 4, 2, 5), rows=(0.6, 1))
    remap_box(out, src, b["mane"], (58, 0, 2, 16, 4))
    tail = b["tail"]
    remap_box(out, src, tail, (44, 0, 2, 2, 3), rows=(0, 0.2))
    remap_box(out, src, tail, (38, 7, 3, 4, 7), rows=(0.2, 0.6))
    remap_box(out, src, tail, (24, 3, 3, 4, 7), rows=(0.6, 1))
    leg = b["front_left_leg"]
    for u in (78, 96):
        remap_box(out, src, leg, (u, 29, 4, 9, 5), rows=(0, 0.6))
        remap_box(out, src, leg, (u, 43, 3, 5, 3), rows=(0.45, 0.8))
        remap_box(out, src, leg, (u, 51, 4, 3, 4), rows=(0.72, 1))
    for u in (44, 60):
        remap_box(out, src, leg, (u, 29, 3, 8, 4), rows=(0, 0.6))
        remap_box(out, src, leg, (u, 41, 3, 5, 3), rows=(0.45, 0.8))
        remap_box(out, src, leg, (u, 51, 4, 3, 4), rows=(0.72, 1))
    if ears:
        e = b["left_ear"]
        if e[3] >= 5:      # long donkey / mule ears
            remap_box(out, src, e, (0, 12, 2, 7, 1))
        else:
            remap_box(out, src, e, (0, 0, 2, 3, 1))
    if "left_chest" in b:
        remap_box(out, src, b["left_chest"], (0, 34, 8, 8, 3))
        remap_box(out, src, b["left_chest"], (0, 47, 8, 8, 3))


def saddle_parts(out):
    """Leather saddle, stirrups and reins on the old sheet's accessory boxes."""
    ctx = out.ctx
    sh = Sheet(ctx)
    m = np.zeros((ctx.H, ctx.W), bool)
    for box in ((80, 0, 10, 1, 8), (106, 9, 3, 1, 2), (80, 9, 8, 1, 2), (70, 0, 1, 6, 1), (80, 0, 1, 6, 1)):
        for r in faces(*box).values():
            m |= sh.rect(r)
    _strap(sh, m, "oldsaddle")
    reins = sh.rect((44, 26, 76, 29)) | sh.rect((44, 21, 76, 24))
    _strap(sh, reins, "oldrein", height=0.55)
    metal = np.zeros((ctx.H, ctx.W), bool)
    for box in ((74, 0, 1, 2, 2), (74, 4, 1, 2, 2), (74, 13, 1, 2, 2)):
        for r in faces(*box).values():
            metal |= sh.rect(r)
    sh.put(metal, ctx.palette(IRON_P[1:], ctx.texel_noise("oldbit")), height=0.7, smooth=0.6, metal=230)
    t = sh.tex(grain=0.04)
    out.paste(t)


def horse_old(ctx, name):
    model = "donkey" if name == "donkey" else "mule" if name == "mule" else \
        "skeleton_horse" if name == "horse_skeleton" else "zombie_horse" if name == "horse_zombie" else "horse"
    src = render(f"entity/horse/{name}", ctx.s, 64, 64)
    out = blank(ctx)
    body_parts(out, src, model)
    saddle_parts(out)
    out.normal_strength, out.grain = src.normal_strength, src.grain
    return out


def overlay_old(ctx, key, ears=True):
    src = render(key, ctx.s, 64, 64)
    out = blank(ctx)
    body_parts(out, src, "horse", ears=ears)
    out.normal_strength, out.grain = src.normal_strength, src.grain
    return out


for _n in ANIMALS:
    reg(f"entity/horse/{_n}@128x128", lambda ctx, n=_n: horse_old(ctx, n), size=(128, 128))
for _n in MARKINGS:
    reg(f"entity/horse/{_n}@128x128", lambda ctx, n=_n: overlay_old(ctx, f"entity/horse/{n}"), size=(128, 128))
for _o, _n in ARMOR.items():
    reg(f"entity/horse/armor/horse_armor_{_o}@128x128",
        lambda ctx, n=_n: overlay_old(ctx, f"entity/equipment/horse_body/{n}", ears=False), size=(128, 128))
