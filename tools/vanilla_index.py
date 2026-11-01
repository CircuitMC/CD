#!/usr/bin/env python3
"""Index the texture *interface* of a vanilla client version without downloading its art.

    python3 tools/vanilla_index.py 26.3 1.12.2 ...   # writes data/vanilla-<version>.json

Uses HTTP range requests to fetch only:
  * the jar's ZIP central directory (the file name table),
  * version.json (pack format),
  * the first bytes of each PNG, enough to read the IHDR header (width/height),
  * .mcmeta sidecars (animation / nine-slice metadata).
No pixel data is ever downloaded or decoded, so no vanilla artwork is seen.
"""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import struct
import sys
import urllib.request
import zlib

MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"


def get(url, rng=None):
    req = urllib.request.Request(url, headers={"Range": f"bytes={rng}"} if rng else {})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def size_of(url):
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers["Content-Length"])


def central_directory(url):
    total = size_of(url)
    tail = get(url, f"{total - 65558}-{total - 1}")
    eocd = tail.rfind(b"PK\x05\x06")
    count, cd_size, cd_offset = struct.unpack("<HII", tail[eocd + 10:eocd + 20])
    cd = get(url, f"{cd_offset}-{cd_offset + cd_size - 1}")
    entries, pos = {}, 0
    for _ in range(count):
        (method, csize, usize, nlen, xlen, clen, local) = struct.unpack(
            "<10xH8xII HHH8xI", cd[pos:pos + 46])
        name = cd[pos + 46:pos + 46 + nlen].decode()
        entries[name] = (method, csize, local)
        pos += 46 + nlen + xlen + clen
    return entries


def read_small(url, entry):
    method, csize, local = entry
    head = get(url, f"{local}-{local + 29}")
    nlen, xlen = struct.unpack("<HH", head[26:30])
    start = local + 30 + nlen + xlen
    data = get(url, f"{start}-{start + csize - 1}")
    return zlib.decompress(data, -15) if method == 8 else data


def png_size(url, name, entry):
    method, csize, local = entry
    head = get(url, f"{local}-{local + 29 + len(name) + 400}")
    nlen, xlen = struct.unpack("<HH", head[26:30])
    data = head[30 + nlen + xlen:]
    if method == 8:
        data = zlib.decompressobj(-15).decompress(data)
    assert data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR", name
    return struct.unpack(">II", data[16:24])


def main():
    manifest = json.loads(get(MANIFEST))
    for version in sys.argv[1:] or [manifest["latest"]["release"]]:
        index_version(manifest, version)


def index_version(manifest, version):
    meta_url = next(v["url"] for v in manifest["versions"] if v["id"] == version)
    jar = json.loads(get(meta_url))["downloads"]["client"]["url"]
    entries = central_directory(jar)
    info = json.loads(read_small(jar, entries["version.json"])) if "version.json" in entries else {}
    prefix = "assets/minecraft/textures/"
    names = sorted(n for n in entries if n.startswith(prefix) and n.endswith(".png"))

    def describe(name):
        w, h = png_size(jar, name, entries[name])
        item = {"w": w, "h": h}
        meta = entries.get(name + ".mcmeta")
        if meta:
            try:
                item["mcmeta"] = json.loads(read_small(jar, meta))
            except ValueError:
                item["mcmeta"] = {}
        return name[len(prefix):-4], item

    with ThreadPoolExecutor(24) as pool:
        textures = dict(pool.map(describe, names))
    out = Path(__file__).resolve().parent.parent / "data" / f"vanilla-{version}.json"
    out.write_text(json.dumps({"version": version, "pack_version": info.get("pack_version"),
                               "textures": textures}, indent=1, sort_keys=True))
    print(f"{len(textures)} textures -> {out}")


if __name__ == "__main__":
    main()
