# Test Data Directory

This directory contains test data files used by the VCD2Image test suite.

## Files

- `counter.v` - Verilog source code for a simple counter module
- `timer.vcd` - VCD (Value Change Dump) file containing simulation results for a timer module

## Purpose

These files provide realistic test data for unit and integration tests, ensuring:

- Tests use actual VCD parsing and signal processing logic
- Test stability (not affected by changes to example files)
- Realistic test scenarios with real signal data
- End-to-end validation of the VCD2Image pipeline

## Usage

The `timer_vcd_file` fixture in `conftest.py` provides access to `timer.vcd` for tests that need real VCD data.

## Signals in timer.vcd

The timer.vcd file contains the following signals:
- `tb_timer/pulse` (1-bit wire)
- `tb_timer/clock` (1-bit reg)
- `tb_timer/reset` (1-bit reg)
- `tb_timer/u_timer/clock` (1-bit wire)
- `tb_timer/u_timer/reset` (1-bit wire)
- `tb_timer/u_timer/count_eq11` (1-bit wire)
- `tb_timer/u_timer/count` (4-bit reg)
- `tb_timer/u_timer/pulse` (1-bit reg)
