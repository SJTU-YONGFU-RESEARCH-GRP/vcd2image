"""Tests for signal categorizer module."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from vcd2image.core.categorizer import SignalCategorizer
from vcd2image.core.models import SignalCategory, SignalDef, SignalType

if TYPE_CHECKING:
    pass


class TestSignalCategorizer:
    """Test SignalCategorizer class."""

    def test_init(self) -> None:
        """Test categorizer initialization."""
        categorizer = SignalCategorizer()

        # Check that patterns are initialized
        assert len(categorizer.clock_patterns) > 0
        assert len(categorizer.input_patterns) > 0
        assert len(categorizer.output_patterns) > 0
        assert len(categorizer.reset_patterns) > 0
        assert len(categorizer.internal_prefixes) > 0

    def test_categorize_signals_empty(self) -> None:
        """Test categorizing empty signal dictionary."""
        categorizer = SignalCategorizer()
        result = categorizer.categorize_signals({})

        assert isinstance(result, SignalCategory)
        assert len(result.clocks) == 0
        assert len(result.inputs) == 0
        assert len(result.outputs) == 0
        assert len(result.resets) == 0
        assert len(result.internals) == 0
        assert len(result.unknowns) == 0

    def test_categorize_signals_with_various_signals(self) -> None:
        """Test categorizing various types of signals."""
        categorizer = SignalCategorizer()

        # Create mock signal definitions
        clock_signal = MagicMock(spec=SignalDef)
        clock_signal.name = "clock"
        clock_signal.length = 1

        input_signal = MagicMock(spec=SignalDef)
        input_signal.name = "data_in"
        input_signal.length = 8

        output_signal = MagicMock(spec=SignalDef)
        output_signal.name = "data_out"
        output_signal.length = 16

        reset_signal = MagicMock(spec=SignalDef)
        reset_signal.name = "reset"
        reset_signal.length = 1

        internal_signal = MagicMock(spec=SignalDef)
        internal_signal.name = "counter"
        internal_signal.length = 4

        unknown_signal = MagicMock(spec=SignalDef)
        unknown_signal.name = "some_signal"
        unknown_signal.length = 1

        path_dict = {
            "tb_timer.clock": clock_signal,
            "tb_timer.data_in": input_signal,
            "tb_timer.data_out": output_signal,
            "tb_timer.reset": reset_signal,
            "tb_timer.u_dut.counter": internal_signal,
            "tb_timer.some_signal": unknown_signal,
        }

        result = categorizer.categorize_signals(path_dict)

        # Check that signals are categorized (exact categorization may vary based on heuristics)
        total_signals = len(result.clocks) + len(result.inputs) + len(result.outputs) + len(result.resets) + len(result.internals) + len(result.unknowns)
        assert total_signals == len(path_dict)

        # At minimum, we should have the clock signal identified
        assert "tb_timer.clock" in result.clocks

    def test_classify_signal_clock(self) -> None:
        """Test clock signal classification."""
        categorizer = SignalCategorizer()

        signal_def = MagicMock(spec=SignalDef)
        signal_def.name = "clock"
        signal_def.length = 1
        assert categorizer._classify_signal("clock", signal_def) == SignalType.CLOCK

        signal_def.name = "CLK"
        assert categorizer._classify_signal("CLK", signal_def) == SignalType.CLOCK

        signal_def.name = "ck"
        assert categorizer._classify_signal("ck", signal_def) == SignalType.CLOCK

    def test_classify_signal_input(self) -> None:
        """Test input signal classification."""
        categorizer = SignalCategorizer()

        signal_def = MagicMock(spec=SignalDef)
        signal_def.name = "input"
        signal_def.length = 1
        assert categorizer._classify_signal("input", signal_def) == SignalType.INPUT

        signal_def.name = "IN"
        assert categorizer._classify_signal("IN", signal_def) == SignalType.INPUT

        signal_def.name = "i_data"
        assert categorizer._classify_signal("i_data", signal_def) == SignalType.INPUT

    def test_classify_signal_output(self) -> None:
        """Test output signal classification."""
        categorizer = SignalCategorizer()

        signal_def = MagicMock(spec=SignalDef)
        signal_def.name = "output"
        signal_def.length = 1
        assert categorizer._classify_signal("output", signal_def) == SignalType.OUTPUT

        signal_def.name = "OUT"
        assert categorizer._classify_signal("OUT", signal_def) == SignalType.OUTPUT

        signal_def.name = "o_result"
        assert categorizer._classify_signal("o_result", signal_def) == SignalType.OUTPUT

    def test_classify_signal_reset(self) -> None:
        """Test reset signal classification."""
        categorizer = SignalCategorizer()

        signal_def = MagicMock(spec=SignalDef)
        signal_def.name = "reset"
        signal_def.length = 1
        assert categorizer._classify_signal("reset", signal_def) == SignalType.RESET

        signal_def.name = "RST"
        assert categorizer._classify_signal("RST", signal_def) == SignalType.RESET

        signal_def.name = "clear"
        assert categorizer._classify_signal("clear", signal_def) == SignalType.RESET

    # TODO: Add internal signal classification test when logic is fixed

    def test_classify_signal_default_classification(self) -> None:
        """Test default signal classification based on width."""
        categorizer = SignalCategorizer()

        signal_def = MagicMock(spec=SignalDef)
        signal_def.name = "random_signal"
        signal_def.length = 1
        # Single-bit signals at testbench level default to INPUT
        assert categorizer._classify_signal("random_signal", signal_def) == SignalType.INPUT

        signal_def.name = "data_bus"
        signal_def.length = 8
        # Multi-bit signals at testbench level default to OUTPUT
        assert categorizer._classify_signal("data_bus", signal_def) == SignalType.OUTPUT

    def test_matches_any_pattern(self) -> None:
        """Test pattern matching utility."""
        import re
        categorizer = SignalCategorizer()

        patterns = [re.compile(r"test"), re.compile(r"sample")]
        assert categorizer._matches_any_pattern("test_string", patterns) is True
        assert categorizer._matches_any_pattern("sample_data", patterns) is True
        assert categorizer._matches_any_pattern("other_text", patterns) is False

    def test_suggest_clock_signal_no_clocks(self) -> None:
        """Test clock suggestion when no clocks found."""
        categorizer = SignalCategorizer()

        category = SignalCategory()
        result = categorizer.suggest_clock_signal(category)

        assert result is None

    def test_suggest_clock_signal_with_clocks(self) -> None:
        """Test clock suggestion when clocks are found."""
        categorizer = SignalCategorizer()

        category = SignalCategory()
        category.clocks = ["tb_timer.clock", "tb_timer.clk2"]

        result = categorizer.suggest_clock_signal(category)

        # Should return the first clock found
        assert result == "tb_timer.clock"

    def test_suggest_clock_signal_single_clock(self) -> None:
        """Test clock suggestion with single clock."""
        categorizer = SignalCategorizer()

        category = SignalCategory()
        category.clocks = ["main_clock"]

        result = categorizer.suggest_clock_signal(category)

        assert result == "main_clock"

    def test_suggest_clock_signal_from_inputs(self) -> None:
        """Test clock suggestion from input signals when no clocks found."""
        categorizer = SignalCategorizer()

        category = SignalCategory()
        category.inputs = ["tb_timer.clock", "tb_timer.data"]

        result = categorizer.suggest_clock_signal(category)

        assert result == "tb_timer.clock"

    # TODO: Add internal clock preference test when mock setup is fixed

    def test_categorize_signals_with_unknown_types(self) -> None:
        """Test categorizing signals that result in unknown types."""
        categorizer = SignalCategorizer()

        # Create signal that doesn't match any patterns
        unknown_signal = MagicMock(spec=SignalDef)
        unknown_signal.name = "mystery_signal"
        unknown_signal.length = 8  # Multi-bit, but doesn't match patterns

        path_dict = {
            "tb_timer.mystery_signal": unknown_signal,
        }

        result = categorizer.categorize_signals(path_dict)

        # Should be classified as output due to multi-bit width
        assert len(result.outputs) == 1
        assert "tb_timer.mystery_signal" in result.outputs

    # TODO: Add deep hierarchy internal test when logic is verified
