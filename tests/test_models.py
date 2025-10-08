"""Tests for data models."""

from typing import TYPE_CHECKING

from vcd2image.core.models import SignalCategory, SignalDef

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

    def test_init_with_path(self) -> None:
        """Test SignalDef initialization with path."""
        signal = SignalDef(name="test", sid="!", length=8, path="tb/u_dut/test")
        assert signal.name == "test"
        assert signal.sid == "!"
        assert signal.length == 8
        assert signal.path == "tb/u_dut/test"
        assert signal.fmt == "x"  # default format

    def test_init_edge_cases(self) -> None:
        """Test SignalDef initialization with edge cases."""
        # Empty name
        signal = SignalDef(name="", sid="", length=0)
        assert signal.name == ""
        assert signal.sid == ""
        assert signal.length == 0

        # Very large length
        signal = SignalDef(name="big_signal", sid="!", length=999999)
        assert signal.length == 999999


class TestSignalCategory:
    """Test SignalCategory class."""

    def test_init(self) -> None:
        """Test SignalCategory initialization."""
        category = SignalCategory()
        assert category.clocks == []
        assert category.inputs == []
        assert category.outputs == []
        assert category.resets == []
        assert category.internals == []
        assert category.unknowns == []

    def test_backward_compatibility_aliases(self) -> None:
        """Test backward compatibility aliases."""
        category = SignalCategory()
        assert category.clock_signals is category.clocks
        assert category.input_ports is category.inputs
        assert category.output_ports is category.outputs
        assert category.internal_signals is category.internals

    def test_get_ports(self) -> None:
        """Test get_ports method."""
        category = SignalCategory()
        category.input_ports = ["input1", "input2"]
        category.output_ports = ["output1", "output2"]

        ports = category.get_ports()
        assert ports == ["input1", "input2", "output1", "output2"]

    def test_get_all_signals(self) -> None:
        """Test get_all_signals method."""
        category = SignalCategory()
        category.clock_signals = ["clock"]
        category.input_ports = ["input1"]
        category.output_ports = ["output1"]
        category.internal_signals = ["internal1"]

        all_signals = category.get_all_signals()
        assert all_signals == ["clock", "input1", "output1", "internal1"]

    def test_repr(self) -> None:
        """Test string representation."""
        category = SignalCategory()
        category.clock_signals = ["clock"]
        category.input_ports = ["input1", "input2"]
        category.output_ports = ["output1"]

        repr_str = repr(category)
        assert "SignalCategory" in repr_str
        assert "clock_signals=1" in repr_str
        assert "input_ports=2" in repr_str
        assert "output_ports=1" in repr_str
        assert "internal_signals=0" in repr_str

    def test_empty_category_methods(self) -> None:
        """Test methods with empty categories."""
        category = SignalCategory()

        assert category.get_ports() == []
        assert category.get_all_signals() == []
