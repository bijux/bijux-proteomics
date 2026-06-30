# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical review-graph report contract and public builder."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
)
from bijux_proteomics.review.evidence_graph.evidence_graph import (
    ProteomicsEvidenceGraph,
    ProteomicsEvidenceGraphBuilder,
    ProteomicsEvidenceNodeKind,
)
from bijux_proteomics.review.evidence_graph.evidence_graph_downgrades import (
    EvidenceGraphFinalResultReport,
    build_evidence_graph_final_result_table,
)
from bijux_proteomics.study import ExperimentDesign, coerce_experiment_design
from bijux_proteomics.workflow.reports.biological_result_graph_protein_claims import (
    _add_biological_result_graph_protein_claims,
)
from bijux_proteomics.workflow.reports.biological_result_graph_run_context import (
    _add_biological_result_graph_run_context,
)
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics_lab.handoffs.qc_feedback import LabRunQcFeedbackReport


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
    builder = ProteomicsEvidenceGraphBuilder()
    run_context = _add_biological_result_graph_run_context(
        builder,
        experiment_design,
        lab_run_qc_feedback_report=lab_run_qc_feedback_report,
    )
    _add_biological_result_graph_protein_claims(
        builder,
        quant_table,
        differential_report,
        run_context,
        max_adjusted_p_value=max_adjusted_p_value,
        min_absolute_log2_fold_change=min_absolute_log2_fold_change,
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


__all__ = [
    "BiologicalResultGraphReport",
    "build_biological_result_graph_report",
]
