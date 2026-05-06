from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.architecture.runtime_boundaries import (
    check_runtime_imports_compat_package,
    load_policy,
)

REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "packages").is_dir() and (parent / "configs").is_dir())


def test_runtime_package_does_not_import_compat_package() -> None:
    policy = load_policy(REPO_ROOT)
    failures = check_runtime_imports_compat_package(policy)
    assert not failures, "runtime must not import compat package:\n" + "\n".join(
        failures
    )
