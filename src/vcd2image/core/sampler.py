"""Signal sampling from VCD files."""

import logging
from typing import TextIO

logger = logging.getLogger(__name__)


class SignalSampler:
    """Samples signal values from VCD dump section."""

    def __init__(self, wave_chunk: int, start_time: int, end_time: int) -> None:
        """Initialize signal sampler.

        Args:
            wave_chunk: Number of samples per time group.
            start_time: Sampling start time.
            end_time: Sampling end time (0 = until end).
        """
        self.wave_chunk = wave_chunk
        self.start_time = start_time
        self.end_time = end_time
        self.now = 0

    def sample_signals(
        self, fin: TextIO, clock_sid: str, signal_sids: list[str]
    ) -> list[dict[str, list[str]]]:
        """Sample signal values from VCD file.

        Args:
            fin: Open file handle positioned at start of dump section.
            clock_sid: Clock signal identifier.
            signal_sids: List of signal identifiers to sample.

        Returns:
            List of sample dictionaries for each time group.
        """
        sample_groups: list[dict[str, list[str]]] = []

        # Initialize value and sample dictionaries
        # Note: dict.fromkeys() with mutable defaults shares the same object, so create individually
        value_dict = {sid: "x" for sid in [clock_sid] + signal_sids}
        sample_dict = {sid: [] for sid in [clock_sid] + signal_sids}

        clock_prev = value_dict[clock_sid]  # initial clock value

        logger.debug(f"Sampling signals with clock_sid={clock_sid}, signal_sids={signal_sids}")
        data_count = 0

        while True:
            if self.end_time != 0 and self.end_time < int(self.now):
                break

            line = fin.readline()
            if not line:
                break

            words = line.split()
            if not words:
                continue

            char = words[0][0]

            # Skip comment lines
            if char == "$":
                continue

            # Skip real number lines
            if char == "r":
                continue

            # Handle scalar values
            if char in ("0", "1", "x", "z"):
                sid = words[0][1:]
                if sid in value_dict:
                    value_dict[sid] = char
                continue

            # Handle vector values
            if char == "b":
                sid = words[1]
                if sid in value_dict:
                    value_dict[sid] = words[0][1:]
                continue

            # Handle timestamp changes
            if char == "#":
                next_now = words[0][1:]
                self.now = int(next_now)

                # Sample at regular time intervals instead of just clock edges
                # This gives a more complete view of signal behavior
                if self.start_time <= self.now and (self.end_time == 0 or self.now <= self.end_time):
                    # Check if we should sample at this time point
                    # Sample every time unit for now (could be made configurable)
                    should_sample = True  # Sample at every timestamp for complete waveform

                    if should_sample:
                        # Sample all signals at this time point
                        for sid in sample_dict:
                            sample_dict[sid].append(value_dict[sid])
                        data_count += 1

                        # Check if we have enough samples for this group
                        if data_count == self.wave_chunk:
                            sample_groups.append({sid: sample_dict[sid][:] for sid in sample_dict})
                            # Reset for next group
                            for sid in sample_dict:
                                sample_dict[sid].clear()
                            data_count = 0
                continue

            raise ValueError(f"Unexpected character in VCD file: '{char}'")

        # Save any remaining incomplete group
        if any(sample_dict[sid] for sid in sample_dict):
            sample_groups.append({sid: sample_dict[sid][:] for sid in sample_dict})

        return sample_groups
