from __future__ import annotations

from bijux_proteomics_dev.release.governance.benchmark_asset_governance import (
    build_benchmark_asset_audit,
    run,
)


def test_benchmark_asset_governance_pages_are_up_to_date() -> None:
    assert run(check=True) == 0


def test_benchmark_asset_audit_covers_primary_and_companion_roots() -> None:
    entries = build_benchmark_asset_audit()

    assert len(entries) == 12
    families = {entry.workflow_family.value for entry in entries}
    assert families == {"dda", "dia", "lfq", "multiplex", "ptm", "targeted"}
    assert sum(entry.package_role == "primary flagship package" for entry in entries) == 6
    assert (
        sum(entry.package_role == "companion generalization package" for entry in entries)
        == 6
    )
    assert all(entry.support_files_present for entry in entries)
    assert all(entry.source_rows for entry in entries)
    assert all(
        source.local_sha256 and source.upstream_repo_source_path
        for entry in entries
        for source in entry.source_rows
    )
