# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Graph-based downgrade rules for final proteomics claims."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.review.evidence_graph import (
    ProteomicsEvidenceEdge,
    ProteomicsEvidenceEdgeKind,
    ProteomicsEvidenceGraph,
    ProteomicsEvidenceNode,
    ProteomicsEvidenceNodeKind,
)
from bijux_proteomics.review.evidence_graph.evidence_graph_confidence import (
    EvidenceGraphConfidenceEntry,
    EvidenceGraphConfidenceTier,
    propagate_evidence_graph_confidence,
)
from bijux_proteomics.review.evidence_graph.evidence_graph_contradictions import (
    EvidenceGraphContradictionReport,
    EvidenceGraphContradictionSeverity,
    detect_evidence_graph_contradictions,
)
from bijux_proteomics_foundation import JsonModel


class EvidenceGraphDowngradeReason(StrEnum):
    """Stable downgrade reasons derived from graph evidence."""

    SHARED_PEPTIDE_ONLY = "shared_peptide_only"
    CONTAMINANT_OVERLAP = "contaminant_overlap"
    CONTRADICTION_CAUTION = "contradiction_caution"
    POOR_RUN_QC = "poor_run_qc"
    IMPUTATION_DEPENDENCE = "imputation_dependence"
    LOW_LOCALIZATION = "low_localization"
    POOR_REPRODUCIBILITY = "poor_reproducibility"
    SEVERE_CONTRADICTION = "severe_contradiction"


class FinalClaimEvidenceTier(StrEnum):
    """Stable review tiers for final graph-backed claims."""

    HIGH_CONFIDENCE = "high_confidence"
    MODERATE = "moderate"
    WEAK = "weak"
    AMBIGUOUS = "ambiguous"


class EvidenceGraphFinalResultEntry(JsonModel):
    """One downgraded final result row derived from the canonical graph."""

    model_config = ConfigDict(extra="forbid")

    claim_node_id: str = Field(..., min_length=1)
    claim_node_ref: str = Field(..., min_length=1)
    subject_node_id: str = Field(..., min_length=1)
    subject_node_ref: str = Field(..., min_length=1)
    subject_node_kind: ProteomicsEvidenceNodeKind
    propagated_score: float = Field(..., ge=0.0, le=1.0)
    confidence_tier: EvidenceGraphConfidenceTier
    evidence_tier: FinalClaimEvidenceTier
    downgrade_reasons: tuple[EvidenceGraphDowngradeReason, ...] = Field(
        default_factory=tuple
    )
    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    rationale: str = Field(..., min_length=1)


class EvidenceGraphFinalResultReport(JsonModel):
    """Final graph-backed result table with downgrade semantics."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[EvidenceGraphFinalResultEntry, ...] = Field(default_factory=tuple)
    entry_count: int = Field(..., ge=0)
    evidence_tier_counts: dict[str, int] = Field(default_factory=dict)
    downgrade_reason_counts: dict[str, int] = Field(default_factory=dict)


def build_evidence_graph_final_result_table(
    graph: ProteomicsEvidenceGraph,
) -> EvidenceGraphFinalResultReport:
    """Build final result rows with graph-derived evidence tiers and downgrade reasons."""

    confidence_report = propagate_evidence_graph_confidence(graph)
    contradiction_report = detect_evidence_graph_contradictions(graph)
    contradiction_reasons_by_claim_node_id = _contradiction_reasons_by_claim_node_id(
        contradiction_report
    )
    entries: list[EvidenceGraphFinalResultEntry] = []
    for confidence_entry in confidence_report.entries:
        reasons = _downgrade_reasons_for_entry(
            graph,
            confidence_entry,
            contradiction_reasons_by_claim_node_id=contradiction_reasons_by_claim_node_id,
        )
        effective_confidence_tier = _apply_confidence_downgrades(
            confidence_entry.confidence_tier,
            reasons,
        )
        evidence_tier = _evidence_tier(confidence_entry.confidence_tier, reasons)
        source_rows = set(confidence_entry.source_row_refs)
        source_rows.update(
            edge.source_row_ref
            for edge in _incoming_edges(graph, confidence_entry.claim_node_id)
        )
        entries.append(
            EvidenceGraphFinalResultEntry(
                claim_node_id=confidence_entry.claim_node_id,
                claim_node_ref=confidence_entry.claim_node_ref,
                subject_node_id=confidence_entry.subject_node_id,
                subject_node_ref=confidence_entry.subject_node_ref,
                subject_node_kind=confidence_entry.subject_node_kind,
                propagated_score=confidence_entry.propagated_score,
                confidence_tier=effective_confidence_tier,
                evidence_tier=evidence_tier,
                downgrade_reasons=reasons,
                source_row_refs=tuple(sorted(source_rows)),
                rationale=_build_rationale(
                    confidence_entry.confidence_tier,
                    evidence_tier,
                    reasons,
                ),
            )
        )

    sorted_entries = tuple(
        sorted(
            entries,
            key=lambda entry: (entry.subject_node_kind.value, entry.claim_node_ref),
        )
    )
    evidence_tier_counts: dict[str, int] = {}
    downgrade_reason_counts: dict[str, int] = {}
    for entry in sorted_entries:
        evidence_tier_counts[entry.evidence_tier.value] = (
            evidence_tier_counts.get(entry.evidence_tier.value, 0) + 1
        )
        for reason in entry.downgrade_reasons:
            downgrade_reason_counts[reason.value] = (
                downgrade_reason_counts.get(reason.value, 0) + 1
            )
    return EvidenceGraphFinalResultReport(
        entries=sorted_entries,
        entry_count=len(sorted_entries),
        evidence_tier_counts=dict(sorted(evidence_tier_counts.items())),
        downgrade_reason_counts=dict(sorted(downgrade_reason_counts.items())),
    )


def render_evidence_graph_final_results_tsv(
    report: EvidenceGraphFinalResultReport,
) -> str:
    """Render graph-backed final result rows as TSV."""

    rows = [
        {
            "claim_node_id": entry.claim_node_id,
            "claim_node_ref": entry.claim_node_ref,
            "subject_node_id": entry.subject_node_id,
            "subject_node_ref": entry.subject_node_ref,
            "subject_node_kind": entry.subject_node_kind.value,
            "propagated_score": f"{entry.propagated_score:.4f}",
            "confidence_tier": entry.confidence_tier.value,
            "evidence_tier": entry.evidence_tier.value,
            "downgrade_reasons": "|".join(
                reason.value for reason in entry.downgrade_reasons
            ),
            "source_row_refs": "|".join(entry.source_row_refs),
            "rationale": entry.rationale,
        }
        for entry in report.entries
    ]
    return _dict_rows_to_tsv(rows)


def _downgrade_reasons_for_entry(
    graph: ProteomicsEvidenceGraph,
    entry: EvidenceGraphConfidenceEntry,
    *,
    contradiction_reasons_by_claim_node_id: dict[
        str,
        tuple[EvidenceGraphDowngradeReason, ...],
    ],
) -> tuple[EvidenceGraphDowngradeReason, ...]:
    subject = _require_node_by_id(graph, entry.subject_node_id)
    reasons: set[EvidenceGraphDowngradeReason] = set()

    if subject.entity_type is ProteomicsEvidenceNodeKind.PROTEIN:
        reasons.update(_protein_downgrade_reasons(graph, subject))
    elif subject.entity_type is ProteomicsEvidenceNodeKind.PTM_SITE:
        reasons.update(_ptm_site_downgrade_reasons(graph, subject))
    elif subject.entity_type is ProteomicsEvidenceNodeKind.PATHWAY:
        reasons.update(_pathway_downgrade_reasons(graph, subject))
    else:
        raise ValueError(
            f"unsupported final-result subject kind: {subject.entity_type.value}"
        )

    reasons.update(
        _claim_level_downgrade_reasons(
            graph,
            entry.claim_node_id,
            contradiction_reasons_by_claim_node_id=contradiction_reasons_by_claim_node_id,
        )
    )
    return tuple(sorted(reasons, key=lambda value: value.value))


def _protein_downgrade_reasons(
    graph: ProteomicsEvidenceGraph,
    protein: ProteomicsEvidenceNode,
) -> set[EvidenceGraphDowngradeReason]:
    reasons: set[EvidenceGraphDowngradeReason] = set()
    peptides = _source_nodes_for_relation(
        graph,
        protein.node_id,
        ProteomicsEvidenceEdgeKind.PEPTIDE_QUANTIFIES_PROTEIN,
    )
    if peptides and all(
        _protein_mapping_count(graph, peptide.node_id) > 1 for peptide in peptides
    ):
        reasons.add(EvidenceGraphDowngradeReason.SHARED_PEPTIDE_ONLY)
    if protein.trust_class == "contaminant" or any(
        _maps_to_contaminant_protein(graph, peptide.node_id) for peptide in peptides
    ):
        reasons.add(EvidenceGraphDowngradeReason.CONTAMINANT_OVERLAP)
    if any(_peptide_has_poor_run_qc(graph, peptide.node_id) for peptide in peptides):
        reasons.add(EvidenceGraphDowngradeReason.POOR_RUN_QC)
    if protein.trust_class in {"single_run_only", "exploratory"}:
        reasons.add(EvidenceGraphDowngradeReason.POOR_REPRODUCIBILITY)
    return reasons


def _ptm_site_downgrade_reasons(
    graph: ProteomicsEvidenceGraph,
    ptm_site: ProteomicsEvidenceNode,
) -> set[EvidenceGraphDowngradeReason]:
    reasons: set[EvidenceGraphDowngradeReason] = set()
    proteins = _target_nodes_for_relation(
        graph,
        ptm_site.node_id,
        ProteomicsEvidenceEdgeKind.PTM_SITE_BELONGS_TO_PROTEIN,
    )
    if any(protein.trust_class == "contaminant" for protein in proteins):
        reasons.add(EvidenceGraphDowngradeReason.CONTAMINANT_OVERLAP)
    localization_edges = _incoming_edges_for_relation(
        graph,
        ptm_site.node_id,
        ProteomicsEvidenceEdgeKind.MODIFIED_PEPTIDE_LOCALIZES_PTM_SITE,
    )
    if (
        any(edge.confidence < 0.75 for edge in localization_edges)
        or ptm_site.trust_class == "low"
    ):
        reasons.add(EvidenceGraphDowngradeReason.LOW_LOCALIZATION)
    parent_peptides = tuple(
        peptide
        for modified in _source_nodes_for_relation(
            graph,
            ptm_site.node_id,
            ProteomicsEvidenceEdgeKind.MODIFIED_PEPTIDE_LOCALIZES_PTM_SITE,
        )
        for peptide in _source_nodes_for_relation(
            graph,
            modified.node_id,
            ProteomicsEvidenceEdgeKind.PEPTIDE_HAS_MODIFIED_FORM,
        )
    )
    if any(
        _peptide_has_poor_run_qc(graph, peptide.node_id) for peptide in parent_peptides
    ):
        reasons.add(EvidenceGraphDowngradeReason.POOR_RUN_QC)
    if any(
        protein.trust_class in {"single_run_only", "exploratory"}
        for protein in proteins
    ):
        reasons.add(EvidenceGraphDowngradeReason.POOR_REPRODUCIBILITY)
    return reasons


def _pathway_downgrade_reasons(
    graph: ProteomicsEvidenceGraph,
    pathway: ProteomicsEvidenceNode,
) -> set[EvidenceGraphDowngradeReason]:
    reasons: set[EvidenceGraphDowngradeReason] = set()
    proteins = _source_nodes_for_relation(
        graph,
        pathway.node_id,
        ProteomicsEvidenceEdgeKind.PROTEIN_MEMBER_OF_PATHWAY,
    )
    if any(protein.trust_class == "contaminant" for protein in proteins):
        reasons.add(EvidenceGraphDowngradeReason.CONTAMINANT_OVERLAP)
    if any(
        protein.trust_class in {"single_run_only", "exploratory"}
        for protein in proteins
    ):
        reasons.add(EvidenceGraphDowngradeReason.POOR_REPRODUCIBILITY)
    if any(
        _peptide_has_poor_run_qc(graph, peptide.node_id)
        for protein in proteins
        for peptide in _source_nodes_for_relation(
            graph,
            protein.node_id,
            ProteomicsEvidenceEdgeKind.PEPTIDE_QUANTIFIES_PROTEIN,
        )
    ):
        reasons.add(EvidenceGraphDowngradeReason.POOR_RUN_QC)
    return reasons


def _claim_level_downgrade_reasons(
    graph: ProteomicsEvidenceGraph,
    claim_node_id: str,
    *,
    contradiction_reasons_by_claim_node_id: dict[
        str,
        tuple[EvidenceGraphDowngradeReason, ...],
    ],
) -> set[EvidenceGraphDowngradeReason]:
    reasons: set[EvidenceGraphDowngradeReason] = set()
    quant_values = _source_nodes_for_relation(
        graph,
        claim_node_id,
        ProteomicsEvidenceEdgeKind.QUANT_VALUE_SUPPORTS_STATISTICAL_RESULT,
    )
    if any(quant_value.trust_class == "imputed" for quant_value in quant_values):
        reasons.add(EvidenceGraphDowngradeReason.IMPUTATION_DEPENDENCE)
    if any(
        _quant_value_has_poor_run_qc(graph, quant_value) for quant_value in quant_values
    ):
        reasons.add(EvidenceGraphDowngradeReason.POOR_RUN_QC)
    claim_node = _require_node_by_id(graph, claim_node_id)
    if claim_node.trust_class in {"single_run_only", "exploratory"}:
        reasons.add(EvidenceGraphDowngradeReason.POOR_REPRODUCIBILITY)
    reasons.update(contradiction_reasons_by_claim_node_id.get(claim_node_id, ()))
    return reasons


def _contradiction_reasons_by_claim_node_id(
    contradiction_report: EvidenceGraphContradictionReport,
) -> dict[str, tuple[EvidenceGraphDowngradeReason, ...]]:
    reasons_by_claim_node_id: dict[str, set[EvidenceGraphDowngradeReason]] = {}
    for contradiction in contradiction_report.entries:
        reasons = reasons_by_claim_node_id.setdefault(
            contradiction.claim_node_id, set()
        )
        if contradiction.severity is EvidenceGraphContradictionSeverity.FAIL:
            reasons.add(EvidenceGraphDowngradeReason.SEVERE_CONTRADICTION)
        else:
            reasons.add(EvidenceGraphDowngradeReason.CONTRADICTION_CAUTION)
    return {
        claim_node_id: tuple(sorted(reasons, key=lambda value: value.value))
        for claim_node_id, reasons in reasons_by_claim_node_id.items()
    }


def _protein_mapping_count(graph: ProteomicsEvidenceGraph, peptide_node_id: str) -> int:
    return len(
        _target_nodes_for_relation(
            graph,
            peptide_node_id,
            ProteomicsEvidenceEdgeKind.PEPTIDE_MAPS_TO_PROTEIN,
        )
    )


def _maps_to_contaminant_protein(
    graph: ProteomicsEvidenceGraph, peptide_node_id: str
) -> bool:
    return any(
        protein.trust_class == "contaminant"
        for protein in _target_nodes_for_relation(
            graph,
            peptide_node_id,
            ProteomicsEvidenceEdgeKind.PEPTIDE_MAPS_TO_PROTEIN,
        )
    )


def _peptide_has_poor_run_qc(
    graph: ProteomicsEvidenceGraph, peptide_node_id: str
) -> bool:
    psms = _source_nodes_for_relation(
        graph,
        peptide_node_id,
        ProteomicsEvidenceEdgeKind.PSM_SUPPORTS_PEPTIDE,
    )
    precursors = _source_nodes_for_relation(
        graph,
        peptide_node_id,
        ProteomicsEvidenceEdgeKind.PRECURSOR_SUPPORTS_PEPTIDE,
    )
    spectra = {
        spectrum.node_id: spectrum
        for psm in psms
        for spectrum in _source_nodes_for_relation(
            graph,
            psm.node_id,
            ProteomicsEvidenceEdgeKind.SPECTRUM_SUPPORTS_PSM,
        )
    }
    spectra.update(
        {
            spectrum.node_id: spectrum
            for precursor in precursors
            for spectrum in _source_nodes_for_relation(
                graph,
                precursor.node_id,
                ProteomicsEvidenceEdgeKind.SPECTRUM_ASSIGNS_PRECURSOR,
            )
        }
    )
    for spectrum in spectra.values():
        runs = _source_nodes_for_relation(
            graph,
            spectrum.node_id,
            ProteomicsEvidenceEdgeKind.RUN_ACQUIRED_SPECTRUM,
        )
        for run in runs:
            qc_decisions = _target_nodes_for_relation(
                graph,
                run.node_id,
                ProteomicsEvidenceEdgeKind.RUN_GOVERNED_BY_QC_DECISION,
            )
            if any(
                qc.claim_state in {"caution", "fail", "failed", "rejected"}
                or qc.trust_class == "low"
                for qc in qc_decisions
            ):
                return True
    return False


def _quant_value_has_poor_run_qc(
    graph: ProteomicsEvidenceGraph,
    quant_value: ProteomicsEvidenceNode,
) -> bool:
    run_refs = [
        context.entity_ref
        for context in quant_value.context_refs
        if context.entity_type is ProteomicsEvidenceNodeKind.RUN
    ]
    sample_refs = [
        context.entity_ref
        for context in quant_value.context_refs
        if context.entity_type is ProteomicsEvidenceNodeKind.SAMPLE
    ]
    if not run_refs:
        run_refs = [
            run.entity_ref
            for sample_ref in sample_refs
            for sample in (
                _require_node_by_ref(
                    graph, ProteomicsEvidenceNodeKind.SAMPLE, sample_ref
                ),
            )
            for run in _target_nodes_for_relation(
                graph,
                sample.node_id,
                ProteomicsEvidenceEdgeKind.SAMPLE_CONTAINS_RUN,
            )
        ]
    for run_ref in run_refs:
        run = _require_node_by_ref(graph, ProteomicsEvidenceNodeKind.RUN, run_ref)
        qc_decisions = _target_nodes_for_relation(
            graph,
            run.node_id,
            ProteomicsEvidenceEdgeKind.RUN_GOVERNED_BY_QC_DECISION,
        )
        if any(
            qc.claim_state in {"caution", "fail", "failed", "rejected"}
            or qc.trust_class == "low"
            for qc in qc_decisions
        ):
            return True
    return False


def _apply_confidence_downgrades(
    confidence_tier: EvidenceGraphConfidenceTier,
    reasons: tuple[EvidenceGraphDowngradeReason, ...],
) -> EvidenceGraphConfidenceTier:
    effective_tier = confidence_tier
    if EvidenceGraphDowngradeReason.SEVERE_CONTRADICTION in reasons:
        if effective_tier in {
            EvidenceGraphConfidenceTier.HIGH,
            EvidenceGraphConfidenceTier.MODERATE,
        }:
            effective_tier = EvidenceGraphConfidenceTier.LOW
    elif (
        EvidenceGraphDowngradeReason.CONTRADICTION_CAUTION in reasons
        and effective_tier is EvidenceGraphConfidenceTier.HIGH
    ):
        effective_tier = EvidenceGraphConfidenceTier.MODERATE
    if EvidenceGraphDowngradeReason.POOR_RUN_QC in reasons:
        if effective_tier is EvidenceGraphConfidenceTier.HIGH:
            effective_tier = EvidenceGraphConfidenceTier.MODERATE
        elif effective_tier is EvidenceGraphConfidenceTier.MODERATE:
            effective_tier = EvidenceGraphConfidenceTier.LOW
    return effective_tier


def _evidence_tier(
    confidence_tier: EvidenceGraphConfidenceTier,
    reasons: tuple[EvidenceGraphDowngradeReason, ...],
) -> FinalClaimEvidenceTier:
    if EvidenceGraphDowngradeReason.SHARED_PEPTIDE_ONLY in reasons:
        return FinalClaimEvidenceTier.AMBIGUOUS
    if EvidenceGraphDowngradeReason.SEVERE_CONTRADICTION in reasons:
        return FinalClaimEvidenceTier.WEAK

    if confidence_tier is EvidenceGraphConfidenceTier.HIGH:
        tier = FinalClaimEvidenceTier.HIGH_CONFIDENCE
    elif confidence_tier is EvidenceGraphConfidenceTier.MODERATE:
        tier = FinalClaimEvidenceTier.MODERATE
    else:
        tier = FinalClaimEvidenceTier.WEAK

    if EvidenceGraphDowngradeReason.CONTRADICTION_CAUTION in reasons:
        if tier is FinalClaimEvidenceTier.HIGH_CONFIDENCE:
            tier = FinalClaimEvidenceTier.MODERATE
        elif tier is FinalClaimEvidenceTier.MODERATE:
            tier = FinalClaimEvidenceTier.WEAK

    degrade_steps = sum(
        reason
        in {
            EvidenceGraphDowngradeReason.CONTAMINANT_OVERLAP,
            EvidenceGraphDowngradeReason.POOR_RUN_QC,
            EvidenceGraphDowngradeReason.IMPUTATION_DEPENDENCE,
            EvidenceGraphDowngradeReason.LOW_LOCALIZATION,
            EvidenceGraphDowngradeReason.POOR_REPRODUCIBILITY,
        }
        for reason in reasons
    )
    if degrade_steps == 0:
        return tier
    if tier is FinalClaimEvidenceTier.HIGH_CONFIDENCE and degrade_steps == 1:
        return FinalClaimEvidenceTier.MODERATE
    return FinalClaimEvidenceTier.WEAK


def _build_rationale(
    confidence_tier: EvidenceGraphConfidenceTier,
    evidence_tier: FinalClaimEvidenceTier,
    reasons: tuple[EvidenceGraphDowngradeReason, ...],
) -> str:
    if not reasons:
        return (
            f"graph confidence remains {confidence_tier.value}, so final evidence tier stays "
            f"{evidence_tier.value}"
        )
    return (
        f"graph confidence starts at {confidence_tier.value} and downgrades to "
        f"{evidence_tier.value} because "
        + ", ".join(reason.value for reason in reasons)
    )


def _incoming_edges(
    graph: ProteomicsEvidenceGraph,
    target_node_id: str,
) -> tuple[ProteomicsEvidenceEdge, ...]:
    return tuple(edge for edge in graph.edges if edge.target_node_id == target_node_id)


def _incoming_edges_for_relation(
    graph: ProteomicsEvidenceGraph,
    target_node_id: str,
    relation: ProteomicsEvidenceEdgeKind,
) -> tuple[ProteomicsEvidenceEdge, ...]:
    return tuple(
        edge
        for edge in graph.edges
        if edge.target_node_id == target_node_id and edge.relation is relation
    )


def _source_nodes_for_relation(
    graph: ProteomicsEvidenceGraph,
    target_node_id: str,
    relation: ProteomicsEvidenceEdgeKind,
) -> tuple[ProteomicsEvidenceNode, ...]:
    return tuple(
        _require_node_by_id(graph, edge.source_node_id)
        for edge in graph.edges
        if edge.target_node_id == target_node_id and edge.relation is relation
    )


def _target_nodes_for_relation(
    graph: ProteomicsEvidenceGraph,
    source_node_id: str,
    relation: ProteomicsEvidenceEdgeKind,
) -> tuple[ProteomicsEvidenceNode, ...]:
    return tuple(
        _require_node_by_id(graph, edge.target_node_id)
        for edge in graph.edges
        if edge.source_node_id == source_node_id and edge.relation is relation
    )


def _require_node_by_id(
    graph: ProteomicsEvidenceGraph,
    node_id: str,
) -> ProteomicsEvidenceNode:
    for node in graph.nodes:
        if node.node_id == node_id:
            return node
    raise ValueError(f"graph node is missing by node_id: {node_id}")


def _require_node_by_ref(
    graph: ProteomicsEvidenceGraph,
    entity_type: ProteomicsEvidenceNodeKind,
    entity_ref: str,
) -> ProteomicsEvidenceNode:
    for node in graph.nodes:
        if node.entity_type is entity_type and node.entity_ref == entity_ref:
            return node
    raise ValueError(
        f"graph node is missing by entity_ref: {entity_type.value}:{entity_ref}"
    )


def _dict_rows_to_tsv(rows: list[dict[str, object]]) -> str:
    if not rows:
        return ""
    fieldnames = list(rows[0])
    buffer = StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=fieldnames,
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()
