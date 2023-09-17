from functools import partial

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
from faker_graphics.randomcolor import RandomColor


@click.group(name="faker_graphics")
def cli():
    pass


@cli.command()
@click.argument("output", type=click.File("wb"))
@click.argument("hue")
@click.option("-s", "--size", nargs=2, type=int, default=(256, 256))
@click.option("-l", "--luminosity")
@click.option("-a", "--alpha", "color_alpha", default=0.5)
@click.option("-r", "--random", "seed", help="Random seed")
def png(output, hue=None, luminosity=None, seed=None, size=None, color_alpha=None):
    color_ = RandomColor(seed=seed).generate(hue=hue, luminosity=luminosity)
    pattern = cairo.SolidPattern(*color_.rgb, color_alpha)
    with PlaceholderPNG(output, *size) as drawing:
        drawing.draw(pattern)


@cli.command()
@click.argument("hue")
@click.option("-c", "--count", default=1)
@click.option("-l", "--luminosity")
@click.option("-s", "--sorted", "sort", is_flag=True)
@click.option("-r", "--random", "seed", help="Random seed")
def color(hue, luminosity=None, seed=None, count=10, sort=False):
    generator = partial(
        RandomColor(seed=seed).generate,
        luminosity=luminosity,
        hue=hue,
    )
    colors = (generator() for _ in range(count))
    if sort:
        colors = sorted(colors)
    for c in list(colors):
        click.echo(f"{sty.bg(*c.int_rgb)}{c.int_hsv}{sty.bg.rs}")


@cli.command()
def colormap():
    click.echo(RandomColor().colormap)


if __name__ == "__main__":
    cli()
