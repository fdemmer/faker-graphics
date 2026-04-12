import unittest


try:
    import faker_graphics_rs as fgr
except ImportError:
    fgr = None


@unittest.skipIf(fgr is None, "faker_graphics_rs not installed (run: maturin develop)")
class TestLuminosity(unittest.TestCase):
    def test_string_constructor(self):
        for value in ("random", "bright", "dark", "light"):
            lum = fgr.Luminosity(value)
            self.assertEqual(str(lum), value)

    def test_class_attributes(self):
        self.assertEqual(str(fgr.Luminosity.random), "random")
        self.assertEqual(str(fgr.Luminosity.bright), "bright")
        self.assertEqual(str(fgr.Luminosity.dark), "dark")
        self.assertEqual(str(fgr.Luminosity.light), "light")

    def test_equality(self):
        self.assertEqual(fgr.Luminosity("bright"), fgr.Luminosity.bright)
        self.assertEqual(fgr.Luminosity("dark"), fgr.Luminosity.dark)
        self.assertNotEqual(fgr.Luminosity("bright"), fgr.Luminosity.dark)

    def test_repr(self):
        self.assertIn("bright", repr(fgr.Luminosity.bright))

    def test_invalid_string(self):
        with self.assertRaises(ValueError):
            fgr.Luminosity("invalid")

    def test_invalid_empty(self):
        with self.assertRaises(ValueError):
            fgr.Luminosity("")


@unittest.skipIf(fgr is None, "faker_graphics_rs not installed (run: maturin develop)")
class TestHsvColor(unittest.TestCase):
    def setUp(self):
        self.color = fgr.RandomColor(seed=42).generate()

    def test_h_range(self):
        self.assertGreaterEqual(self.color.h, 0)
        self.assertLessEqual(self.color.h, 360)

    def test_s_range(self):
        self.assertGreaterEqual(self.color.s, 0)
        self.assertLessEqual(self.color.s, 100)

    def test_v_range(self):
        self.assertGreaterEqual(self.color.v, 0)
        self.assertLessEqual(self.color.v, 100)

    def test_hex_format(self):
        hex_color = self.color.hex()
        self.assertRegex(hex_color, r"^#[0-9a-f]{6}$")

    def test_rgb(self):
        r, g, b = self.color.rgb()
        for channel in (r, g, b):
            self.assertGreaterEqual(channel, 0.0)
            self.assertLessEqual(channel, 1.0)

    def test_int_rgb(self):
        r, g, b = self.color.int_rgb()
        for channel in (r, g, b):
            self.assertGreaterEqual(channel, 0)
            self.assertLessEqual(channel, 255)

    def test_int_hsv(self):
        h, s, v = self.color.int_hsv()
        self.assertEqual(h, self.color.h)
        self.assertEqual(s, self.color.s)
        self.assertEqual(v, self.color.v)

    def test_hls(self):
        h, l, s = self.color.hls()  # noqa: E741
        for channel in (h, l, s):
            self.assertGreaterEqual(channel, 0.0)
            self.assertLessEqual(channel, 1.0)

    def test_equality(self):
        color_a = fgr.RandomColor(seed=42).generate()
        color_b = fgr.RandomColor(seed=42).generate()
        self.assertEqual(color_a, color_b)

    def test_repr(self):
        r = repr(self.color)
        self.assertIn(str(self.color.h), r)
        self.assertIn(str(self.color.s), r)
        self.assertIn(str(self.color.v), r)


@unittest.skipIf(fgr is None, "faker_graphics_rs not installed (run: maturin develop)")
class TestRandomColor(unittest.TestCase):
    def setUp(self):
        self.rand_color = fgr.RandomColor(seed=42)

    def test_hue(self):
        # Pink hue range is roughly 300-360; all generated pinks should fall there
        for _ in range(5):
            color = self.rand_color.generate(hue="pink")
            self.assertGreaterEqual(color.h, 290)
            self.assertLessEqual(color.h, 360)

    def test_luminosity_bright(self):
        # Bright luminosity enforces saturation >= 55
        for _ in range(5):
            color = self.rand_color.generate(luminosity=fgr.Luminosity.bright)
            self.assertGreaterEqual(color.s, 55)

    def test_luminosity_dark(self):
        # Dark constrains brightness to a narrow window (b_min..b_min+20)
        for _ in range(5):
            color = self.rand_color.generate(luminosity=fgr.Luminosity.dark)
            self.assertIsInstance(color, fgr.HsvColor)

    def test_luminosity_light(self):
        # Light colors have high brightness (b_min = (b_max + b_min) / 2)
        for _ in range(5):
            color = self.rand_color.generate(luminosity=fgr.Luminosity.light)
            self.assertGreaterEqual(color.v, 50)

    def test_hue_luminosity(self):
        color = self.rand_color.generate(hue="orange", luminosity=fgr.Luminosity.dark)
        # Orange hue range is 13-40
        self.assertGreaterEqual(color.h, 13)
        self.assertLessEqual(color.h, 40)

    def test_invalid_luminosity(self):
        with self.assertRaises(ValueError):
            fgr.Luminosity("invalid")

    def test_monochrome(self):
        color = self.rand_color.generate(hue="monochrome")
        self.assertEqual(color.s, 0)
        self.assertEqual(color.h, 0)

    def test_seed_int_reproducible(self):
        color_a = fgr.RandomColor(seed=42).generate()
        color_b = fgr.RandomColor(seed=42).generate()
        self.assertEqual(color_a, color_b)
        self.assertEqual(color_a.hex(), color_b.hex())

    def test_seed_str_reproducible(self):
        color_a = fgr.RandomColor(seed="hello").generate()
        color_b = fgr.RandomColor(seed="hello").generate()
        self.assertEqual(color_a, color_b)

    def test_seed_sequence_reproducible(self):
        rc_a = fgr.RandomColor(seed=42)
        rc_b = fgr.RandomColor(seed=42)
        for _ in range(10):
            self.assertEqual(rc_a.generate(), rc_b.generate())

    def test_no_seed(self):
        color = fgr.RandomColor().generate()
        self.assertIsInstance(color, fgr.HsvColor)

    def test_no_seed_varies(self):
        # Two unseeded instances should not produce the same sequence
        # (may fail with astronomically small probability)
        colors_a = [fgr.RandomColor().generate().hex() for _ in range(5)]
        colors_b = [fgr.RandomColor().generate().hex() for _ in range(5)]
        self.assertNotEqual(colors_a, colors_b)

    def test_numeric_hue_string(self):
        # Hue given as a numeric string should be accepted
        color = self.rand_color.generate(hue="200")
        self.assertIsInstance(color, fgr.HsvColor)


@unittest.skipIf(fgr is None, "faker_graphics_rs not installed (run: maturin develop)")
class TestDrawPlaceholder(unittest.TestCase):
    def test_returns_bytes(self):
        result = fgr.draw_placeholder(256, 256)
        self.assertIsInstance(result, bytes)

    def test_png_magic_bytes(self):
        result = fgr.draw_placeholder(256, 256)
        self.assertTrue(result.startswith(b"\x89PNG\r\n"))

    def test_default_size(self):
        result = fgr.draw_placeholder(256, 256)
        self.assertGreater(len(result), 1000)

    def test_non_square(self):
        result = fgr.draw_placeholder(640, 320)
        self.assertTrue(result.startswith(b"\x89PNG\r\n"))

    def test_tall(self):
        result = fgr.draw_placeholder(100, 400)
        self.assertTrue(result.startswith(b"\x89PNG\r\n"))

    def test_with_color_overlay(self):
        result = fgr.draw_placeholder(256, 256, color=(0.2, 0.5, 0.9, 0.5))
        self.assertTrue(result.startswith(b"\x89PNG\r\n"))

    def test_without_color(self):
        result = fgr.draw_placeholder(256, 256, color=None)
        self.assertTrue(result.startswith(b"\x89PNG\r\n"))

    def test_color_affects_output(self):
        without = fgr.draw_placeholder(64, 64)
        with_color = fgr.draw_placeholder(64, 64, color=(1.0, 0.0, 0.0, 0.8))
        self.assertNotEqual(without, with_color)
