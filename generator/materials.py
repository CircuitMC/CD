"""Reusable material builders. Each returns a Tex for the given Ctx.

Conventions (see docs/STYLE.md):
  * light comes from the top-left; raised parts are lighter on their
    top/left edges and darker bottom/right,
  * height: 0 = deepest crevice, 1 = highest bump, 0.5 = neutral surface,
  * palettes go dark -> light,
  * everything tiles unless stated otherwise.
"""
import numpy as np

from .engine import Tex, blur, pal, smoothstep

# --------------------------------------------------------------- palettes
STONE = pal("5b5b5e", "68686b", "737376", "7e7e81", "89898c", "959598")
DEEPSLATE = pal("2b2b30", "35353b", "3f3f45", "4a4a50", "55555b", "616167")
DIRT = pal("5c3f2a", "6b4b33", "79563b", "866144", "936d4e", "a07a59")
SAND = pal("c9b783", "d4c28e", "ddcb98", "e4d3a2", "eadbad", "f0e3b8")
RED_SAND = pal("9f4e1d", "ab5822", "b6622a", "c06c31", "c97739", "d28243")
SNOW = pal("dfe7ee", "e7eef4", "eef3f8", "f4f8fb", "fbfcfe")
MOSS = pal("3f5b24", "4b6a2b", "597b32", "678c3a", "759b43")
GRASS_SIDE = np.array([0.50, 0.70, 0.31], np.float32)  # fallback green baked in grass_block_side


def lerp(a, b, t):
    t = np.asarray(t, np.float32)
    if np.ndim(a) and np.ndim(t) == 2:
        t = t[..., None]
    return a + (b - a) * t


# --------------------------------------------------------------- rock & soil

def rock(ctx, p=STONE, cell=8, contrast=0.75, streaks=4, salt="", smooth=0.18, porosity=0.12):
    """Generic stone: mid-scale mottling + a few chipped grooves."""
    n = ctx.noise(cell, 3, 0.55, salt=f"rock{salt}")
    g = ctx.texel_noise(f"rock{salt}")
    v = n * contrast + g * (1 - contrast)
    height = 0.45 + n * 0.25 + g * 0.08
    color = ctx.palette(p[1:-1], v)
    rng = ctx.rng(f"streak{salt}")
    for _ in range(streaks):
        x, y = rng.integers(0, ctx.w), rng.integers(0, ctx.h)
        length = rng.integers(2, 5)
        groove = ctx.segment(x, y + 0.5, x + length, y + 0.5 + rng.choice([-1, 0, 0, 1]), 1.0)
        groove = _wrap_mask(ctx, groove, x, y)
        lip = np.roll(groove, -ctx.s, 0) * (1 - groove)
        color = np.where(groove[..., None] > 0, p[0], color)
        color = np.where(lip[..., None] > 0, p[-1], color)
        height = np.where(groove > 0, 0.15, np.where(lip > 0, height + 0.1, height))
    return Tex(ctx, color, height=height, smooth=smooth, porosity=porosity)


def _wrap_mask(ctx, m, x, y):
    """Shapes drawn near the right/bottom border also appear on the opposite side."""
    out = m.copy()
    if x > ctx.w - 6:
        out = np.maximum(out, np.roll(m, -ctx.w * ctx.s, 1))
    return out


def layered(ctx, p, stretch=4, salt="", bands=0, smooth=0.15):
    """Horizontally compressed layers (deepslate, sandstone, basalt sides when rotated)."""
    n = ctx.noise(4, 3, 0.5, salt=f"lay{salt}", stretch=(stretch, 1))
    g = ctx.texel_noise(f"lay{salt}")
    v = n * 0.8 + g * 0.2
    height = 0.4 + n * 0.3
    color = ctx.palette(p[1:], v)
    if bands:
        rng = ctx.rng(f"band{salt}")
        for _ in range(bands):
            y0 = rng.integers(0, ctx.h)
            x0 = rng.integers(0, ctx.w)
            length = rng.integers(3, 7)
            m = ctx.rect(x0, y0, x0 + length, y0 + 1)
            m = np.maximum(m, ctx.rect(x0 - ctx.w, y0, x0 + length - ctx.w, y0 + 1))
            color = np.where(m[..., None] > 0, p[0], color)
            height = np.where(m > 0, 0.15, height)
    return Tex(ctx, color, height=height, smooth=smooth, porosity=0.1)


def soil(ctx, p=DIRT, salt="", pebbles=6, porosity=0.6):
    """Dirt-like: fine grain with light pebbles and dark pores."""
    n = ctx.noise(4, 2, 0.6, salt=f"soil{salt}")
    g = ctx.texel_noise(f"soil{salt}")
    v = n * 0.45 + g * 0.55
    color = ctx.palette(p[1:-1], v)
    height = 0.4 + v * 0.25
    rng = ctx.rng(f"pebble{salt}")
    for i in range(pebbles):
        x, y = rng.integers(0, ctx.w), rng.integers(0, ctx.h)
        m = ctx.organic(ctx.rect(x, y, x + 1, y + 1), 0.3, f"pb{i}").astype(np.float32)
        sh = ctx.organic(ctx.rect(x + 1, y + 1, x + 2, y + 2), 0.3, f"ps{i}").astype(np.float32) * (1 - m)
        color = np.where(m[..., None] > 0, lerp(p[-1], np.array([0.62, 0.58, 0.52]), 0.5), color)
        color = np.where(sh[..., None] > 0, p[0], color)
        height = np.where(m > 0, 0.85, np.where(sh > 0, 0.2, height))
    pores = ctx.organic(ctx.texel_noise(f"pore{salt}", soft=False) > 0.94, 0.4, f"pore{salt}")
    color = np.where(pores[..., None], p[0], color)
    height = np.where(pores, 0.15, height)
    return Tex(ctx, color, height=height, smooth=0.05, porosity=porosity)


def granular(ctx, p, salt="", dark=None, light=None, smooth=0.08, porosity=1.0):
    """Sand-like: very fine, low contrast, with sparse specks."""
    n = ctx.noise(8, 3, 0.5, salt=f"gr{salt}")
    g = ctx.texel_noise(f"gr{salt}")
    v = n * 0.5 + g * 0.5
    color = ctx.palette(p[1:-1], v)
    height = 0.45 + g * 0.2 + n * 0.1
    r = ctx.texel_noise(f"speck{salt}", soft=False)
    if dark is not None:
        color = np.where((r < 0.05)[..., None], dark, color)
        height = np.where(r < 0.05, 0.3, height)
    if light is not None:
        color = np.where((r > 0.97)[..., None], light, color)
        height = np.where(r > 0.97, 0.7, height)
    return Tex(ctx, color, height=height, smooth=smooth, porosity=porosity)


def pebbles(ctx, colors, count, min_dist, gap, salt="", edge=0.8, bevel=0.32, smooth=0.2):
    """Rounded stones packed together (cobblestone, gravel, rubble)."""
    vo = ctx.voronoi(count, salt=f"peb{salt}", min_dist=min_dist)
    rng = ctx.rng(f"pebc{salt}")
    tones = np.stack([colors[rng.integers(0, len(colors))] for _ in vo["points"]])
    jitter = rng.uniform(0.92, 1.08, len(vo["points"])).astype(np.float32)
    border = vo["f2"] - vo["f1"]
    inside = smoothstep(edge * 0.6, edge * 1.4, border) if not ctx.pixel_art else (border > edge).astype(np.float32)
    dome = np.clip(border / 3.0, 0, 1) ** 0.6
    light = np.clip(-(vo["dx"] + vo["dy"]) / 5.0, -1, 1)
    grain = ctx.texel_noise(f"pebg{salt}")
    f = jitter[vo["id"]] * (1 + light * bevel) * (0.94 + grain * 0.12)
    color = tones[vo["id"]] * f[..., None]
    color = lerp(gap, color, inside)
    height = 0.15 + inside * (0.35 + dome * 0.5)
    return Tex(ctx, np.clip(color, 0, 1), height=height, smooth=smooth, porosity=0.15)


def overgrow(ctx, tex, amount=0.6, p=MOSS, salt="moss"):
    """Patches of moss over an existing Tex."""
    n = ctx.noise(8, 2, 0.5, salt=salt) + ctx.texel_noise(salt) * 0.15
    m = n > amount
    t = np.clip((n - amount) / (1.15 - amount), 0, 1) * 0.7 + ctx.texel_noise(salt + "c") * 0.3
    tex.color = np.where(m[..., None], ctx.palette(p, t), tex.color)
    tex.height = np.where(m, np.maximum(tex.height, 0.6 + t * 0.2), tex.height)
    tex.porosity = np.where(m, 0.0, tex.porosity)
    tex.sss = np.where(m, 0.35, tex.sss)
    tex.smooth = np.where(m, 0.05, tex.smooth)
    return tex


# --------------------------------------------------------------- masonry

def masonry(ctx, courses, fill, mortar, bevel=True, mortar_w=1.0, salt=""):
    """Block/brick layout.

    courses: list of (height_texels, [seam_x, ...]) from top to bottom; each
    course is a row of blocks split at the given x positions (texels).
    fill: Tex used for the block faces (its color/height are reused).
    mortar: RGB (or palette) for joints.
    Returns (Tex, block_id) where block_id numbers each block.
    """
    joint = ctx.zeros()
    block_id = np.zeros((ctx.H, ctx.W), np.int32)
    lit = ctx.zeros()
    dark = ctx.zeros()
    y0, bid = 0, 0
    for ch, seams in courses:
        row = ctx.rect(0, y0, ctx.w, y0 + ch)
        joint = np.maximum(joint, ctx.rect(0, y0 + ch - mortar_w, ctx.w, y0 + ch))
        seams = sorted(s % ctx.w for s in seams)
        for sx in seams:
            joint = np.maximum(joint, ctx.rect(sx, y0, sx + mortar_w, y0 + ch) * row)
        edges = [0] + seams + [ctx.w]
        for a, b in zip(edges[:-1], edges[1:]):
            m = ctx.rect(a, y0, b, y0 + ch) > 0
            block_id[m] = bid
            bid += 1
        if bevel:
            lit = np.maximum(lit, ctx.rect(0, y0, ctx.w, y0 + 1) * row)
            for sx in seams:
                lit = np.maximum(lit, ctx.rect(sx + mortar_w, y0, sx + mortar_w + 1, y0 + ch))
            dark = np.maximum(dark, ctx.rect(0, y0 + ch - mortar_w - 1, ctx.w, y0 + ch - mortar_w))
            for sx in seams:
                dark = np.maximum(dark, ctx.rect(sx - 1, y0, sx, y0 + ch))
        y0 += ch
    # Blocks wrapping across the left/right border share an id.
    if (block_id[:, 0] != block_id[:, -1]).any():
        for y in range(ctx.H):
            a, b = block_id[y, -1], block_id[y, 0]
            if joint[y, -1] < 0.5 and joint[y, 0] < 0.5:
                block_id[y][block_id[y] == a] = b
    tex = fill.copy()
    rng = ctx.rng(f"mas{salt}")
    tone = rng.uniform(-0.06, 0.06, bid + 1).astype(np.float32)
    tex.color = np.clip(tex.color * (1 + tone[block_id])[..., None], 0, 1)
    tex.color = np.where(lit[..., None] > 0, np.clip(tex.color * 1.12, 0, 1), tex.color)
    tex.color = np.where(dark[..., None] > 0, tex.color * 0.86, tex.color)
    mcol = mortar if np.ndim(mortar) == 1 else ctx.palette(mortar, ctx.texel_noise("mortar"))
    tex.color = np.where(joint[..., None] > 0, mcol, tex.color)
    tex.height = np.where(joint > 0, 0.12, np.clip(tex.height * 0.5 + 0.45 + lit * 0.08 - dark * 0.05, 0, 1))
    tex.porosity = np.where(joint > 0, 0.5, tex.porosity)
    return tex, block_id


def running_bond(rows, row_h, brick_w, width=16):
    """Courses for a classic offset brick wall."""
    return [(row_h, list(range((brick_w // 2) * (i % 2), width, brick_w))) for i in range(rows)]


def bordered_panel(ctx, p, inset=0, salt="", smooth=0.3):
    """Flat slab with a raised bevel frame (smooth stone, polished blocks)."""
    n = ctx.noise(8, 2, 0.5, salt=f"pan{salt}")
    color = ctx.palette(p[1:-1], n * 0.7 + ctx.texel_noise(f"pan{salt}") * 0.3)
    top = ctx.rect(inset, inset, ctx.w - inset, inset + 1) + ctx.rect(inset, inset, inset + 1, ctx.h - inset)
    bot = ctx.rect(inset, ctx.h - inset - 1, ctx.w - inset, ctx.h - inset) + \
        ctx.rect(ctx.w - inset - 1, inset, ctx.w - inset, ctx.h - inset)
    color = np.where((top > 0)[..., None], p[-1], color)
    color = np.where((bot > 0)[..., None] & ~(top > 0)[..., None], p[0], color)
    height = 0.5 + n * 0.05 + np.clip(top, 0, 1) * 0.15 - np.clip(bot, 0, 1) * 0.25
    return Tex(ctx, color, height=height, smooth=smooth, porosity=0.05)


# --------------------------------------------------------------- wood

def planks(ctx, p, boards=4, salt="", knots=1):
    """Horizontal boards with seams, butt joints and streaky grain."""
    bh = ctx.h / boards
    grain = ctx.noise(4, 3, 0.55, salt=f"grain{salt}", stretch=(4, 1))
    fine = ctx.noise(1, 1, 0.5, salt=f"fine{salt}", stretch=(8, 1))
    rng = ctx.rng(f"planks{salt}")
    v = grain * 0.7 + fine * 0.2 + ctx.texel_noise(f"pl{salt}") * 0.1
    seam = ctx.zeros()
    joint = ctx.zeros()
    lip = ctx.zeros()
    prev = None
    tone = ctx.zeros()
    for b in range(boards):
        y0 = b * bh
        jx = int(rng.integers(0, ctx.w))
        while prev is not None and abs(jx - prev) < 5:
            jx = int(rng.integers(0, ctx.w))
        prev = jx
        row = ctx.rect(0, y0, ctx.w, y0 + bh)
        tone += row * rng.uniform(-0.1, 0.1)
        seam = np.maximum(seam, ctx.rect(0, y0 + bh - 1, ctx.w, y0 + bh))
        joint = np.maximum(joint, ctx.rect(jx, y0, jx + 1, y0 + bh - 1))
        lip = np.maximum(lip, ctx.rect((jx + 1) % ctx.w, y0, (jx + 1) % ctx.w + 1, y0 + bh - 1))
    v = np.clip(v + tone, 0, 1)
    color = ctx.palette(p[1:], v)
    cut = np.maximum(seam, joint)
    color = np.where(cut[..., None] > 0, p[0], color)
    color = np.where((lip > 0)[..., None] & ~(cut > 0)[..., None], p[-1], color)
    height = np.where(cut > 0, 0.1, 0.5 + grain * 0.15 + fine * 0.05 + lip * 0.05)
    for _ in range(knots):
        kx, ky = rng.uniform(1, ctx.w - 2), (int(rng.integers(0, boards)) + 0.5) * bh - 0.5
        k = ctx.circle(kx, ky, 0.9)
        color = np.where(k[..., None] > 0, lerp(p[0], p[1], 0.5), color)
        height = np.where(k > 0, 0.35, height)
    return Tex(ctx, color, height=height, smooth=0.25, porosity=0.2)


def bark(ctx, p, salt="", fissures=5, style="ridged"):
    """Log side. style: 'ridged' (vertical furrows) or 'banded' (birch-like)."""
    if style == "banded":
        n = ctx.noise(8, 2, 0.5, salt=f"bark{salt}")
        v = n * 0.6 + ctx.texel_noise(f"bark{salt}") * 0.4
        color = ctx.palette(p[1:], v)
        height = 0.6 + n * 0.1
        rng = ctx.rng(f"lent{salt}")
        for _ in range(7):
            x, y = rng.integers(0, ctx.w), rng.integers(0, ctx.h)
            m = ctx.rect(x, y, x + rng.integers(2, 6), y + 1)
            m = np.maximum(m, np.roll(m, -ctx.w * ctx.s, 1) if x > ctx.w - 6 else m)
            color = np.where(m[..., None] > 0, p[0], color)
            height = np.where(m > 0, 0.2, height)
        return Tex(ctx, color, height=height, smooth=0.1, porosity=0.3)
    cols = ctx.lattice_noise(2, ctx.h, f"cols{salt}")
    streak = ctx.noise(2, 2, 0.5, salt=f"str{salt}", stretch=(1, 4))
    v = cols * 0.45 + streak * 0.4 + ctx.texel_noise(f"bk{salt}") * 0.15
    color = ctx.palette(p, v)
    height = 0.35 + cols * 0.4 + streak * 0.2
    rng = ctx.rng(f"fis{salt}")
    for _ in range(fissures):
        x, y = int(rng.integers(0, ctx.w)), int(rng.integers(0, ctx.h))
        length = int(rng.integers(3, 8))
        m = ctx.rect(x, y, x + 1, y + length)
        m = np.maximum(m, ctx.rect(x, y - ctx.h, x + 1, y + length - ctx.h))
        color = np.where(m[..., None] > 0, p[0], color)
        height = np.where(m > 0, 0.05, height)
    return Tex(ctx, color, height=height, smooth=0.08, porosity=0.35)


def end_grain(ctx, rings, rim, salt="", rim_w=1, ring_scale=0.75):
    """Log top: concentric rings with a bark rim. rings: 2+ alternating colors."""
    dx, dy = ctx.x - ctx.w / 2, ctx.y - ctx.h / 2
    d = np.maximum(np.abs(dx), np.abs(dy)) * 0.55 + np.hypot(dx, dy) * 0.45
    wob = ctx.noise(4, 2, 0.5, salt=f"ring{salt}")
    r = d * ring_scale + wob * 0.9
    idx = np.floor(r).astype(np.int32) % len(rings)
    color = np.asarray(rings)[idx]
    if not ctx.pixel_art:
        frac = (r - np.floor(r))[..., None]
        nxt = np.asarray(rings)[(idx + 1) % len(rings)]
        color = lerp(color, nxt, smoothstep(0.7, 1.0, frac[..., 0]) * ctx.smooth_t)
    color = color * (0.96 + ctx.texel_noise(f"eg{salt}")[..., None] * 0.08)
    pith = d < 1.2
    color = np.where(pith[..., None], np.asarray(rings)[0] * 0.85, color)
    height = 0.5 + (idx % 2) * 0.04
    edge = (ctx.x < rim_w) | (ctx.x >= ctx.w - rim_w) | (ctx.y < rim_w) | (ctx.y >= ctx.h - rim_w)
    rimc = ctx.palette(rim, ctx.texel_noise(f"rim{salt}"))
    color = np.where(edge[..., None], rimc, color)
    height = np.where(edge, 0.6, height)
    return Tex(ctx, np.clip(color, 0, 1), height=height, smooth=0.2, porosity=0.25)


def stripped(ctx, p, salt=""):
    """Debarked log side: long vertical grain."""
    g = ctx.lattice_noise(2, ctx.h, f"sg{salt}")
    f = ctx.noise(1, 2, 0.5, salt=f"sf{salt}", stretch=(1, 4))
    v = g * 0.55 + f * 0.3 + ctx.texel_noise(f"st{salt}") * 0.15
    return Tex(ctx, ctx.palette(p, v), height=0.5 + g * 0.1 + f * 0.05, smooth=0.3, porosity=0.2)


def leaves(ctx, low=0.42, high=0.82, count=14, gap=0.55, holes=0.75, salt="", tint=True, color=None):
    """Leaf clusters with see-through gaps.

    tint=True -> grayscale (biome colored in game). Otherwise multiply by color.
    Transparent texels keep a dark RGB: Fast graphics shows it through gaps.
    """
    vo = ctx.voronoi(count, salt=f"leaf{salt}", min_dist=2.4)
    border = vo["f2"] - vo["f1"]
    hole = (border < gap) & (ctx.texel_noise(f"hole{salt}", soft=False) < holes)
    light = np.clip(-(vo["dx"] + vo["dy"]) / 4, -1, 1)
    t = np.clip(0.5 + light * 0.25 + (ctx.texel_noise(f"lv{salt}") - 0.5) * 0.3, 0, 1)
    lv = ctx.quantize(low + (high - low) * t, 6) if ctx.pixel_art else low + (high - low) * t
    rgb = np.repeat(lv[..., None], 3, -1)
    if not tint and color is not None:
        rgb = rgb * color / max(1e-3, float(np.mean(color))) * 0.55
    rgb = np.where(hole[..., None], 0.22, rgb)
    alpha = np.where(hole, 0.0, 1.0)
    height = np.clip(border / 2.5, 0, 1) * 0.6 + 0.3
    return Tex(ctx, np.clip(rgb, 0, 1), alpha=alpha, height=height, smooth=0.35, sss=0.6, f0=0.03)


# --------------------------------------------------------------- metals & gems

def metal_block(ctx, p, metal_id=None, salt="", rivets=False, smooth=0.75):
    """Solid metal storage block: brushed surface with a beveled frame."""
    brush = ctx.noise(1, 2, 0.5, salt=f"brush{salt}", stretch=(8, 1))
    n = ctx.noise(8, 2, 0.5, salt=f"met{salt}")
    v = 0.55 + (brush - 0.5) * 0.25 + (n - 0.5) * 0.3
    tex = bordered_panel(ctx, p, salt=salt, smooth=smooth)
    inner = ctx.rect(1, 1, ctx.w - 1, ctx.h - 1) > 0
    tex.color = np.where(inner[..., None], ctx.palette(p[1:-1], v), tex.color)
    tex.height = np.where(inner, 0.55 + brush * 0.03, tex.height)
    if rivets:
        for cx, cy in ((2.5, 2.5), (ctx.w - 2.5, 2.5), (2.5, ctx.h - 2.5), (ctx.w - 2.5, ctx.h - 2.5)):
            r = ctx.circle(cx, cy, 0.8) > 0
            tex.color = np.where(r[..., None], p[-1], tex.color)
            tex.height = np.where(r, 0.9, tex.height)
    tex.smooth = ctx.full(smooth) - brush * 0.1
    if metal_id:
        tex.set_metal(ctx.full(1), metal_id)
    tex.porosity = ctx.zeros()
    return tex


def gem_block(ctx, p, salt="", smooth=0.85, f0=0.17):
    """Cut-gem storage block: faceted tiles."""
    vo = ctx.voronoi(7, salt=f"gem{salt}", min_dist=4)
    facet = np.clip(-(vo["dx"] * 0.7 + vo["dy"]) / 4 + 0.5, 0, 1)
    tex = bordered_panel(ctx, p, salt=salt, smooth=smooth)
    inner = ctx.rect(1, 1, ctx.w - 1, ctx.h - 1) > 0
    edge = (vo["f2"] - vo["f1"]) < 0.5
    col = ctx.palette(p[1:], facet * 0.8 + ctx.texel_noise(f"gm{salt}") * 0.2)
    col = np.where(edge[..., None], p[1], col)
    tex.color = np.where(inner[..., None], col, tex.color)
    tex.height = np.where(inner, 0.5 + facet * 0.2 - edge * 0.2, tex.height)
    tex.smooth = ctx.full(smooth)
    tex.f0 = ctx.full(f0)
    return tex


def blobs(ctx, count, size_range, salt="", margin=1, spacing=2):
    """Chunky texel clusters (ore veins, spots). Returns list of sets of (x, y) texels."""
    rng = ctx.rng(f"blob{salt}")
    taken, out = set(), []
    n4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for _ in range(count * 80):
        if len(out) == count:
            break
        x, y = int(rng.integers(margin, ctx.w - margin)), int(rng.integers(margin, ctx.h - margin))
        if any((x + a, y + b) in taken for a in range(-spacing, spacing + 1) for b in range(-spacing, spacing + 1)):
            continue
        blob = {(x, y)}
        target = int(rng.integers(size_range[0], size_range[1] + 1))
        for _ in range(200):
            if len(blob) >= target:
                break
            frontier = sorted({(bx + a, by + b) for bx, by in blob for a, b in n4} - blob)
            weights = np.array([sum((fx + a, fy + b) in blob for a, b in n4) ** 2 for fx, fy in frontier], float)
            fx, fy = frontier[rng.choice(len(frontier), p=weights / weights.sum())]
            if margin <= fx < ctx.w - margin and margin <= fy < ctx.h - margin and not any(
                    (fx + a, fy + b) in taken for a in (-1, 0, 1) for b in (-1, 0, 1)):
                blob.add((fx, fy))
        out.append(blob)
        taken |= blob
    return out


def texel_mask(ctx, cells):
    m = np.zeros((ctx.h, ctx.w), bool)
    for x, y in cells:
        m[y % ctx.h, x % ctx.w] = True
    return m[ctx.ty % ctx.h, ctx.tx % ctx.w]


def ore(ctx, host, p, salt="", count=7, size=(4, 6), spacing=1, smooth=0.5, f0=0.04, metal_id=None, glow=0.0):
    """Mineral clusters embedded in a host rock Tex. p = (shadow, body, highlight)."""
    tex = host.copy()
    shadow_m = np.zeros((ctx.H, ctx.W), bool)
    for bi, blob in enumerate(blobs(ctx, count, size, salt=f"ore{salt}", spacing=spacing)):
        bm = ctx.organic(texel_mask(ctx, blob), 0.3, f"ore{salt}{bi}")
        sh = ctx.s
        cast = (np.roll(bm, sh, 1) | np.roll(bm, sh, 0) | np.roll(np.roll(bm, sh, 0), sh, 1)) & ~bm
        shadow_m |= cast
        top = texel_mask(ctx, {(x, y) for x, y in blob if (x, y - 1) not in blob and
                               ((x - 1, y) not in blob or (x + 1, y) in blob)})
        bot = texel_mask(ctx, {(x, y) for x, y in blob if (x, y + 1) not in blob or (x + 1, y) not in blob})
        col = np.where(top[..., None], p[2], np.where(bot[..., None], p[0], p[1]))
        if not ctx.pixel_art:  # facet sparkle inside each texel at high res
            spark = ctx.noise(0.5, 1, salt=f"spk{salt}")
            col = col * (0.9 + spark[..., None] * 0.2)
        tex.color = np.where(bm[..., None], col, tex.color)
        tex.height = np.where(bm, 0.7 + top * 0.2, tex.height)
        tex.smooth = np.where(bm, smooth, tex.smooth)
        tex.f0 = np.where(bm, f0, tex.f0)
        tex.porosity = np.where(bm, 0.0, tex.porosity)
        if metal_id:
            tex.metal = np.where(bm, metal_id, tex.metal)
        if glow:
            tex.emissive = np.where(bm, glow, tex.emissive)
    tex.color = np.where(shadow_m[..., None], tex.color * 0.72, tex.color)
    tex.height = np.where(shadow_m, tex.height * 0.7, tex.height)
    return tex


# --------------------------------------------------------------- misc

def grayscale(ctx, tex, lo=0.0, hi=1.0):
    """Convert a Tex to grayscale for biome-tinted textures, remapped to lo..hi."""
    lum = tex.color @ np.array([0.3, 0.59, 0.11], np.float32)
    lum = lo + (hi - lo) * _norm(lum)
    tex.color = np.repeat(lum[..., None], 3, -1)
    return tex


def _norm(a):
    lo, hi = float(a.min()), float(a.max())
    return (a - lo) / (hi - lo) if hi > lo else a * 0


def soft_blur(ctx, a, texels=0.5):
    return blur(a, max(1, ctx.s * texels))
