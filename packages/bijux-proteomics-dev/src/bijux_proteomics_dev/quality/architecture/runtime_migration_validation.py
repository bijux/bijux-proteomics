from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
from typing import Callable

from bijux_proteomics_dev.api.freeze_contracts import run as run_api_freeze
from bijux_proteomics_dev.quality.architecture.runtime_boundaries import run as run_runtime_boundaries
from bijux_proteomics_dev.quality.architecture.runtime_migration_ledger import run as run_migration_ledger


REQUIRED_RELEASE_SLUGS = ("bijux-proteomics-runtime", "agentic-proteins")
COMPATIBILITY_TESTS = (
    "packages/agentic-proteins/tests/unit/compat/test_import_forwarding.py",
    "packages/bijux-proteomics-dev/tests/test_runtime_boundaries_compat_forwarding.py",
    "packages/bijux-proteomics-dev/tests/test_runtime_api_contract_roots.py",
    "packages/bijux-proteomics-dev/tests/test_runtime_public_surfaces.py",
)


@dataclass(frozen=True)
class ValidationResult:
    name: str
    ok: bool
    detail: str


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
    variables = (
        "BIJUX_RELEASE_BUILD_MATRIX_JSON",
        "BIJUX_PYPI_PACKAGE_MATRIX_JSON",
        "BIJUX_GHCR_RELEASE_PACKAGE_MATRIX_JSON",
    )
    missing_by_matrix: dict[str, list[str]] = {}
    for variable in variables:
        matrix = _load_release_matrix(repo_root, variable)
        slugs = {str(entry.get("package_slug", "")).strip() for entry in matrix}
        missing = [slug for slug in REQUIRED_RELEASE_SLUGS if slug not in slugs]
        if missing:
            missing_by_matrix[variable] = missing
    if missing_by_matrix:
        return ValidationResult(
            name="release-matrices",
            ok=False,
            detail=f"missing slugs by matrix: {missing_by_matrix}",
        )
    return ValidationResult(
        name="release-matrices",
        ok=True,
        detail="release matrices include canonical runtime and compatibility packages",
    )


def _run_pytest(repo_root: Path) -> ValidationResult:
    cmd = [sys.executable, "-m", "pytest", "-q", *COMPATIBILITY_TESTS]
    result = subprocess.run(
        cmd,
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        output = "\n".join(
            line for line in (result.stdout + "\n" + result.stderr).splitlines()[-20:]
        )
        return ValidationResult(
            name="compatibility-tests",
            ok=False,
            detail=output,
        )
    return ValidationResult(
        name="compatibility-tests",
        ok=True,
        detail="compatibility tests passed",
    )


def _check(name: str, fn: Callable[[], int], success_detail: str) -> ValidationResult:
    code = fn()
    return ValidationResult(name=name, ok=code == 0, detail=success_detail if code == 0 else "failed")


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
            "release matrices include canonical runtime and compatibility packages",
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
