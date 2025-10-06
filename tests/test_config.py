"""Tests for configuration module."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from vcd2image.utils.config import Config

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestConfig:
    """Test Config dataclass."""

    def test_init_default_values(self) -> None:
        """Test Config initialization with default values."""
        config = Config()

        assert config.wave_chunk == 20
        assert config.start_time == 0
        assert config.end_time == 0
        assert config.skin == "default"
        assert config.width is None
        assert config.height is None
        assert config.output_format == "png"

    def test_init_custom_values(self) -> None:
        """Test Config initialization with custom values."""
        config = Config(
            wave_chunk=10,
            start_time=5,
            end_time=100,
            skin="dark",
            width=800,
            height=600,
            output_format="svg",
        )

        assert config.wave_chunk == 10
        assert config.start_time == 5
        assert config.end_time == 100
        assert config.skin == "dark"
        assert config.width == 800
        assert config.height == 600
        assert config.output_format == "svg"

    def test_from_args(self) -> None:
        """Test creating Config from command-line arguments."""
        # Mock argparse namespace
        mock_args = MagicMock()
        mock_args.wave_chunk = 15
        mock_args.start_time = 10
        mock_args.end_time = 200

        config = Config.from_args(mock_args)

        assert config.wave_chunk == 15
        assert config.start_time == 10
        assert config.end_time == 200
        # Other fields should be default
        assert config.skin == "default"
        assert config.output_format == "png"

    def test_from_args_missing_attributes(self) -> None:
        """Test from_args handles missing attributes gracefully."""
        mock_args = MagicMock()
        # Remove attributes to test getattr fallback
        del mock_args.wave_chunk
        del mock_args.start_time
        del mock_args.end_time

        config = Config.from_args(mock_args)

        # Should use default values
        assert config.wave_chunk == 20
        assert config.start_time == 0
        assert config.end_time == 0

    def test_from_env(self) -> None:
        """Test creating Config from environment variables."""
        # Mock environment variables
        mock_env = {
            "VCD2IMAGE_WAVE_CHUNK": "25",
            "VCD2IMAGE_START_TIME": "50",
            "VCD2IMAGE_END_TIME": "500",
            "VCD2IMAGE_SKIN": "narrow",
            "VCD2IMAGE_FORMAT": "pdf",
        }

        with pytest.MonkeyPatch().context() as m:
            for key, value in mock_env.items():
                m.setenv(key, value)

            config = Config.from_env()

            assert config.wave_chunk == 25
            assert config.start_time == 50
            assert config.end_time == 500
            assert config.skin == "narrow"
            assert config.output_format == "pdf"

    def test_from_env_missing_variables(self) -> None:
        """Test from_env uses defaults when environment variables are missing."""
        # Ensure no relevant env vars are set
        with pytest.MonkeyPatch().context() as m:
            # Clear any existing env vars
            for key in [
                "VCD2IMAGE_WAVE_CHUNK",
                "VCD2IMAGE_START_TIME",
                "VCD2IMAGE_END_TIME",
                "VCD2IMAGE_SKIN",
                "VCD2IMAGE_FORMAT",
            ]:
                m.delenv(key, raising=False)

            config = Config.from_env()

            assert config.wave_chunk == 20
            assert config.start_time == 0
            assert config.end_time == 0
            assert config.skin == "default"
            assert config.output_format == "png"

    def test_to_dict(self) -> None:
        """Test converting Config to dictionary."""
        config = Config(
            wave_chunk=12,
            start_time=3,
            end_time=99,
            skin="lowkey",
            width=1024,
            height=768,
            output_format="jpg",
        )

        config_dict = config.to_dict()

        expected = {
            "wave_chunk": 12,
            "start_time": 3,
            "end_time": 99,
            "skin": "lowkey",
            "width": 1024,
            "height": 768,
            "output_format": "jpg",
        }

        assert config_dict == expected

    def test_to_dict_default_values(self) -> None:
        """Test to_dict with default Config values."""
        config = Config()
        config_dict = config.to_dict()

        expected = {
            "wave_chunk": 20,
            "start_time": 0,
            "end_time": 0,
            "skin": "default",
            "width": None,
            "height": None,
            "output_format": "png",
        }

        assert config_dict == expected
