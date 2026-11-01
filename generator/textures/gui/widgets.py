"""Buttons, sliders, text fields, tabs, scrollers, tooltips, toasts, list/menu backgrounds."""
import numpy as np

from ...engine import Tex
from ...registry import register
from .common import (BLACK, C, Canvas, FACE, GOLD, GREEN, HI, INK, RED, SHADE, WHITE, bevel, inset,
                     mix, panel)

# button colour sets: outline, top highlight, face, bottom shade
BTN = dict(ink=C("16171a"), hi=C("b3b7c0"), face=C("858992"), sh=C("5a5e67"), sh2=C("4c4f57"))
BTN_HL = dict(ink=C("eef2f8"), hi=C("c9d4ea"), face=C("8f9db9"), sh=C("63708c"), sh2=C("55617a"))
BTN_OFF = dict(ink=C("1c1d20"), face=C("45474c"))
REALMS = dict(ink=C("16171a"), hi=C("a9d3a0"), face=C("6f9a68"), sh=C("4b6d46"), sh2=C("3f5c3b"))
REALMS_HL = dict(ink=C("eef8ec"), hi=C("c7ecbf"), face=C("80b578"), sh=C("588452"), sh2=C("4a7045"))


def button_face(c, x, y, w, h, p):
    """Raised button with 1-texel outline (corners keep a 3-texel border)."""
    c.rect(x, y, w, h, p["ink"])
    c.rect(x + 1, y + 1, w - 2, h - 2, p["face"])
    if "hi" in p:
        c.hline(x + 1, x + w - 2, y + 1, p["hi"])
        c.vline(x + 1, y + 1, y + h - 3, p["hi"])
        c.hline(x + 1, x + w - 2, y + h - 2, p["sh2"])
        c.hline(x + 2, x + w - 2, y + h - 3, p["sh"])
        c.vline(x + w - 2, y + 2, y + h - 2, p["sh"])
        c.px(x + 1, y + h - 3, p["face"])
    return c


def _button(p):
    def fn(ctx):
        c = Canvas(ctx)
        button_face(c, 0, 0, ctx.w, ctx.h, p)
        return c.tex()
    return fn


for base in ("widget", "friends"):
    register(f"gui/sprites/{base}/button", _button(BTN))
    register(f"gui/sprites/{base}/button_highlighted", _button(BTN_HL))
    register(f"gui/sprites/{base}/button_disabled", _button(BTN_OFF))
register("gui/sprites/widget/realms_button", _button(REALMS))
register("gui/sprites/widget/realms_button_highlighted", _button(REALMS_HL))
register("gui/sprites/widget/realms_button_disabled", _button(BTN_OFF))


def _flat_box(fill, edge, a=1.0):
    def fn(ctx):
        c = Canvas(ctx)
        c.rect(0, 0, ctx.w, ctx.h, edge)
        c.rect(1, 1, ctx.w - 2, ctx.h - 2, fill, a)
        if a < 1:
            c.a[ctx.s:-ctx.s, ctx.s:-ctx.s] = a
        return c.tex()
    return fn


register("gui/sprites/widget/text_field", _flat_box(C("0c0d0f"), C("8e9198")))
register("gui/sprites/widget/text_field_highlighted", _flat_box(C("0c0d0f"), C("f2f3f5")))
register("gui/sprites/widget/slider", _flat_box(C("26272b"), C("0f1012")))
register("gui/sprites/widget/slider_highlighted", _flat_box(C("26272b"), C("dfe5ef")))


def _preedit(ctx):
    c = Canvas(ctx)
    c.frame(0, 0, ctx.w, ctx.h, C("d6dbe6"))
    c.rect(1, 1, ctx.w - 2, ctx.h - 2, C("2a3550"), 0.55)
    return c.tex()


register("gui/sprites/widget/preedit", _preedit)


def _slider_handle(p):
    def fn(ctx):
        c = Canvas(ctx)
        c.rect(0, 0, 8, 20, p["ink"])
        c.rect(1, 1, 6, 18, p["face"])
        c.hline(1, 6, 1, p["hi"])
        c.vline(1, 1, 16, p["hi"])
        c.hline(1, 6, 18, p["sh2"])
        c.hline(2, 6, 17, p["sh"])
        c.vline(6, 2, 18, p["sh"])
        return c.tex()
    return fn


register("gui/sprites/widget/slider_handle", _slider_handle(BTN))
register("gui/sprites/widget/slider_handle_highlighted", _slider_handle(BTN_HL))


def _scroller(ctx):
    c = Canvas(ctx)
    c.rect(0, 0, ctx.w, ctx.h, C("aeb1b9"))
    c.hline(0, ctx.w - 2, 0, C("e3e5ea"))
    c.vline(0, 0, ctx.h - 2, C("e3e5ea"))
    c.hline(1, ctx.w - 1, ctx.h - 1, C("62656e"))
    c.vline(ctx.w - 1, 1, ctx.h - 1, C("62656e"))
    return c.tex()


def _scroller_bg(ctx):
    c = Canvas(ctx)
    c.rect(0, 0, ctx.w, ctx.h, C("101114"), 0.85)
    c.frame(0, 0, ctx.w, ctx.h, C("2e3036"))
    return c.tex()


register("gui/sprites/widget/scroller", _scroller)
register("gui/sprites/widget/scroller_background", _scroller_bg)


def _tab(selected, hl):
    def fn(ctx):
        c = Canvas(ctx)
        w, h = ctx.w, ctx.h
        ink = C("eef2f8") if hl else C("16171a")
        face = C("4a4c53") if selected else C("2a2b30")
        if hl:
            face = mix(face, C("8f9db9"), 0.35)
        c.rect(1, 0, w - 2, h, ink)
        c.rect(0, 1, w, h - 1, ink)
        c.rect(1, 1, w - 2, h - 1, face)
        c.hline(1, w - 2, 1, mix(face, WHITE, 0.25))
        if selected:  # accent stripe inside the fixed top border
            c.hline(2, w - 3, 1, C("e8c24a"))
        return c.tex()
    return fn


for _s in (False, True):
    for _h in (False, True):
        _n = "tab" + ("_selected" if _s else "") + ("_highlighted" if _h else "")
        register(f"gui/sprites/widget/{_n}", _tab(_s, _h))


def checkbox_box(c, hl):
    c.rect(0, 0, 20, 20, C("eef2f8") if hl else C("16171a"))
    inset(c, 1, 1, 18, 18, face=C("1d1e22"), dk=C("0c0c0e"), hi=C("6d7078"))
    c.rect(2, 2, 16, 16, C("26272c") if not hl else C("2e3442"))


CHECK = ["..........#",
         ".........##",
         "........##.",
         "#......##..",
         "##....##...",
         ".##..##....",
         "..####.....",
         "...##......"]


def _checkbox(sel, hl):
    def fn(ctx):
        c = Canvas(ctx)
        checkbox_box(c, hl)
        if sel:
            c.art(CHECK, {"#": C("1d3d1a")}, 5, 7)
            c.art(CHECK, {"#": C("74e06a")}, 4, 6)
        return c.tex()
    return fn


register("gui/sprites/widget/checkbox", _checkbox(False, False))
register("gui/sprites/widget/checkbox_highlighted", _checkbox(False, True))
register("gui/sprites/widget/checkbox_selected", _checkbox(True, False))
register("gui/sprites/widget/checkbox_selected_highlighted", _checkbox(True, True))

LOCK = [".####.",
        "#....#",
        "#....#",
        "######",
        "##..##",
        "###.##",
        "######"]
UNLOCK = [".####.....",
          "#....#....",
          "#....#....",
          "#.........",
          "######....",
          "##..##....",
          "###.##....",
          "######...."]


def _lock(locked, state):
    def fn(ctx):
        c = Canvas(ctx)
        p = {"": BTN, "_highlighted": BTN_HL, "_disabled": BTN_OFF}[state]
        button_face(c, 0, 0, 20, 20, p)
        col = C("f2c33a") if state != "_disabled" else C("8a8d93")
        dark = mix(col, BLACK, 0.55)
        if locked:
            c.art(LOCK, {"#": dark}, 8, 7)
            c.art(LOCK, {"#": col}, 7, 6)
        else:
            c.art(UNLOCK[1:], {"#": dark}, 8, 7)
            c.art(UNLOCK[1:], {"#": col}, 7, 6)
        return c.tex()
    return fn


for _st in ("", "_highlighted", "_disabled"):
    register(f"gui/sprites/widget/locked_button{_st}", _lock(True, _st))
    register(f"gui/sprites/widget/unlocked_button{_st}", _lock(False, _st))


def _cross(hl):
    def fn(ctx):
        c = Canvas(ctx)
        col = C("ffffff") if hl else C("b9bcc4")
        for i in range(8):
            for d in (0, 1):
                c.px(3 + i, 3 + i + d - (d and i == 7), col)
                c.px(10 - i, 3 + i + d - (d and i == 7), col)
        return c.tex()
    return fn


register("gui/sprites/widget/cross_button", _cross(False))
register("gui/sprites/widget/cross_button_highlighted", _cross(True))


def page_arrow(c, x, y, w, h, right, col, dark):
    """Book-style chunky arrow pointing right/left inside w x h."""
    mid = y + h // 2
    head = h // 2 + 1
    shaft_t = max(1, h // 5)
    for dx_dark, colr in ((1, dark), (0, col)):
        for i in range(head):
            xx = (x + w - 1 - i) if right else (x + i)
            c.vline(xx + dx_dark, mid - (head - 1 - i) + dx_dark, mid + (head - 1 - i) + dx_dark, colr)
        if right:
            c.fill(x + dx_dark, mid - shaft_t + dx_dark, x + w - head + 1 + dx_dark, mid + shaft_t + 1 + dx_dark, colr)
        else:
            c.fill(x + head - 1 + dx_dark, mid - shaft_t + dx_dark, x + w + dx_dark, mid + shaft_t + 1 + dx_dark, colr)


def _page(right, hl):
    def fn(ctx):
        c = Canvas(ctx)
        col = C("f0d9a4") if hl else C("c8a46a")
        page_arrow(c, 1, 0, ctx.w - 3, ctx.h - 1, right, col, C("5a4024"))
        return c.tex()
    return fn


register("gui/sprites/widget/page_forward", _page(True, False))
register("gui/sprites/widget/page_forward_highlighted", _page(True, True))
register("gui/sprites/widget/page_backward", _page(False, False))
register("gui/sprites/widget/page_backward_highlighted", _page(False, True))


def _slot_frame(ctx):
    c = Canvas(ctx)
    w, h = ctx.w, ctx.h
    inset(c, 0, 0, w, h, face=C("8a8d95"))
    c.frame(1, 1, w - 2, h - 2, C("7c7f87"))
    return c.tex()


register("gui/sprites/widget/slot_frame", _slot_frame)


def _warning(state):
    def fn(ctx):
        c = Canvas(ctx)
        p = {"": BTN, "_highlighted": BTN_HL, "_disabled": BTN_OFF}[state]
        button_face(c, 0, 0, 20, 20, p)
        y = C("f2c33a") if state != "_disabled" else C("8a8d93")
        c.poly([(10, 3), (17, 16), (3, 16)], mix(y, BLACK, 0.5))
        c.poly([(10, 4.2), (16, 15.2), (4, 15.2)], y)
        c.rect(9, 7, 2, 5, C("2b2210"))
        c.rect(9, 13, 2, 1, C("2b2210"))
        return c.tex()
    return fn


register("gui/sprites/dialog/warning_button", _warning(""))
register("gui/sprites/dialog/warning_button_highlighted", _warning("_highlighted"))
register("gui/sprites/dialog/warning_button_disabled", _warning("_disabled"))


# ----------------------------------------------------------------- list rows / popups
def _rounded_panel(fill, edge, border, inner=None, a=1.0):
    def fn(ctx):
        c = Canvas(ctx)
        w, h = ctx.w, ctx.h
        c.rect(1, 0, w - 2, h, edge)
        c.rect(0, 1, w, h - 2, edge)
        c.rect(1, 1, w - 2, h - 2, fill, a)
        if inner is not None:
            c.frame(2, 2, w - 4, h - 4, inner)
        return c.tex()
    return fn


register("gui/sprites/friends/background", _rounded_panel(C("2b2d34"), C("0f1013"), 8, C("3c3f48")))
register("gui/sprites/friends/background_dark", _rounded_panel(C("1b1c21"), C("0a0a0c"), 6, C("26282e")))
register("gui/sprites/social_interactions/background", _rounded_panel(C("2b2d34"), C("0f1013"), 8, C("3c3f48")))
register("gui/sprites/popup/background", _rounded_panel(C("23252b"), C("c9ccd3"), 6, C("3a3d45")))


def _sep(ctx, top, bottom):
    c = Canvas(ctx)
    c.hline(0, ctx.w - 1, 0, top)
    c.hline(0, ctx.w - 1, 1, bottom)
    return c.tex()


register("gui/header_separator", lambda ctx: _sep(ctx, C("6d7079"), C("101114")))
register("gui/footer_separator", lambda ctx: _sep(ctx, C("101114"), C("6d7079")))
register("gui/inworld_header_separator", lambda ctx: _sep(ctx, C("c8ccd4"), C("000000")))
register("gui/inworld_footer_separator", lambda ctx: _sep(ctx, C("000000"), C("c8ccd4")))
register("gui/sprites/friends/list_separator_top", lambda ctx: _sep(ctx, C("6d7079"), C("101114")))


def _menu_tile(base, var, alpha=1.0, salt="m"):
    """Seamless 16x16 dark tile: soft tiled bricks of slate with texel grain."""
    def fn(ctx):
        n = ctx.noise(4, 2, 0.5, salt=salt)
        g = ctx.texel_noise(salt + "g")
        rows = (ctx.ty // 4) % 4
        offs = np.where(rows % 2 == 0, 0, 4)
        seam = ((ctx.ty % 4) == 3) | (((ctx.tx + offs) % 8) == 7)
        v = 0.5 + (n - 0.5) * 0.35 + (g - 0.5) * 0.25 - seam * 0.45
        col = C(base)[None, None, :] * (1 + (v[..., None] - 0.5) * var)
        return Tex(ctx, np.clip(col, 0, 1), alpha=alpha, wrap=True, grain=0)
    return fn


register("gui/menu_background", _menu_tile("3a3b41", 0.5, salt="menu"))
register("gui/menu_list_background", _menu_tile("26272b", 0.5, salt="list"))
register("gui/inworld_menu_background", _menu_tile("1a1b1f", 0.5, 0.55, salt="iw"))
register("gui/inworld_menu_list_background", _menu_tile("0d0d10", 0.5, 0.6, salt="iwl"))
register("gui/tab_header_background", _menu_tile("2d2e33", 0.45, salt="tab"))


# ----------------------------------------------------------------- tooltip
def _tooltip_bg(ctx):
    c = Canvas(ctx)
    col = C("12131c")
    c.rect(9, 8, 82, 84, col, 0.94)
    c.rect(8, 9, 1, 82, col, 0.94)
    c.rect(91, 9, 1, 82, col, 0.94)
    c.a[c.a > 0] = 0.94
    return c.tex()


def _tooltip_frame(ctx):
    c = Canvas(ctx)
    top, bot = C("6a7fc0"), C("3a4677")
    c.hline(10, 89, 9, top)
    c.hline(10, 89, 90, bot)
    c.vline(9, 10, 89, mix(top, bot, 0.5))
    c.vline(90, 10, 89, mix(top, bot, 0.5))
    c.px(10, 10, top)
    c.px(89, 10, top)
    c.px(10, 89, bot)
    c.px(89, 89, bot)
    return c.tex()


register("gui/sprites/tooltip/background", _tooltip_bg)
register("gui/sprites/tooltip/frame", _tooltip_frame)


# ----------------------------------------------------------------- toasts
def toast_base(c, w, h, accent=None, fill=C("24262d"), edge=C("0d0e11"), rim=C("4a4e5a")):
    c.rect(1, 0, w - 2, h, edge)
    c.rect(0, 1, w, h - 2, edge)
    c.rect(1, 1, w - 2, h - 2, rim)
    c.rect(2, 2, w - 4, h - 4, fill)
    c.hline(2, w - 3, 2, mix(fill, WHITE, 0.08))
    if accent is not None:
        c.rect(2, 2, 2, h - 4, accent)
    return c


def _toast(accent=None, fill=C("24262d"), rim=C("4a4e5a")):
    def fn(ctx):
        c = Canvas(ctx)
        toast_base(c, ctx.w, ctx.h, accent, fill=fill, rim=rim)
        return c.tex()
    return fn


register("gui/sprites/toast/advancement", _toast(C("e8c24a")))
register("gui/sprites/toast/recipe", _toast(C("5fb3e0")))
register("gui/sprites/toast/now_playing", _toast(None))
register("gui/sprites/toast/tutorial", _toast(None, fill=C("e8e9ec"), rim=C("9a9da6")))
register("gui/sprites/friends/toast_background", _toast(C("7bd36f")))


def _system_toast(ctx):
    c = Canvas(ctx)
    toast_base(c, ctx.w, ctx.h, None)
    c.rect(2, 2, 13, 26, C("3a3e4a"))
    c.vline(15, 2, 27, C("4a4e5a"))
    c.hline(2, 15, 28, C("4a4e5a"))
    c.circle(8.5, 15, 4, C("e8c24a"))
    c.rect(8, 12, 1, 4, C("24262d"))
    c.rect(8, 17, 1, 1, C("24262d"))
    return c.tex()


register("gui/sprites/toast/system", _system_toast)


# ----------------------------------------------------------------- advancements boxes
def _adv_box(fill, edge, hi):
    def fn(ctx):
        c = Canvas(ctx)
        w, h = ctx.w, ctx.h
        c.rect(2, 0, w - 4, h, edge)
        c.rect(1, 1, w - 2, h - 2, edge)
        c.rect(0, 2, w, h - 4, edge)
        c.rect(2, 2, w - 4, h - 4, fill)
        c.hline(2, w - 3, 2, hi)
        c.vline(2, 2, h - 4, hi)
        c.hline(3, w - 3, h - 3, mix(fill, BLACK, 0.3))
        c.vline(w - 3, 3, h - 3, mix(fill, BLACK, 0.3))
        return c.tex()
    return fn


register("gui/sprites/advancements/box_obtained", _adv_box(C("c99a2e"), C("2a1f08"), C("efcd6c")))
register("gui/sprites/advancements/box_unobtained", _adv_box(C("38598a"), C("0e1a2c"), C("6f93c8")))
register("gui/sprites/advancements/title_box", _adv_box(C("b9bcc4"), C("1c1d21"), C("e6e8ec")))
