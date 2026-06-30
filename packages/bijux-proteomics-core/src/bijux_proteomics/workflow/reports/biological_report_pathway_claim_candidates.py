# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Pathway claim candidate builders for governed biological reports."""

from __future__ import annotations

from bijux_proteomics.domain.semantic_ids import build_pathway_claim_id
from bijux_proteomics.interpretation import PathwayActivityReport
from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimCandidate,
    BiologicalClaimDirection,
    BiologicalClaimKind,
)


def _build_biological_pathway_claim_candidates(
    pathway_activity_report: PathwayActivityReport | None,
) -> tuple[BiologicalClaimCandidate, ...]:
    if pathway_activity_report is None:
        return ()
    candidates: list[BiologicalClaimCandidate] = []
    for entry in pathway_activity_report.condition_comparisons:
        if entry.activity_score_delta is None or entry.activity_score_delta == 0.0:
            continue
        direction = (
            BiologicalClaimDirection.UP
            if entry.activity_score_delta > 0.0
            else BiologicalClaimDirection.DOWN
        )
        verb = "activated" if direction is BiologicalClaimDirection.UP else "suppressed"
        candidates.append(
            BiologicalClaimCandidate(
                claim_id=build_pathway_claim_id(
                    entry.pathway_id,
                    entry.condition_a,
                    entry.condition_b,
                ),
                claim_kind=BiologicalClaimKind.PATHWAY_ACTIVITY_CHANGE,
                subject_id=entry.pathway_id,
                subject_label=entry.pathway_name or entry.pathway_id,
                claim_text=(
                    f"Pathway {entry.pathway_name or entry.pathway_id} {verb} in "
                    f"{entry.condition_b} vs {entry.condition_a}"
                ),
                condition_a=entry.condition_a,
                condition_b=entry.condition_b,
                asserted_direction=direction,
                effect_size=abs(entry.activity_score_delta),
                pathway_confidence_status=entry.comparison_confidence_status.value,
                pathway_delta=entry.activity_score_delta,
                source_ids=(
                    f"pathway-activity:{entry.pathway_id}",
                    f"pathway-activity-comparison:{entry.pathway_id}:{entry.condition_a}:{entry.condition_b}",
                ),
                derived_no_source_reason=(
                    "pathway activity claims aggregate governed pathway activity comparisons rather than preserving one direct input row"
                ),
                note=(
                    "pathway activation claims require explicit directional activity "
                    "deltas with high-confidence comparison support"
                ),
            )
        )
    return tuple(candidates)
