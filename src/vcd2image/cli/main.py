"""Command-line interface for VCD to Image Converter."""

import argparse
import logging
import sys
from pathlib import Path

from ..core.extractor import WaveExtractor
from ..core.multi_renderer import MultiFigureRenderer
from ..core.renderer import WaveRenderer


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application.

    Args:
        verbose: Enable verbose logging if True.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Convert VCD files to timing diagram images via WaveJSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract signals to JSON
  vcd2image timer.vcd -o timer.json -s clock reset pulse

  # Convert JSON to image
  vcd2image timer.json -i timer.png

  # Full pipeline: VCD -> JSON -> Image
  vcd2image timer.vcd -s clock reset pulse --image timer.png

  # Auto plotting: Auto-categorize and plot all signals
  vcd2image timer.vcd --auto-plot --image timer_auto.png

  # Auto plotting: Generate multiple categorized figures
  vcd2image timer.vcd --auto-plot --plot-dir ./figures --plot-formats png svg html
        """,
    )

    parser.add_argument("input_file", type=str, help="Input VCD file or JSON file")

    parser.add_argument("-o", "--output", type=str, help="Output JSON file (when input is VCD)")

    parser.add_argument("-i", "--image", type=str, help="Output image file (PNG/SVG)")

    parser.add_argument(
        "-s", "--signals", nargs="+", help="Signal paths to extract (required for VCD input)"
    )

    parser.add_argument(
        "--start-time", type=int, default=0, help="Start time for sampling (default: 0)"
    )

    parser.add_argument(
        "--end-time", type=int, default=0, help="End time for sampling (default: 0 = until end)"
    )

    parser.add_argument(
        "--wave-chunk", type=int, default=20, help="Samples per time group (default: 20)"
    )

    parser.add_argument(
        "--format", choices=["b", "d", "u", "x", "X"], help="Display format for multi-bit signals"
    )

    parser.add_argument(
        "--list-signals", action="store_true", help="List all available signals in VCD file"
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    parser.add_argument(
        "--auto-plot", action="store_true", help="Auto-categorize and plot all signals"
    )

    parser.add_argument(
        "--plot-dir", type=str, help="Output directory for auto-plotting multiple figures"
    )

    parser.add_argument(
        "--plot-formats",
        nargs="+",
        choices=["png", "svg", "html"],
        help="Output formats for auto-plotting (default: png)",
    )

    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    return parser


def validate_args(args: argparse.Namespace) -> None:
    """Validate command-line arguments for consistency and requirements.

    Args:
        args: Parsed command-line arguments containing input/output paths,
            signal specifications, and processing parameters.

    Raises:
        ValueError: If arguments are invalid or inconsistent (e.g., missing
            required signals for VCD input, or invalid file extensions).
    """
    input_path = Path(args.input_file)

    if not input_path.exists():
        raise ValueError(f"Input file does not exist: {args.input_file}")

    if input_path.suffix.lower() == ".vcd":
        # Auto plotting mode
        if args.auto_plot or args.plot_dir:
            if args.signals:
                raise ValueError(
                    "Cannot specify signals with auto plotting (--auto-plot or --plot-dir)"
                )
            if args.output:
                raise ValueError("Cannot specify output JSON with auto plotting")
        elif not args.signals and not args.list_signals:
            raise ValueError(
                "Signal paths are required for VCD input (use -s/--signals), or use --auto-plot for automatic signal selection"
            )

    elif input_path.suffix.lower() == ".json":
        if args.signals:
            raise ValueError("Signal paths cannot be specified for JSON input")
        if args.auto_plot or args.plot_dir:
            raise ValueError("Auto plotting options are not valid for JSON input")
        if not args.image:
            raise ValueError("Image output is required for JSON input")
    else:
        raise ValueError("Input file must be .vcd or .json")

    # Validate auto plotting options
    if args.plot_dir and not args.auto_plot:
        raise ValueError("--plot-dir requires --auto-plot")
    if args.plot_formats and not (args.auto_plot or args.plot_dir):
        raise ValueError("--plot-formats requires --auto-plot or --plot-dir")


def main() -> int:
    """Main CLI entry point for VCD to Image Converter.

    Parses command-line arguments, validates them, creates configuration,
    and executes the appropriate conversion workflow (VCD->JSON or JSON->Image).

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = create_parser()
    args = parser.parse_args()

    try:
        setup_logging(args.verbose)
        validate_args(args)

        if Path(args.input_file).suffix.lower() == ".vcd":
            if args.auto_plot:
                # Auto plotting mode
                multi_renderer = MultiFigureRenderer()

                if args.plot_dir:
                    # Generate multiple categorized figures
                    formats = args.plot_formats or ["png"]
                    result = multi_renderer.render_categorized_figures(
                        vcd_file=args.input_file, output_dir=args.plot_dir, formats=formats
                    )
                    if result == 0:
                        logging.info("Generated categorized figures successfully")
                else:
                    # Generate single auto plot
                    if not args.image:
                        raise ValueError("Image output required for auto plotting (use -i/--image)")
                    result = multi_renderer.render_lazy_plot(
                        vcd_file=args.input_file, output_file=args.image
                    )
                    if result == 0:
                        logging.info(f"Created auto plot: {args.image}")

            else:
                # Traditional VCD to JSON conversion
                extractor = WaveExtractor(
                    vcd_file=args.input_file,
                    json_file=args.output or "",
                    path_list=args.signals or [],
                )

                extractor.wave_chunk = args.wave_chunk
                extractor.start_time = args.start_time
                extractor.end_time = args.end_time

                if args.format:
                    for signal in args.signals:
                        extractor.wave_format(signal, args.format)

                if args.list_signals:
                    extractor.print_props()
                else:
                    extractor.execute()
                    json_file = args.output or args.input_file.replace(".vcd", ".json")
                    logging.info(f"Created WaveJSON file: {json_file}")

                    if args.image:
                        # Convert JSON to image
                        renderer = WaveRenderer()
                        renderer.render_to_image(json_file, args.image)
                        logging.info(f"Created image file: {args.image}")

        else:
            # JSON to image conversion
            renderer = WaveRenderer()
            renderer.render_to_image(args.input_file, args.image)
            logging.info(f"Created image file: {args.image}")

        return 0

    except Exception as e:
        logging.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
