# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.isotope_labeling import (
    SilacLabel,
    parse_silac_feature_table,
    build_silac_ratio_report,
)


def _fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent / "fixtures" / "isotope_labeling" / name
    )


def test_silac_pair_ratio_report_builds_charge_resolved_peptide_ratios() -> None:
    import_report = parse_silac_feature_table(_fixture("silac_features.tsv"))

    report = build_silac_ratio_report(import_report)

    assert import_report.summary.accepted_row_count == 13
    assert import_report.summary.sample_count == 2
    assert report.summary.expected_label_count == 2
    assert report.summary.peptide_ratio_count == 5
    assert report.summary.missing_ratio_count == 1
    first = next(
        entry
        for entry in report.peptide_ratios
        if entry.sample_id == "sample_a"
        and entry.peptide_id == "PEPTIDE/z2"
        and entry.numerator_label is SilacLabel.HEAVY
    )
    assert round(first.ratio or 0.0, 6) == 1.6
    missing = next(
        entry
        for entry in report.peptide_ratios
        if entry.sample_id == "sample_a"
        and entry.peptide_id == "DPEPTIDE/z2"
        and entry.numerator_label is SilacLabel.HEAVY
    )
    assert missing.ratio is None
    assert missing.missing_reason == "numerator_label_missing"
