# VCD2Image

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/vcd2image.svg)](https://pypi.org/project/vcd2image/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checking: mypy](https://img.shields.io/badge/type%20checking-mypy-blue.svg)](https://mypy-lang.org/)
[![CI](https://img.shields.io/github/actions/workflow/status/SJTU-YONGFU-RESEARCH-GRP/vcd2image/ci.yml?branch=main&label=CI)](https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image/actions)
[![Code Quality](https://img.shields.io/github/actions/workflow/status/SJTU-YONGFU-RESEARCH-GRP/vcd2image/code-quality.yml?branch=main&label=quality)](https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image/actions)
[![Coverage Status](https://img.shields.io/badge/coverage-report-blue.svg)](https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image/actions)
[![GitHub release](https://img.shields.io/github/release/SJTU-YONGFU-RESEARCH-GRP/vcd2image.svg)](https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image/releases)
[![GitHub stars](https://img.shields.io/github/stars/SJTU-YONGFU-RESEARCH-GRP/vcd2image.svg)](https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/SJTU-YONGFU-RESEARCH-GRP/vcd2image.svg)](https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/SJTU-YONGFU-RESEARCH-GRP/vcd2image.svg)](https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image/pulls)

**Convert VCD (Value Change Dump) files to beautiful timing diagram images**

VCD2Image is a modern Python tool that converts VCD (Value Change Dump) files from digital circuit simulations into professional timing diagram images. It uses WaveDrom, the industry-standard JavaScript library for rendering digital timing diagrams, to generate publication-quality SVG and PNG images.

## 📋 Table of Contents

- [✨ Features](#-features)
- [📦 Installation](#-installation)
  - [From PyPI (Recommended)](#from-pypi-recommended)
  - [From Source](#from-source)
  - [With Rendering Dependencies](#with-rendering-dependencies)
- [🚀 Quick Start](#-quick-start)
  - [Command Line](#command-line)
  - [Python API](#python-api)
- [📖 Usage Examples](#-usage-examples)
  - [Basic Signal Extraction](#basic-signal-extraction)
  - [Advanced Configuration](#advanced-configuration)
- [🤖 Auto Plotting](#-auto-plotting)
  - [Single Plot Mode](#single-plot-mode)
  - [Multi-Figure Mode](#multi-figure-mode)
  - [Signal Categorization](#signal-categorization)
- [🎨 Output Formats](#-output-formats)
- [🔧 Configuration](#-configuration)
  - [Environment Variables](#environment-variables)
  - [Configuration File](#configuration-file)
- [🏗️ Architecture](#️-architecture)
- [📚 API Reference](#-api-reference)
  - [WaveExtractor](#waveextractor)
  - [WaveRenderer](#waverenderer)
  - [MultiFigureRenderer](#multifigurereenderer)
  - [SignalCategorizer](#signalcategorizer)
  - [SignalPlotter](#signalplotter)
  - [VerilogParser](#verilogparser)
- [🧪 Development](#-development)
  - [Setup Development Environment](#setup-development-environment)
  - [Run Tests](#run-tests)
  - [Code Quality](#code-quality)
  - [Development Scripts](#development-scripts)
    - [`install.sh` - Environment Setup](#installsh---environment-setup)
    - [`test.sh` - Comprehensive Testing Suite](#testsh---comprehensive-testing-suite)
    - [`clean.sh` - Project Cleaning Utility](#cleansh---project-cleaning-utility)
    - [`github_ops.sh` - GitHub Operations](#github_opssh---github-operations)
  - [Development Workflow](#development-workflow)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [🙏 Acknowledgments](#-acknowledgments)
- [📞 Support](#-support)

## ✨ Features

- **🚀 Fast VCD Processing**: Efficiently parse large VCD files from Verilog/VHDL simulations
- **🎨 Professional Diagrams**: Generate beautiful timing diagrams using WaveDrom
- **🤖 Auto Plotting**: Intelligent signal categorization and automatic diagram generation
- **🔧 Flexible Output**: Support for multiple image formats (SVG, PNG, PDF)
- **⚙️ Customizable**: Configurable signal formatting, sampling rates, and diagram styles
- **📊 Multi-Figure Generation**: Create categorized plots (ports, internal signals, etc.)
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

# Auto plotting: Generate single organized plot with all signals
vcd2image timer.vcd --auto-plot --image timer_auto.png

# Auto plotting: Generate multiple categorized figures
vcd2image timer.vcd --auto-plot --plot-dir ./figures --plot-formats png svg html
```

### Python API

```python
from vcd2image import WaveExtractor, WaveRenderer, MultiFigureRenderer

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

# Auto plotting: Generate single organized plot
multi_renderer = MultiFigureRenderer()
multi_renderer.render_auto_plot('timer.vcd', 'timer_auto.png')

# Auto plotting: Generate multiple categorized figures
multi_renderer.render_categorized_figures(
    vcd_file='timer.vcd',
    output_dir='./figures',
    formats=['png', 'svg', 'html']
)
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

# Auto plotting: Generate organized timing diagrams automatically
vcd2image timer.vcd --auto-plot --image auto_plot.png

# Advanced auto plotting: Multiple figures in different formats
vcd2image timer.vcd --auto-plot \
    --plot-dir ./waveforms \
    --plot-formats png svg html
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

## 🤖 Auto Plotting

VCD2Image features intelligent auto-plotting capabilities that automatically categorize and organize signals into meaningful timing diagrams:

### Single Plot Mode (`--auto-plot --image`)
Generates a single, well-organized timing diagram with all signals grouped logically:
- **Clock signals** at the top
- **Input ports** (reset, enable, data inputs)
- **Output ports** (data outputs, status signals)
- **Internal signals** (state machines, counters, etc.)

### Multi-Figure Mode (`--auto-plot --plot-dir`)
Creates separate categorized diagrams:
- `*_ports.png/svg/html`: Input and output ports
- `*_internal.png/svg/html`: Internal module signals
- `*_all.png/svg/html`: Complete signal overview

### Signal Categorization
The intelligent categorizer uses pattern matching to identify:
- **Clock signals**: `clock`, `clk`, `ck`
- **Input ports**: `i_`, `in`, `input`
- **Output ports**: `o_`, `out`, `output`
- **Reset signals**: `reset`, `rst`, `clear`
- **Internal signals**: `u_`, `dut_`, module hierarchies

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
│   └── main.py         # CLI entry point and argument parsing
├── core/          # Core business logic
│   ├── categorizer.py  # Intelligent signal categorization
│   ├── extractor.py    # VCD parsing and WaveJSON generation
│   ├── generator.py    # WaveJSON generation logic
│   ├── models.py       # Data models and type definitions
│   ├── multi_renderer.py # Multi-figure rendering and auto-plotting
│   ├── parser.py       # VCD file parsing
│   ├── renderer.py     # WaveDrom-based image rendering
│   ├── sampler.py      # Signal sampling and data reduction
│   ├── signal_plotter.py # Enhanced matplotlib-based plotting
│   └── verilog_parser.py # Verilog file parsing and module analysis
└── utils/         # Utilities and configuration
    └── config.py       # Configuration management and environment variables
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

### MultiFigureRenderer

Automatically generates categorized timing diagrams from VCD files with intelligent signal grouping.

```python
class MultiFigureRenderer:
    def __init__(self, skin: str = "default") -> None
    def render_auto_plot(self, vcd_file: str, output_file: str) -> int
    def render_categorized_figures(
        self,
        vcd_file: str,
        output_dir: str,
        base_name: str = "waveform",
        formats: List[str] = None
    ) -> int
```

### SignalCategorizer

Intelligent signal categorization engine that automatically groups signals based on naming patterns and hierarchy.

```python
class SignalCategorizer:
    def categorize_signals(self, signals: Dict[str, SignalDef]) -> Dict[SignalCategory, List[str]]
    def get_signal_type(self, signal_path: str) -> SignalType
```

### SignalPlotter

Enhanced plotting engine that generates matplotlib-based timing diagrams with advanced categorization and golden reference support.

```python
class SignalPlotter:
    def __init__(self, vcd_file: str, verilog_file: str = None)
    def parse_signals(self) -> bool
    def categorize_signals(self) -> SignalCategory
    def plot_signals(self, output_dir: str = "plots", format: str = "png") -> bool
    def generate_signal_report(self, output_file: str = "signal_analysis_report.md") -> bool
```

### VerilogParser

Parses Verilog files to extract module information including inputs, outputs, wires, and registers for enhanced signal analysis.

```python
@dataclass
class VerilogModule:
    name: str
    inputs: Dict[str, Tuple[int, str]]     # signal_name -> (width, description)
    outputs: Dict[str, Tuple[int, str]]
    wires: Dict[str, Tuple[int, str]]
    regs: Dict[str, Tuple[int, str]]
    parameters: Dict[str, str]

class VerilogParser:
    def __init__(self, verilog_file: str)
    def parse(self) -> bool
    def get_module_info(self) -> VerilogModule | None
    def print_module_summary(self) -> None
```

## 🧪 Development

### Setup Development Environment

#### Quick Start (Recommended)

```bash
# Clone repository
git clone https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image.git
cd vcd2image

# One-command setup for testing (includes environment + dependencies)
./scripts/setup-testing.sh

# Or use the comprehensive installation script
./scripts/install.sh
```

#### Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with development dependencies
pip install -e ".[dev,rendering]"

# Verify installation
python -c "from vcd2image.core.models import SignalDef; print('✓ Setup complete')"
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

### Continuous Integration & Deployment

VCD2Image uses GitHub Actions for automated testing and deployment across multiple platforms and Python versions.

#### CI Pipeline

The CI pipeline runs automatically on:
- **Push** to `main` and `develop` branches
- **Pull requests** targeting `main` and `develop` branches
- **Manual trigger** via GitHub Actions UI

**Test Matrix:**
- **OS:** Ubuntu, Windows, macOS
- **Python:** 3.10, 3.11, 3.12, 3.13
- **Checks:** Code formatting, linting, type checking, unit tests, examples testing

#### Workflows

- **`ci.yml`** - Main CI pipeline with cross-platform testing and coverage reporting
- **`code-quality.yml`** - Fast quality checks for pull requests (formatting, linting, types)
- **`nightly.yml`** - Daily comprehensive testing with artifact collection

#### Coverage Reporting

Test coverage is automatically uploaded to [Codecov](https://codecov.io) with detailed reports and PR comments.

**Setup Codecov (Optional):**
1. Visit [codecov.io](https://codecov.io) and sign in with GitHub
2. Add your repository (it should appear automatically after the first CI run)
3. The coverage badge will display once Codecov processes your first coverage report

**Local Coverage Reports:**
Coverage reports are also saved as CI artifacts and can be generated locally:

```bash
# Generate comprehensive coverage reports
./scripts/generate-coverage.sh

# View HTML report
python -m http.server 8000 -d htmlcov/
# Open http://localhost:8000 in your browser
```

#### Automated Dependency Updates

[Dependabot](https://github.com/dependabot) automatically creates pull requests for:
- Python dependency updates (weekly)
- GitHub Actions updates (weekly)

### Development Scripts

The `scripts/` directory contains comprehensive utilities to streamline development, testing, and deployment workflows. All scripts are designed to be idempotent, provide colored output, and include proper error handling.

#### `install.sh` - Environment Setup

**Purpose**: Automated development environment setup and dependency installation.

**Key Features**:
- Creates and activates Python virtual environment
- Installs package in development mode with optional dependencies
- Interactive menu for selecting development tools and rendering dependencies
- Installation verification and environment checks

**Usage**:
```bash
# Interactive installation (recommended)
./scripts/install.sh

# Manual activation (if not done automatically)
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
```

**Dependencies Options**:
- **Development tools**: pytest, ruff, mypy, coverage
- **Rendering extras**: playwright, pillow for image generation
- **All optional**: Complete development environment

#### `test.sh` - Comprehensive Testing Suite

**Purpose**: Run complete testing pipeline including code quality checks and unit tests.

**Key Features**:
- **Code formatting**: `ruff format` - checks code style consistency
- **Linting**: `ruff check` - identifies code quality issues
- **Type checking**: `mypy` - static type analysis
- **Unit testing**: `pytest` with coverage reporting
- **Timing information**: Performance metrics for each step
- **Selective testing**: Run specific test types individually

**Usage**:
```bash
# Run complete testing suite
./scripts/test.sh

# Run specific test categories
./scripts/test.sh --unit     # Only unit tests with coverage
./scripts/test.sh --lint     # Only linting checks
./scripts/test.sh --type     # Only type checking
./scripts/test.sh --format   # Only code formatting checks
```

#### `clean.sh` - Project Cleaning Utility

**Purpose**: Clean generated files, build artifacts, and caches while preserving source code.

**Key Features**:
- **Selective cleaning**: Clean examples, build artifacts, or everything
- **Dry-run mode**: Preview what will be deleted before execution
- **Interactive confirmation**: Prompts before destructive operations
- **Force mode**: Skip confirmations for automated workflows
- **Colored output**: Clear visual feedback for operations

**Usage**:
```bash
# Clean examples directory (generated plots, JSON files)
./scripts/clean.sh examples

# Clean everything (examples + build artifacts + caches)
./scripts/clean.sh all

# Preview what would be cleaned (dry run)
./scripts/clean.sh --dry-run
./scripts/clean.sh examples --dry-run
./scripts/clean.sh all --dry-run

# Skip confirmation prompts
./scripts/clean.sh --force
./scripts/clean.sh examples --force
./scripts/clean.sh all --force

# Show help
./scripts/clean.sh --help
```

**What Gets Cleaned**:

**Examples directory** (`examples`):
- Generated JSON files (*.json) - WaveJSON data
- Generated images (*.png, *.svg, *.html) - Plots and diagrams
- Generated directories (*single_figure/, *categorized_figures/, etc.)

**Full clean** (`all`):
- Everything in examples directory
- Python cache files (__pycache__/, *.pyc)
- Build artifacts (build/, dist/, *.egg-info/)
- Coverage reports (htmlcov/, .coverage)
- Linter caches (.ruff_cache/, .mypy_cache/)

#### `github_ops.sh` - GitHub Operations

**Purpose**: Streamlined GitHub repository management and release operations.

**Key Features**:
- **Repository initialization**: Set up git with proper .gitignore
- **Remote management**: Configure GitHub remotes
- **Push operations**: Safe and force push capabilities
- **Release management**: Automated version bumping and tagging
- **PR workflow**: Create feature branches for pull requests
- **Submodule operations**: Complete submodule lifecycle management

**Usage**:
```bash
# Repository setup
./scripts/github_ops.sh init                    # Initialize git repository
./scripts/github_ops.sh remote                 # Set up default remote
./scripts/github_ops.sh remote <url>           # Set custom remote

# Push operations
./scripts/github_ops.sh push                   # Push current branch
./scripts/github_ops.sh push main force        # Force push to main

# Release management
./scripts/github_ops.sh release 1.0.0 "Release description"
./scripts/github_ops.sh pr-branch feature/new-feature

# Submodule operations
./scripts/github_ops.sh submodule add <url> <path>
./scripts/github_ops.sh submodule update
./scripts/github_ops.sh submodule status
./scripts/github_ops.sh submodule init
./scripts/github_ops.sh submodule sync
./scripts/github_ops.sh submodule foreach "git pull origin main"

# Repository status
./scripts/github_ops.sh status
./scripts/github_ops.sh help
```

### Development Workflow

A complete development workflow using the scripts:

```bash
# 1. Initial setup
./scripts/install.sh                    # Set up environment
source venv/bin/activate               # Activate virtual environment

# 2. Repository setup
./scripts/github_ops.sh init           # Initialize git
./scripts/github_ops.sh remote         # Set up remote
./scripts/github_ops.sh submodule update  # Initialize submodules

# 3. Development cycle
# Make code changes...

# 4. Quality assurance
./scripts/test.sh                      # Run full test suite

# 5. Clean before commit (optional)
./scripts/clean.sh examples            # Clean generated files

# 6. Push changes
./scripts/github_ops.sh push           # Push to remote

# 7. Release (when ready)
./scripts/github_ops.sh release 1.0.0 "Major release"
```

For detailed documentation of all scripts, see [scripts/SCRIPTS.md](scripts/SCRIPTS.md).

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
