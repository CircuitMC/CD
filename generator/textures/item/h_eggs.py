"""Spawn eggs (h-z mobs): one egg silhouette, per-mob colors and markings."""
import numpy as np

from ...registry import register
from .h_lib import cells, compose, paint, ramp, rgb, spr

# mob: (shell, markings, pattern[, accent])
EGGS = {
    "happy_ghast": ("f2f0ee", "8a6a4a", "band", "6ab8e0"),
    "hoglin": ("c4806a", "6a4430", "spots", "e8dcc0"),
    "horse": ("b07a46", "4a3020", "spots"),
    "husk": ("7a7058", "c4ae78", "speckle"),
    "iron_golem": ("d6d0c4", "6a8a3a", "cracks"),
    "llama": ("d8c4a0", "8a6440", "spots"),
    "magma_cube": ("4a1a0e", "f08a1a", "bands"),
    "mooshroom": ("a81a14", "c8c8c8", "spots"),
    "mule": ("4e3020", "8a5a36", "speckle"),
    "nautilus": ("e6dcc8", "b0542e", "stripes"),
    "ocelot": ("e6c46a", "5a3a1e", "spots"),
    "panda": ("eeeeea", "2a2a2a", "patches"),
    "parched": ("cdb88e", "6a5a44", "cracks"),
    "parrot": ("1ec01e", "e02020", "top", "2a6ae0"),
    "phantom": ("3a4a7a", "8ad030", "speckle"),
    "pig": ("eba2a0", "c4706e", "spots"),
    "piglin_brute": ("6a4a2a", "e8c040", "bands"),
    "piglin": ("e09a88", "e8c040", "spots"),
    "pillager": ("4a5a5a", "a8a8a0", "band"),
    "polar_bear": ("f0f0ec", "c4c4bc", "speckle"),
    "pufferfish": ("e8b81a", "3aa0b0", "spots"),
    "rabbit": ("9a7650", "e6d6c0", "speckle"),
    "ravager": ("6a6660", "3a3430", "bands"),
    "salmon": ("a42a26", "3a6a54", "top"),
    "sheep": ("ececec", "f4c4a8", "speckle"),
    "shulker": ("946a96", "4a3a4e", "bands"),
    "silverfish": ("7a7a7e", "4a4a50", "stripes"),
    "skeleton_horse": ("a8a89a", "6a6a5e", "stripes"),
    "skeleton": ("c4c4c4", "4a4a4a", "cracks"),
    "slime": ("5abc4a", "306a28", "spots"),
    "sniffer": ("8a2a20", "3aa06a", "speckle"),
    "snow_golem": ("f2f8fa", "e88a20", "top"),
    "spider": ("3a322e", "c41a1a", "spots"),
    "squid": ("22405a", "6a8aa0", "stripes"),
    "stray": ("7a9496", "d4e0e0", "cracks"),
    "strider": ("9a2e30", "4a4a4e", "bands"),
    "sulfur_cube": ("d8cc3a", "8a8a20", "patches"),
    "tadpole": ("6a5034", "1e140c", "top"),
    "trader_llama": ("e6d8b8", "2a52a8", "band", "c41a1a"),
    "tropical_fish": ("ee6a1a", "f8f4ee", "stripes"),
    "turtle": ("eaeacc", "3a8a2a", "spots"),
    "vex": ("8aa0b8", "e6eef6", "speckle"),
    "villager": ("5a3a26", "b8846a", "band"),
    "vindicator": ("8a9090", "1e5a5a", "band"),
    "wandering_trader": ("44608c", "e0b848", "band"),
    "warden": ("0e3a44", "3ad2d6", "spots"),
    "witch": ("3a0e2a", "4a9a2a", "spots"),
    "wither_skeleton": ("1e1e1e", "4a4a4a", "cracks"),
    "wither": ("161616", "4e5a6a", "patches"),
    "wolf": ("d6d2ce", "c4a07a", "patches"),
    "zoglin": ("c47a6a", "e6e0dc", "spots"),
    "zombie_horse": ("2e5a26", "8ab47a", "speckle"),
    "zombie_nautilus": ("6a8a6a", "b0542e", "stripes"),
    "zombie": ("00a8a8", "6a9a4a", "spots"),
    "zombie_villager": ("5a3a26", "6a9a4a", "band"),
    "zombified_piglin": ("e09a88", "4a7a30", "patches"),
}


def egg_mask(ctx):
    k = ctx.w / 16
    x, y = ctx.x / k - 8.0, ctx.y / k - 8.8
    # egg: narrower at the top
    ry = np.where(y < 0, 6.6, 5.8)
    rx = 5.4 * (1 - 0.13 * np.clip(-y / 6.6, 0, 1) - 0.02 * np.clip(y / 5.8, 0, 1))
    return ((x / rx) ** 2 + (y / ry) ** 2 < 1).astype(np.float32)


def egg(ctx, mob):
    spec = EGGS[mob]
    shell, mark, pattern = spec[:3]
    accent = spec[3] if len(spec) > 3 else None
    m = egg_mask(ctx)
    p = ramp(shell, 5, lo=0.42, lift=0.5)
    t = spr(ctx, m, p, smooth=0.45, f0=0.04, bevel=3)
    ring = ctx.edge(m, 1) > 0
    inner = (m > 0.5) & ~ring
    mp = ramp(mark, 4, lo=0.6, lift=0.35)
    rng = ctx.rng("spots")
    k = ctx.w / 16
    X, Y = ctx.x / k, ctx.y / k
    mk = np.zeros_like(inner)
    if pattern in ("spots", "patches"):
        n = 6 if pattern == "spots" else 3
        r = (1.0, 1.6) if pattern == "spots" else (1.8, 2.6)
        for _ in range(n):
            cx, cy = rng.uniform(4.5, 11.5), rng.uniform(4.5, 13.5)
            rr = rng.uniform(*r)
            mk |= np.hypot(X - cx, (Y - cy) * 1.1) < rr
    elif pattern == "speckle":
        cl = [(int(rng.integers(4, 12)), int(rng.integers(4, 14))) for _ in range(12)]
        mk |= cells(ctx, cl) > 0.5
    elif pattern == "bands":
        mk |= ((np.floor(Y) % 4) == 1)
    elif pattern == "band":
        mk |= (Y >= 9) & (Y < 11.2)
    elif pattern == "stripes":
        mk |= ((np.floor(X + Y * 0.5) % 4) == 0)
    elif pattern == "top":
        mk |= Y < 6.4
    elif pattern == "cracks":
        pts = [(7, 4), (7, 5), (8, 6), (8, 7), (7, 8), (9, 7), (10, 8), (5, 10), (6, 11), (6, 12),
               (10, 12), (11, 11)]
        off = int(rng.integers(-1, 2))
        mk |= cells(ctx, [(x + off, y) for x, y in pts]) > 0.5
    mk &= inner
    if pattern in ("cracks",):
        t.color[mk] = mp[0]
    else:
        # markings follow the shell shading: light on the lit side
        shade = np.clip((t.color.mean(-1) - p[1:].mean(-1).min()) / (p[-1].mean() - p[1].mean() + 1e-6), 0, 1)
        idx = np.clip((shade * 3.0).astype(int), 0, 3)
        t.color[mk] = mp[idx[mk]]
        t.color[mk & (ctx.edge(mk.astype(np.float32), 1, "br") > 0)] *= 0.85
    if accent:
        am = inner & (cells(ctx, [(10, 5), (11, 6), (5, 12), (6, 12)]) > 0.5)
        t.color[am] = rgb(accent)
    # glossy highlight
    paint(t, (cells(ctx, [(5, 5), (6, 4)]) > 0.5) & inner, np.clip(p[-1] * 1.05 + 0.05, 0, 1))
    return t


for _mob in EGGS:
    register(f"item/{_mob}_spawn_egg", lambda ctx, m=_mob: egg(ctx, m))
