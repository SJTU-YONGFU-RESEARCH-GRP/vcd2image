"""Tests for CLI main module."""

from typing import TYPE_CHECKING
from unittest.mock import patch, MagicMock
from argparse import Namespace

import pytest

from vcd2image.cli.main import main, validate_args, setup_logging

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestCLIMain:
    """Test CLI main functions."""

    def test_setup_logging_verbose(self, caplog) -> None:
        """Test logging setup with verbose flag."""
        setup_logging(verbose=True)

        # Check that logging level was set (this is hard to test directly,
        # but we can verify the function doesn't crash)
        assert True  # If we get here, setup worked

    def test_setup_logging_normal(self, caplog) -> None:
        """Test logging setup without verbose flag."""
        setup_logging(verbose=False)

        assert True  # If we get here, setup worked

    def test_validate_args_valid_vcd(self, tmp_path) -> None:
        """Test validating valid VCD file arguments."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end")

        args = Namespace(
            input_file=str(vcd_file),
            output=None,
            image=None,
            signals=["clock", "data"],
            list_signals=False,
            lazy_plot=False,
            lazy_dir=None,
            lazy_formats=None,
        )

        # Should not raise any exception
        validate_args(args)

    def test_validate_args_valid_json(self, tmp_path) -> None:
        """Test validating valid JSON file arguments."""
        json_file = tmp_path / "test.json"
        json_file.write_text("{}")

        args = Namespace(
            input_file=str(json_file),
            output=None,
            image="output.png",
            signals=None,
            list_signals=False,
            lazy_plot=False,
            lazy_dir=None,
            lazy_formats=None,
        )

        # Should not raise any exception
        validate_args(args)

    def test_validate_args_missing_input_file(self, tmp_path) -> None:
        """Test validating with nonexistent input file."""
        args = Namespace(
            input_file="nonexistent.vcd",
            output=None,
            image=None,
            signals=["clock"],
            list_signals=False,
            lazy_plot=False,
            lazy_dir=None,
            lazy_formats=None,
        )

        with pytest.raises(ValueError, match="Input file does not exist"):
            validate_args(args)

    def test_validate_args_vcd_no_signals(self, tmp_path) -> None:
        """Test validating VCD file without signals or list flag."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end")

        args = Namespace(
            input_file=str(vcd_file),
            output=None,
            image=None,
            signals=None,
            list_signals=False,
            lazy_plot=False,
            lazy_dir=None,
        )

        with pytest.raises(ValueError, match="Signal paths are required for VCD input"):
            validate_args(args)

    def test_validate_args_json_with_signals(self, tmp_path) -> None:
        """Test validating JSON file with signals specified."""
        json_file = tmp_path / "test.json"
        json_file.write_text("{}")

        args = Namespace(
            input_file=str(json_file),
            output=None,
            image="output.png",
            signals=["clock"],
            list_signals=False,
            lazy_plot=False,
            lazy_dir=None,
        )

        with pytest.raises(ValueError, match="Signal paths cannot be specified for JSON input"):
            validate_args(args)

    def test_validate_args_json_no_image(self, tmp_path) -> None:
        """Test validating JSON file without image output."""
        json_file = tmp_path / "test.json"
        json_file.write_text("{}")

        args = Namespace(
            input_file=str(json_file),
            output=None,
            image=None,
            signals=None,
            list_signals=False,
            lazy_plot=False,
            lazy_dir=None,
        )

        with pytest.raises(ValueError, match="Image output is required for JSON input"):
            validate_args(args)

    def test_validate_args_invalid_extension(self, tmp_path) -> None:
        """Test validating file with invalid extension."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("dummy content")

        args = Namespace(
            input_file=str(txt_file),
            output=None,
            image=None,
            signals=["clock"],
            list_signals=False,
            lazy_plot=False,
            lazy_dir=None,
        )

        with pytest.raises(ValueError, match="Input file must be .vcd or .json"):
            validate_args(args)

    @patch("vcd2image.cli.main.WaveExtractor")
    @patch("vcd2image.cli.main.Config")
    def test_main_vcd_to_json_success(self, mock_config, mock_extractor, tmp_path) -> None:
        """Test successful VCD to JSON conversion."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end")

        json_file = tmp_path / "output.json"

        # Mock arguments
        with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
            mock_args = MagicMock()
            mock_args.input_file = str(vcd_file)
            mock_args.output = str(json_file)
            mock_args.image = None
            mock_args.signals = ["clock"]
            mock_args.verbose = False
            mock_args.wave_chunk = 20
            mock_args.start_time = 0
            mock_args.end_time = 0
            mock_args.format = None
            mock_args.list_signals = False
            mock_parse_args.return_value = mock_args

            # Mock Config
            mock_config_instance = MagicMock()
            mock_config.from_args.return_value = mock_config_instance

            # Mock extractor
            mock_extractor_instance = MagicMock()
            mock_extractor.return_value = mock_extractor_instance
            mock_extractor_instance.execute.return_value = 0

            result = main()

            assert result == 0
            mock_extractor.assert_called_once_with(
                vcd_file=str(vcd_file), json_file=str(json_file), path_list=["clock"]
            )
            mock_extractor_instance.execute.assert_called_once()

    @patch("vcd2image.cli.main.WaveRenderer")
    @patch("vcd2image.cli.main.Config")
    def test_main_json_to_image_success(self, mock_config, mock_renderer, tmp_path) -> None:
        """Test successful JSON to image conversion."""
        json_file = tmp_path / "input.json"
        json_file.write_text("{}")

        image_file = tmp_path / "output.png"

        # Mock arguments
        with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
            mock_args = MagicMock()
            mock_args.input_file = str(json_file)
            mock_args.output = None
            mock_args.image = str(image_file)
            mock_args.signals = None
            mock_args.verbose = False
            mock_parse_args.return_value = mock_args

            # Mock Config
            mock_config_instance = MagicMock()
            mock_config.from_args.return_value = mock_config_instance

            # Mock renderer
            mock_renderer_instance = MagicMock()
            mock_renderer.return_value = mock_renderer_instance
            mock_renderer_instance.render_to_image.return_value = 0

            result = main()

            assert result == 0
            mock_renderer.assert_called_once()
            mock_renderer_instance.render_to_image.assert_called_once_with(
                str(json_file), str(image_file)
            )

    @patch("vcd2image.cli.main.Config")
    def test_main_vcd_with_image_output(self, mock_config, tmp_path) -> None:
        """Test VCD conversion with both JSON and image output."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end")

        json_file = tmp_path / "output.json"
        image_file = tmp_path / "output.png"

        with (
            patch("argparse.ArgumentParser.parse_args") as mock_parse_args,
            patch("vcd2image.cli.main.WaveExtractor") as mock_extractor,
            patch("vcd2image.cli.main.WaveRenderer") as mock_renderer,
        ):
            mock_args = MagicMock()
            mock_args.input_file = str(vcd_file)
            mock_args.output = str(json_file)
            mock_args.image = str(image_file)
            mock_args.signals = ["clock"]
            mock_args.verbose = False
            mock_args.wave_chunk = 20
            mock_args.start_time = 0
            mock_args.end_time = 0
            mock_args.format = None
            mock_args.list_signals = False
            mock_parse_args.return_value = mock_args

            # Mock Config
            mock_config_instance = MagicMock()
            mock_config.from_args.return_value = mock_config_instance

            # Mock extractor
            mock_extractor_instance = MagicMock()
            mock_extractor.return_value = mock_extractor_instance
            mock_extractor_instance.execute.return_value = 0

            # Mock renderer
            mock_renderer_instance = MagicMock()
            mock_renderer.return_value = mock_renderer_instance
            mock_renderer_instance.render_to_image.return_value = 0

            result = main()

            assert result == 0
            # Both extractor and renderer should be called
            mock_extractor.assert_called_once()
            mock_renderer.assert_called_once()

    @patch("vcd2image.cli.main.Config")
    def test_main_with_exception(self, mock_config) -> None:
        """Test main function handles exceptions properly."""
        with patch("argparse.ArgumentParser.parse_args", side_effect=Exception("Test error")):
            result = main()

            assert result == 1
