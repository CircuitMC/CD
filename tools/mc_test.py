#!/usr/bin/env python3
"""Smoke-test a built pack in a real (offline) Minecraft client.

    .venv/bin/python tools/mc_test.py 1.21.1 dist/CircuitMC-Default-0.3.0-16x.zip [--seconds 90]

Downloads the client + libraries into a cache folder, launches it in offline
mode with the pack enabled, waits, takes a screenshot of the display and
scans the game log for resource-loading problems. Needs a display (WSLg/X11).
The vanilla client is only *run*; its assets are never opened by this script.
"""
import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import zipfile
from pathlib import Path

MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
ADOPTIUM = "https://api.adoptium.net/v3/binary/latest/{v}/ga/linux/x64/jdk/hotspot/normal/eclipse"
SYSTEM_JVMS = {8: "/usr/lib/jvm/java-8-openjdk-amd64", 17: "/usr/lib/jvm/java-17-openjdk-amd64",
               21: "/usr/lib/jvm/java-21-openjdk-amd64"}
LOG_PATTERNS = re.compile(
    r"(Failed to (load|parse|stitch)|Unable to (load|parse)|Missing (texture|model)|Invalid (pack|frame)|"
    r"Couldn't (load|parse)|not a multiple of|Exception|incompatible|Using missing texture)", re.I)


def fetch(url, dest, sha1=None):
    dest = Path(dest)
    if dest.exists() and (not sha1 or hashlib.sha1(dest.read_bytes()).hexdigest() == sha1):
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "cmc-test/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)
    return dest


def rules_ok(rules):
    if not rules:
        return True
    allow = False
    for r in rules:
        os_rule = r.get("os", {})
        if os_rule and os_rule.get("name") not in (None, "linux"):
            continue
        if "features" in r:
            continue
        allow = r["action"] == "allow"
    return allow


def java_for(major, cache):
    if major in SYSTEM_JVMS and Path(SYSTEM_JVMS[major]).exists():
        return Path(SYSTEM_JVMS[major]) / "bin" / "java"
    home = cache / f"jdk-{major}"
    if not home.exists():
        tgz = fetch(ADOPTIUM.format(v=major), cache / f"jdk-{major}.tar.gz")
        with tarfile.open(tgz) as t:
            t.extractall(cache / f"jdk-{major}-tmp")
        inner = next((cache / f"jdk-{major}-tmp").iterdir())
        inner.rename(home)
        shutil.rmtree(cache / f"jdk-{major}-tmp")
    return home / "bin" / "java"


def prepare(version, cache):
    manifest = json.loads(urllib.request.urlopen(MANIFEST, timeout=60).read())
    url = next(v["url"] for v in manifest["versions"] if v["id"] == version)
    meta = json.loads(fetch(url, cache / "versions" / f"{version}.json").read_text())
    jar = fetch(meta["downloads"]["client"]["url"], cache / "versions" / f"{version}.jar",
                meta["downloads"]["client"]["sha1"])
    cp, natives = [jar], cache / "natives" / version
    natives.mkdir(parents=True, exist_ok=True)
    for lib in meta["libraries"]:
        if not rules_ok(lib.get("rules")):
            continue
        dl = lib.get("downloads", {})
        art = dl.get("artifact")
        if art:
            cp.append(fetch(art["url"], cache / "libraries" / art["path"], art.get("sha1")))
        cls = (lib.get("natives") or {}).get("linux")
        if cls and cls.replace("${arch}", "64") in dl.get("classifiers", {}):
            n = dl["classifiers"][cls.replace("${arch}", "64")]
            f = fetch(n["url"], cache / "libraries" / n["path"], n.get("sha1"))
            with zipfile.ZipFile(f) as z:
                for name in z.namelist():
                    if name.endswith(".so"):
                        (natives / Path(name).name).write_bytes(z.read(name))
    idx = meta["assetIndex"]
    index = json.loads(fetch(idx["url"], cache / "assets" / "indexes" / f"{idx['id']}.json",
                             idx.get("sha1")).read_text())
    # Non-sound assets (language files, fonts, title panorama): small, and the
    # game logs noisy errors without them. Sounds/music are skipped.
    jobs = []
    for name, obj in index["objects"].items():
        if "sounds" in name or name.startswith(("music", "records")):
            continue
        h = obj["hash"]
        jobs.append((f"https://resources.download.minecraft.net/{h[:2]}/{h}",
                     cache / "assets" / "objects" / h[:2] / h, h))
        if index.get("map_to_resources") or index.get("virtual"):
            jobs.append((jobs[-1][0], cache / "assets" / "virtual" / idx["id"] / name, h))
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(16) as pool:
        list(pool.map(lambda j: fetch(*j), jobs))
    return meta, cp, natives


LEGACY_FORMATS = {"1.6": 1, "1.7": 1, "1.8": 1, "1.9": 2, "1.10": 2, "1.11": 3, "1.12": 3}


def client_format(vid):
    if vid.startswith("1.") and int(vid.split(".")[1]) < 13:
        return LEGACY_FORMATS[".".join(vid.split(".")[:2])]
    data = Path(__file__).resolve().parent.parent / "data" / f"vanilla-{vid}.json"
    pv = json.loads(data.read_text()).get("pack_version") if data.exists() else None
    if isinstance(pv, dict):
        return pv.get("resource", pv.get("resource_major"))
    return pv


def pack_compatible(zip_path, fmt):
    with zipfile.ZipFile(zip_path) as z:
        meta = json.loads(z.read("pack.mcmeta"))["pack"]
    lo, hi = meta.get("supported_formats", [meta["pack_format"]] * 2)
    if fmt is None:
        return True
    if fmt >= 18:  # 1.20.2+ read supported_formats / min..max
        return lo <= fmt <= hi
    return meta["pack_format"] == fmt


def options_lines(version_meta, zips):
    """Enable the packs; pre-confirm the "made for another version" prompt only for
    packs the client really considers incompatible (26.x drops compatible ones listed there)."""
    vid = version_meta["id"]
    legacy = vid.startswith("1.") and int(vid.split(".")[1]) < 13
    fmt = client_format(vid)
    ids = [Path(z).name if legacy else f"file/{Path(z).name}" for z in zips]
    lst = ",".join(f'"{i}"' for i in ids)
    bad = ",".join(f'"{i}"' for i, z in zip(ids, zips) if not pack_compatible(z, fmt))
    packs = f"[{lst}]" if legacy else f'["vanilla",{lst}]'
    return f"resourcePacks:{packs}\nincompatibleResourcePacks:[{bad}]\n"


def press_f2(game):
    """Ask the game itself for a screenshot (F2 via XTEST); returns the saved file."""
    try:
        from Xlib import X, XK, display
        from Xlib.ext import xtest
        d = display.Display()
        win = find_window(d.screen().root)
        if win is not None:
            win.set_input_focus(X.RevertToParent, X.CurrentTime)
            win.raise_window()
            d.sync()
            time.sleep(1.5)
        key = d.keysym_to_keycode(XK.string_to_keysym("F2"))
        xtest.fake_input(d, X.KeyPress, key)
        d.sync()
        time.sleep(0.15)
        xtest.fake_input(d, X.KeyRelease, key)
        d.sync()
        time.sleep(4)
        shots = sorted((game / "screenshots").glob("*.png"))
        return shots[-1] if shots else None
    except Exception as e:  # noqa: BLE001
        print(f"screenshot failed: {e}")
        return None


def find_window(root):
    stack = [root]
    while stack:
        w = stack.pop()
        try:
            name = w.get_wm_name() or ""
            if "Minecraft" in str(name):
                return w
            stack.extend(w.query_tree().children)
        except Exception:  # noqa: BLE001
            continue
    return None


def substitute(arg, values):
    return re.sub(r"\$\{(\w+)\}", lambda m: values.get(m.group(1), ""), arg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("version")
    ap.add_argument("packs", nargs="+")
    ap.add_argument("--seconds", type=int, default=90)
    ap.add_argument("--cache", default=os.environ.get("CMC_MC_CACHE", str(Path.home() / ".cache" / "cmc-mc")))
    ap.add_argument("--out", default="dist/test")
    args = ap.parse_args()
    cache = Path(args.cache)
    out = Path(args.out) / args.version
    game = out / "game"
    shutil.rmtree(out, ignore_errors=True)
    (game / "resourcepacks").mkdir(parents=True)
    meta, cp, natives = prepare(args.version, cache)
    names = []
    for p in args.packs:
        shutil.copy(p, game / "resourcepacks")
        names.append(Path(p).name)
    opts = options_lines(meta, args.packs)
    (game / "options.txt").write_text(opts + "fullscreen:false\nonboardAccessibility:false\n"
                                      "tutorialStep:none\nskipMultiplayerWarning:true\njoinedFirstServer:true\n")
    values = {
        "auth_player_name": "CircuitTest", "version_name": args.version, "game_directory": str(game.resolve()),
        "assets_root": str((cache / "assets").resolve()), "assets_index_name": meta["assetIndex"]["id"],
        "auth_uuid": "00000000-0000-0000-0000-000000000000", "auth_access_token": "0", "user_type": "legacy",
        "version_type": "release", "natives_directory": str(natives.resolve()), "launcher_name": "cmc-test",
        "launcher_version": "1", "classpath": os.pathsep.join(str(Path(c).resolve()) for c in cp),
        "user_properties": "{}", "clientid": "0", "auth_xuid": "0",
        "game_assets": str((cache / "assets" / ("virtual/" + meta["assetIndex"]["id"]
                                                 if meta["assetIndex"]["id"] in ("legacy", "pre-1.6") else "")).resolve()),
        "auth_session": "0", "game_assets_legacy": "",
    }
    if "arguments" in meta:
        jvm = [substitute(a, values) for a in meta["arguments"]["jvm"] if isinstance(a, str)]
        game_args = [substitute(a, values) for a in meta["arguments"]["game"] if isinstance(a, str)]
    else:
        jvm = [f"-Djava.library.path={values['natives_directory']}", "-cp", values["classpath"]]
        game_args = [substitute(a, values) for a in meta["minecraftArguments"].split()]
    java = java_for(meta.get("javaVersion", {}).get("majorVersion", 8), cache)
    cmd = [str(java), "-Xmx3G", *jvm, meta["mainClass"], *game_args, "--width", "1280", "--height", "720"]
    log = open(out / "stdout.log", "w")
    env = dict(os.environ, __GL_THREADED_OPTIMIZATIONS="0")
    proc = subprocess.Popen(cmd, cwd=game, stdout=log, stderr=subprocess.STDOUT, env=env)
    t0 = time.time()
    while time.time() - t0 < args.seconds and proc.poll() is None:
        time.sleep(2)
    shot = None
    if proc.poll() is None:
        shot = press_f2(game)
        proc.terminate()
        try:
            proc.wait(20)
        except subprocess.TimeoutExpired:
            proc.kill()
    log.close()
    text = (out / "stdout.log").read_text(errors="replace")
    latest = game / "logs" / "latest.log"
    if latest.exists():
        text += latest.read_text(errors="replace")
    hits = [l for l in text.splitlines() if LOG_PATTERNS.search(l)]
    print(f"{args.version}: ran {time.time() - t0:.0f}s, exit={proc.returncode}, log lines={len(text.splitlines())}, "
          f"suspicious={len(hits)}, screenshot={shot}")
    for l in hits[:40]:
        print("  " + l[:220])


if __name__ == "__main__":
    sys.exit(main())
