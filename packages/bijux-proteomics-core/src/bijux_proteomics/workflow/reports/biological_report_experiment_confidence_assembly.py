# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Experiment-confidence assembly for biological report bundles."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.lab.protocol_context import (
    parse_lab_protocol_context_table,
    require_single_lab_protocol_context,
)
from bijux_proteomics.quantification.contracts import LabelFreeQuantTable
from bijux_proteomics.quantification.missingness import (
    build_missingness_condition_summary_report,
)
from bijux_proteomics.quantification.statistics import build_power_estimation_report
from bijux_proteomics.study import (
    ExperimentConfidenceReport,
    ExperimentDesign,
    LcmsRunQcReport,
    QcRunAssessmentReport,
    build_experiment_confidence_report,
    build_experiment_feasibility_report,
    build_protocol_consistency_report,
)
from bijux_proteomics.workflow.cards.protein_evidence_cards import (
    ProteinEvidenceCardReport,
)


def _build_biological_experiment_confidence_report(
    *,
    normalized_table: LabelFreeQuantTable,
    experiment_design: ExperimentDesign,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    protein_cards: ProteinEvidenceCardReport,
    resolved_condition_a: str,
    resolved_condition_b: str,
    protocol_context_tsv_path: Path | None,
    run_qc_reports: tuple[LcmsRunQcReport, ...],
    run_qc_assessments: tuple[QcRunAssessmentReport, ...],
) -> ExperimentConfidenceReport:
    feasibility_report = build_experiment_feasibility_report(
        experiment_design,
        condition_a=resolved_condition_a,
        condition_b=resolved_condition_b,
    )
    protocol_consistency_report = None
    if protocol_context_tsv_path is not None:
        protocol_consistency_report = build_protocol_consistency_report(
            require_single_lab_protocol_context(
                parse_lab_protocol_context_table(protocol_context_tsv_path)
            ),
            run_qc_report=run_qc_reports[0] if len(run_qc_reports) == 1 else None,
        )
    return build_experiment_confidence_report(
        experiment_design,
        validity_report=feasibility_report.validity_report,
        feasibility_report=feasibility_report,
        missingness_condition_summary_report=build_missingness_condition_summary_report(
            normalized_table,
            design_entries=design_entries,
        ),
        power_estimation_report=build_power_estimation_report(
            normalized_table,
            design_entries,
        ),
        run_qc_reports=run_qc_reports,
        run_qc_assessments=run_qc_assessments,
        protocol_consistency_report=protocol_consistency_report,
        warning_card_count=protein_cards.summary.warning_card_count,
        protein_card_count=protein_cards.summary.protein_result_count,
    )


__all__ = ["_build_biological_experiment_confidence_report"]
