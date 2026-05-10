from __future__ import annotations

from pathlib import Path
import re

from bijux_proteomics_dev.governance.support.workspace_inventory import (
    package_root,
)

__all__ = [
    "architecture_doc_path",
    "boundary_doc_path",
    "markdown_bullets",
    "module_topology_tokens",
    "readme_path",
    "readme_opening_lines",
    "section_lines",
]


def boundary_doc_path(package_name: str) -> Path:
    root = package_root(package_name)
    if package_name == "bijux-proteomics-dev":
        return root / "docs" / "SCOPE.md"
    return root / "docs" / "BOUNDARIES.md"


def architecture_doc_path(package_name: str) -> Path:
    return package_root(package_name) / "docs" / "ARCHITECTURE.md"


def readme_path(package_name: str) -> Path:
    return package_root(package_name) / "README.md"


def readme_opening_lines(package_name: str) -> tuple[str, ...]:
    lines = readme_path(package_name).read_text(encoding="utf-8").splitlines()
    opening: list[str] = []
    in_generated_badges = False
    for line in lines:
        stripped = line.rstrip()
        if stripped == "<!-- bijux-proteomics-badges:generated:start -->":
            in_generated_badges = True
            continue
        if stripped == "<!-- bijux-proteomics-badges:generated:end -->":
            in_generated_badges = False
            continue
        if in_generated_badges:
            continue
        if stripped.startswith("## "):
            break
        if stripped.startswith("# "):
            continue
        opening.append(stripped)
    return tuple(opening)


def section_lines(path: Path, heading: str) -> tuple[str, ...]:
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    section: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if in_section:
                break
            in_section = line.strip() == heading
            continue
        if in_section:
            section.append(line.rstrip())
    return tuple(section)


def markdown_bullets(path: Path, heading: str) -> tuple[str, ...]:
    return tuple(
        line[2:].strip()
        for line in section_lines(path, heading)
        if line.startswith("- ")
    )


def module_topology_tokens(package_name: str) -> tuple[str, ...]:
    tokens: list[str] = []
    path = architecture_doc_path(package_name)
    if not path.exists():
        return ()
    for line in section_lines(path, "## Module topology"):
        tokens.extend(match.group(1) for match in re.finditer(r"`([^`]+)`", line))
    return tuple(tokens)
