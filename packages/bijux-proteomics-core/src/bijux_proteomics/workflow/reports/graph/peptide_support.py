# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Peptide evidence wiring for biological result graph protein claims."""

from __future__ import annotations

from bijux_proteomics.review.evidence_graph.evidence_graph import (
    ProteomicsEvidenceGraphBuilder,
)


def _add_biological_result_graph_peptide_support(
    builder: ProteomicsEvidenceGraphBuilder,
    *,
    protein_node_id: str,
    entity_id: str,
    entity_member_peptides: tuple[str, ...],
    peptide_membership_counts: dict[str, int],
) -> None:
    for peptide_sequence in sorted(entity_member_peptides):
        peptide = builder.add_peptide(
            peptide_sequence,
            label=peptide_sequence,
            trust_class=(
                "shared_only"
                if peptide_membership_counts.get(peptide_sequence, 0) > 1
                else "high"
            ),
        )
        builder.add_peptide_maps_to_protein(
            peptide.node_id,
            protein_node_id,
            source_row_ref=f"membership:{entity_id}:{peptide_sequence}",
            confidence=1.0,
            reason=(
                f"entity peptide {peptide_sequence} maps to protein group {entity_id}"
            ),
        )
        builder.add_peptide_quantifies_protein(
            peptide.node_id,
            protein_node_id,
            source_row_ref=f"quantifying:{entity_id}:{peptide_sequence}",
            confidence=0.9,
            reason=(
                f"entity peptide {peptide_sequence} quantifies protein group {entity_id}"
            ),
        )
