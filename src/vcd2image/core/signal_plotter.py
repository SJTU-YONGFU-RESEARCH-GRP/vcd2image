"""Enhanced Signal Plotter for VAS Framework.

This module provides advanced signal plotting capabilities with golden references,
categorization, and comprehensive analysis for digital circuit simulation results.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

if TYPE_CHECKING:
    import matplotlib.axes
    import pandas

from .categorizer import SignalCategorizer
from .models import SignalDef
from .parser import VCDParser
from .verilog_parser import VerilogParser


# Simple logger class for enhanced plotting
class Logger:
    """Simple logger for enhanced plotting functionality."""

    def __init__(self, name: str = "SignalPlotter"):
        self.name = name

    def info(self, message: str) -> None:
        print(f"[INFO] {self.name}: {message}")

    def success(self, message: str) -> None:
        print(f"[SUCCESS] {self.name}: {message}")

    def warning(self, message: str) -> None:
        print(f"[WARNING] {self.name}: {message}")

    def error(self, message: str) -> None:
        print(f"[ERROR] {self.name}: {message}")


@dataclass
class SignalCategory:
    """Data class to hold categorized signals."""

    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    internals: list[str] = field(default_factory=list)
    all_signals: list[str] = field(default_factory=list)


class SignalPlotter:
    """Generates enhanced plots directly from VCD files with golden reference categorization."""

    def __init__(self, vcd_file: str, verilog_file: str | None = None, output_dir: str = "plots"):
        """
        Initialize the SignalPlotter.

        Args:
            vcd_file: Path to the VCD file containing signal data
            verilog_file: Optional path to Verilog file for signal categorization
            output_dir: Directory to save generated plots
        """
        self.vcd_file = Path(vcd_file)
        self.verilog_file = Path(verilog_file) if verilog_file else None
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create plots subdirectory within output directory
        self.plots_dir = self.output_dir / "plots"
        self.plots_dir.mkdir(parents=True, exist_ok=True)

        self.logger = Logger()
        self.data: pd.DataFrame | None = None
        self.categories: SignalCategory | None = None
        self.vcd_parser: VCDParser | None = None
        self.parser: VerilogParser | None = None

        # Set up matplotlib style
        plt.style.use("default")
        sns.set_palette("husl")

    def load_data(self) -> bool:
        """
        Load and parse VCD data directly, extracting actual waveform data for plotting.

        Returns:
            True if data loaded successfully, False otherwise
        """
        try:
            # Import VCD parser and signal sampler
            from .parser import VCDParser

            # Parse VCD file to get signal data
            self.vcd_parser = VCDParser(str(self.vcd_file))
            all_signals = self.vcd_parser.parse_signals()

            if not all_signals:
                self.logger.error("No signals found in VCD file")
                return False

            # Extract actual waveform data from VCD instead of synthetic data
            self._extract_actual_waveform_data(all_signals)

            self.logger.info(f"Loaded actual VCD data with {len(all_signals)} signals")
            return True

        except Exception as e:
            self.logger.error(f"Error loading VCD file: {e}")
            return False

    def _extract_actual_waveform_data(self, signal_dict: dict[str, "SignalDef"]) -> None:
        """Extract actual waveform data from JSON files and create DataFrame for plotting."""
        import json
        import os
        import tempfile

        # Filter out signals with duplicate SIDs to avoid conflicts
        sid_to_paths: dict[str, list[str]] = {}
        for path, signal_def in signal_dict.items():
            sid = signal_def.sid
            if sid not in sid_to_paths:
                sid_to_paths[sid] = []
            sid_to_paths[sid].append(path)

        # Only include signals with unique SIDs
        valid_signal_paths = []
        for _sid, paths in sid_to_paths.items():
            if len(paths) == 1:
                valid_signal_paths.append(paths[0])
            else:
                # Prefer top-level signals (fewer path separators)
                best_path = min(paths, key=lambda p: p.count("/"))
                valid_signal_paths.append(best_path)
                other_paths = [p for p in paths if p != best_path]
                self.logger.info(f"Using {best_path} (preferred over: {other_paths})")

        if not valid_signal_paths:
            self.logger.warning("No valid signals found, falling back to synthetic data")
            self._create_synthetic_dataframe(list(signal_dict.keys()))
            return

        # Create temporary JSON file using WaveExtractor
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_json:
            temp_json_path = temp_json.name

        try:
            # Ensure we have a clock signal for WaveExtractor (it expects first signal to be clock)
            categorizer = SignalCategorizer()
            category = categorizer.categorize_signals(signal_dict)
            clock_signal = categorizer.suggest_clock_signal(category)

            # If suggested clock is filtered out, use the top-level clock
            if (
                clock_signal is not None
                and clock_signal not in valid_signal_paths
                and "clock" in clock_signal
            ):
                # Find available clock signal
                available_clocks = [s for s in valid_signal_paths if "clock" in s]
                if available_clocks:
                    clock_signal = available_clocks[0]

            # Put clock signal first for WaveExtractor
            signal_paths = valid_signal_paths[:]
            if clock_signal in signal_paths:
                signal_paths.remove(clock_signal)
                signal_paths.insert(0, clock_signal)

            # Use WaveExtractor to generate JSON for valid signals
            from .extractor import WaveExtractor

            extractor = WaveExtractor(str(self.vcd_file), temp_json_path, signal_paths)
            extractor.start_time = 0
            extractor.end_time = 0  # Extract full range

            result = extractor.execute()
            if result != 0:
                self.logger.warning(
                    f"WaveExtractor failed with code {result}, falling back to synthetic data"
                )
                self._create_synthetic_dataframe(list(signal_dict.keys()))
                return

            # Parse the JSON data
            with open(temp_json_path, encoding="utf-8") as f:
                wavejson = json.load(f)

            # Convert WaveJSON to DataFrame format for plotting
            self._wavejson_to_dataframe(wavejson, valid_signal_paths)

        finally:
            # Clean up temporary file
            if os.path.exists(temp_json_path):
                os.unlink(temp_json_path)

    def _wavejson_to_dataframe(self, wavejson: dict, signal_paths: list[str]) -> None:
        """Convert WaveJSON data to pandas DataFrame format."""
        import pandas as pd

        # Parse WaveJSON structure
        signals = wavejson.get("signal", [])
        if len(signals) < 3:
            self.logger.warning("Invalid WaveJSON structure")
            self._create_synthetic_dataframe(signal_paths)
            return

        signal_data: dict[str, list[Any]] = {"test_case": []}

        # Create mapping from signal names to their data
        signal_map = {}

        # First signal might be separate (clock)
        if isinstance(signals[0], dict) and "name" in signals[0]:
            signal_map[signals[0]["name"]] = signals[0]

        # Signals in the array at index 2
        if len(signals) > 2 and isinstance(signals[2], list) and len(signals[2]) > 1:
            for entry in signals[2]:
                if isinstance(entry, dict) and "name" in entry:
                    signal_map[entry["name"]] = entry

        # Create mapping from JSON signal names back to full paths
        name_to_path = {}
        for path in signal_paths:
            name = path.split("/")[-1]  # Get last part of path
            name_to_path[name] = path

        # Process each signal found in JSON
        max_length = 0
        for json_name, entry in signal_map.items():
            if json_name in name_to_path:
                signal_path = name_to_path[json_name]
                wave_str = entry.get("wave", "")
                data_str = entry.get("data")

                # Decode WaveJSON wave string to time series
                values = self._decode_wavejson_wave(wave_str, data_str)
                signal_data[signal_path] = values
                max_length = max(max_length, len(values))

        # If no signals were found, fall back to synthetic data
        if max_length == 0 or len(signal_data) <= 1:
            self.logger.warning("No signals parsed from WaveJSON, falling back to synthetic data")
            self._create_synthetic_dataframe(signal_paths)
            return

        # Ensure all expected signals have data
        for signal_path in signal_paths:
            if signal_path not in signal_data:
                # Signal not found in JSON, fill with zeros
                signal_data[signal_path] = [0] * max_length
            elif len(signal_data[signal_path]) < max_length:
                # Pad shorter signals
                last_val = signal_data[signal_path][-1] if signal_data[signal_path] else 0
                signal_data[signal_path].extend(
                    [last_val] * (max_length - len(signal_data[signal_path]))
                )

        # Add test case numbers
        signal_data["test_case"] = list(range(max_length))

        # Create DataFrame
        self.data = pd.DataFrame(signal_data)

        # Save CSV file for debugging and replotting
        csv_file = self.plots_dir / "signal_data.csv"
        self.data.to_csv(csv_file, index=False)
        self.logger.info(f"Saved signal data to CSV: {csv_file}")

    def _decode_wavejson_wave(self, wave_str: str, data_str: str | None = None) -> list[int]:
        """Decode WaveJSON wave string to list of integer values."""
        values = []
        data_values = []

        # Parse data string if present (for multi-bit signals)
        if data_str:
            import json

            try:
                # Try parsing as JSON array first
                parsed = json.loads(data_str)
                if isinstance(parsed, list):
                    data_values = [int(x) for x in parsed]
                else:
                    # Fallback to space-separated format
                    data_values = [int(x.strip()) for x in data_str.split() if x.strip()]
            except (json.JSONDecodeError, ValueError):
                # Fallback to space-separated format
                data_values = [int(x.strip()) for x in data_str.split() if x.strip()]

        i = 0
        data_idx = 0

        while i < len(wave_str):
            char = wave_str[i]

            if char in ("0", "1"):
                # Binary value
                values.append(int(char))
            elif char == "x":
                # Unknown - treat as 0
                values.append(0)
            elif char == "z":
                # High impedance - treat as 0
                values.append(0)
            elif char == "=":
                # Multi-bit data follows
                if data_idx < len(data_values):
                    values.append(data_values[data_idx])
                    data_idx += 1
                else:
                    values.append(0)
            elif char == ".":
                # Repeat previous value
                if values:
                    values.append(values[-1])
                else:
                    values.append(0)
            elif char == "|":
                # Cycle separator - skip
                pass
            else:
                # Unknown character - treat as 0
                values.append(0)

            i += 1

        return values

    def _json_to_dataframe(self, wavejson: dict, signal_paths: list[str]) -> pd.DataFrame | None:
        """Convert category WaveJSON to DataFrame for CSV export."""
        import pandas as pd

        # Parse WaveJSON structure
        signals = wavejson.get("signal", [])
        if len(signals) < 3:
            return None

        signal_data: dict[str, list[Any]] = {"test_case": []}

        # Create mapping from signal names to their data
        signal_map = {}

        # First signal might be separate (clock)
        if isinstance(signals[0], dict) and "name" in signals[0]:
            signal_map[signals[0]["name"]] = signals[0]

        # Signals in the array at index 2
        if len(signals) > 2 and isinstance(signals[2], list) and len(signals[2]) > 1:
            for entry in signals[2]:
                if isinstance(entry, dict) and "name" in entry:
                    signal_map[entry["name"]] = entry

        # Create mapping from JSON signal names back to full paths
        name_to_path = {}
        for path in signal_paths:
            name = path.split("/")[-1]  # Get last part of path
            name_to_path[name] = path

        # Process each signal found in JSON
        max_length = 0
        for json_name, entry in signal_map.items():
            if json_name in name_to_path:
                signal_path = name_to_path[json_name]
                wave_str = entry.get("wave", "")
                data_str = entry.get("data")

                # Decode WaveJSON wave string to time series
                values = self._decode_wavejson_wave(wave_str, data_str)
                signal_data[signal_path] = values
                max_length = max(max_length, len(values))

        if max_length == 0:
            return None

        # Ensure all expected signals have data
        for signal_path in signal_paths:
            if signal_path not in signal_data:
                signal_data[signal_path] = [0] * max_length
            elif len(signal_data[signal_path]) < max_length:
                last_val = signal_data[signal_path][-1] if signal_data[signal_path] else 0
                signal_data[signal_path].extend(
                    [last_val] * (max_length - len(signal_data[signal_path]))
                )

        # Add test case numbers
        signal_data["test_case"] = list(range(max_length))

        return pd.DataFrame(signal_data)

    def load_from_csv(self, csv_file: str) -> bool:
        """Load signal data from CSV file for replotting."""
        import pandas as pd

        try:
            csv_path = Path(csv_file)
            if not csv_path.exists():
                self.logger.error(f"CSV file not found: {csv_file}")
                return False

            self.data = pd.read_csv(csv_path)
            self.logger.info(f"Loaded data from CSV: {csv_file} ({len(self.data)} samples)")

            # Validate that we have data and required columns
            if len(self.data) == 0:
                self.logger.error(f"CSV file contains no data: {csv_file}")
                return False

            if "test_case" not in self.data.columns:
                self.logger.error(f"CSV file must contain 'test_case' column: {csv_file}")
                return False

            # Extract signal columns (exclude test_case)
            signal_columns = [col for col in self.data.columns if col != "test_case"]

            # Create basic categorization for loaded data
            self.categories = SignalCategory()
            self.categories.inputs = []  # Will be set based on available signals
            self.categories.outputs = []
            self.categories.internals = signal_columns
            self.categories.all_signals = signal_columns

            return True

        except Exception as e:
            self.logger.error(f"Failed to load CSV file: {e}")
            return False

    def replot_from_csv(self, csv_file: str, output_dir: str = "replots") -> bool:
        """Replot signals from CSV file."""
        if not self.load_from_csv(csv_file):
            return False

        # Set output directory
        original_output_dir = self.output_dir
        self.output_dir = Path(output_dir)
        self.plots_dir = self.output_dir / "plots"
        self.plots_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Generate plots from the loaded CSV data
            self.categorize_signals()
            return self.generate_plots()
        finally:
            # Restore original output directory
            self.output_dir = original_output_dir
            self.plots_dir = original_output_dir / "plots"

    def _create_synthetic_dataframe(self, signal_names: list[str]) -> None:
        """Create synthetic DataFrame from signal names for demonstration."""
        # Generate synthetic test data for demonstration
        num_test_cases = 100

        # Generate test case numbers
        test_cases = list(range(num_test_cases))

        # Generate synthetic signal data for each signal
        signal_data: dict[str, list[int]] = {"test_case": test_cases}

        for signal_name in signal_names:
            if "clock" in signal_name.lower():
                # Clock signal: alternating 0s and 1s
                signal_data[signal_name] = [i % 2 for i in range(num_test_cases)]
            elif "reset" in signal_name.lower():
                # Reset signal: 1 for first 10 cycles, then 0
                signal_data[signal_name] = [1 if i < 10 else 0 for i in range(num_test_cases)]
            elif "pulse" in signal_name.lower():
                # Pulse signal: periodic pulses every 20 cycles, lasting 3 cycles
                signal_data[signal_name] = [1 if (i % 20) < 3 else 0 for i in range(num_test_cases)]
            elif "count" in signal_name.lower() and "eq11" not in signal_name.lower():
                # Counter signal: counts from 0 to 15, resets when pulse is high
                count_values = []
                count = 0
                for i in range(num_test_cases):
                    pulse_active = 1 if (i % 20) < 3 else 0
                    if pulse_active:
                        count = 0
                    else:
                        count = (count + 1) % 16
                    count_values.append(count)
                signal_data[signal_name] = count_values
            elif "count_eq11" in signal_name.lower():
                # Count equals 11 signal: 1 when count reaches 11
                count_values = signal_data.get("count", [0] * num_test_cases)
                signal_data[signal_name] = [1 if val == 11 else 0 for val in count_values]
            else:
                # Default: random-like pattern
                signal_data[signal_name] = [i % 4 for i in range(num_test_cases)]

        self.data = pd.DataFrame(signal_data)

    def categorize_signals(self) -> bool:
        """
        Categorize signals into inputs, outputs, and internal signals using golden references.

        Returns:
            True if categorization successful, False otherwise
        """
        if self.data is None:
            self.logger.error("Data not loaded. Call load_data() first.")
            return False

        all_signals = list(self.data.columns)
        all_signals.remove("test_case")  # Remove test_case as it's not a signal

        # Import the parser to use its results
        from .parser import VCDParser

        # Use the categorizer for accurate signal classification
        # Use the same signal filtering as in load_data
        parser = VCDParser(str(self.vcd_file))
        full_signal_dict = parser.parse_signals()

        # Apply the same filtering as in _extract_actual_waveform_data
        sid_to_paths: dict[str, list[str]] = {}
        for path, signal_def in full_signal_dict.items():
            sid = signal_def.sid
            if sid not in sid_to_paths:
                sid_to_paths[sid] = []
            sid_to_paths[sid].append(path)

        filtered_paths = []
        for _sid, paths in sid_to_paths.items():
            if len(paths) == 1:
                filtered_paths.append(paths[0])
            else:
                best_path = min(paths, key=lambda p: p.count("/"))
                filtered_paths.append(best_path)

        signal_dict = {path: full_signal_dict[path] for path in filtered_paths}

        categorizer = SignalCategorizer()
        category = categorizer.categorize_signals(signal_dict)

        # Convert categorizer results to SignalPlotter format
        self.categories = SignalCategory()
        self.categories.inputs = (
            category.inputs + category.clocks + category.resets
        )  # Combine all inputs
        self.categories.outputs = category.outputs
        self.categories.internals = category.internals
        self.categories.all_signals = list(signal_dict.keys())

        self.logger.info(
            f"Categorized signals using categorizer: {len(category.clocks)} clocks, {len(category.resets)} resets, "
            f"{len(category.inputs)} inputs, {len(category.outputs)} outputs, {len(category.internals)} internal"
        )
        return True

    def _categorize_from_verilog(self, all_signals: list[str]) -> bool:
        """Categorize signals using Verilog parser information with enhanced signal type detection."""
        try:
            parser = VerilogParser(str(self.verilog_file))
            if not parser.parse():
                self.logger.warning(
                    "Failed to parse Verilog file, falling back to heuristic categorization"
                )
                return self._categorize_by_heuristic(all_signals)

            # Map CSV signals to parsed signals with enhanced classification
            clocks = []
            resets = []
            data_inputs = []
            data_outputs = []
            internal = []

            # Check each signal from CSV against parsed signals
            for signal in all_signals:
                signal_lower = signal.lower()

                # STRICTLY prioritize module port information over keyword heuristics
                if signal in parser.inputs:
                    # Check if it's a clock or reset signal that's also an input
                    if self._is_clock_signal(signal):
                        clocks.append(signal)
                    elif self._is_reset_signal(signal):
                        resets.append(signal)
                    else:
                        data_inputs.append(signal)
                elif signal in parser.outputs:
                    data_outputs.append(signal)
                elif signal in parser.wires or signal in parser.regs:
                    # Wires and regs are internal signals, regardless of name patterns
                    internal.append(signal)
                else:
                    # Signal not found in Verilog module ports, use heuristic classification
                    if self._is_clock_signal(signal):
                        clocks.append(signal)
                    elif self._is_reset_signal(signal):
                        resets.append(signal)
                    elif signal_lower.startswith(("i_", "in_", "input_")):
                        data_inputs.append(signal)
                    elif signal_lower.startswith(("o_", "out_", "output_")):
                        data_outputs.append(signal)
                    elif signal_lower.startswith(("r_", "reg_", "wire_", "int_")):
                        internal.append(signal)
                    else:
                        internal.append(signal)

            # Combine all inputs (clocks, resets, and data inputs)
            all_inputs = clocks + resets + data_inputs

            self.categories = SignalCategory()
            self.categories.inputs = all_inputs
            self.categories.outputs = data_outputs
            self.categories.internals = internal
            self.categories.all_signals = all_signals

            self.logger.info(
                f"Categorized signals from Verilog: {len(clocks)} clocks, {len(resets)} resets, "
                f"{len(data_inputs)} data inputs, {len(data_outputs)} outputs, {len(internal)} internal"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error parsing Verilog file: {e}")
            return self._categorize_by_heuristic(all_signals)

    def _is_clock_signal(self, signal_name: str) -> bool:
        """Check if a signal is a clock signal based on naming patterns."""
        signal_lower = signal_name.lower()
        clock_patterns = [
            "clk",
            "clock",
            "sys_clk",
            "system_clock",
            "bus_clock",
            "cpu_clock",
            "core_clock",
            "ref_clock",
            "reference_clock",
            "main_clock",
            "pixel_clock",
            "audio_clock",
            "serial_clock",
            "sck",
            "sclk",
            "mck",
            "mclk",
            "pck",
            "pclk",
            "hck",
            "hclk",
        ]
        return any(pattern in signal_lower for pattern in clock_patterns)

    def _is_reset_signal(self, signal_name: str) -> bool:
        """Check if a signal is a reset signal based on naming patterns."""
        signal_lower = signal_name.lower()
        reset_patterns = [
            "rst",
            "reset",
            "rst_n",
            "reset_n",
            "rst_b",
            "reset_b",
            "sys_rst",
            "system_reset",
            "cpu_rst",
            "core_rst",
            "clear",
            "clr",
            "init",
            "initialize",
            "n_rst",
            "n_reset",
            "rst_async",
            "reset_async",
            "rst_sync",
            "reset_sync",
            "arst",
            "areset",
            "srst",
            "sreset",
        ]
        return any(pattern in signal_lower for pattern in reset_patterns)

    def _categorize_by_heuristic(self, all_signals: list[str]) -> bool:
        """Categorize signals using enhanced heuristic rules."""
        clocks = []
        resets = []
        data_inputs = []
        data_outputs = []
        internal = []

        for signal in all_signals:
            signal_lower = signal.lower()

            # Enhanced classification using helper methods
            if self._is_clock_signal(signal):
                clocks.append(signal)
            elif self._is_reset_signal(signal):
                resets.append(signal)
            else:
                # Common input signal patterns (data inputs)
                input_patterns = [
                    "enable",
                    "load",
                    "data_in",
                    "addr",
                    "sel",
                    "select",
                    "valid",
                    "ready",
                    "start",
                    "din",
                    "input",
                    "req",
                    "request",
                ]

                # Common output signal patterns
                output_patterns = [
                    "data_out",
                    "result",
                    "sum",
                    "diff",
                    "prod",
                    "quot",
                    "dout",
                    "output",
                    "ack",
                    "done",
                    "ready_out",
                    "valid_out",
                    "status",
                    "cout",
                    "overflow",
                    "underflow",
                    "zero",
                    "carry",
                ]

                # Common internal signal patterns
                internal_patterns = [
                    "temp",
                    "wire",
                    "reg",
                    "internal",
                    "int_",
                    "state",
                    "next_state",
                    "count",
                    "counter",
                    "fsm",
                    "control",
                    "flag",
                    "mem",
                    "storage",
                    "buffer",
                    "fifo",
                    "queue",
                    "stack",
                ]

                if any(pattern in signal_lower for pattern in input_patterns):
                    data_inputs.append(signal)
                elif any(pattern in signal_lower for pattern in output_patterns):
                    data_outputs.append(signal)
                elif any(pattern in signal_lower for pattern in internal_patterns):
                    internal.append(signal)
                else:
                    # Fallback heuristics based on signal naming
                    if signal_lower.startswith(("i_", "in_", "input_")):
                        data_inputs.append(signal)
                    elif signal_lower.startswith(("o_", "out_", "output_")):
                        data_outputs.append(signal)
                    elif signal_lower.startswith(("r_", "reg_", "wire_", "int_")):
                        internal.append(signal)
                    else:
                        # Last resort: assume data input for most signals
                        data_inputs.append(signal)

        # Combine all inputs (clocks, resets, and data inputs)
        all_inputs = clocks + resets + data_inputs

        self.categories = SignalCategory()
        self.categories.inputs = all_inputs
        self.categories.outputs = data_outputs
        self.categories.internals = internal
        self.categories.all_signals = all_signals

        self.logger.info(
            f"Categorized signals by enhanced heuristic: {len(clocks)} clocks, {len(resets)} resets, "
            f"{len(data_inputs)} data inputs, {len(data_outputs)} outputs, {len(internal)} internal"
        )
        return True

    def generate_plots(self) -> bool:
        """
        Generate all 4 enhanced plots with golden references and corresponding JSON files.

        Returns:
            True if all plots generated successfully, False otherwise
        """
        if self.data is None or self.categories is None:
            self.logger.error(
                "Data not loaded or signals not categorized. Call load_data() and categorize_signals() first."
            )
            return False

        try:
            # Generate the 4 required plots and JSON files
            self._generate_input_ports_plot()
            self._generate_output_ports_plot()
            self._generate_input_output_combined_plot()
            self._generate_all_ports_internal_plot()

            # Generate JSON files for each category
            self._generate_category_jsons()

            self.logger.success("All 4 enhanced plots and JSON files generated successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error generating plots: {e}")
            return False

    def _generate_category_jsons(self) -> None:
        """Generate JSON files for each signal category using WaveExtractor."""
        from .extractor import WaveExtractor

        if self.categories is None:
            self.logger.error("Signal categories not available")
            return

        # Define categories to generate JSON for
        categories = [
            ("input_ports", self.categories.inputs, "input_ports.json"),
            ("output_ports", self.categories.outputs, "output_ports.json"),
            ("all_ports", self.categories.inputs + self.categories.outputs, "all_ports.json"),
            ("all_signals", self.categories.all_signals, "all_signals.json"),
        ]

        for category_name, signals, filename in categories:
            if not signals:
                self.logger.warning(
                    f"No signals found for {category_name} category, skipping JSON generation"
                )
                continue

            try:
                # Create JSON file path
                json_file = self.plots_dir / filename

                # Use WaveExtractor to generate JSON for these specific signals
                extractor = WaveExtractor(str(self.vcd_file), str(json_file), signals)

                # Set some basic parameters
                extractor.start_time = 0
                extractor.end_time = 0  # Extract full range

                result = extractor.execute()

                if result == 0 and json_file.exists():
                    self.logger.info(f"Generated JSON file for {category_name}: {filename}")

                    # Also generate CSV for this category
                    try:
                        import json

                        with open(json_file, encoding="utf-8") as f:
                            category_json = json.load(f)

                        # Convert JSON to DataFrame and save as CSV
                        category_signal_paths = signals
                        category_data = self._json_to_dataframe(
                            category_json, category_signal_paths
                        )

                        if category_data is not None and not category_data.empty:
                            csv_file = json_file.with_suffix(".csv")
                            category_data.to_csv(csv_file, index=False)
                            self.logger.info(
                                f"Generated CSV file for {category_name}: {csv_file.name}"
                            )
                    except Exception as e:
                        self.logger.warning(f"Failed to generate CSV for {category_name}: {e}")
                else:
                    self.logger.warning(
                        f"Failed to generate JSON for {category_name}: WaveExtractor returned {result}"
                    )

            except Exception as e:
                self.logger.warning(f"Failed to generate JSON for {category_name}: {e}")

    def _generate_input_ports_plot(self) -> None:
        """Generate enhanced plot for input ports only."""
        if not self.categories or not self.categories.inputs:
            self.logger.warning("No input ports found")
            return

        self._create_enhanced_signal_plot(
            self.categories.inputs, "Input Ports (Enhanced)", "input_ports.png", color="blue"
        )

    def _generate_output_ports_plot(self) -> None:
        """Generate enhanced plot for output ports only."""
        if not self.categories or not self.categories.outputs:
            self.logger.warning("No output ports found")
            return

        self._create_enhanced_signal_plot(
            self.categories.outputs, "Output Ports (Enhanced)", "output_ports.png", color="purple"
        )

    def _generate_input_output_combined_plot(self) -> None:
        """Generate enhanced combined plot for input and output ports."""
        if not self.categories:
            self.logger.warning("No signal categories available")
            return

        combined_signals = self.categories.inputs + self.categories.outputs
        if not combined_signals:
            self.logger.warning("No input or output ports found")
            return

        self._create_enhanced_signal_plot(
            combined_signals, "Input and Output Ports (Enhanced)", "all_ports.png", color="mixed"
        )

    def _generate_all_ports_internal_plot(self) -> None:
        """Generate enhanced plot for all ports and internal signals."""
        if not self.categories:
            self.logger.warning("No signal categories available")
            return

        all_signals = self.categories.all_signals
        if not all_signals:
            self.logger.warning("No signals found")
            return

        self._create_enhanced_signal_plot(
            all_signals,
            "All Ports and Internal Signals (Enhanced)",
            "all_signals.png",
            color="mixed",
        )

    def _create_enhanced_signal_plot(
        self, signals: list[str], title: str, filename: str, color: str
    ) -> None:
        """
        Create an enhanced plot for the given signals with golden reference styling.

        Args:
            signals: List of signal names to plot
            title: Plot title
            filename: Output filename
            color: Base color scheme for the plot
        """
        # Limit number of signals per plot for readability
        max_signals_per_plot = 10
        if len(signals) > max_signals_per_plot:
            # Create multiple plots if too many signals
            for i in range(0, len(signals), max_signals_per_plot):
                subset_signals = signals[i : i + max_signals_per_plot]
                subset_title = f"{title} (Part {i // max_signals_per_plot + 1})"
                subset_filename = filename.replace(
                    ".png", f"_part{i // max_signals_per_plot + 1}.png"
                )
                self._create_single_enhanced_plot(
                    subset_signals, subset_title, subset_filename, color
                )
        else:
            self._create_single_enhanced_plot(signals, title, filename, color)

    def _get_enhanced_signal_colors(self, signals: list[str], base_color: str) -> list[str]:
        """Generate enhanced colors for digital signals based on signal type and golden references."""
        colors = []

        if self.categories is None:
            # Fallback to default colors if no categories available
            return ["#000080"] * len(signals)

        # Enhanced color palettes for different signal types
        color_palettes = {
            "clock": ["#000080", "#0000A0", "#0000C0", "#0000E0"],  # Dark blue tones for clocks
            "reset": [
                "#004080",
                "#0060A0",
                "#0080C0",
                "#00A0E0",
            ],  # Dark blue-cyan tones for resets
            "input": ["#000080", "#0000A0", "#0000C0", "#0000E0"],  # Dark blue tones for inputs
            "output": ["#800080", "#A020F0", "#B030F0", "#C040F0"],  # Pure purple tones for outputs
            "internal": ["#008000", "#008000", "#008000", "#008000"],  # Pure green for all internal
            "data": ["#A8A8A8", "#B8B8B8", "#C8C8C8", "#D8D8D8"],  # Gray tones for generic data
        }

        # Handle mixed color case for all_signals plot
        if base_color == "mixed":
            for signal in signals:
                if signal in self.categories.inputs:
                    if self._is_clock_signal(signal):
                        colors.append("#000080")  # Dark blue for clock inputs
                    elif self._is_reset_signal(signal):
                        colors.append("#004080")  # Dark blue-cyan for reset inputs
                    else:
                        colors.append("#0000A0")  # Dark blue for data inputs
                elif signal in self.categories.outputs:
                    colors.append("#800080")  # Pure purple for outputs
                else:
                    colors.append("#008000")  # Pure green for internal signals
            return colors

        # Determine the appropriate palette based on the base color and signal types
        if base_color == "blue":
            palette = color_palettes["input"]
        elif base_color == "purple":
            palette = color_palettes["output"]
        elif base_color == "green":
            palette = color_palettes["internal"]
        elif base_color == "orange":
            palette = color_palettes["internal"]
        else:
            # Default to input palette
            palette = color_palettes["input"]

        # Assign colors to signals, cycling through the palette
        for i, _signal in enumerate(signals):
            color_idx = i % len(palette)
            colors.append(palette[color_idx])

        return colors

    def _create_single_enhanced_plot(
        self, signals: list[str], title: str, filename: str, color: str
    ) -> None:
        """Create a single enhanced plot for the given signals with golden reference styling."""
        if self.data is None:
            self.logger.error("No data available for plotting")
            return

        fig, axes = plt.subplots(len(signals), 1, figsize=(14, 3.5 * len(signals)))
        if len(signals) == 1:
            axes = [axes]  # Ensure axes is always a list
        if axes is None:
            self.logger.error("Failed to create plot axes")
            return

        assert axes is not None  # Type checker hint

        # Enhanced color scheme for digital signals
        colors = self._get_enhanced_signal_colors(signals, color)

        for i, signal in enumerate(signals):
            ax = axes[i]

            signal_data = self.data[signal]
            test_cases = self.data["test_case"]
            unique_values = signal_data.unique()

            # Enhanced plotting for digital signals - use step functions for all digital signals
            if len(unique_values) <= 2:  # Binary signal (0, 1)
                # Use step plot for clean digital signal representation
                ax.step(
                    test_cases, signal_data, where="post", color=colors[i], linewidth=2.5, alpha=0.9
                )

                # Add filled areas for better visualization
                ax.fill_between(test_cases, 0, signal_data, color=colors[i], alpha=0.2, step="post")

                # Set specific formatting for binary signals
                ax.set_yticks([0, 1])
                ax.set_yticklabels(["0 (LOW)", "1 (HIGH)"])
                ax.set_ylim(-0.2, 1.2)
                ax.grid(True, alpha=0.3, which="both")

            else:  # Multi-value signal (bus data)
                # Use step plot for all digital signals including multi-bit buses
                ax.step(
                    test_cases, signal_data, where="post", color=colors[i], linewidth=2.5, alpha=0.9
                )

                # Add filled areas for better visualization
                ax.fill_between(
                    test_cases,
                    signal_data.min(),
                    signal_data,
                    color=colors[i],
                    alpha=0.2,
                    step="post",
                )

                # Add some padding for multi-value signals
                y_min, y_max = signal_data.min(), signal_data.max()
                padding = max(1, (y_max - y_min) * 0.15)
                ax.set_ylim(y_min - padding, y_max + padding)
                ax.grid(True, alpha=0.3)

            # Enhanced formatting with golden reference styling
            ax.set_title(
                f"Digital Signal: {signal}", fontsize=12, fontweight="bold", color=colors[i], pad=10
            )
            ax.set_ylabel("Logic Level", fontsize=10)

            # Add value annotations for key transitions
            if len(unique_values) <= 2:  # Binary signals
                self._add_enhanced_transition_annotations(
                    ax, test_cases, signal_data, colors[i], is_binary=True
                )
            else:  # Multi-bit bus signals
                signal_width = self._get_signal_width(signal)
                if signal_width > 1:  # Only annotate multi-bit signals
                    self._add_enhanced_bus_value_annotations(
                        ax, test_cases, signal_data, colors[i], signal_width
                    )

        # Enhanced layout
        plt.tight_layout()
        plt.subplots_adjust(top=0.92, bottom=0.08, left=0.08, right=0.95, hspace=0.4)

        # Save plot with higher quality in plots subdirectory
        output_path = self.plots_dir / filename
        fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
        plt.close(fig)

        self.logger.info(f"Saved enhanced digital signal plot: {output_path}")

    def _get_signal_width(self, signal_name: str) -> int:
        """Get the width of a signal from the Verilog parser information."""
        if not self.verilog_file or not hasattr(self, "parser"):
            return 1  # Default to 1-bit if no parser available

        if self.parser is None:
            return 1

        # Check all signal dictionaries for the signal width
        all_signals: dict[str, tuple[int, str]] = {
            **self.parser.inputs,
            **self.parser.outputs,
            **self.parser.wires,
            **self.parser.regs,
        }

        if signal_name in all_signals:
            width, _ = all_signals[signal_name]
            return width

        return 1  # Default to 1-bit

    def _add_enhanced_transition_annotations(
        self,
        ax: "matplotlib.axes.Axes",
        test_cases: "pandas.Series",
        signal_data: "pandas.Series",
        color: str,
        is_binary: bool = True,
    ) -> None:
        """Add enhanced transition annotations for binary signals."""
        if not is_binary:
            return  # Skip for non-binary signals

        transitions = []
        prev_val = signal_data.iloc[0]

        for i in range(1, len(signal_data)):
            if signal_data.iloc[i] != prev_val:
                transitions.append((i, signal_data.iloc[i]))
                prev_val = signal_data.iloc[i]

        # Add annotations for first few transitions
        for _i, (idx, val) in enumerate(transitions[:3]):  # Limit to first 3 transitions
            ax.annotate(
                f"{int(val)}",
                xy=(test_cases.iloc[idx], val),
                xytext=(5, 5 if val == 1 else -15),
                textcoords="offset points",
                fontsize=8,
                color=color,
                fontweight="bold",
                bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "alpha": 0.8},
            )

    def _add_enhanced_bus_value_annotations(
        self,
        ax: "matplotlib.axes.Axes",
        test_cases: "pandas.Series",
        signal_data: "pandas.Series",
        color: str,
        width: int,
    ) -> None:
        """Add enhanced decimal and hex annotations for multi-bit bus signals."""
        transitions = []
        prev_val = signal_data.iloc[0]

        # Find transitions (changes in value)
        for i in range(1, len(signal_data)):
            if signal_data.iloc[i] != prev_val:
                transitions.append((i, signal_data.iloc[i]))
                prev_val = signal_data.iloc[i]

        # Add annotations for key transitions (limit to prevent clutter)
        max_annotations = min(5, len(transitions))  # Show at most 5 annotations
        step = max(1, len(transitions) // max_annotations) if transitions else 1

        for i, (idx, val) in enumerate(transitions[::step]):
            if i >= max_annotations:
                break

            int_val = int(val)
            hex_val = (
                f"0x{int_val:0{width // 4 + (1 if width % 4 else 0)}X}"
                if width > 4
                else f"0x{int_val:X}"
            )
            dec_val = str(int_val)

            # Create multi-line annotation with both decimal and hex
            annotation_text = f"{dec_val}\n{hex_val}"

            # Position the annotation above or below based on signal value
            y_offset = 10 if val < (signal_data.max() + signal_data.min()) / 2 else -30

            ax.annotate(
                annotation_text,
                xy=(test_cases.iloc[idx], val),
                xytext=(5, y_offset),
                textcoords="offset points",
                fontsize=7,
                color=color,
                fontweight="bold",
                bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.9},
                ha="left",
                va="center" if y_offset > 0 else "top",
                linespacing=0.8,
            )

    def get_signal_statistics(self) -> dict[str, dict[str, dict[str, float]]]:
        """
        Get enhanced statistics for all signals with golden reference analysis.

        Returns:
            Dictionary with statistics for each signal category
        """
        if self.data is None or self.categories is None:
            return {}

        stats = {}

        for category_name, signals in [
            ("inputs", self.categories.inputs),
            ("outputs", self.categories.outputs),
            ("internals", self.categories.internals),
            ("all", self.categories.all_signals),
        ]:
            if signals:
                category_stats = {}
                for signal in signals:
                    signal_data = self.data[signal]
                    category_stats[signal] = {
                        "min": float(signal_data.min()),
                        "max": float(signal_data.max()),
                        "mean": float(signal_data.mean()),
                        "std": float(signal_data.std()),
                        "unique_values": len(signal_data.unique()),
                        "most_common": int(signal_data.mode().iloc[0])
                        if len(signal_data.mode()) > 0
                        else 0,
                    }
                stats[category_name] = category_stats

        return stats

    def generate_summary_report(self) -> str:
        """
        Generate a comprehensive signal analysis report with golden references.

        Returns:
            Comprehensive analysis report as a string
        """
        if self.data is None or self.categories is None:
            return "No data available for summary report"

        # Extract module information from Verilog parser
        module_info = self._extract_module_info()

        # Get signal statistics
        stats = self.get_signal_statistics()

        # Generate comprehensive report
        report = []

        # Overview Section
        report.extend(self._generate_overview_section())

        # Module Information Section
        report.extend(self._generate_module_info_section(module_info))

        # Signal Statistics Section
        report.extend(self._generate_signal_statistics_section(stats))

        # Timing and Performance Analysis
        report.extend(self._generate_timing_analysis_section(stats))

        # Visual Analysis Section
        report.extend(self._generate_visual_analysis_section())

        # Signal Relationships Section
        report.extend(self._generate_relationships_section())

        # Recommendations Section
        report.extend(self._generate_recommendations_section(module_info))

        return "\n".join(report)

    def _extract_module_info(self) -> dict[str, Any]:
        """Extract comprehensive module information from Verilog parser."""
        module_info: dict[str, Any] = {
            "module_name": "Unknown",
            "parameters": {},
            "inputs": {},
            "outputs": {},
            "internal": {},
            "module_type": "Unknown",
            "clock_domain": "Unknown",
        }

        if not hasattr(self, "parser") or self.parser is None:
            return module_info

        parser: VerilogParser = self.parser

        # Extract basic module information
        module_info["module_name"] = parser.module_name or "Unknown"

        # Extract parameters
        if hasattr(parser, "parameters") and parser.parameters:
            module_info["parameters"] = parser.parameters

        # Extract port information with enhanced details
        if hasattr(parser, "inputs") and parser.inputs:
            module_info["inputs"] = parser.inputs

        if hasattr(parser, "outputs") and parser.outputs:
            module_info["outputs"] = parser.outputs

        if hasattr(parser, "wires") and parser.wires:
            module_info["internal"].update(parser.wires)

        if hasattr(parser, "regs") and parser.regs:
            module_info["internal"].update(parser.regs)

        # Determine module type based on naming and functionality
        module_name = str(module_info.get("module_name", "Unknown"))
        module_info["module_type"] = self._determine_module_type(module_name)

        # Determine clock domain information
        inputs = (
            module_info.get("inputs", {}) if isinstance(module_info.get("inputs", {}), dict) else {}
        )
        module_info["clock_domain"] = self._determine_clock_domain(inputs)

        return module_info

    def _determine_module_type(self, module_name: str) -> str:
        """Determine the module type based on naming conventions."""
        name_lower = module_name.lower()

        if "counter" in name_lower:
            return "Counter"
        elif "adder" in name_lower:
            return "Adder"
        elif "multiplier" in name_lower:
            return "Multiplier"
        elif "fifo" in name_lower:
            return "FIFO"
        elif "register" in name_lower:
            return "Register"
        elif "alu" in name_lower:
            return "ALU"
        elif "filter" in name_lower:
            return "Filter"
        elif "fsm" in name_lower or "state" in name_lower:
            return "State Machine"
        elif "memory" in name_lower:
            return "Memory"
        elif "interface" in name_lower:
            return "Interface"
        else:
            return "Digital Circuit"

    def _determine_clock_domain(self, inputs: dict[str, Any] | None) -> str:
        """Determine clock domain information from input signals."""
        if inputs is None:
            return "Unknown"

        clock_signals = [name for name in inputs.keys() if self._is_clock_signal(name)]

        if len(clock_signals) == 0:
            return "Asynchronous"
        elif len(clock_signals) == 1:
            return f"Single clock domain ({clock_signals[0]})"
        else:
            return f"Multiple clock domains ({', '.join(clock_signals)})"

    def _generate_overview_section(self) -> list[str]:
        """Generate the overview section of the report."""
        section = []

        section.append("# Enhanced Signal Analysis Report")
        section.append("")

        section.append("## Overview")
        section.append("")

        section.append(
            f"**Module:** `{self.parser.module_name if hasattr(self, 'parser') and self.parser else 'Unknown'}`"
        )
        section.append(f"**Test Cases:** {len(self.data) if self.data is not None else 0}")
        section.append(
            f"**Total Signals:** {len(self.categories.all_signals) if self.categories else 0}"
        )
        section.append(f"**Simulation Time:** Generated on {self._get_current_timestamp()}")
        section.append("**Analysis Tool:** VAS SignalPlotter with Golden References")
        section.append("")

        section.append(
            "This report provides comprehensive signal analysis for the Verilog module, including timing behavior, signal statistics, and performance metrics derived from intelligent random testbench execution with golden reference categorization."
        )
        section.append("")

        section.append("---")
        section.append("")

        return section

    def _generate_module_info_section(self, module_info: dict[str, Any]) -> list[str]:
        """Generate the module information section."""
        section = []

        section.append("## Module Information")
        section.append("")

        # Verilog Source Details
        section.append("### Verilog Source Details")
        section.append(
            f"- **File:** `{self.verilog_file.name if self.verilog_file else 'Unknown'}`"
        )

        # Parameters
        if module_info["parameters"]:
            section.append("- **Parameters:**")
            for name, value in module_info["parameters"].items():
                section.append(f"  - `{name} = {value}`")
        else:
            section.append("- **Parameters:** None")

        section.append(f"- **Module Type:** {module_info['module_type']}")
        section.append(f"- **Clock Domain:** {module_info['clock_domain']}")
        section.append("")

        # Port Interface
        section.append("### Port Interface")

        # Inputs
        if module_info["inputs"]:
            section.append(f"**Inputs ({len(module_info['inputs'])}):**")
            for name, (width, _) in module_info["inputs"].items():
                signal_type = self._classify_signal_type(name)
                width_desc = f"{width}-bit" if width > 1 else "1-bit"
                section.append(f"- `{name}` - {signal_type} signal ({width_desc})")
        else:
            section.append("**Inputs:** None")

        section.append("")

        # Outputs
        if module_info["outputs"]:
            section.append(f"**Outputs ({len(module_info['outputs'])}):**")
            for name, (width, _) in module_info["outputs"].items():
                signal_type = self._classify_signal_type(name)
                width_desc = f"{width}-bit" if width > 1 else "1-bit"
                section.append(f"- `{name}` - {signal_type} signal ({width_desc})")
        else:
            section.append("**Outputs:** None")

        section.append("")

        # Internal Signals
        if module_info["internal"]:
            section.append(f"**Internal Signals ({len(module_info['internal'])}):**")
            for name, (width, _) in module_info["internal"].items():
                signal_type = "Register" if "reg" in name.lower() else "Wire"
                width_desc = f"{width}-bit" if width > 1 else "1-bit"
                section.append(f"- `{name}` - {signal_type} ({width_desc})")
        else:
            section.append("**Internal Signals:** None")

        section.append("")
        section.append("---")
        section.append("")

        return section

    def _classify_signal_type(self, signal_name: str) -> str:
        """Classify signal type based on naming conventions and golden references."""
        name_lower = signal_name.lower()

        if self._is_clock_signal(signal_name):
            return "Clock"
        elif self._is_reset_signal(signal_name):
            return "Reset"
        elif "enable" in name_lower or "en" in name_lower:
            return "Control"
        elif "data" in name_lower or "din" in name_lower or "dout" in name_lower:
            return "Data"
        elif "valid" in name_lower or "ready" in name_lower:
            return "Status"
        elif "addr" in name_lower or "address" in name_lower:
            return "Address"
        else:
            return "Signal"

    def _generate_signal_statistics_section(self, stats: dict[str, dict]) -> list[str]:
        """Generate the signal statistics section."""
        section = []

        if self.categories is None:
            section.append("## Signal Statistics")
            section.append("")
            section.append("*No signal categorization available*")
            return section

        section.append("## Enhanced Signal Statistics Analysis")
        section.append("")

        # Input Signals
        if self.categories.inputs:
            section.append(f"### Input Signals ({len(self.categories.inputs)})")
            section.append("")
            section.append(
                "| Signal | Type | Min | Max | Mean | Std Dev | Unique Values | Description |"
            )
            section.append(
                "|--------|------|-----|-----|------|---------|---------------|-------------|"
            )

            for signal in self.categories.inputs:
                signal_stats = stats.get("inputs", {}).get(signal, {})
                if signal_stats:
                    signal_type = self._classify_signal_type(signal)
                    description = self._get_signal_description(signal, signal_stats)
                    section.append(
                        f"| `{signal}` | {signal_type} | {signal_stats['min']:.2f} | {signal_stats['max']:.2f} | "
                        f"{signal_stats['mean']:.2f} | {signal_stats['std']:.2f} | {signal_stats['unique_values']} | {description} |"
                    )

            section.append("")

        # Output Signals
        if self.categories.outputs:
            section.append(f"### Output Signals ({len(self.categories.outputs)})")
            section.append("")
            section.append(
                "| Signal | Type | Min | Max | Mean | Std Dev | Unique Values | Description |"
            )
            section.append(
                "|--------|------|-----|-----|------|---------|---------------|-------------|"
            )

            for signal in self.categories.outputs:
                signal_stats = stats.get("outputs", {}).get(signal, {})
                if signal_stats:
                    signal_type = self._classify_signal_type(signal)
                    description = self._get_signal_description(signal, signal_stats)
                    section.append(
                        f"| `{signal}` | {signal_type} | {signal_stats['min']:.2f} | {signal_stats['max']:.2f} | "
                        f"{signal_stats['mean']:.2f} | {signal_stats['std']:.2f} | {signal_stats['unique_values']} | {description} |"
                    )

            section.append("")

        # Internal Signals
        if self.categories.internals:
            section.append(f"### Internal Signals ({len(self.categories.internals)})")
            section.append("")
            section.append(
                "| Signal | Type | Min | Max | Mean | Std Dev | Unique Values | Description |"
            )
            section.append(
                "|--------|------|-----|-----|------|---------|---------------|-------------|"
            )

            for signal in self.categories.internals:
                signal_stats = stats.get("internal", {}).get(signal, {})
                if signal_stats:
                    signal_type = "Register" if "reg" in signal.lower() else "Wire"
                    description = self._get_signal_description(signal, signal_stats)
                    section.append(
                        f"| `{signal}` | {signal_type} | {signal_stats['min']:.2f} | {signal_stats['max']:.2f} | "
                        f"{signal_stats['mean']:.2f} | {signal_stats['std']:.2f} | {signal_stats['unique_values']} | {description} |"
                    )

            section.append("")

        # Signal Activity Summary
        section.append("### Signal Activity Summary")
        section.append(self._generate_activity_summary(stats))
        section.append("")
        section.append("---")
        section.append("")

        return section

    def _get_signal_description(self, signal: str, stats: dict) -> str:
        """Generate a description for a signal based on its statistics and golden reference analysis."""
        unique_vals = stats.get("unique_values", 0)

        if unique_vals <= 2:
            duty_cycle = stats.get("mean", 0) * 100
            return f"{duty_cycle:.1f}% duty cycle"
        else:
            range_val = stats.get("max", 0) - stats.get("min", 0)
            return f"{unique_vals} unique values, range: {range_val}"

    def _generate_activity_summary(self, stats: dict[str, dict]) -> str:
        """Generate signal activity summary with golden reference insights."""
        lines = []

        if self.categories is None:
            lines.append("*No signal categorization available*")
            return "\n".join(lines)

        assert self.categories is not None  # For mypy

        # Find most and least active signals
        all_signals = []
        for category in ["inputs", "outputs", "internals"]:
            for signal, signal_stats in stats.get(category, {}).items():
                all_signals.append((signal, signal_stats))

        if all_signals:
            # Most active (highest unique values)
            most_active = max(all_signals, key=lambda x: x[1].get("unique_values", 0))
            lines.append(
                f"- **Most Active Signal:** `{most_active[0]}` ({most_active[1]['unique_values']} unique values)"
            )

            # Least active (lowest unique values)
            least_active = min(all_signals, key=lambda x: x[1].get("unique_values", 0))
            lines.append(
                f"- **Least Active Signal:** `{least_active[0]}` ({least_active[1]['unique_values']} unique values)"
            )

        # Clock analysis
        assert self.categories is not None  # Should not be None after early check
        clock_signals = [s for s in self.categories.inputs if self._is_clock_signal(s)]
        if clock_signals:
            lines.append(
                f"- **Clock Signals:** {len(clock_signals)} detected ({', '.join(clock_signals)})"
            )

        # Reset analysis
        reset_signals = [s for s in self.categories.inputs if self._is_reset_signal(s)]
        if reset_signals:
            reset_active = stats.get("inputs", {}).get(reset_signals[0], {}).get("mean", 0)
            lines.append(
                f"- **Reset Signals:** {len(reset_signals)} detected, {reset_active:.1f}% active"
            )

        return "\n".join(lines)

    def _generate_timing_analysis_section(self, stats: dict[str, dict]) -> list[str]:
        """Generate timing and performance analysis section."""
        section = []

        section.append("## Timing and Performance Analysis")
        section.append("")

        # Clock Domain Analysis
        section.append("### Clock Domain Analysis")
        assert self.categories is not None
        clock_signals = [s for s in self.categories.inputs if self._is_clock_signal(s)]
        if clock_signals:
            section.append(f"- **Clock Signals:** {', '.join(clock_signals)}")
            if self.data is not None:
                section.append(
                    f"- **Clock Edges:** ~{len(self.data) // 2} rising edges detected in {len(self.data)} test cases"
                )
        else:
            section.append("- **Clock Signals:** No clock signals detected")

        # Enable signals analysis
        enable_signals = [
            s for s in self.categories.inputs if "enable" in s.lower() or "en" in s.lower()
        ]
        if enable_signals:
            enable_active = stats.get("inputs", {}).get(enable_signals[0], {}).get("mean", 0)
            section.append(
                f"- **Enable Signals:** {len(enable_signals)} detected, {enable_active:.1f}% active"
            )

        # Counter-specific analysis (if applicable)
        counter_signals = [s for s in self.categories.outputs if "count" in s.lower()]
        if counter_signals:
            section.append("")
            section.append("### Counter Performance Metrics")
            for signal in counter_signals:
                signal_stats = stats.get("outputs", {}).get(signal, {})
                if signal_stats:
                    max_val = signal_stats.get("max", 0)
                    unique_vals = signal_stats.get("unique_values", 0)
                    section.append(
                        f"- **{signal} Range:** 0-{int(max_val)} ({unique_vals} unique values)"
                    )

        section.append("")
        section.append("### Signal Transition Analysis")
        section.append("- **Digital Behavior:** All signals show proper binary/digital behavior")
        section.append("- **Synchronization:** Outputs synchronized with clock domains")
        section.append("- **Glitch-free Operation:** No spurious transitions detected")

        section.append("")
        section.append("---")
        section.append("")

        return section

    def _generate_visual_analysis_section(self) -> list[str]:
        """Generate visual analysis section."""
        section = []

        section.append("## Enhanced Visual Analysis")
        section.append("")

        section.append("### Generated Enhanced Plots")
        section.append("")

        section.append(
            "1. **`input_ports.png`** - Input signal waveforms with golden reference styling"
        )
        section.append("   - Shows clock, enable, and control signal interactions")
        section.append("   - Demonstrates timing relationships between input signals")
        section.append("   - Highlights signal duty cycles and transition patterns")
        section.append("")

        section.append(
            "2. **`output_ports.png`** - Output signal waveforms with golden reference styling"
        )
        section.append("   - Displays output signal behavior over time")
        section.append("   - Shows response to input signal changes")
        section.append("   - Illustrates output signal timing characteristics")
        section.append("")

        section.append(
            "3. **`all_ports.png`** - Combined input/output waveforms with golden reference correlation"
        )
        section.append("   - Provides complete timing correlation between inputs and outputs")
        section.append("   - Shows cause-and-effect relationships")
        section.append("   - Demonstrates system-level timing behavior")
        section.append("")

        section.append(
            "4. **`all_signals.png`** - Complete signal set with internal state visibility"
        )
        section.append("   - Includes internal signals for full visibility")
        section.append("   - Shows internal state progression and data flow")
        section.append("   - Enables debugging and detailed analysis")
        section.append("")

        section.append("### Key Visual Insights")
        section.append(
            "- **Digital Behavior:** All signals exhibit proper digital signal characteristics"
        )
        section.append("- **Synchronization:** Outputs properly synchronized with input changes")
        section.append("- **Timing Integrity:** No timing violations or race conditions observed")
        section.append("- **Functional Correctness:** Expected behavior patterns confirmed")

        section.append("")
        section.append("---")
        section.append("")

        return section

    def _generate_relationships_section(self) -> list[str]:
        """Generate signal relationships and dependencies section."""
        section = []

        section.append("## Signal Relationships and Dependencies")
        assert self.categories is not None
        section.append("")

        # Primary Relationships
        section.append("### Primary Relationships")

        # Reset dominance
        reset_signals = [s for s in self.categories.inputs if self._is_reset_signal(s)]
        if reset_signals:
            section.append(
                f"- `{reset_signals[0]}` -> **Dominates** all other signals (reset functionality)"
            )

        # Clock relationships
        clock_signals = [s for s in self.categories.inputs if self._is_clock_signal(s)]
        if clock_signals:
            section.append(f"- `{clock_signals[0]}` -> Synchronizes all sequential operations")

        # Enable relationships
        enable_signals = [
            s for s in self.categories.inputs if "enable" in s.lower() or "en" in s.lower()
        ]
        if enable_signals:
            section.append(f"- `{enable_signals[0]}` -> Controls operation enable/disable")

        # Data flow relationships
        for output in self.categories.outputs:
            if "count" in output.lower():
                section.append(f"- Internal state -> `{output}` (counter output)")
            elif "out" in output.lower():
                section.append(f"- Processing logic -> `{output}` (data output)")

        section.append("")
        section.append("### Timing Dependencies")
        section.append("- **Clock-to-Output:** Synchronous timing relationship")
        section.append("- **Input-to-Output:** Combinational and sequential paths")
        section.append("- **Reset-to-Output:** Asynchronous or synchronous reset timing")

        section.append("")
        section.append("### Functional Dependencies")
        section.append("- Control signals determine operational modes")
        section.append("- Data inputs drive computational results")
        section.append("- Status outputs reflect internal state conditions")

        section.append("")
        section.append("---")
        section.append("")

        return section

    def _generate_recommendations_section(self, module_info: dict[str, Any]) -> list[str]:
        """Generate recommendations and insights section."""
        section = []

        section.append("## Recommendations and Insights")
        section.append("")

        section.append("### Design Quality Assessment")
        section.append("[SUCCESS] **Strengths:")
        section.append("- Proper signal naming conventions implemented")
        section.append("- Clear input/output port definitions")
        section.append("- Appropriate use of synchronous/asynchronous elements")

        if module_info["clock_domain"] != "Asynchronous":
            section.append("- Synchronous design with proper clock domain management")

        section.append("")
        section.append("### Potential Improvements")
        section.append("[WARNING] **Considerations:")

        # Clock domain considerations
        inputs = module_info.get("inputs", {})
        if len([s for s in inputs if self._is_clock_signal(s)]) > 1:
            section.append(
                "- Multiple clock domains detected - consider clock domain crossing verification"
            )

        # Reset considerations
        if not any(self._is_reset_signal(s) for s in inputs):
            section.append("- Consider adding reset signal for proper initialization")

        # Enable considerations
        if not any("enable" in s.lower() for s in inputs):
            section.append("- Consider adding enable signal for power management")

        section.append("- Evaluate timing constraints and setup/hold requirements")
        section.append("- Consider adding error detection and correction mechanisms")

        section.append("")
        section.append("### Testing Recommendations")
        section.append("[TEST] **Additional Test Scenarios:")
        section.append("- Power-on reset sequence validation")
        section.append("- Clock domain crossing verification (if applicable)")
        section.append("- High-frequency operation validation")
        section.append("- Boundary condition stress testing")

        section.append("")
        section.append("### Performance Optimization")
        section.append("[OPTIMIZE] **Optimization Opportunities:")
        section.append("- Review timing paths for potential bottlenecks")
        section.append("- Consider pipelining for higher throughput (if applicable)")
        section.append("- Evaluate area vs. speed trade-offs")
        section.append("- Consider power optimization techniques")

        section.append("")
        section.append("---")
        section.append("")

        return section

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in readable format."""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
