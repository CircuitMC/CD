"""Buckets, potions (bottle + tinted overlay), honey and ominous bottles (h-z).

The bottle geometry matches the item_1 glass bottle (same body circle, neck, lip).
"""
import numpy as np

from ...registry import register
from .common import IRON as IRON_P, GRAY
from .h_lib import (IRON, U, arc_pts, box, cells, circ, compose, dots, ell, flat_layer, inter, line, metal, minus,
                    paint, pal, rgb, spr, stroke)

GLASS = pal("4a6a7a", "86a8b8", "b6d2de", "e4f4fa")
CORK = pal("4a2e18", "7a5030", "a07048", "c49468")


def _bottle_masks(ctx):
    body = circ(ctx, 8.0, 10.6, 4.6)
    neck = box(ctx, 6.6, 3.4, 9.4, 7.0)
    lip = box(ctx, 6.0, 2.0, 10.0, 3.6)
    return body, neck, lip


def liquid_mask(ctx):
    body, neck, lip = _bottle_masks(ctx)
    inner = (U(body, neck, lip) > 0.5) & ~(ctx.edge(U(body, neck, lip), 1) > 0)
    return inter(circ(ctx, 8.0, 10.6, 3.7), box(ctx, 0, 7.6, 16, 16)) * inner


def bottle(ctx, liquid=None, emissive=0.0, kind="plain", glass=GLASS, hollow=False):
    """kind: plain / splash / lingering. hollow=True leaves the liquid area clear (for overlays)."""
    body, neck, lip = _bottle_masks(ctx)
    if kind == "splash":  # short neck with a pinched collar and a side grip
        neck = box(ctx, 6.6, 4.4, 9.4, 7.0)
        lip = U(box(ctx, 5.6, 3.0, 10.4, 4.6), box(ctx, 6.6, 1.8, 9.4, 3.2))
    elif kind == "lingering":  # wide flared mouth
        neck = box(ctx, 6.4, 4.2, 9.6, 7.0)
        lip = U(box(ctx, 4.8, 2.2, 11.2, 4.2), box(ctx, 5.8, 1.4, 10.2, 2.4))
    m = U(body, neck, lip)
    ring = ctx.edge(m, 1) > 0
    t = spr(ctx, m, glass, bevel=1, smooth=0.95)
    alpha = np.maximum(ring.astype(np.float32), lip)
    lipm = (lip > 0.5) & ~ring
    paint(t, lipm, CORK[2] if kind == "plain" else glass[2])
    if kind == "plain":
        paint(t, lipm & (box(ctx, 0, 2.0, 16, 2.9) > 0.5), CORK[3])
    inner = (m > 0.5) & ~ring
    lm = liquid_mask(ctx) > 0.5
    if liquid is not None and not hollow:
        tl = spr(ctx, lm.astype(np.float32), liquid, outline=False, bevel=2, emissive=emissive, smooth=0.8)
        alpha = np.maximum(alpha, lm)
        t.color = np.where(lm[..., None], tl.color, t.color)
        t.emissive = np.where(lm, emissive, 0.0)
        paint(t, lm & (box(ctx, 0, 7.6, 16, 8.6) > 0.5), liquid[-1])
    gl = U(line(ctx, [(5.6, 9.6), (5.6, 11.6)], 0.8), dots(ctx, [(6, 8)], 0.45))
    glm = (gl > 0.5) & inner
    alpha = np.maximum(alpha, glm)
    paint(t, glm, glass[3])
    if kind == "lingering":
        sw = cells(ctx, [(9, 12), (10, 11), (6, 13)]) > 0.5
        alpha = np.maximum(alpha, sw & inner)
        paint(t, sw & inner, glass[2])
    t.alpha = alpha * (m > 0.5)
    if hollow:
        t.alpha[lm & ~glm & ~(sw & inner if kind == "lingering" else np.zeros_like(lm))] = 0
    return t


def potion_overlay(ctx):
    lm = liquid_mask(ctx)
    t = spr(ctx, lm, pal("5a5a5a", "8a8a8a", "b0b0b0", "d0d0d0", "ececec"), outline=False, bevel=2, smooth=0.8)
    paint(t, (lm > 0.5) & (box(ctx, 0, 7.6, 16, 8.6) > 0.5), rgb("f0f0f0"))
    paint(t, cells(ctx, [(9, 10), (7, 12)]), rgb("e0e0e0"))
    return t


register("item/potion", lambda ctx: bottle(ctx, hollow=True))
register("item/splash_potion", lambda ctx: bottle(ctx, kind="splash", hollow=True))
register("item/lingering_potion", lambda ctx: bottle(ctx, kind="lingering", hollow=True))
register("item/potion_overlay", potion_overlay)
HONEY = pal("8a4a06", "c47a10", "e8a420", "f8c840", "ffe68a")
register("item/honey_bottle", lambda ctx: bottle(ctx, HONEY))
OMINOUS_GLASS = pal("1e2a2e", "3a4e54", "5a7a80", "9ab8bc")
OMINOUS = pal("0a1a14", "14342a", "1e5040", "2e7058", "4a9a7a")


def ominous_bottle(ctx):
    t = bottle(ctx, OMINOUS, 0.25, glass=OMINOUS_GLASS)
    # pale skull mark on the liquid
    paint(t, cells(ctx, [(7, 10), (9, 10), (7, 9), (8, 9), (9, 9), (8, 11)]), rgb("c8d8c8"))
    paint(t, cells(ctx, [(8, 10)]), OMINOUS[0])
    return t


register("item/ominous_bottle", ominous_bottle)

# ------------------------------------------------------------------ buckets
PAIL = pal("3a3a40", "6e6e76", "9a9aa2", "c4c4cc", "e8e8ee")


def bucket(ctx, fill=None, emissive=0.0, extra=None):
    handle = stroke(ctx, arc_pts(8.0, 6.0, 5.6, 180, 360, 20), 1.0)
    hd = metal(ctx, minus(handle, box(ctx, 0, 5.2, 16, 16)), PAIL, IRON, outline=False, bevel=1)
    paint(hd, box(ctx, 0, 0, 16, 16), PAIL[1])
    paint(hd, box(ctx, 0, 0, 8, 3), PAIL[2])
    body = U(box(ctx, 2.4, 6.0, 13.6, 7.0), ctx.polygon([(x * ctx.w / 16, y * ctx.w / 16) for x, y in
                                                          [(2.4, 6.4), (13.6, 6.4), (12.2, 13.2), (3.8, 13.2)]]),
             ell(ctx, 8.0, 13.0, 4.2, 1.4), ell(ctx, 8.0, 6.2, 5.6, 1.8))
    t = metal(ctx, body, PAIL, IRON, bevel=2, smooth=0.65)
    ring = ctx.edge(body, 1) > 0
    inner = (body > 0.5) & ~ring
    # bands
    paint(t, (box(ctx, 0, 9.0, 16, 10.0) > 0.5) & inner, PAIL[1])
    paint(t, (box(ctx, 0, 8.0, 16, 9.0) > 0.5) & inner, PAIL[4])
    mouth = (ell(ctx, 8.0, 6.2, 4.6, 1.15) > 0.5) & inner
    if fill is None:
        paint(t, mouth, PAIL[0])
        paint(t, mouth & (box(ctx, 0, 6.2, 16, 8) > 0.5), PAIL[1])
    else:
        fp = fill
        paint(t, mouth, fp[2], metal=0, smooth=0.85, emissive=emissive)
        paint(t, mouth & (box(ctx, 0, 0, 7.5, 6.2) > 0.5), fp[3], metal=0, emissive=emissive)
        paint(t, mouth & (box(ctx, 9.5, 6.2, 16, 16) > 0.5), fp[1], metal=0, emissive=emissive)
    layers = [hd, t]
    if extra is not None:
        layers.append(extra(ctx))
    return compose(ctx, *layers)


WATER = pal("1a3a8a", "2a5ac4", "3a7ae0", "6aa4f4", "aad0ff")
LAVA = pal("8a1a04", "d44a0a", "f47a14", "fcb03a", "fff08a")
MILK = pal("b8bcc4", "dcdee4", "f2f2f4", "ffffff", "ffffff")
SNOW = pal("9ab4c8", "c8dcea", "e4f0f8", "f8fcff", "ffffff")


def fish_peek(p, pts, eye=None):
    def f(ctx):
        m = U(*[ell(ctx, cx, cy, rx, ry, r) for cx, cy, rx, ry, r in pts])
        t = spr(ctx, m, p, bevel=1.5, smooth=0.5)
        if eye:
            paint(t, cells(ctx, [eye]), rgb("101010"))
        return t
    return f


SALMON_P = pal("4a1410", "8a2a22", "b8443a", "e07a5a", "f4a888")
PUFF_P = pal("6a4a06", "b88a10", "e8c030", "f8e070", "fff4b0")
TROP_P = pal("8a2a06", "d0561a", "f08a2a", "f8b45a", "fff0d0")
TAD_P = pal("1a120a", "3a2a1a", "5a4430", "7a6048")
SULF_P = pal("6a5a06", "aa9a14", "d8c83a", "f0e46a", "fff8b0")


def tadpoles(ctx):
    m = U(ell(ctx, 6.0, 5.6, 1.0, 0.8), ell(ctx, 10.0, 6.4, 1.0, 0.8), line(ctx, [(6.8, 5.8), (8.2, 5.2)], 0.6),
          line(ctx, [(10.8, 6.4), (12.0, 7.0)], 0.6))
    return spr(ctx, m, TAD_P, outline=False, bevel=1)


def sulfur_cube(ctx):
    m = box(ctx, 5.6, 2.4, 10.4, 6.8)
    t = spr(ctx, m, SULF_P, bevel=1.5, smooth=0.4)
    paint(t, cells(ctx, [(7, 4), (9, 4)]), rgb("3a3006"))
    return t


def snow_speckle(ctx):
    m = cells(ctx, [(6, 5), (9, 6), (11, 5), (7, 7)])
    return flat_layer(ctx, m, SNOW[0])


register("item/water_bucket", lambda ctx: bucket(ctx, WATER))
register("item/lava_bucket", lambda ctx: bucket(ctx, LAVA, 0.9))
register("item/milk_bucket", lambda ctx: bucket(ctx, MILK))
register("item/powder_snow_bucket", lambda ctx: bucket(ctx, SNOW, extra=snow_speckle))
register("item/salmon_bucket", lambda ctx: bucket(ctx, WATER, extra=fish_peek(
    SALMON_P, [(8.6, 4.2, 3.4, 1.4, -0.3), (5.0, 6.0, 1.4, 1.0, 0.6)], (10, 3))))
register("item/pufferfish_bucket", lambda ctx: bucket(ctx, WATER, extra=fish_peek(
    PUFF_P, [(8.0, 4.4, 2.6, 2.2, 0.0)], (7, 3))))
register("item/tropical_fish_bucket", lambda ctx: bucket(ctx, WATER, extra=fish_peek(
    TROP_P, [(8.4, 4.4, 2.8, 1.6, 0.2), (5.2, 5.4, 1.2, 1.2, 0.0)], (10, 4))))
register("item/tadpole_bucket", lambda ctx: bucket(ctx, WATER, extra=tadpoles))
register("item/sulfur_cube_bucket", lambda ctx: bucket(ctx, WATER, extra=sulfur_cube))
