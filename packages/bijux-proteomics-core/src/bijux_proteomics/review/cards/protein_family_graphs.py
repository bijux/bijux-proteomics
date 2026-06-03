# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Protein-family evidence graph models for peptide/protein support tracking."""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.sequences.digestion import PeptideProteinIndexEntry
from bijux_proteomics_foundation import JsonModel


class ProteinFamilyEvidenceNodeKind(StrEnum):
    """Node kinds in a protein-family evidence graph."""

    PROTEIN_FAMILY = "protein_family"
    PROTEIN = "protein"
    PEPTIDE = "peptide"


class ProteinFamilyEvidenceNode(JsonModel):
    """One evidence graph node."""

    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(..., min_length=1)
    kind: ProteinFamilyEvidenceNodeKind
    label: str = Field(..., min_length=1)


class ProteinFamilyEvidenceEdge(JsonModel):
    """One evidence graph edge."""

    model_config = ConfigDict(extra="forbid")

    source_node_id: str = Field(..., min_length=1)
    target_node_id: str = Field(..., min_length=1)
    relation: str = Field(..., min_length=1)
    support_count: int = Field(default=1, ge=1)


class ProteinFamilyEvidenceGraph(JsonModel):
    """Protein-family evidence graph preserving homolog/isoform support context."""

    model_config = ConfigDict(extra="forbid")

    nodes: tuple[ProteinFamilyEvidenceNode, ...] = Field(default_factory=tuple)
    edges: tuple[ProteinFamilyEvidenceEdge, ...] = Field(default_factory=tuple)


def build_protein_family_evidence_graph(
    entries: Sequence[PeptideProteinIndexEntry],
    *,
    homolog_pairs: Sequence[tuple[str, str]] = (),
) -> ProteinFamilyEvidenceGraph:
    """Build a protein-family evidence graph from peptide-protein mappings."""
    node_map: dict[
        tuple[ProteinFamilyEvidenceNodeKind, str], ProteinFamilyEvidenceNode
    ] = {}
    edges: list[ProteinFamilyEvidenceEdge] = []

    def _node(kind: ProteinFamilyEvidenceNodeKind, token: str, label: str) -> str:
        key = (kind, token)
        if key not in node_map:
            node_map[key] = ProteinFamilyEvidenceNode(
                node_id=f"{kind.value}:{token}",
                kind=kind,
                label=label,
            )
        return node_map[key].node_id

    for entry in entries:
        peptide_node = _node(
            ProteinFamilyEvidenceNodeKind.PEPTIDE,
            entry.sequence,
            entry.sequence,
        )
        for protein_accession, protein_family in zip(
            entry.protein_accessions, entry.protein_families, strict=False
        ):
            protein_node = _node(
                ProteinFamilyEvidenceNodeKind.PROTEIN,
                protein_accession,
                protein_accession,
            )
            family_node = _node(
                ProteinFamilyEvidenceNodeKind.PROTEIN_FAMILY,
                protein_family,
                protein_family,
            )
            edges.append(
                ProteinFamilyEvidenceEdge(
                    source_node_id=peptide_node,
                    target_node_id=protein_node,
                    relation="supports",
                )
            )
            edges.append(
                ProteinFamilyEvidenceEdge(
                    source_node_id=protein_node,
                    target_node_id=family_node,
                    relation="member_of_family",
                )
            )
    for left, right in homolog_pairs:
        left_node = _node(ProteinFamilyEvidenceNodeKind.PROTEIN, left, left)
        right_node = _node(ProteinFamilyEvidenceNodeKind.PROTEIN, right, right)
        edges.append(
            ProteinFamilyEvidenceEdge(
                source_node_id=left_node,
                target_node_id=right_node,
                relation="homolog_of",
            )
        )
    return ProteinFamilyEvidenceGraph(
        nodes=tuple(sorted(node_map.values(), key=lambda node: node.node_id)),
        edges=tuple(edges),
    )
