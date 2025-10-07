"""Data models for VCD signal processing."""

from enum import Enum


class SignalType(Enum):
    """Enumeration of signal types for categorization."""

    INPUT = "input"
    OUTPUT = "output"
    INTERNAL = "internal"
    CLOCK = "clock"
    RESET = "reset"
    UNKNOWN = "unknown"


class SignalDef:
    """Definition of a VCD signal."""

    def __init__(self, name: str, sid: str, length: int, path: str = "") -> None:
        """Initialize signal definition.

        Args:
            name: Signal name.
            sid: Signal identifier.
            length: Signal bit length.
            path: Full hierarchical path to the signal.
        """
        self.name = name
        self.sid = sid
        self.length = length
        self.path = path
        self.fmt = "x"  # Default format
        self.signal_type: SignalType = SignalType.INTERNAL

    def __repr__(self) -> str:
        """String representation of signal definition."""
        return f"SignalDef(name='{self.name}', sid='{self.sid}', length={self.length}, path='{self.path}')"


class SignalCategory:
    """Container for categorized signals."""

    def __init__(self) -> None:
        """Initialize signal category container."""
        self.clocks: list[str] = []
        self.inputs: list[str] = []
        self.outputs: list[str] = []
        self.resets: list[str] = []
        self.internals: list[str] = []
        self.unknowns: list[str] = []

        # Backward compatibility aliases
        self.clock_signals = self.clocks
        self.input_ports = self.inputs
        self.output_ports = self.outputs
        self.internal_signals = self.internals

    def get_ports(self) -> list[str]:
        """Get all input and output ports.

        Returns:
            List of signal paths that are input or output ports.
        """
        return self.input_ports + self.output_ports

    def get_all_signals(self) -> list[str]:
        """Get all categorized signals.

        Returns:
            List of all signal paths.
        """
        return self.clock_signals + self.input_ports + self.output_ports + self.internal_signals

    def __repr__(self) -> str:
        """String representation of signal categories."""
        return (
            f"SignalCategory("
            f"clock_signals={len(self.clock_signals)}, "
            f"input_ports={len(self.input_ports)}, "
            f"output_ports={len(self.output_ports)}, "
            f"internal_signals={len(self.internal_signals)})"
        )
