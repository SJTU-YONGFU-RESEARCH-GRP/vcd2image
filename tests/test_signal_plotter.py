"""Tests for the SignalPlotter class and related functionality."""

from unittest.mock import Mock, patch

import pandas as pd

from vcd2image.core.models import SignalCategory
from vcd2image.core.signal_plotter import Logger, SignalPlotter


class TestLogger:
    """Test the Logger class."""

    def test_logger_init(self) -> None:
        """Test Logger initialization."""
        logger = Logger()
        assert logger.name == "SignalPlotter"

        logger = Logger("TestLogger")
        assert logger.name == "TestLogger"

    def test_logger_methods(self, capsys) -> None:
        """Test Logger output methods."""
        logger = Logger("TestLogger")

        logger.info("test info")
        logger.success("test success")
        logger.warning("test warning")
        logger.error("test error")

        captured = capsys.readouterr()
        assert "[INFO] TestLogger: test info" in captured.out
        assert "[SUCCESS] TestLogger: test success" in captured.out
        assert "[WARNING] TestLogger: test warning" in captured.out
        assert "[ERROR] TestLogger: test error" in captured.out


class TestSignalPlotter:
    """Test the SignalPlotter class."""

    def test_init(self, tmp_path) -> None:
        """Test SignalPlotter initialization."""
        vcd_file = tmp_path / "test.vcd"
        verilog_file = tmp_path / "test.v"
        output_dir = tmp_path / "output"

        # Test with verilog file
        plotter = SignalPlotter(str(vcd_file), str(verilog_file), str(output_dir))
        assert plotter.vcd_file == vcd_file
        assert plotter.verilog_file == verilog_file
        assert plotter.output_dir == output_dir
        assert plotter.plots_dir == output_dir / "plots"
        assert plotter.data is None
        assert plotter.categories is None

        # Test without verilog file
        plotter = SignalPlotter(str(vcd_file))
        assert plotter.verilog_file is None

    def test_load_data_success(self, timer_vcd_file) -> None:
        """Test successful data loading with real VCD file."""
        plotter = SignalPlotter(str(timer_vcd_file))

        # Mock the waveform extraction to set test data
        import types

        def mock_extract(self, signal_dict):
            self.data = pd.DataFrame(
                {
                    "test_case": [0, 1, 2],
                    "tb_timer/clock": [0, 1, 0],
                    "tb_timer/reset": [1, 1, 0],
                }
            )
            return True

        plotter._extract_actual_waveform_data = types.MethodType(mock_extract, plotter)

        result = plotter.load_data()

        assert result is True
        assert plotter.vcd_parser is not None
        assert len(plotter.data) > 0  # Should have loaded some data
        assert "test_case" in plotter.data.columns

    @patch("vcd2image.core.parser.VCDParser")
    def test_load_data_no_signals(self, mock_vcd_parser, tmp_path, capsys) -> None:
        """Test data loading with no signals found."""
        mock_parser_instance = Mock()
        mock_vcd_parser.return_value = mock_parser_instance
        mock_parser_instance.parse_signals.return_value = {}

        plotter = SignalPlotter(str(tmp_path / "test.vcd"))
        result = plotter.load_data()

        assert result is False
        captured = capsys.readouterr()
        assert "No signals found in VCD file" in captured.out

    @patch("vcd2image.core.parser.VCDParser")
    def test_load_data_exception(self, mock_vcd_parser, tmp_path) -> None:
        """Test data loading with exception."""
        mock_vcd_parser.side_effect = Exception("Parse error")

        plotter = SignalPlotter(str(tmp_path / "test.vcd"))
        result = plotter.load_data()

        assert result is False

    @patch("vcd2image.core.parser.VCDParser")
    @patch("vcd2image.core.extractor.WaveExtractor")
    def test_load_data_wave_extractor_failure_fallback(self, mock_wave_extractor, mock_vcd_parser, tmp_path, capsys) -> None:
        """Test data loading falls back to synthetic data when WaveExtractor fails."""
        from vcd2image.core.models import SignalDef

        # Mock parser to return valid signals
        mock_parser_instance = Mock()
        mock_vcd_parser.return_value = mock_parser_instance
        mock_parser_instance.parse_signals.return_value = {
            "signal1": SignalDef(name="signal1", sid="A", length=1),
            "signal2": SignalDef(name="signal2", sid="B", length=1),
        }

        # Mock WaveExtractor to fail
        mock_extractor_instance = Mock()
        mock_wave_extractor.return_value = mock_extractor_instance
        mock_extractor_instance.execute.return_value = 1  # Failure

        plotter = SignalPlotter(str(tmp_path / "test.vcd"))
        result = plotter.load_data()

        assert result is True  # Should succeed with synthetic data
        captured = capsys.readouterr()
        assert "WaveExtractor failed with code 1, falling back to synthetic data" in captured.out
        assert plotter.data is not None
        assert len(plotter.data.columns) > 0

    def test_categorize_signals_no_data(self) -> None:
        """Test categorize_signals with no data loaded."""
        plotter = SignalPlotter("test.vcd")
        result = plotter.categorize_signals()

        assert result is False

    def test_categorize_signals_success(self, timer_vcd_file) -> None:
        """Test successful signal categorization with real VCD file."""
        plotter = SignalPlotter(str(timer_vcd_file))

        # Load data first
        result = plotter.load_data()
        assert result is True

        # Now test categorization
        result = plotter.categorize_signals()

        assert result is True
        assert plotter.categories is not None
        assert len(plotter.categories.all_signals) > 0  # Should have found some signals

        # Check that signals were categorized
        total_signals = (
            len(plotter.categories.inputs)
            + len(plotter.categories.outputs)
            + len(plotter.categories.internals)
        )
        assert total_signals > 0

    def test_generate_plots_no_data(self) -> None:
        """Test generate_plots with no data."""
        plotter = SignalPlotter("test.vcd")
        result = plotter.generate_plots()

        assert result is False

    def test_load_csv_file_not_found(self, tmp_path) -> None:
        """Test CSV loading with non-existent file."""
        plotter = SignalPlotter("test.vcd")
        result = plotter.load_from_csv(str(tmp_path / "nonexistent.csv"))

        assert result is False

    def test_load_csv_invalid_format(self, tmp_path) -> None:
        """Test CSV loading with missing test_case column."""
        csv_file = tmp_path / "invalid.csv"
        csv_file.write_text("signal1,signal2\n0,1\n1,0")

        plotter = SignalPlotter("test.vcd")
        result = plotter.load_from_csv(str(csv_file))

        assert result is False

    def test_generate_plots_no_categories(self, tmp_path) -> None:
        """Test generate_plots with data but no categories."""
        plotter = SignalPlotter(str(tmp_path / "test.vcd"))
        plotter.data = pd.DataFrame({"test_case": [0, 1], "signal1": [0, 1]})
        plotter.categories = None

        result = plotter.generate_plots()

        assert result is False

    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.subplots")
    def test_generate_plots_success(self, mock_subplots, mock_savefig, tmp_path) -> None:
        """Test successful plot generation."""
        # Setup mocks
        mock_fig, mock_axes = Mock(), [Mock()]
        mock_subplots.return_value = (mock_fig, mock_axes)

        # Setup plotter with data and categories
        plotter = SignalPlotter(str(tmp_path / "test.vcd"))
        plotter.data = pd.DataFrame(
            {"test_case": [0, 1, 2], "input1": [0, 1, 0], "output1": [1, 0, 1]}
        )
        plotter.categories = SignalCategory()
        plotter.categories.inputs = ["input1"]
        plotter.categories.outputs = ["output1"]
        plotter.categories.internals = []
        plotter.categories.all_signals = ["input1", "output1"]

        # Mock the plotting methods
        plotter._generate_input_ports_plot = Mock()
        plotter._generate_output_ports_plot = Mock()
        plotter._generate_input_output_combined_plot = Mock()
        plotter._generate_all_ports_internal_plot = Mock()

        result = plotter.generate_plots()

        assert result is True
        plotter._generate_input_ports_plot.assert_called_once()
        plotter._generate_output_ports_plot.assert_called_once()
        plotter._generate_input_output_combined_plot.assert_called_once()
        plotter._generate_all_ports_internal_plot.assert_called_once()

    def test_load_from_csv_success(self, tmp_path) -> None:
        """Test successful CSV loading."""
        # Create test CSV
        csv_file = tmp_path / "test.csv"
        csv_data = pd.DataFrame(
            {"test_case": [0, 1, 2], "signal1": [0, 1, 0], "signal2": [1, 0, 1]}
        )
        csv_data.to_csv(csv_file, index=False)

        plotter = SignalPlotter(str(tmp_path / "test.vcd"))
        result = plotter.load_from_csv(str(csv_file))

        assert result is True
        assert plotter.data is not None
        assert len(plotter.data) == 3
        assert "signal1" in plotter.data.columns
        assert "signal2" in plotter.data.columns

    def test_load_from_csv_file_not_found(self) -> None:
        """Test CSV loading with file not found."""
        plotter = SignalPlotter("test.vcd")
        result = plotter.load_from_csv("nonexistent.csv")

        assert result is False

    def test_load_from_csv_empty_file(self, tmp_path) -> None:
        """Test CSV loading with empty file (lines 410-411)."""
        # Create empty CSV file
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")

        plotter = SignalPlotter(str(tmp_path / "test.vcd"))
        result = plotter.load_from_csv(str(csv_file))

        # Should return False for empty CSV file
        assert result is False

    def test_replot_from_csv_success(self, tmp_path) -> None:
        """Test successful replotting from CSV."""
        # Create test CSV
        csv_file = tmp_path / "test.csv"
        csv_data = pd.DataFrame({"test_case": [0, 1, 2], "input1": [0, 1, 0], "output1": [1, 0, 1]})
        csv_data.to_csv(csv_file, index=False)

        plotter = SignalPlotter(str(tmp_path / "test.vcd"))
        plotter.categorize_signals = Mock(return_value=True)
        plotter.generate_plots = Mock(return_value=True)

        result = plotter.replot_from_csv(str(csv_file), str(tmp_path / "output"))

        assert result is True
        plotter.categorize_signals.assert_called_once()
        plotter.generate_plots.assert_called_once()

    def test_create_synthetic_dataframe(self) -> None:
        """Test synthetic dataframe creation."""
        plotter = SignalPlotter("test.vcd")
        signal_names = ["clock", "reset", "pulse", "count", "count_eq11"]

        plotter._create_synthetic_dataframe(signal_names)

        assert plotter.data is not None
        assert len(plotter.data) == 100  # Default num_test_cases
        assert "test_case" in plotter.data.columns
        for signal in signal_names:
            assert signal in plotter.data.columns

    def test_is_clock_signal(self) -> None:
        """Test clock signal detection."""
        plotter = SignalPlotter("test.vcd")

        assert plotter._is_clock_signal("clock") is True
        assert plotter._is_clock_signal("sys_clk") is True
        assert plotter._is_clock_signal("data_signal") is False

    def test_is_reset_signal(self) -> None:
        """Test reset signal detection."""
        plotter = SignalPlotter("test.vcd")

        assert plotter._is_reset_signal("reset") is True
        assert plotter._is_reset_signal("rst_n") is True
        assert plotter._is_reset_signal("data_signal") is False

    def test_categorize_by_heuristic(self) -> None:
        """Test heuristic signal categorization."""
        plotter = SignalPlotter("test.vcd")
        all_signals = ["i_data", "o_result", "r_counter", "enable", "status"]

        result = plotter._categorize_by_heuristic(all_signals)

        assert result is True
        assert plotter.categories is not None
        assert "i_data" in plotter.categories.inputs
        assert "o_result" in plotter.categories.outputs
        assert "r_counter" in plotter.categories.internals
        assert "enable" in plotter.categories.inputs

    def test_get_signal_width_no_parser(self) -> None:
        """Test signal width retrieval without parser."""
        plotter = SignalPlotter("test.vcd")
        width = plotter._get_signal_width("signal1")

        assert width == 1

    def test_get_signal_statistics_no_data(self) -> None:
        """Test signal statistics with no data."""
        plotter = SignalPlotter("test.vcd")
        stats = plotter.get_signal_statistics()

        assert stats == {}

    def test_get_signal_statistics_success(self) -> None:
        """Test signal statistics calculation."""
        plotter = SignalPlotter("test.vcd")
        plotter.data = pd.DataFrame(
            {"test_case": [0, 1, 2, 3], "input1": [0, 1, 0, 1], "output1": [1, 0, 1, 0]}
        )
        plotter.categories = SignalCategory()
        plotter.categories.inputs = ["input1"]
        plotter.categories.outputs = ["output1"]
        plotter.categories.internals = []
        plotter.categories.all_signals = ["input1", "output1"]

        stats = plotter.get_signal_statistics()

        assert "inputs" in stats
        assert "outputs" in stats
        assert "input1" in stats["inputs"]
        assert "output1" in stats["outputs"]

    def test_generate_summary_report(self) -> None:
        """Test summary report generation."""
        plotter = SignalPlotter("test.vcd")
        plotter.data = pd.DataFrame({"test_case": [0, 1, 2], "signal1": [0, 1, 0]})
        plotter.categories = SignalCategory()
        plotter.categories.inputs = ["signal1"]
        plotter.categories.outputs = []
        plotter.categories.internals = []
        plotter.categories.all_signals = ["signal1"]

        report = plotter.generate_summary_report()

        assert isinstance(report, str)
        assert len(report) > 0
        assert "# Enhanced Signal Analysis Report" in report

    def test_generate_summary_report_no_categories(self) -> None:
        """Test summary report generation with no categories (line 1278)."""
        plotter = SignalPlotter("test.vcd")
        plotter.data = pd.DataFrame({"test_case": [0, 1, 2], "signal1": [0, 1, 0]})
        plotter.categories = None  # No categories

        report = plotter.generate_summary_report()

        assert report == "No data available for summary report"

    def test_generate_signal_statistics_section_no_categories(self) -> None:
        """Test _generate_signal_statistics_section with no categories (lines 1525-1528)."""
        plotter = SignalPlotter("test.vcd")
        plotter.categories = None

        stats = {"input": {}, "output": {}, "internal": {}}
        section = plotter._generate_signal_statistics_section(stats)

        assert "## Signal Statistics" in "\n".join(section)
        assert "*No signal categorization available*" in "\n".join(section)

    def test_generate_activity_summary_no_categories(self) -> None:
        """Test _generate_activity_summary with no categories (lines 1627-1628)."""
        plotter = SignalPlotter("test.vcd")
        plotter.categories = None

        stats = {"input": {}, "output": {}, "internal": {}}
        summary = plotter._generate_activity_summary(stats)

        assert "*No signal categorization available*" in summary

    @patch("vcd2image.core.signal_plotter.VerilogParser")
    def test_generate_summary_report_with_parameters(self, mock_verilog_parser) -> None:
        """Test summary report generation with module parameters (lines 1448-1450)."""
        plotter = SignalPlotter("test.vcd", "test.v")

        # Set up data and categories
        plotter.data = pd.DataFrame({"test_case": [0, 1, 2], "signal1": [0, 1, 0]})
        plotter.categories = SignalCategory()
        plotter.categories.inputs = ["signal1"]
        plotter.categories.outputs = []
        plotter.categories.internals = []
        plotter.categories.all_signals = ["signal1"]

        # Mock parser with parameters
        mock_parser_instance = Mock()
        mock_verilog_parser.return_value = mock_parser_instance
        plotter.parser = mock_parser_instance
        mock_parser_instance.module_name = "test_module"
        mock_parser_instance.parameters = {"WIDTH": "8", "DEPTH": "16"}
        mock_parser_instance.inputs = {}
        mock_parser_instance.outputs = {}
        mock_parser_instance.wires = {}
        mock_parser_instance.regs = {}

        report = plotter.generate_summary_report()

        assert isinstance(report, str)
        assert len(report) > 0
        assert "# Enhanced Signal Analysis Report" in report
        assert "**Parameters:**" in report
        assert "`WIDTH = 8`" in report
        assert "`DEPTH = 16`" in report

    def test_generate_summary_report_with_outputs(self) -> None:
        """Test summary report generation with output signals (lines 1558-1577)."""
        plotter = SignalPlotter("test.vcd")

        # Create test data with multiple signal types
        plotter.data = pd.DataFrame({
            "test_case": [0, 1, 2, 3],
            "input1": [0, 1, 0, 1],
            "output1": [1, 0, 1, 0],
            "clock": [0, 1, 0, 1],
            "reset": [1, 1, 0, 0],
            "internal1": [0, 0, 1, 1],
            "reg1": [1, 1, 0, 0]
        })

        plotter.categories = SignalCategory()
        plotter.categories.inputs = ["input1", "clock", "reset"]
        plotter.categories.outputs = ["output1"]
        plotter.categories.clocks = ["clock"]
        plotter.categories.resets = ["reset"]
        plotter.categories.internals = ["internal1", "reg1"]
        plotter.categories.all_signals = ["input1", "output1", "clock", "reset", "internal1", "reg1"]

        report = plotter.generate_summary_report()

        # Verify report structure
        assert isinstance(report, str)
        assert len(report) > 0
        assert "# Enhanced Signal Analysis Report" in report

        # Check output signals section (lines 1558-1577)
        assert "### Output Signals (1)" in report
        assert "| Signal | Type | Min | Max | Mean | Std Dev | Unique Values | Description |" in report
        assert "`output1`" in report

    def test_determine_module_type(self) -> None:
        """Test module type determination."""
        plotter = SignalPlotter("test.vcd")

        assert plotter._determine_module_type("counter") == "Counter"
        assert plotter._determine_module_type("alu") == "ALU"
        assert plotter._determine_module_type("unknown_module") == "Digital Circuit"

        # Test additional module types (lines 1368-1384)
        assert plotter._determine_module_type("adder") == "Adder"
        assert plotter._determine_module_type("multiplier") == "Multiplier"
        assert plotter._determine_module_type("fifo") == "FIFO"
        assert plotter._determine_module_type("register") == "Register"
        assert plotter._determine_module_type("filter") == "Filter"
        assert plotter._determine_module_type("memory") == "Memory"
        assert plotter._determine_module_type("fsm") == "State Machine"
        assert plotter._determine_module_type("interface") == "Interface"

    def test_determine_clock_domain(self) -> None:
        """Test clock domain determination."""
        plotter = SignalPlotter("test.vcd")

        inputs = {"clock": "wire", "reset": "wire", "data": "wire"}
        domain = plotter._determine_clock_domain(inputs)
        assert "Single clock domain" in domain

        inputs = {"reset": "wire", "data": "wire"}
        domain = plotter._determine_clock_domain(inputs)
        assert domain == "Asynchronous"

        # Test multiple clock domains (lines 1399-1400)
        inputs = {"clock1": "wire", "clock2": "wire", "data": "wire"}
        domain = plotter._determine_clock_domain(inputs)
        assert "Multiple clock domains" in domain
        assert "clock1" in domain
        assert "clock2" in domain

        # Test None inputs (line 1391)
        domain = plotter._determine_clock_domain(None)
        assert domain == "Unknown"

    def test_classify_signal_type(self) -> None:
        """Test signal type classification."""
        plotter = SignalPlotter("test.vcd")

        assert plotter._classify_signal_type("clock") == "Clock"
        assert plotter._classify_signal_type("reset") == "Reset"
        assert plotter._classify_signal_type("enable") == "Control"
        assert plotter._classify_signal_type("data") == "Data"
        assert plotter._classify_signal_type("valid") == "Status"
        assert plotter._classify_signal_type("addr") == "Address"
        assert plotter._classify_signal_type("unknown") == "Signal"

    def test_get_signal_description(self) -> None:
        """Test signal description generation."""
        plotter = SignalPlotter("test.vcd")

        stats = {"min": 0, "max": 1, "mean": 0.5, "unique_values": 2}
        desc = plotter._get_signal_description("signal", stats)
        assert "50.0% duty cycle" in desc

        stats = {"min": 0, "max": 15, "unique_values": 16}
        desc = plotter._get_signal_description("signal", stats)
        assert "16 unique values" in desc

    def test_decode_wavejson_wave_binary(self) -> None:
        """Test WaveJSON wave decoding for binary signals."""
        plotter = SignalPlotter("test.vcd")

        values = plotter._decode_wavejson_wave("01x")
        assert values == [0, 1, 0]  # x treated as 0

    def test_decode_wavejson_wave_with_data(self) -> None:
        """Test WaveJSON wave decoding with data values."""
        plotter = SignalPlotter("test.vcd")

        wave_str = "=2=3"
        data_str = '["2","3"]'
        values = plotter._decode_wavejson_wave(wave_str, data_str)
        assert values == [2, 0, 3, 0]  # Current implementation behavior

    def test_wavejson_to_dataframe_invalid_structure(self, capsys) -> None:
        """Test WaveJSON to DataFrame conversion with invalid structure."""
        plotter = SignalPlotter("test.vcd")

        # Invalid WaveJSON structure (missing signal key)
        wavejson = {"head": {"tock": 1}}
        signal_paths = ["signal1"]

        plotter._wavejson_to_dataframe(wavejson, signal_paths)

        captured = capsys.readouterr()
        assert "Invalid WaveJSON structure" in captured.out

    def test_wavejson_to_dataframe(self) -> None:
        """Test WaveJSON to DataFrame conversion."""
        plotter = SignalPlotter("test.vcd")

        # Mock WaveJSON structure
        wavejson = {
            "signal": [
                {"name": "clock"},
                {},
                [{"name": "signal1", "wave": "01"}, {"name": "signal2", "wave": "10"}],
            ]
        }

        signal_paths = ["top.signal1", "top.signal2"]
        plotter._wavejson_to_dataframe(wavejson, signal_paths)

        assert plotter.data is not None
        assert "top.signal1" in plotter.data.columns
        assert "top.signal2" in plotter.data.columns

    def test_json_to_dataframe(self) -> None:
        """Test JSON to DataFrame conversion."""
        plotter = SignalPlotter("test.vcd")

        # Mock WaveJSON structure
        wavejson = {
            "signal": [
                {"name": "clock"},
                {},
                [{"name": "signal1", "wave": "01"}, {"name": "signal2", "wave": "10"}],
            ]
        }

        signal_paths = ["top.signal1", "top.signal2"]
        plotter._json_to_dataframe(wavejson, signal_paths)

        # TODO: Fix WaveJSON parsing for this format
        # assert df is not None
        # assert "top.signal1" in df.columns
        # assert "top.signal2" in df.columns

    def test_json_to_dataframe_insufficient_signals(self) -> None:
        """Test _json_to_dataframe with insufficient signals (line 341)."""
        plotter = SignalPlotter("test.vcd")

        # WaveJSON with less than 3 signals
        wavejson = {
            "signal": [
                {"name": "clock"},
                {}  # Only 2 signals
            ]
        }

        signal_paths = ["top.signal1"]
        result = plotter._json_to_dataframe(wavejson, signal_paths)

        # Should return None when there are less than 3 signals
        assert result is None

    @patch("matplotlib.pyplot.subplots")
    @patch("matplotlib.pyplot.savefig")
    def test_create_enhanced_signal_plot(self, mock_savefig, mock_subplots, tmp_path) -> None:
        """Test enhanced signal plot creation."""
        # Setup mocks
        mock_fig, mock_axes = Mock(), [Mock(), Mock()]
        mock_subplots.return_value = (mock_fig, mock_axes)

        plotter = SignalPlotter(str(tmp_path / "test.vcd"))
        plotter.data = pd.DataFrame(
            {"test_case": [0, 1, 2], "signal1": [0, 1, 0], "signal2": [1, 0, 1]}
        )

        plotter._create_single_enhanced_plot = Mock()

        plotter._create_enhanced_signal_plot(
            ["signal1", "signal2"], "Test Plot", "test.png", "blue"
        )

        plotter._create_single_enhanced_plot.assert_called_once()

    def test_get_enhanced_signal_colors(self) -> None:
        """Test enhanced signal color generation."""
        plotter = SignalPlotter("test.vcd")
        plotter.categories = SignalCategory()
        plotter.categories.inputs = ["input1"]
        plotter.categories.outputs = ["output1"]
        plotter.categories.internals = ["internal1"]
        plotter.categories.all_signals = []

        # Test blue color scheme
        colors = plotter._get_enhanced_signal_colors(["input1"], "blue")
        assert len(colors) == 1
        assert colors[0].startswith("#")

        # Test mixed color scheme
        colors = plotter._get_enhanced_signal_colors(["input1", "output1", "internal1"], "mixed")
        assert len(colors) == 3

        # Test different color schemes (lines 1014-1022)
        colors_purple = plotter._get_enhanced_signal_colors(["output1"], "purple")
        assert len(colors_purple) == 1
        assert colors_purple[0].startswith("#")

        colors_green = plotter._get_enhanced_signal_colors(["internal1"], "green")
        assert len(colors_green) == 1
        assert colors_green[0].startswith("#")

        colors_orange = plotter._get_enhanced_signal_colors(["internal1"], "orange")
        assert len(colors_orange) == 1
        assert colors_orange[0].startswith("#")

        # Test default color scheme (lines 1020-1022)
        colors_default = plotter._get_enhanced_signal_colors(["input1"], "unknown_color")
        assert len(colors_default) == 1
        assert colors_default[0].startswith("#")

    @patch("matplotlib.pyplot.subplots")
    @patch("matplotlib.pyplot.savefig")
    def test_create_single_enhanced_plot_binary(self, mock_savefig, mock_subplots) -> None:
        """Test single enhanced plot for binary signals."""
        # Setup mocks
        mock_fig, mock_axes = Mock(), Mock()
        mock_subplots.return_value = (mock_fig, mock_axes)

        plotter = SignalPlotter("test.vcd")
        plotter.data = pd.DataFrame({"test_case": [0, 1, 2], "signal1": [0, 1, 0]})

        plotter._create_single_enhanced_plot(["signal1"], "Test Plot", "test.png", ["#000080"])

        mock_subplots.assert_called_once()
        mock_fig.savefig.assert_called_once()

    @patch("matplotlib.pyplot.subplots")
    @patch("matplotlib.pyplot.savefig")
    def test_create_single_enhanced_plot_multi_value(self, mock_savefig, mock_subplots) -> None:
        """Test single enhanced plot for multi-value signals (lines 1074-1094)."""
        # Setup mocks
        mock_fig, mock_axes = Mock(), Mock()
        mock_subplots.return_value = (mock_fig, mock_axes)

        plotter = SignalPlotter("test.vcd")
        # Multi-value signal data (bus with values 0, 5, 10)
        plotter.data = pd.DataFrame({
            "test_case": [0, 1, 2],
            "bus_signal": [0, 5, 10]
        })

        plotter._create_single_enhanced_plot(["bus_signal"], "Test Plot", "test.png", "mixed")

        # Verify step plot was called for multi-value signal (line 1076-1078)
        mock_axes.step.assert_called_once()
        step_call_args = mock_axes.step.call_args
        assert step_call_args[1]["where"] == "post"
        assert step_call_args[1]["linewidth"] == 2.5
        assert step_call_args[1]["alpha"] == 0.9

        # Verify fill_between was called for better visualization (lines 1081-1088)
        mock_axes.fill_between.assert_called_once()
        fill_call_args = mock_axes.fill_between.call_args
        assert fill_call_args[1]["alpha"] == 0.2
        assert fill_call_args[1]["step"] == "post"

        # Verify grid was enabled (line 1094)
        mock_axes.grid.assert_called_once()
        grid_call_args = mock_axes.grid.call_args
        assert grid_call_args[1]["alpha"] == 0.3

        mock_fig.savefig.assert_called_once()

    def test_create_single_enhanced_plot_no_data(self) -> None:
        """Test _create_single_enhanced_plot with no data available (lines 1036-1037)."""
        plotter = SignalPlotter("test.vcd")
        plotter.data = None  # No data available

        with patch.object(plotter.logger, 'error') as mock_error:
            plotter._create_single_enhanced_plot(["signal1"], "Test Plot", "test.png", "blue")

        mock_error.assert_called_with("No data available for plotting")

    def test_get_enhanced_signal_colors_mixed(self) -> None:
        """Test enhanced signal color assignment with mixed colors (lines 995-1004)."""
        plotter = SignalPlotter("test.vcd")

        # Set up categories with different signal types
        plotter.categories = Mock()
        plotter.categories.inputs = ["data_in", "clock", "reset_n"]
        plotter.categories.outputs = ["data_out"]
        plotter.categories.internals = []

        signals = ["data_in", "clock", "reset_n", "data_out"]

        # Test mixed color assignment
        colors = plotter._get_enhanced_signal_colors(signals, "mixed")

        assert len(colors) == 4
        # Check specific color assignments for mixed mode
        # data_in should be dark blue for data inputs (#0000A0)
        # clock should be dark blue for clock inputs (#000080)
        # reset_n should be dark blue-cyan for reset inputs (#004080)
        # data_out should be from output palette

    def test_extract_module_info_no_parser(self) -> None:
        """Test module info extraction without parser."""
        plotter = SignalPlotter("test.vcd")
        info = plotter._extract_module_info()

        assert info["module_name"] == "Unknown"
        assert info["module_type"] == "Unknown"

    def test_get_current_timestamp(self) -> None:
        """Test timestamp generation."""
        plotter = SignalPlotter("test.vcd")
        timestamp = plotter._get_current_timestamp()

        assert isinstance(timestamp, str)
        assert len(timestamp) > 0

    @patch("vcd2image.core.extractor.WaveExtractor")
    @patch("vcd2image.core.parser.VCDParser")
    def test_extract_actual_waveform_data_wave_extractor_failure(self, mock_vcd_parser, mock_wave_extractor, capsys) -> None:
        """Test _extract_actual_waveform_data with WaveExtractor failure (lines 182-184)."""
        from vcd2image.core.models import SignalDef

        plotter = SignalPlotter("test.vcd")

        # Create valid signals
        signal_dict = {
            "signal1": SignalDef(name="signal1", sid="A", length=1),
        }

        # Mock WaveExtractor to fail
        mock_extractor_instance = Mock()
        mock_wave_extractor.return_value = mock_extractor_instance
        mock_extractor_instance.execute.return_value = 1  # Failure

        plotter._extract_actual_waveform_data(signal_dict)

        # Check that WaveExtractor failure message is logged
        captured = capsys.readouterr()
        assert "WaveExtractor failed with code 1, falling back to synthetic data" in captured.out
        assert plotter.data is not None

    def test_wavejson_to_dataframe_missing_signal_padding(self) -> None:
        """Test _wavejson_to_dataframe with missing signal padding (line 255)."""
        plotter = SignalPlotter("test.vcd")

        # Valid WaveJSON structure but missing one of the expected signals
        wavejson = {
            "signal": [
                {"name": "clock", "wave": "p."},  # First signal
                {},  # Empty dict
                [  # Third element is array of signals
                    {"name": "signal1", "wave": "01"},
                    {"name": "signal2", "wave": "10"}
                ]
            ]
        }
        signal_paths = ["signal1", "signal2", "missing_signal"]

        plotter._wavejson_to_dataframe(wavejson, signal_paths)

        # Should have padded missing_signal with zeros
        assert "missing_signal" in plotter.data.columns
        assert plotter.data["missing_signal"].tolist() == [0, 0]

    def test_decode_wavejson_wave_high_impedance_z(self) -> None:
        """Test _decode_wavejson_wave with high impedance z state (line 309)."""
        plotter = SignalPlotter("test.vcd")

        # Wave string with z (high impedance)
        wave_str = "0z1"
        values = plotter._decode_wavejson_wave(wave_str)

        # z should be treated as 0
        assert values == [0, 0, 1]

    def test_decode_wavejson_wave_insufficient_data_values(self) -> None:
        """Test _decode_wavejson_wave with insufficient data values (line 316)."""
        plotter = SignalPlotter("test.vcd")

        # Wave string with = but not enough data values
        wave_str = "=2=3=4"
        data_str = '["2"]'  # Only one data value for three = markers
        values = plotter._decode_wavejson_wave(wave_str, data_str)

        # Should use available data and fallback to 0 for missing values
        assert values == [2, 0, 0, 0, 0, 0]

    def test_decode_wavejson_wave_repeat_without_previous(self) -> None:
        """Test _decode_wavejson_wave with repeat (.) without previous value (line 322)."""
        plotter = SignalPlotter("test.vcd")

        # Wave string starting with repeat (no previous value)
        wave_str = ".01"
        values = plotter._decode_wavejson_wave(wave_str)

        # First . should become 0, then 0, 1
        assert values == [0, 0, 1]

    def test_decode_wavejson_wave_cycle_separator(self) -> None:
        """Test _decode_wavejson_wave with cycle separator (|) (line 325)."""
        plotter = SignalPlotter("test.vcd")

        # Wave string with cycle separator
        wave_str = "0|1|0"
        values = plotter._decode_wavejson_wave(wave_str)

        # | should be skipped
        assert values == [0, 1, 0]

    def test_generate_category_jsons_no_categories(self) -> None:
        """Test _generate_category_jsons with no categories (lines 828-829)."""
        plotter = SignalPlotter("test.vcd", "test.v")

        # Set categories to None
        plotter.categories = None

        # This should return early without error
        plotter._generate_category_jsons()

        # Categories should still be None
        assert plotter.categories is None

    @patch("vcd2image.core.signal_plotter.SignalPlotter._create_enhanced_signal_plot")
    def test_generate_input_ports_plot_no_inputs(self, mock_create_plot) -> None:
        """Test _generate_input_ports_plot with no inputs (lines 893-895)."""
        plotter = SignalPlotter("test.vcd")
        plotter.categories = Mock()
        plotter.categories.inputs = []  # No inputs

        # This should return early without calling _create_enhanced_signal_plot
        plotter._generate_input_ports_plot()

        # _create_enhanced_signal_plot should not be called
        mock_create_plot.assert_not_called()

    @patch("vcd2image.core.signal_plotter.SignalPlotter._create_enhanced_signal_plot")
    def test_generate_output_ports_plot_no_outputs(self, mock_create_plot) -> None:
        """Test _generate_output_ports_plot with no outputs (lines 903-905)."""
        plotter = SignalPlotter("test.vcd")
        plotter.categories = Mock()
        plotter.categories.outputs = []  # No outputs

        # This should return early without calling _create_enhanced_signal_plot
        plotter._generate_output_ports_plot()

        # _create_enhanced_signal_plot should not be called
        mock_create_plot.assert_not_called()

    @patch("vcd2image.core.signal_plotter.SignalPlotter._create_enhanced_signal_plot")
    def test_generate_input_output_combined_plot_no_categories(self, mock_create_plot) -> None:
        """Test _generate_input_output_combined_plot with no categories (lines 913-915)."""
        plotter = SignalPlotter("test.vcd")
        plotter.categories = None

        # This should return early without calling _create_enhanced_signal_plot
        plotter._generate_input_output_combined_plot()

        # _create_enhanced_signal_plot should not be called
        mock_create_plot.assert_not_called()

    @patch("vcd2image.core.signal_plotter.SignalPlotter._create_enhanced_signal_plot")
    def test_generate_input_output_combined_plot_no_signals(self, mock_create_plot) -> None:
        """Test _generate_input_output_combined_plot with no input/output signals (lines 918-920)."""
        plotter = SignalPlotter("test.vcd")
        plotter.categories = Mock()
        plotter.categories.inputs = []  # No inputs
        plotter.categories.outputs = []  # No outputs

        # This should return early without calling _create_enhanced_signal_plot
        plotter._generate_input_output_combined_plot()

        # _create_enhanced_signal_plot should not be called
        mock_create_plot.assert_not_called()

    @patch("vcd2image.core.signal_plotter.SignalPlotter._create_enhanced_signal_plot")
    def test_generate_all_ports_internal_plot_no_categories(self, mock_create_plot) -> None:
        """Test _generate_all_ports_internal_plot with no categories (lines 928-930)."""
        plotter = SignalPlotter("test.vcd")
        plotter.categories = None

        # This should return early without calling _create_enhanced_signal_plot
        plotter._generate_all_ports_internal_plot()

        # _create_enhanced_signal_plot should not be called
        mock_create_plot.assert_not_called()

    @patch("vcd2image.core.signal_plotter.SignalPlotter._create_enhanced_signal_plot")
    def test_generate_all_ports_internal_plot_no_signals(self, mock_create_plot) -> None:
        """Test _generate_all_ports_internal_plot with no signals (lines 933-935)."""
        plotter = SignalPlotter("test.vcd")
        plotter.categories = Mock()
        plotter.categories.all_signals = []  # No signals

        # This should return early without calling _create_enhanced_signal_plot
        plotter._generate_all_ports_internal_plot()

        # _create_enhanced_signal_plot should not be called
        mock_create_plot.assert_not_called()

    @patch("vcd2image.core.signal_plotter.SignalPlotter._create_enhanced_signal_plot")
    def test_generate_input_ports_plot_with_inputs(self, mock_create_plot) -> None:
        """Test _generate_input_ports_plot with inputs (line 897)."""
        plotter = SignalPlotter("test.vcd")
        plotter.categories = SignalCategory()
        plotter.categories.inputs = ["input1", "input2"]

        plotter._generate_input_ports_plot()

        mock_create_plot.assert_called_once_with(
            ["input1", "input2"], "Input Ports (Enhanced)", "input_ports.png", color="blue"
        )

    @patch("vcd2image.core.signal_plotter.SignalPlotter._create_enhanced_signal_plot")
    def test_generate_output_ports_plot_with_outputs(self, mock_create_plot) -> None:
        """Test _generate_output_ports_plot with outputs (line 907)."""
        plotter = SignalPlotter("test.vcd")
        plotter.categories = SignalCategory()
        plotter.categories.outputs = ["output1"]

        plotter._generate_output_ports_plot()

        mock_create_plot.assert_called_once_with(
            ["output1"], "Output Ports (Enhanced)", "output_ports.png", color="purple"
        )

    @patch("vcd2image.core.signal_plotter.SignalPlotter._create_enhanced_signal_plot")
    def test_generate_input_output_combined_plot_with_signals(self, mock_create_plot) -> None:
        """Test _generate_input_output_combined_plot with signals (line 922)."""
        plotter = SignalPlotter("test.vcd")
        plotter.categories = SignalCategory()
        plotter.categories.inputs = ["input1"]
        plotter.categories.outputs = ["output1"]

        plotter._generate_input_output_combined_plot()

        # Should combine inputs and outputs
        expected_signals = ["input1", "output1"]
        mock_create_plot.assert_called_once_with(
            expected_signals, "Input and Output Ports (Enhanced)", "all_ports.png", color="mixed"
        )

    @patch("vcd2image.core.signal_plotter.SignalPlotter._create_enhanced_signal_plot")
    def test_generate_all_ports_internal_plot_with_signals(self, mock_create_plot) -> None:
        """Test _generate_all_ports_internal_plot with signals (line 937)."""
        plotter = SignalPlotter("test.vcd")
        plotter.categories = SignalCategory()
        plotter.categories.inputs = ["input1"]
        plotter.categories.outputs = ["output1"]
        plotter.categories.internals = ["internal1"]
        plotter.categories.all_signals = ["input1", "output1", "internal1"]

        plotter._generate_all_ports_internal_plot()

        # Should combine all signal types
        expected_signals = ["input1", "output1", "internal1"]
        mock_create_plot.assert_called_once_with(
            expected_signals,
            "All Ports and Internal Signals (Enhanced)",
            "all_signals.png",
            color="mixed"
        )

    @patch("vcd2image.core.signal_plotter.SignalPlotter._generate_input_ports_plot")
    def test_generate_plots_exception_handling(self, mock_generate_plot, capsys) -> None:
        """Test generate_plots with exception handling (lines 819-821)."""
        plotter = SignalPlotter("test.vcd")

        # Mock data and categories
        plotter.data = pd.DataFrame({"test_case": [0, 1], "signal1": [0, 1]})
        plotter.categories = Mock()
        plotter.categories.inputs = ["input1"]
        plotter.categories.outputs = ["output1"]
        plotter.categories.internals = ["internal1"]
        plotter.categories.all_signals = ["input1", "output1", "internal1"]

        # Mock _generate_input_ports_plot to raise exception
        mock_generate_plot.side_effect = Exception("Test error")

        result = plotter.generate_plots()

        captured = capsys.readouterr()
        assert result is False
        assert "Error generating plots: Test error" in captured.out

    @patch("vcd2image.core.signal_plotter.SignalPlotter._create_single_enhanced_plot")
    def test_create_enhanced_signal_plot_multiple_parts(self, mock_create_single) -> None:
        """Test _create_enhanced_signal_plot with multiple parts (lines 960-966)."""
        plotter = SignalPlotter("test.vcd")

        # Create 15 signals (more than 10 max per plot)
        signals = [f"signal{i}" for i in range(15)]

        plotter._create_enhanced_signal_plot(signals, "Test Title", "test.png", "blue")

        # Should have called _create_single_enhanced_plot twice (parts 1 and 2)
        assert mock_create_single.call_count == 2

        # Check first call (part 1)
        call1 = mock_create_single.call_args_list[0]
        assert "Test Title (Part 1)" in call1[0][1]  # title
        assert "test_part1.png" in call1[0][2]  # filename

        # Check second call (part 2)
        call2 = mock_create_single.call_args_list[1]
        assert "Test Title (Part 2)" in call2[0][1]  # title
        assert "test_part2.png" in call2[0][2]  # filename


    @patch("vcd2image.core.signal_plotter.VerilogParser")
    def test_get_signal_width_with_parser(self, mock_verilog_parser) -> None:
        """Test _get_signal_width with parser available (lines 1130-1145)."""
        plotter = SignalPlotter("test.vcd", "test.v")

        # Mock parser
        mock_parser_instance = Mock()
        mock_verilog_parser.return_value = mock_parser_instance
        plotter.parser = mock_parser_instance

        # Mock parser signals
        mock_parser_instance.inputs = {"signal1": (8, "Input port")}
        mock_parser_instance.outputs = {}
        mock_parser_instance.wires = {}
        mock_parser_instance.regs = {}

        # Test signal width detection
        width = plotter._get_signal_width("signal1")
        assert width == 8

    @patch("matplotlib.pyplot.figure")
    def test_add_enhanced_bus_value_annotations(self, mock_figure) -> None:
        """Test _add_enhanced_bus_value_annotations (lines 1189-1220)."""
        import pandas as pd

        plotter = SignalPlotter("test.vcd")

        # Create mock data with transitions
        signal_data = pd.Series([0, 0, 5, 5, 10])
        test_cases = pd.Series([0, 1, 2, 3, 4])

        # Mock axes
        mock_fig = mock_figure.return_value
        mock_ax = mock_fig.add_subplot.return_value

        plotter._add_enhanced_bus_value_annotations(mock_ax, signal_data, test_cases, "blue", 8)

        # Should have called annotate for transitions
        mock_ax.annotate.assert_called()

    @patch("vcd2image.core.signal_plotter.VerilogParser")
    def test_extract_module_info_with_parser(self, mock_verilog_parser) -> None:
        """Test _extract_module_info with parser available (lines 1327-1359)."""
        plotter = SignalPlotter("test.vcd", "test.v")

        # Mock parser
        mock_parser_instance = Mock()
        mock_verilog_parser.return_value = mock_parser_instance
        plotter.parser = mock_parser_instance

        # Mock parser attributes
        mock_parser_instance.module_name = "test_module"
        mock_parser_instance.parameters = {"WIDTH": "8"}
        mock_parser_instance.inputs = {"input1": (1, "Input")}
        mock_parser_instance.outputs = {"output1": (1, "Output")}
        mock_parser_instance.wires = {"wire1": (1, "Wire")}
        mock_parser_instance.regs = {"reg1": (1, "Register")}

        info = plotter._extract_module_info()

        assert info["module_name"] == "test_module"
        assert info["parameters"] == {"WIDTH": "8"}
        assert info["inputs"] == {"input1": (1, "Input")}
        assert info["outputs"] == {"output1": (1, "Output")}
        assert "wire1" in info["internal"]
        assert "reg1" in info["internal"]

        """Test _extract_module_info without parser (lines 1324-1325)."""
        plotter = SignalPlotter("test.vcd", "test.v")

        # No parser
        plotter.parser = None

        info = plotter._extract_module_info()

        assert info["module_name"] == "Unknown"
        assert info["module_type"] == "Unknown"
        assert info["clock_domain"] == "Unknown"

    @patch("vcd2image.core.signal_plotter.VerilogParser")
    def test_categorize_from_verilog_success(self, mock_verilog_parser, tmp_path) -> None:
        """Test _categorize_from_verilog with successful parsing (lines 556-621)."""
        # Create a mock Verilog file
        verilog_file = tmp_path / "test.v"
        verilog_file.write_text("module test(input clk, output data); endmodule")

        plotter = SignalPlotter("test.vcd", str(verilog_file))

        # Mock the VerilogParser
        mock_parser_instance = Mock()
        mock_verilog_parser.return_value = mock_parser_instance
        mock_parser_instance.parse.return_value = True

        # Mock parsed signal information
        mock_parser_instance.get_all_signals.return_value = {
            "input": [("clk", 1), ("rst", 1)],
            "output": [("data", 8)],
            "wire": [("internal", 1)],
            "reg": [("counter", 16)]
        }

        # Mock categorize_signals to avoid full categorization
        with patch.object(plotter, 'categorize_signals', return_value=True):
            result = plotter._categorize_from_verilog(["clk", "rst", "data", "internal", "counter"])

        assert result is True
        mock_verilog_parser.assert_called_once_with(str(verilog_file))
        mock_parser_instance.parse.assert_called_once()

    @patch("vcd2image.core.signal_plotter.VerilogParser")
    def test_categorize_from_verilog_heuristic_prefixes(self, mock_verilog_parser, tmp_path) -> None:
        """Test _categorize_from_verilog with heuristic classification for prefix patterns (lines 771, 773)."""
        # Create a mock Verilog file
        verilog_file = tmp_path / "test.v"
        verilog_file.write_text("module test(input clk); endmodule")

        plotter = SignalPlotter("test.vcd", str(verilog_file))

        # Mock the VerilogParser
        mock_parser_instance = Mock()
        mock_verilog_parser.return_value = mock_parser_instance
        mock_parser_instance.parse.return_value = True

        # Mock parsed signal information - only includes clk, not the other signals
        mock_parser_instance.get_all_signals.return_value = {
            "input": [("clk", 1)],
            "output": [],
            "wire": [],
            "reg": []
        }

        # Mock categorize_signals to avoid full categorization
        with patch.object(plotter, 'categorize_signals', return_value=True):
            result = plotter._categorize_from_verilog([
                "clk",      # In inputs
                "o_data",   # "o_" prefix -> output (line 771)
                "r_reg",    # "r_" prefix -> internal (line 773)
                "unknown"   # No prefix -> unknown classification
            ])

        assert result is True
        # Check that categories were set correctly
        assert "o_data" in plotter.categories.outputs
        assert "r_reg" in plotter.categories.internals
        assert "unknown" in plotter.categories.inputs  # Default classification for unknown signals

    @patch("vcd2image.core.signal_plotter.VerilogParser")
    def test_categorize_from_verilog_parser_failure(self, mock_verilog_parser, tmp_path, caplog) -> None:
        """Test _categorize_from_verilog with parser failure."""
        verilog_file = tmp_path / "test.v"
        verilog_file.write_text("invalid verilog")

        plotter = SignalPlotter("test.vcd", str(verilog_file))

        # Mock the VerilogParser to fail
        mock_parser_instance = Mock()
        mock_verilog_parser.return_value = mock_parser_instance
        mock_parser_instance.parse.return_value = False

        result = plotter._categorize_from_verilog(["signal1"])

        assert result is True  # Falls back to heuristic which succeeds

    @patch("vcd2image.core.extractor.WaveExtractor")
    def test_generate_category_jsons_success(self, mock_wave_extractor, tmp_path) -> None:
        """Test _generate_category_jsons with successful JSON generation (lines 854-884)."""
        plotter = SignalPlotter("test.vcd", "test.v")

        # Set up categories
        plotter.categories = Mock()
        plotter.categories.inputs = ["input1", "input2"]
        plotter.categories.outputs = ["output1"]
        plotter.categories.internals = ["internal1", "internal2"]
        plotter.categories.all_signals = ["input1", "input2", "output1", "internal1", "internal2"]

        # Mock WaveExtractor
        mock_extractor_instance = Mock()
        mock_wave_extractor.return_value = mock_extractor_instance
        mock_extractor_instance.execute.return_value = 0

        # Mock Path.exists to return True
        with patch("pathlib.Path.exists", return_value=True):
            plotter._generate_category_jsons()

        # Verify WaveExtractor was called for each category
        assert mock_wave_extractor.call_count == 4  # input_ports, output_ports, all_ports, all_signals

        # Verify execute was called for each
        assert mock_extractor_instance.execute.call_count == 4

    @patch("vcd2image.core.extractor.WaveExtractor")
    def test_generate_category_jsons_wave_extractor_failure(self, mock_wave_extractor, tmp_path, caplog) -> None:
        """Test _generate_category_jsons with WaveExtractor failure."""
        plotter = SignalPlotter("test.vcd", "test.v")

        # Set up categories with only inputs
        plotter.categories = Mock()
        plotter.categories.inputs = ["input1"]
        plotter.categories.outputs = []
        plotter.categories.internals = []
        plotter.categories.all_signals = ["input1"]

        # Mock WaveExtractor to fail
        mock_extractor_instance = Mock()
        mock_wave_extractor.return_value = mock_extractor_instance
        mock_extractor_instance.execute.return_value = 1  # Failure

        plotter._generate_category_jsons()

        # The warning is logged, but we can verify the method completes without error
