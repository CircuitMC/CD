"""Technical blocks: command blocks, structure / jigsaw / test blocks,
trial spawner, vault, spawner, heavy core and reinforced deepslate."""
import math

import numpy as np

from ...engine import IRON, Tex, pal
from ...materials import DEEPSLATE, layered
from .func_common import (DARK_IRON, IRON_P, M, bevel, bind, blank, cast_shadow, glyph, metal_surface,
                          paint, rectm, reg, ring, surface, texel_set, tone)

# ------------------------------------------------------------------ command blocks
CMD = {
    "": dict(body=pal("5a3a26", "7a5034", "9a6844", "b78055", "cf9a69", "e4b682"),
             light=pal("6a3a12", "c06a1e", "f39a36", "ffcf7a", "fff1cc")),
    "chain_": dict(body=pal("2c4a3c", "3c6450", "4f7f66", "64987c", "7cb193", "9ccaae"),
                   light=pal("1d5a33", "2e9a52", "52d07a", "a2f2b8", "e6fff0")),
    "repeating_": dict(body=pal("3a2c58", "4e3c74", "65508f", "7d67a9", "9781c0", "b5a0d8"),
                       light=pal("3d1e70", "6a38b8", "9c6af0", "cfaeff", "f2e8ff")),
}
SCREEN = pal("0b0f12", "121a1f", "1a252c")


def cmd_body(ctx, kind):
    p = CMD[kind]["body"]
    t = surface(ctx.sub(f"block/{kind}command_body"), p, salt="cmd", cell=6, lo=0.3, hi=0.75, smooth=0.45)
    # recessed panel seams forming a frame
    seam = ring(ctx, 2, 2, 14, 14)
    paint(t, seam, p[0], h=0.3)
    tone(t, ring(ctx, 3, 3, 13, 13) & (rectm(ctx, 3, 3, 13, 4) | rectm(ctx, 3, 3, 4, 13)), 1.15)
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16), lit=1.2, dark=0.7)
    for cx, cy in ((0, 0), (14, 0), (0, 14), (14, 14)):
        c = rectm(ctx, cx, cy, cx + 2, cy + 2)
        paint(t, c, ctx.palette(IRON_P[2:6], ctx.texel_noise("cc")), h=0.7, metal=IRON, smooth=0.6)
        paint(t, texel_set(ctx, [(cx, cy)]), IRON_P[6])
    return t


def pulse(ctx, k=0.0):
    return 0.5 + 0.5 * math.cos(2 * math.pi * (ctx.frame / max(1, ctx.frames) - k))


def cmd_arrow(ctx, t, kind, conditional=False):
    L = CMD[kind]["light"]
    track = rectm(ctx, 6, 3, 10, 13)
    paint(t, track, SCREEN[1], h=0.3)
    for i, y0 in enumerate((9, 6, 3)):
        chev = glyph(ctx, ["..##..", ".#..#.", "#....#"], 5, y0)
        chev &= rectm(ctx, 4, 0, 12, 16)
        b = pulse(ctx, i / 3)
        paint(t, chev, ctx.palette(L, 0.35 + b * 0.6), h=0.6, emissive=0.35 + b * 0.6)
    if conditional:
        notch = glyph(ctx, ["#....#", "######"], 5, 12)
        paint(t, notch, L[3], h=0.6, emissive=0.8)
    return t


def cmd_side(ctx, kind, conditional=False):
    t = cmd_body(ctx, kind)
    return cmd_arrow(ctx, t, kind, conditional)


def cmd_front(ctx, kind):
    t = cmd_body(ctx, kind)
    L = CMD[kind]["light"]
    scr = rectm(ctx, 3, 3, 13, 13)
    paint(t, scr, ctx.palette(SCREEN, ctx.texel_noise("scr") * 0.5 + (ctx.y - 3) / 20), h=0.35, smooth=0.9)
    bevel(ctx, t, scr, raised=False)
    prompt = glyph(ctx, ["#..", ".#.", "#.."], 4, 5)
    paint(t, prompt, L[3], emissive=0.9)
    rng = ctx.rng("cmdtext")
    for row, y in enumerate((5, 7, 9, 11)):
        n = int(rng.integers(2, 6)) if row else 4
        x0 = 8 if row == 0 else 4
        line = rectm(ctx, x0, y, min(12, x0 + n), y + 1)
        paint(t, line, L[2], emissive=0.6)
    if ctx.frame % 2 == 0:
        paint(t, rectm(ctx, 11, 11, 12, 12), L[4], emissive=1.0)
    return t


def cmd_back(ctx, kind):
    t = cmd_body(ctx, kind)
    L = CMD[kind]["light"]
    port = rectm(ctx, 5, 5, 11, 11)
    paint(t, port, ctx.palette(IRON_P[1:4], ctx.texel_noise("po")), h=0.4, metal=IRON)
    bevel(ctx, t, port, raised=False)
    core = rectm(ctx, 7, 7, 9, 9)
    b = pulse(ctx)
    paint(t, core, ctx.palette(L, 0.3 + b * 0.6), emissive=0.4 + b * 0.6, metal=0)
    for x, y in ((7, 3), (7, 12), (3, 7), (12, 7)):
        d = rectm(ctx, x, y, x + 2 if x == 7 else x + 1, y + 1 if x == 7 else y + 2)
        paint(t, d, L[1], h=0.45, emissive=0.3)
    return t


# ------------------------------------------------------------------ structure / jigsaw / test
STRUCT = pal("1f1a26", "2a2333", "362d41", "433850", "52455f", "64566f")
ICON = pal("8f86a0", "b2aac2", "d6d0e2", "f2eef8")


def struct_body(ctx, salt="sb"):
    t = surface(ctx.sub("block/structure_body"), STRUCT, salt=salt, cell=5, lo=0.25, hi=0.7, smooth=0.3)
    fr = ring(ctx, 0, 0, 16, 16, 1)
    paint(t, fr & (rectm(ctx, 0, 0, 16, 1) | rectm(ctx, 0, 0, 1, 16)), STRUCT[5], h=0.65)
    paint(t, fr & ~(rectm(ctx, 0, 0, 16, 1) | rectm(ctx, 0, 0, 1, 16)), STRUCT[0], h=0.3)
    # dashed inner guide
    dash = ring(ctx, 2, 2, 14, 14) & (((ctx.tx + ctx.ty) % 3) != 0)
    paint(t, dash, STRUCT[4], h=0.55)
    return t


def icon(ctx, t, rows, x0, y0, color=None, em=0.0):
    m = glyph(ctx, rows, x0, y0)
    c = ICON[2] if color is None else color
    paint(t, m, c, h=0.7, emissive=em)
    tone(t, M(ctx.edge(m, 1, "br")), 0.8)
    cast_shadow(ctx, t, m, 0.6)
    return t


ICONS = {
    "structure_block": ["#.#.#.", "......", "#....#", "......", "#....#", "......", ".#.#.#"],
    "structure_block_save": ["..##..", "..##..", "######", ".####.", "..##..", "#....#", "######"],
    "structure_block_load": ["..##..", ".####.", "######", "..##..", "..##..", "#....#", "######"],
    "structure_block_corner": ["####..", "#.....", "#.....", "#..##.", "...##.", "......", "......"],
    "structure_block_data": [".#..#.", "#....#", "#....#", "##..##", "#....#", "#....#", ".#..#."],
    "jigsaw_top": ["..##..", "..##..", "######", "######", "#.##.#", "..##..", ".####."],
    "jigsaw_side": ["..##..", ".####.", "##..##", "......", "..##..", ".####.", "##..##"],
    "jigsaw_lock": [".####.", "#....#", "#....#", "######", "##..##", "##..##", "######"],
    "test_block_accept": ["......", ".....#", "....##", "#..##.", "####..", ".##...", "......"],
    "test_block_fail": ["#....#", "##..##", ".####.", "..##..", ".####.", "##..##", "#....#"],
    "test_block_log": ["######", "......", "####..", "......", "#####.", "......", "###..."],
    "test_block_start": ["##....", "####..", "######", "######", "####..", "##....", "......"],
    "test_instance_block": [".####.", "..##..", "..##..", ".#..#.", "#....#", "######", ".####."],
}
ICON_COLORS = {
    "test_block_accept": (pal("6bdc6b")[0], 0.6), "test_block_fail": (pal("e04848")[0], 0.6),
    "test_block_log": (pal("e8d48a")[0], 0.3), "test_block_start": (pal("6ab8f0")[0], 0.6),
    "test_instance_block": (pal("b98cf0")[0], 0.4), "jigsaw_lock": (pal("d8b24a")[0], 0.0),
}


def struct_face(ctx, name):
    t = struct_body(ctx, name)
    col, em = ICON_COLORS.get(name, (None, 0.0))
    if name == "jigsaw_bottom":
        tone(t, rectm(ctx, 5, 5, 11, 11), 0.8)
        return t
    icon(ctx, t, ICONS[name], 5, 4, col, em)
    return t


# ------------------------------------------------------------------ trial spawner & vault
TS_BODY = pal("1d1f22", "2a2d31", "383c41", "474c52", "585e65", "6b7178")
TS_COPPER = pal("5a2f1c", "7d4429", "a05c37", "c27848", "dd9a65")
GLOW = {False: pal("6a2a08", "b8520e", "f08a22", "ffc25a", "fff0b8"),
        True: pal("0b3a4a", "13708a", "2ab4cc", "7ee8f2", "e0fdff")}


def ts_body(ctx, ominous, salt="ts"):
    p = TS_BODY if not ominous else pal("16191f", "20252d", "2b313b", "373e4a", "444c5a", "535c6c")
    t = surface(ctx.sub("block/trial_body"), p, salt=salt, cell=5, lo=0.25, hi=0.8, smooth=0.3)
    return t, p


def trial_side(ctx, active=False, ominous=False):
    t, p = ts_body(ctx, ominous)
    G = GLOW[ominous]
    fr = ring(ctx, 0, 0, 16, 16, 2)
    paint(t, fr, ctx.palette(p[2:], ctx.texel_noise("tf")), h=0.7)
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16))
    # copper corner plates
    for cx, cy in ((0, 0), (12, 0), (0, 12), (12, 12)):
        c = rectm(ctx, cx, cy, cx + 4, cy + 4) & fr
        paint(t, c, ctx.palette(TS_COPPER, 0.3 + ctx.texel_noise("tc") * 0.5), metal=IRON if False else 0,
              smooth=0.4)
    # cage bars (cut out)
    inner = rectm(ctx, 2, 2, 14, 14)
    bars_m = (rectm(ctx, 5, 2, 6, 14) | rectm(ctx, 10, 2, 11, 14) | rectm(ctx, 2, 7, 14, 9)) & inner
    paint(t, bars_m, ctx.palette(p[1:4], ctx.texel_noise("tb")), h=0.6)
    gap = inner & ~bars_m
    t.alpha[M(gap)] = 0
    t.color[M(gap)] *= 0.3
    t.wrap = False
    # eye lights on the cross bar
    eyes = rectm(ctx, 3, 7, 5, 9) | rectm(ctx, 11, 7, 13, 9) | rectm(ctx, 7, 7, 9, 9)
    if active:
        paint(t, eyes, ctx.palette(G[2:], ctx.texel_noise("ey")), emissive=0.95, h=0.7)
        paint(t, M(ctx.edge(fr, 1, "tl")) & ~rectm(ctx, 0, 0, 2, 2), G[1], emissive=0.3)
    else:
        paint(t, eyes, p[0], h=0.5)
    return t


def trial_top(ctx, state="inactive", ominous=False):
    t, p = ts_body(ctx, ominous, "tt")
    G = GLOW[ominous]
    fr = ring(ctx, 0, 0, 16, 16, 2)
    paint(t, fr, ctx.palette(p[2:], ctx.texel_noise("tf")), h=0.7)
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16))
    d = np.hypot(ctx.x - 8, ctx.y - 8)
    ring_m = (d < 5.4) & (d >= 3.4)
    paint(t, ring_m, ctx.palette(TS_COPPER, 0.3 + ctx.texel_noise("rg") * 0.5), h=0.65)
    bevel(ctx, t, ring_m)
    hole = d < (3.4 if state != "ejecting_reward" else 4.4)
    if state == "inactive":
        paint(t, hole, ctx.palette(p[:2], ctx.texel_noise("ho")), h=0.2)
    else:
        v = np.clip(1 - d / 4.4, 0, 1)
        bright = 0.35 if state == "active" else 0.6
        paint(t, hole, ctx.palette(G, bright + v * 0.4), h=0.3, emissive=0.6 + v * 0.4)
        if state == "active":
            paint(t, ring_m & (((ctx.tx + ctx.ty) % 4) == 0), G[3], emissive=0.8)
    for x in range(3, 13, 3):
        paint(t, rectm(ctx, x, 0, x + 1, 2) | rectm(ctx, x, 14, x + 1, 16), p[0], h=0.4)
    return t


def trial_bottom(ctx):
    t, p = ts_body(ctx, False, "tbm")
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16))
    tone(t, ring(ctx, 3, 3, 13, 13), 0.75)
    for cx, cy in ((1, 1), (14, 1), (1, 14), (14, 14)):
        paint(t, rectm(ctx, cx, cy, cx + 1, cy + 1), TS_COPPER[3])
    return t


VAULT = pal("23262a", "30343a", "3e434a", "4e545c", "60666f", "747b84")
VAULT_OM = pal("1a1e26", "252b36", "313949", "3e485a", "4d596d", "5e6b82")


def vault_body(ctx, ominous, salt):
    p = VAULT_OM if ominous else VAULT
    t = metal_surface(ctx.sub("block/vault_body"), p, salt=salt, metal=None, lo=0.25, hi=0.75, smooth=0.45)
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16), lit=1.25, dark=0.65)
    trim = ring(ctx, 1, 1, 15, 15)
    paint(t, trim, ctx.palette(TS_COPPER, 0.25 + ctx.texel_noise("vt") * 0.5), h=0.65)
    return t, p


def vault_front(ctx, state="off", ominous=False):
    t, p = vault_body(ctx, ominous, "vf")
    G = GLOW[ominous]
    door = rectm(ctx, 3, 3, 13, 13)
    paint(t, door, ctx.palette(p[1:4], ctx.texel_noise("vd")), h=0.45)
    bevel(ctx, t, door, raised=False)
    key = glyph(ctx, [".##.", "####", "####", ".##.", ".##.", ".##."], 6, 5)
    if state == "off":
        paint(t, key, pal("0c0d10")[0], h=0.1)
    elif state == "on":
        paint(t, key, ctx.palette(G[1:], ctx.texel_noise("vk")), h=0.2, emissive=0.9)
    else:
        mouthm = rectm(ctx, 4, 6, 12, 11)
        paint(t, mouthm, ctx.palette(G[2:], 0.3 + (ctx.y - 6) / 8), h=0.2, emissive=1.0)
        paint(t, rectm(ctx, 4, 5, 12, 6), p[0], h=0.3)
    for cx, cy in ((4, 4), (11, 4), (4, 11), (11, 11)):
        paint(t, rectm(ctx, cx, cy, cx + 1, cy + 1), p[5], h=0.7)
    return t


def vault_side(ctx, on=False, ominous=False):
    t, p = vault_body(ctx, ominous, "vs")
    G = GLOW[ominous]
    for y0 in (4, 9):
        slot = rectm(ctx, 3, y0, 13, y0 + 3)
        paint(t, slot, p[0], h=0.2)
        tone(t, rectm(ctx, 3, y0, 13, y0 + 1), 0.7)
        rune = slot & (((ctx.tx * 3 + ctx.ty) % 5) < 2) & rectm(ctx, 4, y0 + 1, 12, y0 + 2)
        paint(t, rune, G[3] if on else p[2], emissive=0.8 if on else 0)
    return t


def vault_top(ctx, ejecting=False, ominous=False):
    t, p = vault_body(ctx, ominous, "vtp")
    G = GLOW[ominous]
    grate = rectm(ctx, 4, 4, 12, 12)
    paint(t, grate, p[0], h=0.15)
    for x in (5, 7, 9):
        bar = rectm(ctx, x + 0.0, 4, x + 1, 12) if not ejecting else rectm(ctx, x, 4, x + 1, 5)
        paint(t, bar, p[3], h=0.5)
    if ejecting:
        inside = grate & ~rectm(ctx, 4, 4, 12, 5)
        d = np.hypot(ctx.x - 8, ctx.y - 8.5)
        paint(t, inside, ctx.palette(G, np.clip(1 - d / 5, 0, 1) * 0.6 + 0.3), emissive=0.9, h=0.25)
    return t


def vault_bottom(ctx, ominous=False):
    t, p = vault_body(ctx, ominous, "vb")
    tone(t, rectm(ctx, 5, 5, 11, 11), 0.8)
    return t


# ------------------------------------------------------------------ spawner, heavy core, reinforced deepslate
def spawner(ctx):
    t = blank(ctx)
    P = DARK_IRON
    fr = ring(ctx, 0, 0, 16, 16, 1)
    bars_m = fr | rectm(ctx, 5, 0, 6, 16) | rectm(ctx, 10, 0, 11, 16) | rectm(ctx, 0, 5, 16, 6) | \
        rectm(ctx, 0, 10, 16, 11)
    v = 0.45 + ctx.texel_noise("sp") * 0.3
    v = v + ((ctx.tx == 0) | (ctx.ty == 0)) * 0.25 - ((ctx.tx == 15) | (ctx.ty == 15)) * 0.2
    paint(t, bars_m, ctx.palette(P, np.clip(v, 0, 1)), h=0.7, alpha=1, metal=IRON, smooth=0.5)
    nodes = texel_set(ctx, [(x, y) for x in (0, 5, 10, 15) for y in (0, 5, 10, 15)])
    paint(t, nodes & bars_m, P[5], h=0.8)
    # diagonal braces in the corner cells
    for (x0, y0) in ((1, 1), (11, 11), (11, 1), (1, 11)):
        d = texel_set(ctx, [(x0 + i, y0 + (i if (x0 == y0) else 3 - i)) for i in range(4)])
        paint(t, d, P[2], h=0.6, alpha=1, metal=IRON)
    return t


def heavy_core(ctx):
    P = pal("1c1d22", "272930", "33363e", "40444d", "50555f", "646a75")
    t = metal_surface(ctx.sub("block/heavy_core"), P, salt="hc", lo=0.2, hi=0.7, brushed=False, smooth=0.5)
    for qx in (0, 8):
        for qy in (0, 8):
            q = rectm(ctx, qx, qy, qx + 8, qy + 8)
            bevel(ctx, t, q, lit=1.35, dark=0.6)
            core = rectm(ctx, qx + 3, qy + 3, qx + 5, qy + 5)
            paint(t, core, P[0], h=0.2)
            paint(t, rectm(ctx, qx + 2, qy + 2, qx + 6, qy + 3) | rectm(ctx, qx + 2, qy + 2, qx + 3, qy + 6),
                  P[1], h=0.35)
    return t


REIN = pal("6f6c63", "8a867b", "a29d90", "bbb6a8", "d2cdbf")


def reinforced(ctx, face="side"):
    t = layered(ctx.sub("block/reinforced_core"), DEEPSLATE, stretch=3 if face == "side" else 1, bands=3)
    fr = ring(ctx, 0, 0, 16, 16, 3) if face == "side" else ring(ctx, 0, 0, 16, 16, 2)
    g = ctx.noise(2, 2, 0.5, salt="rf")
    paint(t, fr, ctx.palette(REIN, 0.25 + g * 0.5), h=0.7, smooth=0.3)
    bevel(ctx, t, rectm(ctx, 0, 0, 16, 16), lit=1.15, dark=0.7)
    k = 3 if face == "side" else 2
    bevel(ctx, t, rectm(ctx, k, k, 16 - k, 16 - k), raised=False)
    if face == "side":
        for cx, cy in ((1, 1), (14, 1), (1, 14), (14, 14), (7, 1), (7, 14)):
            paint(t, rectm(ctx, cx, cy, cx + (2 if cx == 7 else 1), cy + 1), REIN[0], h=0.5)
        cross = rectm(ctx, 7, 3, 9, 13) if True else None
        paint(t, cross, ctx.palette(REIN[:3], g), h=0.6)
        bevel(ctx, t, cross)
    elif face == "top":
        c = rectm(ctx, 6, 6, 10, 10)
        paint(t, c, ctx.palette(REIN, 0.4 + g * 0.3), h=0.7)
        bevel(ctx, t, c)
        paint(t, rectm(ctx, 7, 7, 9, 9), pal("16282e")[0], h=0.3)
    else:
        tone(t, ring(ctx, 5, 5, 11, 11), 0.75)
    return t


# ------------------------------------------------------------------ registration
for _k in CMD:
    reg(f"block/{_k}command_block_side", bind(cmd_side, _k))
    reg(f"block/{_k}command_block_conditional", bind(cmd_side, _k, True))
    reg(f"block/{_k}command_block_front", bind(cmd_front, _k))
    reg(f"block/{_k}command_block_back", bind(cmd_back, _k))
for _n in ICONS:
    reg(f"block/{_n}", bind(struct_face, _n))
reg("block/jigsaw_bottom", bind(struct_face, "jigsaw_bottom"))
for _o, _suf in ((False, ""), (True, "_ominous")):
    reg(f"block/trial_spawner_side_active{_suf}", bind(trial_side, True, _o))
    reg(f"block/trial_spawner_side_inactive{_suf}", bind(trial_side, False, _o))
    reg(f"block/trial_spawner_top_active{_suf}", bind(trial_top, "active", _o))
    reg(f"block/trial_spawner_top_inactive{_suf}", bind(trial_top, "inactive", _o))
    reg(f"block/trial_spawner_top_ejecting_reward{_suf}", bind(trial_top, "ejecting_reward", _o))
    reg(f"block/vault_front_off{_suf}", bind(vault_front, "off", _o))
    reg(f"block/vault_front_on{_suf}", bind(vault_front, "on", _o))
    reg(f"block/vault_front_ejecting{_suf}", bind(vault_front, "ejecting", _o))
    reg(f"block/vault_side_off{_suf}", bind(vault_side, False, _o))
    reg(f"block/vault_side_on{_suf}", bind(vault_side, True, _o))
    reg(f"block/vault_top{_suf}", bind(vault_top, False, _o))
    reg(f"block/vault_top_ejecting{_suf}", bind(vault_top, True, _o))
    reg(f"block/vault_bottom{_suf}", bind(vault_bottom, _o))
reg("block/trial_spawner_bottom", trial_bottom)
reg("block/spawner", spawner)
reg("block/heavy_core", heavy_core)
reg("block/reinforced_deepslate_side", reinforced)
reg("block/reinforced_deepslate_top", bind(reinforced, "top"))
reg("block/reinforced_deepslate_bottom", bind(reinforced, "bottom"))
_ = Tex
