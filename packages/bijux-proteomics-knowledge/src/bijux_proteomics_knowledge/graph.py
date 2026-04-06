# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Evidence graph models for explainable decision tracing."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_knowledge.claims import EvidenceClaim
from bijux_proteomics_knowledge.evidence import EvidenceBundle
from bijux_proteomics_knowledge.serialization import JsonModel


class EvidenceNodeType(StrEnum):
    """Supported node kinds in the evidence graph."""

    TARGET = "target"
    CLAIM = "claim"
    EVIDENCE = "evidence"
    DECISION = "decision"


class EvidenceNode(JsonModel):
    """Node in an evidence graph."""

    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(..., min_length=1, description="Stable node identifier.")
    node_type: EvidenceNodeType = Field(..., description="Type of graph node.")
    label: str = Field(..., min_length=1, description="Human-readable node label.")


class EvidenceEdge(JsonModel):
    """Directed relation between graph nodes."""

    model_config = ConfigDict(extra="forbid")

    source_node_id: str = Field(..., min_length=1, description="Source node identifier.")
    target_node_id: str = Field(..., min_length=1, description="Target node identifier.")
    relation: str = Field(..., min_length=1, description="Relation label.")


class EvidenceGraph(JsonModel):
    """Graph representation of evidence and decision links."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1, description="Stable bundle identifier.")
    target_id: str = Field(..., min_length=1, description="Target identifier.")
    nodes: list[EvidenceNode] = Field(default_factory=list, description="Graph nodes.")
    edges: list[EvidenceEdge] = Field(default_factory=list, description="Graph edges.")


def build_evidence_graph(
    bundle: EvidenceBundle,
    claims: list[EvidenceClaim] | None = None,
) -> EvidenceGraph:
    """Build a graph from bundle contents and optional claim lineage."""
    target_node = EvidenceNode(
        node_id=f"target:{bundle.target_id}",
        node_type=EvidenceNodeType.TARGET,
        label=bundle.target_id,
    )
    nodes = [target_node]
    edges: list[EvidenceEdge] = []
    claims = claims or []

    for claim in claims:
        claim_node = EvidenceNode(
            node_id=f"claim:{claim.claim_id}",
            node_type=EvidenceNodeType.CLAIM,
            label=claim.statement,
        )
        nodes.append(claim_node)
        edges.append(
            EvidenceEdge(
                source_node_id=target_node.node_id,
                target_node_id=claim_node.node_id,
                relation="frames",
            )
        )
        for decision_tag in {
            decision_tag
            for record in bundle.records
            if record.evidence_id in claim.evidence_ids
            for decision_tag in record.decision_tags
        }:
            decision_node_id = f"decision:{decision_tag}"
            if all(node.node_id != decision_node_id for node in nodes):
                nodes.append(
                    EvidenceNode(
                        node_id=decision_node_id,
                        node_type=EvidenceNodeType.DECISION,
                        label=decision_tag,
                    )
                )
            edges.append(
                EvidenceEdge(
                    source_node_id=claim_node.node_id,
                    target_node_id=decision_node_id,
                    relation="supports_decision",
                )
            )

    for record in bundle.records:
        evidence_node = EvidenceNode(
            node_id=f"evidence:{record.evidence_id}",
            node_type=EvidenceNodeType.EVIDENCE,
            label=record.title,
        )
        nodes.append(evidence_node)
        edges.append(
            EvidenceEdge(
                source_node_id=target_node.node_id,
                target_node_id=evidence_node.node_id,
                relation="supported_by",
            )
        )
        for claim in claims:
            if record.evidence_id in claim.evidence_ids:
                edges.append(
                    EvidenceEdge(
                        source_node_id=f"claim:{claim.claim_id}",
                        target_node_id=evidence_node.node_id,
                        relation="supported_by_evidence",
                    )
                )
        for decision_tag in record.decision_tags:
            decision_node_id = f"decision:{decision_tag}"
            if all(node.node_id != decision_node_id for node in nodes):
                nodes.append(
                    EvidenceNode(
                        node_id=decision_node_id,
                        node_type=EvidenceNodeType.DECISION,
                        label=decision_tag,
                    )
                )
            edges.append(
                EvidenceEdge(
                    source_node_id=evidence_node.node_id,
                    target_node_id=decision_node_id,
                    relation="informs",
                )
            )
        for upstream_id in record.derived_from:
            edges.append(
                EvidenceEdge(
                    source_node_id=f"evidence:{upstream_id}",
                    target_node_id=evidence_node.node_id,
                    relation="derived_into",
                )
            )

    return EvidenceGraph(
        bundle_id=bundle.bundle_id,
        target_id=bundle.target_id,
        nodes=nodes,
        edges=edges,
    )
