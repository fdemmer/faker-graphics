import unittest
import randomcolor


class TestRandomColor(unittest.TestCase):
    def setUp(self):
        self.rand_color = randomcolor.RandomColor(42)

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

    def test_format(self):
        expected_color_rgb = "rgb(7, 7, 7)"
        expected_color_hex = "#4f4f4f"

        color_rgb = self.rand_color.generate(hue="monochrome", color_format="rgb")
        color_hex = self.rand_color.generate(hue="monochrome")

        self.assertEqual(color_rgb, expected_color_rgb)
        self.assertEqual(color_hex, expected_color_hex)

    def test_seed(self):
        expected_color = "#e094be"

        color = self.rand_color.generate()
        self.assertEqual(color, expected_color)
        self.assertEqual(color, randomcolor.RandomColor(42).generate())
