# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import (
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    build_differential_abundance_report,
    build_label_free_intensity_table,
    normalize_label_free_table,
    parse_ms1_feature_table,
)
from bijux_proteomics.quantification.differential_abundance import (
    apply_benjamini_hochberg,
)
from bijux_proteomics.review import (
    VolcanoReviewPolicy,
    build_quantification_volcano_review,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_build_quantification_volcano_review_preserves_significance_and_labels() -> (
    None
):
    mapping = Ms1FeatureColumnMapping(
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
    )
    parse_report = parse_ms1_feature_table(
        _fixture("biological_report_features.tsv"),
        mapping=mapping,
    )
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    normalized_table = normalize_label_free_table(
        build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.SUM,
            top_n=3,
        ),
        method=NormalizationMethod.MEDIAN,
    )
    differential_report = apply_benjamini_hochberg(
        build_differential_abundance_report(
            normalized_table,
            design_entries,
            condition_a="control",
            condition_b="treatment",
        )
    )

    review = build_quantification_volcano_review(
        differential_report,
        protein_refs_by_entity=normalized_table.entity_protein_refs,
        policy=VolcanoReviewPolicy(top_label_count=2),
    )

    assert review.source_kind.value == "quantification"
    assert review.significant_point_count >= 3
    assert any(point.raw_p_value > 0.0 for point in review.points)
    assert sum(1 for point in review.points if point.top_labeled) == 2
