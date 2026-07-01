# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Scientific artifact export for biological report bundles."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.reports.biological_report_claim_exports import (
    _write_biological_optional_claim_exports,
)
from bijux_proteomics.workflow.reports.biological_report_hypothesis_exports import (
    _write_biological_optional_hypothesis_exports,
)
from bijux_proteomics.workflow.reports.biological_report_ranking_exports import (
    _write_biological_optional_ranking_exports,
)
from bijux_proteomics.workflow.reports.biological_report_regulator_exports import (
    _write_biological_optional_regulator_exports,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_export_contracts import (
    BiologicalScientificExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_export_name_building import (
    _build_biological_scientific_export_names,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_required_exports import (
    _write_biological_required_scientific_exports,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_summary_tables import (
    render_biological_report_section_confidence_tsv as _render_section_confidence_tsv,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_summary_tables import (
    render_biological_result_report_summary_tsv as _render_report_summary_tsv,
)


def render_biological_result_report_summary_tsv(
    report: BiologicalResultReportBundle,
) -> str:
    return _render_report_summary_tsv(report)


def render_biological_report_section_confidence_tsv(
    report: BiologicalResultReportBundle,
) -> str:
    return _render_section_confidence_tsv(report)


def write_biological_scientific_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalScientificExportNames:
    """Write core scientific report artifacts."""
    report_summary_tsv = render_biological_result_report_summary_tsv(report)
    section_confidence_tsv = render_biological_report_section_confidence_tsv(report)
    required_export_names = _write_biological_required_scientific_exports(
        report,
        output_dir,
        report_summary_tsv=report_summary_tsv,
        section_confidence_tsv=section_confidence_tsv,
    )

    ranking_export_names = _write_biological_optional_ranking_exports(
        report,
        output_dir,
    )
    claim_export_names = _write_biological_optional_claim_exports(report, output_dir)
    hypothesis_export_names = _write_biological_optional_hypothesis_exports(
        report, output_dir
    )
    regulator_export_names = _write_biological_optional_regulator_exports(
        report, output_dir
    )

    return _build_biological_scientific_export_names(
        required_export_names=required_export_names,
        ranking_export_names=ranking_export_names,
        claim_export_names=claim_export_names,
        hypothesis_export_names=hypothesis_export_names,
        regulator_export_names=regulator_export_names,
    )
