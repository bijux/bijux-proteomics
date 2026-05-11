from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    import_root,
    workspace_package_names,
)

__all__ = [
    "SourcePathIssue",
    "SourcePathReference",
    "collect_source_path_references",
    "validate_source_path_references",
]


SOURCE_PATH_RE = re.compile(
    r"(?<!https://github\.com/bijux/bijux-proteomics/blob/main/)"
    r"(?P<path>(?:packages/[^)\s`]+/src/[A-Za-z0-9_./-]+|src/[A-Za-z0-9_./-]+))"
)


@dataclass(frozen=True)
class SourcePathReference:
    """One markdown reference to a repository source path."""

    doc_path: Path
    referenced_path: str


@dataclass(frozen=True)
class SourcePathIssue:
    """One stale or unresolvable source-path reference in repository docs."""

    doc_path: Path
    referenced_path: str
    resolved_path: Path


def _markdown_docs() -> tuple[Path, ...]:
    docs: list[Path] = []
    root_readme = REPO_ROOT / "README.md"
    if root_readme.exists():
        docs.append(root_readme)
    docs.extend(sorted((REPO_ROOT / "docs").rglob("*.md")))
    for package_name in workspace_package_names():
        package_root = REPO_ROOT / "packages" / package_name
        readme_path = package_root / "README.md"
        if readme_path.exists():
            docs.append(readme_path)
        package_docs = package_root / "docs"
        if package_docs.exists():
            docs.extend(sorted(package_docs.rglob("*.md")))
    return tuple(dict.fromkeys(docs))


def _resolve_reference(doc_path: Path, reference: str) -> Path:
    if reference.startswith("packages/"):
        return REPO_ROOT / reference
    if "packages" not in doc_path.parts:
        parts = Path(reference).parts
        if len(parts) >= 2 and parts[0] == "src":
            import_name = parts[1]
            for package_name in workspace_package_names():
                if import_root(package_name) == import_name:
                    return REPO_ROOT / "packages" / package_name / reference
        return doc_path.parent / reference
    package_index = doc_path.parts.index("packages")
    package_root = Path(*doc_path.parts[: package_index + 2])
    return package_root / reference


def _should_track_reference(doc_path: Path, reference: str) -> bool:
    if reference.startswith("packages/"):
        return True
    return reference.startswith("src/")


def collect_source_path_references() -> tuple[SourcePathReference, ...]:
    """Collect `src/...` references from repository markdown docs."""

    references: list[SourcePathReference] = []
    for doc_path in _markdown_docs():
        text = doc_path.read_text(encoding="utf-8")
        for match in SOURCE_PATH_RE.finditer(text):
            reference = match.group("path")
            if not _should_track_reference(doc_path, reference):
                continue
            references.append(
                SourcePathReference(
                    doc_path=doc_path,
                    referenced_path=reference,
                )
            )
    return tuple(references)


def validate_source_path_references() -> tuple[SourcePathIssue, ...]:
    """Return every stale source-path reference in repository markdown docs."""

    issues: list[SourcePathIssue] = []
    for reference in collect_source_path_references():
        resolved_path = _resolve_reference(
            reference.doc_path, reference.referenced_path
        )
        if not resolved_path.exists():
            issues.append(
                SourcePathIssue(
                    doc_path=reference.doc_path,
                    referenced_path=reference.referenced_path,
                    resolved_path=resolved_path,
                )
            )
    return tuple(issues)
