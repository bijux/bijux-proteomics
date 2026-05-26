# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import (
    Ms1FeatureColumnMapping,
    QuantEntityLevel,
    QuantRollupMethod,
    build_differential_abundance_report,
    build_label_free_intensity_table,
    normalize_label_free_table,
    parse_ms1_feature_table,
)
from bijux_proteomics.quantification.differential_abundance import apply_benjamini_hochberg
from bijux_proteomics.workflow import build_biological_result_graph_report
from bijux_proteomics_lab.handoffs.qc_feedback import (
    LabRunQcObservation,
    build_lab_run_qc_feedback_report,
)
from bijux_proteomics_lab.outcomes.observations import AssayObservationRecord, QcState


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_build_biological_result_graph_report_preserves_graph_backed_final_claims() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    parse_report = parse_ms1_feature_table(
        _fixture("biological_report_features.tsv"),
        mapping=Ms1FeatureColumnMapping(
            sample_id="sample_id",
            feature_id="feature_id",
            peptide="peptide",
            intensity="intensity",
            protein_refs="proteins",
            charge="charge",
            mz="mz",
            retention_time_seconds="retention_time_seconds",
            missing_reason="missing_reason",
            protein_separator=";",
        ),
    )
    quant_table = build_label_free_intensity_table(
        parse_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
        top_n=3,
    )
    normalized_table = normalize_label_free_table(quant_table)
    differential_report = apply_benjamini_hochberg(
        build_differential_abundance_report(
            normalized_table,
            design_entries,
            condition_a="control",
            condition_b="treatment",
        )
    )

    report = build_biological_result_graph_report(
        normalized_table,
        differential_report,
        design_entries,
        max_adjusted_p_value=0.1,
        min_absolute_log2_fold_change=1.0,
    )

    assert report.protein_claim_count == len(differential_report.entries)
    assert report.graph.summary.node_kind_counts["protein"] == len(differential_report.entries)
    assert report.graph.summary.node_kind_counts["statistical_result"] == len(differential_report.entries)
    assert report.final_results.entry_count == len(differential_report.entries)
    assert all(
        entry.claim_node_id.startswith("statistical_result:")
        and entry.subject_node_id.startswith("protein:")
        for entry in report.final_results.entries
    )


def test_build_biological_result_graph_report_routes_lab_run_qc_feedback_into_graph_results() -> (
    None
):
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    parse_report = parse_ms1_feature_table(
        _fixture("biological_report_features.tsv"),
        mapping=Ms1FeatureColumnMapping(
            sample_id="sample_id",
            feature_id="feature_id",
            peptide="peptide",
            intensity="intensity",
            protein_refs="proteins",
            charge="charge",
            mz="mz",
            retention_time_seconds="retention_time_seconds",
            missing_reason="missing_reason",
            protein_separator=";",
        ),
    )
    quant_table = build_label_free_intensity_table(
        parse_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
        top_n=3,
    )
    normalized_table = normalize_label_free_table(quant_table)
    differential_report = apply_benjamini_hochberg(
        build_differential_abundance_report(
            normalized_table,
            design_entries,
            condition_a="control",
            condition_b="treatment",
        )
    )
    feedback = build_lab_run_qc_feedback_report(
        (
            LabRunQcObservation(
                run_id=design_entries[0].spectra_file,
                sample_id=design_entries[0].sample_id,
                observation=AssayObservationRecord(
                    assay_id="assay_cv_screen",
                    metric="coefficient_of_variation",
                    value=0.38,
                    replicate_values=[0.35, 0.38, 0.41],
                    qc_state=QcState.FAILED,
                    qc_passed=False,
                    dispersion=0.38,
                    normalization_method="median",
                    interpretation_confidence=0.7,
                ),
            ),
        )
    )
    qc_report = build_biological_result_graph_report(
        normalized_table,
        differential_report,
        design_entries,
        max_adjusted_p_value=0.1,
        min_absolute_log2_fold_change=1.0,
        lab_run_qc_feedback_report=feedback,
    )

    assert qc_report.graph.summary.node_kind_counts["qc_decision"] == 1
    assert qc_report.graph.summary.edge_kind_counts["run_governed_by_qc_decision"] == 1
    quant_node = next(
        node
        for node in qc_report.graph.nodes
        if node.entity_type.value == "quant_value"
        and any(
            context.entity_type.value == "sample"
            and context.entity_ref == design_entries[0].sample_id
            for context in node.context_refs
        )
    )
    assert {f"{context.entity_type.value}:{context.entity_ref}" for context in quant_node.context_refs} >= {
        f"sample:{design_entries[0].sample_id}",
        f"run:{design_entries[0].spectra_file}",
    }
