use std::io::Write;

use anyhow::Context as _;
use clap::{Args, Parser, Subcommand};
use owo_colors::OwoColorize;

use crate::{draw_placeholder, Luminosity, RandomColor};


/// faker_graphics commandline interface.
#[derive(Parser)]
#[command(name = "fgr", version)]
struct Cli {
    /// Increase verbosity (-v for warnings, -vv for info, -vvv for debug).
    /// Currently controls whether backtraces are shown on error.
    #[arg(short, long, action = clap::ArgAction::Count, global = true)]
    verbose: u8,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Generate a placeholder PNG image.
    ///
    /// HUE can be a named color (monochrome, grey, red, orange, yellow, green,
    /// cyan, blue, purple, magenta, pink) or an integer 0-360.
    /// Pass - as OUTPUT to write to stdout.
    Image(ImageArgs),

    /// Print random color swatches in the terminal.
    ///
    /// HUE can be a named color (monochrome, grey, red, orange, yellow, green,
    /// cyan, blue, purple, magenta, pink) or an integer 0-360.
    Color(ColorArgs),

    /// Print the colormap used by the random color generator as JSON.
    Colormap,
}

#[derive(Args)]
struct ImageArgs {
    /// Output file path, or - for stdout.
    output: String,

    /// Color hue: named color or integer 0-360.
    hue: Option<String>,

    /// Image dimensions in pixels.
    #[arg(short, long, num_args = 2, value_names = ["WIDTH", "HEIGHT"],
          default_values_t = [256u32, 256u32])]
    size: Vec<u32>,

    /// Color luminosity (random, bright, dark, light).
    #[arg(short, long)]
    luminosity: Option<String>,

    /// Alpha of color overlay (0.0-1.0).
    #[arg(short = 'a', long = "alpha", default_value_t = 0.5)]
    color_alpha: f64,

    /// Custom random seed for reproducible output.
    #[arg(short = 'r', long = "random", value_name = "SEED")]
    seed: Option<String>,
}

#[derive(Args)]
struct ColorArgs {
    /// Color hue: named color or integer 0-360.
    hue: String,

    /// Number of colors to generate.
    #[arg(short, long, default_value_t = 1)]
    count: usize,

    /// Color luminosity (random, bright, dark, light).
    #[arg(short, long)]
    luminosity: Option<String>,

    /// Sort colors by hue.
    #[arg(short = 's', long = "sorted")]
    sort: bool,

    /// Custom random seed for reproducible output.
    #[arg(short = 'r', long = "random", value_name = "SEED")]
    seed: Option<String>,
}

pub fn run() -> anyhow::Result<()> {
    run_with_args(std::env::args_os())
}

pub fn run_with_args<I, T>(args: I) -> anyhow::Result<()>
where
    I: IntoIterator<Item = T>,
    T: Into<std::ffi::OsString> + Clone,
{
    let cli = Cli::parse_from(args);
    match cli.command {
        Commands::Image(args) => cmd_image(args),
        Commands::Color(args) => cmd_color(args),
        Commands::Colormap => cmd_colormap(),
    }
}

fn parse_luminosity(s: Option<&str>) -> anyhow::Result<Option<Luminosity>> {
    match s {
        None => Ok(None),
        Some(s) => Luminosity::from_str(s)
            .map(Some)
            .ok_or_else(|| anyhow::anyhow!(
                "invalid luminosity {:?}; allowed: random, bright, dark, light", s
            )),
    }
}

fn make_rng(seed: Option<&str>) -> RandomColor {
    match seed {
        Some(s) => RandomColor::from_str_seed(s),
        None => RandomColor::new(),
    }
}

fn cmd_image(args: ImageArgs) -> anyhow::Result<()> {
    let luminosity = parse_luminosity(args.luminosity.as_deref())?;
    let mut rc = make_rng(args.seed.as_deref());

    let color = rc.generate(args.hue.as_deref(), luminosity)?;
    let (r, g, b) = color.rgb();
    let overlay = Some((r, g, b, args.color_alpha));

    let width = args.size[0] as i32;
    let height = args.size[1] as i32;

    if args.output == "-" {
        let stdout = std::io::stdout();
        let mut handle = stdout.lock();
        draw_placeholder(&mut handle, width, height, overlay)
            .context("drawing placeholder to stdout")?;
    } else {
        let mut file = std::fs::File::create(&args.output)
            .with_context(|| format!("creating output file {:?}", args.output))?;
        draw_placeholder(&mut file, width, height, overlay)
            .context("drawing placeholder to file")?;
    }
    Ok(())
}

fn cmd_color(args: ColorArgs) -> anyhow::Result<()> {
    let luminosity = parse_luminosity(args.luminosity.as_deref())?;
    let mut rc = make_rng(args.seed.as_deref());

    let mut colors: Vec<_> = (0..args.count)
        .map(|_| rc.generate(Some(&args.hue), luminosity))
        .collect::<anyhow::Result<_>>()?;

    if args.sort {
        colors.sort();
    }

    let is_light = luminosity == Some(Luminosity::Light);
    let stdout = std::io::stdout();
    let mut out = stdout.lock();

    for c in &colors {
        let (r, g, b) = c.int_rgb();
        let label = format!(
            " hsv{:?} rgb{:?} {} ",
            c.int_hsv(),
            c.int_rgb(),
            c.hex()
        );
        if is_light {
            writeln!(out, "{}", label.on_truecolor(r, g, b).black())?;
        } else {
            writeln!(out, "{}", label.on_truecolor(r, g, b).white())?;
        }
    }
    Ok(())
}

fn cmd_colormap() -> anyhow::Result<()> {
    let rc = RandomColor::new();
    let json = serde_json::to_string_pretty(&rc.colormap)
        .context("serializing colormap")?;
    println!("{}", json);
    Ok(())
}
