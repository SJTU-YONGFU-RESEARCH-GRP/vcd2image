"""Tests for data models."""

from typing import TYPE_CHECKING

from vcd2image.core.models import SignalDef

if TYPE_CHECKING:
    pass


class TestSignalDef:
    """Test SignalDef class."""

    def test_init(self) -> None:
        """Test SignalDef initialization."""
        signal = SignalDef(name="test_signal", sid="!", length=8)
        assert signal.name == "test_signal"
        assert signal.sid == "!"
        assert signal.length == 8
        assert signal.fmt == "x"  # default format

    def test_repr(self) -> None:
        """Test string representation."""
        signal = SignalDef(name="test", sid="!", length=1)
        repr_str = repr(signal)
        assert "SignalDef" in repr_str
        assert "test" in repr_str
        assert "!" in repr_str
        assert "1" in repr_str
