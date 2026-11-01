"""Clock (64 frames) and compass (32 frames).

Frame conventions (from how the item models pick frames):
  clock_NN:   NN/64 of a day after noon -> the sun sits at the top for clock_00 and
              the sky disc turns clockwise (sun sets to the right / west).
  compass_NN: the needle points (NN - 16)/32 of a turn clockwise from straight up;
              compass_16 = target straight ahead, compass_00 = behind.
"""
import math

import numpy as np

from ...engine import GOLD as GOLD_ID, IRON as IRON_ID, pal
from ...registry import register
from ...sprites import compose
from .common import GOLD, IRON
from .a_lib import U, box, circ, dots, ell, inter, line, minus, paint, poly, spr

SKY_DAY = pal("2e5ab4", "4a7ad4", "6a9ae8")
SKY_DUSK = pal("c4602a", "e8904a")
SKY_NIGHT = pal("0a1030", "141c48", "222c60")
SUN = pal("f0a010", "ffd84a", "fff4b0")
MOON = pal("8a92a4", "c8ccd8", "eef0f6")
GROUND = pal("2a3a14", "3e5a1c", "56782a")


def clock(ctx, i):
    k = ctx.w / 16
    case = circ(ctx, 8.0, 8.0, 7.0)
    t = spr(ctx, case, GOLD, bevel=1.5, smooth=0.75)
    t.set_metal(case, GOLD_ID)
    face = circ(ctx, 8.0, 8.0, 5.0)
    a = i / 64 * 2 * math.pi
    x, y = ctx.x / k - 8.0, ctx.y / k - 8.0
    # rotate pixel into dial space (dial turns clockwise by a)
    c, s = math.cos(-a), math.sin(-a)
    u, v = x * c - y * s, x * s + y * c
    day = v < 0
    col = np.where(day[..., None], SKY_DAY[1], SKY_NIGHT[1])
    col = np.where((day & (v > -0.8))[..., None], SKY_DAY[2], col)
    col = np.where((~day & (v < 0.8))[..., None], SKY_NIGHT[2], col)
    sun = np.hypot(u, v + 3.0) < 1.6
    moon = (np.hypot(u, v - 3.0) < 1.5) & ~(np.hypot(u + 0.7, v - 3.4) < 1.1)
    stars = ((np.abs(u - 2.4) < 0.5) & (np.abs(v - 1.6) < 0.5)) | ((np.abs(u + 2.6) < 0.5) & (np.abs(v - 2.0) < 0.5))
    col = np.where(sun[..., None], SUN[1], col)
    col = np.where(moon[..., None], MOON[2], col)
    col = np.where((stars & ~day & ~moon)[..., None], pal("e8ecff")[0], col)
    fm = face > 0.5
    t.color = np.where(fm[..., None], col, t.color)
    t.metal = np.where(fm, 0, t.metal)
    t.emissive = np.where(fm & (sun | moon), 0.4, 0.0)
    # static horizon: hills cover the lower part of the window
    hill = inter(face, U(box(ctx, 0, 9.4, 16, 16), ell(ctx, 6.0, 9.6, 3.0, 1.2), ell(ctx, 11.0, 9.8, 2.2, 0.9)))
    paint(t, hill, GROUND[1])
    paint(t, inter(hill, box(ctx, 0, 11.6, 16, 16)), GROUND[0])
    paint(t, inter(face, ctx.edge(face, 1, "tl")), GOLD[0])
    paint(t, dots(ctx, [(3, 4), (4, 3)], 0.45), GOLD[4])
    return t


def compass(ctx, i):
    k = ctx.w / 16
    case = circ(ctx, 8.0, 8.0, 7.0)
    t = spr(ctx, case, IRON, bevel=1.5, smooth=0.75)
    t.set_metal(case, IRON_ID)
    face = circ(ctx, 8.0, 8.0, 5.0)
    paint(t, face, pal("d8ccae")[0])
    t.metal = np.where(face > 0.5, 0, t.metal)
    paint(t, inter(face, ctx.edge(face, 1, "tl")), IRON[0])
    for ang in (0, 90, 180, 270):
        r = math.radians(ang)
        paint(t, dots(ctx, [(8 + math.sin(r) * 4.0 - 0.5, 8 - math.cos(r) * 4.0 - 0.5)], 0.45), pal("8a7a5a")[0])
    a = (i - 16) / 32 * 2 * math.pi
    dx, dy = math.sin(a), -math.cos(a)
    px, py = -dy, dx
    tip = U(poly(ctx, [(8 + px * 1.1, 8 + py * 1.1), (8 + dx * 4.6, 8 + dy * 4.6), (8 - px * 1.1, 8 - py * 1.1)]),
            line(ctx, [(8.0, 8.0), (8 + dx * 4.0, 8 + dy * 4.0)], 1.5))
    tail = U(poly(ctx, [(8 + px * 1.1, 8 + py * 1.1), (8 - dx * 4.0, 8 - dy * 4.0), (8 - px * 1.1, 8 - py * 1.1)]),
             line(ctx, [(8.0, 8.0), (8 - dx * 3.4, 8 - dy * 3.4)], 1.5))
    paint(t, minus(tail, tip), pal("5a5a64")[0])
    paint(t, tip, pal("d0281e")[0])
    paint(t, circ(ctx, 8.0, 8.0, 0.75), IRON[3])
    paint(t, dots(ctx, [(3, 4), (4, 3)], 0.45), IRON[4])
    return t


for _i in range(64):
    register(f"item/clock_{_i:02d}", lambda ctx, i=_i: clock(ctx, i))
for _i in range(32):
    register(f"item/compass_{_i:02d}", lambda ctx, i=_i: compass(ctx, i))
