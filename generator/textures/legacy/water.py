"""1.7-1.12 water: those versions do not tint water by biome, so the texture carries its color."""
import numpy as np

from ...registry import TEXTURES, register

WATER_BLUE = np.array([0.24, 0.43, 0.84], np.float32)


def blue(key):
    def fn(ctx):
        t = TEXTURES[key].fn(ctx)
        frames = t if isinstance(t, list) else [t]
        for f in frames:
            f.color = np.clip(f.color * WATER_BLUE * 1.15, 0, 1)
        return t
    return fn


for _name in ("water_still", "water_flow", "water_overlay"):
    _spec = TEXTURES[f"block/{_name}"]
    register(f"block/{_name}#pre-1.13", blue(f"block/{_name}"), size=_spec.size, frames=_spec.frames,
             frametime=_spec.frametime, interpolate=_spec.interpolate)
