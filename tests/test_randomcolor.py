import unittest

import faker_graphics.randomcolor as randomcolor


class TestRandomColor(unittest.TestCase):
    def setUp(self):
        self.rand_color = randomcolor.RandomColor(42)

    def test_load_colormap(self):
        expected_colormap = {
            "monochrome": {
                "hue_range": [0, 0],
                "lower_bounds": [[0, 0], [100, 0]],
                "brightness_range": [0, 0],
                "saturation_range": [0, 100],
            }
        }
        rand_color = randomcolor.RandomColor(42, colormap="data/colormap.json")
        self.assertEqual(rand_color.colormap, expected_colormap)

    def test_hue(self):
        expected_colors = ["#b98bd3", "#ac5ed1", "#a786d6"]
        purple = [self.rand_color.generate(hue="purple") for _ in expected_colors]
        self.assertEqual(purple, expected_colors)

    def test_luminosity(self):
        expected_colors = ["#d35098", "#3dce6e", "#dbf760"]
        bright = [self.rand_color.generate(luminosity="bright") for _ in expected_colors]
        self.assertEqual(bright, expected_colors)

    def test_hue_luminosity(self):
        expected_color = "#b27910"
        color = self.rand_color.generate(hue="orange", luminosity="dark")
        self.assertEqual(color, expected_color)

    def test_color_format(self):
        expected_color_hex = "#070707"
        expected_color_hsv = "hsv(0, 0, 31)"
        expected_color_rgb = "rgb(43, 43, 43)"
        expected_color_a_hsv = [0, 0, 86]
        expected_color_a_rgb = [191, 191, 191]

        color_hex = self.rand_color.generate(hue="monochrome")
        color_hsv = self.rand_color.generate(hue="monochrome", color_format="hsv")
        color_rgb = self.rand_color.generate(hue="monochrome", color_format="rgb")
        color_a_hsv = self.rand_color.generate(hue="monochrome", color_format="Array hsv")
        color_a_rgb = self.rand_color.generate(hue="monochrome", color_format="Array rgb")

        self.assertEqual(color_hex, expected_color_hex)
        self.assertEqual(color_hsv, expected_color_hsv)
        self.assertEqual(color_rgb, expected_color_rgb)
        self.assertEqual(color_a_hsv, expected_color_a_hsv)
        self.assertEqual(color_a_rgb, expected_color_a_rgb)

        with self.assertRaisesRegex(ValueError, "Unrecognized format"):
            self.rand_color.generate(color_format="hsl")

    def test_seed(self):
        expected_color = "#e094be"

        color = self.rand_color.generate()
        self.assertEqual(color, expected_color)
        self.assertEqual(color, randomcolor.RandomColor(42).generate())
