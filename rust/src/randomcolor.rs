use std::collections::BTreeMap;
use std::io::Read;

use rand::rngs::SmallRng;
use rand::{Rng, SeedableRng};
use serde::{Deserialize, Serialize};


// Parsed (processed) colormap entry, stored after load_colormap.
#[derive(Debug, Clone, Serialize)]
pub struct ColorEntry {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub hue_range: Option<[i32; 2]>,
    pub lower_bounds: Vec<[i32; 2]>,
    pub saturation_range: [i32; 2],
    pub brightness_range: [i32; 2],
}

// Raw JSON shape before processing.
#[derive(Deserialize)]
struct RawColorEntry {
    hue_range: Option<[i32; 2]>,
    lower_bounds: Vec<[i32; 2]>,
}

/// Color luminosity level.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Luminosity {
    Random,
    Bright,
    Dark,
    Light,
}

impl Luminosity {
    pub fn from_str(s: &str) -> Option<Self> {
        match s {
            "random" => Some(Luminosity::Random),
            "bright" => Some(Luminosity::Bright),
            "dark" => Some(Luminosity::Dark),
            "light" => Some(Luminosity::Light),
            _ => None,
        }
    }
}

impl std::fmt::Display for Luminosity {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let s = match self {
            Luminosity::Random => "random",
            Luminosity::Bright => "bright",
            Luminosity::Dark => "dark",
            Luminosity::Light => "light",
        };
        write!(f, "{}", s)
    }
}

/// A color in HSV space with integer components (h: 0-360, s: 0-100, v: 0-100).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct HsvColor {
    pub h: i32,
    pub s: i32,
    pub v: i32,
}

impl HsvColor {
    /// Normalized HSV floats (0.0-1.0 each).
    pub fn hsv(&self) -> (f64, f64, f64) {
        (self.h as f64 / 360.0, self.s as f64 / 100.0, self.v as f64 / 100.0)
    }

    /// RGB as floats (0.0-1.0 each), matching Python colorsys.hsv_to_rgb.
    pub fn rgb(&self) -> (f64, f64, f64) {
        let (h, s, v) = self.hsv();
        hsv_to_rgb(h, s, v)
    }

    /// RGB as integers (0-255 each), truncated like Python int().
    pub fn int_rgb(&self) -> (u8, u8, u8) {
        let (r, g, b) = self.rgb();
        ((r * 255.0) as u8, (g * 255.0) as u8, (b * 255.0) as u8)
    }

    /// HSV as integer tuple.
    pub fn int_hsv(&self) -> (i32, i32, i32) {
        (self.h, self.s, self.v)
    }

    /// Lowercase hex color string like "#rrggbb".
    pub fn hex(&self) -> String {
        let (r, g, b) = self.int_rgb();
        format!("#{:02x}{:02x}{:02x}", r, g, b)
    }

    /// HLS floats, matching Python colorsys.rgb_to_hls (returns h, l, s).
    pub fn hls(&self) -> (f64, f64, f64) {
        let (r, g, b) = self.rgb();
        rgb_to_hls(r, g, b)
    }
}

/// Convert HSV (all 0.0-1.0) to RGB, matching Python colorsys.hsv_to_rgb.
fn hsv_to_rgb(h: f64, s: f64, v: f64) -> (f64, f64, f64) {
    if s == 0.0 {
        return (v, v, v);
    }
    let i = (h * 6.0) as u32;
    let f = h * 6.0 - i as f64;
    let p = v * (1.0 - s);
    let q = v * (1.0 - f * s);
    let t = v * (1.0 - (1.0 - f) * s);
    match i % 6 {
        0 => (v, t, p),
        1 => (q, v, p),
        2 => (p, v, t),
        3 => (p, q, v),
        4 => (t, p, v),
        _ => (v, p, q),
    }
}

/// Convert RGB (all 0.0-1.0) to HLS, matching Python colorsys.rgb_to_hls (returns h, l, s).
fn rgb_to_hls(r: f64, g: f64, b: f64) -> (f64, f64, f64) {
    let max = r.max(g).max(b);
    let min = r.min(g).min(b);
    let l = (max + min) / 2.0;
    if (max - min).abs() < f64::EPSILON {
        return (0.0, l, 0.0);
    }
    let delta = max - min;
    let s = if l <= 0.5 {
        delta / (max + min)
    } else {
        delta / (2.0 - max - min)
    };
    let h = if (max - r).abs() < f64::EPSILON {
        (g - b) / delta + if g < b { 6.0 } else { 0.0 }
    } else if (max - g).abs() < f64::EPSILON {
        (b - r) / delta + 2.0
    } else {
        (r - g) / delta + 4.0
    } / 6.0;
    (h, l, s)
}

/// Port of randomColor.js / Python RandomColor.
pub struct RandomColor {
    pub colormap: BTreeMap<String, ColorEntry>,
    wrap_around_hue: Option<i32>,
    rng: SmallRng,
}

impl RandomColor {
    /// Create with a random (entropy-based) seed.
    pub fn new() -> Self {
        Self::with_rng(SmallRng::from_entropy())
    }

    /// Create with a fixed integer seed for reproducible output.
    pub fn with_seed(seed: u64) -> Self {
        Self::with_rng(SmallRng::seed_from_u64(seed))
    }

    /// Create with a string seed (parsed as u64, or hashed).
    pub fn from_str_seed(s: &str) -> Self {
        let seed = s.parse::<u64>().unwrap_or_else(|_| {
            // djb2-style hash
            let mut hash: u64 = 5381;
            for b in s.bytes() {
                hash = hash.wrapping_mul(33).wrapping_add(b as u64);
            }
            hash
        });
        Self::with_seed(seed)
    }

    fn with_rng(rng: SmallRng) -> Self {
        let json = include_str!("data/colormap.json");
        let (colormap, wrap_around_hue) = Self::load_colormap(json.as_bytes())
            .expect("built-in colormap is always valid");
        RandomColor { colormap, wrap_around_hue, rng }
    }

    /// Load a colormap from a JSON reader, returning the processed map and
    /// the wrap-around hue (used for the red range that crosses 0/360).
    pub fn load_colormap<R: Read>(
        reader: R,
    ) -> anyhow::Result<(BTreeMap<String, ColorEntry>, Option<i32>)> {
        let raw: BTreeMap<String, RawColorEntry> = serde_json::from_reader(reader)?;
        let mut colormap = BTreeMap::new();
        let mut wrap_around_hue: Option<i32> = None;

        for (name, mut raw_entry) in raw {
            // Normalize hue ranges that wrap around 0 (red: 346..12 -> -14..12)
            if let Some(hr) = &mut raw_entry.hue_range {
                if hr[0] > hr[1] {
                    wrap_around_hue = Some(hr[0]);
                    hr[0] -= 360;
                }
            }

            // Compute saturation/brightness ranges from sorted lower_bounds
            let mut sorted = raw_entry.lower_bounds.clone();
            sorted.sort();
            let [s_min, b_max] = sorted[0];
            let [s_max, b_min] = sorted[sorted.len() - 1];

            let mut sat = [s_min, s_max];
            sat.sort();
            let mut bri = [b_min, b_max];
            bri.sort();

            colormap.insert(
                name,
                ColorEntry {
                    hue_range: raw_entry.hue_range,
                    lower_bounds: raw_entry.lower_bounds, // keep original order
                    saturation_range: sat,
                    brightness_range: bri,
                },
            );
        }

        // Sort by hue_range start for deterministic iteration (mirrors Python sort)
        let mut sorted_colormap: BTreeMap<String, ColorEntry> = BTreeMap::new();
        let mut entries: Vec<(String, ColorEntry)> = colormap.into_iter().collect();
        entries.sort_by_key(|(_, e)| e.hue_range.map(|r| r[0]).unwrap_or(-360));
        for (k, v) in entries {
            sorted_colormap.insert(k, v);
        }

        Ok((sorted_colormap, wrap_around_hue))
    }

    /// Generate a random color.
    ///
    /// `hue` - named color, integer 0-360 as string, or None for any color.
    /// `luminosity` - optional luminosity constraint.
    pub fn generate(
        &mut self,
        hue: Option<&str>,
        luminosity: Option<Luminosity>,
    ) -> anyhow::Result<HsvColor> {
        let h = self.pick_hue(hue);
        let s = if h.is_some() {
            self.pick_saturation(h.unwrap(), luminosity)
        } else {
            0
        };
        // For monochrome (h is None), pass original hue to pick_brightness
        let b = self.pick_brightness_input(hue, h, s, luminosity);
        Ok(HsvColor { h: h.unwrap_or(0), s, v: b })
    }

    fn pick_hue(&mut self, color_input: Option<&str>) -> Option<i32> {
        let range = self.get_hue_range(color_input)?;
        let hue = self.rng.gen_range(range[0]..=range[1]);
        // Re-map negative hues (the wrapped red range) to 346-360
        Some(if hue < 0 { hue + 360 } else { hue })
    }

    fn pick_saturation(&mut self, hue: i32, luminosity: Option<Luminosity>) -> i32 {
        if luminosity == Some(Luminosity::Random) {
            return self.rng.gen_range(0..=100);
        }
        let entry = self.get_color_info_by_hue(hue).expect("hue must be valid");
        let [mut s_min, mut s_max] = entry.saturation_range;

        match luminosity {
            Some(Luminosity::Bright) => s_min = 55,
            Some(Luminosity::Dark) => s_min = s_max - 10,
            Some(Luminosity::Light) => s_max = 55,
            _ => {}
        }
        self.rng.gen_range(s_min..=s_max)
    }

    fn pick_brightness_input(
        &mut self,
        hue_str: Option<&str>,
        h: Option<i32>,
        saturation: i32,
        luminosity: Option<Luminosity>,
    ) -> i32 {
        // When h is None (monochrome), look up by the name string
        let entry = match h {
            Some(hue) => self.get_color_info_by_hue(hue).expect("hue must be valid"),
            None => {
                let name = hue_str.unwrap_or("monochrome");
                self.colormap.get(name).expect("named color must exist")
            }
        };
        // Clone what we need to avoid borrow conflicts
        let brightness_range = entry.brightness_range;
        let lower_bounds = entry.lower_bounds.clone();

        let [_, mut b_max] = brightness_range;
        let mut b_min = Self::get_minimum_brightness_from(&lower_bounds, saturation);

        match luminosity {
            Some(Luminosity::Dark) => b_max = b_min + 20,
            Some(Luminosity::Light) => b_min = (b_max + b_min) / 2,
            Some(Luminosity::Random) => {
                b_min = 0;
                b_max = 100;
            }
            _ => {}
        }
        self.rng.gen_range(b_min..=b_max)
    }

    fn get_minimum_brightness_from(lower_bounds: &[[i32; 2]], saturation: i32) -> i32 {
        for w in lower_bounds.windows(2) {
            let [s1, v1] = w[0];
            let [s2, v2] = w[1];
            if s1 <= saturation && saturation <= s2 {
                if saturation > 0 {
                    let m = (v2 - v1) / (s2 - s1);
                    let b = v1 - m * s1;
                    return m * saturation + b;
                } else {
                    return v2;
                }
            }
        }
        0
    }

    fn get_hue_range(&self, color_input: Option<&str>) -> Option<[i32; 2]> {
        let input = match color_input {
            None => return Some([0, 360]),
            Some(s) => s,
        };

        // Numeric hue: exact range
        if let Ok(n) = input.parse::<i32>() {
            if (0..=360).contains(&n) {
                return Some([n, n]);
            }
        }

        // Named color
        if let Some(entry) = self.colormap.get(input) {
            return entry.hue_range; // None for monochrome
        }

        // Unknown: full range
        Some([0, 360])
    }

    fn get_color_info_by_hue(&self, hue: i32) -> Option<&ColorEntry> {
        // Named lookup by hue value is not possible - use integer lookup
        let mut normalized = hue;
        if let Some(wrap) = self.wrap_around_hue {
            if wrap <= normalized && normalized <= 360 {
                normalized -= 360;
            }
        }
        for entry in self.colormap.values() {
            if let Some([lo, hi]) = entry.hue_range {
                if lo <= normalized && normalized <= hi {
                    return Some(entry);
                }
            }
        }
        None
    }
}

impl Default for RandomColor {
    fn default() -> Self {
        Self::new()
    }
}


#[cfg(test)]
mod tests {
    use super::*;

    fn seeded() -> RandomColor {
        RandomColor::with_seed(42)
    }

    #[test]
    fn test_generate_returns_valid_hsv() {
        let color = seeded().generate(None, None).unwrap();
        assert!((0..=360).contains(&color.h));
        assert!((0..=100).contains(&color.s));
        assert!((0..=100).contains(&color.v));
    }

    #[test]
    fn test_hue_filter() {
        // All generated colors for "pink" should fall in the pink hue range (321-345)
        let mut rc = seeded();
        for _ in 0..20 {
            let c = rc.generate(Some("pink"), None).unwrap();
            assert!(
                (321..=345).contains(&c.h),
                "pink hue {} out of range 321-345",
                c.h
            );
        }
    }

    #[test]
    fn test_luminosity_bright_saturation() {
        let mut rc = seeded();
        for _ in 0..20 {
            let c = rc.generate(Some("blue"), Some(Luminosity::Bright)).unwrap();
            // bright forces s_min >= 55
            assert!(c.s >= 55, "bright saturation {} < 55", c.s);
        }
    }

    #[test]
    fn test_monochrome_zero_saturation() {
        let mut rc = seeded();
        for _ in 0..10 {
            let c = rc.generate(Some("monochrome"), None).unwrap();
            assert_eq!(c.s, 0, "monochrome saturation should be 0");
            assert_eq!(c.h, 0, "monochrome hue should be 0");
        }
    }

    #[test]
    fn test_numeric_hue_string() {
        // "180" should produce exactly hue 180
        let mut rc = seeded();
        let c = rc.generate(Some("180"), None).unwrap();
        assert_eq!(c.h, 180);
    }

    #[test]
    fn test_hex_format() {
        let c = HsvColor { h: 0, s: 0, v: 0 };
        assert_eq!(c.hex(), "#000000");
        let c = HsvColor { h: 0, s: 0, v: 100 };
        assert_eq!(c.hex(), "#ffffff");
    }

    #[test]
    fn test_seeded_reproducible() {
        let c1 = RandomColor::with_seed(42).generate(None, None).unwrap();
        let c2 = RandomColor::with_seed(42).generate(None, None).unwrap();
        assert_eq!(c1, c2, "same seed should produce same color");
    }

    #[test]
    fn test_invalid_luminosity_string() {
        // Luminosity::from_str with an unknown value returns None
        assert!(Luminosity::from_str("invalid").is_none());
        assert!(Luminosity::from_str("bright").is_some());
    }

    #[test]
    fn test_load_colormap_processes_red_wrap() {
        let rc = seeded();
        let red = rc.colormap.get("red").unwrap();
        // After normalization: hue_range[0] should be negative (346 - 360 = -14)
        assert_eq!(red.hue_range, Some([-14, 12]));
        assert_eq!(rc.wrap_around_hue, Some(346));
    }

    #[test]
    fn test_colormap_saturation_brightness_ranges() {
        let rc = seeded();
        let blue = rc.colormap.get("blue").unwrap();
        // From the JSON: lower_bounds starts at [20, 100] and ends at [100, 35]
        assert_eq!(blue.saturation_range, [20, 100]);
        assert_eq!(blue.brightness_range, [35, 100]);
    }

    #[test]
    fn test_rgb_black_white() {
        let black = HsvColor { h: 0, s: 0, v: 0 };
        assert_eq!(black.rgb(), (0.0, 0.0, 0.0));
        assert_eq!(black.int_rgb(), (0, 0, 0));

        let white = HsvColor { h: 0, s: 0, v: 100 };
        let (r, g, b) = white.rgb();
        assert!((r - 1.0).abs() < 1e-9);
        assert!((g - 1.0).abs() < 1e-9);
        assert!((b - 1.0).abs() < 1e-9);
        assert_eq!(white.int_rgb(), (255, 255, 255));
    }
}
