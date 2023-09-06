import io
import unittest

from faker_graphics.drawing import CairoImageDrawing, CairoSVGDrawing, PlaceholderPNG


class TestRandomColor(unittest.TestCase):
    def setUp(self):
        pass

    def test_image_drawing(self):
        # png data is written on save()
        with io.BytesIO() as fh:
            CairoImageDrawing(fh).save()
            value = fh.getvalue()
        self.assertTrue(value.startswith(b"\x89PNG\r\n"))

    def test_svg_drawing(self):
        # svg is written on init
        with io.BytesIO() as fh:
            CairoSVGDrawing(fh)
            value = fh.getvalue()
        self.assertTrue(value.startswith(b'<?xml version="1.0" encoding="UTF-8"?>\n'))

    def test_placeholder_drawing(self):
        # png data is written on contextmanager __exit__ via save()
        with io.BytesIO() as fh:
            with PlaceholderPNG(fh) as drawing:
                drawing.draw()
            value = fh.getvalue()
        self.assertTrue(value.startswith(b"\x89PNG\r\n"))
