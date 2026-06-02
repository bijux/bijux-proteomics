# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from .parser_memory_benchmark_support import (
    benchmark_mgf_streaming_memory,
    benchmark_mzml_streaming_memory,
)


def test_generated_large_mgf_streaming_stays_below_memory_ceiling(tmp_path) -> None:
    report = benchmark_mgf_streaming_memory(tmp_path)

    assert report.parser_id == "mgf_streaming"
    assert report.generated_unit_count == 8_000
    assert report.ceiling_respected is True
    assert report.memory_headroom_mb >= 0.0


@pytest.mark.slow
def test_generated_large_mzml_streaming_stays_below_memory_ceiling(tmp_path) -> None:
    report = benchmark_mzml_streaming_memory(tmp_path)

    assert report.parser_id == "mzml_streaming"
    assert report.generated_unit_count == 3_000
    assert report.ceiling_respected is True
    assert report.memory_headroom_mb >= 0.0
