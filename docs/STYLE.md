# Style & Generator Guide

How textures are made in this repository. Read this before adding or changing any texture.

## 1. Clean-room rules (non-negotiable)

- **Never** open, download, decode, trace, sample or color-pick vanilla Minecraft images (client jar,
  wiki images, screenshots, third-party packs). Not even "just to compare".
- **Allowed interface data** (functional facts needed for compatibility), all already collected in
  `data/vanilla-26.3.json`: texture paths, image dimensions, and `.mcmeta` metadata (animation,
  nine-slice GUI scaling, mipmap strategy, villager hats).
- **Allowed layout data**: where things must sit for the game to use them correctly, e.g. entity UV box
  positions/sizes, GUI slot coordinates, font glyph grid. This may come from your own knowledge or
  from text documentation/model geometry (e.g. Blockbench / OptiFine CEM model JSON), **never** from
  looking at an image.
- **Allowed references**: real-world materials, general knowledge of what a thing is ("diamond ore is
  cyan gems in stone", "a creeper is green and mottled"), and generic pixel-art technique.
- Design every texture yourself. "Vanilla-like" means *following the same art conventions* (below),
  never reproducing a specific vanilla pixel layout from memory. When in doubt, make it different.

## 2. Art conventions ("vanilla-like")

- 16x is the reference look: pixel art, no anti-aliasing, each texel deliberate.
- Light from the **top-left**. Raised features: light top/left edge, dark bottom/right edge, small
  cast shadow down-right.
- Palettes of 4–7 shades per material, dark → light, mid contrast. Avoid pure black/white
  except for tiny accents. Hue shifts slightly toward warm in highlights and cool in shadows.
- Block textures **tile seamlessly** (all noise/Voronoi helpers wrap automatically).
- Sizes/feature scale: noise features of ~2–8 texels, 1-texel grain. Don't fill 16x16 with pure noise.
- Items/plants/sprites: readable silhouette, 1-texel outline in a darker shade of the local color
  (not pure black), interior highlights top-left.
- Tinted textures are **grayscale** (the game multiplies them by biome/dye color): grass top, grass
  side overlay, short/tall grass, ferns, most leaves, vines, lily pad, sugar cane, water, stems,
  redstone dust, leather armor base layers, potion overlays, spawn egg (if any) etc. Keep their gray
  values around 0.45–0.9.
- Cutout textures (plants, glass, leaves, rails…) must use alpha 0 or 1 only. Translucent ones (stained
  glass, water, ice, slime, honey) may use partial alpha.
- Higher resolutions (64x/256x/1024x) are rendered from the same code: large shapes must match the 16x
  design; more resolution adds detail, not a new design.

## 3. Engine overview

```
generator/engine.py     Ctx (coordinates, noise, Voronoi, shapes, palette), Tex (layers), encode()
generator/materials.py  reusable builders: rock, layered, soil, granular, pebbles, overgrow,
                        masonry, running_bond, bordered_panel, planks, bark, end_grain, stripped,
                        leaves, metal_block, gem_block, blobs, texel_mask, ore, ...
generator/registry.py   @texture / register / static_file
generator/textures/     one package per work area (block/, item/, entity/, gui/, misc/, addons/)
data/assignments.json   which work area owns each vanilla path
```

A generator receives a `Ctx` and returns a `Tex` (or a list of `Tex`, one per animation frame):

```python
from ...engine import Tex, pal
from ...materials import rock
from ...registry import texture, register

STONE = pal("5b5b5e", "68686b", "737376", "7e7e81", "89898c")

@texture("block/andesite")
def andesite(ctx):
    t = rock(ctx, STONE, cell=4, salt="andesite")
    return t
```

### Ctx (all coordinates in texels; 1 texel = `ctx.s` pixels)

| member | meaning |
|---|---|
| `ctx.name, ctx.w, ctx.h, ctx.s` | path, native size in texels, scale (1=16x, 4=64x, 16=256x, 64=1024x) |
| `ctx.x, ctx.y` | float arrays (H, W): texel coordinates of each pixel center |
| `ctx.tx, ctx.ty` | integer texel index of each pixel |
| `ctx.frame, ctx.frames` | animation frame index / count |
| `ctx.pixel_art`, `ctx.smooth_t` | True at 16x; 0→1 blend factor toward painterly at high res |
| `ctx.rng(salt)` | numpy Generator seeded by texture name + salt (resolution independent) |
| `ctx.sub(name)` | same geometry, other seed: reuse another texture's generator |
| `ctx.noise(cell, octaves, persistence, salt, stretch=(sx, sy))` | tileable fBm 0..1 |
| `ctx.lattice_noise(cx, cy, salt)` | single tileable value-noise octave |
| `ctx.texel_noise(salt, soft=True)` | per-texel random (smooth grain above 16x) |
| `ctx.voronoi(n, salt, min_dist)` | dict `id, f1, f2, dx, dy, points` (tileable) |
| `ctx.palette(pal, v)` | map 0..1 to palette (hard steps at 16x, blended at high res) |
| `ctx.quantize(v, levels)` | posterize at 16x |
| `ctx.rect, circle, polygon, segment` | float masks in texel space |
| `ctx.texels(rows, colors, x0, y0)` | stamp a hand-drawn texel map (list of strings) |
| `ctx.organic(mask)` | round off texel-stepped masks above 16x |
| `ctx.edge(mask, width, side)` | boundary pixels ('tl' lit edge / 'br' shadow edge) |
| `ctx.distance(mask)` | inside distance to edge (for bevels / domes) |

### Tex layers

`Tex(ctx, color, alpha=1, height=0.5, smooth=0.1, f0=0.04, porosity=0, sss=0, emissive=0,
normal_strength=1, wrap=True, grain=0.08)`

- `color` (H, W, 3) or RGB; `alpha`; `height` 0..1 (0.5 = flat surface) drives the normal map,
  ambient occlusion and parallax.
- `smooth` perceptual smoothness, `f0` reflectance (0.02–0.05 for most dielectrics, 0.17 gems),
  `tex.set_metal(mask, IRON|GOLD|COPPER|...)` for metals, `porosity` (sand 1.0, wood 0.2, metal 0),
  `sss` (leaves 0.6, wax, skin, snow), `emissive` 0..1 for glowing parts (lava, lamps, ores glow).
- `wrap=False` for non-tiling sprites (items, GUI, entities, plants).
- `grain=0` disables high-res micro detail (glass, GUI flat colors, fonts).
- `tex.shade()` bakes top-left lighting from the height map into the color — handy for items and
  sprites drawn as height fields.
- `tex.paste(other, mask)`, `tex.copy()`.

Outputs per texture: `name.png`, and for block/item/entity textures `name_n.png` + `name_s.png`
in **LabPBR 1.3** (normal XY DirectX-style + AO + height; smoothness, F0/metal, porosity/SSS,
emission).

### Registry

```python
@texture("block/a", "block/b")              # same generator for several paths
register(f"block/{name}", fn, frames=32, frametime=2, interpolate=False, size=(16, 16), pbr=True)
static_file("minecraft/optifine/ctm/x/x.properties", text)   # non-image files
```

- Older layouts of the same path (used by older game versions) are registered as
  `"<path>@<w>x<h>"` (frame size in texels). Paths that only existed in older versions are registered
  under their old name (see `data/old_only.json`, `data/aliases.json`, `generator/textures/legacy/`).
- Native size and frame count default to the vanilla interface data; set `frames=` to choose your own
  animation length (the strip height is computed for you). `size=` is required for new paths.
- Functional vanilla `.mcmeta` sections (`texture`, `gui`, `villager`, `palette`) are written for you;
  animations come from `frames`/`frametime`.

## 4. Workflow

```bash
.venv/bin/python build.py --res 16 --only block/ --no-zip --preview block/
.venv/bin/python build.py --res 64 256 --only item/ --no-zip
```

- `dist/preview.png` shows every texture tiled 2x2 (seams!) with preview tints; `dist/preview.txt`
  maps grid positions to names. Look at it after every change.
- Check one high-res result too (64x and 256x) — detail must increase, design must stay the same.
- Keep generators fast: a full 16x build of everything should stay well under a minute.
- Only edit files in your own work area folder unless asked. Shared helpers go to
  `generator/materials.py` only when they are clearly general.
