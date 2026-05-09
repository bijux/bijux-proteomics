# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review.protein_family_graphs import (
    ProteinFamilyEvidenceNodeKind,
    build_protein_family_evidence_graph,
)
from bijux_proteomics.sequences.digestion import (
    PeptideProteinIndexEntry,
    PeptideUniqueness,
)


def test_build_protein_family_evidence_graph_links_peptides_proteins_and_families() -> (
    None
):
    graph = build_protein_family_evidence_graph(
        (
            PeptideProteinIndexEntry(
                sequence="PEPTIDEA",
                protein_accessions=("P001",),
                protein_families=("FAM_A",),
                source_identifiers=("sp|P001|",),
                uniqueness=PeptideUniqueness.UNIQUE,
            ),
            PeptideProteinIndexEntry(
                sequence="PEPTIDEB",
                protein_accessions=("P002", "P003"),
                protein_families=("FAM_B", "FAM_B"),
                source_identifiers=("sp|P002|", "sp|P003|"),
                uniqueness=PeptideUniqueness.SHARED_ISOFORM_FAMILY,
            ),
        ),
        homolog_pairs=(("P002", "P003"),),
    )

    assert any(
        node.kind is ProteinFamilyEvidenceNodeKind.PEPTIDE for node in graph.nodes
    )
    assert any(
        node.kind is ProteinFamilyEvidenceNodeKind.PROTEIN for node in graph.nodes
    )
    assert any(
        edge.relation == "member_of_family"
        and edge.source_node_id == "protein:P001"
        and edge.target_node_id == "protein_family:FAM_A"
        for edge in graph.edges
    )
    assert any(edge.relation == "homolog_of" for edge in graph.edges)
