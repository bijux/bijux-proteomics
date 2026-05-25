# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Scientific conclusion diffs between two proteomics evidence graphs."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.review.evidence_graph import (
    ProteomicsEvidenceEdgeKind,
    ProteomicsEvidenceGraph,
    ProteomicsEvidenceNodeKind,
)
from bijux_proteomics.review.evidence_graph.evidence_graph_downgrades import build_evidence_graph_final_result_table
from bijux_proteomics_foundation import JsonModel


class EvidenceGraphRunDiffCategory(StrEnum):
    """Stable scientific conclusion categories compared across analysis runs."""

    PROTEIN = "protein"
    PEPTIDE = "peptide"
    PTM_SITE = "ptm_site"
    QC_DECISION = "qc_decision"
    PATHWAY = "pathway"


class EvidenceGraphRunDiffKind(StrEnum):
    """Stable run-diff change classes."""

    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"


class EvidenceGraphRunDiffEntry(JsonModel):
    """One scientific conclusion difference between two evidence graphs."""

    model_config = ConfigDict(extra="forbid")

    category: EvidenceGraphRunDiffCategory
    change_kind: EvidenceGraphRunDiffKind
    entity_ref: str = Field(..., min_length=1)
    left_claim_state: str | None = None
    right_claim_state: str | None = None
    left_evidence_tier: str | None = None
    right_evidence_tier: str | None = None
    left_confidence_tier: str | None = None
    right_confidence_tier: str | None = None
    left_source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    right_source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    rationale: str = Field(..., min_length=1)


class EvidenceGraphRunDiffReport(JsonModel):
    """Deterministic scientific conclusion diff across two analysis runs."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[EvidenceGraphRunDiffEntry, ...] = Field(default_factory=tuple)
    entry_count: int = Field(..., ge=0)
    category_counts: dict[str, int] = Field(default_factory=dict)
    change_counts: dict[str, int] = Field(default_factory=dict)


def compare_evidence_graph_runs(
    left_graph: ProteomicsEvidenceGraph,
    right_graph: ProteomicsEvidenceGraph,
) -> EvidenceGraphRunDiffReport:
    """Compare two canonical evidence graphs by scientific conclusion category."""

    entries: list[EvidenceGraphRunDiffEntry] = []
    entries.extend(
        _compare_claim_snapshots(
            _protein_snapshots(left_graph),
            _protein_snapshots(right_graph),
            category=EvidenceGraphRunDiffCategory.PROTEIN,
        )
    )
    entries.extend(
        _compare_claim_snapshots(
            _peptide_snapshots(left_graph),
            _peptide_snapshots(right_graph),
            category=EvidenceGraphRunDiffCategory.PEPTIDE,
        )
    )
    entries.extend(
        _compare_claim_snapshots(
            _ptm_snapshots(left_graph),
            _ptm_snapshots(right_graph),
            category=EvidenceGraphRunDiffCategory.PTM_SITE,
        )
    )
    entries.extend(
        _compare_claim_snapshots(
            _qc_snapshots(left_graph),
            _qc_snapshots(right_graph),
            category=EvidenceGraphRunDiffCategory.QC_DECISION,
        )
    )
    entries.extend(
        _compare_claim_snapshots(
            _pathway_snapshots(left_graph),
            _pathway_snapshots(right_graph),
            category=EvidenceGraphRunDiffCategory.PATHWAY,
        )
    )

    sorted_entries = tuple(
        sorted(
            entries,
            key=lambda entry: (entry.category.value, entry.entity_ref, entry.change_kind.value),
        )
    )
    category_counts: dict[str, int] = {}
    change_counts: dict[str, int] = {}
    for entry in sorted_entries:
        category_counts[entry.category.value] = (
            category_counts.get(entry.category.value, 0) + 1
        )
        change_counts[entry.change_kind.value] = (
            change_counts.get(entry.change_kind.value, 0) + 1
        )
    return EvidenceGraphRunDiffReport(
        entries=sorted_entries,
        entry_count=len(sorted_entries),
        category_counts=dict(sorted(category_counts.items())),
        change_counts=dict(sorted(change_counts.items())),
    )


def render_evidence_graph_run_diff_tsv(report: EvidenceGraphRunDiffReport) -> str:
    """Render run-diff scientific conclusion changes as TSV."""

    rows = [
        {
            "category": entry.category.value,
            "change_kind": entry.change_kind.value,
            "entity_ref": entry.entity_ref,
            "left_claim_state": entry.left_claim_state or "",
            "right_claim_state": entry.right_claim_state or "",
            "left_evidence_tier": entry.left_evidence_tier or "",
            "right_evidence_tier": entry.right_evidence_tier or "",
            "left_confidence_tier": entry.left_confidence_tier or "",
            "right_confidence_tier": entry.right_confidence_tier or "",
            "left_source_row_refs": "|".join(entry.left_source_row_refs),
            "right_source_row_refs": "|".join(entry.right_source_row_refs),
            "rationale": entry.rationale,
        }
        for entry in report.entries
    ]
    return _dict_rows_to_tsv(rows)


class _ClaimSnapshot(JsonModel):
    model_config = ConfigDict(extra="forbid")

    claim_state: str
    evidence_tier: str | None = None
    confidence_tier: str | None = None
    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)


def _compare_claim_snapshots(
    left: dict[str, _ClaimSnapshot],
    right: dict[str, _ClaimSnapshot],
    *,
    category: EvidenceGraphRunDiffCategory,
) -> tuple[EvidenceGraphRunDiffEntry, ...]:
    entries: list[EvidenceGraphRunDiffEntry] = []
    for entity_ref in sorted(set(left) | set(right)):
        left_snapshot = left.get(entity_ref)
        right_snapshot = right.get(entity_ref)
        if left_snapshot is None:
            entries.append(
                EvidenceGraphRunDiffEntry(
                    category=category,
                    change_kind=EvidenceGraphRunDiffKind.ADDED,
                    entity_ref=entity_ref,
                    right_claim_state=right_snapshot.claim_state if right_snapshot else None,
                    right_evidence_tier=right_snapshot.evidence_tier if right_snapshot else None,
                    right_confidence_tier=(
                        right_snapshot.confidence_tier if right_snapshot else None
                    ),
                    right_source_row_refs=(
                        right_snapshot.source_row_refs if right_snapshot else ()
                    ),
                    rationale=f"{category.value.replace('_', ' ')} conclusion was added",
                )
            )
            continue
        if right_snapshot is None:
            entries.append(
                EvidenceGraphRunDiffEntry(
                    category=category,
                    change_kind=EvidenceGraphRunDiffKind.REMOVED,
                    entity_ref=entity_ref,
                    left_claim_state=left_snapshot.claim_state,
                    left_evidence_tier=left_snapshot.evidence_tier,
                    left_confidence_tier=left_snapshot.confidence_tier,
                    left_source_row_refs=left_snapshot.source_row_refs,
                    rationale=f"{category.value.replace('_', ' ')} conclusion was removed",
                )
            )
            continue
        if _snapshots_equal(left_snapshot, right_snapshot):
            continue
        entries.append(
            EvidenceGraphRunDiffEntry(
                category=category,
                change_kind=EvidenceGraphRunDiffKind.CHANGED,
                entity_ref=entity_ref,
                left_claim_state=left_snapshot.claim_state,
                right_claim_state=right_snapshot.claim_state,
                left_evidence_tier=left_snapshot.evidence_tier,
                right_evidence_tier=right_snapshot.evidence_tier,
                left_confidence_tier=left_snapshot.confidence_tier,
                right_confidence_tier=right_snapshot.confidence_tier,
                left_source_row_refs=left_snapshot.source_row_refs,
                right_source_row_refs=right_snapshot.source_row_refs,
                rationale=f"{category.value.replace('_', ' ')} conclusion changed",
            )
        )
    return tuple(entries)


def _protein_snapshots(graph: ProteomicsEvidenceGraph) -> dict[str, _ClaimSnapshot]:
    return _final_result_snapshots(
        graph,
        subject_kind=ProteomicsEvidenceNodeKind.PROTEIN,
    )


def _ptm_snapshots(graph: ProteomicsEvidenceGraph) -> dict[str, _ClaimSnapshot]:
    return _final_result_snapshots(
        graph,
        subject_kind=ProteomicsEvidenceNodeKind.PTM_SITE,
    )


def _pathway_snapshots(graph: ProteomicsEvidenceGraph) -> dict[str, _ClaimSnapshot]:
    return _final_result_snapshots(
        graph,
        subject_kind=ProteomicsEvidenceNodeKind.PATHWAY,
    )


def _final_result_snapshots(
    graph: ProteomicsEvidenceGraph,
    *,
    subject_kind: ProteomicsEvidenceNodeKind,
) -> dict[str, _ClaimSnapshot]:
    final_results = build_evidence_graph_final_result_table(graph)
    node_by_id = {node.node_id: node for node in graph.nodes}
    snapshots: dict[str, _ClaimSnapshot] = {}
    for entry in final_results.entries:
        if entry.subject_node_kind is not subject_kind:
            continue
        claim_node = node_by_id[entry.claim_node_id]
        snapshots[entry.subject_node_ref] = _ClaimSnapshot(
            claim_state=claim_node.claim_state,
            evidence_tier=entry.evidence_tier.value,
            confidence_tier=entry.confidence_tier.value,
            source_row_refs=entry.source_row_refs,
        )
    return snapshots


def _peptide_snapshots(graph: ProteomicsEvidenceGraph) -> dict[str, _ClaimSnapshot]:
    snapshots: dict[str, _ClaimSnapshot] = {}
    node_by_id = {node.node_id: node for node in graph.nodes}
    for edge in graph.edges:
        if edge.relation is not ProteomicsEvidenceEdgeKind.PEPTIDE_SUPPORTS_STATISTICAL_RESULT:
            continue
        peptide = node_by_id[edge.source_node_id]
        claim = node_by_id[edge.target_node_id]
        snapshots[peptide.entity_ref] = _ClaimSnapshot(
            claim_state=claim.claim_state,
            confidence_tier=_confidence_tier(_average((edge.confidence, _trust_score(peptide.trust_class)))),
            source_row_refs=(edge.source_row_ref,),
        )
    return snapshots


def _qc_snapshots(graph: ProteomicsEvidenceGraph) -> dict[str, _ClaimSnapshot]:
    snapshots: dict[str, _ClaimSnapshot] = {}
    node_by_id = {node.node_id: node for node in graph.nodes}
    for edge in graph.edges:
        if edge.relation is not ProteomicsEvidenceEdgeKind.RUN_GOVERNED_BY_QC_DECISION:
            continue
        run = node_by_id[edge.source_node_id]
        qc_decision = node_by_id[edge.target_node_id]
        snapshots[run.entity_ref] = _ClaimSnapshot(
            claim_state=qc_decision.claim_state,
            confidence_tier=_confidence_tier(
                _average((edge.confidence, _trust_score(qc_decision.trust_class)))
            ),
            source_row_refs=(edge.source_row_ref,),
        )
    return snapshots


def _snapshots_equal(left: _ClaimSnapshot, right: _ClaimSnapshot) -> bool:
    return (
        left.claim_state == right.claim_state
        and left.evidence_tier == right.evidence_tier
        and left.confidence_tier == right.confidence_tier
    )


def _confidence_tier(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.65:
        return "moderate"
    return "low"


def _average(values: tuple[float, ...]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _trust_score(trust_class: str) -> float:
    return {
        "high": 0.95,
        "medium": 0.75,
        "low": 0.4,
        "unreviewed": 0.6,
        "accepted": 0.8,
        "caution": 0.5,
        "rejected": 0.2,
        "single_run_only": 0.45,
        "exploratory": 0.45,
        "contaminant": 0.3,
        "imputed": 0.4,
    }.get(trust_class, 0.6)


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
