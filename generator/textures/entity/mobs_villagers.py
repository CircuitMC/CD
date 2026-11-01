"""Villagers (base, biome types, professions, levels), zombie villagers, wandering trader,
witch and illagers (entity_mobs).

Villager textures are layered in game: base skin, then biome type, then profession, then
profession level badge. Overlays are mostly transparent.
"""
import numpy as np

from ...registry import register
from .mobs_base import SIDES, Mat, Skin, col, mix, shades

PUPIL = "1a1614"


def reg(paths, fn, *args):
    for p in paths:
        register(p, lambda ctx, p=p: fn(ctx, p, *args))


def parts(sk):
    """Semantic villager parts for any of the villager-like layouts."""
    P = dict(head=None, nose=None, hat=None, brim=None, body=None, robe=None, arms=[], xarms=[], legs=[])
    for b in sk.boxes:
        n = b.part
        if n == "head" and b.idx == 0:
            P["head"] = b
        elif (n == "head" and b.idx == 1) or n == "nose":
            P["nose"] = b
        elif n in ("headwear2", "hat_rim", "headwear/rotation"):
            P["brim"] = b
        elif n == "headwear":
            P["hat"] = b
        elif n == "body" and b.idx == 0:
            P["body"] = b
        elif (n == "body" and b.idx == 1) or n == "bodywear":
            P["robe"] = b
        elif n.startswith("arms") or n == "right_hand":
            P["xarms"].append(b)
        elif n in ("left_arm", "right_arm"):
            P["arms"].append(b)
        elif "leg" in n:
            P["legs"].append(b)
    return P


def is_baby(P, sk):
    return P["head"] is not None and P["head"].h / sk.k < 10


class Painter:
    """Paints villager clothing with optional zombie styling (desaturated, torn)."""

    def __init__(self, sk, zombie=False):
        self.sk, self.zombie = sk, zombie
        self.P = parts(sk)
        self.baby = is_baby(self.P, sk)

    def c(self, c):
        c = col(c)
        if self.zombie:
            g = c @ np.array([0.3, 0.59, 0.11])
            c = mix(c * 0.85, np.array([g * 0.8, g * 0.95, g * 0.75]), 0.4)
        return c

    def mat(self, c, **kw):
        kw.setdefault("sss", 0.05)
        kw.setdefault("grain", 0.2)
        kw.setdefault("mottle", 0.22)
        return Mat(self.c(c), **kw)

    def torn(self, b, thr=0.72):
        if not self.zombie or b is None:
            return
        sk = self.sk
        for f, r in b.faces.items():
            sl = sk._sl(*r)
            if sl is not None:
                fy = (sk.ctx.y[sl] - r[1]) / max(r[3] - r[1], 1)
                cut = (sk.noise["small"][sl] > thr) & ((fy > 0.6) | (sk.noise["mid"][sl] > 0.6))
                sk.alpha[sl][cut] = 0

    # -------------------------------------------------- garments
    def robe(self, c, trim=None, belt=None, sleeves=True, legs=None):
        sk, P = self.sk, self.P
        m = self.mat(c)
        for b in (P["body"], P["robe"]):
            sk.paint(b, m)
        if sleeves:
            for a in P["xarms"]:
                sk.paint(a, m)
            for a in P["arms"]:
                sk.paint(a, m)
        if trim is not None and P["robe"] is not None:
            sk.band(P["robe"], -1 if self.baby else -2, 0, self.mat(trim, grain=0.15))
        if belt is not None:
            b = P["robe"] or P["body"]
            y = 2 if self.baby else 8
            sk.band(b, y, y + 1, self.mat(belt, grain=0.15))
            if P["body"] is not None and not self.baby:
                sk.band(P["body"], y, y + 1, self.mat(belt, grain=0.15))
        if legs is not None:
            for l in P["legs"]:
                sk.paint(l, self.mat(legs))
        for b in (P["body"], P["robe"]):
            self.torn(b)

    def apron(self, c, strap=None, top=2, full=False):
        """Front panel on the robe (and body)."""
        sk, P = self.sk, self.P
        m = self.mat(c)
        if self.baby:
            for b in (P["body"], P["robe"]):
                sk.frect(b, "front", 1 if not full else 0, 1, -1 if not full else 0, 0, m)
            return
        sk.frect(P["robe"], "front", 1 if not full else 0, top, -1 if not full else 0, -2, m)
        sk.frect(P["body"], "front", 1 if not full else 0, top, -1 if not full else 0, 0, m)
        if strap is not None:
            s = self.c(strap)
            for b in (P["robe"], P["body"]):
                sk.frect(b, "front", 1, 0, 2, top, s, height=0.55)
                sk.frect(b, "front", 6, 0, 7, top, s, height=0.55)
                sk.frect(b, "back", 1, 0, 2, 8, s, height=0.55)
                sk.frect(b, "back", 6, 0, 7, 8, s, height=0.55)
        self.torn(P["robe"], 0.78)

    def vest(self, c, open_front=True):
        sk, P = self.sk, self.P
        m = self.mat(c)
        for b in (P["body"], P["robe"]):
            if b is None:
                continue
            ln = 12 if b is P["body"] else 12
            if self.baby:
                ln = 4
            for f in ("left", "right", "back"):
                sk.frect(b, f, 0, 0, 0, ln, m)
            sk.frect(b, "front", 0, 0, 2 if not self.baby else 1, ln, m)
            sk.frect(b, "front", -2 if not self.baby else -1, 0, 0, ln, m)
            if not open_front:
                sk.frect(b, "front", 0, 0, 0, ln, m)
            sk.frect(b, "top", 0, 0, 0, 0, m)
        for a in P["xarms"] + P["arms"]:
            sk.paint(a, m)

    def scarf(self, c, rows=2):
        sk, P = self.sk, self.P
        m = self.mat(c, streak=0.4)
        for b in (P["robe"], P["body"]):
            sk.band(b, 0, rows if not self.baby else 1, m, top=True)

    def sash(self, c):
        """Diagonal band across the robe front."""
        sk, P = self.sk, self.P
        b = P["robe"]
        if b is None or "front" not in b.faces:
            return
        h = 12 if not self.baby else 5
        w = 8 if not self.baby else 4
        cc = self.c(c)
        for i in range(h):
            x = int(i * w / h)
            sk.frect(b, "front", x, i, x + 2, i + 1, cc, height=0.55)
        sk.frect(b, "back", 0, 0, 0, 1, cc)

    def hat(self, c, rows=3, brim=None, brim_r=7.5, top=True, band=None, crown_extra=None):
        """Hat on the headwear box; rows = how far down the sides it reaches; brim on the
        flat brim plane (disc of radius brim_r)."""
        sk, P = self.sk, self.P
        h = P["hat"]
        m = self.mat(c, mottle=0.3)
        if h is not None:
            if top:
                sk.paint(h, m, faces=("top",))
            sk.band(h, 0, rows, m)
            if band is not None:
                sk.band(h, rows - 1, rows, self.mat(band, grain=0.1))
            self.torn(h, 0.8)
        b = P["brim"]
        if brim is not None and b is not None:
            mb = self.mat(brim, mottle=0.3)
            f = "front" if "front" in b.faces and b.faces["front"][2] - b.faces["front"][0] > 4 * sk.k and \
                b.faces["front"][3] - b.faces["front"][1] > 4 * sk.k else "top"
            x0, y0, x1, y1 = b.faces[f]
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            sl = sk._sl(x0, y0, x1, y1)
            r = brim_r * sk.k * (0.75 if self.baby else 1)
            d = np.hypot(sk.ctx.x[sl] - cx, (sk.ctx.y[sl] - cy) * (x1 - x0) / max(y1 - y0, 1))
            disc = d < r
            v = mb.base + (sk.noise["mid"][sl] - 0.5) * mb.mottle + (sk.grain[sl] - 0.5) * mb.grain \
                - (d / r) * 0.15
            sk._write(sl, sk.ctx.palette(mb.p, v), mb, height=0.55, mask=disc)
            ring = disc & (d > r - sk.k * 1.0)
            sk.color[sl][ring] *= 0.85
            if self.zombie:
                sk.alpha[sl][disc & (sk.noise["small"][sl] > 0.8)] = 0

    def headband(self, c, row=1, rows=1):
        sk, h = self.sk, self.P["hat"] or self.P["head"]
        sk.band(h, row, row + rows, self.mat(c, grain=0.15))

    def badge(self, gem, frame):
        sk, P = self.sk, self.P
        b = P["robe"] or P["body"]
        if self.baby:
            sk.frect(b, "front", 1, 1, 3, 2, self.c(frame), height=0.6, smooth=0.6)
            sk.frect(b, "front", 1, 1, 2, 2, self.c(gem), height=0.7, smooth=0.8)
            return
        g, fr = self.c(gem), self.c(frame)
        sk.frect(b, "front", 3, 7, 5, 10, fr, height=0.6, smooth=0.55)
        sk.frect(b, "front", 3, 8, 5, 9, g, height=0.72, smooth=0.85, f0=0.1)
        sk.frect(b, "front", 3, 8, 4, 9, mix(g, "ffffff", 0.35), height=0.75, smooth=0.9)
        sk.band(b, 8, 9, self.mat("4a3424", grain=0.15), faces=("left", "right", "back"))


# ---------------------------------------------------------------- base villager


def villager_face(sk, P, skin, eye="3a7a3a", zombie=False):
    head, nose = P["head"], P["nose"]
    baby = is_baby(P, sk)
    skin_dark = col(skin.p[0])
    if baby:
        sk.sym(head, "front", 1, 3, 3, 4, "ece6da", height=0.45, smooth=0.6, sss=0.0)
        sk.sym(head, "front", 2, 3, 3, 4, eye, height=0.4, smooth=0.6, sss=0.0)
        sk.sym(head, "front", 1, 2, 3, 3, mix(skin_dark, "2a1a10", 0.4), height=0.55)
        sk.frect(head, "front", 3, 6, 5, 7, mix(skin_dark, "2a1a10", 0.3), height=0.4)
    else:
        sk.sym(head, "front", 1, 4, 3, 5, "ece6da" if not zombie else "c8d8a0", height=0.45, smooth=0.6, sss=0.0)
        sk.sym(head, "front", 2, 4, 3, 5, eye, height=0.4, smooth=0.6, sss=0.0)
        sk.sym(head, "front", 1, 3, 3, 4, mix(skin_dark, "2a1a10", 0.45), height=0.58)   # brows
        sk.frect(head, "front", 3, 3, 5, 4, skin.but(base=0.42))
        sk.frect(head, "front", 2, 8, 6, 9, mix(skin_dark, "2a1a10", 0.3), height=0.4)  # mouth
        sk.tint(head, "front", 0, 9, 8, 10, 0.9)
    if nose is not None:
        sk.paint(nose, skin.but(base=0.5))
        sk.frect(nose, "front", 0, -1, 0, 0, skin.but(base=0.35))
    if zombie and not baby:
        sk.sym(head, "front", 1, 5, 3, 6, skin.but(base=0.3))


VILLAGER_SKIN = Mat("b8865c", mottle=0.18, grain=0.18, sss=0.35)
ZV_SKIN = Mat("5f8a4a", mottle=0.3, grain=0.25, sss=0.3, blotch=("4d7240", 0.62, "mid"))


def villager_base(ctx, path):
    name = path.split("/")[-1]
    zombie = "zombie" in path
    baby = "baby" in name
    model = ("zombie_villager" if zombie else "villager") + ("_baby" if baby else "")
    sk = Skin(ctx, model)
    pt = Painter(sk, zombie)
    P = pt.P
    skin = ZV_SKIN if zombie else VILLAGER_SKIN
    sk.paint(P["head"], skin)
    pt.robe("6a5a48", trim="4a3e32", belt="4a3424", legs="4a3e32")
    for a in P["arms"]:        # zombie villagers: bare forearms
        sk.paint(a, skin)
        sk.band(a, 0, 4 if not baby else 2, pt.mat("6a5a48"), top=True)
    for a in P["xarms"]:
        if a.w / sk.k >= 8 or (baby and a.part.startswith("arms")):   # crossed-arm bar: hands at the ends
            sk.paint(a, pt.mat("6a5a48"))
            sk.frect(a, "front", 0, 0, 1 if baby else 2, 0, skin)
            sk.frect(a, "front", -1 if baby else -2, 0, 0, 0, skin)
        else:
            sk.paint(a, pt.mat("6a5a48"))
            sk.band(a, -1 if baby else -2, 0, skin, bottom=True)
    for l in P["legs"]:
        sk.band(l, -1 if baby else -2, 0, pt.mat("3a2c22"), bottom=True)
    villager_face(sk, P, skin, eye="3a7a3a" if not zombie else "c03020", zombie=zombie)
    if zombie:  # rotten patches on the skin
        sk.face_spots(P["head"], skin.but(base=0.3), 0.75, "small")
    return sk.tex()


reg(["entity/villager/villager", "entity/villager/villager_baby", "entity/zombie_villager/zombie_villager",
     "entity/zombie_villager/zombie_villager_baby"], villager_base)


# ---------------------------------------------------------------- biome types

def type_overlay(ctx, path):
    parts_ = path.split("/")
    zombie = parts_[1] == "zombie_villager"
    baby = parts_[2] == "baby"
    biome = parts_[-1]
    model = ("zombie_villager" if zombie else "villager") + ("_baby" if baby else "")
    sk = Skin(ctx, model)
    pt = Painter(sk, zombie)
    if biome == "desert":
        pt.robe("c8a46a", trim="8a3a2a", belt="8a3a2a")
        pt.sash("b84a30")
        pt.hat("e0cc98", rows=4, band="b84a30")             # head wrap
    elif biome == "jungle":
        pt.robe("4a6a30", trim="7a4a20", belt="7a4a20")
        pt.scarf("3a8a3a")
        pt.headband("6a8a2a", row=2)
        sk.frect(pt.P["hat"], "front", 5, 0, 6, 3, pt.c("d84a2a"), height=0.6)   # feather
        sk.frect(pt.P["hat"], "front", 5, 0, 6, 1, pt.c("e8c040"), height=0.6)
    elif biome == "plains":
        pt.robe("7a6a4a", trim="5a7a3a", belt="5a4030")
        pt.scarf("8a7a50")
    elif biome == "savanna":
        pt.robe("b8642a", trim="e8c040", belt="6a3a20")
        for y in (3, 6, 12, 15):   # woven pattern rows
            sk.band(pt.P["robe"], y, y + 1, pt.mat("e8c040", grain=0.1)) if not baby else None
        pt.headband("d8a030", row=2)
    elif biome == "snow":
        pt.robe("5a6a8a", trim="eceae4", belt="3a3a4a")
        pt.scarf("c83a3a", rows=2)
        pt.hat("eceae4", rows=4, band="a8a8b0")              # fur cap
    elif biome == "swamp":
        pt.robe("3a4a32", trim="5a6a3a", belt="2a3424")
        sk.face_spots(pt.P["robe"], pt.mat("5a7a30"), 0.7, "streak")
        pt.hat("3a5a2a", rows=2, top=True)
        sk.face_spots(pt.P["hat"], pt.mat("6a8a3a"), 0.6, "streak", faces=SIDES)
    elif biome == "taiga":
        pt.robe("5a4030", trim="3a2a20", belt="2a1c14")
        pt.scarf("8a6a4a", rows=2)
        pt.hat("6a4a34", rows=2, band="3a2a20")
    for a in pt.P["arms"]:   # zombie arms keep skin below the sleeve
        sk.clear((a.faces["front"][0], a.faces["front"][1] + 4 * sk.k, a.faces["back"][2], a.faces["back"][3])) \
            if "front" in a.faces else None
    return sk.tex()


BIOMES = ("desert", "jungle", "plains", "savanna", "snow", "swamp", "taiga")
reg([f"entity/{v}/{t}/{b}" for v in ("villager", "zombie_villager") for t in ("type", "baby") for b in BIOMES],
    type_overlay)


# ---------------------------------------------------------------- professions

def profession_overlay(ctx, path):
    zombie = "zombie_villager" in path
    prof = path.split("/")[-1]
    sk = Skin(ctx, "zombie_villager" if zombie else "villager")
    pt = Painter(sk, zombie)
    P = pt.P
    if prof == "armorer":
        pt.apron("3a3a40", strap="2a2a2e")
        pt.hat("4a4a52", rows=2, top=True)
        sk.frect(P["hat"], "front", 1, 3, 7, 5, pt.c("2a2a30"), height=0.6, smooth=0.6)   # welding visor
        sk.frect(P["hat"], "front", 2, 4, 6, 5, pt.c("6a9aa8"), height=0.62, smooth=0.9)
    elif prof == "butcher":
        pt.apron("e8e4dc", strap="d8d0c4")
        sk.face_spots(P["robe"], pt.mat("a83a32"), 0.75, "small", faces=("front",))
        pt.headband("c83a32", row=1)
    elif prof == "cartographer":
        pt.vest("4a5a7a")
        sk.frect(P["head"], "front", 4, 4, 7, 6, pt.c("d8b040"), height=0.65, smooth=0.7)  # monocle
        sk.frect(P["head"], "front", 5, 4, 6, 5, pt.c("a8d0e0"), height=0.66, smooth=0.95)
    elif prof == "cleric":
        pt.robe("6a3a8a", trim="d8b040", belt="d8b040")
        pt.scarf("8a5aa8")
    elif prof == "farmer":
        pt.apron("8a6a3a", strap="6a4a2a")
        pt.hat("d8c070", rows=2, brim="c8b060", brim_r=7.5, band="8a4a2a")   # straw hat
    elif prof == "fisherman":
        pt.vest("3a7a8a")
        pt.hat("c8b880", rows=2, brim="b8a870", brim_r=6.5, band="3a6a7a")
    elif prof == "fletcher":
        pt.vest("5a7a3a")
        pt.hat("6a8a3a", rows=2, brim=None, band="4a3a2a")
        sk.frect(P["hat"], "left", 2, 0, 4, 3, pt.c("e8e4dc"), height=0.6)     # feather
        sk.frect(P["hat"], "left", 3, 0, 4, 1, pt.c("c83a2a"), height=0.6)
    elif prof == "leatherworker":
        pt.apron("8a5a34", strap="6a4024", full=True)
        sk.band(P["robe"], 9, 10, pt.mat("c8a050", grain=0.1))
    elif prof == "librarian":
        pt.robe("8a2a2a", trim="d8b040", belt="4a2020")
        pt.hat("a83030", rows=3, brim=None, band="d8b040")
        sk.frect(P["hat"], "top", 3, 3, 5, 5, pt.c("d8b040"), height=0.6)
    elif prof == "mason":
        pt.apron("5a5a5a", strap="3a3a3a")
        sk.face_spots(P["robe"], pt.mat("8a8a88"), 0.72, "small", faces=("front",))
    elif prof == "nitwit":
        pt.robe("3a7a3a", trim="2a5a2a", belt=None)
    elif prof == "shepherd":
        pt.vest("e0d8c8")
        pt.hat("8a6a4a", rows=3, brim="7a5a3a", brim_r=6.0)
    elif prof == "toolsmith":
        pt.apron("2a2a2e", strap="1a1a1e")
        sk.frect(P["robe"], "front", 2, 9, 3, 13, pt.c("8a8a8a"), height=0.65, smooth=0.6)  # hammer in pocket
        sk.frect(P["robe"], "front", 1, 9, 4, 10, pt.c("5a4030"), height=0.65)
    elif prof == "weaponsmith":
        pt.apron("2a2a2e", strap="1a1a1e")
        sk.frect(P["head"], "front", 1, 3, 4, 5, pt.c("1a1616"), height=0.6)        # eyepatch
        sk.frect(P["hat"] or P["head"], "front", 0, 3, 8, 4, pt.c("1a1616"), height=0.6)
    for a in P["arms"]:   # zombie arms: sleeves only
        if "front" in a.faces:
            sk.clear((a.faces["right"][0], a.faces["front"][1] + 4 * sk.k, a.faces["back"][2], a.faces["back"][3]))
    return sk.tex()


PROFS = ("armorer", "butcher", "cartographer", "cleric", "farmer", "fisherman", "fletcher", "leatherworker",
         "librarian", "mason", "nitwit", "shepherd", "toolsmith", "weaponsmith")
reg([f"entity/{v}/profession/{p}" for v in ("villager", "zombie_villager") for p in PROFS], profession_overlay)

LEVELS = {"stone": ("8a8a88", "5a5a58"), "iron": ("e0e0dc", "8a8a88"), "gold": ("f0c838", "a87a20"),
          "emerald": ("3ad870", "1a7a3a"), "diamond": ("6ae8e0", "2a8a90")}


def level_overlay(ctx, path):
    zombie = "zombie_villager" in path
    lv = path.split("/")[-1]
    sk = Skin(ctx, "zombie_villager" if zombie else "villager")
    pt = Painter(sk, zombie)
    gem, frame = LEVELS[lv]
    pt.badge(gem, frame if lv not in ("gold",) else "6a4a20")
    return sk.tex()


reg([f"entity/{v}/profession_level/{l}" for v in ("villager", "zombie_villager") for l in LEVELS], level_overlay)


# ---------------------------------------------------------------- wandering trader & witch

def wandering_trader(ctx, path):
    sk = Skin(ctx, "wandering_trader")
    pt = Painter(sk)
    P = pt.P
    sk.paint(P["head"], VILLAGER_SKIN)
    pt.robe("2a4a8a", trim="d8b040", belt="6a4a2a", legs="2a2a3a")
    for a in P["xarms"]:
        if a.w / sk.k >= 8:
            sk.frect(a, "front", 0, 0, 2, 0, VILLAGER_SKIN)
            sk.frect(a, "front", -2, 0, 0, 0, VILLAGER_SKIN)
    pt.hat("3a5a9a", rows=6, top=True, band="d8b040")    # hood
    sk.frect(P["hat"], "front", 1, 2, 7, 10, (0, 0, 0), alpha=0.0)
    pt.scarf("c84a3a")
    villager_face(sk, P, VILLAGER_SKIN, eye="3a5a8a")
    return sk.tex()


reg(["entity/wandering_trader/wandering_trader"], wandering_trader)


def witch(ctx, path):
    sk = Skin(ctx, "witch")
    pt = Painter(sk)
    P = pt.P
    skin = Mat("a8a070", mottle=0.2, grain=0.2, sss=0.35)
    sk.paint(P["head"], skin)
    pt.robe("4a2a5a", trim="2a1a34", belt="6a4a2a", legs="2a1a2a")
    for a in P["xarms"]:
        if a.w / sk.k >= 8:
            sk.frect(a, "front", 0, 0, 2, 0, skin)
            sk.frect(a, "front", -2, 0, 0, 0, skin)
    villager_face(sk, P, skin, eye="8a3aa8")
    sk.frect(P["nose"], "front", 1, 2, 2, 3, "5a6a2a", height=0.7)   # wart
    hat = Mat("2a2a2e", mottle=0.25, grain=0.2, sss=0.05)
    for b in sk.find("headwear"):
        sk.paint(b, hat)
    sk.band(sk.box("headwear/hat2"), -1, 0, Mat("6a3a8a", grain=0.1))
    sk.paint(sk.box("mole"), Mat("4a5a2a", grain=0.1))
    return sk.tex()


reg(["entity/witch/witch"], witch)


# ---------------------------------------------------------------- illagers

ILLAGER_SKIN = Mat("8a9494", mottle=0.18, grain=0.18, sss=0.3)


def illager(ctx, path):
    name = path.split("/")[-1]
    sk = Skin(ctx, name)
    pt = Painter(sk)
    P = pt.P
    sk.paint(P["head"], ILLAGER_SKIN)
    head = P["head"]
    garb = {"evoker": ("1e1e24", "d8b040", "2a2a30"), "vindicator": ("3a3a40", "2a2a2e", "24242a"),
            "pillager": ("5a4a3a", "3a2a20", "2a2a2e"), "illusioner": ("2a4a8a", "d8d0c0", "1e2a4a")}[name]
    pt.robe(garb[0], trim=garb[1], belt="3a2a20", legs=garb[2])
    if name == "pillager":
        pt.sash("2a2a2e")
    for a in P["xarms"]:
        if a.w / sk.k >= 8:
            sk.frect(a, "front", 0, 0, 2, 0, ILLAGER_SKIN)
            sk.frect(a, "front", -2, 0, 0, 0, ILLAGER_SKIN)
    for a in P["arms"]:
        sk.band(a, -2, 0, ILLAGER_SKIN, bottom=True)
    for l in P["legs"]:
        sk.band(l, -2, 0, Mat("1e1a18", grain=0.1), bottom=True)
    # face: heavy single brow, narrow eyes
    eye = {"evoker": "3a8a8a", "vindicator": "3a6a4a", "pillager": "4a4a6a", "illusioner": "4a7ae0"}[name]
    sk.frect(head, "front", 0, 3, 8, 4, "2a2a2c", height=0.6)
    sk.sym(head, "front", 1, 4, 3, 5, "d8dcd8", height=0.45, smooth=0.6, sss=0.0)
    sk.sym(head, "front", 2, 4, 3, 5, eye, height=0.4, smooth=0.6, sss=0.0,
           emissive=0.4 if name == "illusioner" else 0.0)
    sk.frect(head, "front", 2, 8, 6, 9, "4a5050", height=0.4)
    sk.paint(P["nose"], ILLAGER_SKIN.but(base=0.48))
    if name == "illusioner":
        hood = Mat("2a4a8a", mottle=0.25, grain=0.2, sss=0.05)
        hw = P["hat"]
        sk.paint(hw, hood)
        sk.frect(hw, "front", 1, 2, 7, 11, (0, 0, 0), alpha=0.0)
        sk.clear(hw.faces["bottom"])
    if name == "evoker":
        sk.frect(P["robe"], "front", 3, 0, 5, 18, pt.c("d8b040"), height=0.55)
    if name == "vindicator":
        sk.frect(head, "front", 0, 0, 8, 2, "2a2420")    # dark hair line
        sk.paint(head, Mat("2a2420", grain=0.2), faces=("top",))
    return sk.tex()


reg(["entity/illager/evoker", "entity/illager/illusioner", "entity/illager/pillager",
     "entity/illager/vindicator"], illager)
