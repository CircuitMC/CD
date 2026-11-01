"""Armor items (a-g): chainmail / copper / diamond / golden armor pieces, horse
armor, nautilus armor, elytra."""
import numpy as np

from ...engine import COPPER as COPPER_ID, GOLD as GOLD_ID, IRON as IRON_ID, pal
from ...registry import register
from ...sprites import compose
from .common import CHAIN, COPPER, DIAMOND, GOLD
from . import h_armor as H
from .a_lib import (U, arc_pts, box, circ, darker, ell, line, metal, minus, paint, poly, spr, stroke)

MATS = {
    "chainmail": dict(p=CHAIN, metal=IRON_ID, smooth=0.55),
    "copper": dict(p=COPPER, metal=COPPER_ID, smooth=0.6),
    "diamond": dict(p=DIAMOND, metal=None, smooth=0.9, f0=0.17),
    "golden": dict(p=GOLD, metal=GOLD_ID, smooth=0.75),
}


def chain_pattern(ctx, t, p):
    """Punch a mail-ring pattern into the interior of an armor sprite."""
    mask = (t.alpha > 0.5).astype(np.float32)
    inner = (ctx.distance(mask, 2) > 1.0) & (mask > 0.5)
    if ctx.pixel_art:
        holes = inner & ((ctx.tx + ctx.ty) % 2 == 0)
    else:
        d = np.hypot(ctx.x % 1 - 0.5, ctx.y % 1 - 0.5)
        holes = inner & (d < 0.22)
    t.color[holes] = t.color[holes] * 0.55 + p[0] * 0.3
    t.height[holes] -= 0.15
    return t


def piece(ctx, kind, mat):
    """Same silhouettes as the h-z armor sets (shared shape maps in h_armor)."""
    m = MATS[mat]
    t = H.armor_piece(ctx, kind, m["p"], m["metal"], smooth=m["smooth"])
    if m.get("f0"):
        t.f0 = np.where(t.alpha > 0.5, m["f0"], t.f0)
    if mat == "chainmail":
        chain_pattern(ctx, t, m["p"])
    return t


for _mat in MATS:
    for _kind in ("helmet", "chestplate", "leggings", "boots"):
        register(f"item/{_mat}_{_kind}", lambda ctx, k=_kind, m=_mat: piece(ctx, k, m))


def horse(ctx, mat):
    m = MATS[mat]
    t = H.horse_armor(ctx, m["p"], m["metal"], smooth=m["smooth"])
    if m.get("f0"):
        t.f0 = np.where(t.alpha > 0.5, m["f0"], t.f0)
    return t


def nautilus(ctx, mat):
    m = MATS[mat]
    accent = {"copper": pal("3f9a7c")[0], "diamond": pal("f4fffe")[0], "golden": pal("d84a2a")[0]}[mat]
    t = H.nautilus_armor(ctx, m["p"], m["metal"], smooth=m["smooth"], accent=accent)
    if m.get("f0"):
        t.f0 = np.where(t.alpha > 0.5, m["f0"], t.f0)
    return t


for _mat in ("copper", "diamond", "golden"):
    register(f"item/{_mat}_horse_armor", lambda ctx, m=_mat: horse(ctx, m))
    register(f"item/{_mat}_nautilus_armor", lambda ctx, m=_mat: nautilus(ctx, m))


# ------------------------------------------------------------------ elytra

MEMBRANE = pal("2e2838", "4c4460", "6e6488", "9488ac", "b8aecc")
BROKEN = pal("2a2730", "45404f", "5f5a6b", "7c7688", "9893a4")


def elytra(ctx, broken=False):
    p = BROKEN if broken else MEMBRANE
    wing = [(7.6, 1.0), (3.6, 1.2), (1.2, 3.4), (0.8, 8.0), (1.8, 12.6), (3.4, 15.4), (5.0, 14.0), (6.0, 9.6), (7.6, 5.0)]
    left = poly(ctx, wing)
    right = poly(ctx, [(16 - x, y) for x, y in wing])
    m = U(left, right)
    if broken:
        holes = U(circ(ctx, 3.6, 8.0, 1.0), circ(ctx, 11.6, 11.0, 1.2), poly(ctx, [(1, 12), (3.4, 13), (1, 15)]),
                  poly(ctx, [(15.2, 6), (13.6, 7.2), (15.2, 8.6)]))
        m = minus(m, holes)
    t = spr(ctx, m, p, smooth=0.3, sss=0.15)
    ring = ctx.edge(m, 1) > 0
    for x0, y0, x1, y1 in ((6.6, 2.4, 2.6, 6.4), (6.2, 5.4, 2.4, 10.6), (5.6, 8.6, 3.0, 13.6)):
        paint(t, line(ctx, [(x0, y0), (x1, y1)], 0.7) * (~ring), p[1])
        paint(t, line(ctx, [(16 - x0, y0), (16 - x1, y1)], 0.7) * (~ring), p[1])
    paint(t, line(ctx, [(5.0, 2.6), (2.8, 4.6)], 0.7) * (~ring), p[4])
    paint(t, line(ctx, [(11.0, 2.6), (13.2, 4.6)], 0.7) * (~ring), p[3])
    return t


register("item/elytra", lambda ctx: elytra(ctx))
register("item/elytra_broken", lambda ctx: elytra(ctx, True))
