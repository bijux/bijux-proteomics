# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Confidence propagation over the canonical proteomics evidence graph."""

from __future__ import annotations

import csv
from io import StringIO
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.confidence import ConfidenceTier
from bijux_proteomics.io.chromatographic_evidence import (
    ChromatographicEvidenceScoreReport,
)
from bijux_proteomics.io.dia_fragment_coelution import DiaFragmentCoelutionReport
from bijux_proteomics.io.fragment_ratio_stability import FragmentRatioStabilityReport
from bijux_proteomics.review.evidence_graph import (
    ProteomicsEvidenceEdge,
    ProteomicsEvidenceEdgeKind,
    ProteomicsEvidenceGraph,
    ProteomicsEvidenceNode,
    ProteomicsEvidenceNodeKind,
)
from bijux_proteomics.sequences import PeptideChemicalLiabilityReport
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.quantification.peptide_profile_inconsistency import (
        PeptideProfileInconsistencyReport,
    )


EvidenceGraphConfidenceTier = ConfidenceTier


class EvidenceGraphConfidenceEntry(JsonModel):
    """Propagated confidence for one final reviewable claim."""

    model_config = ConfigDict(extra="forbid")

    claim_node_id: str = Field(..., min_length=1)
    claim_node_ref: str = Field(..., min_length=1)
    subject_node_id: str = Field(..., min_length=1)
    subject_node_ref: str = Field(..., min_length=1)
    subject_node_kind: ProteomicsEvidenceNodeKind
    propagated_score: float = Field(..., ge=0.0, le=1.0)
    confidence_tier: EvidenceGraphConfidenceTier
    upstream_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    rationale: str = Field(..., min_length=1)


class EvidenceGraphConfidenceReport(JsonModel):
    """Confidence propagation report for final proteomics claims."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[EvidenceGraphConfidenceEntry, ...] = Field(default_factory=tuple)
    entry_count: int = Field(..., ge=0)
    tier_counts: dict[str, int] = Field(default_factory=dict)


def propagate_evidence_graph_confidence(
    graph: ProteomicsEvidenceGraph,
    *,
    chromatographic_score_report: ChromatographicEvidenceScoreReport | None = None,
    dia_fragment_coelution_report: DiaFragmentCoelutionReport | None = None,
    dia_fragment_ratio_stability_report: FragmentRatioStabilityReport | None = None,
    peptide_profile_inconsistency_report: PeptideProfileInconsistencyReport
    | None = None,
    peptide_liability_reports: tuple[PeptideChemicalLiabilityReport, ...] = (),
) -> EvidenceGraphConfidenceReport:
    """Propagate upstream evidence quality into final protein, PTM, and pathway claims."""

    protein_cache: dict[str, tuple[float, set[str], set[str]]] = {}
    ptm_cache: dict[str, tuple[float, set[str], set[str]]] = {}
    chromatographic_scores_by_peptide = (
        {}
        if chromatographic_score_report is None
        else {
            entry.peptide_ref: entry.chromatographic_evidence_score
            for entry in chromatographic_score_report.peptide_entries
        }
    )
    coelution_scores_by_precursor = (
        {}
        if dia_fragment_coelution_report is None
        else _coelution_scores_by_precursor(dia_fragment_coelution_report)
    )
    ratio_stability_scores_by_precursor = (
        {}
        if dia_fragment_ratio_stability_report is None
        else _ratio_stability_scores_by_analyte(dia_fragment_ratio_stability_report)
    )
    peptide_profile_scores_by_protein_and_peptide = (
        {}
        if peptide_profile_inconsistency_report is None
        else {
            (entry.entity_id, entry.peptide_sequence): entry.profile_agreement_score
            for entry in peptide_profile_inconsistency_report.entries
        }
    )
    peptide_liability_scores_by_peptide = {
        report.detectability_report.property_report.residue_sequence: (
            report.suitability_score
        )
        for report in peptide_liability_reports
    }
    entries: list[EvidenceGraphConfidenceEntry] = []

    for claim in _statistical_results(graph):
        support_edges = _incoming_edges(
            graph,
            claim.node_id,
            (
                ProteomicsEvidenceEdgeKind.PROTEIN_SUPPORTS_STATISTICAL_RESULT,
                ProteomicsEvidenceEdgeKind.PTM_SITE_SUPPORTS_STATISTICAL_RESULT,
                ProteomicsEvidenceEdgeKind.PATHWAY_SUPPORTS_STATISTICAL_RESULT,
            ),
        )
        for support_edge in support_edges:
            subject = _require_node_by_id(graph, support_edge.source_node_id)
            score, upstream_ids, source_rows = _subject_confidence(
                graph,
                subject,
                protein_cache=protein_cache,
                ptm_cache=ptm_cache,
                chromatographic_scores_by_peptide=chromatographic_scores_by_peptide,
                coelution_scores_by_precursor=coelution_scores_by_precursor,
                ratio_stability_scores_by_precursor=ratio_stability_scores_by_precursor,
                peptide_profile_scores_by_protein_and_peptide=(
                    peptide_profile_scores_by_protein_and_peptide
                ),
                peptide_liability_scores_by_peptide=peptide_liability_scores_by_peptide,
            )
            propagated_score = _average(
                (
                    support_edge.confidence,
                    score,
                    _trust_score(subject.trust_class),
                    _trust_score(claim.trust_class),
                )
            )
            upstream_node_ids = tuple(sorted({subject.node_id} | upstream_ids))
            source_row_refs = tuple(sorted({support_edge.source_row_ref} | source_rows))
            entries.append(
                EvidenceGraphConfidenceEntry(
                    claim_node_id=claim.node_id,
                    claim_node_ref=claim.entity_ref,
                    subject_node_id=subject.node_id,
                    subject_node_ref=subject.entity_ref,
                    subject_node_kind=subject.entity_type,
                    propagated_score=round(propagated_score, 4),
                    confidence_tier=_confidence_tier(propagated_score),
                    upstream_node_ids=upstream_node_ids,
                    source_row_refs=source_row_refs,
                    rationale=_build_rationale(
                        subject.entity_type,
                        propagated_score,
                        peptide_chromatography_used=bool(
                            chromatographic_scores_by_peptide
                        ),
                        fragment_ratio_used=bool(ratio_stability_scores_by_precursor),
                        peptide_profile_used=bool(
                            peptide_profile_scores_by_protein_and_peptide
                        ),
                        peptide_liability_used=bool(
                            peptide_liability_scores_by_peptide
                        ),
                    ),
                )
            )

    sorted_entries = tuple(
        sorted(
            entries,
            key=lambda entry: (entry.subject_node_kind.value, entry.claim_node_ref),
        )
    )
    tier_counts: dict[str, int] = {}
    for entry in sorted_entries:
        tier_counts[entry.confidence_tier.value] = (
            tier_counts.get(entry.confidence_tier.value, 0) + 1
        )
    return EvidenceGraphConfidenceReport(
        entries=sorted_entries,
        entry_count=len(sorted_entries),
        tier_counts=dict(sorted(tier_counts.items())),
    )


def render_evidence_graph_confidence_tsv(
    report: EvidenceGraphConfidenceReport,
) -> str:
    """Render propagated confidence as a deterministic TSV surface."""

    rows = [
        {
            "claim_node_id": entry.claim_node_id,
            "claim_node_ref": entry.claim_node_ref,
            "subject_node_id": entry.subject_node_id,
            "subject_node_ref": entry.subject_node_ref,
            "subject_node_kind": entry.subject_node_kind.value,
            "propagated_score": f"{entry.propagated_score:.4f}",
            "confidence_tier": entry.confidence_tier.value,
            "upstream_node_ids": "|".join(entry.upstream_node_ids),
            "source_row_refs": "|".join(entry.source_row_refs),
            "rationale": entry.rationale,
        }
        for entry in report.entries
    ]
    return _dict_rows_to_tsv(rows)


def _subject_confidence(
    graph: ProteomicsEvidenceGraph,
    subject: ProteomicsEvidenceNode,
    *,
    protein_cache: dict[str, tuple[float, set[str], set[str]]],
    ptm_cache: dict[str, tuple[float, set[str], set[str]]],
    chromatographic_scores_by_peptide: dict[str, float],
    coelution_scores_by_precursor: dict[str, float],
    ratio_stability_scores_by_precursor: dict[str, float],
    peptide_profile_scores_by_protein_and_peptide: dict[tuple[str, str], float],
    peptide_liability_scores_by_peptide: dict[str, float],
) -> tuple[float, set[str], set[str]]:
    if subject.entity_type is ProteomicsEvidenceNodeKind.PROTEIN:
        return _protein_confidence(
            graph,
            subject.node_id,
            protein_cache=protein_cache,
            chromatographic_scores_by_peptide=chromatographic_scores_by_peptide,
            coelution_scores_by_precursor=coelution_scores_by_precursor,
            ratio_stability_scores_by_precursor=ratio_stability_scores_by_precursor,
            peptide_profile_scores_by_protein_and_peptide=(
                peptide_profile_scores_by_protein_and_peptide
            ),
            peptide_liability_scores_by_peptide=peptide_liability_scores_by_peptide,
        )
    if subject.entity_type is ProteomicsEvidenceNodeKind.PTM_SITE:
        return _ptm_site_confidence(
            graph,
            subject.node_id,
            protein_cache=protein_cache,
            ptm_cache=ptm_cache,
            chromatographic_scores_by_peptide=chromatographic_scores_by_peptide,
            coelution_scores_by_precursor=coelution_scores_by_precursor,
            ratio_stability_scores_by_precursor=ratio_stability_scores_by_precursor,
            peptide_profile_scores_by_protein_and_peptide=(
                peptide_profile_scores_by_protein_and_peptide
            ),
            peptide_liability_scores_by_peptide=peptide_liability_scores_by_peptide,
        )
    if subject.entity_type is ProteomicsEvidenceNodeKind.PATHWAY:
        return _pathway_confidence(
            graph,
            subject.node_id,
            protein_cache=protein_cache,
            chromatographic_scores_by_peptide=chromatographic_scores_by_peptide,
            coelution_scores_by_precursor=coelution_scores_by_precursor,
            ratio_stability_scores_by_precursor=ratio_stability_scores_by_precursor,
            peptide_profile_scores_by_protein_and_peptide=(
                peptide_profile_scores_by_protein_and_peptide
            ),
            peptide_liability_scores_by_peptide=peptide_liability_scores_by_peptide,
        )
    raise ValueError(
        f"unsupported confidence subject kind: {subject.entity_type.value}"
    )


def _protein_confidence(
    graph: ProteomicsEvidenceGraph,
    protein_node_id: str,
    *,
    protein_cache: dict[str, tuple[float, set[str], set[str]]],
    chromatographic_scores_by_peptide: dict[str, float],
    coelution_scores_by_precursor: dict[str, float],
    ratio_stability_scores_by_precursor: dict[str, float],
    peptide_profile_scores_by_protein_and_peptide: dict[tuple[str, str], float],
    peptide_liability_scores_by_peptide: dict[str, float],
) -> tuple[float, set[str], set[str]]:
    cached = protein_cache.get(protein_node_id)
    if cached is not None:
        return cached

    protein = _require_node_by_id(graph, protein_node_id)
    quant_edges = _incoming_edges(
        graph,
        protein_node_id,
        (ProteomicsEvidenceEdgeKind.PEPTIDE_QUANTIFIES_PROTEIN,),
    )
    if not quant_edges:
        quant_edges = _incoming_edges(
            graph,
            protein_node_id,
            (ProteomicsEvidenceEdgeKind.PEPTIDE_MAPS_TO_PROTEIN,),
        )

    path_scores: list[float] = []
    upstream_ids: set[str] = set()
    source_rows: set[str] = set()
    for edge in quant_edges:
        peptide = _require_node_by_id(graph, edge.source_node_id)
        peptide_score, peptide_ids, peptide_rows = _peptide_confidence(
            graph,
            peptide.node_id,
            chromatographic_scores_by_peptide=chromatographic_scores_by_peptide,
            coelution_scores_by_precursor=coelution_scores_by_precursor,
            ratio_stability_scores_by_precursor=ratio_stability_scores_by_precursor,
            peptide_liability_scores_by_peptide=peptide_liability_scores_by_peptide,
        )
        profile_score = peptide_profile_scores_by_protein_and_peptide.get(
            (protein.entity_ref, peptide.entity_ref)
        )
        if profile_score is not None:
            peptide_score = _average((peptide_score, profile_score))
        path_scores.append(
            _average(
                (edge.confidence, peptide_score, _trust_score(peptide.trust_class))
            )
        )
        upstream_ids.update(peptide_ids | {peptide.node_id})
        source_rows.update(peptide_rows | {edge.source_row_ref})

    if path_scores:
        score = _average(
            tuple(sorted(path_scores, reverse=True)[:2])
            + (_trust_score(protein.trust_class),)
        )
    else:
        score = _trust_score(protein.trust_class)

    result = (score, upstream_ids, source_rows)
    protein_cache[protein_node_id] = result
    return result


def _ptm_site_confidence(
    graph: ProteomicsEvidenceGraph,
    ptm_site_node_id: str,
    *,
    protein_cache: dict[str, tuple[float, set[str], set[str]]],
    ptm_cache: dict[str, tuple[float, set[str], set[str]]],
    chromatographic_scores_by_peptide: dict[str, float],
    coelution_scores_by_precursor: dict[str, float],
    ratio_stability_scores_by_precursor: dict[str, float],
    peptide_profile_scores_by_protein_and_peptide: dict[tuple[str, str], float],
    peptide_liability_scores_by_peptide: dict[str, float],
) -> tuple[float, set[str], set[str]]:
    cached = ptm_cache.get(ptm_site_node_id)
    if cached is not None:
        return cached

    ptm_site = _require_node_by_id(graph, ptm_site_node_id)
    localization_edges = _incoming_edges(
        graph,
        ptm_site_node_id,
        (ProteomicsEvidenceEdgeKind.MODIFIED_PEPTIDE_LOCALIZES_PTM_SITE,),
    )
    path_scores: list[float] = []
    upstream_ids: set[str] = set()
    source_rows: set[str] = set()
    for edge in localization_edges:
        modified_peptide = _require_node_by_id(graph, edge.source_node_id)
        parent_edges = _incoming_edges(
            graph,
            modified_peptide.node_id,
            (ProteomicsEvidenceEdgeKind.PEPTIDE_HAS_MODIFIED_FORM,),
        )
        if parent_edges:
            for parent_edge in parent_edges:
                parent_peptide = _require_node_by_id(graph, parent_edge.source_node_id)
                peptide_score, peptide_ids, peptide_rows = _peptide_confidence(
                    graph,
                    parent_peptide.node_id,
                    chromatographic_scores_by_peptide=chromatographic_scores_by_peptide,
                    coelution_scores_by_precursor=coelution_scores_by_precursor,
                    ratio_stability_scores_by_precursor=ratio_stability_scores_by_precursor,
                    peptide_liability_scores_by_peptide=peptide_liability_scores_by_peptide,
                )
                path_scores.append(
                    _average(
                        (
                            peptide_score,
                            parent_edge.confidence,
                            edge.confidence,
                            _trust_score(modified_peptide.trust_class),
                        )
                    )
                )
                upstream_ids.update(
                    peptide_ids | {parent_peptide.node_id, modified_peptide.node_id}
                )
                source_rows.update(
                    peptide_rows | {parent_edge.source_row_ref, edge.source_row_ref}
                )
        else:
            path_scores.append(
                _average((edge.confidence, _trust_score(modified_peptide.trust_class)))
            )
            upstream_ids.add(modified_peptide.node_id)
            source_rows.add(edge.source_row_ref)

    protein_edges = _outgoing_edges(
        graph,
        ptm_site_node_id,
        (ProteomicsEvidenceEdgeKind.PTM_SITE_BELONGS_TO_PROTEIN,),
    )
    protein_scores: list[float] = []
    for edge in protein_edges:
        protein_score, protein_ids, protein_rows = _protein_confidence(
            graph,
            edge.target_node_id,
            protein_cache=protein_cache,
            chromatographic_scores_by_peptide=chromatographic_scores_by_peptide,
            coelution_scores_by_precursor=coelution_scores_by_precursor,
            ratio_stability_scores_by_precursor=ratio_stability_scores_by_precursor,
            peptide_profile_scores_by_protein_and_peptide=(
                peptide_profile_scores_by_protein_and_peptide
            ),
            peptide_liability_scores_by_peptide=peptide_liability_scores_by_peptide,
        )
        protein_scores.append(_average((edge.confidence, protein_score)))
        upstream_ids.update(protein_ids | {edge.target_node_id})
        source_rows.update(protein_rows | {edge.source_row_ref})

    components: tuple[float, ...]
    if path_scores and protein_scores:
        components = (
            _average(tuple(sorted(path_scores, reverse=True)[:2])),
            max(protein_scores),
            _trust_score(ptm_site.trust_class),
        )
    elif path_scores:
        components = (
            _average(tuple(sorted(path_scores, reverse=True)[:2])),
            _trust_score(ptm_site.trust_class),
        )
    elif protein_scores:
        components = (max(protein_scores), _trust_score(ptm_site.trust_class))
    else:
        components = (_trust_score(ptm_site.trust_class),)

    score = _average(components)
    result = (score, upstream_ids, source_rows)
    ptm_cache[ptm_site_node_id] = result
    return result


def _pathway_confidence(
    graph: ProteomicsEvidenceGraph,
    pathway_node_id: str,
    *,
    protein_cache: dict[str, tuple[float, set[str], set[str]]],
    chromatographic_scores_by_peptide: dict[str, float],
    coelution_scores_by_precursor: dict[str, float],
    ratio_stability_scores_by_precursor: dict[str, float],
    peptide_profile_scores_by_protein_and_peptide: dict[tuple[str, str], float],
    peptide_liability_scores_by_peptide: dict[str, float],
) -> tuple[float, set[str], set[str]]:
    pathway = _require_node_by_id(graph, pathway_node_id)
    membership_edges = _incoming_edges(
        graph,
        pathway_node_id,
        (ProteomicsEvidenceEdgeKind.PROTEIN_MEMBER_OF_PATHWAY,),
    )
    member_scores: list[float] = []
    upstream_ids: set[str] = set()
    source_rows: set[str] = set()
    for edge in membership_edges:
        protein = _require_node_by_id(graph, edge.source_node_id)
        protein_score, protein_ids, protein_rows = _protein_confidence(
            graph,
            protein.node_id,
            protein_cache=protein_cache,
            chromatographic_scores_by_peptide=chromatographic_scores_by_peptide,
            coelution_scores_by_precursor=coelution_scores_by_precursor,
            ratio_stability_scores_by_precursor=ratio_stability_scores_by_precursor,
            peptide_profile_scores_by_protein_and_peptide=(
                peptide_profile_scores_by_protein_and_peptide
            ),
            peptide_liability_scores_by_peptide=peptide_liability_scores_by_peptide,
        )
        member_scores.append(
            _average(
                (edge.confidence, protein_score, _trust_score(protein.trust_class))
            )
        )
        upstream_ids.update(protein_ids | {protein.node_id})
        source_rows.update(protein_rows | {edge.source_row_ref})

    if member_scores:
        score = _average(member_scores + [_trust_score(pathway.trust_class)])
    else:
        score = _trust_score(pathway.trust_class)
    return score, upstream_ids, source_rows


def _peptide_confidence(
    graph: ProteomicsEvidenceGraph,
    peptide_node_id: str,
    *,
    chromatographic_scores_by_peptide: dict[str, float],
    coelution_scores_by_precursor: dict[str, float],
    ratio_stability_scores_by_precursor: dict[str, float],
    peptide_liability_scores_by_peptide: dict[str, float],
) -> tuple[float, set[str], set[str]]:
    peptide = _require_node_by_id(graph, peptide_node_id)
    support_edges = _incoming_edges(
        graph,
        peptide_node_id,
        (
            ProteomicsEvidenceEdgeKind.PSM_SUPPORTS_PEPTIDE,
            ProteomicsEvidenceEdgeKind.PRECURSOR_SUPPORTS_PEPTIDE,
        ),
    )
    support_scores: list[float] = []
    upstream_ids: set[str] = set()
    source_rows: set[str] = set()
    for edge in support_edges:
        upstream = _require_node_by_id(graph, edge.source_node_id)
        acquisition_score, acquisition_ids, acquisition_rows = _acquisition_confidence(
            graph,
            upstream.node_id,
        )
        support_score = _average(
            (edge.confidence, acquisition_score, _trust_score(upstream.trust_class))
        )
        if upstream.entity_type is ProteomicsEvidenceNodeKind.PRECURSOR:
            coelution_score = coelution_scores_by_precursor.get(upstream.entity_ref)
            if coelution_score is not None:
                support_score = _average((support_score, coelution_score))
            ratio_stability_score = ratio_stability_scores_by_precursor.get(
                upstream.entity_ref
            )
            if ratio_stability_score is not None:
                support_score = _average((support_score, ratio_stability_score))
        support_scores.append(support_score)
        upstream_ids.update(acquisition_ids | {upstream.node_id})
        source_rows.update(acquisition_rows | {edge.source_row_ref})

    if support_scores:
        score = _average(
            tuple(sorted(support_scores, reverse=True)[:2])
            + (_trust_score(peptide.trust_class),)
        )
    else:
        score = _trust_score(peptide.trust_class)
    chromatographic_score = chromatographic_scores_by_peptide.get(peptide.entity_ref)
    if chromatographic_score is not None:
        score = _average((score, chromatographic_score))
    liability_score = peptide_liability_scores_by_peptide.get(peptide.entity_ref)
    if liability_score is not None:
        score = _average((score, liability_score))
    return score, upstream_ids, source_rows


def _acquisition_confidence(
    graph: ProteomicsEvidenceGraph,
    node_id: str,
) -> tuple[float, set[str], set[str]]:
    node = _require_node_by_id(graph, node_id)
    if node.entity_type is ProteomicsEvidenceNodeKind.PSM:
        incoming = _incoming_edges(
            graph,
            node_id,
            (ProteomicsEvidenceEdgeKind.SPECTRUM_SUPPORTS_PSM,),
        )
    elif node.entity_type is ProteomicsEvidenceNodeKind.PRECURSOR:
        incoming = _incoming_edges(
            graph,
            node_id,
            (ProteomicsEvidenceEdgeKind.SPECTRUM_ASSIGNS_PRECURSOR,),
        )
    else:
        return _trust_score(node.trust_class), set(), set()

    if not incoming:
        return _trust_score(node.trust_class), set(), set()

    scores: list[float] = []
    upstream_ids: set[str] = set()
    source_rows: set[str] = set()
    for edge in incoming:
        spectrum = _require_node_by_id(graph, edge.source_node_id)
        scores.append(_average((edge.confidence, _trust_score(spectrum.trust_class))))
        upstream_ids.add(spectrum.node_id)
        source_rows.add(edge.source_row_ref)
    return _average(scores), upstream_ids, source_rows


def _statistical_results(
    graph: ProteomicsEvidenceGraph,
) -> tuple[ProteomicsEvidenceNode, ...]:
    return tuple(
        node
        for node in graph.nodes
        if node.entity_type is ProteomicsEvidenceNodeKind.STATISTICAL_RESULT
    )


def _incoming_edges(
    graph: ProteomicsEvidenceGraph,
    target_node_id: str,
    relations: tuple[ProteomicsEvidenceEdgeKind, ...],
) -> tuple[ProteomicsEvidenceEdge, ...]:
    return tuple(
        edge
        for edge in graph.edges
        if edge.target_node_id == target_node_id and edge.relation in relations
    )


def _outgoing_edges(
    graph: ProteomicsEvidenceGraph,
    source_node_id: str,
    relations: tuple[ProteomicsEvidenceEdgeKind, ...],
) -> tuple[ProteomicsEvidenceEdge, ...]:
    return tuple(
        edge
        for edge in graph.edges
        if edge.source_node_id == source_node_id and edge.relation in relations
    )


def _require_node_by_id(
    graph: ProteomicsEvidenceGraph,
    node_id: str,
) -> ProteomicsEvidenceNode:
    for node in graph.nodes:
        if node.node_id == node_id:
            return node
    raise ValueError(f"graph node is missing by node_id: {node_id}")


def _confidence_tier(score: float) -> EvidenceGraphConfidenceTier:
    if score >= 0.85:
        return EvidenceGraphConfidenceTier.HIGH
    if score >= 0.65:
        return EvidenceGraphConfidenceTier.MODERATE
    return EvidenceGraphConfidenceTier.LOW


def _trust_score(trust_class: str) -> float:
    return {
        "high": 0.95,
        "medium": 0.75,
        "low": 0.4,
        "unreviewed": 0.6,
        "accepted": 0.8,
        "caution": 0.5,
        "rejected": 0.2,
    }.get(trust_class, 0.6)


def _average(values: tuple[float, ...] | list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _build_rationale(
    subject_kind: ProteomicsEvidenceNodeKind,
    score: float,
    *,
    peptide_chromatography_used: bool,
    fragment_ratio_used: bool,
    peptide_profile_used: bool,
    peptide_liability_used: bool,
) -> str:
    qualifiers: list[str] = []
    if peptide_chromatography_used:
        qualifiers.append("peptide chromatographic evidence")
    if peptide_liability_used:
        qualifiers.append("peptide chemical liability")
    if peptide_profile_used:
        qualifiers.append("peptide profile inconsistency")
    if fragment_ratio_used:
        qualifiers.append("fragment-ratio stability")
    qualifier = "" if not qualifiers else " and " + " and ".join(qualifiers)
    return (
        f"{subject_kind.value.replace('_', ' ')} confidence propagates from upstream support "
        f"quality{qualifier} with final score {score:.4f}"
    )


def _coelution_scores_by_precursor(
    report: DiaFragmentCoelutionReport,
) -> dict[str, float]:
    grouped_scores: dict[str, list[float]] = {}
    for entry in report.run_entries:
        grouped_scores.setdefault(entry.precursor_id, []).append(entry.coelution_score)
    return {
        precursor_id: _average(scores)
        for precursor_id, scores in grouped_scores.items()
    }


def _ratio_stability_scores_by_analyte(
    report: FragmentRatioStabilityReport,
) -> dict[str, float]:
    grouped_scores: dict[str, list[float]] = {}
    for entry in report.fragment_entries:
        grouped_scores.setdefault(entry.analyte_id, []).append(entry.stability_score)
    return {
        analyte_id: _average(scores) for analyte_id, scores in grouped_scores.items()
    }


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
