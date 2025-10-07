"""Test configuration and fixtures."""

import subprocess
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def real_vcd_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Generate a real VCD file using iverilog simulation.

    This fixture compiles and runs a Verilog testbench to create an actual
    VCD file instead of using mock data.

    Returns:
        Path to the generated VCD file.
    """
    # Use the existing timer testbench
    verilog_file = Path(__file__).parent.parent / "examples" / "timer.v"

    if not verilog_file.exists():
        pytest.skip("Verilog test file not found")

    # Create a temporary directory for simulation
    sim_dir = tmp_path / "simulation"
    sim_dir.mkdir()

    vcd_file = sim_dir / "timer.vcd"

    try:
        # Compile the Verilog file
        compile_result = subprocess.run(
            ["iverilog", "-o", str(sim_dir / "timer_tb"), str(verilog_file)],
            capture_output=True,
            text=True,
            cwd=sim_dir,
            timeout=30
        )

        if compile_result.returncode != 0:
            pytest.skip(f"iverilog compilation failed: {compile_result.stderr}")

        # Run the simulation
        run_result = subprocess.run(
            ["vvp", str(sim_dir / "timer_tb")],
            capture_output=True,
            text=True,
            cwd=sim_dir,
            timeout=30
        )

        if run_result.returncode != 0:
            pytest.skip(f"Simulation failed: {run_result.stderr}")

        # Check if VCD file was created
        if not vcd_file.exists():
            pytest.skip("VCD file was not generated")

        yield vcd_file

    except subprocess.TimeoutExpired:
        pytest.skip("Simulation timed out")
    except FileNotFoundError:
        pytest.skip("iverilog or vvp not found")
