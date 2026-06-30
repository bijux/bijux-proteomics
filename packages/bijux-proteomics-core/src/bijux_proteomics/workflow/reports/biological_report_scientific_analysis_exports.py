# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Analysis-owned scientific artifact export for biological report bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.quantification.statistics import (
    render_differential_abundance_tsv,
)
from bijux_proteomics.review.evidence_graph.evidence_graph_export import (
    export_proteomics_evidence_graph,
    render_proteomics_evidence_graph_edges_tsv,
    render_proteomics_evidence_graph_nodes_tsv,
)
from bijux_proteomics.study import (
    render_experiment_confidence_component_tsv,
    render_experiment_confidence_summary_tsv,
)
from bijux_proteomics.workflow.cards.protein_evidence_cards import (
    render_protein_evidence_card_summary_tsv,
    render_protein_evidence_card_tsv,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    render_protein_mechanism_card_summary_tsv,
    render_protein_mechanism_card_tsv,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


@dataclass(frozen=True)
class BiologicalScientificAnalysisExportNames:
    """Artifact names emitted for analysis-owned scientific outputs."""

    summary_name: str
    differential_name: str
    protein_card_summary_name: str
    protein_card_name: str
    protein_mechanism_card_summary_name: str
    protein_mechanism_card_name: str
    evidence_graph_nodes_name: str
    evidence_graph_edges_name: str
    experiment_confidence_summary_name: str
    experiment_confidence_components_name: str
    section_confidence_name: str


def _write_biological_analysis_scientific_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
    *,
    report_summary_tsv: str,
    section_confidence_tsv: str,
) -> BiologicalScientificAnalysisExportNames:
    summary_name = "biological_report_summary.tsv"
    differential_name = "biological_differential.tsv"
    protein_card_summary_name = "biological_protein_card_summary.tsv"
    protein_card_name = "biological_protein_cards.tsv"
    protein_mechanism_card_summary_name = (
        "biological_protein_mechanism_card_summary.tsv"
    )
    protein_mechanism_card_name = "biological_protein_mechanism_cards.tsv"
    evidence_graph_nodes_name = "biological_evidence_graph_nodes.tsv"
    evidence_graph_edges_name = "biological_evidence_graph_edges.tsv"
    experiment_confidence_summary_name = "biological_experiment_confidence_summary.tsv"
    experiment_confidence_components_name = (
        "biological_experiment_confidence_components.tsv"
    )
    section_confidence_name = "biological_report_section_confidence.tsv"

    write_output_table_tsv(output_dir / summary_name, report_summary_tsv)
    write_output_table_tsv(
        output_dir / differential_name,
        render_differential_abundance_tsv(report.differential_report),
    )
    write_output_table_tsv(
        output_dir / protein_card_summary_name,
        render_protein_evidence_card_summary_tsv(report.protein_cards),
    )
    write_output_table_tsv(
        output_dir / protein_card_name,
        render_protein_evidence_card_tsv(report.protein_cards),
    )
    write_output_table_tsv(
        output_dir / protein_mechanism_card_summary_name,
        render_protein_mechanism_card_summary_tsv(report.protein_mechanism_cards),
    )
    write_output_table_tsv(
        output_dir / protein_mechanism_card_name,
        render_protein_mechanism_card_tsv(report.protein_mechanism_cards),
    )
    graph_export = export_proteomics_evidence_graph(report.graph_report.graph)
    write_output_table_tsv(
        output_dir / evidence_graph_nodes_name,
        render_proteomics_evidence_graph_nodes_tsv(graph_export),
    )
    write_output_table_tsv(
        output_dir / evidence_graph_edges_name,
        render_proteomics_evidence_graph_edges_tsv(graph_export),
    )
    write_output_table_tsv(
        output_dir / experiment_confidence_summary_name,
        render_experiment_confidence_summary_tsv(report.experiment_confidence_report),
    )
    write_output_table_tsv(
        output_dir / experiment_confidence_components_name,
        render_experiment_confidence_component_tsv(report.experiment_confidence_report),
    )
    write_output_table_tsv(output_dir / section_confidence_name, section_confidence_tsv)

    return BiologicalScientificAnalysisExportNames(
        summary_name=summary_name,
        differential_name=differential_name,
        protein_card_summary_name=protein_card_summary_name,
        protein_card_name=protein_card_name,
        protein_mechanism_card_summary_name=protein_mechanism_card_summary_name,
        protein_mechanism_card_name=protein_mechanism_card_name,
        evidence_graph_nodes_name=evidence_graph_nodes_name,
        evidence_graph_edges_name=evidence_graph_edges_name,
        experiment_confidence_summary_name=experiment_confidence_summary_name,
        experiment_confidence_components_name=experiment_confidence_components_name,
        section_confidence_name=section_confidence_name,
    )


__all__ = [
    "BiologicalScientificAnalysisExportNames",
    "_write_biological_analysis_scientific_exports",
]
