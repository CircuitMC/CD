"""Tools and weapons (items a-g): copper / diamond / golden tool sets, spears,
bows, crossbows, arrows, fishing rods, brush, flint and steel."""
import numpy as np

from ...engine import COPPER as COPPER_ID, GOLD as GOLD_ID, IRON as IRON_ID, pal
from ...registry import register, texture
from ...sprites import compose
from .common import COPPER, DIAMOND, GOLD, IRON, STRING, WOOD
from .a_lib import (Diag, U, arc_pts, bez_pts, box, darker, circ, curve, dots, line, metal, minus, paint, poly, rod, spr,
                    stroke)

FLINT = pal("1f1f22", "38383d", "55555b", "727279", "8e8e96")
FEATHER = pal("8a8a8a", "c4c4c4", "e6e6e6", "fafafa")

MATS = {
    "copper": dict(p=COPPER, metal=COPPER_ID, smooth=0.6),
    "diamond": dict(p=DIAMOND, metal=None, smooth=0.9, f0=0.17),
    "golden": dict(p=GOLD, metal=GOLD_ID, smooth=0.75),
}

D = Diag(1.5, 14.5)  # tools: handle bottom-left, head top-right


def head_layer(ctx, mask, mat, **kw):
    m = MATS[mat]
    t = spr(ctx, mask, m["p"], smooth=m["smooth"], f0=m.get("f0", 0.04), **kw)
    if m["metal"]:
        t.set_metal(mask, m["metal"])
    return t


def handle(ctx, u0, u1, w=1.5, d=D):
    return rod(ctx, [d.p(u0, 0), d.p(u1, 0)], w, WOOD, outline=False, porosity=0.2)


def handle_end(ctx, u, d=D):
    """Darker butt cap texel at the end of a handle."""
    return spr(ctx, d.seg(ctx, u, u + 0.6, 1.6), WOOD[:3], outline=False, bevel=1)


def glint_line(ctx, t, pts, rgb, w=0.8):
    paint(t, line(ctx, pts, w), rgb)


# ------------------------------------------------------------------ tools

def sword(ctx, mat):
    p = MATS[mat]["p"]
    d = Diag(5.0, 11.0)
    blade = d.poly(ctx, [(0.4, -1.5), (9.2, -1.5), (11.4, 0), (9.2, 1.5), (0.4, 1.5)])
    guard = d.rect(ctx, -1.0, -3.4, 0.7, 3.4)
    t_blade = head_layer(ctx, blade, mat)
    glint_line(ctx, t_blade, [d.p(1.4, -0.4), d.p(9.0, -0.4)], p[4], 0.7)
    t_guard = spr(ctx, guard, darker(p, 1), bevel=1, smooth=0.5)
    metal(t_guard, guard, MATS[mat]["metal"])
    grip = handle(ctx, -4.4, -0.8, 1.6, d)
    pm = d.rect(ctx, -5.6, -1.1, -4.0, 1.1)
    pommel = spr(ctx, pm, darker(p, 1), bevel=1)
    metal(pommel, pm, MATS[mat]["metal"])
    return compose(ctx, grip, t_blade, t_guard, pommel)


def pickaxe(ctx, mat):
    p = MATS[mat]["p"]
    head = U(D.curve(ctx, (9.6, -6.6), (15.6, 0), (9.6, 6.6), 1.5, 1.5),
             D.curve(ctx, (11.2, -4.0), (14.2, 0), (11.2, 4.0), 2.6, 2.6))
    t = head_layer(ctx, head, mat)
    glint_line(ctx, t, [D.p(10.4, -5.0), D.p(12.6, -2.2)], p[4], 0.7)
    return compose(ctx, handle(ctx, 0, 12.0), t)


def axe(ctx, mat):
    p = MATS[mat]["p"]
    head = D.poly(ctx, [(9.0, 0.9), (13.3, 0.9), (13.9, -1.4), (15.0, -3.6), (14.2, -5.6), (11.6, -5.0),
                        (9.0, -5.6), (8.0, -3.6), (9.2, -1.4)])
    t = head_layer(ctx, head, mat)
    glint_line(ctx, t, [D.p(9.2, -4.4), D.p(11.4, -3.9)], p[4], 0.7)
    return compose(ctx, handle(ctx, 0, 13.0), t)


def shovel(ctx, mat):
    p = MATS[mat]["p"]
    head = D.poly(ctx, [(10.0, -1.0), (10.6, -2.5), (13.6, -2.6), (15.6, -1.4), (16.6, 0), (15.6, 1.4),
                        (13.6, 2.6), (10.6, 2.5), (10.0, 1.0)])
    t = head_layer(ctx, head, mat)
    glint_line(ctx, t, [D.p(11.2, -1.4), D.p(14.6, -1.2)], p[4], 0.7)
    neck = head_layer(ctx, D.rect(ctx, 8.6, -0.9, 10.4, 0.9), mat, bevel=1)
    return compose(ctx, handle(ctx, 0, 9.4), neck, t)


def hoe(ctx, mat):
    p = MATS[mat]["p"]
    head = D.poly(ctx, [(11.0, 1.0), (13.4, 1.0), (13.4, -4.4), (12.6, -5.6), (8.6, -5.6), (8.6, -3.8),
                        (11.0, -3.8)])
    t = head_layer(ctx, head, mat)
    glint_line(ctx, t, [D.p(12.2, 0.0), D.p(12.2, -3.8)], p[4], 0.7)
    return compose(ctx, handle(ctx, 0, 12.4), t)


def spear(ctx, mat):
    p = MATS[mat]["p"]
    d = Diag(1.0, 15.0)
    shaft = handle(ctx, 0.2, 13.5, 1.4, d)
    headm = d.poly(ctx, [(12.6, 0), (14.0, -1.7), (17.2, -1.2), (20.4, 0), (17.2, 1.2), (14.0, 1.7)])
    t = head_layer(ctx, headm, mat)
    glint_line(ctx, t, [d.p(14.0, -0.6), d.p(18.4, -0.3)], p[4], 0.6)
    collar = head_layer(ctx, d.rect(ctx, 11.0, -1.0, 12.8, 1.0), mat, bevel=1)
    wrap = spr(ctx, d.rect(ctx, 4.0, -0.95, 6.4, 0.95), pal("3a2416", "5c3a22", "7c5232", "966a44"), bevel=1)
    return compose(ctx, shaft, wrap, collar, t)


def reg_tools():
    for mat in MATS:
        for kind, fn in (("sword", sword), ("pickaxe", pickaxe), ("axe", axe), ("shovel", shovel),
                         ("hoe", hoe), ("spear", spear)):
            register(f"item/{mat}_{kind}", lambda ctx, f=fn, m=mat: f(ctx, m))
        # in-hand spear is a 32x32 sprite: the same design at double detail
        register(f"item/{mat}_spear_in_hand", lambda ctx, m=mat: spear(ctx, m))


reg_tools()


# ------------------------------------------------------------------ bows

BOW_WOOD = pal("3a2410", "5e3c1c", "84572b", "a8773e", "c79a5a")
GRIP = pal("2a1a10", "4a3020", "6a4630", "835b3e")
BD = Diag(8.0, 8.0)  # centre frame for bows


def bow_body(ctx, bend=0.0):
    """Limbs: circular arc bulging toward the top-right corner."""
    import math
    c = -3.2 + bend * 1.2          # arc centre on the u axis
    half = 7.0 - bend * 0.5        # tip offset along v
    r = math.hypot(c, half)
    a = math.degrees(math.atan2(half, -c))
    pts = [BD.p(c + r * math.cos(math.radians(t)), r * math.sin(math.radians(t)))
           for t in np.linspace(-a, a, 25)]
    limbs = U(stroke(ctx, pts[:13], 1.2, 1.9), stroke(ctx, pts[12:], 1.9, 1.2))
    t = spr(ctx, limbs, BOW_WOOD, bevel=1, porosity=0.2)
    apex = c + r
    gm = BD.rect(ctx, apex - 1.4, -1.3, apex + 0.6, 1.3)
    grip = spr(ctx, gm, GRIP, bevel=1)
    return t, grip, pts[0], pts[-1], apex


def string(ctx, pts):
    return rod(ctx, pts, 0.8, STRING, outline=False)


ARROWHEAD = pal("26262a", "44444a", "66666e", "8e8e98")


def arrow_layer(ctx, d, u0, u1, head_p=ARROWHEAD):
    """Arrow along frame d from u0 (nock) to u1 (tip): [fletching, shaft, head] layers."""
    shaft = rod(ctx, [d.p(u0 + 0.6, 0), d.p(u1 - 2.0, 0)], 1.5, WOOD, outline=False)
    hm = d.poly(ctx, [(u1 - 3.4, -2.1), (u1, 0), (u1 - 3.4, 2.1), (u1 - 2.6, 0)])
    head = spr(ctx, hm, head_p, bevel=1, outline=False)
    paint(head, ctx.edge(hm, 1, "br") > 0, head_p[0])
    fl = d.poly(ctx, [(u0, -2.6), (u0 + 2.6, -2.6), (u0 + 5.0, 0), (u0 + 2.6, 2.6), (u0, 2.6), (u0 + 2.4, 0)])
    fletch = spr(ctx, fl, FEATHER, bevel=1, outline=False)
    return [fletch, shaft, head]


def bow(ctx, pull=-1):
    bend = 0.0 if pull < 0 else (0.3, 0.65, 1.0)[pull]
    limbs, grip, a, b, apex = bow_body(ctx, bend)
    if pull < 0:
        return compose(ctx, string(ctx, [a, b]), limbs, grip)
    back = (1.6, 3.0, 4.2)[pull]
    q = BD.p(-back, 0)
    arr = arrow_layer(ctx, BD, -back - 0.6, apex + 3.6 - back * 0.3)
    return compose(ctx, string(ctx, [a, q, b]), limbs, *arr[:2], grip, arr[2])


register("item/bow", lambda ctx: bow(ctx))
for _i in range(3):
    register(f"item/bow_pulling_{_i}", lambda ctx, i=_i: bow(ctx, i))


# ------------------------------------------------------------- crossbow

CD = Diag(1.6, 14.4)
STOCK = pal("2e1c0e", "4e321a", "6f4a28", "8f6338", "aa7c4a")


def crossbow(ctx, state):
    """state: 'standby' | 0 | 1 | 2 | 'arrow' | 'firework'."""
    sm = U(CD.rect(ctx, 0.0, -1.1, 13.4, 1.1), CD.rect(ctx, 0.0, -1.6, 3.4, 1.6))
    stock = spr(ctx, sm, STOCK, bevel=1, porosity=0.2)
    flex = {"standby": 0.0, 0: 0.35, 1: 0.7}.get(state, 1.0)
    tip_u, tip_v = 9.0 - flex * 1.4, 6.6 - flex * 0.6
    l_tip, r_tip = CD.p(tip_u, -tip_v), CD.p(tip_u, tip_v)
    prod_m = curve(ctx, l_tip, CD.p(13.6 + flex * 0.6, 0), r_tip, 1.7, 1.7)
    prod = spr(ctx, prod_m, pal("3a2410", "84572b", "a8773e", "c79a5a"), bevel=1, porosity=0.2)
    cm = U(circ(ctx, *l_tip, 1.05), circ(ctx, *r_tip, 1.05))
    caps = spr(ctx, cm, IRON, bevel=1)
    metal(caps, cm, IRON_ID)
    mm = CD.rect(ctx, 10.0, -1.5, 12.2, 1.5)
    mount = spr(ctx, mm, IRON, bevel=1)
    metal(mount, mm, IRON_ID)
    q_u = {"standby": tip_u, 0: 7.0, 1: 5.4}.get(state, 4.2)
    s = rod(ctx, [l_tip, CD.p(q_u, 0), r_tip], 0.8, pal("4a4a4a", "7a7a7a", "a4a4a4"))
    layers = [stock, s, prod, mount]
    if state == "arrow":
        layers += arrow_layer(ctx, CD, 4.0, 18.6)
    elif state == "firework":
        body = spr(ctx, CD.rect(ctx, 5.6, -1.4, 13.6, 1.4), pal("5a1010", "9a2020", "c83a30", "e86050"), bevel=1)
        cone = spr(ctx, CD.poly(ctx, [(13.4, -1.6), (17.0, 0), (13.4, 1.6)]), pal("23234a", "36369a", "5a5ad0"),
                   bevel=1)
        band = spr(ctx, CD.rect(ctx, 8.6, -1.45, 9.6, 1.45), pal("6a5a20", "d8c060", "f8e8a0"), bevel=1)
        layers += [body, band, cone]
    return compose(ctx, *layers)


register("item/crossbow_standby", lambda ctx: crossbow(ctx, "standby"))
register("item/crossbow_arrow", lambda ctx: crossbow(ctx, "arrow"))
register("item/crossbow_firework", lambda ctx: crossbow(ctx, "firework"))
for _i in range(3):
    register(f"item/crossbow_pulling_{_i}", lambda ctx, i=_i: crossbow(ctx, i))


# ---------------------------------------------------------------- arrow

@texture("item/arrow")
def arrow(ctx):
    return compose(ctx, *arrow_layer(ctx, Diag(2.0, 14.0), 0.6, 16.9))


# ---------------------------------------------------------- fishing rods

ROD_PTS = [(2.0, 14.6), (5.0, 11.0), (8.4, 7.2), (11.6, 4.0), (14.0, 1.8)]


def rod_layers(ctx):
    r = rod(ctx, ROD_PTS, 1.5, WOOD, porosity=0.2)
    grip = rod(ctx, ROD_PTS[:2], 1.9, pal("2a1a10", "4a3020", "6a4630", "835b3e"))
    reel = spr(ctx, circ(ctx, 5.6, 11.6, 1.3), IRON, bevel=1)
    reel.set_metal(reel.alpha, IRON_ID)
    return [r, grip, reel]


def fishing_rod(ctx, cast=False):
    layers = rod_layers(ctx)
    if not cast:
        s = rod(ctx, [(14.2, 2.0), (14.4, 9.0), (13.8, 12.2)], 0.8, STRING)
        hook = spr(ctx, U(line(ctx, [(13.6, 11.6), (13.6, 13.8), (12.3, 14.4), (11.6, 13.2)], 0.9)),
                   IRON, outline=False, bevel=1)
        hook.set_metal(hook.alpha, IRON_ID)
        layers += [s, hook]
    return compose(ctx, *layers)


register("item/fishing_rod", lambda ctx: fishing_rod(ctx))
register("item/fishing_rod_cast", lambda ctx: fishing_rod(ctx, True))

CARROT = pal("6a2a08", "b8520c", "e8771a", "f8a23c", "ffd08a")
LEAF = pal("1e4a12", "2e7a1c", "48a82a", "78d046")


@texture("item/carrot_on_a_stick")
def carrot_on_a_stick(ctx):
    layers = rod_layers(ctx)
    s = rod(ctx, [(14.2, 2.0), (13.6, 6.6)], 0.8, STRING)
    car = spr(ctx, poly(ctx, [(11.0, 7.4), (15.0, 7.4), (14.2, 10.4), (13.0, 15.4), (11.8, 10.4)]), CARROT, bevel=1.2)
    paint(car, line(ctx, [(12.0, 9.4), (13.2, 9.8)], 0.6) * (~(ctx.edge(car.alpha, 1) > 0)), CARROT[1])
    top = spr(ctx, U(line(ctx, [(13.0, 7.6), (11.6, 5.6)], 1.2), line(ctx, [(13.0, 7.6), (14.8, 5.8)], 1.2)), LEAF,
              bevel=1)
    return compose(ctx, *layers, s, top, car)


# ---------------------------------------------------------------- brush

@texture("item/brush")
def brush(ctx):
    d = Diag(1.5, 14.5)
    h = handle(ctx, 0, 8.6, 1.6, d)
    ferrule = spr(ctx, d.rect(ctx, 8.0, -1.4, 10.0, 1.4), COPPER, bevel=1, smooth=0.6)
    ferrule.set_metal(ferrule.alpha, COPPER_ID)
    bristles = spr(ctx, d.poly(ctx, [(9.8, -1.6), (13.6, -2.6), (15.2, -1.4), (15.6, 0), (15.2, 1.4), (13.6, 2.6),
                                     (9.8, 1.6)]), pal("5a4632", "8e7656", "b8a07a", "d8c6a2", "efe4c8"), bevel=1.2,
                   porosity=0.4)
    tex = compose(ctx, h, ferrule, bristles)
    for vv in (-1.2, 0.0, 1.2):
        paint(tex, line(ctx, [d.p(11.0, vv * 0.8), d.p(14.6, vv)], 0.45), pal("8e7656")[0])
    return tex


# ------------------------------------------------------- flint and steel

@texture("item/flint_and_steel")
def flint_and_steel(ctx):
    ring = stroke(ctx, arc_pts(6.2, 6.2, 3.6, 70, 380, 28), 2.1)
    steel = spr(ctx, ring, IRON, bevel=1, smooth=0.7)
    metal(steel, ring, IRON_ID)
    fl = poly(ctx, [(8.6, 9.4), (11.6, 7.8), (14.8, 9.4), (15.0, 13.0), (12.0, 15.0), (8.4, 13.4)])
    flint = spr(ctx, fl, FLINT, bevel=1.5, smooth=0.5)
    paint(flint, poly(ctx, [(9.6, 10.0), (11.6, 8.8), (13.6, 9.8), (11.4, 11.0)]), FLINT[4])
    paint(flint, poly(ctx, [(11.4, 11.0), (13.6, 9.8), (14.0, 12.6), (12.0, 13.8)]), FLINT[2])
    return compose(ctx, steel, flint)
