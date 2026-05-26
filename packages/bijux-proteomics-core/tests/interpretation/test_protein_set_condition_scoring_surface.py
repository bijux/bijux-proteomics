# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.interpretation import (
    build_protein_set_scoring_report,
    parse_protein_set_table,
)
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


def test_protein_set_condition_scores_preserve_mean_activity_by_condition() -> None:
    design_report = parse_experimental_design_table(_quant_fixture_path("quant.design.tsv"))
    protein_sets = parse_protein_set_table(_fixture_path("protein_sets.tsv"))

    report = build_protein_set_scoring_report(
        _build_fixture_table(),
        protein_sets.accepted_records,
        design_entries=design_report.accepted_entries,
    )

    condition_scores = {
        (entry.set_id, entry.condition): entry for entry in report.condition_scores
    }
    assert condition_scores[("activation", "control")].sample_count == 2
    assert condition_scores[("activation", "treatment")].sample_count == 2
    assert condition_scores[("activation", "control")].scored_sample_count == 2
    assert condition_scores[("activation", "treatment")].scored_sample_count == 2
    assert (
        condition_scores[("activation", "control")].low_confidence_sample_count >= 1
    )
    assert (
        condition_scores[("activation", "control")].confidence_status.value
        == "low"
    )
    assert condition_scores[("activation", "treatment")].mean_activity_score is not None
    assert condition_scores[("activation", "control")].mean_activity_score is not None
    assert (
        condition_scores[("activation", "treatment")].mean_activity_score
        > condition_scores[("activation", "control")].mean_activity_score
    )
