# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Scientific artifact export for biological report bundles."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow.reports.biological_report_claim_exports import (
    _write_biological_optional_claim_exports,
)
from bijux_proteomics.workflow.reports.biological_report_hypothesis_exports import (
    _write_biological_optional_hypothesis_exports,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.reports.biological_report_ranking_exports import (
    _write_biological_optional_ranking_exports,
)
from bijux_proteomics.workflow.reports.biological_report_regulator_exports import (
    _write_biological_optional_regulator_exports,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_required_exports import (
    _write_biological_required_scientific_exports,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_export_contracts import (
    BiologicalScientificExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_summary_tables import (
    render_biological_report_section_confidence_tsv as _render_section_confidence_tsv,
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

    return BiologicalScientificExportNames(
        summary_name=required_export_names.summary_name,
        differential_name=required_export_names.differential_name,
        protein_card_summary_name=required_export_names.protein_card_summary_name,
        protein_card_name=required_export_names.protein_card_name,
        protein_mechanism_card_summary_name=(
            required_export_names.protein_mechanism_card_summary_name
        ),
        protein_mechanism_card_name=required_export_names.protein_mechanism_card_name,
        evidence_graph_nodes_name=required_export_names.evidence_graph_nodes_name,
        evidence_graph_edges_name=required_export_names.evidence_graph_edges_name,
        experiment_confidence_summary_name=(
            required_export_names.experiment_confidence_summary_name
        ),
        experiment_confidence_components_name=(
            required_export_names.experiment_confidence_components_name
        ),
        section_confidence_name=required_export_names.section_confidence_name,
        evidence_aware_ranking_name=ranking_export_names.evidence_aware_ranking_name,
        claim_validation_summary_name=(
            claim_export_names.claim_validation_summary_name
        ),
        supported_claim_name=claim_export_names.supported_claim_name,
        rejected_claim_name=claim_export_names.rejected_claim_name,
        biological_hypothesis_summary_name=(
            hypothesis_export_names.biological_hypothesis_summary_name
        ),
        biological_hypothesis_name=hypothesis_export_names.biological_hypothesis_name,
        rejected_hypothesis_candidate_name=(
            hypothesis_export_names.rejected_hypothesis_candidate_name
        ),
        foreground_background_summary_name=(
            required_export_names.foreground_background_summary_name
        ),
        foreground_background_entry_name=(
            required_export_names.foreground_background_entry_name
        ),
        foreground_background_issue_name=(
            required_export_names.foreground_background_issue_name
        ),
        regulator_inference_summary_name=(
            regulator_export_names.regulator_inference_summary_name
        ),
        regulator_inference_name=regulator_export_names.regulator_inference_name,
        regulator_unresolved_name=regulator_export_names.regulator_unresolved_name,
        regulator_rejected_name=regulator_export_names.regulator_rejected_name,
        annotation_summary_name=required_export_names.annotation_summary_name,
        annotation_name=required_export_names.annotation_name,
        annotation_unmapped_name=required_export_names.annotation_unmapped_name,
    )
