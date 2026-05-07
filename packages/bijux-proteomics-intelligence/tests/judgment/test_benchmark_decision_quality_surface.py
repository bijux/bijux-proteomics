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
    assert traps.entries[0].scenario_id == "borderline-dia-burden-still-confuses-current-policy"
    assert wins.entries
    assert any(
        entry.scenario_id == "refuse-thin-targeted-and-ptm-promotion"
        for entry in wins.entries
    )
