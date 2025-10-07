"""Python-based renderer for converting WaveJSON to images using matplotlib."""

import json
import logging
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


class WaveRenderer:
    """Renderer for converting WaveJSON to images using matplotlib."""

    def __init__(self, skin: str = "default") -> None:
        """Initialize wave renderer.

        Args:
            skin: Rendering style/theme (currently unused, for compatibility).
        """
        self.skin = skin

    def render_to_image(self, json_file: str, image_file: str) -> int:
        """Render WaveJSON file to image.

        Args:
            json_file: Path to WaveJSON file.
            image_file: Path to output image file.

        Returns:
            Exit code (0 for success).
        """
        json_path = Path(json_file)
        image_path = Path(image_file)

        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_file}")

        logger.info(f"Rendering {json_file} to {image_file}")

        # Read WaveJSON
        with open(json_path, encoding="utf-8") as f:
            wavejson = json.load(f)

        # Parse and render the waveform
        self._render_waveform_to_image(wavejson, image_path)

        logger.info(f"Image saved to: {image_file}")
        return 0

    def render_to_html(self, json_file: str, html_file: str) -> int:
        """Render WaveJSON to HTML file (currently outputs JSON data).

        Args:
            json_file: Path to WaveJSON file.
            html_file: Path to output HTML file.

        Returns:
            Exit code (0 for success).
        """
        json_path = Path(json_file)
        html_path = Path(html_file)

        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_file}")

        logger.info(f"Generating HTML from {json_file} to {html_file}")

        # Read WaveJSON
        with open(json_path, encoding="utf-8") as f:
            wavejson = json.load(f)

        # Generate simple HTML with JSON data (for debugging/inspection)
        html_content = self._generate_html(wavejson)

        # Save HTML file
        html_path.write_text(html_content, encoding="utf-8")
        logger.info(f"HTML saved to: {html_file}")
        return 0

    def _render_waveform_to_image(self, wavejson: dict[str, Any], image_path: Path) -> None:
        """Render waveform data to image using matplotlib.

        Args:
            wavejson: Parsed WaveJSON data.
            image_path: Path to save the image.
        """
        # Parse the waveform data
        signals, time_steps = self._parse_wavejson(wavejson)

        if not signals:
            logger.warning("No signals found in WaveJSON")
            return

        # Create subplots - one for each signal
        fig, axes = plt.subplots(
            len(signals), 1,
            figsize=(12, 2 * len(signals)),
            sharex=True,
            gridspec_kw={'hspace': 0.3}
        )

        # Handle single signal case
        if len(signals) == 1:
            axes = [axes]

        # Plot each signal in its own subplot
        for i, (signal, ax) in enumerate(zip(signals, axes, strict=False)):
            self._plot_single_signal_subplot(ax, signal, time_steps, i == len(signals) - 1)

        # Set common x-axis label only on the bottom subplot
        if len(signals) > 0:
            axes[-1].set_xlabel("Time Steps")

        # Save the plot
        plt.tight_layout()
        image_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(image_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

    def _parse_wavejson(self, wavejson: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
        """Parse WaveJSON format into signal data.

        Args:
            wavejson: WaveJSON data structure.

        Returns:
            Tuple of (signals list, total time steps).
        """
        signals = []
        total_time_steps = 0

        if "signal" not in wavejson:
            return signals, total_time_steps

        signal_data = wavejson["signal"]

        for item in signal_data:
            if isinstance(item, dict) and "name" in item and "wave" in item:
                # Regular signal
                signal_info = self._parse_signal(item)
                if signal_info:
                    signals.append(signal_info)
                    total_time_steps = max(total_time_steps, len(signal_info["values"]))
            elif isinstance(item, list) and len(item) > 1:
                # Time group with multiple signals
                for sub_item in item[1:]:
                    if isinstance(sub_item, dict) and "name" in sub_item and "wave" in sub_item:
                        signal_info = self._parse_signal(sub_item)
                        if signal_info:
                            signals.append(signal_info)
                            total_time_steps = max(total_time_steps, len(signal_info["values"]))

        return signals, total_time_steps

    def _parse_signal(self, signal_dict: dict[str, Any]) -> dict[str, Any] | None:
        """Parse a single signal from WaveJSON.

        Args:
            signal_dict: Signal dictionary from WaveJSON.

        Returns:
            Parsed signal information or None if invalid.
        """
        name = signal_dict.get("name", "").strip()
        wave_str = signal_dict.get("wave", "")
        data_str = signal_dict.get("data", "")

        if not name or not wave_str:
            return None

        # Parse the wave string
        values = self._parse_wave_string(wave_str)

        # If there's data, it overrides some values
        if data_str:
            if isinstance(data_str, list):
                data_values = [str(v).strip() for v in data_str]
            else:
                data_values = [v.strip() for v in str(data_str).split()]
            data_idx = 0
            for i, val in enumerate(values):
                if val == "=":  # Data change marker
                    if data_idx < len(data_values):
                        values[i] = data_values[data_idx]
                        data_idx += 1
                    else:
                        values[i] = "x"

        return {
            "name": name,
            "values": values,
            "is_clock": "p" in wave_str
        }

    def _parse_wave_string(self, wave_str: str) -> list[str]:
        """Parse wave string into value list.

        Args:
            wave_str: Wave string (e.g., "p.....", "10x..", etc.).

        Returns:
            List of values for each time step.
        """
        values = []
        prev_value = "0"

        for char in wave_str:
            if char == ".":
                values.append(prev_value)
            elif char in ["0", "1", "x", "z", "p"]:
                values.append(char)
                prev_value = char
            elif char == "=":
                # Data change - will be replaced by data values later
                values.append("=")
            else:
                # Unknown character, treat as x
                values.append("x")
                prev_value = "x"

        return values

    def _plot_single_signal_subplot(self, ax: plt.Axes, signal: dict[str, Any], time_steps: int, is_bottom: bool) -> None:
        """Plot a single signal in its own subplot with professional digital styling.

        Args:
            ax: Matplotlib axes to plot on.
            signal: Signal information dictionary.
            time_steps: Total number of time steps.
            is_bottom: Whether this is the bottom subplot (for x-axis label).
        """
        values = signal["values"]
        signal_name = signal["name"]

        # Extend values to match time_steps if needed
        while len(values) < time_steps:
            values.append(values[-1] if values else "x")

        # Set up the subplot with professional digital styling
        ax.set_xlim(0, time_steps)
        ax.set_ylim(-0.2, 1.2)  # Tighter range for cleaner look
        ax.set_yticks([0, 1])
        ax.set_yticklabels(["0", "1"])
        ax.set_title(f"{signal_name}", fontsize=11, fontweight='bold', pad=10)
        ax.grid(True, alpha=0.15, linestyle='-', linewidth=0.8, color='lightgray')

        # Professional spine styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(2.0)
        ax.spines['bottom'].set_linewidth(2.0)
        ax.spines['left'].set_color('black')
        ax.spines['bottom'].set_color('black')

        # Remove x-axis labels except for bottom plot
        if not is_bottom:
            ax.set_xticklabels([])
            ax.set_xlabel("")

        # Get color based on signal type
        color = self._get_signal_color(signal)

        # Plot the signal with the appropriate color
        self._plot_signal_data(ax, values, time_steps, color)

    def _get_signal_color(self, signal: dict[str, Any]) -> str:
        """Get the appropriate color for a signal based on its type.

        Args:
            signal: Signal information dictionary.

        Returns:
            Color string for matplotlib plotting.
        """
        # Use name-based detection for signal type classification
        name = signal["name"].lower()

        # Input signals (blue)
        if any(keyword in name for keyword in ["input", "in", "din", "data_in", "valid_in", "ready_in"]):
            return "#1f77b4"  # Blue

        # Output signals (green)
        elif any(keyword in name for keyword in ["output", "out", "dout", "data_out", "valid_out", "ready_out"]):
            return "#2ca02c"  # Green

        # Clock signals (purple)
        elif any(keyword in name for keyword in ["clock", "clk", "ck"]):
            return "#9467bd"  # Purple

        # Reset signals (orange)
        elif any(keyword in name for keyword in ["reset", "rst", "clear", "clr"]):
            return "#ff7f0e"  # Orange

        # Default for internal/unknown signals (purple)
        else:
            return "#9467bd"  # Purple

    def _plot_signal_data(self, ax: plt.Axes, values: list[str], time_steps: int, color: str) -> None:
        """Plot signal data in the given axes with sharp digital transitions.

        Args:
            ax: Matplotlib axes to plot on.
            values: Signal values to plot.
            time_steps: Total number of time steps.
            color: Color to use for the signal.
        """
        if not values:
            return

        # Process the entire signal including special states
        for t in range(len(values)):
            val = values[t]

            if val == "p":
                # Clock pulse: plot triangular pulse
                self._plot_clock_pulse(ax, t, color)
            elif val in ["0", "1"]:
                # Regular digital signal - plot as horizontal line with sharp edges
                numeric_val = 1 if val == "1" else 0
                ax.plot([t, t + 1], [numeric_val, numeric_val], color=color, linewidth=3.0,
                       solid_capstyle='butt', solid_joinstyle='miter')
            elif val == "x":
                # Unknown state - draw with red X marks
                ax.plot([t, t + 1], [0.5, 0.5], color='red', marker='x', markersize=8,
                       linewidth=2, alpha=0.9, linestyle='-')
            elif val == "z":
                # High-Z state - draw with gray diamonds at the middle (floating)
                ax.plot([t, t + 1], [0.5, 0.5], color='gray', marker='D', markersize=6,
                       linewidth=2, alpha=0.8, linestyle='-')
            else:
                # Handle other values (like data values from multi-bit signals)
                try:
                    numeric_val = float(val) if val.replace(".", "").isdigit() else 0.5
                    ax.plot([t, t + 1], [numeric_val, numeric_val], color=color, linewidth=3.0,
                           solid_capstyle='butt', solid_joinstyle='miter')
                except (ValueError, AttributeError):
                    # Fallback for unknown characters
                    ax.plot([t, t + 1], [0.5, 0.5], color='red', marker='x', markersize=8,
                           linewidth=2, alpha=0.9, linestyle='-')

    def _plot_clock_pulse(self, ax: plt.Axes, t: int, color: str) -> None:
        """Plot a clock pulse (triangular wave) at time t.

        Args:
            ax: Matplotlib axes to plot on.
            t: Time step where the clock pulse occurs.
            color: Color to use for the clock pulse.
        """
        # Clock pulse: low->high->low with sharp transitions
        # Low segment (if not at start)
        if t > 0:
            ax.plot([t, t + 0.5], [0, 0], color=color, linewidth=3.0,
                   solid_capstyle='butt', solid_joinstyle='miter')
        # Rising edge (vertical)
        ax.plot([t + 0.5, t + 0.5], [0, 1], color=color, linewidth=3.0,
               solid_capstyle='butt', solid_joinstyle='miter')
        # High segment
        ax.plot([t + 0.5, t + 1], [1, 1], color=color, linewidth=3.0,
               solid_capstyle='butt', solid_joinstyle='miter')


    def _generate_html(self, wavejson: dict[str, Any]) -> str:
        """Generate simple HTML page displaying the WaveJSON data.

        Args:
            wavejson: WaveJSON data.

        Returns:
            HTML content as string.
        """
        json_str = json.dumps(wavejson, indent=2)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>WaveJSON Data</title>
    <style>
        body {{
            font-family: monospace;
            margin: 20px;
            background: #f5f5f5;
        }}
        .json-container {{
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
    </style>
</head>
<body>
    <h1>WaveJSON Data</h1>
    <div class="json-container">
        <pre>{json_str}</pre>
    </div>
</body>
</html>"""
        return html
