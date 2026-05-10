from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path
import sys
import tomllib
import subprocess  # nosec B404

from bijux_proteomics_dev.governance.contracts.freeze_contracts import (
    run as run_api_freeze,
)
from bijux_proteomics_dev.quality.architecture.runtime_boundaries import (
    run as run_runtime_boundaries,
)
from bijux_proteomics_dev.release.governance.compatibility_ledger import (
    run as run_migration_ledger,
)

COMPATIBILITY_TESTS = (
    "packages/agentic-proteins/tests/package/test_import_forwarding.py",
    "packages/bijux-proteomics/tests/compatibility/test_bijux_proteomics_alias.py",
    "packages/proteomics/tests/compatibility/test_proteomics_alias.py",
    "packages/proteomics-core/tests/compatibility/test_proteomics_core_alias.py",
    "packages/proteomics-foundation/tests/compatibility/test_proteomics_foundation_alias.py",
    "packages/proteomics-runtime/tests/compatibility/test_proteomics_runtime_alias.py",
    "packages/proteomics-intelligence/tests/compatibility/test_proteomics_intelligence_alias.py",
    "packages/proteomics-knowledge/tests/compatibility/test_proteomics_knowledge_alias.py",
    "packages/proteomics-lab/tests/compatibility/test_proteomics_lab_alias.py",
    "packages/bijux-proteomics-dev/tests/quality/architecture/test_runtime_boundaries_compat_forwarding.py",
    "packages/bijux-proteomics-dev/tests/governance/runtime/test_api_contract_roots.py",
    "packages/bijux-proteomics-dev/tests/governance/runtime/test_public_surfaces.py",
)


@dataclass(frozen=True)
class ValidationResult:
    name: str
    ok: bool
    detail: str


def _workspace_public_release_slugs(repo_root: Path) -> tuple[str, ...]:
    with (repo_root / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    workspace = data["tool"]["bijux_proteomics"]
    docs_package = str(workspace["docs_package"])
    packages = workspace["packages"]
    if not isinstance(packages, list):
        raise ValueError("tool.bijux_proteomics.packages must be a list")
    return tuple(str(package) for package in packages if str(package) != docs_package)


def _load_release_matrix(repo_root: Path, variable: str) -> list[dict[str, object]]:
    release_env = repo_root / ".github" / "release.env"
    for line in release_env.read_text(encoding="utf-8").splitlines():
        if not line.startswith(f"{variable}="):
            continue
        value = line.split("=", 1)[1].strip().strip("'")
        loaded = json.loads(value)
        if not isinstance(loaded, list):
            raise ValueError(f"{variable} must be a JSON list")
        return [item for item in loaded if isinstance(item, dict)]
    raise ValueError(f"missing release variable: {variable}")


def _check_release_matrices(repo_root: Path) -> ValidationResult:
    required_slugs = set(_workspace_public_release_slugs(repo_root))
    variables = (
        "BIJUX_RELEASE_BUILD_MATRIX_JSON",
        "BIJUX_PYPI_PACKAGE_MATRIX_JSON",
        "BIJUX_GHCR_RELEASE_PACKAGE_MATRIX_JSON",
    )
    mismatches_by_matrix: dict[str, dict[str, list[str]]] = {}
    for variable in variables:
        matrix = _load_release_matrix(repo_root, variable)
        slugs = {str(entry.get("package_slug", "")).strip() for entry in matrix}
        missing = sorted(required_slugs - slugs)
        unexpected = sorted(slugs - required_slugs)
        if missing or unexpected:
            mismatches_by_matrix[variable] = {
                "missing": missing,
                "unexpected": unexpected,
            }
    if mismatches_by_matrix:
        return ValidationResult(
            name="release-matrices",
            ok=False,
            detail=f"release matrix mismatches: {mismatches_by_matrix}",
        )
    return ValidationResult(
        name="release-matrices",
        ok=True,
        detail="release matrices include every published install surface",
    )


def _run_pytest(repo_root: Path) -> ValidationResult:
    cache_dir = repo_root / "artifacts" / "root" / "pytest-cache"
    for test_path in COMPATIBILITY_TESTS:
        command = [
            sys.executable,
            "-m",
            "pytest",
            "--rootdir",
            str(repo_root),
            "-o",
            f"cache_dir={cache_dir}",
            "-q",
            test_path,
        ]
        result = subprocess.run(  # nosec B603
            command,
            cwd=repo_root,
            check=False,
        )
        if result.returncode != 0:
            return ValidationResult(
                name="compatibility-tests",
                ok=False,
                detail=(
                    f"compatibility test failures in {test_path} "
                    f"(exit code {result.returncode})"
                ),
            )
    if not COMPATIBILITY_TESTS:
        return ValidationResult(
            name="compatibility-tests",
            ok=False,
            detail="no compatibility tests are configured",
        )
    return ValidationResult(
        name="compatibility-tests",
        ok=True,
        detail="compatibility tests passed",
    )


def _check(name: str, fn: Callable[[], int], success_detail: str) -> ValidationResult:
    code = fn()
    return ValidationResult(
        name=name, ok=code == 0, detail=success_detail if code == 0 else "failed"
    )


def run(repo_root: Path) -> int:
    checks: list[ValidationResult] = [
        _check(
            "runtime-boundaries",
            lambda: run_runtime_boundaries(repo_root),
            "runtime boundary contracts passed",
        ),
        _check(
            "migration-ledger",
            lambda: run_migration_ledger(check=True),
            "migration ledger is up to date",
        ),
        _check(
            "api-freeze",
            lambda: run_api_freeze(repo_root),
            "api freeze contracts passed",
        ),
        _check(
            "release-matrices",
            lambda: 0 if _check_release_matrices(repo_root).ok else 1,
            "release matrices include every published install surface",
        ),
        _run_pytest(repo_root),
    ]

    failures = [result for result in checks if not result.ok]
    for result in checks:
        state = "PASS" if result.ok else "FAIL"
        print(f"[{state}] {result.name}: {result.detail}")
    if failures:
        return 1
    print("runtime migration validation passed")
    return 0


def main() -> int:
    return run(Path.cwd())


if __name__ == "__main__":
    raise SystemExit(main())
