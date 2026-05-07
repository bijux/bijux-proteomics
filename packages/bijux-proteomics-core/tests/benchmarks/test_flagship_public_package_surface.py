# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.benchmarks.flagship_public_packages import (
    build_flagship_dda_public_benchmark_package,
    build_flagship_lfq_public_benchmark_package,
    build_flagship_ptm_public_benchmark_package,
    build_flagship_public_benchmark_catalog,
)


def test_flagship_public_benchmark_catalog_tracks_dda_lfq_and_ptm_packages() -> None:
    catalog = build_flagship_public_benchmark_catalog()

    assert {entry.workflow_family for entry in catalog.entries} == {"dda", "lfq", "ptm"}
    assert all(entry.source_assets for entry in catalog.entries)
    assert all(entry.expected_review_artifacts for entry in catalog.entries)


def test_flagship_dda_public_benchmark_package_anchors_raw_and_review_paths() -> None:
    package = build_flagship_dda_public_benchmark_package()

    assert package.package_id == "flagship_public_package:dda_reviewable_run"
    assert package.workflow_family == "dda"
    assert any(
        asset.path.endswith("public_benchmark_packages/dda_reviewable_run/package_manifest.json")
        for asset in package.source_assets
    )
    assert any(
        asset.path.endswith("public_benchmark_packages/dda_reviewable_run/warning_demonstrations.json")
        for asset in package.source_assets
    )
    assert any(
        asset.path.endswith("search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv")
        for asset in package.source_assets
    )
    assert "cross-engine protein rollup drift" in package.scientific_pressures
    assert "invariant ledgers" in package.claim_scope


def test_flagship_lfq_public_benchmark_package_anchors_study_scale_quant_pressure() -> None:
    package = build_flagship_lfq_public_benchmark_package()

    assert package.workflow_family == "lfq"
    assert any(asset.path.endswith("quant/study_scale_ms1_features.tsv") for asset in package.source_assets)
    assert any(asset.path.endswith("quant/study_scale.design.tsv") for asset in package.source_assets)
    assert "effect-size instability" in package.scientific_pressures
    assert "study-scale public quant evidence" in package.claim_scope


def test_flagship_ptm_public_benchmark_package_anchors_localization_and_raw_spectra() -> (
    None
):
    package = build_flagship_ptm_public_benchmark_package()

    assert package.workflow_family == "ptm"
    assert any(asset.path.endswith("ptm/localization_results.tsv") for asset in package.source_assets)
    assert any(asset.path.endswith("production_run/spectra.mgf") for asset in package.source_assets)
    assert "site ambiguity" in package.scientific_pressures
    assert "raw-spectrum validation" in package.note
