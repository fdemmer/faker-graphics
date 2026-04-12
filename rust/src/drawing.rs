use std::io::Write;

use anyhow::Context as _;
use cairo::{Context, FontSlant, FontWeight, Format, ImageSurface};


/// Draw a placeholder PNG and write it to `writer`.
///
/// `color` is an optional RGBA tuple (r, g, b, a) each 0.0-1.0.  When given,
/// a semi-transparent color overlay is painted on top of the grey base image.
pub fn draw_placeholder<W: Write>(
    writer: &mut W,
    width: i32,
    height: i32,
    color: Option<(f64, f64, f64, f64)>,
) -> anyhow::Result<()> {
    let surface = ImageSurface::create(Format::ARgb32, width, height)
        .context("create image surface")?;
    let cr = Context::new(&surface).context("create cairo context")?;

    cr.set_line_width(4.0);
    cr.select_font_face("sans-serif", FontSlant::Normal, FontWeight::Bold);
    cr.set_font_size(20.0);

    // Grey background
    cr.set_source_rgb(0.6, 0.6, 0.6);
    cr.paint().context("paint background")?;

    // Lighter grey: diagonals and centered square
    cr.set_source_rgb(0.7, 0.7, 0.7);
    cr.move_to(0.0, 0.0);
    cr.line_to(width as f64, height as f64);
    cr.stroke().context("stroke diagonal 1")?;
    cr.move_to(width as f64, 0.0);
    cr.line_to(0.0, height as f64);
    cr.stroke().context("stroke diagonal 2")?;
    let sq = width.min(height) as f64 / 2.0;
    cr.rectangle((width as f64 - sq) / 2.0, (height as f64 - sq) / 2.0, sq, sq);
    cr.stroke().context("stroke square")?;

    // Darker grey: dimension and aspect-ratio labels
    cr.set_source_rgb(0.45, 0.45, 0.45);
    let top = format!("{} x {}", width, height);
    let ext = cr.text_extents(&top).context("text extents (top)")?;
    // y_offset=2: y = text_height * 2  (same as Python write(text, y_offset=2))
    cr.move_to((width as f64 - ext.width()) / 2.0, ext.height() * 2.0);
    cr.show_text(&top).context("show top text")?;

    let bottom = format!("{}:1", format_aspect_ratio(width as f64 / height as f64));
    let ext = cr.text_extents(&bottom).context("text extents (bottom)")?;
    // y_offset=-1: y = height + text_height * -1  (same as Python write(text, y_offset=-1))
    cr.move_to(
        (width as f64 - ext.width()) / 2.0,
        height as f64 - ext.height(),
    );
    cr.show_text(&bottom).context("show bottom text")?;

    // Optional semi-transparent color overlay
    if let Some((r, g, b, a)) = color {
        cr.set_source_rgba(r, g, b, a);
        cr.paint().context("paint color overlay")?;
    }

    surface
        .write_to_png(writer)
        .map_err(|e| anyhow::anyhow!("write PNG: {:?}", e))?;
    Ok(())
}

/// Format a ratio as 2 significant figures without trailing zeros,
/// matching Python's `:.2g` format specifier.
fn format_aspect_ratio(ratio: f64) -> String {
    // Find the order of magnitude so we know how many decimal places to keep
    let sig_digits = 2;
    if ratio == 0.0 {
        return "0".to_string();
    }
    let mag = ratio.abs().log10().floor() as i32;
    // Decimal places needed for `sig_digits` significant figures
    let dp = (sig_digits - 1 - mag).max(0) as usize;
    let formatted = format!("{:.prec$}", ratio, prec = dp);
    // Strip trailing zeros and unnecessary decimal point (matches Python :.2g)
    if formatted.contains('.') {
        formatted
            .trim_end_matches('0')
            .trim_end_matches('.')
            .to_string()
    } else {
        formatted
    }
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_aspect_ratio_formatting() {
        assert_eq!(format_aspect_ratio(1.0), "1");
        assert_eq!(format_aspect_ratio(1.5), "1.5");
        assert_eq!(format_aspect_ratio(1.333), "1.3");
        assert_eq!(format_aspect_ratio(2.0), "2");
        assert_eq!(format_aspect_ratio(10.0), "10");
        assert_eq!(format_aspect_ratio(0.5), "0.5");
    }

    #[test]
    fn test_draw_placeholder_no_color() {
        let mut buf = Vec::new();
        draw_placeholder(&mut buf, 256, 256, None).unwrap();
        assert!(buf.starts_with(b"\x89PNG\r\n"), "output should be a PNG");
    }

    #[test]
    fn test_draw_placeholder_with_color() {
        let mut buf = Vec::new();
        draw_placeholder(&mut buf, 320, 240, Some((0.2, 0.5, 0.9, 0.5))).unwrap();
        assert!(buf.starts_with(b"\x89PNG\r\n"), "output should be a PNG");
        assert!(buf.len() >= 1000, "PNG should have meaningful size");
    }

    #[test]
    fn test_draw_placeholder_non_square() {
        let mut buf = Vec::new();
        draw_placeholder(&mut buf, 640, 320, None).unwrap();
        assert!(buf.starts_with(b"\x89PNG\r\n"));
    }
}
