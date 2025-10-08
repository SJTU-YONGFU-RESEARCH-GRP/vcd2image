"""Multi-figure renderer for generating categorized signal plots."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .categorizer import SignalCategorizer
from .extractor import WaveExtractor
from .models import SignalDef
from .parser import VCDParser
from .renderer import WaveRenderer
from .signal_plotter import SignalPlotter

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class MultiFigureRenderer:
    """Renderer for generating multiple figures from categorized signals."""

    def __init__(self, skin: str = "default") -> None:
        """Initialize multi-figure renderer.

        Args:
            skin: Rendering style/theme (currently unused, for compatibility).
        """
        self.skin = skin
        self.categorizer = SignalCategorizer()
        self.renderer = WaveRenderer(skin)

    def render_categorized_figures(
        self,
        vcd_file: str,
        output_dir: str,
        base_name: str = "waveform",
        formats: list[str] | None = None,
        verilog_file: str | None = None,
    ) -> int:
        """Render enhanced categorized figures using SignalPlotter with golden references.

        Args:
            vcd_file: Path to VCD file.
            output_dir: Output directory for generated files.
            base_name: Base name for output files.
            formats: List of formats to generate ('png', 'svg', 'html').
            verilog_file: Optional Verilog file for enhanced categorization.

        Returns:
            Exit code (0 for success).
        """
        if formats is None:
            formats = ["png"]

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Rendering enhanced categorized figures from {vcd_file}")

        try:
            # Use enhanced SignalPlotter for better styling
            plotter = SignalPlotter(
                vcd_file=vcd_file, verilog_file=verilog_file, output_dir=output_dir
            )

            # Load and categorize data
            if not plotter.load_data():
                logger.error("Failed to load VCD data")
                return 1

            if not plotter.categorize_signals():
                logger.error("Failed to categorize signals")
                return 1

            # Generate enhanced categorized plots
            self._generate_enhanced_categorized_plots(plotter, output_path, base_name, formats)

            logger.info(f"Generated enhanced categorized figures in {output_dir}")
            return 0

        except Exception as e:
            logger.error(f"Error in enhanced categorized plotting: {e}")
            return 1

    def _generate_enhanced_categorized_plots(
        self, plotter: "SignalPlotter", output_path: Path, base_name: str, formats: list[str]
    ) -> None:
        """Generate enhanced categorized plots using SignalPlotter."""

        # The SignalPlotter already has categorized signals, use them directly
        if not plotter.categories:
            logger.warning("No categorized signals available")
            return

        category = plotter.categories

        # Determine clock signal for reference from available categorized signals
        clock_signals = [s for s in category.inputs if "clock" in s.lower() or "clk" in s.lower()]
        reset_signals = [s for s in category.inputs if "reset" in s.lower() or "rst" in s.lower()]

        # Use the first available clock signal (they should already be filtered to top-level)
        clock_signal = clock_signals[0] if clock_signals else None

        # Generate figures for each category with enhanced styling
        category_configs = [
            ("clocks", "Clock Signals", clock_signals),
            ("resets", "Reset Signals", reset_signals),
            (
                "inputs",
                "Input Ports",
                [s for s in category.inputs if s not in clock_signals and s not in reset_signals],
            ),
            ("outputs", "Output Ports", category.outputs),
            ("internals", "Internal Signals", category.internals),
        ]

        for category_name, title, signals in category_configs:
            if not signals:
                logger.warning(f"No signals found for {category_name} category")
                continue

            # Add clock signal if available
            plot_signals = [clock_signal] + signals if clock_signal else signals

            if len(plot_signals) <= 1:
                logger.warning(f"Skipping {category_name} figure: insufficient signals")
                continue

            logger.info(
                f"Generating enhanced {category_name} figure with {len(plot_signals)} signals"
            )

            # Create enhanced plot using SignalPlotter
            plotter._create_enhanced_signal_plot(
                plot_signals,
                f"{title} (Enhanced)",
                f"{base_name}_{category_name}.png",
                color="mixed",  # Use mixed colors for categorized plots
            )

            # Generate additional formats if requested
            for fmt in formats:
                if fmt == "svg":
                    # For SVG, we'd need to implement SVG export in SignalPlotter
                    logger.info(f"SVG format requested for {category_name} but not yet implemented")
                elif fmt == "html":
                    # For HTML, we'd need to implement HTML export in SignalPlotter
                    logger.info(
                        f"HTML format requested for {category_name} but not yet implemented"
                    )

            # Generate JSON file for this category
            self._generate_category_json(plotter, category_name, signals, output_path)

    def _generate_category_json(
        self, plotter: "SignalPlotter", category_name: str, signals: list[str], output_path: Path
    ) -> None:
        """Generate JSON file for a specific signal category.

        Args:
            plotter: The SignalPlotter instance with VCD data
            category_name: Name of the signal category
            signals: List of signal paths in this category
            output_path: Base output directory path
        """
        if not signals:
            logger.warning(
                f"No signals found for {category_name} category, skipping JSON generation"
            )
            return

        try:
            # Create JSON file path in plots subdirectory
            json_file = output_path / "plots" / f"{category_name}.json"

            # Get suggested clock signal for sampling from the original categorizer results
            from .categorizer import SignalCategorizer

            parser = VCDParser(str(plotter.vcd_file))
            signal_dict = parser.parse_signals()
            categorizer = SignalCategorizer()
            original_category = categorizer.categorize_signals(signal_dict)
            clock_signal = categorizer.suggest_clock_signal(original_category)

            # Prepare signals list with clock as first element for WaveExtractor
            # WaveExtractor expects first signal to be clock for sampling
            if clock_signal and clock_signal not in signals:
                signals_with_clock = [clock_signal] + signals
            else:
                signals_with_clock = signals

            # Use WaveExtractor to generate JSON for these specific signals
            extractor = WaveExtractor(str(plotter.vcd_file), str(json_file), signals_with_clock)

            # Set some basic parameters
            extractor.start_time = 0
            extractor.end_time = 0  # Extract full range

            result = extractor.execute()

            if result == 0 and json_file.exists():
                logger.info(f"Generated JSON file for {category_name}: {json_file}")
            else:
                logger.warning(
                    f"Failed to generate JSON for {category_name}: WaveExtractor returned {result}"
                )

        except Exception as e:
            logger.warning(f"Failed to generate JSON for {category_name}: {e}")

    def render_enhanced_plots_with_golden_references(
        self, vcd_file: str, verilog_file: str | None = None, output_dir: str = "enhanced_plots"
    ) -> int:
        """Render enhanced plots with golden references using SignalPlotter.

        Args:
            vcd_file: Path to VCD file.
            verilog_file: Optional path to Verilog file for enhanced categorization.
            output_dir: Output directory for enhanced plots.

        Returns:
            Exit code (0 for success).
        """
        try:
            logger.info(f"Rendering enhanced plots with golden references from {vcd_file}")

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Step 1: Create SignalPlotter and generate enhanced plots directly from VCD
            logger.info("Generating enhanced plots with golden references...")
            plotter = SignalPlotter(
                vcd_file=vcd_file, verilog_file=verilog_file, output_dir=str(output_path)
            )

            # Load and categorize data
            if not plotter.load_data():
                logger.error("Failed to load VCD data")
                return 1

            if not plotter.categorize_signals():
                logger.error("Failed to categorize signals")
                return 1

            # Generate all 4 types of plots
            if not plotter.generate_plots():
                logger.error("Failed to generate plots")
                return 1

            logger.info("Generated 4 types of enhanced plots:")
            logger.info("  - input_ports.png")
            logger.info("  - output_ports.png")
            logger.info("  - all_ports.png")
            logger.info("  - all_signals.png")

            # Step 3: Generate comprehensive report
            logger.info("Generating comprehensive analysis report...")
            report = plotter.generate_summary_report()

            # Save report to file
            report_file = output_path / "signal_analysis_report.md"
            with open(report_file, "w") as f:
                f.write(report)

            logger.info(f"Generated comprehensive report: {report_file}")

            logger.info("Enhanced plotting with golden references completed successfully")
            return 0

        except Exception as e:
            logger.error(f"Error in enhanced plotting: {e}")
            return 1

    def _extract_signals_to_json(
        self,
        vcd_file: str,
        signal_paths: list[str],
        json_file: str,
        path_dict: dict[str, "SignalDef"] | None = None,
    ) -> None:
        """Extract specified signals to JSON file.

        Args:
            vcd_file: Path to VCD file.
            signal_paths: List of signal paths to extract.
            json_file: Output JSON file path.
            path_dict: Pre-parsed signal dictionary (optional).
        """
        logger.info(f"Extracting signals: {signal_paths}")

        if path_dict:
            # Use pre-filtered path dict
            filtered_dict = {path: path_dict[path] for path in signal_paths if path in path_dict}
            extractor = WaveExtractor(vcd_file, json_file, signal_paths, filtered_dict)
        else:
            extractor = WaveExtractor(vcd_file, json_file, signal_paths)

        result = extractor.execute()
        if result != 0:
            raise RuntimeError(f"Signal extraction failed with code {result}")

    def render_auto_plot(
        self, vcd_file: str, output_file: str, max_signals_per_figure: int = 10
    ) -> int:
        """Render an auto plot with all signals in a single organized figure using enhanced plotting.

        Args:
            vcd_file: Path to VCD file.
            output_file: Output image file path.
            max_signals_per_figure: Maximum signals per figure (for very large designs).

        Returns:
            Exit code (0 for success).
        """
        logger.info(f"Rendering enhanced auto plot from {vcd_file}")

        try:
            # Use enhanced SignalPlotter for better styling
            plotter = SignalPlotter(
                vcd_file=vcd_file,
                verilog_file=None,
                output_dir=".",  # No Verilog file for basic auto plotting
            )

            # Load and categorize data
            if not plotter.load_data():
                logger.error("Failed to load VCD data")
                return 1

            if not plotter.categorize_signals():
                logger.error("Failed to categorize signals")
                return 1

            # Get all signals in organized order
            if plotter.categories is None:
                logger.error("Signal categories not available after categorization")
                return 1

            all_signals = plotter.categories.all_signals

            if len(all_signals) <= 1:
                raise ValueError("Insufficient signals for plotting")

            # Use enhanced plotting for the single organized figure
            plotter._create_enhanced_signal_plot(
                all_signals, "Auto Plot (Enhanced)", Path(output_file).name, color="mixed"
            )

            logger.info(f"Created enhanced auto plot: {output_file}")
            return 0

        except Exception as e:
            logger.error(f"Error in enhanced auto plotting: {e}")
            return 1
