# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.isotope_labeling import (
    SilacLabel,
    SilacValidationPolicy,
    build_silac_validation_report,
    parse_silac_feature_table,
)


def _fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent / "fixtures" / "isotope_labeling" / name
    )


def test_silac_validation_report_flags_abnormal_distribution_and_weak_labels() -> None:
    import_report = parse_silac_feature_table(_fixture("silac_features.tsv"))

    report = build_silac_validation_report(
        import_report,
        policy=SilacValidationPolicy(
            expected_labels=(
                SilacLabel.LIGHT,
                SilacLabel.MEDIUM,
                SilacLabel.HEAVY,
            ),
        ),
    )

    assert report.summary.abnormal_distribution_count == 1
    assert report.summary.weak_label_count == 2
    abnormal = next(
        entry
        for entry in report.distribution_entries
        if entry.sample_id == "sample_b" and entry.label is SilacLabel.MEDIUM
    )
    assert round(abnormal.ratio_to_sample_median or 0.0, 6) == round(1500.0 / 2200.0, 6)
    assert abnormal.abnormal_distribution is True
    issue_kinds = {
        entry.issue_kind
        for entry in report.weak_evidence
        if entry.sample_id == "sample_b" and entry.label is SilacLabel.MEDIUM
    }
    assert issue_kinds == {
        "incomplete_pair_coverage",
        "weak_total_intensity",
    }
