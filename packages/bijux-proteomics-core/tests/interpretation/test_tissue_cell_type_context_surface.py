# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    build_tissue_cell_type_context_report,
    parse_biological_context_table,
    render_tissue_cell_type_context_summary_tsv,
    render_tissue_cell_type_interpretation_tsv,
    render_tissue_cell_type_sample_consistency_tsv,
    render_tissue_cell_type_unexpected_signal_tsv,
)
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import (
    LabelFreeQuantTable,
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    normalize_label_free_table,
    parse_ms1_feature_table,
)
from bijux_proteomics.study import build_experiment_design


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _build_protein_table() -> LabelFreeQuantTable:
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
        ),
    )
    return normalize_label_free_table(
        build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.SUM,
        ),
        method=NormalizationMethod.MEDIAN,
    )


def test_build_tissue_cell_type_context_report_flags_sample_mismatch_warning() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report_tissue_context.design.tsv")
        ).accepted_entries
    )
    context_import = parse_biological_context_table(
        _fixture("biological_report_tissue_markers.tsv")
    )

    report = build_tissue_cell_type_context_report(
        _build_protein_table(),
        build_experiment_design(design_entries),
        context_import.accepted_records,
    )

    assert report.summary.sample_count == 6
    assert report.summary.marker_context_count == 2
    assert report.summary.mismatch_warning_count == 1
    assert report.summary.unexpected_signal_count >= 1
    by_sample = {entry.sample_id: entry for entry in report.sample_consistency_entries}
    assert by_sample["C1"].status.value == "consistent"
    assert by_sample["T3"].status.value == "mismatch_warning"
    assert by_sample["T3"].qc_warning is True
    assert by_sample["T3"].warning_code == "unexpected_marker_context_dominates"
    assert by_sample["T3"].highest_unexpected_context_id == "neuron"
    assert by_sample["T3"].matched_context_ids == ("liver",)
    assert any(
        entry.sample_id == "T3" and entry.context_id == "neuron"
        for entry in report.unexpected_signal_entries
    )
    by_label = {
        entry.tissue_or_cell_type: entry for entry in report.interpretation_entries
    }
    assert by_label["liver"].mismatch_warning_count == 1
    assert by_label["liver"].dominant_unexpected_context_id == "neuron"
    assert "mismatch_warning_count" in render_tissue_cell_type_context_summary_tsv(
        report
    )
    assert (
        "unexpected_marker_context_dominates"
        in render_tissue_cell_type_sample_consistency_tsv(report)
    )
    assert "context_kind" in render_tissue_cell_type_unexpected_signal_tsv(report)
    assert (
        "dominant_unexpected_context_id"
        in render_tissue_cell_type_interpretation_tsv(report)
    )
