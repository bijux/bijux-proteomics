# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Evidence-chain reconstruction over the canonical proteomics evidence graph."""

from __future__ import annotations

from collections import deque
import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.review.evidence_graph.evidence_graph import (
    ProteomicsEvidenceEdge,
    ProteomicsEvidenceEdgeKind,
    ProteomicsEvidenceGraph,
    ProteomicsEvidenceNode,
    ProteomicsEvidenceNodeKind,
)
from bijux_proteomics_foundation import JsonModel


class EvidenceChainClaimKind(StrEnum):
    """Supported final-claim kinds for evidence-chain reconstruction."""

    PROTEIN = "protein"
    PTM_SITE = "ptm_site"
    PATHWAY = "pathway"


class EvidenceChainSourceRow(JsonModel):
    """One parsed source-row reference preserved inside a reconstructed chain."""

    model_config = ConfigDict(extra="forbid")

    source_row_ref: str = Field(..., min_length=1)
    input_file: str = Field(..., min_length=1)
    row_number: str = Field(..., min_length=1)


class EvidenceChainNodeStep(JsonModel):
    """One node in a reconstructed evidence chain."""

    model_config = ConfigDict(extra="forbid")

    depth: int = Field(..., ge=0)
    node: ProteomicsEvidenceNode


class EvidenceChainReport(JsonModel):
    """Structured chain from source rows to one final proteomics claim."""

    model_config = ConfigDict(extra="forbid")

    claim_kind: EvidenceChainClaimKind
    claim_node: ProteomicsEvidenceNode
    statistical_result: ProteomicsEvidenceNode | None = None
    chain_nodes: tuple[EvidenceChainNodeStep, ...] = Field(default_factory=tuple)
    chain_edges: tuple[ProteomicsEvidenceEdge, ...] = Field(default_factory=tuple)
    source_rows: tuple[EvidenceChainSourceRow, ...] = Field(default_factory=tuple)
    node_count: int = Field(..., ge=0)
    edge_count: int = Field(..., ge=0)
    source_row_count: int = Field(..., ge=0)


def reconstruct_protein_evidence_chain(
    graph: ProteomicsEvidenceGraph,
    *,
    protein_id: str,
    statistical_result_id: str,
) -> EvidenceChainReport:
    """Reconstruct the full protein-result chain from source rows to final result."""

    protein = _require_node(graph, ProteomicsEvidenceNodeKind.PROTEIN, protein_id)
    statistical_result = _require_node(
        graph,
        ProteomicsEvidenceNodeKind.STATISTICAL_RESULT,
        statistical_result_id,
    )
    return _build_report(
        graph,
        claim_kind=EvidenceChainClaimKind.PROTEIN,
        claim_node=protein,
        statistical_result=statistical_result,
        seed_node_ids=(protein.node_id, statistical_result.node_id),
        relation_filter={
            ProteomicsEvidenceEdgeKind.RUN_ACQUIRED_SPECTRUM,
            ProteomicsEvidenceEdgeKind.SPECTRUM_ASSIGNS_PRECURSOR,
            ProteomicsEvidenceEdgeKind.SPECTRUM_SUPPORTS_PSM,
            ProteomicsEvidenceEdgeKind.PRECURSOR_SUPPORTS_PEPTIDE,
            ProteomicsEvidenceEdgeKind.PSM_SUPPORTS_PEPTIDE,
            ProteomicsEvidenceEdgeKind.PEPTIDE_MAPS_TO_PROTEIN,
            ProteomicsEvidenceEdgeKind.PEPTIDE_QUANTIFIES_PROTEIN,
            ProteomicsEvidenceEdgeKind.PROTEIN_MEMBER_OF_GROUP,
            ProteomicsEvidenceEdgeKind.PROTEIN_QUANTIFIED_BY_QUANT_VALUE,
            ProteomicsEvidenceEdgeKind.QUANT_VALUE_SUPPORTS_STATISTICAL_RESULT,
            ProteomicsEvidenceEdgeKind.PROTEIN_SUPPORTS_STATISTICAL_RESULT,
        },
        max_depth=6,
    )


def reconstruct_ptm_site_evidence_chain(
    graph: ProteomicsEvidenceGraph,
    *,
    ptm_site_id: str,
    statistical_result_id: str,
) -> EvidenceChainReport:
    """Reconstruct the full PTM-site result chain from source rows to final result."""

    ptm_site = _require_node(graph, ProteomicsEvidenceNodeKind.PTM_SITE, ptm_site_id)
    statistical_result = _require_node(
        graph,
        ProteomicsEvidenceNodeKind.STATISTICAL_RESULT,
        statistical_result_id,
    )
    return _build_report(
        graph,
        claim_kind=EvidenceChainClaimKind.PTM_SITE,
        claim_node=ptm_site,
        statistical_result=statistical_result,
        seed_node_ids=(ptm_site.node_id, statistical_result.node_id),
        relation_filter={
            ProteomicsEvidenceEdgeKind.RUN_ACQUIRED_SPECTRUM,
            ProteomicsEvidenceEdgeKind.SPECTRUM_SUPPORTS_PSM,
            ProteomicsEvidenceEdgeKind.PSM_SUPPORTS_PEPTIDE,
            ProteomicsEvidenceEdgeKind.PEPTIDE_HAS_MODIFIED_FORM,
            ProteomicsEvidenceEdgeKind.MODIFIED_PEPTIDE_LOCALIZES_PTM_SITE,
            ProteomicsEvidenceEdgeKind.PTM_SITE_BELONGS_TO_PROTEIN,
            ProteomicsEvidenceEdgeKind.PTM_SITE_SUPPORTS_STATISTICAL_RESULT,
        },
        max_depth=6,
    )


def reconstruct_pathway_evidence_chain(
    graph: ProteomicsEvidenceGraph,
    *,
    pathway_id: str,
    statistical_result_id: str,
) -> EvidenceChainReport:
    """Reconstruct the full pathway-result chain from source rows to final result."""

    pathway = _require_node(graph, ProteomicsEvidenceNodeKind.PATHWAY, pathway_id)
    statistical_result = _require_node(
        graph,
        ProteomicsEvidenceNodeKind.STATISTICAL_RESULT,
        statistical_result_id,
    )
    return _build_report(
        graph,
        claim_kind=EvidenceChainClaimKind.PATHWAY,
        claim_node=pathway,
        statistical_result=statistical_result,
        seed_node_ids=(pathway.node_id, statistical_result.node_id),
        relation_filter={
            ProteomicsEvidenceEdgeKind.RUN_ACQUIRED_SPECTRUM,
            ProteomicsEvidenceEdgeKind.SPECTRUM_SUPPORTS_PSM,
            ProteomicsEvidenceEdgeKind.PSM_SUPPORTS_PEPTIDE,
            ProteomicsEvidenceEdgeKind.PEPTIDE_MAPS_TO_PROTEIN,
            ProteomicsEvidenceEdgeKind.PEPTIDE_QUANTIFIES_PROTEIN,
            ProteomicsEvidenceEdgeKind.PROTEIN_MEMBER_OF_PATHWAY,
            ProteomicsEvidenceEdgeKind.PATHWAY_SUPPORTS_STATISTICAL_RESULT,
        },
        max_depth=6,
    )


def render_evidence_chain_tsv(report: EvidenceChainReport) -> str:
    """Render one reconstructed evidence chain as TSV."""

    rows: list[dict[str, object]] = []
    source_row_map = {item.source_row_ref: item for item in report.source_rows}
    for edge in report.chain_edges:
        source_row = source_row_map.get(edge.source_row_ref)
        rows.append(
            {
                "claim_kind": report.claim_kind.value,
                "claim_id": report.claim_node.entity_ref,
                "statistical_result_id": (
                    report.statistical_result.entity_ref
                    if report.statistical_result is not None
                    else ""
                ),
                "relation": edge.relation.value,
                "source_node_id": edge.source_node_id,
                "target_node_id": edge.target_node_id,
                "input_file": source_row.input_file if source_row is not None else "",
                "row_number": source_row.row_number if source_row is not None else "",
                "source_row_ref": edge.source_row_ref,
                "confidence": edge.confidence,
                "evidence_type": edge.evidence_type.value,
                "reason": edge.reason,
            }
        )
    return _dict_rows_to_tsv(rows)


def _build_report(
    graph: ProteomicsEvidenceGraph,
    *,
    claim_kind: EvidenceChainClaimKind,
    claim_node: ProteomicsEvidenceNode,
    statistical_result: ProteomicsEvidenceNode | None,
    seed_node_ids: tuple[str, ...],
    relation_filter: set[ProteomicsEvidenceEdgeKind],
    max_depth: int,
) -> EvidenceChainReport:
    node_depths, chain_edges = _walk_chain(
        graph,
        seed_node_ids=seed_node_ids,
        relation_filter=relation_filter,
        max_depth=max_depth,
    )
    chain_nodes = tuple(
        sorted(
            (
                EvidenceChainNodeStep(
                    depth=depth,
                    node=_require_node_by_id(graph, node_id),
                )
                for node_id, depth in node_depths.items()
            ),
            key=lambda step: (step.depth, step.node.node_id),
        )
    )
    source_rows = _collect_source_rows(chain_edges)
    return EvidenceChainReport(
        claim_kind=claim_kind,
        claim_node=claim_node,
        statistical_result=statistical_result,
        chain_nodes=chain_nodes,
        chain_edges=chain_edges,
        source_rows=source_rows,
        node_count=len(chain_nodes),
        edge_count=len(chain_edges),
        source_row_count=len(source_rows),
    )


def _walk_chain(
    graph: ProteomicsEvidenceGraph,
    *,
    seed_node_ids: tuple[str, ...],
    relation_filter: set[ProteomicsEvidenceEdgeKind],
    max_depth: int,
) -> tuple[dict[str, int], tuple[ProteomicsEvidenceEdge, ...]]:
    queue: deque[tuple[str, int]] = deque((node_id, 0) for node_id in seed_node_ids)
    node_depths = dict.fromkeys(seed_node_ids, 0)
    collected_edges: list[ProteomicsEvidenceEdge] = []

    while queue:
        node_id, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for edge in _adjacent_edges(graph, node_id):
            if edge.relation not in relation_filter:
                continue
            collected_edges.append(edge)
            neighbor_id = (
                edge.target_node_id
                if edge.source_node_id == node_id
                else edge.source_node_id
            )
            next_depth = depth + 1
            if neighbor_id not in node_depths or next_depth < node_depths[neighbor_id]:
                node_depths[neighbor_id] = next_depth
                queue.append((neighbor_id, next_depth))

    return node_depths, _unique_edges(tuple(collected_edges))


def _collect_source_rows(
    edges: tuple[ProteomicsEvidenceEdge, ...],
) -> tuple[EvidenceChainSourceRow, ...]:
    items = []
    seen: set[str] = set()
    for edge in edges:
        if edge.source_row_ref in seen:
            continue
        seen.add(edge.source_row_ref)
        input_file, row_number = _parse_source_row_ref(edge.source_row_ref)
        items.append(
            EvidenceChainSourceRow(
                source_row_ref=edge.source_row_ref,
                input_file=input_file,
                row_number=row_number,
            )
        )
    return tuple(sorted(items, key=lambda item: (item.input_file, item.row_number)))


def _parse_source_row_ref(source_row_ref: str) -> tuple[str, str]:
    input_file, row_number = source_row_ref.rsplit(":", 1)
    return input_file, row_number


def _adjacent_edges(
    graph: ProteomicsEvidenceGraph,
    node_id: str,
) -> tuple[ProteomicsEvidenceEdge, ...]:
    return tuple(
        edge
        for edge in graph.edges
        if edge.source_node_id == node_id or edge.target_node_id == node_id
    )


def _require_node(
    graph: ProteomicsEvidenceGraph,
    kind: ProteomicsEvidenceNodeKind,
    entity_ref: str,
) -> ProteomicsEvidenceNode:
    for node in graph.nodes:
        if node.entity_type is kind and node.entity_ref == entity_ref:
            return node
    raise ValueError(f"graph node is missing: {kind.value}:{entity_ref}")


def _require_node_by_id(
    graph: ProteomicsEvidenceGraph,
    node_id: str,
) -> ProteomicsEvidenceNode:
    for node in graph.nodes:
        if node.node_id == node_id:
            return node
    raise ValueError(f"graph node is missing by node_id: {node_id}")


def _unique_edges(
    edges: tuple[ProteomicsEvidenceEdge, ...],
) -> tuple[ProteomicsEvidenceEdge, ...]:
    edge_map = {
        (
            edge.source_node_id,
            edge.target_node_id,
            edge.relation.value,
            edge.source_row_ref,
        ): edge
        for edge in edges
    }
    return tuple(
        sorted(
            edge_map.values(),
            key=lambda edge: (
                edge.source_node_id,
                edge.target_node_id,
                edge.relation.value,
                edge.source_row_ref,
            ),
        )
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
