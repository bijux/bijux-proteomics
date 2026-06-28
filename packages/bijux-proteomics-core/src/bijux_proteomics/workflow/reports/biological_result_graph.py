# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical review-graph assembly for biological result reporting."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
    MissingValueKind,
)
from bijux_proteomics.quantification.contracts.matrix_models import QuantValue
from bijux_proteomics.review import (
    EvidenceGraphFinalResultReport,
    ProteomicsEvidenceContextRef,
    ProteomicsEvidenceGraph,
    ProteomicsEvidenceGraphBuilder,
    ProteomicsEvidenceNodeKind,
    build_evidence_graph_final_result_table,
)
from bijux_proteomics.review.evidence_graph.evidence_graph import ProteomicsEvidenceNode
from bijux_proteomics.study import ExperimentDesign, coerce_experiment_design
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics_lab.handoffs.qc_feedback import (
        LabRunQcFeedbackEntry,
        LabRunQcFeedbackReport,
    )


class BiologicalResultGraphReport(JsonModel):
    """Review-graph bundle that anchors final biological protein claims."""

    model_config = ConfigDict(extra="forbid")

    graph: ProteomicsEvidenceGraph
    final_results: EvidenceGraphFinalResultReport
    protein_claim_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


def build_biological_result_graph_report(
    quant_table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    lab_run_qc_feedback_report: LabRunQcFeedbackReport | None = None,
) -> BiologicalResultGraphReport:
    """Build one canonical review graph for graph-backed biological final reports."""

    experiment_design = coerce_experiment_design(design_entries)
    design_entries = experiment_design.entries
    builder = ProteomicsEvidenceGraphBuilder()
    sample_conditions = {
        sample.sample_id: sample.condition for sample in experiment_design.samples
    }
    run_nodes_by_id: dict[str, ProteomicsEvidenceNode] = {}
    run_sample_ids_by_id = {}
    run_ids_by_sample: dict[str, list[str]] = {}
    for entry in experiment_design.runs:
        sample = builder.add_sample(
            entry.sample_id,
            label=entry.sample_id,
            trust_class="high",
        )
        run = builder.add_run(
            entry.spectra_file,
            label=entry.spectra_file,
            trust_class="high",
            context_refs=(
                ProteomicsEvidenceContextRef(
                    entity_type=ProteomicsEvidenceNodeKind.SAMPLE,
                    entity_ref=entry.sample_id,
                ),
            ),
        )
        run_nodes_by_id[entry.spectra_file] = run
        run_sample_ids_by_id[entry.spectra_file] = entry.sample_id
        run_ids_by_sample.setdefault(entry.sample_id, []).append(entry.spectra_file)
        builder.add_sample_contains_run(
            sample.node_id,
            run.node_id,
            source_row_ref=f"design:{entry.sample_id}",
            confidence=1.0,
            reason=f"design entry assigns spectra file {entry.spectra_file} to sample {entry.sample_id}",
        )
    if lab_run_qc_feedback_report is not None:
        _attach_lab_run_qc_feedback(
            builder,
            run_nodes_by_id=run_nodes_by_id,
            run_sample_ids_by_id=run_sample_ids_by_id,
            feedback_report=lab_run_qc_feedback_report,
        )

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
                reason=f"entity peptide {peptide_sequence} maps to protein group {entity_id}",
            )
            builder.add_peptide_quantifies_protein(
                peptide.node_id,
                protein.node_id,
                source_row_ref=f"quantifying:{entity_id}:{peptide_sequence}",
                confidence=0.9,
                reason=f"entity peptide {peptide_sequence} quantifies protein group {entity_id}",
            )

        for value in sorted(
            values_by_entity.get(entity_id, ()), key=lambda item: item.sample_id
        ):
            run_contexts = tuple(
                ProteomicsEvidenceContextRef(
                    entity_type=ProteomicsEvidenceNodeKind.RUN,
                    entity_ref=run_id,
                )
                for run_id in sorted(run_ids_by_sample.get(value.sample_id, ()))
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
                    f"under condition {sample_conditions.get(value.sample_id, 'unknown')}"
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
                    reason=f"sample-level abundance for {entity_id} supports the final statistical result",
                )

    graph = builder.build()
    final_results = build_evidence_graph_final_result_table(graph)
    protein_claim_count = sum(
        1
        for entry in final_results.entries
        if entry.subject_node_kind is ProteomicsEvidenceNodeKind.PROTEIN
    )
    return BiologicalResultGraphReport(
        graph=graph,
        final_results=final_results,
        protein_claim_count=protein_claim_count,
        note=(
            "biological result graph reporting builds one canonical review graph over "
            "protein groups, quantifying peptides, sample abundances, and final statistical "
            "results so the final report claim surface is generated from graph-owned entries"
        ),
    )


def _attach_lab_run_qc_feedback(
    builder: ProteomicsEvidenceGraphBuilder,
    *,
    run_nodes_by_id: dict[str, ProteomicsEvidenceNode],
    run_sample_ids_by_id: dict[str, str],
    feedback_report: LabRunQcFeedbackReport,
) -> None:
    for entry in feedback_report.entries:
        run = run_nodes_by_id.get(entry.run_id)
        if run is None:
            raise ValueError(
                f"lab run qc feedback references an unknown workflow run: {entry.run_id}"
            )
        expected_sample_id = run_sample_ids_by_id[entry.run_id]
        if entry.sample_id != expected_sample_id:
            raise ValueError(
                "lab run qc feedback sample does not match the workflow design for "
                f"run {entry.run_id}: expected {expected_sample_id}, got {entry.sample_id}"
            )
        decision = builder.add_qc_decision(
            f"lab:{entry.run_id}",
            label=f"lab qc decision {entry.run_id}",
            claim_state=_qc_claim_state(entry),
            trust_class=_qc_trust_class(entry),
            context_refs=(
                ProteomicsEvidenceContextRef(
                    entity_type=ProteomicsEvidenceNodeKind.RUN,
                    entity_ref=entry.run_id,
                ),
                ProteomicsEvidenceContextRef(
                    entity_type=ProteomicsEvidenceNodeKind.SAMPLE,
                    entity_ref=entry.sample_id,
                ),
            ),
        )
        builder.add_run_governed_by_qc_decision(
            run.node_id,
            decision.node_id,
            source_row_ref=entry.source_refs[0]
            if entry.source_refs
            else f"lab_qc:{entry.run_id}",
            confidence=max(0.05, min(0.99, entry.composite_quality)),
            reason=entry.note,
        )


def _qc_claim_state(entry: LabRunQcFeedbackEntry) -> str:
    from bijux_proteomics_lab.handoffs.qc_feedback import LabRunQcFeedbackStatus

    if entry.status is LabRunQcFeedbackStatus.FAILED:
        return "failed"
    if entry.status is LabRunQcFeedbackStatus.CAUTION:
        return "caution"
    return "passed"


def _qc_trust_class(entry: LabRunQcFeedbackEntry) -> str:
    from bijux_proteomics_lab.handoffs.qc_feedback import LabRunQcFeedbackStatus

    if entry.status is LabRunQcFeedbackStatus.FAILED:
        return "low"
    if entry.status is LabRunQcFeedbackStatus.CAUTION:
        return "medium"
    return "high"


def _protein_label(entity_id: str, quant_table: LabelFreeQuantTable) -> str:
    protein_refs = quant_table.entity_protein_refs.get(entity_id, ())
    return protein_refs[0] if protein_refs else entity_id


def _protein_trust_class(entry: DifferentialAbundanceEntry) -> str:
    if min(entry.observations_a, entry.observations_b) <= 1:
        return "single_run_only"
    return "high"


def _quant_trust_class(missing_value_kind: MissingValueKind) -> str:
    if missing_value_kind is MissingValueKind.OBSERVED:
        return "high"
    return "imputed"


def _claim_state(
    entry: DifferentialAbundanceEntry,
    *,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
) -> str:
    adjusted = entry.adjusted_p_value
    if adjusted is None:
        return "unchanged"
    if adjusted > max_adjusted_p_value:
        return "unchanged"
    if abs(entry.log2_fold_change) < min_absolute_log2_fold_change:
        return "unchanged"
    return "upregulated" if entry.log2_fold_change >= 0.0 else "downregulated"


def _claim_confidence(entry: DifferentialAbundanceEntry) -> float:
    adjusted = 1.0 if entry.adjusted_p_value is None else entry.adjusted_p_value
    return max(0.05, min(0.99, 1.0 - adjusted))
