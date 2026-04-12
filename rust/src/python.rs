use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

use crate::drawing::draw_placeholder as rust_draw_placeholder;
use crate::randomcolor::{
    HsvColor as RustHsvColor, Luminosity as RustLuminosity, RandomColor as RustRandomColor,
};

fn anyhow_to_pyerr(e: anyhow::Error) -> PyErr {
    PyValueError::new_err(format!("{:#}", e))
}

/// Color luminosity level.
///
/// Can be constructed from a string (``Luminosity("bright")``) or accessed as
/// class attributes (``Luminosity.bright``).  Valid values: ``random``,
/// ``bright``, ``dark``, ``light``.
#[pyclass(name = "Luminosity")]
#[derive(Clone)]
pub struct PyLuminosity {
    inner: RustLuminosity,
}

#[pymethods]
impl PyLuminosity {
    #[new]
    fn new(value: &str) -> PyResult<Self> {
        RustLuminosity::from_str(value)
            .map(|inner| PyLuminosity { inner })
            .ok_or_else(|| {
                PyValueError::new_err(format!(
                    "Invalid luminosity {:?}; valid values: random, bright, dark, light",
                    value
                ))
            })
    }

    #[classattr]
    fn random() -> Self {
        PyLuminosity { inner: RustLuminosity::Random }
    }
    #[classattr]
    fn bright() -> Self {
        PyLuminosity { inner: RustLuminosity::Bright }
    }
    #[classattr]
    fn dark() -> Self {
        PyLuminosity { inner: RustLuminosity::Dark }
    }
    #[classattr]
    fn light() -> Self {
        PyLuminosity { inner: RustLuminosity::Light }
    }

    fn __str__(&self) -> String {
        self.inner.to_string()
    }

    fn __repr__(&self) -> String {
        format!("Luminosity({:?})", self.inner.to_string())
    }

    fn __eq__(&self, other: &PyLuminosity) -> bool {
        self.inner == other.inner
    }
}

/// A color in HSV space (h: 0-360, s: 0-100, v: 0-100).
#[pyclass(name = "HsvColor")]
#[derive(Clone)]
pub struct PyHsvColor {
    inner: RustHsvColor,
}

#[pymethods]
impl PyHsvColor {
    #[getter]
    fn h(&self) -> i32 {
        self.inner.h
    }
    #[getter]
    fn s(&self) -> i32 {
        self.inner.s
    }
    #[getter]
    fn v(&self) -> i32 {
        self.inner.v
    }

    fn hex(&self) -> String {
        self.inner.hex()
    }
    fn rgb(&self) -> (f64, f64, f64) {
        self.inner.rgb()
    }
    fn int_rgb(&self) -> (u8, u8, u8) {
        self.inner.int_rgb()
    }
    fn int_hsv(&self) -> (i32, i32, i32) {
        self.inner.int_hsv()
    }
    fn hls(&self) -> (f64, f64, f64) {
        self.inner.hls()
    }

    fn __repr__(&self) -> String {
        format!(
            "HsvColor(h={}, s={}, v={}, hex={:?})",
            self.inner.h,
            self.inner.s,
            self.inner.v,
            self.inner.hex()
        )
    }

    fn __eq__(&self, other: &PyHsvColor) -> bool {
        self.inner == other.inner
    }
}

/// Random color generator.
///
/// ``seed`` may be an ``int``, a ``str``, or ``None`` (entropy-seeded).
#[pyclass(name = "RandomColor", unsendable)]
pub struct PyRandomColor {
    inner: RustRandomColor,
}

#[pymethods]
impl PyRandomColor {
    #[new]
    #[pyo3(signature = (seed=None))]
    fn new(seed: Option<&Bound<'_, PyAny>>) -> PyResult<Self> {
        let inner = match seed {
            None => RustRandomColor::new(),
            Some(obj) => {
                if let Ok(n) = obj.extract::<u64>() {
                    RustRandomColor::with_seed(n)
                } else if let Ok(s) = obj.extract::<String>() {
                    RustRandomColor::from_str_seed(&s)
                } else {
                    return Err(PyValueError::new_err("seed must be int, str, or None"));
                }
            }
        };
        Ok(PyRandomColor { inner })
    }

    /// Generate a random color.
    ///
    /// ``hue`` is an optional color name (e.g. ``"blue"``).
    /// ``luminosity`` is an optional :class:`Luminosity` value.
    #[pyo3(signature = (hue=None, luminosity=None))]
    fn generate(
        &mut self,
        hue: Option<String>,
        luminosity: Option<PyLuminosity>,
    ) -> PyResult<PyHsvColor> {
        self.inner
            .generate(hue.as_deref(), luminosity.map(|l| l.inner))
            .map(|c| PyHsvColor { inner: c })
            .map_err(anyhow_to_pyerr)
    }
}

/// Generate a placeholder PNG image and return it as bytes.
///
/// ``color`` is an optional ``(r, g, b, a)`` tuple of floats in ``[0.0, 1.0]``
/// that overlays a semi-transparent tint on the image.
#[pyfunction]
#[pyo3(signature = (width, height, color=None))]
fn draw_placeholder(
    py: Python<'_>,
    width: i32,
    height: i32,
    color: Option<(f64, f64, f64, f64)>,
) -> PyResult<Py<PyBytes>> {
    let mut buf: Vec<u8> = Vec::new();
    rust_draw_placeholder(&mut buf, width, height, color).map_err(anyhow_to_pyerr)?;
    Ok(PyBytes::new(py, &buf).into())
}

#[pyfunction]
fn main(py: Python<'_>) {
    let argv: Vec<String> = py
        .import("sys")
        .and_then(|sys| sys.getattr("argv"))
        .and_then(|a| a.extract())
        .unwrap_or_default();
    if let Err(e) = crate::cli::run_with_args(argv) {
        eprintln!("error: {:#}", e);
        std::process::exit(1);
    }
}

#[pymodule]
fn faker_graphics_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyLuminosity>()?;
    m.add_class::<PyHsvColor>()?;
    m.add_class::<PyRandomColor>()?;
    m.add_function(wrap_pyfunction!(draw_placeholder, m)?)?;
    m.add_function(wrap_pyfunction!(main, m)?)?;
    Ok(())
}
