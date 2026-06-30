# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein claim graph population for biological result graphs."""

from __future__ import annotations

from collections import Counter

from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
    MissingValueKind,
    QuantValue,
)
from bijux_proteomics.review.evidence_graph.evidence_graph import (
    ProteomicsEvidenceContextRef,
    ProteomicsEvidenceGraphBuilder,
    ProteomicsEvidenceNodeKind,
)
from bijux_proteomics.workflow.reports.biological_result_graph_claim_policy import (
    _claim_confidence,
    _claim_state,
    _protein_label,
    _protein_trust_class,
    _quant_trust_class,
)
from bijux_proteomics.workflow.reports.biological_result_graph_run_context import (
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
    peptide_membership_counts = Counter(
        peptide
        for peptides in quant_table.entity_member_peptides.values()
        for peptide in peptides
    )
    differential_by_entity = {
        entry.entity_id: entry for entry in differential_report.entries
    }
    values_by_entity: dict[str, list[QuantValue]] = {}
    for value in quant_table.values:
        values_by_entity.setdefault(value.entity_id, []).append(value)

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

        for peptide_sequence in sorted(
            quant_table.entity_member_peptides.get(entity_id, ())
        ):
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
                protein.node_id,
                source_row_ref=f"membership:{entity_id}:{peptide_sequence}",
                confidence=1.0,
                reason=(
                    f"entity peptide {peptide_sequence} maps to protein group {entity_id}"
                ),
            )
            builder.add_peptide_quantifies_protein(
                peptide.node_id,
                protein.node_id,
                source_row_ref=f"quantifying:{entity_id}:{peptide_sequence}",
                confidence=0.9,
                reason=(
                    f"entity peptide {peptide_sequence} quantifies protein group {entity_id}"
                ),
            )

        for value in sorted(
            values_by_entity.get(entity_id, ()), key=lambda item: item.sample_id
        ):
            run_contexts = tuple(
                ProteomicsEvidenceContextRef(
                    entity_type=ProteomicsEvidenceNodeKind.RUN,
                    entity_ref=run_id,
                )
                for run_id in sorted(
                    run_context.run_ids_by_sample.get(value.sample_id, ())
                )
            )
            quant_node = builder.add_quant_value(
                f"quant:{value.sample_id}:{entity_id}",
                label=f"quant {value.sample_id} {entity_id}",
                trust_class=_quant_trust_class(value.missing_value_kind),
                context_refs=(
                    ProteomicsEvidenceContextRef(
                        entity_type=ProteomicsEvidenceNodeKind.SAMPLE,
                        entity_ref=value.sample_id,
                    ),
                    ProteomicsEvidenceContextRef(
                        entity_type=ProteomicsEvidenceNodeKind.PROTEIN,
                        entity_ref=entity_id,
                    ),
                )
                + run_contexts,
            )
            builder.add_protein_quantified_by_quant_value(
                protein.node_id,
                quant_node.node_id,
                source_row_ref=f"quant:{entity_id}:{value.sample_id}",
                confidence=0.9
                if value.missing_value_kind is MissingValueKind.OBSERVED
                else 0.6,
                reason=(
                    f"sample {value.sample_id} contributes protein abundance for {entity_id} "
                    f"under condition {run_context.sample_conditions.get(value.sample_id, 'unknown')}"
                ),
            )
            if value.abundance is not None:
                builder.add_quant_value_supports_statistical_result(
                    quant_node.node_id,
                    claim.node_id,
                    source_row_ref=f"quant-support:{entity_id}:{value.sample_id}",
                    confidence=0.9
                    if value.missing_value_kind is MissingValueKind.OBSERVED
                    else 0.6,
                    reason=(
                        f"sample-level abundance for {entity_id} supports the final "
                        "statistical result"
                    ),
                )


__all__ = [
    "_add_biological_result_graph_protein_claims",
]
