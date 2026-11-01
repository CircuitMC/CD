"""Wolves, cats, ocelots, foxes, rabbits, parrots (entity_mobs)."""
import numpy as np

from ...registry import register
from .mobs_base import SIDES, Mat, Skin, col, mix, shades

PUPIL = "1a1614"


def reg(paths, fn, *args):
    for p in paths:
        register(p, lambda ctx, p=p: fn(ctx, p, *args))


def stripes(sk, b, c, period=3, width=1, faces=("left", "right", "back", "top"), wobble=0.8, phase=0):
    """Fur stripes across the length of a body (direction follows the box orientation)."""
    if b is None:
        return
    for f in faces:
        if f not in b.faces:
            continue
        x0, y0, x1, y1 = b.faces[f]
        sl = sk._sl(x0, y0, x1, y1)
        if sl is None:
            continue
        along_y = b.quad or f in ("top", "bottom")
        t = (sk.ctx.y[sl] - y0) if along_y else (sk.ctx.x[sl] - x0)
        w = (sk.noise["mid"][sl] - 0.5) * wobble * 2
        m = ((t / sk.k + w + phase) % period) < width
        if isinstance(c, Mat):
            v = c.base + (sk.grain[sl] - 0.5) * c.grain
            cc = sk.ctx.palette(c.p, v)
        else:
            cc = col(c)
        sk._write(sl, cc, c if isinstance(c, Mat) else None, height=0.45, mask=m, sss=0.3)


def belly(sk, b, mat):
    if b is None:
        return
    f = "front" if b.quad else "bottom"
    if f in b.faces:
        sk.fill(b.faces[f], mat)
    # lower strip of the sides
    for s in ("left", "right"):
        if s not in b.faces:
            continue
        x0, y0, x1, y1 = b.faces[s]
        if b.quad:
            w = (x1 - x0) * 0.25
            r = (x1 - w, y0, x1, y1) if s == "right" else (x0, y0, x0 + w, y1)
        else:
            hh = (y1 - y0) * 0.25
            r = (x0, y1 - hh, x1, y1)
        sk.fill(r, mat, off=-0.03)


# ---------------------------------------------------------------- wolves

WOLVES = {
    # name: (fur, light, dark)
    "pale": ("c8c4bc", "ece8e0", "8a8680"),
    "ashen": ("9a9a9e", "d0d0d2", "4e4e54"),
    "black": ("3a3634", "6a625c", "1e1c1c"),
    "chestnut": ("8a5a3a", "d8c0a0", "4a3020"),
    "rusty": ("b06a3a", "e0b890", "6a3a22"),
    "snowy": ("eceae6", "fafaf8", "b8b4ae"),
    "spotted": ("d8c8a8", "f0e8d8", "7a5a3a"),
    "striped": ("b89a70", "e0d0b0", "5a4630"),
    "woods": ("6a5040", "a89078", "3a2c22"),
}


def wolf(ctx, path):
    name = path.split("/")[-1]
    baby = name.endswith("_baby")
    n = name.replace("_baby", "")
    if n.startswith("wolf_armor_crackiness"):
        return armor_cracks(ctx, n.split("_")[-1])
    if n == "wolf_collar":
        return collar(ctx, "wolf_baby" if baby else "wolf_collar", wolf=True)
    parts = n.split("_")[1:]
    variant = "pale"
    mood = None
    for p in parts:
        if p in WOLVES:
            variant = p
        elif p in ("angry", "tame"):
            mood = p
    fur_c, light_c, dark_c = WOLVES[variant]
    sk = Skin(ctx, "wolf_baby" if baby else "wolf")
    fur = Mat(fur_c, mottle=0.3, grain=0.25, streak=0.6, sss=0.3,
              blotch=(dark_c, 0.64, "big") if variant == "spotted" else None)
    light = Mat(light_c, mottle=0.25, grain=0.2, streak=0.5, sss=0.3)
    dark = Mat(dark_c, mottle=0.25, grain=0.2, streak=0.5, sss=0.3)
    sk.paint_all([("mane", fur.but(base=0.62)), ("tail", fur.but(base=0.58))], fur)
    head = sk.largest("head")
    hb = [b for b in sk.find("head") if b is not head]
    muzzle = max(hb, key=lambda b: b.d) if hb else None
    for b in hb:
        if b is muzzle:
            sk.paint(b, light)
            sk.frect(b, "front", 0, 0, 0, 1 if baby else 1, "221c1a", height=0.6, smooth=0.6)  # nose
            sk.frect(b, "top", 0, -1, 0, 0, "221c1a", height=0.6, smooth=0.6)
            sk.frect(b, "front", 0, -1, 0, 0, mix(light_c, "000000", 0.25))
        else:  # ears
            sk.paint(b, fur)
            sk.frect(b, "front", 0, 0, 0, 0, dark.but(base=0.5)) if False else None
            sk.frect(b, "front", 0, 1, 0, 0, mix(dark_c, "c08a80", 0.5), height=0.4)
    body = sk.largest("body")
    belly(sk, body, light)
    if variant == "striped":
        stripes(sk, body, dark, period=3, width=1)
        mane = sk.box("mane")
        stripes(sk, mane, dark, period=3, width=1)
    if variant in ("woods", "chestnut", "black", "ashen"):
        # darker saddle on the back
        f = "back" if body.quad else "top"
        sk.fill(body.faces[f], dark.but(base=0.6))
    for l in sk.find("leg"):
        sk.band(l, -1 if not baby else -1, 0, light if variant not in ("black",) else dark, bottom=True)
    tail = sk.find("tail")
    for t in tail:
        sk.band(t, -2 if not baby else -2, 0, light if variant != "snowy" else dark.but(base=0.7))
    # face
    hw = head.w / sk.k
    ey = 2 if not baby else 1
    if mood == "angry":
        sk.sym(head, "front", 0, ey, 2, ey + 1, "1a1210", height=0.4)
        sk.sym(head, "front", 1, ey, 2, ey + 1, "d8302a", height=0.4, emissive=0.0)
        sk.sym(head, "front", 0, ey - 1, 2, ey, dark.but(base=0.3))
        sk.sym(head, "front", 1, ey - 1, 2, ey, "1a1210", height=0.4)
    else:
        white = "f0ece4" if mood == "tame" else mix(light_c, "ffffff", 0.3)
        sk.sym(head, "front", 0, ey, 2, ey + 1, white, height=0.45, smooth=0.6)
        sk.sym(head, "front", 1, ey, 2, ey + 1, PUPIL if mood != "tame" else "3a2618", height=0.4, smooth=0.7)
        if mood == "tame":
            sk.sym(head, "front", 1, ey - 1, 2, ey, light.but(base=0.8))
    sk.frect(head, "front", 2 if not baby else 2, 0, -2 if not baby else -2, ey + 1, light.but(base=0.65)) \
        if variant in ("chestnut", "woods", "ashen", "black") else None
    return sk.tex()


def collar(ctx, model, wolf=False):
    """Grayscale (dye-tinted) collar band around the neck."""
    sk = Skin(ctx, model)
    band = Mat(shades("d0d0d0", 5, 0.75, 1.1), mottle=0.1, grain=0.15, grad=0.2, sss=0.0, smooth=0.3)
    if wolf:
        b = sk.box("mane") or sk.largest("body")
        if b is not None:
            if b.quad:  # mane: collar near the head end (top rows of the long faces)
                for f in ("left", "right", "back", "front"):
                    if f in b.faces:
                        x0, y0, x1, y1 = b.faces[f]
                        sk.fill((x0, y0, x1, y0 + 2 * sk.k), band)
                        sk.rect(x0 + (x1 - x0) / 2 - sk.k / 2, y0 + sk.k, x0 + (x1 - x0) / 2 + sk.k / 2, y0 + 2 * sk.k,
                                "e8c040", height=0.7, smooth=0.6) if f == "front" else None
            else:
                for f in SIDES:
                    if f in b.faces:
                        x0, y0, x1, y1 = b.faces[f]
                        if f in ("left", "right"):
                            r = (x0, y0, x0 + 2 * sk.k, y1) if f == "left" else (x1 - 2 * sk.k, y0, x1, y1)
                            sk.fill(r, band)
                        elif f == "front":
                            sk.fill((x0, y0, x1, y0 + 2 * sk.k), band)
                if "top" in b.faces:
                    x0, y0, x1, y1 = b.faces["top"]
                    sk.fill((x0, y1 - 2 * sk.k, x1, y1), band)
    else:
        b = sk.largest("body")
        if b is not None:
            for f in SIDES + ("top",):
                if f in b.faces:
                    x0, y0, x1, y1 = b.faces[f]
                    if b.quad:
                        if f == "top":
                            sk.fill((x0, y0, x1, y1), band)
                        else:
                            sk.fill((x0, y0, x1, y0 + 1 * sk.k), band)
                    else:
                        if f in ("left",):
                            sk.fill((x0, y0, x0 + sk.k, y1), band)
                        elif f == "right":
                            sk.fill((x1 - sk.k, y0, x1, y1), band)
                        elif f == "top":
                            sk.fill((x0, y1 - sk.k, x1, y1), band)
                        elif f == "front":
                            sk.fill((x0, y0, x1, y1), band)
        head = sk.largest("head")
        if head is not None:  # neck strap under the head
            for f in ("left", "right", "back"):
                if f in head.faces:
                    x0, y0, x1, y1 = head.faces[f]
                    sk.fill((x0, y1 - sk.k, x1, y1), band)
            if "bottom" in head.faces:
                sk.fill(head.faces["bottom"], band)
    return sk.tex(grain=0.02)


def armor_cracks(ctx, level):
    """Cracks overlay for wolf armor: dark fissures, rest transparent."""
    sk = Skin(ctx, "wolf_armor")
    thr = {"low": 0.07, "medium": 0.13, "high": 0.2}[level]
    vo = ctx.voronoi({"low": 10, "medium": 16, "high": 24}[level], salt="crk")
    crack = (vo["f2"] - vo["f1"]) < (0.35 + thr)
    sel = ctx.noise(5, 2, salt="crksel") < 0.3 + thr * 2.5
    covered = np.zeros((ctx.H, ctx.W), bool)
    for b in sk.boxes:
        for f, r in b.faces.items():
            sl = sk._sl(*r)
            if sl is not None:
                covered[sl] = True
    m = crack & sel & covered
    sk.color[:] = np.where(m[..., None], col("2a2826"), col("2a2826"))
    sk.alpha[:] = m.astype(np.float32)
    sk.height[:] = np.where(m, 0.2, 0.5)
    sk.smooth[:] = 0.2
    return sk.tex(grain=0)


reg(sorted({f"entity/wolf/{n}" for n in [
    "wolf", "wolf_angry", "wolf_tame", "wolf_baby", "wolf_angry_baby", "wolf_tame_baby",
    "wolf_collar", "wolf_collar_baby",
    "wolf_armor_crackiness_high", "wolf_armor_crackiness_low", "wolf_armor_crackiness_medium"] + [
    f"wolf_{v}{m}{b}" for v in WOLVES if v != "pale" for m in ("", "_angry", "_tame") for b in ("", "_baby")]}),
    wolf)


# ---------------------------------------------------------------- cats

CATS = {
    # name: (fur, secondary, pattern, eye)
    "all_black": ("2a2628", None, None, "e8c840"),
    "black": ("2e2a2c", "ece8e0", "tux", "e8c840"),
    "british_shorthair": ("8a909a", None, None, "e0a040"),
    "calico": ("ece6da", "d07a30", "calico", "70b040"),
    "jellie": ("8a8a8a", "eceae4", "bib", "70c060"),
    "persian": ("e8c898", "f4e4c8", "bib", "50a0d0"),
    "ragdoll": ("ece4d4", "6a5848", "points", "4a90e0"),
    "red": ("d8843a", "a85a22", "tabby", "e0c040"),
    "siamese": ("e4d8c0", "4a3a30", "points", "4aa0f0"),
    "tabby": ("8a7258", "4a3a2a", "tabby", "90b040"),
    "white": ("f0eeea", None, None, "6ab0e0"),
    "ocelot": ("e0b850", "4a3a20", "spots", "60b040"),
}


def cat(ctx, path):
    name = path.split("/")[-1]
    baby = name.endswith("_baby")
    n = name.replace("_baby", "")
    if n == "cat_collar":
        return collar(ctx, "cat_baby_collar" if baby else "cat_collar")
    key = "ocelot" if n == "ocelot" else n[4:]
    model = ("ocelot" if key == "ocelot" else "cat") + ("_baby" if baby else "")
    fur_c, sec_c, pattern, eye_c = CATS[key]
    sk = Skin(ctx, model)
    fur = Mat(fur_c, mottle=0.25, grain=0.2, streak=0.5, sss=0.3,
              blotch=(sec_c, 0.62, "big") if pattern == "calico" else None)
    sk.paint_all([], fur)
    head = sk.largest("head")
    body = sk.largest("body")
    hb = [b for b in sk.find("head") if b is not head]
    nose = max(hb, key=lambda b: b.w) if hb else None
    sec = Mat(sec_c, mottle=0.2, grain=0.2, streak=0.5, sss=0.3) if sec_c else None
    tails = sk.find("tail")
    legs = [b for b in sk.boxes if "leg" in b.part]
    if pattern == "calico":
        sk.face_spots(body, Mat("3a3230", grain=0.2), 0.72, "mid")
        sk.face_spots(head, Mat(sec_c, grain=0.2), 0.6, "big")
    elif pattern in ("tabby",):
        stripes(sk, body, sec, period=3, width=1)
        for t in tails:
            stripes(sk, t, sec, period=2, width=1, faces=SIDES)
        for l in legs:
            stripes(sk, l, sec, period=3, width=1, faces=SIDES) if l.quad else None
        sk.frect(head, "top", 1, 0, 2, 0, sec.but(base=0.4))
        sk.frect(head, "top", 3, 0, 4, 0, sec.but(base=0.4))
    elif pattern == "spots":
        sk.face_spots(body, Mat(sec_c, grain=0.2), 0.68, "small")
        for t in tails:
            stripes(sk, t, sec, period=2, width=1, faces=SIDES)
        for l in legs:
            sk.face_spots(l, Mat(sec_c, grain=0.2), 0.72, "small")
    elif pattern in ("tux", "bib"):
        belly(sk, body, sec)
        for l in legs:
            sk.band(l, -2 if not baby else -1, 0, sec, bottom=True)
        if tails:
            sk.band(tails[-1], -2, 0, sec)
    elif pattern == "points":
        for l in legs:
            sk.band(l, -4 if not baby else -1, 0, sec, bottom=True)
        for t in tails:
            sk.paint(t, sec)
        for b in hb:
            if b is not nose:
                sk.paint(b, sec)
    # face
    hh = head.h / sk.k
    mask_c = sec if pattern == "points" else None
    if mask_c is not None:
        sk.frect(head, "front", 1, 1, -1, 0, mask_c)
    if nose is not None:
        if mask_c is not None:
            sk.paint(nose, mask_c)
        elif pattern in ("tux", "bib"):
            sk.paint(nose, sec)
        else:
            sk.paint(nose, fur.but(base=0.68, blotch=None))
        nw = nose.w / sk.k
        sk.frect(nose, "front", 1 if nw >= 3 else 0, 0, 2 if nw >= 3 else 1, 1, "d88a8a", height=0.6, sss=0.4)
    ey = 1 if baby else 2
    sk.sym(head, "front", 0 if baby else 1, ey, 1 if baby else 2, ey + 1, eye_c, height=0.45, smooth=0.7, sss=0.0)
    if not baby:
        sk.sym(head, "front", 1, ey - 1, 2, ey, mix(fur_c, "000000", 0.3))
    for b in hb:
        if b is not nose:  # ears: pink inner
            sk.frect(b, "front", 0, 0, 0, 0, "c88080", height=0.4)
    return sk.tex()


reg([f"entity/cat/cat_{k}{b}" for k in list(CATS)[:-1] + ["collar"] for b in ("", "_baby")]
    + ["entity/cat/ocelot", "entity/cat/ocelot_baby"], cat)


# ---------------------------------------------------------------- foxes

def fox(ctx, path):
    name = path.split("/")[-1]
    baby = name.endswith("_baby")
    snow = "snow" in name
    sleep = "sleep" in name
    sk = Skin(ctx, "fox_baby" if baby else "fox")
    fur = Mat("f0eeea" if snow else "d8742a", mottle=0.25, grain=0.2, streak=0.5, sss=0.3)
    white = Mat("fafaf6" if not snow else "d8d8dc", mottle=0.15, grain=0.15, sss=0.3)
    dark = Mat("3a2a22" if not snow else "6a6a72", mottle=0.15, grain=0.2, sss=0.2)
    sk.paint_all([], fur)
    head = sk.largest("head")
    hb = [b for b in sk.find("head") if b is not head]
    snout = max(hb, key=lambda b: b.w * b.d) if hb else None
    for b in hb:
        if b is snout:
            sk.paint(b, white)
            sk.frect(b, "front", 1 if b.w / sk.k >= 4 else 0, 0, -1 if b.w / sk.k >= 4 else 0, 1, "1e1816",
                     height=0.6, smooth=0.6)
        else:
            sk.paint(b, fur)
            sk.frect(b, "front", 0, 0, 0, 1, dark)
    hw, hh = head.w / sk.k, head.h / sk.k
    sk.frect(head, "front", 0, hh - 2, 0, 0, white)  # white cheeks
    ey = 2 if not baby else 2
    if sleep:
        sk.sym(head, "front", 1, ey, 3, ey + 1, dark.but(base=0.3))
    else:
        sk.sym(head, "front", 1, ey, 3, ey + 1, "1a1412", height=0.4, smooth=0.6)
        sk.sym(head, "front", 2 if hw >= 8 else 1, ey, 3 if hw >= 8 else 2, ey + 1, "e8b040", height=0.4, smooth=0.6) \
            if not baby else None
    body = sk.largest("body")
    belly(sk, body, white)
    for l in sk.find("leg"):
        sk.paint(l, dark)
    tail = sk.box("tail")
    if tail:
        if tail.quad:  # white tip at the end (bottom rows)
            for f in ("left", "right", "front", "back"):
                if f in tail.faces:
                    x0, y0, x1, y1 = tail.faces[f]
                    sk.fill((x0, y1 - 3 * sk.k, x1, y1), white)
            sk.fill(tail.faces["bottom"], white) if "bottom" in tail.faces else None
        else:
            for f in ("left", "right"):
                if f in tail.faces:
                    x0, y0, x1, y1 = tail.faces[f]
                    r = (x1 - 2 * sk.k, y0, x1, y1) if f == "right" else (x0, y0, x0 + 2 * sk.k, y1)
                    sk.fill(r, white)
            sk.fill(tail.faces["back"], white) if "back" in tail.faces else None
    return sk.tex()


reg([f"entity/fox/{n}" for n in ("fox", "fox_baby", "fox_sleep", "fox_sleep_baby", "fox_snow", "fox_snow_baby",
                                 "fox_snow_sleep", "fox_snow_sleep_baby")], fox)


# ---------------------------------------------------------------- rabbits

RABBITS = {
    "black": ("2e2a2a", None, "c0a060"),
    "brown": ("8a6448", None, "1a1412"),
    "caerbannog": ("f2f0ec", None, "d02020"),
    "gold": ("e0c070", None, "1a1412"),
    "salt": ("b8b0a0", "4a4440", "1a1412"),
    "toast": ("5a4a40", "f0ece4", "1a1412"),
    "white": ("f2f0ec", None, "c84060"),
    "white_splotched": ("f2f0ec", "2e2a2a", "1a1412"),
}


def rabbit(ctx, path):
    name = path.split("/")[-1]
    baby = name.endswith("_baby")
    key = name.replace("_baby", "")[7:]
    fur_c, sec_c, eye_c = RABBITS[key]
    sk = Skin(ctx, "rabbit_baby" if baby else "rabbit")
    fur = Mat(fur_c, mottle=0.25, grain=0.22, streak=0.4, sss=0.35,
              blotch=(sec_c, 0.62 if key != "salt" else 0.55, "big" if key != "salt" else "small") if sec_c else None)
    sk.paint_all([], fur)
    head = sk.largest("head")
    ey = 1
    sk.sym(head, "front", 0, ey, 1, ey + 1, eye_c, height=0.45, smooth=0.7)
    hw = head.w / sk.k
    sk.frect(head, "front", 2, 2, 3, 3, "d08888", height=0.6, sss=0.4)
    sk.frect(head, "front", 1, 3, 4, 4, mix(fur_c, "ffffff", 0.4))
    for e in sk.find("left_ear") + sk.find("right_ear"):
        sk.frect(e, "front", 0, 1, 0, 0, "d8a0a0", height=0.4)
    t = sk.box("tail")
    sk.paint(t, Mat(mix(fur_c, "ffffff", 0.6), mottle=0.2, grain=0.25, sss=0.35))
    body = sk.largest("body")
    belly(sk, body, fur.but(base=0.68, blotch=None, p=shades(mix(fur_c, "ffffff", 0.35))))
    if key == "toast":
        sk.frect(head, "front", 0, 0, 0, 1, Mat(sec_c, grain=0.1))
    return sk.tex()


reg([f"entity/rabbit/rabbit_{k}{b}" for k in RABBITS for b in ("", "_baby")], rabbit)


# ---------------------------------------------------------------- parrots

PARROTS = {
    "blue": ("2a5ad8", "e8c838", "1a2a6a"),
    "green": ("4ab830", "e8d040", "2a5a8a"),
    "grey": ("a8acb0", "e8e8e8", "c83a2a"),
    "red_blue": ("d02a22", "e8c030", "2a4ad0"),
    "yellow_blue": ("2aa8e0", "f0c830", "1a5aa0"),
}


def parrot(ctx, path):
    key = path.split("/")[-1][7:]
    main_c, face_c, wing_c = PARROTS[key]
    sk = Skin(ctx, "parrot")
    main = Mat(main_c, mottle=0.2, grain=0.2, sss=0.25, smooth=0.25)
    wing = Mat(wing_c if key != "grey" else "8a8e94", mottle=0.2, grain=0.2, sss=0.25, smooth=0.25)
    beak = Mat("3a3434" if key in ("blue", "yellow_blue", "red_blue") else "e8a83a", grain=0.15, smooth=0.4,
               sss=0.0, mottle=0.1)
    sk.paint_all([("left_wing", wing), ("right_wing", wing), ("left_leg", Mat("6a6a6a", grain=0.1)),
                  ("right_leg", Mat("6a6a6a", grain=0.1)), ("tail", wing.but(base=0.45))], main)
    head = sk.box("head", 0)
    feather = sk.box("head/feather")
    sk.paint(feather, main.but(base=0.7))
    for b in sk.find("head"):
        if b is not head and b is not feather:
            sk.paint(b, beak)
    sk.frect(head, "front", 0, 1, 0, 2, Mat(face_c, grain=0.15, mottle=0.1))
    for f in ("left", "right"):
        sk.frect(head, f, 0, 0, 0, 2, Mat(face_c, grain=0.15, mottle=0.1))
        sk.frect(head, f, 0, 1, 1, 2, "141010", height=0.4, smooth=0.7)
    if key == "grey":
        sk.paint(sk.box("tail"), Mat(wing_c, grain=0.15))
    for w in sk.find("left_wing") + sk.find("right_wing"):
        sk.band(w, -2, 0, wing.but(base=0.3))
    return sk.tex()


reg([f"entity/parrot/parrot_{k}" for k in PARROTS], parrot)
