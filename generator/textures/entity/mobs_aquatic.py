"""Aquatic mobs: fish, squids, dolphins, guardians, turtles, axolotls, frogs, tadpoles,
nautiluses (entity_mobs)."""
import numpy as np

from ...registry import register
from .mobs_base import SIDES, Mat, Skin, col, mix, shades

PUPIL = "141214"


def reg(paths, fn, *args):
    for p in paths:
        register(p, lambda ctx, p=p: fn(ctx, p, *args))


def flank_eyes(sk, b, fy, from_front=0, c=PUPIL, ring=None, size=1):
    """Eyes on the left/right faces of a forward-facing box."""
    if b is None:
        return
    for f in ("right", "left"):
        if f not in b.faces:
            continue
        dm = b.d / sk.k
        x = dm - from_front - size if f == "right" else from_front
        if ring is not None:
            sk.frect(b, f, x - (1 if f == "left" else 0) * 0 , fy, x + size, fy + size, ring, height=0.45)
        sk.frect(b, f, x, fy, x + size, fy + size, c, height=0.4, smooth=0.8, sss=0.0)


def scales(sk, b, mat, period=2):
    """Scale rows: slightly darker every other row (offset grid)."""
    if b is None:
        return
    for f in ("left", "right", "top"):
        if f not in b.faces:
            continue
        x0, y0, x1, y1 = b.faces[f]
        sl = sk._sl(x0, y0, x1, y1)
        if sl is None:
            continue
        tx = ((sk.ctx.x[sl] - x0) / sk.k).astype(int)
        ty = ((sk.ctx.y[sl] - y0) / sk.k).astype(int)
        m = ((tx + (ty % 2)) % period == 0) & (ty % 2 == 0)
        sk.color[sl][m] *= 0.9


def belly_band(sk, b, mat, frac=0.35):
    if b is None:
        return
    for f in ("left", "right", "front", "back"):
        if f in b.faces:
            x0, y0, x1, y1 = b.faces[f]
            sk.fill((x0, y1 - (y1 - y0) * frac, x1, y1), mat, off=-0.02)
    if "bottom" in b.faces:
        sk.fill(b.faces["bottom"], mat)


# ---------------------------------------------------------------- fish

def cod(ctx, path):
    sk = Skin(ctx, "cod")
    body = Mat("a89a7a", mottle=0.3, grain=0.25, sss=0.2, smooth=0.5, blotch=("7a6a4a", 0.66, "small"))
    fin = Mat("c8b890", mottle=0.15, grain=0.2, sss=0.4, smooth=0.4)
    sk.paint_all([("body/", fin), ("fin", fin), ("tail", fin), ("nose", body.but(base=0.62))], body)
    for b in (sk.box("body"), sk.box("head")):
        belly_band(sk, b, Mat("e8e0d0", grain=0.15, sss=0.2, smooth=0.5))
    flank_eyes(sk, sk.box("head"), 1, from_front=0)
    scales(sk, sk.box("body"), body)
    return sk.tex()


def salmon(ctx, path):
    sk = Skin(ctx, "salmon")
    body = Mat("a84a3a", mottle=0.3, grain=0.25, sss=0.2, smooth=0.5)
    back = Mat("4a5a5a", mottle=0.25, grain=0.25, sss=0.2, smooth=0.5)
    fin = Mat("8a4a3a", mottle=0.15, grain=0.2, sss=0.4, smooth=0.4)
    sk.paint_all([("fin", fin), ("tail", fin), ("head", back)], body)
    for key in ("body_front", "body_back"):
        b = sk.box(key)
        if b is not None:
            sk.paint(b, back, faces=("top",))
            for f in ("left", "right"):
                sk.frect(b, f, 0, 0, 0, 1, back)
            belly_band(sk, b, Mat("e8c8b0", grain=0.15, sss=0.2, smooth=0.5), 0.25)
            sk.face_spots(b, Mat("2a2a2a", grain=0.1), 0.8, "small", faces=("left", "right", "top"))
    flank_eyes(sk, sk.box("head"), 1, from_front=0)
    return sk.tex()


def pufferfish(ctx, path):
    sk = Skin(ctx, "puffer_fish_big")
    skin = Mat("e0c040", mottle=0.3, grain=0.25, sss=0.3, smooth=0.4, blotch=("b89a30", 0.68, "small"))
    spike = Mat("f0eac8", mottle=0.1, grain=0.2, sss=0.1, grad=0.4)
    for model in ("puffer_fish_small", "puffer_fish_medium", "puffer_fish_big"):
        sub = Skin(ctx, model)
        for b in sub.boxes:
            if "spike" in b.part:
                sk.paint(b, spike)
            elif "fin" in b.part or "tail" in b.part:
                sk.paint(b, Mat("c8a040", grain=0.2, sss=0.4))
            elif "eye" in b.part:
                sk.paint(b, Mat("1a1a1a", grain=0.05, smooth=0.8, sss=0.0))
            else:
                sk.paint(b, skin)
                belly_band(sk, b, Mat("f0ead0", grain=0.15, sss=0.2), 0.3)
                bw = b.w / sk.k
                if bw >= 5:   # big / medium: eyes on the front face
                    sk.sym(b, "front", 1, 1, 2, 2, PUPIL, height=0.4, smooth=0.8)
                    sk.frect(b, "front", bw / 2 - 1, -2, bw / 2 + 1, -1, "6a4a20", height=0.3)
                    for f in ("left", "right", "top", "back"):   # dark speckles
                        if f in b.faces:
                            sk.spots(b.faces[f], Mat("6a6a30", grain=0.1), 0.78, "small")
    return sk.tex()


def tropical(ctx, path):
    """Tropical fish: grayscale (tinted in game). Base body or white pattern overlay."""
    name = path.split("/")[-1]
    shape = "a" if name.startswith("tropical_a") else "b"
    pattern = int(name.split("_")[-1]) if "pattern" in name else 0
    sk = Skin(ctx, f"tropical_fish_{shape}")
    if not pattern:
        body = Mat(shades("e8e8e8", 5, 0.75, 1.05), mottle=0.2, grain=0.2, sss=0.3, smooth=0.5)
        fin = Mat(shades("f4f4f4", 5, 0.8, 1.05), mottle=0.1, grain=0.15, sss=0.5, smooth=0.4)
        sk.paint_all([("body/", fin), ("fin", fin), ("tail", fin)], body)
        b = sk.box("body")
        flank_eyes(sk, b, 1, from_front=1, c="2a2a2a")
        return sk.tex()
    white = Mat(shades("f0f0f0", 5, 0.82, 1.05), mottle=0.1, grain=0.15, sss=0.3, smooth=0.5)
    b = sk.box("body")
    dm, hm = b.d / sk.k, b.h / sk.k
    k = sk.k
    for f in ("left", "right", "top", "bottom"):
        if f not in b.faces:
            continue
        x0, y0, x1, y1 = b.faces[f]
        sl = sk._sl(x0, y0, x1, y1)
        if sl is None:
            continue
        u = (sk.ctx.x[sl] - x0) / k          # along body (d)
        v = (sk.ctx.y[sl] - y0) / k
        if f == "left":
            u = dm - u
        w = x1 - x0
        if pattern == 1:     # vertical bands
            m = (np.floor(u) % 3) == 1
        elif pattern == 2:   # rear half
            m = u > dm * 0.55
        elif pattern == 3:   # horizontal stripe
            m = (np.abs(v - hm / 2) < 0.75) if f in ("left", "right") else np.zeros_like(u, bool)
        elif pattern == 4:   # dots
            m = ((np.floor(u) + np.floor(v)) % 3 == 0) & ((np.floor(v)) % 2 == 0)
        elif pattern == 5:   # top half
            m = (v < hm / 2) if f in ("left", "right") else (f == "top") | np.zeros_like(u, bool)
        else:                # head mask + tail tip
            m = (u < 2) | (u > dm - 1)
        vv = white.base + (sk.grain[sl] - 0.5) * white.grain
        sk._write(sl, sk.ctx.palette(white.p, vv), white, height=0.5, mask=m)
    if pattern in (2, 5, 6):
        for bb in sk.boxes:
            if "fin" in bb.part or "tail" in bb.part:
                sk.paint(bb, white)
    return sk.tex()


reg(["entity/fish/cod"], cod)
reg(["entity/fish/salmon"], salmon)
reg(["entity/fish/pufferfish"], pufferfish)
reg([f"entity/fish/tropical_{s}{p}" for s in ("a", "b") for p in [""] + [f"_pattern_{i}" for i in range(1, 7)]],
    tropical)


# ---------------------------------------------------------------- squids

def squid(ctx, path):
    name = path.split("/")[-1]
    glow = name.startswith("glow")
    baby = name.endswith("_baby")
    sk = Skin(ctx, "squid_baby" if baby else "squid")
    base_c = "2a4a6a" if not glow else "1e6a6a"
    body = Mat(base_c, mottle=0.3, grain=0.25, sss=0.4, smooth=0.45,
               blotch=(mix(base_c, "6ab0d0" if not glow else "60f0d0", 0.45), 0.66, "mid"))
    sk.paint_all([("tentacle", body.but(base=0.45))], body)
    b = sk.box("body")
    bw = b.w / sk.k
    ey = -5 if not baby else -4
    for f in ("front", "back", "left", "right"):
        sk.sym(b, f, 2 if not baby else 1, ey, 4 if not baby else 3, ey + 2 if not baby else ey + 1,
               "e8e4d0" if not glow else "c8fff0", height=0.45, emissive=0.6 if glow else 0.0) if f == "front" else None
    sk.sym(b, "front", 3 if not baby else 2, ey, 4 if not baby else 3, ey + 1, PUPIL, height=0.4)
    t = sk.box("tentacle1")
    if t is not None:   # suckers
        for y in range(2, int(t.h / sk.k), 3):
            sk.frect(t, "front", 0, y, 0, y + 1, mix(base_c, "e0c0c0", 0.5), height=0.55)
    if glow:   # bioluminescent freckles
        for bb in sk.boxes:
            for f, r in bb.faces.items():
                sl = sk._sl(*r)
                if sl is None:
                    continue
                m = (sk.grain[sl] > 0.95)
                sk._write(sl, col("7affe8"), None, height=0.55, mask=m, emissive=1.0, sss=0.3, smooth=0.5)
    return sk.tex()


reg([f"entity/squid/{n}" for n in ("squid", "squid_baby", "glow_squid", "glow_squid_baby")], squid)


# ---------------------------------------------------------------- dolphin

def dolphin(ctx, path):
    baby = path.endswith("_baby")
    sk = Skin(ctx, "dolphin_baby" if baby else "dolphin")
    skin = Mat("7a8a9a", mottle=0.2, grain=0.18, sss=0.3, smooth=0.6)
    sk.paint_all([("fin", skin.but(base=0.45)), ("tail_fin", skin.but(base=0.45))], skin)
    light = Mat("d8dce0", mottle=0.1, grain=0.15, sss=0.3, smooth=0.6)
    for b in sk.boxes:
        if b.part in ("head", "body", "tail") and b.w / sk.k >= 4:
            belly_band(sk, b, light, 0.4)
    head = max(sk.find("head"), key=lambda b: b.w)
    flank_eyes(sk, head, 2 if not baby else 1, from_front=1, c=PUPIL)
    for b in sk.find("head") + sk.find("body"):
        if b.w / sk.k <= 2:   # beak
            sk.paint(b, light.but(base=0.5))
    return sk.tex()


reg(["entity/dolphin/dolphin", "entity/dolphin/dolphin_baby"], dolphin)


# ---------------------------------------------------------------- guardians

def guardian(ctx, path):
    name = path.split("/")[-1]
    if name == "guardian_beam":
        return beam(ctx)
    elder = name == "guardian_elder"
    sk = Skin(ctx, "elder_guardian" if elder else "guardian")
    hide_c = "6a9a8a" if not elder else "c8c4b0"
    hide = Mat(hide_c, mottle=0.3, grain=0.25, sss=0.2, smooth=0.4,
               blotch=(mix(hide_c, "d87a40" if not elder else "8a8070", 0.45), 0.66, "mid"))
    spine = Mat("e8e0c8", mottle=0.1, grain=0.15, grad=0.5, sss=0.0, smooth=0.5)
    sk.paint_all([("spine", spine), ("eye", Mat("e8e4d0", grain=0.1, sss=0.0, smooth=0.8))], hide)
    eye = sk.box("eye")
    sk.frect(eye, "front", 1, 0, 2, 2, "2a1a1a" if not elder else "6a2a6a", height=0.45, smooth=0.9)
    body = sk.box("body")
    # plated grid on the large faces
    for f in ("front", "back", "left", "right", "top", "bottom"):
        if f in body.faces:
            x0, y0, x1, y1 = body.faces[f]
            sl = sk._sl(x0, y0, x1, y1)
            tx = ((sk.ctx.x[sl] - x0) / sk.k).astype(int)
            ty = ((sk.ctx.y[sl] - y0) / sk.k).astype(int)
            m = (tx % 4 == 0) | (ty % 4 == 0)
            sk.color[sl][m] *= 0.85
            sk.height[sl][m] = 0.35
    sk.frect(body, "front", 3, 3, 9, 9, "3a2a2a", height=0.3)   # eye socket (eye box sits in front)
    for t in sk.find("tail"):
        sk.band(t, 0, 1, hide.but(base=0.35))
    return sk.tex()


def beam(ctx):
    """Guardian laser: bright core streaks, transparent edges (scrolls in game)."""
    sk = Skin(ctx)
    x, y = ctx.x / ctx.w, ctx.y / ctx.h
    wav = 0.5 + 0.5 * np.sin(y * np.pi * 8 + np.sin(x * np.pi * 4) * 1.5)
    core = np.abs(x - 0.5) < 0.18 + wav * 0.08
    glow = np.abs(x - 0.5) < 0.42
    c = np.where(core[..., None], mix("f8f0ff", "c0a0ff", wav[..., None] * 0.5), col("8a5ad8"))
    sk.color[:] = c
    sk.alpha[:] = np.where(core, 1.0, np.where(glow, 0.6, 0.0))
    sk.emissive[:] = np.where(glow, 1.0, 0.0)
    sk.height[:] = 0.5
    return sk.tex(grain=0)


reg(["entity/guardian/guardian", "entity/guardian/guardian_elder", "entity/guardian/guardian_beam"], guardian)


# ---------------------------------------------------------------- turtle

def turtle(ctx, path):
    baby = path.endswith("_baby")
    sk = Skin(ctx, "turtle_baby" if baby else "turtle")
    skin = Mat("6aa058", mottle=0.25, grain=0.22, sss=0.3, smooth=0.3, blotch=("a8c870", 0.68, "small"))
    shell = Mat("3a6a3a", mottle=0.3, grain=0.25, sss=0.05, smooth=0.5, blotch=("5a8a3a", 0.6, "mid"))
    belly = Mat("d8c88a", mottle=0.15, grain=0.2, sss=0.1, smooth=0.4)
    sk.paint_all([("body/body_rotation#1", belly), ("body2", belly), ("body", shell)], skin)
    shell_box = sk.box("body") if baby else sk.box("body/body_rotation", 0)
    if shell_box is not None:   # scute outlines on the shell back
        f = "back" if shell_box.quad else "top"
        if f in shell_box.faces:
            x0, y0, x1, y1 = shell_box.faces[f]
            sl = sk._sl(x0, y0, x1, y1)
            tx = ((sk.ctx.x[sl] - x0) / sk.k).astype(int)
            ty = ((sk.ctx.y[sl] - y0) / sk.k).astype(int)
            per = 5 if not baby else 2
            m = ((tx + (ty // per) * 2) % per == 0) | (ty % per == 0)
            sk.color[sl][m] = col("2a4a2a")
            sk.height[sl][m] = 0.35
    head = sk.box("head")
    hw = head.w / sk.k
    if baby:
        sk.sym(head, "front", 0, 1, 1, 2, PUPIL, height=0.4)
    else:
        flank_eyes(sk, head, 1, from_front=1)
        sk.frect(head, "front", 1, -2, -1, -1, "3a5a2a", height=0.35)
    return sk.tex()


reg(["entity/turtle/turtle", "entity/turtle/turtle_baby"], turtle)


# ---------------------------------------------------------------- axolotl

AXOLOTLS = {"lucy": ("f0a8c0", "d85a8a"), "wild": ("7a5a3a", "c8a070"), "gold": ("e8c040", "f0e090"),
            "cyan": ("b8e0ec", "e070b0"), "blue": ("4a5ad8", "8ab0f0")}


def axolotl(ctx, path):
    name = path.split("/")[-1]
    baby = name.endswith("_baby")
    key = name.replace("_baby", "")[8:]
    main_c, gill_c = AXOLOTLS[key]
    sk = Skin(ctx, "axolotl_baby" if baby else "axolotl")
    skin = Mat(main_c, mottle=0.25, grain=0.22, sss=0.5, smooth=0.55,
               blotch=(mix(main_c, "2a1a10", 0.35), 0.66, "small") if key == "wild" else None)
    gill = Mat(gill_c, mottle=0.2, grain=0.25, sss=0.6, smooth=0.4)
    sk.paint_all([("top_gills", gill), ("left_gills", gill), ("right_gills", gill),
                  ("leg", skin.but(base=0.62)), ("tail", skin.but(base=0.6))], skin)
    head = sk.box("head")
    hw = head.w / sk.k
    sk.sym(head, "front", 1, 1, 2, 2, PUPIL, height=0.45, smooth=0.9)
    sk.frect(head, "front", 2, -2 if not baby else -1, -2, -1 if not baby else 0, mix(main_c, "2a1010", 0.5),
             height=0.35)
    body = max(sk.find("body"), key=lambda b: b.w)
    belly_band(sk, body, skin.but(base=0.68, blotch=None), 0.3)
    return sk.tex()


reg([f"entity/axolotl/axolotl_{k}{b}" for k in AXOLOTLS for b in ("", "_baby")], axolotl)


# ---------------------------------------------------------------- frogs & tadpole

FROGS = {"temperate": ("c87a3a", "e8c890"), "warm": ("e0dccc", "b8a888"), "cold": ("5a8a3a", "a8c870")}


def frog(ctx, path):
    key = path.split("/")[-1][5:]
    main_c, belly_c = FROGS[key]
    sk = Skin(ctx, "frog")
    skin = Mat(main_c, mottle=0.3, grain=0.22, sss=0.45, smooth=0.55, blotch=(mix(main_c, "3a2a1a", 0.4), 0.7, "small"))
    belly = Mat(belly_c, mottle=0.15, grain=0.2, sss=0.45, smooth=0.5)
    sk.paint_all([("croaking_body", Mat(mix(belly_c, "ffffff", 0.3), grain=0.15, sss=0.5, alpha=0.9)),
                  ("tongue", Mat("d86a7a", grain=0.15, sss=0.5, smooth=0.6)),
                  ("eyes", Mat(main_c, grain=0.2, sss=0.4))], skin)
    for b in sk.find("eyes"):
        sk.frect(b, "front", 0, 0, 0, 0, "e8d860", height=0.55, smooth=0.9)
        sk.frect(b, "front", 1, 0, 2, 2, PUPIL, height=0.5, smooth=0.9)
        sk.frect(b, "top", 0, 0, 0, 0, Mat(main_c, grain=0.2))
    for b in sk.find("body"):
        if "bottom" in b.faces:
            sk.fill(b.faces["bottom"], belly)
    for b in sk.boxes:   # webbed feet planes
        if b.part.endswith(("arm", "leg")) and b.h / sk.k == 0:
            sk.paint(b, skin.but(base=0.45))
    head = sk.box("head", 1)
    if head is not None:
        sk.frect(head, "front", 0, -1, 0, 0, mix(main_c, "2a1a10", 0.45), height=0.35)
    return sk.tex()


def tadpole(ctx, path):
    sk = Skin(ctx, "tadpole")
    m = Mat("5a4a3a", mottle=0.2, grain=0.2, sss=0.4, smooth=0.5)
    sk.paint_all([("tail", m.but(base=0.65))], m)
    b = sk.box("body")
    sk.sym(b, "front", 0, 0, 1, 1, "1a1412", height=0.4)
    return sk.tex()


reg([f"entity/frog/frog_{k}" for k in FROGS], frog)
reg(["entity/tadpole/tadpole"], tadpole)


# ---------------------------------------------------------------- nautilus

def nautilus(ctx, path):
    name = path.split("/")[-1]
    baby = name.endswith("_baby")
    zombie = name.startswith("zombie")
    coral = name.endswith("coral")
    model = name
    sk = Skin(ctx, model)
    shell_c = "e8dcc8" if not zombie else "8a9a88"
    shell = Mat(shell_c, mottle=0.25, grain=0.2, sss=0.1, smooth=0.6, f0=0.06)
    body = Mat("c88a6a" if not zombie else "5a7a5a", mottle=0.25, grain=0.22, sss=0.4, smooth=0.5)
    sk.paint_all([("shell/", None), ("shell", shell), ("body", body), ("upper_mouth", body.but(base=0.45)),
                  ("lower_mouth", body.but(base=0.45)), ("inner_mouth", Mat("3a1a1a", grain=0.1))], shell,
                 skip=("shell/",))
    # tiger stripes across the shell
    for b in sk.find("shell"):
        if b.part != "shell":
            continue
        for f, (x0, y0, x1, y1) in b.faces.items():
            sl = sk._sl(x0, y0, x1, y1)
            if sl is None:
                continue
            t = (sk.ctx.x[sl] - x0) / sk.k + (sk.noise["mid"][sl] - 0.5) * 2
            m = (t % 4) < 1.4
            sk.color[sl][m] = mix(shell_c, "8a4a2a" if not zombie else "3a4a3a", 0.6)
    bb = max(sk.find("body"), key=lambda b: b.d)
    flank_eyes(sk, bb, 2 if not baby else 1, from_front=2 if not baby else 1, c="1a1a1a" if not zombie else "c8e060")
    if zombie:
        for b in sk.boxes:
            for f, r in b.faces.items():
                sk.spots(r, Mat("3a4a3a", grain=0.2), 0.75, "small")
    if coral:
        colors = {"pink": "e070a0", "red": "c83a3a", "yellow": "e8c840", "blue": "3a6ad8"}
        for b in sk.find("shell/"):
            cname = b.part.split("/")[1].split("_")[0]
            c = colors.get(cname, "e070a0")
            sk.paint(b, Mat(c, mottle=0.3, grain=0.3, sss=0.3))
            for f, r in b.faces.items():
                sl = sk._sl(*r)
                if sl is not None:
                    sk.alpha[sl][sk.noise["small"][sl] > 0.62] = 0
    return sk.tex()


reg(["entity/nautilus/nautilus", "entity/nautilus/nautilus_baby", "entity/nautilus/zombie_nautilus",
     "entity/nautilus/zombie_nautilus_coral"], nautilus)
