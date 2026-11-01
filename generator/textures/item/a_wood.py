"""Wood-species items (a-g species): boats, chest boats, bamboo rafts, doors,
signs and hanging signs; copper doors."""
import numpy as np

from ...engine import COPPER as COPPER_ID, IRON as IRON_ID, pal
from ...registry import register
from ...sprites import compose
from .common import CHAIN, COPPER, GOLD, IRON
from .a_lib import U, box, circ, dots, ell, inter, line, metal, minus, paint, poly, rod, spr

# ------------------------------------------------------------ bamboo raft

RAFT = pal("5a4a12", "8e7a22", "b8a032", "d6be4a", "ecd870")
RAFT_TIE = pal("2e3a0e", "4a5e18", "667e26")


def raft(ctx, chest=False):
    """Flat raft of bamboo poles lashed together, with a short paddle."""
    from . import h_wood as HW
    paddle = rod(ctx, [(3.4, 2.2), (9.4, 8.6)], 1.2, pal("4a3a10", "8e7a22", "b8a032", "d6be4a"))
    blade = spr(ctx, ell(ctx, 3.0, 2.4, 1.0, 1.8, -0.75), RAFT, bevel=1)
    layers = [paddle, blade]
    if chest:
        cm = box(ctx, 8.0, 4.0, 14.0, 9.0)
        c = spr(ctx, cm, HW.CHEST, bevel=1.5, smooth=0.25)
        paint(c, box(ctx, 9.0, 6.0, 13.0, 7.0), HW.CHEST[1])
        lt = spr(ctx, box(ctx, 10.0, 6.0, 12.0, 8.0), HW.LATCH, bevel=1, outline=False)
        lt.set_metal(lt.alpha, IRON_ID)
        layers += [c, lt]
    for i, y in enumerate((9.0, 11.0, 13.0)):
        m = box(ctx, 0.6 + (i % 2), y, 15.4 - (i % 2), y + 2.0)
        t = spr(ctx, m, RAFT, bevel=1, porosity=0.2, smooth=0.3)
        ring = ctx.edge(m, 1) > 0
        for x in (4.0 + i, 9.0 - i, 13.0):
            paint(t, box(ctx, x, y, x + 1, y + 2) * (~ring), RAFT[1])
        paint(t, box(ctx, 1.6, y + 0.0, 14.4, y + 1.0) * (~ring), RAFT[3])
        layers.append(t)
    layers.append(spr(ctx, U(box(ctx, 3.0, 8.4, 4.0, 15.4), box(ctx, 12.0, 8.4, 13.0, 15.4)), RAFT_TIE, bevel=1,
                      outline=False))
    return compose(ctx, *layers)


register("item/bamboo_raft", lambda ctx: raft(ctx))
register("item/bamboo_chest_raft", lambda ctx: raft(ctx, True))


# --------------------------------------------- boats / doors / signs
# The h-z wood module (h_wood) owns the shared silhouettes. Add the a-g species
# to its palette tables (new keys only; its own registrations ran already) and
# register our paths with its generators, so every species shares one design.
from . import h_wood as HW  # noqa: E402

MY_PLANKS = {  # same values as the block area's planks
    "acacia": pal("7b3a1f", "a2502c", "b25b33", "c0663b", "cc7144", "d77c4e"),
    "birch": pal("9a8a5e", "b8a777", "c6b583", "d2c28f", "ddce9b", "e6d9a7"),
    "cherry": pal("94675f", "bd8c83", "cc9a91", "d8a8a0", "e2b5ad", "eac0b9"),
    "dark_oak": pal("251709", "3e2914", "4a321b", "553b21", "604428", "6a4d30"),
    "bamboo": pal("7a6a26", "a6933a", "b8a444", "c7b34f", "d3c05a", "dccb66"),
    "crimson": pal("3e1524", "5c2136", "6d2840", "7c2f49", "8a3652", "963e5b"),
}
MY_BARK = {
    "acacia": pal("2e2b27", "433f39", "524e47", "605b53", "6d685f"),
    "birch": pal("26221e", "8a8478", "bdb8ad", "dedad1", "f5f3ee"),
    "cherry": pal("1a1014", "2c1c22", "38252b", "443036", "4f3a40"),
    "dark_oak": pal("150e07", "22180e", "2d2013", "372818", "41301d"),
    "bamboo": pal("3d5418", "55721f", "668826", "779b2e", "88ad37"),
    "crimson": pal("230c13", "3a1520", "4a1b28", "5a2230", "6a2939"),
}
MY_WINDOWS = {
    "acacia": [(7, 2), (8, 2), (6, 3), (9, 3), (7, 4), (8, 4), (7, 10), (8, 10), (6, 11), (9, 11), (7, 12), (8, 12)],
    "birch": [(x, y) for x in (6, 9) for y in (2, 3, 4, 5)],
    "cherry": [(7, 2), (8, 2), (6, 3), (9, 3), (6, 4), (9, 4), (6, 5), (9, 5)],
    "dark_oak": [(x, y) for x in (6, 7, 8, 9) for y in (3, 4)],
    "bamboo": [(x, y) for x in (5, 7, 9) for y in (2, 3, 4, 5)],
    "crimson": [(6, 2), (5, 3), (9, 3), (10, 4), (6, 10), (9, 11), (5, 12)],
}
for _w in MY_PLANKS:
    HW.PLANKS.setdefault(_w, MY_PLANKS[_w])
    HW.BARK.setdefault(_w, MY_BARK[_w])
    HW.WINDOWS.setdefault(_w, MY_WINDOWS[_w])
    register(f"item/{_w}_door", lambda ctx, w=_w: HW.door(ctx, w))
    register(f"item/{_w}_sign", lambda ctx, w=_w: HW.sign(ctx, w))
    register(f"item/{_w}_hanging_sign", lambda ctx, w=_w: HW.hanging_sign(ctx, w))
    if _w not in ("bamboo", "crimson"):
        register(f"item/{_w}_boat", lambda ctx, w=_w: HW.boat(ctx, w))
        register(f"item/{_w}_chest_boat", lambda ctx, w=_w: HW.boat(ctx, w, True))

register("item/copper_door", lambda ctx: HW.metal_door(ctx, COPPER, COPPER_ID, "cu"))
register("item/exposed_copper_door",
         lambda ctx: HW.metal_door(ctx, pal("5a3424", "8e5a42", "ae785c", "c49276", "d8ae92"), COPPER_ID, "ec",
                                   pal("4a4a3a", "7a7a62", "9a9a7c")))
