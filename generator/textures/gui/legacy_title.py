"""Old title-screen textures: pre-1.20 split logo sheet, small edition banner, loading splash,
old panorama face sizes. Everything shows the original CircuitMC wordmark."""
from ...registry import register
from .common import C, Canvas, WHITE
from .scenes import _panorama, word_cells, wordmark


def _logo_256(ctx):
    """1.7-1.19: logo halves 155x44 at (0,0) and (0,45); the game draws them side by side."""
    from ...engine import Ctx
    text = "CIRCUITMC"
    cells, w = word_cells(text)
    big = Ctx("gui/title/minecraft", 310, 44, ctx.s)
    px = min((310 - 12) // (w + 1), (44 - 8) // 8)
    x0 = (310 - w * px) // 2 - px // 4
    y0 = (44 - 7 * px) // 2 - px // 4
    full = wordmark(big, text, px, x0, y0, depth=2)
    c = Canvas(ctx)
    from .legacy_common import put_canvas
    put_canvas(c, full, 0, 0, crop=(0, 0, 155, 44))
    put_canvas(c, full, 0, 45, crop=(155, 0, 310, 44))
    return c.tex()


register("gui/title/minecraft@256x256", _logo_256, size=(256, 256))


def _edition_small(ctx):
    # Old title screens only show the top-left 98x14 of this sheet.
    text = "DEFAULT EDITION"
    cells, w = word_cells(text)
    if w > 96:
        text = "DEFAULT"
        cells, w = word_cells(text)
    c = Canvas(ctx)
    x0 = max(0, (98 - w) // 2)
    y0 = (14 - 7) // 2
    for (gx, gy) in cells:
        c.px(x0 + gx + 1, y0 + gy + 1, C("5a3a0a"))
    for (gx, gy) in cells:
        c.px(x0 + gx, y0 + gy, C("f2c33a") if gy > 0 else C("ffe58a"))
    return c.tex()


register("gui/title/edition@128x16", _edition_small, size=(128, 16))


def _mojang_splash(ctx):
    """Pre-1.16 loading splash: whole wordmark centred on white."""
    c = Canvas(ctx, bg=C("f4f4f4"))
    text = "CIRCUITMC"
    cells, w = word_cells(text)
    px = max(1, (ctx.w - ctx.w // 8) // (w + 2))
    x0 = (ctx.w - w * px) // 2
    y0 = (ctx.h - 7 * px) // 2
    logo = wordmark(ctx, text, px, x0, y0, depth=2)
    c.paste(logo, 0, 0)
    return c.tex()


register("gui/title/mojang", _mojang_splash, size=(512, 512))
register("gui/title/mojang@256x256", _mojang_splash, size=(256, 256))

for _i in range(6):
    for _s in (256, 1024):
        register(f"gui/title/background/panorama_{_i}@{_s}x{_s}", _panorama(_i), size=(_s, _s))

# 1.16+ jars index the panorama faces as 1x1 placeholders while the game reads real cube faces:
# expose 512x512 faces (and the 16x128 overlay) under the placeholder size key as well.
for _i in range(6):
    register(f"gui/title/background/panorama_{_i}@1x1", _panorama(_i), size=(512, 512))
from .scenes import _overlay  # noqa: E402
register("gui/title/background/panorama_overlay@1x1", _overlay, size=(16, 128))
