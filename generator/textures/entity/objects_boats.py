"""Boats and chest boats for every wood type (bamboo uses the raft model).

Layouts from the CEM templates boat/chest_boat/raft/chest_raft.jem.
Boat (128x64): bottom uv(0,0) 28x16x3, back (0,19) 18x6x2, front (0,27)
16x6x2, right (0,35) 28x6x2, left (0,43) 28x6x2, paddles (62,0)/(62,20): shaft
2x2x18 + blade 1x6x7 at the same offset.
Raft (128x64): bottom (0,0) 28x20x4 (+28x16x4), paddles (0,24)/(40,24).
Chest boats (128x128) add chest base (0,76) 12x8x12, lid (0,59) 12x5x12,
knob (0,59) 2x4x1.
"""
import numpy as np

from ...engine import IRON, pal
from ...registry import register
from .objects_common import Sheet, frame, wood_field

# Own boat palettes (dark -> light), close to each wood's plank color.
BOAT_WOODS = {
    "oak": pal("4e371c", "6f512c", "86643a", "9a7546", "ad8752", "be985e"),
    "spruce": pal("2e1f12", "45301c", "573d24", "68492c", "775535", "86613e"),
    "birch": pal("8a7c52", "a89a68", "bcae7a", "cbbd88", "d8cb96", "e4d8a6"),
    "jungle": pal("5a3a24", "7c5236", "926242", "a5714c", "b58056", "c48e62"),
    "acacia": pal("6a3018", "8f4426", "a8522e", "bc5f36", "cc6c40", "da7a4c"),
    "dark_oak": pal("22150a", "33210f", "422b15", "50351b", "5d3f22", "6a4929"),
    "mangrove": pal("4a1a18", "6a2a24", "7f352c", "924034", "a24b3c", "b25846"),
    "cherry": pal("8a5450", "b07a72", "c68e84", "d6a096", "e2b0a6", "ecc2b8"),
    "pale_oak": pal("8a8278", "aca498", "c0b8ac", "cec8bc", "dad4ca", "e6e2d8"),
    "poplar": pal("6e6650", "8e8466", "a39878", "b4a986", "c3b994", "d0c8a4"),
    "bamboo": pal("6a5a1a", "8f7c26", "aa9632", "c0aa3e", "d0bb4c", "dccb5e"),
}
CHEST_WOOD = pal("3d2712", "5a3b1c", "744d26", "8a5e30", "9e6e39", "b17f44")
IRON_P = pal("34343a", "5d5d66", "8a8a94", "b5b5bf", "dcdce4")


def _wood_faces(ctx, sh, faces, p, salt, board_px=4, along="x", rim=True, skip=()):
    c, h = wood_field(ctx, p, salt=salt, along=along, board_px=board_px)
    for name, r in faces.items():
        if name in skip or r[2] <= r[0] or r[3] <= r[1]:
            continue
        m = sh.rect(r)
        sh.put(m, c, height=h, smooth=0.25, porosity=0.25)
        if rim:
            sh.put(frame(ctx, r, 1) & m, ctx.palette(p[:2], ctx.texel_noise("rim" + salt)), height=0.6)
            sh.shade(frame(ctx, (r[0] + 1, r[1] + 1, r[2] - 1, r[3] - 1), 1, "t") & m, 1.12)


def _paddle(ctx, sh, u, v, p):
    shaft = sh.faces(u, v, 2, 2, 18)
    blade = sh.faces(u, v, 1, 6, 7)
    c, h = wood_field(ctx, p, salt="paddle", along="x", board_px=99, seam=False)
    for r in shaft.values():
        sh.put(sh.rect(r), c * 0.92, height=h, smooth=0.3)
    for name, r in blade.items():
        m = sh.rect(r)
        sh.put(m, np.clip(c * 1.06, 0, 1), height=h, smooth=0.3)
        sh.put(frame(ctx, r, 1) & m, p[1], height=0.55)
    # Grip wrap near the end of the shaft.
    for name in ("right", "left"):
        x0, y0, x1, y1 = shaft[name]
        grip = ctx.rect(x0 + (0 if name == "right" else 13), y0, x0 + (5 if name == "right" else 18), y1) > 0.5
        sh.put(grip, ctx.palette(pal("3a2414", "553620", "6a462a"), ctx.texel_noise("grip")), height=0.6)


def _chest(ctx, sh):
    c, h = wood_field(ctx, CHEST_WOOD, salt="cb", along="x", board_px=4)
    metal = ctx.palette(IRON_P[1:-1], ctx.noise(2, 1, salt="cbm") * 0.6 + 0.2)
    for faces in (sh.faces(0, 76, 12, 8, 12), sh.faces(0, 59, 12, 5, 12)):
        for name, r in faces.items():
            m = sh.rect(r)
            sh.put(m, c, height=h, smooth=0.22, porosity=0.25)
            sh.put(frame(ctx, r, 1) & m, CHEST_WOOD[0], height=0.62)
            for cx in (r[0], r[2] - 1):
                for cy in (r[1], r[3] - 1):
                    sh.put(ctx.rect(cx, cy, cx + 1, cy + 1) > 0.5, metal, height=0.8, metal=IRON)
    lock = sh.faces(0, 59, 2, 4, 1)
    for r in lock.values():
        sh.put(sh.rect(r), metal, height=0.8, metal=IRON, smooth=0.6)
        sh.bevel(r, 1.2, 0.75)


def boat(ctx, wood, chest=False):
    sh = Sheet(ctx)
    p = BOAT_WOODS[wood]
    if wood == "bamboo":
        return raft(ctx, sh, p, chest)
    _wood_faces(ctx, sh, sh.faces(0, 0, 28, 16, 3), p, "hull", board_px=4)
    for i, (u, v, w) in enumerate(((0, 19, 18), (0, 27, 16), (0, 35, 28), (0, 43, 28))):
        faces = sh.faces(u, v, w, 6, 2)
        _wood_faces(ctx, sh, faces, p, f"wall{i}", board_px=3)
        # Gunwale: the top rim of each wall is a lighter cap rail.
        for name in ("front", "back"):
            r = faces[name]
            sh.shade(ctx.rect(r[0], r[1], r[2], r[1] + 1), 1.2)
    _paddle(ctx, sh, 62, 0, p)
    _paddle(ctx, sh, 62, 20, p)
    if chest:
        _chest(ctx, sh)
    return sh.tex(grain=0.05)


def raft(ctx, sh, p, chest):
    """Bamboo raft: stalks along the length with node rings."""
    for u, v, w, h, d in ((0, 0, 28, 20, 4), (0, 0, 28, 16, 4)):
        for name, r in sh.faces(u, v, w, h, d).items():
            m = sh.rect(r)
            lx, ly, fw, fh = sh.local(r)
            horizontal = fw >= fh
            across = ly if horizontal else lx
            along = lx if horizontal else ly
            stalk = np.floor(across / 3).astype(int)
            pos = across - stalk * 3
            v_ = 0.65 - (pos - 1) * 0.18 + ctx.texel_noise("rf") * 0.15
            col = ctx.palette(p[1:], np.clip(v_, 0, 1))
            col = np.where((pos >= 2)[..., None], p[1], col)
            node = ((np.floor(along).astype(int) + stalk * 5) % 9) == 0
            col = np.where(node[..., None], p[2], col)
            sh.put(m, col, height=0.5 + (1 - np.abs(pos - 1)) * 0.15, smooth=0.35, porosity=0.15)
            if not horizontal or fh < 5:
                sh.put(frame(ctx, r, 1) & m, p[0], height=0.4)
    # Lashing bands.
    for x in (8, 22):
        band = (ctx.rect(4 + x, 0, 6 + x, 24) > 0.5) & (sh.alpha > 0.5)
        sh.put(band, ctx.palette(pal("4a3a1a", "6a5428", "8a7036"), ctx.texel_noise("lash")), height=0.7)
    _paddle(ctx, sh, 0, 24, p)
    _paddle(ctx, sh, 40, 24, p)
    if chest:
        _chest(ctx, sh)
    return sh.tex(grain=0.05)


for _w in BOAT_WOODS:
    register(f"entity/boat/{_w}", (lambda w: lambda ctx: boat(ctx, w))(_w))
    register(f"entity/chest_boat/{_w}", (lambda w: lambda ctx: boat(ctx, w, True))(_w))
