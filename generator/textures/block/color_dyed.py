"""Dyed block families: wool, concrete, concrete powder, terracotta, shulker boxes.

All 16 dyes come from color_common.DYE (shared with stained glass) and each
family transforms them consistently (wool soft, concrete saturated, powder
pale, terracotta muted / earthy).
"""
import numpy as np

from ...engine import Tex, hexc
from ...registry import register
from .color_common import DYE, DYE_NAMES, adjust, mix, ramp

# ------------------------------------------------------------------ family colors

TERRACOTTA = hexc("9a5c42")


def wool_color(d):
    return np.clip(mix(d, np.ones(3), 0.05), 0, 1)


def concrete_color(name, d):
    c = adjust(d, sat=1.08, val=0.92)
    if name == "white":
        c = hexc("d9dde0")
    elif name == "black":
        c = hexc("101115")
    return c


def powder_color(name, d):
    c = mix(adjust(d, sat=0.88), np.array([0.93, 0.90, 0.84], np.float32), 0.16)
    if name == "black":
        c = hexc("1e1f24")
    return np.clip(c, 0, 1)


def terracotta_color(name, d):
    """Muted, earthy version of a dye (clay fired with pigment)."""
    special = {"white": "d0b3a2", "black": "2a1b16", "light_gray": "8a6c64", "gray": "3c2d29",
               "brown": "4e3424", "yellow": "b88528", "orange": "a35628", "red": "8d3a2c"}
    if name in special:
        return hexc(special[name])
    c = mix(d, TERRACOTTA, 0.42)
    return adjust(c, sat=0.78, val=0.82)


# ------------------------------------------------------------------ wool

def wool(ctx, base, salt="wool"):
    """Knitted wool: columns of soft V stitches (two tilted grains each), fluffy fibers."""
    p = ramp(base, 6, dark=0.64, light=1.16)
    cw, ch = 4.0, 4.0
    col = np.floor(ctx.x / cw)
    # Every other column shifts half a stitch: a braided, hand-knit look.
    yy = ctx.y + (col % 2) * (ch / 2)
    row = np.floor(yy / ch)
    lx = ctx.x - col * cw
    ly = yy - row * ch
    h = np.zeros_like(lx)
    lit = np.zeros_like(lx)
    for cx, dx in ((1.05, 0.5), (2.95, -0.5)):
        n = np.hypot(dx, 1.0)
        ax, ay = dx / n, 1.0 / n            # grain axis (leaning toward the cell center)
        for oy in (-ch, 0.0, ch):            # neighbours so grains overlap cell rows
            px, py = lx - cx, ly - 2.0 - oy
            u = px * ax + py * ay             # along the grain
            v = -px * ay + py * ax            # across
            r2 = (u / 2.25) ** 2 + (v / 1.05) ** 2
            g = np.clip(1 - r2, 0, 1)
            take = g > h
            # top-left lit: upper part of each grain and its left flank are brighter
            lit = np.where(take, -u / 2.25 * 0.5 - v / 1.05 * 0.35 * np.sign(ax + 1e-6), lit)
            h = np.maximum(h, g)
    rng = ctx.rng(f"{salt}tone")
    ncol, nrow = int(ctx.w // cw), int(ctx.h // ch) + 1
    tone = rng.uniform(-0.07, 0.07, (nrow, ncol)).astype(np.float32)
    st = tone[row.astype(np.int32) % nrow, col.astype(np.int32) % ncol]
    fuzz = ctx.noise(1, 2, 0.55, salt=f"{salt}f", stretch=(1, 2))
    body = np.sqrt(h)
    v = 0.12 + body * 0.55 + lit * body * 0.3 + st + (fuzz - 0.5) * 0.14
    v = v + (ctx.texel_noise(f"{salt}g") - 0.5) * 0.08
    color = ctx.palette(p, np.clip(v, 0, 1))
    height = np.clip(0.25 + body * 0.55 + (fuzz - 0.5) * 0.12, 0, 1)
    return Tex(ctx, color, height=height, smooth=0.04, f0=0.03, porosity=0.75, sss=0.12,
               normal_strength=0.8, grain=0.12)


# ------------------------------------------------------------------ concrete

def concrete(ctx, base, salt="con"):
    """Cast concrete: almost flat, faint cloudy variation and sparse speckle."""
    n = ctx.noise(8, 3, 0.5, salt=f"{salt}n")
    g = ctx.texel_noise(f"{salt}g")
    lum = float(np.mean(base))
    amp = 0.035 if lum > 0.15 else 0.06
    f = 1 + (n - 0.5) * amp * 1.6 + (g - 0.5) * amp * 0.6
    color = base * f[..., None]
    sp = ctx.texel_noise(f"{salt}sp", soft=False)
    dark_sp = ctx.organic((sp < 0.035).astype(np.float32), 0.4, f"{salt}d")
    light_sp = ctx.organic((sp > 0.975).astype(np.float32), 0.4, f"{salt}l")
    color = np.where(dark_sp[..., None], base * (0.9 if lum > 0.15 else 0.8), color)
    color = np.where(light_sp[..., None], np.clip(base * 1.07 + 0.025, 0, 1), color)
    height = 0.5 + (n - 0.5) * 0.04 - dark_sp * 0.08
    return Tex(ctx, np.clip(color, 0, 1), height=height, smooth=0.32, f0=0.04, porosity=0.25,
               normal_strength=0.6, grain=0.03)


def concrete_powder(ctx, base, salt="pow"):
    """Loose cement powder: granular, clumpy, light and dark grains."""
    p = ramp(base, 6, dark=0.78, light=1.14, hue_shift=0.06)
    n = ctx.noise(4, 2, 0.6, salt=f"{salt}n")
    g = ctx.texel_noise(f"{salt}g")
    v = n * 0.45 + g * 0.55
    color = ctx.palette(p[1:-1], v)
    r = ctx.texel_noise(f"{salt}sp", soft=False)
    dk = ctx.organic((r < 0.07).astype(np.float32), 0.5, f"{salt}d")
    lt = ctx.organic((r > 0.94).astype(np.float32), 0.5, f"{salt}l")
    color = np.where(dk[..., None], p[0], color)
    color = np.where(lt[..., None], p[-1], color)
    height = 0.42 + v * 0.25 - dk * 0.12 + lt * 0.12
    return Tex(ctx, color, height=height, smooth=0.03, f0=0.03, porosity=1.0, grain=0.14)


# ------------------------------------------------------------------ terracotta

def terracotta(ctx, base, salt="ter"):
    """Fired clay: matte, soft mottling with a few tiny mineral flecks."""
    p = ramp(base, 5, dark=0.86, light=1.1, hue_shift=0.05)
    n = ctx.noise(8, 3, 0.55, salt=f"{salt}n")
    w = ctx.noise(4, 2, 0.5, salt=f"{salt}w", stretch=(3, 1))
    g = ctx.texel_noise(f"{salt}g")
    v = n * 0.5 + w * 0.2 + g * 0.3
    color = ctx.palette(p[1:-1], v)
    fl = ctx.texel_noise(f"{salt}fl", soft=False)
    color = np.where(ctx.organic((fl > 0.975).astype(np.float32), 0.4, f"{salt}a")[..., None], p[-1], color)
    color = np.where(ctx.organic((fl < 0.02).astype(np.float32), 0.4, f"{salt}b")[..., None], p[0], color)
    height = 0.48 + n * 0.08 + g * 0.04
    return Tex(ctx, color, height=height, smooth=0.12, f0=0.04, porosity=0.4,
               normal_strength=0.7, grain=0.06)


# ------------------------------------------------------------------ shulker box (particle / block)

SHULKER_PLAIN = hexc("8a5f8e")


def shulker_box(ctx, base, salt="shk"):
    """Shell panel: lid band over a body, with a hard rim and seam."""
    p = ramp(base, 6, dark=0.62, light=1.2)
    n = ctx.noise(4, 2, 0.5, salt=f"{salt}n")
    g = ctx.texel_noise(f"{salt}g")
    v = 0.5 + (n - 0.5) * 0.4 + (g - 0.5) * 0.2
    color = ctx.palette(p[1:-1], v)
    height = ctx.full(0.55)
    # Lid: rows 0..7, seam at 8, body below; rim of 1 texel all around.
    seam = ctx.rect(0, 8, ctx.w, 9)
    lid_lip = ctx.rect(0, 7, ctx.w, 8)
    rim_l = ctx.rect(0, 0, ctx.w, 1) + ctx.rect(0, 0, 1, ctx.h)
    rim_d = ctx.rect(0, ctx.h - 1, ctx.w, ctx.h) + ctx.rect(ctx.w - 1, 0, ctx.w, ctx.h)
    body_shadow = ctx.rect(1, 9, ctx.w - 1, 10)
    color = np.where((body_shadow > 0)[..., None], p[1], color)
    color = np.where((lid_lip > 0)[..., None], p[-2], color)
    color = np.where((rim_l > 0)[..., None], p[-1], color)
    color = np.where((rim_d > 0)[..., None], p[1], color)
    color = np.where((seam > 0)[..., None], p[0], color)
    # A soft lighter plate in the middle of the lid and of the body.
    plate = ctx.rect(3, 2, ctx.w - 3, 6) + ctx.rect(3, 11, ctx.w - 3, 14)
    color = np.where((plate > 0)[..., None], p[-2] * 0.35 + color * 0.65, color)
    height = np.where(seam > 0, 0.15, height + rim_l * 0.15 - rim_d * 0.1 + lid_lip * 0.1 + plate * 0.05)
    return Tex(ctx, np.clip(color, 0, 1), height=height, smooth=0.55, f0=0.045, porosity=0.0,
               normal_strength=0.9, grain=0.04)


# ------------------------------------------------------------------ registration

def _bind(fn, *args, **kw):
    return lambda ctx: fn(ctx, *args, **kw)


for _n in DYE_NAMES:
    _d = DYE[_n]
    register(f"block/{_n}_wool", _bind(wool, wool_color(_d)))
    register(f"block/{_n}_concrete", _bind(concrete, concrete_color(_n, _d)))
    register(f"block/{_n}_concrete_powder", _bind(concrete_powder, powder_color(_n, _d)))
    register(f"block/{_n}_terracotta", _bind(terracotta, terracotta_color(_n, _d)))
    register(f"block/{_n}_shulker_box", _bind(shulker_box, adjust(_d, sat=0.95, val=0.95)))

register("block/terracotta", _bind(terracotta, TERRACOTTA))
register("block/shulker_box", _bind(shulker_box, SHULKER_PLAIN))
