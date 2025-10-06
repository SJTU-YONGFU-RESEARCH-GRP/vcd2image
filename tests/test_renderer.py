"""Tests for wave renderer module."""

from typing import TYPE_CHECKING
from unittest.mock import patch, MagicMock

import pytest

from vcd2image.core.renderer import WaveRenderer

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


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
        json_file.write_text('{"test": "data"}')

        image_file = tmp_path / "subdir" / "output.png"

        renderer = WaveRenderer()

        with patch.object(renderer, "_render_html_to_image_async") as mock_render:
            result = renderer.render_to_image(str(json_file), str(image_file))

            assert result == 0
            mock_render.assert_called_once()

    @patch("tempfile.NamedTemporaryFile")
    @patch("os.unlink")
    def test_render_to_image_success(
        self, mock_unlink, mock_tempfile, tmp_path, sample_wavejson
    ) -> None:
        """Test successful image rendering."""
        json_file = tmp_path / "input.json"
        json_file.write_text(str(sample_wavejson).replace("'", '"'))

        image_file = tmp_path / "output.png"

        renderer = WaveRenderer()

        # Mock temporary file
        mock_temp_file = MagicMock()
        mock_temp_file.name = "temp.html"
        mock_tempfile.return_value.__enter__.return_value = mock_temp_file

        # Mock async rendering
        with patch.object(renderer, "_render_html_to_image_async") as mock_render:
            result = renderer.render_to_image(str(json_file), str(image_file))

            assert result == 0
            mock_render.assert_called_once_with("temp.html", image_file)
            mock_unlink.assert_called_once_with("temp.html")

    @patch("tempfile.NamedTemporaryFile")
    @patch("os.unlink")
    def test_render_to_image_cleanup_on_error(
        self, mock_unlink, mock_tempfile, tmp_path, sample_wavejson
    ) -> None:
        """Test temporary file cleanup on rendering error."""
        json_file = tmp_path / "input.json"
        json_file.write_text(str(sample_wavejson).replace("'", '"'))

        renderer = WaveRenderer()

        # Mock temporary file
        mock_temp_file = MagicMock()
        mock_temp_file.name = "temp.html"
        mock_tempfile.return_value.__enter__.return_value = mock_temp_file

        # Mock async rendering to raise exception
        with patch.object(
            renderer, "_render_html_to_image_async", side_effect=Exception("Render failed")
        ):
            with pytest.raises(Exception, match="Render failed"):
                renderer.render_to_image(str(json_file), "output.png")

            # Should still cleanup
            mock_unlink.assert_called_once_with("temp.html")

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
        assert "WaveDrom" in html_content
        assert "Timing Diagram" in html_content

    def test_generate_html_content(self, sample_wavejson) -> None:
        """Test HTML content generation."""
        renderer = WaveRenderer()

        html = renderer._generate_html(sample_wavejson)

        assert "<!DOCTYPE html>" in html
        assert "WaveDrom" in html
        assert "WaveDrom.ProcessAll()" in html
        assert "Timing Diagram" in html

        # Check that WaveJSON is embedded
        import json

        expected_json = json.dumps(sample_wavejson, indent=2)
        assert expected_json in html

    @pytest.mark.asyncio
    async def test_render_html_to_image_png(self, tmp_path) -> None:
        """Test async HTML to PNG rendering."""
        html_file = tmp_path / "test.html"
        html_file.write_text("<html><body>Test</body></html>")

        image_file = tmp_path / "output.png"

        renderer = WaveRenderer()

        # Mock playwright
        with patch("vcd2image.core.renderer.async_playwright") as mock_playwright:
            mock_browser = MagicMock()
            mock_page = MagicMock()
            mock_context = MagicMock()

            mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = (
                mock_browser
            )
            mock_browser.new_page.return_value = mock_page
            mock_page.query_selector.return_value = MagicMock()

            await renderer._render_html_to_image_async(str(html_file), image_file)

            mock_page.goto.assert_called_once_with(f"file://{html_file}")
            mock_page.wait_for_selector.assert_called_once_with(".waveform svg", timeout=10000)
            mock_page.screenshot.assert_called_once_with(path=str(image_file), full_page=True)

    @pytest.mark.asyncio
    async def test_render_html_to_image_svg(self, tmp_path) -> None:
        """Test async HTML to SVG rendering."""
        html_file = tmp_path / "test.html"
        html_file.write_text("<html><body>Test</body></html>")

        image_file = tmp_path / "output.svg"

        renderer = WaveRenderer()

        # Mock playwright
        with patch("vcd2image.core.renderer.async_playwright") as mock_playwright:
            mock_browser = MagicMock()
            mock_page = MagicMock()
            mock_svg_element = MagicMock()

            mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = (
                mock_browser
            )
            mock_browser.new_page.return_value = mock_page
            mock_page.query_selector.return_value = mock_svg_element
            mock_svg_element.inner_html.return_value = "<svg>test</svg>"

            await renderer._render_html_to_image_async(str(html_file), image_file)

            # Should extract SVG content and write to file
            assert image_file.exists()
            content = image_file.read_text()
            assert '<?xml version="1.0" encoding="UTF-8"?>' in content
            assert '<svg xmlns="http://www.w3.org/2000/svg"' in content

    @pytest.mark.asyncio
    async def test_render_html_to_image_no_svg_element(self, tmp_path) -> None:
        """Test rendering when no SVG element is found."""
        html_file = tmp_path / "test.html"
        html_file.write_text("<html><body>Test</body></html>")

        image_file = tmp_path / "output.svg"

        renderer = WaveRenderer()

        # Mock playwright
        with patch("vcd2image.core.renderer.async_playwright") as mock_playwright:
            mock_browser = MagicMock()
            mock_page = MagicMock()

            mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = (
                mock_browser
            )
            mock_browser.new_page.return_value = mock_page
            mock_page.query_selector.return_value = None  # No SVG element

            with pytest.raises(RuntimeError, match="Could not find SVG element"):
                await renderer._render_html_to_image_async(str(html_file), image_file)
