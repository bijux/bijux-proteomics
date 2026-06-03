# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.benchmarks import (
    ScientificFixtureCaseKind,
    build_scientific_fixture_catalog,
    get_scientific_fixture_manifest,
    render_scientific_fixture_catalog_summary_tsv,
    scientific_fixture_repo_path,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


def test_scientific_fixture_catalog_covers_all_hard_biological_cases() -> None:
    catalog = build_scientific_fixture_catalog()

    assert len(catalog.entries) == 9
    assert {entry.case_kind for entry in catalog.entries} == set(
        ScientificFixtureCaseKind
    )
    for entry in catalog.entries:
        assert entry.accepted_rows
        assert entry.rejected_rows
        assert entry.biological_interpretation
        for asset in entry.input_assets:
            assert scientific_fixture_repo_path(asset.repo_relative_path).is_file()
            assert (REPO_ROOT / asset.repo_relative_path).is_file()


def test_scientific_fixture_manifest_lookup_preserves_missing_sample_assets() -> None:
    manifest = get_scientific_fixture_manifest(
        ScientificFixtureCaseKind.MISSING_SAMPLES
    )

    assert manifest.fixture_id == "scientific_fixture:missing_samples"
    assert manifest.owner_surface == "quantification.missingness_review"
    assert {asset.role for asset in manifest.input_assets} == {
        "feature_table",
        "design_table",
    }
    assert "condition-specific biology" in manifest.biological_interpretation


def test_scientific_fixture_catalog_summary_tsv_stays_reviewable() -> None:
    catalog = build_scientific_fixture_catalog()
    tsv = render_scientific_fixture_catalog_summary_tsv(catalog)

    assert tsv.startswith(
        "fixture_id\tcase_kind\towner_surface\tasset_count\t"
        "accepted_expectation_count\trejected_expectation_count\t"
        "biological_interpretation\n"
    )
    assert "scientific_fixture:shared_peptides\tshared_peptides\t" in tsv
    assert "scientific_fixture:poor_dia_run\tpoor_dia_run\tdia.run_qc\t1\t1\t1\t" in tsv
