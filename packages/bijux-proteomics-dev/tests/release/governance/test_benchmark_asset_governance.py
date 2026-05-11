from __future__ import annotations

from bijux_proteomics_dev.release.governance.benchmark_asset_governance import (
    build_benchmark_asset_audit,
    build_benchmark_incompleteness_ledger,
    build_benchmark_licensing_matrix,
    run,
)


def test_benchmark_asset_governance_pages_are_up_to_date() -> None:
    assert run(check=True) == 0


def test_benchmark_asset_audit_covers_primary_and_companion_roots() -> None:
    entries = build_benchmark_asset_audit()

    assert len(entries) == 12
    families = {entry.workflow_family.value for entry in entries}
    assert families == {"dda", "dia", "lfq", "multiplex", "ptm", "targeted"}
    assert (
        sum(entry.package_role == "primary flagship package" for entry in entries) == 6
    )
    assert (
        sum(
            entry.package_role == "companion generalization package"
            for entry in entries
        )
        == 6
    )
    assert all(entry.support_files_present for entry in entries)
    assert all(entry.source_rows for entry in entries)
    assert all(entry.benchmark_title for entry in entries)
    assert all(entry.public_dataset_identity for entry in entries)
    assert all(
        source.public_source_name
        and source.local_sha256
        and source.upstream_repo_source_path
        for entry in entries
        for source in entry.source_rows
    )


def test_benchmark_asset_governance_keeps_licensing_and_incompleteness_explicit() -> (
    None
):
    licensing = build_benchmark_licensing_matrix()
    incompleteness = build_benchmark_incompleteness_ledger()

    assert len(licensing) == 12
    assert len(incompleteness) == 12
    assert all(entry.dataset_license_and_reuse_note for entry in licensing)
    assert all(entry.source_license_notes for entry in licensing)
    assert all(entry.redistributed_artifact_paths for entry in licensing)
    assert all(entry.quality_blockers for entry in incompleteness)
    assert all(entry.non_transfer_zones for entry in incompleteness)
