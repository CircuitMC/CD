"""Ice & snow, froglights, sculk, special soils and suspicious sand / gravel."""
import numpy as np

from ...engine import Tex, pal
from ...materials import DIRT, SNOW, lerp, soil
from ...registry import register, texture
from .stone_common import frame, mottled, ore_clusters, pits, speckle
from .terrain import fringe, gravel, sand

# ---------------------------------------------------------------- ice & snow

ICE = pal("7fa6e0", "93b6ea", "a6c5f0", "b9d3f5", "cfe2fa", "e8f2ff")
PACKED_ICE = pal("6f96d2", "82a6dc", "94b5e4", "a6c3ec", "b9d1f2", "d6e6fa")
BLUE_ICE = pal("3a6cc4", "4a7ed2", "5b90dc", "6ea2e6", "86b6ee", "aed0f8")


def ice_cracks(ctx, salt, n=6):
    vo = ctx.voronoi(n, f"ice{salt}", min_dist=4.5)
    m = ((vo["f2"] - vo["f1"]) < 0.45) & (ctx.noise(4, 1, salt=f"icc{salt}") > 0.42)
    return m


def ice_body(ctx, p, salt):
    n = ctx.noise(8, 2, 0.5, salt=f"ib{salt}")
    streak = ctx.noise(2, 2, 0.5, salt=f"is{salt}", stretch=(3, 0.6))
    # diagonal streaks (frozen flow)
    diag = ctx.lattice_noise(16, 3, f"id{salt}", x=(ctx.x + ctx.y) % 16, y=ctx.y * 0 + 1)
    v = n * 0.45 + streak * 0.25 + diag * 0.2 + ctx.texel_noise(f"ig{salt}") * 0.1
    return ctx.palette(p[1:-1], v), n


@texture("block/ice")
def ice(ctx):
    col, n = ice_body(ctx, ICE, "i")
    cr = ice_cracks(ctx, "i")
    col = np.where(cr[..., None], ICE[-1], col)
    alpha = 0.62 + n * 0.12 + cr * 0.2
    return Tex(ctx, col, alpha=alpha, height=0.5 + cr * 0.1, smooth=0.95, f0=0.02, grain=0.02)


@texture("block/packed_ice")
def packed_ice(ctx):
    col, n = ice_body(ctx, PACKED_ICE, "p")
    cr = ice_cracks(ctx, "p", n=9)
    col = np.where(cr[..., None], PACKED_ICE[-1], col)
    sh = np.roll(cr, ctx.s, 0) & ~cr
    col = np.where(sh[..., None], PACKED_ICE[0], col)
    return Tex(ctx, col, height=0.5 + cr * 0.1 - sh * 0.1, smooth=0.85, f0=0.02, grain=0.03)


@texture("block/blue_ice")
def blue_ice(ctx):
    col, n = ice_body(ctx, BLUE_ICE, "b")
    cr = ice_cracks(ctx, "b", n=7)
    col = np.where(cr[..., None], BLUE_ICE[-1], col)
    sh = np.roll(cr, ctx.s, 0) & ~cr
    col = np.where(sh[..., None], BLUE_ICE[0], col)
    sp = ctx.texel_noise("bis", soft=False) < 0.025
    col = np.where(sp[..., None], pal("e4f0ff")[0], col)
    return Tex(ctx, col, height=0.5 + cr * 0.1 - sh * 0.1, smooth=0.95, f0=0.02, grain=0.02)


@texture("block/powder_snow")
def powder_snow(ctx):
    n = ctx.noise(4, 2, 0.5, salt="ps")
    g = ctx.texel_noise("psg")
    p = pal("c9d6e4", "d9e3ee", "e5edf5", "eef3f9", "f6f9fc", "fdfeff")
    t = Tex(ctx, ctx.palette(p[1:], n * 0.4 + g * 0.6), height=0.45 + g * 0.2, smooth=0.25, sss=0.6,
            porosity=0.6, f0=0.02)
    speckle(ctx, t, p[0], 0.05, "psd", height=0.3)
    speckle(ctx, t, pal("ffffff")[0], 0.04, "psl", height=0.7, smooth=0.6)
    return t


# ---------------------------------------------------------------- froglights

FROG = {
    "ochre": pal("8c5a1c", "b57f28", "d9a63c", "f0c95e", "fbe496", "fff6d2"),
    "verdant": pal("3c6630", "558c42", "74ad58", "98cb74", "c2e59e", "e8f9d6"),
    "pearlescent": pal("7a4c6c", "a06e90", "c194b4", "dcb6d2", "f0d6ea", "fdf0f8"),
}


def froglight_top(ctx, kind):
    p = FROG[kind]
    dx, dy = np.abs(ctx.x - 8), np.abs(ctx.y - 8)
    r = np.maximum(dx, dy) * 0.7 + np.hypot(dx, dy) * 0.3
    ring = np.floor(r / 2.0)
    v = 1.0 - ring * 0.16 + (ctx.texel_noise(f"ft{kind}") - 0.5) * 0.12
    col = ctx.palette(p[1:], np.clip(v, 0, 1))
    t = Tex(ctx, col, height=0.7 - ring * 0.06, smooth=0.5, sss=0.6, emissive=0.85)
    frame(ctx, t, 0, 0, 16, 16, p[2], p[0])
    t.emissive = np.where(t.height < 0.45, 0.5, t.emissive)
    return t


def froglight_side(ctx, kind):
    p = FROG[kind]
    lx = ctx.x % 4
    v = 0.75 - np.abs(lx - 1.5) * 0.18 + (ctx.noise(2, 2, salt=f"fsn{kind}", stretch=(0.5, 4)) - 0.5) * 0.3
    v = v + (ctx.texel_noise(f"fs{kind}") - 0.5) * 0.1
    col = ctx.palette(p[1:], np.clip(v, 0, 1))
    seam = lx >= 3.0
    col = np.where(seam[..., None], p[1], col)
    t = Tex(ctx, col, height=np.where(seam, 0.35, 0.6), smooth=0.5, sss=0.6, emissive=np.where(seam, 0.55, 0.85))
    band = (ctx.rect(0, 0, 16, 1) + ctx.rect(0, 15, 16, 16)) > 0
    t.color = np.where(band[..., None], p[0], t.color)
    t.emissive = np.where(band, 0.4, t.emissive)
    return t


for _k in FROG:
    register(f"block/{_k}_froglight_top", (lambda k: lambda ctx: froglight_top(ctx, k))(_k))
    register(f"block/{_k}_froglight_side", (lambda k: lambda ctx: froglight_side(ctx, k))(_k))


# ---------------------------------------------------------------- sculk

SCULK = pal("05101a", "0a1a24", "0f2430", "142e3c", "1a3a4a")
SCULK_GLOW = pal("0c5a68", "15909e", "29c8d6", "7ff2fa")


def sculk(ctx):
    c = ctx.sub("block/sculk")
    n = c.noise(4, 3, 0.55, salt="sk")
    t = Tex(ctx, ctx.palette(SCULK, n * 0.65 + c.texel_noise("skg") * 0.35), height=0.45 + n * 0.2,
            smooth=0.35, sss=0.3)
    vo = c.voronoi(7, "skv", min_dist=4)
    vein = ((vo["f2"] - vo["f1"]) < 0.5) & (c.noise(3, 1, salt="skvn") > 0.5)
    ph = ctx.frame / max(1, ctx.frames) * 2 * np.pi
    off = c.rng("skph").uniform(0, 2 * np.pi, len(vo["points"])).astype(np.float32)[vo["id"]]
    pulse = 0.5 + 0.5 * np.sin(ph + off)
    vc = ctx.palette(SCULK_GLOW[:3], 0.3 + pulse * 0.6)
    t.color = np.where(vein[..., None], vc, t.color)
    t.emissive = np.where(vein, 0.3 + pulse * 0.5, 0.0)
    # glowing specks (one per cell center region)
    spk = (vo["f1"] < 0.75) & (c.texel_noise("sks", soft=False) < 0.8)
    t.color = np.where(spk[..., None], ctx.palette(SCULK_GLOW[1:], pulse), t.color)
    t.emissive = np.where(spk, 0.5 + pulse * 0.5, t.emissive)
    t.height = np.where(spk | vein, 0.65, t.height)
    return t


register("block/sculk", sculk, frametime=20, interpolate=True)


# ---------------------------------------------------------------- soils

PODZOL = pal("2e1a0c", "3e2410", "4f2f14", "5f3a19", "70461f", "825426")
MYCELIUM = pal("5a4a58", "6a5868", "7a6878", "8a7888", "9b8a98", "ae9eaa")


@texture("block/podzol_top")
def podzol_top(ctx):
    t = soil(ctx.sub("block/podzol_top"), PODZOL, pebbles=2, porosity=0.6)
    rng = ctx.rng("needles")
    needle = pal("a0601e", "c07a2a", "6e3e14")
    for i in range(22):
        x, y = float(rng.uniform(0, 16)), float(rng.uniform(0, 16))
        a = float(rng.uniform(0, np.pi))
        L = float(rng.uniform(1.5, 3.0))
        x2, y2 = x + np.cos(a) * L, y + np.sin(a) * L
        m = ctx.segment(x, y, x2, y2, 0.8) > 0
        m |= ctx.segment(x - 16, y, x2 - 16, y2, 0.8) > 0
        m |= ctx.segment(x, y - 16, x2, y2 - 16, 0.8) > 0
        t.color = np.where(m[..., None], needle[i % 3], t.color)
        t.height = np.where(m, 0.65, t.height)
    return t


def fringe_side(ctx, top_fn, salt):
    t = soil(ctx.sub("block/dirt"), DIRT)
    top = top_fn(ctx)
    m, depth = fringe(ctx, salt)
    t.color = np.where(m[..., None], top.color, t.color)
    t.height = np.where(m, top.height * 0.5 + 0.35, t.height)
    edge = np.roll(m, ctx.s, 0) & ~m
    t.color = np.where(edge[..., None], t.color * 0.75, t.color)
    return t


@texture("block/podzol_side")
def podzol_side(ctx):
    return fringe_side(ctx, podzol_top, "podzol")


@texture("block/mycelium_top")
def mycelium_top(ctx):
    n = ctx.noise(4, 2, 0.5, salt="my")
    g = ctx.texel_noise("myg")
    t = Tex(ctx, ctx.palette(MYCELIUM[1:], n * 0.45 + g * 0.55), height=0.45 + g * 0.25, smooth=0.05,
            porosity=0.5, sss=0.2)
    speckle(ctx, t, pal("c9bcc8")[0], 0.06, "myl", height=0.7)
    speckle(ctx, t, MYCELIUM[0], 0.06, "myd", height=0.3)
    return t


@texture("block/mycelium_side")
def mycelium_side(ctx):
    return fringe_side(ctx, mycelium_top, "mycelium")


@texture("block/coarse_dirt")
def coarse_dirt(ctx):
    t = soil(ctx.sub("block/coarse_dirt"), DIRT, pebbles=4)
    stones = pal("6a6460", "857e78", "a09890")
    return ore_clusters(ctx, t, stones, salt="cgrv", count=9, size=(1, 3), min_dist=3.6, smooth=0.2,
                        rim=0.7, height=0.7)


@texture("block/rooted_dirt")
def rooted_dirt(ctx):
    t = soil(ctx.sub("block/dirt"), DIRT)
    rng = ctx.rng("roots")
    root = pal("b89a70", "9c7e58")
    for i in range(5):
        x, y = float(rng.uniform(0, 16)), float(rng.uniform(0, 16))
        for _ in range(int(rng.integers(4, 8))):
            nx, ny = x + float(rng.choice([-1, 0, 1])), y + 1
            m = np.zeros((ctx.H, ctx.W), bool)
            for wy in (-16, 0, 16):
                for wx in (-16, 0, 16):
                    m |= ctx.segment(x + 0.5 + wx, y + 0.5 + wy, nx + 0.5 + wx, ny + 0.5 + wy, 0.9) > 0
            t.color = np.where(m[..., None], root[i % 2], t.color)
            t.height = np.where(m, 0.6, t.height)
            x, y = nx, ny
    return t


# ---------------------------------------------------------------- suspicious sand / gravel

def disturbed(ctx, base, stage, salt):
    """Progressively brushed-away surface: stage 0 subtle lumps .. stage 3 deep hollow."""
    t = base.copy()
    c = ctx.sub(f"susp{salt}")
    d = np.hypot((ctx.x - 8) / 1.2, ctx.y - 8)
    n = c.noise(4, 2, 0.5, salt="sd") + (1 - np.clip(d / 9, 0, 1)) * 0.6
    n = n / 1.6
    thr = [0.62, 0.52, 0.44, 0.36][stage]
    hollow = n > thr
    deep = n > thr + 0.12
    t.color = np.where(hollow[..., None], t.color * 0.84, t.color)
    t.color = np.where(deep[..., None], t.color * 0.86, t.color)
    lip_hi = hollow & ~np.roll(hollow, -ctx.s, 0)        # bottom edge of hollow catches light
    lip_sh = hollow & ~np.roll(hollow, ctx.s, 0)          # top inner edge in shadow
    t.color = np.where(lip_sh[..., None], t.color * 0.8, t.color)
    t.color = np.where(lip_hi[..., None], np.clip(t.color * 1.25, 0, 1), t.color)
    t.height = np.where(deep, 0.15, np.where(hollow, 0.3, t.height))
    # brush streaks around the hollow
    streak = (np.abs(c.noise(1, 1, salt="sst", stretch=(5, 1)) - 0.5) < 0.06) & ~hollow & (n > thr - 0.15)
    t.color = np.where(streak[..., None], np.clip(t.color * 1.1, 0, 1), t.color)
    # loose grains pushed onto the surface
    loose = (c.texel_noise(f"sl{stage}", soft=False) < 0.04 + stage * 0.02) & (n > thr - 0.2) & ~hollow
    t.color = np.where(loose[..., None], t.color * 0.8, t.color)
    return t


for _s in range(4):
    register(f"block/suspicious_sand_{_s}",
             (lambda s: lambda ctx: disturbed(ctx, sand(ctx.sub("block/sand")), s, "sand"))(_s))
    register(f"block/suspicious_gravel_{_s}",
             (lambda s: lambda ctx: disturbed(ctx, gravel(ctx.sub("block/gravel")), s, "gravel"))(_s))
