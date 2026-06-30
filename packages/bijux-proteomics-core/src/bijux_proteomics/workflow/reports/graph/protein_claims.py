# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein claim graph population for biological result graphs."""

from __future__ import annotations

from collections import Counter

from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
)
from bijux_proteomics.review.evidence_graph.evidence_graph import (
    ProteomicsEvidenceContextRef,
    ProteomicsEvidenceGraphBuilder,
    ProteomicsEvidenceNodeKind,
)
from bijux_proteomics.workflow.reports.graph.claim_policy import (
    _claim_confidence,
    _claim_state,
    _protein_label,
    _protein_trust_class,
)
from bijux_proteomics.workflow.reports.graph.peptide_support import (
    _add_biological_result_graph_peptide_support,
)
from bijux_proteomics.workflow.reports.graph.quant_support import (
    _add_biological_result_graph_quant_support,
    _group_quant_values_by_entity,
)
from bijux_proteomics.workflow.reports.graph.run_context import (
    BiologicalResultGraphRunContext,
)


def _add_biological_result_graph_protein_claims(
    builder: ProteomicsEvidenceGraphBuilder,
    quant_table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    run_context: BiologicalResultGraphRunContext,
    *,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
) -> None:
    peptide_membership_counts = _count_peptide_memberships(quant_table)
    differential_by_entity = {
        entry.entity_id: entry for entry in differential_report.entries
    }
    values_by_entity = _group_quant_values_by_entity(quant_table.values)

    for entity_id in sorted(quant_table.entity_ids):
        differential_entry = differential_by_entity.get(entity_id)
        if differential_entry is None:
            continue
        protein = builder.add_protein(
            entity_id,
            label=_protein_label(entity_id, quant_table),
            trust_class=_protein_trust_class(differential_entry),
        )
        claim = builder.add_statistical_result(
            f"protein:{differential_entry.condition_a}_vs_{differential_entry.condition_b}:{entity_id}",
            label=f"protein differential result {entity_id}",
            claim_state=_claim_state(
                differential_entry,
                max_adjusted_p_value=max_adjusted_p_value,
                min_absolute_log2_fold_change=min_absolute_log2_fold_change,
            ),
            context_refs=(
                ProteomicsEvidenceContextRef(
                    entity_type=ProteomicsEvidenceNodeKind.PROTEIN,
                    entity_ref=entity_id,
                ),
            ),
        )
        builder.add_protein_supports_statistical_result(
            protein.node_id,
            claim.node_id,
            source_row_ref=f"differential:{entity_id}",
            confidence=_claim_confidence(differential_entry),
            reason=(
                f"protein differential result for {entity_id} compares "
                f"{differential_entry.condition_a} vs {differential_entry.condition_b}"
                ),
        )

        _add_biological_result_graph_peptide_support(
            builder,
            protein_node_id=protein.node_id,
            entity_id=entity_id,
            entity_member_peptides=quant_table.entity_member_peptides.get(entity_id, ()),
            peptide_membership_counts=peptide_membership_counts,
        )
        _add_biological_result_graph_quant_support(
            builder,
            protein_node_id=protein.node_id,
            claim_node_id=claim.node_id,
            entity_id=entity_id,
            quant_values=tuple(values_by_entity.get(entity_id, ())),
            run_context=run_context,
        )


def _count_peptide_memberships(quant_table: LabelFreeQuantTable) -> dict[str, int]:
    return dict(
        Counter(
            peptide
            for peptides in quant_table.entity_member_peptides.values()
            for peptide in peptides
        )
    )


__all__ = [
    "_add_biological_result_graph_protein_claims",
    "_count_peptide_memberships",
]
