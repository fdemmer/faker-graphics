# faker-graphics

[![CI](https://github.com/fdemmer/faker-graphics/actions/workflows/test.yml/badge.svg)](https://github.com/fdemmer/faker-graphics/actions/workflows/test.yml)
[![Version](https://img.shields.io/pypi/v/faker-graphics.svg)](https://pypi.org/project/faker-graphics/)
[![Python](https://img.shields.io/pypi/pyversions/faker-graphics.svg)](https://pypi.org/project/faker-graphics/)
[![License](https://img.shields.io/pypi/l/faker-graphics.svg)](https://pypi.org/project/faker-graphics/)

Provider for [Faker](https://pypi.org/project/Faker/) to generate placeholder images with [cairo](https://www.cairographics.org).

- Includes a random color generator forked from the
  [Python port](https://github.com/kevinwuhoo/randomcolor-py) of
  [randomColor.js](https://github.com/davidmerfield/randomColor)
- Provides a simple CLI to generate image files or just colors in the terminal
- Generated images show size, aspect ratio and a simple geometry

## Quickstart

Use `fgr` command to generate a placeholder image with random hue:

```bash
$ uvx --from faker-graphics[cli] --with cairocffi fgr image --size 400 320 --luminosity dark placeholder.png green
```

Show 10 bright random hues of blue in your terminal:

```bash
uvx --from faker-graphics[cli] --with cairocffi fgr color --count 10 --luminosity bright --sorted blue
```

## Installation

```bash
$ pip install faker-graphics
```

## Usage with Faker and/or Factory-Boy

### Register the provider with Faker

The faker-graphics provider will reuse Faker's random instance.

```python
from faker import Faker
from faker_graphics import Provider

fake = Faker()
fake.add_provider(Provider)
```

### Alternatively register the provider with Faker via Factory-Boy

```python
import factory
from faker_graphics import Provider

factory.Faker.add_provider(Provider)
```

### Using the "placeholder_image" fake

After registration the "placeholder_image" fake is available.
It returns a PNG image as bytes.

```python
from faker import Faker

fake = Faker()
data = fake.placeholder_image()
assert data[:6] == b'\x89PNG\r\n'
```

`placeholder_image()` accepts the following optional arguments:

- `width`: image size in pixels, default: 256
- `height`: image size in pixels, default: 256
- `hue`: influence the color randomizer, e.g. a hue name like "green", "blue", "pink" (see `fgr colormap` command below) or a number in a 360° spectrum, default: `None` results in random color
- `luminosity`: "random", "bright", "dark", "light", default: `Luminosity.light`

### Usage with Factory-Boy/Django

```python
import factory

class ModelWithImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'models.ModelWithImage'

    image = factory.django.FileField(
        filename='mock_image.png',
        data=factory.Faker(
            'placeholder_image',
            width=640,
            height=320,
            hue='green',
            luminosity='dark',
        ),
    )
```

## CLI Usage

The CLI provides sub commands for various tasks.

```bash
$ fgr --help
Usage: fgr [OPTIONS] COMMAND [ARGS]...

  faker_graphics commandline interface.

Options:
  -v, --verbose  Increase verbosity.
  --help         Show this message and exit.

Commands:
  color     Show random colors in your terminal.
  colormap  Show colormap used by random color generator as JSON.
  image     Generate a placeholder image with random hue.
```

All subcommands provide their own `--help` messages!

### Generate an image via CLI

Create image files or write to stdout using `-` as `OUTPUT`.

```bash
$ fgr image sample.png green --size 640 320 --luminosity dark
```

![Example Image](https://raw.githubusercontent.com/fdemmer/faker-graphics/main/docs/img/example.png)

### Show colormap

The `colormap` command returns the whole colormap as JSON; you could use `jq` to extract the known hue names.

```bash
$ fgr colormap | jq "keys_unsorted"
[
  "monochrome",
  "grey",
  "red",
  "orange",
  "yellow",
  "green",
  "cyan",
  "blue",
  "purple",
  "magenta",
  "pink"
]
```

### Generate random colors

Generate one or multiple random colors. Colors are returned line by line as HSV/B, RGB and RGB-hex values and shown as background color if your terminal supports it.

```bash
$ fgr color pink --count 3 --luminosity light --sorted
 hsv(328, 30, 98) rgb(249, 174, 214) #f9aed6
 hsv(334, 55, 97) rgb(247, 111, 170) #f76faa
 hsv(344, 26, 100) rgb(255, 188, 206) #ffbcce
```

## Rust port

The `rust/` directory contains a direct Rust port of the Python package as a Cargo crate. It provides the same `fgr` CLI and can also be built as a Python extension module (`faker_graphics_rs`) via [maturin](https://www.maturin.rs) and [PyO3](https://pyo3.rs).

Build and run the CLI:

```bash
cd rust/
cargo build
./target/debug/fgr image output.png green --size 640 320 --luminosity dark
```

Build and install the Python extension into a virtualenv:

```bash
uv venv --python 3.13 .venv && source .venv/bin/activate
uvx maturin develop --manifest-path rust/Cargo.toml --features python
```

Note: the Rust RNG algorithm differs from Python, so generated colors will not match for the same seed.
