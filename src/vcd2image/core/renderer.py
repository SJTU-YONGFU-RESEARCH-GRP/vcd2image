"""WaveDrom-based renderer for converting WaveJSON to images."""

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None

logger = logging.getLogger(__name__)


class WaveRenderer:
    """Renderer for converting WaveJSON to images using WaveDrom."""

    def __init__(self, skin: str = "default") -> None:
        """Initialize wave renderer.

        Args:
            skin: WaveDrom skin to use for rendering.
        """
        self.skin = skin

    def render_to_image(self, json_file: str, image_file: str) -> int:
        """Render WaveJSON file to image.

        Args:
            json_file: Path to WaveJSON file.
            image_file: Path to output image file.

        Returns:
            Exit code (0 for success).
        """
        json_path = Path(json_file)
        image_path = Path(image_file)

        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_file}")

        logger.info(f"Rendering {json_file} to {image_file}")

        # Read WaveJSON
        with open(json_path, encoding="utf-8") as f:
            wavejson = json.load(f)

        # Generate HTML with WaveDrom
        html_content = self._generate_html(wavejson)

        # Save HTML to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            html_file = f.name

        try:
            # Use headless browser to render to image
            asyncio.run(self._render_html_to_image_async(html_file, image_path))
            logger.info(f"Image saved to: {image_file}")
            return 0
        finally:
            # Clean up temporary file
            os.unlink(html_file)

    async def _render_html_to_image_async(self, html_file: str, image_path: Path) -> None:
        """Render HTML file to image using Playwright.

        Args:
            html_file: Path to HTML file.
            image_path: Path to output image.
        """
        if async_playwright is None:
            raise ImportError(
                "Playwright is required for image rendering. "
                "Install with: pip install vcd2image[rendering]"
            )

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Load the HTML file
            await page.goto(f"file://{html_file}")

            # Wait for WaveDrom to render
            await page.wait_for_selector(".waveform svg", timeout=10000)

            # Take screenshot
            if image_path.suffix.lower() == ".png":
                await page.screenshot(path=str(image_path), full_page=True)
            elif image_path.suffix.lower() == ".pdf":
                await page.pdf(path=str(image_path))
            else:
                # For SVG, we need to extract the SVG content
                svg_element = await page.query_selector(".waveform svg")
                if svg_element:
                    svg_content = await svg_element.inner_html()
                    # Add SVG wrapper
                    full_svg = f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" version="1.1">\n{svg_content}\n</svg>'
                    image_path.write_text(full_svg, encoding="utf-8")
                else:
                    raise RuntimeError("Could not find SVG element in rendered page")

            await browser.close()

    def render_to_html(self, json_file: str, html_file: str) -> int:
        """Render WaveJSON to HTML file (without browser rendering).

        Args:
            json_file: Path to WaveJSON file.
            html_file: Path to output HTML file.

        Returns:
            Exit code (0 for success).
        """
        json_path = Path(json_file)
        html_path = Path(html_file)

        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_file}")

        logger.info(f"Generating HTML from {json_file} to {html_file}")

        # Read WaveJSON
        with open(json_path, encoding="utf-8") as f:
            wavejson = json.load(f)

        # Generate HTML with WaveDrom
        html_content = self._generate_html(wavejson)

        # Save HTML file
        html_path.write_text(html_content, encoding="utf-8")
        logger.info(f"HTML saved to: {html_file}")
        return 0

    def _generate_html(self, wavejson: dict) -> str:
        """Generate HTML page with WaveDrom for rendering.

        Args:
            wavejson: WaveJSON data.

        Returns:
            HTML content as string.
        """
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>WaveDrom Timing Diagram</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/wavedrom/3.5.0/wavedrom.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        .waveform {{
            margin: 20px 0;
            border-radius: 4px;
            overflow: hidden;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Timing Diagram</h1>
            <p>Generated by VCD2Image</p>
        </div>

        <div class="waveform">
            <script type="WaveDrom">
{json.dumps(wavejson, indent=2)}
            </script>
        </div>

        <div class="footer">
            <p>Rendered with <a href="https://wavedrom.com/" target="_blank">WaveDrom</a></p>
        </div>
    </div>

    <script>
        // Render WaveDrom when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            WaveDrom.ProcessAll();
        }});
    </script>
</body>
</html>"""
        return html
