"""Tests for wave renderer module."""

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from vcd2image.core.renderer import WaveRenderer

if TYPE_CHECKING:
    pass


class TestWaveRenderer:
    """Test WaveRenderer class."""

    @pytest.fixture
    def sample_wavejson(self) -> dict:
        """Sample WaveJSON data for testing."""
        return {
            "head": {"tock": 1},
            "signal": [
                {"name": "clock", "wave": "p."},
                {"name": "data", "wave": "=.=", "data": ["00", "FF"]},
            ],
        }

    def test_init(self) -> None:
        """Test renderer initialization."""
        renderer = WaveRenderer(skin="dark")
        assert renderer.skin == "dark"

        renderer_default = WaveRenderer()
        assert renderer_default.skin == "default"

    def test_render_to_image_missing_json(self) -> None:
        """Test rendering with missing JSON file raises error."""
        renderer = WaveRenderer()

        with pytest.raises(FileNotFoundError, match="JSON file not found"):
            renderer.render_to_image("nonexistent.json", "output.png")

    def test_render_to_image_missing_image_dir(self, tmp_path) -> None:
        """Test rendering creates output directory if needed."""
        json_file = tmp_path / "input.json"
        json_file.write_text('{"head": {"tock": 1}, "signal": [{"name": "test", "wave": "0"}]}')

        image_file = tmp_path / "subdir" / "output.png"

        renderer = WaveRenderer()

        result = renderer.render_to_image(str(json_file), str(image_file))

        assert result == 0
        assert image_file.exists()
        assert image_file.parent.exists()

    def test_render_to_image_success(self, tmp_path, sample_wavejson) -> None:
        """Test successful image rendering."""
        json_file = tmp_path / "input.json"
        json_file.write_text(str(sample_wavejson).replace("'", '"'))

        image_file = tmp_path / "output.png"

        renderer = WaveRenderer()
        result = renderer.render_to_image(str(json_file), str(image_file))

        assert result == 0
        assert image_file.exists()

    def test_render_to_html_missing_json(self) -> None:
        """Test HTML rendering with missing JSON file raises error."""
        renderer = WaveRenderer()

        with pytest.raises(FileNotFoundError, match="JSON file not found"):
            renderer.render_to_html("nonexistent.json", "output.html")

    def test_render_to_html_success(self, tmp_path, sample_wavejson) -> None:
        """Test successful HTML rendering."""
        json_file = tmp_path / "input.json"
        json_file.write_text(str(sample_wavejson).replace("'", '"'))

        html_file = tmp_path / "output.html"

        renderer = WaveRenderer()
        result = renderer.render_to_html(str(json_file), str(html_file))

        assert result == 0
        assert html_file.exists()

        html_content = html_file.read_text()
        assert "<!DOCTYPE html>" in html_content
        assert "WaveJSON Data" in html_content

    def test_generate_html_content(self, sample_wavejson) -> None:
        """Test HTML content generation."""
        renderer = WaveRenderer()

        html = renderer._generate_html(sample_wavejson)

        assert "<!DOCTYPE html>" in html
        assert "WaveJSON Data" in html
        assert "json-container" in html

        # Check that WaveJSON is embedded
        import json

        expected_json = json.dumps(sample_wavejson, indent=2)
        assert expected_json in html

    def test_render_to_image_no_signals(self, tmp_path) -> None:
        """Test rendering with no signals in WaveJSON."""
        json_file = tmp_path / "input.json"
        # Create WaveJSON with empty signal list
        wavejson = {"head": {"tock": 1}, "signal": []}
        json_file.write_text(str(wavejson).replace("'", '"'))

        image_file = tmp_path / "output.png"

        renderer = WaveRenderer()
        with patch('vcd2image.core.renderer.logger') as mock_logger:
            result = renderer.render_to_image(str(json_file), str(image_file))

            assert result == 0  # Should succeed but not create image
            assert not image_file.exists()  # No image should be created
            mock_logger.warning.assert_called_once_with("No signals found in WaveJSON")

    def test_parse_wavejson_no_signal_key(self) -> None:
        """Test _parse_wavejson with missing signal key."""
        renderer = WaveRenderer()

        # WaveJSON without "signal" key
        wavejson = {"head": {"tock": 1}}

        signals, time_steps = renderer._parse_wavejson(wavejson)
        assert signals == []
        assert time_steps == 0

    def test_parse_signal_empty_name_or_wave(self) -> None:
        """Test _parse_signal with empty name or wave."""
        renderer = WaveRenderer()

        # Test with empty name
        signal_dict = {"name": "", "wave": "01"}
        result = renderer._parse_signal(signal_dict)
        assert result is None

        # Test with empty wave
        signal_dict = {"name": "test", "wave": ""}
        result = renderer._parse_signal(signal_dict)
        assert result is None

        # Test with missing name
        signal_dict = {"wave": "01"}
        result = renderer._parse_signal(signal_dict)
        assert result is None

    def test_parse_wavejson_time_groups(self) -> None:
        """Test _parse_wavejson with time groups containing multiple signals."""
        renderer = WaveRenderer()

        # WaveJSON with time group
        wavejson = {
            "head": {"tock": 1},
            "signal": [
                {"name": "clock", "wave": "p."},
                [  # Time group with multiple signals
                    "10",  # timestamp
                    {"name": "signal1", "wave": "01"},
                    {"name": "signal2", "wave": "10"}
                ]
            ]
        }

        signals, time_steps = renderer._parse_wavejson(wavejson)
        assert len(signals) == 3  # clock + signal1 + signal2
        signal_names = [s["name"] for s in signals]
        assert "clock" in signal_names
        assert "signal1" in signal_names
        assert "signal2" in signal_names

    def test_parse_signal_with_string_data(self) -> None:
        """Test signal parsing with string data_str (line 185)."""
        renderer = WaveRenderer()

        # Test with string data_str instead of list
        signal_dict = {
            "name": "test_signal",
            "wave": "=2=3",
            "data": "2 3"  # Space-separated string
        }
        result = renderer._parse_signal(signal_dict)

        # Should parse string and replace = markers with data values
        assert result is not None
        assert result["name"] == "test_signal"
        assert len(result["values"]) == 4  # =2=3 becomes [2, =, 3, =] but then processed
        assert "2" in result["values"]
        assert "3" in result["values"]

    def test_parse_signal_data_index_overflow(self) -> None:
        """Test signal parsing when data index exceeds data values (line 193)."""
        renderer = WaveRenderer()

        # More = markers than data values
        signal_dict = {
            "name": "test_signal",
            "wave": "=2=3=4",
            "data": ["2", "3"]  # Only 2 data values for 3 = markers
        }
        result = renderer._parse_signal(signal_dict)

        # Should set remaining = markers to "x"
        assert result is not None
        assert result["name"] == "test_signal"
        assert len(result["values"]) == 6  # =2=3=4 becomes [=, 2, =, 3, =, 4] then processed
        assert "2" in result["values"]
        assert "3" in result["values"]
        assert "x" in result["values"]  # Overflow becomes "x"

    def test_parse_wave_string_unknown_character(self) -> None:
        """Test wave string parsing with unknown character (lines 220-221)."""
        renderer = WaveRenderer()

        # Wave string with unknown character
        wave_str = "01?"  # ? is unknown, no valid char after
        values = renderer._parse_wave_string(wave_str)

        # Unknown character should become "x"
        assert values == ["0", "1", "x"]

    def test_get_signal_color_input(self) -> None:
        """Test input signal color assignment (line 286)."""
        renderer = WaveRenderer()

        # Test various input signal names
        assert renderer._get_signal_color({"name": "data_in"}) == "#1f77b4"  # Blue
        assert renderer._get_signal_color({"name": "input_signal"}) == "#1f77b4"
        assert renderer._get_signal_color({"name": "din"}) == "#1f77b4"

    def test_get_signal_color_output(self) -> None:
        """Test output signal color assignment (line 293)."""
        renderer = WaveRenderer()

        # Test various output signal names
        assert renderer._get_signal_color({"name": "data_out"}) == "#2ca02c"  # Green
        assert renderer._get_signal_color({"name": "output_signal"}) == "#2ca02c"
        assert renderer._get_signal_color({"name": "dout"}) == "#2ca02c"

    def test_get_signal_color_reset(self) -> None:
        """Test reset signal color assignment (line 301)."""
        renderer = WaveRenderer()

        # Test various reset signal names
        assert renderer._get_signal_color({"name": "reset"}) == "#ff7f0e"  # Orange
        assert renderer._get_signal_color({"name": "rst"}) == "#ff7f0e"
        assert renderer._get_signal_color({"name": "clear"}) == "#ff7f0e"

    @patch("matplotlib.pyplot.figure")
    def test_plot_signal_data_empty_values(self, mock_figure) -> None:
        """Test plotting signal data with empty values (line 319)."""
        renderer = WaveRenderer()

        # Mock figure and axes
        mock_fig = mock_figure.return_value
        mock_ax = mock_fig.add_subplot.return_value

        # Call with empty values - should return early
        renderer._plot_signal_data(mock_ax, [], 10, "blue")

        # Should not have called any plotting functions
        mock_ax.plot.assert_not_called()

    @patch("matplotlib.pyplot.figure")
    def test_plot_signal_data_x_state(self, mock_figure) -> None:
        """Test plotting signal data with x state (line 341)."""
        renderer = WaveRenderer()

        # Mock figure and axes
        mock_fig = mock_figure.return_value
        mock_ax = mock_fig.add_subplot.return_value

        # Call with x state values
        renderer._plot_signal_data(mock_ax, ["x"], 1, "red")

        # Should have called plot with x marker
        mock_ax.plot.assert_called()
        call_args = mock_ax.plot.call_args
        assert call_args[1]["marker"] == "x"
        assert call_args[1]["color"] == "red"

    @patch("matplotlib.pyplot.figure")
    def test_plot_signal_data_z_state(self, mock_figure) -> None:
        """Test plotting signal data with z state (line 353)."""
        renderer = WaveRenderer()

        # Mock figure and axes
        mock_fig = mock_figure.return_value
        mock_ax = mock_fig.add_subplot.return_value

        # Call with z state values
        renderer._plot_signal_data(mock_ax, ["z"], 1, "gray")

        # Should have called plot with diamond marker
        mock_ax.plot.assert_called()
        call_args = mock_ax.plot.call_args
        assert call_args[1]["marker"] == "D"
        assert call_args[1]["color"] == "gray"

    @patch("matplotlib.pyplot.figure")
    def test_plot_signal_data_unknown_char_exception(self, mock_figure) -> None:
        """Test plotting signal data with unknown character exception (lines 375-377)."""
        renderer = WaveRenderer()

        # Mock figure and axes
        mock_fig = mock_figure.return_value
        mock_ax = mock_fig.add_subplot.return_value

        # Make plot raise an exception to trigger the exception handler
        mock_ax.plot.side_effect = [ValueError("Test exception"), None]

        # Call with some value that might cause issues
        renderer._plot_signal_data(mock_ax, ["?"], 1, "red")

        # Should have called plot twice - first failed, second succeeded with fallback
        assert mock_ax.plot.call_count == 2
