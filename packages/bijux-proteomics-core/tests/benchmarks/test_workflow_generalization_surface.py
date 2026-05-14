# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.benchmarks.workflow_generalization import (
    build_secondary_public_package_asset_registry,
    build_workflow_family_stability_scorecard,
    build_workflow_generalization_reports,
    count_public_packages_for_family,
    list_secondary_public_benchmark_packages,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_secondary_public_packages_cover_all_six_workflow_families() -> None:
    packages = list_secondary_public_benchmark_packages()

    assert tuple(package.workflow_family for package in packages) == (
        "dda",
        "dia",
        "lfq",
        "multiplex",
        "ptm",
        "targeted",
    )
    assert all(
        package.package_root.startswith(
            "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        )
        for package in packages
    )
    assert all(package.source_assets for package in packages)
    assert all((REPO_ROOT / package.package_root).is_dir() for package in packages)


def test_secondary_public_package_asset_registry_tracks_all_companion_roots() -> None:
    registry = build_secondary_public_package_asset_registry()

    assert registry.artifact_path.endswith("generalization_asset_registry.json")
    assert len(registry.entries) == 6
    assert all(entry.asset_root.endswith("_package") for entry in registry.entries)
    assert all(entry.remote_sources for entry in registry.entries)
    assert all(entry.citations for entry in registry.entries)
    assert all(entry.generated_boundaries for entry in registry.entries)


def test_workflow_generalization_reports_keep_two_package_transfer_visible() -> None:
    reports = {
        report.workflow_family: report
        for report in build_workflow_generalization_reports()
    }

    assert set(reports) == {"dda", "dia", "lfq", "multiplex", "ptm", "targeted"}
    assert reports["dda"].family_stability_score < 1.0
    assert reports["multiplex"].family_stability_label in {
        "fragile_transfer",
        "package_specific",
    }
    assert all(len(report.package_manifest_paths) == 2 for report in reports.values())
    assert all(len(report.runtime_package_ids) == 2 for report in reports.values())


def test_family_stability_scorecard_derives_from_generalization_reports() -> None:
    scorecard = build_workflow_family_stability_scorecard()

    assert scorecard.artifact_path.endswith("family_stability_scorecard.json")
    assert len(scorecard.entries) == 6
    assert all(0.0 <= entry.stability_score <= 1.0 for entry in scorecard.entries)
    assert count_public_packages_for_family("dda") == 2
    assert count_public_packages_for_family("targeted") == 2
