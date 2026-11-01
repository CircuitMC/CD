"""Mob skins in pre-26.x / pre-1.21.5 layouts.

* cow / mooshroom / pig / pig saddle (64x32): the 26.3 sheets keep the classic
  UVs in their upper half, so the old sheet is the top 32 rows.
* ghast (64x32): the 26.3 generator rendered on a 64x32 canvas (same model).
* rabbits (64x32, 1.8-1.21.8): the 26.3 rabbit painter run on the old model
  boxes: body 6x5x10 uv(0,0), head 5x4x5 uv(32,0), nose 1x1x1 uv(32,9), ears
  2x5x1 uv(52,0)/(58,0), tail 3x3x2 uv(52,6), front legs 2x7x2 uv(0,15)/(8,15),
  thighs 2x4x5 uv(16,15)/(30,15), feet 2x1x7 uv(8,24)/(26,24).
* magma cube (64x32, <= 1.21.3): segments 8x1x8 at uv(0,i) for i = 0,1,4..7,
  uv(24,10) for i = 2, uv(24,19) for i = 3; core 4x4x4 uv(0,16). Faces copied
  from the 26.3 segment boxes.
* bat (64x64, <= 1.20.2) and vex (64x64, 1.11-1.19): painted fresh on the old
  boxes with the 26.3 materials.
* villagers / zombie villagers before 1.14: the 1.14+ layers merged.
* pre-1.11 zombie villager and zombie pigman: biped layouts filled from the
  26.3 zombie villager / zombified piglin sheets.
"""
from contextlib import contextmanager

import numpy as np

from ...engine import Ctx
from ...registry import TEXTURES
from ..entity.mobs_base import Mat, Skin
from ..entity.mobs_layouts import LAYOUTS
from .kit import blank, blit, crop, faces, layered, put, reg, remap_box, render, top_part


@contextmanager
def layout(model, spec):
    """Run a 26.3 painter on another set of model boxes (restored afterwards)."""
    old = LAYOUTS.get(model)
    LAYOUTS[model] = spec
    try:
        yield
    finally:
        if old is None:
            LAYOUTS.pop(model, None)
        else:
            LAYOUTS[model] = old


def custom_skin(ctx, size, raw, salt=""):
    with layout("__legacy__", (size, raw)):
        return Skin(ctx, "__legacy__", salt=salt)


# ------------------------------------------------------------------ classic 64x32 farm sheets

for _old, _new in (("entity/cow/cow", "entity/cow/cow_temperate"),
                   ("entity/cow/mooshroom", "entity/cow/mooshroom_red"),
                   ("entity/cow/red_mooshroom@64x32", "entity/cow/mooshroom_red"),
                   ("entity/cow/brown_mooshroom@64x32", "entity/cow/mooshroom_brown"),
                   ("entity/pig/pig", "entity/pig/pig_temperate"),
                   ("entity/pig/pig_saddle", "entity/equipment/pig_saddle/saddle")):
    reg(_old, lambda ctx, k=_new: top_part(ctx, k), **({"size": (64, 32)} if "@" in _old else {}))


def ghast_old(ctx, key):
    t = render(key, ctx.s, 64, 32)
    out = blank(ctx)
    out.paste(t, np.ones((ctx.H, ctx.W), np.float32))
    out.normal_strength, out.grain = t.normal_strength, t.grain
    return out


reg("entity/ghast/ghast@64x32", lambda ctx: ghast_old(ctx, "entity/ghast/ghast"), size=(64, 32))
reg("entity/ghast/ghast_shooting@64x32", lambda ctx: ghast_old(ctx, "entity/ghast/ghast_shooting"), size=(64, 32))


# ------------------------------------------------------------------ rabbits

OLD_RABBIT = ((64, 32), [
    ("head", 32, 0, 5, 4, 5, 0),
    ("head", 32, 9, 1, 1, 1, 0),
    ("left_ear", 58, 0, 2, 5, 1, 0),
    ("right_ear", 52, 0, 2, 5, 1, 0),
    ("body", 0, 0, 6, 5, 10, -20),
    ("body/left_front_leg", 8, 15, 2, 7, 2, 0),
    ("body/right_front_leg", 0, 15, 2, 7, 2, 0),
    ("left_haunch", 30, 15, 2, 4, 5, 0),
    ("right_haunch", 16, 15, 2, 4, 5, 0),
    ("left_foot", 26, 24, 2, 1, 7, 0),
    ("right_foot", 8, 24, 2, 1, 7, 0),
    ("tail", 52, 6, 3, 3, 2, 0),
])
RABBIT_KEYS = ["black", "brown", "caerbannog", "gold", "salt", "toast", "white", "white_splotched"]


def rabbit_old(ctx, k):
    key = f"entity/rabbit/rabbit_{k}"
    with layout("rabbit", OLD_RABBIT):
        t = TEXTURES[key].fn(Ctx(key, 64, 32, ctx.s))
    out = blank(ctx)
    out.paste(t, np.ones((ctx.H, ctx.W), np.float32))
    # pink nose tip on the little nose box
    nose = faces(32, 9, 1, 1, 1)["front"]
    s = ctx.s
    out.color[nose[1] * s:nose[3] * s, nose[0] * s:nose[2] * s] = (0.82, 0.5, 0.52)
    out.normal_strength, out.grain = t.normal_strength, t.grain
    return out


for _k in RABBIT_KEYS:
    reg(f"entity/rabbit/{_k}", lambda ctx, k=_k: rabbit_old(ctx, k))


# ------------------------------------------------------------------ magma cube

OLD_SEGMENTS = [(0, 0), (0, 1), (24, 10), (24, 19), (0, 4), (0, 5), (0, 6), (0, 7)]


def magmacube_old(ctx):
    src = render("entity/slime/magmacube", ctx.s, 64, 64)
    (_, _), raw = LAYOUTS["magma_cube"]
    segs = sorted([b for b in raw if b[0].startswith("segment")], key=lambda b: int(b[0][7:]))
    core = [b for b in raw if b[0] == "core"][0]
    out = blank(ctx)
    # caps first (they overlap on the old sheet; the top segment's cap wins), then the side rings
    for i in reversed(range(8)):
        sb = segs[i][1:6]
        u, v = OLD_SEGMENTS[i]
        sf, df = faces(*sb), faces(u, v, 8, 1, 8)
        for n in ("top", "bottom"):
            blit(out, src, sf[n], df[n])
    for i in range(8):
        sb = segs[i][1:6]
        u, v = OLD_SEGMENTS[i]
        sf, df = faces(*sb), faces(u, v, 8, 1, 8)
        for n in ("right", "front", "left", "back"):
            blit(out, src, sf[n], df[n])
    remap_box(out, src, core[1:6], (0, 16, 4, 4, 4))
    out.normal_strength, out.grain = src.normal_strength, src.grain
    return out


reg("entity/slime/magmacube@64x32", magmacube_old, size=(64, 32))


# ------------------------------------------------------------------ bat (<= 1.20.2)

OLD_BAT = [
    ("head", 0, 0, 6, 6, 6, 0),
    ("ear", 24, 0, 3, 4, 1, 0),
    ("body", 0, 16, 6, 12, 6, 0),
    ("body", 0, 34, 10, 6, 1, 0),
    ("right_wing", 42, 0, 10, 16, 1, 0),
    ("outer_right_wing", 24, 16, 8, 12, 1, 0),
]


def bat_old(ctx):
    sk = custom_skin(ctx, (64, 64), OLD_BAT, salt="oldbat")
    fur = Mat("4a3a30", mottle=0.3, grain=0.25, sss=0.3, streak=0.4)
    wing = Mat("2e2624", mottle=0.2, grain=0.2, sss=0.5, smooth=0.3)
    sk.paint_all([("right_wing", wing), ("outer", wing), ("ear", wing.but(base=0.6)),
                  ("body#1", fur.but(base=0.45))], fur)
    head = sk.box("head")
    sk.sym(head, "front", 1, 2, 2, 3, "e8a030", height=0.45, emissive=0.2)
    sk.frect(head, "front", 2, 4, 4, 5, "1a1210", height=0.35)
    sk.sym(head, "front", 2, 5, 3, 6, "d8d0c0", height=0.5)   # little fangs
    ear = sk.box("ear")
    sk.frect(ear, "front", 1, 1, 2, 0, "6a4a44", height=0.4)
    for w in sk.find("outer") + sk.find("right_wing"):   # finger bones
        for f in ("front", "back"):
            if f in w.faces:
                ww = (w.faces[f][2] - w.faces[f][0]) / sk.k
                for x in range(1, int(ww), 3):
                    sk.frect(w, f, x, 0, x + 1, -2, "4a3e3a", height=0.6)
    return sk.tex()


reg("entity/bat@64x64", bat_old, size=(64, 64))


# ------------------------------------------------------------------ vex (1.11-1.19)

OLD_VEX = [
    ("head", 0, 0, 8, 8, 8, 0),
    ("body", 16, 16, 8, 12, 4, 0),
    ("right_arm", 40, 16, 4, 12, 4, 0),
    ("leg", 32, 0, 6, 10, 4, 0),
    ("right_wing", 0, 32, 20, 12, 1, 0),
]


def vex_old(ctx, charging):
    sk = custom_skin(ctx, (64, 64), OLD_VEX, salt="oldvex")
    main = Mat("a8b0c0", mottle=0.25, grain=0.2, sss=0.5, smooth=0.5)
    wing = Mat("e8ecf0", mottle=0.15, grain=0.2, sss=0.3, alpha=0.8, smooth=0.6)
    sk.paint_all([("right_wing", wing)], main)
    head = sk.box("head")
    sk.sym(head, "front", 1, 3, 3, 4, "1a1a1e" if not charging else "e83a3a", height=0.4,
           emissive=0.0 if not charging else 0.8)
    sk.frect(head, "front", 2, 5, 6, 6, "2a2a30" if not charging else "6a1a1a", height=0.35)
    sk.paint(head, Mat("e8e0c0", grain=0.15), faces=("top",))
    for f in ("right", "left", "back"):
        sk.frect(head, f, 0, 0, 0, 2, Mat("e8e0c0", grain=0.15))
    sk.frect(head, "front", 0, 0, 0, 1, Mat("e8e0c0", grain=0.15))
    body = sk.box("body")
    sk.band(body, -4, 0, main.but(base=0.42))   # wispy lower body
    w = sk.box("right_wing")
    for f, r in w.faces.items():
        sl = sk._sl(*r)
        if sl is not None:
            m = ((sk.ctx.ty[sl] - int(r[1] * sk.ctx.s)) // sk.ctx.s) % 2 == 0
            sk.color[sl][m] *= 0.92
    return sk.tex()


reg("entity/illager/vex@64x64", lambda ctx: vex_old(ctx, False), size=(64, 64))
reg("entity/illager/vex_charging@64x64", lambda ctx: vex_old(ctx, True), size=(64, 64))


# ------------------------------------------------------------------ villagers before 1.14

PROFESSIONS = {"butcher": "butcher", "farmer": "farmer", "librarian": "librarian", "priest": "cleric",
               "smith": "weaponsmith"}


def villager_old(ctx, prof, zombie=False):
    v = "zombie_villager" if zombie else "villager"
    keys = [f"entity/{v}/{v}", f"entity/{v}/type/plains"] + ([f"entity/{v}/profession/{prof}"] if prof else [])
    return layered(ctx, keys)


for _o, _n in PROFESSIONS.items():
    reg(f"entity/villager/{_o}", lambda ctx, n=_n: villager_old(ctx, n))
    reg(f"entity/zombie_villager/zombie_{_o}", lambda ctx, n=_n: villager_old(ctx, n, True))


def zombie_villager_pre111(ctx):
    """1.7-1.10 zombie villager: biped zombie sheet with the villager head at uv(0,32)."""
    src = layered(Ctx("entity/zombie_villager/zombie_villager", 64, 64, ctx.s),
                  ["entity/zombie_villager/zombie_villager", "entity/zombie_villager/type/plains"])
    out = blank(ctx)
    remap_box(out, src, (0, 0, 8, 10, 8), (0, 32, 8, 10, 8))     # villager head
    remap_box(out, src, (24, 0, 2, 4, 2), (24, 32, 2, 4, 2))     # nose
    remap_box(out, src, (0, 0, 8, 10, 8), (0, 0, 8, 8, 8))       # plain biped head (child model)
    remap_box(out, src, (16, 20, 8, 12, 6), (16, 16, 8, 12, 4))  # body
    remap_box(out, src, (44, 22, 4, 12, 4), (40, 16, 4, 12, 4))  # arms
    remap_box(out, src, (0, 22, 4, 12, 4), (0, 16, 4, 12, 4))    # legs
    out.normal_strength, out.grain = src.normal_strength, src.grain
    return out


reg("entity/zombie/zombie_villager", zombie_villager_pre111)


def zombie_pigman(ctx):
    """1.7-1.14 zombie pigman: biped zombie layout from the zombified piglin."""
    src = render("entity/piglin/zombified_piglin", ctx.s, 64, 64)
    out = blank(ctx)
    for r in ((16, 16, 40, 32), (40, 16, 56, 32), (0, 16, 16, 32), (32, 48, 48, 64), (16, 48, 32, 64)):
        blit(out, src, r)                                          # body, arms, legs share the biped UVs
    remap_box(out, src, (0, 0, 10, 8, 8), (0, 0, 8, 8, 8))       # wide piglin head squeezed to 8 wide
    hf = faces(0, 0, 8, 8, 8)["front"]
    snout = faces(31, 1, 4, 4, 1)["front"]
    put(out, crop(src, snout), (hf[0] + 2, hf[1] + 4, hf[0] + 6, hf[1] + 8))
    out.normal_strength, out.grain = src.normal_strength, src.grain
    return out


reg("entity/zombie_pigman", zombie_pigman)


# ------------------------------------------------------------------ misc old sheets

reg("entity/llama/llama", lambda ctx: _same(ctx, "entity/llama/llama_creamy"))
reg("entity/projectiles/wind_charge@64x64",
    lambda ctx: _same(ctx, "entity/projectiles/wind_charge"), size=(64, 64))


def _same(ctx, key):
    """Render another generator on this canvas size (same texel coordinates)."""
    t = TEXTURES[key].fn(Ctx(key, ctx.w, ctx.h, ctx.s))
    out = blank(ctx)
    out.paste(t, np.ones((ctx.H, ctx.W), np.float32))
    out.normal_strength, out.grain = t.normal_strength, t.grain
    return out
