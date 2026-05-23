# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Confidence propagation over the canonical proteomics evidence graph."""

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
from bijux_proteomics_foundation import JsonModel


class EvidenceGraphConfidenceTier(StrEnum):
    """Deterministic confidence tiers for final proteomics claims."""

    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


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
) -> EvidenceGraphConfidenceReport:
    """Propagate upstream evidence quality into final protein, PTM, and pathway claims."""

    protein_cache: dict[str, tuple[float, set[str], set[str]]] = {}
    ptm_cache: dict[str, tuple[float, set[str], set[str]]] = {}
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
                    rationale=_build_rationale(subject.entity_type, propagated_score),
                )
            )

    sorted_entries = tuple(
        sorted(entries, key=lambda entry: (entry.subject_node_kind.value, entry.claim_node_ref))
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
) -> tuple[float, set[str], set[str]]:
    if subject.entity_type is ProteomicsEvidenceNodeKind.PROTEIN:
        return _protein_confidence(graph, subject.node_id, protein_cache=protein_cache)
    if subject.entity_type is ProteomicsEvidenceNodeKind.PTM_SITE:
        return _ptm_site_confidence(
            graph,
            subject.node_id,
            protein_cache=protein_cache,
            ptm_cache=ptm_cache,
        )
    if subject.entity_type is ProteomicsEvidenceNodeKind.PATHWAY:
        return _pathway_confidence(graph, subject.node_id, protein_cache=protein_cache)
    raise ValueError(f"unsupported confidence subject kind: {subject.entity_type.value}")


def _protein_confidence(
    graph: ProteomicsEvidenceGraph,
    protein_node_id: str,
    *,
    protein_cache: dict[str, tuple[float, set[str], set[str]]],
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
        peptide_score, peptide_ids, peptide_rows = _peptide_confidence(graph, peptide.node_id)
        path_scores.append(
            _average((edge.confidence, peptide_score, _trust_score(peptide.trust_class)))
        )
        upstream_ids.update(peptide_ids | {peptide.node_id})
        source_rows.update(peptide_rows | {edge.source_row_ref})

    if path_scores:
        score = _average(tuple(sorted(path_scores, reverse=True)[:2]) + (_trust_score(protein.trust_class),))
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
                upstream_ids.update(peptide_ids | {parent_peptide.node_id, modified_peptide.node_id})
                source_rows.update(peptide_rows | {parent_edge.source_row_ref, edge.source_row_ref})
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
        )
        member_scores.append(
            _average((edge.confidence, protein_score, _trust_score(protein.trust_class)))
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
        support_scores.append(
            _average((edge.confidence, acquisition_score, _trust_score(upstream.trust_class)))
        )
        upstream_ids.update(acquisition_ids | {upstream.node_id})
        source_rows.update(acquisition_rows | {edge.source_row_ref})

    if support_scores:
        score = _average(tuple(sorted(support_scores, reverse=True)[:2]) + (_trust_score(peptide.trust_class),))
    else:
        score = _trust_score(peptide.trust_class)
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


def _build_rationale(subject_kind: ProteomicsEvidenceNodeKind, score: float) -> str:
    return (
        f"{subject_kind.value.replace('_', ' ')} confidence propagates from upstream support "
        f"quality with final score {score:.4f}"
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
