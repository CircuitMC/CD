"""Texture registry.

Paths are relative to assets/minecraft/textures/ (e.g. "block/stone") unless
they start with "/", in which case they are relative to assets/ (e.g.
"/minecraft/optifine/ctm/glass/0" or "/circuitmc/textures/block/x").

Generators take a `Ctx` and return a `Tex`, or a list of `Tex` (one per
animation frame) when the texture is animated.
"""
from dataclasses import dataclass, field
from typing import Callable, Optional

TEXTURES = {}
FILES = {}  # extra static files: assets-relative path -> text, per pack


@dataclass
class Spec:
    path: str
    fn: Callable
    size: Optional[tuple] = None       # native frame size in texels; default: vanilla size
    frames: Optional[int] = None       # default: vanilla frame count (1 if not animated)
    frametime: int = 2
    interpolate: bool = False
    pbr: Optional[bool] = None         # default: on for block/, item/, entity/
    pack: str = "core"                 # "core" or an addon pack id
    meta: dict = field(default_factory=dict)  # extra .mcmeta sections


def texture(*paths, **kw):
    def wrap(fn):
        for path in paths:
            register(path, fn, **kw)
        return fn
    return wrap


def register(path, fn, **kw):
    if path in TEXTURES:
        raise ValueError(f"duplicate texture: {path}")
    TEXTURES[path] = Spec(path, fn, **kw)


def static_file(path, text, pack="core"):
    """Register a non-image file (models, blockstates, CTM .properties...)."""
    FILES[(pack, path)] = text
