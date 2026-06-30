# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Optional scientific artifact export for biological report bundles."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interpretation import (
    render_regulator_inference_summary_tsv,
    render_regulator_inference_tsv,
    render_rejected_regulator_evidence_tsv,
    render_unresolved_regulator_target_tsv,
)
from bijux_proteomics.review.belief.evidence_aware_ranking import (
    render_evidence_aware_ranking_tsv,
)
from bijux_proteomics.review.claims.biological_claim_validation import (
    render_biological_claim_validation_summary_tsv,
    render_rejected_biological_claim_tsv,
    render_supported_biological_claim_tsv,
)
from bijux_proteomics.review.claims.biological_hypotheses import (
    render_biological_hypothesis_summary_tsv,
    render_biological_hypothesis_tsv,
    render_rejected_biological_hypothesis_candidate_tsv,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


def _write_biological_optional_ranking_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> tuple[str | None]:
    evidence_aware_ranking_name = None
    if report.evidence_aware_ranking_report is not None:
        evidence_aware_ranking_name = "biological_evidence_aware_ranking.tsv"
        write_output_table_tsv(
            output_dir / evidence_aware_ranking_name,
            render_evidence_aware_ranking_tsv(report.evidence_aware_ranking_report),
        )
    return (evidence_aware_ranking_name,)


def _write_biological_optional_claim_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> tuple[str | None, str | None, str | None]:
    claim_validation_summary_name = None
    supported_claim_name = None
    rejected_claim_name = None
    if report.claim_validation_report is not None:
        claim_validation_summary_name = "biological_claim_validation_summary.tsv"
        supported_claim_name = "biological_supported_claims.tsv"
        rejected_claim_name = "biological_rejected_claims.tsv"
        write_output_table_tsv(
            output_dir / claim_validation_summary_name,
            render_biological_claim_validation_summary_tsv(
                report.claim_validation_report
            ),
        )
        write_output_table_tsv(
            output_dir / supported_claim_name,
            render_supported_biological_claim_tsv(report.claim_validation_report),
        )
        write_output_table_tsv(
            output_dir / rejected_claim_name,
            render_rejected_biological_claim_tsv(report.claim_validation_report),
        )
    return (
        claim_validation_summary_name,
        supported_claim_name,
        rejected_claim_name,
    )


def _write_biological_optional_hypothesis_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> tuple[str | None, str | None, str | None]:
    biological_hypothesis_summary_name = None
    biological_hypothesis_name = None
    rejected_hypothesis_candidate_name = None
    if report.biological_hypothesis_report is not None:
        biological_hypothesis_summary_name = "biological_hypothesis_summary.tsv"
        biological_hypothesis_name = "biological_hypotheses.tsv"
        rejected_hypothesis_candidate_name = (
            "biological_rejected_hypothesis_candidates.tsv"
        )
        write_output_table_tsv(
            output_dir / biological_hypothesis_summary_name,
            render_biological_hypothesis_summary_tsv(
                report.biological_hypothesis_report
            ),
        )
        write_output_table_tsv(
            output_dir / biological_hypothesis_name,
            render_biological_hypothesis_tsv(report.biological_hypothesis_report),
        )
        write_output_table_tsv(
            output_dir / rejected_hypothesis_candidate_name,
            render_rejected_biological_hypothesis_candidate_tsv(
                report.biological_hypothesis_report
            ),
        )
    return (
        biological_hypothesis_summary_name,
        biological_hypothesis_name,
        rejected_hypothesis_candidate_name,
    )


def _write_biological_optional_regulator_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> tuple[str | None, str | None, str | None, str | None]:
    regulator_inference_summary_name = None
    regulator_inference_name = None
    regulator_unresolved_name = None
    regulator_rejected_name = None
    if (
        report.regulator_evidence_import_report is not None
        and report.regulator_inference_report is not None
    ):
        regulator_inference_summary_name = "biological_regulator_inference_summary.tsv"
        regulator_inference_name = "biological_regulator_inference.tsv"
        regulator_unresolved_name = "biological_regulator_inference_unresolved.tsv"
        regulator_rejected_name = "biological_regulator_evidence_rejected.tsv"
        write_output_table_tsv(
            output_dir / regulator_inference_summary_name,
            render_regulator_inference_summary_tsv(report.regulator_inference_report),
        )
        write_output_table_tsv(
            output_dir / regulator_inference_name,
            render_regulator_inference_tsv(report.regulator_inference_report),
        )
        write_output_table_tsv(
            output_dir / regulator_unresolved_name,
            render_unresolved_regulator_target_tsv(report.regulator_inference_report),
        )
        write_output_table_tsv(
            output_dir / regulator_rejected_name,
            render_rejected_regulator_evidence_tsv(
                report.regulator_evidence_import_report
            ),
        )
    return (
        regulator_inference_summary_name,
        regulator_inference_name,
        regulator_unresolved_name,
        regulator_rejected_name,
    )


__all__ = [
    "_write_biological_optional_claim_exports",
    "_write_biological_optional_hypothesis_exports",
    "_write_biological_optional_ranking_exports",
    "_write_biological_optional_regulator_exports",
]
