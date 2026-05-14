# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.benchmarks.flagship_public_packages import (
    build_flagship_lfq_public_benchmark_package,
)
from bijux_proteomics.benchmarks.quantification_pressure import (
    build_quantification_pressure_corpus_report,
)
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.quantification.benchmarks import (
    build_effect_size_stability_benchmark_report,
    build_quant_missingness_robustness_report,
    build_quant_normalization_impact_benchmark_report,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "quant" / name


def test_quantification_pressure_corpus_report_anchors_study_scale_lfq_evidence() -> (
    None
):
    package = build_flagship_lfq_public_benchmark_package()
    feature_records = parse_ms1_feature_table(
        _fixture("study_scale_ms1_features.tsv")
    ).accepted_records
    design_entries = parse_experimental_design_table(
        _fixture("study_scale.design.tsv")
    ).accepted_entries
    missingness = build_quant_missingness_robustness_report(
        feature_records,
        design_entries=design_entries,
    )
    normalization = build_quant_normalization_impact_benchmark_report(
        feature_records,
        design_entries=design_entries,
        condition_a="control",
        condition_b="treatment",
    )
    perturbed_records = tuple(
        record.model_copy(
            update={
                "intensity": (
                    round(record.intensity * 1.01, 6)
                    if record.intensity is not None and record.sample_id.startswith("T")
                    else record.intensity
                )
            }
        )
        for record in feature_records
    )
    effect_size = build_effect_size_stability_benchmark_report(
        feature_records,
        perturbed_records,
        design_entries=design_entries,
        condition_a="control",
        condition_b="treatment",
    )

    report = build_quantification_pressure_corpus_report(
        benchmark_package_id=package.package_id,
        supporting_identity_paths=tuple(asset.path for asset in package.source_assets),
        missingness_robustness=missingness,
        normalization_impact=normalization,
        effect_size_stability=effect_size,
    )

    assert report.benchmark_package_id == package.package_id
    assert any(
        path.endswith("study_scale_ms1_features.tsv")
        for path in report.supporting_identity_paths
    )
    assert any(
        path.endswith("study_scale.design.tsv")
        for path in report.supporting_identity_paths
    )
    assert report.missingness_robustness.entity_level.value == "protein"
    assert report.effect_size_stability.overlap_fraction >= 0.0
    assert "study-scale missingness" in report.note
