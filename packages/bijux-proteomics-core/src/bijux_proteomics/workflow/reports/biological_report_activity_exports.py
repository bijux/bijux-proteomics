# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Optional activity artifact export for biological report bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalActivityReportBundle,
)
from bijux_proteomics.workflow.reports.biological_report_compartment_activity_exports import (
    _write_biological_compartment_activity_exports,
)
from bijux_proteomics.workflow.reports.biological_report_complex_activity_exports import (
    _write_biological_complex_activity_exports,
)
from bijux_proteomics.workflow.reports.biological_report_pathway_activity_exports import (
    _write_biological_pathway_activity_exports,
)


@dataclass(frozen=True)
class BiologicalActivityExportNames:
    """Artifact names emitted for optional biological activity sections."""

    compartment_summary_name: str | None
    compartment_enrichment_name: str | None
    compartment_activity_matrix_name: str | None
    compartment_activity_sample_name: str | None
    compartment_activity_condition_name: str | None
    compartment_activity_comparison_name: str | None
    compartment_activity_unresolved_name: str | None
    compartment_unknown_name: str | None
    pathway_card_name: str | None
    pathway_activity_summary_name: str | None
    pathway_activity_matrix_name: str | None
    pathway_activity_sample_name: str | None
    pathway_activity_condition_name: str | None
    pathway_activity_comparison_name: str | None
    pathway_activity_member_name: str | None
    pathway_activity_unresolved_name: str | None
    complex_activity_summary_name: str | None
    complex_activity_matrix_name: str | None
    complex_activity_sample_name: str | None
    complex_activity_condition_name: str | None
    complex_activity_comparison_name: str | None
    complex_activity_member_name: str | None
    complex_activity_unresolved_name: str | None


def write_biological_activity_exports(
    report: BiologicalActivityReportBundle,
    output_dir: Path,
) -> BiologicalActivityExportNames:
    """Write optional compartment, pathway, and complex activity artifacts."""

    compartment_export_names = _write_biological_compartment_activity_exports(
        report, output_dir
    )
    pathway_export_names = _write_biological_pathway_activity_exports(
        report, output_dir
    )
    complex_export_names = _write_biological_complex_activity_exports(
        report, output_dir
    )

    return BiologicalActivityExportNames(
        compartment_summary_name=compartment_export_names.summary_name,
        compartment_enrichment_name=compartment_export_names.enrichment_name,
        compartment_activity_matrix_name=(
            compartment_export_names.activity_matrix_name
        ),
        compartment_activity_sample_name=(
            compartment_export_names.activity_sample_name
        ),
        compartment_activity_condition_name=(
            compartment_export_names.activity_condition_name
        ),
        compartment_activity_comparison_name=(
            compartment_export_names.activity_comparison_name
        ),
        compartment_activity_unresolved_name=(
            compartment_export_names.activity_unresolved_name
        ),
        compartment_unknown_name=compartment_export_names.unknown_name,
        pathway_card_name=pathway_export_names.card_name,
        pathway_activity_summary_name=pathway_export_names.activity_summary_name,
        pathway_activity_matrix_name=pathway_export_names.activity_matrix_name,
        pathway_activity_sample_name=pathway_export_names.activity_sample_name,
        pathway_activity_condition_name=pathway_export_names.activity_condition_name,
        pathway_activity_comparison_name=(
            pathway_export_names.activity_comparison_name
        ),
        pathway_activity_member_name=pathway_export_names.activity_member_name,
        pathway_activity_unresolved_name=(
            pathway_export_names.activity_unresolved_name
        ),
        complex_activity_summary_name=complex_export_names.activity_summary_name,
        complex_activity_matrix_name=complex_export_names.activity_matrix_name,
        complex_activity_sample_name=complex_export_names.activity_sample_name,
        complex_activity_condition_name=complex_export_names.activity_condition_name,
        complex_activity_comparison_name=(
            complex_export_names.activity_comparison_name
        ),
        complex_activity_member_name=complex_export_names.activity_member_name,
        complex_activity_unresolved_name=(
            complex_export_names.activity_unresolved_name
        ),
    )
