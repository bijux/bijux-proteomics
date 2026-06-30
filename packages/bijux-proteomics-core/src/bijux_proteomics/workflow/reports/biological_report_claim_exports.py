# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Optional scientific export for biological claim validation outputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.review.claims.biological_claim_validation import (
    render_biological_claim_validation_summary_tsv,
    render_rejected_biological_claim_tsv,
    render_supported_biological_claim_tsv,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


@dataclass(frozen=True)
class BiologicalClaimExportNames:
    """Artifact names emitted for optional claim validation outputs."""

    claim_validation_summary_name: str | None
    supported_claim_name: str | None
    rejected_claim_name: str | None


def _write_biological_optional_claim_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalClaimExportNames:
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
    return BiologicalClaimExportNames(
        claim_validation_summary_name=claim_validation_summary_name,
        supported_claim_name=supported_claim_name,
        rejected_claim_name=rejected_claim_name,
    )


__all__ = [
    "BiologicalClaimExportNames",
    "_write_biological_optional_claim_exports",
]
