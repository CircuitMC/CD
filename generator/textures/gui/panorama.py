"""Title-screen panorama: a small numpy voxel raycaster over a procedural blocky landscape,
textured with the pack's own block generators (grass, dirt, stone, sand, water, logs, leaves, snow).

The scene is a heightfield of 1-block columns plus an optional floating leaf canopy per column.
Rays are traced with a 2D DDA over the column grid; each column segment is tested against the
ground interval [-inf, top] and the canopy interval [c0, c1]. Every cube face looks into the same
3D scene, so the six faces join seamlessly.
"""
import functools
import math

import numpy as np

from ...engine import Ctx, Tex
from ...registry import TEXTURES

N = 384            # world size in columns (centred on the camera)
WATER = 14         # sea level
SNOW = 52          # snow line
DMAX = 190.0       # draw distance in blocks
CLOUD_Y = 92.0

GRASS_TINT = np.array([0.50, 0.75, 0.34], np.float32)
OAK_TINT = np.array([0.38, 0.66, 0.24], np.float32)
BIRCH_TINT = np.array([0.52, 0.68, 0.34], np.float32)
WATER_TINT = np.array([0.25, 0.46, 0.89], np.float32)

SUN = np.array([0.55, 0.42, -0.72], np.float32)
SUN /= np.linalg.norm(SUN)


# ----------------------------------------------------------------- block textures
def _tex(name):
    spec = TEXTURES[f"block/{name}"]
    frames = spec.frames or 1
    ctx = Ctx(f"block/{name}", 16, 16, 1, frame=0, frames=frames)
    out = spec.fn(ctx)
    if isinstance(out, list):
        out = out[0]
    return np.clip(np.asarray(out.color, np.float32), 0, 1), np.clip(np.asarray(out.alpha, np.float32), 0, 1)


def _safe(name, fallback):
    try:
        return _tex(name)
    except Exception:
        return np.broadcast_to(np.asarray(fallback, np.float32), (16, 16, 3)).copy(), np.ones((16, 16), np.float32)


# material ids
(GRASS_TOP, GRASS_SIDE, DIRT, STONE, SAND, WATER_M, OAK_LOG, OAK_TOP, OAK_LEAF, BIRCH_LOG, BIRCH_LEAF,
 SNOW_M, FLOWER_TOP, GRAVEL) = range(14)


@functools.lru_cache(maxsize=1)
def textures():
    gt, _ = _safe("grass_block_top", (0.6, 0.6, 0.6))
    gs, _ = _safe("grass_block_side", (0.5, 0.36, 0.24))
    ov, ova = _safe("grass_block_side_overlay", (0.6, 0.6, 0.6))
    dirt, _ = _safe("dirt", (0.5, 0.36, 0.24))
    side = gs * (1 - ova[..., None]) + ov * GRASS_TINT * ova[..., None]
    stone, _ = _safe("stone", (0.5, 0.5, 0.5))
    sand, _ = _safe("sand", (0.85, 0.8, 0.6))
    water, _ = _safe("water_still", (0.7, 0.7, 0.7))
    oak, _ = _safe("oak_log", (0.4, 0.3, 0.2))
    oak_top, _ = _safe("oak_log_top", (0.6, 0.5, 0.3))
    oleaf, _ = _safe("oak_leaves", (0.6, 0.6, 0.6))
    birch, _ = _safe("birch_log", (0.85, 0.85, 0.8))
    bleaf, _ = _safe("birch_leaves", (0.6, 0.6, 0.6))
    snow, _ = _safe("snow", (0.95, 0.97, 1.0))
    gravel, _ = _safe("gravel", (0.55, 0.53, 0.52))
    flower = gt * GRASS_TINT
    for name, (x, y) in (("poppy", (3, 4)), ("dandelion", (10, 9)), ("poppy", (12, 2)), ("dandelion", (5, 12))):
        pc, pa = _safe(name, (0.9, 0.2, 0.2))
        mean = (pc * pa[..., None]).sum((0, 1)) / max(1e-6, pa.sum())
        flower[y:y + 2, x:x + 2] = mean * 1.15
    gray = lambda t, tint: np.clip(t * tint, 0, 1)
    T = np.stack([gray(gt, GRASS_TINT), side, dirt, stone, sand, gray(water, WATER_TINT), oak, oak_top,
                  gray(oleaf, OAK_TINT), birch, gray(bleaf, BIRCH_TINT), snow, flower, gravel]).astype(np.float32)
    return T, T.mean((1, 2))


# ----------------------------------------------------------------- terrain
def _value_noise(rng, n, cell):
    g = max(2, n // cell)
    grid = rng.random((g + 1, g + 1)).astype(np.float32)
    grid[-1, :] = grid[0, :]
    grid[:, -1] = grid[:, 0]
    t = np.arange(n, dtype=np.float32) / n * g
    i = np.floor(t).astype(int)
    f = t - i
    f = f * f * (3 - 2 * f)
    a = grid[i][:, i]
    b = grid[i][:, i + 1]
    c = grid[i + 1][:, i]
    d = grid[i + 1][:, i + 1]
    fx, fy = f[None, :], f[:, None]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


@functools.lru_cache(maxsize=1)
def world():
    rng = np.random.default_rng(20261101)
    n = sum(_value_noise(rng, N, c) * a for c, a in ((96, 1.0), (48, 0.5), (24, 0.25), (12, 0.12), (6, 0.06)))
    n /= 1.93
    z, x = np.mgrid[0:N, 0:N].astype(np.float32) - N / 2
    r = np.hypot(x, z)
    h = 18.5 + (n - 0.5) * 36
    # distant mountain ring with ridges
    ridge = 1 - np.abs(_value_noise(rng, N, 40) * 2 - 1)
    ring = np.clip((r - 85) / 60, 0, 1)
    h += ring ** 1.3 * (14 + ridge * 44)
    # a winding river and a lake in front of the camera (face 0 looks toward -z)
    river = np.abs(x - 26 * np.sin(z / 37.0) - 30) - 3.5
    h = np.where(river < 4, np.minimum(h, WATER - 2 + np.clip(river, 0, 4) * 1.5), h)
    lake = np.hypot(x + 6, z + 34) - 15
    h = np.where(lake < 6, np.minimum(h, WATER - 3 + np.clip(lake, 0, 6) * 1.2), h)
    # keep the camera spot grassy and a little raised
    h = np.where(r < 6, np.maximum(h, WATER + 4), h)
    hg = np.round(h).astype(np.int32)
    top = np.maximum(hg, WATER)
    mat_top = np.full((N, N), GRASS_TOP, np.int32)
    mat_top[hg <= WATER + 1] = SAND
    mat_top[hg < WATER] = WATER_M
    steep = np.maximum.reduce([np.abs(np.roll(hg, k, a) - hg) for k in (1, -1) for a in (0, 1)])
    mat_top[(steep >= 3) & (hg > WATER + 1)] = STONE
    mat_top[hg >= SNOW - (ridge * 6).astype(int)] = SNOW_M
    fl = rng.random((N, N))
    mat_top[(mat_top == GRASS_TOP) & (fl < 0.06)] = FLOWER_TOP
    mat_top[(mat_top == SAND) & (fl > 0.97)] = GRAVEL
    # trees: trunk extends the ground column; canopy is a floating leaf interval
    trunk = top.copy()
    log = np.full((N, N), -1, np.int32)
    c0 = np.full((N, N), 1 << 20, np.int32)
    c1 = np.full((N, N), -(1 << 20), np.int32)
    leaf = np.full((N, N), OAK_LEAF, np.int32)
    trng = np.random.default_rng(7)
    for _ in range(900):
        tx, tz = trng.integers(4, N - 4, 2)
        rr = math.hypot(tx - N / 2, tz - N / 2)
        if rr < 14 or rr > 120 or mat_top[tz, tx] not in (GRASS_TOP, FLOWER_TOP) or steep[tz, tx] > 1:
            continue
        if trng.random() > 0.55 - rr / 400:
            continue
        birch = trng.random() < 0.35
        th = int(trng.integers(4, 7))
        base = hg[tz, tx]
        trunk[tz, tx] = base + th
        log[tz, tx] = BIRCH_LOG if birch else OAK_LOG
        for dz in range(-2, 3):
            for dx in range(-2, 3):
                if abs(dx) == 2 and abs(dz) == 2:
                    continue
                lo = base + th - 2 if max(abs(dx), abs(dz)) == 2 else base + th - 3
                hi = base + th + (1 if max(abs(dx), abs(dz)) <= 1 else 0)
                zz, xx = tz + dz, tx + dx
                c0[zz, xx] = min(c0[zz, xx], lo)
                c1[zz, xx] = max(c1[zz, xx], hi)
                leaf[zz, xx] = BIRCH_LEAF if birch else OAK_LEAF
    return dict(hg=hg, top=top, trunk=trunk, log=log, c0=c0, c1=c1, leaf=leaf, mat_top=mat_top,
                hmax=int(max(trunk.max(), c1.max())) + 1)


# ----------------------------------------------------------------- tracing
def trace(o, d):
    """o: (3,) camera, d: (M, 3) unit directions -> (t, material, face, hitpoint) arrays."""
    W = world()
    M = len(d)
    dx, dy, dz = d[:, 0], d[:, 1], d[:, 2]
    off = N / 2
    px, pz = o[0] + off, o[2] + off
    ix = np.full(M, int(math.floor(px)))
    iz = np.full(M, int(math.floor(pz)))
    stepx = np.where(dx > 0, 1, -1)
    stepz = np.where(dz > 0, 1, -1)
    with np.errstate(divide="ignore"):
        tdx = np.where(dx != 0, 1 / np.abs(dx), np.inf)
        tdz = np.where(dz != 0, 1 / np.abs(dz), np.inf)
    tmx = np.where(dx > 0, (ix + 1 - px) * tdx, (px - ix) * tdx)
    tmz = np.where(dz > 0, (iz + 1 - pz) * tdz, (pz - iz) * tdz)
    t_in = np.zeros(M, np.float32)
    axis = np.zeros(M, np.int8)  # 0 entered via x boundary, 1 via z
    t_hit = np.full(M, np.inf, np.float32)
    face = np.zeros(M, np.int8)  # 0 top, 1 side-x, 2 side-z, 3 bottom
    kind = np.zeros(M, np.int8)  # 1 ground, 2 canopy
    cell = np.zeros((M, 2), np.int32)
    active = np.arange(M)
    hmax = W["hmax"]
    for _ in range(int(DMAX * 1.6)):
        if active.size == 0:
            break
        a = active
        cx, cz = ix[a], iz[a]
        inside = (cx >= 0) & (cx < N) & (cz >= 0) & (cz < N)
        cxc, czc = np.clip(cx, 0, N - 1), np.clip(cz, 0, N - 1)
        t_out = np.minimum(tmx[a], tmz[a])
        y_in = o[1] + dy[a] * t_in[a]
        y_out = o[1] + dy[a] * t_out
        top = np.where(inside, W["trunk"][czc, cxc], -1000)
        c0 = np.where(inside, W["c0"][czc, cxc], 1 << 20)
        c1 = np.where(inside, W["c1"][czc, cxc], -(1 << 20))
        best = np.full(a.size, np.inf, np.float32)
        bface = np.zeros(a.size, np.int8)
        bkind = np.zeros(a.size, np.int8)
        side_face = np.where(axis[a] == 0, 1, 2).astype(np.int8)
        # ground
        g_side = y_in <= top
        g_top = (~g_side) & (y_out <= top)
        with np.errstate(divide="ignore", invalid="ignore"):
            tt = (top - o[1]) / dy[a]
        cand = np.where(g_side, t_in[a], np.where(g_top, tt, np.inf))
        upd = cand < best
        best = np.where(upd, cand, best)
        bface = np.where(upd, np.where(g_side, side_face, 0), bface)
        bkind = np.where(upd, 1, bkind)
        # canopy
        has = c1 >= c0
        l_side = has & (y_in >= c0) & (y_in <= c1)
        l_top = has & (y_in > c1) & (y_out <= c1)
        l_bot = has & (y_in < c0) & (y_out >= c0)
        with np.errstate(divide="ignore", invalid="ignore"):
            tt1 = (c1 - o[1]) / dy[a]
            tt0 = (c0 - o[1]) / dy[a]
        cand = np.where(l_side, t_in[a], np.where(l_top, tt1, np.where(l_bot, tt0, np.inf)))
        upd = cand < best
        best = np.where(upd, cand, best)
        bface = np.where(upd, np.where(l_side, side_face, np.where(l_top, 0, 3)), bface)
        bkind = np.where(upd, 2, bkind)
        hit = np.isfinite(best)
        hi = a[hit]
        t_hit[hi] = best[hit]
        face[hi] = bface[hit]
        kind[hi] = bkind[hit]
        cell[hi, 0] = cx[hit]
        cell[hi, 1] = cz[hit]
        # advance the rest
        stepx_now = tmx[a] < tmz[a]
        t_in[a] = t_out
        ix[a] = np.where(stepx_now, ix[a] + stepx[a], ix[a])
        iz[a] = np.where(stepx_now, iz[a], iz[a] + stepz[a])
        tmx[a] = np.where(stepx_now, tmx[a] + tdx[a], tmx[a])
        tmz[a] = np.where(stepx_now, tmz[a], tmz[a] + tdz[a])
        axis[a] = np.where(stepx_now, 0, 1)
        gone = (~hit) & ((t_out > DMAX) | ((y_out > hmax) & (dy[a] >= 0)))
        active = a[~hit & ~gone]
    p = o[None, :] + d * np.where(np.isfinite(t_hit), t_hit, 0)[:, None]
    return t_hit, kind, face, cell, p


def shade(o, d):
    W = world()
    T, avg = textures()
    t, kind, face, cell, p = trace(o, d)
    M = len(d)
    hitm = np.isfinite(t)
    cx, cz = np.clip(cell[:, 0], 0, N - 1), np.clip(cell[:, 1], 0, N - 1)
    y = p[:, 1]
    fy = np.floor(y - 1e-4)
    # materials
    mat = np.full(M, STONE, np.int32)
    hg = W["hg"][cz, cx]
    top_m = W["mat_top"][cz, cx]
    logm = W["log"][cz, cx]
    ground = kind == 1
    is_log = ground & (logm >= 0) & (y > hg + 1e-3)
    on_top = face == 0
    mat = np.where(ground & on_top, top_m, mat)
    side_g = ground & ~on_top
    below_top = fy < W["top"][cz, cx] - 1
    side_mat = np.where(top_m == WATER_M, np.where(y > hg, WATER_M, SAND),
                        np.where(np.isin(top_m, (GRASS_TOP, FLOWER_TOP)),
                                 np.where(below_top, np.where(fy < hg - 4, STONE, DIRT), GRASS_SIDE),
                                 np.where(top_m == SNOW_M, np.where(fy >= SNOW - 4, SNOW_M, STONE), np.where(top_m == GRAVEL, GRAVEL, top_m))))
    mat = np.where(side_g, side_mat, mat)
    mat = np.where(is_log, np.where(on_top, OAK_TOP, logm), mat)
    mat = np.where(kind == 2, W["leaf"][cz, cx], mat)
    # texture coordinates
    off = N / 2
    wx, wz = p[:, 0] + off, p[:, 2] + off
    fr = lambda v: v - np.floor(v)
    u = np.where(face == 1, fr(wz), fr(wx))
    v = np.where((face == 0) | (face == 3), fr(wz), 1 - fr(y - 1e-4))
    tu = np.clip((u * 16).astype(int), 0, 15)
    tv = np.clip((v * 16).astype(int), 0, 15)
    col = T[mat, tv, tu]
    lod = np.clip((t - 18) / 70, 0, 1)[:, None]
    col = col * (1 - lod) + avg[mat] * lod
    # face light: top brightest, sun-facing sides brighter
    nrm = np.zeros((M, 3), np.float32)
    nrm[face == 0, 1] = 1
    nrm[face == 3, 1] = -1
    nrm[face == 1, 0] = -np.sign(d[face == 1, 0])
    nrm[face == 2, 2] = -np.sign(d[face == 2, 2])
    lam = np.clip(nrm @ SUN, 0, 1)
    base = np.select([face == 0, face == 3, face == 1], [1.0, 0.5, 0.78], 0.66)
    col = col * (base * 0.82 + lam * 0.28)[:, None]
    # water: a bit glossy toward the horizon
    col = np.where((mat == WATER_M)[:, None], col * 0.85 + sky(d) * 0.25, col)
    # sky, clouds, fog
    sk = sky(d)
    fog = np.clip(1 - np.exp(-(np.clip(np.where(hitm, t, DMAX) - 40, 0, None) / (DMAX * 0.75)) ** 2), 0, 1)
    fog = np.where(hitm, np.maximum(fog, np.clip((t - DMAX * 0.9) / (DMAX * 0.1), 0, 1)), 1)
    out = np.where(hitm[:, None], col * (1 - fog[:, None]) + horizon(d) * fog[:, None], sk)
    return np.clip(out, 0, 1)


def horizon(d):
    return np.broadcast_to(np.array([0.70, 0.80, 0.95], np.float32), d.shape)


def sky(d):
    e = np.clip(d[:, 1], -1, 1)
    t = np.clip(e * 1.6, 0, 1)[:, None]
    col = np.array([0.74, 0.84, 0.96], np.float32) * (1 - t) + np.array([0.30, 0.52, 0.88], np.float32) * t
    # blocky square sun
    s = d @ SUN
    e1 = np.cross(SUN, np.array([0, 1, 0], np.float32))
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(e1, SUN)
    sun = (s > 0) & (np.maximum(np.abs(d @ e1), np.abs(d @ e2)) < 0.055)
    glow = np.clip((s - 0.95) / 0.05, 0, 1) ** 2
    col = col + glow[:, None] * np.array([0.25, 0.22, 0.12], np.float32)
    col = np.where(sun[:, None], np.array([1.0, 0.97, 0.82], np.float32), col)
    # cloud layer on a plane, 12x12-block cells
    up = d[:, 1] > 0.02
    with np.errstate(divide="ignore", invalid="ignore"):
        tc = np.where(up, CLOUD_Y / d[:, 1], np.inf)
    cxp = np.floor(d[:, 0] * tc / 12).astype(np.int64)
    czp = np.floor(d[:, 2] * tc / 12).astype(np.int64)
    cloud = up & (clouds()[czp % 256, cxp % 256] > 0.6) & (tc < 900)
    k = np.clip(1 - tc / 900, 0, 1) * 0.9
    col = np.where(cloud[:, None], col * (1 - k[:, None]) + np.array([1, 1, 1], np.float32) * k[:, None], col)
    return col


@functools.lru_cache(maxsize=1)
def clouds():
    rng = np.random.default_rng(99)
    return _value_noise(rng, 256, 6) * 0.65 + _value_noise(rng, 256, 3) * 0.35


def camera():
    W = world()
    c = N // 2
    return np.array([0.5, W["top"][c - 3:c + 4, c - 3:c + 4].max() + 9.5, 0.5], np.float32)


def face_dirs(face, res):
    v, u = np.mgrid[0:res, 0:res].astype(np.float32)
    u = (u + 0.5) / res * 2 - 1
    v = (v + 0.5) / res * 2 - 1
    if face < 4:
        a = face * math.pi / 2
        f = np.array([math.sin(a), 0, -math.cos(a)], np.float32)
        r = np.array([math.cos(a), 0, math.sin(a)], np.float32)
        d = f[None, None] + u[..., None] * r[None, None] - v[..., None] * np.array([0, 1, 0], np.float32)
    elif face == 4:  # up: bottom edge joins face 0's top edge
        d = np.stack([u, np.ones_like(u), -v], -1)
    else:            # down: top edge joins face 0's bottom edge
        d = np.stack([u, -np.ones_like(u), v], -1)
    d = d.reshape(-1, 3)
    return d / np.linalg.norm(d, axis=1, keepdims=True)


def render_face(ctx, face):
    res = min(ctx.W, 1024)
    col = shade(camera(), face_dirs(face, res)).reshape(res, res, 3)
    if ctx.W != res:
        k = ctx.W // res
        col = np.repeat(np.repeat(col, k, 0), k, 1)
    return Tex(ctx, col.astype(np.float32), wrap=False, grain=0)
