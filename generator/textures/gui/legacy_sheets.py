"""Pre-1.20.2 GUI sheets (widgets, icons, bars, toasts, tabs, list buttons ...) composed from the
modern sprite generators at the old sheet coordinates, plus small old-only sprites."""
import numpy as np

from ...engine import Ctx, Tex
from ...registry import TEXTURES, register
from .common import BLACK, C, Canvas, WHITE, inset, mix, panel
from .legacy_common import icon_button, put, render, sprite
from .legacy_embed import EMBED

SP = "gui/sprites/"
HUD = SP + "hud/"
H = HUD + "heart/"


def sheet(items_fn):
    """Register helper: items_fn(c, ctx) draws onto an empty canvas."""
    def fn(ctx):
        c = Canvas(ctx)
        items_fn(c, ctx)
        return c.tex()
    return fn


def place_all(c, ctx, items):
    for it in items:
        put(c, ctx, *it)


# ----------------------------------------------------------------- small old-only sprites
def _slot_with(hint):
    def fn(ctx):
        c = render(ctx, SP + "container/slot")
        if hint:
            put(c, ctx, SP + f"container/slot/{hint}", 1, 1)
        return c.tex()
    return fn


register(SP + "container/horse/armor_slot", _slot_with("horse_armor"))
register(SP + "container/horse/llama_armor_slot", _slot_with("llama_armor"))
register(SP + "container/horse/saddle_slot", _slot_with("saddle"))


def _bundle_slot(blocked):
    def fn(ctx):
        c = Canvas(ctx)
        inset(c, 0, 0, 18, 20)
        if blocked:
            put(c, ctx, SP + "container/crafter/disabled_slot", 0, 0)
            c.hline(1, 16, 18, C("5d6068"))
        return c.tex()
    return fn


register(SP + "container/bundle/slot", _bundle_slot(False))
register(SP + "container/bundle/blocked_slot", _bundle_slot(True))
register(SP + "container/inventory/effect_background_large",
         lambda ctx: sprite(ctx, SP + "container/inventory/effect_background", 120, 32).tex())


def _brighter(path):
    def fn(ctx):
        c = render(ctx, path)
        c.rgb = np.clip(c.rgb * 1.25 + 0.12, 0, 1)
        return c.tex()
    return fn


for _n in ("make_operator", "remove_operator", "remove_player"):
    register(SP + f"player_list/{_n}_highlighted", _brighter(SP + f"player_list/{_n}"))


def _toast_system_short(ctx):
    """1.20.4-1.21.1 system toast (160x32): same look as the 160x64 version, shorter."""
    c = Canvas(ctx)
    from .widgets import toast_base
    toast_base(c, ctx.w, ctx.h, C("e8c24a"))
    return c.tex()


register(SP + "toast/system@160x32", _toast_system_short, size=(160, 32))


# ----------------------------------------------------------------- big sheets
def _widgets(c, ctx):
    put(c, ctx, HUD + "hotbar", 0, 0)
    put(c, ctx, HUD + "hotbar_selection", 0, 22)
    put(c, ctx, HUD + "hotbar_offhand_left", 24, 22)
    put(c, ctx, HUD + "hotbar_offhand_right", 53, 22)
    put(c, ctx, SP + "widget/button_disabled", 0, 46)
    put(c, ctx, SP + "widget/button", 0, 66)
    put(c, ctx, SP + "widget/button_highlighted", 0, 86)
    icon_button(c, ctx, 0, 106, SP + "icon/language", "")
    icon_button(c, ctx, 0, 126, SP + "icon/language", "_highlighted")
    for col, kind in ((0, "locked_button"), (20, "unlocked_button")):
        for row, st in ((146, ""), (166, "_highlighted"), (186, "_disabled")):
            put(c, ctx, SP + f"widget/{kind}{st}", col, row)


register("gui/widgets", sheet(_widgets))

KINDS = ["", "poisoned", "withered", "absorbing", "frozen"]


def _heart_name(kind, hardcore, half, blink):
    return "_".join(p for p in (kind, "hardcore" if hardcore else "", "half" if half else "full",
                                "blinking" if blink else "") if p)


def _icons(c, ctx):
    put(c, ctx, HUD + "crosshair", 0, 0)
    for hc, y in ((False, 0), (True, 45)):
        sfx = "_hardcore" if hc else ""
        put(c, ctx, H + f"container{sfx}", 16, y)
        put(c, ctx, H + f"container{sfx}_blinking", 25, y)
        cols = {("", False, False): 52, ("", True, False): 61, ("", False, True): 70, ("", True, True): 79,
                ("poisoned", False, False): 88, ("poisoned", True, False): 97,
                ("poisoned", False, True): 106, ("poisoned", True, True): 115,
                ("withered", False, False): 124, ("withered", True, False): 133,
                ("withered", False, True): 142, ("withered", True, True): 151,
                ("absorbing", False, False): 160, ("absorbing", True, False): 169,
                ("frozen", False, False): 178, ("frozen", True, False): 187}
        for (kind, half, blink), x in cols.items():
            put(c, ctx, H + _heart_name(kind, hc, half, blink), x, y)
    put(c, ctx, H + "vehicle_container", 52, 9)
    put(c, ctx, H + "vehicle_full", 88, 9)
    put(c, ctx, H + "vehicle_half", 97, 9)
    put(c, ctx, HUD + "armor_empty", 16, 9)
    put(c, ctx, HUD + "armor_half", 25, 9)
    put(c, ctx, HUD + "armor_full", 34, 9)
    put(c, ctx, HUD + "air", 16, 18)
    put(c, ctx, HUD + "air_bursting", 25, 18)
    for name, x in (("food_empty", 16), ("food_empty_hunger", 133), ("food_full", 52), ("food_half", 61),
                    ("food_full_hunger", 88), ("food_half_hunger", 97)):
        put(c, ctx, HUD + name, x, 27)
    put(c, ctx, HUD + "experience_bar_background", 0, 64)
    put(c, ctx, HUD + "experience_bar_progress", 0, 69)
    put(c, ctx, HUD + "jump_bar_background", 0, 84)
    put(c, ctx, HUD + "jump_bar_progress", 0, 89)
    put(c, ctx, HUD + "hotbar_attack_indicator_background", 0, 94)
    put(c, ctx, HUD + "hotbar_attack_indicator_progress", 18, 94)
    put(c, ctx, HUD + "crosshair_attack_indicator_background", 36, 94)
    put(c, ctx, HUD + "crosshair_attack_indicator_progress", 52, 94)
    put(c, ctx, HUD + "crosshair_attack_indicator_full", 68, 94)
    for k in range(5):
        put(c, ctx, SP + f"server_list/ping_{5 - k}", 0, 176 + 8 * k)
        put(c, ctx, SP + f"server_list/pinging_{k + 1}", 10, 176 + 8 * k)
    put(c, ctx, SP + "server_list/unreachable", 0, 216)


register("gui/icons", sheet(_icons))

BOSS = ["pink", "blue", "red", "green", "yellow", "purple", "white"]


def _bars(c, ctx):
    for i, col in enumerate(BOSS):
        put(c, ctx, SP + f"boss_bar/{col}_background", 0, 10 * i)
        put(c, ctx, SP + f"boss_bar/{col}_progress", 0, 10 * i + 5)
    for k, n in enumerate((6, 10, 12, 20)):
        put(c, ctx, SP + f"boss_bar/notched_{n}_background", 0, 80 + 10 * k)
        put(c, ctx, SP + f"boss_bar/notched_{n}_progress", 0, 85 + 10 * k)


register("gui/bars", sheet(_bars))

AD = SP + "advancements/"


def _adv_tabs(c, ctx):
    for side, parts, x0, y0, step in (("above", ("left", "middle", "right"), 0, 0, 28),
                                      ("below", ("left", "middle", "right"), 84, 0, 28),
                                      ("left", ("top", "middle", "bottom"), 0, 64, 32),
                                      ("right", ("top", "middle", "bottom"), 96, 64, 32)):
        dy = 32 if side in ("above", "below") else 28
        for i, p in enumerate(parts):
            put(c, ctx, AD + f"tab_{side}_{p}", x0 + i * step, y0)
            put(c, ctx, AD + f"tab_{side}_{p}_selected", x0 + i * step, y0 + dy)


def _adv_widgets(c, ctx):
    put(c, ctx, AD + "box_obtained", 0, 0)
    put(c, ctx, AD + "box_unobtained", 0, 26)
    put(c, ctx, AD + "title_box", 0, 52)
    for x, kind in ((0, "task"), (26, "challenge"), (52, "goal")):
        put(c, ctx, AD + f"{kind}_frame_obtained", x, 128)
        put(c, ctx, AD + f"{kind}_frame_unobtained", x, 154)


register("gui/advancements/tabs", sheet(_adv_tabs))
register("gui/advancements/widgets", sheet(_adv_widgets))


def _achievements(c, ctx):
    panel(c, 0, 0, 256, 202)
    c.rect(15, 16, 226, 170, C("16171a"))
    c.clear(16, 17, 224, 168)
    put(c, ctx, AD + "task_frame_obtained", 0, 202)
    put(c, ctx, AD + "challenge_frame_obtained", 26, 202)
    put(c, ctx, SP + "toast/advancement", 96, 202)


register("gui/achievement/achievement_background", sheet(_achievements))


def _creative_tabs(c, ctx):
    """1.19.3-1.20.1 layout (served by the base folder): 26x32 cells at u = column * 26."""
    for col in range(7):
        n = col + 1
        for y, st in ((0, "top_unselected"), (32, "top_selected"), (64, "bottom_unselected"), (96, "bottom_selected")):
            put(c, ctx, SP + f"container/creative_inventory/tab_{st}_{n}", 26 * col, y)


register("gui/container/creative_inventory/tabs", sheet(_creative_tabs))


def _stats_icons(c, ctx):
    put(c, ctx, SP + "container/slot", 0, 0)
    put(c, ctx, SP + "statistics/sort_down", 18, 0)
    put(c, ctx, SP + "statistics/sort_up", 36, 0)
    put(c, ctx, SP + "statistics/header", 0, 18)
    for x, n in ((18, "item_crafted"), (36, "item_used"), (54, "block_mined"), (72, "item_broken"),
                 (90, "item_picked_up"), (108, "item_dropped")):
        put(c, ctx, SP + f"statistics/{n}", x, 18)


register("gui/container/stats_icons", sheet(_stats_icons))

V = SP + "container/villager/"


def _villager2(c, ctx):
    put(c, ctx, "gui/container/villager", 0, 0, 512, 256)
    c.clear(0, 166, 512, 90)
    c.clear(276, 0, 236, 166)
    put(c, ctx, V + "out_of_stock", 311, 0)
    put(c, ctx, V + "discount_strikethrough", 0, 176)
    put(c, ctx, V + "trade_arrow", 15, 171)
    put(c, ctx, V + "trade_arrow_out_of_stock", 25, 171)
    put(c, ctx, V + "experience_bar_result", 0, 181)
    put(c, ctx, V + "experience_bar_background", 0, 186)
    put(c, ctx, V + "experience_bar_current", 0, 191)
    put(c, ctx, V + "scroller", 0, 199)
    put(c, ctx, V + "scroller_disabled", 6, 199)


register("gui/container/villager2", sheet(_villager2))


def _toasts(c, ctx):
    put(c, ctx, SP + "toast/advancement", 0, 0)
    put(c, ctx, SP + "toast/recipe", 0, 32)
    put(c, ctx, SP + "toast/system@160x32", 0, 64)
    put(c, ctx, SP + "toast/tutorial", 0, 96)
    for (x, y), n in (((0, 0), "movement_keys"), ((1, 0), "mouse"), ((2, 0), "tree"), ((0, 1), "recipe_book"),
                      ((1, 1), "wooden_planks"), ((2, 1), "social_interactions"), ((3, 1), "right_click")):
        put(c, ctx, SP + f"toast/{n}", 176 + 20 * x, 20 * y)


register("gui/toasts", sheet(_toasts))


def _list_sheet(base, names):
    def draw(c, ctx):
        for x, n in names:
            put(c, ctx, SP + f"{base}/{n}", x, 0)
            put(c, ctx, SP + f"{base}/{n}_highlighted", x, 32)
    return sheet(draw)


register("gui/resource_packs", _list_sheet("transferable_list", ((0, "select"), (32, "unselect"),
                                                                  (64, "move_down"), (96, "move_up"))))
register("gui/server_selection", _list_sheet("server_list", ((0, "join"), (64, "move_down"), (96, "move_up"))))
register("gui/world_selection", _list_sheet("world_list", ((0, "join"), (32, "marked_join"), (64, "warning"),
                                                           (96, "error"))))


def _spectator(c, ctx):
    for x, n in ((0, "teleport_to_player"), (16, "teleport_to_team"), (128, "close"), (144, "scroll_left"),
                 (160, "scroll_right")):
        put(c, ctx, SP + f"spectator/{n}", x, 0)


register("gui/spectator_widgets", sheet(_spectator))


def _checkbox(c, ctx):
    W = SP + "widget/checkbox"
    if ctx.w == 64:
        place_all(c, ctx, [(W, 0, 0), (W + "_highlighted", 20, 0), (W + "_selected", 0, 20),
                           (W + "_selected_highlighted", 20, 20)])
    else:
        place_all(c, ctx, [(W, 0, 0), (W + "_selected", 0, 20)])


register("gui/checkbox", sheet(_checkbox), size=(64, 64))
register("gui/checkbox@32x64", sheet(_checkbox), size=(32, 64))
register("gui/accessibility", sheet(lambda c, ctx: (icon_button(c, ctx, 0, 0, SP + "icon/accessibility", ""),
                                                    icon_button(c, ctx, 0, 20, SP + "icon/accessibility",
                                                                "_highlighted"))))
register("gui/chat_tags", sheet(lambda c, ctx: put(c, ctx, SP + "icon/chat_modified", 0, 0)))
register("gui/recipe_button", sheet(lambda c, ctx: place_all(c, ctx, [
    (SP + "recipe_book/button", 0, 0), (SP + "recipe_book/button_highlighted", 0, 19)])))
register("gui/report_button", sheet(lambda c, ctx: place_all(c, ctx, [
    (SP + "social_interactions/report_button", 0, 0), (SP + "social_interactions/report_button_highlighted", 0, 20),
    (SP + "social_interactions/report_button_disabled", 0, 40)])))
register("gui/slider", sheet(lambda c, ctx: place_all(c, ctx, [
    (SP + "widget/slider", 0, 0), (SP + "widget/slider_highlighted", 0, 20),
    (SP + "widget/slider_handle", 0, 40, 200, 20), (SP + "widget/slider_handle_highlighted", 0, 60, 200, 20)])))
register("gui/tab_button", sheet(lambda c, ctx: place_all(c, ctx, [
    (SP + "widget/tab_selected", 0, 0), (SP + "widget/tab_selected_highlighted", 0, 24),
    (SP + "widget/tab", 0, 48), (SP + "widget/tab_highlighted", 0, 72)])))
register("gui/social_interactions", sheet(lambda c, ctx: place_all(c, ctx, [
    (SP + "social_interactions/background", 0, 0),
    (SP + "social_interactions/mute_button", 0, 38), (SP + "social_interactions/mute_button_highlighted", 0, 58),
    (SP + "social_interactions/unmute_button", 20, 38),
    (SP + "social_interactions/unmute_button_highlighted", 20, 58)])))


def _bundle_sheet(c, ctx):
    edge = C("2a2b30")
    put(c, ctx, SP + "container/bundle/slot", 0, 0)
    put(c, ctx, SP + "container/bundle/blocked_slot", 0, 40)
    c.vline(0, 18, 37, edge)
    c.hline(0, 17, 20, edge)
    c.hline(0, 17, 60, edge)


register("gui/container/bundle", sheet(_bundle_sheet))
register("gui/container/recipe_background", sheet(lambda c, ctx: place_all(c, ctx, EMBED["recipe_book"])))


def _demo(c, ctx):
    panel(c, 0, 0, 248, 166)


register("gui/demo_background", sheet(_demo))


# ----------------------------------------------------------------- old trading GUI (1.7-1.13)
def _old_villager(ctx):
    from .containers import empty_arrow, base
    from .common import item_slot, player_inventory
    c = base(ctx)
    item_slot(c, 36, 53)
    item_slot(c, 62, 53)
    item_slot(c, 120, 53)
    empty_arrow(c, 86, 52)
    player_inventory(c, 8, 84)
    from .widgets import page_arrow, button_face, BTN, BTN_HL, BTN_OFF
    for col, right in ((176, True), (188, False)):
        for row, p in ((0, BTN), (19, BTN_HL), (38, BTN_OFF)):
            button_face(c, col, row, 12, 19, p)
            page_arrow(c, col + 3, row + 5, 6, 9, right, WHITE if p is not BTN_OFF else C("8a8d93"), C("2a2b30"))
    put(c, ctx, V + "out_of_stock", 212, 0)
    return c.tex()


register("gui/container/villager@256x256", _old_villager, size=(256, 256))


# ----------------------------------------------------------------- dirt backgrounds (block/dirt)
def _dirt(bright):
    def fn(ctx):
        t = TEXTURES["block/dirt"].fn(ctx)
        col = np.asarray(t.color, np.float32)
        if bright:
            col = np.clip(col * 1.35 + 0.08, 0, 1)
        return Tex(ctx, col, alpha=1.0, wrap=True, grain=0)
    return fn


register("gui/options_background", _dirt(False))
register("gui/light_dirt_background", _dirt(True))


# ----------------------------------------------------------------- removed features (no 26.3 equivalent)
def _preset(seed, tint):
    from .scenes import framed, landscape

    def fn(ctx):
        return framed(ctx, landscape(ctx, seed, 0.55, tint)).tex()
    return fn


for _n, _seed, _tint in (("chaos", 21.0, ("7a3ab0", 0.35)), ("delight", 22.0, ("f2c0e0", 0.2)),
                         ("drought", 23.0, ("d8b060", 0.45)), ("luck", 24.0, ("60d060", 0.25)),
                         ("madness", 25.0, ("e04030", 0.35)), ("water", 26.0, ("3f76c4", 0.5))):
    register(f"gui/presets/{_n}", _preset(_seed, _tint))


def _backup(kind, hl):
    def fn(ctx):
        c = Canvas(ctx)
        col = C("ffffff") if hl else C("c4c7ce")
        if kind == "changes":
            c.rect(1, 0, 7, 9, C("1a1b1f"))
            c.rect(2, 1, 5, 7, col)
            c.hline(3, 5, 3, C("6d7079"))
            c.hline(3, 5, 5, C("6d7079"))
        else:
            c.ring(4.5, 4.5, 4.2, 1.2, col)
            c.rect(0, 0, 3, 3, col)
        return c.tex()
    return fn


for _k in ("changes", "restore"):
    register(SP + f"backup/{_k}", _backup(_k, False))
    register(SP + f"backup/{_k}_highlighted", _backup(_k, True))


def _bundle_bg(ctx):
    c = Canvas(ctx)
    c.rect(1, 0, 30, 32, C("2a1e14"))
    c.rect(0, 1, 32, 30, C("2a1e14"))
    c.rect(1, 1, 30, 30, C("6b4a2e"))
    c.rect(2, 2, 28, 28, C("4a3424"))
    return c.tex()


register(SP + "container/bundle/background", _bundle_bg)


def _legacy_smithing(ctx):
    from .containers import base, empty_arrow, plus
    from .common import big_slot, item_slot, player_inventory
    c = base(ctx)
    item_slot(c, 27, 47)
    item_slot(c, 76, 47)
    big_slot(c, 134, 47)
    plus(c, 52, 49)
    empty_arrow(c, 101, 47)
    player_inventory(c, 8, 84)
    put(c, ctx, SP + "container/smithing/error", 176, 0)
    return c.tex()


register("gui/container/legacy_smithing", _legacy_smithing)


def _stream(ctx):
    c = Canvas(ctx)
    for k in range(4):
        col = [C("e5483d"), C("ec9d3a"), C("5ad65a"), C("6d7079")][k]
        c.circle(8, 8 + 16 * k, 5.5, mix(col, BLACK, 0.5))
        c.circle(8, 8 + 16 * k, 4.5, col)
    return c.tex()


register("gui/stream_indicator", _stream)
