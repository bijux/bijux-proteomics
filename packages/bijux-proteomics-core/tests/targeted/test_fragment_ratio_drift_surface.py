# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.targeted.fragment_ratios import (
    TargetedFragmentRatioMatrixEntry,
    render_fragment_ratio_drift_tsv,
    score_fragment_ratio_drift,
)


def test_score_fragment_ratio_drift_flags_unstable_transition_ratios() -> None:
    rows = score_fragment_ratio_drift(
        (
            TargetedFragmentRatioMatrixEntry(
                target_id="PEPTIDEK/2",
                sample_id="control_r1",
                transition_id="y7",
                intensity=80000.0,
            ),
            TargetedFragmentRatioMatrixEntry(
                target_id="PEPTIDEK/2",
                sample_id="control_r1",
                transition_id="y8",
                intensity=20000.0,
            ),
            TargetedFragmentRatioMatrixEntry(
                target_id="PEPTIDEK/2",
                sample_id="control_r2",
                transition_id="y7",
                intensity=82000.0,
            ),
            TargetedFragmentRatioMatrixEntry(
                target_id="PEPTIDEK/2",
                sample_id="control_r2",
                transition_id="y8",
                intensity=18000.0,
            ),
            TargetedFragmentRatioMatrixEntry(
                target_id="PEPTIDEK/2",
                sample_id="treat_r1",
                transition_id="y7",
                intensity=95000.0,
            ),
            TargetedFragmentRatioMatrixEntry(
                target_id="PEPTIDEK/2",
                sample_id="treat_r1",
                transition_id="y8",
                intensity=5000.0,
            ),
        )
    )
    rendered = render_fragment_ratio_drift_tsv(rows)

    stable_row = next(
        row
        for row in rows
        if row.target_id == "PEPTIDEK/2" and row.transition_id == "y7"
    )
    drifted_row = next(
        row
        for row in rows
        if row.target_id == "PEPTIDEK/2" and row.transition_id == "y8"
    )

    assert round(stable_row.expected_ratio, 6) == 0.82
    assert round(stable_row.observed_ratio_cv or 0.0, 6) == 0.095072
    assert stable_row.drift_flag is False
    assert round(drifted_row.expected_ratio, 6) == 0.18
    assert round(drifted_row.observed_ratio_cv or 0.0, 6) == 0.568223
    assert drifted_row.drift_flag is True
    assert (
        "target_id\ttransition_id\texpected_ratio\tobserved_ratio_cv\tdrift_flag"
        in rendered
    )
    assert "PEPTIDEK/2\ty8\t0.180000\t0.568223\ttrue" in rendered
