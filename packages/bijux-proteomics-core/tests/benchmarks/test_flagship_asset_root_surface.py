# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.benchmarks.flagship_asset_roots import (
    build_flagship_asset_obsolescence_audit,
    build_flagship_asset_refresh_report,
    build_flagship_asset_root_contract,
    flagship_asset_contract_path,
    flagship_asset_obsolescence_audit_path,
    flagship_asset_refresh_report_path,
    list_flagship_asset_root_entries,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_flagship_asset_root_contract_tracks_all_six_product_owned_roots() -> None:
    contract = build_flagship_asset_root_contract()

    assert contract.contract_path == flagship_asset_contract_path()
    assert tuple(entry.workflow_family for entry in contract.entries) == (
        "dda",
        "dia",
        "lfq",
        "multiplex",
        "ptm",
        "targeted",
    )
    for entry in contract.entries:
        assert entry.asset_root.startswith(
            "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        )
        assert entry.source_locator_manifest_path.endswith("source_locator_manifest.json")
        assert entry.citation_manifest_path.endswith("citation_manifest.json")
        assert entry.generated_boundary_path.endswith("generated_boundary.json")
        assert entry.rebuild_instructions_path.endswith("rebuild_instructions.md")
        assert entry.remote_sources
        assert entry.citations
        assert entry.generated_boundaries
        assert (REPO_ROOT / entry.asset_root).is_dir()


def test_flagship_asset_entries_keep_written_support_files_and_copied_snapshots_visible() -> None:
    entries = list_flagship_asset_root_entries()

    assert len(entries) == 6
    for entry in entries:
        assert (REPO_ROOT / entry.source_locator_manifest_path).exists()
        assert (REPO_ROOT / entry.citation_manifest_path).exists()
        assert (REPO_ROOT / entry.generated_boundary_path).exists()
        assert (REPO_ROOT / entry.rebuild_instructions_path).exists()
        for source in entry.remote_sources:
            assert (REPO_ROOT / source.local_artifact_path).exists()


def test_flagship_asset_refresh_report_stays_ready_when_local_support_files_exist() -> None:
    report = build_flagship_asset_refresh_report(check_remote=False)

    assert report.report_path == flagship_asset_refresh_report_path()
    assert len(report.entries) == 6
    for entry in report.entries:
        assert entry.local_paths_present is True
        assert entry.local_path_count >= 1
        assert entry.freshness_state == "ready"
        assert entry.remote_checks
        assert all(check.detail for check in entry.remote_checks)


def test_flagship_asset_obsolescence_audit_keeps_stronger_dataset_pressure_visible() -> None:
    audit = build_flagship_asset_obsolescence_audit()

    assert audit.audit_path == flagship_asset_obsolescence_audit_path()
    assert len(audit.entries) == 6
    assert all(entry.stronger_public_dataset_needed for entry in audit.entries)
    assert all(entry.replacement_direction for entry in audit.entries)
