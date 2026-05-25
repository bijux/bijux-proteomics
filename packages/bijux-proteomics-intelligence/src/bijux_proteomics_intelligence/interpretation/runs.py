# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Run-level interpretation summaries over QC and quant evidence."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.quantification import LabelFreeQuantTable
from bijux_proteomics.lab.qc import (
    LcmsRunQcReport,
    QcAssessmentSeverity,
    QcRunAssessmentReport,
)
from bijux_proteomics_foundation import JsonModel


class RunInterpretationSignal(JsonModel):
    """One compact run-level interpretation signal."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    severity: QcAssessmentSeverity
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)


class RunInterpretationSummary(JsonModel):
    """Reviewable summary of one proteomics run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    condition: str | None = None
    spectrum_count: int = Field(..., ge=0)
    identified_spectrum_count: int = Field(..., ge=0)
    psm_count: int = Field(..., ge=0)
    quantified_entity_count: int = Field(..., ge=0)
    qc_blocked: bool
    major_signals: tuple[RunInterpretationSignal, ...] = Field(default_factory=tuple)
    interpretation_summary: str = Field(..., min_length=1)


def build_run_interpretation_summary(
    run_report: LcmsRunQcReport,
    run_assessment: QcRunAssessmentReport,
    *,
    quant_table: LabelFreeQuantTable | None = None,
) -> RunInterpretationSummary:
    """Build a concise run-level interpretation with QC-aware signals."""
    signals: list[RunInterpretationSignal] = []
    quant_entity_count = 0 if quant_table is None else len(quant_table.entity_ids)
    if run_assessment.blocked:
        signals.append(
            RunInterpretationSignal(
                code="qc-blocked",
                summary="QC policy blocks routine downstream interpretation for this run.",
                severity=QcAssessmentSeverity.FAILED,
                evidence_refs=("qc_run_assessment_report",),
            )
        )
    elif run_report.identification_rate >= 0.2:
        signals.append(
            RunInterpretationSignal(
                code="identification-ready",
                summary="Identification rate is high enough for routine interpretation.",
                severity=QcAssessmentSeverity.PASSED,
                evidence_refs=("lcms_run_qc_report.identification_rate",),
            )
        )
    if run_report.contaminant_summary.contaminant_psm_fraction >= 0.1:
        signals.append(
            RunInterpretationSignal(
                code="contaminant-pressure",
                summary="Contaminant burden is high enough to color biological interpretation.",
                severity=QcAssessmentSeverity.WARNING,
                evidence_refs=("lcms_run_qc_report.contaminant_summary",),
            )
        )
    if quant_table is not None and quant_table.entity_ids:
        signals.append(
            RunInterpretationSignal(
                code="quant-available",
                summary=f"{len(quant_table.entity_ids)} quantified entities are available for follow-on interpretation.",
                severity=QcAssessmentSeverity.PASSED,
                evidence_refs=("label_free_quant_table",),
            )
        )
    if not signals:
        signals.append(
            RunInterpretationSignal(
                code="interpretation-limited",
                summary="Run has limited stable signal and should be interpreted cautiously.",
                severity=QcAssessmentSeverity.NOT_ASSESSED,
                evidence_refs=("lcms_run_qc_report",),
            )
        )
    return RunInterpretationSummary(
        run_id=run_report.run_id,
        sample_id=run_report.sample_id,
        condition=run_report.condition,
        spectrum_count=run_report.spectrum_count,
        identified_spectrum_count=run_report.identified_spectrum_count,
        psm_count=run_report.psm_count,
        quantified_entity_count=quant_entity_count,
        qc_blocked=run_assessment.blocked,
        major_signals=tuple(signals),
        interpretation_summary=signals[0].summary,
    )
