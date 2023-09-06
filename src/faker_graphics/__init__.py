import io

import cairo
from faker.providers import BaseProvider

from faker_graphics import randomcolor
from faker_graphics.drawing import PlaceholderPNG


class Provider(BaseProvider):
    def placeholder_image(
        self,
        width=256,
        height=256,
        hue="monochrome",
        luminosity="light",
    ):
        color = None
        if hue != "monochrome":
            # use seed from Faker
            rand_color = randomcolor.RandomColor(self.generator._global_seed)
            # generate pseudo-random color
            rgb_color = rand_color.generate(
                hue=hue,
                luminosity=luminosity,
                color_format="Array rgb",
            )
            # cairo requires float values between 0 and 1
            r, g, b = (channel / 255 for channel in rgb_color)
            color = cairo.SolidPattern(r, g, b, 0.5)

        with io.BytesIO() as fh:
            with PlaceholderPNG(fh, width, height) as d:
                d.draw(color)
            return fh.getvalue()
