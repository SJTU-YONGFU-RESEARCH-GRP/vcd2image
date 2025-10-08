#!/usr/bin/env python
"""Core examples demonstrating vcd2image capabilities.

This file demonstrates the main features of the vcd2image tool based on
the actual implementation in src/vcd2image/:
- Basic signal extraction (VCD to JSON)
- Auto plotting with signal categorization
- Enhanced plotting with golden references
- JSON to image rendering
- Signal categorization intelligence
"""

from pathlib import Path

from vcd2image.core.extractor import WaveExtractor
from vcd2image.core.multi_renderer import MultiFigureRenderer


def example1():
    """Basic signal extraction (VCD to JSON)."""

    path_list = [
        "tb_timer/u_timer/clock",
        "tb_timer/u_timer/reset",
        "tb_timer/u_timer/pulse",
        "tb_timer/u_timer/count",
    ]

    vcd_file = Path(__file__).parent / "timer.vcd"
    output_dir = Path(__file__).parent / "01_basic_extraction"
    output_dir.mkdir(exist_ok=True)
    json_file = output_dir / "signals.json"

    extractor = WaveExtractor(str(vcd_file), str(json_file), path_list)
    extractor.execute()

    print(f"Created WaveJSON file: {json_file}")


def example2():
    """Auto plotting with signal categorization."""

    output_dir = Path(__file__).parent / "02_auto_plotting"
    output_dir.mkdir(exist_ok=True)

    vcd_file = Path(__file__).parent / "timer.vcd"

    renderer = MultiFigureRenderer()

    # Generate multiple categorized figures
    print("Generating multiple categorized figures...")
    renderer.render_categorized_figures(
        vcd_file=str(vcd_file),
        output_dir=str(output_dir),
        base_name="categorized",
        formats=["png", "svg"],
    )

    print(f"Generated categorized plotting results in: {output_dir}/")


def example3():
    """Enhanced plotting with golden references."""

    from vcd2image.core.multi_renderer import MultiFigureRenderer

    output_dir = Path(__file__).parent / "03_enhanced_plotting"
    output_dir.mkdir(exist_ok=True)

    vcd_file = Path(__file__).parent / "timer.vcd"
    verilog_file = Path(__file__).parent / "timer.v"

    renderer = MultiFigureRenderer()
    result = renderer.render_enhanced_plots_with_golden_references(
        vcd_file=str(vcd_file), verilog_file=str(verilog_file), output_dir=str(output_dir)
    )

    if result == 0:
        print("Generated enhanced plots with golden references:")
        print("  - input_ports.png")
        print("  - output_ports.png")
        print("  - all_ports.png")
        print("  - all_signals.png")
        print(f"Output directory: {output_dir}")


def example4():
    """Signal categorization intelligence."""

    from vcd2image.core.categorizer import SignalCategorizer
    from vcd2image.core.parser import VCDParser

    # Parse all signals
    vcd_file = Path(__file__).parent / "timer.vcd"
    parser = VCDParser(str(vcd_file))
    all_signals = parser.parse_signals()

    # Categorize signals
    categorizer = SignalCategorizer()
    category = categorizer.categorize_signals(all_signals)

    print("Signal Categorization Results:")
    print(f"Clock signals: {len(category.clock_signals)}")
    print(f"Input ports: {len(category.input_ports)}")
    print(f"Output ports: {len(category.output_ports)}")
    print(f"Reset signals: {len(category.resets)}")
    print(f"Internal signals: {len(category.internal_signals)}")
    print(f"Unknown signals: {len(category.unknowns)}")

    # Show suggested clock
    suggested_clock = categorizer.suggest_clock_signal(category)
    print(f"Suggested clock signal: {suggested_clock}")


if __name__ == "__main__":
    print("VCD2Image Core Examples")
    print("=" * 50)

    examples = [
        ("Basic signal extraction (VCD to JSON)", example1),
        ("Auto plotting with signal categorization", example2),
        ("Enhanced plotting with golden references", example3),
        ("Signal categorization intelligence", example4),
    ]

    for i, (description, example_func) in enumerate(examples, 1):
        print(f"\n{i}. {description}")
        print("-" * (len(description) + 3))
        try:
            example_func()
        except Exception as e:
            print(f"Error in example {i}: {e}")

    print(f"\n{'=' * 50}")
    print("All core examples completed!")
    print("\nGenerated files demonstrate the actual capabilities of vcd2image:")
    print("- WaveJSON extraction from VCD files")
    print("- Automatic signal categorization and plotting")
