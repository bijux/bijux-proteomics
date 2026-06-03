# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Deterministic query engine over the canonical proteomics evidence graph."""

from __future__ import annotations

from collections import deque
import csv
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.review.evidence_graph.evidence_graph import (
    ProteomicsEvidenceEdge,
    ProteomicsEvidenceEdgeKind,
    ProteomicsEvidenceGraph,
    ProteomicsEvidenceNode,
    ProteomicsEvidenceNodeKind,
)
from bijux_proteomics.review.evidence_graph.lazy_evidence_graph import (
    LazyProteomicsEvidenceGraph,
)
from bijux_proteomics_foundation import JsonModel

EvidenceGraphQuerySurface = ProteomicsEvidenceGraph | LazyProteomicsEvidenceGraph


class EvidenceGraphPathStep(JsonModel):
    """One node reached while traversing a deterministic evidence path."""

    model_config = ConfigDict(extra="forbid")

    depth: int = Field(..., ge=0)
    node: ProteomicsEvidenceNode


class ProteinEvidenceSummaryReport(JsonModel):
    """Structured protein evidence summary over the canonical graph."""

    model_config = ConfigDict(extra="forbid")

    protein: ProteomicsEvidenceNode
    mapped_peptides: tuple[ProteomicsEvidenceNode, ...] = Field(default_factory=tuple)
    quantifying_peptides: tuple[ProteomicsEvidenceNode, ...] = Field(
        default_factory=tuple
    )
    protein_groups: tuple[ProteomicsEvidenceNode, ...] = Field(default_factory=tuple)
    quant_values: tuple[ProteomicsEvidenceNode, ...] = Field(default_factory=tuple)
    support_edges: tuple[ProteomicsEvidenceEdge, ...] = Field(default_factory=tuple)
    support_edge_count: int = Field(..., ge=0)


class PeptideSupportChainReport(JsonModel):
    """Deterministic peptide support chain over spectra, PSMs, precursors, and proteins."""

    model_config = ConfigDict(extra="forbid")

    peptide: ProteomicsEvidenceNode
    chain_steps: tuple[EvidenceGraphPathStep, ...] = Field(default_factory=tuple)
    support_edges: tuple[ProteomicsEvidenceEdge, ...] = Field(default_factory=tuple)
    step_count: int = Field(..., ge=0)
    edge_count: int = Field(..., ge=0)


class PtmSiteEvidenceReport(JsonModel):
    """Structured PTM-site evidence over localized peptides and mapped proteins."""

    model_config = ConfigDict(extra="forbid")

    ptm_site: ProteomicsEvidenceNode
    localized_modified_peptides: tuple[ProteomicsEvidenceNode, ...] = Field(
        default_factory=tuple
    )
    supporting_peptides: tuple[ProteomicsEvidenceNode, ...] = Field(
        default_factory=tuple
    )
    supporting_psms: tuple[ProteomicsEvidenceNode, ...] = Field(default_factory=tuple)
    supporting_spectra: tuple[ProteomicsEvidenceNode, ...] = Field(
        default_factory=tuple
    )
    proteins: tuple[ProteomicsEvidenceNode, ...] = Field(default_factory=tuple)
    support_edges: tuple[ProteomicsEvidenceEdge, ...] = Field(default_factory=tuple)
    support_edge_count: int = Field(..., ge=0)


class RejectedEvidencePathReport(JsonModel):
    """Deterministic rejected-evidence path around one rejected node."""

    model_config = ConfigDict(extra="forbid")

    rejected_node: ProteomicsEvidenceNode
    path_steps: tuple[EvidenceGraphPathStep, ...] = Field(default_factory=tuple)
    path_edges: tuple[ProteomicsEvidenceEdge, ...] = Field(default_factory=tuple)
    step_count: int = Field(..., ge=0)
    edge_count: int = Field(..., ge=0)


class PathwaySupportProteinReport(JsonModel):
    """Structured pathway support query over proteins contributing to one pathway."""

    model_config = ConfigDict(extra="forbid")

    pathway: ProteomicsEvidenceNode
    supporting_proteins: tuple[ProteomicsEvidenceNode, ...] = Field(
        default_factory=tuple
    )
    support_edges: tuple[ProteomicsEvidenceEdge, ...] = Field(default_factory=tuple)
    support_edge_count: int = Field(..., ge=0)


class SampleQcReasonReport(JsonModel):
    """Structured sample QC reasons over linked runs and QC decisions."""

    model_config = ConfigDict(extra="forbid")

    sample: ProteomicsEvidenceNode
    runs: tuple[ProteomicsEvidenceNode, ...] = Field(default_factory=tuple)
    qc_decisions: tuple[ProteomicsEvidenceNode, ...] = Field(default_factory=tuple)
    qc_edges: tuple[ProteomicsEvidenceEdge, ...] = Field(default_factory=tuple)
    run_edge_count: int = Field(..., ge=0)
    qc_edge_count: int = Field(..., ge=0)


def query_protein_evidence_summary(
    graph: EvidenceGraphQuerySurface,
    *,
    protein_id: str,
) -> ProteinEvidenceSummaryReport:
    """Summarize peptide, quantification, and grouping support for one protein."""

    protein = _require_node(graph, ProteomicsEvidenceNodeKind.PROTEIN, protein_id)
    incoming = _incoming_edges(graph, protein.node_id)
    outgoing = _outgoing_edges(graph, protein.node_id)

    mapped_peptides = _unique_nodes(
        _source_nodes_for_relation(
            graph,
            _incoming_edges_for_relation(
                graph,
                protein.node_id,
                ProteomicsEvidenceEdgeKind.PEPTIDE_MAPS_TO_PROTEIN,
            ),
            ProteomicsEvidenceEdgeKind.PEPTIDE_MAPS_TO_PROTEIN,
        )
    )
    quantifying_peptides = _unique_nodes(
        _source_nodes_for_relation(
            graph,
            _incoming_edges_for_relation(
                graph,
                protein.node_id,
                ProteomicsEvidenceEdgeKind.PEPTIDE_QUANTIFIES_PROTEIN,
            ),
            ProteomicsEvidenceEdgeKind.PEPTIDE_QUANTIFIES_PROTEIN,
        )
    )
    protein_groups = _unique_nodes(
        _target_nodes_for_relation(
            graph,
            _outgoing_edges_for_relation(
                graph,
                protein.node_id,
                ProteomicsEvidenceEdgeKind.PROTEIN_MEMBER_OF_GROUP,
            ),
            ProteomicsEvidenceEdgeKind.PROTEIN_MEMBER_OF_GROUP,
        )
    )
    quant_values = _unique_nodes(
        _target_nodes_for_relation(
            graph,
            _outgoing_edges_for_relation(
                graph,
                protein.node_id,
                ProteomicsEvidenceEdgeKind.PROTEIN_QUANTIFIED_BY_QUANT_VALUE,
            ),
            ProteomicsEvidenceEdgeKind.PROTEIN_QUANTIFIED_BY_QUANT_VALUE,
        )
    )
    support_edges = _unique_edges(
        tuple(
            edge
            for edge in incoming + outgoing
            if edge.relation
            in {
                ProteomicsEvidenceEdgeKind.PEPTIDE_MAPS_TO_PROTEIN,
                ProteomicsEvidenceEdgeKind.PEPTIDE_QUANTIFIES_PROTEIN,
                ProteomicsEvidenceEdgeKind.PROTEIN_MEMBER_OF_GROUP,
                ProteomicsEvidenceEdgeKind.PROTEIN_QUANTIFIED_BY_QUANT_VALUE,
            }
        )
    )
    return ProteinEvidenceSummaryReport(
        protein=protein,
        mapped_peptides=mapped_peptides,
        quantifying_peptides=quantifying_peptides,
        protein_groups=protein_groups,
        quant_values=quant_values,
        support_edges=support_edges,
        support_edge_count=len(support_edges),
    )


def render_protein_evidence_summary_tsv(report: ProteinEvidenceSummaryReport) -> str:
    """Render one protein evidence summary as TSV."""

    return _dict_rows_to_tsv(
        [
            {
                "protein_id": report.protein.entity_ref,
                "protein_label": report.protein.label,
                "relation": edge.relation.value,
                "source_node_id": edge.source_node_id,
                "target_node_id": edge.target_node_id,
                "source_row_ref": edge.source_row_ref,
                "confidence": edge.confidence,
                "evidence_type": edge.evidence_type.value,
                "reason": edge.reason,
            }
            for edge in report.support_edges
        ]
    )


def query_peptide_support_chain(
    graph: EvidenceGraphQuerySurface,
    *,
    peptide_id: str,
) -> PeptideSupportChainReport:
    """Trace the deterministic support chain around one peptide node."""

    peptide = _require_node(graph, ProteomicsEvidenceNodeKind.PEPTIDE, peptide_id)
    path = _walk_edges(
        graph,
        seed_node_id=peptide.node_id,
        relation_filter={
            ProteomicsEvidenceEdgeKind.PRECURSOR_SUPPORTS_PEPTIDE,
            ProteomicsEvidenceEdgeKind.PSM_SUPPORTS_PEPTIDE,
            ProteomicsEvidenceEdgeKind.PEPTIDE_HAS_MODIFIED_FORM,
            ProteomicsEvidenceEdgeKind.PEPTIDE_MAPS_TO_PROTEIN,
            ProteomicsEvidenceEdgeKind.PEPTIDE_QUANTIFIES_PROTEIN,
            ProteomicsEvidenceEdgeKind.SPECTRUM_SUPPORTS_PSM,
            ProteomicsEvidenceEdgeKind.SPECTRUM_ASSIGNS_PRECURSOR,
            ProteomicsEvidenceEdgeKind.RUN_ACQUIRED_SPECTRUM,
        },
        max_depth=3,
    )
    return PeptideSupportChainReport(
        peptide=peptide,
        chain_steps=path[0],
        support_edges=path[1],
        step_count=len(path[0]),
        edge_count=len(path[1]),
    )


def render_peptide_support_chain_tsv(report: PeptideSupportChainReport) -> str:
    """Render one peptide support chain as TSV."""

    return _dict_rows_to_tsv(
        [
            {
                "peptide_id": report.peptide.entity_ref,
                "depth": step.depth,
                "node_id": step.node.node_id,
                "entity_type": step.node.entity_type.value,
                "entity_ref": step.node.entity_ref,
                "label": step.node.label,
                "claim_state": step.node.claim_state,
                "trust_class": step.node.trust_class,
            }
            for step in report.chain_steps
        ]
    )


def query_ptm_site_evidence(
    graph: EvidenceGraphQuerySurface,
    *,
    ptm_site_id: str,
) -> PtmSiteEvidenceReport:
    """Summarize localized peptide and protein support for one PTM site."""

    ptm_site = _require_node(graph, ProteomicsEvidenceNodeKind.PTM_SITE, ptm_site_id)
    incoming = _incoming_edges(graph, ptm_site.node_id)
    outgoing = _outgoing_edges(graph, ptm_site.node_id)

    localized_modified_peptides = _unique_nodes(
        _source_nodes_for_relation(
            graph,
            _incoming_edges_for_relation(
                graph,
                ptm_site.node_id,
                ProteomicsEvidenceEdgeKind.MODIFIED_PEPTIDE_LOCALIZES_PTM_SITE,
            ),
            ProteomicsEvidenceEdgeKind.MODIFIED_PEPTIDE_LOCALIZES_PTM_SITE,
        )
    )
    proteins = _unique_nodes(
        _target_nodes_for_relation(
            graph,
            _outgoing_edges_for_relation(
                graph,
                ptm_site.node_id,
                ProteomicsEvidenceEdgeKind.PTM_SITE_BELONGS_TO_PROTEIN,
            ),
            ProteomicsEvidenceEdgeKind.PTM_SITE_BELONGS_TO_PROTEIN,
        )
    )
    supporting_peptides = _unique_nodes(
        tuple(
            _source_node(graph, edge)
            for modified in localized_modified_peptides
            for edge in _incoming_edges(graph, modified.node_id)
            if edge.relation is ProteomicsEvidenceEdgeKind.PEPTIDE_HAS_MODIFIED_FORM
        )
    )
    supporting_psms = _unique_nodes(
        tuple(
            _source_node(graph, edge)
            for peptide in supporting_peptides
            for edge in _incoming_edges(graph, peptide.node_id)
            if edge.relation is ProteomicsEvidenceEdgeKind.PSM_SUPPORTS_PEPTIDE
        )
    )
    supporting_spectra = _unique_nodes(
        tuple(
            _source_node(graph, edge)
            for psm in supporting_psms
            for edge in _incoming_edges(graph, psm.node_id)
            if edge.relation is ProteomicsEvidenceEdgeKind.SPECTRUM_SUPPORTS_PSM
        )
    )
    support_edges = _unique_edges(
        tuple(incoming)
        + tuple(outgoing)
        + tuple(
            edge
            for modified in localized_modified_peptides
            for edge in _incoming_edges(graph, modified.node_id)
            if edge.relation is ProteomicsEvidenceEdgeKind.PEPTIDE_HAS_MODIFIED_FORM
        )
        + tuple(
            edge
            for peptide in supporting_peptides
            for edge in _incoming_edges(graph, peptide.node_id)
            if edge.relation is ProteomicsEvidenceEdgeKind.PSM_SUPPORTS_PEPTIDE
        )
        + tuple(
            edge
            for psm in supporting_psms
            for edge in _incoming_edges(graph, psm.node_id)
            if edge.relation is ProteomicsEvidenceEdgeKind.SPECTRUM_SUPPORTS_PSM
        )
    )
    return PtmSiteEvidenceReport(
        ptm_site=ptm_site,
        localized_modified_peptides=localized_modified_peptides,
        supporting_peptides=supporting_peptides,
        supporting_psms=supporting_psms,
        supporting_spectra=supporting_spectra,
        proteins=proteins,
        support_edges=support_edges,
        support_edge_count=len(support_edges),
    )


def render_ptm_site_evidence_tsv(report: PtmSiteEvidenceReport) -> str:
    """Render one PTM-site evidence report as TSV."""

    return _dict_rows_to_tsv(
        [
            {
                "ptm_site_id": report.ptm_site.entity_ref,
                "relation": edge.relation.value,
                "source_node_id": edge.source_node_id,
                "target_node_id": edge.target_node_id,
                "source_row_ref": edge.source_row_ref,
                "confidence": edge.confidence,
                "evidence_type": edge.evidence_type.value,
                "reason": edge.reason,
            }
            for edge in report.support_edges
        ]
    )


def query_rejected_evidence_path(
    graph: EvidenceGraphQuerySurface,
    *,
    node_id: str,
    max_depth: int = 2,
) -> RejectedEvidencePathReport:
    """Walk the deterministic neighborhood around one rejected evidence node."""

    rejected_node = _require_node_by_id(graph, node_id)
    if rejected_node.claim_state != "rejected":
        raise ValueError(f"node is not rejected evidence: {node_id}")
    path = _walk_edges(
        graph, seed_node_id=node_id, relation_filter=None, max_depth=max_depth
    )
    return RejectedEvidencePathReport(
        rejected_node=rejected_node,
        path_steps=path[0],
        path_edges=path[1],
        step_count=len(path[0]),
        edge_count=len(path[1]),
    )


def render_rejected_evidence_path_tsv(report: RejectedEvidencePathReport) -> str:
    """Render one rejected evidence path as TSV."""

    return _dict_rows_to_tsv(
        [
            {
                "rejected_node_id": report.rejected_node.node_id,
                "depth": step.depth,
                "node_id": step.node.node_id,
                "entity_type": step.node.entity_type.value,
                "entity_ref": step.node.entity_ref,
                "claim_state": step.node.claim_state,
                "trust_class": step.node.trust_class,
            }
            for step in report.path_steps
        ]
    )


def query_pathway_support_proteins(
    graph: EvidenceGraphQuerySurface,
    *,
    pathway_id: str,
) -> PathwaySupportProteinReport:
    """List proteins that support one pathway node."""

    pathway = _require_node(graph, ProteomicsEvidenceNodeKind.PATHWAY, pathway_id)
    incoming = tuple(
        edge
        for edge in _incoming_edges_for_relation(
            graph,
            pathway.node_id,
            ProteomicsEvidenceEdgeKind.PROTEIN_MEMBER_OF_PATHWAY,
        )
    )
    supporting_proteins = _unique_nodes(
        tuple(_source_node(graph, edge) for edge in incoming)
    )
    return PathwaySupportProteinReport(
        pathway=pathway,
        supporting_proteins=supporting_proteins,
        support_edges=_unique_edges(incoming),
        support_edge_count=len(incoming),
    )


def render_pathway_support_proteins_tsv(report: PathwaySupportProteinReport) -> str:
    """Render one pathway support report as TSV."""

    return _dict_rows_to_tsv(
        [
            {
                "pathway_id": report.pathway.entity_ref,
                "protein_id": node.entity_ref,
                "protein_label": node.label,
            }
            for node in report.supporting_proteins
        ]
    )


def query_sample_qc_reasons(
    graph: EvidenceGraphQuerySurface,
    *,
    sample_id: str,
) -> SampleQcReasonReport:
    """List runs and QC decisions connected to one sample."""

    sample = _require_node(graph, ProteomicsEvidenceNodeKind.SAMPLE, sample_id)
    run_edges = tuple(
        edge
        for edge in _outgoing_edges_for_relation(
            graph,
            sample.node_id,
            ProteomicsEvidenceEdgeKind.SAMPLE_CONTAINS_RUN,
        )
    )
    runs = _unique_nodes(tuple(_target_node(graph, edge) for edge in run_edges))
    qc_edges = _unique_edges(
        tuple(
            edge
            for run in runs
            for edge in _outgoing_edges_for_relation(
                graph,
                run.node_id,
                ProteomicsEvidenceEdgeKind.RUN_GOVERNED_BY_QC_DECISION,
            )
        )
    )
    qc_decisions = _unique_nodes(tuple(_target_node(graph, edge) for edge in qc_edges))
    return SampleQcReasonReport(
        sample=sample,
        runs=runs,
        qc_decisions=qc_decisions,
        qc_edges=qc_edges,
        run_edge_count=len(run_edges),
        qc_edge_count=len(qc_edges),
    )


def render_sample_qc_reasons_tsv(report: SampleQcReasonReport) -> str:
    """Render one sample QC reason report as TSV."""

    return _dict_rows_to_tsv(
        [
            {
                "sample_id": report.sample.entity_ref,
                "run_id": _source_node_id_from_qc_edge(report, edge),
                "qc_decision_id": _target_node(
                    graph_nodes=report.qc_decisions, edge=edge
                ).entity_ref,
                "source_row_ref": edge.source_row_ref,
                "confidence": edge.confidence,
                "evidence_type": edge.evidence_type.value,
                "reason": edge.reason,
            }
            for edge in report.qc_edges
        ]
    )


def _source_node_id_from_qc_edge(
    report: SampleQcReasonReport,
    edge: ProteomicsEvidenceEdge,
) -> str:
    return _source_node_from_nodes(report.runs, edge).entity_ref


def _source_node_from_nodes(
    nodes: tuple[ProteomicsEvidenceNode, ...],
    edge: ProteomicsEvidenceEdge,
) -> ProteomicsEvidenceNode:
    node_by_id = {node.node_id: node for node in nodes}
    return node_by_id[edge.source_node_id]


def _target_node(
    graph: EvidenceGraphQuerySurface | None = None,
    edge: ProteomicsEvidenceEdge | None = None,
    *,
    graph_nodes: tuple[ProteomicsEvidenceNode, ...] | None = None,
) -> ProteomicsEvidenceNode:
    if edge is None:
        raise ValueError("edge is required")
    if graph is not None:
        return _require_node_by_id(graph, edge.target_node_id)
    if graph_nodes is None:
        raise ValueError("graph or graph_nodes is required")
    node_by_id = {node.node_id: node for node in graph_nodes}
    return node_by_id[edge.target_node_id]


def _source_node(
    graph: EvidenceGraphQuerySurface,
    edge: ProteomicsEvidenceEdge,
) -> ProteomicsEvidenceNode:
    return _require_node_by_id(graph, edge.source_node_id)


def _target_node_for_edge(
    graph: EvidenceGraphQuerySurface,
    edge: ProteomicsEvidenceEdge,
) -> ProteomicsEvidenceNode:
    return _require_node_by_id(graph, edge.target_node_id)


def _source_nodes_for_relation(
    graph: EvidenceGraphQuerySurface,
    edges: tuple[ProteomicsEvidenceEdge, ...],
    relation: ProteomicsEvidenceEdgeKind,
) -> tuple[ProteomicsEvidenceNode, ...]:
    return tuple(
        _source_node(graph, edge) for edge in edges if edge.relation is relation
    )


def _target_nodes_for_relation(
    graph: EvidenceGraphQuerySurface,
    edges: tuple[ProteomicsEvidenceEdge, ...],
    relation: ProteomicsEvidenceEdgeKind,
) -> tuple[ProteomicsEvidenceNode, ...]:
    return tuple(
        _target_node_for_edge(graph, edge)
        for edge in edges
        if edge.relation is relation
    )


def _walk_edges(
    graph: EvidenceGraphQuerySurface,
    *,
    seed_node_id: str,
    relation_filter: set[ProteomicsEvidenceEdgeKind] | None,
    max_depth: int,
) -> tuple[tuple[EvidenceGraphPathStep, ...], tuple[ProteomicsEvidenceEdge, ...]]:
    queue: deque[tuple[str, int]] = deque([(seed_node_id, 0)])
    depths: dict[str, int] = {seed_node_id: 0}
    collected_edges: list[ProteomicsEvidenceEdge] = []

    while queue:
        node_id, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for edge in _adjacent_edges(graph, node_id):
            if relation_filter is not None and edge.relation not in relation_filter:
                continue
            collected_edges.append(edge)
            neighbor_id = (
                edge.target_node_id
                if edge.source_node_id == node_id
                else edge.source_node_id
            )
            next_depth = depth + 1
            if neighbor_id not in depths or next_depth < depths[neighbor_id]:
                depths[neighbor_id] = next_depth
                queue.append((neighbor_id, next_depth))

    steps = tuple(
        sorted(
            (
                EvidenceGraphPathStep(
                    depth=depth, node=_require_node_by_id(graph, node_id)
                )
                for node_id, depth in depths.items()
            ),
            key=lambda step: (step.depth, step.node.node_id),
        )
    )
    return steps, _unique_edges(tuple(collected_edges))


def _adjacent_edges(
    graph: EvidenceGraphQuerySurface,
    node_id: str,
) -> tuple[ProteomicsEvidenceEdge, ...]:
    if isinstance(graph, LazyProteomicsEvidenceGraph):
        return graph.adjacent_edges(node_id)
    return tuple(
        edge
        for edge in graph.edges
        if edge.source_node_id == node_id or edge.target_node_id == node_id
    )


def _incoming_edges(
    graph: EvidenceGraphQuerySurface,
    node_id: str,
) -> tuple[ProteomicsEvidenceEdge, ...]:
    if isinstance(graph, LazyProteomicsEvidenceGraph):
        return graph.incoming_edges(node_id)
    return tuple(edge for edge in graph.edges if edge.target_node_id == node_id)


def _incoming_edges_for_relation(
    graph: EvidenceGraphQuerySurface,
    node_id: str,
    relation: ProteomicsEvidenceEdgeKind,
) -> tuple[ProteomicsEvidenceEdge, ...]:
    if isinstance(graph, LazyProteomicsEvidenceGraph):
        return graph.incoming_edges_for_relation(node_id, relation)
    return tuple(
        edge
        for edge in graph.edges
        if edge.target_node_id == node_id and edge.relation is relation
    )


def _outgoing_edges(
    graph: EvidenceGraphQuerySurface,
    node_id: str,
) -> tuple[ProteomicsEvidenceEdge, ...]:
    if isinstance(graph, LazyProteomicsEvidenceGraph):
        return graph.outgoing_edges(node_id)
    return tuple(edge for edge in graph.edges if edge.source_node_id == node_id)


def _outgoing_edges_for_relation(
    graph: EvidenceGraphQuerySurface,
    node_id: str,
    relation: ProteomicsEvidenceEdgeKind,
) -> tuple[ProteomicsEvidenceEdge, ...]:
    if isinstance(graph, LazyProteomicsEvidenceGraph):
        return graph.outgoing_edges_for_relation(node_id, relation)
    return tuple(
        edge
        for edge in graph.edges
        if edge.source_node_id == node_id and edge.relation is relation
    )


def _require_node(
    graph: EvidenceGraphQuerySurface,
    kind: ProteomicsEvidenceNodeKind,
    entity_ref: str,
) -> ProteomicsEvidenceNode:
    if isinstance(graph, LazyProteomicsEvidenceGraph):
        return graph.require_node(kind, entity_ref)
    for node in graph.nodes:
        if node.entity_type is kind and node.entity_ref == entity_ref:
            return node
    raise ValueError(f"graph node is missing: {kind.value}:{entity_ref}")


def _require_node_by_id(
    graph: EvidenceGraphQuerySurface,
    node_id: str,
) -> ProteomicsEvidenceNode:
    if isinstance(graph, LazyProteomicsEvidenceGraph):
        return graph.require_node_by_id(node_id)
    for node in graph.nodes:
        if node.node_id == node_id:
            return node
    raise ValueError(f"graph node is missing by node_id: {node_id}")


def _unique_nodes(
    nodes: tuple[ProteomicsEvidenceNode, ...],
) -> tuple[ProteomicsEvidenceNode, ...]:
    return tuple(
        sorted(
            {node.node_id: node for node in nodes}.values(),
            key=lambda node: node.node_id,
        )
    )


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
        buffer, fieldnames=fieldnames, delimiter="\t", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()
