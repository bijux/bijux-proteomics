# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.isotope_labeling import (
    SilacLabel,
    SilacValidationPolicy,
    build_silac_validation_report,
    build_tmt_validation_report,
    export_silac_validation_distribution_tsv,
    export_silac_validation_label_tsv,
    export_silac_validation_summary_tsv,
    export_silac_validation_weak_tsv,
    export_tmt_validation_channel_tsv,
    export_tmt_validation_distribution_tsv,
    export_tmt_validation_summary_tsv,
    export_tmt_validation_weak_tsv,
    parse_silac_feature_table,
    render_silac_validation_distribution_tsv,
    render_silac_validation_label_tsv,
    render_silac_validation_summary_tsv,
    render_silac_validation_weak_tsv,
    render_tmt_validation_channel_tsv,
    render_tmt_validation_distribution_tsv,
    render_tmt_validation_summary_tsv,
    render_tmt_validation_weak_tsv,
)
from bijux_proteomics.multiplex import (
    TmtSearchResultSourceKind,
    build_tmt_reporter_feature_bundle,
    parse_tmt_reporter_table,
)


def _silac_fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent / "fixtures" / "isotope_labeling" / name
    )


def _multiplex_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_validation_renderers_and_exports_emit_silac_and_tmt_ledgers(
    tmp_path: Path,
) -> None:
    silac_report = build_silac_validation_report(
        parse_silac_feature_table(_silac_fixture("silac_features.tsv")),
        policy=SilacValidationPolicy(
            expected_labels=(
                SilacLabel.LIGHT,
                SilacLabel.MEDIUM,
                SilacLabel.HEAVY,
            ),
        ),
    )
    tmt_import_report = parse_tmt_reporter_table(
        _multiplex_fixture("maxquant_tmt_evidence.tsv"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )
    tmt_feature_bundle = build_tmt_reporter_feature_bundle(
        tmt_import_report,
        design_entries=parse_experimental_design_table(
            _multiplex_fixture("tmt.design.tsv")
        ).accepted_entries,
    )
    tmt_report = build_tmt_validation_report(tmt_feature_bundle)

    silac_summary_tsv = render_silac_validation_summary_tsv(silac_report)
    silac_label_tsv = render_silac_validation_label_tsv(silac_report)
    silac_distribution_tsv = render_silac_validation_distribution_tsv(silac_report)
    silac_weak_tsv = render_silac_validation_weak_tsv(silac_report)
    tmt_summary_tsv = render_tmt_validation_summary_tsv(tmt_report)
    tmt_channel_tsv = render_tmt_validation_channel_tsv(tmt_report)
    tmt_distribution_tsv = render_tmt_validation_distribution_tsv(tmt_report)
    tmt_weak_tsv = render_tmt_validation_weak_tsv(tmt_report)

    assert "missing_pair_member_count" in silac_summary_tsv
    assert "sample_b\tmedium\t2\t1\t1" in silac_label_tsv
    assert "sample_b\tmedium\t1500.0\t2200.0" in silac_distribution_tsv
    assert "weak_total_intensity" in silac_weak_tsv
    assert "missing_channel_count" in tmt_summary_tsv
    assert "plex-a\t129N\tplex_a_129N" in tmt_channel_tsv
    assert "plex-a\t126\tplex_a_126" in tmt_distribution_tsv
    assert "channel_missing" in tmt_weak_tsv

    export_silac_validation_summary_tsv(silac_report, tmp_path / "silac.summary.tsv")
    export_silac_validation_label_tsv(silac_report, tmp_path / "silac.labels.tsv")
    export_silac_validation_distribution_tsv(
        silac_report,
        tmp_path / "silac.distribution.tsv",
    )
    export_silac_validation_weak_tsv(silac_report, tmp_path / "silac.weak.tsv")
    export_tmt_validation_summary_tsv(tmt_report, tmp_path / "tmt.summary.tsv")
    export_tmt_validation_channel_tsv(tmt_report, tmp_path / "tmt.channels.tsv")
    export_tmt_validation_distribution_tsv(
        tmt_report,
        tmp_path / "tmt.distribution.tsv",
    )
    export_tmt_validation_weak_tsv(tmt_report, tmp_path / "tmt.weak.tsv")

    assert (tmp_path / "silac.summary.tsv").read_text(
        encoding="utf-8"
    ) == silac_summary_tsv
    assert (tmp_path / "silac.labels.tsv").read_text(
        encoding="utf-8"
    ) == silac_label_tsv
    assert (tmp_path / "silac.distribution.tsv").read_text(
        encoding="utf-8"
    ) == silac_distribution_tsv
    assert (tmp_path / "silac.weak.tsv").read_text(encoding="utf-8") == silac_weak_tsv
    assert (tmp_path / "tmt.summary.tsv").read_text(encoding="utf-8") == tmt_summary_tsv
    assert (tmp_path / "tmt.channels.tsv").read_text(
        encoding="utf-8"
    ) == tmt_channel_tsv
    assert (tmp_path / "tmt.distribution.tsv").read_text(
        encoding="utf-8"
    ) == tmt_distribution_tsv
    assert (tmp_path / "tmt.weak.tsv").read_text(encoding="utf-8") == tmt_weak_tsv
