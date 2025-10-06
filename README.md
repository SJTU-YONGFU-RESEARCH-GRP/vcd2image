# VCD2Image

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/vcd2image.svg)](https://pypi.org/project/vcd2image/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checking: mypy](https://img.shields.io/badge/type%20checking-mypy-blue.svg)](https://mypy-lang.org/)
[![Test Status](https://img.shields.io/github/actions/workflow/status/SJTU-YONGFU-RESEARCH-GRP/vcd2image/ci.yml?branch=main&label=tests)](https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image/actions)
[![GitHub release](https://img.shields.io/github/release/SJTU-YONGFU-RESEARCH-GRP/vcd2image.svg)](https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image/releases)
[![GitHub stars](https://img.shields.io/github/stars/SJTU-YONGFU-RESEARCH-GRP/vcd2image.svg)](https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/SJTU-YONGFU-RESEARCH-GRP/vcd2image.svg)](https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/SJTU-YONGFU-RESEARCH-GRP/vcd2image.svg)](https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image/pulls)

**Convert VCD (Value Change Dump) files to beautiful timing diagram images**

VCD2Image is a modern Python tool that converts VCD (Value Change Dump) files from digital circuit simulations into professional timing diagram images. It uses WaveDrom, the industry-standard JavaScript library for rendering digital timing diagrams, to generate publication-quality SVG and PNG images.

## ✨ Features

- **🚀 Fast VCD Processing**: Efficiently parse large VCD files from Verilog/VHDL simulations
- **🎨 Professional Diagrams**: Generate beautiful timing diagrams using WaveDrom
- **🔧 Flexible Output**: Support for multiple image formats (SVG, PNG, PDF)
- **⚙️ Customizable**: Configurable signal formatting, sampling rates, and diagram styles
- **🖥️ CLI & API**: Both command-line interface and Python API for integration
- **🎯 Type-Safe**: Full type annotations and modern Python practices

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install vcd2image
```

### From Source

```bash
git clone https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image.git
cd vcd2image
pip install -e .
```

### With Rendering Dependencies

For image generation (PNG/PDF), install with rendering extras:

```bash
pip install vcd2image[rendering]
```

## 🚀 Quick Start

### Command Line

```bash
# Convert VCD to JSON
vcd2image timer.vcd -o timer.json -s clock reset pulse counter

# Convert JSON to image
vcd2image timer.json -i timer.png

# Full pipeline: VCD → JSON → Image
vcd2image timer.vcd -s clock reset pulse counter --image timer.png
```

### Python API

```python
from vcd2image import WaveExtractor, WaveRenderer

# Extract signals from VCD
extractor = WaveExtractor('timer.vcd', 'timer.json', [
    'tb_timer/u_timer/clock',
             'tb_timer/u_timer/reset',
             'tb_timer/u_timer/pulse',
    'tb_timer/u_timer/counter'
])
extractor.execute()

# Render to image
renderer = WaveRenderer()
renderer.render_to_image('timer.json', 'timer.png')
```

## 📖 Usage Examples

### Basic Signal Extraction

```bash
# List all available signals in a VCD file
vcd2image timer.vcd --list-signals

# Extract specific signals with custom formatting
vcd2image timer.vcd -o output.json \
    -s clock reset pulse counter \
    --format hex \
    --wave-chunk 25 \
    --start-time 100 \
    --end-time 1000
```

### Advanced Configuration

```python
from vcd2image import WaveExtractor

extractor = WaveExtractor('simulation.vcd', 'waves.json', signal_paths)

# Configure sampling
extractor.wave_chunk = 30  # Samples per group
extractor.start_time = 50  # Start at time 50
extractor.end_time = 500   # End at time 500

# Set display formats for multi-bit signals
extractor.wave_format('data_bus', 'x')  # Hexadecimal
extractor.wave_format('counter', 'd')   # Decimal

extractor.execute()
```

## 🎨 Output Formats

VCD2Image generates WaveJSON format that can be rendered into multiple image formats:

- **SVG**: Scalable vector graphics, perfect for documentation
- **PNG**: Raster images with transparent backgrounds
- **PDF**: Vector format for high-quality printing

## 🔧 Configuration

### Environment Variables

```bash
export VCD2IMAGE_WAVE_CHUNK=20
export VCD2IMAGE_SKIN=default
export VCD2IMAGE_FORMAT=png
```

### Configuration File

Create a `config.yaml` or use environment variables for persistent settings.

## 🏗️ Architecture

```
vcd2image/
├── cli/           # Command-line interface
├── core/          # Core business logic
│   ├── extractor.py    # VCD parsing and WaveJSON generation
│   ├── renderer.py     # WaveDrom-based image rendering
│   ├── parser.py       # VCD file parsing
│   ├── sampler.py      # Signal sampling
│   └── models.py       # Data models
└── utils/         # Utilities and configuration
```

## 📚 API Reference

### WaveExtractor

Main class for extracting timing data from VCD files.

```python
class WaveExtractor:
    def __init__(self, vcd_file: str, json_file: str, path_list: List[str])
    def execute(self) -> int
    def print_props(self) -> int
    def wave_format(self, signal_path: str, fmt: str) -> int

    @property
    def wave_chunk(self) -> int
    @property
    def start_time(self) -> int
    @property
    def end_time(self) -> int
```

### WaveRenderer

Renders WaveJSON to images using WaveDrom.

```python
class WaveRenderer:
    def __init__(self, skin: str = "default")
    def render_to_image(self, json_file: str, image_file: str) -> int
```

## 🧪 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image.git
cd vcd2image

# Run installation script (recommended)
./scripts/install.sh

# Or manual setup:
# python -m venv venv
# source venv/bin/activate  # On Windows: venv\Scripts\activate
# pip install -e ".[dev,rendering]"
```

### Run Tests

```bash
# Run all tests and quality checks
./scripts/test.sh

# Or run individual test types:
./scripts/test.sh --unit     # Only unit tests
./scripts/test.sh --lint     # Only linting
./scripts/test.sh --type     # Only type checking
./scripts/test.sh --format   # Only code formatting

# Or manual testing:
pytest
```

### Code Quality

```bash
# All quality checks (via test script)
./scripts/test.sh

# Individual tools:
ruff check .          # Linting
ruff format .         # Code formatting
mypy src/            # Type checking
```

### Development Scripts

The `scripts/` directory contains helpful utilities for development:

```bash
# Complete development setup
./scripts/install.sh

# Run comprehensive testing suite
./scripts/test.sh

# GitHub operations (init, push, releases, etc.)
./scripts/github_ops.sh help
```

See [scripts/SCRIPTS.md](scripts/SCRIPTS.md) for detailed documentation of available scripts.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the CC BY 4.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [WaveDrom](https://wavedrom.com/) - The amazing timing diagram rendering library
- Original `vcd2json` implementation that inspired this project

## 📞 Support

- 📖 [Documentation](https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image#readme)
- 🐛 [Issue Tracker](https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image/issues)
- 💬 [Discussions](https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image/discussions)
- 📧 [Email Support](mailto:)

---

**Made with ❤️ for the digital design community**
