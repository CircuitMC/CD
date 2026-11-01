"""Overworld ores (stone and deepslate hosts): chunky 3-6 texel mineral clusters."""
from ...engine import COPPER, GOLD, IRON, pal
from ...registry import register
from .stone_common import ore_clusters
from .terrain import deepslate, stone

# shadow, body, highlight, sparkle; plus PBR / layout hints
ORES = {
    "coal": (pal("141416", "232326", "37373b", "4d4d52"), dict(smooth=0.3, count=8, size=(4, 7))),
    "iron": (pal("8a5d40", "b98c68", "dcb48e", "f2d8bb"), dict(smooth=0.55, metal_id=IRON)),
    "copper": (pal("6e3a1d", "b0613a", "dc8a5a", "f4b98c"), dict(smooth=0.55, metal_id=COPPER, count=8)),
    "gold": (pal("9a6c0c", "dcae24", "f6da4c", "fff3a6"), dict(smooth=0.7, metal_id=GOLD)),
    "redstone": (pal("6e0909", "b51414", "e83a2a", "ff8a76"), dict(smooth=0.5, glow=0.3, count=8)),
    "emerald": (pal("0a5a2c", "15994a", "3fd57a", "b6ffd2"), dict(smooth=0.9, f0=0.16, count=6, size=(3, 6))),
    "lapis": (pal("142474", "2442b2", "4a72e6", "9cbcff"), dict(smooth=0.6, f0=0.06, count=8)),
    "diamond": (pal("137370", "2fbcb4", "74e8e0", "dcfffb"), dict(smooth=0.95, f0=0.17, count=6, size=(3, 6))),
}

DEEP_SHIFT = 0.88  # minerals in deepslate read slightly darker


def _make(mineral, deep):
    colors, opts = ORES[mineral]
    host = deepslate if deep else stone

    def gen(ctx):
        base = host(ctx.sub("block/deepslate" if deep else "block/stone"))
        p = colors * (DEEP_SHIFT if deep and mineral != "coal" else 1.0)
        halo = 1.3 if (deep and mineral == "coal") else 1.0
        return ore_clusters(ctx, base, p, salt="ore", rim=0.66, halo=halo, **opts)
    return gen


for _m in ORES:
    register(f"block/{_m}_ore", _make(_m, False))
    register(f"block/deepslate_{_m}_ore", _make(_m, True))
