"""VCD file parser for extracting signal definitions and hierarchies."""

import logging
from pathlib import Path
from typing import TextIO

from .models import SignalDef

logger = logging.getLogger(__name__)


class VCDParser:
    """Parser for VCD (Value Change Dump) files."""

    def __init__(self, vcd_file: str) -> None:
        """Initialize VCD parser.

        Args:
            vcd_file: Path to VCD file.
        """
        self.vcd_file = Path(vcd_file)
        if not self.vcd_file.exists():
            raise FileNotFoundError(f"VCD file not found: {vcd_file}")

    def parse_signals(self, path_list: list[str] | None = None) -> dict[str, SignalDef]:
        """Parse signal definitions from VCD file.

        Args:
            path_list: List of signal paths to extract. If None, extract all signals.

        Returns:
            Dictionary mapping signal paths to signal definitions.

        Raises:
            ValueError: If requested signals are not found.
        """
        logger.info(f"Parsing VCD file: {self.vcd_file}")

        with open(self.vcd_file, encoding="utf-8") as fin:
            all_paths, path_dict = self._create_path_dict(fin)

        if path_list:
            path_dict = self._filter_path_dict(path_list, path_dict)

        logger.info(f"Found {len(path_dict)} signals")
        return path_dict

    def _create_path_dict(self, fin: TextIO) -> tuple[list[str], dict[str, SignalDef]]:
        """Create path dictionary from VCD definitions section.

        Args:
            fin: Open file handle to VCD file.

        Returns:
            Tuple of (all_paths, path_dict).
        """
        hier_list: list[str] = []
        path_list: list[str] = []
        path_dict: dict[str, SignalDef] = {}

        while True:
            line = fin.readline()
            if not line:
                raise EOFError("Can't find word '$enddefinitions' in VCD file.")

            words = line.split()
            if not words:
                continue

            if words[0] == "$enddefinitions":
                return path_list, path_dict

            if words[0] == "$scope":
                hier_list.append(words[2])
            elif words[0] == "$var":
                path = "/".join(hier_list + [words[4]])
                path_list.append(path)
                path_dict[path] = SignalDef(
                    name=words[4], sid=words[3], length=int(words[2]), path=path
                )
            elif words[0] == "$upscope":
                if hier_list:
                    hier_list.pop()

    def _filter_path_dict(
        self, path_list: list[str], path_dict: dict[str, SignalDef]
    ) -> dict[str, SignalDef]:
        """Filter path dictionary to only include requested signals.

        Args:
            path_list: List of signal paths to keep.
            path_dict: Full path dictionary.

        Returns:
            Filtered path dictionary.

        Raises:
            ValueError: If any requested path is not found.
        """
        filtered_dict = {}
        for path in path_list:
            path = path.strip("/")
            signal_def = path_dict.get(path)
            if not signal_def:
                raise ValueError(f"Can't find signal path: {path}")
            filtered_dict[path] = signal_def
        return filtered_dict
