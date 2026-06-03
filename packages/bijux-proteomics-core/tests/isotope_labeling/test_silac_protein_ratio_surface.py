# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.isotope_labeling import (
    SilacLabel,
    SilacQuantificationPolicy,
    build_silac_ratio_report,
    parse_silac_feature_table,
)


def _fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent / "fixtures" / "isotope_labeling" / name
    )


def test_silac_pair_ratio_report_builds_protein_ratios() -> None:
    import_report = parse_silac_feature_table(_fixture("silac_features.tsv"))

    report = build_silac_ratio_report(import_report)

    assert report.summary.protein_ratio_count == 4
    first = next(
        entry
        for entry in report.protein_ratios
        if entry.sample_id == "sample_a"
        and entry.protein_id == "P001"
        and entry.numerator_label is SilacLabel.HEAVY
    )
    assert first.contributing_peptide_ids == ("PEPTIDE/z2", "PEPTIDE/z3")
    assert round(first.ratio or 0.0, 6) == round((1600.0 + 800.0) / (1000.0 + 500.0), 6)
    missing = next(
        entry
        for entry in report.protein_ratios
        if entry.sample_id == "sample_a"
        and entry.protein_id == "P002"
        and entry.numerator_label is SilacLabel.HEAVY
    )
    assert missing.ratio is None
    assert missing.missing_reason == "numerator_label_missing"


def test_silac_triplet_ratio_report_builds_collapsed_protein_ratios() -> None:
    import_report = parse_silac_feature_table(_fixture("silac_features.tsv"))

    report = build_silac_ratio_report(
        import_report,
        policy=SilacQuantificationPolicy(
            expected_labels=(
                SilacLabel.LIGHT,
                SilacLabel.MEDIUM,
                SilacLabel.HEAVY,
            ),
            separate_charge_states=False,
        ),
    )

    medium = next(
        entry
        for entry in report.protein_ratios
        if entry.sample_id == "sample_a"
        and entry.protein_id == "P001"
        and entry.numerator_label is SilacLabel.MEDIUM
    )
    assert medium.contributing_peptide_ids == ("PEPTIDE",)
    assert round(medium.ratio or 0.0, 6) == round(2000.0 / 1500.0, 6)
