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


def test_silac_pair_ratio_report_builds_charge_resolved_peptide_ratios() -> None:
    import_report = parse_silac_feature_table(_fixture("silac_features.tsv"))

    report = build_silac_ratio_report(import_report)

    assert import_report.summary.accepted_row_count == 13
    assert import_report.summary.sample_count == 2
    assert report.summary.expected_label_count == 2
    assert report.summary.peptide_ratio_count == 5
    assert report.summary.protein_ratio_count == 4
    assert report.summary.missing_ratio_count == 2
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


def test_silac_triplet_ratio_report_collapses_charge_states_when_requested() -> None:
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

    assert report.summary.expected_label_count == 3
    assert report.summary.peptide_ratio_count == 8
    assert report.summary.protein_ratio_count == 8
    assert report.summary.missing_ratio_count == 4
    medium = next(
        entry
        for entry in report.peptide_ratios
        if entry.sample_id == "sample_a"
        and entry.peptide_id == "PEPTIDE"
        and entry.numerator_label is SilacLabel.MEDIUM
    )
    assert medium.charge is None
    assert round(medium.ratio or 0.0, 6) == round(2000.0 / 1500.0, 6)
    heavy = next(
        entry
        for entry in report.peptide_ratios
        if entry.sample_id == "sample_a"
        and entry.peptide_id == "PEPTIDE"
        and entry.numerator_label is SilacLabel.HEAVY
    )
    assert round(heavy.ratio or 0.0, 6) == round(2400.0 / 1500.0, 6)


def test_silac_import_rejects_invalid_labels_and_duplicate_feature_ids(
    tmp_path: Path,
) -> None:
    feature_path = tmp_path / "silac_invalid.tsv"
    feature_path.write_text(
        "\n".join(
            (
                "feature_id\tsample_id\tpeptide\tprotein_refs\tcharge\tlabel\tintensity",
                "f1\tsample_a\tPEPTIDE\tP11111\t2\tlight\t1000",
                "f1\tsample_a\tPEPTIDE\tP11111\t2\tsuperheavy\t-5",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_silac_feature_table(feature_path)

    assert len(report.accepted_rows) == 0
    assert len(report.rejected_rows) == 2
    assert "duplicates identifier" in report.rejected_rows[0].reason
    assert (
        "unsupported value" in report.rejected_rows[1].reason
        or "negative" in report.rejected_rows[1].reason
    )
