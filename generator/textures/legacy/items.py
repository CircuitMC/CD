"""Old item sprites: 1.7/1.8 animated clock/compass strips, flat head icons, flat
bed / banner icons, spawn-egg templates, map markings, unused leftovers."""
import numpy as np

from ...engine import Tex, hexc, pal
from ...sprites import compose, sprite
from ..item.a_lib import U, cells, circ, ell, line, minus, poly, shades, spr
from ..item.a_spawn_eggs import egg_mask
from .kit import adopt, blank, crop, put, reg, render


# ------------------------------------------------------------------ dial strips

reg("items/clock", lambda ctx: adopt(ctx, render(f"item/clock_{ctx.frame:02d}", ctx.s, 16, 16)))
reg("items/compass", lambda ctx: adopt(ctx, render(f"item/compass_{ctx.frame:02d}", ctx.s, 16, 16)))


# ------------------------------------------------------------------ flat head icons (1.7)

HEADS = {
    "creeper": "entity/creeper/creeper",
    "skeleton": "entity/skeleton/skeleton",
    "steve": "entity/player/wide/steve",
    "wither": "entity/skeleton/wither_skeleton",
    "zombie": "entity/zombie/zombie",
}


def head_icon(ctx, mob):
    """Small three-quarter head: front face 8x8, squashed top and right side."""
    src = render(HEADS[mob], ctx.s)
    k = src.ctx.w / 64  # some skins are drawn on larger sheets
    t = blank(ctx)
    front = crop(src, (8 * k, 8 * k, 16 * k, 16 * k))
    top = crop(src, (8 * k, 0, 16 * k, 8 * k))
    side = crop(src, (0, 8 * k, 8 * k, 16 * k))
    put(t, top, (4, 2, 12, 5))
    put(t, side, (12, 3, 14, 13))
    put(t, front, (4, 5, 12, 13))
    # lighting: top lit, side shaded, then a soft dark outline
    sl = lambda r: np.s_[r[1] * ctx.s:r[3] * ctx.s, r[0] * ctx.s:r[2] * ctx.s]
    t.color[sl((4, 2, 12, 5))] *= 1.12
    t.color[sl((12, 3, 14, 13))] *= 0.7
    m = t.alpha > 0.5
    ring = ctx.edge(m.astype(np.float32), 1) > 0
    t.color[ring] *= 0.72
    t.color = np.clip(t.color, 0, 1)
    t.alpha = m.astype(np.float32)
    t.height = np.where(m, 0.6, 0.0)
    t.wrap = False
    return t


for _m in HEADS:
    reg(f"items/skull_{_m}", lambda ctx, m=_m: head_icon(ctx, m))


# ------------------------------------------------------------------ flat bed icon (1.7-1.8)

BED_WOOD = pal("3e2818", "5a3c26", "77513a", "8f6545", "a67a52")
BED_RED = pal("4a1010", "781a1a", "a02424", "c03a30", "da5a48")
BED_SHEET = pal("8a8580", "b6b0aa", "d6d2cc", "ecebe6", "faf8f4")


def bed_item(ctx):
    slab = poly(ctx, [(1, 7), (11, 7), (15, 9), (15, 12), (5, 12), (1, 10)])
    top = poly(ctx, [(1, 7), (11, 7), (15, 9), (5, 9)])
    pillow = poly(ctx, [(2, 6.5), (5.5, 6.5), (7.5, 8.2), (4, 8.2)])
    legs = U(cells(ctx, [(1, 10), (1, 11), (5, 12), (5, 13), (14, 12), (14, 13)]))
    wood = spr(ctx, U(legs, poly(ctx, [(1, 9), (5, 11), (15, 11), (15, 12), (5, 12), (1, 10)])), BED_WOOD, bevel=1)
    body = spr(ctx, slab, BED_RED, bevel=1.5, sss=0.1, porosity=0.5)
    blanket_top = (top > 0.5) & ~(ctx.edge(slab, 1) > 0)
    body.color[blanket_top] = np.clip(body.color[blanket_top] * 1.12, 0, 1)
    sheet = spr(ctx, U(poly(ctx, [(1, 7), (5, 7), (8, 9), (5, 9)]), poly(ctx, [(5, 9), (8, 9), (8, 11), (5, 11)])),
                BED_SHEET, bevel=1, outline=False)
    pil = spr(ctx, pillow, BED_SHEET, bevel=1)
    rail = spr(ctx, poly(ctx, [(5, 11), (15, 11), (15, 12), (5, 12)]), BED_WOOD, bevel=1, outline=False)
    return compose(ctx, body, sheet, wood, rail, pil)


reg("items/bed", bed_item)


# ------------------------------------------------------------------ spawn egg templates (grey, tinted)

EGG_GREY = shades("c8c8c8", 5, 0.5, 1.22)
SPOT_GREY = shades("d0d0d0", 3, 0.78, 1.12)


def egg_base(ctx):
    m = egg_mask(ctx)
    t = spr(ctx, m, EGG_GREY, bevel=3.0, light=0.32, smooth=0.35)
    hl = (circ(ctx, 5.6, 4.6, 0.7) > 0.5) & ~(ctx.edge(m, 1) > 0)
    t.color[hl] = EGG_GREY[4]
    return t


def egg_spots(ctx):
    m = egg_mask(ctx)
    inner = (m > 0.5) & ~(ctx.edge(m, 1) > 0)
    rng = ctx.rng("eggspots")
    s = ctx.zeros()
    for cx, cy, r in ((6.2, 7.0, 1.3), (10.2, 6.2, 1.0), (9.2, 10.6, 1.5), (5.6, 12.0, 1.0), (11.0, 13.0, 0.8)):
        s = np.maximum(s, circ(ctx, cx + rng.uniform(-0.2, 0.2), cy, r))
    s = (s > 0.5) & inner
    t = spr(ctx, s.astype(np.float32), SPOT_GREY, bevel=1, outline=False, light=0.2)
    t.alpha = s.astype(np.float32)
    return t


for _p in ("items/", "item/"):
    reg(f"{_p}spawn_egg", egg_base)
    reg(f"{_p}spawn_egg_overlay", egg_spots)


# ------------------------------------------------------------------ flat banner (1.8)

POLE = pal("3a2616", "5a3c22", "7a5432", "946a42", "aa804f")
CLOTH_GREY = shades("dedede", 5, 0.55, 1.12)


def banner_cloth_mask(ctx):
    return poly(ctx, [(4, 3), (12, 3), (12, 13), (8, 11.6), (4, 13)])


def banner_base(ctx):
    pole = spr(ctx, poly(ctx, [(7, 3), (9, 3), (9, 16), (7, 16)]), POLE, bevel=1)
    bar = spr(ctx, poly(ctx, [(3, 2), (13, 2), (13, 3), (3, 3)]), POLE, bevel=1)
    back = spr(ctx, banner_cloth_mask(ctx), shades("b8b4ac", 5, 0.55, 1.1), bevel=1.5, sss=0.1, porosity=0.4)
    return compose(ctx, pole, back, bar)


def banner_overlay(ctx):
    m = banner_cloth_mask(ctx)
    t = spr(ctx, m, CLOTH_GREY, bevel=1.5, sss=0.1, porosity=0.4)
    folds = (cells(ctx, [(6, y) for y in range(4, 12)]) > 0.5) | (cells(ctx, [(10, y) for y in range(4, 12)]) > 0.5)
    t.color[folds & (t.alpha > 0.5) & ~(ctx.edge(m, 1) > 0)] *= 0.9
    return t


reg("items/banner_base", banner_base)
reg("items/banner_overlay", banner_overlay)


# ------------------------------------------------------------------ map markings overlay (tinted)

def map_markings(ctx):
    """Grey ink marks inside the map paper; the game tints them."""
    rng = ctx.rng("marks")
    m = ctx.zeros()
    pts = [(4.5, 5.5), (6.5, 4.5), (8.5, 6.2), (10.5, 5.0), (11.5, 7.5)]
    m = np.maximum(m, line(ctx, pts, 0.9))
    m = np.maximum(m, line(ctx, [(4.0, 9.5), (6.0, 10.5), (7.5, 9.0), (9.5, 11.5), (12.0, 10.5)], 0.9))
    for _ in range(5):
        x, y = int(rng.integers(4, 12)), int(rng.integers(7, 13))
        m = np.maximum(m, cells(ctx, [(x, y)]))
    mm = (m > 0.5).astype(np.float32)
    v = 0.62 + (ctx.texel_noise("ink") - 0.5) * 0.12
    t = Tex(ctx, np.repeat(v[..., None], 3, -1), alpha=mm, height=np.where(mm > 0, 0.48, 0.0), smooth=0.1,
            porosity=0.5, wrap=False, grain=0.03)
    return t


reg("items/map_filled_markings", map_markings)
reg("item/filled_map_markings", map_markings)


# ------------------------------------------------------------------ unused leftovers

def ruby(ctx):
    t = adopt(ctx, render("item/emerald", ctx.s, 16, 16))
    c = t.color
    lum = c @ np.array([0.3, 0.59, 0.11], np.float32)
    red = np.stack([np.clip(lum * 1.55 + 0.06, 0, 1), lum * 0.32, lum * 0.42], -1)
    t.color = np.where((t.alpha > 0.5)[..., None], red, c).astype(np.float32)
    return t


reg("items/ruby", ruby)
reg("item/ruby", ruby)

QUIVER = pal("3a2214", "5e3a22", "804f2e", "9c663c", "b47e4e")
FLETCH = pal("8a8a8a", "c4c4c4", "eeeeee")


def quiver(ctx):
    bag = poly(ctx, [(3, 6), (8, 3), (13, 9), (8, 14)])
    t = spr(ctx, bag, QUIVER, bevel=1.5, porosity=0.4)
    strap = line(ctx, [(4, 12), (12, 4)], 0.9)
    t.color[(strap > 0.5) & (t.alpha > 0.5) & ~(ctx.edge(bag, 1) > 0)] = QUIVER[1]
    shafts = U(line(ctx, [(5, 6), (2.5, 2.5)], 0.9), line(ctx, [(7, 4.5), (5, 1.5)], 0.9))
    sh = spr(ctx, minus(shafts, bag), pal("5a4026", "8a6a42", "b08c5c"), bevel=1, outline=False)
    tips = spr(ctx, cells(ctx, [(1, 1), (2, 1), (1, 2), (4, 0), (5, 0)]), FLETCH, bevel=1, outline=False)
    return compose(ctx, sh, tips, t)


reg("items/quiver", quiver)


def bundle_filled(ctx):
    """Bundle with a bulging top: the empty bundle plus items poking out."""
    t = adopt(ctx, render("item/bundle", ctx.s, 16, 16))
    gem = spr(ctx, ell(ctx, 6.5, 4.6, 1.8, 1.4), shades("4ab8c8", 5, 0.5, 1.3), bevel=1, smooth=0.7)
    stick = spr(ctx, line(ctx, [(9.0, 6.0), (11.5, 2.5)], 1.1), pal("4a321c", "7a5632", "a07848"), bevel=1)
    top = compose(ctx, stick, gem)
    under = t.alpha > 0.5
    keep = top.alpha > 0.5
    out = blank(ctx)
    out.paste(top)
    out.paste(t, under & ~(keep & (ctx.y < 6.5)))
    out.normal_strength, out.grain = t.normal_strength, t.grain
    return out


reg("item/bundle_filled", bundle_filled)


# ------------------------------------------------------------------ plain helpers

def white(ctx):
    return Tex(ctx, (1.0, 1.0, 1.0), wrap=False, grain=0)


reg("misc/white", white, pbr=False)


def footprint(ctx):
    """1.7-1.16 footstep particle: two soft grey sole prints."""
    # a_lib shapes use 16-unit coordinates: double the 8x8 positions
    m = np.maximum(ell(ctx, 5.0, 6.0, 2.2, 4.2), ell(ctx, 11.0, 10.0, 2.2, 4.2))
    mm = (m > 0.5).astype(np.float32)
    v = 0.42 + (ctx.texel_noise("fp") - 0.5) * 0.1
    return Tex(ctx, np.repeat(v[..., None], 3, -1), alpha=mm, height=0.0, wrap=False, grain=0)


reg("particle/footprint", footprint, pbr=False)
