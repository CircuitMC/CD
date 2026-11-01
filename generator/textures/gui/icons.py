"""Small UI icons: menus, server/world lists, statistics, spectator, toasts, social screens."""
import math

import numpy as np

from ...registry import register
from .common import BLACK, C, Canvas, WHITE, inset, mix
from .widgets import BTN, BTN_HL, BTN_OFF, button_face

INK = C("1a1b1f")
LIGHT = C("eef0f4")
GRAYI = C("9a9da6")
GRN, GRN_D = C("62d65a"), C("27621f")
RED_, RED_D = C("e5483d"), C("6b1712")
YEL, YEL_D = C("f2c33a"), C("6b4f0c")
BLU, BLU_D = C("57a3ec"), C("1d4672")


def art(c, rows, pal, x=0, y=0):
    c.art(rows, pal, x, y)


def outlined(c, rows, fill, ink=INK, x=0, y=0, shadow=None):
    """Stamp '#' cells with a 1-texel ink outline around them (drawn first)."""
    if isinstance(rows, str):
        rows = rows.split()
    cells = {(i, j) for j, r in enumerate(rows) for i, ch in enumerate(r) if ch == "#"}
    ring = {(px + dx, py + dy) for (px, py) in cells for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - cells
    for (px, py) in ring:
        c.px(x + px, y + py, ink)
    for (px, py) in cells:
        c.px(x + px, y + py, fill)
    return cells


def icon(fn, *paths, **kw):
    for p in paths:
        register(p, fn, **kw)


# ----------------------------------------------------------------- generic arrows
def tri(c, cx, cy, size, direction, col):
    """Solid texel triangle; direction in 'udlr'; size = half height."""
    for i in range(size):
        if direction in "lr":
            x = cx + (i if direction == "l" else -i)
            c.vline(x, cy - i, cy + i, col)
        else:
            y = cy + (i if direction == "u" else -i)
            c.hline(cx - i, cx + i, y, col)


def _hover_arrow(kind, hl):
    """32x32 overlays drawn on list icons (join / move / select)."""
    def fn(ctx):
        c = Canvas(ctx)
        col = LIGHT if hl else C("c4c7ce")
        sh = C("202227")
        if kind in ("join", "select", "marked_join"):
            c.rect(0, 0, 32, 32, C("000000"), 0.35 if hl else 0.2)
            for i in range(9):
                c.vline(10 + i + 1, 16 - (8 - i) + 1, 16 + (8 - i) + 1, sh)
                c.vline(10 + i, 16 - (8 - i), 16 + (8 - i), col)
            if kind == "marked_join":
                c.circle(26, 6, 3.6, sh)
                c.circle(26, 6, 3, YEL)
        elif kind == "unselect":
            c.rect(0, 0, 16, 32, C("000000"), 0.3 if hl else 0.15)
            for i in range(7):
                c.vline(3 + i + 1, 16 - i + 1, 16 + i + 1, sh)
                c.vline(3 + i, 16 - i, 16 + i, col)
        elif kind == "move_up":
            c.rect(16, 0, 16, 16, C("000000"), 0.3 if hl else 0.15)
            for i in range(6):
                c.hline(24 - i + 1, 24 + i + 1, 4 + i + 1, sh)
                c.hline(24 - i, 24 + i, 4 + i, col)
        elif kind == "move_down":
            c.rect(16, 16, 16, 16, C("000000"), 0.3 if hl else 0.15)
            for i in range(6):
                c.hline(24 - i + 1, 24 + i + 1, 27 - i + 1, sh)
                c.hline(24 - i, 24 + i, 27 - i, col)
        return c.tex()
    return fn


for _hl in (False, True):
    _s = "_highlighted" if _hl else ""
    for _k in ("join", "move_up", "move_down"):
        register(f"gui/sprites/server_list/{_k}{_s}", _hover_arrow(_k, _hl))
    for _k in ("move_up", "move_down", "select", "unselect"):
        register(f"gui/sprites/transferable_list/{_k}{_s}", _hover_arrow(_k, _hl))
    for _k in ("join", "marked_join"):
        register(f"gui/sprites/world_list/{_k}{_s}", _hover_arrow(_k, _hl))


def _world_alert(kind, hl):
    def fn(ctx):
        c = Canvas(ctx)
        c.rect(0, 0, 32, 32, C("000000"), 0.35 if hl else 0.2)
        if kind == "warning":
            col, dk = (YEL, YEL_D)
            c.poly([(16, 4), (29, 27), (3, 27)], dk)
            c.poly([(16, 6.3), (27.3, 26), (4.7, 26)], mix(col, WHITE, 0.2) if hl else col)
            c.rect(15, 11, 2, 9, C("2b2210"))
            c.rect(15, 22, 2, 2, C("2b2210"))
        else:
            c.circle(16, 16, 12, RED_D)
            c.circle(16, 16, 10.8, mix(RED_, WHITE, 0.2) if hl else RED_)
            for i in range(11):
                for d in (0, 1):
                    c.px(11 + i - d, 10 + i, LIGHT) if 0 <= i else None
                    c.px(21 - i + d, 10 + i, LIGHT)
        return c.tex()
    return fn


for _hl in (False, True):
    _s = "_highlighted" if _hl else ""
    register(f"gui/sprites/world_list/warning{_s}", _world_alert("warning", _hl))
    register(f"gui/sprites/world_list/error{_s}", _world_alert("error", _hl))


# ----------------------------------------------------------------- ping bars (10x8)
def _ping(level, color=None, frame_anim=None, cross=False):
    def fn(ctx):
        c = Canvas(ctx)
        for i in range(5):
            h = 2 + i * 1.5
            x = i * 2
            on = (i < level) if frame_anim is None else (i == frame_anim or i == 4 - frame_anim and False)
            col = (color if on else C("3a3b40"))
            c.fill(x, 8 - math.ceil(h), x + 1, 8, col)
        if cross:
            for i in range(5):
                c.px(5 + i, 1 + i, RED_) if i < 5 else None
                c.px(9 - i, 1 + i, RED_)
        return c.tex()
    return fn


_PING = {1: C("e5483d"), 2: C("ec8d3a"), 3: C("e8cf3a"), 4: C("9ed64a"), 5: C("5ad65a")}
for _l in range(1, 6):
    register(f"gui/sprites/server_list/ping_{_l}", _ping(_l, _PING[_l]))
    register(f"gui/sprites/icon/ping_{_l}", _ping(_l, _PING[_l]))
    register(f"gui/sprites/server_list/pinging_{_l}", _ping(0, C("6fb4f0"), frame_anim=_l - 1))
register("gui/sprites/icon/ping_unknown", _ping(0, cross=True))
register("gui/sprites/server_list/unreachable", _ping(0, cross=True))


def _incompatible(ctx):
    c = Canvas(ctx)
    for i in range(5):
        c.fill(i * 2, 8 - math.ceil(2 + i * 1.5), i * 2 + 1, 8, C("3a3b40"))
    c.rect(4, 0, 2, 5, YEL)
    c.rect(4, 6, 2, 2, YEL)
    return c.tex()


register("gui/sprites/server_list/incompatible", _incompatible)


# ----------------------------------------------------------------- notification badges 8x8
def _badge(text):
    def fn(ctx):
        c = Canvas(ctx)
        c.rect(1, 0, 6, 8, C("8c1712"))
        c.rect(0, 1, 8, 6, C("8c1712"))
        c.rect(1, 1, 6, 6, C("e23a30"))
        c.hline(1, 6, 1, C("ff7a6a"))
        if text == "more":
            c.vline(4, 2, 6, WHITE)
            c.hline(2, 6, 4, WHITE)
        else:
            from . import glyphs
            c.cells(glyphs.tiny(text), 2, 1, WHITE)
        return c.tex()
    return fn


for _t in ("1", "2", "3", "4", "5", "more"):
    register(f"gui/sprites/notification/{_t}", _badge(_t))


# ----------------------------------------------------------------- generic icon helpers
def accept_reject(accept, hl, size=18):
    def fn(ctx):
        c = Canvas(ctx)
        o = (size - 18) // 2
        col, dk = (GRN, GRN_D) if accept else (RED_, RED_D)
        if hl:
            col = mix(col, WHITE, 0.3)
        c.rect(o + 1, o, 16, 18, dk)
        c.rect(o, o + 1, 18, 16, dk)
        c.rect(o + 1, o + 1, 16, 16, col)
        c.hline(o + 1, o + 16, o + 1, mix(col, WHITE, 0.35))
        c.hline(o + 1, o + 16, o + 16, mix(col, BLACK, 0.25))
        if accept:
            check = ["......#", ".....##", "#...##.", "##.##..", ".###...", "..#...."]
            art(c, check, {"#": WHITE}, o + 6, o + 6)
        else:
            for i in range(8):
                c.px(o + 5 + i, o + 5 + i, WHITE)
                c.px(o + 12 - i, o + 5 + i, WHITE)
                c.px(o + 6 + i, o + 5 + i, WHITE) if i < 7 else None
                c.px(o + 11 - i, o + 5 + i, WHITE) if i < 7 else None
        return c.tex()
    return fn


for _base in ("friends", "pending_invite"):
    register(f"gui/sprites/{_base}/accept", accept_reject(True, False))
    register(f"gui/sprites/{_base}/accept_highlighted", accept_reject(True, True))
    register(f"gui/sprites/{_base}/reject", accept_reject(False, False))
    register(f"gui/sprites/{_base}/reject_highlighted", accept_reject(False, True))


PERSON = [".###.",
          "#####",
          "#####",
          ".###.",
          ".....",
          ".###.",
          "#####",
          "#####"]


def person(c, x, y, col, ink=INK):
    outlined(c, PERSON, col, ink, x, y)


def _friends(ctx):
    c = Canvas(ctx)
    person(c, 9, 4, C("9aa6be"))
    person(c, 3, 5, C("e8eaee"))
    return c.tex()


def _cancel(ctx):
    c = Canvas(ctx)
    c.circle(8, 8, 6.5, RED_D)
    c.circle(8, 8, 5.5, RED_)
    c.rect(4, 7, 8, 2, WHITE)
    return c.tex()


def _remove(ctx):
    c = Canvas(ctx)
    person(c, 1, 2, C("c4c7ce"))
    c.rect(8, 6, 5, 2, RED_)
    return c.tex()


def _send_request(ctx):
    c = Canvas(ctx)
    person(c, 1, 3, C("c4c7ce"))
    c.rect(10, 7, 5, 1, GRN)
    c.rect(12, 5, 1, 5, GRN)
    return c.tex()


register("gui/sprites/friends/friends", _friends)
register("gui/sprites/friends/cancel", _cancel)
register("gui/sprites/friends/remove", _remove)
register("gui/sprites/friends/send_request", _send_request)


def _loading(ctx):
    c = Canvas(ctx)
    for i in range(3):
        on = i == ctx.frame
        c.px(i * 2, 0, LIGHT if on else C("6d7079"))
        c.px(i * 2, 1, LIGHT if on else C("6d7079"))
    return c.tex()


register("gui/sprites/friends/loading", _loading, size=(5, 2), frames=3, frametime=6)


def _illustration(ctx):
    """Friends screen banner: three figures on a hill under a sky."""
    c = Canvas(ctx)
    sky = mix(C("5a8fd8"), C("b9dcff"), np.clip(ctx.y / 48, 0, 1)[..., None])
    c.mask(ctx.full(1), sky)
    hill = ctx.circle(64, 120, 84)
    c.mask(hill, C("5fae3a"))
    c.mask(ctx.circle(64, 120, 84) * (ctx.y < 38.5) * (ctx.y >= 37.5), C("8fd45c"))
    for i, (x, col) in enumerate(((44, C("e8c24a")), (60, C("e56a5a")), (76, C("5aa0e5")))):
        y = 26 - (i == 1) * 2
        c.rect(x, y, 8, 8, C("e8c39c"))
        c.rect(x + 2, y + 3, 1, 1, INK)
        c.rect(x + 5, y + 3, 1, 1, INK)
        c.rect(x, y, 8, 2, C("5a3a1e"))
        c.rect(x, y + 8, 8, 10, col)
    for (x, y) in ((14, 9), (100, 6), (116, 14)):
        c.rect(x, y, 10, 3, WHITE, 0.85)
        c.rect(x + 2, y - 2, 6, 2, WHITE, 0.85)
    return c.tex()


register("gui/sprites/friends/illustrations_00", _illustration)


# ----------------------------------------------------------------- icon/*
def _accessibility(ctx):
    c = Canvas(ctx)
    c.circle(7.5, 7.5, 7.2, C("2b5fa8"))
    c.circle(7.5, 7.5, 6.2, C("3f7fd6"))
    c.rect(7, 2, 2, 2, WHITE)
    c.rect(3, 5, 10, 1, WHITE)
    c.rect(7, 5, 2, 5, WHITE)
    c.rect(6, 10, 1, 3, WHITE)
    c.rect(9, 10, 1, 3, WHITE)
    return c.tex()


def _chat_modified(ctx):
    c = Canvas(ctx)
    c.rect(1, 1, 7, 5, C("e8eaee"))
    c.px(2, 6, C("e8eaee"))
    c.rect(2, 2, 5, 1, C("6d7079"))
    c.rect(2, 4, 3, 1, YEL)
    return c.tex()


def _checkmark(ctx):
    c = Canvas(ctx)
    art(c, ["........#", ".......##", "#.....##.", "##...##..", ".##.##...", "..###....", "...#....."],
        {"#": WHITE}, 0, 0)
    return c.tex()


def _draft(ctx):
    c = Canvas(ctx)
    c.rect(2, 1, 10, 13, INK)
    c.rect(3, 2, 8, 11, C("eef0f4"))
    for y in (4, 6, 8):
        c.hline(4, 9, y, C("8a8d95"))
    for i in range(6):
        c.px(8 + i, 12 - i, YEL)
        c.px(9 + i, 12 - i, YEL_D) if i < 5 else None
    return c.tex()


def _info(ctx):
    c = Canvas(ctx)
    c.circle(10, 10, 9, C("1d4672"))
    c.circle(10, 10, 8, C("3f87d6"))
    c.rect(9, 4, 2, 2, WHITE)
    c.rect(9, 8, 2, 7, WHITE)
    c.rect(8, 8, 1, 1, WHITE)
    c.rect(8, 14, 4, 1, WHITE)
    return c.tex()


def _envelope(c, x, y, w, h, col=C("eef0f4")):
    c.rect(x, y, w, h, INK)
    c.rect(x + 1, y + 1, w - 2, h - 2, col)
    for i in range((w - 2) // 2):
        c.px(x + 1 + i, y + 1 + i * (h - 3) // max(1, (w - 2) // 2), C("8a8d95"))
        c.px(x + w - 2 - i, y + 1 + i * (h - 3) // max(1, (w - 2) // 2), C("8a8d95"))


def _invite(ctx):
    c = Canvas(ctx)
    _envelope(c, 0, 3, 14, 10)
    return c.tex()


def _language(ctx):
    c = Canvas(ctx)
    c.circle(7.5, 7.5, 7, C("1d4672"))
    c.circle(7.5, 7.5, 6, C("57a3ec"))
    c.mask(ctx.circle(6, 6, 3.2), C("5fae3a"))
    c.mask(ctx.circle(10.5, 10, 2.4), C("5fae3a"))
    c.hline(1, 13, 7, C("1d4672"), 0.5)
    c.vline(7, 1, 13, C("1d4672"), 0.5)
    return c.tex()


def _link(hl):
    def fn(ctx):
        c = Canvas(ctx)
        col = C("8fc8ff") if hl else C("57a3ec")
        for (x, y) in ((1, 7), (7, 1)):
            c.rect(x + 1, y, 5, 7, col)
            c.rect(x, y + 1, 7, 5, col)
            c.rect(x + 2, y + 2, 3, 3, C("000000"))
            c.erase(ctx.rect(x + 2, y + 2, x + 5, y + 5))
        c.line(4, 10, 10, 4, col, 1.5)
        return c.tex()
    return fn


def _music_notes(ctx):
    c = Canvas(ctx)
    f = ctx.frame
    hue = [C("e5483d"), C("ec8d3a"), C("e8cf3a"), C("5ad65a"), C("4ad6c8"), C("57a3ec"), C("9a6ae8"), C("e56ab8")][f]
    dy = [0, -1, -1, 0, 1, 1, 0, 0][f]
    c.rect(4, 10 + dy, 3, 3, hue)
    c.rect(10, 8 + dy, 3, 3, hue)
    c.vline(6, 3 + dy, 11 + dy, hue)
    c.vline(12, 1 + dy, 9 + dy, hue)
    c.hline(6, 12, 2 + dy, hue)
    c.hline(6, 12, 3 + dy, hue)
    return c.tex()


def _new_realm(ctx):
    c = Canvas(ctx)
    c.rect(1, 2, 38, 16, C("2b5d2a"))
    c.rect(2, 3, 36, 14, C("4ea84a"))
    c.hline(2, 37, 3, C("8fd884"))
    c.text("NEW", 8, 6, WHITE)
    return c.tex()


def _news(ctx):
    c = Canvas(ctx)
    c.rect(1, 2, 12, 10, INK)
    c.rect(2, 3, 10, 8, C("eef0f4"))
    c.rect(3, 4, 4, 3, C("57a3ec"))
    c.hline(8, 10, 4, C("6d7079"))
    c.hline(8, 10, 6, C("6d7079"))
    c.hline(3, 10, 8, C("6d7079"))
    return c.tex()


def _search(ctx):
    c = Canvas(ctx)
    col = C("d8dbe2")
    c.ring(4.5, 4.5, 4.2, 1.4, col)
    for i in range(4):
        c.rect(7 + i, 7 + i, 2, 2, col)
    return c.tex()


def _trial(ctx):
    c = Canvas(ctx)
    f = ctx.frame
    k = [0, 1, 2, 3, 2, 1][f] / 3
    c.rect(1, 0, 6, 8, mix(C("e8c24a"), WHITE, k * 0.6))
    c.rect(0, 1, 8, 6, mix(C("e8c24a"), WHITE, k * 0.6))
    c.rect(3, 2, 2, 3, C("4a3008"))
    c.rect(3, 6, 2, 1, C("4a3008"))
    return c.tex()


def _unseen(ctx):
    c = Canvas(ctx)
    c.circle(5, 5, 4.6, C("6b1712"))
    c.circle(5, 5, 3.6, C("ef4a3a"))
    c.px(3, 3, C("ffb0a0"))
    return c.tex()


def _video(hl):
    def fn(ctx):
        c = Canvas(ctx)
        col = C("ff6a5a") if hl else C("e5483d")
        c.rect(1, 3, 13, 9, col)
        c.rect(0, 4, 15, 7, col)
        for i in range(4):
            c.vline(6 + i, 5 + i // 1 - 0 + 0 if False else 7 - (3 - i), 7 + (3 - i), WHITE)
        return c.tex()
    return fn


register("gui/sprites/icon/accessibility", _accessibility)
register("gui/sprites/icon/chat_modified", _chat_modified)
register("gui/sprites/icon/checkmark", _checkmark)
register("gui/sprites/icon/draft_report", _draft)
register("gui/sprites/icon/info", _info)
register("gui/sprites/icon/invite", _invite)
register("gui/sprites/icon/language", _language)
register("gui/sprites/icon/link", _link(False))
register("gui/sprites/icon/link_highlighted", _link(True))
register("gui/sprites/icon/music_notes", _music_notes, size=(16, 16), frames=8, frametime=2)
register("gui/sprites/icon/new_realm", _new_realm)
register("gui/sprites/icon/news", _news)
register("gui/sprites/icon/search", _search)
register("gui/sprites/icon/trial_available", _trial, size=(8, 8), frames=6, frametime=2)
register("gui/sprites/icon/unseen_notification", _unseen)
register("gui/sprites/icon/video_link", _video(False))
register("gui/sprites/icon/video_link_highlighted", _video(True))


# ----------------------------------------------------------------- pause menu / player list
def _bug(ctx):
    c = Canvas(ctx)
    c.mask(ctx.circle(6.5, 7.5, 4.6), C("2b2d33"))
    c.mask(ctx.circle(6.5, 7.5, 3.6), C("5aa04a"))
    c.vline(6, 4, 11, C("2b2d33"))
    c.mask(ctx.circle(6.5, 2.8, 2.2), C("2b2d33"))
    for y in (5, 8, 11):
        c.px(0 + 1, y, C("2b2d33"))
        c.px(11, y, C("2b2d33"))
    return c.tex()


def _report(ctx):
    c = Canvas(ctx)
    c.vline(2, 1, 13, C("8a8d95"))
    c.rect(3, 1, 10, 7, RED_D)
    c.rect(3, 2, 9, 5, RED_)
    c.rect(7, 2, 1, 3, WHITE)
    c.px(7, 6, WHITE)
    return c.tex()


def _social(ctx):
    c = Canvas(ctx)
    person(c, 11, 5, C("9aa6be"))
    person(c, 4, 6, C("e8eaee"))
    return c.tex()


register("gui/sprites/pause_menu/bug", _bug)
register("gui/sprites/pause_menu/player_reporting", _report)
register("gui/sprites/pause_menu/social_interactions", _social)


def _op(kind):
    def fn(ctx):
        c = Canvas(ctx)
        if kind == "make":
            tri(c, 3, 1, 4, "u", GRN)
            c.rect(2, 4, 3, 3, GRN)
        elif kind == "remove_op":
            tri(c, 3, 5, 4, "d", RED_)
            c.rect(2, 0, 3, 3, RED_)
        else:
            for i in range(7):
                c.px(i, i, RED_)
                c.px(6 - i, i, RED_)
                c.px(i + 1, i, RED_) if i < 6 else None
                c.px(7 - i, i, RED_) if i > 0 else None
        return c.tex()
    return fn


register("gui/sprites/player_list/make_operator", _op("make"))
register("gui/sprites/player_list/remove_operator", _op("remove_op"))
register("gui/sprites/player_list/remove_player", _op("remove"))


# ----------------------------------------------------------------- realm status (10x28)
def _realm_status(col, blink=False):
    def fn(ctx):
        c = Canvas(ctx)
        k = col if not blink or ctx.frame == 0 else mix(col, BLACK, 0.5)
        c.rect(1, 0, 8, 28, INK)
        c.rect(0, 1, 10, 26, INK)
        c.rect(1, 1, 8, 26, mix(k, BLACK, 0.3))
        c.rect(2, 2, 6, 24, k)
        c.vline(2, 2, 25, mix(k, WHITE, 0.4))
        return c.tex()
    return fn


register("gui/sprites/realm_status/open", _realm_status(C("5ad65a")))
register("gui/sprites/realm_status/closed", _realm_status(C("e5483d")))
register("gui/sprites/realm_status/expired", _realm_status(C("7a7d86")))
register("gui/sprites/realm_status/expires_soon", _realm_status(C("ec9d3a"), True), size=(10, 28), frames=2, frametime=10)


# ----------------------------------------------------------------- social interaction buttons (20x20)
def _speaker(c, col, muted):
    c.rect(4, 8, 3, 4, col)
    for i in range(4):
        c.vline(7 + i, 8 - i, 11 + i, col)
    if muted:
        for i in range(5):
            c.px(12 + i, 8 + i, RED_)
            c.px(16 - i, 8 + i, RED_)
    else:
        c.vline(13, 8, 11, col)
        c.vline(15, 7, 12, col)


def _social_btn(kind, state):
    def fn(ctx):
        c = Canvas(ctx)
        p = {"": BTN, "_highlighted": BTN_HL, "_disabled": BTN_OFF}[state]
        button_face(c, 0, 0, 20, 20, p)
        col = WHITE if state != "_disabled" else C("8a8d93")
        if kind == "mute":
            _speaker(c, col, True)
        elif kind == "unmute":
            _speaker(c, col, False)
        else:
            c.vline(6, 4, 15, col)
            c.rect(7, 4, 8, 6, RED_ if state != "_disabled" else C("6d7079"))
            c.rect(10, 5, 1, 2, col)
            c.px(10, 8, col)
        return c.tex()
    return fn


for _k, _states in (("mute", ("", "_highlighted")), ("unmute", ("", "_highlighted")),
                    ("report", ("", "_highlighted", "_disabled"))):
    for _st in _states:
        register(f"gui/sprites/social_interactions/{_k}_button{_st}", _social_btn(_k, _st))


# ----------------------------------------------------------------- spectator (16x16)
def _spec(kind):
    def fn(ctx):
        c = Canvas(ctx)
        if kind == "close":
            for i in range(10):
                for d in (0, 1):
                    c.px(3 + i + d, 3 + i, LIGHT) if 3 + i + d <= 12 else None
                    c.px(12 - i - d, 3 + i, LIGHT) if 12 - i - d >= 3 else None
        elif kind in ("scroll_left", "scroll_right"):
            r = kind == "scroll_right"
            for i in range(6):
                x = (5 + i) if r else (10 - i)
                c.vline(x, 2 + i, 13 - i, LIGHT)
        elif kind == "teleport_to_player":
            c.rect(4, 2, 8, 8, C("c49a72"))
            c.rect(4, 2, 8, 3, C("5a3a1e"))
            c.rect(5, 6, 2, 1, INK)
            c.rect(9, 6, 2, 1, INK)
            c.rect(3, 10, 10, 5, C("4a8fe0"))
        else:
            for k, col in enumerate((C("e5483d"), C("57a3ec"), C("5ad65a"))):
                c.rect(1 + k * 5, 4 + (k == 1) * -2, 4, 4, mix(col, WHITE, 0.3))
                c.rect(1 + k * 5, 9 + (k == 1) * -2, 4, 5, col)
        return c.tex()
    return fn


for _k in ("close", "scroll_left", "scroll_right", "teleport_to_player", "teleport_to_team"):
    register(f"gui/sprites/spectator/{_k}", _spec(_k))


# ----------------------------------------------------------------- statistics (18x18)
def _stat_frame(c):
    inset(c, 0, 0, 18, 18, face=C("8a8d95"))


def _stat(kind):
    def fn(ctx):
        c = Canvas(ctx)
        if kind in ("header", "sort_up", "sort_down"):
            _stat_frame(c) if kind == "header" else None
            if kind == "sort_up":
                tri(c, 9, 5, 6, "u", C("2b2d33"))
                tri(c, 9, 6, 5, "u", LIGHT)
            elif kind == "sort_down":
                tri(c, 9, 12, 6, "d", C("2b2d33"))
                tri(c, 9, 11, 5, "d", LIGHT)
            return c.tex()
        _stat_frame(c)
        if kind == "block_mined":
            c.rect(3, 6, 9, 9, C("6b6e76"))
            c.rect(3, 6, 9, 1, C("a3a6ae"))
            c.line(9, 3, 15, 9, C("8a5a2e"), 1)
            c.line(10, 2, 14, 2, C("c9ccd3"))
            c.line(14, 2, 15, 3, C("c9ccd3"))
            c.line(11, 2, 8, 5, C("c9ccd3"))
        elif kind == "item_broken":
            c.line(3, 14, 7, 10, C("8a5a2e"))
            c.line(9, 8, 13, 4, C("c9ccd3"))
            c.px(8, 9, RED_)
            c.px(10, 10, RED_)
            c.px(7, 7, RED_)
        elif kind == "item_crafted":
            for (x, y) in ((3, 3), (7, 3), (11, 3), (3, 7), (7, 7), (11, 7), (3, 11), (7, 11), (11, 11)):
                c.rect(x, y, 3, 3, C("a3743e"))
            c.rect(7, 7, 3, 3, C("e8c24a"))
        elif kind == "item_dropped":
            c.rect(6, 3, 6, 6, C("57a3ec"))
            tri(c, 9, 14, 4, "d", LIGHT)
            c.rect(8, 9, 2, 3, LIGHT)
        elif kind == "item_picked_up":
            c.rect(6, 10, 6, 5, C("57a3ec"))
            tri(c, 9, 3, 4, "u", LIGHT)
            c.rect(8, 6, 2, 3, LIGHT)
        elif kind == "item_used":
            c.circle(9, 9, 5, C("e8c24a"))
            c.circle(9, 9, 3, C("8a8d95"))
            for (x, y) in ((8, 2), (8, 14), (2, 8), (14, 8)):
                c.rect(x, y, 2, 2, C("e8c24a"))
        return c.tex()
    return fn


for _k in ("block_mined", "header", "item_broken", "item_crafted", "item_dropped", "item_picked_up",
           "item_used", "sort_down", "sort_up"):
    register(f"gui/sprites/statistics/{_k}", _stat(_k))


# ----------------------------------------------------------------- tutorial toast icons (20x20)
def _toast_icon(kind):
    def fn(ctx):
        c = Canvas(ctx)
        if kind in ("mouse", "right_click"):
            c.rect(5, 2, 10, 16, INK)
            c.rect(6, 3, 8, 14, C("d8dbe2"))
            c.hline(6, 13, 9, INK)
            c.vline(9, 3, 9, INK)
            c.vline(10, 3, 9, INK)
            if kind == "right_click":
                c.rect(11, 3, 3, 6, RED_)
        elif kind == "movement_keys":
            for (x, y) in ((7, 1), (1, 7), (7, 7), (13, 7)):
                c.rect(x, y, 6, 6, INK)
                c.rect(x + 1, y + 1, 4, 4, C("d8dbe2"))
                c.hline(x + 1, x + 4, y + 4, C("8a8d95"))
            c.rect(1, 14, 18, 5, INK)
            c.rect(2, 15, 16, 3, C("d8dbe2"))
        elif kind == "recipe_book":
            c.rect(3, 2, 14, 16, C("4a2a12"))
            c.rect(4, 3, 12, 14, C("8a4f22"))
            c.rect(15, 3, 1, 14, C("e8e2d0"))
            c.rect(6, 6, 7, 5, C("c49a3a"))
            c.rect(7, 7, 5, 3, C("e8c24a"))
        elif kind == "social_interactions":
            person(c, 11, 4, C("9aa6be"))
            person(c, 4, 6, C("e8eaee"))
        elif kind == "tree":
            c.rect(8, 11, 4, 8, C("6b4423"))
            c.vline(9, 11, 18, C("8a5a2e"))
            c.circle(10, 7, 6, C("2f6b26"))
            c.circle(9, 6, 4.5, C("4a9a3a"))
            c.px(7, 4, C("7ac85c"))
        elif kind == "wooden_planks":
            c.rect(2, 2, 16, 16, C("5a3a1e"))
            for k in range(4):
                c.rect(3, 3 + k * 4, 14, 3, C("a8784a") if k % 2 == 0 else C("9a6b40"))
                c.px(3 + (k * 7) % 12, 4 + k * 4, C("7a522c"))
        return c.tex()
    return fn


for _k in ("mouse", "movement_keys", "recipe_book", "right_click", "social_interactions", "tree", "wooden_planks"):
    register(f"gui/sprites/toast/{_k}", _toast_icon(_k))


# ----------------------------------------------------------------- gamemode switcher
def _gm(kind):
    def fn(ctx):
        c = Canvas(ctx)
        if kind == "slot":
            c.rect(0, 0, 26, 26, C("16171a"), 0.9)
            c.rect(1, 1, 24, 24, C("3a3c43"), 0.9)
            c.rect(2, 2, 22, 22, C("26272c"), 0.9)
        else:
            c.frame(0, 0, 26, 26, C("f6f7fa"))
            c.frame(1, 1, 24, 24, C("9aa6be"))
        return c.tex()
    return fn


register("gui/sprites/gamemode_switcher/slot", _gm("slot"))
register("gui/sprites/gamemode_switcher/selection", _gm("selection"))
