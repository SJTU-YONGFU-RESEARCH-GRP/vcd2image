"""Intelligent signal categorization for automatic plotting."""

import logging
import re

from .models import SignalCategory, SignalDef, SignalType

logger = logging.getLogger(__name__)


class SignalCategorizer:
    """Intelligent categorizer for VCD signals based on naming patterns and hierarchy."""

    def __init__(self) -> None:
        """Initialize signal categorizer."""
        # Common clock signal patterns
        self.clock_patterns = [
            re.compile(r"\bclock\b", re.IGNORECASE),
            re.compile(r"\bclk\b", re.IGNORECASE),
            re.compile(r"\bck\b", re.IGNORECASE),
        ]

        # Common input port patterns
        self.input_patterns = [
            re.compile(r"\bin\b", re.IGNORECASE),
            re.compile(r"\binput\b", re.IGNORECASE),
            re.compile(r"\bi_\w+", re.IGNORECASE),
        ]

        # Common output port patterns
        self.output_patterns = [
            re.compile(r"\bout\b", re.IGNORECASE),
            re.compile(r"\boutput\b", re.IGNORECASE),
            re.compile(r"\bo_\w+", re.IGNORECASE),
        ]

        # Common reset signal patterns
        self.reset_patterns = [
            re.compile(r"\breset\b", re.IGNORECASE),
            re.compile(r"\brst\b", re.IGNORECASE),
            re.compile(r"\bclear\b", re.IGNORECASE),
        ]

        # Module instance prefixes that indicate internal signals
        self.internal_prefixes = [
            "u_",  # Common Verilog instance prefix
            "i_",  # Common instance prefix
            "dut_",  # Design Under Test
            "tb_",  # Testbench
        ]

    def categorize_signals(self, path_dict: dict[str, SignalDef]) -> SignalCategory:
        """Categorize signals based on naming patterns and hierarchy.

        Args:
            path_dict: Dictionary mapping signal paths to signal definitions.

        Returns:
            SignalCategory object containing categorized signals.
        """
        category = SignalCategory()

        for path, signal_def in path_dict.items():
            signal_type = self._classify_signal(path, signal_def)
            signal_def.signal_type = signal_type

            if signal_type == SignalType.CLOCK:
                category.clocks.append(path)
            elif signal_type == SignalType.INPUT:
                category.inputs.append(path)
            elif signal_type == SignalType.OUTPUT:
                category.outputs.append(path)
            elif signal_type == SignalType.RESET:
                category.resets.append(path)
            elif signal_type == SignalType.INTERNAL:
                category.internals.append(path)
            else:  # SignalType.UNKNOWN
                category.unknowns.append(path)

        # Sort signals for consistent ordering
        category.clocks.sort()
        category.inputs.sort()
        category.outputs.sort()
        category.resets.sort()
        category.internals.sort()
        category.unknowns.sort()

        logger.info(f"Categorized signals: {category}")
        return category

    def _classify_signal(self, path: str, signal_def: SignalDef) -> SignalType:
        """Classify a single signal based on its path and name.

        Args:
            path: Full hierarchical path to the signal.
            signal_def: Signal definition object.

        Returns:
            SignalType classification.
        """
        name = signal_def.name.lower()
        path_lower = path.lower()

        # Check for clock signals first
        if self._matches_any_pattern(name, self.clock_patterns):
            return SignalType.CLOCK

        # Check for reset signals
        if self._matches_any_pattern(name, self.reset_patterns):
            return SignalType.RESET

        # Check for explicit input/output patterns
        if self._matches_any_pattern(name, self.input_patterns):
            return SignalType.INPUT
        if self._matches_any_pattern(name, self.output_patterns):
            return SignalType.OUTPUT

        # Analyze hierarchy depth and prefixes
        path_parts = path.split("/")

        # Check for internal module prefixes (but not for top-level testbench signals)
        if len(path_parts) > 2:  # Only check internal prefixes for deeply nested signals
            if any(any(part.startswith(prefix) for part in path_parts[1:]) for prefix in self.internal_prefixes):
                return SignalType.INTERNAL

        # Testbench-level signals (tb_* or top-level) - analyze based on typical usage
        if len(path_parts) <= 2 or path_parts[0].startswith("tb_"):
            # Common testbench outputs: pulse, done, ready, valid, etc.
            output_indicators = ["pulse", "done", "ready", "valid", "out", "result"]
            if any(indicator in name for indicator in output_indicators):
                return SignalType.OUTPUT

            # Single-bit signals at testbench level are often inputs (controls)
            if signal_def.length == 1:
                return SignalType.INPUT
            else:
                # Multi-bit signals at testbench level are often outputs (results)
                return SignalType.OUTPUT

        # Signals with multiple hierarchy levels in modules are likely internal
        if len(path_parts) > 2:
            return SignalType.INTERNAL

        # Default classification based on signal width
        # Single-bit signals are often inputs, multi-bit are often outputs
        return SignalType.INPUT if signal_def.length == 1 else SignalType.OUTPUT

    def _matches_any_pattern(self, text: str, patterns: list[re.Pattern]) -> bool:
        """Check if text matches any of the given regex patterns.

        Args:
            text: Text to check.
            patterns: List of compiled regex patterns.

        Returns:
            True if any pattern matches.
        """
        return any(pattern.search(text) for pattern in patterns)

    def suggest_clock_signal(self, category: SignalCategory) -> str | None:
        """Suggest the most likely clock signal from categorized signals.

        Prefers internal clock signals over testbench clock signals.

        Args:
            category: Categorized signals.

        Returns:
            Path to suggested clock signal, or None if no suitable clock found.
        """
        if not category.clocks:
            # Look for clock-like signals in inputs
            for path in category.inputs:
                signal_name = path.split("/")[-1].lower()
                if self._matches_any_pattern(signal_name, self.clock_patterns):
                    return path
            return None

        # Prefer internal clock signals (longer paths, deeper in hierarchy)
        internal_clocks = [path for path in category.clocks if len(path.split("/")) > 2]
        if internal_clocks:
            return internal_clocks[0]

        # Otherwise return the first clock signal
        return category.clocks[0]
