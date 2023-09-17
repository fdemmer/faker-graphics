import io

from faker.providers import BaseProvider

from faker_graphics import randomcolor
from faker_graphics.compat import cairo
from faker_graphics.drawing import PlaceholderPNG


class Provider(BaseProvider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # crate RandomColor and reuse random instance from Faker
        self.rand_color = randomcolor.RandomColor()
        self.rand_color.random = self.generator.random

    def placeholder_image(
        self,
        width=256,
        height=256,
        hue=None,
        luminosity="light",
        color_alpha=0.6,
    ):
        pattern = None
        if hue != "monochrome":
            # generate pseudo-random color
            color = self.rand_color.generate(hue=hue, luminosity=luminosity)
            pattern = cairo.SolidPattern(*color.rgb, color_alpha)

        with io.BytesIO() as fh:
            with PlaceholderPNG(fh, width, height) as d:
                d.draw(pattern)
            return fh.getvalue()
