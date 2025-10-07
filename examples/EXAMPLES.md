# VCD2Image Examples

This directory contains core examples demonstrating the main features of the vcd2image tool.

## Overview

The `example.py` script showcases 4 core use cases that demonstrate the actual capabilities implemented in `src/vcd2image/`:

1. **Basic signal extraction (VCD to JSON)** - Extract signals and save as WaveJSON format
2. **Auto plotting with signal categorization** - Generate categorized figures with enhanced styling
3. **Enhanced plotting with golden references** - Professional plots with golden reference analysis and CSV export
4. **Signal categorization intelligence** - Understand automatic signal classification

## Workflow

The tool follows this data processing pipeline:

```
VCD → WaveExtractor → JSON → CSV → Plots
```

- **VCD**: Raw simulation data from Verilog testbenches
- **WaveExtractor**: Extracts waveforms using signal sampling
- **JSON**: Structured WaveJSON format for waveform data
- **CSV**: Tabular data for debugging and replotting
- **Plots**: Enhanced matplotlib visualizations with golden references

## Running the Examples

```bash
python examples/example.py
```

## Generated Files

After running the examples, you'll find various output files in numbered directories:

### Example 1: Basic Extraction
- `01_basic_extraction/signals.json` - WaveJSON file with extracted signals

### Example 2: Auto Plotting
- `02_auto_plotting/auto_plot.png` - Single organized plot
- `02_auto_plotting/plots/` - Categorized plots (clocks, resets, outputs, internals)
- `02_auto_plotting/plots/` - JSON files for each category (clocks.json, resets.json, outputs.json, internals.json)

### Example 3: Enhanced Plotting
- `03_enhanced_plotting/plots/` - Enhanced plots with golden references
- `03_enhanced_plotting/plots/signal_data.csv` - Complete signal data for replotting
- `03_enhanced_plotting/signal_analysis_report.md` - Comprehensive analysis report
- JSON and CSV files for each signal category (input_ports, output_ports, all_ports, all_signals)

### Example 4: Categorization
- Demonstrates signal categorization results

## Key Features Demonstrated

### Core Capabilities
- **VCD to WaveJSON extraction** with intelligent signal processing
- **Automatic signal categorization** using naming patterns and hierarchy
- **Enhanced plotting** with golden reference styling and professional appearance
- **Professional waveform visualization** in PNG format
- **Signal intelligence** showing how signals are automatically classified

### Technical Features
- Intelligent clock signal detection and suggestions
- Hierarchical signal path handling
- Multi-bit signal support
- Verilog file integration for enhanced categorization
- Comprehensive analysis reporting

## Test Data

- `timer.vcd`: VCD dump from a simple timer circuit simulation
- `timer.v`: Verilog source code for the timer design (used for enhanced categorization)
- Various output files demonstrating the tool's capabilities

## Replotting from CSV

You can replot signals from saved CSV files for debugging or different visualizations:

```python
from vcd2image.core.signal_plotter import SignalPlotter

plotter = SignalPlotter('dummy.vcd')  # VCD not needed for replotting
plotter.replot_from_csv('path/to/signal_data.csv', 'new_plots')
```

This allows you to:
- Debug plotting issues by inspecting the raw data
- Create different visualizations from the same data
- Share data with others for independent plotting

## Implementation Notes

These examples reflect the actual capabilities implemented in the `src/vcd2image/` codebase:
- Focus on core functionality rather than exhaustive edge cases
- Demonstrate integration between components (extractor, categorizer, renderer, signal_plotter)
- Show both basic and enhanced (golden reference) workflows
- Include both data extraction, CSV export, and visualization capabilities
- Follow the VCD → WaveExtractor → JSON → CSV → Plots pipeline
