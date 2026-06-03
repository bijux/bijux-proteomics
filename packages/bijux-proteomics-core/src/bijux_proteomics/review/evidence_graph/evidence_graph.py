# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical proteomics evidence graph owner for review and trust surfaces."""

from __future__ import annotations

from enum import StrEnum
from typing import TypedDict, Unpack

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class ProteomicsEvidenceNodeKind(StrEnum):
    """Stable node kinds admitted into the canonical proteomics evidence graph."""

    CANDIDATE = "candidate"
    SAMPLE = "sample"
    RUN = "run"
    SPECTRUM = "spectrum"
    PRECURSOR = "precursor"
    PEPTIDE = "peptide"
    MODIFIED_PEPTIDE = "modified_peptide"
    PSM = "psm"
    PROTEIN = "protein"
    PROTEIN_GROUP = "protein_group"
    PTM_SITE = "ptm_site"
    TRANSITION = "transition"
    QUANT_VALUE = "quant_value"
    STATISTICAL_RESULT = "statistical_result"
    PATHWAY = "pathway"
    QC_DECISION = "qc_decision"


class ProteomicsEvidenceEdgeKind(StrEnum):
    """Stable typed relations admitted into the canonical proteomics evidence graph."""

    CANDIDATE_SUPPORTS_PROTEIN = "candidate_supports_protein"
    SAMPLE_CONTAINS_RUN = "sample_contains_run"
    RUN_ACQUIRED_SPECTRUM = "run_acquired_spectrum"
    SPECTRUM_ASSIGNS_PRECURSOR = "spectrum_assigns_precursor"
    SPECTRUM_SUPPORTS_PSM = "spectrum_supports_psm"
    PRECURSOR_SUPPORTS_PEPTIDE = "precursor_supports_peptide"
    PSM_SUPPORTS_PEPTIDE = "psm_supports_peptide"
    PEPTIDE_HAS_MODIFIED_FORM = "peptide_has_modified_form"
    MODIFIED_PEPTIDE_LOCALIZES_PTM_SITE = "modified_peptide_localizes_ptm_site"
    PEPTIDE_MAPS_TO_PROTEIN = "peptide_maps_to_protein"
    PEPTIDE_QUANTIFIES_PROTEIN = "peptide_quantifies_protein"
    PTM_SITE_BELONGS_TO_PROTEIN = "ptm_site_belongs_to_protein"
    PROTEIN_MEMBER_OF_GROUP = "protein_member_of_group"
    PRECURSOR_SUPPORTS_TRANSITION = "precursor_supports_transition"
    PROTEIN_QUANTIFIED_BY_QUANT_VALUE = "protein_quantified_by_quant_value"
    PEPTIDE_SUPPORTS_STATISTICAL_RESULT = "peptide_supports_statistical_result"
    QUANT_VALUE_SUPPORTS_STATISTICAL_RESULT = "quant_value_supports_statistical_result"
    PROTEIN_SUPPORTS_STATISTICAL_RESULT = "protein_supports_statistical_result"
    PTM_SITE_SUPPORTS_STATISTICAL_RESULT = "ptm_site_supports_statistical_result"
    PATHWAY_SUPPORTS_STATISTICAL_RESULT = "pathway_supports_statistical_result"
    PROTEIN_MEMBER_OF_PATHWAY = "protein_member_of_pathway"
    RUN_GOVERNED_BY_QC_DECISION = "run_governed_by_qc_decision"


class ProteomicsEvidenceType(StrEnum):
    """Evidence classes attached to typed graph edges."""

    INFERENCE = "inference"
    SPECTRUM_ASSIGNMENT = "spectrum_assignment"
    PRECURSOR_ASSIGNMENT = "precursor_assignment"
    SEQUENCE_MAPPING = "sequence_mapping"
    PTM_LOCALIZATION = "ptm_localization"
    QUANTIFICATION = "quantification"
    ANNOTATION = "annotation"
    QC = "qc"
    WORKFLOW_CONTEXT = "workflow_context"
    TARGETED_ASSAY = "targeted_assay"


class ProteomicsEvidenceContextRef(JsonModel):
    """One stable context reference attached to a graph node."""

    model_config = ConfigDict(extra="forbid")

    entity_type: ProteomicsEvidenceNodeKind
    entity_ref: str = Field(..., min_length=1)


class _EnsureNodeKwargs(TypedDict, total=False):
    label: str | None
    claim_state: str
    trust_class: str
    contradiction_ids: tuple[str, ...]
    context_refs: tuple[ProteomicsEvidenceContextRef, ...]


class ProteomicsEvidenceNode(JsonModel):
    """One canonical node in the proteomics evidence graph."""

    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(..., min_length=1)
    entity_type: ProteomicsEvidenceNodeKind
    entity_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    claim_state: str = Field(default="observed", min_length=1)
    trust_class: str = Field(default="unreviewed", min_length=1)
    contradiction_ids: tuple[str, ...] = Field(default_factory=tuple)
    context_refs: tuple[ProteomicsEvidenceContextRef, ...] = Field(default_factory=tuple)


class ProteomicsEvidenceEdge(JsonModel):
    """One directed relation between canonical evidence-graph nodes."""

    model_config = ConfigDict(extra="forbid")

    source_node_id: str = Field(..., min_length=1)
    target_node_id: str = Field(..., min_length=1)
    relation: ProteomicsEvidenceEdgeKind
    source_row_ref: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_type: ProteomicsEvidenceType
    reason: str = Field(..., min_length=1)
    support_count: int = Field(default=1, ge=1)


class ProteomicsEvidenceGraphSummary(JsonModel):
    """Deterministic summary of one proteomics evidence graph."""

    model_config = ConfigDict(extra="forbid")

    node_count: int = Field(..., ge=0)
    edge_count: int = Field(..., ge=0)
    contradiction_node_count: int = Field(..., ge=0)
    node_kind_counts: dict[str, int] = Field(default_factory=dict)
    edge_kind_counts: dict[str, int] = Field(default_factory=dict)
    evidence_type_counts: dict[str, int] = Field(default_factory=dict)


class ProteomicsEvidenceGraph(JsonModel):
    """Canonical proteomics evidence graph over review-grade scientific entities."""

    model_config = ConfigDict(extra="forbid")

    nodes: tuple[ProteomicsEvidenceNode, ...] = Field(default_factory=tuple)
    edges: tuple[ProteomicsEvidenceEdge, ...] = Field(default_factory=tuple)
    summary: ProteomicsEvidenceGraphSummary


def build_proteomics_evidence_graph(
    nodes: tuple[ProteomicsEvidenceNode, ...],
    edges: tuple[ProteomicsEvidenceEdge, ...],
) -> ProteomicsEvidenceGraph:
    """Build one canonical proteomics evidence graph with endpoint validation."""

    node_ids = {node.node_id for node in nodes}
    for edge in edges:
        if edge.source_node_id not in node_ids:
            raise ValueError(
                f"edge source node is missing from graph: {edge.source_node_id}"
            )
        if edge.target_node_id not in node_ids:
            raise ValueError(
                f"edge target node is missing from graph: {edge.target_node_id}"
            )

    sorted_nodes = tuple(sorted(nodes, key=lambda node: node.node_id))
    sorted_edges = tuple(
        sorted(
            edges,
            key=lambda edge: (
                edge.source_node_id,
                edge.target_node_id,
                edge.relation,
            ),
        )
    )
    kind_counts: dict[str, int] = {}
    edge_kind_counts: dict[str, int] = {}
    evidence_type_counts: dict[str, int] = {}
    for node in sorted_nodes:
        kind_counts[node.entity_type.value] = kind_counts.get(node.entity_type.value, 0) + 1
    for edge in sorted_edges:
        edge_kind_counts[edge.relation.value] = edge_kind_counts.get(edge.relation.value, 0) + 1
        evidence_type_counts[edge.evidence_type.value] = (
            evidence_type_counts.get(edge.evidence_type.value, 0) + 1
        )

    summary = ProteomicsEvidenceGraphSummary(
        node_count=len(sorted_nodes),
        edge_count=len(sorted_edges),
        contradiction_node_count=sum(bool(node.contradiction_ids) for node in sorted_nodes),
        node_kind_counts=dict(sorted(kind_counts.items())),
        edge_kind_counts=dict(sorted(edge_kind_counts.items())),
        evidence_type_counts=dict(sorted(evidence_type_counts.items())),
    )
    return ProteomicsEvidenceGraph(
        nodes=sorted_nodes,
        edges=sorted_edges,
        summary=summary,
    )


class ProteomicsEvidenceGraphBuilder:
    """Builder that canonicalizes nodes and preserves typed evidentiary edges."""

    def __init__(self) -> None:
        self._nodes_by_id: dict[str, ProteomicsEvidenceNode] = {}
        self._edges: list[ProteomicsEvidenceEdge] = []

    def add_node(
        self,
        node: ProteomicsEvidenceNode,
    ) -> ProteomicsEvidenceNode:
        """Add one canonical node or reject conflicting duplicate definitions."""

        existing = self._nodes_by_id.get(node.node_id)
        if existing is None:
            self._nodes_by_id[node.node_id] = node
            return node
        if existing != node:
            raise ValueError(f"conflicting node definition for {node.node_id}")
        return existing

    def ensure_node(
        self,
        entity_type: ProteomicsEvidenceNodeKind,
        entity_ref: str,
        *,
        label: str | None = None,
        claim_state: str = "observed",
        trust_class: str = "unreviewed",
        contradiction_ids: tuple[str, ...] = (),
        context_refs: tuple[ProteomicsEvidenceContextRef, ...] = (),
    ) -> ProteomicsEvidenceNode:
        """Add or return one canonical node with a stable graph-local identifier."""

        return self.add_node(
            ProteomicsEvidenceNode(
                node_id=f"{entity_type.value}:{entity_ref}",
                entity_type=entity_type,
                entity_ref=entity_ref,
                label=label or entity_ref,
                claim_state=claim_state,
                trust_class=trust_class,
                contradiction_ids=contradiction_ids,
                context_refs=context_refs,
            )
        )

    def add_edge(
        self,
        source_node_id: str,
        target_node_id: str,
        relation: ProteomicsEvidenceEdgeKind,
        *,
        source_row_ref: str,
        confidence: float,
        evidence_type: ProteomicsEvidenceType,
        reason: str,
        support_count: int = 1,
    ) -> None:
        """Add one typed evidentiary relation between existing nodes."""

        if source_node_id not in self._nodes_by_id:
            raise ValueError(f"source node is missing from builder: {source_node_id}")
        if target_node_id not in self._nodes_by_id:
            raise ValueError(f"target node is missing from builder: {target_node_id}")
        self._edges.append(
            ProteomicsEvidenceEdge(
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                relation=relation,
                source_row_ref=source_row_ref,
                confidence=confidence,
                evidence_type=evidence_type,
                reason=reason,
                support_count=support_count,
            )
        )

    def add_sample_contains_run(
        self,
        sample_node_id: str,
        run_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            sample_node_id,
            run_node_id,
            ProteomicsEvidenceEdgeKind.SAMPLE_CONTAINS_RUN,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.WORKFLOW_CONTEXT,
            reason=reason,
        )

    def add_run_acquired_spectrum(
        self,
        run_node_id: str,
        spectrum_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            run_node_id,
            spectrum_node_id,
            ProteomicsEvidenceEdgeKind.RUN_ACQUIRED_SPECTRUM,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.WORKFLOW_CONTEXT,
            reason=reason,
        )

    def add_spectrum_assigns_precursor(
        self,
        spectrum_node_id: str,
        precursor_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            spectrum_node_id,
            precursor_node_id,
            ProteomicsEvidenceEdgeKind.SPECTRUM_ASSIGNS_PRECURSOR,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.PRECURSOR_ASSIGNMENT,
            reason=reason,
        )

    def add_spectrum_supports_psm(
        self,
        spectrum_node_id: str,
        psm_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            spectrum_node_id,
            psm_node_id,
            ProteomicsEvidenceEdgeKind.SPECTRUM_SUPPORTS_PSM,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.SPECTRUM_ASSIGNMENT,
            reason=reason,
        )

    def add_precursor_supports_peptide(
        self,
        precursor_node_id: str,
        peptide_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            precursor_node_id,
            peptide_node_id,
            ProteomicsEvidenceEdgeKind.PRECURSOR_SUPPORTS_PEPTIDE,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.PRECURSOR_ASSIGNMENT,
            reason=reason,
        )

    def add_psm_supports_peptide(
        self,
        psm_node_id: str,
        peptide_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            psm_node_id,
            peptide_node_id,
            ProteomicsEvidenceEdgeKind.PSM_SUPPORTS_PEPTIDE,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.SPECTRUM_ASSIGNMENT,
            reason=reason,
        )

    def add_peptide_has_modified_form(
        self,
        peptide_node_id: str,
        modified_peptide_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            peptide_node_id,
            modified_peptide_node_id,
            ProteomicsEvidenceEdgeKind.PEPTIDE_HAS_MODIFIED_FORM,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.INFERENCE,
            reason=reason,
        )

    def add_modified_peptide_localizes_ptm_site(
        self,
        modified_peptide_node_id: str,
        ptm_site_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            modified_peptide_node_id,
            ptm_site_node_id,
            ProteomicsEvidenceEdgeKind.MODIFIED_PEPTIDE_LOCALIZES_PTM_SITE,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.PTM_LOCALIZATION,
            reason=reason,
        )

    def add_peptide_maps_to_protein(
        self,
        peptide_node_id: str,
        protein_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            peptide_node_id,
            protein_node_id,
            ProteomicsEvidenceEdgeKind.PEPTIDE_MAPS_TO_PROTEIN,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.SEQUENCE_MAPPING,
            reason=reason,
        )

    def add_peptide_quantifies_protein(
        self,
        peptide_node_id: str,
        protein_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            peptide_node_id,
            protein_node_id,
            ProteomicsEvidenceEdgeKind.PEPTIDE_QUANTIFIES_PROTEIN,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.QUANTIFICATION,
            reason=reason,
        )

    def add_ptm_site_belongs_to_protein(
        self,
        ptm_site_node_id: str,
        protein_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            ptm_site_node_id,
            protein_node_id,
            ProteomicsEvidenceEdgeKind.PTM_SITE_BELONGS_TO_PROTEIN,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.SEQUENCE_MAPPING,
            reason=reason,
        )

    def add_protein_member_of_group(
        self,
        protein_node_id: str,
        protein_group_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            protein_node_id,
            protein_group_node_id,
            ProteomicsEvidenceEdgeKind.PROTEIN_MEMBER_OF_GROUP,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.INFERENCE,
            reason=reason,
        )

    def add_precursor_supports_transition(
        self,
        precursor_node_id: str,
        transition_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            precursor_node_id,
            transition_node_id,
            ProteomicsEvidenceEdgeKind.PRECURSOR_SUPPORTS_TRANSITION,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.TARGETED_ASSAY,
            reason=reason,
        )

    def add_protein_quantified_by_quant_value(
        self,
        protein_node_id: str,
        quant_value_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            protein_node_id,
            quant_value_node_id,
            ProteomicsEvidenceEdgeKind.PROTEIN_QUANTIFIED_BY_QUANT_VALUE,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.QUANTIFICATION,
            reason=reason,
        )

    def add_peptide_supports_statistical_result(
        self,
        peptide_node_id: str,
        statistical_result_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            peptide_node_id,
            statistical_result_node_id,
            ProteomicsEvidenceEdgeKind.PEPTIDE_SUPPORTS_STATISTICAL_RESULT,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.INFERENCE,
            reason=reason,
        )

    def add_protein_member_of_pathway(
        self,
        protein_node_id: str,
        pathway_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            protein_node_id,
            pathway_node_id,
            ProteomicsEvidenceEdgeKind.PROTEIN_MEMBER_OF_PATHWAY,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.ANNOTATION,
            reason=reason,
        )

    def add_quant_value_supports_statistical_result(
        self,
        quant_value_node_id: str,
        statistical_result_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            quant_value_node_id,
            statistical_result_node_id,
            ProteomicsEvidenceEdgeKind.QUANT_VALUE_SUPPORTS_STATISTICAL_RESULT,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.QUANTIFICATION,
            reason=reason,
        )

    def add_protein_supports_statistical_result(
        self,
        protein_node_id: str,
        statistical_result_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            protein_node_id,
            statistical_result_node_id,
            ProteomicsEvidenceEdgeKind.PROTEIN_SUPPORTS_STATISTICAL_RESULT,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.INFERENCE,
            reason=reason,
        )

    def add_ptm_site_supports_statistical_result(
        self,
        ptm_site_node_id: str,
        statistical_result_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            ptm_site_node_id,
            statistical_result_node_id,
            ProteomicsEvidenceEdgeKind.PTM_SITE_SUPPORTS_STATISTICAL_RESULT,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.INFERENCE,
            reason=reason,
        )

    def add_pathway_supports_statistical_result(
        self,
        pathway_node_id: str,
        statistical_result_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            pathway_node_id,
            statistical_result_node_id,
            ProteomicsEvidenceEdgeKind.PATHWAY_SUPPORTS_STATISTICAL_RESULT,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.INFERENCE,
            reason=reason,
        )

    def add_run_governed_by_qc_decision(
        self,
        run_node_id: str,
        qc_decision_node_id: str,
        *,
        source_row_ref: str,
        confidence: float,
        reason: str,
    ) -> None:
        self.add_edge(
            run_node_id,
            qc_decision_node_id,
            ProteomicsEvidenceEdgeKind.RUN_GOVERNED_BY_QC_DECISION,
            source_row_ref=source_row_ref,
            confidence=confidence,
            evidence_type=ProteomicsEvidenceType.QC,
            reason=reason,
        )

    def add_candidate(
        self, candidate_id: str, **kwargs: Unpack[_EnsureNodeKwargs]
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.CANDIDATE, candidate_id, **kwargs)

    def add_sample(
        self, sample_id: str, **kwargs: Unpack[_EnsureNodeKwargs]
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.SAMPLE, sample_id, **kwargs)

    def add_run(
        self, run_id: str, **kwargs: Unpack[_EnsureNodeKwargs]
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.RUN, run_id, **kwargs)

    def add_spectrum(
        self, spectrum_id: str, **kwargs: Unpack[_EnsureNodeKwargs]
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.SPECTRUM, spectrum_id, **kwargs)

    def add_precursor(
        self, precursor_id: str, **kwargs: Unpack[_EnsureNodeKwargs]
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.PRECURSOR, precursor_id, **kwargs)

    def add_peptide(
        self, peptide_id: str, **kwargs: Unpack[_EnsureNodeKwargs]
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.PEPTIDE, peptide_id, **kwargs)

    def add_modified_peptide(
        self, modified_peptide_id: str, **kwargs: Unpack[_EnsureNodeKwargs]
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(
            ProteomicsEvidenceNodeKind.MODIFIED_PEPTIDE,
            modified_peptide_id,
            **kwargs,
        )

    def add_psm(
        self, psm_id: str, **kwargs: Unpack[_EnsureNodeKwargs]
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.PSM, psm_id, **kwargs)

    def add_protein(
        self, protein_id: str, **kwargs: Unpack[_EnsureNodeKwargs]
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.PROTEIN, protein_id, **kwargs)

    def add_protein_group(
        self, protein_group_id: str, **kwargs: Unpack[_EnsureNodeKwargs]
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(
            ProteomicsEvidenceNodeKind.PROTEIN_GROUP,
            protein_group_id,
            **kwargs,
        )

    def add_ptm_site(
        self, ptm_site_id: str, **kwargs: Unpack[_EnsureNodeKwargs]
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.PTM_SITE, ptm_site_id, **kwargs)

    def add_transition(
        self, transition_id: str, **kwargs: Unpack[_EnsureNodeKwargs]
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.TRANSITION, transition_id, **kwargs)

    def add_quant_value(
        self, quant_value_id: str, **kwargs: Unpack[_EnsureNodeKwargs]
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(
            ProteomicsEvidenceNodeKind.QUANT_VALUE,
            quant_value_id,
            **kwargs,
        )

    def add_statistical_result(
        self, statistical_result_id: str, **kwargs: Unpack[_EnsureNodeKwargs]
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(
            ProteomicsEvidenceNodeKind.STATISTICAL_RESULT,
            statistical_result_id,
            **kwargs,
        )

    def add_pathway(
        self, pathway_id: str, **kwargs: Unpack[_EnsureNodeKwargs]
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.PATHWAY, pathway_id, **kwargs)

    def add_qc_decision(
        self, qc_decision_id: str, **kwargs: Unpack[_EnsureNodeKwargs]
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(
            ProteomicsEvidenceNodeKind.QC_DECISION,
            qc_decision_id,
            **kwargs,
        )

    def build(self) -> ProteomicsEvidenceGraph:
        """Build one validated canonical graph from the accumulated nodes and edges."""

        return build_proteomics_evidence_graph(
            tuple(self._nodes_by_id.values()),
            tuple(self._edges),
        )
