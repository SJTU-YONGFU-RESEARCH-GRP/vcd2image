"""Tests for wave renderer module."""

from typing import TYPE_CHECKING

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

