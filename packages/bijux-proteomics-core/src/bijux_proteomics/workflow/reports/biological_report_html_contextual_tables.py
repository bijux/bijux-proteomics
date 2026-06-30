# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""HTML tables for contextual biological report sections."""

from __future__ import annotations

from html import escape

from bijux_proteomics.workflow.reports.biological_report_html_support import (
    _format_optional_float,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


def _render_regulator_inference_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    regulator_report = report.regulator_inference_report
    if regulator_report is None:
        return "<p>No regulator inference report was generated.</p>"
    headers = (
        "Regulator",
        "Evidence type",
        "Signal surface",
        "Direction",
        "Score",
        "Supporting proteins",
        "Supporting sites",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.regulator)}</td>"
            f"<td>{escape(entry.evidence_type.value)}</td>"
            f"<td>{escape(entry.signal_surface.value)}</td>"
            f"<td>{escape(entry.direction.value)}</td>"
            f"<td>{entry.score:.3f}</td>"
            f"<td>{escape('; '.join(entry.supporting_protein_refs))}</td>"
            f"<td>{escape('; '.join(entry.supporting_site_keys))}</td>"
            "</tr>"
        )
        for entry in regulator_report.entries[:10]
    )
    return (
        "<p>"
        f"<strong>Regulators</strong>: {regulator_report.summary.regulator_count} | "
        f"<strong>Entries</strong>: {regulator_report.summary.entry_count} | "
        f"<strong>Site support</strong>: "
        f"{regulator_report.summary.site_regulation_entry_count} | "
        f"<strong>Abundance support</strong>: "
        f"{regulator_report.summary.protein_abundance_entry_count} | "
        f"<strong>Unresolved targets</strong>: "
        f"{regulator_report.summary.unresolved_target_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


def _render_drug_target_table_html(report: BiologicalResultReportBundle) -> str:
    drug_target_report = report.drug_target_report
    if drug_target_report is None:
        return "<p>No drug-target interpretation report was generated.</p>"
    headers = (
        "Drug",
        "Protein",
        "Relationship",
        "Evidence tier",
        "Effect",
        "Pathways",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.drug_name or entry.drug_id)}</td>"
            f"<td>{escape(entry.protein_ref)}</td>"
            f"<td>{escape(entry.relationship.value)}</td>"
            f"<td>{escape(entry.evidence_tier.value)}</td>"
            f"<td>{escape(entry.effect_direction.value)} ({entry.log2_fold_change:.3f})</td>"
            f"<td>{escape('; '.join(entry.supporting_pathway_ids))}</td>"
            "</tr>"
        )
        for entry in drug_target_report.entries[:10]
    )
    return (
        "<p>"
        f"<strong>Drugs</strong>: {drug_target_report.summary.drug_count} | "
        f"<strong>Direct targets</strong>: "
        f"{drug_target_report.summary.direct_target_entry_count} | "
        f"<strong>Indirect pathway neighbors</strong>: "
        f"{drug_target_report.summary.indirect_pathway_neighbor_entry_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


def _render_disease_phenotype_table_html(report: BiologicalResultReportBundle) -> str:
    disease_phenotype_report = report.disease_phenotype_report
    if disease_phenotype_report is None:
        return "<p>No disease or phenotype interpretation report was generated.</p>"
    headers = (
        "Kind",
        "Term",
        "Source",
        "Foreground overlap",
        "Adjusted p-value",
        "Confidence",
        "Supporting proteins",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.context_kind.value)}</td>"
            f"<td>{escape(entry.term_name or entry.term_id)}</td>"
            f"<td>{escape(entry.source_name or '')}</td>"
            f"<td>{entry.foreground_overlap_count}</td>"
            f"<td>{_format_optional_float(entry.adjusted_p_value)}</td>"
            f"<td>{escape(entry.confidence_status.value)}</td>"
            f"<td>{escape('; '.join(entry.supporting_protein_refs))}</td>"
            "</tr>"
        )
        for entry in disease_phenotype_report.entries[:10]
    )
    return (
        "<p>"
        f"<strong>Evaluated terms</strong>: "
        f"{disease_phenotype_report.summary.evaluated_term_count} | "
        f"<strong>Passing terms</strong>: "
        f"{disease_phenotype_report.summary.filter_passing_term_count} | "
        f"<strong>High-confidence terms</strong>: "
        f"{disease_phenotype_report.summary.high_confidence_term_count} | "
        f"<strong>Unknown foreground proteins</strong>: "
        f"{disease_phenotype_report.summary.unknown_foreground_protein_count} | "
        f"<strong>Unknown background proteins</strong>: "
        f"{disease_phenotype_report.summary.unknown_background_protein_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


def _render_tissue_cell_type_context_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    tissue_context_report = report.tissue_cell_type_context_report
    if tissue_context_report is None:
        return "<p>No tissue or cell-type context report was generated.</p>"
    headers = (
        "Sample",
        "Label",
        "Expected score",
        "Unexpected context",
        "Unexpected score",
        "QC warning",
        "Status",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.sample_id)}</td>"
            f"<td>{escape(entry.tissue_or_cell_type or '-')}</td>"
            f"<td>{_format_optional_float(entry.expected_marker_score)}</td>"
            f"<td>{escape(entry.highest_unexpected_context_name or entry.highest_unexpected_context_id or '-')}</td>"
            f"<td>{_format_optional_float(entry.highest_unexpected_marker_score)}</td>"
            f"<td>{escape(str(entry.qc_warning).lower())}</td>"
            f"<td>{escape(entry.status.value)}</td>"
            "</tr>"
        )
        for entry in tissue_context_report.sample_consistency_entries[:10]
    )
    summary = tissue_context_report.summary
    return (
        "<p>"
        f"<strong>Samples</strong>: {summary.sample_count} | "
        f"<strong>Labeled</strong>: {summary.labeled_sample_count} | "
        f"<strong>Marker contexts</strong>: {summary.marker_context_count} | "
        f"<strong>QC warnings</strong>: {summary.mismatch_warning_count} | "
        f"<strong>Unexpected signals</strong>: {summary.unexpected_signal_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


def _render_cohort_stratification_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    cohort_report = report.cohort_stratification_report
    if cohort_report is None:
        return "<p>No cohort stratification report was generated.</p>"
    headers = (
        "Field",
        "Left subgroup",
        "Right subgroup",
        "Entity",
        "Kind",
        "Delta",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.field_name.value)}</td>"
            f"<td>{escape(entry.left_subgroup_value)}</td>"
            f"<td>{escape(entry.right_subgroup_value)}</td>"
            f"<td>{escape(entry.entity_id)}</td>"
            f"<td>{escape(entry.candidate_kind.value)}</td>"
            f"<td>{entry.interaction_delta:.4f}</td>"
            "</tr>"
        )
        for entry in cohort_report.interaction_candidates[:10]
    )
    summary = cohort_report.summary
    return (
        "<p>"
        f"<strong>Fields</strong>: {summary.field_count} | "
        f"<strong>Supported strata</strong>: {summary.supported_stratum_count} | "
        f"<strong>Blocked strata</strong>: {summary.blocked_stratum_count} | "
        f"<strong>Subgroup effects</strong>: {summary.subgroup_effect_count} | "
        f"<strong>Interaction candidates</strong>: {summary.interaction_candidate_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


def _render_compartment_biology_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    compartment_biology_report = report.compartment_biology_report
    if compartment_biology_report is None:
        return "<p>No compartment biology report was generated.</p>"
    headers = (
        "Compartment",
        "Condition A",
        "Condition B",
        "Delta",
        "Comparison confidence",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.set_name or entry.set_id)}</td>"
            f"<td>{escape(entry.condition_a)}</td>"
            f"<td>{escape(entry.condition_b)}</td>"
            f"<td>{_format_optional_float(entry.activity_score_delta)}</td>"
            f"<td>{escape(entry.comparison_confidence_status.value)}</td>"
            "</tr>"
        )
        for entry in compartment_biology_report.activity_report.condition_comparisons[
            :10
        ]
    )
    return (
        "<p>"
        f"<strong>Compartments</strong>: {compartment_biology_report.summary.compartment_count} | "
        f"<strong>Enriched compartments</strong>: "
        f"{compartment_biology_report.summary.enriched_compartment_count} | "
        f"<strong>Low-confidence sample scores</strong>: "
        f"{compartment_biology_report.summary.low_confidence_sample_score_count} | "
        f"<strong>Unresolved members</strong>: "
        f"{compartment_biology_report.summary.unresolved_member_count} | "
        f"<strong>Unknown foreground proteins</strong>: "
        f"{compartment_biology_report.summary.unknown_foreground_protein_count} | "
        f"<strong>Unknown background proteins</strong>: "
        f"{compartment_biology_report.summary.unknown_background_protein_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


def _render_pathway_activity_table_html(report: BiologicalResultReportBundle) -> str:
    pathway_activity_report = report.pathway_activity_report
    if pathway_activity_report is None:
        return "<p>No pathway activity report was generated.</p>"
    headers = (
        "Pathway",
        "Condition A",
        "Condition B",
        "Delta",
        "Comparison confidence",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.pathway_name or entry.pathway_id)}</td>"
            f"<td>{escape(entry.condition_a)}</td>"
            f"<td>{escape(entry.condition_b)}</td>"
            f"<td>{_format_optional_float(entry.activity_score_delta)}</td>"
            f"<td>{escape(entry.comparison_confidence_status.value)}</td>"
            "</tr>"
        )
        for entry in pathway_activity_report.condition_comparisons[:10]
    )
    return (
        "<p>"
        f"<strong>Pathways</strong>: {pathway_activity_report.summary.pathway_count} | "
        f"<strong>Low-confidence sample scores</strong>: "
        f"{pathway_activity_report.summary.low_confidence_sample_score_count} | "
        f"<strong>Unresolved members</strong>: "
        f"{pathway_activity_report.summary.unresolved_member_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


def _render_complex_activity_table_html(report: BiologicalResultReportBundle) -> str:
    complex_activity_report = report.complex_activity_report
    if complex_activity_report is None:
        return "<p>No complex activity report was generated.</p>"
    headers = (
        "Complex",
        "Condition A",
        "Condition B",
        "Delta",
        "Limiting members",
        "Comparison confidence",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.complex_name or entry.complex_id)}</td>"
            f"<td>{escape(entry.condition_a)}</td>"
            f"<td>{escape(entry.condition_b)}</td>"
            f"<td>{_format_optional_float(entry.activity_score_delta)}</td>"
            f"<td>{escape('; '.join(entry.condition_b_limiting_member_ids))}</td>"
            f"<td>{escape(entry.comparison_confidence_status.value)}</td>"
            "</tr>"
        )
        for entry in complex_activity_report.condition_comparisons[:10]
    )
    return (
        "<p>"
        f"<strong>Complexes</strong>: {complex_activity_report.summary.complex_count} | "
        f"<strong>Low-confidence sample scores</strong>: "
        f"{complex_activity_report.summary.low_confidence_sample_score_count} | "
        f"<strong>Unresolved members</strong>: "
        f"{complex_activity_report.summary.unresolved_member_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )
