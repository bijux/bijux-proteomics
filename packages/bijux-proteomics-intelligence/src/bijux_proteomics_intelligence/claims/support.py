# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Graph-backed validation of analytical claim support."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.memory.integrity.graph import EvidenceGraph
from bijux_proteomics_knowledge.memory.models.claims import EvidenceClaim


class ClaimSupportStatus(StrEnum):
    """Support posture for one claim after graph-backed validation."""

    SUPPORTED = "supported"
    CONFLICTED = "conflicted"
    CONTRADICTED = "contradicted"
    INVALID = "invalid"


class ClaimSupportValidationEntry(JsonModel):
    """One claim-support validation row."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    support_status: ClaimSupportStatus
    missing_support: tuple[str, ...] = Field(default_factory=tuple)
    contradicting_evidence: tuple[str, ...] = Field(default_factory=tuple)


class ClaimSupportValidationSummary(JsonModel):
    """Stable summary over claim-support validation."""

    model_config = ConfigDict(extra="forbid")

    claim_count: int = Field(..., ge=0)
    supported_claim_count: int = Field(..., ge=0)
    conflicted_claim_count: int = Field(..., ge=0)
    contradicted_claim_count: int = Field(..., ge=0)
    invalid_claim_count: int = Field(..., ge=0)


class ClaimSupportValidationReport(JsonModel):
    """Owned report over graph-backed claim-support validation."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ClaimSupportValidationEntry, ...] = Field(default_factory=tuple)
    summary: ClaimSupportValidationSummary
    note: str = Field(..., min_length=1)


def validate_claim_support(
    claims: tuple[EvidenceClaim, ...] | list[EvidenceClaim],
    evidence_graph: EvidenceGraph,
) -> ClaimSupportValidationReport:
    """Validate that each claim is backed by explicit graph evidence."""

    claim_items = tuple(claims)
    graph_node_ids = {node.node_id for node in evidence_graph.nodes}
    support_edges = _claim_edge_index(
        evidence_graph=evidence_graph,
        relation="supported_by_evidence",
    )
    contradiction_edges = _claim_edge_index(
        evidence_graph=evidence_graph,
        relation="contradicted_by_evidence",
    )

    entries: list[ClaimSupportValidationEntry] = []
    for claim in claim_items:
        claim_node_id = f"claim:{claim.claim_id}"
        missing_support: list[str] = []
        if not claim.evidence_ids:
            missing_support.append("claim declares no supporting evidence ids")
        if claim_node_id not in graph_node_ids:
            missing_support.append("claim node missing from evidence graph")

        declared_support_nodes = tuple(
            f"evidence:{evidence_id}" for evidence_id in claim.evidence_ids
        )
        graph_support_nodes = support_edges.get(claim_node_id, ())
        for evidence_node_id in declared_support_nodes:
            if evidence_node_id not in graph_node_ids:
                missing_support.append(
                    f"missing graph evidence node {evidence_node_id}"
                )
            elif evidence_node_id not in graph_support_nodes:
                missing_support.append(
                    f"missing support edge for {evidence_node_id.removeprefix('evidence:')}"
                )
        if claim_node_id in graph_node_ids and not graph_support_nodes:
            missing_support.append("claim has no supporting evidence edge")

        graph_contradicting_nodes = contradiction_edges.get(claim_node_id, ())
        support_status = _support_status(
            missing_support=tuple(missing_support),
            contradicting_nodes=graph_contradicting_nodes,
        )
        entries.append(
            ClaimSupportValidationEntry(
                claim_id=claim.claim_id,
                support_status=support_status,
                missing_support=tuple(dict.fromkeys(missing_support)),
                contradicting_evidence=tuple(
                    sorted(
                        node_id.removeprefix("evidence:")
                        for node_id in graph_contradicting_nodes
                    )
                ),
            )
        )

    return ClaimSupportValidationReport(
        entries=tuple(entries),
        summary=ClaimSupportValidationSummary(
            claim_count=len(entries),
            supported_claim_count=sum(
                1
                for entry in entries
                if entry.support_status is ClaimSupportStatus.SUPPORTED
            ),
            conflicted_claim_count=sum(
                1
                for entry in entries
                if entry.support_status is ClaimSupportStatus.CONFLICTED
            ),
            contradicted_claim_count=sum(
                1
                for entry in entries
                if entry.support_status is ClaimSupportStatus.CONTRADICTED
            ),
            invalid_claim_count=sum(
                1
                for entry in entries
                if entry.support_status is ClaimSupportStatus.INVALID
            ),
        ),
        note=(
            "claim support validation checks that each analytical claim is anchored "
            "to explicit evidence-graph support edges, keeps contradicting graph "
            "evidence visible, and marks claims invalid when their declared support "
            "does not exist in the graph"
        ),
    )


def render_claim_support_validation_tsv(
    entries: tuple[ClaimSupportValidationEntry, ...],
) -> str:
    """Render claim-support validation rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        ("claim_id", "support_status", "missing_support", "contradicting_evidence")
    )
    for entry in entries:
        writer.writerow(
            (
                entry.claim_id,
                entry.support_status.value,
                ";".join(entry.missing_support),
                ";".join(entry.contradicting_evidence),
            )
        )
    return handle.getvalue()


def _claim_edge_index(
    *,
    evidence_graph: EvidenceGraph,
    relation: str,
) -> dict[str, tuple[str, ...]]:
    claim_to_targets: dict[str, list[str]] = {}
    for edge in evidence_graph.edges:
        if edge.relation != relation or not edge.source_node_id.startswith("claim:"):
            continue
        claim_to_targets.setdefault(edge.source_node_id, []).append(edge.target_node_id)
    return {
        claim_node_id: tuple(sorted(targets))
        for claim_node_id, targets in claim_to_targets.items()
    }


def _support_status(
    *,
    missing_support: tuple[str, ...],
    contradicting_nodes: tuple[str, ...],
) -> ClaimSupportStatus:
    if missing_support:
        return ClaimSupportStatus.INVALID
    if contradicting_nodes:
        return ClaimSupportStatus.CONFLICTED
    return ClaimSupportStatus.SUPPORTED
