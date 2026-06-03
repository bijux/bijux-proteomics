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


def test_silac_validation_report_preserves_expected_labels_and_missing_pair_members() -> (
    None
):
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

    assert report.summary.sample_count == 2
    assert report.summary.expected_label_count == 3
    assert report.summary.label_entry_count == 6
    assert report.summary.missing_label_count == 0
    assert report.summary.missing_pair_member_count == 2
    sample_a_heavy = next(
        entry
        for entry in report.label_entries
        if entry.sample_id == "sample_a" and entry.label is SilacLabel.HEAVY
    )
    assert sample_a_heavy.expected_group_count == 3
    assert sample_a_heavy.observed_group_count == 2
    assert sample_a_heavy.missing_group_count == 1
    sample_b_medium = next(
        entry
        for entry in report.label_entries
        if entry.sample_id == "sample_b" and entry.label is SilacLabel.MEDIUM
    )
    assert sample_b_medium.expected_group_count == 2
    assert sample_b_medium.observed_group_count == 1
    assert sample_b_medium.missing_group_count == 1
