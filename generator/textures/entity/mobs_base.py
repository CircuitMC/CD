"""Shared painter for mob skins (entity_mobs work area).

A `Skin` knows the model's UV boxes (from mobs_layouts.LAYOUTS) and paints
them face by face with `Mat` materials:

  * every face gets an *elevation* field (1 = top of the creature in the world,
    0 = underside), so fur / skin is lighter on top and darker underneath even
    on quadruped bodies whose box is rotated 90 degrees;
  * mottling, per-texel grain and optional blotch patterns come from noise
    fields computed once over the whole image (they continue across faces);
  * small features (eyes, noses, stripes...) are painted in *face-local model
    texels* with `frect` / `stamp` and mirrored with `sym`.

Model texture sizes may differ from the image size (e.g. a 64x32 model on a
128x64 image): boxes and features are scaled by `k` automatically.
"""
import numpy as np

from ...engine import Tex, hexc
from .mobs_layouts import LAYOUTS

SIDES = ("front", "back", "left", "right")
FACE_OFF = dict(top=0.08, bottom=-0.12, front=0.0, back=-0.03, right=-0.02, left=-0.02)
QUAD_ROLE = dict(back="top", front="bottom", top="front", bottom="back", left="left", right="right")


def col(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def shades(base, n=5, lo=0.62, hi=1.22, warm=0.035):
    """Dark -> light palette around a base color (cool shadows, warm highlights)."""
    c = col(base)
    out = []
    for i in range(n):
        t = i / (n - 1)
        f = lo + (hi - lo) * t
        cc = c * f if f <= 1 else c + (1 - c) * (f - 1) * 0.9
        s = (t - 0.5) * warm
        out.append(np.clip(cc + np.array([s, s * 0.35, -s]), 0, 1))
    return np.stack(out).astype(np.float32)


def mix(a, b, t):
    return col(a) * (1 - t) + col(b) * t


class Mat:
    """Surface material: palette + noise character + PBR values.

    p: palette (array dark->light) or a base color string (expanded with `shades`).
    blotch: optional (palette2, threshold, which_noise) second color patches.
    """

    def __init__(self, p, mottle=0.25, grain=0.22, grad=0.3, base=0.55, streak=0.0, sss=0.3,
                 smooth=0.12, f0=0.04, metal=None, emissive=0.0, porosity=0.0, relief=0.3,
                 alpha=1.0, blotch=None, n=5, lo=0.7, hi=1.18):
        self.p = shades(p, n, lo, hi) if isinstance(p, str) or np.ndim(p) == 1 else np.asarray(p, np.float32)
        self.mottle, self.grain, self.grad, self.base, self.streak = mottle, grain, grad, base, streak
        self.sss, self.smooth, self.f0, self.metal, self.emissive = sss, smooth, f0, metal, emissive
        self.porosity, self.relief, self.alpha = porosity, relief, alpha
        self.blotch = None
        if blotch:
            p2, thr, key = (blotch + ("big",))[:3]
            self.blotch = (shades(p2, n, lo, hi) if isinstance(p2, str) or np.ndim(p2) == 1
                           else np.asarray(p2, np.float32), thr, key)

    def but(self, **kw):
        m = Mat.__new__(Mat)
        m.__dict__ = dict(self.__dict__)
        for k, v in kw.items():
            if k == "p" and (isinstance(v, str) or np.ndim(v) == 1):
                v = shades(v)
            setattr(m, k, v)
        return m


class Box:
    __slots__ = ("part", "idx", "u", "v", "w", "h", "d", "rot", "faces", "quad")

    def __repr__(self):
        return f"Box({self.part}#{self.idx} {self.u},{self.v} {self.w}x{self.h}x{self.d})"


def box_rects(u, v, w, h, d):
    return {
        "top": (u + d, v, u + d + w, v + d),
        "bottom": (u + d + w, v, u + d + 2 * w, v + d),
        "right": (u, v + d, u + d, v + d + h),
        "front": (u + d, v + d, u + d + w, v + d + h),
        "left": (u + d + w, v + d, u + 2 * d + w, v + d + h),
        "back": (u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h),
    }


class Skin:
    def __init__(self, ctx, model=None, salt=""):
        self.ctx = ctx
        H, W = ctx.H, ctx.W
        self.color = np.zeros((H, W, 3), np.float32)
        self.alpha = np.zeros((H, W), np.float32)
        self.height = np.zeros((H, W), np.float32)
        self.smooth = np.zeros((H, W), np.float32)
        self.f0 = np.full((H, W), 0.04, np.float32)
        self.sss = np.zeros((H, W), np.float32)
        self.emissive = np.zeros((H, W), np.float32)
        self.porosity = np.zeros((H, W), np.float32)
        self.metal = np.zeros((H, W), np.float32)
        self.k = 1.0
        self.boxes = []
        if model:
            (tw, th), raw = LAYOUTS[model]
            self.k = ctx.w / tw
            count = {}
            for part, u, v, w, h, d, rot in raw:
                b = Box()
                b.part, b.rot = part, rot
                b.idx = count.get(part, 0)
                count[part] = b.idx + 1
                k = self.k
                b.u, b.v, b.w, b.h, b.d = u * k, v * k, w * k, h * k, d * k
                b.faces = {f: r for f, r in box_rects(b.u, b.v, b.w, b.h, b.d).items()
                           if r[2] > r[0] and r[3] > r[1]}
                b.quad = rot <= -80
                self.boxes.append(b)
        s = f"{salt}"
        self.noise = {
            "mid": ctx.noise(2.5, 2, 0.5, salt=f"mid{s}"),
            "big": ctx.noise(6, 2, 0.55, salt=f"big{s}"),
            "small": ctx.noise(1.5, 2, 0.5, salt=f"small{s}"),
            "streak": ctx.noise(1.2, 2, 0.5, salt=f"str{s}", stretch=(0.7, 3.0)),
        }
        self.grain = ctx.texel_noise(f"grain{s}")

    # ------------------------------------------------------------ lookup
    def find(self, key, idx=None):
        """Boxes whose part equals key or starts with key (key may be a tuple)."""
        keys = (key,) if isinstance(key, str) else key
        out = [b for b in self.boxes if any(b.part == k or b.part.startswith(k) for k in keys)]
        if idx is not None:
            out = [b for b in out if b.idx == idx]
        return out

    def box(self, key, idx=0):
        for b in self.boxes:
            if (b.part == key or b.part.startswith(key)) and b.idx == idx:
                return b
        for b in self.boxes:
            if key in b.part and b.idx == idx:
                return b
        return None

    def largest(self, key):
        bs = self.find(key)
        return max(bs, key=lambda b: b.w * b.h * max(b.d, 1)) if bs else None

    # ------------------------------------------------------------ low level
    def _sl(self, x0, y0, x1, y1):
        s, ctx = self.ctx.s, self.ctx
        X0 = int(round(max(0, x0) * s)); Y0 = int(round(max(0, y0) * s))
        X1 = int(round(min(ctx.w, x1) * s)); Y1 = int(round(min(ctx.h, y1) * s))
        if X1 <= X0 or Y1 <= Y0:
            return None
        return np.s_[Y0:Y1, X0:X1]

    def _write(self, sl, color, mat=None, height=None, alpha=1.0, smooth=None, sss=None, emissive=None,
               f0=None, metal=None, mask=None):
        m = mat
        if mask is None:
            mask = np.ones(self.alpha[sl].shape, bool)
        def put(arr, val):
            sub = arr[sl]
            sub[mask] = np.broadcast_to(val, sub.shape)[mask] if np.ndim(val) else val
        cs = self.color[sl]
        cs[mask] = np.broadcast_to(color, cs.shape)[mask]
        put(self.alpha, alpha)
        put(self.height, 0.5 if height is None else height)
        put(self.smooth, smooth if smooth is not None else (m.smooth if m else 0.15))
        put(self.sss, sss if sss is not None else (m.sss if m else 0.0))
        put(self.emissive, emissive if emissive is not None else (m.emissive if m else 0.0))
        put(self.f0, f0 if f0 is not None else (m.f0 if m else 0.04))
        put(self.porosity, m.porosity if m else 0.0)
        mt = metal if metal is not None else (m.metal if m and m.metal else 0)
        put(self.metal, mt)

    def elev(self, b, face, X, Y):
        x0, y0, x1, y1 = b.faces[face]
        fx = np.clip((X - x0) / max(x1 - x0, 1e-6), 0, 1)
        fy = np.clip((Y - y0) / max(y1 - y0, 1e-6), 0, 1)
        if b is None or not b.quad:
            if face == "top":
                return np.ones_like(X)
            if face == "bottom":
                return np.zeros_like(X)
            return 1 - fy
        return {"back": np.ones_like(X), "front": np.zeros_like(X), "top": 1 - fy,
                "bottom": np.full_like(X, 0.5), "right": 1 - fx, "left": fx}[face]

    def fill(self, rect, mat, elev=None, off=0.0, mask=None):
        sl = self._sl(*rect)
        if sl is None:
            return
        X, Y = self.ctx.x[sl], self.ctx.y[sl]
        e = np.full(X.shape, 0.5, np.float32) if elev is None else elev(X, Y)
        nz = self.noise["streak"][sl] * mat.streak + self.noise["mid"][sl] * (1 - mat.streak)
        g = self.grain[sl]
        v = mat.base + off + (e - 0.5) * mat.grad + (nz - 0.5) * mat.mottle + (g - 0.5) * mat.grain
        c = self.ctx.palette(mat.p, v)
        if mat.blotch is not None:
            p2, thr, key = mat.blotch
            bm = self.noise[key][sl] > thr
            c = np.where(bm[..., None], self.ctx.palette(p2, v), c)
        h = np.clip(0.5 + (v - mat.base) * mat.relief, 0.05, 0.95)
        m = None if mask is None else mask[sl] > 0.5
        self._write(sl, c, mat, height=h, alpha=mat.alpha, mask=m)

    # ------------------------------------------------------------ boxes
    def paint(self, b, mat, faces=None, off=0.0):
        if b is None:
            return
        for f, rect in b.faces.items():
            if faces is not None and f not in faces:
                continue
            role = QUAD_ROLE[f] if b.quad else f
            self.fill(rect, mat, elev=lambda X, Y, f=f: self.elev(b, f, X, Y), off=off + FACE_OFF[role])

    def paint_all(self, mats, default=None, skip=()):
        """mats: list of (key, Mat) matched against part names in order ('#n' selects box n)."""
        for b in self.boxes:
            if any(b.part.startswith(s) for s in skip):
                continue
            m = default
            for key, mm in mats:
                k, _, i = key.partition("#")
                if (b.part == k or b.part.startswith(k)) and (not i or int(i) == b.idx):
                    m = mm
                    break
            if m is not None:
                self.paint(b, m)

    def band(self, b, y0, y1, mat, faces=SIDES, bottom=False, top=False, off=0.0):
        """Horizontal band across side faces, y in model texels from the face top
        (negative = from the bottom edge)."""
        if b is None:
            return
        k = self.k
        for f in faces:
            if f not in b.faces:
                continue
            x0, fy0, x1, fy1 = b.faces[f]
            a = fy0 + y0 * k if y0 >= 0 else fy1 + y0 * k
            z = fy0 + y1 * k if y1 > 0 else fy1 + y1 * k
            role = QUAD_ROLE[f] if b.quad else f
            self.fill((x0, a, x1, z), mat, elev=lambda X, Y, f=f: self.elev(b, f, X, Y), off=off + FACE_OFF[role])
        if bottom and "bottom" in b.faces:
            self.fill(b.faces["bottom"], mat, off=off - 0.1)
        if top and "top" in b.faces:
            self.fill(b.faces["top"], mat, off=off + 0.08)

    # ------------------------------------------------------------ features
    def frect_xy(self, b, face, fx0, fy0, fx1, fy1):
        x0, y0, x1, y1 = b.faces[face]
        k = self.k
        ax = lambda f: x0 + f * k if f >= 0 else x1 + f * k
        ay = lambda f: y0 + f * k if f >= 0 else y1 + f * k
        bx = lambda f: x0 + f * k if f > 0 else x1 + f * k
        by = lambda f: y0 + f * k if f > 0 else y1 + f * k
        return ax(fx0), ay(fy0), bx(fx1), by(fy1)

    def frect(self, b, face, fx0, fy0, fx1, fy1, c, mat=None, **kw):
        """Paint a rectangle in face-local model texels. Negative coords count from the
        right / bottom edge (fx1 = 0 means the far edge). c: color, or a Mat for textured fill."""
        if b is None or face not in b.faces:
            return
        r = self.frect_xy(b, face, fx0, fy0, fx1, fy1)
        if isinstance(c, Mat):
            self.fill(r, c, off=kw.get("off", 0.0))
            return
        self.rect(*r, c, mat=mat, **kw)

    def sym(self, b, face, fx0, fy0, fx1, fy1, c, **kw):
        """frect plus its left-right mirror on the same face."""
        if b is None or face not in b.faces:
            return
        x0, y0, x1, y1 = b.faces[face]
        wm = (x1 - x0) / self.k
        self.frect(b, face, fx0, fy0, fx1, fy1, c, **kw)
        self.frect(b, face, wm - fx1, fy0, wm - fx0, fy1, c, **kw)

    def rect(self, x0, y0, x1, y1, c, mat=None, height=None, alpha=1.0, smooth=None, sss=None,
             emissive=None, f0=None, metal=None, jitter=0.0):
        sl = self._sl(x0, y0, x1, y1)
        if sl is None:
            return
        cc = col(c)
        if jitter:
            g = (self.grain[sl] - 0.5) * jitter
            cc = np.clip(cc + g[..., None], 0, 1)
        self._write(sl, cc, mat, height=height, alpha=alpha, smooth=smooth, sss=sss, emissive=emissive,
                    f0=f0, metal=metal)

    def stamp(self, b, face, fx, fy, rows, colors, mirror=False, **kw):
        """Hand-drawn texel map in face-local model texels; '.'/' ' = skip.
        colors: char -> color or (color, dict(height=..., emissive=...)). mirror=True also
        stamps the horizontally flipped map at the mirrored position."""
        if b is None or face not in b.faces:
            return
        x0, y0, x1, y1 = b.faces[face]
        k = self.k
        wm = (x1 - x0) / k
        maps = [(fx, rows)]
        if mirror:
            mw = max(len(r) for r in rows)
            maps.append((wm - fx - mw, [r.ljust(mw)[::-1] for r in rows]))
        for ox, rr in maps:
            for j, row in enumerate(rr):
                for i, ch in enumerate(row):
                    if ch in ". " or ch not in colors:
                        continue
                    spec = colors[ch]
                    extra = dict(kw)
                    if isinstance(spec, tuple) and len(spec) == 2 and isinstance(spec[1], dict):
                        spec, more = spec
                        extra.update(more)
                    X = x0 + (ox + i) * k
                    Y = y0 + (fy + j) * k
                    if isinstance(spec, Mat):
                        self.fill((X, Y, X + k, Y + k), spec)
                    else:
                        self.rect(X, Y, X + k, Y + k, spec, **extra)

    def shade_rect(self, x0, y0, x1, y1, f):
        """Multiply existing color in a rect (darken < 1 / lighten > 1)."""
        sl = self._sl(x0, y0, x1, y1)
        if sl is not None:
            self.color[sl] = np.clip(self.color[sl] * f, 0, 1)

    def tint(self, b, face, fx0, fy0, fx1, fy1, f):
        if b is None or face not in b.faces:
            return
        self.shade_rect(*self.frect_xy(b, face, fx0, fy0, fx1, fy1), f)

    def clear(self, rect):
        sl = self._sl(*rect)
        if sl is not None:
            self.alpha[sl] = 0
            self.emissive[sl] = 0

    def spots(self, rect, c, thr, key="mid", height=None, emissive=None, mat=None):
        """Recolor where a noise field exceeds thr inside rect (patterns, moss, cracks)."""
        sl = self._sl(*rect)
        if sl is None:
            return
        m = (self.noise[key][sl] > thr) & (self.alpha[sl] > 0.5)
        if isinstance(c, Mat):
            v = c.base + (self.grain[sl] - 0.5) * c.grain + (self.noise["mid"][sl] - 0.5) * c.mottle
            cc = self.ctx.palette(c.p, v)
            self._write(sl, cc, c, height=height, mask=m, emissive=emissive)
        else:
            self._write(sl, col(c), mat, height=height, mask=m, emissive=emissive)

    def face_spots(self, b, mat_or_color, thr, key="mid", faces=None):
        if b is None:
            return
        for f, r in b.faces.items():
            if faces is None or f in faces:
                self.spots(r, mat_or_color, thr, key)

    # ------------------------------------------------------------ output
    def tex(self, grain=0.05, normal_strength=1.0):
        a = self.alpha
        t = Tex(self.ctx, self.color, alpha=a, height=np.where(a > 0.5, self.height, 0.0), smooth=self.smooth,
                f0=self.f0, porosity=self.porosity, sss=np.where(a > 0.5, self.sss, 0.0),
                emissive=np.where(a > 0.5, self.emissive, 0.0), normal_strength=normal_strength,
                wrap=False, grain=grain)
        for mid in np.unique(self.metal):
            if mid >= 230:
                t.set_metal((self.metal == mid).astype(np.float32), int(mid))
        return t


def head_front(sk, key="head"):
    """(box, face) of the main head box front."""
    b = sk.largest(key) if sk.find(key) else None
    return b


def eye_pair(sk, b, y, x, w=2, h=1, white="e8e4dc", pupil="1d1a22", inner=True, face="front", hgt=0.4):
    """Classic mob eyes: white + pupil, mirrored. x = distance of the eye from the face edge."""
    if b is None or face not in b.faces:
        return
    sk.sym(b, face, x, y, x + w, y + h, white, height=hgt, smooth=0.5, sss=0.0)
    if pupil is not None:
        px = x + w - 1 if inner else x
        sk.sym(b, face, px, y, px + 1, y + h, pupil, height=hgt - 0.05, smooth=0.6, sss=0.0)
