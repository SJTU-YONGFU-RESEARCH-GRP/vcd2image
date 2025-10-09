"""Tests for the MultiFigureRenderer class."""

import logging
from unittest.mock import Mock, patch

import pytest

from vcd2image.core.multi_renderer import MultiFigureRenderer


class TestMultiFigureRenderer:
    """Test the MultiFigureRenderer class."""

    def test_init(self) -> None:
        """Test MultiFigureRenderer initialization."""

        renderer = MultiFigureRenderer()

        assert renderer.skin == "default"

        assert renderer.categorizer is not None

        assert renderer.renderer is not None

    def test_extract_signals_to_json_success(self, timer_vcd_file, tmp_path) -> None:
        """Test successful signal extraction to JSON with real VCD file."""

        renderer = MultiFigureRenderer()

        # Use real timer.vcd file and extract a real signal

        output_json = tmp_path / "output.json"

        renderer._extract_signals_to_json(str(timer_vcd_file), ["tb_timer/clock"], str(output_json))

        # Check that output file was created

        assert output_json.exists()

    def test_extract_signals_to_json_failure(self, timer_vcd_file) -> None:
        """Test signal extraction failure with non-existent signal."""

        renderer = MultiFigureRenderer()

        # Use real timer.vcd file but request a signal that doesn't exist

        with pytest.raises(ValueError, match="Can't find signal path"):
            renderer._extract_signals_to_json(
                str(timer_vcd_file), ["non_existent_signal"], "output.json"
            )

    def test_generate_enhanced_categorized_plots_no_categories(self) -> None:
        """Test _generate_enhanced_categorized_plots with no categories."""
        from pathlib import Path

        renderer = MultiFigureRenderer()
        mock_plotter = Mock()
        mock_plotter.categories = None

        with patch("vcd2image.core.multi_renderer.logger") as mock_logger:
            renderer._generate_enhanced_categorized_plots(
                mock_plotter, Path("/tmp"), "test", ["png"]
            )

            mock_logger.warning.assert_called_once_with("No categorized signals available")

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_render_categorized_figures_exception_handling(
        self, mock_signal_plotter, tmp_path
    ) -> None:
        """Test exception handling in render_categorized_figures."""

        mock_plotter_instance = Mock()

        mock_signal_plotter.return_value = mock_plotter_instance

        mock_plotter_instance.load_data.side_effect = RuntimeError("Test exception")

        renderer = MultiFigureRenderer()

        result = renderer.render_categorized_figures(
            vcd_file="dummy.vcd", output_dir=str(tmp_path / "output"), formats=["png"]
        )

        assert result == 1  # Should return error code

        mock_signal_plotter.assert_called_once_with(
            vcd_file="dummy.vcd", verilog_file=None, output_dir=str(tmp_path / "output")
        )

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_render_categorized_figures_success(
        self, mock_signal_plotter, tmp_path, caplog
    ) -> None:
        """Test successful render_categorized_figures (lines 68-79)."""

        mock_plotter_instance = Mock()

        mock_signal_plotter.return_value = mock_plotter_instance

        # Mock successful operations

        mock_plotter_instance.load_data.return_value = True

        mock_plotter_instance.categorize_signals.return_value = True

        renderer = MultiFigureRenderer()

        output_dir = tmp_path / "output"

        with caplog.at_level(logging.INFO):
            with patch.object(renderer, "_generate_enhanced_categorized_plots"):
                result = renderer.render_categorized_figures(
                    vcd_file=str(tmp_path / "test.vcd"), output_dir=str(output_dir), formats=["png"]
                )

        assert result == 0  # Should return success code

        # Check that success logging occurred (line 78)

        assert f"Generated enhanced categorized figures in {output_dir}" in caplog.text

        # Verify methods were called

        mock_plotter_instance.load_data.assert_called_once()

        mock_plotter_instance.categorize_signals.assert_called_once()

    def test_generate_enhanced_categorized_plots_insufficient_signals(self) -> None:
        """Test _generate_enhanced_categorized_plots with insufficient signals."""

        from pathlib import Path
        from unittest.mock import Mock

        renderer = MultiFigureRenderer()

        mock_plotter = Mock()

        mock_plotter.categories = Mock()

        mock_plotter.categories.inputs = ["clock"]  # Only clock signal

        mock_plotter.categories.outputs = []

        mock_plotter.categories.internals = []

        with patch("vcd2image.core.multi_renderer.logger") as mock_logger:
            with patch.object(renderer, "_generate_category_json"):
                renderer._generate_enhanced_categorized_plots(
                    mock_plotter, Path("/tmp"), "test", ["png"]
                )

            # Should warn about categories with no signals after filtering

            mock_logger.warning.assert_any_call("No signals found for inputs category")

            mock_logger.warning.assert_any_call("No signals found for outputs category")

            mock_logger.warning.assert_any_call("No signals found for internals category")

    def test_generate_category_json_no_signals(self, capsys) -> None:
        """Test _generate_category_json with no signals."""

        from pathlib import Path
        from unittest.mock import Mock

        renderer = MultiFigureRenderer()

        mock_plotter = Mock()

        mock_plotter.vcd_file = "/tmp/test.vcd"

        with patch("vcd2image.core.multi_renderer.logger") as mock_logger:
            renderer._generate_category_json(mock_plotter, "test_category", [], Path("/tmp"))

            mock_logger.warning.assert_called_with(
                "No signals found for test_category category, skipping JSON generation"
            )

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_render_categorized_figures_load_data_failure(
        self, mock_signal_plotter, tmp_path
    ) -> None:
        """Test render_categorized_figures with load_data failure (lines 68-69)."""
        mock_plotter_instance = Mock()
        mock_signal_plotter.return_value = mock_plotter_instance

        # Mock load_data failure
        mock_plotter_instance.load_data.return_value = False
        mock_plotter_instance.categorize_signals.return_value = True

        renderer = MultiFigureRenderer()

        result = renderer.render_categorized_figures(
            vcd_file="dummy.vcd", output_dir=str(tmp_path / "output"), formats=["png"]
        )

        assert result == 1  # Should return error code
        mock_plotter_instance.load_data.assert_called_once()
        mock_plotter_instance.categorize_signals.assert_not_called()

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_render_categorized_figures_categorize_failure(
        self, mock_signal_plotter, tmp_path
    ) -> None:
        """Test render_categorized_figures with categorize_signals failure (lines 72-73)."""
        mock_plotter_instance = Mock()
        mock_signal_plotter.return_value = mock_plotter_instance

        # Mock categorize_signals failure
        mock_plotter_instance.load_data.return_value = True
        mock_plotter_instance.categorize_signals.return_value = False

        renderer = MultiFigureRenderer()

        result = renderer.render_categorized_figures(
            vcd_file="dummy.vcd", output_dir=str(tmp_path / "output"), formats=["png"]
        )

        assert result == 1  # Should return error code
        mock_plotter_instance.load_data.assert_called_once()
        mock_plotter_instance.categorize_signals.assert_called_once()

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_render_categorized_figures_with_formats_none(
        self, mock_signal_plotter, tmp_path, caplog
    ) -> None:
        """Test render_categorized_figures with formats=None (line 53)."""
        mock_plotter_instance = Mock()
        mock_signal_plotter.return_value = mock_plotter_instance

        # Mock successful operations
        mock_plotter_instance.load_data.return_value = True
        mock_plotter_instance.categorize_signals.return_value = True

        renderer = MultiFigureRenderer()

        with caplog.at_level(logging.INFO):
            with patch.object(renderer, "_generate_enhanced_categorized_plots"):
                result = renderer.render_categorized_figures(
                    vcd_file=str(tmp_path / "test.vcd"),
                    output_dir=str(tmp_path / "output"),
                    formats=None,  # Should default to ["png"]
                )

        assert result == 0  # Should return success code

    def test_generate_enhanced_categorized_plots_insufficient_signals_after_filtering(self) -> None:
        """Test _generate_enhanced_categorized_plots with insufficient signals after filtering (lines 126-127)."""
        from pathlib import Path

        renderer = MultiFigureRenderer()

        mock_plotter = Mock()
        mock_plotter.categories = Mock()

        # Only one signal in inputs (no clock/reset to filter), should trigger insufficient signals
        mock_plotter.categories.inputs = ["single_input"]  # Only 1 signal, no clock/reset
        mock_plotter.categories.outputs = ["output1"]  # Has signals
        mock_plotter.categories.internals = ["internal1"]  # Has signals

        with patch("vcd2image.core.multi_renderer.logger") as mock_logger:
            with patch.object(renderer, "_generate_category_json"):
                renderer._generate_enhanced_categorized_plots(
                    mock_plotter, Path("/tmp"), "test", ["png"]
                )

        # Should warn about insufficient signals for inputs (after filtering)
        mock_logger.warning.assert_any_call("Skipping inputs figure: insufficient signals")

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_generate_enhanced_categorized_plots_svg_format(self, mock_signal_plotter) -> None:
        """Test _generate_enhanced_categorized_plots with SVG format (line 145)."""
        from pathlib import Path

        mock_plotter_instance = Mock()
        mock_signal_plotter.return_value = mock_plotter_instance

        renderer = MultiFigureRenderer()

        mock_plotter = Mock()
        mock_plotter.categories = Mock()
        mock_plotter.categories.inputs = ["clock", "reset", "input1"]
        mock_plotter.categories.outputs = ["output1"]
        mock_plotter.categories.internals = ["internal1"]

        with patch("vcd2image.core.multi_renderer.logger") as mock_logger:
            with patch.object(renderer, "_generate_category_json"):
                with patch.object(mock_plotter, "_create_enhanced_signal_plot"):
                    renderer._generate_enhanced_categorized_plots(
                        mock_plotter, Path("/tmp"), "test", ["svg"]
                    )

        # Should log SVG not implemented for each category
        mock_logger.info.assert_any_call("SVG format requested for clocks but not yet implemented")
        mock_logger.info.assert_any_call("SVG format requested for resets but not yet implemented")
        mock_logger.info.assert_any_call("SVG format requested for inputs but not yet implemented")
        mock_logger.info.assert_any_call("SVG format requested for outputs but not yet implemented")
        mock_logger.info.assert_any_call(
            "SVG format requested for internals but not yet implemented"
        )

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_generate_enhanced_categorized_plots_html_format(self, mock_signal_plotter) -> None:
        """Test _generate_enhanced_categorized_plots with HTML format (line 148)."""
        from pathlib import Path

        mock_plotter_instance = Mock()
        mock_signal_plotter.return_value = mock_plotter_instance

        renderer = MultiFigureRenderer()

        mock_plotter = Mock()
        mock_plotter.categories = Mock()
        mock_plotter.categories.inputs = ["clock", "reset", "input1"]
        mock_plotter.categories.outputs = ["output1"]
        mock_plotter.categories.internals = ["internal1"]

        with patch("vcd2image.core.multi_renderer.logger") as mock_logger:
            with patch.object(renderer, "_generate_category_json"):
                with patch.object(mock_plotter, "_create_enhanced_signal_plot"):
                    renderer._generate_enhanced_categorized_plots(
                        mock_plotter, Path("/tmp"), "test", ["html"]
                    )

        # Should log HTML not implemented for each category
        mock_logger.info.assert_any_call("HTML format requested for clocks but not yet implemented")
        mock_logger.info.assert_any_call("HTML format requested for resets but not yet implemented")
        mock_logger.info.assert_any_call("HTML format requested for inputs but not yet implemented")
        mock_logger.info.assert_any_call(
            "HTML format requested for outputs but not yet implemented"
        )
        mock_logger.info.assert_any_call(
            "HTML format requested for internals but not yet implemented"
        )

    def test_generate_category_json_success(self, tmp_path) -> None:
        """Test _generate_category_json with empty signals (covers lines 166-167)."""
        renderer = MultiFigureRenderer()

        mock_plotter = Mock()

        with patch("vcd2image.core.multi_renderer.logger") as mock_logger:
            renderer._generate_category_json(mock_plotter, "test_category", [], tmp_path)

        # Should warn about no signals
        mock_logger.warning.assert_called_with(
            "No signals found for test_category category, skipping JSON generation"
        )

    def test_generate_category_json_with_real_data(self, timer_vcd_file, tmp_path) -> None:
        """Test _generate_category_json with real VCD data (lines 173-210)."""
        from pathlib import Path

        renderer = MultiFigureRenderer()

        # Create a mock plotter with the timer VCD file
        plotter = Mock()
        plotter.vcd_file = timer_vcd_file

        # Create output directory and plots subdirectory
        output_path = Path(tmp_path / "output")
        output_path.mkdir()
        plots_dir = output_path / "plots"
        plots_dir.mkdir()

        # Test with real signals from timer.vcd - this should execute the JSON generation logic
        renderer._generate_category_json(plotter, "test_category", ["tb_timer/clock"], output_path)

        # Check that JSON file was created
        json_file = output_path / "plots" / "test_category.json"
        assert json_file.exists()

        # Check that the JSON file contains valid data
        import json

        with open(json_file) as f:
            data = json.load(f)
        assert "signal" in data
        assert len(data["signal"]) > 0

    def test_generate_category_json_wave_extractor_failure(self, tmp_path, caplog) -> None:
        """Test _generate_category_json with WaveExtractor failure (lines 205-207)."""
        renderer = MultiFigureRenderer()

        mock_plotter = Mock()
        mock_plotter.vcd_file = str(tmp_path / "nonexistent.vcd")  # Non-existent VCD file

        with caplog.at_level(logging.WARNING):
            renderer._generate_category_json(mock_plotter, "test_category", ["signal1"], tmp_path)

        # Should warn about WaveExtractor failure (VCD file not found)
        assert "Failed to generate JSON for test_category: VCD file not found" in caplog.text

    def test_generate_category_json_exception_handling(self, tmp_path, caplog) -> None:
        """Test _generate_category_json with general exception handling (lines 209-210)."""
        # Create a minimal valid VCD file
        vcd_file = tmp_path / "test.vcd"
        vcd_content = """$date
Test
$end
$timescale 1ns $end
$scope module test $end
$var wire 1 ! clk $end
$upscope $end
$enddefinitions $end
$dumpvars
0!
$end
"""
        vcd_file.write_text(vcd_content)

        renderer = MultiFigureRenderer()

        mock_plotter = Mock()
        mock_plotter.vcd_file = str(vcd_file)

        # This should work normally, but let's test with a signal that doesn't exist
        # to trigger some other exception path
        with caplog.at_level(logging.WARNING):
            renderer._generate_category_json(
                mock_plotter, "test_category", ["nonexistent_signal"], tmp_path
            )

        # Should warn about some failure
        assert "Failed to generate JSON for test_category:" in caplog.text

    def test_render_enhanced_plots_with_golden_references_exception(self, tmp_path) -> None:
        """Test render_enhanced_plots_with_golden_references exception handling (lines 271-273)."""
        mock_plotter_instance = Mock()
        mock_plotter_instance.load_data.return_value = True
        mock_plotter_instance.categorize_signals.return_value = True
        mock_plotter_instance.generate_plots.side_effect = RuntimeError("Test exception")

        with patch(
            "vcd2image.core.multi_renderer.SignalPlotter", return_value=mock_plotter_instance
        ):
            renderer = MultiFigureRenderer()

            result = renderer.render_enhanced_plots_with_golden_references(
                vcd_file=str(tmp_path / "test.vcd"),
                verilog_file=str(tmp_path / "test.v"),
                output_dir=str(tmp_path / "enhanced_plots"),
            )

        # Should return 1 due to exception
        assert result == 1

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_render_enhanced_plots_with_golden_references_success(
        self, mock_signal_plotter, tmp_path, caplog
    ) -> None:
        """Test render_enhanced_plots_with_golden_references success (lines 225-273)."""
        mock_plotter_instance = Mock()
        mock_signal_plotter.return_value = mock_plotter_instance

        # Mock successful operations
        mock_plotter_instance.load_data.return_value = True
        mock_plotter_instance.categorize_signals.return_value = True
        mock_plotter_instance.generate_plots.return_value = True
        mock_plotter_instance.generate_summary_report.return_value = "# Test Report"

        renderer = MultiFigureRenderer()

        with caplog.at_level(logging.INFO):
            result = renderer.render_enhanced_plots_with_golden_references(
                vcd_file=str(tmp_path / "test.vcd"),
                verilog_file=str(tmp_path / "test.v"),
                output_dir=str(tmp_path / "enhanced_plots"),
            )

        assert result == 0  # Should return success code

        # Check logging
        assert "Generated 4 types of enhanced plots:" in caplog.text
        assert "  - input_ports.png" in caplog.text
        assert "  - output_ports.png" in caplog.text
        assert "  - all_ports.png" in caplog.text
        assert "  - all_signals.png" in caplog.text
        assert "Generated comprehensive report:" in caplog.text

        # Verify methods were called
        mock_plotter_instance.load_data.assert_called_once()
        mock_plotter_instance.categorize_signals.assert_called_once()
        mock_plotter_instance.generate_plots.assert_called_once()
        mock_plotter_instance.generate_summary_report.assert_called_once()

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_render_enhanced_plots_with_golden_references_load_failure(
        self, mock_signal_plotter, tmp_path
    ) -> None:
        """Test render_enhanced_plots_with_golden_references with load_data failure."""
        mock_plotter_instance = Mock()
        mock_signal_plotter.return_value = mock_plotter_instance

        mock_plotter_instance.load_data.return_value = False

        renderer = MultiFigureRenderer()

        result = renderer.render_enhanced_plots_with_golden_references(
            vcd_file=str(tmp_path / "test.vcd"), output_dir=str(tmp_path / "enhanced_plots")
        )

        assert result == 1  # Should return error code

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_render_enhanced_plots_with_golden_references_categorize_failure(
        self, mock_signal_plotter, tmp_path
    ) -> None:
        """Test render_enhanced_plots_with_golden_references with categorize_signals failure."""
        mock_plotter_instance = Mock()
        mock_signal_plotter.return_value = mock_plotter_instance

        mock_plotter_instance.load_data.return_value = True
        mock_plotter_instance.categorize_signals.return_value = False

        renderer = MultiFigureRenderer()

        result = renderer.render_enhanced_plots_with_golden_references(
            vcd_file=str(tmp_path / "test.vcd"), output_dir=str(tmp_path / "enhanced_plots")
        )

        assert result == 1  # Should return error code

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_render_enhanced_plots_with_golden_references_generate_plots_failure(
        self, mock_signal_plotter, tmp_path
    ) -> None:
        """Test render_enhanced_plots_with_golden_references with generate_plots failure."""
        mock_plotter_instance = Mock()
        mock_signal_plotter.return_value = mock_plotter_instance

        mock_plotter_instance.load_data.return_value = True
        mock_plotter_instance.categorize_signals.return_value = True
        mock_plotter_instance.generate_plots.return_value = False

        renderer = MultiFigureRenderer()

        result = renderer.render_enhanced_plots_with_golden_references(
            vcd_file=str(tmp_path / "test.vcd"), output_dir=str(tmp_path / "enhanced_plots")
        )

        assert result == 1  # Should return error code

    def test_extract_signals_to_json_with_path_dict(self, tmp_path) -> None:
        """Test _extract_signals_to_json with path_dict parameter (lines 294-295)."""
        from vcd2image.core.models import SignalDef

        renderer = MultiFigureRenderer()

        # Create test data
        signal_def = SignalDef(name="test_signal", sid="!", length=1, path="top.signal")
        path_dict = {"top.signal": signal_def}

        output_json = tmp_path / "output.json"

        with patch("vcd2image.core.multi_renderer.WaveExtractor") as mock_extractor:
            mock_extractor_instance = Mock()
            mock_extractor.return_value = mock_extractor_instance
            mock_extractor_instance.execute.return_value = 0

            renderer._extract_signals_to_json(
                vcd_file=str(tmp_path / "test.vcd"),
                signal_paths=["top.signal"],
                json_file=str(output_json),
                path_dict=path_dict,
            )

            # Should use filtered path_dict
            mock_extractor.assert_called_once_with(
                str(tmp_path / "test.vcd"),
                str(output_json),
                ["top.signal"],
                {"top.signal": signal_def},  # filtered_dict
            )

    @patch("vcd2image.core.multi_renderer.WaveExtractor")
    def test_extract_signals_to_json_wave_extractor_failure(self, mock_extractor) -> None:
        """Test _extract_signals_to_json with WaveExtractor failure (line 301)."""
        renderer = MultiFigureRenderer()

        mock_extractor_instance = Mock()
        mock_extractor.return_value = mock_extractor_instance
        mock_extractor_instance.execute.return_value = 1  # Failure

        with pytest.raises(RuntimeError, match="Signal extraction failed with code 1"):
            renderer._extract_signals_to_json(
                vcd_file="test.vcd", signal_paths=["signal1"], json_file="output.json"
            )

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_render_auto_plot_success(self, mock_signal_plotter, tmp_path, caplog) -> None:
        """Test render_auto_plot success (lines 316-355)."""
        mock_plotter_instance = Mock()
        mock_signal_plotter.return_value = mock_plotter_instance

        # Mock successful operations
        mock_plotter_instance.load_data.return_value = True
        mock_plotter_instance.categorize_signals.return_value = True
        mock_plotter_instance.categories = Mock()
        mock_plotter_instance.categories.all_signals = ["signal1", "signal2", "signal3"]

        renderer = MultiFigureRenderer()

        output_file = tmp_path / "auto_plot.png"

        with caplog.at_level(logging.INFO):
            result = renderer.render_auto_plot(
                vcd_file=str(tmp_path / "test.vcd"), output_file=str(output_file)
            )

        assert result == 0  # Should return success code
        assert "Created enhanced auto plot:" in caplog.text

        # Verify SignalPlotter was called correctly
        mock_signal_plotter.assert_called_once_with(
            vcd_file=str(tmp_path / "test.vcd"), verilog_file=None, output_dir="."
        )

        mock_plotter_instance.load_data.assert_called_once()
        mock_plotter_instance.categorize_signals.assert_called_once()

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_render_auto_plot_load_data_failure(self, mock_signal_plotter, tmp_path) -> None:
        """Test render_auto_plot with load_data failure."""
        mock_plotter_instance = Mock()
        mock_signal_plotter.return_value = mock_plotter_instance

        mock_plotter_instance.load_data.return_value = False

        renderer = MultiFigureRenderer()

        result = renderer.render_auto_plot(
            vcd_file=str(tmp_path / "test.vcd"), output_file=str(tmp_path / "auto_plot.png")
        )

        assert result == 1  # Should return error code

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_render_auto_plot_categorize_failure(self, mock_signal_plotter, tmp_path) -> None:
        """Test render_auto_plot with categorize_signals failure."""
        mock_plotter_instance = Mock()
        mock_signal_plotter.return_value = mock_plotter_instance

        mock_plotter_instance.load_data.return_value = True
        mock_plotter_instance.categorize_signals.return_value = False

        renderer = MultiFigureRenderer()

        result = renderer.render_auto_plot(
            vcd_file=str(tmp_path / "test.vcd"), output_file=str(tmp_path / "auto_plot.png")
        )

        assert result == 1  # Should return error code

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_render_auto_plot_insufficient_signals(self, mock_signal_plotter, tmp_path) -> None:
        """Test render_auto_plot with insufficient signals."""
        mock_plotter_instance = Mock()
        mock_signal_plotter.return_value = mock_plotter_instance

        mock_plotter_instance.load_data.return_value = True
        mock_plotter_instance.categorize_signals.return_value = True
        mock_plotter_instance.categories = Mock()
        mock_plotter_instance.categories.all_signals = ["single_signal"]  # Only one signal

        renderer = MultiFigureRenderer()

        result = renderer.render_auto_plot(
            vcd_file=str(tmp_path / "test.vcd"), output_file=str(tmp_path / "auto_plot.png")
        )

        assert result == 1  # Should return error code due to insufficient signals

    @patch("vcd2image.core.multi_renderer.SignalPlotter")
    def test_render_auto_plot_categories_none(self, mock_signal_plotter, tmp_path) -> None:
        """Test render_auto_plot when categories is None."""
        mock_plotter_instance = Mock()
        mock_signal_plotter.return_value = mock_plotter_instance

        mock_plotter_instance.load_data.return_value = True
        mock_plotter_instance.categorize_signals.return_value = True
        mock_plotter_instance.categories = None  # categories is None

        renderer = MultiFigureRenderer()

        result = renderer.render_auto_plot(
            vcd_file=str(tmp_path / "test.vcd"), output_file=str(tmp_path / "auto_plot.png")
        )

        assert result == 1  # Should return error code
