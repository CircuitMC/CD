"""Default player skins: nine original characters, wide (4px) and slim (3px) arms.

Standard 64x64 player layout: head (0,0) 8^3, hat (32,0); body (16,16) 8x12x4,
jacket (16,32); right arm (40,16), sleeve (40,32); left arm (32,48), sleeve (48,48);
right leg (0,16), pants (0,32); left leg (16,48), pants (0,48).
Only the character names come from the game; every design here is original.
"""
import numpy as np

from ...engine import pal
from ...registry import register
from .objects_common import Sheet, ramp

SKIN = {
    "fair": "f0c8a8", "light": "e6b48e", "tan": "c99470", "olive": "b98a5e",
    "brown": "92603e", "deep": "6a4028", "dark": "4e2e1c",
}

CHARS = {
    "steve": dict(skin="tan", hair="2a1e16", style="short", eyes="3a5a8a", shirt="b0552a", shirt2="e8d8b8",
                  top="vest", sleeves="long", pants="2e3e5a", shoes="2a2420", beard=True),
    "alex": dict(skin="fair", hair="d8b860", style="braid", eyes="3e7a4a", shirt="2a3a6a", shirt2="e8e4dc",
                 top="collar", sleeves="long", pants="6a6a70", shoes="5a3a22", freckles=True),
    "ari": dict(skin="light", hair="3a2418", style="bun", eyes="5a3a20", shirt="6a3a8a", shirt2="a87ac0",
                top="sweater", sleeves="long", pants="22222a", shoes="e8e8e8"),
    "efe": dict(skin="deep", hair="161210", style="twists", eyes="3a2416", shirt="c8962a", shirt2="3a3a3a",
                top="jacket", sleeves="long", pants="4a5228", shoes="3a2a1e"),
    "kai": dict(skin="light", hair="141418", style="spiky", eyes="2a2a2a", shirt="a82a2a", shirt2="ececec",
                top="jacket", sleeves="long", pants="5a5e66", shoes="1e1e22"),
    "makena": dict(skin="dark", hair="181412", style="braids", eyes="3a2416", shirt="2a7a4a", shirt2="e0b040",
                   top="wrap", sleeves="short", pants="6a4a2e", shoes="2a1e16"),
    "noor": dict(skin="olive", hair="2a1e16", style="scarf", scarf="2a8a8a", eyes="5a4024", shirt="ddd2b8",
                 shirt2="b8a888", top="coat", sleeves="long", pants="2e2a2a", shoes="3a2a20"),
    "sunny": dict(skin="fair", hair="e888a8", style="bob", eyes="4a7ab0", shirt="f2f2ee", shirt2="6aa8d8",
                  top="overalls", sleeves="short", pants="6aa8d8", shoes="d84a3a"),
    "zuri": dict(skin="brown", hair="2a1a10", style="puff", eyes="3a2416", shirt="d8582a", shirt2="f0c040",
                 top="pattern", sleeves="short", pants="3a5a8a", shoes="f0f0f0", shorts=True),
}


def _p(hexc, spread=0.38):
    return ramp(hexc, 5, spread=spread)


class Skin:
    def __init__(self, ctx, spec):
        self.ctx, self.spec = ctx, spec
        self.sh = Sheet(ctx)
        self.skin = _p(SKIN[spec["skin"]], 0.3)
        self.hair = _p(spec["hair"], 0.5)
        self.shirt = _p(spec["shirt"])
        self.shirt2 = _p(spec["shirt2"])
        self.pants = _p(spec["pants"])
        self.shoes = _p(spec["shoes"])

    def fill(self, r, p, salt, v0=0.45, var=0.35, mask=None, sss=0.0, alpha=1.0):
        ctx = self.ctx
        m = self.sh.rect(r) if mask is None else (self.sh.rect(r) & mask)
        n = ctx.noise(3, 2, 0.5, salt=salt)
        v = v0 + (n - 0.5) * var * 0.6 + (ctx.texel_noise(salt) - 0.5) * var * 0.25
        self.sh.put(m, ctx.palette(p[1:], np.clip(v, 0, 1)), alpha=alpha, height=0.5 + n * 0.05,
                    smooth=0.15, sss=sss)
        return m

    def px(self, x, y, col, w=1, h=1):
        m = self.ctx.rect(x, y, x + w, y + h) > 0.5
        self.sh.put(m, col, height=0.55)


def _local(sk, r):
    return sk.sh.local(r)


def paint_head(sk, f, hat):
    s, ctx, sp = sk.spec, sk.ctx, sk.spec
    for n, r in f.items():
        sk.fill(r, sk.skin, "skin" + n, 0.55, 0.2, sss=0.4)
    # Hair coverage per face.
    style = sp["style"]
    hp = sk.hair
    for n, r in f.items():
        lx, ly, W, H = _local(sk, r)
        if n == "top":
            m = np.ones_like(lx, bool)
        elif n == "bottom":
            m = np.zeros_like(lx, bool)
        elif n == "back":
            depth = {"short": 6, "spiky": 6, "twists": 6, "braid": 8, "braids": 8, "bun": 7, "bob": 7,
                     "puff": 7, "scarf": 8}[style]
            m = ly < depth
        elif n in ("right", "left"):
            depth = {"short": 2, "spiky": 3, "twists": 3, "braid": 3, "braids": 7, "bun": 3, "bob": 6,
                     "puff": 3, "scarf": 8}[style]
            # side faces: hair deeper toward the back (front edge is next to the face)
            back_side = lx if n == "right" else (W - lx)   # distance from the back edge
            m = (ly < depth) | ((ly < depth + 3) & (back_side < 4) & (depth > 2))
            m |= ly < 2
        else:  # front
            if style == "short":
                m = ly < 1.5
            elif style == "spiky":
                m = (ly < 1) | ((ly < 2) & (np.floor(lx) % 2 == 0))
            elif style in ("braid", "bob"):
                m = (ly < 2) | ((ly < 3) & (lx < 4)) | ((lx < 1) | (lx >= W - 1)) & (ly < (7 if style == "bob" else 4))
            elif style == "braids":
                m = (ly < 2) | (((lx < 1) | (lx >= W - 1)) & (ly < 8))
            elif style == "scarf":
                m = (ly < 2) | (((lx < 1) | (lx >= W - 1)) & (ly < 8)) | (ly >= 7)
            else:
                m = ly < 2
        sel = sk.sh.rect(r) & m
        if style == "scarf":
            p = _p(sp["scarf"], 0.4)
            n_ = ctx.noise(2, 2, 0.5, salt="scarf")
            sk.sh.put(sel, ctx.palette(p[1:], n_ * 0.6 + 0.2), height=0.55, smooth=0.1, sss=0)
            continue
        hv = ctx.noise(2, 2, 0.5, salt="hair" + n, stretch=(1, 3))
        strand = (np.floor(ctx.x) % 2 == 0) * 0.15
        v = np.clip(hv * 0.5 + strand + ctx.texel_noise("ht" + n) * 0.25, 0, 1)
        sk.sh.put(sel, ctx.palette(hp[:-1], v), height=0.58, smooth=0.25, sss=0)
    # Face details.
    fr = f["front"]
    x0, y0 = fr[0], fr[1]
    eye = pal(sp["eyes"])[0]
    white = pal("f0eee8")[0]
    for ex in (1, 5):
        sk.px(x0 + ex, y0 + 4, white)
        sk.px(x0 + ex + 1, y0 + 4, eye)
    if sp["style"] in ("braid", "bob", "bun", "braids", "scarf", "puff"):
        sk.px(x0 + 1, y0 + 3, sk.hair[0] if sp["style"] != "scarf" else sk.hair[1])
        sk.px(x0 + 6, y0 + 3, sk.hair[0] if sp["style"] != "scarf" else sk.hair[1])
    else:
        sk.px(x0 + 1, y0 + 3, sk.hair[1], 2)
        sk.px(x0 + 5, y0 + 3, sk.hair[1], 2)
    sk.px(x0 + 3, y0 + 5, sk.skin[1], 2)        # nose shadow
    sk.px(x0 + 3, y0 + 6, sk.skin[0] * 0.85 + pal("a04040")[0] * 0.15, 2)  # mouth
    if sp.get("beard"):
        for bx in range(1, 7):
            if bx not in (3, 4):
                sk.px(x0 + bx, y0 + 6, sk.hair[1])
        sk.px(x0 + 2, y0 + 7, sk.hair[1], 4)
    if sp.get("freckles"):
        for fx in (1, 2, 5, 6):
            if (fx * 7) % 3 != 0:
                sk.px(x0 + fx, y0 + 5, sk.skin[1])
    # Hat layer (overlay): hair volume / accessories.
    style = sp["style"]
    if style == "bun":
        t = hat["top"]
        sk.fill((t[0] + 2, t[1] + 4, t[0] + 6, t[1] + 8), hp, "bun", 0.4, 0.3)
        b = hat["back"]
        sk.fill((b[0] + 2, b[1], b[0] + 6, b[1] + 3), hp, "bunb", 0.35, 0.3)
    elif style == "puff":
        for n in ("top", "right", "left", "back"):
            r = hat[n]
            lx, ly, W, H = _local(sk, r)
            m = (ly < 4) if n != "top" else (ly >= 0)
            sk.fill(r, hp, "puff" + n, 0.4, 0.45, mask=m & (ctx.texel_noise("pz" + n, soft=False) > 0.12))
        band = (hat["front"][0], hat["front"][1] + 1, hat["front"][2], hat["front"][1] + 2)
        sk.fill(band, _p(sp["shirt2"]), "band", 0.5, 0.2)
    elif style == "braid":
        b = hat["back"]
        lx, ly, W, H = _local(sk, b)
        m = (np.abs(lx - 4) < 1.2) & (ly >= 4)
        sk.fill(b, hp, "braidb", 0.45, 0.3, mask=m)
        sk.sh.put(sk.sh.rect(b) & (np.abs(lx - 4) < 1.2) & (np.floor(ly) % 2 == 0) & (ly >= 4),
                  hp[1], height=0.55)
    elif style == "braids":
        for n in ("right", "left", "back"):
            r = hat[n]
            lx, ly, W, H = _local(sk, r)
            m = (np.floor(lx) % 2 == 0) & (ly >= 2)
            sk.fill(r, hp, "brds" + n, 0.4, 0.3, mask=m)
            beads = sk.sh.rect(r) & m & (np.floor(ly) == 7)
            sk.sh.put(beads, pal("e0b040")[0], height=0.7, smooth=0.6)
    elif style == "spiky":
        t = hat["top"]
        lx, ly, W, H = _local(sk, t)
        sk.fill(t, hp, "spk", 0.4, 0.4, mask=((np.floor(lx) + np.floor(ly)) % 3 == 0))
    elif style == "scarf":
        p = _p(sp["scarf"], 0.4)
        for n in ("right", "left", "back", "top"):
            r = hat[n]
            lx, ly, W, H = _local(sk, r)
            m = np.ones_like(lx, bool) if n == "top" else (ly < 7)
            sk.sh.put(sk.sh.rect(r) & m, ctx.palette(p[:-1], ctx.noise(2, 2, salt="sc" + n) * 0.6 + 0.2), height=0.6)
        fr2 = hat["front"]
        sk.sh.put(sk.sh.rect((fr2[0], fr2[1], fr2[2], fr2[1] + 1)), p[2], height=0.6)


def paint_body(sk, f, jacket):
    sp, ctx = sk.spec, sk.ctx
    top = sp["top"]
    for n, r in f.items():
        sk.fill(r, sk.shirt, "shirt" + n, 0.5, 0.25)
        # belt / waist row in pants color
        lx, ly, W, H = _local(sk, r)
        if n in ("right", "front", "left", "back"):
            sk.fill(r, sk.pants, "waist" + n, 0.4, 0.2, mask=ly >= H - 1)
            if top != "overalls" and not sp.get("shorts"):
                sk.sh.put(sk.sh.rect(r) & (ly >= H - 2) & (ly < H - 1), sk.pants[0] * 0.8, height=0.5)
    fr = f["front"]
    x0, y0 = fr[0], fr[1]
    if top == "vest":
        sk.fill(fr, sk.shirt2, "inner", 0.55, 0.2, mask=(np.abs(sk.ctx.x - (x0 + 4)) < 1.5) & (sk.ctx.y < y0 + 10))
        for k in range(2, 10, 3):
            sk.px(x0 + 5, y0 + k, sk.shirt[0])
        sk.px(x0, y0 + 9, sk.shoes[2], 8)  # tool belt
        sk.px(x0 + 1, y0 + 8, pal("8a8a90")[0], 2)
    elif top == "collar":
        sk.px(x0 + 2, y0, sk.shirt2[3], 4)
        sk.px(x0 + 3, y0 + 1, sk.shirt2[3], 2)
        for k in (3, 5, 7):
            sk.px(x0 + 4, y0 + k, sk.shirt2[2])
    elif top == "sweater":
        for k in range(0, 10, 2):
            sk.sh.put(sk.sh.rect(fr) & (np.floor(sk.ctx.y) == y0 + k) & ((sk.ctx.tx + k) % 4 == 0), sk.shirt2[2])
        sk.px(x0 + 2, y0, sk.shirt[0], 4)
    elif top == "jacket":
        sk.fill(fr, sk.shirt2, "tee", 0.5, 0.2, mask=(np.abs(sk.ctx.x - (x0 + 4)) < 2) & (sk.ctx.y < y0 + 10))
        sk.px(x0 + 2, y0, sk.shirt[4], 1, 10)
        sk.px(x0 + 5, y0, sk.shirt[4], 1, 10)
    elif top == "wrap":
        for k in range(10):
            sk.px(x0 + min(7, k), y0 + k, sk.shirt2[2])
    elif top == "coat":
        sk.px(x0 + 4, y0, sk.shirt[0], 1, 11)
        for k in (2, 5, 8):
            sk.px(x0 + 3, y0 + k, pal("6a5a3a")[0])
        sk.px(x0, y0 + 7, sk.shirt[1], 8)
    elif top == "overalls":
        bib = (sk.ctx.x >= x0 + 1) & (sk.ctx.x < x0 + 7) & (sk.ctx.y >= y0 + 4)
        sk.fill(fr, sk.pants, "bib", 0.5, 0.2, mask=bib)
        sk.px(x0 + 1, y0, sk.pants[2], 1, 4)
        sk.px(x0 + 6, y0, sk.pants[2], 1, 4)
        sk.px(x0 + 1, y0 + 4, pal("f0d050")[0])
        sk.px(x0 + 6, y0 + 4, pal("f0d050")[0])
        sk.px(x0 + 3, y0 + 6, sk.pants[3], 2, 2)
        bk = f["back"]
        sk.px(bk[0] + 1, bk[1], sk.pants[2], 1, 8)
        sk.px(bk[0] + 6, bk[1], sk.pants[2], 1, 8)
        sk.fill(bk, sk.pants, "bibb", 0.5, 0.2, mask=sk.ctx.y >= bk[1] + 8)
    elif top == "pattern":
        for n in ("right", "front", "left", "back"):
            r = f[n]
            m = sk.sh.rect(r) & (((sk.ctx.tx * 2 + sk.ctx.ty) % 5) == 0) & (sk.ctx.y < r[3] - 2)
            sk.sh.put(m, sk.shirt2[2], height=0.55)
    # Jacket overlay: open coat flaps / hoods for some outfits.
    if top in ("jacket", "coat"):
        for n, r in jacket.items():
            if n in ("top", "bottom"):
                continue
            lx, ly, W, H = _local(sk, r)
            m = np.ones_like(lx, bool)
            if n == "front":
                m = (lx < 2) | (lx >= W - 2)
            if top == "jacket":
                m &= ly < H - 2
            sk.fill(r, sk.shirt, "jk" + n, 0.48, 0.25, mask=m)
            if top == "jacket":
                sk.sh.put(sk.sh.rect(r) & (ly >= H - 3) & (ly < H - 2) & m, sk.shirt[0], height=0.55)


def paint_arm(sk, f, sleeve, w):
    sp, ctx = sk.spec, sk.ctx
    long_ = sp["sleeves"] == "long"
    for n, r in f.items():
        sk.fill(r, sk.skin, "arm" + n, 0.55, 0.2, sss=0.4)
        lx, ly, W, H = _local(sk, r)
        if n == "top":
            sk.fill(r, sk.shirt, "sh" + n, 0.55, 0.2)
        elif n != "bottom":
            cut = 10 if long_ else 4
            if sp["top"] == "overalls":
                cut = 3
            sk.fill(r, sk.shirt, "sl" + n, 0.48, 0.25, mask=ly < cut)
            sk.sh.put(sk.sh.rect(r) & (ly >= cut - 1) & (ly < cut), sk.shirt[1], height=0.55)
    if sp["top"] in ("jacket", "coat"):
        for n, r in sleeve.items():
            if n in ("top", "bottom"):
                continue
            lx, ly, W, H = _local(sk, r)
            sk.fill(r, sk.shirt, "jsl" + n, 0.5, 0.25, mask=(ly < 10) & (ly >= 8))


def paint_leg(sk, f, pants):
    sp = sk.spec
    shorts = sp.get("shorts")
    for n, r in f.items():
        lx, ly, W, H = _local(sk, r)
        sk.fill(r, sk.pants, "leg" + n, 0.45, 0.25)
        if shorts and n not in ("top", "bottom"):
            sk.fill(r, sk.skin, "knee" + n, 0.55, 0.2, mask=ly >= 5, sss=0.4)
        if n == "bottom":
            sk.fill(r, sk.shoes, "sole", 0.3, 0.2)
        elif n != "top":
            shoe = 3 if not shorts else 2
            sk.fill(r, sk.shoes, "shoe" + n, 0.5, 0.2, mask=ly >= H - shoe)
            sk.sh.put(sk.sh.rect(r) & (ly >= H - 1), sk.shoes[0] if sp["shoes"] != "f0f0f0" else pal("c0c0c4")[0],
                      height=0.5)
            if shorts:
                sk.sh.put(sk.sh.rect(r) & (ly >= H - 3) & (ly < H - 2), pal("f0f0f0")[0], height=0.55)  # socks
            if not shorts:
                sk.sh.put(sk.sh.rect(r) & (ly >= 0) & (ly < 1), sk.pants[0], height=0.5)
    if sp["top"] == "overalls":
        r = pants["front"]
        lx, ly, W, H = _local(sk, r)
        sk.fill(r, sk.pants, "cuff", 0.6, 0.2, mask=(ly >= H - 4) & (ly < H - 3))


def player(ctx, name, slim):
    sk = Skin(ctx, CHARS[name])
    sh = sk.sh
    aw = 3 if slim else 4
    paint_head(sk, sh.faces(0, 0, 8, 8, 8), sh.faces(32, 0, 8, 8, 8))
    paint_body(sk, sh.faces(16, 16, 8, 12, 4), sh.faces(16, 32, 8, 12, 4))
    paint_arm(sk, sh.faces(40, 16, aw, 12, 4), sh.faces(40, 32, aw, 12, 4), aw)
    paint_arm(sk, sh.faces(32, 48, aw, 12, 4), sh.faces(48, 48, aw, 12, 4), aw)
    paint_leg(sk, sh.faces(0, 16, 4, 12, 4), sh.faces(0, 32, 4, 12, 4))
    paint_leg(sk, sh.faces(16, 48, 4, 12, 4), sh.faces(0, 48, 4, 12, 4))
    # Shade the bottom edge of each limb face slightly (form shading).
    return sh.tex(grain=0.03)


for _n in CHARS:
    register(f"entity/player/wide/{_n}", (lambda n: lambda ctx: player(ctx, n, False))(_n))
    register(f"entity/player/slim/{_n}", (lambda n: lambda ctx: player(ctx, n, True))(_n))
