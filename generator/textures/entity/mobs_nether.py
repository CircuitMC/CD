"""Nether & floating mobs: blaze, ghasts, hoglins, piglins, striders, magma cube, slime,
sulfur cube, wither (entity_mobs)."""
import numpy as np

from ...registry import register
from .mobs_base import SIDES, Mat, Skin, col, mix, shades

PUPIL = "1a1614"


def reg(paths, fn, *args):
    for p in paths:
        register(p, lambda ctx, p=p: fn(ctx, p, *args))


def lava_cracks(sk, b, thr=0.12, emit=0.9, c=("e85a10", "ffc040"), key="crk"):
    """Glowing crack network on the faces of a box (Voronoi edges)."""
    if b is None:
        return
    if key not in sk.noise:
        vo = sk.ctx.voronoi(max(6, int(sk.ctx.w * sk.ctx.h / 90)), salt="lava", min_dist=3)
        sk.noise[key] = vo["f2"] - vo["f1"]
    for f, r in b.faces.items():
        sl = sk._sl(*r)
        if sl is None:
            continue
        e = sk.noise[key][sl]
        m = e < thr * 4
        hot = e < thr * 2
        cc = np.where(hot[..., None], col(c[1]), col(c[0]))
        sk._write(sl, cc, None, height=0.3, mask=m, emissive=emit, sss=0.0, smooth=0.4)


# ---------------------------------------------------------------- blaze

def blaze(ctx, path):
    sk = Skin(ctx, "blaze")
    head = sk.box("head")
    sk.paint(head, Mat("d89a2a", mottle=0.35, grain=0.3, sss=0.1, emissive=0.15,
                       blotch=("f0d050", 0.6, "mid")))
    rod = Mat("e0a020", mottle=0.2, grain=0.25, grad=0.4, sss=0.0, smooth=0.4, emissive=0.5)
    for b in sk.find("stick"):
        sk.paint(b, rod)
    sk.sym(head, "front", 1, 3, 3, 4, "2a1a10", height=0.3)
    sk.sym(head, "front", 2, 3, 3, 4, "fff0a0", height=0.35, emissive=1.0)
    sk.frect(head, "front", 1, 5, 7, 6, "6a3010", height=0.3)
    sk.frect(head, "front", 2, 6, 6, 7, "3a1a08", height=0.3)
    sk.frect(head, "front", 0, 2, 8, 3, "b86a18", height=0.55)
    return sk.tex()


reg(["entity/blaze/blaze"], blaze)


# ---------------------------------------------------------------- ghasts

GHAST = Mat(shades("e8e8e6", 6, 0.78, 1.04), mottle=0.25, grain=0.2, grad=0.25, sss=0.5, smooth=0.2)


def ghast(ctx, path):
    shooting = path.endswith("shooting")
    sk = Skin(ctx, "ghast")
    sk.paint_all([("tentacle", GHAST.but(base=0.5))], GHAST)
    body = sk.box("body")
    tear = "8a8a90"
    if shooting:
        sk.sym(body, "front", 2, 4, 6, 7, "1a1416", height=0.25)
        sk.sym(body, "front", 3, 5, 5, 6, "e84030", height=0.3, emissive=0.8)
        sk.frect(body, "front", 5, 10, 11, 14, "1a1416", height=0.2)
        sk.frect(body, "front", 6, 11, 10, 13, "8a1a1a", height=0.25, emissive=0.3)
    else:
        sk.sym(body, "front", 2, 5, 6, 6, "3a3a40", height=0.35)
        sk.frect(body, "front", 6, 11, 10, 12, "4a4a50", height=0.35)
    sk.sym(body, "front", 3, 7 if shooting else 6, 4, 10, tear, height=0.4)
    sk.sym(body, "front", 3, 10, 4, 12, mix(tear, "e8e8e6", 0.5), height=0.45)
    return sk.tex()


def happy_ghast(ctx, path):
    name = path.split("/")[-1]
    if name == "happy_ghast_ropes":
        return ropes(ctx)
    baby = name.endswith("_baby")
    sk = Skin(ctx, "happy_ghast_baby" if baby else "happy_ghast")
    soft = GHAST.but(p=shades("f0eeec", 6, 0.8, 1.03), mottle=0.3)
    sk.paint_all([("tentacle", soft.but(base=0.5)), ("inner_body", soft.but(alpha=1.0, base=0.62))], soft)
    body = sk.box("body")
    k = sk.k
    # big friendly eyes and a small smile, rosy cheeks
    sk.sym(body, "front", 3, 6, 6, 9, "2a2228", height=0.35, smooth=0.7)
    sk.sym(body, "front", 4, 6, 5, 7, "f8f8ff", height=0.4, smooth=0.8)
    sk.sym(body, "front", 2, 10, 4, 11, "f0a0a8", height=0.5)
    sk.frect(body, "front", 7, 11, 9, 12, "6a4a50", height=0.35)
    sk.frect(body, "front", 6, 10, 7, 11, "6a4a50", height=0.35)
    sk.frect(body, "front", 9, 10, 10, 11, "6a4a50", height=0.35)
    if baby:
        inner = sk.box("inner_body")
        sk.sym(inner, "front", 3, 6, 6, 9, "2a2228", height=0.35)
    return sk.tex()


def ropes(ctx):
    """Harness ropes overlay on the happy ghast (transparent elsewhere)."""
    sk = Skin(ctx, "happy_ghast_ropes")
    rope = Mat("b08a50", mottle=0.15, grain=0.3, sss=0.05, grad=0.2)
    body = sk.box("body")
    for f in SIDES:   # ropes running around the body
        sk.frect(body, f, 0, 4, 0, 5, rope)
        sk.frect(body, f, 0, 11, 0, 12, rope)
    for f in ("front", "back"):   # vertical straps
        sk.frect(body, f, 3, 0, 4, 0, rope)
        sk.frect(body, f, 12, 0, 13, 0, rope)
    sk.frect(body, "top", 3, 0, 4, 0, rope)
    sk.frect(body, "top", 12, 0, 13, 0, rope)
    sk.frect(body, "top", 0, 4, 0, 5, rope)
    sk.frect(body, "top", 0, 11, 0, 12, rope)
    for f in ("front", "back"):   # knots
        for x in (3, 12):
            for y in (4, 11):
                sk.frect(body, f, x - 0.5, y - 0.5, x + 1.5, y + 1.5, "8a6a38", height=0.7)
    return sk.tex()


reg(["entity/ghast/ghast", "entity/ghast/ghast_shooting"], ghast)
reg(["entity/ghast/happy_ghast", "entity/ghast/happy_ghast_baby", "entity/ghast/happy_ghast_ropes"], happy_ghast)


# ---------------------------------------------------------------- hoglins

def hoglin(ctx, path):
    name = path.split("/")[-1]
    baby = name.endswith("_baby")
    zog = name.startswith("zoglin")
    sk = Skin(ctx, ("zoglin" if zog else "hoglin") + ("_baby" if baby else ""))
    hide_c = "b8786a" if zog else "8a5a3a"
    hide = Mat(hide_c, mottle=0.3, grain=0.25, sss=0.3,
               blotch=(mix(hide_c, "4a6a3a", 0.35), 0.62, "mid") if zog else None)
    bristle = Mat("d8d0b8" if zog else "e0b880", mottle=0.3, grain=0.35, streak=1.0, sss=0.2)
    tusk = Mat("ece4cc", mottle=0.1, grain=0.15, grad=0.4, sss=0.0, smooth=0.4)
    sk.paint_all([("mane", bristle), ("body#1", bristle)], hide)
    heads = sk.find("head")
    head = max(heads, key=lambda b: b.w * b.h * b.d)
    for b in heads:
        if b is not head:
            sk.paint(b, tusk)
    # snout plate on the front face; eyes on the sides near the front
    sk.frect(head, "front", 2, 1, -2, -1, hide.but(base=0.4, blotch=None))
    sk.sym(head, "front", 4 if not baby else 2, 2, 6 if not baby else 4, 4 if not baby else 3,
           mix(hide_c, "000000", 0.6), height=0.3)
    eye = "e8e0c0" if zog else "1a1210"
    for f in ("right", "left"):
        if f in head.faces:
            dm = head.d / sk.k
            x = dm - 4 if f == "right" else 3
            sk.frect(head, f, x, 1, x + 1, 2, eye, height=0.4, emissive=0.4 if zog else 0.0)
    body = sk.largest("body")
    sk.frect(body, "top", 5 if not baby else 3, 0, -5 if not baby else -3, 0, bristle)   # dorsal ridge
    if zog:
        for f in ("left", "right"):
            for i in range(3):
                x = 8 + i * 3 if not baby else 4 + i * 2
                sk.frect(body, f, x, 4 if not baby else 2, x + 1, 9 if not baby else 5, "e8e0c8", height=0.6)
    for l in sk.boxes:
        if "leg" in l.part:
            sk.band(l, -2 if not baby else -1, 0, Mat("3a2a24", grain=0.15, sss=0.0), bottom=True)
    for e in sk.find("left_ear") + sk.find("right_ear"):
        sk.paint(e, hide.but(base=0.45))
    return sk.tex()


reg(["entity/hoglin/hoglin", "entity/hoglin/hoglin_baby", "entity/hoglin/zoglin", "entity/hoglin/zoglin_baby"],
    hoglin)


# ---------------------------------------------------------------- piglins

def piglin(ctx, path):
    name = path.split("/")[-1]
    baby = name.endswith("_baby")
    zomb = name.startswith("zombified")
    brute = name == "piglin_brute"
    model = name
    sk = Skin(ctx, model)
    skin_c = "c88a7a" if not zomb else "d8a090"
    skin = Mat(skin_c, mottle=0.25, grain=0.22, sss=0.4,
               blotch=(mix(skin_c, "5a7a4a", 0.45), 0.6, "mid") if zomb else None)
    cloth = Mat("6a4a2a" if not brute else "3a3a3a", mottle=0.25, grain=0.2, sss=0.05)
    gold = Mat("e8c040", mottle=0.15, grain=0.2, grad=0.4, sss=0.0, smooth=0.7, metal=231)
    heads = sk.find("head")
    head = max(heads, key=lambda b: b.w * b.h * b.d)
    sk.paint(head, skin)
    for b in heads:
        if b is head:
            continue
        if b.w / sk.k >= 3:   # snout
            sk.paint(b, skin.but(base=0.65, blotch=None))
            sk.sym(b, "front", 1 if b.w / sk.k >= 4 else 0, 1, 2 if b.w / sk.k >= 4 else 1, 2 if b.w / sk.k >= 4 else 3,
                   mix(skin_c, "2a1010", 0.6), height=0.3)
        else:                 # tusks
            sk.paint(b, Mat("ece4cc", grain=0.1, sss=0.0, smooth=0.4))
    for e in sk.find("left_ear") + sk.find("right_ear"):
        sk.paint(e, skin.but(base=0.48))
        if not zomb:
            sk.band(e, 0, 1, gold) if not baby else None
    hw = head.w / sk.k
    ey = 3 if not baby else 2
    eye = "e8d0c0" if not zomb else "c8e0b0"
    sk.sym(head, "front", 1, ey, 3, ey + 1, eye, height=0.45, smooth=0.6, sss=0.0)
    sk.sym(head, "front", 2, ey, 3, ey + 1, PUPIL if not zomb else "4a5a30", height=0.4)
    sk.sym(head, "front", 1, ey - 1, 3, ey, mix(skin_c, "2a1010", 0.45), height=0.55)
    if not baby:
        sk.frect(head, "top", 0, 0, 0, 0, skin)
        sk.frect(head, "front", 0, 0, 0, 1, Mat("3a2418" if not zomb else "4a4038", grain=0.25))   # bristly hair
    if zomb:  # exposed skull on one side
        sk.frect(head, "front", hw - 4, 1, hw - 1, 4 if not baby else 3, "e0dcc8", height=0.55)
        sk.frect(head, "front", hw - 3, ey, hw - 2, ey + 1, "1a1410", height=0.3)
    body = sk.box("body")
    sk.paint(body, cloth if not zomb else cloth.but(p=shades("5a5040")))
    sk.frect(body, "front", 0, 0, 2 if not baby else 1, 0, skin)   # open vest
    sk.frect(body, "front", -2 if not baby else -1, 0, 0, 0, skin)
    sk.band(body, -4 if not baby else -2, -3 if not baby else -1, Mat("4a2a1a", grain=0.1, sss=0.0))
    for a in sk.find("left_arm", 0) + sk.find("right_arm", 0):
        sk.paint(a, skin)
        if brute:
            sk.band(a, 0, 3, Mat("3a3a3a", grain=0.2, sss=0.0))
        elif not zomb:
            sk.band(a, -4 if not baby else -2, -3 if not baby else -1, gold)   # gold bracelet
    for l in sk.find("left_leg", 0) + sk.find("right_leg", 0):
        sk.paint(l, Mat("4a3a2a" if not zomb else "4a4a3a", grain=0.2, sss=0.05))
        sk.band(l, -2 if not baby else -1, 0, Mat("2a1e16", grain=0.1), bottom=True)
    # outer layers: belt, gold chains / brute armor straps
    jacket = sk.box("jacket")
    if jacket is not None:
        if brute:
            sk.frect(jacket, "front", 0, 0, 0, 2, Mat("e8c040", grain=0.2, metal=231, smooth=0.7))
            sk.frect(jacket, "back", 0, 0, 0, 2, Mat("e8c040", grain=0.2, metal=231, smooth=0.7))
        else:
            sk.frect(jacket, "front", 2, 0, 3, 6, gold if not zomb else Mat("8a8a60", grain=0.2))
            sk.frect(jacket, "front", 5, 0, 6, 6, gold if not zomb else Mat("8a8a60", grain=0.2))
            sk.band(jacket, 9, 10, Mat("5a3a20", grain=0.15))
    for b in sk.find("left_pants") + sk.find("right_pants"):
        sk.band(b, 0, 2, Mat("5a3a20" if not brute else "2a2a2a", grain=0.15))
    for b in sk.find("left_sleeve") + sk.find("right_sleeve"):
        if brute:
            sk.band(b, 0, 2, Mat("e8c040", grain=0.2, metal=231, smooth=0.7))
    if zomb:
        for b in [body] + sk.find("left_leg") + sk.find("right_leg"):
            for f in SIDES:
                if b is not None and f in b.faces:
                    x0, y0, x1, y1 = b.faces[f]
                    sk.spots((x0, y0 + (y1 - y0) * 0.5, x1, y1), skin, 0.7, "small")
    return sk.tex()


reg(["entity/piglin/piglin", "entity/piglin/piglin_baby", "entity/piglin/piglin_brute",
     "entity/piglin/zombified_piglin", "entity/piglin/zombified_piglin_baby"], piglin)


# ---------------------------------------------------------------- striders

def strider(ctx, path):
    name = path.split("/")[-1]
    baby = name.endswith("_baby")
    cold = "cold" in name
    sk = Skin(ctx, "strider_baby" if baby else "strider")
    skin_c = "9a3a3a" if not cold else "6a5a7a"
    skin = Mat(skin_c, mottle=0.3, grain=0.25, sss=0.3, blotch=(mix(skin_c, "e0603a" if not cold else "8a8aa0", 0.4),
                                                                 0.62, "mid"))
    hair = Mat("e8d0a0" if not cold else "9a9ab0", mottle=0.2, grain=0.3, streak=1.0, sss=0.2)
    sk.paint_all([("hair", hair), ("bristle", hair)], skin)
    body = sk.box("body")
    ey = 3 if not baby else 2
    sk.sym(body, "front", 2 if not baby else 1, ey, 5 if not baby else 3, ey + 2 if not baby else ey + 1,
           "e8e0d0", height=0.45)
    sk.sym(body, "front", 4 if not baby else 2, ey, 5 if not baby else 3, ey + 2 if not baby else ey + 1, PUPIL,
           height=0.4)
    sk.frect(body, "front", 4 if not baby else 2, -4 if not baby else -2, -4 if not baby else -2,
             -3 if not baby else -1, "3a1414", height=0.3)
    for l in sk.find("left_leg") + sk.find("right_leg"):
        sk.band(l, -2 if not baby else -1, 0, skin.but(base=0.3), bottom=True)
    return sk.tex()


reg(["entity/strider/strider", "entity/strider/strider_baby", "entity/strider/strider_cold",
     "entity/strider/strider_cold_baby"], strider)


# ---------------------------------------------------------------- magma cube & slime

def magma_cube(ctx, path):
    sk = Skin(ctx, "magma_cube")
    crust = Mat("3a1a14", mottle=0.35, grain=0.3, sss=0.0, smooth=0.25, blotch=("5a2a1a", 0.6, "mid"))
    sk.paint_all([("core", Mat("f08020", mottle=0.3, grain=0.3, sss=0.0, emissive=1.0, smooth=0.5))], crust)
    for b in sk.find("segment"):
        lava_cracks(sk, b, thr=0.1)
    s3 = sk.box("segment3")
    s4 = sk.box("segment4")
    for s in (s3, s4):
        if s is not None:
            sk.sym(s, "front", 1, 0, 3, 1, "ffd040", emissive=1.0, height=0.3)
    s6 = sk.box("segment6")
    if s6 is not None:
        sk.frect(s6, "front", 2, 0, 6, 1, "1a0a08", height=0.2)
    return sk.tex()


def slime(ctx, path):
    sk = Skin(ctx, "slime")
    outer = Skin(ctx, "slime_outer")
    jelly = Mat("6ac850", mottle=0.25, grain=0.2, sss=0.6, smooth=0.75, alpha=0.75)
    core = Mat("4aa838", mottle=0.25, grain=0.25, sss=0.6, smooth=0.6)
    for b in outer.boxes:
        sk.paint(Box_like(sk, b), jelly)
    sk.paint(sk.box("body"), core)
    sk.paint(sk.box("right_eye"), Mat("1a3a14", grain=0.1, sss=0.0, smooth=0.7))
    sk.paint(sk.box("left_eye"), Mat("1a3a14", grain=0.1, sss=0.0, smooth=0.7))
    sk.paint(sk.box("mouth"), Mat("2a5a1e", grain=0.1, sss=0.0))
    return sk.tex()


def Box_like(sk, b):
    return b   # same image size and scale: boxes are interchangeable


reg(["entity/slime/magmacube"], magma_cube)
reg(["entity/slime/slime"], slime)


def sulfur_cube(ctx, path):
    name = path.split("/")[-1]
    small = name.endswith("_small")
    inner = "inner" in name
    model = "sulfur_cube" + ("_small" if small else "") + ("_inner" if inner else "")
    sk = Skin(ctx, model)
    if inner:
        m = Mat("c8b020", mottle=0.4, grain=0.3, sss=0.4, smooth=0.4, blotch=("e8d850", 0.62, "mid"))
        sk.paint_all([], m)
        b = sk.boxes[0]
        sk.sym(b, "front", 3 if not small else 2, 5 if not small else 3, 6 if not small else 4,
               7 if not small else 4, "3a3008", height=0.3)
        sk.frect(b, "front", 6 if not small else 4, -5 if not small else -3, -6 if not small else -4,
                 -4 if not small else -2, "3a3008", height=0.3)
    else:
        m = Mat("e8e070", mottle=0.3, grain=0.2, sss=0.5, smooth=0.8, alpha=0.6)
        sk.paint_all([], m)
        for b in sk.boxes:
            for f, r in b.faces.items():
                sk.spots(r, Mat("f8f4b0", grain=0.1, alpha=0.8, smooth=0.9), 0.75, "small")
    return sk.tex()


reg([f"entity/sulfur_cube/sulfur_cube_{a}{b}" for a in ("inner", "outer") for b in ("", "_small")], sulfur_cube)


# ---------------------------------------------------------------- wither

def wither(ctx, path):
    name = path.split("/")[-1]
    if name == "wither_armor":
        sk = Skin(ctx, "wither_armor")
        n = ctx.noise(4, 2, 0.5, salt="warmor")
        swirl = np.sin((ctx.x - ctx.y) * 0.8 + n * 7.0)
        m = swirl > 0.3
        sk.color[:] = np.where(m[..., None], col("9ab8ff"), col("4a5ad8"))
        sk.alpha[:] = np.where(m, 0.8, 0.0)
        sk.emissive[:] = np.where(m, 0.8, 0.0)
        sk.height[:] = 0.5
        return sk.tex(grain=0)
    inv = name == "wither_invulnerable"
    sk = Skin(ctx, "wither")
    bone = Mat(shades("3a3a3e" if not inv else "6a7aa8", 6, 0.6, 1.35), mottle=0.3, grain=0.25, sss=0.05,
               smooth=0.3, emissive=0.0 if not inv else 0.2)
    sk.paint_all([], bone)
    glow = "e8e8f0" if not inv else "c8e0ff"
    for i, key in enumerate(("head1", "head2", "head3")):
        h = sk.box(key)
        if h is None:
            continue
        hw = h.w / sk.k
        big = hw >= 8
        sk.sym(h, "front", 1, 2 if big else 1, 3, 4 if big else 3, "0e0e10", height=0.2)
        sk.sym(h, "front", 2, 3 if big else 2, 3, 4 if big else 3, glow, height=0.25, emissive=0.8)
        for x in range(1, int(hw) - 1, 2):
            sk.frect(h, "front", x, hw - 2, x + 1, hw - 1, "0e0e10", height=0.25)
    for b in sk.find("body2", 1) + sk.find("body2", 2) + sk.find("body2", 3):
        sk.band(b, 0, 2, bone.but(base=0.65))
    return sk.tex()


reg(["entity/wither/wither", "entity/wither/wither_armor", "entity/wither/wither_invulnerable"], wither)
