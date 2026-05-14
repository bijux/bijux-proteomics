from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, cast

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
BIJUX_PROTEOMICS_DOCS_URL = "https://bijux.io/bijux-proteomics/"


def _workspace_metadata() -> dict[str, Any]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return cast(dict[str, Any], data["tool"]["bijux_proteomics"])


def _package_path(package_name: str) -> Path:
    return REPO_ROOT / "packages" / package_name


def _package_project(package_name: str) -> dict[str, Any]:
    with (_package_path(package_name) / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return cast(dict[str, Any], data["project"])


def _public_package_docs_urls() -> dict[str, str]:
    workspace = _workspace_metadata()
    urls: dict[str, str] = {}
    docs_package = cast(str, workspace["docs_package"])
    for package_name in cast(list[str], workspace["packages"]):
        if package_name == docs_package:
            continue
        project_urls = _package_project(package_name).get("urls", {})
        urls[package_name] = str(project_urls["Documentation"])
    return urls


def _docs_source_path(docs_url: str) -> Path:
    assert docs_url.startswith(BIJUX_PROTEOMICS_DOCS_URL), docs_url
    relative_path = docs_url.removeprefix(BIJUX_PROTEOMICS_DOCS_URL).rstrip("/")
    docs_root = REPO_ROOT / "docs"
    candidates = [
        docs_root / relative_path / "index.md",
        docs_root / f"{relative_path}.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def test_public_package_documentation_urls_resolve_to_checked_in_pages() -> None:
    failures: list[str] = []
    for package_name, docs_url in sorted(_public_package_docs_urls().items()):
        docs_path = _docs_source_path(docs_url)
        if not docs_path.exists():
            failures.append(f"{package_name}: missing docs page for {docs_url}")
    assert not failures, "public package docs URLs failed:\n" + "\n".join(failures)


def test_root_readme_package_map_advertises_resolvable_docs_pages() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    failures: list[str] = []
    for package_name, docs_url in sorted(_public_package_docs_urls().items()):
        if docs_url not in readme:
            failures.append(f"{package_name}: README should advertise {docs_url}")
            continue
        docs_path = _docs_source_path(docs_url)
        if not docs_path.exists():
            failures.append(
                f"{package_name}: README points at missing docs page {docs_url}"
            )

    assert not failures, "README docs publication contract failed:\n" + "\n".join(
        failures
    )


def _handbook_layout(section_root: Path) -> tuple[list[str], list[str], dict[str, int]]:
    root_markdown = sorted(path.name for path in section_root.glob("*.md"))
    section_dirs = sorted(path.name for path in section_root.iterdir() if path.is_dir())
    section_counts = {
        path.name: len(list(path.glob("*.md")))
        for path in section_root.iterdir()
        if path.is_dir()
    }
    return root_markdown, section_dirs, section_counts


def test_repository_handbook_layout_is_sectioned() -> None:
    root_markdown, section_dirs, section_counts = _handbook_layout(
        REPO_ROOT / "docs" / "01-bijux-proteomics"
    )

    assert root_markdown == ["index.md"]
    assert section_dirs
    assert all(section_counts[section] > 0 for section in section_dirs)


def test_maintenance_handbook_layout_is_sectioned() -> None:
    root_markdown, section_dirs, section_counts = _handbook_layout(
        REPO_ROOT / "docs" / "08-bijux-proteomics-maintain"
    )

    assert root_markdown == ["index.md"]
    assert section_dirs
    assert all(section_counts[section] > 0 for section in section_dirs)
