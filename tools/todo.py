#!/usr/bin/env python3
"""List vanilla paths of a work area that have no generator yet.

    .venv/bin/python tools/todo.py block_stone          # missing paths with size/frames
    .venv/bin/python tools/todo.py block_stone --all    # every path of the area
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build  # noqa: E402  (loads generators)
from generator.registry import TEXTURES  # noqa: E402

area = sys.argv[1]
assign = json.loads((build.ROOT / "data" / "assignments.json").read_text())
paths = [p for p, a in assign.items() if a == area]
done = [p for p in paths if p in TEXTURES]
print(f"# {area}: {len(done)}/{len(paths)} done")
for p in paths:
    if p in TEXTURES and "--all" not in sys.argv:
        continue
    v = build.VANILLA_INDEX[p]
    meta = v.get("mcmeta", {})
    extra = f"  meta={json.dumps(meta)}" if meta else ""
    print(f"{p}  {v['w']}x{v['h']}{extra}")
