# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Quant-value evidence wiring for biological result graph protein claims."""

from __future__ import annotations

from bijux_proteomics.quantification.contracts import (
    MissingValueKind,
    QuantValue,
)
from bijux_proteomics.review.evidence_graph.evidence_graph import (
    ProteomicsEvidenceContextRef,
    ProteomicsEvidenceGraphBuilder,
    ProteomicsEvidenceNodeKind,
)
from bijux_proteomics.workflow.reports.graph.claim_policy import (
    _quant_trust_class,
)
from bijux_proteomics.workflow.reports.graph.run_context import (
    BiologicalResultGraphRunContext,
)


def _group_quant_values_by_entity(
    quant_values: tuple[QuantValue, ...],
) -> dict[str, list[QuantValue]]:
    values_by_entity: dict[str, list[QuantValue]] = {}
    for value in quant_values:
        values_by_entity.setdefault(value.entity_id, []).append(value)
    return values_by_entity


def _add_biological_result_graph_quant_support(
    builder: ProteomicsEvidenceGraphBuilder,
    *,
    protein_node_id: str,
    claim_node_id: str,
    entity_id: str,
    quant_values: tuple[QuantValue, ...],
    run_context: BiologicalResultGraphRunContext,
) -> None:
    for value in sorted(quant_values, key=lambda item: item.sample_id):
        run_contexts = tuple(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.RUN,
                entity_ref=run_id,
            )
            for run_id in sorted(run_context.run_ids_by_sample.get(value.sample_id, ()))
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
        quant_confidence = (
            0.9 if value.missing_value_kind is MissingValueKind.OBSERVED else 0.6
        )
        builder.add_protein_quantified_by_quant_value(
            protein_node_id,
            quant_node.node_id,
            source_row_ref=f"quant:{entity_id}:{value.sample_id}",
            confidence=quant_confidence,
            reason=(
                f"sample {value.sample_id} contributes protein abundance for {entity_id} "
                f"under condition {run_context.sample_conditions.get(value.sample_id, 'unknown')}"
            ),
        )
        if value.abundance is not None:
            builder.add_quant_value_supports_statistical_result(
                quant_node.node_id,
                claim_node_id,
                source_row_ref=f"quant-support:{entity_id}:{value.sample_id}",
                confidence=quant_confidence,
                reason=(
                    f"sample-level abundance for {entity_id} supports the final "
                    "statistical result"
                ),
            )
