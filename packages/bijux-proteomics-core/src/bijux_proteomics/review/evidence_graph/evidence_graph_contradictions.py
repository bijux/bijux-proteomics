# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Contradiction detection over the canonical proteomics evidence graph."""

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


class EvidenceGraphContradictionKind(StrEnum):
    """Deterministic contradiction categories emitted by graph rules."""

    PROTEIN_UNCHANGED_WITH_CHANGED_PEPTIDES = "protein_unchanged_with_changed_peptides"
    PTM_CHANGE_EXPLAINED_BY_PROTEIN = "ptm_change_explained_by_protein"
    PATHWAY_ENRICHMENT_WITH_WEAK_PROTEINS = "pathway_enrichment_with_weak_proteins"


class EvidenceGraphContradictionSeverity(StrEnum):
    """Operator-facing contradiction severity."""

    CAUTION = "caution"
    FAIL = "fail"


class EvidenceGraphContradictionEntry(JsonModel):
    """One contradiction detected from the proteomics evidence graph."""

    model_config = ConfigDict(extra="forbid")

    contradiction_id: str = Field(..., min_length=1)
    kind: EvidenceGraphContradictionKind
    severity: EvidenceGraphContradictionSeverity
    claim_node_id: str = Field(..., min_length=1)
    claim_node_ref: str = Field(..., min_length=1)
    related_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    reason: str = Field(..., min_length=1)


class EvidenceGraphContradictionReport(JsonModel):
    """Contradiction report emitted from graph rules."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[EvidenceGraphContradictionEntry, ...] = Field(default_factory=tuple)
    contradiction_count: int = Field(..., ge=0)
    kind_counts: dict[str, int] = Field(default_factory=dict)


def detect_evidence_graph_contradictions(
    graph: ProteomicsEvidenceGraph,
) -> EvidenceGraphContradictionReport:
    """Detect deterministic contradictions from final-result and support patterns."""

    entries: list[EvidenceGraphContradictionEntry] = []
    entries.extend(_detect_protein_peptide_contradictions(graph))
    entries.extend(_detect_ptm_protein_explanations(graph))
    entries.extend(_detect_pathway_support_weakness(graph))

    kind_counts: dict[str, int] = {}
    for entry in entries:
        kind_counts[entry.kind.value] = kind_counts.get(entry.kind.value, 0) + 1
    return EvidenceGraphContradictionReport(
        entries=tuple(sorted(entries, key=lambda entry: entry.contradiction_id)),
        contradiction_count=len(entries),
        kind_counts=dict(sorted(kind_counts.items())),
    )


def render_evidence_graph_contradictions_tsv(
    report: EvidenceGraphContradictionReport,
) -> str:
    """Render contradictions as the governed `contradictions.tsv` surface."""

    rows: list[dict[str, object]] = [
        {
            "contradiction_id": entry.contradiction_id,
            "kind": entry.kind.value,
            "severity": entry.severity.value,
            "claim_node_id": entry.claim_node_id,
            "claim_node_ref": entry.claim_node_ref,
            "related_node_ids": "|".join(entry.related_node_ids),
            "source_row_refs": "|".join(entry.source_row_refs),
            "reason": entry.reason,
        }
        for entry in report.entries
    ]
    return _dict_rows_to_tsv(rows)


def _detect_protein_peptide_contradictions(
    graph: ProteomicsEvidenceGraph,
) -> tuple[EvidenceGraphContradictionEntry, ...]:
    entries: list[EvidenceGraphContradictionEntry] = []
    for protein_result in _statistical_results_with_claim_state(graph, "unchanged"):
        protein = _claim_support_node(
            graph,
            protein_result.node_id,
            ProteomicsEvidenceEdgeKind.PROTEIN_SUPPORTS_STATISTICAL_RESULT,
        )
        if protein is None:
            continue
        peptides = _incoming_source_nodes(
            graph,
            protein.node_id,
            ProteomicsEvidenceEdgeKind.PEPTIDE_QUANTIFIES_PROTEIN,
        )
        changed_peptide_results = tuple(
            peptide_result
            for peptide in peptides
            for peptide_result in _outgoing_target_nodes(
                graph,
                peptide.node_id,
                ProteomicsEvidenceEdgeKind.PEPTIDE_SUPPORTS_STATISTICAL_RESULT,
            )
            if peptide_result.claim_state in {"changed", "upregulated", "downregulated"}
        )
        if len(changed_peptide_results) < 2:
            continue
        source_rows = _unique_source_rows(
            _edges_between_claim_and_support(
                graph,
                protein_result.node_id,
                protein.node_id,
                ProteomicsEvidenceEdgeKind.PROTEIN_SUPPORTS_STATISTICAL_RESULT,
            )
            + tuple(
                edge
                for peptide in peptides
                for edge in _outgoing_edges(graph, peptide.node_id)
                if edge.relation
                is ProteomicsEvidenceEdgeKind.PEPTIDE_SUPPORTS_STATISTICAL_RESULT
            )
        )
        entries.append(
            EvidenceGraphContradictionEntry(
                contradiction_id=f"contradiction:{protein_result.entity_ref}:peptides",
                kind=EvidenceGraphContradictionKind.PROTEIN_UNCHANGED_WITH_CHANGED_PEPTIDES,
                severity=EvidenceGraphContradictionSeverity.FAIL,
                claim_node_id=protein_result.node_id,
                claim_node_ref=protein_result.entity_ref,
                related_node_ids=tuple(
                    sorted(
                        {protein.node_id}
                        | {node.node_id for node in peptides}
                        | {node.node_id for node in changed_peptide_results}
                    )
                ),
                source_row_refs=source_rows,
                reason=(
                    "protein result is unchanged while multiple quantifying peptides are "
                    "reported as changed"
                ),
            )
        )
    return tuple(entries)


def _detect_ptm_protein_explanations(
    graph: ProteomicsEvidenceGraph,
) -> tuple[EvidenceGraphContradictionEntry, ...]:
    entries: list[EvidenceGraphContradictionEntry] = []
    for ptm_result in _statistical_results_with_claim_state(
        graph,
        "upregulated",
        "downregulated",
        "changed",
    ):
        ptm_site = _claim_support_node(
            graph,
            ptm_result.node_id,
            ProteomicsEvidenceEdgeKind.PTM_SITE_SUPPORTS_STATISTICAL_RESULT,
        )
        if ptm_site is None:
            continue
        proteins = _outgoing_target_nodes(
            graph,
            ptm_site.node_id,
            ProteomicsEvidenceEdgeKind.PTM_SITE_BELONGS_TO_PROTEIN,
        )
        for protein in proteins:
            protein_results = _outgoing_target_nodes(
                graph,
                protein.node_id,
                ProteomicsEvidenceEdgeKind.PROTEIN_SUPPORTS_STATISTICAL_RESULT,
            )
            for protein_result in protein_results:
                if protein_result.claim_state != ptm_result.claim_state:
                    continue
                source_rows = _unique_source_rows(
                    _edges_between_claim_and_support(
                        graph,
                        ptm_result.node_id,
                        ptm_site.node_id,
                        ProteomicsEvidenceEdgeKind.PTM_SITE_SUPPORTS_STATISTICAL_RESULT,
                    )
                    + _edges_between_claim_and_support(
                        graph,
                        protein_result.node_id,
                        protein.node_id,
                        ProteomicsEvidenceEdgeKind.PROTEIN_SUPPORTS_STATISTICAL_RESULT,
                    )
                )
                entries.append(
                    EvidenceGraphContradictionEntry(
                        contradiction_id=f"contradiction:{ptm_result.entity_ref}:protein",
                        kind=EvidenceGraphContradictionKind.PTM_CHANGE_EXPLAINED_BY_PROTEIN,
                        severity=EvidenceGraphContradictionSeverity.CAUTION,
                        claim_node_id=ptm_result.node_id,
                        claim_node_ref=ptm_result.entity_ref,
                        related_node_ids=(
                            ptm_site.node_id,
                            protein.node_id,
                            protein_result.node_id,
                        ),
                        source_row_refs=source_rows,
                        reason=(
                            "PTM-site change tracks the same directional protein-abundance "
                            "change and may be explained by protein abundance"
                        ),
                    )
                )
    return tuple(entries)


def _detect_pathway_support_weakness(
    graph: ProteomicsEvidenceGraph,
) -> tuple[EvidenceGraphContradictionEntry, ...]:
    entries: list[EvidenceGraphContradictionEntry] = []
    for pathway_result in _statistical_results_with_claim_state(graph, "enriched"):
        pathway = _claim_support_node(
            graph,
            pathway_result.node_id,
            ProteomicsEvidenceEdgeKind.PATHWAY_SUPPORTS_STATISTICAL_RESULT,
        )
        if pathway is None:
            continue
        proteins = _incoming_source_nodes(
            graph,
            pathway.node_id,
            ProteomicsEvidenceEdgeKind.PROTEIN_MEMBER_OF_PATHWAY,
        )
        if not proteins:
            continue
        if not all(protein.trust_class == "low" for protein in proteins):
            continue
        source_rows = _unique_source_rows(
            _edges_between_claim_and_support(
                graph,
                pathway_result.node_id,
                pathway.node_id,
                ProteomicsEvidenceEdgeKind.PATHWAY_SUPPORTS_STATISTICAL_RESULT,
            )
            + tuple(
                edge
                for protein in proteins
                for edge in _outgoing_edges(graph, protein.node_id)
                if edge.relation is ProteomicsEvidenceEdgeKind.PROTEIN_MEMBER_OF_PATHWAY
                and edge.target_node_id == pathway.node_id
            )
        )
        entries.append(
            EvidenceGraphContradictionEntry(
                contradiction_id=f"contradiction:{pathway_result.entity_ref}:weak-support",
                kind=EvidenceGraphContradictionKind.PATHWAY_ENRICHMENT_WITH_WEAK_PROTEINS,
                severity=EvidenceGraphContradictionSeverity.FAIL,
                claim_node_id=pathway_result.node_id,
                claim_node_ref=pathway_result.entity_ref,
                related_node_ids=tuple(
                    sorted(
                        {pathway.node_id} | {protein.node_id for protein in proteins}
                    )
                ),
                source_row_refs=source_rows,
                reason=(
                    "pathway enrichment is significant while all supporting proteins carry "
                    "weak evidence tiers"
                ),
            )
        )
    return tuple(entries)


def _statistical_results_with_claim_state(
    graph: ProteomicsEvidenceGraph,
    *claim_states: str,
) -> tuple[ProteomicsEvidenceNode, ...]:
    allowed = set(claim_states)
    return tuple(
        node
        for node in graph.nodes
        if node.entity_type is ProteomicsEvidenceNodeKind.STATISTICAL_RESULT
        and node.claim_state in allowed
    )


def _claim_support_node(
    graph: ProteomicsEvidenceGraph,
    claim_node_id: str,
    relation: ProteomicsEvidenceEdgeKind,
) -> ProteomicsEvidenceNode | None:
    for edge in graph.edges:
        if edge.relation is relation and edge.target_node_id == claim_node_id:
            return _require_node_by_id(graph, edge.source_node_id)
    return None


def _incoming_source_nodes(
    graph: ProteomicsEvidenceGraph,
    target_node_id: str,
    relation: ProteomicsEvidenceEdgeKind,
) -> tuple[ProteomicsEvidenceNode, ...]:
    return tuple(
        _require_node_by_id(graph, edge.source_node_id)
        for edge in graph.edges
        if edge.relation is relation and edge.target_node_id == target_node_id
    )


def _outgoing_target_nodes(
    graph: ProteomicsEvidenceGraph,
    source_node_id: str,
    relation: ProteomicsEvidenceEdgeKind,
) -> tuple[ProteomicsEvidenceNode, ...]:
    return tuple(
        _require_node_by_id(graph, edge.target_node_id)
        for edge in graph.edges
        if edge.relation is relation and edge.source_node_id == source_node_id
    )


def _edges_between_claim_and_support(
    graph: ProteomicsEvidenceGraph,
    claim_node_id: str,
    support_node_id: str,
    relation: ProteomicsEvidenceEdgeKind,
) -> tuple[ProteomicsEvidenceEdge, ...]:
    return tuple(
        edge
        for edge in graph.edges
        if edge.relation is relation
        and edge.source_node_id == support_node_id
        and edge.target_node_id == claim_node_id
    )


def _outgoing_edges(
    graph: ProteomicsEvidenceGraph,
    node_id: str,
) -> tuple[ProteomicsEvidenceEdge, ...]:
    return tuple(edge for edge in graph.edges if edge.source_node_id == node_id)


def _require_node_by_id(
    graph: ProteomicsEvidenceGraph,
    node_id: str,
) -> ProteomicsEvidenceNode:
    for node in graph.nodes:
        if node.node_id == node_id:
            return node
    raise ValueError(f"graph node is missing by node_id: {node_id}")


def _unique_source_rows(
    edges: tuple[ProteomicsEvidenceEdge, ...],
) -> tuple[str, ...]:
    return tuple(sorted({edge.source_row_ref for edge in edges}))


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
