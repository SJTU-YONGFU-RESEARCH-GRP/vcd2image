"""Verilog Parser for VAS Framework.

This module provides functionality to parse Verilog files and extract
module information including inputs, outputs, wires, and registers.
"""

import re
from typing import Dict, List, Tuple, Optional, Set
from pathlib import Path
from dataclasses import dataclass


@dataclass
class VerilogModule:
    """Data class to hold Verilog module information."""
    name: str
    inputs: Dict[str, Tuple[int, str]]  # signal_name -> (width, description)
    outputs: Dict[str, Tuple[int, str]]
    wires: Dict[str, Tuple[int, str]]
    regs: Dict[str, Tuple[int, str]]
    parameters: Dict[str, str]


class VerilogParser:
    """Parses Verilog files to extract module and signal information."""

    def __init__(self, verilog_file: str):
        """
        Initialize the VerilogParser.

        Args:
            verilog_file: Path to the Verilog file to parse
        """
        self.verilog_file = Path(verilog_file)
        self.content: str = ""
        self.module_name: Optional[str] = None
        self.module: Optional[VerilogModule] = None

        # Direct access to parsed data for compatibility
        self.inputs: Dict[str, Tuple[int, str]] = {}
        self.outputs: Dict[str, Tuple[int, str]] = {}
        self.wires: Dict[str, Tuple[int, str]] = {}
        self.regs: Dict[str, Tuple[int, str]] = {}
        self.parameters: Dict[str, str] = {}

    def parse(self) -> bool:
        """
        Parse the Verilog file and extract module information.

        Returns:
            True if parsing successful, False otherwise
        """
        try:
            if not self.verilog_file.exists():
                return False

            with open(self.verilog_file, 'r') as f:
                self.content = f.read()

            return self._parse_module()

        except Exception:
            return False

    def _parse_module(self) -> bool:
        """Parse module definition and extract signal information."""
        # Find module declaration
        module_pattern = r'module\s+(\w+)\s*(?:\([^)]*\))?\s*;'
        match = re.search(module_pattern, self.content, re.IGNORECASE)

        if not match:
            return False

        self.module_name = match.group(1)

        # Extract parameters, inputs, outputs, wires, regs
        self.inputs = self._parse_inputs()
        self.outputs = self._parse_outputs()
        self.wires = self._parse_wires()
        self.regs = self._parse_regs()
        self.parameters = self._parse_parameters()

        self.module = VerilogModule(
            name=self.module_name,
            inputs=self.inputs,
            outputs=self.outputs,
            wires=self.wires,
            regs=self.regs,
            parameters=self.parameters
        )

        return True

    def _parse_inputs(self) -> Dict[str, Tuple[int, str]]:
        """Parse input port declarations."""
        inputs = {}

        # Find input declarations within the module
        input_pattern = r'input\s+(?:wire\s+)?(?:\[(\d+):(\d+)\]\s+)?(\w+);'
        matches = re.findall(input_pattern, self.content, re.IGNORECASE)

        for match in matches:
            if len(match) == 3:
                width_str, _, signal_name = match
                if width_str:
                    width = int(width_str) + 1  # Convert [MSB:LSB] to width
                else:
                    width = 1
                inputs[signal_name] = (width, "Input port")
            elif len(match) == 1:
                signal_name = match[0]
                inputs[signal_name] = (1, "Input port")

        return inputs

    def _parse_outputs(self) -> Dict[str, Tuple[int, str]]:
        """Parse output port declarations."""
        outputs = {}

        # Find output declarations within the module
        output_pattern = r'output\s+(?:wire\s+|reg\s+)?(?:\[(\d+):(\d+)\]\s+)?(\w+);'
        matches = re.findall(output_pattern, self.content, re.IGNORECASE)

        for match in matches:
            if len(match) == 3:
                width_str, _, signal_name = match
                if width_str:
                    width = int(width_str) + 1  # Convert [MSB:LSB] to width
                else:
                    width = 1
                outputs[signal_name] = (width, "Output port")
            elif len(match) == 1:
                signal_name = match[0]
                outputs[signal_name] = (1, "Output port")

        return outputs

    def _parse_wires(self) -> Dict[str, Tuple[int, str]]:
        """Parse wire declarations."""
        wires = {}

        # Find wire declarations within the module
        wire_pattern = r'wire\s+(?:\[(\d+):(\d+)\]\s+)?(\w+);'
        matches = re.findall(wire_pattern, self.content, re.IGNORECASE)

        for match in matches:
            if len(match) == 3:
                width_str, _, signal_name = match
                if width_str:
                    width = int(width_str) + 1  # Convert [MSB:LSB] to width
                else:
                    width = 1
                wires[signal_name] = (width, "Wire")
            elif len(match) == 1:
                signal_name = match[0]
                wires[signal_name] = (1, "Wire")

        return wires

    def _parse_regs(self) -> Dict[str, Tuple[int, str]]:
        """Parse register declarations."""
        regs = {}

        # Find reg declarations within the module
        reg_pattern = r'reg\s+(?:\[(\d+):(\d+)\]\s+)?(\w+);'
        matches = re.findall(reg_pattern, self.content, re.IGNORECASE)

        for match in matches:
            if len(match) == 3:
                width_str, _, signal_name = match
                if width_str:
                    width = int(width_str) + 1  # Convert [MSB:LSB] to width
                else:
                    width = 1
                regs[signal_name] = (width, "Register")
            elif len(match) == 1:
                signal_name = match[0]
                regs[signal_name] = (1, "Register")

        return regs

    def _parse_parameters(self) -> Dict[str, str]:
        """Parse parameter declarations."""
        parameters = {}

        # Find parameter declarations within the module
        param_pattern = r'parameter\s+(\w+)\s*=\s*([^;]+);'
        matches = re.findall(param_pattern, self.content, re.IGNORECASE)

        for match in matches:
            param_name, param_value = match
            parameters[param_name] = param_value.strip()

        return parameters

    def get_signal_info(self, signal_name: str) -> Optional[Tuple[int, str]]:
        """Get information about a specific signal."""
        if not self.module:
            return None

        # Check all signal dictionaries
        all_signals = {**self.module.inputs, **self.module.outputs,
                      **self.module.wires, **self.module.regs}

        return all_signals.get(signal_name)

    def get_all_signals(self) -> Set[str]:
        """Get all signal names from the module."""
        if not self.module:
            return set()

        all_signals = {**self.module.inputs, **self.module.outputs,
                      **self.module.wires, **self.module.regs}

        return set(all_signals.keys())
