from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, cast

from bijux_proteomics_dev.governance.package_shape.package_tree_layout import (
    load_package_tree_layout_policy,
)

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
    if package_name == "bijux-proteomics":
        return "bijux_proteomics_alias"
    return package_name.replace("-", "_")


def _section(text: str, heading: str) -> str:
    marker = f"## {heading}\n"
    start = text.find(marker)
    assert start >= 0, f"missing section heading: {heading}"
    start += len(marker)
    end = text.find("\n## ", start)
    if end < 0:
        end = len(text)
    return text[start:end]


def test_workspace_packages_expose_architecture_docs() -> None:
    missing = [
        path.relative_to(REPO_ROOT).as_posix()
        for package_name in _package_names()
        for path in [_package_dir(package_name) / "docs" / "ARCHITECTURE.md"]
        if not path.exists()
    ]
    assert not missing, "missing package architecture docs:\n" + "\n".join(missing)


def test_architecture_docs_share_identity_and_structure_sections() -> None:
    failures: list[str] = []

    for package_name in _package_names():
        path = _package_dir(package_name) / "docs" / "ARCHITECTURE.md"
        text = path.read_text(encoding="utf-8")
        expected_bits = [
            "## Package identity",
            f"- Distribution name: `{package_name}`",
            f"- Import root: `{_import_root(package_name)}`",
            "## Architectural role",
            "## Design constraints",
            "## Canonical tree layout",
            "## Dependency direction",
            "## Downstream expectations",
            "## Extension signals",
            "## Misplacement signals",
            "## Review questions",
        ]
        missing = [bit for bit in expected_bits if bit not in text]
        if missing:
            failures.append(
                f"{path.relative_to(REPO_ROOT).as_posix()}: missing {', '.join(missing)}"
            )

    assert not failures, "package architecture docs contract failed:\n" + "\n".join(
        failures
    )


def test_architecture_docs_publish_canonical_tree_layouts() -> None:
    failures: list[str] = []
    policy_by_package = {
        entry.distribution_name: entry
        for entry in load_package_tree_layout_policy().packages
    }

    for package_name in _package_names():
        path = _package_dir(package_name) / "docs" / "ARCHITECTURE.md"
        section = _section(path.read_text(encoding="utf-8"), "Canonical tree layout")
        entry = policy_by_package[package_name]
        expected_bits = [
            f"- Import roots: {_inline_list(entry.import_roots)}",
            f"- Top-level families: {_inline_list(tuple(f'{name}/' for name in entry.top_level_families))}",
            f"- Root modules: {_inline_list(entry.root_module_files)}",
        ]
        missing = [bit for bit in expected_bits if bit not in section]
        if missing:
            failures.append(
                f"{path.relative_to(REPO_ROOT).as_posix()}: missing {', '.join(missing)}"
            )

    assert not failures, "package architecture tree layout docs failed:\n" + "\n".join(
        failures
    )


def _inline_list(values: tuple[str, ...]) -> str:
    if not values:
        return "none"
    return ", ".join(f"`{value}`" for value in values)
