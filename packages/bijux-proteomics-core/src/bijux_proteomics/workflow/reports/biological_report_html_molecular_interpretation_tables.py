# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""HTML tables for molecular interpretation report sections."""

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
