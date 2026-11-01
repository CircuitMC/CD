"""Resolution-independent texture engine.

Every generator works in *texel* coordinates (a 16x16 block is 16 texels
wide no matter the output resolution).  The same code renders:

  * scale 1   -> 16x  pixel art (palette steps, hard edges, vanilla-like)
  * scale 4   -> 64x  (finer noise octaves, softer palette blending)
  * scale 16  -> 256x
  * scale 64  -> 1024x

Random lattices are seeded from the texture name only, so large features are
identical across resolutions; higher resolutions only *add* detail.

A generator returns a `Tex` (or a list of them for animation frames). A Tex
carries color + alpha and the physical layers used for LabPBR shader maps:
height, smoothness, f0 / metal, porosity, subsurface scattering, emission.
"""
import math
import zlib

import numpy as np

# LabPBR predefined metal ids (green channel of _s maps).
IRON, GOLD, ALUMINUM, CHROME, COPPER, LEAD, PLATINUM, SILVER = range(230, 238)
ALBEDO_METAL = 255

LIGHT = np.array([-0.45, -0.55, 0.70])  # top-left light used for baked shading
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def hexc(value):
    """'#a1b2c3' / 'a1b2c3' -> float RGB array in 0..1."""
    value = value.lstrip("#")
    return np.array([int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)], dtype=np.float32)


def pal(*values):
    """Dark-to-light palette as an (N, 3) float array."""
    return np.stack([hexc(v) for v in values])


def seed_of(*parts):
    return zlib.crc32(":".join(str(p) for p in parts).encode())


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


class Ctx:
    """Rendering context handed to every generator."""

    def __init__(self, name, w, h, scale=1, frame=0, frames=1):
        self.name, self.w, self.h, self.s = name, w, h, scale
        self.W, self.H = w * scale, h * scale
        self.frame, self.frames = frame, frames
        ys, xs = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
        self.x = (xs + 0.5) / scale   # texel coordinates of pixel centers
        self.y = (ys + 0.5) / scale
        self.tx = np.floor(self.x).astype(np.int32)  # integer texel index
        self.ty = np.floor(self.y).astype(np.int32)

    # ------------------------------------------------------------ helpers
    @property
    def pixel_art(self):
        return self.s == 1

    @property
    def smooth_t(self):
        """0 at 16x, ~0.5 at 64x, 1 at 256x+: how far to move from pixel art to painterly."""
        return min(1.0, math.log2(self.s) / 4)

    def rng(self, salt=""):
        return np.random.default_rng(seed_of(self.name, salt))

    def sub(self, name):
        """Same geometry, different seed (to reuse another texture's generator)."""
        return Ctx(name, self.w, self.h, self.s, self.frame, self.frames)

    def zeros(self):
        return np.zeros((self.H, self.W), np.float32)

    def full(self, v):
        return np.full((self.H, self.W), v, np.float32)

    # ------------------------------------------------------------ noise
    def lattice_noise(self, cell_x, cell_y, salt, x=None, y=None):
        """One tileable value-noise octave. cell sizes in texels."""
        x = self.x if x is None else x
        y = self.y if y is None else y
        gx = max(1, round(self.w / cell_x))
        gy = max(1, round(self.h / cell_y))
        grid = self.rng(f"lat:{salt}:{gx}:{gy}").random((gy, gx), dtype=np.float32)
        fx, fy = x / self.w * gx - 0.5, y / self.h * gy - 0.5
        x0, y0 = np.floor(fx).astype(np.int32), np.floor(fy).astype(np.int32)
        tx, ty = fx - x0, fy - y0
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        x0m, x1m, y0m, y1m = x0 % gx, (x0 + 1) % gx, y0 % gy, (y0 + 1) % gy
        a, b = grid[y0m, x0m], grid[y0m, x1m]
        c, d = grid[y1m, x0m], grid[y1m, x1m]
        return (a + (b - a) * tx) * (1 - ty) + (c + (d - c) * tx) * ty

    def noise(self, cell=8, octaves=3, persistence=0.5, salt="", stretch=(1, 1),
              detail=True, norm=True):
        """Tileable fBm in 0..1.

        `octaves` are always rendered (cell, cell/2, ...). With detail=True,
        extra finer octaves are added while they stay >= 2 output pixels, so
        64x+ outputs gain real detail instead of upscaled blobs.
        """
        total = np.zeros((self.H, self.W), np.float32)
        amp, amp_sum, k, c = 1.0, 0.0, 0, float(cell)
        while True:
            fine = k >= octaves
            if fine and (not detail or c * self.s < 2 or c < 1 / 16):
                break
            total += self.lattice_noise(c * stretch[0], c * stretch[1], f"{salt}:{k}") * amp
            amp_sum += amp
            amp *= persistence
            c /= 2
            k += 1
        total /= amp_sum
        return self.normalize(total) if norm else total

    def texel_noise(self, salt="", soft=True):
        """Random value per texel (16x look). Above 16x, with soft=True, it becomes
        smooth noise of the same feature size plus sub-texel grain (no blocky squares)."""
        r = self.rng(f"texel:{salt}").random((self.h, self.w), dtype=np.float32)
        if self.s == 1 or not soft:
            return r[self.ty % self.h, self.tx % self.w]
        return self.noise(1, 1, 0.65, salt=f"g{salt}")

    def organic(self, mask, rough=0.35, salt=""):
        """Round off texel-aligned masks above 16x so organic shapes lose their stair steps."""
        if self.s == 1:
            return mask > 0.5
        m = blur(blur(mask.astype(np.float32), self.s * 0.5), self.s * 0.5)
        n = self.noise(0.5, 1, salt=f"org{salt}") - 0.5
        return m > 0.5 + n * rough

    @staticmethod
    def normalize(a):
        lo, hi = float(a.min()), float(a.max())
        return (a - lo) / (hi - lo) if hi > lo else np.zeros_like(a)

    def voronoi(self, count, salt="", min_dist=0.0, points=None):
        """Tileable Voronoi. Returns dict(id, f1, f2, dx, dy, points) in texel units."""
        if points is None:
            rng = self.rng(f"vor:{salt}")
            points = []
            for _ in range(count * 300):
                if len(points) >= count:
                    break
                p = (rng.uniform(0, self.w), rng.uniform(0, self.h))
                if all(self._wrapdist(p, q) >= min_dist for q in points):
                    points.append(p)
        pts = np.array(points, np.float32)
        dx = self.x[..., None] - pts[:, 0]
        dy = self.y[..., None] - pts[:, 1]
        dx = (dx + self.w / 2) % self.w - self.w / 2
        dy = (dy + self.h / 2) % self.h - self.h / 2
        d = np.sqrt(dx * dx + dy * dy)
        order = np.argsort(d, axis=-1)
        idx = order[..., 0]
        f1 = np.take_along_axis(d, order[..., :1], -1)[..., 0]
        f2 = np.take_along_axis(d, order[..., 1:2], -1)[..., 0] if len(pts) > 1 else f1 + 99
        return dict(id=idx, f1=f1, f2=f2,
                    dx=np.take_along_axis(dx, idx[..., None], -1)[..., 0],
                    dy=np.take_along_axis(dy, idx[..., None], -1)[..., 0],
                    points=pts)

    def _wrapdist(self, a, b):
        dx = abs(a[0] - b[0]); dx = min(dx, self.w - dx)
        dy = abs(a[1] - b[1]); dy = min(dy, self.h - dy)
        return math.hypot(dx, dy)

    # ------------------------------------------------------------ color
    def palette(self, p, v, dither=0.0):
        """Map 0..1 values onto a palette.

        16x: hard steps (pixel art).  Higher res: blends neighbouring entries
        progressively, keeping the same overall look with smoother gradients.
        """
        p = np.asarray(p, np.float32)
        n = len(p)
        v = np.clip(v, 0, 1) * (n - 1e-4)
        if dither:
            v = v + (self.texel_noise("dither") - 0.5) * dither
        v = np.clip(v, 0, n - 1e-4)
        i = np.floor(v).astype(np.int32)
        hard = p[i]
        if self.pixel_art:
            return hard
        t = self.smooth_t
        f = np.clip(v - 0.5, 0, n - 1)
        i0 = np.floor(f).astype(np.int32)
        i1 = np.minimum(i0 + 1, n - 1)
        frac = (f - i0)[..., None]
        soft = p[i0] * (1 - frac) + p[i1] * frac
        return hard * (1 - t) + soft * t

    def quantize(self, v, levels):
        q = np.floor(np.clip(v, 0, 0.9999) * levels) / (levels - 1)
        return q if self.pixel_art else q * (1 - self.smooth_t) + v * self.smooth_t

    # ------------------------------------------------------------ shapes
    def rect(self, x0, y0, x1, y1):
        """Mask of the texel-space rectangle [x0, x1) x [y0, y1)."""
        return ((self.x >= x0) & (self.x < x1) & (self.y >= y0) & (self.y < y1)).astype(np.float32)

    def circle(self, cx, cy, r):
        return (np.hypot(self.x - cx, self.y - cy) < r).astype(np.float32)

    def polygon(self, pts):
        """Even-odd fill of a texel-space polygon."""
        inside = np.zeros((self.H, self.W), bool)
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if y1 == y2:
                continue
            cond = (self.y >= min(y1, y2)) & (self.y < max(y1, y2))
            xint = x1 + (self.y - y1) * (x2 - x1) / (y2 - y1)
            inside ^= cond & (self.x < xint)
        return inside.astype(np.float32)

    def segment(self, x1, y1, x2, y2, width):
        """Capsule (thick line) mask, width in texels."""
        px, py = self.x - x1, self.y - y1
        bx, by = x2 - x1, y2 - y1
        t = np.clip((px * bx + py * by) / max(1e-6, bx * bx + by * by), 0, 1)
        d = np.hypot(px - bx * t, py - by * t)
        return (d < width / 2).astype(np.float32)

    def texels(self, rows, colors, x0=0, y0=0):
        """Stamp a small hand-drawn texel map (list of strings) at (x0, y0).

        Characters index into `colors` (dict char -> RGB or None for skip).
        Returns (rgb, mask). Each map texel covers scale x scale pixels.
        """
        rgb = np.zeros((self.H, self.W, 3), np.float32)
        mask = self.zeros()
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                col = colors.get(ch)
                if col is None:
                    continue
                m = (self.tx == x0 + i) & (self.ty == y0 + j)
                rgb[m] = col
                mask[m] = 1
        return rgb, mask

    def distance(self, mask, max_texels=4):
        """Approximate inside distance (texels) to the mask edge (chamfer)."""
        inside = mask > 0.5
        steps = max(1, int(max_texels * self.s))
        dist = np.where(inside, float(steps), 0).astype(np.float32)
        cur = inside.copy()
        for i in range(steps):
            er = cur & np.roll(cur, 1, 0) & np.roll(cur, -1, 0) & np.roll(cur, 1, 1) & np.roll(cur, -1, 1)
            dist[cur & ~er] = i + 0.5
            cur = er
            if not cur.any():
                break
        return np.where(inside, dist, 0) / self.s

    def edge(self, mask, width=1.0, side=None):
        """Pixels of `mask` within `width` texels of its boundary.

        side: None (all), or 'tl' / 'br' for the lit / shadowed edge only.
        """
        sh = max(1, round(width * self.s))
        m = mask > 0.5
        out = np.zeros_like(m)
        # (dy, dx) shifts that bring the top / left (or bottom / right) neighbour in.
        dirs = {"tl": [(1, 0), (0, 1)], "br": [(-1, 0), (0, -1)]}.get(
            side, [(1, 0), (0, 1), (-1, 0), (0, -1)])
        for dy, dx in dirs:
            out |= m & ~_shift(m, dy * sh, dx * sh)
        return out.astype(np.float32)


def _shift(a, dy, dx):
    """Shift without wrap; vacated cells are False (so outer borders count as edges)."""
    out = np.zeros_like(a)
    H, W = a.shape
    ys = slice(max(0, dy), H + min(0, dy)), slice(max(0, -dy), H + min(0, -dy))
    xs = slice(max(0, dx), W + min(0, dx)), slice(max(0, -dx), W + min(0, -dx))
    out[ys[0], xs[0]] = a[ys[1], xs[1]]
    return out


class Tex:
    """Color + physical layers. All arrays are (H, W[, 3]) float32."""

    def __init__(self, ctx, color, alpha=None, height=None, smooth=0.1, f0=0.04,
                 porosity=0.0, sss=0.0, emissive=0.0, normal_strength=1.0, wrap=True, grain=0.08):
        self.ctx = ctx
        self.color = np.asarray(color, np.float32)
        if self.color.ndim == 1:
            self.color = np.broadcast_to(self.color, (ctx.H, ctx.W, 3)).copy()
        self.alpha = self._field(1.0 if alpha is None else alpha)
        self.height = self._field(0.5 if height is None else height)
        self.smooth = self._field(smooth)
        self.f0 = self._field(f0)          # 0..1 linear F0, or a metal id (>= 230) via set_metal
        self.metal = ctx.zeros()            # 0 or a LabPBR metal id per pixel
        self.porosity = self._field(porosity)
        self.sss = self._field(sss)
        self.emissive = self._field(emissive)
        self.normal_strength = normal_strength
        self.wrap = wrap  # tileable surfaces use wrapped gradients for normals
        self.grain = grain  # high-res micro detail strength (0 = none, e.g. glass, GUI)

    def _field(self, v):
        return np.broadcast_to(np.asarray(v, np.float32), (self.ctx.H, self.ctx.W)).copy()

    def set_metal(self, mask, metal_id):
        self.metal = np.where(mask > 0.5, metal_id, self.metal).astype(np.float32)
        return self

    def paste(self, other, mask=None):
        """Overlay `other` where mask (default: other's alpha) is set."""
        m = (other.alpha if mask is None else mask) > 0.5
        for attr in ("alpha", "height", "smooth", "f0", "metal", "porosity", "sss", "emissive"):
            getattr(self, attr)[m] = getattr(other, attr)[m]
        self.color[m] = other.color[m]
        return self

    def copy(self):
        t = Tex.__new__(Tex)
        t.__dict__ = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in self.__dict__.items()}
        return t

    def shade(self, amount=0.35, ao=0.25):
        """Bake top-left lighting from the height map into the color (vanilla-style)."""
        n = normals(self.height, self.ctx, self.normal_strength * 1.5, self.wrap)
        lam = np.tensordot(n, LIGHT * np.array([1, 1, 1]), axes=([2], [0]))
        flat = LIGHT[2]
        light = 1 + (lam - flat) * amount * 2
        cav = cavity(self.height, self.ctx, self.wrap)
        self.color = np.clip(self.color * light[..., None] * (1 - cav * ao)[..., None], 0, 1)
        return self


def normals(height, ctx, strength=1.0, wrap=True):
    """Unit normals (H, W, 3) in image space (x right, y down, z out)."""
    h = height * 2.0  # height range spans 2 texels of relief
    if wrap or min(h.shape) < 2:  # np.gradient needs >= 2 samples per axis
        gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * ctx.s
        gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * ctx.s
    else:
        gy, gx = np.gradient(h)
        gx, gy = gx * ctx.s, gy * ctx.s
    n = np.stack([-gx * strength, -gy * strength, np.ones_like(h)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def blur(a, radius_px, wrap=True):
    """Cheap box blur (two passes) in pixels."""
    r = max(1, int(radius_px))
    out = a
    for axis in (0, 1):
        acc = np.zeros_like(out)
        for d in range(-r, r + 1):
            acc += np.roll(out, d, axis) if wrap else _shift(out, d * (axis == 0), d * (axis == 1))
        out = acc / (2 * r + 1)
    return out


def cavity(height, ctx, wrap=True):
    """0..1 occlusion amount from local height (crevices are darker)."""
    b = blur(blur(height, ctx.s * 1.0, wrap), ctx.s * 1.0, wrap)
    return np.clip((b - height) * 3.0, 0, 1)


def micro_detail(tex):
    """Above 16x, add fine surface grain so high resolutions read as more detailed,
    not just smoother. Strength is per Tex (`tex.grain`, 0 disables)."""
    ctx = tex.ctx
    if ctx.s == 1 or tex.grain <= 0:
        return
    g = ctx.noise(0.25, 2, 0.6, salt="micro") - 0.5
    k = tex.grain * ctx.smooth_t
    solid = (tex.alpha > 0.5)[..., None]
    tex.color = np.where(solid, np.clip(tex.color * (1 + g[..., None] * k * 2), 0, 1), tex.color)
    tex.height = np.clip(tex.height + g * k, 0, 1)


def encode(tex):
    """Tex -> (rgba, normal_rgba, specular_rgba) uint8 arrays following LabPBR 1.3."""
    ctx = tex.ctx
    micro_detail(tex)
    a = np.clip(tex.alpha, 0, 1)
    rgba = np.dstack([np.clip(tex.color, 0, 1), a])
    n = normals(tex.height, ctx, tex.normal_strength, tex.wrap)
    n[a < 0.5] = (0, 0, 1)
    ao = 1 - cavity(tex.height, ctx, tex.wrap) * 0.6
    nrm = np.dstack([n[..., 0] * 0.5 + 0.5, n[..., 1] * 0.5 + 0.5, ao,
                     np.clip(tex.height, 1 / 255, 1)])
    g = np.where(tex.metal >= 230, tex.metal / 255, np.clip(tex.f0, 0, 229 / 255))
    b = np.where(tex.sss > 0, (65 + np.clip(tex.sss, 0, 1) * 190) / 255,
                 np.clip(tex.porosity, 0, 1) * 64 / 255)
    em = np.where(tex.emissive > 0, np.clip(tex.emissive, 0, 1) * 254 / 255, 1.0)
    spec = np.dstack([np.clip(tex.smooth, 0, 1), g, b, em])
    to8 = lambda x: np.round(np.clip(x, 0, 1) * 255).astype(np.uint8)
    return to8(rgba), to8(nrm), to8(spec)
