"""Glass, tinted glass, stained glass and panes, plus connected-texture tiles.

Connected glass uses the OptiFine CTM `ctm_compact` format (also read by the
Continuity mod on Fabric/Quilt/NeoForge). The 5 compact tiles are:
  0 unconnected (full frame)   1 fully connected (no frame)
  2 connected vertically (left/right frame)   3 connected horizontally
  (top/bottom frame)   4 connected on all sides (corner dots only)
"""
import numpy as np

from ...engine import Tex, hexc, pal
from ...registry import register, static_file

DYES = {
    "white": "f2f4f5", "orange": "f07d1f", "magenta": "c24fbe", "light_blue": "3cb2e0",
    "yellow": "f8d22e", "lime": "79c51d", "pink": "ef8fad", "gray": "4a5054",
    "light_gray": "9c9d97", "cyan": "169c9c", "purple": "7b2fb0", "blue": "3a43a8",
    "brown": "7a4e2c", "green": "556e1c", "red": "a52a24", "black": "1c1c21",
}

CLEAR_FRAME = pal("9cb6c3", "c4dae3", "e8f5fa")
TINTED = pal("1d1720", "2c2430", "3d3442")

# frame sides drawn for each compact tile: (top, left, bottom, right, corners_only)
TILE_SIDES = {
    0: (1, 1, 1, 1, 0),
    1: (0, 0, 0, 0, 0),
    2: (0, 1, 0, 1, 0),
    3: (1, 0, 1, 0, 0),
    4: (0, 0, 0, 0, 1),
}


def frame_masks(ctx, sides):
    top, left, bottom, right, corners = sides
    w = 1
    lit = ctx.zeros()
    dark = ctx.zeros()
    if top:
        lit = np.maximum(lit, ctx.rect(0, 0, ctx.w, w))
    if left:
        lit = np.maximum(lit, ctx.rect(0, 0, w, ctx.h))
    if bottom:
        dark = np.maximum(dark, ctx.rect(0, ctx.h - w, ctx.w, ctx.h))
    if right:
        dark = np.maximum(dark, ctx.rect(ctx.w - w, 0, ctx.w, ctx.h))
    if corners:
        lit = np.maximum(lit, ctx.rect(0, 0, w, w))
        dark = np.maximum(dark, ctx.rect(ctx.w - w, ctx.h - w, ctx.w, ctx.h))
        dark = np.maximum(dark, ctx.rect(ctx.w - w, 0, ctx.w, w) + ctx.rect(0, ctx.h - w, w, ctx.h))
    return lit > 0, (dark > 0) & ~(lit > 0)


def glints(ctx):
    m = ctx.zeros()
    for (x, y), n in (((3, 5), 3), ((5, 4), 2), ((10, 12), 2)):
        for i in range(n):
            m = np.maximum(m, ctx.rect(x + i, y - i, x + i + 1, y - i + 1))
    return m > 0


def clear_glass(ctx, sides, frame=CLEAR_FRAME, glint=True):
    """Cutout glass: pixels are either opaque frame/glint or fully clear."""
    lit, dark = frame_masks(ctx, sides)
    color = np.zeros((ctx.H, ctx.W, 3), np.float32)
    alpha = ctx.zeros()
    color[lit] = frame[2]
    color[dark] = frame[0]
    alpha[lit | dark] = 1
    if glint:
        g = glints(ctx) & ~(lit | dark)
        color[g] = frame[2]
        alpha[g] = 1
    height = np.where(lit | dark, 0.8, 0.5)
    return Tex(ctx, color, alpha=alpha, height=height, smooth=0.95, f0=0.04, wrap=False, grain=0)


def stained_glass(ctx, rgb, sides, body_alpha=0.42):
    """Translucent stained glass: tinted body, denser frame, faint streaks."""
    lit, dark = frame_masks(ctx, sides)
    streak = ctx.noise(4, 2, 0.5, salt="streak", stretch=(1, 2))
    body = rgb * (0.92 + streak[..., None] * 0.12)
    color = np.where(lit[..., None], np.clip(rgb * 1.25 + 0.08, 0, 1),
                     np.where(dark[..., None], rgb * 0.62, body))
    alpha = np.where(lit | dark, 0.88, body_alpha + (streak - 0.5) * 0.06)
    g = glints(ctx) & ~(lit | dark)
    color[g] = np.clip(rgb * 1.3 + 0.15, 0, 1)
    alpha[g] = 0.7
    return Tex(ctx, color, alpha=alpha, height=np.where(lit | dark, 0.8, 0.5),
               smooth=0.95, f0=0.04, wrap=False, grain=0)


def pane_top(ctx, rgb, alpha=1.0):
    """Edge strip seen on top of panes (sampled from the middle columns)."""
    v = ctx.noise(4, 1, salt="pane", stretch=(1, 2))
    return Tex(ctx, np.clip(rgb * (0.9 + v[..., None] * 0.2), 0, 1), alpha=ctx.full(alpha),
               height=0.6, smooth=0.9)


def ctm_properties(blocks, tiles="0-4"):
    return (f"# Connected textures (OptiFine / Continuity), CircuitMC Default\n"
            f"matchBlocks={blocks}\nmethod=ctm_compact\ntiles={tiles}\nconnect=block\n")


def _bind(fn, *args):
    return lambda ctx: fn(ctx, *args)


register("block/glass", _bind(clear_glass, TILE_SIDES[0]))
register("block/glass_pane_top", _bind(pane_top, CLEAR_FRAME[1]))
register("block/tinted_glass", lambda ctx: stained_glass(ctx, TINTED[1], TILE_SIDES[0], 0.85))
for _i, _sides in TILE_SIDES.items():
    register(f"/minecraft/optifine/ctm/glass/{_i}", _bind(clear_glass, _sides), size=(16, 16))
    register(f"/minecraft/optifine/ctm/tinted_glass/{_i}",
             lambda ctx, s=_sides: stained_glass(ctx, TINTED[1], s, 0.85), size=(16, 16))
static_file("minecraft/optifine/ctm/glass/glass.properties", ctm_properties("glass"))
static_file("minecraft/optifine/ctm/glass/glass_pane.properties", ctm_properties("glass_pane"))
static_file("minecraft/optifine/ctm/tinted_glass/tinted_glass.properties", ctm_properties("tinted_glass"))

for _dye, _hex in DYES.items():
    _rgb = hexc(_hex)
    register(f"block/{_dye}_stained_glass", _bind(stained_glass, _rgb, TILE_SIDES[0]))
    register(f"block/{_dye}_stained_glass_pane_top", _bind(pane_top, _rgb * 0.8, 0.9))
    for _i, _sides in TILE_SIDES.items():
        register(f"/minecraft/optifine/ctm/stained_glass/{_dye}/{_i}",
                 _bind(stained_glass, _rgb, _sides), size=(16, 16))
    static_file(f"minecraft/optifine/ctm/stained_glass/{_dye}/{_dye}_stained_glass.properties",
                ctm_properties(f"{_dye}_stained_glass"))
    static_file(f"minecraft/optifine/ctm/stained_glass/{_dye}/{_dye}_stained_glass_pane.properties",
                ctm_properties(f"{_dye}_stained_glass_pane"))
