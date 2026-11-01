"""Misc items (a-g): emblems (templates, sherds, banner patterns, explorer maps)
registered on the shared h-z designs, buckets, block-like items, minecarts,
lanterns, chains, fireworks, frames.

Reusable families (minecart, lantern, chain, campfire, item_frame, diode) take
their palettes as arguments so the h-z variants can share them."""
import numpy as np

from ...engine import COPPER as COPPER_ID, GOLD as GOLD_ID, IRON as IRON_ID, pal
from ...registry import register, texture
from ...sprites import compose
from .common import CHAIN, COPPER, GOLD, GRAY, IRON, STONE, WOOD
from . import h_dials as HDL
from . import h_emblems as HE
from . import h_liquids as HL
from .a_lib import (U, arc_pts, box, circ, dots, ell, inter, line, minus, paint, poly, rod, shades, spr, stroke)
from .h_lib import rgb, rows_mask

# ------------------------------------------------------- smithing templates
MY_TRIMS = {
    "bolt": ("9a6a44", "f2c04a", ["....##..", "...##...", "..##....", ".######.", "....##..", "...##...", "..##....",
                                  "........"]),
    "coast": ("4a7a7a", "d8f0e0", ["........", "..##....", ".#..#..#", "#....##.", "..##....", ".#..#..#",
                                   "#....##.", "........"]),
    "dune": ("c8a46a", "6a4a22", ["...##...", "..#..#..", ".#....#.", "########", "........", ".##..##.", "#..##..#",
                                  "........"]),
    "eye": ("2e2a44", "b8e86a", ["........", "..####..", ".#....#.", "#..##..#", "#..##..#", ".#....#.", "..####..",
                                 "........"]),
    "flow": ("6a8ac4", "e0eaff", ["..####..", ".#....#.", "#..##..#", "#.#..#.#", "#.#.##.#", "#..#...#", ".#....#.",
                                  "..####.."]),
}
for _n, _v in MY_TRIMS.items():
    HE.TRIMS.setdefault(_n, _v)
    register(f"item/{_n}_armor_trim_smithing_template", lambda ctx, v=_v: HE.template(ctx, *v))

# ----------------------------------------------------------- pottery sherds
MY_SHERDS = {
    "angler": ["...#...", "...#...", "...#...", "#..#...", "#..#..#", ".###.#."],
    "archer": ["..#....", ".#.#...", "#...#..", "#######", "#...#..", ".#.#..."],
    "arms_up": ["#.###.#", "#.###.#", ".#####.", "..###..", "..#.#..", ".#...#."],
    "blade": ["......#", ".....#.", "....#..", "#..#...", ".##....", ".##...."],
    "brewer": ["..###..", "...#...", "..###..", ".#####.", ".#####.", "..###.."],
    "burn": ["...#...", "..##.#.", ".####..", ".#####.", "##.####", ".#####."],
    "danger": ["#######", "#.#.#.#", "#######", "##...##", "#.#.#.#", "#######"],
    "explorer": ["#######", "#..#..#", "#.###.#", "#..#..#", "#.....#", "#######"],
    "flow": ["..###..", ".#...#.", "#..#..#", "#.#.#.#", "#.#...#", ".#.###."],
    "friend": ["##...##", "##...##", ".......", "#.....#", ".#...#.", "..###.."],
    "guster": [".##.##.", "#..#..#", "...#...", ".###...", "#...##.", ".###..."],
}
for _n, _v in MY_SHERDS.items():
    HE.SHERDS.setdefault(_n, _v)
    register(f"item/{_n}_pottery_sherd", lambda ctx, n=_n: HE.sherd(ctx, n))

# ------------------------------------------------------------ banner patterns
MY_PATTERNS = {
    "bordure_indented": ["#.#.#.#.", ".#.#.#.#", "#......#", ".#....#.", "#......#", ".#.#.#.#", "#.#.#.#."],
    "creeper": ["........", "##....##", "##....##", "...##...", "..####..", "..#..#..", "........"],
    "field_masoned": ["###.####", "........", "#.####.#", "........", "###.####", "........", "#.####.#"],
    "flow": ["..####..", ".#....#.", "#..##..#", "#.#..#.#", "#.#.##.#", ".#.#...#", "..#.###."],
    "flower": ["...##...", ".#.##.#.", "..####..", "###..###", "..####..", ".#.##.#.", "...##..."],
    "globe": ["..####..", ".#.##.#.", "#.###..#", "#..###.#", "#.##...#", ".#.##.#.", "..####.."],
    "guster": [".###....", "#...#...", "...#..#.", "..#..#.#", ".#....#.", "#..###..", ".##....."],
}
for _n, _v in MY_PATTERNS.items():
    HE.PATTERNS.setdefault(_n, _v)
    register(f"item/{_n}_banner_pattern", lambda ctx, n=_n: HE.banner_pattern(ctx, n))

# ------------------------------------------------------------ explorer maps
HOUSE = ["..#..", ".###.", "#####", ".#.#.", ".###."]
MY_MARKERS = {
    "abandoned_camp": ("7a9a4a", "land", ["..#..", ".#.#.", ".#.#.", "#...#", "#####"], "c8b48a"),
    "buried_ancient_city": ("3a4a5a", "land", ["#####", "#.#.#", "#####", ".#.#.", "#####"], "2a8a9a"),
    "buried_mineshaft": ("8a7a5a", "land", ["#####", "#...#", "#...#", "#...#", "#...#"], "6a4a2a"),
    "buried_treasure": ("c8b878", "sea", ["#...#", ".#.#.", "..#..", ".#.#.", "#...#"], "b42a1e"),
    "buried_trial_chambers": ("6a7a6a", "land", ["#####", "#.#.#", "#####", "#.#.#", "#####"], "c8703c"),
    "desert_pyramid": ("e0c88a", "land", ["..#..", ".###.", ".###.", "#####", "#####"], "b8904a"),
    "desert_village": ("dcc480", "land", HOUSE, "a8783a"),
}
for _n, _v in MY_MARKERS.items():
    HDL.MARKERS.setdefault(_n, _v)
    register(f"item/{_n}_map", lambda ctx, n=_n: HDL.explorer_map(ctx, n))


@texture("item/filled_map")
def filled_map(ctx):
    t, inr, edge = HDL.map_base(ctx)
    n = ctx.noise(5, 2, 0.5, salt="filled")
    water = n < 0.42
    col = np.where(water[..., None], HDL.WATER, HDL.LAND)
    q = ctx.quantize(n, 4)
    col = col * (0.86 + 0.14 * q[..., None])
    t.color = np.where(inr[..., None], col, t.color)
    coast = water & ~(np.roll(water, ctx.s, 0) & np.roll(water, -ctx.s, 0) & np.roll(water, ctx.s, 1) &
                      np.roll(water, -ctx.s, 1))
    paint(t, coast & inr, HDL.INK * 1.4)
    return t


# ------------------------------------------------------------------ buckets
AXOLOTL_P = pal("6a2a44", "c45a8a", "f290bc", "fcc4dc", "fff0f6")
COD_P = pal("3e3424", "6e6046", "9a8a68", "bcae8a", "dcd0b0")
register("item/bucket", lambda ctx: HL.bucket(ctx))
register("item/cod_bucket", lambda ctx: HL.bucket(ctx, HL.WATER, extra=HL.fish_peek(
    COD_P, [(8.4, 4.4, 3.2, 1.4, 0.25), (4.8, 5.6, 1.2, 1.1, -0.5)], (10, 4))))


def axolotl_peek(ctx):
    m = U(ell(ctx, 8.4, 4.6, 3.0, 1.6, -0.15), ell(ctx, 4.6, 5.6, 1.6, 0.8, 0.4))
    t = spr(ctx, m, AXOLOTL_P, bevel=1.5, smooth=0.5)
    gills = spr(ctx, U(line(ctx, [(10.4, 3.6), (11.6, 1.8)], 0.9), line(ctx, [(11.2, 4.2), (13.0, 3.0)], 0.9)),
                pal("8a1a4a", "c8306a", "e85a8a"), outline=False, bevel=1)
    paint(t, dots(ctx, [(10, 4)], 0.45), rgb("1a0a10"))
    return compose(ctx, t, gills)


register("item/axolotl_bucket", lambda ctx: HL.bucket(ctx, HL.WATER, extra=axolotl_peek))


# ------------------------------------------------------------- minecarts

CART = pal("2a2a2e", "4a4a50", "6e6e76", "94949c", "b8b8c0")
CHEST = pal("3a2410", "6a4420", "94612e", "b8803e", "d09a52")


def minecart(ctx, cargo=None):
    """Side view iron cart; cargo(ctx) -> layer drawn inside, peeking over the rim."""
    body = poly(ctx, [(1.0, 6.6), (15.0, 6.6), (13.6, 12.6), (2.4, 12.6)])
    t = spr(ctx, body, CART, bevel=1.5, smooth=0.55)
    t.set_metal(body, IRON_ID)
    ring = ctx.edge(body, 1) > 0
    paint(t, box(ctx, 2.0, 7.6, 14.0, 8.6) * (~ring), CART[4])
    paint(t, box(ctx, 2.6, 10.6, 13.4, 11.4) * (~ring), CART[1])
    for x in (5.0, 11.0):
        paint(t, dots(ctx, [(x - 0.5, 9.0)], 0.45) * (~ring), CART[4])
    wheels = U(circ(ctx, 4.6, 13.0, 1.8), circ(ctx, 11.4, 13.0, 1.8))
    tw = spr(ctx, wheels, pal("141416", "2a2a2e", "44444a", "60606a"), bevel=1)
    paint(tw, U(circ(ctx, 4.6, 13.0, 0.5), circ(ctx, 11.4, 13.0, 0.5)), CART[3])
    layers = []
    if cargo is not None:
        layers.append(cargo(ctx))
    return compose(ctx, *layers, t, tw)


def chest_cargo(ctx):
    m = box(ctx, 3.4, 2.0, 12.6, 7.6)
    t = spr(ctx, m, CHEST, bevel=1.5, porosity=0.2)
    ring = ctx.edge(m, 1) > 0
    paint(t, box(ctx, 3.4, 4.0, 12.6, 5.0) * (~ring), CHEST[0])
    latch = spr(ctx, box(ctx, 7.0, 3.6, 9.0, 6.0), IRON, bevel=1)
    latch.set_metal(latch.alpha, IRON_ID)
    return compose(ctx, t, latch)


def furnace_cargo(ctx):
    m = box(ctx, 3.4, 1.6, 12.6, 7.6)
    t = spr(ctx, m, STONE, bevel=1.2)
    ring = ctx.edge(m, 1) > 0
    n = ctx.texel_noise("fur")
    inner = (m > 0.5) & ~ring
    t.color[inner & (n < 0.2)] = STONE[1]
    t.color[inner & (n > 0.85)] = STONE[4]
    mouth = box(ctx, 6.0, 3.6, 10.0, 6.0)
    paint(t, mouth, pal("1a1210")[0])
    flame = inter(mouth, box(ctx, 6.0, 4.6, 10.0, 6.0))
    paint(t, flame, pal("f29a1a")[0])
    paint(t, inter(flame, box(ctx, 7.0, 5.0, 9.0, 6.0)), pal("ffe070")[0])
    t.emissive = np.where(flame > 0.5, 0.8, 0.0)
    return t


def command_cargo(ctx):
    p = pal("4a2a14", "8a5428", "b07438", "c8904a", "e0b06a")
    m = box(ctx, 3.4, 1.6, 12.6, 7.6)
    t = spr(ctx, m, p, bevel=1.2, smooth=0.5)
    ring = ctx.edge(m, 1) > 0
    paint(t, box(ctx, 5.0, 3.0, 11.0, 7.0) * (~ring), pal("c8c4b8")[0])
    paint(t, box(ctx, 6.0, 4.0, 10.0, 6.4), pal("2a2a2a")[0])
    paint(t, U(box(ctx, 6.6, 4.6, 7.6, 5.6), box(ctx, 8.4, 4.6, 9.4, 5.6)), pal("8ad0e8")[0])
    t.emissive = np.where(U(box(ctx, 6.6, 4.6, 7.6, 5.6), box(ctx, 8.4, 4.6, 9.4, 5.6)) > 0.5, 0.5, 0.0)
    return t


register("item/chest_minecart", lambda ctx: minecart(ctx, chest_cargo))
register("item/furnace_minecart", lambda ctx: minecart(ctx, furnace_cargo))
register("item/command_block_minecart", lambda ctx: minecart(ctx, command_cargo))


# --------------------------------------------------------- chains, lanterns

EXPOSED = pal("4e3428", "7e5a48", "a07c66", "b89a82", "d0b8a0")
COPPER_FLAME = pal("2a8a5a", "5ad08a", "a8f4c4", "eafff2")


def chain(ctx, p, metal_id=None):
    layers = []
    for i, y in enumerate(range(0, 16, 4)):
        if i % 2 == 0:  # link seen face-on: ring
            m = minus(box(ctx, 6.0, y, 10.0, y + 4.6), box(ctx, 7.0, y + 1.0, 9.0, y + 3.6))
        else:  # link seen edge-on: bar
            m = box(ctx, 7.0, y - 0.6, 9.0, y + 4.6)
        t = spr(ctx, m, p, bevel=1, smooth=0.6)
        if metal_id:
            t.set_metal(m, metal_id)
        layers.append(t)
    return compose(ctx, *layers[1::2], *layers[0::2])


def lantern(ctx, frame_p, flame_p, metal_id=None, emissive=0.9):
    cage = box(ctx, 4.0, 5.0, 12.0, 15.0)
    t = spr(ctx, cage, frame_p, bevel=1, smooth=0.55)
    if metal_id:
        t.set_metal(cage, metal_id)
    glass = box(ctx, 5.0, 7.0, 11.0, 13.0)
    gl_col = np.clip(flame_p[1] * 0.75 + 0.1, 0, 1)
    paint(t, glass, gl_col)
    core = box(ctx, 6.0, 8.0, 10.0, 12.0)
    paint(t, core, flame_p[2])
    paint(t, box(ctx, 7.0, 9.0, 9.0, 11.0), flame_p[3])
    t.metal = np.where(glass > 0.5, 0, t.metal)
    t.emissive = np.where(glass > 0.5, emissive * 0.7, 0.0)
    t.emissive = np.where(core > 0.5, emissive, t.emissive)
    paint(t, U(box(ctx, 4.0, 7.0, 5.0, 13.0), box(ctx, 11.0, 7.0, 12.0, 13.0)), frame_p[1])
    lid = box(ctx, 5.0, 3.0, 11.0, 5.0)
    tl = spr(ctx, lid, frame_p, bevel=1, smooth=0.55)
    hook = spr(ctx, minus(box(ctx, 6.0, 0.0, 10.0, 3.0), box(ctx, 7.0, 1.0, 9.0, 3.0)), CHAIN, bevel=1)
    if metal_id:
        tl.set_metal(lid, metal_id)
    hook.set_metal(hook.alpha, IRON_ID)
    return compose(ctx, hook, t, tl)


register("item/copper_chain", lambda ctx: chain(ctx, COPPER, COPPER_ID))
register("item/exposed_copper_chain", lambda ctx: chain(ctx, EXPOSED, COPPER_ID))
register("item/copper_lantern", lambda ctx: lantern(ctx, COPPER, COPPER_FLAME, COPPER_ID))
register("item/exposed_copper_lantern", lambda ctx: lantern(ctx, EXPOSED, COPPER_FLAME, COPPER_ID))


# --------------------------------------------------------- block-like items

LOG = pal("2a1c0e", "4a3218", "6a4a24", "8a6230", "a87c40")
FLAME = pal("b02a06", "f06a10", "fcae2a", "fff07a")


def campfire(ctx, flame_p=FLAME):
    logs = U(line(ctx, [(1.6, 13.0), (14.4, 10.6)], 2.4), line(ctx, [(1.6, 10.6), (14.4, 13.0)], 2.4))
    tl = spr(ctx, logs, LOG, bevel=1, porosity=0.3)
    ring = ctx.edge(logs, 1) > 0
    paint(tl, dots(ctx, [(1, 12), (14, 12), (1, 10), (14, 10)], 0.6), pal("8a6230")[0])
    fl = U(poly(ctx, [(4.0, 11.0), (5.4, 6.0), (6.6, 8.0), (8.0, 2.0), (9.6, 7.0), (10.6, 5.0), (12.0, 11.0)]))
    tf = spr(ctx, fl, flame_p, bevel=1.5, outline=False, emissive=1.0)
    paint(tf, poly(ctx, [(6.0, 11.0), (7.0, 8.0), (8.0, 5.6), (9.0, 8.0), (10.0, 11.0)]), flame_p[3])
    paint(tf, ctx.edge(fl, 1) > 0, flame_p[0])
    return compose(ctx, tf, tl)


register("item/campfire", lambda ctx: campfire(ctx))

IRON_POT = pal("1a1a1e", "2e2e34", "44444c", "5e5e68", "7a7a84")


@texture("item/cauldron")
def cauldron(ctx):
    body = U(box(ctx, 1.0, 3.0, 15.0, 13.0), box(ctx, 1.0, 13.0, 4.0, 15.0), box(ctx, 12.0, 13.0, 15.0, 15.0))
    t = spr(ctx, body, IRON_POT, bevel=1.5, smooth=0.45)
    t.set_metal(body, IRON_ID)
    ring = ctx.edge(body, 1) > 0
    paint(t, box(ctx, 2.0, 4.0, 14.0, 5.0), IRON_POT[4])
    paint(t, box(ctx, 2.0, 5.0, 14.0, 6.0), IRON_POT[1])
    paint(t, box(ctx, 4.0, 13.0, 12.0, 15.0), pal("000000")[0])
    t.alpha = np.where(box(ctx, 4.0, 13.0, 12.0, 15.0) > 0.5, 0.0, t.alpha)
    paint(t, U(box(ctx, 3.0, 8.0, 5.0, 10.0), box(ctx, 11.0, 8.0, 13.0, 10.0)) * (~ring), IRON_POT[1])
    return t


@texture("item/flower_pot")
def flower_pot(ctx):
    p = pal("4a1e10", "7a3420", "a04a2e", "bc6040", "d47c58")
    body = U(box(ctx, 3.0, 4.0, 13.0, 7.0), poly(ctx, [(4.0, 7.0), (12.0, 7.0), (11.0, 15.0), (5.0, 15.0)]))
    t = spr(ctx, body, p, bevel=1.5, porosity=0.6)
    paint(t, box(ctx, 4.0, 5.0, 12.0, 6.0), pal("2a1810")[0])
    paint(t, box(ctx, 4.0, 4.0, 12.0, 5.0) * (~(ctx.edge(body, 1) > 0)), p[4])
    paint(t, box(ctx, 4.0, 7.0, 12.0, 8.0) * (~(ctx.edge(body, 1) > 0)), p[1])
    return t


@texture("item/bell")
def bell(ctx):
    body = U(poly(ctx, [(5.0, 4.0), (11.0, 4.0), (12.0, 10.0), (13.6, 12.6), (2.4, 12.6), (4.0, 10.0)]),
             ell(ctx, 8.0, 4.4, 3.0, 1.8))
    t = spr(ctx, body, GOLD, bevel=2.0, smooth=0.75)
    t.set_metal(body, GOLD_ID)
    ring = ctx.edge(body, 1) > 0
    paint(t, box(ctx, 3.0, 11.0, 13.0, 12.0) * (~ring), GOLD[1])
    paint(t, line(ctx, [(5.6, 5.0), (5.0, 9.6)], 0.8) * (~ring), GOLD[4])
    top = spr(ctx, minus(box(ctx, 6.6, 0.6, 9.4, 3.4), box(ctx, 7.6, 1.6, 8.4, 3.4)), pal("2a2a2e", "4a4a50", "6e6e76"),
              bevel=1)
    clap = spr(ctx, circ(ctx, 8.0, 13.6, 1.2), pal("2a2a2e", "4a4a50", "6e6e76", "94949c"), bevel=1)
    return compose(ctx, top, clap, t)


@texture("item/armor_stand")
def armor_stand(ctx):
    p = WOOD
    base = spr(ctx, box(ctx, 2.0, 13.4, 14.0, 15.6), pal("3a3a3c", "5a5a5d", "7a7a7d", "959598", "b3b3b6"), bevel=1)
    pole = rod(ctx, [(8.0, 3.4), (8.0, 13.6)], 1.6, p)
    sh = spr(ctx, box(ctx, 2.6, 5.0, 13.4, 6.8), p, bevel=1, porosity=0.2)
    hip = spr(ctx, box(ctx, 4.6, 10.0, 11.4, 11.6), p, bevel=1, porosity=0.2)
    legs = rod(ctx, [(6.0, 11.0), (6.0, 13.6)], 1.4, p)
    legs2 = rod(ctx, [(10.0, 11.0), (10.0, 13.6)], 1.4, p)
    head = spr(ctx, box(ctx, 6.4, 0.6, 9.6, 3.8), p, bevel=1, porosity=0.2)
    return compose(ctx, base, pole, legs, legs2, hip, sh, head)


@texture("item/bamboo")
def bamboo(ctx):
    p = pal("3a4a12", "5a7020", "7a9430", "9ab448", "bcd468")
    stalk = line(ctx, [(4.6, 15.0), (10.0, 2.0)], 2.4)
    t = spr(ctx, stalk, p, bevel=1, smooth=0.4)
    for f in (0.25, 0.55, 0.82):
        x, y = 4.6 + (10.0 - 4.6) * f, 15.0 - 13.0 * f
        paint(t, line(ctx, [(x - 1.2, y - 0.4), (x + 1.2, y + 0.4)], 0.8), p[0])
    leaves = spr(ctx, U(ell(ctx, 12.0, 3.4, 2.6, 0.9, 0.5), ell(ctx, 6.4, 6.0, 2.4, 0.9, -0.5),
                        ell(ctx, 12.4, 8.4, 2.4, 0.8, 0.3)), pal("2e5a14", "4a8a20", "6ab030", "8ad04a"), bevel=1)
    return compose(ctx, t, leaves)


@texture("item/barrier")
def barrier(ctx):
    ring = minus(circ(ctx, 8.0, 8.0, 7.2), circ(ctx, 8.0, 8.0, 5.0))
    slash = inter(line(ctx, [(3.6, 3.6), (12.4, 12.4)], 2.2), circ(ctx, 8.0, 8.0, 5.4))
    m = U(ring, slash)
    t = spr(ctx, m, pal("5a0808", "a01414", "d42a22", "f05a48"), bevel=1, smooth=0.5)
    t.emissive = np.where(m > 0.5, 0.3, 0.0)
    return t


@texture("item/brewing_stand")
def brewing_stand(ctx):
    base = spr(ctx, U(box(ctx, 1.0, 13.0, 6.0, 15.0), box(ctx, 10.0, 13.0, 15.0, 15.0), box(ctx, 5.6, 13.6, 10.4, 15.0)),
               STONE, bevel=1)
    rod_t = spr(ctx, box(ctx, 7.0, 2.0, 9.0, 14.0), pal("7a3404", "d0700c", "f6a420", "ffd250"), bevel=1,
                emissive=0.4)
    arms = rod(ctx, [(3.0, 9.0), (8.0, 6.0), (13.0, 9.0)], 1.0, pal("3a2a1a", "6a5034", "8a7050"))
    bottles = []
    for cx in (3.0, 13.0):
        b = U(circ(ctx, cx, 11.0, 1.8), box(ctx, cx - 0.6, 8.6, cx + 0.6, 10.0))
        bottles.append(spr(ctx, b, pal("4a6a7a", "86a8b8", "b6d2de", "e4f4fa"), bevel=1, smooth=0.9))
    return compose(ctx, base, arms, rod_t, *bottles)


@texture("item/comparator")
def comparator(ctx):
    slab = poly(ctx, [(1.0, 9.0), (8.0, 5.6), (15.0, 9.0), (8.0, 12.4)])
    side = U(slab, poly(ctx, [(1.0, 9.0), (8.0, 12.4), (15.0, 9.0), (15.0, 10.6), (8.0, 14.0), (1.0, 10.6)]))
    t = spr(ctx, side, pal("3a3a3c", "5a5a5d", "8a8a8d", "a5a5a8", "c3c3c6"), bevel=1)
    ring = ctx.edge(side, 1) > 0
    paint(t, slab * (~ring), pal("a5a5a8")[0])
    paint(t, line(ctx, [(5.0, 9.4), (8.0, 7.6), (11.0, 9.4)], 0.6) * (~ring), pal("8a1010")[0])
    layers = [t]
    for x, y, lit in ((4.6, 8.6, True), (11.4, 8.6, True), (8.0, 11.0, False)):
        stick = rod(ctx, [(x, y), (x, y - 3.4)], 1.0, WOOD)
        head = spr(ctx, circ(ctx, x, y - 3.6, 0.9), pal("5a0808", "c41f1f", "ff6a50") if lit else
                   pal("3a0606", "6a1010", "8a2020"), bevel=1, emissive=0.8 if lit else 0.0)
        layers += [stick, head]
    return compose(ctx, *layers)


@texture("item/end_crystal")
def end_crystal(ctx):
    glass = poly(ctx, [(8.0, 1.0), (14.6, 7.6), (8.0, 14.2), (1.4, 7.6)])
    tg = spr(ctx, glass, pal("6a5a7a", "a898c0", "d0c4e2", "f2ecff"), bevel=1, smooth=0.95)
    inner = poly(ctx, [(8.0, 3.0), (12.6, 7.6), (8.0, 12.2), (3.4, 7.6)])
    tg.alpha = np.where((inner > 0.5) & ~(ctx.edge(glass, 1) > 0) & ~(ctx.edge(inner, 1) > 0), 0.0, tg.alpha)
    paint(tg, ctx.edge(inner, 1) > 0, pal("8a7aa0")[0])
    core = box(ctx, 5.6, 5.2, 10.4, 10.0)
    tc = spr(ctx, core, pal("4a1a5a", "8a3aa0", "c46ae0", "f0b0ff"), bevel=1.5, emissive=0.8, smooth=0.8)
    paint(tc, box(ctx, 6.6, 6.2, 8.0, 7.6), pal("ffe0ff")[0])
    base = spr(ctx, box(ctx, 3.0, 13.0, 13.0, 15.4), pal("0e0e12", "1e1e24", "2e2e36", "40404a"), bevel=1)
    return compose(ctx, base, tg, tc)


@texture("item/firefly_bush")
def firefly_bush(ctx):
    p = pal("1a2a0e", "2e4a16", "46682a", "5e863a", "7aa24c")
    m = U(ell(ctx, 8.0, 10.0, 6.4, 4.6), circ(ctx, 5.0, 7.0, 3.0), circ(ctx, 11.0, 6.6, 3.0), circ(ctx, 8.0, 5.0, 3.0))
    t = spr(ctx, m, p, bevel=2.0, sss=0.4)
    ring = ctx.edge(m, 1) > 0
    n = ctx.texel_noise("bush")
    inner = (m > 0.5) & ~ring
    t.color[inner & (n < 0.2)] = p[1]
    t.color[inner & (n > 0.85)] = p[4]
    flies = dots(ctx, [(3, 3), (13, 2), (12, 10), (5, 11), (8, 7), (14, 6)], 0.5)
    paint(t, flies, pal("e8f86a")[0], inside=False)
    t.alpha = np.maximum(t.alpha, flies)
    t.emissive = np.where(flies > 0.5, 1.0, 0.0)
    return t


# ---------------------------------------------------------------- fireworks

@texture("item/firework_rocket")
def firework_rocket(ctx):
    stick = rod(ctx, [(2.0, 14.6), (7.0, 9.6)], 1.2, WOOD)
    from .a_lib import Diag
    d = Diag(6.0, 10.0)
    tube_m = d.rect(ctx, 0.0, -2.2, 6.4, 2.2)
    tube = spr(ctx, tube_m, pal("4a0c0c", "8a1a1a", "c42e2a", "e85a4a", "fa9080"), bevel=1.2, porosity=0.4)
    ring = ctx.edge(tube_m, 1) > 0
    paint(tube, d.rect(ctx, 2.4, -2.2, 3.6, 2.2) * (~ring), pal("f2ead6")[0])
    cone = spr(ctx, d.poly(ctx, [(6.2, -2.4), (9.6, 0), (6.2, 2.4)]), pal("2a2a50", "40409a", "6060d0", "9090f0"),
               bevel=1)
    fuse = rod(ctx, [d.p(-0.4, 0.8), d.p(-1.6, 2.4)], 0.8, pal("3a3a3a", "6a6a6a", "9a9a9a"))
    return compose(ctx, stick, fuse, tube, cone)


STAR_M = None


def star_mask(ctx):
    return U(circ(ctx, 8.0, 8.4, 4.6), circ(ctx, 4.6, 5.4, 1.8), circ(ctx, 11.6, 5.0, 1.8), circ(ctx, 12.4, 11.6, 1.8),
             circ(ctx, 4.0, 11.8, 1.8), circ(ctx, 8.4, 13.4, 1.4))


@texture("item/firework_star")
def firework_star(ctx):
    m = star_mask(ctx)
    t = spr(ctx, m, pal("1e1e20", "3a3a3e", "56565c", "74747a", "96969c"), bevel=2.0, porosity=0.8)
    inner = circ(ctx, 8.0, 8.4, 3.0)
    paint(t, inner, pal("2a2a2e")[0])  # covered by the tinted overlay
    return t


@texture("item/firework_star_overlay")
def firework_star_overlay(ctx):
    """Grayscale core tinted by the star's colors (gray 0.5..0.9)."""
    m = circ(ctx, 8.0, 8.4, 3.0)
    t = spr(ctx, m, pal("7a7a7a", "a0a0a0", "c4c4c4", "e2e2e2"), bevel=1.5, outline=False, porosity=0.6)
    return t


# --------------------------------------------------------------- item frame

def item_frame(ctx, frame_p, back_p, glow=0.0):
    outer = box(ctx, 1.0, 1.0, 15.0, 15.0)
    t = spr(ctx, outer, frame_p, bevel=1.5, porosity=0.2, emissive=glow)
    inner = box(ctx, 3.0, 3.0, 13.0, 13.0)
    tb = spr(ctx, inner, back_p, bevel=1, outline=False, porosity=0.5)
    paint(tb, ctx.edge(inner, 1, "tl") > 0, back_p[0])
    tb.emissive = np.zeros_like(tb.emissive)
    t = compose(ctx, t, tb)
    n = ctx.texel_noise("frame")
    fr = (outer > 0.5) & ~(inner > 0.5) & ~(ctx.edge(outer, 1) > 0)
    t.color[fr & (n < 0.2)] = frame_p[1]
    t.color[fr & (n > 0.85)] = frame_p[-1]
    return t


register("item/glow_item_frame", lambda ctx: item_frame(
    ctx, pal("1e4a3a", "2e7a5e", "4aa880", "7ad4a6", "b0f4d0"), pal("4a2c18", "6e4428", "8a5a36", "a07040"), 0.5))
