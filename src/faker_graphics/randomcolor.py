import colorsys
import json
import random
from pathlib import Path


class RandomColor:
    def __init__(self, seed=None, colormap=None):
        if colormap is None:
            colormap = Path(__file__).parent / "data/colormap.json"
        with open(colormap) as fh:  # noqa: PTH123
            self.colormap = self.load_colormap(fh)

        self.random = random.Random(seed)

    @staticmethod
    def load_colormap(fh):
        # Load color dictionary and populate the color dictionary
        colormap = json.load(fh)

        for color_attrs in colormap.values():
            lower_bounds = sorted(color_attrs["lower_bounds"])
            s_min, b_max = lower_bounds[0]
            s_max, b_min = lower_bounds[-1]
            color_attrs["saturation_range"] = [s_min, s_max]
            color_attrs["brightness_range"] = [b_min, b_max]

        return colormap

    def generate(self, hue=None, luminosity=None, color_format="hex"):
        # First we pick a hue (H)
        h = self.pick_hue(hue)

        # Then use H to determine saturation (S)
        s = self.pick_saturation(h, hue, luminosity)

        # Then use S and H to determine brightness (B).
        b = self.pick_brightness(h, s, luminosity)

        # Then we return the HSB color in the desired format
        return self.set_format([h, s, b], color_format)

    def pick_hue(self, hue):
        hue_range = self.get_hue_range(hue)
        hue = self.random_within(hue_range)

        # Instead of storing red as two separate ranges,
        # we group them, using negative numbers
        if hue < 0:
            hue += 360

        return hue

    def pick_saturation(self, hue, hue_name, luminosity):
        if luminosity == "random":
            return self.random_within([0, 100])

        if hue_name == "monochrome":
            return 0

        s_min, s_max = self.get_saturation_range(hue)

        if luminosity == "bright":
            s_min = 55
        elif luminosity == "dark":
            s_min = s_max - 10
        elif luminosity == "light":
            s_max = 55

        return self.random_within([s_min, s_max])

    def pick_brightness(self, h, s, luminosity):
        b_min = self.get_minimum_brightness(h, s)
        b_max = 100

        if luminosity == "dark":
            b_max = b_min + 20
        elif luminosity == "light":
            b_min = (b_max + b_min) / 2
        elif luminosity == "random":
            b_min = 0
            b_max = 100

        return self.random_within([b_min, b_max])

    def set_format(self, hsv, format_):
        if "hsv" in format_:
            color = hsv
        elif "rgb" in format_:
            color = self.hsv_to_rgb(hsv)
        elif "hex" in format_:
            r, g, b = self.hsv_to_rgb(hsv)
            return f"#{r:02x}{g:02x}{b:02x}"
        else:
            raise ValueError("Unrecognized format")

        if "Array" in format_ or format_ == "hex":
            return color
        else:
            prefix = format_[:3]
            color_values = [str(x) for x in color]
            return "{}({})".format(prefix, ", ".join(color_values))

    def get_minimum_brightness(self, h, s):
        lower_bounds = self.get_color_info(h)["lower_bounds"]

        for bounds in zip(lower_bounds, lower_bounds[1:]):
            (s1, v1), (s2, v2) = bounds

            if s1 <= s <= s2:
                m = (v2 - v1) / (s2 - s1)
                b = v1 - m * s1

                return m * s + b

        return 0

    def get_hue_range(self, color_input):
        if color_input and color_input.isdigit():
            number = int(color_input)

            if 0 < number < 360:
                return [number, number]

        elif color_input and color_input in self.colormap:
            color = self.colormap[color_input]
            if "hue_range" in color:
                return color["hue_range"]

        else:
            return [0, 360]

    def get_saturation_range(self, hue):
        return self.get_color_info(hue)["saturation_range"]

    def get_color_info(self, hue):
        # Maps red colors to make picking hue easier
        if 334 <= hue <= 360:
            hue -= 360

        for color_name, color in self.colormap.items():
            if (
                color["hue_range"]
                and color["hue_range"][0] <= hue <= color["hue_range"][1]
            ):
                return self.colormap[color_name]

        raise ValueError("Color not found")

    def random_within(self, r):
        return self.random.randint(int(r[0]), int(r[1]))

    @classmethod
    def hsv_to_rgb(cls, hsv):
        h, s, v = hsv
        h = 1 if h == 0 else h
        h = 359 if h == 360 else h

        h = h / 360
        s = s / 100
        v = v / 100

        rgb = colorsys.hsv_to_rgb(h, s, v)
        return [int(c * 255) for c in rgb]
