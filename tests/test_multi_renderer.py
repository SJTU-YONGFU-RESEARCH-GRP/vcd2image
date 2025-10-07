"""Tests for multi-figure renderer module."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from vcd2image.core.multi_renderer import MultiFigureRenderer

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestMultiFigureRenderer:
    """Test MultiFigureRenderer class."""

    def test_init(self) -> None:
        """Test multi-figure renderer initialization."""
        renderer = MultiFigureRenderer()
        assert renderer.skin == "default"
        assert renderer.categorizer is not None
        assert renderer.renderer is not None

    def test_init_custom_skin(self) -> None:
        """Test multi-figure renderer initialization with custom skin."""
        renderer = MultiFigureRenderer(skin="dark")
        assert renderer.skin == "dark"

    @patch("vcd2image.core.multi_renderer.SignalCategorizer")
    @patch("vcd2image.core.multi_renderer.WaveRenderer")
    @patch("vcd2image.core.parser.VCDParser")
    def test_render_categorized_figures(self, mock_vcd_parser, mock_wave_renderer, mock_categorizer, tmp_path) -> None:
        """Test rendering categorized figures."""
        # Setup mocks
        mock_parser_instance = MagicMock()
        mock_vcd_parser.return_value = mock_parser_instance
        mock_parser_instance.parse_signals.return_value = {
            "clock": MagicMock(), "input1": MagicMock(), "input2": MagicMock(),
            "output1": MagicMock(), "output2": MagicMock(),
            "internal1": MagicMock(), "internal2": MagicMock()
        }

        mock_category = MagicMock()
        mock_category.clocks = ["clock"]
        mock_category.inputs = ["input1", "input2"]
        mock_category.outputs = ["output1", "output2"]
        mock_category.internals = ["internal1", "internal2"]
        mock_category.input_ports = ["input1", "input2"]
        mock_category.output_ports = ["output1", "output2"]
        mock_category.internal_signals = ["internal1", "internal2"]

        mock_categorizer_instance = MagicMock()
        mock_categorizer_instance.categorize_signals.return_value = mock_category
        mock_categorizer.return_value = mock_categorizer_instance

        mock_renderer_instance = MagicMock()
        mock_wave_renderer.return_value = mock_renderer_instance
        mock_renderer_instance.render_to_html = MagicMock()

        # Create test instance
        renderer = MultiFigureRenderer()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Mock the _extract_signals_to_json method
        renderer._extract_signals_to_json = MagicMock(return_value=0)

        result = renderer.render_categorized_figures(
            vcd_file="test.vcd",
            output_dir=str(output_dir),
            formats=["png", "svg", "html"]
        )

        assert result == 0
        mock_categorizer_instance.categorize_signals.assert_called_once()
        # Should create multiple render calls for different categories and formats
        assert mock_renderer_instance.render_to_image.call_count > 0
        # Should also call render_to_html for HTML format
        mock_renderer_instance.render_to_html.assert_called()

    @patch("vcd2image.core.multi_renderer.SignalCategorizer")
    @patch("vcd2image.core.multi_renderer.WaveRenderer")
    @patch("vcd2image.core.parser.VCDParser")
    def test_render_categorized_figures_no_clock_fallback(self, mock_vcd_parser, mock_wave_renderer, mock_categorizer, tmp_path) -> None:
        """Test render_categorized_figures with no clock signal (fallback logic)."""
        # Setup mocks
        mock_parser_instance = MagicMock()
        mock_vcd_parser.return_value = mock_parser_instance
        mock_parser_instance.parse_signals.return_value = {
            "clock": MagicMock(), "input1": MagicMock(), "input2": MagicMock(),
            "output1": MagicMock(), "output2": MagicMock(),
            "internal1": MagicMock(), "internal2": MagicMock()
        }

        mock_category = MagicMock()
        mock_category.clocks = []  # No clocks found
        mock_category.inputs = ["input1", "input2"]
        mock_category.outputs = ["output1", "output2"]
        mock_category.internals = ["internal1", "internal2"]
        mock_category.input_ports = ["input1", "input2"]
        mock_category.output_ports = ["output1", "output2"]
        mock_category.internal_signals = ["internal1", "internal2"]

        mock_categorizer_instance = MagicMock()
        mock_categorizer_instance.categorize_signals.return_value = mock_category
        mock_categorizer_instance.suggest_clock_signal.return_value = None  # No clock found
        mock_categorizer.return_value = mock_categorizer_instance

        mock_renderer_instance = MagicMock()
        mock_wave_renderer.return_value = mock_renderer_instance
        mock_renderer_instance.render_to_html = MagicMock()

        # Create test instance
        renderer = MultiFigureRenderer()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Mock the _extract_signals_to_json method
        renderer._extract_signals_to_json = MagicMock(return_value=0)

        result = renderer.render_categorized_figures(
            vcd_file="test.vcd",
            output_dir=str(output_dir),
            formats=["png"]
        )

        assert result == 0
        # Should use first signal as clock fallback
        mock_categorizer_instance.suggest_clock_signal.assert_called_once()

    @patch("vcd2image.core.multi_renderer.SignalCategorizer")
    @patch("vcd2image.core.multi_renderer.WaveRenderer")
    @patch("vcd2image.core.parser.VCDParser")
    def test_render_categorized_figures_no_signals_error(self, mock_vcd_parser, mock_wave_renderer, mock_categorizer, tmp_path) -> None:
        """Test render_categorized_figures with no signals at all."""
        # Setup mocks
        mock_parser_instance = MagicMock()
        mock_vcd_parser.return_value = mock_parser_instance
        mock_parser_instance.parse_signals.return_value = {}  # Empty signals

        mock_category = MagicMock()
        mock_category.clocks = []
        mock_category.inputs = []
        mock_category.outputs = []
        mock_category.internals = []

        mock_categorizer_instance = MagicMock()
        mock_categorizer_instance.categorize_signals.return_value = mock_category
        mock_categorizer_instance.suggest_clock_signal.return_value = None
        mock_categorizer.return_value = mock_categorizer_instance

        # Create test instance
        renderer = MultiFigureRenderer()

        with pytest.raises(ValueError, match="No signals found in VCD file"):
            renderer.render_categorized_figures(
                vcd_file="test.vcd",
                output_dir=str(tmp_path / "output"),
                formats=["png"]
            )

    # TODO: Add render_auto_plot test when mocking is fixed

    def test_extract_signals_to_json(self, tmp_path) -> None:
        """Test extracting signals to JSON."""
        from vcd2image.core.extractor import WaveExtractor

        # Create a mock VCD file
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end")

        renderer = MultiFigureRenderer()

        with patch("vcd2image.core.extractor.WaveExtractor") as mock_extractor:
            mock_extractor_instance = MagicMock()
            mock_extractor.return_value = mock_extractor_instance
            mock_extractor_instance.execute.return_value = 0

            # _extract_signals_to_json doesn't return a value, it raises on error
            renderer._extract_signals_to_json(
                str(vcd_file), ["signal1"], "output.json"
            )
            mock_extractor.assert_called_once_with(
                str(vcd_file), "output.json", ["signal1"]
            )
            mock_extractor_instance.execute.assert_called_once()

    def test_extract_signals_to_json_with_path_dict(self, tmp_path) -> None:
        """Test extracting signals to JSON with pre-filtered path dict."""
        from vcd2image.core.extractor import WaveExtractor

        # Create a mock VCD file
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end")

        renderer = MultiFigureRenderer()

        mock_path_dict = {"signal1": MagicMock()}

        with patch("vcd2image.core.extractor.WaveExtractor") as mock_extractor:
            mock_extractor_instance = MagicMock()
            mock_extractor.return_value = mock_extractor_instance
            mock_extractor_instance.execute.return_value = 0

            # _extract_signals_to_json doesn't return a value, it raises on error
            renderer._extract_signals_to_json(
                str(vcd_file), ["signal1"], "output.json", mock_path_dict
            )
            mock_extractor.assert_called_once_with(
                str(vcd_file), "output.json", ["signal1"], mock_path_dict
            )
            mock_extractor_instance.execute.assert_called_once()
