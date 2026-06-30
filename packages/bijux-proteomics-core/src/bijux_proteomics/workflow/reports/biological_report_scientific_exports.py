# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Scientific artifact export for biological report bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interpretation import (
    render_biological_foreground_background_entry_tsv,
    render_biological_foreground_background_issue_tsv,
    render_biological_foreground_background_summary_tsv,
    render_protein_annotation_summary_tsv,
    render_protein_annotation_tsv,
    render_regulator_inference_summary_tsv,
    render_regulator_inference_tsv,
    render_rejected_regulator_evidence_tsv,
    render_unmapped_protein_annotation_tsv,
    render_unresolved_regulator_target_tsv,
)
from bijux_proteomics.quantification.statistics import (
    render_differential_abundance_tsv,
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
from bijux_proteomics.workflow.reports.biological_report_scientific_summary_tables import (
    render_biological_report_section_confidence_tsv as _render_section_confidence_tsv,
    render_biological_result_report_summary_tsv as _render_report_summary_tsv,
)


@dataclass(frozen=True)
class BiologicalScientificExportNames:
    """Artifact names emitted for core scientific report outputs."""

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
    evidence_aware_ranking_name: str | None
    claim_validation_summary_name: str | None
    supported_claim_name: str | None
    rejected_claim_name: str | None
    biological_hypothesis_summary_name: str | None
    biological_hypothesis_name: str | None
    rejected_hypothesis_candidate_name: str | None
    foreground_background_summary_name: str
    foreground_background_entry_name: str
    foreground_background_issue_name: str
    regulator_inference_summary_name: str | None
    regulator_inference_name: str | None
    regulator_unresolved_name: str | None
    regulator_rejected_name: str | None
    annotation_summary_name: str
    annotation_name: str
    annotation_unmapped_name: str


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
    foreground_background_summary_name = (
        "biological_enrichment_foreground_background_summary.tsv"
    )
    foreground_background_entry_name = (
        "biological_enrichment_foreground_background_entries.tsv"
    )
    foreground_background_issue_name = (
        "biological_enrichment_foreground_background_issues.tsv"
    )
    annotation_summary_name = "biological_annotation_summary.tsv"
    annotation_name = "biological_annotations.tsv"
    annotation_unmapped_name = "biological_annotation_unmapped.tsv"

    write_output_table_tsv(
        output_dir / summary_name, render_biological_result_report_summary_tsv(report)
    )
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
    write_output_table_tsv(
        output_dir / section_confidence_name,
        render_biological_report_section_confidence_tsv(report),
    )

    evidence_aware_ranking_name = None
    if report.evidence_aware_ranking_report is not None:
        evidence_aware_ranking_name = "biological_evidence_aware_ranking.tsv"
        write_output_table_tsv(
            output_dir / evidence_aware_ranking_name,
            render_evidence_aware_ranking_tsv(report.evidence_aware_ranking_report),
        )

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

    write_output_table_tsv(
        output_dir / foreground_background_summary_name,
        render_biological_foreground_background_summary_tsv(
            report.foreground_background_model
        ),
    )
    write_output_table_tsv(
        output_dir / foreground_background_entry_name,
        render_biological_foreground_background_entry_tsv(
            report.foreground_background_model
        ),
    )
    write_output_table_tsv(
        output_dir / foreground_background_issue_name,
        render_biological_foreground_background_issue_tsv(
            report.foreground_background_model
        ),
    )

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

    write_output_table_tsv(
        output_dir / annotation_summary_name,
        render_protein_annotation_summary_tsv(report.annotation_report),
    )
    write_output_table_tsv(
        output_dir / annotation_name,
        render_protein_annotation_tsv(report.annotation_report),
    )
    write_output_table_tsv(
        output_dir / annotation_unmapped_name,
        render_unmapped_protein_annotation_tsv(report.annotation_report),
    )

    return BiologicalScientificExportNames(
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
        evidence_aware_ranking_name=evidence_aware_ranking_name,
        claim_validation_summary_name=claim_validation_summary_name,
        supported_claim_name=supported_claim_name,
        rejected_claim_name=rejected_claim_name,
        biological_hypothesis_summary_name=biological_hypothesis_summary_name,
        biological_hypothesis_name=biological_hypothesis_name,
        rejected_hypothesis_candidate_name=rejected_hypothesis_candidate_name,
        foreground_background_summary_name=foreground_background_summary_name,
        foreground_background_entry_name=foreground_background_entry_name,
        foreground_background_issue_name=foreground_background_issue_name,
        regulator_inference_summary_name=regulator_inference_summary_name,
        regulator_inference_name=regulator_inference_name,
        regulator_unresolved_name=regulator_unresolved_name,
        regulator_rejected_name=regulator_rejected_name,
        annotation_summary_name=annotation_summary_name,
        annotation_name=annotation_name,
        annotation_unmapped_name=annotation_unmapped_name,
    )
