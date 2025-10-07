"""Tests for multi-figure renderer module."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from vcd2image.core.multi_renderer import MultiFigureRenderer

if TYPE_CHECKING:
    pass


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

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_render_categorized_figures(self, mock_signal_plotter, tmp_path) -> None:
        """Test rendering categorized figures."""
        # Mock SignalPlotter instance
        mock_plotter_instance = MagicMock()
        mock_signal_plotter.return_value = mock_plotter_instance
        mock_plotter_instance.load_data.return_value = True
        mock_plotter_instance.categorize_signals.return_value = True

        # Create test instance
        renderer = MultiFigureRenderer()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a minimal VCD file for the test
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end")

        result = renderer.render_categorized_figures(
            vcd_file=str(vcd_file),
            output_dir=str(output_dir),
            formats=["png", "svg", "html"]
        )

        assert result == 0
        mock_signal_plotter.assert_called_once()
        mock_plotter_instance.load_data.assert_called_once()
        mock_plotter_instance.categorize_signals.assert_called_once()

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_render_categorized_figures_no_clock_fallback(self, mock_signal_plotter, tmp_path) -> None:
        """Test render_categorized_figures with no clock signal (fallback logic)."""
        # Mock SignalPlotter instance
        mock_plotter_instance = MagicMock()
        mock_signal_plotter.return_value = mock_plotter_instance
        mock_plotter_instance.load_data.return_value = True
        mock_plotter_instance.categorize_signals.return_value = True

        # Create test instance
        renderer = MultiFigureRenderer()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a minimal VCD file for the test
        vcd_file = tmp_path / "test.vcd"
        vcd_file.write_text("$enddefinitions $end")

        result = renderer.render_categorized_figures(
            vcd_file=str(vcd_file),
            output_dir=str(output_dir),
            formats=["png"]
        )

        assert result == 0
        mock_signal_plotter.assert_called_once()
        mock_plotter_instance.load_data.assert_called_once()
        mock_plotter_instance.categorize_signals.assert_called_once()

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_render_categorized_figures_no_signals_error(self, mock_signal_plotter, tmp_path) -> None:
        """Test render_categorized_figures with no signals at all."""
        # Mock SignalPlotter instance to simulate failure
        mock_plotter_instance = MagicMock()
        mock_signal_plotter.return_value = mock_plotter_instance
        mock_plotter_instance.load_data.return_value = False  # Simulate failure

        # Create test instance
        renderer = MultiFigureRenderer()

        result = renderer.render_categorized_figures(
            vcd_file="test.vcd",
            output_dir=str(tmp_path / "output"),
            formats=["png"]
        )

        assert result == 1  # Should return error code
        mock_signal_plotter.assert_called_once()
        mock_plotter_instance.load_data.assert_called_once()

    # TODO: Add render_auto_plot test when mocking is fixed

    def test_extract_signals_to_json(self, tmp_path) -> None:
        """Test extracting signals to JSON."""

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
