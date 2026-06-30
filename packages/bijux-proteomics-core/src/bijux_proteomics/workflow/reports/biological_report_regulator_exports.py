# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Optional scientific export for biological regulator inference outputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interpretation import (
    render_regulator_inference_summary_tsv,
    render_regulator_inference_tsv,
    render_rejected_regulator_evidence_tsv,
    render_unresolved_regulator_target_tsv,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


@dataclass(frozen=True)
class BiologicalRegulatorExportNames:
    """Artifact names emitted for optional regulator inference outputs."""

    regulator_inference_summary_name: str | None
    regulator_inference_name: str | None
    regulator_unresolved_name: str | None
    regulator_rejected_name: str | None


def _write_biological_optional_regulator_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalRegulatorExportNames:
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
    return BiologicalRegulatorExportNames(
        regulator_inference_summary_name=regulator_inference_summary_name,
        regulator_inference_name=regulator_inference_name,
        regulator_unresolved_name=regulator_unresolved_name,
        regulator_rejected_name=regulator_rejected_name,
    )


__all__ = [
    "BiologicalRegulatorExportNames",
    "_write_biological_optional_regulator_exports",
]
