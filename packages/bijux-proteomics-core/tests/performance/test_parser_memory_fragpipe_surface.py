# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from .parser_memory_benchmark_support import benchmark_fragpipe_import_memory


def test_generated_large_fragpipe_import_stays_below_memory_ceiling(
    tmp_path: Path,
) -> None:
    report = benchmark_fragpipe_import_memory(tmp_path)

    assert report.parser_id == "fragpipe_import"
    assert report.generated_unit_count == 4_000
    assert report.ceiling_respected is True
    assert report.memory_headroom_mb >= 0.0
