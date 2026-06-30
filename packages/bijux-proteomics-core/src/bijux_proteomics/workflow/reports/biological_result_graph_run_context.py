# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Run and sample context assembly for biological result graphs."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from bijux_proteomics.review.evidence_graph.evidence_graph import (
    ProteomicsEvidenceContextRef,
    ProteomicsEvidenceGraphBuilder,
    ProteomicsEvidenceNode,
    ProteomicsEvidenceNodeKind,
)
from bijux_proteomics.study import ExperimentDesign
from bijux_proteomics.workflow.reports.biological_report_graph_qc import (
    _attach_lab_run_qc_feedback,
)

if TYPE_CHECKING:
    from bijux_proteomics_lab.handoffs.qc_feedback import LabRunQcFeedbackReport


class BiologicalResultGraphRunContext(NamedTuple):
    """Run-context mappings needed while populating quant-value graph nodes."""

    sample_conditions: dict[str, str]
    run_ids_by_sample: dict[str, list[str]]


def _add_biological_result_graph_run_context(
    builder: ProteomicsEvidenceGraphBuilder,
    experiment_design: ExperimentDesign,
    *,
    lab_run_qc_feedback_report: LabRunQcFeedbackReport | None = None,
) -> BiologicalResultGraphRunContext:
    sample_conditions = {
        sample.sample_id: sample.condition for sample in experiment_design.samples
    }
    run_nodes_by_id: dict[str, ProteomicsEvidenceNode] = {}
    run_sample_ids_by_id: dict[str, str] = {}
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
            reason=(
                f"design entry assigns spectra file {entry.spectra_file} "
                f"to sample {entry.sample_id}"
            ),
        )
    if lab_run_qc_feedback_report is not None:
        _attach_lab_run_qc_feedback(
            builder,
            run_nodes_by_id=run_nodes_by_id,
            run_sample_ids_by_id=run_sample_ids_by_id,
            feedback_report=lab_run_qc_feedback_report,
        )
    return BiologicalResultGraphRunContext(
        sample_conditions=sample_conditions,
        run_ids_by_sample=run_ids_by_sample,
    )


__all__ = [
    "BiologicalResultGraphRunContext",
    "_add_biological_result_graph_run_context",
]
