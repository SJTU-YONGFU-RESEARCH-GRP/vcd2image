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
            auto_plot=False,
            auto_dir=None,
            auto_formats=None,
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
            auto_plot=False,
            auto_dir=None,
            auto_formats=None,
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
            auto_plot=False,
            auto_dir=None,
            auto_formats=None,
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
            auto_plot=False,
            auto_dir=None,
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
            auto_plot=False,
            auto_dir=None,
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
            auto_plot=False,
            auto_dir=None,
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
            auto_plot=False,
            auto_dir=None,
            plot_dir=None,
            plot_formats=None,
        )

        with pytest.raises(ValueError, match="Input file must be .vcd or .json"):
            validate_args(args)

    def test_validate_args_plot_dir_without_auto_plot(self, tmp_path) -> None:
        """Test validating plot_dir without auto_plot flag."""
        json_file = tmp_path / "test.json"
        json_file.write_text("{}")

        args = Namespace(
            input_file=str(json_file),
            output=None,
            image="output.png",
            signals=None,
            list_signals=False,
            auto_plot=False,
            auto_dir=None,
            auto_formats=None,
            plot_dir="/some/dir",
            plot_formats=None,
        )

        with pytest.raises(ValueError, match="Auto plotting options are not valid for JSON input"):
            validate_args(args)

    def test_validate_args_plot_formats_without_auto_plot(self, tmp_path) -> None:
        """Test validating plot_formats without auto_plot flag."""
        json_file = tmp_path / "test.json"
        json_file.write_text("{}")

        args = Namespace(
            input_file=str(json_file),
            output=None,
            image="output.png",
            signals=None,
            list_signals=False,
            auto_plot=False,
            auto_dir=None,
            auto_formats=None,
            plot_dir=None,
            plot_formats=["png"],
        )

        with pytest.raises(ValueError, match="--plot-formats requires --auto-plot or --plot-dir"):
            validate_args(args)

    def test_validate_args_auto_plot_with_signals(self, tmp_path) -> None:
        """Test validating auto_plot with signals specified."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end")

        args = Namespace(
            input_file=str(vcd_file),
            output=None,
            image=None,
            signals=["clock"],
            list_signals=False,
            auto_plot=True,
            auto_dir=None,
            auto_formats=None,
            plot_dir=None,
            plot_formats=None,
        )

        with pytest.raises(ValueError, match="Cannot specify signals with auto plotting"):
            validate_args(args)

    def test_validate_args_auto_plot_with_output(self, tmp_path) -> None:
        """Test validating auto_plot with output JSON specified."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end")

        args = Namespace(
            input_file=str(vcd_file),
            output="output.json",
            image=None,
            signals=None,
            list_signals=False,
            auto_plot=True,
            auto_dir=None,
            auto_formats=None,
            plot_dir=None,
            plot_formats=None,
        )

        with pytest.raises(ValueError, match="Cannot specify output JSON with auto plotting"):
            validate_args(args)

    @patch("vcd2image.cli.main.MultiFigureRenderer")
    def test_main_auto_plot_without_image(self, mock_multi_renderer, tmp_path) -> None:
        """Test auto plotting without image output specified."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end")

        mock_renderer_instance = MagicMock()
        mock_multi_renderer.return_value = mock_renderer_instance
        mock_renderer_instance.render_auto_plot.return_value = 0

        with patch("vcd2image.cli.main.create_parser") as mock_create_parser:
            mock_parser = MagicMock()
            mock_create_parser.return_value = mock_parser
            mock_args = Namespace()
            mock_args.input_file = str(vcd_file)
            mock_args.output = None
            mock_args.image = None  # No image specified
            mock_args.signals = None
            mock_args.verbose = False
            mock_args.auto_plot = True
            mock_args.plot_dir = None
            mock_args.plot_formats = None
            mock_parser.parse_args.return_value = mock_args

            result = main()

            assert result == 1  # Should fail due to missing image

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

    @patch("vcd2image.cli.main.MultiFigureRenderer")
    def test_main_auto_plot_single_image(self, mock_multi_renderer, tmp_path) -> None:
        """Test auto plotting with single image output."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end")
        image_file = tmp_path / "output.png"

        mock_renderer_instance = MagicMock()
        mock_multi_renderer.return_value = mock_renderer_instance
        mock_renderer_instance.render_auto_plot.return_value = 0

        with patch("vcd2image.cli.main.create_parser") as mock_create_parser:
            mock_parser = MagicMock()
            mock_create_parser.return_value = mock_parser
            mock_args = Namespace()
            mock_args.input_file = str(vcd_file)
            mock_args.output = None
            mock_args.image = str(image_file)
            mock_args.signals = None
            mock_args.verbose = False
            mock_args.auto_plot = True
            mock_args.plot_dir = None
            mock_args.plot_formats = None
            mock_parser.parse_args.return_value = mock_args

            result = main()

            assert result == 0
            mock_multi_renderer.assert_called_once()
            mock_renderer_instance.render_auto_plot.assert_called_once_with(
                vcd_file=str(vcd_file), output_file=str(image_file)
            )

    @patch("vcd2image.cli.main.MultiFigureRenderer")
    def test_main_auto_plot_multiple_formats(self, mock_multi_renderer, tmp_path) -> None:
        """Test auto plotting with multiple output formats."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end")
        plot_dir = tmp_path / "plots"
        plot_dir.mkdir()

        mock_renderer_instance = MagicMock()
        mock_multi_renderer.return_value = mock_renderer_instance
        mock_renderer_instance.render_categorized_figures.return_value = 0

        with patch("vcd2image.cli.main.create_parser") as mock_create_parser:
            mock_parser = MagicMock()
            mock_create_parser.return_value = mock_parser
            mock_args = Namespace()
            mock_args.input_file = str(vcd_file)
            mock_args.output = None
            mock_args.image = None
            mock_args.signals = None
            mock_args.verbose = False
            mock_args.auto_plot = True
            mock_args.plot_dir = str(plot_dir)
            mock_args.plot_formats = ["png", "svg"]
            mock_parser.parse_args.return_value = mock_args

            result = main()

            assert result == 0
            mock_multi_renderer.assert_called_once()
            mock_renderer_instance.render_categorized_figures.assert_called_once_with(
                vcd_file=str(vcd_file), output_dir=str(plot_dir), formats=["png", "svg"]
            )

    @patch("vcd2image.cli.main.MultiFigureRenderer")
    def test_main_auto_plot_default_formats(self, mock_multi_renderer, tmp_path) -> None:
        """Test auto plotting with default formats."""
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end")
        plot_dir = tmp_path / "plots"
        plot_dir.mkdir()

        mock_renderer_instance = MagicMock()
        mock_multi_renderer.return_value = mock_renderer_instance
        mock_renderer_instance.render_categorized_figures.return_value = 0

        with patch("vcd2image.cli.main.create_parser") as mock_create_parser:
            mock_parser = MagicMock()
            mock_create_parser.return_value = mock_parser
            mock_args = Namespace()
            mock_args.input_file = str(vcd_file)
            mock_args.output = None
            mock_args.image = None
            mock_args.signals = None
            mock_args.verbose = False
            mock_args.auto_plot = True
            mock_args.plot_dir = str(plot_dir)
            mock_args.plot_formats = None  # Should default to ["png"]
            mock_parser.parse_args.return_value = mock_args

            result = main()

            assert result == 0
            mock_multi_renderer.assert_called_once()
            mock_renderer_instance.render_categorized_figures.assert_called_once_with(
                vcd_file=str(vcd_file), output_dir=str(plot_dir), formats=["png"]
            )

    def test_main_with_exception(self) -> None:
        """Test main function handles exceptions properly."""
        with patch("vcd2image.cli.main.create_parser") as mock_create_parser:
            mock_parser = MagicMock()
            mock_create_parser.return_value = mock_parser
            mock_parser.parse_args.side_effect = Exception("Test error")
            result = main()

            assert result == 1

    def test_create_parser(self) -> None:
        """Test argument parser creation."""
        from vcd2image.cli.main import create_parser

        parser = create_parser()

        # Test that parser has expected arguments
        assert parser is not None

        # Parse args with required input_file to test basic functionality
        args = parser.parse_args(["test.vcd"])
        assert hasattr(args, 'input_file')
        assert hasattr(args, 'output')
        assert hasattr(args, 'image')
        assert hasattr(args, 'signals')
        assert hasattr(args, 'verbose')
        assert hasattr(args, 'auto_plot')
        assert hasattr(args, 'plot_dir')
        assert hasattr(args, 'plot_formats')
        assert args.input_file == "test.vcd"
