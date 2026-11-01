"""Status effect icons (mob_effect/*.png, 18x18): shaded vector sprites, one motif per effect."""
import math

import numpy as np

from ...engine import pal
from ...registry import register
from ...sprites import compose, flat, sprite

# palettes: outline, dark, mid, light, highlight
RED = pal("3a0a0a", "8c1414", "d4302a", "f0645a", "ffb0a0")
PINK = pal("4a0f2a", "a02a5a", "e05a90", "f59ac0", "ffd6e8")
GOLD = pal("3d2a04", "8a5f08", "d9a326", "f2cf5a", "fff2b0")
GREEN = pal("0f2a0a", "2f6b1e", "4fa83a", "86d460", "c8f5a0")
LIME = pal("1c2a06", "4f6b12", "86a52a", "b8d450", "e6f5a0")
BLUE = pal("0a1a3a", "1d4a8c", "3f7fd6", "7fb4f0", "c8e2ff")
CYAN = pal("06282c", "13636c", "2aa8b4", "6ad8e0", "c0f5f8")
PURPLE = pal("1e0a30", "4e2080", "7f4ac0", "b48ae8", "e2d0ff")
GRAY = pal("1c1d21", "4a4d54", "7a7d86", "a9adb6", "dfe2e8")
DARK = pal("0a0a0c", "1e1f24", "34363d", "4f525b", "7a7d86")
ORANGE = pal("3a1604", "8c3a0a", "e0701e", "f5a04a", "ffd8a0")
BROWN = pal("2a1606", "5a3418", "8a5a2e", "b8844e", "e0b47a")
WHITE = pal("4a4d54", "a9adb6", "d8dbe2", "eef0f4", "ffffff")
TEAL = pal("062a24", "136c5a", "2ab494", "6ae0c4", "c0fff0")


HEART_ROWS = {
    13: [".###...###.", "#####.#####", "###########", "###########", "###########", ".#########.",
         "..#######..", "...#####...", "....###....", ".....#....."],
    11: ["..##.##..", ".#######.", "#########", "#########", ".#######.", "..#####..", "...###...", "....#...."],
}


def heart_mask(ctx, cx=9, cy=9.5, s=1.0):
    rows = HEART_ROWS[13] if s >= 0.95 else HEART_ROWS[11]
    w, h = len(rows[0]), len(rows)
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2 + 0.5))
    m = ctx.zeros()
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch == "#":
                m = np.maximum(m, ctx.rect(x0 + i, y0 + j, x0 + i + 1, y0 + j + 1))
    return ctx.organic(m).astype(np.float32)


def drop_mask(ctx, cx=9, cy=10.5, r=5.0):
    return np.maximum(ctx.circle(cx, cy, r), ctx.polygon([(cx - r * 0.85, cy - r * 0.5), (cx, cy - r * 2.0),
                                                         (cx + r * 0.85, cy - r * 0.5)]))


def poly_line(ctx, pts, width):
    m = ctx.zeros()
    for (a, b) in zip(pts[:-1], pts[1:]):
        m = np.maximum(m, ctx.segment(a[0], a[1], b[0], b[1], width))
    return m


def arrow_up(ctx, cx, top, w=5.0, h=11.0):
    head = ctx.polygon([(cx - w, top + w), (cx, top), (cx + w, top + w)])
    shaft = ctx.rect(cx - w * 0.4, top + w - 0.5, cx + w * 0.4, top + h)
    return np.maximum(head, shaft)


def flipy(ctx, m):
    return m[::-1, :]


def skull_mask(ctx):
    head = ctx.circle(9, 8, 6.2)
    jaw = ctx.rect(5, 11, 13, 16)
    return np.maximum(head, jaw)


def skull(ctx, p, eye=(0.05, 0.05, 0.06)):
    base = sprite(ctx, skull_mask(ctx), p)
    eyes = np.maximum(ctx.rect(5.5, 7, 8, 10), ctx.rect(10, 7, 12.5, 10))
    teeth = ctx.rect(7, 14, 8, 16) + ctx.rect(10, 14, 11, 16)
    return compose(ctx, base, flat(ctx, eyes, eye), flat(ctx, np.clip(teeth, 0, 1), eye))


def pickaxe(ctx, p_head, p_handle):
    handle = ctx.segment(3.5, 15.5, 11.5, 7.5, 2.2)
    head = poly_line(ctx, [(4.5, 4.5), (8.5, 2.5), (12.5, 2.8), (15, 5.5), (15.5, 9.5)], 2.6)
    return compose(ctx, sprite(ctx, handle, p_handle), sprite(ctx, head, p_head))


def sword(ctx, p_blade, broken=False):
    blade = ctx.polygon([(14.5, 2.5), (16, 2.5 + 0), (16, 4), (7.5, 12.5), (5.5, 10.5)])
    if broken:
        blade = blade * (1 - ctx.polygon([(9, 5), (14, 10), (12, 12), (10.5, 8.5), (7, 7)]))
    guard = ctx.segment(4, 9.5, 8.5, 14, 2)
    grip = ctx.segment(2.5, 15.5, 6, 12, 2)
    return compose(ctx, sprite(ctx, grip, BROWN), sprite(ctx, guard, GOLD), sprite(ctx, blade, p_blade))


def eye(ctx, p_iris, closed=False):
    white = np.maximum(ctx.polygon([(1.5, 9), (5, 5), (13, 5), (16.5, 9), (13, 13), (5, 13)]), 0)
    if closed:
        lid = sprite(ctx, white, DARK)
        line = ctx.rect(2, 8.5, 16, 10)
        return compose(ctx, lid, flat(ctx, line, (0.02, 0.02, 0.03)))
    base = sprite(ctx, white, WHITE)
    iris = sprite(ctx, ctx.circle(9, 9, 3.4), p_iris, outline=False)
    pupil = flat(ctx, ctx.circle(9, 9, 1.4), (0.03, 0.03, 0.05))
    return compose(ctx, base, iris, pupil)


def shield_mask(ctx):
    return ctx.polygon([(3, 3), (15, 3), (15, 9), (9, 16), (3, 9)])


def clover(ctx, p):
    m = ctx.zeros()
    for (dx, dy) in ((-2.6, -2.6), (2.6, -2.6), (-2.6, 2.6), (2.6, 2.6)):
        m = np.maximum(m, ctx.circle(9 + dx, 8 + dy, 3.1))
    stem = ctx.segment(9, 9, 12.5, 16.5, 1.4)
    return np.maximum(m, stem)


def swirl(ctx, turns=2.2, r0=7.5, width=1.8, cx=9, cy=9):
    pts = []
    for k in range(60):
        t = k / 59
        a = t * turns * 2 * math.pi
        r = r0 * (1 - t) + 0.8
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return poly_line(ctx, pts, width)


def sparkle(ctx, x, y, r=2.0):
    return np.maximum(ctx.rect(x - 0.5, y - r, x + 0.5, y + r + 0.01), ctx.rect(x - r, y - 0.5, x + r + 0.01, y + 0.5))


def feather(ctx):
    vane = ctx.polygon([(15, 1.5), (16.5, 3.5), (14, 9), (8, 13.5), (4, 14), (5, 9), (9, 4.5)])
    quill = ctx.segment(2.5, 15.5, 12, 6, 1.0)
    return vane, quill


# ----------------------------------------------------------------- effects
def e_absorption(ctx):
    ring = ctx.circle(9, 9, 8.6) * (1 - ctx.circle(9, 9, 7.2))
    return compose(ctx, sprite(ctx, ring, GOLD, outline=False), sprite(ctx, heart_mask(ctx, s=0.85), GOLD))


def ominous_banner(ctx, p):
    pole = ctx.rect(3, 1, 15, 3)
    cloth = ctx.polygon([(4, 3), (14, 3), (14, 15), (9, 12.5), (4, 15)])
    face = np.maximum(ctx.rect(6, 6, 8, 8), ctx.rect(10, 6, 12, 8)) + ctx.rect(7, 9.5, 11, 10.5)
    return compose(ctx, sprite(ctx, pole, BROWN), sprite(ctx, cloth, p), flat(ctx, np.clip(face, 0, 1), (0.05, 0.05, 0.06)))


def e_bad_omen(ctx):
    return ominous_banner(ctx, GRAY)


def e_raid_omen(ctx):
    return ominous_banner(ctx, RED)


def e_trial_omen(ctx):
    return ominous_banner(ctx, TEAL)


def e_blindness(ctx):
    return eye(ctx, DARK, closed=True)


def e_night_vision(ctx):
    return compose(ctx, eye(ctx, BLUE), flat(ctx, sparkle(ctx, 14.5, 3.5, 2.0), (1, 1, 0.8)))


def e_breath(ctx):
    shell = ctx.circle(9, 10, 6.5)
    s = sprite(ctx, shell, pal("2a1a10", "8a5a3a", "c8946a", "e8c49a", "fff0d8"))
    sw = flat(ctx, swirl(ctx, 1.6, 5.0, 1.2, 9, 10), (0.45, 0.26, 0.16))
    bub = sprite(ctx, np.maximum(ctx.circle(14.5, 3, 1.6), ctx.circle(11.5, 2, 1.0)), BLUE, outline=False)
    return compose(ctx, s, sw, bub)


def e_conduit(ctx):
    frame = ctx.rect(2.5, 2.5, 15.5, 15.5) * (1 - ctx.rect(5, 5, 13, 13))
    core = sprite(ctx, ctx.circle(9, 9, 3.6), CYAN)
    return compose(ctx, sprite(ctx, frame, BROWN), core, flat(ctx, ctx.circle(9, 9, 1.2), (0.05, 0.1, 0.15)))


def e_darkness(ctx):
    orb = sprite(ctx, ctx.circle(9, 9, 7.5), DARK)
    sw = flat(ctx, swirl(ctx, 1.8, 6.0, 1.2), (0.25, 0.75, 0.8))
    return compose(ctx, orb, sw)


def e_dolphin(ctx):
    body = ctx.polygon([(2, 12), (6, 7), (11, 5.5), (16, 6.5), (13, 9), (8, 11), (4, 14)])
    fin = ctx.polygon([(9, 6), (11, 2), (12, 6)])
    tail = ctx.polygon([(2, 12), (1, 16), (5, 13.5)])
    return compose(ctx, sprite(ctx, np.maximum(np.maximum(body, fin), tail), BLUE))


def flame_mask(ctx, cx=9, by=16):
    outer = np.maximum(ctx.circle(cx, by - 4.5, 4.6), ctx.polygon([(cx - 4.5, by - 5), (cx - 1, by - 15),
                                                                   (cx + 1.5, by - 10), (cx + 4.5, by - 5)]))
    return outer


def e_fire_res(ctx):
    sh = sprite(ctx, shield_mask(ctx), GRAY)
    fl = sprite(ctx, flame_mask(ctx, 9, 14) * ctx.rect(4, 3, 14, 14), ORANGE)
    return compose(ctx, sh, fl)


def e_glowing(ctx):
    pts = []
    for k in range(10):
        r = 8 if k % 2 == 0 else 3.6
        a = -math.pi / 2 + k * math.pi / 5
        pts.append((9 + r * math.cos(a), 9.5 + r * math.sin(a)))
    return sprite(ctx, ctx.polygon(pts), GOLD)


def e_haste(ctx):
    lines = np.maximum(ctx.rect(1, 3, 4, 4), ctx.rect(1, 6, 3, 7))
    return compose(ctx, pickaxe(ctx, GOLD, BROWN), flat(ctx, lines, (1, 0.9, 0.5)))


def e_mining_fatigue(ctx):
    arrow = flipy(ctx, arrow_up(ctx, 14.5, 1.5, 3, 8))
    return compose(ctx, pickaxe(ctx, DARK, BROWN), sprite(ctx, arrow, BLUE))


def e_health_boost(ctx):
    plus = np.maximum(ctx.rect(12, 1, 15, 8), ctx.rect(10, 3, 17, 6))
    return compose(ctx, sprite(ctx, heart_mask(ctx, 8, 10.5, 0.85), RED), sprite(ctx, plus, GOLD))


def e_hero(ctx):
    gem = ctx.polygon([(9, 2), (14, 7), (14, 11), (9, 16), (4, 11), (4, 7)])
    return compose(ctx, sprite(ctx, gem, GREEN), flat(ctx, ctx.rect(7, 6, 8, 9), (0.85, 1, 0.85)))


def e_hunger(ctx):
    meat = ctx.circle(11, 7, 5.2)
    bone = np.maximum(ctx.segment(3.5, 14.5, 8, 10, 2.0), np.maximum(ctx.circle(2.8, 13.5, 1.4), ctx.circle(4.5, 15.5, 1.4)))
    return compose(ctx, sprite(ctx, bone, WHITE), sprite(ctx, meat, LIME))


def e_saturation(ctx):
    meat = ctx.circle(11, 7, 5.2)
    bone = np.maximum(ctx.segment(3.5, 14.5, 8, 10, 2.0), np.maximum(ctx.circle(2.8, 13.5, 1.4), ctx.circle(4.5, 15.5, 1.4)))
    return compose(ctx, sprite(ctx, bone, WHITE), sprite(ctx, meat, ORANGE))


def e_infested(ctx):
    body = np.maximum(np.maximum(ctx.circle(5, 10, 3), ctx.circle(9, 9, 3.4)), ctx.circle(13, 10, 2.6))
    legs = ctx.zeros()
    for x in (5, 9, 13):
        legs = np.maximum(legs, ctx.rect(x - 0.5, 12, x + 0.5, 15))
    return compose(ctx, flat(ctx, legs, (0.25, 0.26, 0.3)), sprite(ctx, body, GRAY))


def e_instant_damage(ctx):
    crack = poly_line(ctx, [(9, 4), (7.5, 7.5), (10.5, 10), (8.5, 15)], 1.2)
    return compose(ctx, sprite(ctx, heart_mask(ctx), pal("1a0404", "4a0a0a", "7a1414", "a02a24", "c85a50")),
                   flat(ctx, crack, (0.05, 0.02, 0.02)))


def e_instant_health(ctx):
    return compose(ctx, sprite(ctx, heart_mask(ctx), RED), flat(ctx, sparkle(ctx, 14.5, 3.5, 2), (1, 1, 1)))


def e_invisibility(ctx):
    m = np.maximum(ctx.circle(9, 5, 3.2), ctx.rect(5, 9, 13, 16.5))
    dots = (((ctx.tx + ctx.ty) % 2) == 0).astype(np.float32)
    edge = ctx.edge(m, 1.0)
    return compose(ctx, flat(ctx, m * dots * 0 + edge * dots, (0.85, 0.88, 0.95)), flat(ctx, m * (1 - edge) * dots * 0.0, (1, 1, 1)))


def e_jump(ctx):
    spring = poly_line(ctx, [(5, 16), (13, 14.5), (5, 13), (13, 11.5)], 1.3)
    return compose(ctx, sprite(ctx, spring, GRAY, outline=False), sprite(ctx, arrow_up(ctx, 9, 1, 5, 10), GREEN))


def e_levitation(ctx):
    a1 = arrow_up(ctx, 5.5, 3, 3.5, 13)
    a2 = arrow_up(ctx, 12.5, 1, 3.5, 11)
    return compose(ctx, sprite(ctx, a1, PURPLE), sprite(ctx, a2, PURPLE))


def e_luck(ctx):
    return sprite(ctx, clover(ctx, GREEN), GREEN)


def e_unluck(ctx):
    m = clover(ctx, DARK) * (1 - ctx.polygon([(9, 2), (10, 2), (8, 9), (11, 15), (10, 15), (7, 9)]))
    return sprite(ctx, m, pal("101208", "2a2e1a", "4a4f30", "6b7048", "8f9468"))


def e_nausea(ctx):
    return compose(ctx, sprite(ctx, ctx.circle(9, 9, 7.6), LIME), flat(ctx, swirl(ctx, 2.0, 6.0, 1.3), (0.2, 0.3, 0.06)))


def e_oozing(ctx):
    blob = np.maximum(ctx.circle(9, 11, 5.5), ctx.circle(6, 8, 3))
    drip = ctx.circle(14, 15, 1.4)
    t = sprite(ctx, np.maximum(blob, drip), GREEN)
    eyes = np.maximum(ctx.rect(6.5, 9, 8, 11), ctx.rect(10.5, 9, 12, 11))
    return compose(ctx, t, flat(ctx, eyes, (0.08, 0.2, 0.05)))


def e_poison(ctx):
    d = sprite(ctx, drop_mask(ctx), LIME)
    s = np.maximum(ctx.rect(7, 10, 8, 12), ctx.rect(10, 10, 11, 12))
    return compose(ctx, d, flat(ctx, s, (0.15, 0.22, 0.04)), flat(ctx, ctx.rect(7.5, 13, 10.5, 14), (0.15, 0.22, 0.04)))


def e_regeneration(ctx):
    ring = swirl(ctx, 0.85, 7.6, 1.4) * (ctx.circle(9, 9, 9))
    return compose(ctx, sprite(ctx, ring, PINK, outline=False), sprite(ctx, heart_mask(ctx, 9, 10, 0.7), PINK))


def e_resistance(ctx):
    sh = sprite(ctx, shield_mask(ctx), GRAY)
    cross = np.maximum(ctx.rect(8, 5, 10, 13), ctx.rect(5.5, 7, 12.5, 9))
    return compose(ctx, sh, flat(ctx, cross, (0.85, 0.2, 0.18)))


def e_slow_falling(ctx):
    vane, quill = feather(ctx)
    return compose(ctx, sprite(ctx, vane, WHITE), flat(ctx, quill, (0.55, 0.57, 0.62)))


def e_slowness(ctx):
    shell = ctx.circle(10.5, 9, 5.5)
    foot = ctx.rect(2, 13, 16, 15.5)
    head = ctx.circle(3.5, 11.5, 2)
    s = compose(ctx, sprite(ctx, np.maximum(foot, head), GRAY), sprite(ctx, shell, BLUE),
                flat(ctx, swirl(ctx, 1.4, 4.0, 1.0, 10.5, 9), (0.1, 0.2, 0.4)))
    return s


def e_speed(ctx):
    boot = ctx.polygon([(7, 2), (12, 2), (12, 10), (16.5, 12), (16.5, 15.5), (7, 15.5)])
    lines = np.maximum(np.maximum(ctx.rect(1, 6, 5, 7), ctx.rect(2, 9, 6, 10)), ctx.rect(1, 12, 5, 13))
    return compose(ctx, sprite(ctx, boot, CYAN), flat(ctx, lines, (0.8, 0.95, 1)))


def e_strength(ctx):
    return sword(ctx, RED)


def e_weakness(ctx):
    return sword(ctx, GRAY, broken=True)


def e_water_breathing(ctx):
    a = sprite(ctx, ctx.circle(7, 11, 4.5), BLUE)
    b = sprite(ctx, ctx.circle(13, 6, 3), BLUE)
    c = sprite(ctx, ctx.circle(13.5, 13.5, 2.2), BLUE)
    hl = np.maximum(ctx.rect(5, 8, 7, 10), ctx.rect(12, 4, 13, 5))
    return compose(ctx, a, b, c, flat(ctx, hl, (1, 1, 1)))


def e_weaving(ctx):
    m = ctx.zeros()
    for k in range(4):
        a = k * math.pi / 4
        m = np.maximum(m, ctx.segment(9 - 8 * math.cos(a), 9 - 8 * math.sin(a), 9 + 8 * math.cos(a), 9 + 8 * math.sin(a), 1.0))
    for r in (3, 6):
        m = np.maximum(m, ctx.circle(9, 9, r + 0.5) * (1 - ctx.circle(9, 9, r - 0.5)))
    return flat(ctx, m, (0.88, 0.9, 0.94))


def e_wind_charged(ctx):
    s1 = swirl(ctx, 1.3, 6.5, 1.6)
    tail = ctx.rect(1, 15, 12, 16.3)
    return compose(ctx, sprite(ctx, np.maximum(s1, tail), pal("2a3a5a", "6a8ac0", "a6c4ec", "d4e6ff", "ffffff"), outline=True))


def e_wither(ctx):
    return skull(ctx, DARK, eye=(0.55, 0.55, 0.6))


EFFECTS = {
    "absorption": e_absorption, "bad_omen": e_bad_omen, "blindness": e_blindness,
    "breath_of_the_nautilus": e_breath, "conduit_power": e_conduit, "darkness": e_darkness,
    "dolphins_grace": e_dolphin, "fire_resistance": e_fire_res, "glowing": e_glowing, "haste": e_haste,
    "health_boost": e_health_boost, "hero_of_the_village": e_hero, "hunger": e_hunger, "infested": e_infested,
    "instant_damage": e_instant_damage, "instant_health": e_instant_health, "invisibility": e_invisibility,
    "jump_boost": e_jump, "levitation": e_levitation, "luck": e_luck, "mining_fatigue": e_mining_fatigue,
    "nausea": e_nausea, "night_vision": e_night_vision, "oozing": e_oozing, "poison": e_poison,
    "raid_omen": e_raid_omen, "regeneration": e_regeneration, "resistance": e_resistance,
    "saturation": e_saturation, "slow_falling": e_slow_falling, "slowness": e_slowness, "speed": e_speed,
    "strength": e_strength, "trial_omen": e_trial_omen, "unluck": e_unluck, "water_breathing": e_water_breathing,
    "weakness": e_weakness, "weaving": e_weaving, "wind_charged": e_wind_charged, "wither": e_wither,
}


def _wrap(fn):
    def g(ctx):
        t = fn(ctx)
        t.grain = 0
        return t
    return g


for _n, _fn in EFFECTS.items():
    register(f"mob_effect/{_n}", _wrap(_fn), pbr=False)
