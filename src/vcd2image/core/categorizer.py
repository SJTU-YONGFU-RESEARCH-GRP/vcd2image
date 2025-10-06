"""Intelligent signal categorization for automatic plotting."""

import logging
import re
from typing import Dict, List, Optional

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

    def categorize_signals(self, path_dict: Dict[str, SignalDef]) -> SignalCategory:
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
                category.clock_signals.append(path)
            elif signal_type == SignalType.INPUT_PORT:
                category.input_ports.append(path)
            elif signal_type == SignalType.OUTPUT_PORT:
                category.output_ports.append(path)
            else:  # SignalType.INTERNAL_SIGNAL
                category.internal_signals.append(path)

        # Sort signals for consistent ordering
        category.clock_signals.sort()
        category.input_ports.sort()
        category.output_ports.sort()
        category.internal_signals.sort()

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

        # Check for reset signals (often treated as inputs)
        if self._matches_any_pattern(name, self.reset_patterns):
            return SignalType.INPUT_PORT

        # Check for explicit input/output patterns
        if self._matches_any_pattern(name, self.input_patterns):
            return SignalType.INPUT_PORT
        if self._matches_any_pattern(name, self.output_patterns):
            return SignalType.OUTPUT_PORT

        # Analyze hierarchy depth and prefixes
        path_parts = path.split("/")

        # Testbench-level signals (tb_* or top-level) - analyze based on typical usage
        if len(path_parts) <= 2 or path_parts[0].startswith("tb_"):
            # Common testbench outputs: pulse, done, ready, valid, etc.
            output_indicators = ["pulse", "done", "ready", "valid", "out", "result"]
            if any(indicator in name for indicator in output_indicators):
                return SignalType.OUTPUT_PORT

            # Single-bit signals at testbench level are often inputs (controls)
            if signal_def.length == 1:
                return SignalType.INPUT_PORT
            else:
                # Multi-bit signals at testbench level are often outputs (results)
                return SignalType.OUTPUT_PORT

        # Check for internal module prefixes
        if any(path_lower.startswith(prefix) for prefix in self.internal_prefixes):
            return SignalType.INTERNAL_SIGNAL

        # Signals with multiple hierarchy levels in modules are likely internal
        if len(path_parts) > 2:
            return SignalType.INTERNAL_SIGNAL

        # Default classification based on signal width
        # Single-bit signals are often inputs, multi-bit are often outputs
        return SignalType.INPUT_PORT if signal_def.length == 1 else SignalType.OUTPUT_PORT

    def _matches_any_pattern(self, text: str, patterns: List[re.Pattern]) -> bool:
        """Check if text matches any of the given regex patterns.

        Args:
            text: Text to check.
            patterns: List of compiled regex patterns.

        Returns:
            True if any pattern matches.
        """
        return any(pattern.search(text) for pattern in patterns)

    def suggest_clock_signal(self, category: SignalCategory) -> Optional[str]:
        """Suggest the most likely clock signal from categorized signals.

        Prefers internal clock signals over testbench clock signals.

        Args:
            category: Categorized signals.

        Returns:
            Path to suggested clock signal, or None if no suitable clock found.
        """
        if not category.clock_signals:
            # Look for clock-like signals in input ports
            for path in category.input_ports:
                signal_name = path.split("/")[-1].lower()
                if self._matches_any_pattern(signal_name, self.clock_patterns):
                    return path
            return None

        # Prefer internal clock signals (longer paths, deeper in hierarchy)
        internal_clocks = [path for path in category.clock_signals if len(path.split("/")) > 2]
        if internal_clocks:
            return internal_clocks[0]

        # Otherwise return the first clock signal
        return category.clock_signals[0]
