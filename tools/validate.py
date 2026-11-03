#!/usr/bin/env python3
"""Structural checks on built packs (run after a full build).

    .venv/bin/python tools/validate.py            # checks every dist/<res>x/<pack>
    .venv/bin/python tools/validate.py --res 16

Checks: pack.mcmeta + overlays, every PNG decodes, image sizes are integer
multiples of the vanilla layout of the versions the pack serves, animation
strips, .mcmeta / model / blockstate JSON, cutout alpha, grayscale tinted
textures, PBR maps matching their base texture, CTM tiles.
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from build import ALL_VERSIONS, DIST, INDEXES, PACKS, frame_layout  # noqa: E402

TINTED = re.compile(r"^block/(grass_block_top|grass_block_side_overlay|short_grass|tall_grass_(top|bottom)|fern|"
                    r"large_fern_(top|bottom)|vine|sugar_cane|lily_pad|(oak|spruce|birch|jungle|acacia|dark_oak|"
                    r"mangrove)_leaves|water_(still|flow|overlay)|redstone_dust_(dot|line0|line1)|"
                    r"(attached_)?(melon|pumpkin)_stem)$")


class Report:
    def __init__(self):
        self.issues = defaultdict(list)
        self.checked = 0

    def add(self, kind, msg):
        self.issues[kind].append(msg)


def expected_layouts(pack, path):
    """All (frame_w, frame_h) layouts vanilla used for this path in the versions the pack serves."""
    g = PACKS[pack]["group"]
    versions = g.versions if g else ALL_VERSIONS
    out = set()
    for v in versions:
        e = INDEXES.get(v, {}).get(path)
        if e:
            out.add(frame_layout(e)[:2])
    return out


def check_png(rep, pack, root, f, res):
    rel = f.relative_to(root).as_posix()
    m = re.match(r"(?:overlay_\d+_\d+/)?assets/minecraft/textures/(.+)\.png$", rel)
    try:
        img = Image.open(f)
        img.load()
    except Exception as e:  # noqa: BLE001
        rep.add("unreadable", f"{rel}: {e}")
        return
    rep.checked += 1
    if not m:
        return
    path = m.group(1)
    if path.endswith(("_n", "_s")):
        base = f.with_name(f.name[:-6] + ".png")
        if base.exists() and Image.open(base).size != img.size:
            rep.add("pbr size", rel)
        return
    meta_f = f.with_name(f.name + ".mcmeta")
    meta = {}
    if meta_f.exists():
        try:
            meta = json.loads(meta_f.read_text())
        except ValueError as e:
            rep.add("bad mcmeta", f"{rel}: {e}")
    W, H = img.size
    anim = meta.get("animation")
    fw = anim.get("width", W) if anim else W
    fh = anim.get("height", fw) if anim else H
    if anim and H % fh:
        rep.add("animation strip", f"{rel}: {W}x{H} not a multiple of frame {fw}x{fh}")
    layouts = expected_layouts(pack, path)
    # The jar only holds 1x1 placeholders for the title panorama (real faces ship as assets).
    if layouts and not path.startswith("gui/title/background/"):
        ok = any(fw % lw == 0 and fh % lh == 0 and fw // lw == fh // lh and (fw // lw) & (fw // lw - 1) == 0
                 for lw, lh in layouts)
        if not ok:
            rep.add("size", f"{rel}: frame {fw}x{fh}, vanilla {sorted(layouts)}")
    a = np.asarray(img.convert("RGBA"))
    mip = meta.get("texture", {}).get("mipmap_strategy", "")
    if "cutout" in mip and not np.isin(a[..., 3], (0, 255)).all():
        rep.add("cutout alpha", rel)
    if TINTED.match(path):
        solid = a[..., 3] > 0
        rgb = a[..., :3][solid].astype(int)
        if len(rgb) and (np.abs(rgb[:, 0] - rgb[:, 1]).max() > 2 or np.abs(rgb[:, 1] - rgb[:, 2]).max() > 2):
            rep.add("tint not grayscale", rel)


def check_json(rep, root):
    for f in root.rglob("*.json"):
        try:
            data = json.loads(f.read_text())
        except ValueError as e:
            rep.add("bad json", f"{f.relative_to(root)}: {e}")
            continue
        if "/models/" in f.as_posix():
            for ref in data.get("textures", {}).values():
                if ref.startswith("#"):
                    continue
                ns, _, p = ref.partition(":") if ":" in ref else ("minecraft", "", ref)
                if ns != "minecraft" and not (root / "assets" / ns / "textures" / f"{p}.png").exists():
                    rep.add("missing model texture", f"{f.relative_to(root)} -> {ref}")
        if "/blockstates/" in f.as_posix():
            for part in data.get("multipart", []):
                model = part["apply"]["model"]
                ns, _, p = model.partition(":")
                if ns != "minecraft" and not (root / "assets" / ns / "models" / f"{p}.json").exists():
                    rep.add("missing model", f"{f.relative_to(root)} -> {model}")


def check_ctm(rep, root):
    for f in root.rglob("*.properties"):
        props = dict(l.split("=", 1) for l in f.read_text().splitlines() if "=" in l and not l.startswith("#"))
        tiles = props.get("tiles", "")
        m = re.match(r"(\d+)-(\d+)$", tiles)
        if m:
            for i in range(int(m.group(1)), int(m.group(2)) + 1):
                if not (f.parent / f"{i}.png").exists():
                    rep.add("ctm tile", f"{f.relative_to(root)}: {i}.png")


def check_pack(rep, root):
    try:
        meta = json.loads((root / "pack.mcmeta").read_text())
    except Exception as e:  # noqa: BLE001
        rep.add("pack.mcmeta", f"{root.name}: {e}")
        return
    for entry in meta.get("overlays", {}).get("entries", []):
        if not (root / entry["directory"]).is_dir():
            rep.add("overlay", f"{root.name}: missing {entry['directory']}")
    if not (root / "pack.png").exists():
        rep.add("pack.png", root.name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", type=int, nargs="*")
    args = ap.parse_args()
    dist = DIST
    bad = 0
    for res_dir in sorted(d for d in dist.glob("*x") if d.name[:-1].isdigit()):
        res = int(res_dir.name[:-1])
        if args.res and res not in args.res:
            continue
        for pack, info in PACKS.items():
            root = res_dir / info["dir"]
            if not root.is_dir():
                continue
            rep = Report()
            check_pack(rep, root)
            for f in root.rglob("*.png"):
                check_png(rep, pack, root, f, res)
            check_json(rep, root)
            check_ctm(rep, root)
            n = sum(len(v) for v in rep.issues.values())
            bad += n
            print(f"{res_dir.name}/{info['dir']}: {rep.checked} images, {n} issues")
            for kind, items in sorted(rep.issues.items()):
                print(f"  {kind}: {len(items)}")
                for msg in items[:8]:
                    print(f"    {msg}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
