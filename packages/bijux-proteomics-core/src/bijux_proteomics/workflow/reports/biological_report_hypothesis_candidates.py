# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Biological hypothesis candidate builders for governed report workflows."""

from __future__ import annotations

from bijux_proteomics.domain.semantic_ids import build_regulator_claim_id
from bijux_proteomics.interpretation import (
    PathwayActivityReport,
    RegulatorInferenceReport,
)
from bijux_proteomics.interpretation.pathway_activity import (
    PathwayConditionComparisonEntry,
)
from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimCandidate,
    BiologicalClaimKind,
    BiologicalClaimValidationReport,
)
from bijux_proteomics.review.claims.biological_hypotheses import (
    BiologicalHypothesisCandidate,
    BiologicalHypothesisKind,
)
from bijux_proteomics.review.evidence_graph.evidence_graph_downgrades import (
    FinalClaimEvidenceTier,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCard,
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_hypothesis_evidence import (
    _graph_node_ids_from_cards as _hypothesis_graph_node_ids_from_cards,
    _pathway_hypothesis_opposing_evidence as _build_pathway_hypothesis_opposing_evidence,
    _pathway_hypothesis_supporting_protein_refs as _build_pathway_hypothesis_supporting_protein_refs,
    _protein_hypothesis_opposing_evidence as _build_protein_hypothesis_opposing_evidence,
    _regulator_hypothesis_opposing_evidence as _build_regulator_hypothesis_opposing_evidence,
)
from bijux_proteomics.workflow.reports.biological_report_hypothesis_scoring import (
    _confidence_tier_score as _hypothesis_confidence_tier_score,
    _evidence_tier_score as _hypothesis_evidence_tier_score,
    _pathway_confidence_score as _hypothesis_pathway_confidence_score,
    _pathway_hypothesis_base_confidence as _build_pathway_hypothesis_confidence,
    _protein_hypothesis_base_confidence as _build_protein_hypothesis_confidence,
    _regulator_hypothesis_base_confidence as _build_regulator_hypothesis_confidence,
)


def _build_biological_protein_hypothesis_candidates(
    claim_validation_report: BiologicalClaimValidationReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
) -> tuple[BiologicalHypothesisCandidate, ...]:
    cards_by_group_id = {
        card.protein_group_id: card for card in protein_mechanism_cards.cards
    }
    candidates: list[BiologicalHypothesisCandidate] = []
    for claim in claim_validation_report.supported_claims:
        if claim.claim_kind is not BiologicalClaimKind.PROTEIN_ABUNDANCE_CHANGE:
            continue
        card = cards_by_group_id.get(claim.subject_id)
        supporting_site_keys = (
            tuple(ptm.site_key for ptm in card.ptms) if card is not None else ()
        )
        supporting_pathway_ids = (
            tuple(pathway.entry_id for pathway in card.pathways)
            if card is not None
            else ()
        )
        candidates.append(
            BiologicalHypothesisCandidate(
                hypothesis_id=f"protein-hypothesis:{claim.subject_id}",
                hypothesis_kind=BiologicalHypothesisKind.PROTEIN_MECHANISM,
                subject_id=claim.subject_id,
                subject_label=claim.subject_label,
                claim=claim.claim_text,
                supporting_protein_refs=(
                    (card.representative_protein_ref,) if card is not None else ()
                ),
                supporting_site_keys=supporting_site_keys,
                supporting_pathway_ids=supporting_pathway_ids,
                opposing_evidence=(
                    _protein_hypothesis_opposing_evidence(card)
                    if card is not None
                    else ()
                ),
                evidence_node_ids=_graph_node_ids_from_cards(
                    () if card is None else (card,)
                ),
                base_confidence_score=_protein_hypothesis_base_confidence(
                    claim, card=card
                ),
                source_ids=claim.source_ids
                + (() if card is None else (card.card_id, card.protein_card_id)),
                note=(
                    "validated protein claims become biological hypotheses only when a "
                    "graph-backed protein mechanism card preserves the supporting claim "
                    "and subject node ids"
                ),
            )
        )
    return tuple(candidates)


def _build_biological_pathway_hypothesis_candidates(
    claim_validation_report: BiologicalClaimValidationReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    pathway_activity_report: PathwayActivityReport | None,
) -> tuple[BiologicalHypothesisCandidate, ...]:
    if pathway_activity_report is None:
        return ()
    cards_by_ref = {
        card.representative_protein_ref: card for card in protein_mechanism_cards.cards
    }
    comparisons = {
        (entry.pathway_id, entry.condition_a, entry.condition_b): entry
        for entry in pathway_activity_report.condition_comparisons
    }
    candidates: list[BiologicalHypothesisCandidate] = []
    for claim in claim_validation_report.supported_claims:
        if claim.claim_kind is not BiologicalClaimKind.PATHWAY_ACTIVITY_CHANGE:
            continue
        comparison = comparisons.get(
            (claim.subject_id, claim.condition_a, claim.condition_b)
        )
        supporting_protein_refs = (
            ()
            if comparison is None
            else _pathway_hypothesis_supporting_protein_refs(
                pathway_activity_report,
                pathway_id=comparison.pathway_id,
                condition_a=comparison.condition_a,
                condition_b=comparison.condition_b,
                cards_by_ref=cards_by_ref,
            )
        )
        supporting_cards = tuple(
            cards_by_ref[protein_ref]
            for protein_ref in supporting_protein_refs
            if protein_ref in cards_by_ref
        )
        candidates.append(
            BiologicalHypothesisCandidate(
                hypothesis_id=(
                    "pathway-hypothesis:"
                    f"{claim.subject_id}:{claim.condition_a}:{claim.condition_b}"
                ),
                hypothesis_kind=BiologicalHypothesisKind.PATHWAY_ACTIVITY,
                subject_id=claim.subject_id,
                subject_label=claim.subject_label,
                claim=claim.claim_text,
                supporting_protein_refs=supporting_protein_refs,
                supporting_pathway_ids=(claim.subject_id,),
                opposing_evidence=(
                    _pathway_hypothesis_opposing_evidence(
                        pathway_activity_report,
                        comparison=comparison,
                    )
                    if comparison is not None
                    else ()
                ),
                evidence_node_ids=_graph_node_ids_from_cards(supporting_cards),
                base_confidence_score=_pathway_hypothesis_base_confidence(
                    claim,
                    comparison=comparison,
                ),
                source_ids=claim.source_ids
                + tuple(card.card_id for card in supporting_cards),
                note=(
                    "pathway hypotheses inherit directional activity support from the "
                    "owned pathway activity report and anchor onto graph-backed member "
                    "protein evidence nodes"
                ),
            )
        )
    return tuple(candidates)


def _build_biological_regulator_hypothesis_candidates(
    claim_validation_report: BiologicalClaimValidationReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    regulator_inference_report: RegulatorInferenceReport | None,
) -> tuple[BiologicalHypothesisCandidate, ...]:
    if regulator_inference_report is None:
        return ()
    cards_by_ref = {
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


def _graph_node_ids_from_cards(
    cards: tuple[ProteinMechanismCard, ...],
) -> tuple[str, ...]:
    return _hypothesis_graph_node_ids_from_cards(cards)


def _protein_hypothesis_base_confidence(
    claim: BiologicalClaimCandidate,
    *,
    card: ProteinMechanismCard | None,
) -> float:
    return _build_protein_hypothesis_confidence(claim, card=card)


def _pathway_hypothesis_base_confidence(
    claim: BiologicalClaimCandidate,
    *,
    comparison: PathwayConditionComparisonEntry | None,
) -> float:
    return _build_pathway_hypothesis_confidence(claim, comparison=comparison)


def _regulator_hypothesis_base_confidence(
    claim: BiologicalClaimCandidate,
    *,
    regulator_score: float | None,
) -> float:
    return _build_regulator_hypothesis_confidence(
        claim,
        regulator_score=regulator_score,
    )


def _evidence_tier_score(evidence_tier: FinalClaimEvidenceTier | None) -> float:
    return _hypothesis_evidence_tier_score(evidence_tier)


def _confidence_tier_score(confidence_tier: str | None) -> float:
    return _hypothesis_confidence_tier_score(confidence_tier)


def _pathway_confidence_score(confidence_status: str | None) -> float:
    return _hypothesis_pathway_confidence_score(confidence_status)


def _protein_hypothesis_opposing_evidence(
    card: ProteinMechanismCard,
) -> tuple[str, ...]:
    return _build_protein_hypothesis_opposing_evidence(card)


def _pathway_hypothesis_supporting_protein_refs(
    pathway_activity_report: PathwayActivityReport,
    *,
    pathway_id: str,
    condition_a: str,
    condition_b: str,
    cards_by_ref: dict[str, ProteinMechanismCard],
) -> tuple[str, ...]:
    return _build_pathway_hypothesis_supporting_protein_refs(
        pathway_activity_report,
        pathway_id=pathway_id,
        condition_a=condition_a,
        condition_b=condition_b,
        cards_by_ref=cards_by_ref,
    )


def _pathway_hypothesis_opposing_evidence(
    pathway_activity_report: PathwayActivityReport,
    *,
    comparison: PathwayConditionComparisonEntry,
) -> tuple[str, ...]:
    return _build_pathway_hypothesis_opposing_evidence(
        pathway_activity_report,
        comparison=comparison,
    )


def _regulator_hypothesis_opposing_evidence(
    regulator_inference_report: RegulatorInferenceReport,
    *,
    regulator: str,
) -> tuple[str, ...]:
    return _build_regulator_hypothesis_opposing_evidence(
        regulator_inference_report,
        regulator=regulator,
    )
