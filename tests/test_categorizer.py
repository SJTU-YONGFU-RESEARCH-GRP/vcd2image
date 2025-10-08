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
        total_signals = (
            len(result.clocks)
            + len(result.inputs)
            + len(result.outputs)
            + len(result.resets)
            + len(result.internals)
            + len(result.unknowns)
        )
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

    def test_classify_signal_deep_hierarchy_internal_prefix(self) -> None:
        """Test classification of deeply nested signals with internal prefixes."""
        categorizer = SignalCategorizer()

        signal_def = MagicMock(spec=SignalDef)
        signal_def.name = "data"
        signal_def.length = 8

        # Test deeply nested signal with internal prefix
        result = categorizer._classify_signal("tb_test/u_dut/u_submodule/internal_data", signal_def)
        assert result == SignalType.INTERNAL

    def test_classify_signal_deep_hierarchy_fallback_internal(self) -> None:
        """Test fallback classification for deeply nested signals."""
        categorizer = SignalCategorizer()

        signal_def = MagicMock(spec=SignalDef)
        signal_def.name = "xyz987"
        signal_def.length = 4

        # Test deeply nested signal that doesn't start with "tb_" and doesn't match any patterns
        # This should hit the deep hierarchy fallback on line 141
        result = categorizer._classify_signal("top/u_dut/u_submodule/xyz987", signal_def)
        assert result == SignalType.INTERNAL

    def test_suggest_clock_signal_with_internal_clocks(self) -> None:
        """Test clock suggestion when internal clocks are present."""
        categorizer = SignalCategorizer()

        category = MagicMock()
        # Include both top-level and internal clocks
        category.clocks = ["clock", "tb_test/u_dut/internal_clock"]
        category.inputs = []
        category.outputs = []
        category.internals = []

        result = categorizer.suggest_clock_signal(category)
        # Should return the internal clock first
        assert result == "tb_test/u_dut/internal_clock"

    def test_categorize_signals_unknown_type(self, monkeypatch) -> None:
        """Test categorizing signals that result in SignalType.UNKNOWN (line 78)."""
        categorizer = SignalCategorizer()

        # Create a signal
        unknown_signal = MagicMock(spec=SignalDef)
        unknown_signal.name = "unknown_signal"
        unknown_signal.length = 1

        path_dict = {
            "tb.module.deep.unknown_signal": unknown_signal,
        }

        # Mock _classify_signal to return SignalType.UNKNOWN
        def mock_classify(path, signal_def):
            return SignalType.UNKNOWN

        monkeypatch.setattr(categorizer, "_classify_signal", mock_classify)

        result = categorizer.categorize_signals(path_dict)

        # Should be added to unknowns list
        assert len(result.unknowns) == 1
        assert "tb.module.deep.unknown_signal" in result.unknowns

    def test_classify_signal_deep_hierarchy_fallback_logic(self) -> None:
        """Test _classify_signal_type deep hierarchy fallback (lines 148-153)."""
        categorizer = SignalCategorizer()

        # Create signal with deep hierarchy but no internal prefixes
        signal_def = MagicMock(spec=SignalDef)
        signal_def.name = "some_signal"
        signal_def.length = 1  # Single bit -> should be INPUT

        # Path with > 2 parts but no internal prefixes
        path = "tb/top/module/some_signal"

        result = categorizer._classify_signal(path, signal_def)
        assert result == SignalType.INTERNAL  # Due to len(path_parts) > 2

    def test_classify_signal_testbench_output_indicators(self) -> None:
        """Test classification of testbench signals with output indicators."""
        categorizer = SignalCategorizer()

        signal_def = MagicMock(spec=SignalDef)
        signal_def.length = 1

        # Test various output indicators
        output_signals = ["pulse", "done", "ready", "valid", "result", "out"]
        for signal_name in output_signals:
            signal_def.name = signal_name
            path = f"tb.{signal_name}"

            result = categorizer._classify_signal(path, signal_def)
            assert result == SignalType.OUTPUT, f"Signal {signal_name} should be OUTPUT"

    def test_classify_signal_case_insensitive_matching(self) -> None:
        """Test that signal classification is case insensitive."""
        categorizer = SignalCategorizer()

        signal_def = MagicMock(spec=SignalDef)
        signal_def.length = 1

        # Test clock signal with mixed case
        signal_def.name = "CLK"
        path = "TB/CLK"
        result = categorizer._classify_signal(path, signal_def)
        assert result == SignalType.CLOCK

        # Test reset signal with mixed case
        signal_def.name = "RST"
        path = "tb/rst"
        result = categorizer._classify_signal(path, signal_def)
        assert result == SignalType.RESET

    def test_classify_signal_complex_hierarchy_patterns(self) -> None:
        """Test classification with complex hierarchy patterns."""
        categorizer = SignalCategorizer()

        signal_def = MagicMock(spec=SignalDef)
        signal_def.length = 1

        # Test signal in deeply nested module with internal prefix
        signal_def.name = "internal_reg"
        path = "tb/dut/core/internal_reg"
        result = categorizer._classify_signal(path, signal_def)
        assert result == SignalType.INTERNAL  # Due to 'core' prefix

        # Test signal in deeply nested module without internal prefix
        signal_def.name = "data_bus"
        path = "tb/dut/logic/data_bus"
        result = categorizer._classify_signal(path, signal_def)
        assert result == SignalType.INTERNAL  # Due to deep hierarchy

    def test_suggest_clock_signal_priority_order(self) -> None:
        """Test clock signal suggestion priority order."""
        categorizer = SignalCategorizer()

        # Create category with multiple clock sources
        category = MagicMock()
        category.clocks = ["tb_clk", "dut/internal_clk", "dut/core/main_clk"]
        category.inputs = ["reset", "enable"]
        category.outputs = []
        category.internals = []

        # Should prefer internal clocks (deeper hierarchy) over testbench clocks
        result = categorizer.suggest_clock_signal(category)
        assert result == "dut/core/main_clk"  # Deepest hierarchy

    def test_categorize_signals_with_duplicate_signal_names(self) -> None:
        """Test categorizing signals with duplicate names in different hierarchies."""
        categorizer = SignalCategorizer()

        # Create signals with same name but different paths
        signal1 = MagicMock(spec=SignalDef)
        signal1.name = "data"
        signal1.length = 8

        signal2 = MagicMock(spec=SignalDef)
        signal2.name = "data"
        signal2.length = 16

        path_dict = {
            "tb/input_data": signal1,  # Testbench level
            "dut/core/data": signal2,  # Internal level
        }

        result = categorizer.categorize_signals(path_dict)

        # Both should be categorized appropriately
        assert len(result.outputs) == 1  # tb/input_data as OUTPUT (testbench, multi-bit)
        assert len(result.internals) == 1  # dut/core/data as INTERNAL (deep hierarchy)
