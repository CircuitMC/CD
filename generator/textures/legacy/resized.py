"""Older layouts that are plain crops, downscales or repeats of a modern texture."""
import numpy as np

from ...engine import Ctx, Tex
from ...registry import TEXTURES, register

LAYERS = ("color", "alpha", "height", "smooth", "f0", "metal", "porosity", "sss", "emissive")


def _render(key, ctx, w, h):
    sub = Ctx(key, w, h, ctx.s, ctx.frame, ctx.frames)
    return TEXTURES[key].fn(sub)


def _rebuild(ctx, src, fn):
    t = Tex(ctx, np.zeros((ctx.H, ctx.W, 3), np.float32), wrap=src.wrap, grain=0)
    for attr in LAYERS:
        setattr(t, attr, np.ascontiguousarray(fn(getattr(src, attr))).astype(np.float32))
    return t


def top_half(key, w, h):
    """64x32 (1.7) skin = upper half of the modern 64x64 skin layout."""
    return lambda ctx: _rebuild(ctx, _render(key, ctx, w, h), lambda a: a[: ctx.H])


def downscaled(key, w, h):
    def fn(ctx):
        src = _render(key, ctx, w, h)
        f = src.color.shape[0] // ctx.H
        return _rebuild(ctx, src, lambda a: a.reshape(ctx.H, f, ctx.W, f, *a.shape[2:]).mean(axis=(1, 3)))
    return fn


def repeated(key, w, h):
    """1.13-1.14 conduit wind: frames stacked in one tall image (animated by the game)."""
    def fn(ctx):
        src = _render(key, ctx, w, h)
        reps = ctx.H // src.color.shape[0]
        return _rebuild(ctx, src, lambda a: np.concatenate([a] * reps, 0))
    return fn


register("entity/steve@64x32", top_half("entity/player/wide/steve", 64, 64), size=(64, 32))
for _eye in ("closed_eye", "open_eye"):
    register(f"entity/conduit/{_eye}@8x8", downscaled(f"entity/conduit/{_eye}", 16, 16), size=(8, 8))
for _wind in ("wind", "wind_vertical"):
    register(f"entity/conduit/{_wind}@64x1024", repeated(f"entity/conduit/{_wind}", 64, 32), size=(64, 1024))
