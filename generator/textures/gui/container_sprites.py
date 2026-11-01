"""Sprites drawn over container backgrounds: progress, tabs, list entries, recipe book, advancements."""
import numpy as np

from ...registry import register
from .common import (BLACK, C, Canvas, FACE, HI, INK, SHADE, SLOT, SLOT_DK, WHITE, arrow_mask_cells,
                     flame_cells, inset, mix, panel)
from .widgets import BTN, BTN_HL, BTN_OFF, button_face

RED_, RED_D = C("e5483d"), C("6b1712")
GOLD_, GOLD_D = C("e8c24a"), C("6b4f0c")
SP = "gui/sprites/container/"


def reg(path, fn, **kw):
    register(SP + path if not path.startswith("gui/") else path, fn, **kw)


# ----------------------------------------------------------------- furnace family
def _burn(ctx):
    c = Canvas(ctx)
    cells = arrow_mask_cells()
    for (x, y) in cells:
        top = (x, y - 1) not in cells
        c.px(x, y, C("ffffff") if top else C("e3e6ec"))
    return c.tex()


def _lit(tone):
    def fn(ctx):
        c = Canvas(ctx)
        cells = flame_cells()
        pal = {"furnace": ("ff5a1e", "ff9a2a", "ffe36a"), "smoker": ("e0501a", "f08a2a", "ffd36a"),
               "blast": ("4a7cff", "8ab4ff", "e6f0ff")}[tone]
        lo, mid, hi = (C(v) for v in pal)
        for (x, y) in cells:
            inner = all((x + dx, y + dy) in cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            deep = all((x + dx, y + dy) in cells for dx in (-2, 0, 2) for dy in (-2, 0, 2))
            c.px(x, y, hi if deep and y > 8 else (mid if inner else lo))
        return c.tex()
    return fn


for _f, _t in (("furnace", "furnace"), ("smoker", "smoker"), ("blast_furnace", "blast")):
    reg(f"{_f}/burn_progress", _burn)
    reg(f"{_f}/lit_progress", _lit(_t))


# ----------------------------------------------------------------- errors / arrows
def _error(w, h):
    def fn(ctx):
        c = Canvas(ctx)
        ox, oy = (w - 18) // 2, (h - 16) // 2
        for i in range(14):
            for d in (0, 1, 2):
                c.px(ox + 2 + i + d - 1, oy + 1 + i, RED_D) if 0 <= i else None
                c.px(ox + 15 - i - d + 1, oy + 1 + i, RED_D)
        for i in range(14):
            for d in (0, 1):
                c.px(ox + 2 + i + d - 1, oy + 1 + i, RED_)
                c.px(ox + 15 - i - d + 1, oy + 1 + i, RED_)
        return c.tex()
    return fn


for _p in ("anvil", "cartography_table", "grindstone", "smithing"):
    reg(f"{_p}/error", _error(28, 21))
reg("villager/out_of_stock", _error(28, 21))
reg("loom/error", _error(26, 26))


def _text_field(disabled):
    def fn(ctx):
        c = Canvas(ctx)
        c.rect(0, 0, 110, 16, C("8e9198") if not disabled else C("5a5d66"))
        c.rect(1, 1, 108, 14, C("0c0d0f") if not disabled else C("2a2b30"))
        return c.tex()
    return fn


reg("anvil/text_field", _text_field(False))
reg("anvil/text_field_disabled", _text_field(True))


# ----------------------------------------------------------------- beacon
def _beacon_btn(state):
    def fn(ctx):
        c = Canvas(ctx)
        p = {"": BTN, "_highlighted": BTN_HL, "_disabled": BTN_OFF,
             "_selected": dict(ink=C("16171a"), hi=C("8ad8e6"), face=C("3f8f9e"), sh=C("2a6470"), sh2=C("1f4f58"))}[state]
        button_face(c, 0, 0, 22, 22, p)
        return c.tex()
    return fn


for _st in ("", "_disabled", "_highlighted", "_selected"):
    reg(f"beacon/button{_st}", _beacon_btn(_st))


def _confirm(ok):
    def fn(ctx):
        c = Canvas(ctx)
        if ok:
            rows = ["...........##", "..........##.", ".........##..", "##......##...", ".##....##....",
                    "..##..##.....", "...####......", "....##......."]
            c.art(rows, {"#": C("27621f")}, 3, 6)
            c.art(rows, {"#": C("74e06a")}, 2, 5)
        else:
            for i in range(11):
                for d in (0, 1):
                    c.px(3 + i + d, 3 + i, RED_D)
                    c.px(14 - i - d, 3 + i, RED_D)
            for i in range(11):
                c.px(3 + i, 3 + i, RED_)
                c.px(14 - i, 3 + i, RED_)
        return c.tex()
    return fn


reg("beacon/confirm", _confirm(True))
reg("beacon/cancel", _confirm(False))


# ----------------------------------------------------------------- brewing
def _brew_progress(ctx):
    c = Canvas(ctx)
    for y in range(28):
        w = 3 if y < 20 else max(0, 9 - (y - 20) * 2 + 1)
        if y < 20:
            c.rect(3, y, 3, 1, mix(C("e3e6ec"), C("ffffff"), y / 20))
        else:
            k = y - 20
            c.hline(k, 8 - k, y, C("ffffff")) if k <= 4 else None
    return c.tex()


def _bubbles(ctx):
    c = Canvas(ctx)
    col, hi = C("cfe6ff"), C("ffffff")
    for (x, y, r) in ((6, 25, 2.6), (3, 18, 2.0), (8, 12, 2.2), (4, 6, 1.6), (8, 2, 1.3)):
        c.ring(x, y, r, 1.0, col)
        c.px(int(x - r / 2), int(y - r / 2), hi)
    return c.tex()


def _fuel(ctx):
    c = Canvas(ctx)
    c.rect(0, 0, 18, 4, C("e88a2a"))
    c.hline(0, 17, 0, C("ffd27a"))
    c.hline(0, 17, 3, C("a2520e"))
    return c.tex()


reg("brewing_stand/brew_progress", _brew_progress)
reg("brewing_stand/bubbles", _bubbles)
reg("brewing_stand/fuel_length", _fuel)


# ----------------------------------------------------------------- bundle
def _bundle_border(ctx):
    c = Canvas(ctx)
    c.rect(0, 0, 12, 12, C("16171a"))
    c.rect(1, 1, 10, 10, C("6b4a2e"))
    c.rect(2, 2, 8, 8, C("2a2b30"))
    return c.tex()


def _bundle_fill(col):
    def fn(ctx):
        c = Canvas(ctx)
        c.rect(0, 0, 6, 6, C(col))
        c.hline(0, 5, 0, mix(C(col), WHITE, 0.4))
        c.hline(0, 5, 5, mix(C(col), BLACK, 0.3))
        return c.tex()
    return fn


def _bundle_slot(kind):
    def fn(ctx):
        c = Canvas(ctx)
        if kind == "background":
            inset(c, 3, 3, 18, 18, face=C("6d5a48"), dk=C("3a2c20"), hi=C("a08a72"))
        elif kind == "back":
            c.rect(4, 4, 16, 16, WHITE, 0.4)
        else:
            c.frame(3, 3, 18, 18, WHITE, 0.85)
            c.frame(2, 2, 20, 20, C("9aa6be"), 0.6)
        return c.tex()
    return fn


reg("bundle/bundle_progressbar_border", _bundle_border)
reg("bundle/bundle_progressbar_fill", _bundle_fill("6f9be8"))
reg("bundle/bundle_progressbar_full", _bundle_fill("e5483d"))
reg("bundle/slot_background", _bundle_slot("background"))
reg("bundle/slot_highlight_back", _bundle_slot("back"))
reg("bundle/slot_highlight_front", _bundle_slot("front"))


def _slot_hl(front):
    def fn(ctx):
        c = Canvas(ctx)
        if front:
            c.frame(3, 3, 18, 18, WHITE, 0.9)
            c.frame(2, 2, 20, 20, C("c9d4ea"), 0.5)
        else:
            c.rect(4, 4, 16, 16, WHITE, 0.45)
        return c.tex()
    return fn


reg("slot_highlight_back", _slot_hl(False))
reg("slot_highlight_front", _slot_hl(True))
reg("slot", lambda ctx: inset(Canvas(ctx), 0, 0, 18, 18).tex())


# ----------------------------------------------------------------- cartography
def map_paper(c, x, y, w, h):
    c.rect(x, y, w, h, C("7a6446"))
    c.rect(x + 1, y + 1, w - 2, h - 2, C("e2d3a8"))
    c.rect(x + 3, y + 3, w - 6, h - 6, C("d4c08e"))


def map_marks(c, ctx, x, y, w, h, scale=1.0):
    land = ctx.noise(10 * scale, 2, 0.5, salt="carto") > 0.5
    inside = ctx.rect(x + 4, y + 4, x + w - 4, y + h - 4)
    c.mask(land * inside, C("9aae6a"))
    c.mask((1 - land) * inside, C("8fb0c8"))


def _map(kind):
    def fn(ctx):
        c = Canvas(ctx)
        if kind == "duplicated":
            map_paper(c, 0, 16, 50, 50)
            map_paper(c, 0, 0, 50, 50)
            map_marks(c, ctx, 0, 0, 50, 50)
        else:
            map_paper(c, 0, 0, 66, 66)
            map_marks(c, ctx, 0, 0, 66, 66, 0.5 if kind == "scaled" else 1.0)
        return c.tex()
    return fn


def _locked(ctx):
    c = Canvas(ctx)
    c.rect(2, 0, 6, 1, C("2a2b30"))
    c.rect(1, 1, 2, 5, C("2a2b30"))
    c.rect(7, 1, 2, 5, C("2a2b30"))
    c.rect(2, 1, 6, 1, C("c9ccd3"))
    c.vline(2, 1, 5, C("c9ccd3"))
    c.vline(7, 1, 5, C("c9ccd3"))
    c.rect(0, 6, 10, 8, C("2a2b30"))
    c.rect(1, 7, 8, 6, GOLD_)
    c.rect(4, 8, 2, 3, GOLD_D)
    return c.tex()


reg("cartography_table/map", _map("map"))
reg("cartography_table/scaled_map", _map("scaled"))
reg("cartography_table/duplicated_map", _map("duplicated"))
reg("cartography_table/locked", _locked)


# ----------------------------------------------------------------- crafter
def _disabled_slot(ctx):
    c = Canvas(ctx)
    inset(c, 0, 0, 18, 18, face=C("5d6068"))
    for i in range(14):
        c.px(2 + i, 2 + i, C("3a3c42"))
        c.px(15 - i, 2 + i, C("3a3c42"))
    return c.tex()


def _redstone(on):
    def fn(ctx):
        c = Canvas(ctx)
        col = C("ff3a2a") if on else C("5a1a16")
        dk = C("8a0f0a") if on else C("2a0c0a")
        c.circle(8, 8, 3.5, dk)
        c.circle(8, 8, 2.5, col)
        c.rect(1, 7, 14, 2, dk)
        c.rect(2, 7, 12, 1, col)
        if on:
            c.px(7, 7, C("ffc0a0"))
        return c.tex()
    return fn


reg("crafter/disabled_slot", _disabled_slot)
reg("crafter/powered_redstone", _redstone(True))
reg("crafter/unpowered_redstone", _redstone(False))


# ----------------------------------------------------------------- scrollers (12x15)
def _scroll(disabled):
    def fn(ctx):
        c = Canvas(ctx)
        w, h = ctx.w, ctx.h
        if disabled:
            c.rect(0, 0, w, h, C("6d7079"))
            c.rect(1, 1, w - 2, h - 2, C("9a9da6"))
        else:
            c.rect(0, 0, w, h, INK)
            c.rect(1, 1, w - 2, h - 2, C("c9ccd3"))
            c.hline(1, w - 2, 1, WHITE)
            c.vline(1, 1, h - 2, WHITE)
            c.hline(2, w - 2, h - 2, C("7a7d86"))
            c.vline(w - 2, 2, h - 2, C("7a7d86"))
            for y in range(h // 2 - 2, h // 2 + 3, 2):
                c.hline(3, w - 4, y, C("8a8d95")) if w > 6 else None
        return c.tex()
    return fn


for _p in ("creative_inventory", "loom", "stonecutter", "villager"):
    reg(f"{_p}/scroller", _scroll(False))
    reg(f"{_p}/scroller_disabled", _scroll(True))


# ----------------------------------------------------------------- creative tabs (26x32)
def _ctab(top, selected):
    def fn(ctx):
        c = Canvas(ctx)
        face = FACE if selected else C("9fa2aa")
        h = 32 if selected else 28
        y0 = 0 if top else 32 - h
        y0 = (0 if top else 0)
        if top:
            y0 = 2 if not selected else 0
            c.rect(1, y0, 24, 32 - y0, INK)
            c.rect(0, y0 + 1, 26, 31 - y0 - (0 if selected else 1), INK)
            c.rect(1, y0 + 1, 24, 31 - y0, face)
            c.hline(1, 24, y0 + 1, HI)
            c.vline(1, y0 + 1, 31, HI)
            c.vline(24, y0 + 2, 31, SHADE)
            if not selected:
                c.hline(0, 25, 31, INK)
        else:
            y1 = 30 if not selected else 32
            c.rect(1, 0, 24, y1, INK)
            c.rect(0, 0, 26, y1 - 1, INK)
            c.rect(1, 0, 24, y1 - 1, face)
            c.vline(1, 0, y1 - 2, HI)
            c.vline(24, 0, y1 - 2, SHADE)
            c.hline(2, 24, y1 - 2, SHADE)
            if not selected:
                c.hline(0, 25, 0, INK)
        return c.tex()
    return fn


for _i in range(1, 8):
    for _pos in ("top", "bottom"):
        for _sel in ("selected", "unselected"):
            reg(f"creative_inventory/tab_{_pos}_{_sel}_{_i}", _ctab(_pos == "top", _sel == "selected"))


# ----------------------------------------------------------------- enchanting
def _ench_slot(state):
    def fn(ctx):
        c = Canvas(ctx)
        face = {"": C("6c5a8a"), "_highlighted": C("8b74b8"), "_disabled": C("3d3a44")}[state]
        c.rect(0, 0, 108, 19, mix(face, BLACK, 0.55))
        c.rect(1, 1, 106, 17, face)
        c.hline(1, 106, 1, mix(face, WHITE, 0.3))
        c.vline(1, 1, 16, mix(face, WHITE, 0.3))
        c.hline(2, 106, 17, mix(face, BLACK, 0.3))
        c.rect(1, 1, 18, 17, mix(face, BLACK, 0.25))
        return c.tex()
    return fn


def _ench_level(n, disabled):
    def fn(ctx):
        from . import glyphs
        c = Canvas(ctx)
        col = C("6ad640") if not disabled else C("5d6068")
        c.circle(8, 8, 7.6, mix(col, BLACK, 0.65))
        c.circle(8, 8, 6.6, col)
        c.circle(7, 7, 4.0, mix(col, WHITE, 0.25))
        g = glyphs.tiny(str(n))
        c.cells(g, 7, 6, mix(col, BLACK, 0.7))
        c.cells(g, 6, 5, WHITE if not disabled else C("9a9da6"))
        return c.tex()
    return fn


for _st in ("", "_disabled", "_highlighted"):
    reg(f"enchanting_table/enchantment_slot{_st}", _ench_slot(_st))
for _n in (1, 2, 3):
    reg(f"enchanting_table/level_{_n}", _ench_level(_n, False))
    reg(f"enchanting_table/level_{_n}_disabled", _ench_level(_n, True))


# ----------------------------------------------------------------- horse / loom / stonecutter / villager
def _chest_slots(ctx):
    c = Canvas(ctx)
    for r in range(3):
        for i in range(5):
            inset(c, i * 18, r * 18, 18, 18)
    return c.tex()


reg("horse/chest_slots", _chest_slots)


def _tile(state, w, h):
    def fn(ctx):
        c = Canvas(ctx)
        face = {"": C("8a8d95"), "_highlighted": C("a9b4cc"), "_selected": C("5d6c8c")}[state]
        c.rect(0, 0, w, h, INK)
        c.rect(1, 1, w - 2, h - 2, face)
        if state == "_selected":
            c.hline(1, w - 2, 1, mix(face, BLACK, 0.3))
            c.vline(1, 1, h - 2, mix(face, BLACK, 0.3))
        else:
            c.hline(1, w - 2, 1, mix(face, WHITE, 0.4))
            c.vline(1, 1, h - 2, mix(face, WHITE, 0.4))
            c.hline(2, w - 2, h - 2, mix(face, BLACK, 0.3))
        return c.tex()
    return fn


for _st in ("", "_highlighted", "_selected"):
    reg(f"loom/pattern{_st}", _tile(_st, 14, 14))
    reg(f"stonecutter/recipe{_st}", _tile(_st, 16, 18))


def _strike(ctx):
    c = Canvas(ctx)
    c.hline(0, 8, 0, RED_)
    c.hline(0, 8, 1, RED_D)
    return c.tex()


def _xp(kind):
    def fn(ctx):
        c = Canvas(ctx)
        if kind == "background":
            c.rect(0, 0, 102, 5, C("101114"))
            c.rect(1, 1, 100, 3, C("2c3a26"))
        else:
            col = C("6ad640") if kind == "current" else C("b8f590")
            c.rect(0, 0, 102, 5, mix(col, BLACK, 0.6))
            c.rect(1, 1, 100, 3, col)
            c.hline(1, 100, 1, mix(col, WHITE, 0.4))
        return c.tex()
    return fn


def _trade_arrow(out):
    def fn(ctx):
        c = Canvas(ctx)
        col = C("e3e6ec") if not out else C("6d7079")
        c.rect(0, 3, 5, 3, col)
        for i in range(5):
            c.vline(5 + i, i, 8 - i, col)
        if out:
            for i in range(9):
                c.px(i, i, RED_)
        return c.tex()
    return fn


reg("villager/discount_strikethrough", _strike)
for _k in ("background", "current", "result"):
    reg(f"villager/experience_bar_{_k}", _xp(_k))
reg("villager/trade_arrow", _trade_arrow(False))
reg("villager/trade_arrow_out_of_stock", _trade_arrow(True))


# ----------------------------------------------------------------- recipe book
RB = "gui/sprites/recipe_book/"


def _rb_button(hl):
    def fn(ctx):
        c = Canvas(ctx)
        button_face(c, 0, 0, 20, 18, BTN_HL if hl else BTN)
        c.rect(5, 3, 10, 12, C("2a1a0c"))
        c.rect(6, 4, 8, 10, C("3f8f4a") if not hl else C("5ab866"))
        c.vline(13, 4, 13, C("e8e2d0"))
        c.rect(8, 6, 3, 3, GOLD_)
        return c.tex()
    return fn


register(RB + "button", _rb_button(False))
register(RB + "button_highlighted", _rb_button(True))


def _overlay(kind, disabled, hl):
    def fn(ctx):
        c = Canvas(ctx)
        face = C("8a8d95") if not disabled else C("8a5a55")
        if hl:
            face = mix(face, WHITE, 0.3)
        c.rect(0, 0, 24, 24, INK)
        c.rect(1, 1, 22, 22, face)
        c.hline(1, 22, 1, mix(face, WHITE, 0.35))
        c.vline(1, 1, 21, mix(face, WHITE, 0.35))
        c.hline(2, 22, 22, mix(face, BLACK, 0.3))
        c.vline(22, 2, 22, mix(face, BLACK, 0.3))
        return c.tex()
    return fn


for _k in ("crafting", "furnace"):
    for _d in (False, True):
        for _h in (False, True):
            name = f"{_k}_overlay" + ("_disabled" if _d else "") + ("_highlighted" if _h else "")
            register(RB + name, _overlay(_k, _d, _h))


def _filter(kind, enabled, hl):
    def fn(ctx):
        c = Canvas(ctx)
        p = BTN_HL if hl else BTN
        if enabled:
            p = dict(p, face=C("5c9a56") if not hl else C("74b86c"), hi=C("9ad890"), sh=C("3d6a38"), sh2=C("2f552b"))
        button_face(c, 0, 0, 26, 16, p)
        if kind == "crafting":
            for (x, y) in ((8, 4), (12, 4), (16, 4), (8, 8), (12, 8), (16, 8)):
                c.rect(x, y, 3, 3, C("3a2a1a"))
                c.rect(x, y, 2, 2, C("c49a5a"))
        else:
            for (x, y) in flame_cells():
                if x % 2 == 0 and y % 2 == 0:
                    c.px(7 + x // 2 + 2, 2 + y // 2 + 2, C("ff9a2a"))
        return c.tex()
    return fn


for _k, _pre in (("crafting", "filter"), ("furnace", "furnace_filter")):
    for _e in (False, True):
        for _h in (False, True):
            register(RB + f"{_pre}_{'enabled' if _e else 'disabled'}" + ("_highlighted" if _h else ""),
                     _filter(_k, _e, _h))


def _overlay_recipe(ctx):
    c = Canvas(ctx)
    c.rect(1, 0, 30, 32, INK)
    c.rect(0, 1, 32, 30, INK)
    c.rect(1, 1, 30, 30, C("c2c4ca"))
    c.hline(1, 30, 1, HI)
    c.vline(1, 1, 30, HI)
    c.hline(2, 30, 30, SHADE)
    c.vline(30, 2, 30, SHADE)
    return c.tex()


register(RB + "overlay_recipe", _overlay_recipe)


def _rb_page(forward, hl):
    def fn(ctx):
        c = Canvas(ctx)
        col = C("f4f5f7") if hl else C("b9bcc4")
        for i in range(8):
            x = (2 + i) if forward else (9 - i)
            c.vline(x + 1, 1 + i + 1, 15 - i + 1, INK)
        for i in range(8):
            x = (2 + i) if forward else (9 - i)
            c.vline(x, 1 + i, 15 - i, col)
        return c.tex()
    return fn


register(RB + "page_forward", _rb_page(True, False))
register(RB + "page_forward_highlighted", _rb_page(True, True))
register(RB + "page_backward", _rb_page(False, False))
register(RB + "page_backward_highlighted", _rb_page(False, True))


def _rb_slot(craftable, many):
    def fn(ctx):
        c = Canvas(ctx)
        face = C("8a8d95") if craftable else C("a0605a")
        if many:
            c.rect(3, 3, 22, 22, INK)
            c.rect(4, 4, 20, 20, mix(face, BLACK, 0.2))
        c.rect(0, 0, 23 if many else 25, 23 if many else 25, INK)
        c.rect(1, 1, 21 if many else 23, 21 if many else 23, face)
        s = 21 if many else 23
        c.hline(1, s, 1, mix(face, WHITE, 0.35))
        c.vline(1, 1, s, mix(face, WHITE, 0.35))
        c.hline(2, s, s, mix(face, BLACK, 0.3))
        c.vline(s, 2, s, mix(face, BLACK, 0.3))
        return c.tex()
    return fn


register(RB + "slot_craftable", _rb_slot(True, False))
register(RB + "slot_many_craftable", _rb_slot(True, True))
register(RB + "slot_uncraftable", _rb_slot(False, False))
register(RB + "slot_many_uncraftable", _rb_slot(False, True))


def _rb_tab(selected):
    def fn(ctx):
        c = Canvas(ctx)
        x0 = 0 if selected else 4
        face = FACE if selected else C("9fa2aa")
        c.rect(x0 + 1, 0, 35 - x0 - 1, 27, INK)
        c.rect(x0, 1, 35 - x0, 25, INK)
        c.rect(x0 + 1, 1, 35 - x0 - 1, 25, face)
        c.hline(x0 + 1, 34, 1, HI)
        c.vline(x0 + 1, 1, 25, HI)
        c.hline(x0 + 2, 34, 25, SHADE)
        return c.tex()
    return fn


register(RB + "tab", _rb_tab(False))
register(RB + "tab_selected", _rb_tab(True))


# ----------------------------------------------------------------- advancement frames & tabs
AD = "gui/sprites/advancements/"


def _frame(kind, obtained):
    def fn(ctx):
        c = Canvas(ctx)
        face = C("e2b23a") if obtained else C("a9adb6")
        dk = C("5a3f0a") if obtained else C("2c2f36")
        lt = mix(face, WHITE, 0.45)
        if kind == "task":
            m = ctx.rect(1, 1, 25, 25)
            inner = ctx.rect(3, 3, 23, 23)
        elif kind == "goal":
            m = np.maximum(ctx.rect(4, 1, 22, 25), np.maximum(ctx.rect(1, 4, 25, 22), ctx.circle(13, 13, 12.2)))
            inner = np.maximum(ctx.rect(5, 3, 21, 23), ctx.rect(3, 5, 23, 21))
        else:
            pts = []
            import math
            for k in range(16):
                r = 12.8 if k % 2 == 0 else 10.2
                a = math.pi * 2 * k / 16 + math.pi / 16
                pts.append((13 + r * math.cos(a), 13 + r * math.sin(a)))
            m = ctx.polygon(pts)
            inner = ctx.circle(13, 13, 9.2)
        c.mask(m, dk)
        c.mask(m * (ctx.edge(m, 1, "tl") == 0) * (ctx.edge(m, 1, "br") == 0), face)
        c.mask(ctx.edge(m, 1.0) * 0 + (ctx.edge(m * (ctx.edge(m, 1) == 0), 1, "tl")), lt)
        c.mask(inner, mix(face, BLACK, 0.45) if obtained else C("3a3d45"))
        c.mask(ctx.edge(inner, 1, "br"), mix(face, WHITE, 0.2))
        return c.tex()
    return fn


for _k in ("task", "goal", "challenge"):
    reg(AD + f"{_k}_frame_obtained", _frame(_k, True))
    reg(AD + f"{_k}_frame_unobtained", _frame(_k, False))


def _adv_tab(side, selected):
    def fn(ctx):
        c = Canvas(ctx)
        w, h = ctx.w, ctx.h
        face = FACE if selected else C("9fa2aa")
        inset_ = 0 if selected else 3
        if side == "above":
            x, y, ww, hh = 0, inset_, w, h - inset_
        elif side == "below":
            x, y, ww, hh = 0, 0, w, h - inset_
        elif side == "left":
            x, y, ww, hh = inset_, 0, w - inset_, h
        else:
            x, y, ww, hh = 0, 0, w - inset_, h
        c.rect(x + 1, y, ww - 2, hh, INK)
        c.rect(x, y + 1, ww, hh - 2, INK)
        c.rect(x + 1, y + 1, ww - 2, hh - 2, face)
        c.hline(x + 1, x + ww - 2, y + 1, HI)
        c.vline(x + 1, y + 1, y + hh - 2, HI)
        c.hline(x + 2, x + ww - 2, y + hh - 2, SHADE)
        c.vline(x + ww - 2, y + 2, y + hh - 2, SHADE)
        if selected:  # open toward the window
            if side == "above":
                c.rect(1, h - 3, w - 2, 3, face)
            elif side == "below":
                c.rect(1, 0, w - 2, 3, face)
            elif side == "left":
                c.rect(w - 3, 1, 3, h - 2, face)
            else:
                c.rect(0, 1, 3, h - 2, face)
        return c.tex()
    return fn


for _side, _parts in (("above", ("left", "middle", "right")), ("below", ("left", "middle", "right")),
                      ("left", ("top", "middle", "bottom")), ("right", ("top", "middle", "bottom"))):
    for _p in _parts:
        reg(AD + f"tab_{_side}_{_p}", _adv_tab(_side, False))
        reg(AD + f"tab_{_side}_{_p}_selected", _adv_tab(_side, True))
