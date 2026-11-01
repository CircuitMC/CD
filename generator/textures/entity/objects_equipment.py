"""Equipment layers: humanoid armor (adult + baby), leggings, elytra, wolf / horse /
nautilus armor, llama carpets, happy ghast harnesses and every saddle.

Layouts (model texels) from the OptiFine CEM template .jem files in
github.com/ewanhowell5195/cemTemplateModels (armor_layer_1/2, elytra, wolf_armor,
horse_armor, horse/donkey/mule/pig/strider/camel(_husk)_saddle, llama_decor,
trader_llama(_baby)_decor, happy_ghast_harness, nautilus). Unconfirmed guesses:
humanoid_baby (no template; mirrors the zombie_baby template boxes) and the
nautilus armor/saddle (assumed to reuse the nautilus shell boxes).
  humanoid 64x32: head (0,0) 8x8x8, body (16,16) 8x12x4, arm (40,16) 4x12x4, leg (0,16) 4x12x4
  humanoid_baby 64x64 (GUESS): head (3,3) 6^3, body (16,16) 4x5x2, arms (28,16)/(36,16) 2x5x2,
      legs (0,16)/(8,16) 2x4x2 (upper rows leggings, lower rows boots)
  elytra 64x32: wing (22,0) 10x20x2
  wolf 64x32: body (18,14) 6x9x6, mane (21,0) 8x6x7, legs (0,18) 2x8x2
  horse 64x64: body (0,32) 10x10x22, neck (0,35) 4x12x7, head (0,13) 6x5x7,
      mouth (0,25) 4x5x5, legs (48,21) 4x11x4; saddle parts see _equine_saddle
  llama 128x64: body (29,0) 12x18x10 (rotated: front face = back of the animal), neck (0,14) 8x18x6
  baby llama 64x64: body (0,15) 8x6x13, head (0,0) 6x11x4
  happy ghast harness: model 64x64 drawn on 128x128 (k=2): harness (0,0) 16^3, goggles (0,32) 16x5x5
  nautilus 128x128: shell (0,0) 14x10x16, lower (0,26) 14x8x20
  pig 64x64: body (28,8) 10x16x8 (rotated);  strider 64x128: body (0,0) 16x14x16
  camel 128x128: see _camel_saddle
"""
import numpy as np

from ...engine import ALBEDO_METAL, COPPER, GOLD, IRON, pal
from ...materials import lerp
from ...registry import register
from .objects_common import DYE_ORDER, DYES, Sheet, frame, gray, metal_field, ramp

# ------------------------------------------------------------------ materials

MATS = {
    "leather": dict(p=pal("6a6a6a", "8a8a8a", "a2a2a2", "b6b6b6", "c8c8c8", "dadada"), kind="leather"),
    "chainmail": dict(p=pal("2a2a30", "4a4a52", "6a6a74", "8e8e98", "b0b0ba", "d0d0d8"), kind="chain", metal=IRON),
    "iron": dict(p=pal("4a4a52", "6e6e78", "9494a0", "b6b6c0", "d4d4dc", "eeeef4"), kind="plate", metal=IRON),
    "gold": dict(p=pal("6a4808", "9a6e0e", "c8961c", "e4b834", "f4d65e", "fff0a0"), kind="plate", metal=GOLD),
    "diamond": dict(p=pal("0b4448", "137078", "1e9ea0", "3cc6c4", "7ce6e0", "c4fff8"), kind="gem"),
    "netherite": dict(p=pal("19151a", "28222a", "372f39", "463c48", "574b59", "6c5f6e"), kind="plate",
                      metal=ALBEDO_METAL),
    "copper": dict(p=pal("5a2a16", "8a4426", "b05c34", "c87446", "de9060", "f0b288"), kind="plate", metal=COPPER),
    "turtle_scute": dict(p=pal("1e4a1a", "2c6a26", "3c8a32", "52a440", "6ebe52", "92d670"), kind="scute"),
    "armadillo_scute": dict(p=pal("5a3430", "7a4a42", "96605a", "ad746c", "c28a80", "d6a498"), kind="scute"),
}
SADDLE = pal("2e1a0c", "4a2c14", "64391b", "7c4824", "93592e", "a86c3a")
IRON_P = pal("34343a", "5d5d66", "8a8a94", "b5b5bf", "dcdce4")
GOLD_P = pal("6a4a08", "a87a14", "d8a92a", "f2d054", "fff1a6")


def _surface(ctx, mat, salt):
    """Color + height field for an armor material."""
    p, kind = mat["p"], mat["kind"]
    if kind == "leather":
        n = ctx.noise(4, 2, 0.5, salt=f"lt{salt}")
        t = ctx.texel_noise(f"ltt{salt}")
        v = n * 0.5 + t * 0.35 + 0.1
        return ctx.palette(p[1:-1], v), 0.5 + n * 0.08
    if kind == "chain":
        ring = ((ctx.tx + (ctx.ty // 1) % 2) % 2 == 0)
        v = np.where(ring, 0.75, 0.35) + ctx.texel_noise(f"ch{salt}") * 0.2
        return ctx.palette(p[1:], np.clip(v, 0, 1)), np.where(ring, 0.65, 0.4)
    if kind == "gem":
        vo = ctx.voronoi(18, salt=f"gm{salt}", min_dist=3)
        facet = np.clip(-(vo["dx"] * 0.7 + vo["dy"]) / 3 + 0.5, 0, 1)
        return ctx.palette(p[1:-1], facet * 0.7 + ctx.texel_noise(f"gt{salt}") * 0.3), 0.55 + facet * 0.1
    if kind == "scute":
        vo = ctx.voronoi(26, salt=f"sc{salt}", min_dist=3)
        border = (vo["f2"] - vo["f1"]) < 0.7
        dome = np.clip(-(vo["dx"] + vo["dy"]) / 4 + 0.55, 0, 1)
        c = ctx.palette(p[1:], dome * 0.75 + ctx.texel_noise(f"st{salt}") * 0.25)
        return np.where(border[..., None], p[0], c), np.where(border, 0.3, 0.55 + dome * 0.15)
    b = ctx.noise(1, 2, 0.5, salt=f"pb{salt}", stretch=(5, 1))
    n = ctx.noise(5, 2, 0.5, salt=f"pn{salt}")
    v = np.clip(0.5 + (b - 0.5) * 0.3 + (n - 0.5) * 0.45, 0, 1)
    return ctx.palette(p[1:-1] if mat.get("metal") == IRON else p[2:], v), 0.55 + (b - 0.5) * 0.05


def _outline(mat):
    return None if mat["kind"] in ("leather", "chain") else mat["p"][0] * 0.9 + mat["p"][1] * 0.1


def _fill(sh, mask, mat, surf, alpha=1.0):
    c, h = surf
    kind = mat["kind"]
    kw = dict(smooth=0.25, porosity=0.3) if kind == "leather" else dict(smooth=0.7, porosity=0.0)
    if kind == "gem":
        kw = dict(smooth=0.85, f0=0.17)
    if kind == "scute":
        kw = dict(smooth=0.45, f0=0.05)
    sh.put(mask, c, alpha=alpha, height=h, metal=mat.get("metal"), **kw)
    if kind == "chain":
        # Small see-through gaps between links.
        holes = mask & ((sh.ctx.tx % 2 == 1) & (sh.ctx.ty % 2 == 1))
        sh.alpha[holes] = 0.0


def _edge_shade(sh, mask, faces, outline=None):
    """Per-face outline + inner top-left highlight: plates read as separate raised pieces."""
    ctx = sh.ctx
    s = ctx.s
    for r in faces.values():
        m = mask & sh.rect(r)
        if not m.any():
            continue
        er = m & np.roll(m, s, 0) & np.roll(m, -s, 0) & np.roll(m, s, 1) & np.roll(m, -s, 1)
        ring = m & ~er
        if min(r[2] - r[0], r[3] - r[1]) <= 3 * sh.k:
            sh.shade(ring, 0.86)   # tiny faces: a full outline would swallow them
            continue
        if outline is not None:
            sh.color[ring] = outline
        else:
            sh.shade(ring, 0.72)
        hl = er & ~(np.roll(er, s, 0) & np.roll(er, s, 1))
        sh.shade(hl, 1.16)
        lo = er & ~(np.roll(er, -s, 0) & np.roll(er, -s, 1)) & ~hl
        sh.shade(lo, 0.88)


def _rows(sh, r, a, b):
    """Rows a..b (texels from the top of face r; negative = from bottom)."""
    x0, y0, x1, y1 = r
    ya = y0 + a if a >= 0 else y1 + a
    yb = min(y1, y0 + b) if b > 0 else y1 + b
    return sh.ctx.rect(x0, max(y0, ya), x1, yb) > 0.5


def _cols(sh, r, a, b):
    x0, y0, x1, y1 = r
    xa = x0 + a if a >= 0 else x1 + a
    xb = min(x1, x0 + b) if b > 0 else x1 + b
    return sh.ctx.rect(max(x0, xa), y0, xb, y1) > 0.5


SIDES = ("right", "front", "left", "back")


# ------------------------------------------------------------------ humanoid pieces

def _helmet(sh, f, mat, surf, deco):
    """f: faces of an 8x8x8-ish head box."""
    ctx = sh.ctx
    m = sh.rect(f["top"])
    for n in ("right", "left", "back"):
        m |= _rows(sh, f[n], 0, 5 if n != "back" else 7)
    # cheek guards next to the face (front = minZ side: right face's right end, left face's left end)
    m |= _rows(sh, f["right"], 5, 7) & _cols(sh, f["right"], -3, 99)
    m |= _rows(sh, f["left"], 5, 7) & _cols(sh, f["left"], 0, 3)
    fr = f["front"]
    m |= _rows(sh, fr, 0, 3) | _cols(sh, fr, 0, 1) & _rows(sh, fr, 0, 7) | _cols(sh, fr, -1, 99) & _rows(sh, fr, 0, 7)
    if mat["kind"] in ("plate", "chain") and mat["p"] is not MATS["gold"]["p"]:
        cx = (fr[0] + fr[2]) // 2
        m |= (ctx.rect(cx - 1, fr[1] + 3, cx + 1, fr[1] + 6) > 0.5)  # nose guard
    _fill(sh, m, mat, surf)
    _edge_shade(sh, m, f, _outline(mat))
    if deco:
        # Crest ridge along the top centre.
        t = f["top"]
        cx = (t[0] + t[2]) / 2
        ridge = (ctx.rect(cx - 0.5, t[1], cx + 0.5, t[3]) > 0.5)
        sh.shade(ridge, 1.22)
    return m


def _chest(sh, body, arm_faces, mat, surf, deco, arm_rows=6):
    ctx = sh.ctx
    m = sh.rect(body["top"])
    for n in SIDES:
        m |= sh.rect(body[n])
    _fill(sh, m, mat, surf)
    _edge_shade(sh, m, body, _outline(mat))
    fr = body["front"]
    # Breastplate ridge + lower plate seam.
    cx = (fr[0] + fr[2]) / 2
    if mat["kind"] != "chain":
        sh.shade(ctx.rect(cx - 0.5, fr[1] + 1, cx + 0.5, fr[3] - 3), 1.15)
        seam = _rows(sh, fr, -3, -2) | _rows(sh, body["back"], -3, -2)
        sh.shade(seam, 0.72)
        for n in ("right", "left"):
            sh.shade(_rows(sh, body[n], -3, -2), 0.72)
    if mat["kind"] == "leather":
        stitch = _rows(sh, fr, 1, 2) & ((ctx.tx % 2) == 0)
        sh.shade(stitch, 0.85)
    if deco:
        trim = _rows(sh, fr, 0, 1) | _rows(sh, body["back"], 0, 1)
        sh.shade(trim, 1.2)
    for af in arm_faces:
        am = sh.rect(af["top"])
        for n in SIDES:
            am |= _rows(sh, af[n], 0, arm_rows)
        _fill(sh, am, mat, surf)
        _edge_shade(sh, am, af, _outline(mat))
        for n in SIDES:
            sh.shade(_rows(sh, af[n], arm_rows - 1, arm_rows), 0.8)
        m |= am
    return m


def _boots(sh, legs, mat, surf, rows=5):
    m = np.zeros((sh.ctx.H, sh.ctx.W), bool)
    for f in legs:
        lm = sh.rect(f["bottom"])
        for n in SIDES:
            lm |= _rows(sh, f[n], -rows, 99)
        _fill(sh, lm, mat, surf)
        _edge_shade(sh, lm, f, _outline(mat))
        for n in SIDES:
            sh.shade(_rows(sh, f[n], -1, 99), 0.7)  # sole
        m |= lm
    return m


def _leggings(sh, legs, waist, mat, surf, leg_rows=10, waist_rows=5, waist_full=False):
    ctx = sh.ctx
    m = np.zeros((ctx.H, ctx.W), bool)
    if waist is not None:
        wm = sh.rect(waist["bottom"])
        for n in SIDES:
            wm |= sh.rect(waist[n]) if waist_full else _rows(sh, waist[n], -waist_rows, 99)
        _fill(sh, wm, mat, surf)
        _edge_shade(sh, wm, waist, _outline(mat))
        for n in SIDES:
            belt = sh.rect(waist[n]) & _rows(sh, waist[n], -waist_rows, -waist_rows + 1) if not waist_full \
                else _rows(sh, waist[n], 0, 1)
            sh.shade(belt, 0.75)
        m |= wm
    for f in legs:
        lm = sh.rect(f["top"])
        for n in SIDES:
            lm |= _rows(sh, f[n], 0, leg_rows)
        _fill(sh, lm, mat, surf)
        _edge_shade(sh, lm, f, _outline(mat))
        # knee plate
        if mat["kind"] in ("plate", "gem"):
            fr = f["front"]
            k = ctx.rect(fr[0], fr[1] + leg_rows // 2, fr[2], fr[1] + leg_rows // 2 + 2) > 0.5
            sh.shade(k & lm, 1.15)
        m |= lm
    return m


def _overlay_leather(sh, leather_mask_parts):
    """Undyed details for leather: brass buckles and lacing."""
    ctx = sh.ctx
    for kind, r in leather_mask_parts:
        x0, y0, x1, y1 = r
        cx = (x0 + x1) // 2
        if kind == "buckle":
            m = ctx.rect(cx - 1, y0, cx + 1, y1) > 0.5
            sh.put(m, ctx.palette(GOLD_P[1:4], ctx.texel_noise("bk")), height=0.8, metal=GOLD, smooth=0.6)
            sh.shade(ctx.rect(cx - 1, y0, cx, y1), 1.2)
        elif kind == "lace":
            m = (ctx.rect(x0, y0, x1, y1) > 0.5) & (((ctx.tx + ctx.ty) % 2) == 0)
            sh.put(m, pal("d8cfb8")[0], height=0.7, smooth=0.2)
        elif kind == "rim":
            m = ctx.rect(x0, y0, x1, y1) > 0.5
            sh.put(m & ((ctx.tx % 2) == 0), pal("c9b27a")[0], height=0.7, smooth=0.3)


def humanoid(ctx, matname, layer):
    """layer: 'outer' (helmet, chestplate, boots) or 'legs'."""
    sh = Sheet(ctx)
    mat = MATS[matname]
    surf = _surface(ctx, mat, matname)
    deco = matname in ("gold", "diamond", "netherite")
    head = sh.faces(0, 0, 8, 8, 8)
    body = sh.faces(16, 16, 8, 12, 4)
    arm = sh.faces(40, 16, 4, 12, 4)
    leg = sh.faces(0, 16, 4, 12, 4)
    if layer == "outer":
        _helmet(sh, head, mat, surf, deco)
        if matname != "turtle_scute":
            _chest(sh, body, [arm], mat, surf, deco)
            _boots(sh, [leg], mat, surf)
    else:
        _leggings(sh, [leg], body, mat, surf)
    return sh.tex(grain=0.05)


def humanoid_overlay(ctx, layer):
    sh = Sheet(ctx)
    head = sh.faces(0, 0, 8, 8, 8)
    body = sh.faces(16, 16, 8, 12, 4)
    leg = sh.faces(0, 16, 4, 12, 4)
    if layer == "outer":
        fr = head["front"]
        parts = [("rim", (fr[0], fr[1] + 2, fr[2], fr[1] + 3)),
                 ("buckle", (body["front"][0], body["front"][3] - 3, body["front"][2], body["front"][3] - 2)),
                 ("lace", (leg["front"][0] + 1, leg["front"][3] - 5, leg["front"][2] - 1, leg["front"][3] - 2))]
    else:
        bf = body["front"]
        parts = [("buckle", (bf[0], bf[3] - 5, bf[2], bf[3] - 3))]
    _overlay_leather(sh, parts)
    return sh.tex(grain=0.03)


def humanoid_baby(ctx, matname, overlay=False):
    """Baby armor. Layout is a GUESS (no CEM template for the baby armor mesh):
    it mirrors the zombie_baby template boxes, one texture for every slot."""
    sh = Sheet(ctx)
    head = sh.faces(3, 3, 6, 6, 6)
    body = sh.faces(16, 16, 4, 5, 2)
    arms = [sh.faces(28, 16, 2, 5, 2), sh.faces(36, 16, 2, 5, 2)]
    legs = [sh.faces(0, 16, 2, 4, 2), sh.faces(8, 16, 2, 4, 2)]
    if overlay:
        fr = head["front"]
        bf = body["front"]
        parts = [("rim", (fr[0], fr[1] + 1, fr[2], fr[1] + 2)),
                 ("buckle", (bf[0], bf[3] - 1, bf[2], bf[3]))]
        _overlay_leather(sh, parts)
        return sh.tex(grain=0.03)
    mat = MATS[matname]
    surf = _surface(ctx, mat, matname)
    deco = matname in ("gold", "diamond", "netherite")
    # Helmet: cap + sides, open face below the brow.
    hm = sh.rect(head["top"])
    for n in ("right", "left", "back"):
        hm |= _rows(sh, head[n], 0, 4 if n != "back" else 5)
    fr = head["front"]
    hm |= _rows(sh, fr, 0, 2) | (_cols(sh, fr, 0, 1) & _rows(sh, fr, 0, 5)) | (_cols(sh, fr, -1, 99) & _rows(sh, fr, 0, 5))
    _fill(sh, hm, mat, surf)
    _edge_shade(sh, hm, head, _outline(mat))
    if deco:
        t = head["top"]
        sh.shade(ctx.rect((t[0] + t[2]) / 2 - 0.5, t[1], (t[0] + t[2]) / 2 + 0.5, t[3]), 1.22)
    if matname != "turtle_scute":
        _chest(sh, body, arms, mat, surf, deco, arm_rows=2)
        for f in legs:
            lm = sh.rect(f["top"])
            for n in SIDES:
                lm |= _rows(sh, f[n], 0, 2)          # leggings
            bm = sh.rect(f["bottom"])
            for n in SIDES:
                bm |= _rows(sh, f[n], -2, 99)        # boots
            _fill(sh, lm | bm, mat, surf)
            _edge_shade(sh, lm, f, _outline(mat))
            _edge_shade(sh, bm, f, _outline(mat))
    return sh.tex(grain=0.05)


for _m in ("chainmail", "copper", "diamond", "gold", "iron", "leather", "netherite", "turtle_scute"):
    register(f"entity/equipment/humanoid/{_m}", (lambda m: lambda ctx: humanoid(ctx, m, "outer"))(_m))
    register(f"entity/equipment/humanoid_baby/{_m}", (lambda m: lambda ctx: humanoid_baby(ctx, m))(_m))
    if _m != "turtle_scute":
        register(f"entity/equipment/humanoid_leggings/{_m}", (lambda m: lambda ctx: humanoid(ctx, m, "legs"))(_m))
register("entity/equipment/humanoid/leather_overlay", lambda ctx: humanoid_overlay(ctx, "outer"))
register("entity/equipment/humanoid_leggings/leather_overlay", lambda ctx: humanoid_overlay(ctx, "legs"))
register("entity/equipment/humanoid_baby/leather_overlay", lambda ctx: humanoid_baby(ctx, None, overlay=True))


# ------------------------------------------------------------------ elytra

def elytra(ctx):
    sh = Sheet(ctx)
    f = sh.faces(22, 0, 10, 20, 2)
    p = pal("2c2838", "403a52", "564e6c", "6c6486", "8880a0", "a8a2bc")
    for name in ("front", "back"):
        r = f[name]
        lx, ly, W, H = sh.local(r)
        inner = (W - lx) if name == "front" else lx   # distance from the spine edge
        t = inner / W
        shape = (ly / H) < 0.5 + 0.5 * t
        shape &= ~((ly / H) > 0.93) | (t > 0.85)
        m = sh.rect(r) & shape
        vein_ang = (lx * 0.6 + ly * 0.35)
        veins = (np.floor(vein_ang) % 4 == 0) & (t > 0.15)
        v = 0.55 + (1 - ly / H) * 0.25 + ctx.texel_noise("ely") * 0.15 - veins * 0.3
        sh.put(m, ctx.palette(p[1:], np.clip(v, 0, 1)), height=0.5 + veins * -0.1, smooth=0.55, f0=0.05)
        edge = m & ~(np.roll(m, ctx.s, 0) & np.roll(m, -ctx.s, 0) & np.roll(m, ctx.s, 1) & np.roll(m, -ctx.s, 1))
        sh.put(edge, p[0], height=0.55)
        sh.shade(m & (ly < 2), 1.15)
    for name in ("top", "bottom", "right", "left"):
        r = f[name]
        sh.put(sh.rect(r), p[1], height=0.5, smooth=0.5)
    # trim the thin side strips to the wing silhouette height
    for name in ("right", "left"):
        r = f[name]
        lx, ly, W, H = sh.local(r)
        cut = sh.rect(r) & ((ly / H) > (1.0 if name == "right" else 0.5))
        sh.alpha[cut] = 0
    return sh.tex(grain=0.04)


register("entity/equipment/wings/elytra", elytra)


# ------------------------------------------------------------------ wolf armor

def wolf_armor(ctx, overlay=False):
    sh = Sheet(ctx)
    mat = MATS["armadillo_scute"]
    surf = _surface(ctx, mat, "wolf")
    body = sh.faces(18, 14, 6, 9, 6)
    mane = sh.faces(21, 0, 8, 6, 7)
    leg = sh.faces(0, 18, 2, 8, 2)
    if overlay:
        # Dyeable trim: bands across the plates (grayscale).
        m = np.zeros((ctx.H, ctx.W), bool)
        for f, rows in ((body, (0, 1)), (body, (-1, 99)), (mane, (0, 1))):
            for n in SIDES:
                m |= _rows(sh, f[n], *rows)
        for n in SIDES:
            m |= _rows(sh, leg[n], 2, 3)
        sh.put(m, gray(0.55 + ctx.texel_noise("wo") * 0.3), height=0.6, smooth=0.3)
        return sh.tex(grain=0.03)
    m = np.zeros((ctx.H, ctx.W), bool)
    for f in (body, mane):
        for n in ("top", "bottom") + SIDES:
            m |= sh.rect(f[n])
    for n in SIDES:
        m |= _rows(sh, leg[n], 0, 3)
    _fill(sh, m, mat, surf)
    _edge_shade(sh, m, body, _outline(mat))
    _edge_shade(sh, m, mane, _outline(mat))
    return sh.tex(grain=0.05)


register("entity/equipment/wolf_body/armadillo_scute", lambda ctx: wolf_armor(ctx))
register("entity/equipment/wolf_body/armadillo_scute_overlay", lambda ctx: wolf_armor(ctx, True))


# ------------------------------------------------------------------ horse armor

def horse_armor(ctx, matname, overlay=False):
    sh = Sheet(ctx)
    mat = MATS[matname]
    surf = _surface(ctx, mat, "horse" + matname)
    body = sh.faces(0, 32, 10, 10, 22)
    neck = sh.faces(0, 35, 4, 12, 7)
    head = sh.faces(0, 13, 6, 5, 7)
    mouth = sh.faces(0, 25, 4, 5, 5)
    legs = sh.faces(48, 21, 4, 11, 4)
    m = sh.rect(body["top"]) | sh.rect(body["front"]) | sh.rect(body["back"])
    m |= _rows(sh, body["right"], 0, 7) | _rows(sh, body["left"], 0, 7)
    m |= sh.rect(neck["top"]) | sh.rect(neck["right"]) | sh.rect(neck["left"]) | sh.rect(neck["front"])
    m |= sh.rect(head["top"]) | sh.rect(head["front"]) | _rows(sh, head["right"], 0, 3) | _rows(sh, head["left"], 0, 3)
    m |= sh.rect(mouth["top"]) | sh.rect(mouth["front"]) | _rows(sh, mouth["right"], 0, 2) | _rows(sh, mouth["left"], 0, 2)
    for n in SIDES:
        m |= _rows(sh, legs[n], 0, 4)
    if overlay:
        # Undyed trim: studded edges along the barding.
        trim = np.zeros((ctx.H, ctx.W), bool)
        for n in ("right", "left"):
            trim |= _rows(sh, body[n], 6, 7)
        trim |= _rows(sh, neck["front"], 0, 1)
        studs = trim & ((ctx.tx % 3) == 1)
        sh.put(trim, ctx.palette(SADDLE[1:4], ctx.texel_noise("ho")), height=0.6, smooth=0.3)
        sh.put(studs, GOLD_P[3], height=0.85, metal=GOLD, smooth=0.6)
        return sh.tex(grain=0.03)
    _fill(sh, m, mat, surf)
    for f in (body, neck, head, mouth, legs):
        _edge_shade(sh, m, f, _outline(mat))
    # Plate seams along the flanks + rivets.
    for n in ("right", "left"):
        r = body[n]
        seams = sh.rect(r) & ((np.floor(ctx.x - r[0]).astype(int) % 6) == 5) & _rows(sh, r, 0, 7)
        sh.shade(seams, 0.78)
        if mat["kind"] != "leather":
            riv = _rows(sh, r, 1, 2) & ((np.floor(ctx.x - r[0]).astype(int) % 6) == 2)
            sh.shade(riv, 1.3)
    return sh.tex(grain=0.05)


for _m in ("copper", "diamond", "gold", "iron", "leather", "netherite"):
    register(f"entity/equipment/horse_body/{_m}", (lambda m: lambda ctx: horse_armor(ctx, m))(_m))
register("entity/equipment/horse_body/leather_overlay", lambda ctx: horse_armor(ctx, "leather", True))


# ------------------------------------------------------------------ nautilus armor

def nautilus_armor(ctx, matname):
    sh = Sheet(ctx)
    mat = MATS[matname]
    surf = _surface(ctx, mat, "naut" + matname)
    shell = sh.faces(0, 0, 14, 10, 16)
    lower = sh.faces(0, 26, 14, 8, 20)
    m = np.zeros((ctx.H, ctx.W), bool)
    for n in ("top",) + SIDES:
        m |= sh.rect(shell[n])
    for n in ("right", "left"):
        m |= _rows(sh, lower[n], 0, 3)
    _fill(sh, m, mat, surf)
    _edge_shade(sh, m, shell, _outline(mat))
    _edge_shade(sh, m, lower, _outline(mat))
    # Spiral plate seams on the big side faces.
    for n in ("right", "left"):
        r = shell[n]
        lx, ly, W, H = sh.local(r)
        rr = np.hypot(lx - W / 2, (ly - H / 2) * 1.4)
        ang = np.arctan2(ly - H / 2, lx - W / 2) / (2 * np.pi)
        seam = (((rr / 3 - ang) % 1) < 0.18) & sh.rect(r)
        sh.shade(seam, 0.75)
    t = shell["top"]
    for k in range(t[1] + 2, t[3] - 1, 4):
        sh.shade(ctx.rect(t[0], k, t[2], k + 1), 0.8)
    return sh.tex(grain=0.05)


for _m in ("copper", "diamond", "gold", "iron", "netherite"):
    register(f"entity/equipment/nautilus_body/{_m}", (lambda m: lambda ctx: nautilus_armor(ctx, m))(_m))


# ------------------------------------------------------------------ saddles

def _leather(ctx, salt="sd", p=SADDLE):
    n = ctx.noise(4, 2, 0.5, salt=salt)
    return ctx.palette(p[1:], n * 0.55 + ctx.texel_noise(salt + "t") * 0.3 + 0.1), 0.55 + n * 0.1


def _strap(sh, mask, salt="st", p=SADDLE, height=0.6):
    c, h = _leather(sh.ctx, salt, p)
    sh.put(mask, c, height=height, smooth=0.3, porosity=0.3)
    edge = mask & ~(np.roll(mask, sh.ctx.s, 0) & np.roll(mask, -sh.ctx.s, 0))
    sh.shade(edge, 0.8)


def _buckle(sh, mask):
    ctx = sh.ctx
    sh.put(mask, ctx.palette(IRON_P[1:4], ctx.texel_noise("bk")), height=0.85, metal=IRON, smooth=0.6, porosity=0)


def _saddle_on(sh, top, sides, seat_rows=None, strap_w=2):
    """Seat on a top face plus girth straps down side faces.

    top: rect of the face the rider sits on; sides: list of (rect, vertical) side faces
    that the girth runs down (centered columns)."""
    ctx = sh.ctx
    x0, y0, x1, y1 = top
    W, H = x1 - x0, y1 - y0
    sx0, sx1 = x0 + max(0, W // 6), x1 - max(0, W // 6)
    sy0, sy1 = y0 + int(H * 0.25), y0 + int(H * 0.75)
    seat = ctx.rect(sx0, sy0, sx1, sy1) > 0.5
    _strap(sh, seat, "seat")
    sh.shade(ctx.rect(sx0, sy0, sx1, sy0 + 1), 1.2)
    sh.shade(ctx.rect(sx0, sy1 - 1, sx1, sy1), 0.7)
    # raised pommel / cantle
    sh.shade(ctx.rect(sx0 + 1, sy0 + 1, sx1 - 1, sy0 + 2), 1.15)
    for r in sides:
        rx0, ry0, rx1, ry1 = r
        cx = (rx0 + rx1) // 2
        st = ctx.rect(cx - strap_w // 2, ry0, cx - strap_w // 2 + strap_w, ry1) > 0.5
        _strap(sh, st, "girth")
        b = ctx.rect(cx - strap_w // 2, ry1 - 3, cx - strap_w // 2 + strap_w, ry1 - 2) > 0.5
        _buckle(sh, b)


def _equine_saddle(ctx):
    sh = Sheet(ctx)
    saddle = sh.faces(26, 0, 10, 9, 9)
    for n, r in saddle.items():
        m = sh.rect(r)
        _strap(sh, m, "saddle")
        sh.bevel(r, 1.15, 0.78)
    # seat dip on the top face, stirrup straps on the sides
    t = saddle["top"]
    sh.shade(ctx.rect(t[0] + 2, t[1] + 2, t[2] - 2, t[3] - 2), 0.88)
    for n in ("right", "left"):
        r = saddle[n]
        cx = (r[0] + r[2]) // 2
        _buckle(sh, ctx.rect(cx - 1, r[3] - 2, cx + 1, r[3]) > 0.5)
    # bit pieces
    for r in sh.faces(29, 5, 1, 2, 2).values():
        _buckle(sh, sh.rect(r))
    # reins (zero-width boxes: west/east faces at (32..48, 18..21), (48..64, 18..21))
    rein = sh.rect((32, 19, 64, 20))
    _strap(sh, rein, "rein", height=0.55)
    # headpiece + noseband: thin straps only, the rest of the box stays transparent
    hp = sh.faces(1, 1, 6, 5, 6)
    hm = np.zeros((ctx.H, ctx.W), bool)
    for n in SIDES:
        r = hp[n]
        hm |= _rows(sh, r, 1, 2)
    hm |= _cols(sh, hp["top"], 2, 4)
    for n in ("right", "left"):
        hm |= _cols(sh, hp[n], 2, 3)
    nb = sh.faces(19, 0, 4, 5, 2)
    for n in SIDES:
        hm |= _rows(sh, nb[n], 2, 3)
    _strap(sh, hm, "bridle", height=0.6)
    return sh.tex(grain=0.04)


def _pig_saddle(ctx):
    sh = Sheet(ctx)
    body = sh.faces(28, 8, 10, 16, 8)
    _saddle_on(sh, body["front"], [_rows_rect(body["right"], 4, 12), _rows_rect(body["left"], 4, 12)])
    return sh.tex(grain=0.04)


def _rows_rect(r, a, b):
    return (r[0], r[1] + a, r[2], r[1] + b)


def _strider_saddle(ctx):
    sh = Sheet(ctx)
    body = sh.faces(0, 0, 16, 14, 16)
    _saddle_on(sh, body["top"], [body["right"], body["left"]], strap_w=3)
    return sh.tex(grain=0.04)


def _nautilus_saddle(ctx):
    sh = Sheet(ctx)
    body = sh.faces(0, 0, 14, 10, 16)
    _saddle_on(sh, body["top"], [body["right"], body["left"]], strap_w=3)
    return sh.tex(grain=0.04)


def _camel_saddle(ctx, husk=False):
    sh = Sheet(ctx)
    p = SADDLE if not husk else pal("2a2418", "443a26", "5c4e32", "72623e", "88764a", "9c8a58")
    blanket_p = pal("5a1c1c", "7e2a24", "9e3a2c", "b84c34", "cc6440", "dc7e52") if not husk else \
        pal("3a3a2a", "54543c", "6a6a4c", "80805c", "96966c", "aaaa7e")
    # hump seat
    for r in sh.faces(74, 64, 9, 5, 11).values():
        _strap(sh, sh.rect(r), "hump", p)
        sh.bevel(r, 1.12, 0.8)
    for r in sh.faces(92, 114, 7, 3, 11).values():
        _strap(sh, sh.rect(r), "seat2", p)
        sh.bevel(r, 1.15, 0.78)
    # blanket over the body: top face + upper flanks, with a woven border
    body = sh.faces(0, 89, 15, 12, 27)
    t = body["top"]
    bm = ctx.rect(t[0], t[1] + 5, t[2], t[3] - 5) > 0.5
    for n in ("right", "left"):
        r = body[n]
        bm |= (ctx.rect(r[0] + 5, r[1], r[2] - 5, r[1] + 7) > 0.5)
    n_ = ctx.noise(4, 2, 0.5, salt="blk")
    stripes = (np.floor(ctx.x) % 4 < 2)
    col = ctx.palette(blanket_p[1:], n_ * 0.4 + stripes * 0.3 + ctx.texel_noise("bl") * 0.2)
    sh.put(bm, col, height=0.55, smooth=0.1, porosity=0.4)
    edge = bm & ~(np.roll(bm, ctx.s, 0) & np.roll(bm, -ctx.s, 0) & np.roll(bm, ctx.s, 1) & np.roll(bm, -ctx.s, 1))
    sh.put(edge, GOLD_P[2] if not husk else blanket_p[0], height=0.6)
    # reins (zero-width west/east faces) and bridle on the head boxes
    _strap(sh, sh.rect((98, 57, 128, 64)) & ((ctx.ty - 57) % 7 == 3), "rein", p)
    _strap(sh, sh.rect((84, 57, 98, 64)) & ((ctx.ty - 57) % 7 == 3), "rein2", p)
    hm = np.zeros((ctx.H, ctx.W), bool)
    for u, v, w, h, d in ((60, 87, 7, 8, 19), (21, 64, 7, 14, 7), (50, 64, 5, 5, 6)):
        f = sh.faces(u, v, w, h, d)
        for n in SIDES:
            hm |= _rows(sh, f[n], 1, 2)
        hm |= _cols(sh, f["top"], 1, 2) | _cols(sh, f["top"], -2, -1)
    _strap(sh, hm, "bridle", p)
    for r in sh.faces(74, 70, 1, 2, 2).values():
        _buckle(sh, sh.rect(r))
    return sh.tex(grain=0.04)


register("entity/equipment/horse_saddle/saddle", _equine_saddle)
register("entity/equipment/donkey_saddle/saddle", _equine_saddle)
register("entity/equipment/mule_saddle/saddle", _equine_saddle)
register("entity/equipment/skeleton_horse_saddle/saddle", _equine_saddle)
register("entity/equipment/zombie_horse_saddle/saddle", _equine_saddle)
register("entity/equipment/pig_saddle/saddle", _pig_saddle)
register("entity/equipment/strider_saddle/saddle", _strider_saddle)
register("entity/equipment/nautilus_saddle/saddle", _nautilus_saddle)
register("entity/equipment/camel_saddle/saddle", lambda ctx: _camel_saddle(ctx))
register("entity/equipment/camel_husk_saddle/saddle", lambda ctx: _camel_saddle(ctx, True))


# ------------------------------------------------------------------ llama carpets

TRADER = dict(base="2c4a8a", trim="e0b030", accent="c03a2a")


def _carpet_col(ctx, tone, accent, salt):
    p = ramp(tone, 5, spread=0.38)
    n = ctx.noise(4, 2, 0.5, salt=salt)
    weave = ((ctx.tx + ctx.ty) % 2 == 0)
    return ctx.palette(p, n * 0.5 + ctx.texel_noise(salt + "t") * 0.3 + weave * 0.15), p, ramp(accent, 5, 0.35)


def llama_carpet(ctx, tone, accent, trader=False):
    sh = Sheet(ctx)
    col, p, ap = _carpet_col(ctx, tone, accent, "carpet")
    body = sh.faces(29, 0, 12, 18, 10)
    back = body["front"]                       # the animal's back (body is rotated)
    m = sh.rect(back)
    # drapes: the side faces' edges next to the back face hold the blanket
    rr, ll = body["right"], body["left"]
    m |= ctx.rect(rr[2] - 6, rr[1], rr[2], rr[3]) > 0.5
    m |= ctx.rect(ll[0], ll[1], ll[0] + 6, ll[3]) > 0.5
    # chest / rear ends: rows adjacent to the back face
    for n in ("top", "bottom"):
        r = body[n]
        m |= ctx.rect(r[0], r[3] - 6, r[2], r[3]) > 0.5
    sh.put(m, col, height=0.55, smooth=0.1, porosity=0.4)
    # pattern: diamond row along the spine + fringe border
    lx, ly, W, H = sh.local(back)
    dia = (np.abs(lx - W / 2) + np.abs(((ly + 2) % 6) - 3) < 2.5) & sh.rect(back)
    sh.put(dia, ctx.palette(ap[1:4], ctx.texel_noise("dia")), height=0.6)
    border = np.zeros_like(m)
    border |= ctx.rect(rr[2] - 6, rr[1], rr[2] - 5, rr[3]) > 0.5
    border |= ctx.rect(ll[0] + 5, ll[1], ll[0] + 6, ll[3]) > 0.5
    for n in ("top", "bottom"):
        r = body[n]
        border |= ctx.rect(r[0], r[3] - 6, r[2], r[3] - 5) > 0.5
    fringe = border & (((ctx.tx + ctx.ty) % 2) == 0)
    sh.put(border, ap[3], height=0.6)
    sh.put(fringe, ap[1], height=0.55)
    # collar band on the neck
    neck = sh.faces(0, 14, 8, 18, 6)
    cm = np.zeros_like(m)
    for n in SIDES:
        cm |= _rows(sh, neck[n], 12, 15)
    sh.put(cm, col, height=0.6, smooth=0.1)
    sh.put(cm & ((ctx.tx % 3) == 0), ap[3], height=0.65)
    if trader:
        # Trader emblem: gold medallion on each drape.
        for cx, cy in ((rr[2] - 3, (rr[1] + rr[3]) / 2), (ll[0] + 3, (ll[1] + ll[3]) / 2)):
            med = ctx.circle(cx, cy, 2.2) > 0.5
            sh.put(med, ctx.palette(GOLD_P[1:4], ctx.texel_noise("med")), height=0.8, metal=GOLD, smooth=0.6)
    return sh.tex(grain=0.03)


def llama_carpet_baby(ctx):
    sh = Sheet(ctx)
    col, p, ap = _carpet_col(ctx, TRADER["base"], TRADER["trim"], "bcarpet")
    body = sh.faces(0, 15, 8, 6, 13)
    m = sh.rect(body["top"])
    for n in SIDES:
        m |= _rows(sh, body[n], 0, 3)
    sh.put(m, col, height=0.55, smooth=0.1, porosity=0.4)
    for n in SIDES:
        sh.put(_rows(sh, body[n], 2, 3), ap[3], height=0.6)
    t = body["top"]
    cx, cy = (t[0] + t[2]) / 2, (t[1] + t[3]) / 2
    sh.put(ctx.circle(cx, cy, 1.6) > 0.5, GOLD_P[3], height=0.8, metal=GOLD)
    head = sh.faces(0, 0, 6, 11, 4)
    hm = np.zeros_like(m)
    for n in SIDES:
        hm |= _rows(sh, head[n], 8, 10)
    sh.put(hm, col, height=0.6)
    return sh.tex(grain=0.03)


_LLAMA_ACCENT = {c: ("e8e2d0" if c not in ("white", "light_gray", "yellow") else "3a3a44") for c in DYE_ORDER}
for _c in DYE_ORDER:
    register(f"entity/equipment/llama_body/{_c}",
             (lambda c: lambda ctx: llama_carpet(ctx, DYES[c], _LLAMA_ACCENT[c]))(_c))
register("entity/equipment/llama_body/trader_llama",
         lambda ctx: llama_carpet(ctx, TRADER["base"], TRADER["trim"], trader=True))
register("entity/equipment/llama_body/trader_llama_baby", llama_carpet_baby)


# ------------------------------------------------------------------ happy ghast harness

def ghast_harness(ctx, color):
    sh = Sheet(ctx, k=2)
    k = 2
    p = ramp(DYES[color], 5, spread=0.4)
    f = sh.faces(0, 0, 16, 16, 16)
    m = np.zeros((ctx.H, ctx.W), bool)
    sw = 3 * k   # strap width in image texels
    for n in ("top", "bottom"):
        r = f[n]
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        m |= (ctx.rect(cx - sw / 2, r[1], cx + sw / 2, r[3]) + ctx.rect(r[0], cy - sw / 2, r[2], cy + sw / 2)) > 0
    for n in SIDES:
        r = f[n]
        cx = (r[0] + r[2]) / 2
        m |= ctx.rect(cx - sw / 2, r[1], cx + sw / 2, r[3]) > 0.5
        m |= ctx.rect(r[0], r[1] + 2 * k, r[2], r[1] + 2 * k + sw) > 0.5  # band around the top
    n_ = ctx.noise(4 * k, 2, 0.5, salt="hn")
    col = ctx.palette(p[1:], n_ * 0.5 + ctx.texel_noise("ht") * 0.3 + 0.1)
    sh.put(m, col, height=0.6, smooth=0.25, porosity=0.3)
    edge = m & ~(np.roll(m, ctx.s * k, 0) & np.roll(m, -ctx.s * k, 0) & np.roll(m, ctx.s * k, 1) & np.roll(m, -ctx.s * k, 1))
    sh.put(edge, p[0], height=0.55)
    # Seat pad on the top face.
    t = f["top"]
    cx, cy = (t[0] + t[2]) / 2, (t[1] + t[3]) / 2
    pad = ctx.rect(cx - 5 * k, cy - 4 * k, cx + 5 * k, cy + 4 * k) > 0.5
    sp = SADDLE
    sh.put(pad, ctx.palette(sp[2:], ctx.noise(3 * k, 2, salt="pad") * 0.6 + 0.2), height=0.7, smooth=0.3)
    sh.put(frame(ctx, (cx - 5 * k, cy - 4 * k, cx + 5 * k, cy + 4 * k), k) & pad, sp[1], height=0.65)
    # Buckles where straps cross the top band.
    for n in SIDES:
        r = f[n]
        cx = (r[0] + r[2]) / 2
        b = ctx.rect(cx - sw / 2, r[1] + 2 * k, cx + sw / 2, r[1] + 2 * k + sw) > 0.5
        _buckle(sh, b)
    # Goggles: strap all round + two glass lenses on the front.
    g = sh.faces(0, 32, 16, 5, 5)
    gm = np.zeros_like(m)
    for n in SIDES:
        gm |= _rows(sh, g[n], 1 * k, 4 * k)
    gm |= _rows(sh, g["top"], 2 * k, 3 * k)
    sh.put(gm, col, height=0.6, smooth=0.25)
    fr = g["front"]
    for lx0 in (fr[0] + 2 * k, fr[2] - 7 * k):
        rim = ctx.rect(lx0, fr[1], lx0 + 5 * k, fr[3]) > 0.5
        _buckle(sh, rim)
        glass = ctx.rect(lx0 + k, fr[1] + k, lx0 + 4 * k, fr[3] - k) > 0.5
        sh.put(glass, ctx.palette(pal("2a5a6a", "4a8aa0", "8ac8d8", "cff0f8"), np.clip(1 - (ctx.y - fr[1]) / (fr[3] - fr[1]), 0, 1)),
               height=0.7, smooth=0.95, f0=0.05, metal=0)
    return sh.tex(grain=0.04)


for _c in DYE_ORDER:
    register(f"entity/equipment/happy_ghast_body/{_c}_harness", (lambda c: lambda ctx: ghast_harness(ctx, c))(_c))
