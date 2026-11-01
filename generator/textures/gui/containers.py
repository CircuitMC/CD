"""Container screen backgrounds (gui/container/*.png) at the game's slot positions."""
from ...registry import register
from .legacy_embed import embed
from .common import (BLACK, C, Canvas, FACE, HI, INK, SHADE, SLOT, SLOT_DK, WHITE, arrow_mask_cells,
                     big_slot, flame_cells, grid, inset, item_slot, mix, panel, player_inventory, slot)

EMPTY = C("8b8e96")      # empty indicator (arrow / flame silhouettes)
DARK = C("16171b")       # render boxes / list wells


def well(c, x, y, w, h, col=DARK):
    inset(c, x, y, w, h, face=col)
    return c


def empty_arrow(c, x, y):
    for (px, py) in arrow_mask_cells():
        c.px(x + px, y + py, EMPTY)
    # carved look: darker top edge
    cells = arrow_mask_cells()
    for (px, py) in cells:
        if (px, py - 1) not in cells:
            c.px(x + px, y + py, mix(EMPTY, BLACK, 0.3))
    return c


def small_arrow(c, x, y, col=EMPTY):
    """16x11 arrow used where no progress sprite is drawn."""
    c.rect(x, y + 4, 10, 3, col)
    for i in range(6):
        c.vline(x + 10 + i, y + i, y + 10 - i, col)


def empty_flame(c, x, y):
    for (px, py) in flame_cells():
        c.px(x + px, y + py, EMPTY)


def plus(c, x, y, col=EMPTY):
    c.rect(x + 5, y, 3, 13, col)
    c.rect(x, y + 5, 13, 3, col)


def base(ctx, w=176, h=166):
    c = Canvas(ctx)
    panel(c, 0, 0, w, h)
    return c


def bg(fn):
    def wrap(ctx):
        return fn(ctx)
    return wrap


# ----------------------------------------------------------------- generic storage
@bg
def inventory(ctx):
    c = base(ctx)
    for i in range(4):
        item_slot(c, 8, 8 + i * 18)
    item_slot(c, 77, 62)
    well(c, 26, 8, 50, 70)
    grid(c, 98, 18, 2, 2)
    item_slot(c, 154, 28)
    small_arrow(c, 136, 31)
    player_inventory(c, 8, 84)
    return c


@bg
def crafting_table(ctx):
    c = base(ctx)
    grid(c, 30, 17, 3, 3)
    big_slot(c, 124, 35)
    empty_arrow(c, 89, 34)
    player_inventory(c, 8, 84)
    return c


@bg
def crafter(ctx):
    c = base(ctx)
    grid(c, 26, 17, 3, 3)
    big_slot(c, 134, 35)
    small_arrow(c, 106, 38)
    player_inventory(c, 8, 84)
    return c


def furnace_like(ctx, accent):
    c = base(ctx)
    item_slot(c, 56, 17)
    item_slot(c, 56, 53)
    empty_flame(c, 56, 36)
    empty_arrow(c, 79, 34)
    big_slot(c, 116, 35)
    if accent is not None:
        c.hline(50, 77, 72, accent)
    player_inventory(c, 8, 84)
    return c


@bg
def generic_54(ctx):
    c = base(ctx, 176, 222)
    grid(c, 8, 18, 9, 6)
    player_inventory(c, 8, 140)
    return c


@bg
def shulker_box(ctx):
    c = base(ctx)
    grid(c, 8, 18, 9, 3)
    player_inventory(c, 8, 84)
    return c


@bg
def dispenser(ctx):
    c = base(ctx)
    grid(c, 62, 17, 3, 3)
    player_inventory(c, 8, 84)
    return c


@bg
def hopper(ctx):
    c = base(ctx, 176, 133)
    grid(c, 44, 20, 5, 1)
    player_inventory(c, 8, 51)
    return c


# ----------------------------------------------------------------- workstations
@bg
def brewing_stand(ctx):
    c = base(ctx)
    pipe = C("9a9da6")
    # glass tubes from the ingredient down to the three bottles
    c.rect(86, 35, 3, 6, pipe)
    c.rect(63, 40, 49, 3, pipe)
    c.rect(63, 40, 3, 10, pipe)
    c.rect(109, 40, 3, 10, pipe)
    c.rect(86, 40, 3, 17, pipe)
    for (x, y) in ((56, 51), (79, 58), (102, 51)):
        item_slot(c, x, y)
    item_slot(c, 79, 17)
    item_slot(c, 17, 17)
    # fuel gauge well + bubble column + brew arrow troughs
    well(c, 59, 43, 20, 6, C("2a2b30"))
    for i in range(3):
        c.rect(64 + i * 4, 15 + i * 2, 2, 26 - i * 4, mix(EMPTY, FACE, 0.3))
    c.rect(97, 16, 9, 28, mix(EMPTY, FACE, 0.3))
    c.rect(18, 36, 14, 4, mix(EMPTY, FACE, 0.3))
    player_inventory(c, 8, 84)
    return c


@bg
def enchanting_table(ctx):
    c = base(ctx)
    item_slot(c, 15, 47)
    item_slot(c, 35, 47)
    well(c, 59, 13, 110, 59)
    # lectern stand under the floating book
    c.rect(18, 36, 22, 3, mix(C("6b4423"), FACE, 0.2))
    player_inventory(c, 8, 84)
    return c


@bg
def anvil(ctx):
    c = base(ctx)
    item_slot(c, 27, 47)
    item_slot(c, 76, 47)
    big_slot(c, 134, 47)
    plus(c, 52, 49)
    empty_arrow(c, 101, 47)
    # hammer badge next to the name field
    c.rect(18, 22, 9, 5, C("5d6068"))
    c.rect(21, 27, 3, 6, C("8a5a2e"))
    c.hline(18, 26, 22, C("9a9da6"))
    player_inventory(c, 8, 84)
    return c


@bg
def smithing(ctx):
    c = base(ctx)
    item_slot(c, 8, 48)
    item_slot(c, 26, 48)
    item_slot(c, 44, 48)
    big_slot(c, 98, 48)
    empty_arrow(c, 67, 47)
    well(c, 121, 8, 48, 71, C("26272c"))
    player_inventory(c, 8, 84)
    return c


@bg
def grindstone(ctx):
    c = base(ctx)
    item_slot(c, 49, 19)
    item_slot(c, 49, 40)
    big_slot(c, 129, 34)
    empty_arrow(c, 94, 33)
    # stone wheel decoration
    c.circle(31, 38, 11, C("7a7d86"))
    c.circle(31, 38, 9, C("9a9da6"))
    c.circle(31, 38, 3, C("6b4423"))
    c.rect(28, 50, 7, 14, C("6b4423"))
    player_inventory(c, 8, 84)
    return c


@bg
def stonecutter(ctx):
    c = base(ctx)
    item_slot(c, 20, 33)
    big_slot(c, 143, 33)
    well(c, 51, 13, 66, 56)
    well(c, 118, 14, 14, 57, C("2a2b30"))
    player_inventory(c, 8, 84)
    return c


@bg
def loom(ctx):
    c = base(ctx)
    item_slot(c, 13, 26)
    item_slot(c, 33, 26)
    item_slot(c, 23, 45)
    big_slot(c, 143, 58)
    well(c, 59, 12, 58, 58)
    well(c, 118, 12, 14, 58, C("2a2b30"))
    well(c, 138, 6, 26, 44, C("26272c"))
    player_inventory(c, 8, 84)
    return c


@bg
def cartography_table(ctx):
    c = base(ctx)
    item_slot(c, 15, 15)
    item_slot(c, 15, 52)
    big_slot(c, 145, 39)
    well(c, 66, 12, 68, 68, C("26272c"))
    small_arrow(c, 40, 40)
    player_inventory(c, 8, 84)
    return c


@bg
def beacon(ctx):
    c = base(ctx, 230, 219)
    # power columns: primary (left) and secondary (right)
    well(c, 14, 14, 92, 92, C("2a2c33"))
    well(c, 124, 14, 92, 92, C("2a2c33"))
    for tier in range(4):  # stepped pyramid marks beside each primary row
        w = 4 + tier * 3
        c.rect(22 - w // 2, 26 + tier * 25 - 4, w, 2, C("6fd2e0") if tier < 3 else C("e8c24a"))
    item_slot(c, 136, 110)
    c.rect(20, 108, 110, 22, mix(FACE, BLACK, 0.06))
    player_inventory(c, 36, 137)
    return c


def mount(ctx):
    c = base(ctx)
    item_slot(c, 8, 18)
    item_slot(c, 8, 36)
    well(c, 25, 17, 54, 54)
    player_inventory(c, 8, 84)
    return c


@bg
def villager(ctx):
    c = Canvas(ctx)
    panel(c, 0, 0, 276, 166)
    well(c, 4, 16, 96, 144, C("2a2c33"))
    well(c, 93, 17, 8, 142, C("1a1b1f"))
    item_slot(c, 136, 37)
    item_slot(c, 162, 37)
    big_slot(c, 220, 37)
    empty_arrow(c, 186, 35)
    player_inventory(c, 108, 84)
    return c


# ----------------------------------------------------------------- creative inventory
def creative(ctx, kind):
    c = Canvas(ctx)
    panel(c, 0, 0, 195, 136)
    if kind == "inventory":
        for (x, y) in ((54, 6), (54, 33), (108, 6), (108, 33), (35, 20)):
            item_slot(c, x, y)
        well(c, 72, 5, 34, 45)
        grid(c, 9, 54, 9, 3)
        grid(c, 9, 112, 9, 1)
        item_slot(c, 173, 112)
        c.rect(175, 114, 12, 12, C("6b1712"), 0.25)
    else:
        grid(c, 9, 18, 9, 5)
        grid(c, 9, 112, 9, 1)  # hotbar row (drawn from the background by the game)
        well(c, 174, 17, 14, 112, C("2a2b30"))
        if kind == "search":
            well(c, 80, 4, 90, 12, C("0c0d0f"))
        embed(c, ctx, "creative_items")
    return c.tex()


def _gamemode(ctx):
    c = Canvas(ctx)
    c.rect(1, 0, 123, 75, C("101114"), 0.92)
    c.rect(0, 1, 125, 73, C("101114"), 0.92)
    c.rect(1, 1, 123, 73, C("2b2d34"), 0.92)
    c.frame(1, 1, 123, 73, C("4a4e5a"))
    embed(c, ctx, "gamemode_switcher")
    return c.tex()


# ----------------------------------------------------------------- registration
for _n, _fn in (("inventory", inventory), ("crafting_table", crafting_table), ("crafter", crafter),
                ("generic_54", generic_54), ("shulker_box", shulker_box), ("dispenser", dispenser),
                ("hopper", hopper), ("brewing_stand", brewing_stand), ("enchanting_table", enchanting_table),
                ("anvil", anvil), ("smithing", smithing), ("grindstone", grindstone),
                ("stonecutter", stonecutter), ("loom", loom), ("cartography_table", cartography_table),
                ("beacon", beacon), ("villager", villager)):
    register(f"gui/container/{_n}", lambda ctx, f=_fn, n=_n: embed(f(ctx), ctx, n).tex())

register("gui/container/furnace", lambda ctx: embed(furnace_like(ctx, None), ctx, "furnace").tex())
register("gui/container/smoker", lambda ctx: embed(furnace_like(ctx, C("8a5a2e")), ctx, "smoker").tex())
register("gui/container/blast_furnace", lambda ctx: embed(furnace_like(ctx, C("6a7cae")), ctx, "blast_furnace").tex())
register("gui/container/horse", lambda ctx: embed(mount(ctx), ctx, "horse").tex())
register("gui/container/nautilus", lambda ctx: mount(ctx).tex())
register("gui/container/creative_inventory/tab_inventory", lambda ctx: creative(ctx, "inventory"))
register("gui/container/creative_inventory/tab_items", lambda ctx: creative(ctx, "items"))
register("gui/container/creative_inventory/tab_item_search", lambda ctx: creative(ctx, "search"))
register("gui/container/gamemode_switcher", _gamemode)
