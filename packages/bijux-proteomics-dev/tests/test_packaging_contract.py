from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[3]
EXPECTED_FALLBACK_VERSION = "0.3.3"
EXPECTED_REQUIRES_PYTHON = ">=3.11,<4"


def _workspace_metadata() -> dict[str, Any]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return cast(dict[str, Any], data["tool"]["bijux_proteomics"])


def _package_names() -> list[str]:
    workspace = _workspace_metadata()
    docs_package = cast(str, workspace["docs_package"])
    return [
        package_name
        for package_name in cast(list[str], workspace["packages"])
        if package_name != docs_package
    ]


def _pyproject(package_name: str) -> dict[str, Any]:
    with (REPO_ROOT / "packages" / package_name / "pyproject.toml").open(
        "rb"
    ) as handle:
        return cast(dict[str, Any], tomllib.load(handle))


def test_publishable_packages_define_hatch_vcs_fallback_versions() -> None:
    failures: list[str] = []

    for package_name in _package_names():
        version_config = _pyproject(package_name).get("tool", {}).get("hatch", {}).get(
            "version", {}
        )
        if version_config.get("fallback-version") != EXPECTED_FALLBACK_VERSION:
            failures.append(package_name)

    assert not failures, "missing hatch-vcs fallback versions:\n" + "\n".join(failures)


def test_publishable_packages_bound_supported_python_major_versions() -> None:
    failures: list[str] = []

    for package_name in _package_names():
        project = _pyproject(package_name).get("project", {})
        if project.get("requires-python") != EXPECTED_REQUIRES_PYTHON:
            failures.append(package_name)

    assert not failures, "misaligned requires-python values:\n" + "\n".join(failures)
