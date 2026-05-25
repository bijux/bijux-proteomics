# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.benchmarks.flagship_public_packages import (
    build_flagship_dda_public_benchmark_package,
    build_flagship_dia_public_benchmark_package,
    build_flagship_lfq_public_benchmark_package,
    build_flagship_multiplex_public_benchmark_package,
    build_flagship_ptm_public_benchmark_package,
    build_flagship_public_benchmark_catalog,
    build_flagship_public_package_artifact_inventories,
    build_flagship_public_package_lifecycle_records,
    build_flagship_public_package_quality_sheets,
    build_flagship_targeted_public_benchmark_package,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


def test_flagship_public_benchmark_catalog_tracks_all_six_packages() -> None:
    catalog = build_flagship_public_benchmark_catalog()

    assert {entry.workflow_family for entry in catalog.entries} == {
        "dda",
        "dia",
        "lfq",
        "multiplex",
        "ptm",
        "targeted",
    }
    assert all(entry.source_assets for entry in catalog.entries)
    assert all(entry.expected_review_artifacts for entry in catalog.entries)
    assert all(entry.package_root for entry in catalog.entries)
    assert all(entry.quality_sheet_path for entry in catalog.entries)
    assert all(entry.lifecycle_record_path for entry in catalog.entries)


def test_dda_public_benchmark_package_keeps_quality_and_lifecycle_visible() -> None:
    package = build_flagship_dda_public_benchmark_package()

    assert package.package_id == "flagship_public_package:dda_reviewable_run"
    assert package.workflow_family == "dda"
    assert (
        package.runtime_availability
        == "import_only runtime lane exists and is reviewable"
    )
    assert any(
        asset.path.endswith(
            "benchmark-assets/flagship-public-packages/dda_reviewable_run/quality_sheet.json"
        )
        for asset in package.source_assets
    )
    assert any(
        asset.path.endswith(
            "benchmark-assets/flagship-public-packages/dda_reviewable_run/lifecycle.json"
        )
        for asset in package.source_assets
    )
    assert package.source_locator_manifest_path.endswith(
        "benchmark-assets/flagship-public-packages/dda_reviewable_run/source_locator_manifest.json"
    )
    assert package.citation_manifest_path.endswith(
        "benchmark-assets/flagship-public-packages/dda_reviewable_run/citation_manifest.json"
    )
    assert "invariant ledgers" in package.claim_scope


def test_dia_public_benchmark_package_promotes_library_conditioned_evidence() -> None:
    package = build_flagship_dia_public_benchmark_package()

    assert package.workflow_family == "dia"
    assert package.public_dataset_identity.startswith("tracked Spectronaut-style")
    assert any(
        asset.path.endswith("primary/spectronaut_report.tsv")
        for asset in package.source_assets
    )
    assert any(
        asset.path.endswith("comparator/diann_pipeline_export.tsv")
        for asset in package.source_assets
    )
    assert "library incompleteness" in package.scientific_pressures
    assert "library-conditioned" in package.note


def test_lfq_public_benchmark_package_promotes_cohort_review_surface() -> None:
    package = build_flagship_lfq_public_benchmark_package()

    assert package.workflow_family == "lfq"
    assert any(
        asset.path.endswith("evidence/study_scale_ms1_features.tsv")
        for asset in package.source_assets
    )
    assert any(
        asset.path.endswith("evidence/study_scale.design.tsv")
        for asset in package.source_assets
    )
    assert "effect-size instability" in package.scientific_pressures
    assert (
        package.runtime_availability
        == "raw-executable runtime lane exists and is reviewable"
    )


def test_multiplex_public_benchmark_package_promotes_tmtpro_review_surface() -> None:
    package = build_flagship_multiplex_public_benchmark_package()

    assert package.workflow_family == "multiplex"
    assert any(
        asset.path.endswith("evidence/tmt_reporter_table.tsv")
        for asset in package.source_assets
    )
    assert any(
        asset.path.endswith("evidence/multiplex.design.tsv")
        for asset in package.source_assets
    )
    assert "ratio compression" in package.scientific_pressures
    assert "TMTpro" in package.package_label


def test_ptm_public_benchmark_package_anchors_localization_and_raw_spectra() -> None:
    package = build_flagship_ptm_public_benchmark_package()

    assert package.workflow_family == "ptm"
    assert any(
        asset.path.endswith("evidence/localization_results.tsv")
        for asset in package.source_assets
    )
    assert any(
        asset.path.endswith(
            "benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/spectra.mgf"
        )
        for asset in package.source_assets
    )
    assert "site ambiguity" in package.scientific_pressures
    assert "raw-executable runtime lane" in package.note


def test_targeted_public_benchmark_package_exposes_follow_up_consequences() -> None:
    package = build_flagship_targeted_public_benchmark_package()

    assert package.workflow_family == "targeted"
    assert any(
        asset.path.endswith("evidence/skyline_targeted_qc_results.tsv")
        for asset in package.source_assets
    )
    assert any(
        asset.path.endswith("evidence/skyline_targeted_qc.design.tsv")
        for asset in package.source_assets
    )
    assert any(
        asset.path.endswith("evidence/targeted_validation_discovery_claims.json")
        for asset in package.source_assets
    )
    assert any(
        asset.path.endswith("evidence/targeted_validation_panel_assays.json")
        for asset in package.source_assets
    )
    assert any(
        asset.path.endswith("evidence/targeted_benchmark_qc.tsv")
        for asset in package.source_assets
    )
    assert any(
        asset.path.endswith("supported_targeted_follow_up.json")
        for asset in package.source_assets
    )
    assert any(
        asset.path.endswith("refused_targeted_follow_up.json")
        for asset in package.source_assets
    )
    assert "transition reproducibility" in package.scientific_pressures
    assert "fragment-ratio drift" in package.scientific_pressures


def test_public_package_artifact_inventories_cover_every_catalog_entry() -> None:
    inventories = {
        inventory.package_id: inventory
        for inventory in build_flagship_public_package_artifact_inventories()
    }

    assert len(inventories) == 6
    for inventory in inventories.values():
        assert inventory.artifacts
        assert inventory.inventory_path.endswith("artifact_inventory.json")
        assert all(record.sha256 for record in inventory.artifacts)
        for record in inventory.artifacts:
            assert (REPO_ROOT / record.repo_relative_path).exists()


def test_public_package_quality_sheets_name_exact_strengths_and_blockers() -> None:
    sheets = {
        sheet.workflow_family: sheet
        for sheet in build_flagship_public_package_quality_sheets()
    }

    assert len(sheets) == 6
    assert (
        sheets["dda"].current_readiness
        == "outsider_auditable_but_not_live_rerun_parity"
    )
    assert (
        sheets["dia"].runtime_state == "reviewable raw-executable runtime lane exists"
    )
    assert (
        sheets["lfq"].runtime_state == "reviewable raw-executable runtime lane exists"
    )
    assert (
        sheets["multiplex"].lab_consequence_state
        == "no multiplex lab consequence packet is shipped"
    )
    assert sheets["ptm"].comparator_state == "bounded external confrontation is shipped"
    assert (
        sheets["targeted"].current_readiness == "outsider_auditable_calibration_bounded"
    )


def test_public_package_lifecycle_records_keep_refresh_and_retirement_visible() -> None:
    records = {
        record.workflow_family: record
        for record in build_flagship_public_package_lifecycle_records()
    }

    assert len(records) == 6
    assert records["dda"].created_on.isoformat() == "2026-05-07"
    assert any(
        "runtime" in trigger.lower() or "package" in trigger.lower()
        for trigger in records["lfq"].obsolescence_triggers
    )
    assert any(
        "Retire" in condition for condition in records["dia"].retirement_conditions
    )
