"""Tests for WaveJSON generator module."""

from typing import TYPE_CHECKING

import pytest

from vcd2image.core.generator import WaveJSONGenerator
from vcd2image.core.models import SignalDef

if TYPE_CHECKING:
    pass


class TestWaveJSONGenerator:
    """Test WaveJSONGenerator class."""

    @pytest.fixture
    def sample_signals(self) -> dict[str, SignalDef]:
        """Sample signal definitions for testing."""
        return {
            "clock": SignalDef("clock", "$", 1),
            "data": SignalDef("data", "#", 8),
            "reset": SignalDef("reset", "%", 1),
        }

    @pytest.fixture
    def sample_sample_groups(self) -> list[dict[str, list[str]]]:
        """Sample signal sample groups for testing."""
        return [
            {
                "$": ["1", "1"],
                "#": ["00000000", "11111111"],
                "%": ["1", "0"],
            },
            {
                "$": ["0", "0"],
                "#": ["10101010", "01010101"],
                "%": ["0", "1"],
            },
        ]

    def test_init(self, sample_signals: dict[str, SignalDef]) -> None:
        """Test generator initialization."""
        path_list = ["clock", "data", "reset"]
        generator = WaveJSONGenerator(path_list, sample_signals, wave_chunk=2)

        assert generator.path_list == path_list
        assert generator.path_dict == sample_signals
        assert generator.wave_chunk == 2
        assert generator.clock_name == "clock"
        assert generator.name_width == 5  # length of "clock"

    def test_generate_json_basic(
        self, sample_signals: dict[str, SignalDef], sample_sample_groups: list[dict[str, list[str]]]
    ) -> None:
        """Test basic JSON generation."""
        path_list = ["clock", "data", "reset"]
        generator = WaveJSONGenerator(path_list, sample_signals, wave_chunk=2)

        json_output = generator.generate_json(sample_sample_groups)

        # Basic structure checks
        assert json_output.startswith('{ "head": {"tock":1},')
        assert '"signal": [' in json_output
        assert '"name": "clock"' in json_output
        assert '"name": "data"' in json_output
        assert '"name": "reset"' in json_output
        assert json_output.endswith(" ]\n}")

    def test_create_header(self, sample_signals: dict[str, SignalDef]) -> None:
        """Test header creation."""
        path_list = ["clock", "data"]
        generator = WaveJSONGenerator(path_list, sample_signals, wave_chunk=2)

        header = generator._create_header()

        assert '"head": {"tock":1}' in header
        assert '"name": "clock"' in header
        assert '"wave": "p."' in header  # clock pattern for chunk size 2

    def test_create_wave_single_bit(self, sample_signals) -> None:
        """Test wave creation for single-bit signals."""
        path_list = ["clock", "data"]
        generator = WaveJSONGenerator(path_list, sample_signals, 2)

        # Test with constant values
        wave = generator._create_wave(["1", "1"])
        assert wave == '"1."'

        # Test with changing values
        wave = generator._create_wave(["1", "0", "1"])
        assert wave == '"101"'

        # Test empty samples
        wave = generator._create_wave([])
        assert wave == '""'

    def test_create_wave_data_multi_bit(self, sample_signals) -> None:
        """Test wave and data creation for multi-bit signals."""
        path_list = ["clock", "data"]
        generator = WaveJSONGenerator(path_list, sample_signals, 2)

        # Test binary data
        samples = ["1010", "1111"]
        wave, data = generator._create_wave_data(samples, 4, "b")

        assert wave == '"=="'  # equals signs for data values
        assert data == '"1010 1111"'

        # Test empty samples
        wave, data = generator._create_wave_data([], 4, "b")
        assert wave == '""'
        assert data == '""'

    def test_format_value_binary(self, sample_signals) -> None:
        """Test binary value formatting."""
        path_list = ["clock", "data"]
        generator = WaveJSONGenerator(path_list, sample_signals, 2)

        # Test binary format
        formatted = generator._format_value("1010", 4, "b")
        assert formatted == "1010"

        # Test signed decimal format (two's complement)
        formatted = generator._format_value("1010", 4, "d")
        assert formatted == "-6"

        # Test unsigned decimal format
        formatted = generator._format_value("1010", 4, "u")
        assert formatted == "10"

        # Test hex format
        formatted = generator._format_value("1111", 4, "x")
        assert formatted == "f"

        # Test uppercase hex format
        formatted = generator._format_value("1111", 4, "X")
        assert formatted == "F"

    def test_format_value_negative_decimal(self, sample_signals) -> None:
        """Test negative decimal formatting (two's complement)."""
        path_list = ["clock", "data"]
        generator = WaveJSONGenerator(path_list, sample_signals, 2)

        # Test negative value (sign bit set for 4-bit number)
        formatted = generator._format_value("1000", 4, "d")  # 8 in unsigned, -8 in signed
        assert formatted == "-8"

    def test_format_value_invalid_binary(self, sample_signals) -> None:
        """Test formatting with invalid binary string."""
        path_list = ["clock", "data"]
        generator = WaveJSONGenerator(path_list, sample_signals, 2)

        formatted = generator._format_value("invalid", 4, "b")
        assert formatted == "x"

    def test_is_binary_string(self, sample_signals) -> None:
        """Test binary string validation."""
        path_list = ["clock", "data"]
        generator = WaveJSONGenerator(path_list, sample_signals, 2)

        assert generator._is_binary_string("1010") is True
        assert generator._is_binary_string("1020") is False
        assert generator._is_binary_string("abc") is False
        assert generator._is_binary_string("") is False
