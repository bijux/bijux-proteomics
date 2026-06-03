# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    build_protein_set_scoring_report,
    parse_protein_set_table,
)
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import (
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    normalize_label_free_table,
    parse_ms1_feature_table,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def _quant_fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "quant" / name


def _build_fixture_table():
    parse_report = parse_ms1_feature_table(
        _quant_fixture_path("ms1_features.tsv"),
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
    protein_table = build_label_free_intensity_table(
        parse_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.TOP_N,
        top_n=2,
    )
    return normalize_label_free_table(
        protein_table,
        method=NormalizationMethod.MEDIAN,
    )


def test_build_protein_set_scoring_report_scores_programs_per_sample() -> None:
    design_report = parse_experimental_design_table(
        _quant_fixture_path("quant.design.tsv")
    )
    protein_sets = parse_protein_set_table(_fixture_path("protein_sets.tsv"))

    report = build_protein_set_scoring_report(
        _build_fixture_table(),
        protein_sets.accepted_records,
        design_entries=design_report.accepted_entries,
    )

    assert report.summary.set_count == 3
    assert report.summary.sample_count == 4
    assert report.summary.unresolved_member_count == 1
    unresolved = report.unresolved_members[0]
    assert unresolved.protein_ref == "P999"
    activation_scores = {
        entry.sample_id: entry
        for entry in report.sample_scores
        if entry.set_id == "activation"
    }
    assert activation_scores["C1"].activity_score is not None
    assert activation_scores["T2"].activity_score is not None
    assert (
        activation_scores["T2"].activity_score > activation_scores["C1"].activity_score
    )
    assert activation_scores["C1"].observed_member_count == 1
    assert activation_scores["C1"].missing_member_count == 2
    assert activation_scores["C1"].confidence_status.value == "low"
    assert activation_scores["C1"].confidence_reason == (
        "observed member count 1 was below minimum 2"
    )
    assert report.summary.low_confidence_sample_score_count >= 1


def test_build_protein_set_scoring_report_emits_condition_deltas() -> None:
    design_report = parse_experimental_design_table(
        _quant_fixture_path("quant.design.tsv")
    )
    protein_sets = parse_protein_set_table(_fixture_path("protein_sets.tsv"))

    report = build_protein_set_scoring_report(
        _build_fixture_table(),
        protein_sets.accepted_records,
        design_entries=design_report.accepted_entries,
    )

    comparisons = {entry.set_id: entry for entry in report.condition_comparisons}
    assert report.summary.condition_count == 2
    assert report.summary.condition_comparison_count == 3
    assert comparisons["activation"].condition_a == "control"
    assert comparisons["activation"].condition_b == "treatment"
    assert comparisons["activation"].activity_score_delta is not None
    assert comparisons["activation"].comparison_confidence_status.value in {
        "high",
        "low",
    }
    assert comparisons["activation"].activity_score_delta > 0.0
    assert comparisons["suppression"].activity_score_delta is not None
    assert comparisons["suppression"].activity_score_delta < 0.0
