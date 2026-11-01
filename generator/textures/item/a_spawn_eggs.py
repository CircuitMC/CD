"""Spawn eggs (a-g mobs): one shaded egg shell per mob with its own base color,
marking color and marking style."""
import numpy as np

from ...registry import register
from ...sprites import compose
from .a_lib import circ, shades

# mob: (base, markings, style, emissive markings)
EGGS = {
    "allay": ("3fb6ea", "d6f6ff", "speckle", 0.3),
    "armadillo": ("a8685c", "5e3430", "bands", 0),
    "axolotl": ("f2a0c4", "b8337f", "spots", 0),
    "bat": ("4c3b2c", "1a130d", "spots", 0),
    "bee": ("efc12e", "3a2814", "bands", 0),
    "blaze": ("eea914", "fff08a", "speckle", 0.5),
    "bogged": ("788a58", "34442a", "spots", 0),
    "breeze": ("b2aae6", "6c62c4", "swirl", 0),
    "camel_husk": ("bc9c6c", "6e5032", "speckle", 0),
    "camel": ("dcb064", "9a6a34", "spots", 0),
    "cat": ("e2bb78", "6a4826", "bands", 0),
    "cave_spider": ("0f4a4c", "b01414", "face", 0),
    "chicken": ("ebebeb", "c41e1e", "spots", 0),
    "cod": ("c4aa82", "ecdcb8", "spots", 0),
    "copper_golem": ("c66c38", "48a28a", "spots", 0),
    "cow": ("4c3424", "dcdcdc", "spots", 0),
    "creaking": ("5c4a38", "f2902a", "face", 0.6),
    "creeper": ("3aa52a", "111111", "spots", 0),
    "dolphin": ("7a8ca4", "eef2f6", "bands", 0),
    "donkey": ("6a5848", "a2927e", "spots", 0),
    "drowned": ("4a9c98", "6a8a36", "spots", 0),
    "elder_guardian": ("d6d2c2", "76668a", "spots", 0),
    "ender_dragon": ("1c1c22", "c254e2", "face", 0.5),
    "enderman": ("161618", "e070f2", "face", 0.5),
    "endermite": ("22222c", "6e6e82", "speckle", 0),
    "evoker": ("8a8e90", "232327", "bands", 0),
    "fox": ("df7a2a", "f6eee2", "spots", 0),
    "frog": ("d08a3c", "f2d6a2", "spots", 0),
    "ghast": ("f0f0f0", "a8a8a8", "face", 0),
    "glow_squid": ("0d5c6c", "6ef2e2", "spots", 0.8),
    "goat": ("cbc3b6", "6a5a48", "spots", 0),
    "guardian": ("5a8a7a", "e07a2a", "spots", 0),
}

CX, CY, RX, RY = 8.0, 8.6, 5.2, 6.7


def egg_mask(ctx):
    k = ctx.w / 16
    x, y = ctx.x / k, ctx.y / k
    yy = (y - CY) / RY
    rx = RX * (1 + 0.15 * yy)
    return ((((x - CX) / rx) ** 2 + yy ** 2) < 1).astype(np.float32)


def markings(ctx, style, salt):
    rng = ctx.rng(f"egg:{salt}")
    m = ctx.zeros()
    if style == "spots":
        for _ in range(6):
            cx, cy = rng.uniform(4.6, 11.6), rng.uniform(4.0, 13.6)
            m = np.maximum(m, circ(ctx, cx, cy, rng.uniform(0.8, 1.5)))
    elif style == "speckle":
        for _ in range(11):
            x, y = int(rng.integers(4, 12)), int(rng.integers(3, 15))
            m = np.maximum(m, circ(ctx, x + 0.5, y + 0.5, 0.55))
    elif style == "bands":
        k = ctx.w / 16
        y = ctx.y / k + 0.25 * np.sin(ctx.x / k * 1.3)
        m = ((y % 4.0) < 1.4) & (y > 4) & (y < 14.6)
        m = m.astype(np.float32)
    elif style == "swirl":
        k = ctx.w / 16
        a = np.arctan2(ctx.y / k - 9, ctx.x / k - 8)
        r = np.hypot(ctx.x / k - 8, ctx.y / k - 9)
        m = (((r + a * 0.9) % 3.2) < 1.1).astype(np.float32)
    elif style == "face":
        m = np.maximum(circ(ctx, 6.0, 8.0, 0.75), circ(ctx, 10.0, 8.0, 0.75))
        m = np.maximum(m, circ(ctx, 8.0 + rng.uniform(-2, 2), 12.0, 0.6))
    return m


def spawn_egg(ctx, mob):
    base, mark, style, glow = EGGS[mob]
    from .a_lib import spr
    egg = egg_mask(ctx)
    p = shades(base, 5, 0.5, 1.3)
    t = spr(ctx, egg, p, bevel=3.0, light=0.32, smooth=0.35, f0=0.04)
    ring = ctx.edge(egg, 1) > 0
    mk = (markings(ctx, style, mob) > 0.5) & (egg > 0.5) & ~ring
    lum = t.color @ np.array([0.3, 0.59, 0.11], np.float32)
    rel = np.clip(lum / max(1e-3, float(p[2] @ np.array([0.3, 0.59, 0.11]))), 0.6, 1.35)
    mc = shades(mark, 3, 0.75, 1.15)[1]
    col = np.clip(mc[None, None, :] * rel[..., None], 0, 1)
    if ctx.pixel_art:  # snap marks to 3 tones
        q = np.where(rel < 0.92, 0, np.where(rel > 1.08, 2, 1))
        col = shades(mark, 3, 0.75, 1.15)[q]
    t.color = np.where(mk[..., None], col, t.color)
    if glow:
        t.emissive = np.where(mk, glow, t.emissive)
    # shell glint
    hl = (circ(ctx, 5.6, 4.6, 0.7) > 0.5) & ~mk & ~ring
    t.color[hl] = np.clip(p[4] * 1.05, 0, 1)
    return t


for _mob in EGGS:
    register(f"item/{_mob}_spawn_egg", lambda ctx, m=_mob: spawn_egg(ctx, m))
