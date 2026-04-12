# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Python

Run the full test matrix (Python 3.8-3.14 x pycairo/cairocffi):
```bash
just test
# or directly:
uvx --with "nox[pbs]" nox
```

Run a single test session (e.g. Python 3.13 + cairocffi):
```bash
uvx --with "nox[pbs]" nox -s "tests-3-13(cairo='cairocffi')"
```

Lint / format:
```bash
uvx ruff check src/ tests/
uvx ruff format src/ tests/
```

Build the package:
```bash
just build
```

Try the Python CLI locally (without installing):
```bash
uvx --with cairocffi --from ".[cli]" fgr image --help
uvx --with cairocffi --from ".[cli]" fgr image output.png green --size 640 320 --luminosity dark
uvx --with cairocffi --from ".[cli]" fgr color --count 5 --luminosity bright blue
```

### Rust

All Rust commands run from the `rust/` directory:

```bash
cd rust/
cargo build              # debug build
cargo build --release    # release build -> target/release/fgr
cargo test               # run all tests
```

Try the Rust CLI locally:
```bash
rust/target/debug/fgr image --help
rust/target/debug/fgr image output.png green --size 640 320 --luminosity dark
rust/target/debug/fgr color --count 5 --luminosity bright blue
rust/target/debug/fgr image - red | xxd | head  # write PNG to stdout
```

### Rust Python extension (`faker_graphics_rs`)

Build and install into a virtualenv (requires an active virtualenv):
```bash
uv venv --python 3.13 .venv
source .venv/bin/activate
uvx maturin develop --manifest-path rust/Cargo.toml --features python
```

Build a wheel:
```bash
uvx maturin build --manifest-path rust/Cargo.toml --features python --interpreter python3.13
```

Check that the python feature compiles without running maturin:
```bash
cd rust/
cargo check --features python
```

## Architecture

### Python (`src/faker_graphics/`)

**`compat.py`** — import shim that tries `cairo` then `cairocffi` at import time, exposing whichever is available as the `cairo` name. Also backfills `StrEnum`/`auto` for Python < 3.11 via the `strenum` package.

**`randomcolor.py`** — `RandomColor` class, a port of randomColor.js. Reads `data/colormap.json` at construction to define hue ranges and saturation/brightness bounds per named color. `generate(hue, luminosity)` returns a `Color` namedtuple with `.rgb`, `.int_rgb`, `.int_hsv`, and `.hex`. `Luminosity` is a `StrEnum` with values `random`, `bright`, `dark`, `light`.

**`drawing.py` / `PlaceholderPNG`** — context manager wrapping a cairo surface+context. `draw(pattern)` fills the background with the given `SolidPattern`, then renders text showing image dimensions and aspect ratio.

**`__init__.py` / `Provider`** — Faker provider. Wires `RandomColor` to reuse Faker's own `random` instance for reproducibility. Exposes `placeholder_image()` returning PNG bytes.

**`__main__.py`** — Click CLI with three subcommands: `image` (write PNG to file/stdout), `color` (print colored terminal swatches), `colormap` (dump colormap JSON).

#### Optional dependencies

The cairo binding (`pycairo` or `cairocffi`) is **required at runtime** but intentionally not declared as a hard dependency — callers choose which binding to install. The `cli` extra adds `click` and `sty`. Without the cairo extra the package cannot be imported at all.

### Rust (`rust/`)

Direct port of the Python package as a Rust crate. The Faker provider is not ported (Python-specific); everything else is.

**`src/randomcolor.rs`** — `RandomColor` struct and `HsvColor` / `Luminosity` types. Colormap JSON is embedded at compile time via `include_str!`. Uses `rand::rngs::SmallRng` (requires the `small_rng` feature). RNG output is not identical to Python (different algorithm).

**`src/drawing.rs`** — `draw_placeholder()` function using `cairo-rs`. Requires the `png` feature on the `cairo` dependency for `Surface::write_to_png`.

**`src/lib.rs`** — library crate re-exporting `RandomColor`, `HsvColor`, `Luminosity`, and `draw_placeholder`. Also conditionally includes `mod python` when built with `--features python`.

**`src/main.rs`** — `fgr` binary using `clap` (derive API). Three subcommands: `image`, `color`, `colormap`. Terminal color swatches use `owo-colors`.

**`src/python.rs`** — PyO3 bindings compiled only with `--features python`. Exposes `RandomColor`, `HsvColor`, `Luminosity`, and `draw_placeholder` to Python as the `faker_graphics_rs` extension module.

**`pyproject.toml`** — maturin build descriptor for the Python extension. Module name is `faker_graphics_rs`; activates the `python` feature automatically.

#### Dependencies note

`cairo-rs` requires system libcairo (the same library used by the Python package). Non-obvious Cargo features:
- `cairo = { ..., features = ["png"] }` - enables `Surface::write_to_png`
- `rand = { ..., features = ["small_rng"] }` - enables `SmallRng`
- `python` feature (optional) - enables PyO3 bindings via maturin; uses `crate-type = ["rlib", "cdylib"]` (rlib for the CLI binary, cdylib for the Python extension). `SmallRng` is `!Send` so `PyRandomColor` is marked `unsendable`.
