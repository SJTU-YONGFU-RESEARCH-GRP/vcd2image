"""Tests for wave extractor module."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from vcd2image.core.extractor import WaveExtractor

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestWaveExtractor:
    """Test WaveExtractor class."""

    @pytest.fixture
    def sample_vcd_content(self) -> str:
        """Sample VCD file content for testing."""
        return """$date
Test date
$end
$timescale 1ns $end
$scope module top $end
$var wire 1 $ clock $end
$var wire 8 # data $end
$var wire 1 % reset $end
$upscope $end
$enddefinitions $end
#0
$dumpvars
1$
b00000000 #
1%
$end
#10
b11111111 #
#20
0$
#30
0%
"""

    def test_init(self, tmp_path, mocker) -> None:
        """Test extractor initialization."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end\n")

        # Mock the parser to avoid parsing issues during init
        mock_parser = mocker.patch("vcd2image.core.extractor.VCDParser")
        mock_parser_instance = mocker.MagicMock()
        mock_parser.return_value = mock_parser_instance

        extractor = WaveExtractor(str(vcd_file), "output.json", ["top/clock", "top/data"])

        assert extractor.vcd_file == str(vcd_file)
        assert extractor.json_file == "output.json"
        assert extractor.path_list == ["top/clock", "top/data"]
        assert extractor.wave_chunk == 20
        assert extractor.start_time == 0
        assert extractor.end_time == 0

    def test_wave_chunk_property(self, mocker) -> None:
        """Test wave_chunk property getter/setter."""
        mocker.patch("vcd2image.core.extractor.VCDParser")
        extractor = WaveExtractor("dummy.vcd", "dummy.json", [])

        extractor.wave_chunk = 10
        assert extractor.wave_chunk == 10

        extractor.wave_chunk = 50
        assert extractor.wave_chunk == 50

    def test_start_time_property(self, mocker) -> None:
        """Test start_time property getter/setter."""
        mocker.patch("vcd2image.core.extractor.VCDParser")
        extractor = WaveExtractor("dummy.vcd", "dummy.json", [])

        extractor.start_time = 100
        assert extractor.start_time == 100

    def test_end_time_property(self, mocker) -> None:
        """Test end_time property getter/setter."""
        mocker.patch("vcd2image.core.extractor.VCDParser")
        extractor = WaveExtractor("dummy.vcd", "dummy.json", [])

        extractor.end_time = 1000
        assert extractor.end_time == 1000

    def test_setup_with_signals(self, tmp_path, mocker: "MockerFixture") -> None:
        """Test setup with specific signal list."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end\n")

        # Mock the parser BEFORE creating extractor to avoid real parsing
        mock_parser = mocker.patch("vcd2image.core.extractor.VCDParser")
        mock_parser_instance = mocker.MagicMock()
        mock_parser.return_value = mock_parser_instance
        mock_signals = {"top/clock": MagicMock()}
        mock_parser_instance.parse_signals.return_value = mock_signals

        # Pass empty path_dict to prevent automatic _setup() call in __init__
        extractor = WaveExtractor(str(vcd_file), "output.json", ["top/clock"], path_dict={})
        # Manually call _setup to test parsing logic
        extractor._setup()

        mock_parser_instance.parse_signals.assert_called_with(["top/clock"])
        assert extractor.path_dict == mock_signals

    def test_setup_without_signals(self, tmp_path, mocker: "MockerFixture") -> None:
        """Test setup without specific signal list."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end\n")

        # Mock the parser BEFORE creating extractor to avoid real parsing
        mock_parser = mocker.patch("vcd2image.core.extractor.VCDParser")
        mock_parser_instance = mocker.MagicMock()
        mock_parser.return_value = mock_parser_instance
        mock_signals = {"clock": MagicMock(), "data": MagicMock()}
        mock_parser_instance.parse_signals.return_value = mock_signals

        # Pass None for path_dict to trigger _setup() call in __init__
        extractor = WaveExtractor(str(vcd_file), "output.json", [], path_dict=None)

        # Should call parse_signals with no args, then set path_list
        mock_parser_instance.parse_signals.assert_called_once_with()
        assert extractor.path_list == ["clock", "data"]

    def test_print_props(self, capsys, mocker) -> None:
        """Test printing properties."""
        mocker.patch("vcd2image.core.extractor.VCDParser")
        extractor = WaveExtractor("test.vcd", "output.json", ["clock", "data"])
        extractor.wave_chunk = 10
        extractor.start_time = 5
        extractor.end_time = 100

        result = extractor.print_props()

        assert result == 0
        captured = capsys.readouterr()
        assert "vcd_file  = 'test.vcd'" in captured.out
        assert "json_file = 'output.json'" in captured.out
        assert "path_list = [" in captured.out
        assert "'clock'" in captured.out
        assert "'data'" in captured.out
        assert "wave_chunk = 10" in captured.out
        assert "start_time = 5" in captured.out
        assert "end_time   = 100" in captured.out

    def test_wave_format_valid(self, mocker) -> None:
        """Test setting valid wave format."""
        mocker.patch("vcd2image.core.extractor.VCDParser")
        extractor = WaveExtractor("dummy.vcd", "dummy.json", [])
        extractor.path_dict = {"signal1": MagicMock()}

        result = extractor.wave_format("signal1", "b")
        assert result == 0
        assert extractor.path_dict["signal1"].fmt == "b"

    def test_wave_format_invalid_character(self, mocker) -> None:
        """Test setting invalid wave format raises ValueError."""
        mocker.patch("vcd2image.core.extractor.VCDParser")
        extractor = WaveExtractor("dummy.vcd", "dummy.json", [])

        with pytest.raises(ValueError, match="'z': Invalid format character"):
            extractor.wave_format("signal1", "z")

    def test_wave_format_missing_signal(self, mocker) -> None:
        """Test formatting nonexistent signal raises ValueError."""
        mocker.patch("vcd2image.core.extractor.VCDParser")
        extractor = WaveExtractor("dummy.vcd", "dummy.json", [])
        extractor.path_dict = {}

        with pytest.raises(ValueError, match="Signal path not found: nonexistent"):
            extractor.wave_format("nonexistent", "b")

    def test_execute_success(self, tmp_path, mocker: "MockerFixture") -> None:
        """Test successful execution."""
        # Create a dummy VCD file
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions\n$dumpvars\n$end\n")

        with mocker.patch("vcd2image.core.extractor.VCDParser"):
            extractor = WaveExtractor(str(vcd_file), "", ["clock"])  # stdout output
            extractor.path_dict = {"clock": MagicMock(sid="$")}

        # Mock components
        mock_sampler = mocker.patch("vcd2image.core.extractor.SignalSampler")
        mock_generator = mocker.patch("vcd2image.core.extractor.WaveJSONGenerator")

        mock_sampler_instance = MagicMock()
        mock_sampler.return_value = mock_sampler_instance
        mock_sampler_instance.sample_signals.return_value = [{"$": ["1"]}]

        mock_generator_instance = MagicMock()
        mock_generator.return_value = mock_generator_instance
        mock_generator_instance.generate_json.return_value = '{"test": "json"}'

        # Mock stdout for output
        mock_stdout = mocker.patch("sys.stdout")

        result = extractor.execute()

        assert result == 0
        mock_stdout.write.assert_called_once_with('{"test": "json"}')

    def test_execute_no_signals(self, mocker) -> None:
        """Test execution with no signals raises error."""
        mocker.patch("vcd2image.core.extractor.VCDParser")
        extractor = WaveExtractor("test.vcd", "output.json", [])
        extractor.path_dict = None

        with pytest.raises(RuntimeError, match="No signals to process"):
            extractor.execute()

    def test_execute_no_samples(self, tmp_path, mocker: "MockerFixture") -> None:
        """Test execution with no samples returns error."""
        # Create a dummy VCD file
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions\n$dumpvars\n$end\n")

        with mocker.patch("vcd2image.core.extractor.VCDParser"):
            extractor = WaveExtractor(str(vcd_file), "output.json", ["clock"])
            extractor.path_dict = {"clock": MagicMock(sid="$")}

        # Mock components to return empty samples
        mock_sampler = mocker.patch("vcd2image.core.extractor.SignalSampler")
        mock_sampler_instance = MagicMock()
        mock_sampler.return_value = mock_sampler_instance
        mock_sampler_instance.sample_signals.return_value = []

        result = extractor.execute()

        assert result == 1

    def test_real_vcd_parsing(self, real_vcd_file: Path) -> None:
        """Test parsing a real VCD file generated by iverilog simulation."""
        from vcd2image.core.parser import VCDParser

        # Test that we can parse signals from a real VCD file
        parser = VCDParser(str(real_vcd_file))
        path_dict = parser.parse_signals()

        # Should find multiple signals from the timer testbench
        assert len(path_dict) > 0, "No signals found in VCD file"
        assert "tb_timer/clock" in path_dict, "Clock signal not found"
        assert "tb_timer/pulse" in path_dict, "Pulse signal not found"
