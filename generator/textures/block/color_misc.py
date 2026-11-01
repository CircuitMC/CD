"""End portal frame, block-breaking crack overlays and debug textures."""
import math

import numpy as np

from ...engine import Tex, pal
from ...registry import register

# ------------------------------------------------------------------ end portal frame

END_STONE = pal("a9a76c", "bdbb7d", "cfcd8e", "dcda9e", "e6e4ae", "f0eebe")
FRAME = pal("12211d", "1d3a33", "2b5448", "3d7262", "56927c", "78b39a")
EYE = pal("0c1f17", "1e4a35", "2f7350", "4fa06c", "86cf8e", "d4f5cf")


def end_stone_base(ctx, salt):
    n = ctx.noise(4, 3, 0.55, salt=f"{salt}n")
    g = ctx.texel_noise(f"{salt}g")
    v = n * 0.6 + g * 0.4
    color = ctx.palette(END_STONE[1:-1], v)
    pit = ctx.texel_noise(f"{salt}p", soft=False) < 0.06
    color = np.where(pit[..., None], END_STONE[0], color)
    return color, 0.5 + n * 0.12 - pit * 0.15


def bevel_band(ctx, color, height, x0, y0, x1, y1, p, base_v=0.5, salt="band"):
    m = ctx.rect(x0, y0, x1, y1) > 0
    n = ctx.noise(2, 2, 0.5, salt=salt)
    c = ctx.palette(p[1:-1], np.clip(base_v + (n - 0.5) * 0.35, 0, 1))
    lit = m & ((ctx.rect(x0, y0, x1, y0 + 1) + ctx.rect(x0, y0, x0 + 1, y1)) > 0)
    dark = m & ((ctx.rect(x0, y1 - 1, x1, y1) + ctx.rect(x1 - 1, y0, x1, y1)) > 0) & ~lit
    c = np.where(lit[..., None], p[-1], np.where(dark[..., None], p[0], c))
    color = np.where(m[..., None], c, color)
    height = np.where(m, 0.75 + lit * 0.08 - dark * 0.1, height)
    return color, height, m


def end_portal_frame_top(ctx):
    color, height = end_stone_base(ctx, "eft")
    # Teal inlay ring around a recessed socket for the eye.
    ring = (ctx.rect(2, 2, 14, 14) > 0) & ~(ctx.rect(3, 3, 13, 13) > 0)
    color = np.where(ring[..., None], FRAME[3], color)
    color = np.where((ring & (ctx.rect(2, 2, 14, 3) + ctx.rect(2, 2, 3, 14) > 0))[..., None], FRAME[4], color)
    socket = ctx.rect(4, 4, 12, 12) > 0
    n = ctx.noise(2, 2, 0.5, salt="sock")
    sc = ctx.palette(FRAME[:3], n * 0.6 + ctx.texel_noise("sk") * 0.4)
    rim_dark = socket & ((ctx.rect(4, 4, 12, 5) + ctx.rect(4, 4, 5, 12)) > 0)   # shadowed inner wall
    rim_lit = socket & ((ctx.rect(4, 11, 12, 12) + ctx.rect(11, 4, 12, 12)) > 0) & ~rim_dark
    sc = np.where(rim_dark[..., None], FRAME[0], np.where(rim_lit[..., None], FRAME[3], sc))
    color = np.where(socket[..., None], sc, color)
    # Corner studs
    for cx, cy in ((1, 1), (14, 1), (1, 14), (14, 14)):
        st = ctx.rect(cx, cy, cx + 1, cy + 1) > 0
        color = np.where(st[..., None], FRAME[4], color)
    height = np.where(socket, 0.15, np.where(ring, 0.62, height))
    return Tex(ctx, np.clip(color, 0, 1), height=height, smooth=0.3, f0=0.04, porosity=0.1)


def end_portal_frame_side(ctx):
    color, height = end_stone_base(ctx, "efs")
    # Teal cap band (the frame's top edge sits on rows 3..5 of the face).
    color, height, _ = bevel_band(ctx, color, height, 0, 0, ctx.w, 6, FRAME, 0.55, "cap")
    notch = np.zeros((ctx.H, ctx.W), bool)
    for x in (2, 7, 12):
        notch |= ctx.rect(x, 4, x + 2, 5) > 0
    color = np.where(notch[..., None], FRAME[1], color)
    # Carved vertical panels in the end stone below.
    for x0 in (1, 9):
        pm = ctx.rect(x0, 8, x0 + 6, 15) > 0
        inner = ctx.rect(x0 + 1, 9, x0 + 5, 14) > 0
        groove_d = pm & ~inner & ((ctx.rect(x0, 8, x0 + 6, 9) + ctx.rect(x0, 8, x0 + 1, 15)) > 0)
        groove_l = pm & ~inner & ~groove_d
        color = np.where(groove_d[..., None], END_STONE[0], color)
        color = np.where(groove_l[..., None], END_STONE[-1], color)
        height = np.where(groove_d, 0.3, np.where(groove_l, 0.6, height))
    shadow = ctx.rect(0, 6, ctx.w, 7) > 0
    color = np.where(shadow[..., None], color * 0.8, color)
    return Tex(ctx, np.clip(color, 0, 1), height=height, smooth=0.25, f0=0.04, porosity=0.12)


def end_portal_frame_eye(ctx):
    """Eye element: top face uses (4,4)-(12,12), its sides use (4,0)-(12,3)."""
    color = np.zeros((ctx.H, ctx.W, 3), np.float32)
    alpha = ctx.zeros()
    height = ctx.zeros()
    # Side band
    band = ctx.rect(4, 0, 12, 3) > 0
    n = ctx.noise(2, 2, 0.5, salt="eyeband")
    bc = ctx.palette(EYE[1:4], n)
    bc = np.where((ctx.rect(4, 0, 12, 1) > 0)[..., None], EYE[4], bc)
    bc = np.where((ctx.rect(4, 2, 12, 3) > 0)[..., None], EYE[1], bc)
    pupil_side = ctx.rect(7, 0, 9, 3) > 0
    bc = np.where(pupil_side[..., None], EYE[0], bc)
    color = np.where(band[..., None], bc, color)
    # Top: an orb with iris rings and a vertical slit pupil.
    top = ctx.rect(4, 4, 12, 12) > 0
    r = np.hypot(ctx.x - 8, ctx.y - 8)
    light = np.clip(-((ctx.x - 8) + (ctx.y - 8)) / 6, -1, 1)
    v = 0.55 - r / 9 + light * 0.25
    tc = ctx.palette(EYE[1:5], np.clip(v + 0.15, 0, 1))
    rim = (r > 3.6)
    tc = np.where(rim[..., None], EYE[1], tc)
    slit = (np.abs(ctx.x - 8) < 0.8 + (r < 1.5) * 0.2) & (r < 3.0)
    tc = np.where(slit[..., None], EYE[0], tc)
    hl = ctx.rect(5.5, 5.5, 6.5, 6.5) > 0
    tc = np.where(hl[..., None], EYE[5], tc)
    color = np.where(top[..., None], tc, color)
    solid = band | top
    alpha = np.where(solid, 1.0, alpha)
    height = np.where(top, 0.5 + np.clip(1 - r / 5, 0, 1) * 0.4, np.where(band, 0.6, 0))
    return Tex(ctx, np.clip(color, 0, 1), alpha=alpha, height=height, smooth=0.85, f0=0.06,
               emissive=np.where(top & ~rim, 0.25, 0.0), wrap=False, grain=0.02)


# ------------------------------------------------------------------ breaking cracks

def crack_segments(seed=7):
    """Branching crack tree in texel space: list of (x1, y1, x2, y2, birth 0..1)."""
    rng = np.random.default_rng(seed)
    segs = []
    stack = []
    for k in range(3):  # three main fractures leave the impact point
        ang = k * 2 * math.pi / 3 + rng.uniform(-0.5, 0.5)
        stack.append((8.0 + rng.uniform(-0.6, 0.6), 8.0 + rng.uniform(-0.6, 0.6), ang, 0.0, 9.0, 0))
    while stack:
        x, y, ang, dist, budget, depth = stack.pop()
        while budget > 0:
            step = rng.uniform(1.2, 2.2)
            ang += rng.uniform(-0.55, 0.55)
            nx, ny = x + math.cos(ang) * step, y + math.sin(ang) * step
            if not (-0.5 < nx < 16.5 and -0.5 < ny < 16.5):
                break
            segs.append((x, y, nx, ny, dist))
            dist += step
            budget -= step
            x, y = nx, ny
            if depth < 3 and rng.random() < 0.32:
                side = rng.choice([-1, 1])
                stack.append((x, y, ang + side * rng.uniform(0.6, 1.2), dist, budget * 0.75 + 1.5, depth + 1))
    # Late hairlines near the rim of the face.
    for _ in range(6):
        x, y = rng.uniform(1, 15), rng.uniform(1, 15)
        ang = rng.uniform(0, 2 * math.pi)
        d0 = 12 + rng.uniform(0, 6)
        for _ in range(int(rng.integers(2, 4))):
            ang += rng.uniform(-0.5, 0.5)
            nx, ny = x + math.cos(ang) * 1.6, y + math.sin(ang) * 1.6
            segs.append((x, y, nx, ny, d0))
            d0 += 1.6
            x, y = nx, ny
    mx = max(s[4] for s in segs) + 1e-3
    return [(a, b, c, d, e / mx) for a, b, c, d, e in segs]


CRACKS = crack_segments()


def crack_mask(ctx, limit):
    m = ctx.zeros()
    w = 1.0 if ctx.pixel_art else 0.75
    for x1, y1, x2, y2, birth in CRACKS:
        if birth <= limit:
            # Main fractures widen as they open up (older = wider).
            width = w + (0.35 if (limit - birth) > 0.45 and not ctx.pixel_art else 0)
            m = np.maximum(m, ctx.segment(x1, y1, x2, y2, width))
    if ctx.pixel_art:  # texel-snap: any texel whose center is near a segment
        return m > 0.5
    return ctx.organic(m, 0.15, "crk")


def destroy(ctx, stage, oit=False):
    limit = 0.06 + stage * 0.104
    m = crack_mask(ctx, limit)
    halo = np.zeros_like(m)
    if stage >= 4:
        s = ctx.s
        halo = (np.roll(m, s, 0) | np.roll(m, s, 1) | np.roll(m, -s, 0) | np.roll(m, -s, 1)) & ~m
        keep = ctx.texel_noise("halo", soft=False) < (stage - 3) * 0.13
        halo &= keep
    lit = (np.roll(m, ctx.s, 0) & ~m & ~halo)  # light lip below-right of the crack edge
    # Breaking overlays are multiplied (x2) onto the block: 0.5 = no change.
    v = np.where(m, 0.22, np.where(halo, 0.40, 0.62))
    v = v - (ctx.texel_noise("crv") - 0.5) * 0.06
    color = np.repeat(v[..., None], 3, -1).astype(np.float32)
    if oit:
        alpha = np.where(m, 0.85, np.where(halo, 0.45, np.where(lit, 0.35, 0.0)))
    else:
        alpha = np.where(m | halo | lit, 1.0, 0.0)
    return Tex(ctx, color, alpha=alpha, height=np.where(m, 0.1, 0.5), wrap=False, grain=0)


# ------------------------------------------------------------------ debug

def debug(ctx):
    """Orientation test card: four colored quadrants, UV gradient, top-left corner marker."""
    u, v = ctx.x / ctx.w, ctx.y / ctx.h
    quad = (ctx.x >= ctx.w / 2).astype(np.int32) + 2 * (ctx.y >= ctx.h / 2)
    base = pal("d8433c", "3fae4a", "3b6fd6", "e8c33a")[quad]
    grad = 0.75 + 0.25 * ((u * 4) % 1)[..., None] * ((v * 4) % 1 < 0.5)[..., None]
    color = base * grad
    grid = (ctx.tx % 4 == 0) | (ctx.ty % 4 == 0)
    color = np.where(grid[..., None], color * 0.8, color)
    mark = (ctx.rect(1, 1, 6, 2) + ctx.rect(1, 1, 2, 6)) > 0     # "L" = top-left
    color = np.where(mark[..., None], np.array([1, 1, 1], np.float32), color)
    dot = ctx.rect(12, 12, 14, 14) > 0
    color = np.where(dot[..., None], np.array([0.1, 0.1, 0.12], np.float32), color)
    return Tex(ctx, np.clip(color, 0, 1), height=0.5, smooth=0.3, grain=0)


def debug2(ctx):
    """Second test card: diagonal stripes, center crosshair and an up arrow."""
    stripe = (np.floor((ctx.x + ctx.y) / 2) % 2) == 0
    color = np.where(stripe[..., None], pal("27c2c9")[0], pal("c93fb4")[0])
    cross = ((np.abs(ctx.x - 8) < 0.5 + 0.5 * ctx.pixel_art) | (np.abs(ctx.y - 8) < 0.5 + 0.5 * ctx.pixel_art))
    cross &= np.hypot(ctx.x - 8, ctx.y - 8) < 5.5
    color = np.where(cross[..., None], np.array([0.98, 0.98, 0.98], np.float32), color)
    arrow = ctx.polygon([(8, 0.5), (11, 3.5), (5, 3.5)]) > 0
    color = np.where(arrow[..., None], np.array([0.1, 0.1, 0.12], np.float32), color)
    border = ctx.edge(ctx.full(1), 1) > 0
    color = np.where(border[..., None], np.array([0.1, 0.1, 0.12], np.float32), color)
    return Tex(ctx, np.clip(color, 0, 1), height=0.5, smooth=0.3, grain=0)


register("block/end_portal_frame_top", end_portal_frame_top)
register("block/end_portal_frame_side", end_portal_frame_side)
register("block/end_portal_frame_eye", end_portal_frame_eye)
register("block/debug", debug)
register("block/debug2", debug2)
for _i in range(10):
    register(f"block/destroy_stage_{_i}", lambda ctx, i=_i: destroy(ctx, i))
    register(f"block/destroy_oit_stage_{_i}", lambda ctx, i=_i: destroy(ctx, i, oit=True))
