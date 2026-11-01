"""Shared entity helpers (read-only for both entity work areas).

Minecraft boxes are unwrapped from a texture offset (u, v) with box size
(w, h, d) in texels:

            [ top  w x d ][ bottom w x d ]
    [ right d x h ][ front w x h ][ left d x h ][ back w x h ]

top at (u+d, v), bottom at (u+d+w, v), right at (u, v+d), front at (u+d, v+d),
left at (u+d+w, v+d), back at (u+2d+w, v+d).
"""


def box_faces(u, v, w, h, d):
    """Texel rects (x0, y0, x1, y1) of each face of a box UV unwrap."""
    return {
        "top": (u + d, v, u + d + w, v + d),
        "bottom": (u + d + w, v, u + d + 2 * w, v + d),
        "right": (u, v + d, u + d, v + d + h),
        "front": (u + d, v + d, u + d + w, v + d + h),
        "left": (u + d + w, v + d, u + 2 * d + w, v + d + h),
        "back": (u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h),
    }


def box_mask(ctx, u, v, w, h, d, faces=None):
    """Union mask of the selected faces (default: all six)."""
    m = ctx.zeros()
    for name, (x0, y0, x1, y1) in box_faces(u, v, w, h, d).items():
        if faces is None or name in faces:
            m = m + ctx.rect(x0, y0, x1, y1)
    return (m > 0).astype("float32")
