# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Regulator biological hypothesis candidate builders."""

from __future__ import annotations

from bijux_proteomics.domain.semantic_ids import build_regulator_claim_id
from bijux_proteomics.interpretation import RegulatorInferenceReport
from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimKind,
    BiologicalClaimValidationReport,
)
from bijux_proteomics.review.claims.biological_hypotheses import (
    BiologicalHypothesisCandidate,
    BiologicalHypothesisKind,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCard,
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_hypothesis_evidence import (
    _graph_node_ids_from_cards,
    _regulator_hypothesis_opposing_evidence,
)
from bijux_proteomics.workflow.reports.biological_report_hypothesis_scoring import (
    _regulator_hypothesis_base_confidence,
)


def _build_biological_regulator_hypothesis_candidates(
    claim_validation_report: BiologicalClaimValidationReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    regulator_inference_report: RegulatorInferenceReport | None,
) -> tuple[BiologicalHypothesisCandidate, ...]:
    if regulator_inference_report is None:
        return ()
    cards_by_ref: dict[str, ProteinMechanismCard] = {
        card.representative_protein_ref: card for card in protein_mechanism_cards.cards
    }
    entries_by_claim_id = {
        build_regulator_claim_id(
            entry.regulator,
            entry.evidence_type.value,
            entry.signal_surface.value,
        ): entry
        for entry in regulator_inference_report.entries
    }
    candidates: list[BiologicalHypothesisCandidate] = []
    for claim in claim_validation_report.supported_claims:
        if claim.claim_kind is not BiologicalClaimKind.REGULATOR_ACTIVITY:
            continue
        regulator_entry = entries_by_claim_id.get(claim.claim_id)
        supporting_protein_refs = (
            ()
            if regulator_entry is None
            else tuple(
                protein_ref
                for protein_ref in regulator_entry.supporting_protein_refs
                if protein_ref in cards_by_ref
            )
        )
        supporting_cards = tuple(
            cards_by_ref[protein_ref]
            for protein_ref in supporting_protein_refs
            if protein_ref in cards_by_ref
        )
        candidates.append(
            BiologicalHypothesisCandidate(
                hypothesis_id=f"regulator-hypothesis:{claim.subject_id}",
                hypothesis_kind=BiologicalHypothesisKind.REGULATOR_ACTIVITY,
                subject_id=claim.subject_id,
                subject_label=claim.subject_label,
                claim=claim.claim_text,
                supporting_protein_refs=supporting_protein_refs,
                supporting_site_keys=(
                    ()
                    if regulator_entry is None
                    else regulator_entry.supporting_site_keys
                ),
                supporting_pathway_ids=(
                    ()
                    if regulator_entry is None
                    else regulator_entry.supporting_pathway_ids
                ),
                opposing_evidence=(
                    _regulator_hypothesis_opposing_evidence(
                        regulator_inference_report,
                        regulator=claim.subject_id,
                    )
                    if regulator_entry is not None
                    else ()
                ),
                evidence_node_ids=_graph_node_ids_from_cards(supporting_cards),
                base_confidence_score=_regulator_hypothesis_base_confidence(
                    claim,
                    regulator_score=(
                        None if regulator_entry is None else regulator_entry.score
                    ),
                ),
                source_ids=claim.source_ids
                + tuple(card.card_id for card in supporting_cards),
                note=(
                    "regulator hypotheses preserve the explicit downstream signal "
                    "surface and anchor onto graph-backed supporting protein evidence"
                ),
            )
        )
    return tuple(candidates)


__all__ = ["_build_biological_regulator_hypothesis_candidates"]
