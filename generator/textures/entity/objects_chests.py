"""Chests (single + double halves), ender chest, copper chests, christmas chest,
and shulker boxes (entity/shulker/*).

Chest layout (64x64, from the CEM templates chest/chest_left/chest_right.jem):
  lid    uv(0,0)  14x5x14  (doubles: 15x5x14)
  base   uv(0,19) 14x10x14 (doubles: 15x10x14)
  knob   uv(0,0)  2x4x1    (doubles: 1x4x1)
The double halves' box coordinates in the templates put the seam at -x for the
left half and +x for the right half. Side-face designs are kept vertically
symmetric so they read correctly whichever way up the game maps them; the two
horizontal cap faces are both drawn as finished wood (one slightly darker as the
interior).
Shulker layout from shulker.jem / shulker_box.jem, bullet from shulker_bullet.jem.
"""
import numpy as np

from ...engine import COPPER, GOLD, IRON, pal
from ...materials import lerp
from ...registry import register
from .objects_common import DYE_ORDER, DYES, Sheet, frame, metal_field, mottle, ramp, wood_field

WOOD = pal("3d2712", "5a3b1c", "744d26", "8a5e30", "9e6e39", "b17f44")
WOOD_FRAME = pal("24170b", "35230f", "463016", "573d1d")
IRON_P = pal("34343a", "5d5d66", "8a8a94", "b5b5bf", "dcdce4")
GOLD_P = pal("6a4a08", "a87a14", "d8a92a", "f2d054", "fff1a6")
RED_P = pal("4a0a0a", "7e1414", "aa2020", "d23a2e", "f06a50")

COPPER_STAGES = {
    "": dict(p=pal("5a2c18", "8a4528", "b05e36", "c97648", "dd9262", "eeb488"), patina=0.0),
    "_exposed": dict(p=pal("5a3a2a", "86574a", "a46e5a", "b5826c", "c49882", "d4ae98"), patina=0.25),
    "_weathered": dict(p=pal("2e4a3e", "3f6a56", "4f8a6c", "62a07e", "7cb894", "98ccaa"), patina=0.6),
    "_oxidized": dict(p=pal("1f4a44", "2c6a5e", "3b8a78", "4fa38e", "68b9a2", "8acdb8"), patina=1.0),
}
PATINA = pal("1d4a42", "2a6a5c", "3a8c78", "52a890", "78c4ac")

SEAMS = {
    None: ({}, None),
    "right": ({"top": "r", "bottom": "r", "front": "r", "back": "l"}, "left"),
    "left": ({"top": "l", "bottom": "l", "front": "l", "back": "r"}, "right"),
}


def _edges(name, seam):
    return "".join(e for e in "tblr" if e != seam.get(name, ""))


def _body(ctx, style, salt):
    """Base material (color, height, extra attrs) for the chest body."""
    if style in ("normal", "trapped"):
        c, h = wood_field(ctx, WOOD, salt=salt, along="x", board_px=5)
        return c, h, dict(smooth=0.22, porosity=0.25)
    if style == "christmas":
        p = pal("5c0e10", "861a1a", "a82424", "c23030", "d6463a")
        c, h = mottle(ctx, p, cell=6, salt=salt, grain=0.25)
        dots = ((ctx.tx * 3 + ctx.ty * 5) % 11 == 0) & ((ctx.ty % 3) == 1)
        c = np.where(dots[..., None], pal("f2ece0")[0], c)
        return c, h, dict(smooth=0.3)
    if style == "ender":
        p = pal("0b0a12", "141220", "1c1a2e", "252338", "302c46")
        c, h = mottle(ctx, p, cell=3, salt=salt, grain=0.45)
        return c, h, dict(smooth=0.55, f0=0.05)
    st = COPPER_STAGES[style]
    n = ctx.noise(6, 2, 0.5, salt=salt)
    v = 0.45 + (n - 0.5) * 0.45 + (ctx.texel_noise(salt) - 0.5) * 0.08
    seam = (np.floor(ctx.x).astype(int) % 5) == 0
    c = ctx.palette(st["p"][1:-1], np.clip(v, 0, 1))
    c = np.where(seam[..., None], c * 0.82, c)
    return c, np.where(seam, 0.4, 0.55), dict(smooth=0.6)


def _frame_col(ctx, style):
    if style in ("normal", "trapped"):
        return ctx.palette(WOOD_FRAME, ctx.texel_noise("fr") * 0.8 + 0.1)
    if style == "christmas":
        return ctx.palette(pal("1c4a1c", "26622a", "2f7a34", "3a8e40"), ctx.texel_noise("fr"))
    if style == "ender":
        return ctx.palette(pal("05050a", "0a0910", "100e18"), ctx.texel_noise("fr"))
    p = COPPER_STAGES[style]["p"]
    return ctx.palette(p[:3], ctx.texel_noise("fr"))


def _accent(style):
    """(palette, metal id) of corner caps and latch."""
    if style == "normal":
        return IRON_P, IRON
    if style == "trapped":
        return pal("2e2a2a", "4e4444", "6e6262", "938484", "b6a8a8"), IRON
    if style == "christmas":
        return GOLD_P, GOLD
    if style == "ender":
        return pal("0f3a36", "1c6a60", "2fa392", "5fd8c4", "b4fff0"), None
    return COPPER_STAGES[style]["p"][1:], COPPER if COPPER_STAGES[style]["patina"] < 0.5 else None


def chest(ctx, style="normal", half=None):
    sh = Sheet(ctx)
    seam, hidden = SEAMS[half]
    W = 14 if half is None else 15
    body_c, body_h, attrs = _body(ctx, style, "body")
    fcol = _frame_col(ctx, style)
    acc_p, acc_metal = _accent(style)
    metal_c = ctx.palette(acc_p[1:-1], ctx.noise(2, 1, salt="acc") * 0.6 + 0.2)
    is_metal_body = style.startswith("_") or style == ""

    lid = sh.faces(0, 0, W, 5, 14)
    base = sh.faces(0, 19, W, 10, 14)
    parts = [("lid", lid), ("base", base)]
    for pname, faces in parts:
        for name, r in faces.items():
            m = sh.rect(r)
            inner = (pname == "base" and name == "bottom") or (pname == "lid" and name == "top")
            sh.put(m, body_c, height=body_h, **attrs)
            if is_metal_body:
                st = COPPER_STAGES[style]
                if st["patina"] < 0.5:
                    sh.metal[m] = COPPER
                if 0 < st["patina"] < 1:
                    pat = ctx.noise(4, 2, 0.45, salt="patina") > 1.0 - st["patina"] * 0.75
                    sh.put(m & pat, ctx.palette(PATINA[1:4], ctx.noise(2, 1, salt="pc") * 0.7 + 0.15), height=0.6, smooth=0.25)
                    sh.unmetal(m & pat)
            edges = _edges(name, seam)
            fr = frame(ctx, r, 1, edges) & m
            sh.put(fr, fcol, height=0.62, smooth=attrs.get("smooth", 0.2))
            if inner:
                if pname == "base":
                    _interior(sh, r, edges, style, body_c)
                else:
                    _lid_underside(sh, r, edges, body_c)
                continue
            # Side faces: symmetric inner bevel (orientation independent).
            if name in ("right", "front", "left", "back"):
                sh.shade(ctx.rect(r[0], r[1] + 1, r[2], r[1] + 2) * (~fr), 1.06)
                sh.shade(ctx.rect(r[0], r[3] - 2, r[2], r[3] - 1) * (~fr), 1.06)
            # Corner caps on outer corners.
            cw = 2
            corners = []
            x0, y0, x1, y1 = r
            for cx, ex in ((x0, "l"), (x1 - cw, "r")):
                for cy in (y0, y1 - cw):
                    if ex in edges:
                        corners.append((cx, cy))
            if name == "top":
                corners = []
            for cx, cy in corners:
                cm = ctx.rect(cx, cy, cx + cw, cy + cw) > 0.5
                sh.put(cm, metal_c, height=0.8, smooth=0.6, metal=acc_metal)
                sh.shade(ctx.rect(cx, cy, cx + 1, cy + 1), 1.25)
                sh.shade(ctx.rect(cx + 1, cy + 1, cx + 2, cy + 2), 0.75)
            if style == "christmas" and name != "top":
                # Ribbon through the middle of each visible face.
                rib_w = 2
                if name in ("front", "back", "bottom") and half is None:
                    mx = (x0 + x1) // 2 - 1
                    rb = ctx.rect(mx, y0, mx + rib_w, y1) > 0.5
                    sh.put(rb & m, ctx.palette(pal("1f5a22", "2a7a30", "3a9a40"), ctx.texel_noise("rib")),
                           height=0.65, smooth=0.5)
                    sh.shade(ctx.rect(mx, y0, mx + 1, y1), 1.2)
                if name in ("right", "left", "bottom"):
                    my = (y0 + y1) // 2 - 1
                    rb = ctx.rect(x0, my, x1, my + rib_w) > 0.5
                    sh.put(rb & m, ctx.palette(pal("1f5a22", "2a7a30", "3a9a40"), ctx.texel_noise("rib")),
                           height=0.65, smooth=0.5)
                    sh.shade(ctx.rect(x0, my, x1, my + 1), 1.2)
            if style == "ender" and name != "top":
                # Faint glowing veins in the stone.
                vein = (np.abs(ctx.noise(5, 2, salt="vein") - 0.5) < 0.035) & m & ~fr
                sh.put(vein, pal("2a8c80")[0], height=0.45, emissive=0.35)
            if style == "trapped" and pname == "base" and name in ("right", "front", "left", "back"):
                # Red warning stripe across the middle of the base.
                my = (y0 + y1) // 2
                st_m = ctx.rect(x0, my, x1, my + 1) * (~fr) > 0.5
                sh.put(st_m, ctx.palette(RED_P[1:4], ctx.texel_noise("tr")), height=0.55, smooth=0.4)

    # Lock / latch (drawn last, it sits over the lid's unused corner).
    lock = sh.faces(0, 0, 2 if half is None else 1, 4, 1)
    lm = np.zeros((ctx.H, ctx.W), bool)
    for r in lock.values():
        lm |= sh.rect(r)
    sh.put(lm, metal_c, height=0.75, smooth=0.6, metal=acc_metal, porosity=0)
    for name, r in lock.items():
        sh.bevel(r, 1.2, 0.72)
    fr = lock["back"]
    gem = None
    if style == "trapped":
        gem = RED_P[3]
    elif style == "ender":
        gem = pal("c8fff4")[0]
    if gem is not None:
        gx = fr[0] + (0 if half else 0)
        gm = ctx.rect(gx, fr[1] + 1, gx + (2 if half is None else 1), fr[1] + 3) > 0.5
        sh.put(gm, gem, height=0.85, emissive=0.8 if style == "ender" else 0.0, smooth=0.8, metal=0)
    else:
        # Keyhole (kept centred on the latch).
        kx = fr[0] + (1 if half is None else 0)
        km = ctx.rect(kx, fr[1] + 1, kx + 1, fr[1] + 2) > 0.5
        sh.put(km, acc_p[0], height=0.3, metal=0)
    if style == "ender":
        sh.emissive[lm] = np.maximum(sh.emissive[lm], 0.25)
    if hidden:
        hm = sh.rect(lid[hidden]) | sh.rect(base[hidden])
        sh.shade(hm, 0.8)
    return sh.tex(grain=0.05)



def _interior(sh, r, edges, style, body_c):
    """Base top face seen with the lid open: hollow box interior.

    Ring 1: lit top rim of the wall thickness. Then the inner wall faces (far
    wall lit, near wall shadowed, side walls in between) and a dark floor.
    The far (hinge) side is taken as the bottom row of the region, the near
    (latch) side as the top row. Seam edges of double halves get no wall, so the
    interior runs straight across the joint.
    """
    ctx = sh.ctx
    x0, y0, x1, y1 = r
    m = sh.rect(r)
    t = 1 if "t" in edges else 0
    b = 1 if "b" in edges else 0
    lft = 1 if "l" in edges else 0
    rgt = 1 if "r" in edges else 0
    # wall depth seen from above: far wall shows more of its face than the near one
    far, near, side = 2, 1, 1
    fx0, fy0 = x0 + lft * (1 + side), y0 + t * (1 + near)
    fx1, fy1 = x1 - rgt * (1 + side), y1 - b * (1 + far)
    floor = (ctx.rect(fx0, fy0, fx1, fy1) > 0.5) & m
    rim = frame(ctx, r, 1, edges) & m
    walls = m & ~rim & ~floor
    base_col = sh.color.copy()
    # inner walls: classify by the nearest edge
    near_w = walls & (ctx.y < fy0)
    far_w = walls & (ctx.y >= fy1)
    left_w = walls & ~near_w & ~far_w & (ctx.x < fx0)
    right_w = walls & ~near_w & ~far_w & (ctx.x >= fx1)
    for mask, f in ((far_w, 0.78), (left_w, 0.62), (right_w, 0.52), (near_w, 0.38)):
        sh.color[mask] = base_col[mask] * f
        sh.height[mask] = 0.3
    # floor: dark, a little darker against the near wall (it casts the shadow)
    fl = np.where(floor, 0.34, 0.0)
    if t:
        fl = np.where(floor & (ctx.y < fy0 + 1), 0.26, fl)
    if lft:
        fl = np.where(floor & (ctx.x < fx0 + 1), np.minimum(fl, 0.3), fl)
    sh.color[floor] = base_col[floor] * fl[floor][..., None]
    sh.height[floor] = 0.05
    if style == "ender":
        sh.emissive[floor] = 0.0
    # rim: top of the wall boards, lighter than the outside
    sh.color[rim] = np.clip(body_c[rim] * 1.12, 0, 1)
    sh.height[rim] = 0.6
    sh.shade(rim & np.roll(walls, -ctx.s, 0), 0.92)   # rim edge over the far wall
    # corner posts where two rims meet stay a touch darker
    if style not in ("", "_exposed"):
        sh.unmetal(floor | walls)


def _lid_underside(sh, r, edges, body_c):
    """Lid underside seen with the lid open: rim + darker recessed panel."""
    ctx = sh.ctx
    x0, y0, x1, y1 = r
    m = sh.rect(r)
    base_col = sh.color.copy()
    rim = frame(ctx, r, 1, edges) & m
    sh.color[rim] = np.clip(body_c[rim] * 1.05, 0, 1)
    sh.height[rim] = 0.6
    px0 = x0 + (1 if "l" in edges else 0)
    py0 = y0 + (1 if "t" in edges else 0)
    px1 = x1 - (1 if "r" in edges else 0)
    py1 = y1 - (1 if "b" in edges else 0)
    panel = (ctx.rect(px0, py0, px1, py1) > 0.5) & m
    sh.color[panel] = body_c[panel] * 0.6
    sh.height[panel] = 0.3
    # recessed: inner edge below the rim on the top/left is in shadow, bottom/right catches light
    if "t" in edges:
        sh.shade(panel & (ctx.y < py0 + 1), 0.78)
    if "l" in edges:
        sh.shade(panel & (ctx.x < px0 + 1) & ~(ctx.y < py0 + 1), 0.82)
    if "b" in edges:
        sh.shade(panel & (ctx.y >= py1 - 1), 1.15)
    if "r" in edges:
        sh.shade(panel & (ctx.x >= px1 - 1) & ~(ctx.y >= py1 - 1), 1.1)


def _bind(style, half):
    return lambda ctx: chest(ctx, style, half)


for _name, _style in (("normal", "normal"), ("trapped", "trapped"), ("christmas", "christmas")):
    register(f"entity/chest/{_name}", _bind(_style, None))
    register(f"entity/chest/{_name}_left", _bind(_style, "left"))
    register(f"entity/chest/{_name}_right", _bind(_style, "right"))
register("entity/chest/ender", _bind("ender", None))
for _sfx in COPPER_STAGES:
    register(f"entity/chest/copper{_sfx}", _bind(_sfx, None))
    register(f"entity/chest/copper{_sfx}_left", _bind(_sfx, "left"))
    register(f"entity/chest/copper{_sfx}_right", _bind(_sfx, "right"))


# ------------------------------------------------------------------ shulker boxes
# Shulker layout (64x64): lid uv(0,0) 16x12x16, base uv(0,28) 16x8x16, head uv(0,52) 6x6x6.

SHULKER_DEFAULT = "8e5f8e"
SHULKER_TONES = dict(DYES, white="dcdcd6", black="2a2a30", gray="54585c", light_gray="9a9a94",
                     brown="7a4e2e", green="5e7a24", blue="3c44a8", purple="7e3cb0", red="aa3030")


def shulker(ctx, tone):
    sh = Sheet(ctx)
    p = ramp(tone, 6, spread=0.5)
    shell_v = ctx.noise(5, 2, 0.5, salt="shell")
    lid = sh.faces(0, 0, 16, 12, 16)
    base = sh.faces(0, 28, 16, 8, 16)
    for faces, part in ((lid, "lid"), (base, "base")):
        for name, r in faces.items():
            m = sh.rect(r)
            lx, ly, w, h = sh.local(r)
            v = shell_v * 0.35 + ctx.texel_noise("sg") * 0.08 + 0.35
            col = ctx.palette(p[1:], v)
            height = 0.5 + shell_v * 0.1
            sh.put(m, col, height=height, smooth=0.45, f0=0.05)
            if name in ("top", "bottom"):
                # Concentric plate on the cap.
                ring = frame(ctx, (r[0] + 3, r[1] + 3, r[2] - 3, r[3] - 3), 1) & m
                sh.put(ring, p[1], height=0.35)
                inner = ctx.rect(r[0] + 4, r[1] + 4, r[2] - 4, r[3] - 4) > 0.5
                sh.shade(inner, 1.08)
                sh.bevel(r, 1.15, 0.8)
                if part == "base" and name == "bottom":
                    sh.shade(m, 0.55)  # inside of the box
                continue
            # Side faces: vertical ribs, rim band at the open edge.
            rib = ((np.floor(lx).astype(int) % 4) == 0) & m
            sh.put(rib, p[1], height=0.4)
            sh.shade(((np.floor(lx).astype(int) % 4) == 1) & m, 1.1)
            if part == "lid":
                band = (ly >= h - 3) & m
                sh.put(band, ctx.palette(p[:4], ctx.texel_noise("band") * 0.5 + 0.4), height=0.6)
                sh.shade(band & (ly < h - 2), 1.15)
                sh.shade(band & (ly >= h - 1), 0.75)
                sh.shade((ly < 1) & m, 1.15)
            else:
                band = (ly < 2) & m
                sh.put(band, ctx.palette(p[:4], ctx.texel_noise("band") * 0.5 + 0.4), height=0.6)
                sh.shade((ly >= h - 1) & m, 0.7)
    # Head (the creature inside): soft, pale, slightly glowing.
    head = sh.faces(0, 52, 6, 6, 6)
    hp = pal("8a8a5a", "b4b47a", "d2d296", "e6e6b0", "f4f4cc")
    for name, r in head.items():
        m = sh.rect(r)
        sh.put(m, ctx.palette(hp, ctx.noise(2, 1, salt="hd") * 0.6 + 0.2), height=0.55, sss=0.5, smooth=0.3)
        sh.bevel(r, 1.08, 0.85)
    fr = head["front"]
    eyes = (ctx.rect(fr[0] + 1, fr[1] + 2, fr[0] + 2, fr[1] + 4) + ctx.rect(fr[0] + 4, fr[1] + 2, fr[0] + 5, fr[1] + 4)) > 0
    sh.put(eyes, pal("1c1c24")[0], height=0.3, sss=0)
    mouth = ctx.rect(fr[0] + 2, fr[1] + 5, fr[0] + 4, fr[1] + 6) > 0.5
    sh.put(mouth, hp[0], height=0.4)
    return sh.tex(grain=0.05)


register("entity/shulker/shulker", lambda ctx: shulker(ctx, SHULKER_DEFAULT))
for _c in DYE_ORDER:
    register(f"entity/shulker/shulker_{_c}", (lambda c: lambda ctx: shulker(ctx, SHULKER_TONES[c]))(_c))


def spark(ctx):
    """Shulker bullet (64x32): boxes (0,0) 8x8x2, (0,10) 2x8x8, (20,0) 8x2x8."""
    sh = Sheet(ctx)
    p = pal("8a6a1a", "c8a032", "f0d060", "fff0a0", "fffbe0")
    for u, v, w, h, d in ((0, 0, 8, 8, 2), (0, 10, 2, 8, 8), (20, 0, 8, 2, 8)):
        for name, r in sh.faces(u, v, w, h, d).items():
            m = sh.rect(r)
            lx, ly, fw, fh = sh.local(r)
            dist = np.maximum(np.abs(lx - fw / 2) / max(fw, 1), np.abs(ly - fh / 2) / max(fh, 1))
            val = 1 - dist * 1.6 + ctx.texel_noise("sp") * 0.25
            sh.put(m, ctx.palette(p, np.clip(val, 0, 1)), height=0.6, emissive=0.7, smooth=0.6)
            sh.put(frame(ctx, r, 1) & m, p[1], height=0.5, emissive=0.4)
    return sh.tex(grain=0.02)


register("entity/shulker/spark", spark)
