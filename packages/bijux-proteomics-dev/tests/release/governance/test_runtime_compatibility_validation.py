from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

from bijux_proteomics_dev.release.governance import runtime_compatibility_validation

REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "packages").is_dir() and (parent / "configs").is_dir())


def test_release_matrix_loader_reads_json_list() -> None:
    matrix = runtime_compatibility_validation._load_release_matrix(
        REPO_ROOT, "BIJUX_RELEASE_BUILD_MATRIX_JSON"
    )
    assert isinstance(matrix, list)
    assert matrix


def test_release_matrix_check_requires_runtime_and_compat_entries() -> None:
    result = runtime_compatibility_validation._check_release_matrices(REPO_ROOT)
    assert result.ok
    assert "compatibility and core release packages" in result.detail


def test_runtime_migration_runner_succeeds_with_stubbed_checks(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        runtime_compatibility_validation,
        "run_runtime_boundaries",
        lambda _repo_root: 0,
    )
    monkeypatch.setattr(
        runtime_compatibility_validation,
        "run_migration_ledger",
        lambda check: 0,
    )
    monkeypatch.setattr(
        runtime_compatibility_validation,
        "run_api_freeze",
        lambda _repo_root: 0,
    )
    monkeypatch.setattr(
        runtime_compatibility_validation,
        "_run_pytest",
        lambda _repo_root: runtime_compatibility_validation.ValidationResult(
            name="compatibility-tests", ok=True, detail="compatibility tests passed"
        ),
    )
    exit_code = runtime_compatibility_validation.run(REPO_ROOT)
    assert exit_code == 0
