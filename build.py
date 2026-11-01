#!/usr/bin/env python3
"""Build the CircuitMC Default resource packs.

    .venv/bin/python build.py                         # 16x and 64x, all textures
    .venv/bin/python build.py --res 16 64 256 1024    # every resolution
    .venv/bin/python build.py --res 16 --only block/ --preview

Outputs dist/<res>x/<pack>/ folders and dist/<pack>-<version>-<res>x.zip.
Hand-drawn PNGs in overrides/<res>x/ (or overrides/16x/, upscaled) win over
generated textures with the same path.

Version support (full builds, i.e. without --area/--only):
  * CircuitMC-Default         1.13 -> 26.x. The base folder uses the texture
    layout of <= 1.20.1 for paths whose size changed later; pack overlays
    (read by 1.20.2+) carry the newer layouts. Old texture names are filled
    from data/aliases.json so renamed textures still resolve.
  * CircuitMC-Default-Legacy  1.7 -> 1.12 (blocks/, items/ era names).
Generators are written for 26.3 paths; a different layout of the same path is
registered as "<path>@<w>x<h>".
"""
import argparse
import os
import importlib
import json
import multiprocessing as mp
import pkgutil
import shutil
import sys
import time
import traceback
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

import generator.textures
from generator.engine import Ctx, encode
from generator.registry import FILES, TEXTURES

ROOT = Path(__file__).resolve().parent
DIST = ROOT / os.environ.get("CMC_DIST", "dist")
OVERRIDES = ROOT / "overrides"
VERSION = "0.3.0"
VANILLA = "26.3"

# Sampled versions and their resource pack formats.
MODERN = [("1.13.2", 4), ("1.14.4", 4), ("1.16.5", 6), ("1.17.1", 7), ("1.19.2", 9), ("1.20.1", 15),
          ("1.20.4", 22), ("1.21.1", 34), ("1.21.4", 46), ("1.21.8", 64), ("26.3", 97)]
LEGACY = [("1.7.10", 1), ("1.8.9", 1), ("1.12.2", 3)]
OVERLAY_MIN = 18      # first format that understands pack overlays (1.20.2)
OPEN_MAX = 999        # "and every later version"
# 26.x rejects ranged ("multi-version") metadata whose minimum is below 15, so the
# declared minimum is 15 (1.20); 1.13-1.19 still load the pack after the
# "made for another version" prompt.
MIN_FORMAT = 15

PACKS = {
    "core": dict(dir="CircuitMC-Default", title="CircuitMC Default",
                 blurb="Original art · CC BY-NC-SA 4.0"),
    "legacy": dict(dir="CircuitMC-Default-Legacy", title="CircuitMC Default (1.7–1.12)",
                   blurb="Original art · CC BY-NC-SA 4.0"),
    "redstone_power": dict(dir="CircuitMC-Redstone-Power", title="CircuitMC Redstone Power",
                           blurb="Shows signal strength on redstone dust"),
}

MAX_FRAME_PIXELS = 4096 * 4096
MAX_STRIP_HEIGHT = 16384
COPY_META = ("texture", "gui", "villager", "palette")  # functional vanilla mcmeta sections
LICENSE_FILES = ["LICENSE", "COMMERCIAL.md", "NOTICE.md"]

INDEXES = {v: json.loads((ROOT / "data" / f"vanilla-{v}.json").read_text())["textures"]
           for v, _ in LEGACY + MODERN if (ROOT / "data" / f"vanilla-{v}.json").exists()}
VANILLA_INDEX = INDEXES[VANILLA]
_alias_file = ROOT / "data" / "aliases.json"
_alias_data = json.loads(_alias_file.read_text()) if _alias_file.exists() else {}
ALIASES = _alias_data.get("aliases", {})
# partial aliases: only valid for some versions; resolve() checks the frame size anyway
VERSION_ALIASES = {p: v["target"] for p, v in _alias_data.get("by_version", {}).items()}
LOAD_ERRORS = []


def load_generators():
    """Import every module under generator/textures, recording (not raising) failures."""
    for mod in pkgutil.walk_packages(generator.textures.__path__, "generator.textures."):
        try:
            importlib.import_module(mod.name)
        except Exception:
            LOAD_ERRORS.append((mod.name, traceback.format_exc()))


load_generators()


def default_pbr(path):
    return path.startswith(("block/", "item/", "entity/", "/minecraft/optifine/", "/circuitmc/textures/block/"))


def frame_layout(entry):
    """(frame_w, frame_h, frames) of a vanilla index entry."""
    anim = entry.get("mcmeta", {}).get("animation")
    if anim is None:
        return entry["w"], entry["h"], 1
    w = anim.get("width", entry["w"])
    h = anim.get("height", w)
    return w, h, max(1, entry["h"] // h)


def index_entry(path):
    """Newest vanilla index entry for a path (26.3 first, then older)."""
    for v, _ in reversed(LEGACY + MODERN):
        e = INDEXES.get(v, {}).get(path)
        if e:
            return e
    return None


def native_layout(spec):
    """(frame_w, frame_h, frames) in texels for a registry entry."""
    base = spec.path.split("@")[0]
    entry = index_entry(base)
    if spec.size:
        w, h = spec.size
        frames = 1
    elif entry:
        w, h, frames = frame_layout(entry)
    else:
        w, h, frames = 16, 16, 1
    return w, h, spec.frames or frames


def pick_scale(res, w, h, frames):
    s = max(1, res // 16)
    while s > 1 and (w * h * s * s > MAX_FRAME_PIXELS or h * s * frames > MAX_STRIP_HEIGHT):
        s //= 2
    return s


def out_file(root, path, suffix=""):
    if path.startswith("/"):
        return root / "assets" / f"{path[1:]}{suffix}.png"
    return root / "assets" / "minecraft" / "textures" / f"{path}{suffix}.png"


def find_override(path, res):
    rel = (path[1:] if path.startswith("/") else f"minecraft/textures/{path}") + ".png"
    for r in (res, 16):
        f = OVERRIDES / f"{r}x" / "assets" / rel
        if f.exists():
            return f, r
    return None, None


@dataclass
class Target:
    pack: str              # key of PACKS
    path: str              # output path (registry style; "/..." = assets-relative)
    key: str               # registry key that renders it
    sub: str = ""          # overlay directory ("" = pack root)
    meta: dict = field(default_factory=dict)  # functional vanilla mcmeta for this layout


def target_root(res, t):
    root = DIST / f"{res}x" / PACKS[t.pack]["dir"]
    return root / t.sub if t.sub else root


def render(job):
    t, res = job
    spec = TEXTURES[t.key]
    root = target_root(res, t)
    target = out_file(root, t.path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        w, h, frames = native_layout(spec)
        pbr = default_pbr(t.path) if spec.pbr is None else spec.pbr
        manual, manual_res = find_override(t.path, res)
        if manual:
            img = Image.open(manual).convert("RGBA")
            if manual_res != res:
                f = max(1, res // manual_res)
                img = img.resize((img.width * f, img.height * f), Image.NEAREST)
            img.save(target)
            for suffix in ("_n", "_s"):
                side = manual.with_name(manual.stem + suffix + ".png")
                if side.exists():
                    shutil.copyfile(side, out_file(root, t.path, suffix))
        else:
            s = pick_scale(res, w, h, frames)
            layers = [[], [], []]
            for i in range(frames):
                ctx = Ctx(t.key.split("@")[0], w, h, s, frame=i, frames=frames)
                out = spec.fn(ctx)
                if isinstance(out, list):
                    out = out[i]
                for k, arr in enumerate(encode(out)):
                    layers[k].append(arr)
            stacked = [np.concatenate(l, 0) for l in layers]
            Image.fromarray(stacked[0], "RGBA").save(target, compress_level=6)
            if pbr:
                Image.fromarray(stacked[1], "RGBA").save(out_file(root, t.path, "_n"), compress_level=6)
                Image.fromarray(stacked[2], "RGBA").save(out_file(root, t.path, "_s"), compress_level=6)
        meta = {k: v for k, v in t.meta.items() if k in COPY_META}
        if frames > 1 and not manual:
            meta["animation"] = {"frametime": spec.frametime, **({"interpolate": True} if spec.interpolate else {})}
            if w != h:
                meta["animation"].update(width=w * s, height=h * s)  # frame size in pixels
        meta.update(spec.meta)
        if meta:
            target.with_name(target.name + ".mcmeta").write_text(json.dumps(meta, indent=1))
        return t, None
    except Exception:
        return t, traceback.format_exc()


# ---------------------------------------------------------------- targets

def resolve(path, dims):
    """Registry key able to render `path` with frame size `dims`, or None."""
    cands = [path] + [a[path] for a in (ALIASES, VERSION_ALIASES) if path in a]
    for cand in cands:
        variant = f"{cand}@{dims[0]}x{dims[1]}"
        if variant in TEXTURES:
            return variant
        if cand in TEXTURES and native_layout(TEXTURES[cand])[:2] == tuple(dims):
            return cand
    return None


def modern_targets():
    """Core pack targets: base layout (<= 1.20.1 wins) + overlays for newer layouts."""
    targets, overlays, skipped = [], {}, []
    paths = sorted(set().union(*(INDEXES[v] for v, _ in MODERN if v in INDEXES)))
    for p in paths:
        seen = [(v, f, INDEXES[v][p]) for v, f in MODERN if p in INDEXES.get(v, {})]
        old = [x for x in seen if x[1] < OVERLAY_MIN]
        # Pre-overlay versions share the base folder: use the layout most of them use
        # (ties -> newest), e.g. the 256x256 title logo of 1.13-1.19 over 1.20's.
        pool = old or seen
        votes = {}
        for v, f, e in pool:
            votes.setdefault(frame_layout(e)[:2], []).append((v, f, e))
        bv, bf, be = max(votes.values(), key=lambda xs: (len(xs), MODERN.index(xs[-1][:2])))[-1]
        bdims = frame_layout(be)[:2]
        key = resolve(p, bdims)
        if key:
            targets.append(Target("core", p, key, meta=be.get("mcmeta", {})))
        else:
            skipped.append((p, bv))
        # newer layouts -> overlays
        prev_fmt, run = None, []
        sampled = [(v, f) for v, f in MODERN if v in INDEXES]
        for i, (v, f) in enumerate(sampled):
            e = INDEXES[v].get(p)
            dims = frame_layout(e)[:2] if e else None
            if f >= OVERLAY_MIN and dims and dims != bdims:
                if run and run[-1][2] == dims:
                    run[-1][1] = f
                else:
                    start = max(OVERLAY_MIN, (sampled[i - 1][1] + 1) if i else OVERLAY_MIN)
                    run.append([start, f, dims, e])
        for start, end, dims, e in run:
            end = OPEN_MAX if end == MODERN[-1][1] else end
            key = resolve(p, dims)
            if key:
                sub = f"overlay_{start}_{end}"
                overlays[sub] = (start, end)
                targets.append(Target("core", p, key, sub=sub, meta=e.get("mcmeta", {})))
            else:
                skipped.append((p, f"{dims[0]}x{dims[1]} overlay"))
    # registry entries outside the vanilla index (CTM tiles, own namespaces, add-ons)
    for key, spec in TEXTURES.items():
        if "@" not in key and (key.startswith("/") or spec.pack != "core"):
            targets.append(Target(spec.pack, key, key))
    return targets, overlays, skipped


def legacy_targets():
    targets, skipped = [], []
    paths = sorted(set().union(*(INDEXES[v] for v, _ in LEGACY if v in INDEXES)))
    for p in paths:
        v, e = [(v, INDEXES[v][p]) for v, _ in LEGACY if p in INDEXES.get(v, {})][-1]
        key = resolve(p, frame_layout(e)[:2])
        if key:
            targets.append(Target("legacy", p, key, meta=e.get("mcmeta", {})))
        else:
            skipped.append((p, v))
    for key in TEXTURES:
        if key.startswith("/minecraft/optifine/ctm/glass/"):
            targets.append(Target("legacy", key, key))
    return targets, skipped


def pack_mcmeta(pack, overlays=None):
    info = PACKS[pack]
    desc = [{"text": f"{info['title']} ", "color": "gold"},
            {"text": f"v{VERSION}\n", "color": "gray"},
            {"text": info["blurb"], "color": "gray"}]
    if pack == "legacy":
        return {"pack": {"pack_format": 3, "description": f"{info['title']} v{VERSION} - {info['blurb']}"}}
    meta = {"pack": {
        "description": desc,
        "pack_format": MIN_FORMAT,                       # read by 1.13 - 1.20.1 (warns below 1.20)
        "supported_formats": [MIN_FORMAT, OPEN_MAX],     # read by 1.20.2 - 1.21.8
        "min_format": MIN_FORMAT,                        # read by 1.21.9+
        "max_format": OPEN_MAX,
    }}
    if overlays:
        meta["overlays"] = {"entries": [
            {"formats": [a, b], "min_format": a, "max_format": b, "directory": d}
            for d, (a, b) in sorted(overlays.items(), key=lambda kv: kv[1])]}
    return meta


def pack_icon(res_root):
    core = res_root / PACKS["core"]["dir"] / "assets" / "minecraft" / "textures" / "block"
    tiles = ["grass_block_side", "stone", "oak_planks", "diamond_ore"]
    icon = Image.new("RGBA", (32, 32))
    for i, name in enumerate(tiles):
        f = core / f"{name}.png"
        if f.exists():
            tile = Image.open(f).convert("RGBA").resize((16, 16), Image.BOX)
            if name == "grass_block_side":
                ov = core / "grass_block_side_overlay.png"
                if ov.exists():
                    o = tinted(Image.open(ov).convert("RGBA").resize((16, 16), Image.BOX), "8cbc58")
                    tile.alpha_composite(o)
            icon.paste(tile, ((i % 2) * 16, (i // 2) * 16))
    return icon.resize((128, 128), Image.NEAREST)


def finish_packs(res, packs, overlays=None):
    res_root = DIST / f"{res}x"
    for pack in packs:
        root = res_root / PACKS[pack]["dir"]
        root.mkdir(parents=True, exist_ok=True)
        for (p, path), text in FILES.items():
            legacy_ok = pack == "legacy" and p == "core" and "optifine/ctm/glass/" in path
            if p == pack or legacy_ok:
                f = root / "assets" / path
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text)
        (root / "pack.mcmeta").write_text(json.dumps(
            pack_mcmeta(pack, overlays if pack == "core" else None), indent=1, ensure_ascii=False))
        for f in LICENSE_FILES:
            shutil.copyfile(ROOT / f, root / f)
    icon = pack_icon(res_root)
    for pack in packs:
        icon.save(res_root / PACKS[pack]["dir"] / "pack.png")


def zip_pack(res, pack):
    root = DIST / f"{res}x" / PACKS[pack]["dir"]
    zpath = DIST / f"{PACKS[pack]['dir']}-{VERSION}-{res}x.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(root.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(root).as_posix())
    return zpath


# ---------------------------------------------------------------- preview

PREVIEW_TINTS = [
    (("grass_block_top", "grass_block_side_overlay", "short_grass", "tall_grass", "fern",
      "large_fern", "sugar_cane", "potted_fern"), "8cbc58"),
    (("oak_leaves", "jungle_leaves", "acacia_leaves", "dark_oak_leaves", "mangrove_leaves",
      "vine"), "68a83a"),
    (("spruce_leaves",), "619961"),
    (("birch_leaves",), "80a755"),
    (("water_",), "3f76e4"),
    (("lily_pad",), "208030"),
    (("redstone_dust",), "e01010"),
    (("melon_stem", "pumpkin_stem", "attached_melon_stem", "attached_pumpkin_stem"), "c0a030"),
]


def tint_for(name):
    base = name.split("/")[-1]
    for keys, color in PREVIEW_TINTS:
        if base.startswith(keys):
            return color
    return None


def tinted(img, color):
    c = np.array([int(color[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255
    a = np.asarray(img, np.float32)
    a[..., :3] *= c
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def preview(prefixes, res=16, cols=32, zoom=2, only=None, tag="all"):
    root = DIST / f"{res}x" / PACKS["core"]["dir"] / "assets" / "minecraft" / "textures"
    names = sorted(p for p in (only or TEXTURES) if not p.startswith("/") and p.startswith(tuple(prefixes))
                   and (root / f"{p}.png").exists())
    cell = 32 * zoom + 4
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell, max(1, rows) * cell), (30, 31, 34, 255))
    checker = Image.new("RGBA", (32 * zoom, 32 * zoom), (44, 45, 49, 255))
    cd = np.asarray(checker).copy()
    yy, xx = np.mgrid[0:32 * zoom, 0:32 * zoom]
    cd[((xx // 4 + yy // 4) % 2) == 1] = (58, 59, 64, 255)
    checker = Image.fromarray(cd)
    for i, name in enumerate(names):
        img = Image.open(root / f"{name}.png").convert("RGBA")
        t = tint_for(name)
        if t:
            img = tinted(img, t)
        if name.startswith("block/"):
            img = img.crop((0, 0, img.width, img.width)) if img.height > img.width else img
            img = img.resize((16, 16 * img.height // img.width), Image.BOX)
            tile = Image.new("RGBA", (32, 32))
            for ox in (0, 16):
                for oy in (0, 16):
                    tile.paste(img.crop((0, 0, 16, 16)), (ox, oy))
        else:  # sprites/sheets: show once, fitted into the cell
            f = 32 / max(img.width, img.height)
            img = img.resize((max(1, round(img.width * f)), max(1, round(img.height * f))),
                             Image.NEAREST if f >= 1 else Image.BOX)
            tile = Image.new("RGBA", (32, 32))
            tile.paste(img, (0, 0))
        tile = tile.resize((32 * zoom, 32 * zoom), Image.NEAREST)
        cell_img = checker.copy()
        cell_img.alpha_composite(tile)
        sheet.paste(cell_img, ((i % cols) * cell + 2, (i // cols) * cell + 2))
    path = DIST / f"preview-{tag}.png"
    sheet.save(path)
    (DIST / f"preview-{tag}.txt").write_text("\n".join(f"{i // cols + 1:>3},{i % cols + 1:>3} {n}" for i, n in enumerate(names)))
    print(f"preview ({len(names)} textures) -> {path}")


# ---------------------------------------------------------------- main

def report_versions(targets):
    """Per sampled version: share of its vanilla textures the matching pack provides."""
    have = {("legacy" if t.pack == "legacy" else "core", t.path) for t in targets}
    for v, f in LEGACY + MODERN:
        if v not in INDEXES:
            continue
        pack = "legacy" if (v, f) in LEGACY else "core"
        n = len(INDEXES[v])
        c = sum(1 for p in INDEXES[v] if (pack, p) in have)
        print(f"  {v:>7} (format {f:>2}): {c}/{n} ({c / n:.0%})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", type=int, nargs="+", default=[16, 64], choices=[16, 32, 64, 128, 256, 512, 1024])
    ap.add_argument("--only", nargs="*", default=[], help="path prefixes to build, e.g. block/ item/")
    ap.add_argument("--area", help="build only one work area from data/assignments.json, e.g. block_stone")
    ap.add_argument("--jobs", type=int, default=mp.cpu_count())
    ap.add_argument("--preview", nargs="*", help="contact sheet of these prefixes (default block/)")
    ap.add_argument("--no-zip", action="store_true")
    ap.add_argument("--clean", action="store_true", help="delete dist/<res>x before building")
    ap.add_argument("--modern-only", action="store_true", help="skip the 1.7-1.12 legacy pack")
    ap.add_argument("--patch", nargs="+", help="full build, but re-render only targets under these path "
                                              "prefixes (pack metadata, static files and zips are refreshed)")
    args = ap.parse_args()

    for mod, err in LOAD_ERRORS:
        print(f"!! failed to import {mod}:\n{err}", file=sys.stderr)

    full = not (args.only or args.area)
    if full:
        targets, overlays, skipped = modern_targets()
        if not args.modern_only:
            lt, lskipped = legacy_targets()
            targets += lt
        if args.patch:
            targets = [t for t in targets if t.path.startswith(tuple(args.patch))]
        paths = sorted({t.key for t in targets})
    else:
        overlays, skipped = {}, []
        paths = sorted(p for p in TEXTURES if "@" not in p and (not args.only or p.startswith(tuple(args.only))))
        if args.area:
            assign = json.loads((ROOT / "data" / "assignments.json").read_text())
            paths = [p for p in paths if assign.get(p) == args.area]
        targets = [Target(TEXTURES[p].pack, p, p, meta=VANILLA_INDEX.get(p, {}).get("mcmeta", {})) for p in paths]
    failures = []
    for res in args.res:
        if args.clean and (DIST / f"{res}x").exists():
            shutil.rmtree(DIST / f"{res}x")
        t0 = time.time()
        ctx = mp.get_context("fork")
        with ctx.Pool(args.jobs) as pool:
            for t, err in pool.imap_unordered(render, [(t, res) for t in targets], chunksize=4):
                if err:
                    failures.append((res, t.path, err))
        packs = sorted({t.pack for t in targets} | ({p for p, _ in FILES} if full else set()) | {"core"}
                       | ({"legacy"} if full and not args.modern_only else set()))
        finish_packs(res, packs, overlays)
        print(f"{res}x: {len(targets)} files from {len(paths)} generators in {time.time() - t0:.1f}s")
        if not args.no_zip:
            for pack in packs:
                print(f"  -> {zip_pack(res, pack)}")

    covered = sum(1 for p in VANILLA_INDEX if p in TEXTURES)
    print(f"coverage: {covered}/{len(VANILLA_INDEX)} vanilla {VANILLA} textures ({covered / len(VANILLA_INDEX):.1%})")
    if full and not args.patch:
        report_versions(targets)
        (DIST / "skipped.txt").write_text("\n".join(f"{p}  ({why})" for p, why in skipped))
    for res, path, err in failures:
        print(f"!! {res}x {path}:\n{err}", file=sys.stderr)
    if args.preview is not None:
        preview(args.preview or [""], only=paths if args.area else None, tag=args.area or "all")
    return 1 if failures or LOAD_ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
