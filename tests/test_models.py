"""Tests for data models."""

from typing import TYPE_CHECKING

import pytest

from vcd2image.core.models import SignalDef

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


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
