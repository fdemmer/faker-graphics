import unittest
from pathlib import Path

from faker_graphics.randomcolor import Luminosity, RandomColor


class TestRandomColor(unittest.TestCase):
    def setUp(self):
        self.rand_color = RandomColor(42)

    def test_load_colormap(self):
        expected_colormap = {
            "monochrome": {
                "hue_range": [0, 0],
                "lower_bounds": [[0, 0], [100, 0]],
                "brightness_range": [0, 0],
                "saturation_range": [0, 100],
            }
        }
        rand_color = RandomColor(
            42, colormap=Path(__file__).parent / "data/colormap.json"
        )
        self.assertEqual(rand_color.colormap, expected_colormap)

    def test_hue(self):
        expected_colors = ["#db90a8", "#c65976", "#db8ab5"]
        purple = [self.rand_color.generate(hue="pink").hex for _ in expected_colors]
        self.assertEqual(purple, expected_colors)

    def test_luminosity(self):
        expected_colors = ["#d14f96", "#3bc66a", "#dbf760"]
        bright = [
            self.rand_color.generate(luminosity="bright").hex for _ in expected_colors
        ]
        self.assertEqual(bright, expected_colors)

    def test_hue_luminosity(self):
        expected_color = "#b26910"
        color = self.rand_color.generate(hue="orange", luminosity=Luminosity.dark).hex
        self.assertEqual(color, expected_color)

    def test_invalid_luminosity(self):
        with self.assertRaises(ValueError):
            self.rand_color.generate(luminosity="invalid")

    def test_color_format(self):
        expected_color_hex = "#cecece"
        expected_color_hsv = (0, 0, 0.14)
        expected_color_hls = (0.0, 0.03, 0.0)
        expected_color_rgb = (0.94, 0.94, 0.94)
        expected_color_a_hsv = (0, 0, 35)
        expected_color_a_rgb = (79, 79, 79)

        color_hex = self.rand_color.generate(hue="monochrome").hex
        color_hsv = self.rand_color.generate(hue="monochrome").hsv
        color_hls = self.rand_color.generate(hue="monochrome").hls
        color_rgb = self.rand_color.generate(hue="monochrome").rgb
        color_a_hsv = self.rand_color.generate(hue="monochrome").int_hsv
        color_a_rgb = self.rand_color.generate(hue="monochrome").int_rgb

        self.assertEqual(color_hex, expected_color_hex)
        self.assertEqual(color_hsv, expected_color_hsv)
        self.assertEqual(color_hls, expected_color_hls)
        self.assertEqual(color_rgb, expected_color_rgb)
        self.assertEqual(color_a_hsv, expected_color_a_hsv)
        self.assertEqual(color_a_rgb, expected_color_a_rgb)

    def test_seed(self):
        expected_color = "#db90b9"
        color = self.rand_color.generate()
        self.assertEqual(color.hex, expected_color)
        self.assertEqual(color, RandomColor(42).generate())
