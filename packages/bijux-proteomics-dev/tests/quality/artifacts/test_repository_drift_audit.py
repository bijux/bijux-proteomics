from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.artifacts.repository_drift_audit import (
    REPOSITORY_DRIFT_AUDIT_PATH,
    build_repository_drift_audit,
    run,
    validate_repository_drift_audit,
)


def test_repository_drift_audit_detects_package_local_owner_duplicates(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "packages" / "bijux-proteomics-runtime"
    (runtime_root / "configs").mkdir(parents=True)
    (runtime_root / "benchmark-assets").mkdir()
    (runtime_root / "docs").mkdir()
    (runtime_root / "docs" / "artifact-governance.md").write_text(
        "duplicate",
        encoding="utf-8",
    )
    (runtime_root / "artifacts").mkdir()

    entries = {
        entry.audit_id: entry for entry in build_repository_drift_audit(tmp_path)
    }

    assert entries["package-governance-mirrors"].offending_paths == (
        "packages/bijux-proteomics-runtime/configs",
    )
    assert entries["benchmark-root-duplicates"].offending_paths == (
        "packages/bijux-proteomics-runtime/benchmark-assets",
    )
    assert entries["singleton-doc-duplicates"].offending_paths == (
        "packages/bijux-proteomics-runtime/docs/artifact-governance.md",
    )
    assert entries["package-local-artifacts"].offending_paths == (
        "packages/bijux-proteomics-runtime/artifacts",
    )


def test_repository_drift_audit_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_live_repo_has_no_repository_drift_duplicates() -> None:
    assert REPOSITORY_DRIFT_AUDIT_PATH.exists()
    assert validate_repository_drift_audit() == ()
