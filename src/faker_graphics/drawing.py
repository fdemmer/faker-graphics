from contextlib import contextmanager

from faker_graphics.common import StructlogMixin
from faker_graphics.compat import cairo


class CairoDrawingBase(StructlogMixin):
    def __init__(
        self,
        file_obj,
        width=256,
        height=256,
        line_width=2,
        source=cairo.SolidPattern(0, 0, 0),  # noqa: B008
        font_family="sans-serif",
        font_size=12,
        font_slant=cairo.FONT_SLANT_NORMAL,
        font_weight=cairo.FONT_WEIGHT_NORMAL,
    ):
        super().__init__()
        self.file_obj, self.width, self.height = file_obj, width, height
        self.surface = self.get_new_surface()
        self.context = self.get_new_context(
            line_width, source, font_family, font_size, font_slant, font_weight
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.save()

    def get_new_surface(self):
        raise NotImplementedError

    def get_new_context(
        self, line_width, source, font_family, font_size, font_slant, font_weight
    ):
        self.log.debug(
            "new context",
            line_width=line_width,
            font_family=font_family,
            font_size=font_size,
            font_slant=font_slant,
            font_weight=font_weight,
        )
        context = cairo.Context(self.surface)
        context.set_source(source)
        context.set_line_width(line_width)
        context.select_font_face(font_family, font_slant, font_weight)
        context.set_font_size(font_size)
        return context

    def save(self):
        raise NotImplementedError

    @contextmanager
    def source(self, source=None):
        if not source:
            yield
        else:
            old_source = self.context.get_source()
            self.context.set_source(source)
            yield
            self.context.set_source(old_source)

    def stroke_line(self, x1, y1, x2, y2):
        # draw a line from xy1 to xy2
        self.log.debug(
            "line",
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            line_width=self.context.get_line_width(),
        )
        self.context.move_to(x1, y1)
        self.context.line_to(x2, y2)
        self.context.stroke()

    def stroke_rectangle(self, width, height):
        # draw centered rectangle
        self.log.debug(
            "rectangle",
            width=width,
            height=height,
            line_width=self.context.get_line_width(),
        )
        x, y = (self.width - width) / 2, (self.height - height) / 2
        self.context.rectangle(x, y, width, height)
        self.context.stroke()

    def stroke_square(self, size):
        # draw centered square
        self.stroke_rectangle(size, size)

    def write(self, text, y_offset=1):
        # write vertically offset, centered text
        self.log.debug("write", text=text)

        # align from top or bottom
        _, _, text_width, text_height, _, _ = self.context.text_extents(text)
        if y_offset > 0:
            y = text_height * y_offset
        else:
            y = self.height + text_height * y_offset
        x = (self.width - text_width) / 2
        self.context.move_to(x, y)

        # write text
        self.context.show_text(text)


class CairoImageDrawing(CairoDrawingBase):
    def get_new_surface(self):
        self.log.debug("new image surface", width=self.width, height=self.height)
        return cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)

    def save(self):
        self.log.debug("writing png data")
        self.surface.write_to_png(self.file_obj)


class CairoSVGDrawing(CairoDrawingBase):
    def get_new_surface(self):
        self.log.debug("new svg surface", width=self.width, height=self.height)
        return cairo.SVGSurface(self.file_obj, self.width, self.height)

    def save(self):
        pass


class PlaceholderPNG(CairoImageDrawing):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("line_width", 4)
        kwargs.setdefault("font_size", 20)
        kwargs.setdefault("font_weight", cairo.FONT_WEIGHT_BOLD)
        super().__init__(*args, **kwargs)

    def draw(self, color=None):
        # monochrome background fill
        with self.source(cairo.SolidPattern(0.6, 0.6, 0.6)):
            self.context.paint()

        with self.source(cairo.SolidPattern(0.7, 0.7, 0.7)):
            # diagonals
            self.stroke_line(0, 0, self.width, self.height)
            self.stroke_line(self.width, 0, 0, self.height)
            # square
            self.stroke_square(min(self.width, self.height) / 2)

        # labels
        with self.source(cairo.SolidPattern(0.45, 0.45, 0.45)):
            self.write(f"{self.width} x {self.height}", y_offset=2)
            self.write(f"{(self.width / self.height):.2g}:1", y_offset=-1)

        # semitransparent color overlay
        if color:
            if (alpha := color.get_rgba()[-1]) > 0.8:
                self.log.warning(
                    "A pattern with alpha of around .5 is recommended!",
                    alpha=alpha,
                )
            self.log.debug("apply color", color=color.get_rgba())
            with self.source(color):
                self.context.paint()
