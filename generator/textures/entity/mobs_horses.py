"""Horses, donkeys, mules, undead horses, llamas, camels (entity_mobs)."""
import numpy as np

from ...registry import register
from .mobs_base import SIDES, Mat, Skin, col, mix, shades

PUPIL = "161212"


def reg(paths, fn, *args):
    for p in paths:
        register(p, lambda ctx, p=p: fn(ctx, p, *args))


def side_eyes(sk, b, fy=1, white=None, pupil=PUPIL, from_front=1, size=1):
    """Eyes on the left/right faces of a forward-pointing head, near the front edge."""
    if b is None:
        return
    for f in ("right", "left"):
        if f not in b.faces:
            continue
        dm = b.d / sk.k
        x = dm - from_front - size if f == "right" else from_front
        sk.frect(b, f, x, fy, x + size, fy + 1, pupil, height=0.4, smooth=0.7, sss=0.0)
        if white is not None:
            wx = x - 1 if f == "right" else x + size
            sk.frect(b, f, wx, fy, wx + 1, fy + 1, white, height=0.45, smooth=0.6, sss=0.0)


HORSES = {
    # name: (coat, mane, muzzle)
    "white": ("e8e4dc", "c8c0b4", "b8aaa0"),
    "creamy": ("d8b880", "f0e0c0", "8a6a50"),
    "chestnut": ("a0582c", "6a3418", "5a3a2c"),
    "brown": ("7a4e30", "2a1c16", "3a2a22"),
    "black": ("2c2626", "141010", "1e1a1a"),
    "gray": ("8a8684", "4a4644", "4a4444"),
    "darkbrown": ("4a3022", "1c1410", "2a1e18"),
    "donkey": ("8a7a6a", "3a302a", "d8d0c4"),
    "mule": ("5a3a28", "2a1a12", "a08870"),
    "zombie": ("5a7a48", "3a4a2c", "4a5a3a"),
}


def horse_base(sk, coat_c, mane_c, muzzle_c, kind="horse", baby=False):
    coat = Mat(coat_c, mottle=0.22, grain=0.2, streak=0.3, sss=0.3, smooth=0.2,
               blotch=(mix(coat_c, "283828", 0.35), 0.66, "mid") if kind == "zombie" else None)
    mane = Mat(mane_c, mottle=0.3, grain=0.3, streak=1.0, sss=0.3)
    muzzle = Mat(muzzle_c, mottle=0.15, grain=0.2, sss=0.35)
    hoof = Mat("3a302a", grain=0.15, sss=0.0, smooth=0.3)
    sk.paint_all([("mane", mane), ("tail", mane), ("left_chest", None), ("right_chest", None)], coat,
                 skip=("left_chest", "right_chest"))
    head = sk.box("head")
    mouth = sk.box("mouth")
    if mouth is not None:
        sk.paint(mouth, muzzle)
        sk.sym(mouth, "front", 0, 2, 1, 3, mix(muzzle_c, "000000", 0.55), height=0.3)
        side_eyes(sk, head, fy=1, white=mix(coat_c, "ffffff", 0.3) if kind != "zombie" else "c8d890",
                  pupil=PUPIL if kind != "zombie" else "2a3a1a")
    else:  # baby: single long head box; muzzle = front third
        hd = head.d / sk.k
        for f in ("right", "left"):
            if f in head.faces:
                x0, y0, x1, y1 = head.faces[f]
                n = 3 * sk.k
                r = (x1 - n, y0, x1, y1) if f == "right" else (x0, y0, x0 + n, y1)
                sk.fill(r, muzzle)
        sk.paint(head, muzzle, faces=("front",))
        sk.sym(head, "front", 1, 2, 2, 3, mix(muzzle_c, "000000", 0.55), height=0.3)
        for f in ("right", "left"):
            x = hd - 5 if f == "right" else 4
            sk.frect(head, f, x, 1, x + 1, 2, PUPIL, height=0.4, smooth=0.7)
    neck = sk.box("neck")
    if neck is not None and mouth is not None:   # mane stripe runs down the back of the neck
        sk.paint(neck, mane, faces=("back",))
    elif neck is not None:
        sk.paint(neck, mane, faces=("back",))
        sk.frect(head, "top", 0, 0, 0, 3, mane) if head is not None else None
    for l in sk.boxes:
        if "leg" in l.part:
            sk.band(l, -1 if baby else -2, 0, hoof, bottom=True)
    if kind == "donkey" or kind == "mule":
        body = sk.box("body")
        sk.frect(body, "top", 4 if not baby else 3, 0, -4 if not baby else -3, 0, mane.but(base=0.4))  # dorsal stripe
        if body is not None:
            sk.fill(body.faces["bottom"], muzzle) if "bottom" in body.faces else None
    for b in sk.find("left_chest") + sk.find("right_chest"):  # saddle bags
        wood = Mat("8a5a30", grain=0.2, mottle=0.2, sss=0.0, streak=0.6)
        sk.paint(b, wood)
        for f in b.faces:
            x0, y0, x1, y1 = b.faces[f]
            sk.rect(x0, y0, x1, y0 + sk.k, "5a3a20", height=0.6)
        sk.frect(b, "left", 3, 3, 5, 5, "b8b0a0", height=0.7, smooth=0.6)
        sk.frect(b, "right", 3, 3, 5, 5, "b8b0a0", height=0.7, smooth=0.6)
    return coat


def horse(ctx, path):
    name = path.split("/")[-1]
    baby = name.endswith("_baby")
    n = name.replace("_baby", "")
    if n.startswith("horse_markings"):
        return markings(ctx, n.split("_")[-1], baby)
    if n in ("donkey", "mule"):
        model = n + ("_baby" if baby else "")
        sk = Skin(ctx, model)
        horse_base(sk, *HORSES[n], kind=n, baby=baby)
        return sk.tex()
    if n == "horse_skeleton":
        return skeleton_horse(ctx, baby)
    key = n[6:]
    model = ("zombie_horse" if key == "zombie" else "horse") + ("_baby" if baby else "")
    sk = Skin(ctx, model)
    coat_c, mane_c, muzzle_c = HORSES[key]
    horse_base(sk, coat_c, mane_c, muzzle_c, kind="zombie" if key == "zombie" else "horse", baby=baby)
    if key == "zombie":  # exposed ribs and torn patches
        body = sk.box("body")
        for f in ("left", "right"):
            if f in body.faces:
                for i in range(3):
                    sk.frect(body, f, 8 + i * 2 if not baby else 5 + i * 2, 2, 9 + i * 2 if not baby else 6 + i * 2,
                             6 if not baby else 4, "d8d0b0", height=0.6)
                sk.frect(body, f, 7 if not baby else 4, 2, 14 if not baby else 10, 3, "3a2020", height=0.3)
    return sk.tex()


def skeleton_horse(ctx, baby):
    sk = Skin(ctx, "skeleton_horse_baby" if baby else "skeleton_horse")
    bone = Mat(shades("d4cfbe", 6, 0.72, 1.08), mottle=0.25, grain=0.22, grad=0.2, sss=0.1, smooth=0.25)
    sk.paint_all([], bone)
    gap = "201c1a"
    body = sk.box("body")
    for f in ("left", "right"):
        if f in body.faces:
            dm = body.d / sk.k
            for x in range(3, int(dm) - 3, 2):
                sk.frect(body, f, x, 2, x + 1, -2, gap, height=0.15)
    for f in ("bottom",):
        sk.frect(body, f, 0, 0, 0, 0, Mat(gap, grain=0.1)) if f in body.faces else None
    head = sk.box("head")
    mouth = sk.box("mouth")
    for f in ("right", "left"):
        if head is not None and f in head.faces:
            dm = head.d / sk.k
            x = dm - 3 if f == "right" else 1
            sk.frect(head, f, x, 1, x + 2, 3, gap, height=0.2)
    if mouth is not None:
        for i in range(0, 4, 2):
            sk.frect(mouth, "front", i, 3, i + 1, 4, gap, height=0.2)
        sk.sym(mouth, "front", 0, 1, 1, 2, gap, height=0.2)
    else:
        sk.sym(head, "front", 1, 1, 2, 2, gap, height=0.2)
        sk.frect(head, "front", 1, 3, -1, 4, gap, height=0.2)
    for l in sk.boxes:
        if "leg" in l.part:
            sk.band(l, 4 if not baby else 3, 5 if not baby else 4, bone.but(base=0.85))
    return sk.tex()


def markings(ctx, kind, baby):
    """Coat marking overlays (transparent except the markings)."""
    sk = Skin(ctx, "horse_baby" if baby else "horse")
    white = Mat(shades("f0ece6", 5, 0.85, 1.05), mottle=0.1, grain=0.15, sss=0.3, grad=0.15)
    black = Mat(shades("2a2422", 5, 0.8, 1.2), mottle=0.1, grain=0.15, sss=0.3, grad=0.15)
    head = sk.box("head")
    mouth = sk.box("mouth")
    legs = [b for b in sk.boxes if "leg" in b.part]
    if kind == "white":   # socks + blaze
        for l in legs:
            sk.band(l, -4 if not baby else -3, 0, white)
        if mouth is not None:
            sk.frect(mouth, "front", 1, 0, 3, 0, white)
            sk.frect(mouth, "top", 1, 0, 3, 0, white)
            sk.frect(head, "front", 2, 0, 4, 0, white)
            sk.frect(head, "top", 2, 0, 4, 0, white)
        else:
            sk.frect(head, "top", 2, 0, 4, 0, white)
            sk.frect(head, "front", 2, 0, 4, 2, white)
    elif kind == "whitefield":  # large white patches
        for b in sk.boxes:
            if b.part in ("mane", "tail"):
                continue
            for f, r in b.faces.items():
                sk.spots(r, white, 0.45, "big")
    elif kind in ("whitedots", "blackdots"):
        mat = white if kind == "whitedots" else black
        for b in sk.boxes:
            if b.part in ("mane", "tail", "head", "mouth", "left_ear", "right_ear"):
                continue
            for f, r in b.faces.items():
                sl = sk._sl(*r)
                if sl is None:
                    continue
                dots = (sk.grain[sl] > 0.86) & (sk.noise["big"][sl] > 0.35)
                v = mat.base + (sk.noise["mid"][sl] - 0.5) * 0.2
                sk._write(sl, sk.ctx.palette(mat.p, v), mat, height=0.5, mask=dots)
    return sk.tex()


reg([f"entity/horse/{n}{b}" for n in (
    "donkey", "mule", "horse_black", "horse_brown", "horse_chestnut", "horse_creamy", "horse_darkbrown",
    "horse_gray", "horse_white", "horse_zombie", "horse_skeleton", "horse_markings_blackdots",
    "horse_markings_white", "horse_markings_whitedots", "horse_markings_whitefield") for b in ("", "_baby")], horse)


# ---------------------------------------------------------------- llamas

LLAMAS = {"brown": ("8a5a3a", "6a4028"), "creamy": ("e0c898", "c8a878"), "gray": ("9a9690", "6a6660"),
          "white": ("ece8e0", "d0ccc4")}


def llama(ctx, path):
    name = path.split("/")[-1]
    if name == "llama_spit":
        return spit(ctx)
    baby = name.endswith("_baby")
    key = name.replace("_baby", "")[6:]
    coat_c, dark_c = LLAMAS[key]
    sk = Skin(ctx, "llama_baby" if baby else "llama")
    wool = Mat(coat_c, mottle=0.4, grain=0.25, sss=0.35, porosity=0.5, relief=0.5,
               blotch=(dark_c, 0.68, "big") if key in ("creamy", "brown") else None)
    face = Mat(mix(coat_c, "ffffff", 0.15), mottle=0.15, grain=0.15, sss=0.35)
    sk.paint_all([("chest", None)], wool, skip=("chest",))
    for b in sk.find("chest"):
        sk.paint(b, Mat("8a5a30", grain=0.2, mottle=0.2, sss=0.0, streak=0.6))
        sk.frect(b, "left", 3, 3, 5, 5, "b8b0a0", height=0.7)
        sk.frect(b, "right", 3, 3, 5, 5, "b8b0a0", height=0.7)
    heads = sk.find("head")
    neck = max(heads, key=lambda b: b.h)        # tall neck/head box
    snout = [b for b in heads if b is not neck and b.d >= b.w][:1]
    snout = snout[0] if snout else None
    if snout is not None and snout.d / sk.k >= 3:
        sk.paint(snout, face)
        sk.sym(snout, "front", 0, 1, 1, 2, "2a2220", height=0.3)
        sk.frect(snout, "front", 1, -1, -1, 0, "4a3a34", height=0.3)
    ey = 1 if not baby else 2
    sk.frect(neck, "front", 0, 0, 0, 4 if not baby else 5, face)
    sk.sym(neck, "front", 1 if not baby else 0, ey, 2 if not baby else 1, ey + 1, PUPIL, height=0.4, smooth=0.7)
    sk.sym(neck, "front", 0 if not baby else 0, ey - 1, 2 if not baby else 1, ey, mix(coat_c, "000000", 0.3))
    for b in heads:
        if b is not neck and b is not snout:
            sk.paint(b, wool.but(base=0.5))
    for l in sk.boxes:
        if "leg" in l.part:
            sk.band(l, -1, 0, Mat("4a3a30", grain=0.15, sss=0.0), bottom=True)
    return sk.tex(grain=0.06)


def spit(ctx):
    sk = Skin(ctx, "llama_spit")
    sk.paint_all([], Mat("e8ecd8", mottle=0.2, grain=0.3, sss=0.3, smooth=0.6, alpha=0.9))
    return sk.tex()


reg([f"entity/llama/llama_{k}{b}" for k in LLAMAS for b in ("", "_baby")] + ["entity/llama/llama_spit"], llama)


# ---------------------------------------------------------------- camels

def camel(ctx, path):
    name = path.split("/")[-1]
    husk = name == "camel_husk"
    baby = name.endswith("_baby")
    sk = Skin(ctx, "camel_husk" if husk else ("camel_baby" if baby else "camel"))
    coat_c = "8a7a5a" if husk else "d0a868"
    coat = Mat(coat_c, mottle=0.25, grain=0.22, sss=0.3, streak=0.4,
               blotch=(mix(coat_c, "3a3020", 0.4), 0.64, "mid") if husk else None)
    shag = Mat(mix(coat_c, "5a3a20", 0.3), mottle=0.4, grain=0.3, streak=1.0, sss=0.3)
    sk.paint_all([("hump", shag), ("tail", shag)], coat)
    heads = sk.find("head")
    head = max(heads, key=lambda b: b.d)          # long head box
    neck = max(heads, key=lambda b: b.h)
    for b in heads:
        if b is not head and b is not neck:      # snout
            sk.paint(b, coat.but(base=0.62, blotch=None))
            sk.sym(b, "front", 1, 1, 2, 2, "2a2018", height=0.3)
            sk.frect(b, "front", 1, -1, -1, 0, "3a2a20", height=0.3)
    sk.paint(neck, shag, faces=("front",))
    side_eyes(sk, head, fy=2 if not baby else 1, white=None, from_front=3 if not baby else 1,
              pupil="1a1210" if not husk else "c8b040")
    if husk:
        side_eyes(sk, head, fy=2 if not baby else 1, white=None, from_front=3, pupil="d8c050")
        for b in sk.boxes:
            for f, r in b.faces.items():
                sk.spots(r, Mat("4a3a2a", grain=0.2), 0.8, "small")
    for l in sk.boxes:
        if "leg" in l.part:
            sk.band(l, -2, 0, Mat(mix(coat_c, "2a2018", 0.5), grain=0.2), bottom=True)
            sk.band(l, 6 if not baby else 4, 8 if not baby else 5, shag)   # knee pads
    return sk.tex()


reg(["entity/camel/camel", "entity/camel/camel_baby", "entity/camel/camel_husk"], camel)
