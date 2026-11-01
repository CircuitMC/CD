"""Tools per material (h-z): wooden, stone, iron, netherite axe/hoe/pickaxe/shovel/sword/spear.

Geometry follows the same diagonal design frame as the item_1 tool sets so all
materials share one silhouette per tool kind.
"""
import numpy as np

from ...registry import register
from .common import IRON as IRON_P, WOOD
from .h_lib import IRON, NETH, Diag, compose, line_paint, pal, rod, spr, U

PLANK = pal("4a3418", "6e5130", "8f6d41", "a98656", "c3a06b")
NETH_P = pal("161214", "2a2326", "3f3639", "564b4f", "73676b")
STONE_P = pal("333335", "555558", "717174", "8d8d90", "aaaaad")
NETH_HANDLE = pal("1c1416", "2e2224", "45353a", "5c4a4f", "75626a")

MATS = {
    "wooden": dict(p=PLANK, metal=None, smooth=0.25, grain=0.85, porosity=0.3),
    "stone": dict(p=STONE_P, metal=None, smooth=0.2, grain=0.8, porosity=0.1),
    "iron": dict(p=IRON_P, metal=IRON, smooth=0.7),
    "netherite": dict(p=NETH_P, metal=NETH, smooth=0.62),
}

D = Diag(1.5, 14.5)


def head_layer(ctx, mask, mat, **kw):
    m = MATS[mat]
    kw.setdefault("bevel", 2.0)
    t = spr(ctx, mask, m["p"], smooth=m["smooth"], porosity=m.get("porosity", 0.0), **kw)
    if m["metal"]:
        t.set_metal(mask, m["metal"])
    if m.get("grain"):  # speckled stone / grainy wood
        inner = (mask > 0.5) & ~(ctx.edge(mask, 1) > 0)
        n = ctx.texel_noise(f"grain{mat}")
        t.color[inner & (n < 0.18)] *= m["grain"]
        t.color[inner & (n > 0.88)] = np.clip(t.color[inner & (n > 0.88)] * 1.1, 0, 1)
    return t


def handle(ctx, mat, u0, u1, w=1.5, d=D):
    p = NETH_HANDLE if mat == "netherite" else WOOD
    return rod(ctx, [d.p(u0, 0), d.p(u1, 0)], w, p, porosity=0.2)


def sword(ctx, mat):
    p = MATS[mat]["p"]
    d = Diag(4.6, 11.4)
    blade = d.poly(ctx, [(0.3, -1.45), (9.4, -1.45), (11.6, 0), (9.4, 1.45), (0.3, 1.45)])
    guard = d.rect(ctx, -0.9, -3.3, 0.6, 3.3)
    tb = head_layer(ctx, blade, mat)
    line_paint(ctx, tb, [d.p(1.5, -0.35), d.p(9.3, -0.35)], p[4], 0.7)
    tg = head_layer(ctx, guard, mat, bevel=1) if mat != "wooden" else spr(ctx, guard, WOOD, bevel=1)
    grip = handle(ctx, mat, -4.6, -0.6, 1.6, d)
    pommel = head_layer(ctx, d.rect(ctx, -5.8, -1.0, -4.3, 1.0), mat, bevel=1)
    return compose(ctx, grip, tb, tg, pommel)


def pickaxe(ctx, mat):
    p = MATS[mat]["p"]
    head = U(D.curve(ctx, (9.6, -6.6), (15.6, 0), (9.6, 6.6), 1.5, 1.5),
             D.curve(ctx, (11.2, -4.0), (14.2, 0), (11.2, 4.0), 2.6, 2.6))
    t = head_layer(ctx, head, mat)
    line_paint(ctx, t, [D.p(10.4, -5.0), D.p(12.6, -2.2)], p[4], 0.7)
    return compose(ctx, handle(ctx, mat, 0, 12.0), t)


def axe(ctx, mat):
    p = MATS[mat]["p"]
    head = D.poly(ctx, [(9.0, 0.9), (13.3, 0.9), (13.9, -1.4), (15.0, -3.6), (14.2, -5.6), (11.6, -5.0),
                        (9.0, -5.6), (8.0, -3.6), (9.2, -1.4)])
    t = head_layer(ctx, head, mat)
    line_paint(ctx, t, [D.p(9.2, -4.4), D.p(11.4, -3.9)], p[4], 0.7)
    return compose(ctx, handle(ctx, mat, 0, 13.0), t)


def shovel(ctx, mat):
    p = MATS[mat]["p"]
    head = D.poly(ctx, [(10.0, -1.0), (10.6, -2.5), (13.6, -2.6), (15.6, -1.4), (16.6, 0), (15.6, 1.4),
                        (13.6, 2.6), (10.6, 2.5), (10.0, 1.0)])
    t = head_layer(ctx, head, mat)
    line_paint(ctx, t, [D.p(11.2, -1.4), D.p(14.6, -1.2)], p[4], 0.7)
    neck = head_layer(ctx, D.rect(ctx, 8.6, -0.9, 10.4, 0.9), mat, bevel=1)
    return compose(ctx, handle(ctx, mat, 0, 9.4), neck, t)


def hoe(ctx, mat):
    p = MATS[mat]["p"]
    head = D.poly(ctx, [(11.0, 1.0), (13.4, 1.0), (13.4, -4.4), (12.6, -5.6), (8.6, -5.6), (8.6, -3.8),
                        (11.0, -3.8)])
    t = head_layer(ctx, head, mat)
    line_paint(ctx, t, [D.p(12.2, 0.0), D.p(12.2, -3.8)], p[4], 0.7)
    return compose(ctx, handle(ctx, mat, 0, 12.4), t)


def spear(ctx, mat):
    p = MATS[mat]["p"]
    d = Diag(1.0, 15.0)
    shaft = handle(ctx, mat, 0.2, 13.5, 1.4, d)
    headm = d.poly(ctx, [(12.6, 0), (14.0, -1.7), (17.2, -1.2), (20.4, 0), (17.2, 1.2), (14.0, 1.7)])
    t = head_layer(ctx, headm, mat)
    line_paint(ctx, t, [d.p(14.0, -0.6), d.p(18.4, -0.3)], p[4], 0.6)
    collar = head_layer(ctx, d.rect(ctx, 11.0, -1.0, 12.8, 1.0), mat, bevel=1)
    wrap = spr(ctx, d.rect(ctx, 4.0, -0.95, 6.4, 0.95), pal("3a2416", "5c3a22", "7c5232", "966a44"), bevel=1)
    return compose(ctx, shaft, wrap, collar, t)


KINDS = dict(sword=sword, pickaxe=pickaxe, axe=axe, shovel=shovel, hoe=hoe, spear=spear)

for _mat in MATS:
    for _kind, _fn in KINDS.items():
        register(f"item/{_mat}_{_kind}", lambda ctx, fn=_fn, m=_mat: fn(ctx, m))
    register(f"item/{_mat}_spear_in_hand", lambda ctx, m=_mat: spear(ctx, m))
