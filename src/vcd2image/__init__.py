"""VCD to Image Converter - Convert VCD files to timing diagram images via WaveJSON."""

from .core.extractor import WaveExtractor
from .core.renderer import WaveRenderer

__all__ = ["WaveExtractor", "WaveRenderer"]
__version__ = "0.1.0"
