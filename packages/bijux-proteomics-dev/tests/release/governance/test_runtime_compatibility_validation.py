from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

from bijux_proteomics_dev.release.governance import runtime_compatibility_validation

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_release_matrix_loader_reads_json_list() -> None:
    matrix = runtime_compatibility_validation._load_release_matrix(
        REPO_ROOT, "BIJUX_RELEASE_BUILD_MATRIX_JSON"
    )
    assert isinstance(matrix, list)
    assert matrix


def test_workspace_release_slug_inventory_matches_public_install_surface() -> None:
    assert runtime_compatibility_validation._workspace_public_release_slugs(
        REPO_ROOT
    ) == (
        "agentic-proteins",
        "bijux-proteomics-foundation",
        "bijux-proteomics-core",
        "bijux-proteomics-runtime",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
        "bijux-proteomics",
        "proteomics",
        "proteomics-core",
        "proteomics-foundation",
        "proteomics-runtime",
        "proteomics-intelligence",
        "proteomics-knowledge",
        "proteomics-lab",
    )


def test_release_matrix_check_requires_every_public_install_surface() -> None:
    result = runtime_compatibility_validation._check_release_matrices(REPO_ROOT)
    assert result.ok
    assert "published install surface" in result.detail


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
