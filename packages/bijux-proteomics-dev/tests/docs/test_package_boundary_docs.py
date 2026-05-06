from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, cast

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


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


def _boundary_doc_path(package_name: str) -> Path:
    package_dir = _package_dir(package_name)
    if package_name == "bijux-proteomics-dev":
        return package_dir / "docs" / "SCOPE.md"
    return package_dir / "docs" / "BOUNDARIES.md"


def test_workspace_packages_expose_boundary_docs() -> None:
    missing = [
        path.relative_to(REPO_ROOT).as_posix()
        for package_name in _package_names()
        for path in [_boundary_doc_path(package_name)]
        if not path.exists()
    ]
    assert not missing, "missing package boundary docs:\n" + "\n".join(missing)


def test_boundary_docs_share_identity_and_ownership_shape() -> None:
    failures: list[str] = []

    for package_name in _package_names():
        path = _boundary_doc_path(package_name)
        text = path.read_text(encoding="utf-8")
        expected_bits = [
            "## Package identity",
            f"- Distribution name: `{package_name}`",
            f"- Import root: `{_import_root(package_name)}`",
            "## This package owns",
            "## This package does not own",
            "## Downstream expectations",
            "## Escalation signals",
            "## Review questions",
        ]
        missing = [bit for bit in expected_bits if bit not in text]
        if missing:
            failures.append(
                f"{path.relative_to(REPO_ROOT).as_posix()}: missing {', '.join(missing)}"
            )

    assert not failures, "package boundary docs contract failed:\n" + "\n".join(
        failures
    )


def test_maintainer_scope_doc_has_owned_surfaces_and_routing_sections() -> None:
    path = REPO_ROOT / "packages" / "bijux-proteomics-dev" / "docs" / "SCOPE.md"
    text = path.read_text(encoding="utf-8")
    expected_bits = [
        "## Package identity",
        "- Distribution name: `bijux-proteomics-dev`",
        "- Import root: `bijux_proteomics_dev`",
        "## This package owns",
        "## Owned maintenance surfaces",
        "## This package does not own",
        "## Downstream expectations",
        "## Change routing expectations",
        "## Escalation signals",
        "## Review questions",
    ]
    missing = [bit for bit in expected_bits if bit not in text]
    assert not missing, (
        f"{path.relative_to(REPO_ROOT).as_posix()}: missing {', '.join(missing)}"
    )


def test_runtime_boundary_doc_has_escalation_section() -> None:
    path = (
        REPO_ROOT / "packages" / "bijux-proteomics-runtime" / "docs" / "BOUNDARIES.md"
    )
    text = path.read_text(encoding="utf-8")
    expected_bits = [
        "## Escalation signals",
        "## Boundary failure signals",
        "boundary failure",
        "owning lower package contract is incomplete",
    ]
    missing = [bit for bit in expected_bits if bit not in text]
    assert not missing, (
        f"{path.relative_to(REPO_ROOT).as_posix()}: missing {', '.join(missing)}"
    )
