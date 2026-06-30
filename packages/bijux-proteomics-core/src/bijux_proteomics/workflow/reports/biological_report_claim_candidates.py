# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Biological claim candidate builders for governed report workflows."""

from __future__ import annotations

from bijux_proteomics.domain.semantic_ids import (
    build_pathway_claim_id,
    build_protein_claim_id,
    build_regulator_claim_id,
)
from bijux_proteomics.interpretation import (
    PathwayActivityReport,
    RegulatorInferenceReport,
)
from bijux_proteomics.quantification.contracts import DifferentialAbundanceReport
from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimCandidate,
    BiologicalClaimDirection,
    BiologicalClaimKind,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
)


def _build_biological_protein_claim_candidates(
    differential_report: DifferentialAbundanceReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
) -> tuple[BiologicalClaimCandidate, ...]:
    differential_by_entity = {
        entry.entity_id: entry for entry in differential_report.entries
    }
    candidates: list[BiologicalClaimCandidate] = []
    for card in protein_mechanism_cards.cards:
        if card.abundance_change.direction.value == "unchanged":
            continue
        differential_entry = differential_by_entity.get(card.protein_group_id)
        if differential_entry is None:
            raise ValueError(
                "biological claim validation requires one differential entry per protein mechanism card"
            )
        direction = (
            BiologicalClaimDirection.UP
            if card.abundance_change.direction.value == "increased"
            else BiologicalClaimDirection.DOWN
        )
        direction_label = (
            "increased" if direction is BiologicalClaimDirection.UP else "decreased"
        )
        candidates.append(
            BiologicalClaimCandidate(
                claim_id=build_protein_claim_id(card.protein_group_id),
                claim_kind=BiologicalClaimKind.PROTEIN_ABUNDANCE_CHANGE,
                subject_id=card.protein_group_id,
                subject_label=card.gene_symbol or card.representative_protein_ref,
                claim_text=(
                    f"Protein {card.gene_symbol or card.representative_protein_ref} "
                    f"{direction_label} in {card.abundance_change.condition_b} vs "
                    f"{card.abundance_change.condition_a}"
                ),
                condition_a=card.abundance_change.condition_a,
                condition_b=card.abundance_change.condition_b,
                asserted_direction=direction,
                significant=card.abundance_change.significant,
                adjusted_p_value=card.abundance_change.adjusted_p_value,
                effect_size=abs(card.abundance_change.log2_fold_change),
                robustness_score=differential_entry.robustness_score,
                imputation_dependent=differential_entry.imputation_dependent_hit,
                evidence_tier=card.evidence_tier,
                confidence_tier=card.confidence_tier,
                source_ids=(
                    card.card_id,
                    card.graph_claim_node_id,
                    card.protein_card_id,
                ),
                source_row_refs=card.source_row_refs,
                derived_no_source_reason=card.derived_no_source_reason,
                note=(
                    "protein abundance claims require robust quantitative support, "
                    "not just nominal differential direction"
                ),
            )
        )
    return tuple(candidates)


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
        noun = "Kinase" if entry.evidence_type.value == "kinase_substrate" else "Regulator"
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
