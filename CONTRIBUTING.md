# Contributing

The value of this project is that **every pixel is provably original**. These rules apply to the
maintainer and to every contributor.

## 1. Clean room

Follow the rules in [docs/STYLE.md §1](docs/STYLE.md). In short: never open, trace, sample or color-pick
vanilla (or third-party) textures; only functional interface/layout data may be used.

## 2. Texture sources

| Source | Location | Notes |
|---|---|---|
| Generated | `generator/textures/**.py` | reproducible, preferred |
| Hand-drawn | `overrides/<res>x/assets/...` | replaces the generated file with the same path |

Keep hand-drawn source files (e.g. `.aseprite`) under `sources/` with the same relative path.

## 3. Commits

- One kind of change per commit; say which textures changed and how (generated / hand-drawn).
- Keep intermediate drafts of hand-drawn work: the history is the evidence of originality.
- Check `dist/preview.png` (`build.py --preview`) and at least one high resolution before committing.

## 4. Contributor license grant (required)

So the project can keep offering commercial licenses next to CC BY-NC-SA 4.0, every external contributor
must agree:

> I confirm that my contribution is my own independent work and follows the clean-room rules. I keep my
> copyright and grant Tab Nahida a worldwide, perpetual, irrevocable, royalty-free, non-exclusive,
> sublicensable license to use, modify and distribute my contribution under CC BY-NC-SA 4.0 and under
> any other terms, including commercial licenses.

State "I agree to the contributor license grant in CONTRIBUTING.md §4" in your pull request.
Contributions without it cannot be merged.
