from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[3]


def _workspace_metadata() -> dict[str, Any]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return cast(dict[str, Any], data["tool"]["bijux_proteomics"])


def _package_names() -> list[str]:
    workspace = _workspace_metadata()
    return list(cast(list[str], workspace["packages"]))


def _package_dir(package_name: str) -> Path:
    return REPO_ROOT / "packages" / package_name


def _import_root(package_name: str) -> str:
    if package_name == "bijux-proteomics-core":
        return "bijux_proteomics"
    return package_name.replace("-", "_")


def _release_doc_packages() -> list[str]:
    return [
        package_name
        for package_name in _package_names()
        if (_package_dir(package_name) / "docs" / "maintainer" / "pypi.md").exists()
    ]


def test_publishable_packages_expose_maintainer_release_docs() -> None:
    missing = [
        path.relative_to(REPO_ROOT).as_posix()
        for package_name in _release_doc_packages()
        for path in [_package_dir(package_name) / "docs" / "maintainer" / "pypi.md"]
        if not path.exists()
    ]
    assert not missing, "missing maintainer release docs:\n" + "\n".join(missing)


def test_release_docs_share_identity_and_release_sections() -> None:
    failures: list[str] = []

    for package_name in _release_doc_packages():
        path = _package_dir(package_name) / "docs" / "maintainer" / "pypi.md"
        text = path.read_text(encoding="utf-8")
        expected_bits = [
            "# PyPI Maintainer Notes",
            "## Package identity",
            f"- package: `{package_name}`",
            f"- import root: `{_import_root(package_name)}`",
            "- repository: `bijux/bijux-proteomics`",
            "## Release surface",
            "## Release contract",
            "## Validation focus",
            "## Release checklist",
            "## Explicit non-goals",
        ]
        missing = [bit for bit in expected_bits if bit not in text]
        if missing:
            failures.append(
                f"{path.relative_to(REPO_ROOT).as_posix()}: missing {', '.join(missing)}"
            )

    assert not failures, "maintainer release docs contract failed:\n" + "\n".join(
        failures
    )


def test_maintainer_package_entry_doc_has_role_and_routing_sections() -> None:
    path = REPO_ROOT / "packages" / "bijux-proteomics-dev" / "docs" / "index.md"
    text = path.read_text(encoding="utf-8")
    expected_bits = [
        "## Package identity",
        "- Distribution name: `bijux-proteomics-dev`",
        "- Import root: `bijux_proteomics_dev`",
        "## Package role",
        "## Boundary reminders",
        "## Key maintainer entrypoints",
        "## Source guide",
        "## Downstream expectation",
    ]
    missing = [bit for bit in expected_bits if bit not in text]
    assert not missing, (
        f"{path.relative_to(REPO_ROOT).as_posix()}: missing {', '.join(missing)}"
    )


def test_maintainer_test_doc_has_scope_and_expectation_sections() -> None:
    path = REPO_ROOT / "packages" / "bijux-proteomics-dev" / "docs" / "TESTS.md"
    text = path.read_text(encoding="utf-8")
    expected_bits = [
        "## Test scope",
        "## Required test strata",
        "## Maintainer expectations",
        "## Common validation surfaces",
        "## Non-goals",
    ]
    missing = [bit for bit in expected_bits if bit not in text]
    assert not missing, (
        f"{path.relative_to(REPO_ROOT).as_posix()}: missing {', '.join(missing)}"
    )
