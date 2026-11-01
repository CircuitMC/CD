"""Remaining creatures: allay, vex, armadillo, bat, polar bear, bees, breeze, copper golem,
creaking, ender dragon, endermite, silverfish, evoker fangs, ravager, iron golem, pandas,
phantom, sniffer, snow golem, warden (entity_mobs)."""
import numpy as np

from ...registry import register
from .mobs_base import SIDES, Mat, Skin, col, mix, shades

PUPIL = "141214"


def reg(paths, fn, *args):
    for p in paths:
        register(p, lambda ctx, p=p: fn(ctx, p, *args))


def side_eyes(sk, b, fy, c=PUPIL, from_front=1, size=1, emissive=0.0, h=1):
    if b is None:
        return
    for f in ("right", "left"):
        if f in b.faces:
            dm = b.d / sk.k
            x = dm - from_front - size if f == "right" else from_front
            sk.frect(b, f, x, fy, x + size, fy + h, c, height=0.4, smooth=0.8, sss=0.0, emissive=emissive)


def cracks(sk, level, color="3a3836", density=None):
    """Mostly transparent crack overlay over all faces of the skin's boxes."""
    ctx = sk.ctx
    n = {"low": 12, "medium": 20, "high": 30}[level]
    vo = ctx.voronoi(n, salt="crk", min_dist=4)
    line = (vo["f2"] - vo["f1"]) < 0.5
    sel = ctx.noise(10, 2, salt="crksel") < {"low": 0.32, "medium": 0.5, "high": 0.7}[level]
    cov = np.zeros((ctx.H, ctx.W), bool)
    for b in sk.boxes:
        for f, r in b.faces.items():
            sl = sk._sl(*r)
            if sl is not None:
                cov[sl] = True
    m = line & sel & cov
    sk.color[:] = col(color)
    sk.alpha[:] = m
    sk.height[:] = np.where(m, 0.15, 0.5)
    sk.smooth[:] = 0.2
    return sk.tex(grain=0)


# ---------------------------------------------------------------- allay / vex

def spirit(ctx, path):
    name = path.split("/")[-1]
    allay = name == "allay"
    sk = Skin(ctx, "allay" if allay else "vex")
    main = Mat("6ac8f0" if allay else "a8b0c0", mottle=0.25, grain=0.2, sss=0.5, smooth=0.5,
               emissive=0.25 if allay else 0.0)
    wing = Mat("d8f0ff" if allay else "e8ecf0", mottle=0.15, grain=0.2, sss=0.3, alpha=0.8, smooth=0.6)
    sk.paint_all([("left_wing", wing), ("right_wing", wing)], main)
    head = sk.box("head")
    if allay:
        sk.sym(head, "front", 1, 2, 2, 3, "1a3a6a", height=0.4, emissive=0.3)
        sk.frect(head, "front", 0, 0, 0, 1, main.but(base=0.75))
    else:
        charging = name.endswith("charging")
        sk.sym(head, "front", 1, 2, 2, 3, "1a1a1e" if not charging else "e83a3a", height=0.4,
               emissive=0.0 if not charging else 0.8)
        sk.frect(head, "front", 1, 3, 4, 4, "2a2a30" if not charging else "6a1a1a", height=0.35)
        sk.paint(head, Mat("e8e0c0", grain=0.15), faces=("top",))   # pale hair
    for w in sk.find("left_wing") + sk.find("right_wing"):
        for f, r in w.faces.items():   # vein lines
            sl = sk._sl(*r)
            if sl is not None:
                m = ((sk.ctx.ty[sl] - int(r[1] * sk.ctx.s)) // sk.ctx.s) % 2 == 0
                sk.color[sl][m] *= 0.92
    return sk.tex()


reg(["entity/allay/allay", "entity/illager/vex", "entity/illager/vex_charging"], spirit)


# ---------------------------------------------------------------- armadillo

def armadillo(ctx, path):
    baby = path.endswith("_baby")
    sk = Skin(ctx, "armadillo_baby" if baby else "armadillo")
    skin = Mat("c88a7a", mottle=0.2, grain=0.2, sss=0.45)
    plate = Mat("8a5a4a", mottle=0.25, grain=0.2, sss=0.1, smooth=0.45, blotch=("a87060", 0.62, "mid"))
    sk.paint_all([("body", plate), ("cube", plate), ("tail", plate)], skin)
    for b in sk.find("body") + sk.find("cube"):   # banded shell
        for f, (x0, y0, x1, y1) in b.faces.items():
            sl = sk._sl(x0, y0, x1, y1)
            if sl is None:
                continue
            along_x = f in ("left", "right")
            t = ((sk.ctx.x[sl] - x0) if along_x else (sk.ctx.y[sl] - y0)) / sk.k
            m = (np.floor(t) % 3) == 0
            sk.color[sl][m] *= 0.8
            sk.height[sl][m] = 0.35
    head = sk.box("head") or sk.box("head_cube")
    if head is not None:
        sk.paint(head, skin)
        sk.sym(head, "front", 0, 1, 1, 2, PUPIL, height=0.4)
    return sk.tex()


reg(["entity/armadillo/armadillo", "entity/armadillo/armadillo_baby"], armadillo)


# ---------------------------------------------------------------- bat

def bat(ctx, path):
    sk = Skin(ctx, "bat")
    fur = Mat("4a3a30", mottle=0.3, grain=0.25, sss=0.3, streak=0.4)
    wing = Mat("2e2624", mottle=0.2, grain=0.2, sss=0.5, smooth=0.3)
    sk.paint_all([("left_wing", wing), ("right_wing", wing), ("outer", wing), ("feet", wing),
                  ("head#1", wing.but(base=0.6)), ("head#2", wing.but(base=0.6))], fur)
    head = sk.box("head")
    sk.sym(head, "front", 0, 1, 1, 2, "e8a030", height=0.45, emissive=0.2)
    sk.frect(head, "front", 1, 2, 3, 3, "1a1210", height=0.35)
    for w in sk.find("outer"):  # finger bones
        for f in ("front", "back"):
            if f in w.faces:
                for x in (1, 3, 5):
                    sk.frect(w, f, x, 0, x + 1, -2, "4a3e3a", height=0.6)
    return sk.tex()


reg(["entity/bat/bat"], bat)


# ---------------------------------------------------------------- polar bear

def polarbear(ctx, path):
    baby = path.endswith("_baby")
    sk = Skin(ctx, "polar_bear_baby" if baby else "polar_bear")
    fur = Mat(shades("ecebe4", 6, 0.78, 1.04), mottle=0.3, grain=0.22, sss=0.4, streak=0.5)
    sk.paint_all([], fur)
    head = sk.largest("head")
    for b in sk.find("head"):
        if b is head:
            continue
        if b.w / sk.k >= 4:   # muzzle
            sk.paint(b, fur.but(base=0.42))
            sk.frect(b, "front", 1, 0, -1, 1, "1e1a1a", height=0.6, smooth=0.6)
        else:
            sk.frect(b, "front", 0, 0, 0, 0, fur.but(base=0.4))
    sk.sym(head, "front", 1, 2, 2, 3, PUPIL, height=0.4, smooth=0.8)
    for l in sk.boxes:
        if "leg" in l.part:
            sk.paint(l, fur.but(base=0.4), faces=("bottom",))
    return sk.tex()


reg(["entity/bear/polarbear", "entity/bear/polarbear_baby"], polarbear)


# ---------------------------------------------------------------- bees

def bee(ctx, path):
    name = path.split("/")[-1]
    if name == "bee_stinger":
        sk = Skin(ctx, "bee_stinger")
        sk.paint_all([], Mat("3a3030", grain=0.1, grad=0.6, sss=0.0))
        return sk.tex()
    baby = name.endswith("_baby")
    angry = "angry" in name
    nectar = "nectar" in name
    sk = Skin(ctx, "bee_baby" if baby else "bee")
    yellow = Mat("e8b830", mottle=0.25, grain=0.25, sss=0.3, streak=0.3)
    black = Mat("2e2420", mottle=0.15, grain=0.2, sss=0.2)
    wing = Mat("e0f0f8", mottle=0.1, grain=0.15, sss=0.2, alpha=0.7, smooth=0.7)
    sk.paint_all([("left_wing", wing), ("right_wing", wing), ("legs", black), ("antenna", black),
                  ("stinger", Mat("d8d0c0", grain=0.1)), ("body", black)], yellow)
    t = sk.box("torso")
    dm = t.d / sk.k
    for f in ("left", "right"):          # stripes across the length
        for x in ((3, 6) if not baby else (2,)):
            xx = x if f == "left" else dm - x - (2 if not baby else 1)
            sk.frect(t, f, xx, 0, xx + (2 if not baby else 1), 0, black)
    for x in ((3, 6) if not baby else (2,)):
        sk.frect(t, "top", 0, dm - x - (2 if not baby else 1), 0, dm - x, black)
        sk.frect(t, "bottom", 0, x, 0, x + (2 if not baby else 1), black)
    sk.paint(t, black, faces=("back",)) if baby else sk.frect(t, "back", 0, 0, 0, 0, yellow)
    tw = t.w / sk.k
    if angry:
        sk.sym(t, "front", 1, 2 if not baby else 1, 3 if not baby else 2, 4 if not baby else 2, "e83a2a", height=0.4)
        sk.sym(t, "front", 1, 1 if not baby else 0, 3 if not baby else 2, 2 if not baby else 1, black.p[0], height=0.5)
    else:
        sk.sym(t, "front", 1, 2 if not baby else 1, 3 if not baby else 2, 4 if not baby else 2, "f0ece0", height=0.4)
        sk.sym(t, "front", 2 if not baby else 1, 2 if not baby else 1, 3 if not baby else 2,
               4 if not baby else 2, PUPIL, height=0.4)
    if nectar:  # pollen dust specks
        for f, r in t.faces.items():
            sl = sk._sl(*r)
            if sl is not None:
                m = sk.grain[sl] > 0.9
                sk._write(sl, col("fff0a0"), None, height=0.6, mask=m, sss=0.2)
    return sk.tex()


reg([f"entity/bee/{n}" for n in ("bee", "bee_angry", "bee_angry_baby", "bee_angry_nectar", "bee_angry_nectar_baby",
                                 "bee_baby", "bee_nectar", "bee_nectar_baby", "bee_stinger")], bee)


# ---------------------------------------------------------------- breeze

def breeze(ctx, path):
    name = path.split("/")[-1]
    if name == "breeze_wind":
        sk = Skin(ctx, "breeze_wind")
        for b in sk.boxes:
            for f, (x0, y0, x1, y1) in b.faces.items():
                sl = sk._sl(x0, y0, x1, y1)
                if sl is None:
                    continue
                t = (sk.ctx.x[sl] - x0) / sk.k + (sk.ctx.y[sl] - y0) / sk.k * 0.6 + sk.noise["mid"][sl] * 3
                m = (t % 4) < 1.6
                sk._write(sl, mix("c8d8f8", "f0f4ff", sk.noise["small"][sl][..., None]), None, height=0.5,
                          mask=m, alpha=0.8, emissive=0.1, sss=0.0)
        return sk.tex(grain=0)
    sk = Skin(ctx, "breeze_eyes" if name == "breeze_eyes" else "breeze")
    head = sk.box("head")
    if name == "breeze_eyes":
        sk.sym(head, "front", 1, 3, 3, 5, "e0f0ff", emissive=1.0, height=0.5)
        sk.sym(head, "front", 2, 3, 3, 4, "ffffff", emissive=1.0, height=0.5)
        return sk.tex(grain=0)
    shell = Mat("a8a0d8", mottle=0.3, grain=0.25, sss=0.2, smooth=0.5, blotch=("c8c0f0", 0.6, "mid"))
    sk.paint_all([("rods", Mat("8a80c0", grain=0.2, grad=0.4, smooth=0.5))], shell)
    sk.sym(head, "front", 1, 3, 3, 5, "3a3a8a", height=0.35)
    sk.frect(head, "front", 2, 6, 6, 7, "4a4a8a", height=0.35)
    return sk.tex()


reg(["entity/breeze/breeze", "entity/breeze/breeze_eyes", "entity/breeze/breeze_wind"], breeze)


# ---------------------------------------------------------------- copper golem

COPPER = {"": ("c8743a", "e8a060"), "exposed": ("a8846a", "c8a080"), "weathered": ("6a9a7a", "8ab890"),
          "oxidized": ("4aa890", "70c8a8")}


def copper_golem(ctx, path):
    name = path.split("/")[-1]
    eyes = "_eyes" in name
    stage = name.replace("copper_golem", "").replace("_eyes", "").strip("_")
    sk = Skin(ctx, "copper_golem")
    head = sk.largest("head")
    if eyes:
        sk.sym(head, "front", 1, 1, 3, 3, "f0e090" if stage in ("", "exposed") else "a0f0e0", emissive=1.0,
               height=0.5)
        return sk.tex(grain=0)
    base_c, light_c = COPPER[stage]
    metal = Mat(shades(base_c, 6, 0.65, 1.2), mottle=0.3, grain=0.25, sss=0.0, smooth=0.65, f0=0.5,
                blotch=(light_c, 0.65, "mid"))
    sk.paint_all([], metal)
    for b in sk.find("head"):
        if b is not head:
            sk.paint(b, metal.but(base=0.7))
    sk.sym(head, "front", 1, 1, 3, 3, "2a1e18", height=0.3)
    sk.frect(head, "front", 0, 0, 0, 1, metal.but(base=0.8))
    for b in sk.boxes:  # rivets
        for f in ("front", "back"):
            if f in b.faces and b.w / sk.k >= 4:
                sk.sym(b, f, 0, 0, 1, 1, metal.but(base=0.9))
    if stage == "":
        return sk.tex()
    return sk.tex()


reg([f"entity/copper_golem/copper_golem{e}{s}" for e in ("", "_eyes") for s in ("", "_exposed", "_weathered",
                                                                                  "_oxidized")], copper_golem)


# ---------------------------------------------------------------- creaking

def creaking(ctx, path):
    eyes = path.endswith("_eyes")
    sk = Skin(ctx, "creaking")
    head = sk.box("head")
    if eyes:
        sk.sym(head, "front", 1, 4, 2, 5, "ff8a20", emissive=1.0, height=0.5)
        return sk.tex(grain=0)
    bark = Mat("5a4a40", mottle=0.35, grain=0.3, sss=0.05, streak=0.9, blotch=("8a7a70", 0.66, "streak"))
    sk.paint_all([], bark)
    for b in sk.boxes:   # twiggy planes: cut gaps
        if (b.w == 0 or b.h == 0 or b.d == 0):
            for f, r in b.faces.items():
                sl = sk._sl(*r)
                if sl is not None:
                    sk.alpha[sl][sk.noise["streak"][sl] > 0.55] = 0
    sk.sym(head, "front", 1, 4, 2, 5, "c8601a", height=0.3, emissive=0.5)
    sk.frect(head, "front", 1, 7, 5, 8, "1e1814", height=0.25)
    return sk.tex()


reg(["entity/creaking/creaking", "entity/creaking/creaking_eyes"], creaking)


# ---------------------------------------------------------------- ender dragon

def dragon(ctx, path):
    name = path.split("/")[-1]
    if name == "dragon_fireball":
        sk = Skin(ctx)
        d = np.hypot(ctx.x - 8, ctx.y - 8)
        n = ctx.noise(3, 2, salt="fb")
        m = d < 6 + (n - 0.5) * 3
        v = np.clip(1 - d / 7 + (n - 0.5) * 0.4, 0, 1)
        c = ctx.palette(shades("b040e0", 5, 0.5, 1.3), v)
        sk.color[:] = c
        sk.alpha[:] = m
        sk.emissive[:] = np.where(m, 1.0, 0.0)
        sk.height[:] = 0.5
        return sk.tex(grain=0)
    sk = Skin(ctx, "dragon")
    head = max(sk.find("head"), key=lambda b: b.w * b.h * b.d)
    snout = sk.box("head", 0)
    if name == "dragon_eyes":
        side_eyes(sk, head, 4, c="e070ff", from_front=2, size=4, emissive=1.0, h=2)
        sk.sym(head, "front", 1, 4, 5, 6, "e070ff", emissive=1.0, height=0.5)
        return sk.tex(grain=0)
    scale = Mat(shades("1e1a24", 6, 0.8, 1.35), mottle=0.3, grain=0.2, sss=0.05, smooth=0.35,
                blotch=(shades("2e2838", 6, 0.8, 1.3), 0.62, "mid"))
    membrane = Mat(shades("3a2a48", 5, 0.6, 1.3), mottle=0.2, grain=0.2, sss=0.4, smooth=0.3)
    horn = Mat("c8c0b0", mottle=0.1, grain=0.2, grad=0.5, sss=0.0, smooth=0.4)
    sk.paint_all([("head#2", horn), ("head#3", horn), ("head/mirrored", horn), ("neck1#1", horn),
                  ("neck2#1", horn), ("neck3#1", horn), ("neck4#1", horn), ("neck5#1", horn), ("body#1", horn),
                  ("body#2", horn), ("body#3", horn)] + [(f"tail{i}#1", horn) for i in range(1, 13)], scale)
    for b in sk.boxes:   # wing membranes (flat planes) and bones
        if "wing" in b.part:
            if b.h == 0:
                sk.paint(b, membrane)
                for f, (x0, y0, x1, y1) in b.faces.items():
                    sl = sk._sl(x0, y0, x1, y1)
                    if sl is None:
                        continue
                    t = (sk.ctx.x[sl] - x0) / sk.k
                    m = (t % 14) < 1.2
                    sk.color[sl][m] = col("1a1420")
            else:
                sk.paint(b, scale.but(base=0.45))
    for b in sk.boxes:
        if b.part.endswith(("foot",)):
            sk.band(b, -1, 0, horn)
    side_eyes(sk, head, 4, c="9a40c8", from_front=2, size=4, emissive=0.6, h=2)
    sk.sym(head, "front", 1, 4, 5, 6, "9a40c8", emissive=0.6, height=0.45)
    if snout is not None:
        sk.sym(snout, "top", 2, 2, 4, 4, "0e0c10", height=0.3)  # nostrils
    if name == "dragon_exploding":   # dissolve variant: brighter, cracked with light
        n = ctx.noise(6, 3, salt="dissolve")
        m = (n > 0.55) & (sk.alpha > 0.5)
        sk.color[m] = mix(sk.color[m], col("e0b0ff"), 0.6)
        sk.emissive[m] = 0.8
    return sk.tex()


reg(["entity/enderdragon/dragon", "entity/enderdragon/dragon_exploding", "entity/enderdragon/dragon_eyes",
     "entity/enderdragon/dragon_fireball"], dragon)


# ---------------------------------------------------------------- endermite & silverfish

def bug(ctx, path):
    name = path.split("/")[-1]
    sk = Skin(ctx, name)
    if name == "endermite":
        shell = Mat(shades("2a2034", 6, 0.6, 1.5), mottle=0.3, grain=0.25, sss=0.05, smooth=0.5,
                    blotch=(shades("5a3a7a", 6, 0.6, 1.3), 0.62, "small"))
        sk.paint_all([], shell)
        sk.sym(sk.box("body1"), "front", 0, 1, 1, 2, "c070f0", emissive=0.8, height=0.5)
    else:
        shell = Mat(shades("8a8a8e", 6, 0.65, 1.2), mottle=0.3, grain=0.25, sss=0.05, smooth=0.45)
        sk.paint_all([("wing", shell.but(base=0.42, streak=0.6))], shell)
        for b in sk.find("body"):
            sk.band(b, 0, 1, shell.but(base=0.3)) if b.h / sk.k >= 2 else None
        sk.sym(sk.box("body1"), "front", 0, 0, 1, 1, PUPIL, height=0.4)
    return sk.tex()


reg(["entity/endermite/endermite", "entity/silverfish/silverfish"], bug)


# ---------------------------------------------------------------- evoker fangs

def fangs(ctx, path):
    sk = Skin(ctx, "evoker_fangs")
    base = Mat("4a4a50", mottle=0.3, grain=0.25, sss=0.0, smooth=0.3)
    jaw = Mat("d8d0b8", mottle=0.2, grain=0.2, grad=0.4, sss=0.0, smooth=0.45)
    sk.paint_all([("base", base)], jaw)
    for b in sk.find("upper_jaw") + sk.find("lower_jaw"):
        for f in ("front", "back"):
            if f in b.faces:
                for y in range(0, int(b.h / sk.k), 3):
                    sk.frect(b, f, 0, y, 0, y + 1, jaw.but(base=0.85))
        sk.paint(b, Mat("6a2a3a", grain=0.15), faces=("left",))
    return sk.tex()


reg(["entity/illager/evoker_fangs"], fangs)


# ---------------------------------------------------------------- ravager

def ravager(ctx, path):
    sk = Skin(ctx, "ravager")
    hide = Mat("5a5048", mottle=0.3, grain=0.25, sss=0.2, blotch=("6e6258", 0.6, "mid"))
    horn = Mat("d8d0b8", mottle=0.15, grain=0.2, grad=0.4, sss=0.0, smooth=0.45)
    sk.paint_all([("head/horns", horn), ("head#1", hide.but(base=0.4))], hide)
    head = sk.box("head", 0)
    sk.sym(head, "front", 2, 6, 5, 8, "1a1614", height=0.3)
    sk.sym(head, "front", 3, 6, 4, 7, "c8a040", height=0.35, emissive=0.3)
    sk.frect(head, "front", 4, 12, 12, 18, hide.but(base=0.35))
    sk.sym(head, "front", 5, 14, 7, 16, "1a1210", height=0.3)
    jaw = sk.box("jaw")
    for x in range(1, 16, 3):
        sk.frect(jaw, "front", x, 0, x + 1, 2, "e8e0c8", height=0.6)
    for b in sk.find("body"):
        if b.idx == 1:   # saddle-like woven back cover
            sk.paint(b, Mat("6a4a30", grain=0.2, streak=0.6, sss=0.05))
    for l in sk.find("leg"):
        sk.band(l, -3, 0, Mat("2a2420", grain=0.15), bottom=True)
    return sk.tex()


reg(["entity/illager/ravager"], ravager)


# ---------------------------------------------------------------- iron golem

def iron_golem(ctx, path):
    name = path.split("/")[-1]
    sk = Skin(ctx, "iron_golem")
    if "crackiness" in name:
        return cracks(sk, name.split("_")[-1], "4a4642")
    iron = Mat(shades("d8d4cc", 6, 0.68, 1.06), mottle=0.3, grain=0.22, sss=0.0, smooth=0.55,
               blotch=(shades("b8b0a4", 6, 0.68, 1.06), 0.64, "mid"))
    sk.paint_all([], iron)
    for b in sk.boxes:   # vines
        for f, r in b.faces.items():
            sl = sk._sl(*r)
            if sl is None:
                continue
            m = sk.noise["streak"][sl] > 0.72
            v = 0.5 + (sk.grain[sl] - 0.5) * 0.4
            sk._write(sl, sk.ctx.palette(shades("4a7a2a"), v), None, height=0.65, mask=m, sss=0.5, smooth=0.1)
    for b in sk.boxes:  # rivets and plate seams on big faces
        for f in ("front", "back"):
            if f in b.faces and b.w / sk.k >= 6:
                sk.sym(b, f, 1, 1, 2, 2, "8a867e", height=0.7, smooth=0.6)
    head = sk.box("head", 0)
    sk.frect(head, "front", 0, 3, 8, 4, iron.but(base=0.35, blotch=None))
    sk.sym(head, "front", 1, 4, 3, 5, "3a1a14", height=0.3)
    sk.sym(head, "front", 2, 4, 3, 5, "c83a2a", height=0.35, emissive=0.5)
    sk.paint(sk.box("head", 1), iron.but(base=0.65))
    return sk.tex()


reg(["entity/iron_golem/iron_golem", "entity/iron_golem/iron_golem_crackiness_high",
     "entity/iron_golem/iron_golem_crackiness_low", "entity/iron_golem/iron_golem_crackiness_medium"], iron_golem)


# ---------------------------------------------------------------- pandas

def panda(ctx, path):
    name = path.split("/")[-1]
    baby = "baby" in name
    gene = "normal"
    for g in ("aggressive", "brown", "lazy", "playful", "weak", "worried"):
        if g in name:
            gene = g
    sk = Skin(ctx, "panda_baby" if baby else "panda")
    white_c = "ece8e0" if gene != "brown" else "d8c8b0"
    dark_c = "2a2624" if gene != "brown" else "6a4a30"
    white = Mat(white_c, mottle=0.25, grain=0.2, sss=0.35, streak=0.4)
    dark = Mat(dark_c, mottle=0.2, grain=0.2, sss=0.3, streak=0.4)
    sk.paint_all([("leg", dark), ("_leg", dark)], white)
    for b in sk.boxes:
        if b.part.endswith("leg"):
            sk.paint(b, dark)
    body = sk.largest("body")
    # dark shoulder band
    if body is not None:
        if body.quad:
            for f in ("left", "right", "back", "front"):
                if f in body.faces:
                    x0, y0, x1, y1 = body.faces[f]
                    sk.fill((x0, y0, x1, y0 + 8 * sk.k), dark)
            sk.fill(body.faces["top"], dark)
        else:
            for f in ("left", "right"):
                if f in body.faces:
                    x0, y0, x1, y1 = body.faces[f]
                    w = 4 * sk.k
                    sk.fill((x1 - w, y0, x1, y1) if f == "right" else (x0, y0, x0 + w, y1), dark)
            sk.fill(body.faces["front"], dark)
            sk.frect(body, "top", 0, -4, 0, 0, dark)
    head = sk.largest("head")
    hb = [b for b in sk.find("head") if b is not head]
    muzzle = max(hb, key=lambda b: b.w) if hb else None
    for b in hb:
        sk.paint(b, white.but(base=0.62) if b is muzzle else dark)
    if muzzle is not None:
        sk.frect(muzzle, "front", 1, 0, -1, 1, "1a1616", height=0.6, smooth=0.6)
    hw = head.w / sk.k
    ey = 4 if not baby else 2
    px = 2 if not baby else 1
    # eye patches (shape varies with the gene)
    patch_h = 3 if gene != "lazy" else 2
    sk.sym(head, "front", px, ey - 1, px + 3 if not baby else px + 2, ey - 1 + patch_h, dark)
    if gene == "worried":
        sk.sym(head, "front", px + 1, ey - 2, px + 3, ey - 1, dark)
    if gene == "aggressive":
        sk.sym(head, "front", px, ey - 2, px + 2, ey - 1, dark)
    pupil_c = "f0ece4" if gene != "weak" else "d8c0c0"
    sk.sym(head, "front", px + 1, ey, px + 2, ey + 1, pupil_c, height=0.45, smooth=0.7)
    if gene == "lazy":
        sk.sym(head, "front", px + 1, ey, px + 2, ey + 1, dark.p[1], height=0.45)
    if gene == "weak":
        sk.frect(muzzle, "front", 1, 1, 2, 2, "6a8ad8", height=0.6) if muzzle is not None else None
    if gene == "playful":
        sk.frect(head, "front", hw / 2 - 1, ey + 3 if not baby else ey + 2, hw / 2 + 1, ey + 4 if not baby else ey + 3,
                 "d86a7a", height=0.4)
    return sk.tex()


reg([f"entity/panda/{n}" for n in (
    "panda", "panda_aggressive", "panda_brown", "panda_lazy", "panda_playful", "panda_weak", "panda_worried",
    "panda_baby", "aggressive_panda_baby", "brown_panda_baby", "lazy_panda_baby", "playful_panda_baby",
    "weak_panda_baby", "worried_panda_baby")], panda)


# ---------------------------------------------------------------- phantom

def phantom(ctx, path):
    eyes = path.endswith("_eyes")
    sk = Skin(ctx, "phantom")
    head = sk.box("head")
    if eyes:
        sk.sym(head, "front", 0, 1, 2, 2, "60f0a0", emissive=1.0, height=0.5)
        return sk.tex(grain=0)
    hide = Mat("3a4a6a", mottle=0.3, grain=0.25, sss=0.3, smooth=0.4, blotch=("4a5a80", 0.62, "mid"))
    membrane = Mat("6a7aa0", mottle=0.25, grain=0.2, sss=0.5, smooth=0.3)
    sk.paint_all([("left_wing_tip", membrane), ("right_wing_tip", membrane)], hide)
    for b in sk.find("left_wing_tip") + sk.find("right_wing_tip"):
        for f in ("top", "bottom"):
            if f in b.faces:
                x0, y0, x1, y1 = b.faces[f]
                sl = sk._sl(x0, y0, x1, y1)
                rag = sk.noise["small"][sl] > 0.68
                sk.alpha[sl][rag] = 0
    sk.sym(head, "front", 0, 1, 2, 2, "60c890", height=0.4, emissive=0.4)
    sk.frect(head, "front", 2, 2, 5, 3, "1a2030", height=0.3)
    return sk.tex()


reg(["entity/phantom/phantom", "entity/phantom/phantom_eyes"], phantom)


# ---------------------------------------------------------------- sniffer

def sniffer(ctx, path):
    baby = path.endswith("snifflet")
    sk = Skin(ctx, "sniffer_baby" if baby else "sniffer")
    fur = Mat("a8483a", mottle=0.35, grain=0.25, sss=0.3, streak=0.8, blotch=("6a8a3a", 0.68, "big"))
    face = Mat("c8b090", mottle=0.2, grain=0.2, sss=0.35)
    sk.paint_all([("nose", Mat("6a5a40", grain=0.2)), ("lower_beak", face), ("left_ear", fur.but(base=0.45)),
                  ("right_ear", fur.but(base=0.45))], fur)
    head = max(sk.find("head"), key=lambda b: b.h)
    sk.frect(head, "front", 0, -6 if not baby else -4, 0, 0, face)
    sk.sym(head, "front", 2 if not baby else 1, 6 if not baby else 3, 4 if not baby else 3,
           8 if not baby else 4, "1a1410", height=0.4)
    sk.sym(head, "front", 3 if not baby else 2, 6 if not baby else 3, 4 if not baby else 3,
           7 if not baby else 4, "e0d8c0", height=0.45)
    nose = sk.box("nose")
    if nose is not None:
        sk.sym(nose, "front", 3 if not baby else 2, 0, 5 if not baby else 3, 1, "1a1410", height=0.3)
    for l in sk.boxes:
        if "leg" in l.part:
            sk.band(l, -2 if not baby else -1, 0, Mat("3a2a20", grain=0.15), bottom=True)
    return sk.tex()


reg(["entity/sniffer/sniffer", "entity/sniffer/snifflet"], sniffer)


# ---------------------------------------------------------------- snow golem

def snow_golem(ctx, path):
    sk = Skin(ctx, "snow_golem")
    snow = Mat(shades("eef2f6", 6, 0.82, 1.03), mottle=0.3, grain=0.2, sss=0.6, smooth=0.25, porosity=0.6)
    stick = Mat("6a4a2a", mottle=0.2, grain=0.25, sss=0.0, streak=0.6)
    pump = Mat("d8801e", mottle=0.25, grain=0.2, sss=0.3, smooth=0.25)
    sk.paint_all([("left_hand", stick), ("right_hand", stick), ("head", pump)], snow)
    head = sk.box("head")
    for f in SIDES:   # pumpkin ribs
        for x in (2, 5):
            sk.frect(head, f, x, 0, x + 1, 0, pump.but(base=0.35))
    sk.paint(head, Mat("5a7a2a", grain=0.2), faces=("top",))
    sk.sym(head, "front", 1, 2, 3, 4, "2a1608", height=0.25)
    sk.sym(head, "front", 2, 3, 3, 4, "f0c040", height=0.3, emissive=0.6)
    sk.frect(head, "front", 1, 5, 7, 6, "2a1608", height=0.25)
    for x in (2, 5):
        sk.frect(head, "front", x, 6, x + 1, 7, "2a1608", height=0.25)
    body = sk.box("body")
    for y in (3, 6):   # coal buttons
        sk.frect(body, "front", 4, y, 6, y + 1, "2a2a2e", height=0.6)
    return sk.tex()


reg(["entity/snow_golem/snow_golem"], snow_golem)


# ---------------------------------------------------------------- warden

def warden(ctx, path):
    name = path.split("/")[-1]
    sk = Skin(ctx, "warden")
    if name == "warden":
        hide = Mat(shades("1e3a40", 6, 0.8, 1.25), mottle=0.3, grain=0.2, sss=0.3, smooth=0.3,
                   blotch=(shades("2a4e56", 6, 0.8, 1.25), 0.62, "mid"))
        bone = Mat("c8c4b0", mottle=0.15, grain=0.2, sss=0.1)
        sk.paint_all([("left_ribcage", bone), ("right_ribcage", bone), ("left_tendril", Mat("2a5a60", grain=0.2)),
                      ("right_tendril", Mat("2a5a60", grain=0.2))], hide)
        for b in sk.find("left_ribcage") + sk.find("right_ribcage"):
            for f, r in b.faces.items():
                sl = sk._sl(*r)
                if sl is not None:
                    gap = ((sk.ctx.ty[sl] // sk.ctx.s) % 3) != 0
                    sk.alpha[sl][gap] = 0
        head = sk.box("head")
        sk.frect(head, "front", 2, 10, 14, 14, "0e1a1e", height=0.25)   # gaping mouth, no eyes
        torso = sk.box("torso")
        sk.frect(torso, "front", 5, 4, 13, 12, "10262a", height=0.3)    # chest cavity
        return sk.tex()
    # emissive overlay layers
    glow = {"warden_bioluminescent_layer": ("40e0e8", 0.5), "warden_heart": ("50f0f8", 0.0),
            "warden_pulsating_spots_1": ("70f8ff", 0.0), "warden_pulsating_spots_2": ("70f8ff", 0.0)}[name]
    c = glow[0]
    if name == "warden_heart":
        torso = sk.box("torso")
        sk.frect(torso, "front", 7, 6, 11, 10, c, emissive=1.0, height=0.5)
        sk.frect(torso, "front", 8, 7, 10, 9, "e0ffff", emissive=1.0, height=0.5)
    elif name == "warden_bioluminescent_layer":
        for b in sk.boxes:
            for f, r in b.faces.items():
                sl = sk._sl(*r)
                if sl is not None:
                    m = sk.noise["streak"][sl] > 0.74
                    sk._write(sl, col(c), None, height=0.5, mask=m, emissive=0.9, sss=0.3)
        head = sk.box("head")
        sk.frect(head, "front", 3, 5, 6, 6, c, emissive=1.0)
        sk.frect(head, "front", 10, 5, 13, 6, c, emissive=1.0)
    else:
        thr = 0.9 if name.endswith("1") else 0.84
        key = "mid" if name.endswith("1") else "small"
        for b in sk.boxes:
            for f, r in b.faces.items():
                sl = sk._sl(*r)
                if sl is not None:
                    m = (sk.grain[sl] > thr) & (sk.noise[key][sl] > 0.45)
                    sk._write(sl, col(c), None, height=0.55, mask=m, emissive=1.0)
    return sk.tex(grain=0)


reg([f"entity/warden/{n}" for n in ("warden", "warden_bioluminescent_layer", "warden_heart",
                                    "warden_pulsating_spots_1", "warden_pulsating_spots_2")], warden)
