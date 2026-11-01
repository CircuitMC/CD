"""Banner and shield textures sharing one heraldic pattern library.

Layouts from the CEM templates banner/banner_flag/banner_base/shield.jem.
Banner flag (64x64): uv(0,0) 20x40x1 -> front face (1,1)-(21,41), back (22,1)-(42,41);
pole (44,0) 2x42x2, bar (0,42) 20x2x2.
Shield (64x64): plate uv(0,0) 12x22x1 -> front (1,1)-(13,23); handle (26,0) 2x6x6.

Pattern textures are white/gray masks with alpha (the game tints them with the
dye color). Every pattern is defined on face-local texel coordinates
(lx, ly) of a W x H face so the same design fits banners and shields.
"""
import math

import numpy as np

from ...engine import IRON, pal
from ...registry import register
from .objects_common import Sheet, frame, gray, wood_field


# ------------------------------------------------------------------ shape helpers (array based)

def _rect(x, y, x0, y0, x1, y1):
    return (x >= x0) & (x < x1) & (y >= y0) & (y < y1)


def _disk(x, y, cx, cy, r):
    return np.hypot(x - cx, y - cy) < r


def _seg(x, y, x1, y1, x2, y2, w):
    px, py = x - x1, y - y1
    bx, by = x2 - x1, y2 - y1
    t = np.clip((px * bx + py * by) / max(1e-6, bx * bx + by * by), 0, 1)
    return np.hypot(px - bx * t, py - by * t) < w / 2


def _poly(x, y, pts):
    inside = np.zeros(np.shape(x), bool)
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if y1 == y2:
            continue
        cond = (y >= min(y1, y2)) & (y < max(y1, y2))
        xint = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
        inside ^= cond & (x < xint)
    return inside


# ------------------------------------------------------------------ motifs (mu, mv in -1..1)

def _m_creeper(u, v):
    eyes = (_rect(u, v, -0.8, -0.65, -0.2, -0.1) | _rect(u, v, 0.2, -0.65, 0.8, -0.1))
    eyes &= ~(_rect(u, v, -0.4, -0.3, -0.2, -0.1) | _rect(u, v, 0.2, -0.3, 0.4, -0.1))  # notched
    mouth = _rect(u, v, -0.2, -0.1, 0.2, 0.45) | _rect(u, v, -0.5, 0.15, -0.2, 0.85) | _rect(u, v, 0.2, 0.15, 0.5, 0.85)
    mouth &= ~_rect(u, v, -0.08, 0.3, 0.08, 0.45)
    return eyes | mouth


def _m_skull(u, v):
    head = _disk(u, v, 0, -0.3, 0.6) | _rect(u, v, -0.38, -0.1, 0.38, 0.35)
    holes = _disk(u, v, -0.25, -0.28, 0.17) | _disk(u, v, 0.25, -0.28, 0.17)
    holes |= _poly(u, v, [(0, -0.05), (-0.1, 0.12), (0.1, 0.12)])
    teeth = _rect(u, v, -0.3, 0.22, 0.3, 0.3) & ((np.floor((u + 1) * 7) % 2) == 0)
    bones = _seg(u, v, -0.85, 0.45, 0.85, 0.95, 0.22) | _seg(u, v, 0.85, 0.45, -0.85, 0.95, 0.22)
    bones |= _disk(u, v, -0.85, 0.45, 0.16) | _disk(u, v, 0.85, 0.45, 0.16)
    bones |= _disk(u, v, -0.85, 0.95, 0.16) | _disk(u, v, 0.85, 0.95, 0.16)
    return (head & ~holes & ~teeth) | (bones & ~head)


def _m_flower(u, v):
    m = np.zeros(np.shape(u), bool)
    for i in range(6):
        a = i * math.pi / 3 + math.pi / 6
        m |= _disk(u, v, math.cos(a) * 0.6, math.sin(a) * 0.6, 0.27)
    m &= ~_disk(u, v, 0, 0, 0.36)
    m |= _disk(u, v, 0, 0, 0.2)
    return m


def _m_globe(u, v):
    r = np.hypot(u, v)
    ring = (r < 0.92) & (r > 0.74)
    lat = (np.abs(v) < 0.08) & (r < 0.8) | (np.abs(np.abs(v) - 0.42) < 0.07) & (r < 0.8)
    mer = np.abs(np.hypot(u / 0.42, v / 0.88) - 1) < 0.14
    land = _disk(u, v, -0.25, -0.2, 0.22) | _disk(u, v, 0.3, 0.25, 0.18)
    return ring | lat | (mer & (r < 0.8)) | (land & (r < 0.74))


def _m_piglin(u, v):
    snout = _rect(u, v, -0.55, -0.15, 0.55, 0.45) | _disk(u, v, -0.42, -0.02, 0.15) | _disk(u, v, 0.42, -0.02, 0.15)
    nostrils = _rect(u, v, -0.32, 0.05, -0.12, 0.3) | _rect(u, v, 0.12, 0.05, 0.32, 0.3)
    tusks = _poly(u, v, [(-0.6, 0.45), (-0.4, 0.45), (-0.6, 0.85)]) | _poly(u, v, [(0.6, 0.45), (0.4, 0.45), (0.6, 0.85)])
    brow = _rect(u, v, -0.75, -0.7, -0.25, -0.5) | _rect(u, v, 0.25, -0.7, 0.75, -0.5)
    ears = _poly(u, v, [(-0.95, -0.95), (-0.6, -0.8), (-0.85, -0.45)]) | _poly(u, v, [(0.95, -0.95), (0.6, -0.8), (0.85, -0.45)])
    return (snout & ~nostrils) | tusks | brow | ears


def _m_emblem(u, v):
    """Original CircuitMC chip emblem (replaces the vanilla brand pattern)."""
    body = _rect(u, v, -0.5, -0.5, 0.5, 0.5) & ~_rect(u, v, -0.32, -0.32, 0.32, 0.32)
    core = _rect(u, v, -0.16, -0.16, 0.16, 0.16)
    pins = np.zeros(np.shape(u), bool)
    for t in (-0.3, 0.0, 0.3):
        pins |= _rect(u, v, t - 0.06, -0.9, t + 0.06, -0.5) | _rect(u, v, t - 0.06, 0.5, t + 0.06, 0.9)
        pins |= _rect(u, v, -0.9, t - 0.06, -0.5, t + 0.06) | _rect(u, v, 0.5, t - 0.06, 0.9, t + 0.06)
    pads = np.zeros(np.shape(u), bool)
    for t in (-0.3, 0.0, 0.3):
        for s in (-0.9, 0.9):
            pads |= _disk(u, v, t, s, 0.1) | _disk(u, v, s, t, 0.1)
    return body | core | pins | pads


def _m_flow(u, v):
    r = np.hypot(u, v)
    a = np.arctan2(v, u) / (2 * math.pi)
    spiral = ((r * 2.2 - a) % 1.0) < 0.42
    return spiral & (r < 0.95) & (r > 0.08)


def _m_guster(u, v):
    head = _disk(u, v, 0, -0.45, 0.42)
    eyes = _rect(u, v, -0.26, -0.55, -0.08, -0.35) | _rect(u, v, 0.08, -0.55, 0.26, -0.35)
    bands = np.zeros(np.shape(u), bool)
    for i, (cy, half) in enumerate(((0.12, 0.85), (0.45, 0.6), (0.78, 0.35))):
        sh = 0.15 if i % 2 else -0.15
        bands |= _rect(u, v, sh - half, cy - 0.1, sh + half, cy + 0.1)
        bands |= _disk(u, v, sh + half, cy - 0.1 if i % 2 == 0 else cy + 0.1, 0.1)
    return (head & ~eyes) | bands


MOTIFS = dict(creeper=_m_creeper, skull=_m_skull, flower=_m_flower, globe=_m_globe, piglin=_m_piglin,
              mojang=_m_emblem, flow=_m_flow, guster=_m_guster)


def _motif(fn, x, y, W, H):
    s = min(W, H) * 0.47
    cx, cy = W / 2, H / 2 if H <= W * 1.3 else H * 0.45
    return fn((x - cx) / s, (y - cy) / s)


# ------------------------------------------------------------------ pattern library

def pattern_alpha(name, x, y, W, H):
    """Alpha (0..1) of pattern `name` at face-local texel coords (x, y)."""
    sw = max(1, round(W * 0.3))      # vertical stripe width
    sh_ = max(1, round(H * 0.25))    # top/bottom stripe height
    u, v = x / W, y / H
    one = np.ones(np.shape(x), bool)
    if name == "base":
        return one.astype(np.float32)
    if name == "gradient":
        return np.clip(1 - v * 1.05, 0, 1).astype(np.float32)
    if name == "gradient_up":
        return np.clip(v * 1.05 - 0.02, 0, 1).astype(np.float32)
    if name in MOTIFS:
        m = _motif(MOTIFS[name], x, y, W, H)
    elif name == "border":
        b = max(1, round(W / 10))
        m = (x < b) | (x >= W - b) | (y < b) | (y >= H - b)
    elif name == "curly_border":
        b = max(1, round(W / 10))
        wave = ((np.floor(x) + np.floor(y)) % 4 < 2)
        m = (x < b) | (x >= W - b) | (y < b) | (y >= H - b)
        m |= ((x < b + 1) | (x >= W - b - 1) | (y < b + 1) | (y >= H - b - 1)) & wave
    elif name == "bricks":
        bh = max(2, round(H / 10))
        bw = max(3, round(W / 4))
        row = np.floor(y / bh)
        off = (row % 2) * (bw // 2)
        m = (np.floor(y) % bh == bh - 1) | (np.floor(x + off) % bw == bw - 1)
    elif name == "circle":
        m = np.hypot(x - W / 2, y - H / 2) < W * 0.3
    elif name == "rhombus":
        m = np.abs(x - W / 2) / (W * 0.38) + np.abs(y - H / 2) / (H * 0.3) < 1
    elif name == "cross":
        k = H / W
        t = max(1.2, W * 0.16)
        m = (np.abs(y - x * k) / math.hypot(1, k) < t) | (np.abs(y - (W - x) * k) / math.hypot(1, k) < t)
    elif name == "straight_cross":
        m = (np.abs(x - W / 2) < sw / 2) | (np.abs(y - H / 2) < sw / 2)
    elif name == "diagonal_left":
        m = u + v < 1
    elif name == "diagonal_right":
        m = v < u
    elif name == "diagonal_up_left":
        m = v > u
    elif name == "diagonal_up_right":
        m = u + v > 1
    elif name == "half_horizontal":
        m = y < H / 2
    elif name == "half_horizontal_bottom":
        m = y >= H / 2
    elif name == "half_vertical":
        m = x < W / 2
    elif name == "half_vertical_right":
        m = x >= W / 2
    elif name == "small_stripes":
        s = max(1, round(W / 10))
        m = (np.floor(x / s) % 2 == 1) & (x >= s) & (x < W - s * (1 if (W // s) % 2 == 0 else 0))
    elif name == "square_top_left":
        q = round(W * 0.4)
        m = (x < q) & (y < q)
    elif name == "square_top_right":
        q = round(W * 0.4)
        m = (x >= W - q) & (y < q)
    elif name == "square_bottom_left":
        q = round(W * 0.4)
        m = (x < q) & (y >= H - q)
    elif name == "square_bottom_right":
        q = round(W * 0.4)
        m = (x >= W - q) & (y >= H - q)
    elif name == "stripe_bottom":
        m = y >= H - sh_
    elif name == "stripe_top":
        m = y < sh_
    elif name == "stripe_left":
        m = x < sw
    elif name == "stripe_right":
        m = x >= W - sw
    elif name == "stripe_center":
        m = np.abs(x - W / 2) < sw / 2
    elif name == "stripe_middle":
        m = np.abs(y - H / 2) < max(1, round(H * 0.1))
    elif name in ("stripe_downright", "stripe_downleft"):
        k = H / W
        xx = x if name == "stripe_downright" else W - x
        m = np.abs(y - xx * k) / math.hypot(1, k) < max(1.2, W * 0.17)
    elif name == "triangle_bottom":
        m = (H - y) < (W / 2 - np.abs(x - W / 2)) * (H * 0.5 / (W / 2)) * 0.75
    elif name == "triangle_top":
        m = y < (W / 2 - np.abs(x - W / 2)) * (H * 0.5 / (W / 2)) * 0.75
    elif name in ("triangles_bottom", "triangles_top"):
        tw = W / 4
        ph = (x % tw) / tw
        tooth = (0.5 - np.abs(ph - 0.5)) * 2 * (tw * 0.9)
        base = max(1, round(H * 0.05))
        d = (H - y) if name == "triangles_bottom" else (y + 1)
        m = d <= base + tooth
    else:
        raise KeyError(name)
    return m.astype(np.float32)


PATTERNS = ["base", "border", "bricks", "circle", "creeper", "cross", "curly_border", "diagonal_left",
            "diagonal_right", "diagonal_up_left", "diagonal_up_right", "flow", "flower", "globe",
            "gradient", "gradient_up", "guster", "half_horizontal", "half_horizontal_bottom",
            "half_vertical", "half_vertical_right", "mojang", "piglin", "rhombus", "skull",
            "small_stripes", "square_bottom_left", "square_bottom_right", "square_top_left",
            "square_top_right", "straight_cross", "stripe_bottom", "stripe_center", "stripe_downleft",
            "stripe_downright", "stripe_left", "stripe_middle", "stripe_right", "stripe_top",
            "triangle_bottom", "triangle_top", "triangles_bottom", "triangles_top"]


def _cloth(ctx, salt):
    """Light fabric grain for pattern masks (values 0.82..1)."""
    n = ctx.noise(5, 2, 0.5, salt=f"pc{salt}")
    t = ctx.texel_noise(f"pt{salt}")
    weave = ((ctx.tx + ctx.ty) % 2 == 0)
    return np.clip(0.86 + n * 0.08 + t * 0.05 + weave * 0.02, 0, 1)


def _paint_face(ctx, sh, name, r, mirror=False, cloth=None):
    x0, y0, x1, y1 = r
    W, H = x1 - x0, y1 - y0
    lx = ctx.x - x0
    if mirror:
        lx = W - lx
    a = pattern_alpha(name, lx, ctx.y - y0, W, H)
    inside = sh.rect(r)
    a = np.where(inside, a, 0)
    m = a > 0.004
    sh.put(m, gray(cloth), alpha=a, height=0.5 + a * 0.04, smooth=0.08, sss=0.15)
    return a


def _edges_from(ctx, sh, name, front, cloth):
    """Flag edge strips take the pattern value of the adjacent front texels."""
    x0, y0, x1, y1 = front
    W, H = x1 - x0, y1 - y0
    for strip, fx, fy in (((x0 - 1, y0, x0, y1), np.full_like(ctx.x, 0.5), ctx.y - y0),       # left side
                          ((x1, y0, x1 + 1, y1), np.full_like(ctx.x, W - 0.5), ctx.y - y0),   # right side
                          ((x0, y0 - 1, x1, y0), ctx.x - x0, np.full_like(ctx.y, 0.5)),       # top edge
                          ((x1, y0 - 1, x1 + W, y0), ctx.x - x1, np.full_like(ctx.y, H - 0.5))):  # bottom edge
        m = sh.rect(strip)
        a = np.where(m, pattern_alpha(name, fx, fy, W, H), 0)
        sh.put(a > 0.004, gray(cloth), alpha=a, height=0.5, smooth=0.08)


def banner_pattern(ctx, name):
    sh = Sheet(ctx)
    cloth = _cloth(ctx, "banner")
    front = (1, 1, 21, 41)
    _paint_face(ctx, sh, name, front, cloth=cloth)
    _paint_face(ctx, sh, name, (22, 1, 42, 41), mirror=True, cloth=cloth)
    _edges_from(ctx, sh, name, front, cloth)
    return sh.tex(grain=0.02)


def shield_pattern(ctx, name):
    sh = Sheet(ctx)
    _paint_face(ctx, sh, name, (1, 1, 13, 23), cloth=_cloth(ctx, "shield"))
    return sh.tex(grain=0.02)


for _p in PATTERNS:
    register(f"entity/banner/{_p}", (lambda p: lambda ctx: banner_pattern(ctx, p))(_p))
    register(f"entity/shield/{_p}", (lambda p: lambda ctx: shield_pattern(ctx, p))(_p))


# ------------------------------------------------------------------ bases

POLE = pal("3a2814", "54391d", "6b4a27", "805a31", "94693a", "a6793f")
SHIELD_WOOD = pal("4a3418", "684a24", "80602e", "947038", "a68042", "b8904e")
RIM = pal("2e2e34", "55555e", "7e7e88", "a6a6b0", "cfcfd8")


def banner_base(ctx):
    """Pole, crossbar and a plain cloth flag (the flag is covered by the base layer)."""
    sh = Sheet(ctx)
    c, h = wood_field(ctx, POLE, salt="pole", along="y", board_px=99, seam=False)
    for faces in (sh.faces(44, 0, 2, 42, 2),):
        for name, r in faces.items():
            m = sh.rect(r)
            sh.put(m, c, height=h, smooth=0.3, porosity=0.2)
            if name in ("right", "front", "left", "back"):
                sh.shade(frame(ctx, r, 1, "r") & m, 0.82)
    c2, h2 = wood_field(ctx, POLE, salt="bar", along="x", board_px=99, seam=False)
    for name, r in sh.faces(0, 42, 20, 2, 2).items():
        m = sh.rect(r)
        sh.put(m, c2, height=h2, smooth=0.3, porosity=0.2)
        sh.shade(frame(ctx, r, 1, "b") & m, 0.82)
        if name in ("front", "back"):
            for ex in (r[0], r[2] - 1):
                sh.put(ctx.rect(ex, r[1], ex + 1, r[3]) > 0.5, RIM[2], height=0.7, metal=IRON, smooth=0.6)
    # Flag cloth: neutral light fabric (base layer tints over it).
    cloth = _cloth(ctx, "bb")
    for name, r in sh.faces(0, 0, 20, 40, 1).items():
        sh.put(sh.rect(r), gray(cloth * 0.95), height=0.5, smooth=0.08, sss=0.15)
    return sh.tex(grain=0.03)


def _shield(ctx, plain):
    sh = Sheet(ctx)
    plate = sh.faces(0, 0, 12, 22, 1)
    c, h = wood_field(ctx, SHIELD_WOOD, salt="shield", along="y", board_px=4)
    rim_c = ctx.palette(RIM[1:-1], ctx.noise(2, 1, salt="rim") * 0.6 + 0.2)
    for name, r in plate.items():
        m = sh.rect(r)
        sh.put(m, c, height=h, smooth=0.28, porosity=0.2)
        if name in ("front", "back"):
            ring = frame(ctx, r, 1) & m
            sh.put(ring, rim_c, height=0.75, metal=IRON, smooth=0.6, porosity=0)
            sh.shade(frame(ctx, r, 1, "tl") & m, 1.15)
            sh.shade(frame(ctx, r, 1, "br") & m, 0.8)
        else:
            sh.put(m, rim_c, height=0.7, metal=IRON, smooth=0.6, porosity=0)
    front = plate["front"]
    x0, y0, x1, y1 = front
    if plain:
        # Iron boss and cross straps on the bare shield.
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        strap = ((ctx.rect(cx - 1, y0, cx + 1, y1) + ctx.rect(x0, cy - 1, x1, cy + 1)) > 0) & sh.rect(front)
        sh.put(strap, rim_c * 0.9, height=0.65, metal=IRON, smooth=0.55, porosity=0)
        boss = ctx.rect(cx - 2, cy - 2, cx + 2, cy + 2) > 0.5
        sh.put(boss, rim_c, height=0.9, metal=IRON, smooth=0.65, porosity=0)
        sh.shade(ctx.rect(cx - 2, cy - 2, cx + 2, cy - 1) + ctx.rect(cx - 2, cy - 1, cx - 1, cy + 2), 1.25)
        sh.shade(ctx.rect(cx + 1, cy - 1, cx + 2, cy + 2) + ctx.rect(cx - 1, cy + 1, cx + 1, cy + 2), 0.75)
        for rx, ry in ((x0 + 1.5, y0 + 1.5), (x1 - 1.5, y0 + 1.5), (x0 + 1.5, y1 - 1.5), (x1 - 1.5, y1 - 1.5)):
            sh.put(ctx.rect(rx - 0.5, ry - 0.5, rx + 0.5, ry + 0.5) > 0.5, RIM[3], height=0.85, metal=IRON)
    else:
        # Patterned shield: the face is a flat panel under the dye layers.
        inner = ctx.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1) > 0.5
        sh.shade(inner, 0.95)
    # Handle.
    hc, hh = wood_field(ctx, POLE, salt="handle", along="x", board_px=99, seam=False)
    for name, r in sh.faces(26, 0, 2, 6, 6).items():
        m = sh.rect(r)
        sh.put(m, hc * 0.9, height=hh, smooth=0.3)
        sh.bevel(r, 1.1, 0.8)
    return sh.tex(grain=0.04)


register("entity/banner/banner_base", banner_base)
register("entity/shield/shield_base", lambda ctx: _shield(ctx, False))
register("entity/shield/shield_base_nopattern", lambda ctx: _shield(ctx, True))
