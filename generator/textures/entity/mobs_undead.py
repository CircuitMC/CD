"""Zombies, skeletons, creeper, spiders, enderman (entity_mobs)."""
from ...registry import register
from .mobs_base import Mat, Skin, col, mix, shades

SIDES = ("front", "back", "left", "right")


def reg(paths, fn, *args):
    for p in paths:
        register(p, lambda ctx, p=p: fn(ctx, p, *args))


def overlay_boxes(sk):
    """Boxes of outer layers (hat / jacket / sleeves) in humanoid layouts."""
    return [b for b in sk.boxes if b.part in ("headwear", "hat", "jacket") or "sleeve" in b.part
            or "pants" in b.part]


# ---------------------------------------------------------------- zombies

ZOMBIE_SKIN = Mat("5f8a4a", mottle=0.35, grain=0.35, sss=0.3, blotch=("4d7240", 0.62, "mid"))
HUSK_SKIN = Mat("a89670", mottle=0.35, grain=0.35, sss=0.25, blotch=("8e7b58", 0.6, "mid"))
DROWNED_SKIN = Mat("5a9a90", mottle=0.35, grain=0.35, sss=0.35, blotch=("4a8078", 0.6, "mid"))


def humanoid_body(sk, skin, shirt, pants, shoe=None, sleeve=4, hem=0, torn=True, belt=None):
    head = sk.box("head")
    sk.paint(head, skin)
    body = sk.box("body")
    sk.paint(body, shirt)
    if hem and body:
        sk.band(body, -hem, 0, pants)
    if belt is not None and body:
        sk.band(body, -hem - 1, -hem if hem else 0, Mat(belt, grain=0.15, sss=0.0))
    for key in ("right_arm", "left_arm"):
        for a in sk.find(key, 0):
            sk.paint(a, skin)
            if sleeve:
                sk.band(a, 0, sleeve, shirt, top=True)
    for key in ("right_leg", "left_leg"):
        for l in sk.find(key, 0):
            sk.paint(l, pants)
            if shoe is not None:
                sk.band(l, -max(1, round(l.h / sk.k / 6)), 0, shoe, bottom=True)
    if torn:  # ragged hems: skin shows through
        for bb in [body] + sk.find("right_leg", 0) + sk.find("left_leg", 0):
            if bb is None:
                continue
            for f in SIDES:
                if f in bb.faces:
                    x0, y0, x1, y1 = bb.faces[f]
                    sk.spots((x0, y1 - (y1 - y0) * 0.3, x1, y1), skin, 0.68, "small")


def zombie_kind(ctx, path):
    name = path.split("/")[-1]
    baby = "baby" in name
    model = "zombie_baby" if baby else "zombie"
    if name.startswith("husk"):
        model = "husk_baby" if baby else "husk"
    if name.startswith("drowned"):
        model = ("drowned_baby" if baby else "drowned") + ("_outer" if "outer" in name else "")
    sk = Skin(ctx, model)
    if "outer" in name:
        return drowned_outer(sk, baby)
    if name.startswith("husk"):
        skin, shirt, pants, shoe = HUSK_SKIN, Mat("6f5a3c", mottle=0.3, sss=0.1), Mat("4b4436", sss=0.1), Mat("3a2c20")
        eye, glint = "2a2116", "e0c070"
    elif name.startswith("drowned"):
        skin, shirt, pants, shoe = DROWNED_SKIN, Mat("5d7d6a", mottle=0.4, sss=0.1, blotch=("3f6a52", 0.6, "small")), \
            Mat("3b4f5a", sss=0.1), None
        eye, glint = "123a3a", "6ff0e0"
    else:
        skin, shirt, pants, shoe = ZOMBIE_SKIN, Mat("7a6a58", mottle=0.3, sss=0.1), Mat("3e4a5a", sss=0.1), Mat("38302c")
        eye, glint = "1b2418", "a8d890"
    humanoid_body(sk, skin, shirt, pants, shoe, sleeve=5 if not baby else 2, hem=0)
    head = sk.box("head")
    if baby:
        sk.sym(head, "front", 1, 2, 2, 4, eye, height=0.25)
        sk.sym(head, "front", 1, 3, 2, 4, glint, height=0.3)
        sk.frect(head, "front", 2, 4, 4, 5, eye, height=0.3)
    else:
        sk.tint(head, "front", 0, 2, 8, 3, 0.86)
        sk.sym(head, "front", 1, 3, 3, 5, eye, height=0.25)
        sk.sym(head, "front", 2, 4, 3, 5, glint, height=0.3, smooth=0.5)
        sk.frect(head, "front", 3, 5, 5, 6, col(skin.p[1]), height=0.6)
        sk.frect(head, "front", 2, 6, 6, 7, eye, height=0.3)
        sk.frect(head, "front", 4, 7, 5, 8, eye, height=0.3)
    if name.startswith("drowned"):
        if baby:
            sk.sym(head, "front", 1, 3, 2, 4, glint, emissive=0.6, height=0.3)
        else:
            sk.sym(head, "front", 2, 4, 3, 5, glint, emissive=0.6, height=0.3)
        # seaweed hair on top
        sk.face_spots(head, Mat("3f7a3a", grain=0.3), 0.5, "streak", faces=("top",))
    return sk.tex()


def drowned_outer(sk, baby):
    """Outer layer: tattered clothing scraps + kelp strands (mostly transparent)."""
    rag = Mat("4d6e7a", mottle=0.4, grain=0.35, sss=0.05)
    kelp = Mat("3d7a34", mottle=0.3, grain=0.35, sss=0.4)
    for b in sk.boxes:
        hd = b.part in ("head", "headwear")
        for f, r in b.faces.items():
            sl = sk._sl(*r)
            if sl is None:
                continue
            fy = (sk.ctx.y[sl] - r[1]) / max(r[3] - r[1], 1)
            if hd:
                m = sk.noise["streak"][sl] > (0.45 if f == "top" else 0.58)
                if f == "front":
                    m &= fy < 0.3
                if f == "bottom":
                    m &= False
                v = 0.5 + (sk.grain[sl] - 0.5) * 0.4 + (sk.noise["mid"][sl] - 0.5) * 0.3
                sk._write(sl, sk.ctx.palette(kelp.p, v), kelp, height=0.6, mask=m)
            else:
                sk.fill(r, rag, off=FACE_OFF_SAFE(f))
                cut = (sk.noise["mid"][sl] > 0.6) | ((fy > 0.8) & (sk.grain[sl] > 0.5))
                sk.alpha[sl][cut] = 0
    return sk.tex()


reg(["entity/zombie/zombie", "entity/zombie/zombie_baby", "entity/zombie/husk", "entity/zombie/husk_baby",
     "entity/zombie/drowned", "entity/zombie/drowned_baby", "entity/zombie/drowned_outer_layer",
     "entity/zombie/drowned_outer_layer_baby"], zombie_kind)


# ---------------------------------------------------------------- skeletons

BONE = Mat(shades("c9c4b2", 6, 0.72, 1.1), mottle=0.25, grain=0.22, grad=0.2, sss=0.15, smooth=0.25)
STRAY_BONE = Mat(shades("b9c6c8", 6, 0.72, 1.1), mottle=0.25, grain=0.22, grad=0.2, sss=0.15, smooth=0.3)
WITHER_BONE = Mat(shades("3a3a3c", 6, 0.55, 1.35), mottle=0.25, grain=0.3, grad=0.2, sss=0.05, smooth=0.3)
BOG_BONE = Mat(shades("a8ae8a", 6, 0.55, 1.12), mottle=0.35, grain=0.3, grad=0.2, sss=0.15,
               blotch=(shades("6f8a56", 6, 0.55, 1.1), 0.62, "mid"))
PARCHED_BONE = Mat(shades("d8c49a", 6, 0.72, 1.1), mottle=0.3, grain=0.22, grad=0.2, sss=0.1, smooth=0.2)


def skull_face(sk, b, bone, socket="231f1d", glow=None):
    dark = col(bone.p[0]) * 0.75
    sk.sym(b, "front", 1, 3, 3, 5, socket, height=0.2)
    sk.sym(b, "front", 1, 2, 3, 3, col(bone.p[1]), height=0.45)
    if glow:
        sk.sym(b, "front", 2, 4, 3, 5, glow, emissive=0.7, height=0.25)
    sk.frect(b, "front", 3, 5, 5, 6, socket, height=0.25)            # nasal cavity
    sk.frect(b, "front", 4, 5, 5, 6, dark, height=0.25)
    for i in range(1, 7):                                              # teeth row
        sk.frect(b, "front", i, 6, i + 1, 7, socket if i % 2 else col(bone.p[4]), height=0.4 + (i % 2) * 0.2)
    sk.frect(b, "front", 1, 7, 7, 8, col(bone.p[2]), height=0.5)
    sk.frect(b, "front", 2, 7, 6, 8, col(bone.p[1]), height=0.5)


def rib_body(sk, bone, gap="1c1a19"):
    body = sk.box("body")
    if body is None:
        return
    sk.paint(body, bone)
    # ribcage: dark gaps between ribs on front/back, spine in the middle
    for f in ("front", "back"):
        for y in (1, 3, 5, 7):
            sk.frect(body, f, 1, y, 3, y + 1, gap, height=0.15)
            sk.frect(body, f, 5, y, 7, y + 1, gap, height=0.15)
        sk.frect(body, f, 0, 9, 3, 10, gap, height=0.15)
        sk.frect(body, f, 5, 9, 8, 10, gap, height=0.15)
        sk.frect(body, f, 3, 0, 5, 12, col(bone.p[3]), height=0.65)
        sk.frect(body, f, 3, 10, 5, 11, col(bone.p[2]), height=0.6)
    for f in ("left", "right"):
        for y in (1, 3, 5, 7):
            sk.frect(body, f, 0, y, 4, y + 1, gap, height=0.15)


def bone_limbs(sk, bone):
    for key in ("right_arm", "left_arm", "right_leg", "left_leg"):
        for b in sk.find(key, 0):
            sk.paint(b, bone)
            sk.band(b, 5, 6, bone.but(base=0.75), off=0.0)  # joint knob


def skeleton(ctx, path):
    name = path.split("/")[-1]
    model = {"skeleton": "skeleton", "stray": "stray", "wither_skeleton": "wither_skeleton",
             "bogged": "bogged", "parched": "parched"}.get(name, name)
    if name == "stray_overlay":
        return stray_overlay(Skin(ctx, "stray_outer"))
    if name == "bogged_overlay":
        return bogged_overlay(Skin(ctx, "bogged_outer"))
    sk = Skin(ctx, model)
    bone = {"skeleton": BONE, "stray": STRAY_BONE, "wither_skeleton": WITHER_BONE, "bogged": BOG_BONE,
            "parched": PARCHED_BONE}[name]
    head = sk.box("head")
    sk.paint(head, bone)
    glow = {"wither_skeleton": None, "stray": "9fd6ff", "bogged": "b8e070"}.get(name)
    skull_face(sk, head, bone, socket="0f0e0e" if name != "wither_skeleton" else "000000", glow=glow)
    if name == "wither_skeleton":
        sk.sym(head, "front", 2, 4, 3, 5, "4a4a4e", height=0.25)
    rib_body(sk, bone)
    bone_limbs(sk, bone)
    if name == "bogged":
        moss = Mat("4f7a32", mottle=0.3, grain=0.4, sss=0.5)
        for b in sk.boxes:
            for f, r in b.faces.items():
                if not b.part.startswith("mush"):
                    sk.spots(r, moss, 0.7, "big")
        # mushrooms (crossed planes): red and brown caps on stalks
        for b in sk.find("mushrooms"):
            for f, (x0, y0, x1, y1) in b.faces.items():
                if f not in ("front", "back", "left", "right"):
                    continue
                k = sk.k
                cap = "b8332c" if b.idx % 2 == 0 else "9a6a44"
                sk.rect(x0 + 1 * k, y0, x1 - 1 * k, y0 + 2 * k, cap, height=0.7, sss=0.3)
                sk.rect(x0 + 2 * k, y0 + 2 * k, x0 + 3 * k, y1, "d9cfb0", height=0.6, sss=0.3)
                sk.rect(x0 + 2 * k, y0, x0 + 3 * k, y0 + 1 * k, "e8e0d0", height=0.75)
    if name == "parched":
        wrap = Mat("c8b388", mottle=0.35, grain=0.35, sss=0.1, streak=0.6, n=5)
        for b in sk.boxes:
            if b.idx >= 1:  # outer wraps
                for f, r in b.faces.items():
                    sk.fill(r, wrap, off=FACE_OFF_SAFE(f))
                    sl = sk._sl(*r)
                    if sl is not None:
                        cut = sk.noise["streak"][sl] > 0.6
                        if b.part == "head" and f == "front":
                            cut = cut | (sk.ctx.y[sl] - r[1] > 2.5 * sk.k) & (sk.ctx.y[sl] - r[1] < 5 * sk.k)
                        sk.alpha[sl][cut] = 0
                        # wrap bands: darker lines every 3 texels
                        band = ((sk.ctx.ty[sl] - int(r[1])) % 3 == 0) & ~cut
                        sk.color[sl][band] *= 0.8
        belt = sk.box("body", 1)
        if belt:
            sk.paint(belt, Mat("7a4e2e", sss=0.05))
    return sk.tex()


def FACE_OFF_SAFE(f):
    return {"top": 0.08, "bottom": -0.12}.get(f, 0.0)


def stray_overlay(sk):
    """Ragged frosty cloak: fills most faces, holes and frayed bottoms."""
    cloth = Mat("6f8790", mottle=0.35, grain=0.35, sss=0.1, streak=0.5)
    for b in sk.boxes:
        for f, r in b.faces.items():
            if b.part == "headwear" or (b.part == "head" and f == "front"):
                continue
            sk.fill(r, cloth, off=FACE_OFF_SAFE(f))
            sl = sk._sl(*r)
            if sl is None:
                continue
            fy = (sk.ctx.y[sl] - r[1]) / max(r[3] - r[1], 1)
            cut = (sk.noise["streak"][sl] > 0.66) | ((fy > 0.75) & (sk.noise["streak"][sl] > 0.45))
            if b.part == "head":
                cut = cut | (f == "bottom")
            sk.alpha[sl][cut] = 0
    head = sk.box("head")
    if head:  # hood rim
        for f in ("left", "right", "back", "top"):
            if f in head.faces:
                x0, y0, x1, y1 = head.faces[f]
                sk.rect(x0, y0, x1, y1, "5c727b", height=0.55)
        sk.frect(head, "front", 0, 0, 8, 1, "4e646d", height=0.6)
        sk.frect(head, "front", 0, 0, 1, 8, "4e646d", height=0.6)
        sk.frect(head, "front", 7, 0, 8, 8, "4e646d", height=0.6)
    return sk.tex()


def bogged_overlay(sk):
    """Mossy vines and leaves hanging from the bones."""
    vine = Mat("4a7a30", mottle=0.3, grain=0.4, sss=0.5, streak=0.9)
    for b in sk.boxes:
        if b.part == "headwear":
            continue
        for f, r in b.faces.items():
            sl = sk._sl(*r)
            if sl is None:
                continue
            m = sk.noise["streak"][sl] > (0.55 if f != "top" else 0.4)
            if b.part == "head" and f == "front":
                m &= (sk.ctx.y[sl] - r[1]) < 2.5 * sk.k
            v = 0.5 + (sk.grain[sl] - 0.5) * 0.5 + (sk.noise["mid"][sl] - 0.5) * 0.3
            c = sk.ctx.palette(vine.p, v)
            sk.color[sl][m] = c[m]
            sk.alpha[sl][m] = 1
            sk.height[sl][m] = 0.65
            sk.sss[sl][m] = 0.5
    return sk.tex()


reg(["entity/skeleton/skeleton", "entity/skeleton/stray", "entity/skeleton/wither_skeleton",
     "entity/skeleton/bogged", "entity/skeleton/parched", "entity/skeleton/stray_overlay",
     "entity/skeleton/bogged_overlay"], skeleton)


# ---------------------------------------------------------------- creeper

CREEPER = Mat(shades("5fa850", 6, 0.62, 1.2), mottle=0.5, grain=0.35, grad=0.15, sss=0.3,
              blotch=(shades("9ccf86", 6, 0.7, 1.12), 0.66, "mid"))


def creeper(ctx, path):
    if path.endswith("creeper_armor"):
        return charge(ctx)
    sk = Skin(ctx, "creeper")
    sk.paint_all([], CREEPER)
    head = sk.box("head")
    d0, d1 = "141a12", "2a3a26"
    # face: square eyes, frowning mouth (own arrangement)
    sk.sym(head, "front", 1, 2, 3, 4, d0, height=0.15)
    sk.sym(head, "front", 2, 2, 3, 3, d1, height=0.2)
    sk.frect(head, "front", 3, 4, 5, 6, d0, height=0.15)
    sk.sym(head, "front", 2, 5, 3, 7, d0, height=0.15)
    sk.frect(head, "front", 3, 6, 5, 7, d1, height=0.2)
    for l in sk.find("leg"):  # dark feet
        sk.band(l, -1, 0, CREEPER.but(base=0.25), bottom=True)
    return sk.tex()


def charge(ctx):
    """Charged-creeper energy shell: scrolling swirl, translucent cyan, emissive."""
    sk = Skin(ctx, "creeper_charge")
    n = ctx.noise(4, 2, 0.5, salt="charge", stretch=(1, 1))
    import numpy as np
    swirl = np.sin((ctx.x + ctx.y) * 0.9 + n * 6.0)
    m = swirl > 0.35
    c = np.where(m[..., None], col("8fd9ff"), col("3a7ad8"))
    sk.color[:] = c
    sk.alpha[:] = np.where(m, 0.85, 0.0)
    sk.emissive[:] = np.where(m, 0.8, 0.0)
    sk.height[:] = 0.5
    return sk.tex(grain=0)


reg(["entity/creeper/creeper", "entity/creeper/creeper_armor"], creeper)


# ---------------------------------------------------------------- spiders

SPIDER = Mat(shades("3b3330", 6, 0.65, 1.3), mottle=0.35, grain=0.3, grad=0.2, sss=0.1, streak=0.4)
CAVE = Mat(shades("23464a", 6, 0.65, 1.3), mottle=0.35, grain=0.3, grad=0.2, sss=0.1, streak=0.4)


def spider_eyes_on(sk, head, colr, emit=0.0, dark="1a0f0f"):
    # two big eyes + four small ones (own placement)
    sk.sym(head, "front", 1, 3, 3, 5, colr, height=0.6, smooth=0.8, emissive=emit)
    sk.sym(head, "front", 2, 3, 3, 4, mix(colr, "ffffff", 0.45), height=0.65, smooth=0.9, emissive=emit)
    sk.sym(head, "front", 3, 2, 4, 3, colr, height=0.55, smooth=0.8, emissive=emit)
    sk.sym(head, "front", 0, 2, 1, 3, colr, height=0.55, smooth=0.8, emissive=emit)
    if dark:
        sk.sym(head, "front", 1, 5, 3, 6, dark, height=0.35)


def spider(ctx, path):
    name = path.split("/")[-1]
    if name == "spider_eyes":
        sk = Skin(ctx, "spider")
        spider_eyes_on(sk, sk.box("head"), "e02818", emit=1.0, dark=None)
        return sk.tex(grain=0)
    cave = name == "cave_spider"
    mat = CAVE if cave else SPIDER
    sk = Skin(ctx, "cave_spider" if cave else "spider")
    sk.paint_all([("leg", mat.but(base=0.5, streak=0.0))], mat)
    body = sk.box("body")
    # hairy abdomen: lighter chevrons on the top (back) face
    mark = "6b5a52" if not cave else "4c7c74"
    for i, y in enumerate((2, 5, 8)):
        sk.frect(body, "top", 3, y, 7, y + 1, mark, height=0.6)
        sk.frect(body, "top", 4, y + 1, 6, y + 2, mark, height=0.6)
    leg = sk.box("leg1")
    for x in (5, 11):  # leg joints
        for f in SIDES:
            sk.frect(leg, f, x, 0, x + 1, 2, mat.p[0], height=0.4)
    head = sk.box("head")
    spider_eyes_on(sk, head, "c42318" if not cave else "d13a2a")
    sk.frect(head, "front", 3, 6, 5, 8, "2a1d1a", height=0.3)  # fangs gap
    sk.sym(head, "front", 2, 6, 3, 8, "8a7f70", height=0.65)
    return sk.tex()


reg(["entity/spider/spider", "entity/spider/cave_spider", "entity/spider/spider_eyes"], spider)


# ---------------------------------------------------------------- enderman

ENDER = Mat(shades("1e1a22", 6, 0.8, 1.3), mottle=0.3, grain=0.2, grad=0.15, sss=0.1, smooth=0.2)


def enderman(ctx, path):
    sk = Skin(ctx, "enderman")
    if path.endswith("_eyes"):
        head = sk.box("head")
        sk.sym(head, "front", 0, 4, 3, 5, "d68cff", emissive=1.0, height=0.5)
        sk.sym(head, "front", 1, 4, 2, 5, "f6dcff", emissive=1.0, height=0.5)
        return sk.tex(grain=0)
    sk.paint_all([("headwear", None)], ENDER, skip=("headwear",))
    hw = sk.box("headwear")
    # jaw (headwear box): only the lower rim is drawn
    for f in SIDES:
        if f in hw.faces:
            sk.frect(hw, f, 0, 6, 0, 8, ENDER.but(base=0.4))
    head = sk.box("head")
    sk.sym(head, "front", 0, 4, 3, 5, "a64ad8", height=0.4, emissive=0.3)
    sk.sym(head, "front", 1, 4, 2, 5, "e8c0ff", height=0.4, emissive=0.3)
    sk.frect(head, "front", 0, 3, 8, 4, ENDER.p[0], height=0.35)
    return sk.tex()


reg(["entity/enderman/enderman", "entity/enderman/enderman_eyes"], enderman)
