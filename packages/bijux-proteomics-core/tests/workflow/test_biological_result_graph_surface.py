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
