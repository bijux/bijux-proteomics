# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Regulator claim candidate builders for governed biological reports."""

from __future__ import annotations

from bijux_proteomics.domain.semantic_ids import build_regulator_claim_id
from bijux_proteomics.interpretation import RegulatorInferenceReport
from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimCandidate,
    BiologicalClaimDirection,
    BiologicalClaimKind,
)


def _build_biological_regulator_claim_candidates(
    regulator_inference_report: RegulatorInferenceReport | None,
) -> tuple[BiologicalClaimCandidate, ...]:
    if regulator_inference_report is None:
        return ()
    candidates: list[BiologicalClaimCandidate] = []
    for entry in regulator_inference_report.entries:
        direction = {
            "up": BiologicalClaimDirection.UP,
            "down": BiologicalClaimDirection.DOWN,
            "mixed": BiologicalClaimDirection.MIXED,
            "unsupported": BiologicalClaimDirection.UNRESOLVED,
        }[entry.direction.value]
        noun = (
            "Kinase" if entry.evidence_type.value == "kinase_substrate" else "Regulator"
        )
        verb = (
            "active"
            if direction is BiologicalClaimDirection.UP
            else (
                "suppressed"
                if direction is BiologicalClaimDirection.DOWN
                else "unresolved"
            )
        )
        candidates.append(
            BiologicalClaimCandidate(
                claim_id=build_regulator_claim_id(
                    entry.regulator,
                    entry.evidence_type.value,
                    entry.signal_surface.value,
                ),
                claim_kind=BiologicalClaimKind.REGULATOR_ACTIVITY,
                subject_id=entry.regulator,
                subject_label=entry.regulator,
                claim_text=(
                    f"{noun} {entry.regulator} {verb} in "
                    f"{regulator_inference_report.condition_b} vs "
                    f"{regulator_inference_report.condition_a}"
                ),
                condition_a=regulator_inference_report.condition_a,
                condition_b=regulator_inference_report.condition_b,
                asserted_direction=direction,
                effect_size=abs(
                    entry.mean_log2_fold_change
                    if entry.mean_log2_fold_change is not None
                    else (entry.mean_activity_score_delta or 0.0)
                ),
                regulator_evidence_type=entry.evidence_type.value,
                regulator_signal_surface=entry.signal_surface.value,
                regulator_score=entry.score,
                source_ids=(
                    f"regulator-inference:{entry.regulator}",
                    f"regulator-surface:{entry.signal_surface.value}",
                ),
                derived_no_source_reason=(
                    "regulator activity claims aggregate governed upstream-target evidence and downstream signal surfaces rather than preserving one direct input row"
                ),
                note=(
                    "regulator claims require directional downstream support on the "
                    "appropriate evidence surface"
                ),
            )
        )
    return tuple(candidates)
