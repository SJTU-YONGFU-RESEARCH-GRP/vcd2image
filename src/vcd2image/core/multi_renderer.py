"""Multi-figure renderer for generating categorized signal plots."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .categorizer import SignalCategorizer
from .models import SignalCategory
from .renderer import WaveRenderer

logger = logging.getLogger(__name__)


class MultiFigureRenderer:
    """Renderer for generating multiple figures from categorized signals."""

    def __init__(self, skin: str = "default") -> None:
        """Initialize multi-figure renderer.

        Args:
            skin: WaveDrom skin to use for rendering.
        """
        self.skin = skin
        self.categorizer = SignalCategorizer()
        self.renderer = WaveRenderer(skin)

    def render_categorized_figures(
        self, vcd_file: str, output_dir: str, base_name: str = "waveform", formats: List[str] = None
    ) -> int:
        """Render categorized figures from VCD file.

        Args:
            vcd_file: Path to VCD file.
            output_dir: Output directory for generated files.
            base_name: Base name for output files.
            formats: List of formats to generate ('png', 'svg', 'html').

        Returns:
            Exit code (0 for success).
        """
        if formats is None:
            formats = ["png"]

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Rendering categorized figures from {vcd_file}")

        # Parse and categorize all signals
        from .parser import VCDParser

        parser = VCDParser(vcd_file)
        all_signals = parser.parse_signals()
        category = self.categorizer.categorize_signals(all_signals)

        # Determine clock signal
        clock_signal = self.categorizer.suggest_clock_signal(category)
        if not clock_signal:
            logger.warning("No suitable clock signal found, using first available signal")
            all_paths = list(all_signals.keys())
            clock_signal = all_paths[0] if all_paths else None

        if not clock_signal:
            raise ValueError("No signals found in VCD file")

        # Generate figures for each category
        figures = {
            "ports": {
                "title": "Input and Output Ports",
                "signals": [clock_signal] + category.get_ports(),
                "filename": f"{base_name}_ports",
            },
            "internal": {
                "title": "Internal Signals",
                "signals": [clock_signal] + category.internal_signals,
                "filename": f"{base_name}_internal",
            },
            "all": {
                "title": "All Signals",
                "signals": [clock_signal] + category.get_ports() + category.internal_signals,
                "filename": f"{base_name}_all",
            },
        }

        for fig_name, fig_config in figures.items():
            if not fig_config["signals"] or len(fig_config["signals"]) <= 1:
                logger.warning(f"Skipping {fig_name} figure: insufficient signals")
                continue

            logger.info(f"Generating {fig_name} figure with {len(fig_config['signals'])} signals")

            # Extract signals to JSON
            json_file = output_path / f"{fig_config['filename']}.json"
            self._extract_signals_to_json(
                vcd_file, fig_config["signals"], str(json_file), all_signals
            )

            # Generate images in requested formats
            for fmt in formats:
                if fmt == "html":
                    html_file = output_path / f"{fig_config['filename']}.html"
                    self.renderer.render_to_html(str(json_file), str(html_file))
                else:
                    image_file = output_path / f"{fig_config['filename']}.{fmt}"
                    self.renderer.render_to_image(str(json_file), str(image_file))

        logger.info(f"Generated figures in {output_dir}")
        return 0

    def _extract_signals_to_json(
        self,
        vcd_file: str,
        signal_paths: List[str],
        json_file: str,
        path_dict: Optional[Dict[str, "SignalDef"]] = None,
    ) -> None:
        """Extract specified signals to JSON file.

        Args:
            vcd_file: Path to VCD file.
            signal_paths: List of signal paths to extract.
            json_file: Output JSON file path.
            path_dict: Pre-parsed signal dictionary (optional).
        """
        logger.info(f"Extracting signals: {signal_paths}")
        from .extractor import WaveExtractor

        if path_dict:
            # Use pre-filtered path dict
            filtered_dict = {path: path_dict[path] for path in signal_paths if path in path_dict}
            extractor = WaveExtractor(vcd_file, json_file, signal_paths, filtered_dict)
        else:
            extractor = WaveExtractor(vcd_file, json_file, signal_paths)

        result = extractor.execute()
        if result != 0:
            raise RuntimeError(f"Signal extraction failed with code {result}")

    def render_lazy_plot(
        self, vcd_file: str, output_file: str, max_signals_per_figure: int = 10
    ) -> int:
        """Render a lazy plot with all signals in a single organized figure.

        Args:
            vcd_file: Path to VCD file.
            output_file: Output image file path.
            max_signals_per_figure: Maximum signals per figure (for very large designs).

        Returns:
            Exit code (0 for success).
        """
        logger.info(f"Rendering lazy plot from {vcd_file}")

        # Parse and categorize all signals
        from .parser import VCDParser

        parser = VCDParser(vcd_file)
        all_signals = parser.parse_signals()
        category = self.categorizer.categorize_signals(all_signals)

        # Build organized signal list
        signal_groups = []

        # Start with clock
        clock_signal = self.categorizer.suggest_clock_signal(category)
        if clock_signal:
            signal_groups.append([clock_signal])
        else:
            # Use first available signal as clock
            all_paths = list(all_signals.keys())
            if all_paths:
                signal_groups.append([all_paths[0]])

        # Add input ports
        if category.input_ports:
            signal_groups.append(category.input_ports[:max_signals_per_figure])

        # Add output ports
        if category.output_ports:
            signal_groups.append(category.output_ports[:max_signals_per_figure])

        # Add internal signals
        if category.internal_signals:
            # Group internal signals in chunks
            for i in range(0, len(category.internal_signals), max_signals_per_figure):
                chunk = category.internal_signals[i : i + max_signals_per_figure]
                signal_groups.append(chunk)

        # Flatten for single JSON extraction
        all_signal_paths = []
        for group in signal_groups:
            all_signal_paths.extend(group)

        if len(all_signal_paths) <= 1:
            raise ValueError("Insufficient signals for plotting")

        # Extract to JSON
        json_file = output_file.replace(".png", ".json").replace(".svg", ".json")
        self._extract_signals_to_json(vcd_file, all_signal_paths, json_file, all_signals)

        # Render to image
        return self.renderer.render_to_image(json_file, output_file)
