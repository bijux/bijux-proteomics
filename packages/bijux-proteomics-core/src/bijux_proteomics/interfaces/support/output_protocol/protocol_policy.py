# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Protocol context and interpretation policy helpers for interface workflows."""

from __future__ import annotations

from bijux_proteomics.lab.protocol_consistency import ProtocolConsistencyReport
from bijux_proteomics.lab.protocol_context import LabProtocolContextEntry
from bijux_proteomics.lab.qc import LcmsRunQcReport
from bijux_proteomics.multiplex.reporter_ion_import import TmtReporterImportReport
from bijux_proteomics.ptm.contracts import PtmEvidenceParseReport

from ..imports import *  # noqa: F401,F403


def _load_protocol_context(
    protocol_context_tsv_path: Path | None,
) -> LabProtocolContextEntry | None:
    if protocol_context_tsv_path is None:
        return None
    return require_single_lab_protocol_context(
        parse_lab_protocol_context_table(protocol_context_tsv_path)
    )


def _build_protocol_consistency_report_from_inputs(
    *,
    protocol_context_tsv_path: Path,
    run_qc_report: LcmsRunQcReport | None = None,
    reporter_table_path: Path | None = None,
    ptm_evidence_tsv_path: Path | None = None,
) -> ProtocolConsistencyReport:
    protocol_context = _load_protocol_context(protocol_context_tsv_path)
    if protocol_context is None:  # pragma: no cover
        raise ValueError("protocol context is required")
    reporter_import_report: TmtReporterImportReport | None = None
    reporter_input_issue = None
    if reporter_table_path is not None:
        try:
            reporter_import_report = parse_tmt_reporter_table(reporter_table_path)
        except Exception as exc:  # noqa: BLE001
            reporter_input_issue = str(exc)
    ptm_evidence_report: PtmEvidenceParseReport | None = None
    ptm_input_issue = None
    if ptm_evidence_tsv_path is not None:
        try:
            ptm_evidence_report = parse_ptm_localization_tsv(ptm_evidence_tsv_path)
        except Exception as exc:  # noqa: BLE001
            ptm_input_issue = str(exc)
    return build_protocol_consistency_report(
        protocol_context,
        run_qc_report=run_qc_report,
        reporter_import_report=reporter_import_report,
        ptm_evidence_report=ptm_evidence_report,
        reporter_input_issue=reporter_input_issue,
        ptm_input_issue=ptm_input_issue,
    )


def _build_protocol_aware_selection_policy(
    *,
    protocol_context_tsv_path: Path | None,
    max_adjusted_p_value: float | None,
    min_absolute_log2_fold_change: float | None,
    heatmap_max_entity_count: int | None,
    heatmap_min_observed_fraction: float | None,
) -> BiologicalResultSelectionPolicy | None:
    if (
        protocol_context_tsv_path is None
        and max_adjusted_p_value is None
        and min_absolute_log2_fold_change is None
        and heatmap_max_entity_count is None
        and heatmap_min_observed_fraction is None
    ):
        return None

    baseline = BiologicalResultSelectionPolicy()
    protocol_context = _load_protocol_context(protocol_context_tsv_path)
    if protocol_context is not None:
        interpretation_profile = build_lab_protocol_interpretation_profile(
            protocol_context
        )
        baseline = baseline.model_copy(
            update={
                "max_adjusted_p_value": interpretation_profile.max_adjusted_p_value,
                "min_absolute_log2_fold_change": (
                    interpretation_profile.min_absolute_log2_fold_change
                ),
                "heatmap_max_entity_count": (
                    interpretation_profile.heatmap_max_entity_count
                ),
            }
        )
    return baseline.model_copy(
        update={
            "max_adjusted_p_value": (
                baseline.max_adjusted_p_value
                if max_adjusted_p_value is None
                else max_adjusted_p_value
            ),
            "min_absolute_log2_fold_change": (
                baseline.min_absolute_log2_fold_change
                if min_absolute_log2_fold_change is None
                else min_absolute_log2_fold_change
            ),
            "heatmap_max_entity_count": (
                baseline.heatmap_max_entity_count
                if heatmap_max_entity_count is None
                else heatmap_max_entity_count
            ),
            "heatmap_min_observed_fraction": (
                baseline.heatmap_min_observed_fraction
                if heatmap_min_observed_fraction is None
                else heatmap_min_observed_fraction
            ),
        }
    )

