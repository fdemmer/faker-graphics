import colorsys
import json
import random
from dataclasses import dataclass
from functools import total_ordering
from pathlib import Path

from faker_graphics.common import StructlogMixin
from faker_graphics.compat import StrEnum, auto


@total_ordering
@dataclass
class HSVColor:
    h: int
    s: int
    v: int

    @property
    def hsv(self):
        return self.h / 360, self.s / 100, self.v / 100

    @property
    def rgb(self):
        return colorsys.hsv_to_rgb(*self.hsv)

    @property
    def hls(self):
        return colorsys.rgb_to_hls(*self.rgb)

    @property
    def int_hsv(self):
        return self.h, self.s, self.v

    @property
    def int_rgb(self):
        return tuple(int(x * 255) for x in self.rgb)

    @property
    def hex(self):  # noqa: A003
        r, g, b = self.int_rgb
        return f"#{r:02x}{g:02x}{b:02x}"

    def __lt__(self, other):
        return self.int_hsv < other.int_hsv


class Luminosity(StrEnum):
    random = auto()
    bright = auto()
    dark = auto()
    light = auto()


class RandomColor(StructlogMixin):
    def __init__(self, seed=None, colormap=None):
        super().__init__()
        if colormap is None:
            colormap = Path(__file__).parent / "data/colormap.json"
        with open(colormap) as fh:  # noqa: PTH123
            self.colormap = self.load_colormap(fh)
        self.log.info("colormap loaded", colormap=str(colormap))

        self.random = random.Random(seed)
        self.log.info("random seed", seed=seed)

    @staticmethod
    def load_colormap(fh):
        # Load color dictionary and populate the color dictionary
        colormap = json.load(fh)

        # sort by hue ranges for deterministic get_color_info
        colormap = dict(
            sorted(colormap.items(), key=lambda x: x[1].get("hue_range", (-360, 0))[0])
        )

        for color_attrs in colormap.values():
            lower_bounds = sorted(color_attrs["lower_bounds"])
            s_min, b_max = lower_bounds[0]
            s_max, b_min = lower_bounds[-1]
            color_attrs["saturation_range"] = sorted([s_min, s_max])
            color_attrs["brightness_range"] = sorted([b_min, b_max])

        return colormap

    def generate(self, hue=None, luminosity=None):
        if luminosity is not None:
            try:
                luminosity = Luminosity[luminosity]
            except KeyError as exc:
                values = [str(enum_) for enum_ in Luminosity]
                raise ValueError(
                    f"Invalid luminosity. Allowed values are: {', '.join(values)}"
                ) from exc
        self.log.info("generating", hue=hue, luminosity=luminosity)

        # First we pick a hue (H)
        h = self.pick_hue(hue)
        self.log.debug("picked hue", h=h)

        # Then use H to determine saturation (S)
        s = self.pick_saturation(h, luminosity) if h is not None else 0
        self.log.debug("picked saturation", s=s)

        # Then use H and S to determine brightness/value (B/V).
        b = self.pick_brightness(hue if h is None else h, s, luminosity)
        self.log.debug("picked brightness", b=b)

        # Then we return the HSV/HSB color
        return HSVColor(h or 0, s, b)

    def pick_hue(self, hue):
        if hue_range := self.get_hue_range(hue):
            hue = self.random.randint(*hue_range)

            # Instead of storing red as two separate ranges,
            # we group them, using negative numbers
            if hue < 0:
                hue += 360

            return hue

    def pick_saturation(self, hue, luminosity):
        log = self.log.bind(hue=hue, luminosity=luminosity)
        log.debug("get saturation from luminosity")
        if luminosity == Luminosity.random:
            return self.random.randint(0, 100)

        s_min, s_max = self.get_color_info(hue)["saturation_range"]
        log.debug("range from hue", s_min=s_min, s_max=s_max)

        if luminosity == Luminosity.bright:
            s_min = 55
        elif luminosity == Luminosity.dark:
            s_min = s_max - 10
        elif luminosity == Luminosity.light:
            s_max = 55

        log.debug("using range", s_min=s_min, s_max=s_max)
        return self.random.randint(s_min, s_max)

    def pick_brightness(self, hue, saturation, luminosity):
        log = self.log.bind(hue=hue, saturation=saturation, luminosity=luminosity)
        log.debug("get brightness from hue, saturation, luminosity")
        b_min, b_max = self.get_color_info(hue)["brightness_range"]
        log.debug("range from hue", b_min=b_min, b_max=b_max)
        b_min = self.get_minimum_brightness(hue, saturation)
        log.debug("adapted minimum", b_min=b_min, b_max=b_max)

        if luminosity == Luminosity.dark:
            b_max = b_min + 20
        elif luminosity == Luminosity.light:
            b_min = (b_max + b_min) // 2
        elif luminosity == Luminosity.random:
            b_min = 0
            b_max = 100

        log.debug("using range", b_min=b_min, b_max=b_max)
        return self.random.randint(b_min, b_max)

    def get_minimum_brightness(self, hue, saturation):
        lower_bounds = self.get_color_info(hue)["lower_bounds"]

        for bounds in zip(lower_bounds, lower_bounds[1:]):
            (s1, v1), (s2, v2) = bounds

            if s1 <= saturation <= s2:
                if saturation > 0:
                    m = (v2 - v1) // (s2 - s1)
                    b = v1 - m * s1
                    return m * saturation + b
                else:
                    return v2

        return 0

    def get_hue_range(self, color_input):
        log = self.log.bind(color_input=color_input)
        log.debug("get hue range from color_input")
        if color_input and color_input.isdigit():
            log.debug("color_input is digit")
            number = int(color_input)

            if 0 <= number <= 360:
                log.debug("using single number range")
                return [number, number]

        elif color_input and color_input in self.colormap:
            log.debug("color_input is in colormap")
            color = self.colormap[color_input]
            if hue_range := color.get("hue_range"):
                log.debug("using range", hue_range=hue_range)
                return hue_range

        else:
            log.debug("fallback to full range")
            return [0, 360]

    def get_color_info(self, color_input):
        # get by name
        if color := self.colormap.get(color_input):
            return color

        hue = int(color_input)
        # Maps red colors to make picking hue easier
        if 334 <= hue <= 360:
            hue -= 360

        # find by matching hue_range
        for color_name, color in self.colormap.items():
            if hue_range := color.get("hue_range"):
                hue_min, hue_max = hue_range
                if hue_min <= hue <= hue_max:
                    return self.colormap[color_name]

        raise ValueError("Color not found")
