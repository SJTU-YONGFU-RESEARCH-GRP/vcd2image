"""WaveJSON generation from sampled signal data."""

import logging
from typing import Dict, List

from .models import SignalDef

logger = logging.getLogger(__name__)


class WaveJSONGenerator:
    """Generates WaveJSON format from signal samples."""

    def __init__(
        self, path_list: List[str], path_dict: Dict[str, SignalDef], wave_chunk: int
    ) -> None:
        """Initialize JSON generator.

        Args:
            path_list: List of signal paths in order.
            path_dict: Dictionary mapping paths to signal definitions.
            wave_chunk: Number of samples per time group.
        """
        self.path_list = path_list
        self.path_dict = path_dict
        self.wave_chunk = wave_chunk
        self.clock_name = path_dict[path_list[0]].name
        self.name_width = max(len(path_dict[path].name) for path in path_list)

    def generate_json(self, sample_groups: List[Dict[str, List[str]]]) -> str:
        """Generate complete WaveJSON string.

        Args:
            sample_groups: List of sample groups from signal sampler.

        Returns:
            Complete WaveJSON string.
        """
        json_parts = []
        json_parts.append(self._create_header())

        for sample_dict in sample_groups:
            json_parts.append(self._create_body(sample_dict))

        json_parts.append(self._create_footer())

        return "\n".join(json_parts)

    def _create_header(self) -> str:
        """Create JSON header with clock signal.

        Returns:
            JSON header string.
        """
        name = f'"{self.clock_name}"'.ljust(self.name_width + 2)
        wave = f'"{"p" + "." * (self.wave_chunk - 1)}"'
        return f'{{ "head": {{"tock":1}},\n  "signal": [\n  {{   "name": {name}, "wave": {wave} }}'

    def _create_body(self, sample_dict: Dict[str, List[str]]) -> str:
        """Create JSON body for a sample group.

        Args:
            sample_dict: Sample dictionary for this time group.

        Returns:
            JSON body string.
        """
        # This is a simplified version - in a real implementation,
        # you'd need to calculate the origin time and format properly
        origin = "0"  # Placeholder - would need to be calculated

        json_lines = []
        json_lines.append(",\n  {}")
        json_lines.append(f',\n  ["{origin}"')

        for path in self.path_list[1:]:  # Skip clock signal
            signal_def = self.path_dict[path]
            sid = signal_def.sid
            samples = sample_dict.get(sid, [])

            name = f'"{signal_def.name}"'.ljust(self.name_width + 2)

            if signal_def.length == 1:
                # Single-bit signal
                wave = self._create_wave(samples)
                json_lines.append(f',\n    {{ "name": {name}, "wave": {wave} }}')
            else:
                # Multi-bit signal
                wave, data = self._create_wave_data(samples, signal_def.length, signal_def.fmt)
                json_lines.append(f',\n    {{ "name": {name}, "wave": {wave}, "data": {data} }}')

        json_lines.append("\n  ]")
        return "".join(json_lines)

    def _create_footer(self) -> str:
        """Create JSON footer.

        Returns:
            JSON footer string.
        """
        return "\n  ]\n}"

    def _create_wave(self, samples: List[str]) -> str:
        """Create wave string for single-bit signals.

        Args:
            samples: List of sample values.

        Returns:
            Wave string in quotes.
        """
        if not samples:
            return '""'

        prev = None
        wave = ""
        for value in samples:
            if value == prev:
                wave += "."
            else:
                wave += value
            prev = value
        return f'"{wave}"'

    def _create_wave_data(self, samples: List[str], length: int, fmt: str) -> tuple[str, str]:
        """Create wave and data strings for multi-bit signals.

        Args:
            samples: List of sample values.
            length: Signal bit length.
            fmt: Display format.

        Returns:
            Tuple of (wave_string, data_string).
        """
        if not samples:
            return '""', '""'

        prev = None
        wave = ""
        data = ""

        for value in samples:
            if value == prev:
                wave += "."
            elif self._is_binary_string(value):
                wave += "="
                data += " " + self._format_value(value, length, fmt)
            elif all(c == "z" for c in value):
                wave += "z"
            else:
                wave += "x"
            prev = value

        return f'"{wave}"', f'"{data[1:]}"'

    def _is_binary_string(self, value: str) -> bool:
        """Check if string contains only binary digits.

        Args:
            value: Value string to check.

        Returns:
            True if string contains only 0s and 1s.
        """
        return all(c in ("0", "1") for c in value)

    def _format_value(self, value: str, length: int, fmt: str) -> str:
        """Format multi-bit value according to specified format.

        Args:
            value: Binary value string.
            length: Signal bit length.
            fmt: Format character (b, d, u, x, X).

        Returns:
            Formatted value string.
        """
        try:
            value_int = int(value, 2)
        except ValueError:
            return "x"

        if fmt == "b":
            fmt_str = f"0{length}b"
        elif fmt == "d":
            if value_int >= 2 ** (length - 1):
                value_int -= 2**length
            fmt_str = "d"
        elif fmt == "u":
            fmt_str = "d"
        elif fmt == "X":
            fmt_str = f"0{((length + 3) // 4)}X"
        else:  # 'x' or default
            fmt_str = f"0{((length + 3) // 4)}x"

        return format(value_int, fmt_str)
