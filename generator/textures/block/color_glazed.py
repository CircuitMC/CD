"""Glazed terracotta: 16 original ornamental tiles.

Each tile is one quadrant of a larger 4-fold rotationally symmetric motif
whose center is the tile's top-left corner. The game places glazed
terracotta rotated by facing, so four blocks set around a corner with the
four facings rebuild the full 32x32 motif. Designs are also mirror symmetric
along the tile diagonal near the shared edges, so neighboring rotated copies
meet without breaks.

Every design maps canonical motif coordinates (u, v >= 0) to integer regions;
regions get colors from a per-dye glaze palette.
"""
import math

import numpy as np

from ...engine import Tex, hexc
from ...registry import register

TAU = 2 * math.pi
Q = math.pi / 2


def canon(u, v):
    """Rotate any motif point into the canonical quadrant (C4 symmetry)."""
    q1 = (u < 0) & (v >= 0)
    q2 = (u < 0) & (v < 0)
    q3 = (u >= 0) & (v < 0)
    cu = np.where(q1, v, np.where(q2, -u, np.where(q3, -v, u)))
    cv = np.where(q1, -u, np.where(q2, -v, np.where(q3, u, v)))
    return cu, cv


class G:
    """Geometry of canonical motif coordinates."""

    def __init__(self, u, v):
        self.u, self.v = u, v
        self.r = np.hypot(u, v)
        self.a = np.arctan2(v, u)          # 0..pi/2
        self.m = np.maximum(u, v)
        self.n = np.minimum(u, v)
        self.d = u + v
        self.e = u - v
        self.r16 = np.hypot(u - 16, v - 16)  # distance to the far corner (2x2 motif corners)
        self.rx = np.hypot(u - 16, v)        # distance to the edge midpoints of the big motif
        self.ry = np.hypot(u, v - 16)


def seg(g, x1, y1, x2, y2):
    px, py = g.u - x1, g.v - y1
    bx, by = x2 - x1, y2 - y1
    t = np.clip((px * bx + py * by) / (bx * bx + by * by), 0, 1)
    return np.hypot(px - bx * t, py - by * t)


def sym_seg(g, x1, y1, x2, y2):
    """Segment mirrored across the diagonal (keeps edge continuity)."""
    return np.minimum(seg(g, x1, y1, x2, y2), seg(g, y1, x1, y2, x2))


def ellipse(g, cx, cy, ax, ay, ang=0.0):
    """Normalized ellipse radius (<1 inside); ang in radians, ax along the axis."""
    px, py = g.u - cx, g.v - cy
    c, s = math.cos(ang), math.sin(ang)
    x = px * c + py * s
    y = -px * s + py * c
    return np.hypot(x / ax, y / ay)


def tri(x):
    """Triangle wave, period 1, range 0..1."""
    f = x - np.floor(x)
    return 1 - np.abs(2 * f - 1)


def pick(shape, *layers):
    """Paint layers in order: each (mask, region)."""
    out = np.zeros(shape, np.int32)
    for m, k in layers:
        out = np.where(m, k, out)
    return out


# ------------------------------------------------------------------ designs
# Each returns region ids (0 = glaze ground). Palettes list colors per id.

def d_white(g):   # lily rosette with a blue ring and corner blossoms
    petal = g.r < 3.6 + 2.6 * np.abs(np.cos(4 * g.a)) ** 1.5
    return pick(g.u.shape,
                ((g.r > 9.6) & (g.r < 11.4), 1),
                (petal, 2), (g.r < 1.9, 3),
                (g.r16 < 4.6, 2), (g.r16 < 2.2, 3),
                (np.minimum(g.rx, g.ry) < 2.4, 1),
                ((np.abs(g.r - 10.5) < 0.5) & (np.cos(16 * g.a) > 0.6), 4))


def d_orange(g):  # sunburst with a framed corner
    rays = (g.r > 3.4) & (g.r < 11.5) & (np.cos(12 * g.a) > 0.15)
    return pick(g.u.shape,
                (rays, 1),
                ((g.m > 13.2) & (g.m < 14.6), 2),
                (g.r < 3.6, 3), (g.r < 1.6, 2),
                (np.abs(g.u - 16) + np.abs(g.v - 16) < 3.2, 1),
                ((g.r > 11.5) & (g.r < 12.5) & (np.cos(12 * g.a) > 0.15), 3))


def d_magenta(g):  # diamond lattice with jewel centers
    s = np.mod(g.u + g.v, 8)
    t = np.mod(g.u - g.v, 8)
    jew = np.abs(s - 4) + np.abs(t - 4)
    line = (np.minimum(t, 8 - t) < 0.6) | (np.minimum(s, 8 - s) < 0.6)
    return pick(g.u.shape,
                (jew < 3.1, 1), (jew < 1.1, 2), (line & (g.r > 3), 3),
                (g.r < 3.2, 2), (g.r < 1.6, 3))


def d_light_blue(g):  # rippling rings
    w = g.r + 0.9 * np.cos(8 * g.a)
    k = np.floor(w / 2.4).astype(np.int32) % 4
    reg = np.choose(k, [0, 1, 0, 2])
    reg = np.where(g.r < 2.2, 3, reg)
    reg = np.where(g.r16 < 3.0, 3, reg)
    return reg


def d_yellow(g):  # quatrefoil flower with diagonal leaves
    p = (g.u + g.v) / math.sqrt(2)
    q = (g.u - g.v) / math.sqrt(2)
    leaf = np.hypot((p - 9.5) / 4.0, q / 1.9) < 1
    petal = (ellipse(g, 6.5, 0, 5.2, 3.2) < 1) | (ellipse(g, 0, 6.5, 3.2, 5.2) < 1)
    return pick(g.u.shape,
                (petal, 1), (leaf, 2), (leaf & (np.abs(q) < 0.6), 3),
                (g.r < 2.6, 4), ((g.r16 < 4.0) & (g.r16 > 2.0), 4),
                ((np.abs(g.u - 16) < 0.6) | (np.abs(g.v - 16) < 0.6), 3))


def d_lime(g):  # four-armed spiral
    arm = (np.mod(g.a / Q + g.r / 9.0, 1.0) < 0.42) & (g.r > 2.2)
    rim = arm & ~(np.mod(g.a / Q + (g.r - 1.0) / 9.0, 1.0) < 0.42)
    return pick(g.u.shape, (arm, 1), (rim, 3), (g.r < 2.2, 2), (g.r16 < 3.2, 2), (g.r16 < 1.5, 1))


def d_pink(g):  # blossoms on a dotted ground
    rr = np.hypot(g.u - 8.5, g.v - 8.5)
    aa = np.arctan2(g.v - 8.5, g.u - 8.5) - math.pi / 4
    blossom = rr < 3.0 + 1.6 * np.cos(5 * aa)
    dots = (np.mod(g.u, 4) > 1) & (np.mod(g.u, 4) < 2) & (np.mod(g.v, 4) > 1) & (np.mod(g.v, 4) < 2)
    center = g.r < 3.6 + 1.0 * np.cos(8 * g.a)
    return pick(g.u.shape, (dots, 3), (blossom, 1), (rr < 1.3, 2), (center, 1), (g.r < 1.7, 2),
                (g.r16 < 2.6, 1), (g.r16 < 1.2, 2))


def d_gray(g):  # nested squares with cyan studs and bridges
    ring = np.mod(g.m, 4) < 1
    bridge = (g.n < 1) & (np.mod(g.m, 8) > 4)
    stud = ring & (np.abs(g.e) < 0.6)
    return pick(g.u.shape, (ring, 1), (bridge, 1), (stud, 2), (g.m < 1, 2),
                ((g.m > 14.5), 3))


def d_light_gray(g):  # compass star
    c2 = np.abs(np.cos(2 * g.a))
    s2 = np.abs(np.sin(2 * g.a))
    edge = 2.6 + np.maximum(9.5 * c2 ** 6, 6.0 * s2 ** 6)
    star = g.r < edge
    # two-tone points: the side of each point facing counter-clockwise is lighter
    half = np.mod(g.a / (math.pi / 4), 1.0) < 0.5
    return pick(g.u.shape, ((g.r16 < 5.4) & (g.r16 > 3.6), 3), (star, 1), (star & half, 2),
                (g.r < 1.6, 3), (g.r16 < 1.6, 2))


def d_cyan(g):  # radial fish scales
    ring_w = 3.5
    k = np.floor(g.r / ring_w)
    count = np.maximum(1, np.round((k + 0.5) * ring_w * Q / 3.6))
    s = g.a / Q * count
    fs = s - np.floor(s)
    fr = g.r / ring_w - k
    arc = (k + 0.5) * ring_w * Q / count
    dist = np.hypot((fs - 0.5) * arc, fr * ring_w)
    scale = dist < 3.0
    inner = dist < 1.8
    return pick(g.u.shape, (scale, 1), (inner, 2), (~scale & (dist < 3.6), 3), (g.r < 1.8, 3))


def d_purple(g):  # polar checker with a gold band
    k = np.floor(g.r / 2.6) + np.floor(g.a / (math.pi / 14))
    reg = np.where((k.astype(np.int32) % 2) == 0, 0, 1)
    reg = np.where((g.r > 11.3) & (g.r < 12.6), 2, reg)
    reg = np.where(g.r < 2.6, 2, reg)
    reg = np.where(g.r16 < 3.0, 3, reg)
    return reg


def d_blue(g):  # crystal / frost star
    arms = g.n < 1.0
    diag = np.abs(g.e) < 0.6
    br = np.full(g.u.shape, 99.0, np.float32)
    for p, ln in ((5.0, 3.0), (9.0, 2.5)):
        br = np.minimum(br, sym_seg(g, p, p, p + ln, p - ln))
    for p, ln in ((6.0, 2.5), (10.0, 2.0)):   # branches on the edge arms
        br = np.minimum(br, sym_seg(g, p, 0, p + ln * 0.6, ln))
    tips = np.hypot(g.u - 11.5, g.v - 11.5) < 1.3
    return pick(g.u.shape, ((arms | diag) & (g.r < 14.5), 1), (br < 0.55, 1), (tips, 2),
                (g.r < 2.0, 2), ((g.r16 < 3.0) & (g.r16 > 1.6), 3),
                (np.minimum(g.rx, g.ry) < 1.5, 2))


def d_brown(g):  # zigzag diamonds
    w = g.d + 2.2 * tri(g.e / 5.0)
    k = np.floor(w / 3.0).astype(np.int32) % 3
    reg = np.choose(k, [0, 1, 2])
    reg = np.where(g.d < 2.0, 3, reg)
    return reg


def d_green(g):  # leaf wreath with berries
    reg = np.zeros(g.u.shape, np.int32)
    for i in range(3):
        ang = (i + 0.5) * Q / 3
        cx, cy = 9.5 * math.cos(ang), 9.5 * math.sin(ang)
        e = ellipse(g, cx, cy, 2.9, 1.4, ang + Q * 0.75)
        reg = np.where(e < 1, 1, reg)
        reg = np.where((e < 1) & (ellipse(g, cx, cy, 2.9, 0.35, ang + Q * 0.75) < 1), 2, reg)
    berry = (np.hypot(g.u - 9.5, g.v) < 1.6) | (np.hypot(g.u, g.v - 9.5) < 1.6)
    reg = np.where(berry, 3, reg)
    flower = g.r < 2.6 + 1.6 * np.abs(np.cos(2 * g.a)) ** 3
    reg = np.where(flower, 4, reg)
    reg = np.where(g.r < 1.2, 3, reg)
    reg = np.where((g.r16 < 3.5), 1, reg)
    reg = np.where((g.r16 < 1.5), 4, reg)
    return reg


def d_red(g):  # rose window
    w = g.r + 1.6 * np.abs(np.cos(4 * g.a))
    k = np.floor(w / 3.0).astype(np.int32)
    reg = np.where(k % 2 == 0, 0, 1)
    reg = np.where(w > 13.5, 0, reg)
    dots = np.zeros(g.u.shape, bool)
    for i in range(4):
        ang = (i + 0.5) * Q / 4
        dots |= np.hypot(g.u - 13.5 * math.cos(ang), g.v - 13.5 * math.sin(ang)) < 1.1
    reg = np.where(dots, 2, reg)
    reg = np.where(g.r < 2.0, 3, reg)
    reg = np.where(g.r16 < 2.2, 3, reg)
    return reg


def d_black(g):  # gold geometry
    sq = np.abs(g.m - 7) < 0.5
    dia = np.abs(g.d - 15) < 0.7
    circ = np.abs(g.r - 11) < 0.55
    diag = (np.abs(g.e) < 0.6) & (g.r < 9.5)
    return pick(g.u.shape, (circ, 2), (sq | dia, 1), (diag, 1), (g.r < 2.2, 1), (g.r < 1, 3),
                (g.r16 < 2.0, 2))


DESIGNS = {
    # name: (fn, palette by region id, raised regions)
    "white": (d_white, ["e9e4d6", "8fb3c9", "5b7f9c", "e0b84a", "ffffff"], (2, 3)),
    "orange": (d_orange, ["d9772c", "f2c14a", "5e3420", "f3e3c2"], (1, 3)),
    "magenta": (d_magenta, ["b5459f", "e597cf", "fbeaf2", "5c1c55"], (1, 2)),
    "light_blue": (d_light_blue, ["63b4dc", "dff0f6", "24578f", "f2d36b"], (1,)),
    "yellow": (d_yellow, ["eac43c", "fbf5dc", "5f9a35", "3b6524", "d36f2a"], (1, 2, 4)),
    "lime": (d_lime, ["93cc3c", "3f7e26", "f1f3d6", "26511b"], (1, 2)),
    "pink": (d_pink, ["e698b3", "fdf1f3", "b2395e", "cf7493"], (1,)),
    "gray": (d_gray, ["4c5257", "9aa1a6", "46b7b5", "2d3034"], (1, 2)),
    "light_gray": (d_light_gray, ["a7a8a3", "e6e7e2", "6aa3a8", "4e5254"], (1, 2)),
    "cyan": (d_cyan, ["137f83", "3cc0b8", "c9efe4", "0b4447"], (1, 2)),
    "purple": (d_purple, ["6c2aa0", "a978d6", "e2b64a", "f1e3f6"], (2,)),
    "blue": (d_blue, ["283a8f", "8db5ec", "f2f6ff", "e2b64a"], (1, 2)),
    "brown": (d_brown, ["70472b", "b88a5b", "e8d3ad", "3d2416"], (1, 2)),
    "green": (d_green, ["3f5a1c", "86b24a", "2a3d12", "c43c34", "f0e6c4"], (1, 3, 4)),
    "red": (d_red, ["a32a27", "6b1517", "f2dfc4", "e5b443"], (1, 2, 3)),
    "black": (d_black, ["1d1d22", "d8a93a", "3aa69e", "f4e7c4"], (1, 2)),
}


def glazed(ctx, dye):
    fn, palette, raised = DESIGNS[dye]
    pal_arr = np.stack([hexc(c) for c in palette])
    # Motif center = top-left corner of the tile; tile spans u, v in [0, 16].
    sx, sy = 16.0 / ctx.w, 16.0 / ctx.h
    u, v = ctx.x * sx, ctx.y * sy
    reg = fn(G(*canon(u, v)))
    o = 1.0
    nb = {}
    for key, (du, dv) in {"l": (-o, 0), "t": (0, -o), "r": (o, 0), "b": (0, o)}.items():
        nb[key] = fn(G(*canon(u + du, v + dv)))
    color = pal_arr[reg]
    rmask = np.isin(reg, raised)
    lower = {k: (nb[k] != reg) & ~np.isin(nb[k], raised) for k in nb}
    lit = rmask & (lower["l"] | lower["t"])
    dark = rmask & (lower["r"] | lower["b"]) & ~lit
    # Glaze: a soft pooled sheen, darker where the glaze runs thin at shape borders.
    sheen = ctx.noise(8, 2, 0.5, salt="glaze")
    color = color * (0.95 + sheen[..., None] * 0.08)
    color = np.where(lit[..., None], np.clip(color * 1.12 + 0.03, 0, 1), color)
    color = np.where(dark[..., None], color * 0.78, color)
    ground_edge = ~rmask & np.isin(nb["l"], raised) | ~rmask & np.isin(nb["t"], raised)
    color = np.where(ground_edge[..., None], color * 0.86, color)  # cast shadow down-right
    craze = ctx.noise(2, 2, 0.5, salt="craze")
    crack = (np.abs(craze - 0.5) < 0.012) if not ctx.pixel_art else np.zeros_like(rmask)
    color = np.where(crack[..., None], color * 0.9, color)
    height = 0.5 + rmask * 0.12 + lit * 0.05 - dark * 0.05 - ground_edge * 0.04
    return Tex(ctx, np.clip(color, 0, 1), height=height, smooth=0.82, f0=0.05, porosity=0.0,
               normal_strength=0.6, grain=0.02)


for _dye in DESIGNS:
    register(f"block/{_dye}_glazed_terracotta", lambda ctx, d=_dye: glazed(ctx, d))
