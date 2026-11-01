"""Shared helpers for the block_stone work area (rock variants, masonry, carving, ores,
spikes, crystals). Only used by block/stone_*.py, terrain.py, ores.py and masonry.py."""
import numpy as np

from ...engine import Tex, blur, hexc, pal, smoothstep
from ...materials import lerp, rock, texel_mask


def ramp(dark, light, n=6, warm=0.0):
    """Palette of n shades between two hex colors (highlights shifted slightly warm)."""
    a, b = hexc(dark), hexc(light)
    t = np.linspace(0, 1, n, dtype=np.float32)[:, None]
    p = a * (1 - t) + b * t
    if warm:
        p = p + np.array([warm, warm * 0.4, -warm], np.float32) * (t - 0.5)
    return np.clip(p, 0, 1)


def mul(p, f):
    return np.clip(np.asarray(p, np.float32) * f, 0, 1)


def wrapped_rect(ctx, x0, y0, x1, y1):
    """Rectangle mask that wraps around the tile borders (x1/y1 may exceed w/h)."""
    xx = (ctx.x - x0) % ctx.w
    yy = (ctx.y - y0) % ctx.h
    return ((xx < (x1 - x0)) & (yy < (y1 - y0))).astype(np.float32)


# ------------------------------------------------------------------ surface detail

def speckle(ctx, tex, color, density, salt, height=None, size=1, smooth=None):
    """Scatter 1-texel (or small) specks of `color` over a Tex."""
    r = ctx.texel_noise(f"spk{salt}", soft=False) < density
    if size > 1:
        rr = r.copy()
        rr |= np.roll(r, ctx.s, 1) & (ctx.texel_noise(f"spk2{salt}", soft=False) < 0.6)
        rr |= np.roll(r, ctx.s, 0) & (ctx.texel_noise(f"spk3{salt}", soft=False) < 0.4)
        r = rr
    m = ctx.organic(r.astype(np.float32), 0.3, f"sp{salt}") if not ctx.pixel_art else r
    c = np.asarray(color, np.float32)
    tex.color = np.where(m[..., None], c if c.ndim == 1 else c, tex.color)
    if height is not None:
        tex.height = np.where(m, height, tex.height)
    if smooth is not None:
        tex.smooth = np.where(m, smooth, tex.smooth)
    return m


def pits(ctx, tex, density, salt, dark_f=0.6, lit_f=1.15):
    """Small holes: dark texel with a lit lip below/right (porous stone)."""
    r = ctx.texel_noise(f"pit{salt}", soft=False) < density
    m = ctx.organic(r.astype(np.float32), 0.3, f"pit{salt}")
    lip = np.roll(m, ctx.s, 0) & ~m
    tex.color = np.where(m[..., None], tex.color * dark_f, tex.color)
    tex.color = np.where(lip[..., None], np.clip(tex.color * lit_f, 0, 1), tex.color)
    tex.height = np.where(m, 0.15, tex.height)
    return m


def cracks(ctx, tex, n, color, salt, length=(5, 9), width=0.8, x_range=None):
    """Jagged random-walk cracks (cracked bricks/tiles)."""
    rng = ctx.rng(f"crk{salt}")
    m = np.zeros((ctx.H, ctx.W), bool)
    for _ in range(n):
        x = float(rng.integers(0, ctx.w)) if x_range is None else float(rng.integers(*x_range))
        y = float(rng.integers(0, ctx.h))
        dx0 = rng.choice([-1, 1])
        for _ in range(int(rng.integers(*length))):
            nx, ny = x + rng.choice([dx0, 0, dx0, -dx0], p=[0.4, 0.3, 0.2, 0.1]), y + rng.choice([0, 1, 1])
            seg = ctx.segment(x + 0.5, y + 0.5, nx + 0.5, ny + 0.5, width) > 0
            seg |= ctx.segment(x + 0.5 - ctx.w, y + 0.5, nx + 0.5 - ctx.w, ny + 0.5, width) > 0
            seg |= ctx.segment(x + 0.5 + ctx.w, y + 0.5, nx + 0.5 + ctx.w, ny + 0.5, width) > 0
            seg |= ctx.segment(x + 0.5, y + 0.5 - ctx.h, nx + 0.5, ny + 0.5 - ctx.h, width) > 0
            m |= seg
            x, y = nx, ny
    lip = np.roll(m, ctx.s, 0) & ~m
    tex.color = np.where(m[..., None], color, tex.color)
    tex.color = np.where(lip[..., None], np.clip(tex.color * 1.1, 0, 1), tex.color)
    tex.height = np.where(m, 0.05, tex.height)
    return m


def carve(ctx, tex, mask, depth=0.78, shadow=0.62, light=1.18):
    """Engrave `mask` into the surface: recessed floor, shadowed top/left inner wall,
    lit bottom/right inner wall."""
    m = mask > 0.5
    tl = ctx.edge(m, 1, "tl") > 0
    br = (ctx.edge(m, 1, "br") > 0) & ~tl
    tex.color = np.where(m[..., None], tex.color * depth, tex.color)
    tex.color = np.where(tl[..., None], tex.color * shadow / depth, tex.color)
    tex.color = np.where(br[..., None], np.clip(tex.color * light, 0, 1), tex.color)
    tex.color = np.clip(tex.color, 0, 1)
    tex.height = np.where(m, np.where(tl, 0.12, 0.25), tex.height)
    return tex


def emboss(ctx, tex, mask, lit=1.18, dark=0.7, cast=0.8, height=0.75):
    """Raise `mask`: lit top/left rim, dark bottom/right rim, small cast shadow."""
    m = mask > 0.5
    tl = ctx.edge(m, 1, "tl") > 0
    br = (ctx.edge(m, 1, "br") > 0) & ~tl
    sh = ctx.s
    out = (np.roll(m, sh, 0) | np.roll(m, sh, 1)) & ~m
    tex.color = np.where(tl[..., None], np.clip(tex.color * lit, 0, 1), tex.color)
    tex.color = np.where(br[..., None], tex.color * dark, tex.color)
    tex.color = np.where(out[..., None], tex.color * cast, tex.color)
    tex.height = np.where(m, height, np.where(out, tex.height * 0.8, tex.height))
    return tex


def frame(ctx, tex, x0, y0, x1, y1, lit, dark, width=1, height=0.15):
    """Bevel frame on rectangle [x0,x1)x[y0,y1): lit top/left, dark bottom/right."""
    top = (ctx.rect(x0, y0, x1, y0 + width) + ctx.rect(x0, y0, x0 + width, y1)) > 0
    bot = ((ctx.rect(x0, y1 - width, x1, y1) + ctx.rect(x1 - width, y0, x1, y1)) > 0) & ~top
    tex.color = np.where(top[..., None], lit, tex.color)
    tex.color = np.where(bot[..., None], dark, tex.color)
    tex.height = np.where(top, np.minimum(1, tex.height + height), tex.height)
    tex.height = np.where(bot, np.maximum(0, tex.height - height * 1.5), tex.height)
    return tex


# ------------------------------------------------------------------ masonry

def blocks(ctx, rects, fill, joint, lit=1.13, dark=0.84, tone=0.06, salt="", mortar_w=1,
           joint_height=0.12, bevel=True):
    """Arbitrary block layout. rects: (x0, y0, w, h) cells (wrapping); each cell's last
    `mortar_w` column/row is joint. Returns (Tex, cell_id, joint_mask)."""
    tex = fill.copy()
    cid = np.full((ctx.H, ctx.W), -1, np.int32)
    lit_m = np.zeros((ctx.H, ctx.W), bool)
    dark_m = np.zeros((ctx.H, ctx.W), bool)
    for i, (x0, y0, w, h) in enumerate(rects):
        inner = wrapped_rect(ctx, x0, y0, x0 + w - mortar_w, y0 + h - mortar_w) > 0
        cid[inner] = i
        if bevel:
            lit_m |= inner & ((wrapped_rect(ctx, x0, y0, x0 + w - mortar_w, y0 + 1) > 0) |
                              (wrapped_rect(ctx, x0, y0, x0 + 1, y0 + h - mortar_w) > 0))
            dark_m |= inner & ((wrapped_rect(ctx, x0, y0 + h - mortar_w - 1, x0 + w - mortar_w, y0 + h - mortar_w) > 0) |
                               (wrapped_rect(ctx, x0 + w - mortar_w - 1, y0, x0 + w - mortar_w, y0 + h - mortar_w) > 0))
    dark_m &= ~lit_m
    jm = cid < 0
    rng = ctx.rng(f"blk{salt}")
    tones = rng.uniform(-tone, tone, len(rects) + 1).astype(np.float32)
    tex.color = np.clip(tex.color * (1 + tones[cid])[..., None], 0, 1)
    tex.color = np.where(lit_m[..., None], np.clip(tex.color * lit, 0, 1), tex.color)
    tex.color = np.where(dark_m[..., None], tex.color * dark, tex.color)
    jc = np.asarray(joint, np.float32)
    if jc.ndim == 2 and jc.shape[0] != ctx.H:
        jc = ctx.palette(jc, ctx.texel_noise(f"jnt{salt}"))
    tex.color = np.where(jm[..., None], jc, tex.color)
    tex.height = np.where(jm, joint_height,
                          np.clip(tex.height * 0.5 + 0.45 + lit_m * 0.08 - dark_m * 0.06, 0, 1))
    tex.porosity = np.where(jm, np.maximum(tex.porosity, 0.4), tex.porosity)
    return tex, cid, jm


def bond(rows, row_h, brick_w, offset=None, width=16, y0=0):
    """Running bond rects."""
    offset = brick_w // 2 if offset is None else offset
    out = []
    for r in range(rows):
        sx = (offset * r) % brick_w
        for x in range(sx, sx + width, brick_w):
            out.append((x, y0 + r * row_h, brick_w, row_h))
    return out


def grid(nx, ny, w=16, h=16):
    cw, ch = w // nx, h // ny
    return [(i * cw, j * ch, cw, ch) for j in range(ny) for i in range(nx)]


# ------------------------------------------------------------------ ore clusters

def clusters(ctx, count, size=(3, 6), salt="", min_dist=4.2, margin=None):
    """Compact texel clusters on the torus (they may wrap across tile edges).
    Returns list of sets of (x, y) with coordinates already wrapped."""
    rng = ctx.rng(f"clu{salt}")
    w, h = ctx.w, ctx.h
    pts = []
    for _ in range(count * 400):
        if len(pts) >= count:
            break
        if margin is None:
            p = (int(rng.integers(0, w)), int(rng.integers(0, h)))
        else:
            p = (int(rng.integers(margin, w - margin)), int(rng.integers(margin, h - margin)))
        ok = True
        for q in pts:
            dx = abs(p[0] - q[0]); dx = min(dx, w - dx)
            dy = abs(p[1] - q[1]); dy = min(dy, h - dy)
            if dx * dx + dy * dy < min_dist * min_dist:
                ok = False
                break
        if ok:
            pts.append(p)
    taken = set()
    out = []
    n8 = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]
    n4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for cx, cy in pts:
        target = int(rng.integers(size[0], size[1] + 1))
        blob = {(cx, cy)}
        for _ in range(60):
            if len(blob) >= target:
                break
            frontier = sorted({((x + a) % w, (y + b) % h) for x, y in blob for a, b in n4} - blob)
            frontier = [f for f in frontier
                        if not any(((f[0] + a) % w, (f[1] + b) % h) in taken for a, b in n8)]
            if not frontier:
                break
            wts = []
            for fx, fy in frontier:
                nb = sum(((fx + a) % w, (fy + b) % h) in blob for a, b in n8)
                ddx = min(abs(fx - cx), w - abs(fx - cx))
                ddy = min(abs(fy - cy), h - abs(fy - cy))
                wts.append((nb + 0.5) ** 3.5 / (1 + max(0, max(ddx, ddy) - 1) * 4))
            wts = np.array(wts)
            blob.add(frontier[rng.choice(len(frontier), p=wts / wts.sum())])
        out.append(blob)
        taken |= blob
    return out


def shade_cluster(blob, w, h):
    """Per texel class: 2 sparkle, 1 lit, 0 body, -1 half shadow, -2 shadow."""
    cls = {}
    for x, y in blob:
        has = lambda a, b: ((x + a) % w, (y + b) % h) in blob
        s = (not has(0, -1)) + (not has(-1, 0)) - (not has(0, 1)) - (not has(1, 0))
        cls[(x, y)] = 1 if s > 0 else (-2 if s <= -2 else (-1 if s < 0 else 0))
    # brightest texel: most top-left lit one
    lit = [k for k, v in cls.items() if v == 1] or list(cls)
    key = min(lit, key=lambda p: ((p[0] - min(q[0] for q in blob)) + (p[1] - min(q[1] for q in blob))))
    if len(blob) >= 3:
        cls[key] = 2
    return cls


def ore_clusters(ctx, host, p, salt="", count=7, size=(4, 7), min_dist=4.6, smooth=0.5, f0=0.04,
                 metal_id=None, glow=0.0, rim=0.62, height=0.78, margin=None, clusters_in=None, halo=1.0):
    """Chunky vanilla-like ore spots. p = (shadow, body, lit[, sparkle])."""
    p = np.asarray(p, np.float32)
    spark = p[3] if len(p) > 3 else np.clip(p[2] * 1.15 + 0.05, 0, 1)
    tex = host.copy()
    blobs_ = clusters_in if clusters_in is not None else clusters(ctx, count, size, salt, min_dist, margin)
    w, h = ctx.w, ctx.h
    cls_map = np.full((h, w), -9, np.int8)
    for blob in blobs_:
        for k, v in shade_cluster(blob, w, h).items():
            cls_map[k[1], k[0]] = v
    full = cls_map > -9
    # outside rim: texels below/right of the cluster (cast shadow) + faint top-left lit rim
    cast = (np.roll(full, 1, 0) | np.roll(full, 1, 1) | np.roll(np.roll(full, 1, 0), 1, 1)) & ~full
    cls_px = cls_map[ctx.ty % h, ctx.tx % w]
    inside = full[ctx.ty % h, ctx.tx % w]
    if not ctx.pixel_art:
        inside = ctx.organic(inside.astype(np.float32), 0.25, f"oc{salt}")
    cast_px = cast[ctx.ty % h, ctx.tx % w] & ~inside
    if halo != 1.0:
        hal = (np.roll(full, -1, 0) | np.roll(full, -1, 1)) & ~full & ~cast
        hal_px = hal[ctx.ty % h, ctx.tx % w] & ~inside
        tex.color = np.where(hal_px[..., None], np.clip(tex.color * halo, 0, 1), tex.color)
    col = np.where((cls_px == 2)[..., None], spark,
                   np.where((cls_px == 1)[..., None], p[2],
                            np.where((cls_px == -2)[..., None], p[0],
                                     np.where((cls_px == -1)[..., None], (p[0] + p[1] * 2) / 3, p[1]))))
    if not ctx.pixel_art:
        sp = ctx.noise(0.5, 1, salt=f"ospk{salt}")
        col = col * (0.92 + sp[..., None] * 0.16)
    tex.color = np.where(inside[..., None], col, tex.color)
    tex.color = np.where(cast_px[..., None], tex.color * rim, tex.color)
    tex.height = np.where(inside, height + (cls_px >= 1) * 0.12 - (cls_px < 0) * 0.08,
                          np.where(cast_px, tex.height * 0.75, tex.height))
    tex.smooth = np.where(inside, smooth, tex.smooth)
    tex.f0 = np.where(inside, f0, tex.f0)
    tex.porosity = np.where(inside, 0.0, tex.porosity)
    if metal_id:
        tex.metal = np.where(inside, metal_id, tex.metal)
    if glow:
        tex.emissive = np.where(inside, glow, tex.emissive)
    return tex


# ------------------------------------------------------------------ simple rocks

def mottled(ctx, p, cell=6, contrast=0.6, salt="", smooth=0.2, porosity=0.1, streaks=0, oct_=3):
    """Rock without grooves by default; more control than materials.rock."""
    n = ctx.noise(cell, oct_, 0.55, salt=f"mot{salt}")
    g = ctx.texel_noise(f"mot{salt}")
    v = n * contrast + g * (1 - contrast)
    t = Tex(ctx, ctx.palette(p, v), height=0.42 + n * 0.25 + g * 0.08, smooth=smooth, porosity=porosity)
    if streaks:
        r = rock(ctx, np.concatenate([p[:1], p, p[-1:]]), cell=cell, streaks=streaks, salt=salt)
        groove = r.height <= 0.16
        t.color = np.where(groove[..., None], p[0] * 0.9, t.color)
        t.height = np.where(groove, 0.15, t.height)
    return t


def polished(ctx, p, salt="", frame_w=1, flecks=None, fleck_density=0.05, smooth=0.45, inset=0):
    """Polished stone: low-contrast smooth face, beveled frame."""
    n = ctx.noise(8, 2, 0.5, salt=f"pol{salt}")
    g = ctx.texel_noise(f"pol{salt}")
    body = p[1:-1]
    t = Tex(ctx, ctx.palette(body, n * 0.55 + g * 0.45), height=0.55 + n * 0.04, smooth=smooth,
            porosity=0.03, f0=0.04)
    if flecks is not None:
        speckle(ctx, t, flecks, fleck_density, f"pf{salt}")
    frame(ctx, t, inset, inset, ctx.w - inset, ctx.h - inset, p[-1], p[0], frame_w)
    return t


def pillar_side(ctx, p, salt="", smooth=0.4, groove_x=(2, 13)):
    """Vertical pillar: vertical grain with two fluting grooves near the sides and a
    lit/dark rim at left/right."""
    g = ctx.noise(2, 2, 0.5, salt=f"pil{salt}", stretch=(1, 6))
    v = g * 0.5 + ctx.texel_noise(f"pil{salt}") * 0.3 + 0.2
    t = Tex(ctx, ctx.palette(p[1:-1], v), height=0.55 + g * 0.05, smooth=smooth, porosity=0.04)
    for gx in groove_x:
        m = ctx.rect(gx, 0, gx + 1, ctx.h) > 0
        lip = ctx.rect(gx + 1, 0, gx + 2, ctx.h) > 0
        t.color = np.where(m[..., None], p[0], t.color)
        t.color = np.where(lip[..., None], p[-1], t.color)
        t.height = np.where(m, 0.2, t.height)
    left = ctx.rect(0, 0, 1, ctx.h) > 0
    right = ctx.rect(ctx.w - 1, 0, ctx.w, ctx.h) > 0
    t.color = np.where(left[..., None], p[-1], t.color)
    t.color = np.where(right[..., None], p[0], t.color)
    return t


def pillar_top(ctx, p, salt="", rings=(0, 2), smooth=0.4):
    """Pillar end: concentric square bevel rings."""
    t = polished(ctx, p, salt=salt, smooth=smooth)
    for r in rings[1:]:
        frame(ctx, t, r, r, ctx.w - r, ctx.h - r, p[0], p[-1], 1, height=-0.1)
    c = ctx.w / 2
    m = (np.maximum(np.abs(ctx.x - c), np.abs(ctx.y - c)) < 2.0)
    carve(ctx, t, m.astype(np.float32))
    return t


# ------------------------------------------------------------------ sprites

def spike_shape(ctx, piece, up):
    """Mask of a pointed-dripstone-like piece (cross model, 16x16).
    Pieces: base (widest), middle, frustum (tapering), tip, tip_merge."""
    y = ctx.y if not up else ctx.h - ctx.y      # distance from the attached end
    c = ctx.w / 2
    x = np.abs(ctx.x - c)
    t = np.clip(y / ctx.h, 0, 1)
    jit = (ctx.lattice_noise(16, 5, "spw") - 0.5) * 0.5
    profiles = {"base": (6.2, 5.0, 1.0), "middle": (5.0, 4.0, 0.6), "frustum": (4.0, 2.0, 0.3)}
    if piece in profiles:
        a, b, j = profiles[piece]
        half = a + (b - a) * t + jit * j
    elif piece == "tip":
        half = 2.0 * np.clip(1 - y / 13.0, 0, 1) ** 0.9
        half = np.where(y > 12, 0, np.maximum(half, 0.5))
    elif piece == "tip_merge":
        # a hanging tip and a rising tip touching in the middle
        half = 0.55 + np.abs(y - 8) / 8 * 1.45
    else:
        raise ValueError(piece)
    if ctx.pixel_art:
        # integer widths per row (odd widths lean left) so tapers step 1 texel at a time
        W = np.round(np.maximum(half, 0) * 2)
        left = c - np.ceil(W / 2)
        return ((ctx.x >= left) & (ctx.x < left + W)).astype(np.float32)
    return (x < np.maximum(half, 0.0)).astype(np.float32)


def spike_tex(ctx, piece, up, p, salt="", smooth=0.35, f0=0.04, ridges=True, glow=0.0):
    m = spike_shape(ctx, piece, up) > 0.5
    c = ctx.w / 2
    rel = (ctx.x - c)
    band = ctx.noise(3, 2, 0.5, salt=f"spb{salt}", stretch=(0.5, 3))
    v = 0.55 - rel * 0.07 + (band - 0.5) * 0.4 + (ctx.texel_noise(f"spt{salt}") - 0.5) * 0.15
    if ridges:
        rings = (np.floor(ctx.y + ctx.lattice_noise(4, 4, f"rg{salt}") * 2) % 4 == 0)
        v = np.where(rings, v - 0.18, v)
    col = ctx.palette(p[1:], np.clip(v, 0, 1))
    edge = ctx.edge(m.astype(np.float32), 1) > 0
    # outline only on the sides, not at the cut ends (pieces stack)
    side = edge & ~(ctx.rect(0, 0, ctx.w, 1) > 0) & ~(ctx.rect(0, ctx.h - 1, ctx.w, ctx.h) > 0)
    side_r = side & (ctx.x > c)
    col = np.where(side[..., None], p[1], col)
    col = np.where(side_r[..., None], p[0], col)
    d = ctx.distance(m.astype(np.float32), 3)
    return Tex(ctx, col, alpha=m.astype(np.float32), height=np.where(m, 0.4 + np.clip(d / 3, 0, 1) * 0.4, 0),
               smooth=smooth, f0=f0, emissive=np.where(m, glow, 0), wrap=False, porosity=0.05)


def crystal_cross(ctx, p, shards, outline=None, smooth=0.85, f0=0.1, glow=0.0, sss=0.0):
    """Cutout cross sprite made of upright crystal shards growing from the bottom edge.
    shards: list of (base_x, base_half_width, height, lean)."""
    out_c = ctx.zeros()
    shade = ctx.zeros()
    alpha = np.zeros((ctx.H, ctx.W), bool)
    order = np.zeros((ctx.H, ctx.W), np.float32)
    for i, (bx, hw, ht, lean) in enumerate(shards):
        y0 = ctx.h
        tipx, tipy = bx + lean, y0 - ht
        pts = [(bx - hw, y0), (bx - hw * 0.9 + lean * 0.6, y0 - ht * 0.72), (tipx, tipy),
               (bx + hw * 0.9 + lean * 0.6, y0 - ht * 0.72), (bx + hw, y0)]
        m = ctx.polygon(pts) > 0
        # facet: left half lit, right half dark, center ridge highlight
        axis_x = bx + lean * (y0 - ctx.y) / max(ht, 1)
        f = np.where(ctx.x < axis_x, 0.75, 0.38)
        ridge = np.abs(ctx.x - axis_x) < 0.5
        f = np.where(ridge, 0.95, f)
        f = f + (ctx.y - tipy) / max(ht, 1) * -0.15
        new = m & ~alpha
        over = m
        shade = np.where(over, f, shade)
        alpha |= m
        e = ctx.edge(m.astype(np.float32), 1) > 0
        out_c = np.where(over, e.astype(np.float32), out_c)
    col = ctx.palette(p[1:], np.clip(shade, 0, 1))
    oc = p[0] if outline is None else outline
    col = np.where((out_c > 0)[..., None], oc, col)
    return Tex(ctx, col, alpha=alpha.astype(np.float32), height=np.where(alpha, 0.4 + shade * 0.4, 0),
               smooth=smooth, f0=f0, emissive=np.where(alpha, glow, 0), sss=sss, wrap=False, grain=0.03)
