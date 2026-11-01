"""1.7-1.12 item glint: same design as the modern glint, on the old 64x64 sheet."""
from ...registry import TEXTURES, register


def old_glint(ctx):
    return TEXTURES["misc/enchanted_glint_item"].fn(ctx.sub("misc/enchanted_glint_item"))


register("misc/enchanted_item_glint@64x64", old_glint, size=(64, 64))
