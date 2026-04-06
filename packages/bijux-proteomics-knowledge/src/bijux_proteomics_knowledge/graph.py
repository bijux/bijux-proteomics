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
    ASSAY = "assay"
    ASSUMPTION = "assumption"
    QUESTION = "question"
    LIABILITY = "liability"


class EvidenceNode(JsonModel):
    """Node in an evidence graph."""

    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(..., min_length=1, description="Stable node identifier.")
    node_type: EvidenceNodeType = Field(..., description="Type of graph node.")
    label: str = Field(..., min_length=1, description="Human-readable node label.")


class EvidenceEdge(JsonModel):
    """Directed relation between graph nodes."""

    model_config = ConfigDict(extra="forbid")

    source_node_id: str = Field(
        ..., min_length=1, description="Source node identifier."
    )
    target_node_id: str = Field(
        ..., min_length=1, description="Target node identifier."
    )
    relation: str = Field(..., min_length=1, description="Relation label.")


class EvidenceGraph(JsonModel):
    """Graph representation of evidence and decision links."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1, description="Stable bundle identifier.")
    target_id: str = Field(..., min_length=1, description="Target identifier.")
    nodes: list[EvidenceNode] = Field(default_factory=list, description="Graph nodes.")
    edges: list[EvidenceEdge] = Field(default_factory=list, description="Graph edges.")


class UnresolvedQuestion(JsonModel):
    """Question that remains unresolved in the current evidence state."""

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(
        ..., min_length=1, description="Stable question identifier."
    )
    text: str = Field(..., min_length=1, description="Unresolved scientific question.")
    related_decision_tags: list[str] = Field(
        default_factory=list, description="Decision tags impacted by the question."
    )


class LiabilityNodeInput(JsonModel):
    """Liability descriptor that should appear in the evidence graph."""

    model_config = ConfigDict(extra="forbid")

    liability_id: str = Field(
        ..., min_length=1, description="Stable liability identifier."
    )
    summary: str = Field(..., min_length=1, description="Liability summary.")
    related_decision_tags: list[str] = Field(
        default_factory=list, description="Decision tags affected by the liability."
    )


class DecisionTracePath(JsonModel):
    """Path trace from a decision node to supporting graph nodes."""

    model_config = ConfigDict(extra="forbid")

    decision_tag: str = Field(..., min_length=1, description="Decision tag origin.")
    terminal_node_id: str = Field(
        ..., min_length=1, description="Terminal node reached by the trace."
    )
    path: list[str] = Field(
        default_factory=list,
        description="Ordered node IDs from decision to terminal node.",
    )


class GraphValidationIssue(JsonModel):
    """Validation issue for graph structural integrity."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1, description="Stable graph issue code.")
    message: str = Field(
        ..., min_length=1, description="Human-readable issue description."
    )


def build_evidence_graph(
    bundle: EvidenceBundle,
    claims: list[EvidenceClaim] | None = None,
    unresolved_questions: list[UnresolvedQuestion] | None = None,
    liabilities: list[LiabilityNodeInput] | None = None,
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
    unresolved_questions = unresolved_questions or []
    liabilities = liabilities or []

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
        for assumption_index, assumption in enumerate(claim.assumptions):
            assumption_node_id = f"assumption:{claim.claim_id}:{assumption_index + 1}"
            nodes.append(
                EvidenceNode(
                    node_id=assumption_node_id,
                    node_type=EvidenceNodeType.ASSUMPTION,
                    label=assumption,
                )
            )
            edges.append(
                EvidenceEdge(
                    source_node_id=claim_node.node_id,
                    target_node_id=assumption_node_id,
                    relation="assumes",
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
            if record.evidence_id in claim.contradicting_evidence_ids:
                edges.append(
                    EvidenceEdge(
                        source_node_id=f"claim:{claim.claim_id}",
                        target_node_id=evidence_node.node_id,
                        relation="contradicted_by_evidence",
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
            if record.kind.value == "assay":
                assay_node_id = f"assay:{record.evidence_id}"
                if all(node.node_id != assay_node_id for node in nodes):
                    nodes.append(
                        EvidenceNode(
                            node_id=assay_node_id,
                            node_type=EvidenceNodeType.ASSAY,
                            label=record.title,
                        )
                    )
                edges.append(
                    EvidenceEdge(
                        source_node_id=assay_node_id,
                        target_node_id=decision_node_id,
                        relation="tests",
                    )
                )
        edges.extend(
            EvidenceEdge(
                source_node_id=f"evidence:{upstream_id}",
                target_node_id=evidence_node.node_id,
                relation="derived_into",
            )
            for upstream_id in record.derived_from
        )
    for question in unresolved_questions:
        question_node_id = f"question:{question.question_id}"
        nodes.append(
            EvidenceNode(
                node_id=question_node_id,
                node_type=EvidenceNodeType.QUESTION,
                label=question.text,
            )
        )
        for decision_tag in question.related_decision_tags:
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
                    source_node_id=question_node_id,
                    target_node_id=decision_node_id,
                    relation="blocks",
                )
            )
    for liability in liabilities:
        liability_node_id = f"liability:{liability.liability_id}"
        nodes.append(
            EvidenceNode(
                node_id=liability_node_id,
                node_type=EvidenceNodeType.LIABILITY,
                label=liability.summary,
            )
        )
        for decision_tag in liability.related_decision_tags:
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
                    source_node_id=liability_node_id,
                    target_node_id=decision_node_id,
                    relation="risks",
                )
            )

    return EvidenceGraph(
        bundle_id=bundle.bundle_id,
        target_id=bundle.target_id,
        nodes=nodes,
        edges=edges,
    )


def extract_decision_subgraph(
    graph: EvidenceGraph, *, decision_tag: str
) -> EvidenceGraph:
    """Extract the decision-scoped subgraph for one decision tag."""
    decision_node_id = f"decision:{decision_tag}"
    related_node_ids = {decision_node_id}
    for edge in graph.edges:
        if (
            edge.source_node_id == decision_node_id
            or edge.target_node_id == decision_node_id
        ):
            related_node_ids.add(edge.source_node_id)
            related_node_ids.add(edge.target_node_id)
    sub_edges = [
        edge
        for edge in graph.edges
        if edge.source_node_id in related_node_ids
        and edge.target_node_id in related_node_ids
    ]
    expanded = True
    while expanded:
        expanded = False
        for edge in graph.edges:
            if (
                edge.source_node_id in related_node_ids
                and edge.target_node_id not in related_node_ids
            ):
                related_node_ids.add(edge.target_node_id)
                expanded = True
            if (
                edge.target_node_id in related_node_ids
                and edge.source_node_id not in related_node_ids
            ):
                related_node_ids.add(edge.source_node_id)
                expanded = True
    sub_nodes = [node for node in graph.nodes if node.node_id in related_node_ids]
    sub_edges = [
        edge
        for edge in graph.edges
        if edge.source_node_id in related_node_ids
        and edge.target_node_id in related_node_ids
    ]
    return EvidenceGraph(
        bundle_id=graph.bundle_id,
        target_id=graph.target_id,
        nodes=sub_nodes,
        edges=sub_edges,
    )


def trace_decision_paths(
    graph: EvidenceGraph, *, decision_tag: str
) -> list[DecisionTracePath]:
    """Trace outbound paths from one decision node to terminal evidence/assay nodes."""
    start = f"decision:{decision_tag}"
    adjacency: dict[str, list[str]] = {}
    for edge in graph.edges:
        adjacency.setdefault(edge.source_node_id, []).append(edge.target_node_id)
        adjacency.setdefault(edge.target_node_id, []).append(edge.source_node_id)
    if start not in adjacency:
        return []
    traces: list[DecisionTracePath] = []
    stack: list[tuple[str, list[str]]] = [(start, [start])]
    visited_paths: set[tuple[str, ...]] = set()
    while stack:
        node_id, path = stack.pop()
        neighbors = adjacency.get(node_id, [])
        progressed = False
        for neighbor in neighbors:
            if neighbor in path:
                continue
            progressed = True
            next_path = path + [neighbor]
            key = tuple(next_path)
            if key in visited_paths:
                continue
            visited_paths.add(key)
            stack.append((neighbor, next_path))
        if not progressed and node_id != start:
            traces.append(
                DecisionTracePath(
                    decision_tag=decision_tag,
                    terminal_node_id=node_id,
                    path=path,
                )
            )
    return sorted(traces, key=lambda item: (len(item.path), item.terminal_node_id))


def validate_evidence_graph(graph: EvidenceGraph) -> list[GraphValidationIssue]:
    """Validate evidence graph structure and derived lineage cycles."""
    issues: list[GraphValidationIssue] = []
    normalized_edges = [
        edge if isinstance(edge, EvidenceEdge) else EvidenceEdge.model_validate(edge)
        for edge in graph.edges
    ]
    node_ids = [node.node_id for node in graph.nodes]
    node_id_set = set(node_ids)
    if len(node_ids) != len(node_id_set):
        issues.append(
            GraphValidationIssue(
                code="duplicate-node-id",
                message="graph contains duplicate node_id entries",
            )
        )
    issues.extend(
        GraphValidationIssue(
            code="dangling-edge",
            message=f"edge {edge.source_node_id}->{edge.target_node_id} references unknown node",
        )
        for edge in normalized_edges
        if (
            edge.source_node_id not in node_id_set
            or edge.target_node_id not in node_id_set
        )
    )
    derived_edges = [
        edge
        for edge in normalized_edges
        if edge.relation == "derived_into"
        and edge.source_node_id.startswith("evidence:")
        and edge.target_node_id.startswith("evidence:")
    ]
    adjacency: dict[str, list[str]] = {}
    for edge in derived_edges:
        adjacency.setdefault(edge.source_node_id, []).append(edge.target_node_id)
    visited: set[str] = set()
    in_stack: set[str] = set()

    def visit(node_id: str) -> bool:
        visited.add(node_id)
        in_stack.add(node_id)
        for neighbor in adjacency.get(node_id, []):
            if neighbor not in visited and visit(neighbor):
                return True
            if neighbor in in_stack:
                return True
        in_stack.remove(node_id)
        return False

    if any(visit(node_id) for node_id in adjacency if node_id not in visited):
        issues.append(
            GraphValidationIssue(
                code="derived-lineage-cycle",
                message="derived_into evidence lineage contains a cycle",
            )
        )
    return issues
