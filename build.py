#!/usr/bin/env python3
"""Build the CircuitMC Default resource packs.

    .venv/bin/python build.py                         # 16x and 64x, all textures
    .venv/bin/python build.py --res 16 64 256 1024    # every resolution
    .venv/bin/python build.py --res 16 --only block/ --preview

Outputs dist/<res>x/<pack>/ folders and dist/<pack>-<version>-<res>x.zip.
Hand-drawn PNGs in overrides/<res>x/ (or overrides/16x/, upscaled) win over
generated textures with the same path.

Version support (full builds, i.e. without --area/--only): one pack per game
version range (GROUPS below), each laid out exactly like the vanilla versions
it serves; the 1.20.2+ pack additionally uses pack overlays for the layout
changes between 1.20.2 and 26.x. Old texture names resolve through
data/aliases.json. Generators are written for 26.3 paths; another layout of the
same path is registered as "<path>@<w>x<h>", and a same-size variant needed by
some ranges as "<path>#<tag>" (tags per group below).
Each generator is rendered once per resolution into dist/<res>x/_cache and
hard-linked into every pack that uses it.
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
VERSION = "0.3.1"
VANILLA = "26.3"

VERSION = "0.4.0"
VANILLA = "26.3"


@dataclass
class Group:
    gid: str               # short id, used in folder and file names
    label: str             # human readable version range
    versions: list         # sampled vanilla versions (indexes in data/), oldest first
    formats: list          # resource pack format of each sampled version
    pack_format: int       # value written to pack.mcmeta
    tags: list = field(default_factory=list)  # variant tags tried before the plain key
    overlays: bool = False  # 1.20.2+: newer layouts go to pack overlays


GROUPS = [
    Group("1.7", "1.7.10", ["1.7.10"], [1], 1, ["pre-1.13", "pre-1.19.3"]),
    Group("1.8-1.12", "1.8–1.12.2", ["1.8.9", "1.10.2", "1.12.2"], [1, 2, 3], 3, ["pre-1.13", "pre-1.19.3"]),
    Group("1.13", "1.13–1.13.2", ["1.13.2"], [4], 4, ["pre-1.19.3"]),
    Group("1.14-1.15", "1.14–1.15.2", ["1.14.4"], [4], 4, ["pre-1.19.3"]),
    Group("1.16", "1.16–1.16.5", ["1.16.5"], [6], 6, ["pre-1.19.3"]),
    Group("1.17-1.19.2", "1.17–1.19.2", ["1.17.1", "1.19.2"], [7, 9], 9, ["pre-1.19.3"]),
    Group("1.19.3-1.19.4", "1.19.3–1.19.4", ["1.19.4"], [13], 13),
    Group("1.20-1.20.1", "1.20–1.20.1", ["1.20.1"], [15], 15),
    Group("1.20.2+", "1.20.2–26.x", ["1.20.4", "1.21.1", "1.21.4", "1.21.8", "26.3"], [22, 34, 46, 64, 97], 18,
          overlays=True),
]
MAIN = GROUPS[-1].gid
OVERLAY_MIN = 18      # first format that understands pack overlays (1.20.2)
OPEN_MAX = 999        # "and every later version"
ADDON_FORMAT = 15     # add-ons: one pack for 1.13+ (26.x rejects ranged metadata below 15)

PACKS = {f"core-{g.gid}": dict(dir=f"CircuitMC-Default-mc{g.gid}", title="CircuitMC Default",
                               blurb=f"Minecraft {g.label} · CC BY-NC-SA 4.0", group=g) for g in GROUPS}
PACKS["redstone_power"] = dict(dir="CircuitMC-Redstone-Power", title="CircuitMC Redstone Power",
                               blurb="Shows signal strength on redstone dust", group=None)
MAIN_PACK = f"core-{MAIN}"

MAX_FRAME_PIXELS = 4096 * 4096
MAX_STRIP_HEIGHT = 16384
COPY_META = ("texture", "gui", "villager", "palette")  # functional vanilla mcmeta sections
LICENSE_FILES = ["LICENSE", "COMMERCIAL.md", "NOTICE.md"]

ALL_VERSIONS = [v for g in GROUPS for v in g.versions]
INDEXES = {v: json.loads((ROOT / "data" / f"vanilla-{v}.json").read_text())["textures"]
           for v in ALL_VERSIONS if (ROOT / "data" / f"vanilla-{v}.json").exists()}
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
    for v in reversed(ALL_VERSIONS):
        e = INDEXES.get(v, {}).get(path)
        if e:
            return e
    return None


def native_layout(spec):
    """(frame_w, frame_h, frames) in texels for a registry entry."""
    base = spec.path.split("@")[0].split("#")[0]
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


def pack_root(res, pack):
    return DIST / f"{res}x" / PACKS[pack]["dir"]


def cache_name(key):
    return key.strip("/").replace("/", "__").replace("#", "~") 


def render(job):
    """Render one registry key into the per-resolution cache. Returns (key, info, error)."""
    key, res = job
    spec = TEXTURES[key]
    cache = DIST / f"{res}x" / "_cache"
    base = cache / cache_name(key)
    try:
        w, h, frames = native_layout(spec)
        pbr = default_pbr(key.split("@")[0].split("#")[0]) if spec.pbr is None else spec.pbr
        s = pick_scale(res, w, h, frames)
        layers = [[], [], []]
        for i in range(frames):
            ctx = Ctx(key.split("@")[0].split("#")[0], w, h, s, frame=i, frames=frames)
            out = spec.fn(ctx)
            if isinstance(out, list):
                out = out[i]
            for k, arr in enumerate(encode(out)):
                layers[k].append(arr)
        stacked = [np.concatenate(l, 0) for l in layers]
        Image.fromarray(stacked[0], "RGBA").save(f"{base}.png", compress_level=6)
        if pbr:
            Image.fromarray(stacked[1], "RGBA").save(f"{base}_n.png", compress_level=6)
            Image.fromarray(stacked[2], "RGBA").save(f"{base}_s.png", compress_level=6)
        return key, dict(w=w, h=h, frames=frames, s=s, pbr=pbr), None
    except Exception:
        return key, None, traceback.format_exc()


def _link(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copyfile(src, dst)


def assemble(res, targets, infos):
    """Place cached renders (or hand-drawn overrides) at every target path."""
    cache = DIST / f"{res}x" / "_cache"
    for t in targets:
        info = infos.get(t.key)
        if info is None:
            continue
        root = pack_root(res, t.pack)
        root = root / t.sub if t.sub else root
        target = out_file(root, t.path)
        manual, manual_res = find_override(t.path, res)
        if manual:
            target.parent.mkdir(parents=True, exist_ok=True)
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
            base = cache / cache_name(t.key)
            _link(Path(f"{base}.png"), target)
            if info["pbr"]:
                _link(Path(f"{base}_n.png"), out_file(root, t.path, "_n"))
                _link(Path(f"{base}_s.png"), out_file(root, t.path, "_s"))
        spec = TEXTURES[t.key]
        meta = {k: v for k, v in t.meta.items() if k in COPY_META}
        if info["frames"] > 1 and not manual:
            meta["animation"] = {"frametime": spec.frametime, **({"interpolate": True} if spec.interpolate else {})}
            if info["w"] != info["h"]:
                meta["animation"].update(width=info["w"] * info["s"], height=info["h"] * info["s"])
        meta.update(spec.meta)
        mf = target.with_name(target.name + ".mcmeta")
        if meta:
            mf.write_text(json.dumps(meta, indent=1))
        elif mf.exists():
            mf.unlink()


# ---------------------------------------------------------------- targets

def resolve(path, dims, tags=()):
    """Registry key able to render `path` with frame size `dims`, or None."""
    cands = [path] + [a[path] for a in (ALIASES, VERSION_ALIASES) if path in a]
    for cand in cands:
        for tag in tags:
            k = f"{cand}#{tag}"
            if k in TEXTURES and native_layout(TEXTURES[k])[:2] == tuple(dims):
                return k
        variant = f"{cand}@{dims[0]}x{dims[1]}"
        if variant in TEXTURES:
            return variant
        if cand in TEXTURES and native_layout(TEXTURES[cand])[:2] == tuple(dims):
            return cand
    return None


def group_targets(g):
    """Targets of one version-range pack. Returns (targets, overlays, skipped)."""
    pack = f"core-{g.gid}"
    targets, overlays, skipped = [], {}, []
    sampled = [(v, f) for v, f in zip(g.versions, g.formats) if v in INDEXES]
    paths = sorted(set().union(*(INDEXES[v] for v, _ in sampled)))
    for p in paths:
        seen = [(v, f, INDEXES[v][p]) for v, f in sampled if p in INDEXES[v]]
        bv, bf, be = seen[-1]                  # base layout: newest version of the range
        bdims = frame_layout(be)[:2]
        key = resolve(p, bdims, g.tags)
        if key:
            targets.append(Target(pack, p, key, meta=be.get("mcmeta", {})))
        else:
            skipped.append((p, bv))
        if not g.overlays:
            continue
        run = []                                # older layouts inside the range -> overlays
        for i, (v, f) in enumerate(sampled):
            e = INDEXES[v].get(p)
            dims = frame_layout(e)[:2] if e else None
            if dims and dims != bdims:
                if run and run[-1][2] == dims and run[-1][1] == sampled[i - 1][1]:
                    run[-1][1] = f
                else:
                    start = max(g.pack_format, (sampled[i - 1][1] + 1) if i else g.pack_format)
                    run.append([start, f, dims, e])
        for start, end, dims, e in run:
            key = resolve(p, dims, g.tags)
            if key:
                sub = f"overlay_{start}_{end}"
                overlays[sub] = (start, end)
                targets.append(Target(pack, p, key, sub=sub, meta=e.get("mcmeta", {})))
            else:
                skipped.append((p, f"{dims[0]}x{dims[1]} overlay"))
    # registry entries outside the vanilla index (CTM tiles, own namespaces)
    legacy = g.versions[-1].startswith("1.") and int(g.versions[-1].split(".")[1]) < 13
    for key, spec in TEXTURES.items():
        if "@" in key or "#" in key or spec.pack != "core" or not key.startswith("/"):
            continue
        if legacy and not key.startswith("/minecraft/optifine/ctm/glass/"):
            continue
        targets.append(Target(pack, key, key))
    return targets, overlays, skipped


def addon_targets():
    return [Target(spec.pack, key, key) for key, spec in TEXTURES.items()
            if spec.pack != "core" and "@" not in key and "#" not in key]


def pack_mcmeta(pack, overlays=None):
    info = PACKS[pack]
    g = info["group"]
    desc = [{"text": f"{info['title']} ", "color": "gold"},
            {"text": f"v{VERSION}\n", "color": "gray"},
            {"text": info["blurb"], "color": "gray"}]
    if g is None:  # add-on
        return {"pack": {"description": desc, "pack_format": ADDON_FORMAT,
                         "supported_formats": [ADDON_FORMAT, OPEN_MAX],
                         "min_format": ADDON_FORMAT, "max_format": OPEN_MAX}}
    if g.pack_format < 4:  # 1.7-1.12 understand plain-string descriptions only
        return {"pack": {"pack_format": g.pack_format,
                         "description": f"{info['title']} v{VERSION} - {info['blurb']}"}}
    meta = {"pack": {"description": desc, "pack_format": g.pack_format}}
    if g.overlays:
        meta["pack"].update(supported_formats=[g.pack_format, OPEN_MAX],
                            min_format=g.pack_format, max_format=OPEN_MAX)
        if overlays:
            meta["overlays"] = {"entries": [
                {"formats": [a, b], "min_format": a, "max_format": b, "directory": d}
                for d, (a, b) in sorted(overlays.items(), key=lambda kv: kv[1])]}
    return meta


def pack_icon(res):
    core = pack_root(res, MAIN_PACK) / "assets" / "minecraft" / "textures" / "block"
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


def static_ok(pack, path):
    """Which packs get which static (non-image) files."""
    g = PACKS[pack]["group"]
    if g is None:
        return False
    if g.pack_format < 4:
        return "optifine/ctm/glass/" in path
    if path.startswith("minecraft/font/include/"):
        return g.pack_format >= 15
    return True


def finish_packs(res, packs, overlays):
    icon = pack_icon(res)
    for pack in packs:
        root = pack_root(res, pack)
        root.mkdir(parents=True, exist_ok=True)
        for (p, path), text in FILES.items():
            if (p == pack) or (p == "core" and pack.startswith("core-") and static_ok(pack, path)):
                f = root / "assets" / path
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text)
        (root / "pack.mcmeta").write_text(json.dumps(
            pack_mcmeta(pack, overlays.get(pack)), indent=1, ensure_ascii=False))
        for f in LICENSE_FILES:
            shutil.copyfile(ROOT / f, root / f)
        icon.save(root / "pack.png")


def zip_pack(res, pack):
    root = pack_root(res, pack)
    g = PACKS[pack]["group"]
    name = PACKS[pack]["dir"] if g is None else f"CircuitMC-Default-mc{g.gid}"
    zpath = DIST / f"{name}-{VERSION}-{res}x.zip"
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
    root = pack_root(res, MAIN_PACK) / "assets" / "minecraft" / "textures"
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
    """Per sampled version: share of its vanilla textures its pack provides."""
    have = {(t.pack, t.path) for t in targets}
    for g in GROUPS:
        for v, f in zip(g.versions, g.formats):
            if v not in INDEXES:
                continue
            n = len(INDEXES[v])
            c = sum(1 for p in INDEXES[v] if (f"core-{g.gid}", p) in have)
            print(f"  {v:>7} (format {f:>2}, pack mc{g.gid}): {c}/{n} ({c / n:.0%})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", type=int, nargs="+", default=[16, 64], choices=[16, 32, 64, 128, 256, 512, 1024])
    ap.add_argument("--only", nargs="*", default=[], help="path prefixes to build, e.g. block/ item/")
    ap.add_argument("--area", help="build only one work area from data/assignments.json, e.g. block_stone")
    ap.add_argument("--groups", nargs="+", help="full build of only these version groups, e.g. 1.20.2+ 1.16")
    ap.add_argument("--jobs", type=int, default=mp.cpu_count())
    ap.add_argument("--preview", nargs="*", help="contact sheet of these prefixes (default: all)")
    ap.add_argument("--no-zip", action="store_true")
    ap.add_argument("--clean", action="store_true", help="delete dist/<res>x before building")
    args = ap.parse_args()

    for mod, err in LOAD_ERRORS:
        print(f"!! failed to import {mod}:\n{err}", file=sys.stderr)

    full = not (args.only or args.area)
    overlays, skipped = {}, []
    if full:
        targets = []
        for g in GROUPS:
            if args.groups and g.gid not in args.groups:
                continue
            t, o, s = group_targets(g)
            targets += t
            overlays[f"core-{g.gid}"] = o
            skipped += [(f"mc{g.gid}", p, why) for p, why in s]
        if not args.groups:
            targets += addon_targets()
    else:
        paths = sorted(p for p in TEXTURES if "@" not in p and "#" not in p
                       and (not args.only or p.startswith(tuple(args.only))))
        if args.area:
            assign = json.loads((ROOT / "data" / "assignments.json").read_text())
            paths = [p for p in paths if assign.get(p) == args.area]
        targets = [Target(MAIN_PACK if TEXTURES[p].pack == "core" else TEXTURES[p].pack, p, p,
                          meta=VANILLA_INDEX.get(p, {}).get("mcmeta", {})) for p in paths]
    keys = sorted({t.key for t in targets})
    packs = sorted({t.pack for t in targets} | {MAIN_PACK})
    failures = []
    for res in args.res:
        if args.clean and (DIST / f"{res}x").exists():
            shutil.rmtree(DIST / f"{res}x")
        (DIST / f"{res}x" / "_cache").mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        infos = {}
        with mp.get_context("fork").Pool(args.jobs) as pool:
            for key, info, err in pool.imap_unordered(render, [(k, res) for k in keys], chunksize=2):
                if err:
                    failures.append((res, key, err))
                else:
                    infos[key] = info
        assemble(res, targets, infos)
        finish_packs(res, packs, overlays)
        print(f"{res}x: {len(keys)} renders -> {len(targets)} files in {len(packs)} packs, {time.time() - t0:.1f}s")
        if full and not args.no_zip:
            for pack in packs:
                print(f"  -> {zip_pack(res, pack)}")

    covered = sum(1 for p in VANILLA_INDEX if p in TEXTURES)
    print(f"coverage: {covered}/{len(VANILLA_INDEX)} vanilla {VANILLA} textures ({covered / len(VANILLA_INDEX):.1%})")
    if full:
        report_versions(targets)
        (DIST / "skipped.txt").write_text("\n".join(f"{g}  {p}  ({why})" for g, p, why in skipped))
    for res, key, err in failures:
        print(f"!! {res}x {key}:\n{err}", file=sys.stderr)
    if args.preview is not None:
        preview(args.preview or [""], only=[t.path for t in targets if t.pack == MAIN_PACK and not t.sub]
                if args.area else None, tag=args.area or "all")
    return 1 if failures or LOAD_ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
