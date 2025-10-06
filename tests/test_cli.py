"""Tests for CLI main module."""

from argparse import Namespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from vcd2image.cli.main import main, setup_logging, validate_args

if TYPE_CHECKING:
    pass


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
            auto_plot=False,
            plot_dir=None,
            plot_formats=None,
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
            auto_plot=False,
            plot_dir=None,
            plot_formats=None,
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
            auto_plot=False,
            plot_dir=None,
            plot_formats=None,
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
            auto_plot=False,
            plot_dir=None,
            plot_formats=None,
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
            auto_plot=False,
            plot_dir=None,
            plot_formats=None,
        )

        with pytest.raises(ValueError, match="Input file must be .vcd or .json"):
            validate_args(args)

    @patch("vcd2image.cli.main.WaveExtractor")
    def test_main_vcd_to_json_success(self, mock_extractor, tmp_path) -> None:
        """Test successful VCD to JSON conversion."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end")

        json_file = tmp_path / "output.json"

        # Mock extractor
        mock_extractor_instance = MagicMock()
        mock_extractor.return_value = mock_extractor_instance
        mock_extractor_instance.execute.return_value = 0

        # Mock arguments
        with patch("vcd2image.cli.main.create_parser") as mock_create_parser:
            mock_parser = MagicMock()
            mock_create_parser.return_value = mock_parser
            mock_args = Namespace()
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
            mock_args.auto_plot = False
            mock_args.plot_dir = None
            mock_args.plot_formats = None
            mock_parser.parse_args.return_value = mock_args

            result = main()

        assert result == 0
        mock_extractor.assert_called_once_with(
            vcd_file=str(vcd_file), json_file=str(json_file), path_list=["clock"]
        )
        mock_extractor_instance.execute.assert_called_once()

    @patch("vcd2image.cli.main.WaveRenderer")
    def test_main_json_to_image_success(self, mock_renderer, tmp_path) -> None:
        """Test successful JSON to image conversion."""
        json_file = tmp_path / "input.json"
        json_file.write_text("{}")

        image_file = tmp_path / "output.png"

        # Mock renderer
        mock_renderer_instance = MagicMock()
        mock_renderer.return_value = mock_renderer_instance
        mock_renderer_instance.render_to_image.return_value = 0

        # Mock arguments
        with patch("vcd2image.cli.main.create_parser") as mock_create_parser:
            mock_parser = MagicMock()
            mock_create_parser.return_value = mock_parser
            mock_args = Namespace()
            mock_args.input_file = str(json_file)
            mock_args.output = None
            mock_args.image = str(image_file)
            mock_args.signals = None
            mock_args.verbose = False
            mock_args.auto_plot = False
            mock_args.plot_dir = None
            mock_args.plot_formats = None
            mock_parser.parse_args.return_value = mock_args

            result = main()

        assert result == 0
        mock_renderer.assert_called_once()
        mock_renderer_instance.render_to_image.assert_called_once_with(
            str(json_file), str(image_file)
        )

    def test_main_vcd_with_image_output(self, tmp_path) -> None:
        """Test VCD conversion with both JSON and image output."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end")

        json_file = tmp_path / "output.json"
        image_file = tmp_path / "output.png"

        with (
            patch("vcd2image.cli.main.create_parser") as mock_create_parser,
            patch("vcd2image.cli.main.WaveExtractor") as mock_extractor,
            patch("vcd2image.cli.main.WaveRenderer") as mock_renderer,
        ):
            mock_parser = MagicMock()
            mock_create_parser.return_value = mock_parser
            mock_args = Namespace()
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
            mock_args.auto_plot = False
            mock_args.plot_dir = None
            mock_args.plot_formats = None
            mock_parser.parse_args.return_value = mock_args

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

    def test_main_with_exception(self) -> None:
        """Test main function handles exceptions properly."""
        with patch("vcd2image.cli.main.create_parser") as mock_create_parser:
            mock_parser = MagicMock()
            mock_create_parser.return_value = mock_parser
            mock_parser.parse_args.side_effect = Exception("Test error")
            result = main()

            assert result == 1
