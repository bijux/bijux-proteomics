# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.runtime.control.workflow_runs import (
    FakeExternalToolKind,
    build_fake_external_engine_harness,
)


def test_build_fake_external_engine_harness_is_deterministic() -> None:
    first = build_fake_external_engine_harness(
        run_id="run-01",
        tool_kinds=(
            FakeExternalToolKind.SEARCH,
            FakeExternalToolKind.QUANT,
            FakeExternalToolKind.QC,
        ),
        seed=23,
    )
    second = build_fake_external_engine_harness(
        run_id="run-01",
        tool_kinds=(
            FakeExternalToolKind.SEARCH,
            FakeExternalToolKind.QUANT,
            FakeExternalToolKind.QC,
        ),
        seed=23,
    )

    assert first.deterministic is True
    assert first.replay_cache_key == second.replay_cache_key
    assert len(first.entries) == 3
    assert all(entry.exit_code == 0 for entry in first.entries)
    assert first.entries[0].tool_kind.value == "search"
