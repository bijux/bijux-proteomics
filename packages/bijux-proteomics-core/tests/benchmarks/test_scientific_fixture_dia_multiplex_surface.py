# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import csv
from pathlib import Path

from bijux_proteomics.benchmarks.scientific_fixture_corpus import (
    ScientificFixtureCaseKind,
    ScientificFixtureManifest,
    get_scientific_fixture_manifest,
)
from bijux_proteomics.dia import build_diann_run_qc_report
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.isotope_labeling import build_tmt_validation_report
from bijux_proteomics.multiplex import (
    TmtSearchResultSourceKind,
    build_tmt_reporter_feature_bundle,
    parse_tmt_reporter_table,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


def _repo_path(repo_relative_path: str) -> Path:
    return REPO_ROOT / repo_relative_path


def _asset_path(manifest: ScientificFixtureManifest, role: str) -> Path:
    asset = next(asset for asset in manifest.input_assets if asset.role == role)
    return _repo_path(asset.repo_relative_path)


def _expected_count(
    manifest: ScientificFixtureManifest,
    *,
    asset_role: str,
    accepted: bool,
) -> int:
    expectations = manifest.accepted_rows if accepted else manifest.rejected_rows
    return next(
        expectation.expected_count
        for expectation in expectations
        if expectation.asset_role == asset_role
    )


def _count_tsv_rows(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle, delimiter="\t"))


def test_poor_dia_run_fixture_keeps_low_coverage_run_flagged() -> None:
    manifest = get_scientific_fixture_manifest(ScientificFixtureCaseKind.POOR_DIA_RUN)
    input_path = _asset_path(manifest, "diann_report")
    report = build_diann_run_qc_report(input_path)

    assert _count_tsv_rows(input_path) == _expected_count(
        manifest, asset_role="diann_report", accepted=True
    )
    assert _expected_count(manifest, asset_role="diann_report", accepted=False) == 0
    assert report.summary.run_count == 3
    assert report.summary.flagged_run_count == 1
    weak_run = next(entry for entry in report.run_entries if entry.run_name == "raw_C")
    assert weak_run.precursor_missing_fraction == 0.75
    assert weak_run.protein_missing_fraction == 0.75
    assert weak_run.flagged is True
    assert report.outlier_runs[0].run_name == "raw_C"


def test_bad_tmt_channel_fixture_keeps_missing_channel_evidence_visible() -> None:
    manifest = get_scientific_fixture_manifest(
        ScientificFixtureCaseKind.BAD_TMT_CHANNELS
    )
    reporter_report = parse_tmt_reporter_table(
        _asset_path(manifest, "reporter_table"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )
    design_report = parse_experimental_design_table(
        _asset_path(manifest, "design_table")
    )
    feature_bundle = build_tmt_reporter_feature_bundle(
        reporter_report,
        design_entries=design_report.accepted_entries,
    )
    validation = build_tmt_validation_report(feature_bundle)

    assert len(reporter_report.accepted_rows) == _expected_count(
        manifest, asset_role="reporter_table", accepted=True
    )
    assert len(reporter_report.rejected_rows) == _expected_count(
        manifest, asset_role="reporter_table", accepted=False
    )
    assert len(design_report.accepted_entries) == _expected_count(
        manifest, asset_role="design_table", accepted=True
    )
    assert len(design_report.rejected_rows) == _expected_count(
        manifest, asset_role="design_table", accepted=False
    )
    assert validation.summary.expected_channel_count == 8
    assert validation.summary.missing_channel_count == 2
    assert validation.summary.weak_channel_count == 2
    missing = next(
        entry
        for entry in validation.channel_entries
        if entry.multiplex_group == "plex-a" and entry.multiplex_channel == "129N"
    )
    assert missing.present is False
    assert missing.source_column_present is False
    weak = next(
        entry
        for entry in validation.weak_evidence
        if entry.multiplex_group == "plex-a" and entry.multiplex_channel == "129N"
    )
    assert weak.issue_kind == "channel_missing"
