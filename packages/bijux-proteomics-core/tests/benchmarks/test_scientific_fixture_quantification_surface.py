# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.benchmarks.scientific_fixture_corpus import (
    ScientificFixtureCaseKind,
    ScientificFixtureManifest,
    get_scientific_fixture_manifest,
)
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import (
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    build_missingness_condition_summary_report,
    build_missingness_entity_summary_report,
    parse_ms1_feature_table,
)
from bijux_proteomics.quantification.review import (
    MissingnessMechanismKind,
    build_missingness_mechanism_profile_report,
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


def test_missing_sample_fixture_preserves_condition_specific_absence_and_technical_dropout() -> (
    None
):
    manifest = get_scientific_fixture_manifest(
        ScientificFixtureCaseKind.MISSING_SAMPLES
    )
    feature_report = parse_ms1_feature_table(_asset_path(manifest, "feature_table"))
    design_report = parse_experimental_design_table(
        _asset_path(manifest, "design_table")
    )
    table = build_label_free_intensity_table(
        feature_report.accepted_records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )
    entity_summary = build_missingness_entity_summary_report(table)
    condition_summary = build_missingness_condition_summary_report(
        table,
        design_entries=design_report.accepted_entries,
    )
    mechanism_summary = build_missingness_mechanism_profile_report(
        table,
        design_entries=design_report.accepted_entries,
    )

    assert len(feature_report.accepted_records) == _expected_count(
        manifest, asset_role="feature_table", accepted=True
    )
    assert len(feature_report.rejected_rows) == _expected_count(
        manifest, asset_role="feature_table", accepted=False
    )
    assert len(design_report.accepted_entries) == _expected_count(
        manifest, asset_role="design_table", accepted=True
    )
    assert len(design_report.rejected_rows) == _expected_count(
        manifest, asset_role="design_table", accepted=False
    )

    by_entity = {entry.entity_id: entry for entry in entity_summary.entries}
    assert by_entity["BIOPEP"].observed_sample_count == 2
    assert by_entity["BIOPEP"].not_observed_sample_count == 2
    assert by_entity["TECHPEP"].observed_sample_count == 3
    assert by_entity["TECHPEP"].not_observed_sample_count == 1

    by_condition = {entry.condition: entry for entry in condition_summary.entries}
    assert by_condition["control"].missing_fraction == 1 / 6
    assert by_condition["treatment"].missing_fraction == 2 / 3
    assert by_condition["treatment"].condition_specific_absence_entity_ids == (
        "BIOPEP",
    )

    by_mechanism = {
        entry.entity_id: entry.mechanism for entry in mechanism_summary.entries
    }
    assert by_mechanism["BIOPEP"] is MissingnessMechanismKind.SPARSE_BIOLOGY_CANDIDATE
    assert by_mechanism["TECHPEP"] is MissingnessMechanismKind.TECHNICAL_FAILURE
