# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Optional scientific export for biological hypothesis outputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.review.claims.biological_hypotheses import (
    render_biological_hypothesis_summary_tsv,
    render_biological_hypothesis_tsv,
    render_rejected_biological_hypothesis_candidate_tsv,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


@dataclass(frozen=True)
class BiologicalHypothesisExportNames:
    """Artifact names emitted for optional biological hypothesis outputs."""

    biological_hypothesis_summary_name: str | None
    biological_hypothesis_name: str | None
    rejected_hypothesis_candidate_name: str | None


def _write_biological_optional_hypothesis_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalHypothesisExportNames:
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
    return BiologicalHypothesisExportNames(
        biological_hypothesis_summary_name=biological_hypothesis_summary_name,
        biological_hypothesis_name=biological_hypothesis_name,
        rejected_hypothesis_candidate_name=rejected_hypothesis_candidate_name,
    )


__all__ = [
    "BiologicalHypothesisExportNames",
    "_write_biological_optional_hypothesis_exports",
]
