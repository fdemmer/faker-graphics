import json
import logging
import sys
from functools import partial

import structlog

try:
    import click
    import sty
except ImportError as exc:
    raise ImportError(
        "The CLI feature of this package requires the following packages: "
        "click, sty. Use the [cli] extra to install them."
    ) from exc

from faker_graphics.compat import cairo
from faker_graphics.drawing import PlaceholderPNG
from faker_graphics.randomcolor import Luminosity, RandomColor


@click.group()
@click.option("-v", "--verbose", help="Increase verbosity.", count=True)
def cli(verbose):
    """faker_graphics commandline interface."""
    level = logging.WARNING - verbose * 10
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(level))
    structlog.configure(logger_factory=structlog.WriteLoggerFactory(sys.stderr))


@cli.command()
@click.argument("output", type=click.File("wb"))
@click.argument("hue", required=False)
@click.option("-s", "--size", nargs=2, type=int, default=(256, 256))
@click.option("-l", "--luminosity")
@click.option("-a", "--alpha", "color_alpha", default=0.5)
@click.option("-r", "--random", "seed", help="Provide a custom random seed.")
def image(output, hue=None, luminosity=None, seed=None, size=None, color_alpha=None):
    """Generate a placeholder image with random hue."""
    color_ = RandomColor(seed=seed).generate(hue=hue, luminosity=luminosity)
    pattern = cairo.SolidPattern(*color_.rgb, color_alpha)
    with PlaceholderPNG(output, *size) as drawing:
        drawing.draw(pattern)


@cli.command()
@click.argument("hue")
@click.option("-c", "--count", default=1)
@click.option("-l", "--luminosity")
@click.option("-s", "--sorted", "sort", is_flag=True, help="Sort colors by hue.")
@click.option("-r", "--random", "seed", help="Provide a custom random seed.")
def color(hue, luminosity=None, seed=None, count=None, sort=None):
    """Show random colors in your terminal."""
    generator = partial(
        RandomColor(seed=seed).generate,
        luminosity=luminosity,
        hue=hue,
    )
    colors = (generator() for _ in range(count))
    if sort:
        colors = sorted(colors)
    for c in list(colors):
        fg = "black" if luminosity == Luminosity.light else "white"
        label = f" hsv{c.int_hsv} rgb{c.int_rgb} {c.hex} "
        click.echo(f"{sty.bg(*c.int_rgb)}{sty.fg(fg)}{label}{sty.bg.rs}")


@cli.command()
def colormap():
    """Show colormap used by random color generator as JSON."""
    click.echo(json.dumps(RandomColor().colormap))


if __name__ == "__main__":
    cli()
