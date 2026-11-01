"""Old block textures (1.7-1.12 blocks/ names) without a direct 26.3 file."""
import numpy as np

from .kit import adopt, blank, reg, render

LEAVES = {"acacia": "acacia", "big_oak": "dark_oak", "birch": "birch", "jungle": "jungle", "oak": "oak",
          "spruce": "spruce"}


def opaque_leaves(ctx, wood):
    """Fast-graphics leaves: the fancy texture with its holes filled by a
    shadowed leaf tone (still grey, the game tints it)."""
    t = adopt(ctx, render(f"block/{wood}_leaves", ctx.s, 16, 16))
    solid = t.alpha > 0.5
    lum = t.color.mean(-1)
    base = float(np.median(lum[solid])) if solid.any() else 0.6
    n = ctx.noise(3, 2, 0.5, salt="holes")
    g = ctx.texel_noise("holes")
    v = base * (0.5 + (n - 0.5) * 0.12 + (g - 0.5) * 0.08)
    dark = np.repeat(v[..., None], 3, -1).astype(np.float32)
    hole = ~solid
    t.color[hole] = dark[hole]
    t.alpha[:] = 1.0
    t.height[hole] = 0.2
    t.sss[hole] = 0.3
    t.smooth[hole] = 0.05
    t.wrap = True
    return t


for _old, _new in LEAVES.items():
    reg(f"blocks/leaves_{_old}_opaque", lambda ctx, w=_new: opaque_leaves(ctx, w))


def dust_cross(ctx):
    line = render("block/redstone_dust_line0", ctx.s, 16, 16)
    dot = render("block/redstone_dust_dot", ctx.s, 16, 16)
    out = blank(ctx)
    out.paste(line)
    rot = line.copy()
    for k in ("color",):
        rot.color = np.rot90(line.color, 1).copy()
    for c in ("alpha", "height", "smooth", "f0", "metal", "porosity", "sss", "emissive"):
        setattr(rot, c, np.rot90(getattr(line, c), 1).copy())
    out.paste(rot)
    out.paste(dot)
    out.grain = line.grain
    return out


reg("blocks/redstone_dust_cross", dust_cross)


def debug(ctx, salt):
    t = adopt(ctx, render("block/debug", ctx.s, 16, 16))
    if salt:  # second debug texture: same pattern, colors swapped around
        t.color = t.color[..., ::-1].copy()
    return t


reg("blocks/debug", lambda ctx: debug(ctx, ""))
reg("blocks/debug2", lambda ctx: debug(ctx, "2"))
reg("blocks/flower_paeonia", lambda ctx: adopt(ctx, render("block/peony_top", ctx.s, 16, 16)))
