"""Main VCD to WaveJSON extractor."""

import logging
import sys
from pathlib import Path
from typing import List, Optional

from .generator import WaveJSONGenerator
from .models import SignalDef
from .parser import VCDParser
from .sampler import SignalSampler

logger = logging.getLogger(__name__)


class WaveExtractor:
    """Extract signal values from VCD file and output in WaveJSON format."""

    def __init__(self, vcd_file: str, json_file: str, path_list: List[str]) -> None:
        """Initialize wave extractor.

        Extract signal values from VCD file and output in JSON format.
        Specify VCD filename, JSON filename, and signal path list.
        If json_file is an empty string, standard output is used.
        Use slashes to separate signal path hierarchies.
        The first signal of the list is regarded as clock.
        Other signals are sampled on the negative edge of the clock.

        Args:
            vcd_file: Path to VCD file.
            json_file: Path to output JSON file (empty string for stdout).
            path_list: List of signal paths to extract.
        """
        self.vcd_file = vcd_file
        self.json_file = json_file
        self.path_list = [path.strip('/') for path in path_list]
        self.wave_chunk = 20
        self.start_time = 0
        self.end_time = 0

        # Initialize components
        self.parser = VCDParser(vcd_file)
        self.path_dict: Optional[Dict[str, SignalDef]] = None
        self.fin = None

        self._setup()

    def _setup(self) -> None:
        """Set up the extractor by parsing signal definitions."""
        if self.path_list:
            self.path_dict = self.parser.parse_signals(self.path_list)
        else:
            # Parse all signals if no specific list provided
            self.path_dict = self.parser.parse_signals()
            self.path_list = list(self.path_dict.keys())

    @property
    def wave_chunk(self) -> int:
        """Number of wave samples per time group."""
        return self._wave_chunk

    @wave_chunk.setter
    def wave_chunk(self, value: int) -> None:
        """Set number of wave samples per time group."""
        self._wave_chunk = value

    @property
    def start_time(self) -> int:
        """Sampling start time."""
        return self._start_time

    @start_time.setter
    def start_time(self, value: int) -> None:
        """Set sampling start time."""
        self._start_time = value

    @property
    def end_time(self) -> int:
        """Sampling end time."""
        return self._end_time

    @end_time.setter
    def end_time(self, value: int) -> None:
        """Set sampling end time."""
        self._end_time = value

    def print_props(self) -> int:
        """Display the properties. If an empty path list is given to
        the constructor, display the list created from the VCD file.

        Returns:
            Exit code (0 for success).
        """
        print(f"vcd_file  = '{self.vcd_file}'")
        print(f"json_file = '{self.json_file}'")
        print("path_list = [", end='')
        for i, path in enumerate(self.path_list):
            if i != 0:
                print("             ", end='')
            print(f"'{path}'", end='')
            if i != len(self.path_list) - 1:
                print(",")
            else:
                print("]")
        print(f"wave_chunk = {self.wave_chunk}")
        print(f"start_time = {self.start_time}")
        print(f"end_time   = {self.end_time}")
        return 0

    def wave_format(self, signal_path: str, fmt: str) -> int:
        """Set the display format of the multi-bit signal.

        Args:
            signal_path: Path to the signal.
            fmt: Format character ('b', 'd', 'u', 'x', 'X').

        Returns:
            Exit code (0 for success).

        Raises:
            ValueError: If format character is invalid.
        """
        if fmt not in ('b', 'd', 'u', 'x', 'X'):
            raise ValueError(f"'{fmt}': Invalid format character.")
        if signal_path not in self.path_dict:
            raise ValueError(f"Signal path not found: {signal_path}")
        self.path_dict[signal_path].fmt = fmt
        return 0

    def execute(self) -> int:
        """Perform signal sampling and JSON generation.

        Returns:
            Exit code (0 for success).
        """
        if not self.path_dict:
            raise RuntimeError("No signals to process")

        logger.info("Starting signal extraction and JSON generation")

        # Open VCD file and skip to dump section
        fin = open(self.vcd_file, 'rt', encoding='utf-8')

        # Skip definitions section
        while True:
            line = fin.readline()
            if not line or line.strip() == '$enddefinitions':
                break

        # Set up sampler and generator
        sampler = SignalSampler(self.wave_chunk, self.start_time, self.end_time)
        generator = WaveJSONGenerator(self.path_list, self.path_dict, self.wave_chunk)

        # Get signal IDs
        clock_sid = self.path_dict[self.path_list[0]].sid
        signal_sids = [self.path_dict[path].sid for path in self.path_list]

        # Sample signals
        sample_groups = sampler.sample_signals(fin, clock_sid, signal_sids)

        if not sample_groups:
            logger.warning("No signal samples found")
            fin.close()
            return 1

        # Generate JSON
        json_content = generator.generate_json(sample_groups)

        # Output JSON
        if self.json_file == '':
            fout = sys.stdout
        else:
            logger.info(f"Creating WaveJSON file: {self.json_file}")
            fout = open(self.json_file, 'wt', encoding='utf-8')

        fout.write(json_content)

        fin.close()
        if self.json_file:
            fout.close()

        logger.info("WaveJSON generation completed")
        return 0
