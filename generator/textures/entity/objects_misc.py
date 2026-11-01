"""Small object entities: armor stand, bell, book, minecart, lead knot, end crystal,
beams, end portal, experience orb, fishing hook, projectiles, trident, conduit, cushions.

Layouts (model texels) from the OptiFine CEM template .jem files in
github.com/ewanhowell5195/cemTemplateModels (armor_stand, bell, enchanting_book,
minecart, lead_knot, end_crystal, arrow, trident, trident_riptide, wind_charge,
conduit). The cushion has no template: its layout is a best guess.
  armor stand 64x64: head (0,0) 2x7x2, right leg (8,0) 2x11x2, right stick (16,0) 2x7x2,
      right arm (24,0) 2x12x2, body (0,26) 12x3x3, left arm (32,16) 2x12x2, left leg (40,16) 2x11x2,
      left stick (48,16) 2x7x2, shoulder stick (0,48) 8x2x2, base plate (0,32) 12x1x12
  bell 32x32: body (0,0) 6x7x6, lip (0,13) 8x2x8
  book 64x32: lids (0,0)/(16,0) 6x10x0, seam (12,0) 2x10x0, pages (0,10)/(12,10) 5x8x1, flip page (24,10) 5x8x0
  minecart 64x32: sides (0,0) 16x8x2, floor (0,10) 20x16x2
  lead knot 32x32: (0,0) 6x8x6
  end crystal: model 64x32 on a 128x64 image (k=2): glass (0,0) 8^3, core (32,0) 8^3, base (0,16) 12x4x12
  arrow 32x32: shaft cross (0,0) 16x5 (nock end left, head right), nock cross (0,5) 5x5
  trident 32x32: pole (0,6) 1x25x1, base (4,0) 3x2x1, side spikes (4,3) 1x4x1, middle spike (0,0) 1x4x1
  riptide 64x64: (0,0) 16x31x16;  wind charge 64x32: core (0,0) 4^3, (0,9) 6x4x6, (15,20) 8x2x8
  conduit: shell 32x16 (0,0) 6^3, cage 32x16 (0,0) 8^3, eye 16x16 (0,0) 8x8x0, wind 64x32 (0,0) 16^3
  cushion 64x64: (0,0) 16x4x16  (GUESS - no CEM template available)
"""
import math

import numpy as np

from ...engine import GOLD, IRON, Tex, pal, smoothstep
from ...materials import lerp
from ...registry import register
from ...sprites import blank, sprite
from .objects_common import DYE_ORDER, DYES, Sheet, frame, gray, metal_field, mottle, ramp, wood_field

IRON_P = pal("34343a", "5d5d66", "8a8a94", "b5b5bf", "dcdce4")
GOLD_P = pal("6a4a08", "a87a14", "d8a92a", "f2d054", "fff1a6")
WOOD = pal("3d2712", "5a3b1c", "744d26", "8a5e30", "9e6e39", "b17f44")
STONE = pal("4a4a4e", "626266", "7a7a7e", "929296", "a8a8ac", "bcbcc0")
OBSIDIAN = pal("08060e", "120e1c", "1c162a", "261e38", "322848", "40345a")
PRISMARINE = pal("1a4a46", "2a6a62", "3c8a80", "52a89a", "72c2b2", "a0dccc")


def _box_paint(sh, faces, col, h=0.5, bevel=True, **kw):
    for r in faces.values():
        if r[2] <= r[0] or r[3] <= r[1]:
            continue
        sh.put(sh.rect(r), col, height=h, **kw)
        if bevel:
            sh.bevel(r, 1.12, 0.8)


# ------------------------------------------------------------------ armor stand

def armorstand(ctx):
    sh = Sheet(ctx)
    c, h = wood_field(ctx, WOOD, salt="as", along="y", board_px=99, seam=False)
    for u, v, w, hh, d in ((0, 0, 2, 7, 2), (8, 0, 2, 11, 2), (16, 0, 2, 7, 2), (24, 0, 2, 12, 2),
                           (0, 26, 12, 3, 3), (32, 16, 2, 12, 2), (40, 16, 2, 11, 2), (48, 16, 2, 7, 2),
                           (0, 48, 8, 2, 2)):
        _box_paint(sh, sh.faces(u, v, w, hh, d), c, h, smooth=0.3, porosity=0.2)
    # Shoulder bar: darker with iron caps.
    body = sh.faces(0, 26, 12, 3, 3)
    for n in ("front", "back"):
        r = body[n]
        for ex in (r[0], r[2] - 1):
            sh.put(ctx.rect(ex, r[1], ex + 1, r[3]) > 0.5, IRON_P[2], height=0.7, metal=IRON, smooth=0.6)
    sc, shh = mottle(ctx, STONE, cell=4, salt="plate", grain=0.3)
    plate = sh.faces(0, 32, 12, 1, 12)
    for n, r in plate.items():
        sh.put(sh.rect(r), sc, height=shh, smooth=0.25)
        if n in ("top", "bottom"):
            sh.put(frame(ctx, r, 1) & sh.rect(r), STONE[1], height=0.6)
            sh.shade(frame(ctx, (r[0] + 1, r[1] + 1, r[2] - 1, r[3] - 1), 1, "tl") & sh.rect(r), 1.12)
    return sh.tex(grain=0.04)


# ------------------------------------------------------------------ bell

def bell(ctx):
    sh = Sheet(ctx)
    body = sh.faces(0, 0, 6, 7, 6)
    lip = sh.faces(0, 13, 8, 2, 8)
    c, h = metal_field(ctx, GOLD_P, salt="bell", stretch=(1, 3))
    for n, r in body.items():
        m = sh.rect(r)
        lx, ly, W, H = sh.local(r)
        sh.put(m, c, height=h, metal=GOLD, smooth=0.75)
        if n not in ("top", "bottom"):
            sh.shade(m & (lx < 1), 1.2)
            sh.shade(m & (lx >= W - 1), 0.75)
            sh.put(m & (np.floor(ly) == 2), GOLD_P[1], height=0.4)   # engraved ring
            sh.put(m & (np.floor(ly) == 5) & ((np.floor(lx) % 2) == 0), GOLD_P[1], height=0.4)
    for n, r in lip.items():
        m = sh.rect(r)
        sh.put(m, c * 0.92, height=h, metal=GOLD, smooth=0.75)
        sh.bevel(r, 1.2, 0.72)
        if n == "bottom":
            inner = ctx.rect(r[0] + 1, r[1] + 1, r[2] - 1, r[3] - 1) > 0.5
            sh.put(inner, GOLD_P[0], height=0.2)
    return sh.tex(grain=0.04)


# ------------------------------------------------------------------ book

def book(ctx):
    sh = Sheet(ctx)
    cover = pal("3a1210", "5a1c18", "7a2820", "963428", "aa4232")
    cn = ctx.noise(3, 2, 0.5, salt="cov")
    ccol = ctx.palette(cover[1:], cn * 0.5 + ctx.texel_noise("cv") * 0.3 + 0.1)
    for r in ((0, 0, 6, 10), (6, 0, 12, 10), (16, 0, 22, 10), (22, 0, 28, 10)):
        m = sh.rect(r)
        sh.put(m, ccol, height=0.55, smooth=0.3, porosity=0.2)
        sh.put(frame(ctx, r, 1) & m, cover[0], height=0.5)
        # gilded corner ornaments and a central rune
        x0, y0, x1, y1 = r
        orn = (ctx.rect(x0 + 1, y0 + 1, x0 + 2, y0 + 2) + ctx.rect(x1 - 2, y0 + 1, x1 - 1, y0 + 2) +
               ctx.rect(x0 + 1, y1 - 2, x0 + 2, y1 - 1) + ctx.rect(x1 - 2, y1 - 2, x1 - 1, y1 - 1)) > 0
        sh.put(orn, GOLD_P[3], height=0.75, metal=GOLD, smooth=0.6)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rune = ((ctx.rect(cx - 1, cy - 2, cx + 1, cy + 2) + ctx.rect(cx - 2, cy - 1, cx + 2, cy + 1)) > 0) & \
            ~(ctx.rect(cx - 1, cy - 1, cx + 1, cy + 1) > 0.5)
        sh.put(rune, GOLD_P[2], height=0.7, metal=GOLD, smooth=0.6)
    seam = (12, 0, 16, 10)
    sh.put(sh.rect(seam), cover[1], height=0.5)
    sh.put(sh.rect(seam) & ((np.floor(ctx.y) % 3) == 1), GOLD_P[2], height=0.7, metal=GOLD)
    paper = pal("8a7a5a", "c8b894", "dccca8", "eadcbc", "f4ead0")
    for u in (0, 12):
        f = sh.faces(u, 10, 5, 8, 1)
        for n, r in f.items():
            m = sh.rect(r)
            if n in ("front", "back"):
                lx, ly, W, H = sh.local(r)
                sh.put(m, paper[3], height=0.5, smooth=0.1)
                lines = m & (np.floor(ly) % 2 == 1) & (lx >= 1) & (lx < W - 1) & (ly >= 1) & (ly < H - 1)
                lines &= ctx.texel_noise("txt" + str(u), soft=False) > 0.25
                sh.put(lines, paper[1], height=0.45)
            else:
                lx, ly, W, H = sh.local(r)
                sh.put(m, np.where(((np.floor(lx + ly) % 2) == 0)[..., None], paper[2], paper[3]), height=0.5)
    flip = (24, 10, 34, 18)
    m = sh.rect(flip)
    lx, ly, W, H = sh.local(flip)
    sh.put(m, paper[3], height=0.5, smooth=0.1)
    glyph = m & (np.floor(ly) % 2 == 1) & ((lx % 5) >= 1) & ((lx % 5) < 4) & (ly >= 1) & (ly < H - 1)
    glyph &= ctx.texel_noise("glyph", soft=False) > 0.3
    sh.put(glyph, pal("5a3aa0")[0], height=0.45, emissive=0.2)
    return sh.tex(grain=0.03)


# ------------------------------------------------------------------ minecart

def minecart(ctx):
    sh = Sheet(ctx)
    c, h = metal_field(ctx, IRON_P, salt="cart", stretch=(4, 1))
    for faces in (sh.faces(0, 0, 16, 8, 2), sh.faces(0, 10, 20, 16, 2)):
        for n, r in faces.items():
            m = sh.rect(r)
            sh.put(m, c, height=h, metal=IRON, smooth=0.55)
            if r[2] - r[0] >= 8 and r[3] - r[1] >= 6:
                sh.put(frame(ctx, r, 1) & m, IRON_P[1], height=0.6)
                sh.shade(frame(ctx, (r[0] + 1, r[1] + 1, r[2] - 1, r[3] - 1), 1, "tl") & m, 1.15)
                sh.shade(frame(ctx, (r[0] + 1, r[1] + 1, r[2] - 1, r[3] - 1), 1, "br") & m, 0.85)
                # rivets at the corners and centre line
                for rx in (r[0] + 2, r[2] - 3, (r[0] + r[2]) // 2):
                    for ry in (r[1] + 2, r[3] - 3):
                        sh.put(ctx.rect(rx, ry, rx + 1, ry + 1) > 0.5, IRON_P[4], height=0.85)
                if r[3] - r[1] >= 12:
                    # floor: rust streaks + plank seams
                    seams = m & ((np.floor(ctx.y - r[1]).astype(int) % 4) == 3) & ~frame(ctx, r, 1)
                    sh.shade(seams, 0.78)
                    rust = m & (ctx.noise(3, 2, salt="rust") > 0.72)
                    sh.tint(rust, pal("7a4a2a")[0], 0.45)
                    sh.unmetal(rust)
            else:
                sh.bevel(r, 1.15, 0.78)
    return sh.tex(grain=0.05)


# ------------------------------------------------------------------ lead knot

def lead_knot(ctx):
    sh = Sheet(ctx)
    p = pal("4a3a26", "6e5838", "8e7650", "ac9468", "c8b086")
    f = sh.faces(0, 0, 6, 8, 6)
    for n, r in f.items():
        m = sh.rect(r)
        lx, ly, W, H = sh.local(r)
        twist = ((np.floor(lx + ly) % 3) == 0)
        v = 0.6 - twist * 0.35 + ctx.texel_noise("rope") * 0.2
        sh.put(m, ctx.palette(p, np.clip(v, 0, 1)), height=0.55 - twist * 0.15, smooth=0.1, porosity=0.4)
        if n in ("right", "front", "left", "back"):
            band = m & ((np.floor(ly) == 2) | (np.floor(ly) == 5))
            sh.put(band, p[1], height=0.45)
    return sh.tex(grain=0.04)


# ------------------------------------------------------------------ end crystal & beams

def end_crystal(ctx):
    sh = Sheet(ctx, k=2)
    k = 2
    # Outer glass frame: translucent pale violet with a bright edge.
    for n, r in sh.faces(0, 0, 8, 8, 8).items():
        m = sh.rect(r)
        lx, ly, W, H = sh.local(r)
        edge = frame(ctx, r, k) & m
        streak = m & (np.abs((lx - ly) % (W / 2) - 2) < 1.2)
        sh.put(m, pal("d8c8f0")[0], alpha=0.35, height=0.5, smooth=0.95, f0=0.04)
        sh.put(streak, pal("f4eeff")[0], alpha=0.55, height=0.5, smooth=0.95)
        sh.put(edge, pal("b8a0e0")[0], alpha=0.85, height=0.6, smooth=0.9, emissive=0.3)
    # Core: glowing magenta/violet crystal, emissive.
    for n, r in sh.faces(32, 0, 8, 8, 8).items():
        m = sh.rect(r)
        lx, ly, W, H = sh.local(r)
        d = np.maximum(np.abs(lx - W / 2), np.abs(ly - H / 2)) / (W / 2)
        facet = np.clip(-(lx - W / 2 + ly - H / 2) / W + 0.5, 0, 1)
        p = pal("4a1450", "7a2a8a", "a848c0", "d07ae0", "f0b8f8", "fff0ff")
        v = np.clip(1 - d * 0.7 + facet * 0.25 + ctx.texel_noise("core") * 0.1 - 0.15, 0, 1)
        sh.put(m, ctx.palette(p, v), height=0.5 + (1 - d) * 0.3, emissive=0.5 + v * 0.5, smooth=0.85, f0=0.17)
    # Base: bedrock-like dark stone.
    bc, bh = mottle(ctx, pal("16141a", "222028", "2e2c36", "3a3844", "484652", "585664"), cell=4, salt="base", grain=0.5)
    for n, r in sh.faces(0, 16, 12, 4, 12).items():
        m = sh.rect(r)
        sh.put(m, bc, height=bh, smooth=0.3)
        sh.bevel(r, 1.15, 0.78, width=k)
        if n == "top":
            ring = frame(ctx, (r[0] + 3 * k, r[1] + 3 * k, r[2] - 3 * k, r[3] - 3 * k), k) & m
            sh.put(ring, pal("6a4a8a")[0], height=0.4, emissive=0.4)
    return sh.tex(grain=0.03)


def end_crystal_beam(ctx):
    """Beam strip (16 wide, tiles vertically): pale core with drifting bands."""
    x = ctx.x
    core = 1 - np.abs(x - ctx.w / 2) / (ctx.w / 2)
    n = ctx.noise(8, 3, 0.5, salt="ecb", stretch=(1, 6))
    bands = 0.5 + 0.5 * np.sin(ctx.y / ctx.h * 2 * math.pi * 6 + n * 4)
    v = np.clip(core * 0.7 + bands * 0.3, 0, 1)
    col = lerp(pal("5a2a7a")[0], pal("f8eaff")[0], v)
    a = np.clip(0.25 + core * 0.75 * (0.6 + bands * 0.4), 0, 1)
    return Tex(ctx, col, alpha=a, height=0.5, emissive=0.6 + v * 0.4, smooth=0.9, wrap=True, grain=0)


def beam(ctx, kind):
    """Beacon / end gateway beam (16x16, scrolls vertically, tinted by the game)."""
    st = ctx.lattice_noise(2, ctx.h, f"beam{kind}")
    fl = ctx.noise(4, 2, 0.5, salt=f"bf{kind}", stretch=(0.5, 4))
    v = np.clip(0.55 + st * 0.3 + (fl - 0.5) * 0.3, 0, 1)
    v = ctx.quantize(v, 6)
    col = gray(0.55 + v * 0.45)
    if kind == "gateway":
        col = lerp(pal("6a4a9a")[0], pal("f0e8ff")[0], v)
    return Tex(ctx, col, alpha=1.0, height=0.5, emissive=0.9, smooth=0.8, wrap=True, grain=0)


def end_portal(ctx):
    """Star field layer used by the end portal shader: sparse specks on black."""
    rng = ctx.rng("stars")
    col = np.zeros((ctx.H, ctx.W, 3), np.float32)
    em = ctx.zeros()
    n = ctx.noise(48, 3, 0.55, salt="nebula")
    neb = np.clip((n - 0.55) * 2.0, 0, 1) * 0.18
    col += neb[..., None] * pal("4a7a6a")[0]
    S = ctx.s
    for i in range(420):
        x, y = rng.uniform(0, ctx.w), rng.uniform(0, ctx.h)
        size = rng.choice([0.6, 0.6, 0.6, 1.0, 1.0, 1.6])
        hue = pal(["b8e8d0", "d0f0e8", "8ad0b8", "f0fff8", "a8c8f0"][rng.integers(0, 5)])[0]
        bright = rng.uniform(0.45, 1.0)
        x0, x1 = max(0, int((x - 3) * S)), min(ctx.W, int((x + 3) * S) + 1)
        y0, y1 = max(0, int((y - 3) * S)), min(ctx.H, int((y + 3) * S) + 1)
        lx, ly = ctx.x[y0:y1, x0:x1], ctx.y[y0:y1, x0:x1]
        m = (np.hypot(lx - x, ly - y) < size).astype(np.float32)
        if size >= 1.6:
            cross = (((np.abs(lx - x) < 2.5) & (np.abs(ly - y) < 0.5)) | ((np.abs(lx - x) < 0.5) & (np.abs(ly - y) < 2.5)))
            m = np.maximum(m, cross * 0.6)
        col[y0:y1, x0:x1] = np.maximum(col[y0:y1, x0:x1], m[..., None] * hue * bright)
        em[y0:y1, x0:x1] = np.maximum(em[y0:y1, x0:x1], m * bright)
    return Tex(ctx, np.clip(col, 0, 1), alpha=1.0, height=0.5, emissive=em, smooth=0.0, wrap=True, grain=0)


# ------------------------------------------------------------------ experience orb

def experience_orb(ctx):
    """4x4 grid of 16x16 orb sprites, size grows with the index (0..10 used)."""
    out = blank(ctx)
    p = pal("3a5a08", "6a9a10", "a8d020", "d8f040", "f6ff9a", "ffffe0")
    for i in range(16):
        ox, oy = (i % 4) * 16, (i // 4) * 16
        r = 1.6 + min(i, 10) * 0.42
        cx, cy = ox + 8, oy + 8
        body = ctx.circle(cx, cy, r)
        if i >= 4:
            # chunky faceted orbs get small lobes
            for a in range(4):
                ang = a * math.pi / 2 + i
                body = np.maximum(body, ctx.circle(cx + math.cos(ang) * r * 0.6, cy + math.sin(ang) * r * 0.6, r * 0.55))
        spr = sprite(ctx, body, p, bevel=max(1.0, r * 0.6), light=0.35, emissive=0.9, smooth=0.6)
        hl = ctx.circle(cx - r * 0.35, cy - r * 0.35, max(0.6, r * 0.22)) * body
        spr.color = np.where((hl > 0.5)[..., None], p[-1], spr.color)
        out.paste(spr)
    return out


# ------------------------------------------------------------------ fishing hook

def fishing_hook(ctx):
    out = blank(ctx)
    red = pal("5a0a0a", "a01818", "d43a2a", "f06a50")
    white = pal("8a8a8a", "d8d8d8", "f2f2f2", "ffffff")
    top = ctx.circle(4, 3, 2.6) * (ctx.y < 3.5)
    bot = ctx.circle(4, 3, 2.6) * (ctx.y >= 3.5)
    out.paste(sprite(ctx, top, red, bevel=1.5))
    out.paste(sprite(ctx, bot, white, bevel=1.5))
    hook = np.maximum(ctx.rect(3.5, 5.5, 4.5, 7.5), ctx.rect(4.5, 6.5, 5.5, 7.5))
    hook = np.maximum(hook, ctx.rect(5.5, 5.5, 6.5, 6.5))
    out.paste(sprite(ctx, hook, IRON_P, outline=False, bevel=1, metal=IRON))
    stem = ctx.rect(3.5, 0, 4.5, 1)
    out.paste(sprite(ctx, stem, white, outline=False, bevel=1))
    return out


# ------------------------------------------------------------------ projectiles

def arrow(ctx, kind):
    sh = Sheet(ctx)
    shaft = pal("3a2814", "5a4024", "7a5a34", "967448")
    if kind == "spectral":
        shaft = pal("6a4a08", "a87a14", "d8a92a", "f2d054")
    head_p = IRON_P if kind != "spectral" else GOLD_P
    feather = pal("8a8a8a", "c8c8c8", "e8e8e8", "ffffff")
    if kind == "tipped":
        head_p = pal("3a2a4a", "5a3a7a", "8a5aa8", "b88ad0", "e0c8f0")
    # Side cross 16x5: nock/fletching at the left, head at the right.
    y0 = 0
    cy = 2
    rod = ctx.rect(2, cy, 13, cy + 1) > 0.5
    sh.put(rod, ctx.palette(shaft[1:], ctx.texel_noise("shaft") * 0.6 + 0.2), height=0.55, smooth=0.3)
    sh.put(ctx.rect(2, cy, 13, cy + 1) * (ctx.tx % 3 == 0) > 0.5, shaft[1], height=0.5)
    fl = ((ctx.rect(0, 0, 5, 2) * (ctx.x - ctx.y > -0.5)) + (ctx.rect(0, 3, 5, 5) * (ctx.x + ctx.y > 4.5))) > 0
    fl &= ctx.rect(0, 0, 6, 5) > 0.5
    sh.put(fl, np.where(((ctx.tx % 2) == 0)[..., None], feather[2], feather[1]), height=0.55)
    sh.put(ctx.rect(0, cy, 2, cy + 1) > 0.5, feather[0], height=0.5)
    head = ctx.polygon([(12, 0.5), (16, 2.5), (12, 4.5)]) > 0.5
    sh.put(head, ctx.palette(head_p[1:], ctx.x / 16), height=0.7, metal=IRON if kind == "normal" else (GOLD if kind == "spectral" else None), smooth=0.6)
    sh.put(head & (ctx.ty == 2) & (ctx.tx >= 12), head_p[-1], height=0.75)
    sh.put(head & ((ctx.ty == 0) | (ctx.ty == 4) | (ctx.tx == 12)), head_p[1], height=0.65)
    if kind == "spectral":
        sh.emissive[sh.alpha > 0.5] = 0.6
    # Nock cross 5x5 at (0,5): feathers seen from behind.
    nock = (ctx.rect(2, 5, 3, 10) + ctx.rect(0, 7, 5, 8)) > 0
    sh.put(nock, feather[2], height=0.55)
    sh.put(ctx.rect(2, 7, 3, 8) > 0.5, shaft[1], height=0.5)
    return sh.tex(grain=0.02)


def wind_charge(ctx):
    sh = Sheet(ctx)
    p = pal("8aa8c8", "a8c4e0", "c4dcf0", "dcecf8", "f4faff")
    for u, v, w, h, d, a in ((15, 20, 8, 2, 8, 0.55), (0, 9, 6, 4, 6, 0.7), (0, 0, 4, 4, 4, 0.95)):
        for n, r in sh.faces(u, v, w, h, d).items():
            m = sh.rect(r)
            lx, ly, W, H = sh.local(r)
            swirl = ((np.floor(lx + ly * 0.7) % 3) == 0)
            val = np.clip(0.55 + swirl * 0.35 + ctx.texel_noise("wc") * 0.15, 0, 1)
            alpha = np.where(swirl, min(1.0, a + 0.3), a * 0.6)
            sh.put(m, ctx.palette(p, val), alpha=alpha, height=0.5, smooth=0.6, emissive=0.15)
    return sh.tex(grain=0.02)


# ------------------------------------------------------------------ trident

def trident(ctx):
    sh = Sheet(ctx)
    p = PRISMARINE
    pole = sh.faces(0, 6, 1, 25, 1)
    for n, r in pole.items():
        m = sh.rect(r)
        lx, ly, W, H = sh.local(r)
        v = 0.5 + ctx.texel_noise("pole") * 0.25 - ((np.floor(ly) % 6) == 5) * 0.35
        sh.put(m, ctx.palette(p[1:], np.clip(v, 0, 1)), height=0.55, smooth=0.6, f0=0.06)
        sh.put(m & (ly >= H - 3), ctx.palette(pal("2a4a4a", "3a6a68", "4a8a86"), ctx.texel_noise("grip")), height=0.6)
    for u, v, w, h, d in ((4, 0, 3, 2, 1), (4, 3, 1, 4, 1), (0, 0, 1, 4, 1)):
        for n, r in sh.faces(u, v, w, h, d).items():
            m = sh.rect(r)
            lx, ly, W, H = sh.local(r)
            sh.put(m, ctx.palette(p[2:], np.clip(1 - ly / max(H, 1) * 0.6 + ctx.texel_noise("tip") * 0.2, 0, 1)),
                   height=0.6, smooth=0.75, f0=0.08)
    return sh.tex(grain=0.03)


def riptide(ctx):
    sh = Sheet(ctx)
    for n, r in sh.faces(0, 0, 16, 31, 16).items():
        m = sh.rect(r)
        lx, ly, W, H = sh.local(r)
        band = ((ly + lx * 0.5) % 8) < 3
        fade = 1 - np.abs(ly - H / 2) / (H / 2) if n not in ("top", "bottom") else 0.3
        a = np.where(band, 0.75, 0.0) * np.clip(fade + 0.2, 0, 1)
        sh.put(m & band, pal("e8f6ff")[0], alpha=a, height=0.5, smooth=0.8, emissive=0.2)
    return sh.tex(grain=0.0)


# ------------------------------------------------------------------ conduit

def conduit_shell(ctx):
    sh = Sheet(ctx)
    p = pal("4a3a2a", "6e5a42", "8e7656", "aa9070", "c4aa88", "dcc4a2")
    for n, r in sh.faces(0, 0, 6, 6, 6).items():
        m = sh.rect(r)
        lx, ly, W, H = sh.local(r)
        rr = np.hypot(lx - W, ly - H)
        ridge = (np.floor(rr) % 2 == 0)
        v = 0.5 + ridge * 0.2 + ctx.texel_noise("shell") * 0.2
        sh.put(m, ctx.palette(p[1:], np.clip(v, 0, 1)), height=0.5 + ridge * 0.1, smooth=0.5)
        sh.bevel(r, 1.15, 0.75)
    return sh.tex(grain=0.03)


def conduit_cage(ctx):
    sh = Sheet(ctx)
    p = PRISMARINE
    for n, r in sh.faces(0, 0, 8, 8, 8).items():
        lx, ly, W, H = sh.local(r)
        bars = sh.rect(r) & ((lx < 1) | (lx >= W - 1) | (ly < 1) | (ly >= H - 1) |
                             ((np.abs(lx - W / 2 + 0.5) < 0.6) & (np.abs(ly - H / 2 + 0.5) > 1.5)))
        sh.put(bars, ctx.palette(p[1:], ctx.texel_noise("cage") * 0.6 + 0.2), height=0.65, smooth=0.6)
    return sh.tex(grain=0.03)


def conduit_eye(ctx, open_):
    out = blank(ctx)
    m = ctx.rect(0, 0, 8, 8)
    sh = Sheet(ctx)
    lid = pal("1a3a4a", "2a5a6a", "3a7a8a", "5a9aaa")
    sh.put(m > 0.5, ctx.palette(lid, ctx.texel_noise("lid") * 0.5 + 0.3), height=0.5)
    if open_:
        white = (ctx.rect(1, 2, 7, 6) + ctx.rect(2, 1, 6, 7)) > 0
        sh.put(white, pal("e8f4f0")[0], height=0.6, emissive=0.6)
        iris = ctx.rect(3, 3, 5, 5) > 0.5
        sh.put(iris, pal("2aa0c0")[0], height=0.6, emissive=1.0)
        sh.put(ctx.rect(3, 3, 4, 4) > 0.5, pal("c0ffff")[0], height=0.6, emissive=1.0)
    else:
        sh.put(ctx.rect(1, 4, 7, 5) > 0.5, lid[0], height=0.4)
        sh.put(ctx.rect(2, 3, 6, 4) > 0.5, lid[3], height=0.6, emissive=0.2)
    sh.put(frame(ctx, (0, 0, 8, 8), 1), lid[0], height=0.45)
    # mirror onto the back face
    sh.color[:, 8 * ctx.s:16 * ctx.s] = sh.color[:, :8 * ctx.s][:, ::-1]
    for a in ("alpha", "height", "emissive", "smooth"):
        arr = getattr(sh, a)
        arr[:, 8 * ctx.s:16 * ctx.s] = arr[:, :8 * ctx.s][:, ::-1]
    return sh.tex(grain=0.0)


def conduit_wind(ctx, vertical):
    sh = Sheet(ctx)
    t = ctx.frame / max(1, ctx.frames)
    for n, r in sh.faces(0, 0, 16, 16, 16).items():
        m = sh.rect(r)
        lx, ly, W, H = sh.local(r)
        a_ = (lx if vertical else ly)
        b_ = (ly if vertical else lx)
        wave = np.sin((b_ / W * 2 * math.pi) + a_ * 0.35 - t * 2 * math.pi) * 2.5
        stripe = (((a_ + wave) % 8) < 2.0)
        a = np.where(stripe, 0.6, 0.0)
        sh.put(m & stripe, pal("d8f0ff")[0], alpha=a, height=0.5, smooth=0.8)
    return sh.tex(grain=0.0)


def conduit_particle(ctx):
    out = blank(ctx)
    p = pal("4a3a2a", "8e7656", "c4aa88", "e8d4b4")
    m = ctx.polygon([(4, 3), (12, 5), (11, 12), (5, 11)])
    out.paste(sprite(ctx, m, p, bevel=2))
    return out


# ------------------------------------------------------------------ cushions

def cushion(ctx, color):
    # Layout is a best guess (one 16x4x16 box at uv 0,0): unconfirmed, no CEM template.
    sh = Sheet(ctx)
    p = ramp(DYES[color], 6, spread=0.4)
    f = sh.faces(0, 0, 16, 4, 16)
    for n, r in f.items():
        m = sh.rect(r)
        lx, ly, W, H = sh.local(r)
        weave = ((ctx.tx + ctx.ty) % 2 == 0)
        if n in ("top", "bottom"):
            # Puffy top: quilted 2x2 grid with button tufts.
            dx = np.minimum(lx, W - lx) / (W / 2)
            dy = np.minimum(ly, H - ly) / (H / 2)
            puff = np.minimum(dx, dy)
            cell = (np.abs(((lx) % 8) - 4) + np.abs(((ly) % 8) - 4)) / 8
            v = np.clip(0.35 + puff * 0.35 + (0.5 - cell) * 0.3 + weave * 0.06 + ctx.texel_noise("cu") * 0.08, 0, 1)
            sh.put(m, ctx.palette(p[1:], v), height=0.5 + puff * 0.3, smooth=0.1, sss=0.2)
            for bx in (4, 12):
                for by in (4, 12):
                    sh.put(ctx.rect(r[0] + bx - 0.5, r[1] + by - 0.5, r[0] + bx + 0.5, r[1] + by + 0.5) > 0.5,
                           p[0], height=0.3)
            sh.put(frame(ctx, r, 1) & m, p[1], height=0.45)
        else:
            v = np.clip(0.45 + weave * 0.06 + ctx.texel_noise("cs") * 0.1 - (np.floor(ly) == 0) * 0.15
                        + (np.floor(ly) == H - 1) * -0.15, 0, 1)
            sh.put(m, ctx.palette(p[1:], v), height=0.5, smooth=0.1, sss=0.2)
            seam = m & (np.floor(ly) == 1) & ((ctx.tx % 2) == 0)
            sh.put(seam, p[3], height=0.55)
    return sh.tex(grain=0.03)


register("entity/armorstand/armorstand", armorstand)
register("entity/bell/bell_body", bell)
register("entity/enchantment/enchanting_table_book", book)
register("entity/minecart/minecart", minecart)
register("entity/lead_knot/lead_knot", lead_knot)
register("entity/end_crystal/end_crystal", end_crystal)
register("entity/end_crystal/end_crystal_beam", end_crystal_beam)
register("entity/beacon/beacon_beam", lambda ctx: beam(ctx, "beacon"))
register("entity/end_portal/end_gateway_beam", lambda ctx: beam(ctx, "gateway"))
register("entity/end_portal/end_portal", end_portal)
register("entity/experience/experience_orb", experience_orb)
register("entity/fishing/fishing_hook", fishing_hook)
register("entity/projectiles/arrow", lambda ctx: arrow(ctx, "normal"))
register("entity/projectiles/arrow_spectral", lambda ctx: arrow(ctx, "spectral"))
register("entity/projectiles/arrow_tipped", lambda ctx: arrow(ctx, "tipped"))
register("entity/projectiles/wind_charge", wind_charge)
register("entity/trident/trident", trident)
register("entity/trident/trident_riptide", riptide)
register("entity/conduit/base", conduit_shell)
register("entity/conduit/cage", conduit_cage)
register("entity/conduit/open_eye", lambda ctx: conduit_eye(ctx, True))
register("entity/conduit/closed_eye", lambda ctx: conduit_eye(ctx, False))
register("entity/conduit/wind", lambda ctx: conduit_wind(ctx, False), frametime=3)
register("entity/conduit/wind_vertical", lambda ctx: conduit_wind(ctx, True), frametime=3)
register("entity/conduit/break_particle", conduit_particle)
for _c in DYE_ORDER:
    register(f"entity/cushion/{_c}_cushion", (lambda c: lambda ctx: cushion(ctx, c))(_c))
