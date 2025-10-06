"""Data models for VCD signal processing."""

from typing import Dict, List


class SignalDef:
    """Definition of a VCD signal."""

    def __init__(self, name: str, sid: str, length: int) -> None:
        """Initialize signal definition.

        Args:
            name: Signal name.
            sid: Signal identifier.
            length: Signal bit length.
        """
        self.name = name
        self.sid = sid
        self.length = length
        self.fmt = 'x'  # Default format

    def __repr__(self) -> str:
        """String representation of signal definition."""
        return f"SignalDef(name='{self.name}', sid='{self.sid}', length={self.length})"
