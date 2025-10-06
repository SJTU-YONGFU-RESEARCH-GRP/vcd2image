"""Tests for VCD parser module."""

from typing import TYPE_CHECKING
from unittest.mock import mock_open

import pytest

from vcd2image.core.models import SignalDef
from vcd2image.core.parser import VCDParser

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestVCDParser:
    """Test VCDParser class."""

    @pytest.fixture
    def sample_vcd_content(self) -> str:
        """Sample VCD file content for testing."""
        return """$date
    Date text. For example: 25-May-2007 10:30:00
$end
$version
    VCD generator tool version info text.
$end
$timescale 1ns $end
$scope module top $end
$var wire 8 # data $end
$var wire 1 $ clock $end
$var wire 1 % reset $end
$upscope $end
$enddefinitions $end
#0
$dumpvars
b00000000 #
1$
1%
$end
#10
b11111111 #
#20
0$
#30
0%
"""

    def test_init_with_existing_file(self, tmp_path) -> None:
        """Test parser initialization with existing VCD file."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end\n")

        parser = VCDParser(str(vcd_file))
        assert parser.vcd_file == vcd_file

    def test_init_with_nonexistent_file(self) -> None:
        """Test parser initialization with nonexistent file raises error."""
        with pytest.raises(FileNotFoundError, match="VCD file not found"):
            VCDParser("nonexistent.vcd")

    def test_parse_signals_all(
        self, sample_vcd_content: str, tmp_path, mocker: "MockerFixture"
    ) -> None:
        """Test parsing all signals from VCD file."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text(sample_vcd_content)

        parser = VCDParser(str(vcd_file))
        signals = parser.parse_signals()

        assert len(signals) == 3
        assert "data" in signals
        assert "clock" in signals
        assert "reset" in signals

        assert signals["data"].name == "data"
        assert signals["data"].sid == "#"
        assert signals["data"].length == 8

        assert signals["clock"].name == "clock"
        assert signals["clock"].sid == "$"
        assert signals["clock"].length == 1

    def test_parse_signals_filtered(self, sample_vcd_content: str, tmp_path) -> None:
        """Test parsing specific signals from VCD file."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text(sample_vcd_content)

        parser = VCDParser(str(vcd_file))
        signals = parser.parse_signals(["top/clock", "top/reset"])

        assert len(signals) == 2
        assert "top/clock" in signals
        assert "top/reset" in signals
        assert "top/data" not in signals

    def test_parse_signals_missing_signal(self, sample_vcd_content: str, tmp_path) -> None:
        """Test parsing with nonexistent signal raises ValueError."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text(sample_vcd_content)

        parser = VCDParser(str(vcd_file))

        with pytest.raises(ValueError, match="Can't find signal path: nonexistent"):
            parser.parse_signals(["nonexistent"])

    def test_create_path_dict(self, tmp_path) -> None:
        """Test creating path dictionary from VCD content."""
        vcd_content = """$scope module top $end
$var wire 1 $ clock $end
$var wire 8 # data $end
$upscope $end
$enddefinitions $end
"""

        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text(vcd_content)

        parser = VCDParser(str(vcd_file))

        with open(str(vcd_file), "rt", encoding="utf-8") as fin:
            all_paths, path_dict = parser._create_path_dict(fin)

        assert len(all_paths) == 2
        assert len(path_dict) == 2
        assert "clock" in path_dict
        assert "data" in path_dict
