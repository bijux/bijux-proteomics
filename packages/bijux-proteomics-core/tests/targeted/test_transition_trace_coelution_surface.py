# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.targeted.transition_coelution import (
    TargetedTransitionTracePoint,
    render_transition_coelution_tsv,
    score_transition_coelution,
)


def test_score_transition_coelution_requires_two_passing_transitions_for_reliable_tier() -> (
    None
):
    rows = score_transition_coelution(
        (
            *_trace(
                "PEPTIDEK/2",
                "treat_r2",
                "y7",
                ((10.0, 10.0), (10.4, 60.0), (10.8, 10.0)),
            ),
            *_trace(
                "PEPTIDEK/2",
                "treat_r2",
                "y8",
                ((10.0, 12.0), (11.1, 55.0), (11.6, 12.0)),
            ),
        ),
        coelution_rt_delta_threshold_minutes=0.2,
    )
    rendered = render_transition_coelution_tsv(rows)
    row = rows[0]

    assert row.target_id == "PEPTIDEK/2"
    assert row.transition_count == 2
    assert row.passing_transition_count == 1
    assert row.apex_rt_spread == 0.7
    assert row.coelution_tier.value == "insufficient"
    assert (
        "target_id\tsample_id\ttransition_count\tpassing_transition_count\tapex_rt_spread\tcoelution_tier"
        in rendered
    )
    assert "PEPTIDEK/2\ttreat_r2\t2\t1\t0.7\tinsufficient" in rendered


def _trace(
    target_id: str,
    sample_id: str,
    transition_id: str,
    points: tuple[tuple[float, float], ...],
) -> tuple[TargetedTransitionTracePoint, ...]:
    return tuple(
        TargetedTransitionTracePoint(
            target_id=target_id,
            sample_id=sample_id,
            transition_id=transition_id,
            rt=rt,
            intensity=intensity,
        )
        for rt, intensity in points
    )
