"""Farm animals: cows, mooshrooms, pigs, sheep, chickens, goats (entity_mobs)."""
from ...registry import register
from .mobs_base import SIDES, Mat, Skin, col, mix, shades

WHITE_EYE = "ece6da"
PUPIL = "1c1716"


def reg(paths, fn, *args):
    for p in paths:
        register(p, lambda ctx, p=p: fn(ctx, p, *args))


def underside(sk, b, mat):
    """Paint the belly face of a body box (rotated quadruped body or plain box)."""
    if b is None:
        return
    f = "front" if b.quad else "bottom"
    if f in b.faces:
        sk.fill(b.faces[f], mat, off=-0.05)


def hooves(sk, mat, rows=1, key="leg"):
    for l in sk.boxes:
        if key in l.part:
            sk.band(l, -rows, 0, mat, bottom=True)


def eyes(sk, b, y, x=1, w=2, white=WHITE_EYE, pupil=PUPIL, face="front", lid=None):
    """Eye pair at row y, x texels from each side edge; pupil on the inner side."""
    if b is None or face not in b.faces:
        return
    if w >= 2 and white:
        sk.sym(b, face, x, y, x + w, y + 1, white, height=0.45, smooth=0.6, sss=0.0)
    sk.sym(b, face, x + w - 1, y, x + w, y + 1, pupil, height=0.4, smooth=0.7, sss=0.0)
    if lid:
        sk.sym(b, face, x, y - 1, x + w, y, lid, height=0.55)


# ---------------------------------------------------------------- cows

COWS = {
    # name: (fur, patches, horn, muzzle)
    "temperate": ("5a3a26", ("e8dcc4", 0.6), "d8cfb8", "c99a8a"),
    "cold": ("8a4a2a", None, "e0d6c0", "b07a68"),
    "warm": ("c9b48e", ("8a6a48", 0.68), "ece4d0", "a07870"),
    "mooshroom_red": ("a8282a", ("d8c8c0", 0.62), "d8cfb8", "c9918a"),
    "mooshroom_brown": ("9a6a40", ("e4d4b0", 0.6), "d8cfb8", "b88a76"),
}


def cow(ctx, path):
    name = path.split("/")[-1]
    baby = name.endswith("_baby")
    key = name.replace("_baby", "")
    if key.startswith("cow_"):
        key = key[4:]
    if key.startswith("mooshroom"):
        model = "mooshroom_baby" if baby else "mooshroom"
    else:
        model = {"temperate": "cow", "cold": "cold_cow", "warm": "warm_cow"}[key] + ("_baby" if baby else "")
    fur_c, patch, horn_c, muzzle_c = COWS[key]
    sk = Skin(ctx, model)
    shag = key == "cold"
    fur = Mat(fur_c, mottle=0.3, grain=0.25, streak=0.6 if shag else 0.2, sss=0.3,
              blotch=(patch[0], patch[1], "big") if patch else None)
    horn = Mat(horn_c, mottle=0.1, grain=0.15, grad=0.5, sss=0.05, smooth=0.35)
    muzzle = Mat(muzzle_c, mottle=0.15, grain=0.2, sss=0.4)
    sk.paint_all([], fur)
    head = sk.boxes[0] if not baby else sk.box("head")
    head = sk.largest("head")
    small = [b for b in sk.find("head") if b is not head]
    for b in small:
        if b.w / sk.k >= 3 and b.h / sk.k >= 3 and b.d / sk.k <= 1:   # muzzle box
            sk.paint(b, muzzle)
            sk.sym(b, "front", 1 if b.w / sk.k > 4 else 0, 1, 2 if b.w / sk.k > 4 else 1, 2, mix(muzzle_c, "000000", 0.5),
                   height=0.3)
        else:
            sk.paint(b, horn)
            sk.band(b, 0, 1, horn.but(base=0.85)) if "horn" in b.part else None
    # face
    hw = head.w / sk.k
    ey = 2 if baby else 3
    eyes(sk, head, ey, x=0 if baby else 1, w=2)
    sk.frect(head, "front", 1 if not baby else 1, -2 if baby else -3, -1, 0, muzzle)
    sk.sym(head, "front", 2 if not baby else 1, -2, 3 if not baby else 2, -1, mix(muzzle_c, "000000", 0.5),
           height=0.3)
    if patch and not baby:  # blaze between the eyes
        sk.frect(head, "front", 3, 0, 5, 4, Mat(patch[0], grain=0.15, mottle=0.1, grad=0.0))
    body = sk.largest("body")
    underside(sk, body, fur.but(base=0.42, blotch=None) if not patch else fur.but(base=0.62))
    for b in sk.find("body"):
        if b.w / sk.k == 4 and b.h / sk.k == 6:  # udder
            sk.paint(b, Mat("e0a8a0", grain=0.15, sss=0.5))
    if key == "cold":
        coat = [b for b in sk.find("body") if b is not body and b.h / sk.k >= 10]
        for b in coat:  # long outer fur layer, ragged
            sk.paint(b, fur.but(base=0.62, streak=0.9, mottle=0.35))
            for f, r in b.faces.items():
                sl = sk._sl(*r)
                if sl is not None:
                    sk.alpha[sl][sk.noise["streak"][sl] > 0.72] = 0
        # shaggy fringe over the eyes
        sk.frect(head, "front", 0, 0, 0, 3 if not baby else 2, fur.but(base=0.7, streak=1.0))
    hooves(sk, Mat("3a2c24", grain=0.2, sss=0.0, smooth=0.25), rows=1 if baby else 2)
    if key.startswith("mooshroom"):
        cap = "c83a32" if key.endswith("red") else "a8784e"
        # little mushroom specks on the back
        sk.face_spots(body, Mat(cap, grain=0.25, sss=0.2), 0.8, "small", faces=("back",) if body.quad else ("top",))
    return sk.tex()


reg([f"entity/cow/{n}" for n in ("cow_cold", "cow_cold_baby", "cow_temperate", "cow_temperate_baby", "cow_warm",
                                 "cow_warm_baby", "mooshroom_brown", "mooshroom_brown_baby", "mooshroom_red",
                                 "mooshroom_red_baby")], cow)


# ---------------------------------------------------------------- pigs

PIGS = {
    "temperate": ("e8a0a0", None),
    "cold": ("d89a90", "d8ccb8"),
    "warm": ("a85a3a", None),
}


def pig(ctx, path):
    name = path.split("/")[-1]
    baby = name.endswith("_baby")
    key = name.replace("_baby", "")[4:]
    model = "pig_baby" if baby else {"temperate": "pig", "cold": "cold_pig", "warm": "warm_pig"}[key]
    sk = Skin(ctx, model)
    skin_c, wool_c = PIGS[key]
    skin = Mat(skin_c, mottle=0.25, grain=0.22, sss=0.45,
               blotch=(mix(skin_c, "5a3020", 0.35), 0.72, "small") if key == "warm" else None)
    sk.paint_all([], skin)
    head = sk.largest("head")
    snout = [b for b in sk.find("head") if b is not head]
    for b in snout:
        sk.paint(b, skin.but(base=0.42, blotch=None))
        sk.sym(b, "front", 0 if baby else 0, 1, 1, 2, mix(skin_c, "3a1818", 0.6), height=0.3)
    if baby:
        eyes(sk, head, 2, x=1, w=2)
    else:
        eyes(sk, head, 3, x=0, w=2)
        sk.frect(head, "front", 0, 2, 8, 3, skin.but(base=0.62))
    hooves(sk, Mat(mix(skin_c, "4a2a24", 0.6), grain=0.15, sss=0.1))
    body = sk.largest("body")
    underside(sk, body, skin.but(base=0.62, blotch=None))
    if key == "warm":  # dried mud on the legs and belly
        mud = Mat("5a4030", grain=0.3, sss=0.0, porosity=0.6)
        for l in sk.find("leg") + [b for b in sk.boxes if "_leg" in b.part]:
            sk.band(l, -3 if not baby else -1, 0, mud, bottom=True)
    if key == "cold" and not baby:
        coat = [b for b in sk.find("body") if b is not body]
        wool = Mat(wool_c, mottle=0.35, grain=0.25, sss=0.3, streak=0.3)
        for b in coat:
            sk.paint(b, wool)
            for f, r in b.faces.items():
                sl = sk._sl(*r)
                if sl is not None and f in ("front", "bottom"):
                    sk.alpha[sl] = 0
    if key == "cold" and baby:
        sk.paint(body, Mat(wool_c, mottle=0.35, grain=0.25, sss=0.3))
        sk.frect(head, "front", 0, 0, 0, 1, Mat(wool_c, mottle=0.3))
    return sk.tex()


reg([f"entity/pig/pig_{k}{b}" for k in ("cold", "temperate", "warm") for b in ("", "_baby")], pig)


# ---------------------------------------------------------------- sheep

WOOL = Mat(shades("e6e3dc", 6, 0.72, 1.06), mottle=0.4, grain=0.3, grad=0.2, sss=0.35, porosity=0.6, relief=0.6)
SHEEP_FACE = Mat("4a3c34", mottle=0.15, grain=0.2, sss=0.3)
SHEEP_SKIN = Mat("d8c8b0", mottle=0.25, grain=0.25, sss=0.35)


def curls(sk, b, salt_key="small"):
    """Woolly bumps: light rings with darker cores from noise."""
    for f, r in b.faces.items():
        sl = sk._sl(*r)
        if sl is None:
            continue
        n = sk.noise[salt_key][sl]
        dark = n < 0.3
        sk.color[sl][dark] *= 0.9
        sk.height[sl][dark] = 0.35


def sheep(ctx, path):
    name = path.split("/")[-1]
    baby = "baby" in name
    if "wool" in name:
        under = "undercoat" in name
        sk = Skin(ctx, "sheep_wool_undercoat" if under else ("sheep_baby_wool" if baby else "sheep_wool"))
        wool = WOOL.but(base=0.5) if under else WOOL
        sk.paint_all([], wool)
        for b in sk.boxes:
            curls(sk, b)
        head = sk.largest("head")
        if head is not None and "front" in head.faces:  # face opening
            x0, y0, x1, y1 = head.faces["front"]
            sk.clear((x0 + sk.k, y0 + 1 * sk.k, x1 - sk.k, y1))
            if "bottom" in head.faces:
                sk.clear(head.faces["bottom"])
        return sk.tex(grain=0.06)
    sk = Skin(ctx, "sheep_baby" if baby else "sheep")
    sk.paint_all([("head", SHEEP_FACE), ("leg", SHEEP_FACE), ("_leg", SHEEP_FACE)], SHEEP_SKIN)
    for b in sk.boxes:
        if "leg" in b.part:
            sk.band(b, 0, 2 if not baby else 1, SHEEP_SKIN)  # wool stubble on upper leg
            sk.band(b, -1, 0, Mat("2a221e", grain=0.1, sss=0.0), bottom=True)
    head = sk.largest("head")
    wv = head.w / sk.k
    if baby:
        sk.sym(head, "front", 0, 2, 2, 3, "d8d0b8", height=0.45)
        sk.sym(head, "front", 1, 2, 2, 3, PUPIL, height=0.4)
        sk.frect(head, "front", 2, 4, 3, 5, "2a201c", height=0.35)
    else:
        sk.sym(head, "front", 0, 2, 2, 3, "d8d0b8", height=0.45)
        sk.sym(head, "front", 1, 2, 2, 3, PUPIL, height=0.4)
        sk.frect(head, "front", 2, 4, 4, 5, SHEEP_FACE.but(base=0.75))
        sk.sym(head, "front", 2, 5, 3, 6, "241c18", height=0.35)
    return sk.tex()


reg(["entity/sheep/sheep", "entity/sheep/sheep_baby", "entity/sheep/sheep_wool", "entity/sheep/sheep_wool_baby",
     "entity/sheep/sheep_wool_undercoat"], sheep)


# ---------------------------------------------------------------- chickens

CHICKENS = {
    "temperate": ("eeeae0", "e8e2d4"),
    "cold": ("5c6670", "c8ccd0"),
    "warm": ("b8642e", "e0a050"),
}
BEAK = Mat("e8a63a", mottle=0.1, grain=0.15, sss=0.1, smooth=0.3)
WATTLE = Mat("c8302a", mottle=0.15, grain=0.2, sss=0.5)
SHANK = Mat("d9902e", mottle=0.1, grain=0.15, sss=0.1)


def chicken(ctx, path):
    name = path.split("/")[-1]
    baby = name.endswith("_baby")
    key = name.replace("_baby", "").split("_")[1]
    if baby:
        sk = Skin(ctx, "chicken_baby")
        down = Mat({"temperate": "f0d860", "cold": "b8bcc0", "warm": "e0a040"}[key], mottle=0.2, grain=0.25, sss=0.4)
        sk.paint_all([("left_leg", SHANK), ("right_leg", SHANK)], down)
        body = sk.box("body")
        beak = sk.box("body", 1)
        sk.paint(beak, BEAK)
        sk.frect(body, "front", 0, 1, 1, 2, PUPIL, height=0.4)
        sk.frect(body, "front", 3, 1, 4, 2, PUPIL, height=0.4)
        for w in sk.find("wing"):
            sk.paint(w, down.but(base=0.45))
        return sk.tex()
    model = {"temperate": "chicken", "cold": "cold_chicken", "warm": "warm_chicken"}[key]
    sk = Skin(ctx, model)
    feather_c, light_c = CHICKENS[key]
    feather = Mat(feather_c, mottle=0.3, grain=0.25, sss=0.3, streak=0.3,
                  blotch=(light_c, 0.7, "mid") if key != "temperate" else None)
    sk.paint_all([("bill", BEAK), ("chin", WATTLE), ("left_leg", SHANK), ("right_leg", SHANK),
                  ("left_wing", feather.but(base=0.45)), ("right_wing", feather.but(base=0.45))], feather)
    head = sk.box("head")
    sk.sym(head, "front", 0, 1, 1, 2, PUPIL, height=0.4)
    sk.frect(head, "front", 0, 0, 0, 1, feather.but(base=0.7))
    # comb on top of the head
    sk.frect(head, "top", 1, 0, 3, 3, WATTLE)
    for w in sk.find("wing"):  # wing feather tips darker
        sk.band(w, -1, 0, feather.but(base=0.3))
    if key == "cold":
        crest = sk.box("head", 1)
        if crest:
            sk.paint(crest, feather.but(p=shades("8a949c"), blotch=None, streak=0.8))
        tail = sk.box("body", 1)
        if tail:
            sk.paint(tail, feather.but(base=0.35))
    for l in sk.find("left_leg") + sk.find("right_leg"):
        sk.band(l, 0, 1, feather)
    return sk.tex()


reg([f"entity/chicken/chicken_{k}{b}" for k in ("cold", "temperate", "warm") for b in ("", "_baby")], chicken)


# ---------------------------------------------------------------- goats

GOAT = Mat(shades("e2dccc", 6, 0.68, 1.08), mottle=0.35, grain=0.25, sss=0.3, streak=0.5)


def goat(ctx, path):
    baby = path.endswith("_baby")
    sk = Skin(ctx, "goat_baby" if baby else "goat")
    horn = Mat("8a8478", mottle=0.1, grain=0.2, grad=0.4, sss=0.0, smooth=0.3)
    sk.paint_all([("left_horn", horn), ("right_horn", horn), ("nose", GOAT.but(base=0.62))], GOAT)
    head = sk.largest("head")
    eyes(sk, head, 2 if baby else 2, x=0, w=2, white="d8b860", pupil="1c1716")
    for b in sk.find("head"):
        if b is not head:
            sk.paint(b, GOAT.but(base=0.6))
    hooves(sk, Mat("3e3832", grain=0.15, sss=0.0, smooth=0.3), rows=1 if baby else 2)
    body = sk.largest("body")
    if body:  # long beard / shaggy belly
        underside(sk, body, GOAT.but(base=0.45, streak=1.0))
    return sk.tex()


reg(["entity/goat/goat", "entity/goat/goat_baby"], goat)
