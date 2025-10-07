# VCD2Image Examples

This directory contains core examples demonstrating the main features of the vcd2image tool.

## Overview

The `example.py` script showcases 4 core use cases that demonstrate the actual capabilities implemented in `src/vcd2image/`:

1. **Basic signal extraction (VCD to JSON)** - Extract signals and save as WaveJSON format
2. **Auto plotting with signal categorization** - Generate categorized figures with enhanced styling
3. **Enhanced plotting with golden references** - Professional plots with golden reference analysis
4. **Signal categorization intelligence** - Understand automatic signal classification

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
- `02_auto_plotting/plots/` - JSON files for each category (clocks.json, resets.json, inputs.json, outputs.json, internals.json)

### Example 3: Enhanced Plotting
- `03_enhanced_plotting/plots/` - Enhanced plots with golden references
- `03_enhanced_plotting/signal_analysis_report.md` - Comprehensive analysis report
- JSON files for each category

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

## Implementation Notes

These examples reflect the actual capabilities implemented in the `src/vcd2image/` codebase:
- Focus on core functionality rather than exhaustive edge cases
- Demonstrate integration between components (extractor, categorizer, renderer, signal_plotter)
- Show both basic and enhanced (golden reference) workflows
- Include both data extraction and visualization capabilities
