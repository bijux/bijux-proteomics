# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.judgment.benchmark_quality import (
    build_benchmark_decision_traps_report,
    build_benchmark_decision_wins_report,
)


def test_trap_and_win_reports_stay_honest() -> None:
    traps = build_benchmark_decision_traps_report()
    wins = build_benchmark_decision_wins_report()

    assert traps.entries
    assert traps.entries[0].scenario_id == "refuse-thin-targeted-and-ptm-promotion"
    assert wins.entries
    assert any(
        entry.scenario_id == "safer-reviewable-path-over-flashy-thin-ptm"
        for entry in wins.entries
    )
