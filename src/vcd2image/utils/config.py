"""Configuration management for VCD to Image Converter."""

import argparse
import os
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration settings for the VCD to Image Converter."""

    # VCD processing settings
    wave_chunk: int = 20
    start_time: int = 0
    end_time: int = 0

    # WaveDrom rendering settings
    skin: str = "default"
    width: int | None = None
    height: int | None = None

    # Output settings
    output_format: str = "png"  # png, svg, pdf

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "Config":
        """Create configuration from command-line arguments.

        Args:
            args: Parsed command-line arguments.

        Returns:
            Configuration instance.
        """
        return cls(
            wave_chunk=getattr(args, "wave_chunk", 20),
            start_time=getattr(args, "start_time", 0),
            end_time=getattr(args, "end_time", 0),
        )

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables.

        Returns:
            Configuration instance.
        """
        return cls(
            wave_chunk=int(os.getenv("VCD2IMAGE_WAVE_CHUNK", "20")),
            start_time=int(os.getenv("VCD2IMAGE_START_TIME", "0")),
            end_time=int(os.getenv("VCD2IMAGE_END_TIME", "0")),
            skin=os.getenv("VCD2IMAGE_SKIN", "default"),
            output_format=os.getenv("VCD2IMAGE_FORMAT", "png"),
        )

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration.
        """
        return {
            "wave_chunk": self.wave_chunk,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "skin": self.skin,
            "width": self.width,
            "height": self.height,
            "output_format": self.output_format,
        }
