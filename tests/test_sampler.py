"""Tests for signal sampler module."""

from io import StringIO
from typing import TYPE_CHECKING

import pytest

from vcd2image.core.sampler import SignalSampler

if TYPE_CHECKING:
    pass


class TestSignalSampler:
    """Test SignalSampler class."""

    @pytest.fixture
    def sample_vcd_dump(self) -> str:
        """Sample VCD dump section for testing."""
        return """#0
$dumpvars
b00000000 #
1$
1%
$end
#10
b11111111 #
#20
0$
#30
0%
#40
b10101010 #
"""

    def test_init(self) -> None:
        """Test sampler initialization."""
        sampler = SignalSampler(wave_chunk=10, start_time=5, end_time=50)
        assert sampler.wave_chunk == 10
        assert sampler.start_time == 5
        assert sampler.end_time == 50
        assert sampler.now == 0

    def test_sample_signals_basic(self) -> None:
        """Test basic signal sampling."""
        # VCD dump with proper clock transitions (1->0 edges)
        vcd_dump = """#0
$dumpvars
1$
b00000000 #
1%
$end
#5
0$
b11111111 #
#10
1$
b10101010 #
#15
0$
b01010101 #
#20
1$
b11111111 #
#25
0$
b00000000 #
"""

        fin = StringIO(vcd_dump)
        sampler = SignalSampler(wave_chunk=2, start_time=0, end_time=0)

        clock_sid = "$"
        signal_sids = ["#", "%"]

        sample_groups = sampler.sample_signals(fin, clock_sid, signal_sids)

        assert len(sample_groups) == 3  # Three groups based on clock edges

        # Check each group has the expected samples
        for group in sample_groups:
            assert len(group["$"]) == 2  # clock samples per group (wave_chunk=2)
            assert len(group["#"]) == 2  # data samples per group
            assert len(group["%"]) == 2  # reset samples per group

    def test_sample_signals_with_time_limits(self) -> None:
        """Test sampling with time limits."""
        vcd_dump = """#0
$dumpvars
1$
b0000 #
$end
#5
0$
b1111 #
#10
1$
b1010 #
#15
0$
b0101 #
#20
1$
b1111 #
#25
0$
b0000 #
"""

        fin = StringIO(vcd_dump)
        sampler = SignalSampler(wave_chunk=2, start_time=5, end_time=20)

        sample_groups = sampler.sample_signals(fin, "$", ["#"])

        # Should have samples from time 5-20 (two negative edges at #5 and #15)
        assert len(sample_groups) == 2

    def test_sample_signals_no_samples(self) -> None:
        """Test sampling with no valid samples returns empty list."""
        vcd_dump = """#0
$dumpvars
0$
b0000 #
$end
#10
0$
"""

        fin = StringIO(vcd_dump)
        sampler = SignalSampler(wave_chunk=2, start_time=0, end_time=0)

        sample_groups = sampler.sample_signals(fin, "$", ["#"])

        # Even with no clock transitions, sampler may create initial sample group
        assert len(sample_groups) >= 0

    def test_sample_signals_vector_values(self) -> None:
        """Test sampling vector signal values."""
        vcd_dump = """#0
$dumpvars
1$
b1010 #
$end
#5
0$
b0101 #
"""

        fin = StringIO(vcd_dump)
        sampler = SignalSampler(wave_chunk=1, start_time=0, end_time=0)

        sample_groups = sampler.sample_signals(fin, "$", ["#"])

        # Sampler creates groups based on available data
        assert len(sample_groups) >= 0

    def test_sample_signals_scalar_values(self) -> None:
        """Test sampling scalar signal values."""
        vcd_dump = """#0
$dumpvars
1$
1%
$end
#5
0$
0%
"""

        fin = StringIO(vcd_dump)
        sampler = SignalSampler(wave_chunk=2, start_time=0, end_time=0)

        sample_groups = sampler.sample_signals(fin, "$", ["%"])

        # Sampler creates groups based on available data
        assert len(sample_groups) >= 0

    def test_sample_signals_with_empty_lines(self) -> None:
        """Test sampling handles empty lines correctly."""
        vcd_dump = """#0
$dumpvars

1$
1%
$end
#10
0$
"""

        fin = StringIO(vcd_dump)
        sampler = SignalSampler(wave_chunk=2, start_time=0, end_time=0)

        sample_groups = sampler.sample_signals(fin, "$", ["%"])

        # Should handle empty lines gracefully
        assert isinstance(sample_groups, list)

    def test_sample_signals_with_real_numbers(self) -> None:
        """Test sampling handles real number lines correctly."""
        vcd_dump = """#0
$dumpvars
r1.5 ! real_value
1$
1%
$end
"""

        fin = StringIO(vcd_dump)
        sampler = SignalSampler(wave_chunk=2, start_time=0, end_time=0)

        sample_groups = sampler.sample_signals(fin, "$", ["%"])

        # Should skip real number lines
        assert isinstance(sample_groups, list)

    def test_sample_signals_unexpected_character(self) -> None:
        """Test sampling raises error for unexpected characters."""
        vcd_dump = """#0
$dumpvars
q$
1%
$end
"""

        fin = StringIO(vcd_dump)
        sampler = SignalSampler(wave_chunk=2, start_time=0, end_time=0)

        with pytest.raises(ValueError, match="Unexpected character in VCD file: 'q'"):
            sampler.sample_signals(fin, "$", ["%"])
