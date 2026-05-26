# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Indexed lazy loader for exported proteomics evidence-graph artifacts."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from bijux_proteomics.review.evidence_graph.evidence_graph import (
    ProteomicsEvidenceContextRef,
    ProteomicsEvidenceEdge,
    ProteomicsEvidenceEdgeKind,
    ProteomicsEvidenceGraphSummary,
    ProteomicsEvidenceNode,
    ProteomicsEvidenceNodeKind,
    ProteomicsEvidenceType,
)


@dataclass(frozen=True, slots=True)
class _IndexedNodeRecord:
    node_id: str
    entity_type: ProteomicsEvidenceNodeKind
    entity_ref: str
    label: str
    claim_state: str
    trust_class: str
    contradiction_ids: tuple[str, ...]
    context_refs: tuple[ProteomicsEvidenceContextRef, ...]


@dataclass(frozen=True, slots=True)
class _IndexedEdgeRecord:
    source_node_id: str
    target_node_id: str
    relation: ProteomicsEvidenceEdgeKind
    source_row_ref: str
    confidence: float
    evidence_type: ProteomicsEvidenceType
    reason: str
    support_count: int

    @property
    def edge_key(self) -> tuple[str, str, str, str]:
        return (
            self.source_node_id,
            self.target_node_id,
            self.relation.value,
            self.source_row_ref,
        )


class LazyProteomicsEvidenceGraph:
    """Indexed evidence graph that materializes nodes and edges on demand."""

    def __init__(
        self,
        *,
        nodes_path: Path,
        edges_path: Path,
        summary: ProteomicsEvidenceGraphSummary,
        node_records_by_id: dict[str, _IndexedNodeRecord],
        node_ids_by_entity: dict[tuple[ProteomicsEvidenceNodeKind, str], str],
        edge_records_by_key: dict[tuple[str, str, str, str], _IndexedEdgeRecord],
        incoming_edge_keys_by_node_id: dict[str, tuple[tuple[str, str, str, str], ...]],
        outgoing_edge_keys_by_node_id: dict[str, tuple[tuple[str, str, str, str], ...]],
    ) -> None:
        self.nodes_path = nodes_path
        self.edges_path = edges_path
        self.summary = summary
        self._node_records_by_id = node_records_by_id
        self._node_ids_by_entity = node_ids_by_entity
        self._edge_records_by_key = edge_records_by_key
        self._incoming_edge_keys_by_node_id = incoming_edge_keys_by_node_id
        self._outgoing_edge_keys_by_node_id = outgoing_edge_keys_by_node_id
        self._materialized_nodes_by_id: dict[str, ProteomicsEvidenceNode] = {}
        self._materialized_edges_by_key: dict[
            tuple[str, str, str, str], ProteomicsEvidenceEdge
        ] = {}

    def require_node(
        self,
        kind: ProteomicsEvidenceNodeKind,
        entity_ref: str,
    ) -> ProteomicsEvidenceNode:
        """Resolve one canonical node by scientific kind and entity reference."""

        node_id = self._node_ids_by_entity.get((kind, entity_ref))
        if node_id is None:
            raise ValueError(f"graph node is missing: {kind.value}:{entity_ref}")
        return self.require_node_by_id(node_id)

    def require_node_by_id(self, node_id: str) -> ProteomicsEvidenceNode:
        """Resolve one canonical node by stable graph-local identifier."""

        cached = self._materialized_nodes_by_id.get(node_id)
        if cached is not None:
            return cached
        record = self._node_records_by_id.get(node_id)
        if record is None:
            raise ValueError(f"graph node is missing by node_id: {node_id}")
        materialized = ProteomicsEvidenceNode(
            node_id=record.node_id,
            entity_type=record.entity_type,
            entity_ref=record.entity_ref,
            label=record.label,
            claim_state=record.claim_state,
            trust_class=record.trust_class,
            contradiction_ids=record.contradiction_ids,
            context_refs=record.context_refs,
        )
        self._materialized_nodes_by_id[node_id] = materialized
        return materialized

    def incoming_edges(self, node_id: str) -> tuple[ProteomicsEvidenceEdge, ...]:
        """Resolve canonical incoming edges for one node."""

        return self._materialize_edges(
            self._incoming_edge_keys_by_node_id.get(node_id, ())
        )

    def outgoing_edges(self, node_id: str) -> tuple[ProteomicsEvidenceEdge, ...]:
        """Resolve canonical outgoing edges for one node."""

        return self._materialize_edges(
            self._outgoing_edge_keys_by_node_id.get(node_id, ())
        )

    def adjacent_edges(self, node_id: str) -> tuple[ProteomicsEvidenceEdge, ...]:
        """Resolve all canonical adjacent edges for one node."""

        edge_keys = {
            *self._incoming_edge_keys_by_node_id.get(node_id, ()),
            *self._outgoing_edge_keys_by_node_id.get(node_id, ()),
        }
        return self._materialize_edges(tuple(sorted(edge_keys)))

    def _materialize_edges(
        self,
        edge_keys: tuple[tuple[str, str, str, str], ...],
    ) -> tuple[ProteomicsEvidenceEdge, ...]:
        return tuple(self._materialize_edge(edge_key) for edge_key in edge_keys)

    def _materialize_edge(
        self,
        edge_key: tuple[str, str, str, str],
    ) -> ProteomicsEvidenceEdge:
        cached = self._materialized_edges_by_key.get(edge_key)
        if cached is not None:
            return cached
        record = self._edge_records_by_key[edge_key]
        materialized = ProteomicsEvidenceEdge(
            source_node_id=record.source_node_id,
            target_node_id=record.target_node_id,
            relation=record.relation,
            source_row_ref=record.source_row_ref,
            confidence=record.confidence,
            evidence_type=record.evidence_type,
            reason=record.reason,
            support_count=record.support_count,
        )
        self._materialized_edges_by_key[edge_key] = materialized
        return materialized


def load_lazy_proteomics_evidence_graph(
    nodes_path: str | Path,
    edges_path: str | Path,
) -> LazyProteomicsEvidenceGraph:
    """Load one indexed evidence graph from exported node and edge TSV artifacts."""

    node_records_by_id, node_ids_by_entity, node_kind_counts, contradiction_count = (
        _load_node_records(Path(nodes_path))
    )
    (
        edge_records_by_key,
        incoming_edge_keys_by_node_id,
        outgoing_edge_keys_by_node_id,
        edge_kind_counts,
        evidence_type_counts,
    ) = _load_edge_records(
        Path(edges_path),
        node_records_by_id=node_records_by_id,
    )
    summary = ProteomicsEvidenceGraphSummary(
        node_count=len(node_records_by_id),
        edge_count=len(edge_records_by_key),
        contradiction_node_count=contradiction_count,
        node_kind_counts=dict(sorted(node_kind_counts.items())),
        edge_kind_counts=dict(sorted(edge_kind_counts.items())),
        evidence_type_counts=dict(sorted(evidence_type_counts.items())),
    )
    return LazyProteomicsEvidenceGraph(
        nodes_path=Path(nodes_path),
        edges_path=Path(edges_path),
        summary=summary,
        node_records_by_id=node_records_by_id,
        node_ids_by_entity=node_ids_by_entity,
        edge_records_by_key=edge_records_by_key,
        incoming_edge_keys_by_node_id=incoming_edge_keys_by_node_id,
        outgoing_edge_keys_by_node_id=outgoing_edge_keys_by_node_id,
    )


def _load_node_records(
    nodes_path: Path,
) -> tuple[
    dict[str, _IndexedNodeRecord],
    dict[tuple[ProteomicsEvidenceNodeKind, str], str],
    dict[str, int],
    int,
]:
    _require_columns(
        nodes_path=nodes_path,
        expected_columns=(
            "node_id",
            "entity_type",
            "entity_ref",
            "label",
            "claim_state",
            "trust_class",
            "contradiction_ids",
            "context_refs",
        ),
    )
    node_records_by_id: dict[str, _IndexedNodeRecord] = {}
    node_ids_by_entity: dict[tuple[ProteomicsEvidenceNodeKind, str], str] = {}
    node_kind_counts: dict[str, int] = defaultdict(int)
    contradiction_count = 0
    for row in _iter_rows(nodes_path):
        record = _parse_node_record(row)
        if record.node_id in node_records_by_id:
            raise ValueError(f"duplicate graph node_id in {nodes_path}: {record.node_id}")
        entity_key = (record.entity_type, record.entity_ref)
        if entity_key in node_ids_by_entity:
            raise ValueError(
                "duplicate graph entity reference in "
                f"{nodes_path}: {record.entity_type.value}:{record.entity_ref}"
            )
        node_records_by_id[record.node_id] = record
        node_ids_by_entity[entity_key] = record.node_id
        node_kind_counts[record.entity_type.value] += 1
        contradiction_count += int(bool(record.contradiction_ids))
    return node_records_by_id, node_ids_by_entity, dict(node_kind_counts), contradiction_count


def _load_edge_records(
    edges_path: Path,
    *,
    node_records_by_id: dict[str, _IndexedNodeRecord],
) -> tuple[
    dict[tuple[str, str, str, str], _IndexedEdgeRecord],
    dict[str, tuple[tuple[str, str, str, str], ...]],
    dict[str, tuple[tuple[str, str, str, str], ...]],
    dict[str, int],
    dict[str, int],
]:
    _require_columns(
        nodes_path=edges_path,
        expected_columns=(
            "source_node_id",
            "target_node_id",
            "relation",
            "source_row_ref",
            "confidence",
            "evidence_type",
            "reason",
            "support_count",
        ),
    )
    edge_records_by_key: dict[tuple[str, str, str, str], _IndexedEdgeRecord] = {}
    incoming_edge_keys_by_node_id: dict[str, list[tuple[str, str, str, str]]] = defaultdict(list)
    outgoing_edge_keys_by_node_id: dict[str, list[tuple[str, str, str, str]]] = defaultdict(list)
    edge_kind_counts: dict[str, int] = defaultdict(int)
    evidence_type_counts: dict[str, int] = defaultdict(int)
    for row in _iter_rows(edges_path):
        record = _parse_edge_record(row)
        if record.source_node_id not in node_records_by_id:
            raise ValueError(
                "edge source node is missing from lazy graph artifacts: "
                f"{record.source_node_id}"
            )
        if record.target_node_id not in node_records_by_id:
            raise ValueError(
                "edge target node is missing from lazy graph artifacts: "
                f"{record.target_node_id}"
            )
        if record.edge_key in edge_records_by_key:
            raise ValueError(f"duplicate graph edge in {edges_path}: {record.edge_key!r}")
        edge_records_by_key[record.edge_key] = record
        incoming_edge_keys_by_node_id[record.target_node_id].append(record.edge_key)
        outgoing_edge_keys_by_node_id[record.source_node_id].append(record.edge_key)
        edge_kind_counts[record.relation.value] += 1
        evidence_type_counts[record.evidence_type.value] += 1
    return (
        edge_records_by_key,
        {
            node_id: tuple(sorted(edge_keys))
            for node_id, edge_keys in incoming_edge_keys_by_node_id.items()
        },
        {
            node_id: tuple(sorted(edge_keys))
            for node_id, edge_keys in outgoing_edge_keys_by_node_id.items()
        },
        dict(edge_kind_counts),
        dict(evidence_type_counts),
    )


def _parse_node_record(row: dict[str, str]) -> _IndexedNodeRecord:
    return _IndexedNodeRecord(
        node_id=row["node_id"],
        entity_type=ProteomicsEvidenceNodeKind(row["entity_type"]),
        entity_ref=row["entity_ref"],
        label=row["label"],
        claim_state=row["claim_state"],
        trust_class=row["trust_class"],
        contradiction_ids=_split_pipe_field(row["contradiction_ids"]),
        context_refs=_parse_context_refs(row["context_refs"]),
    )


def _parse_edge_record(row: dict[str, str]) -> _IndexedEdgeRecord:
    return _IndexedEdgeRecord(
        source_node_id=row["source_node_id"],
        target_node_id=row["target_node_id"],
        relation=ProteomicsEvidenceEdgeKind(row["relation"]),
        source_row_ref=row["source_row_ref"],
        confidence=float(row["confidence"]),
        evidence_type=ProteomicsEvidenceType(row["evidence_type"]),
        reason=row["reason"],
        support_count=int(row["support_count"]),
    )


def _parse_context_refs(serialized_context_refs: str) -> tuple[ProteomicsEvidenceContextRef, ...]:
    if not serialized_context_refs:
        return ()
    context_refs: list[ProteomicsEvidenceContextRef] = []
    for token in serialized_context_refs.split("|"):
        kind, ref = token.split(":", 1)
        context_refs.append(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind(kind),
                entity_ref=ref,
            )
        )
    return tuple(context_refs)


def _split_pipe_field(serialized_values: str) -> tuple[str, ...]:
    if not serialized_values:
        return ()
    return tuple(token for token in serialized_values.split("|") if token)


def _iter_rows(path: Path) -> Iterator[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            yield {key: value or "" for key, value in row.items()}


def _require_columns(
    *,
    nodes_path: Path,
    expected_columns: tuple[str, ...],
) -> None:
    with nodes_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = tuple(reader.fieldnames or ())
    missing = tuple(column for column in expected_columns if column not in fieldnames)
    if missing:
        raise ValueError(
            f"lazy graph artifact is missing required columns in {nodes_path}: {missing!r}"
        )
