"""Shared drawing kit for the block_wood area.

Canvas: a mutable set of layers (color / alpha / height / PBR) with bevel helpers,
plus wood surface builders (boards, plate bark, smooth bark, end grain, leaves)
and helpers for multi-texture objects (doors are drawn on a 16x32 canvas and cut
into top/bottom halves).
"""
import math

import numpy as np

from ...engine import Ctx, IRON, Tex, hexc, pal, smoothstep

IRON_P = pal("2c2c30", "4a4a4f", "6c6c72", "8f8f95", "b4b4b9", "d6d6da")
DARK_IRON = pal("1d1d21", "2e2e33", "414147", "56565c", "6c6c72")


def binary(m):
    return np.asarray(m) > 0.5


class Canvas:
    """Mutable texture layers with bevel/inset/cut helpers (masks are bool or 0..1)."""

    def __init__(self, ctx, color, height=0.5, smooth=0.25, porosity=0.2, f0=0.04, alpha=1.0):
        self.ctx = ctx
        H, W = ctx.H, ctx.W
        self.color = np.array(np.broadcast_to(np.asarray(color, np.float32), (H, W, 3)), np.float32)
        f = lambda v: np.array(np.broadcast_to(np.asarray(v, np.float32), (H, W)), np.float32)
        self.alpha = f(alpha)
        self.height = f(height)
        self.smooth = f(smooth)
        self.porosity = f(porosity)
        self.f0 = f(f0)
        self.metal = ctx.zeros()
        self.emissive = ctx.zeros()
        self.sss = ctx.zeros()

    def put(self, mask, color=None, height=None, dh=None, mul=None, smooth=None, porosity=None,
            f0=None, metal=None, emissive=None, alpha=None, sss=None):
        m = binary(mask)
        if color is not None:
            c = np.asarray(color, np.float32)
            self.color[m] = c[m] if c.ndim == 3 else c
        if mul is not None:
            k = np.asarray(mul, np.float32)
            self.color[m] = np.clip(self.color[m] * (k[m][..., None] if k.ndim == 2 else k), 0, 1)
        for name, v in (("height", height), ("smooth", smooth), ("porosity", porosity), ("f0", f0),
                        ("metal", metal), ("emissive", emissive), ("alpha", alpha), ("sss", sss)):
            if v is not None:
                arr = getattr(self, name)
                v = np.asarray(v, np.float32)
                arr[m] = v[m] if v.ndim == 2 else v
        if dh is not None:
            self.height[m] = np.clip(self.height[m] + dh, 0, 1)
        return self

    def raised(self, mask, lit=1.16, shade=0.74, dh=0.12, w=1.0):
        """Raised feature: lighter top/left rim, darker bottom/right rim."""
        m = binary(mask).astype(np.float32)
        c = self.ctx
        tl = binary(c.edge(m, w, "tl"))
        br = binary(c.edge(m, w, "br")) & ~tl
        self.put(m, dh=dh)
        self.put(tl, mul=lit, dh=0.04)
        self.put(br, mul=shade, dh=-0.04)
        return self

    def sunken(self, mask, shade=0.72, lit=1.1, dh=-0.14, w=1.0, body=0.92):
        """Recessed area: shadow on its inner top/left edge, light on bottom/right."""
        m = binary(mask).astype(np.float32)
        c = self.ctx
        tl = binary(c.edge(m, w, "tl"))
        br = binary(c.edge(m, w, "br")) & ~tl
        self.put(m, dh=dh, mul=body)
        self.put(tl, mul=shade, dh=-0.05)
        self.put(br, mul=lit)
        return self

    def cut(self, mask, rgb=(0.1, 0.08, 0.06)):
        m = binary(mask)
        self.alpha[m] = 0
        self.color[m] = rgb
        self.height[m] = 0
        return self

    def metal_part(self, mask, p=IRON_P, metal_id=IRON, smooth=0.6, bevel=True):
        """Shaded metal hardware (hinges, bands, handles)."""
        m = binary(mask)
        c = self.ctx
        mf = m.astype(np.float32)
        tl = binary(c.edge(mf, 1, "tl"))
        br = binary(c.edge(mf, 1, "br")) & ~tl
        n = c.noise(4, 2, salt="metalpart")
        col = c.palette(p[2:4], n)
        col = np.where(tl[..., None], p[-2], np.where(br[..., None], p[1], col)) if bevel else col
        self.put(m, color=col, height=0.75, smooth=smooth, porosity=0.0, f0=0.0, alpha=1.0)
        self.put(tl, dh=0.08)
        if metal_id:
            self.metal[m] = metal_id
        return self

    def tex(self, wrap=False, grain=0.06, normal_strength=1.0):
        t = Tex(self.ctx, np.clip(self.color, 0, 1), alpha=self.alpha, height=np.clip(self.height, 0, 1),
                smooth=self.smooth, f0=self.f0, porosity=self.porosity, sss=self.sss,
                emissive=self.emissive, wrap=wrap, grain=grain, normal_strength=normal_strength)
        t.metal = self.metal.copy()
        return t


def crop_tex(full, ctx, y0):
    """Cut texel rows [y0, y0 + ctx.h) of a Tex rendered on a taller canvas into a Tex for ctx."""
    s = ctx.s
    rows = slice(y0 * s, y0 * s + ctx.H)
    t = Tex(ctx, full.color[rows], alpha=full.alpha[rows], height=full.height[rows],
            smooth=full.smooth[rows], f0=full.f0[rows], porosity=full.porosity[rows], sss=full.sss[rows],
            emissive=full.emissive[rows], wrap=full.wrap, grain=full.grain,
            normal_strength=full.normal_strength)
    t.metal = full.metal[rows].copy()
    return t


def tall_ctx(ctx, name, h):
    return Ctx(name, ctx.w, h, ctx.s, ctx.frame, ctx.frames)


# ------------------------------------------------------------------ wood surfaces

def board_field(ctx, p, boards=4, vertical=False, salt="", joints=True, straight=0.0, contrast=1.0,
                span=None, offset=0.0, seams=True, knots=1, line_period=2.4):
    """Planks-like boards. Returns Canvas.

    p: 6-shade palette (p[0] seams, p[-1] lit joint lips). vertical=True runs the grain
    (and boards) up/down. span: board region length across the grain (default full).
    Fine grain lines appear above 16x.
    """
    span = span or (ctx.w if vertical else ctx.h)
    along_len = ctx.h if vertical else ctx.w
    a = ctx.y if vertical else ctx.x
    c = (ctx.x if vertical else ctx.y) - offset
    st = (1, 4) if vertical else (4, 1)
    bw = span / boards
    bidx = np.floor(c / bw).astype(np.int32)
    inb = c - bidx * bw  # position across inside the board
    rng = ctx.rng(f"boards{salt}")
    tones = rng.uniform(-0.09, 0.09, boards + 4).astype(np.float32)
    tone = tones[np.clip(bidx, 0, boards + 3)]
    warp = ctx.noise(4, 2, 0.5, salt=f"bw{salt}", stretch=st) * (1 - straight)
    streak = ctx.noise(2, 3, 0.55, salt=f"bs{salt}", stretch=(st[0] * 2, st[1] * 2))
    ph = rng.uniform(0, 10, boards + 4).astype(np.float32)[np.clip(bidx, 0, boards + 3)]
    q = (inb + warp * 2.6 + ph) / line_period
    fr = q - np.floor(q)
    if ctx.pixel_art:
        line = (fr < 0.34).astype(np.float32)
    else:
        line = 1 - smoothstep(0.2, 0.42, fr) + smoothstep(0.9, 1.0, fr)
        qf = q * 4
        fine = 1 - np.abs(qf - np.floor(qf) - 0.5) * 2
        line = np.clip(line + smoothstep(0.75, 1.0, fine) * 0.35 * ctx.smooth_t, 0, 1)
    tex_n = ctx.texel_noise(f"bt{salt}")
    v = 0.62 + tone + (streak - 0.5) * 0.4 * contrast - line * 0.3 * contrast + (tex_n - 0.5) * 0.12
    color = ctx.palette(p[1:], np.clip(v, 0, 1))
    height = 0.55 + (streak - 0.5) * 0.1 - line * 0.06
    cv = Canvas(ctx, color, height=height, smooth=0.28, porosity=0.2)
    if seams:
        seam = (inb >= bw - 1) & (c < span) & (c >= 0)
        cv.put(seam, color=p[0], height=0.1)
        lit = (inb < 1) & (bidx > 0) & (c < span) & (c >= 0)
        cv.put(lit & ~seam, mul=1.07)
    if joints:
        for b in range(boards):
            jx = (int(rng.integers(0, along_len)) + b * 7) % along_len
            if not vertical and boards > 1:
                jx = (jx + 5 * (b % 2)) % along_len
            j = (np.floor(a) == jx) & (bidx == b) & (inb < bw - 1)
            lip = (np.floor(a) == (jx + 1) % along_len) & (bidx == b) & (inb < bw - 1)
            cv.put(j, color=p[0], height=0.12)
            cv.put(lip, color=p[-2], dh=0.03)
    for k in range(knots):
        kb = int(rng.integers(0, boards))
        ka = rng.uniform(2, along_len - 3)
        kc = (kb + 0.5) * bw + offset - 0.5
        kx, ky = (kc, ka) if vertical else (ka, kc)
        ring = ctx.circle(kx, ky, 1.3) > 0
        core = ctx.circle(kx, ky, 0.75) > 0
        cv.put(ring & ~core, mul=0.88)
        cv.put(core, color=(p[0] + p[1]) / 2, height=0.35)
    return cv


def plates(ctx, widths=(2, 4), seglen=(4, 9), salt="", warp=1.0):
    """Tileable vertical bark plates. Returns dict(col, seg, left, right, top, bot, id)."""
    rng = ctx.rng(f"plates{salt}")
    bounds = [0]
    while bounds[-1] < ctx.w:
        bounds.append(bounds[-1] + int(rng.integers(widths[0], widths[1] + 1)))
    bounds[-1] = ctx.w
    if len(bounds) > 2 and bounds[-1] - bounds[-2] < widths[0]:
        del bounds[-2]
    bounds = np.array(bounds, np.float32)
    wv = (ctx.lattice_noise(ctx.w, 4, f"pw{salt}") - 0.5) * 2 * warp
    if ctx.pixel_art:
        wv = np.round(wv)
    else:
        wv = wv + (ctx.noise(1, 1, salt=f"pwf{salt}") - 0.5) * 0.4 * ctx.smooth_t
    u = (ctx.x + wv) % ctx.w
    col = np.clip(np.searchsorted(bounds, u, side="right") - 1, 0, len(bounds) - 2)
    left = u - bounds[col]
    right = bounds[col + 1] - u
    ncol = len(bounds) - 1
    seg = np.zeros_like(col)
    top = ctx.zeros()
    bot = ctx.zeros()
    for ci in range(ncol):
        cuts = []
        y = float(rng.integers(0, ctx.h))
        start = y
        while y < start + ctx.h:
            cuts.append(y)
            y += int(rng.integers(seglen[0], seglen[1] + 1))
        if start + ctx.h - cuts[-1] < seglen[0] and len(cuts) > 1:
            cuts.pop()
        cuts = np.array(cuts + [start + ctx.h], np.float32)
        m = col == ci
        yy = (ctx.y - start) % ctx.h + start
        si = np.clip(np.searchsorted(cuts, yy, side="right") - 1, 0, len(cuts) - 2)
        seg = np.where(m, si + ci * 32, seg)
        top = np.where(m, yy - cuts[si], top)
        bot = np.where(m, cuts[si + 1] - yy, bot)
    lut = rng.uniform(-1, 1, ncol * 32 + 32).astype(np.float32)
    tone_arr = lut[seg]
    return dict(col=col, seg=seg, left=left, right=right, top=top, bot=bot, tone=tone_arr)


def plate_bark(ctx, p, widths=(2, 4), seglen=(4, 9), salt="", furrow=1.0, warp=1.0, crack=True,
               fiber=0.35, tone_amt=0.12, furrow_color=None):
    """Ridged bark: plates separated by dark vertical furrows. p: 5+ shades dark->light."""
    pl = plates(ctx, widths, seglen, salt, warp)
    streak = ctx.noise(2, 2, 0.5, salt=f"pbs{salt}", stretch=(1, 4))
    fib = ctx.noise(0.5, 1, salt=f"pbf{salt}", stretch=(1, 6))
    g = ctx.texel_noise(f"pbg{salt}")
    v = 0.5 + pl["tone"] * tone_amt + (streak - 0.5) * 0.45 + (g - 0.5) * 0.22 + (fib - 0.5) * fiber * ctx.smooth_t
    color = ctx.palette(p[1:], np.clip(v, 0, 1))
    height = 0.6 + (streak - 0.5) * 0.15 + pl["tone"] * 0.05
    cv = Canvas(ctx, color, height=height, smooth=0.08, porosity=0.35)
    fur = pl["left"] < furrow
    lit = (pl["left"] >= furrow) & (pl["left"] < furrow + 1)
    shade = pl["right"] < 1
    cv.put(lit, mul=1.12, dh=0.05)
    cv.put(shade & ~fur, mul=0.85, dh=-0.05)
    if crack:
        cr = (pl["top"] < 1) & ~fur
        cv.put(cr, color=p[1], height=0.3)
        under = (pl["top"] >= 1) & (pl["top"] < 2) & ~fur
        cv.put(under, mul=1.06)
    cv.put(fur, color=p[0] if furrow_color is None else furrow_color, height=0.08)
    return cv


def smooth_bark(ctx, p, salt="", marks="dash", count=8, mark_color=None, light_color=None, streaky=0.5):
    """Smooth bark with horizontal lenticel dashes ('dash'), diamonds ('diamond') or
    birch-like dark patches ('patch'). p: 5+ shades (p[0] = darkest mark color)."""
    n = ctx.noise(8, 2, 0.5, salt=f"sb{salt}")
    st = ctx.noise(2, 2, 0.5, salt=f"sbs{salt}", stretch=(1, 3))
    g = ctx.texel_noise(f"sbg{salt}")
    v = 0.5 + (n - 0.5) * 0.5 + (st - 0.5) * streaky + (g - 0.5) * 0.25
    color = ctx.palette(p[1:], np.clip(v, 0, 1))
    cv = Canvas(ctx, color, height=0.6 + (n - 0.5) * 0.1, smooth=0.15, porosity=0.25)
    rng = ctx.rng(f"marks{salt}")
    mc = p[0] if mark_color is None else mark_color
    lc = p[-1] if light_color is None else light_color
    placed = []
    for i in range(count * 6):
        if len(placed) >= count:
            break
        x, y = int(rng.integers(0, ctx.w)), int(rng.integers(0, ctx.h))
        if any(abs(((x - a + ctx.w // 2) % ctx.w) - ctx.w // 2) < 3 and
               abs(((y - b + ctx.h // 2) % ctx.h) - ctx.h // 2) < 2 for a, b in placed):
            continue
        placed.append((x, y))
        for ox in (0, -ctx.w):
            for oy in (0, -ctx.h):
                X, Y = x + ox, y + oy
                if marks == "dash":
                    L = int(rng.integers(2, 5)) if ox == 0 and oy == 0 else L
                    m = ctx.rect(X, Y, X + L, Y + 1)
                    hl = ctx.rect(X, Y - 1, X + L, Y)
                elif marks == "diamond":
                    m = ctx.polygon([(X + 2, Y - 1), (X + 4.2, Y + 0.5), (X + 2, Y + 2), (X - 0.2, Y + 0.5)])
                    if ctx.pixel_art:
                        m = ctx.rect(X, Y, X + 4, Y + 1) + ctx.rect(X + 1, Y - 1, X + 3, Y + 2)
                    hl = ctx.rect(X + 1, Y + 2, X + 3, Y + 3)
                else:  # patch
                    L = int(rng.integers(2, 6)) if ox == 0 and oy == 0 else L
                    m = ctx.rect(X, Y, X + L, Y + 1) + ctx.rect(X + 1, Y + 1, X + max(2, L - 1), Y + 2) * (L > 3)
                    hl = ctx.rect(X, Y + 2, X + L, Y + 3) * 0
                cv.put(hl > 0, color=lc, dh=0.04)
                cv.put(m > 0, color=mc, height=0.3)
    return cv


def end_grain_rings(ctx, rings, rim, salt="", rim_w=1.0, ring_scale=0.55, heart=None, rim_tex=None):
    """Log top: rings (dark, light), optional heart color, bark rim palette (dark->light)."""
    dx, dy = ctx.x - ctx.w / 2, ctx.y - ctx.h / 2
    d = np.maximum(np.abs(dx), np.abs(dy)) * 0.55 + np.hypot(dx, dy) * 0.45
    wob = ctx.noise(4, 2, 0.5, salt=f"egw{salt}")
    r = d * ring_scale + wob * 0.7
    rings = np.asarray(rings, np.float32)
    fr = r - np.floor(r)
    if ctx.pixel_art:
        dark = (fr < 0.36).astype(np.float32)
    else:
        dark = 1 - smoothstep(0.26, 0.44, fr) + smoothstep(0.92, 1.0, fr)
        fine = np.abs(np.sin(r * math.pi * 5))
        dark = np.clip(dark + (fine < 0.2) * 0.3 * ctx.smooth_t, 0, 1)
    color = rings[1] + (rings[0] - rings[1]) * dark[..., None]
    color = color * (0.95 + ctx.texel_noise(f"egt{salt}")[..., None] * 0.1)
    if heart is not None:
        color = np.where((d < 2.0)[..., None], heart, color)
    color = np.where((d < 0.9)[..., None], rings[0] * 0.85, color)
    cv = Canvas(ctx, color, height=0.52 - dark * 0.04, smooth=0.22, porosity=0.25)
    edge = (ctx.x < rim_w) | (ctx.x >= ctx.w - rim_w) | (ctx.y < rim_w) | (ctx.y >= ctx.h - rim_w)
    rimc = ctx.palette(rim, ctx.texel_noise(f"egr{salt}")) if rim_tex is None else rim_tex
    cv.put(edge, color=rimc, height=0.65)
    inner = (ctx.x < rim_w + 1) | (ctx.x >= ctx.w - rim_w - 1) | (ctx.y < rim_w + 1) | (ctx.y >= ctx.h - rim_w - 1)
    cv.put(inner & ~edge, mul=0.86)
    return cv


def fiber_grain(ctx, p, salt="", vertical=True, contrast=1.0):
    """Debarked log side: long straight grain with occasional darker lines."""
    if vertical:
        g = ctx.lattice_noise(1.6, ctx.h, f"fg{salt}")
        f = ctx.noise(1, 2, 0.5, salt=f"ff{salt}", stretch=(1, 5))
        across = ctx.x
    else:
        g = ctx.lattice_noise(ctx.w, 1.6, f"fg{salt}")
        f = ctx.noise(1, 2, 0.5, salt=f"ff{salt}", stretch=(5, 1))
        across = ctx.y
    w = ctx.noise(4, 1, salt=f"fw{salt}", stretch=(1, 4) if vertical else (4, 1))
    v = 0.5 + (g - 0.5) * 0.6 * contrast + (f - 0.5) * 0.35 + (ctx.texel_noise(f"ft{salt}") - 0.5) * 0.15
    if not ctx.pixel_art:
        q = across * 3 + w * 3
        v -= (np.abs(q - np.floor(q) - 0.5) < 0.1) * 0.08 * ctx.smooth_t
    return Canvas(ctx, ctx.palette(p, np.clip(v, 0, 1)), height=0.5 + (g - 0.5) * 0.12 + (f - 0.5) * 0.06,
                  smooth=0.32, porosity=0.2)


# ------------------------------------------------------------------ leaves

def canopy(ctx, p, count=14, min_dist=2.4, gap=0.55, holes=0.75, salt="", speckle=0.05, light=0.45,
           sss=0.6, wrap=True, noise=0.18):
    """Leaf clusters with cutout gaps. p: palette dark->light (gray for tinted leaves).
    Each cluster is lit from the top-left with a darker lower-right rim."""
    vo = ctx.voronoi(count, salt=f"cn{salt}", min_dist=min_dist)
    border = vo["f2"] - vo["f1"]
    tn = ctx.texel_noise(f"cnh{salt}", soft=False)
    hole = ((border < gap) & (tn < holes)) | (tn > 1 - speckle)
    if not ctx.pixel_art:
        hole = ctx.organic(hole.astype(np.float32), 0.3, salt)
    side = vo["dx"] + vo["dy"]
    lit = np.clip(-side / 3.2, -1, 1)
    tone = ctx.rng(f"cnt{salt}").uniform(-0.08, 0.08, len(vo["points"])).astype(np.float32)[vo["id"]]
    t = 0.52 + lit * light + tone + (ctx.texel_noise(f"cnv{salt}") - 0.5) * noise * 2
    rim = (border < gap + 0.9) & (side > 0)
    t = np.where(rim, t - 0.22, t)
    t = np.where((vo["f1"] < 0.8) & (side < 0.5), t + 0.12, t)
    color = ctx.palette(p, np.clip(t, 0, 1))
    color = np.where(hole[..., None], p[0] * 0.55, color)
    height = np.clip(border / 2.5, 0, 1) * 0.5 + 0.35 + lit * 0.05
    return Tex(ctx, color, alpha=np.where(hole, 0.0, 1.0), height=np.where(hole, 0, height),
               smooth=0.35, sss=sss, f0=0.03, wrap=wrap)


def gray(lo, hi, n=6, warm=0.0):
    """Neutral gray palette for tinted textures."""
    vals = np.linspace(lo, hi, n, dtype=np.float32)
    return np.stack([np.array([v + warm, v + warm * 0.5, v], np.float32) for v in vals]).clip(0, 1)


def lerp_pal(a, b, t):
    return a + (b - a) * t


def shade_pal(rgb, n=5, lo=0.55, hi=1.25):
    c = hexc(rgb) if isinstance(rgb, str) else np.asarray(rgb, np.float32)
    return np.stack([np.clip(c * k, 0, 1) for k in np.linspace(lo, hi, n)]).astype(np.float32)
