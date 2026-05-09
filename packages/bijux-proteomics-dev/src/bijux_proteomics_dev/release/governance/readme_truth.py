from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.release.governance.release_readiness_matrix import (
    RELEASE_READINESS_MATRIX_PATH,
)

__all__ = [
    "ReadmeTruthIssue",
    "validate_readme_truth",
]


README_PATH = REPO_ROOT / "README.md"
BADGE_BLOCK_START = "<!-- bijux-proteomics-badges:generated:start -->"
BADGE_BLOCK_END = "<!-- bijux-proteomics-badges:generated:end -->"
REQUIRED_SECTIONS = (
    "Product Scope",
    "Current Credible Workflow Families",
    "Forbidden Claims",
    "Reader Paths",
    "Package Map",
)
REQUIRED_LINK_SNIPPETS = (
    "foundation/product-architecture/",
    "foundation/cross-package-ownership/",
    "foundation/release-readiness-matrix/",
    "foundation/public-artifact-index/",
    "operations/runtime-migration-validation/",
)
BANNED_STRONG_TERMS = (
    "release-ready",
    "reference-grade",
    "product-grade",
)


@dataclass(frozen=True)
class ReadmeTruthIssue:
    """One root README wording or structure issue."""

    code: str
    detail: str


def _section_bounds(text: str, heading: str) -> tuple[int, int]:
    marker = f"## {heading}\n"
    start = text.find(marker)
    if start < 0:
        raise ValueError(f"missing section {heading!r}")
    start += len(marker)
    end = text.find("\n## ", start)
    if end < 0:
        end = len(text)
    return start, end


def _load_matrix_categories() -> tuple[dict[str, object], ...]:
    with RELEASE_READINESS_MATRIX_PATH.open("rb") as handle:
        raw = tomllib.load(handle)
    return tuple(raw.get("category", ()))


def validate_readme_truth(repo_root: Path = REPO_ROOT) -> tuple[ReadmeTruthIssue, ...]:
    """Validate that the root README stays behind the checked readiness matrix."""

    text = README_PATH.read_text(encoding="utf-8")
    issues: list[ReadmeTruthIssue] = []

    section_positions: list[int] = []
    for heading in REQUIRED_SECTIONS:
        marker = f"## {heading}\n"
        index = text.find(marker)
        if index < 0:
            issues.append(
                ReadmeTruthIssue(
                    code="missing-required-section",
                    detail=f"README is missing section {heading!r}",
                )
            )
            continue
        section_positions.append(index)
    if section_positions != sorted(section_positions):
        issues.append(
            ReadmeTruthIssue(
                code="section-order-drift",
                detail="README scope, limits, reader-path, and package-map sections drifted out of order",
            )
        )

    badge_start = text.find(BADGE_BLOCK_START)
    badge_end = text.find(BADGE_BLOCK_END)
    if badge_start < 0 or badge_end < 0:
        issues.append(
            ReadmeTruthIssue(
                code="missing-badge-block",
                detail="README is missing the managed badge block",
            )
        )
    else:
        forbidden_index = text.find("## Forbidden Claims\n")
        reader_paths_index = text.find("## Reader Paths\n")
        if badge_start < forbidden_index or badge_end > reader_paths_index:
            issues.append(
                ReadmeTruthIssue(
                    code="badge-block-too-early",
                    detail=(
                        "README badges must stay after the limit-setting sections "
                        "and before reader routing"
                    ),
                )
            )

    for snippet in REQUIRED_LINK_SNIPPETS:
        if snippet not in text:
            issues.append(
                ReadmeTruthIssue(
                    code="missing-required-link",
                    detail=f"README is missing required evidence link {snippet}",
                )
            )

    if RELEASE_READINESS_MATRIX_PATH.exists():
        categories = _load_matrix_categories()
        if any(not bool(category["ready"]) for category in categories):
            if "This repository does not yet claim:" not in text:
                issues.append(
                    ReadmeTruthIssue(
                        code="missing-readiness-disclaimer",
                        detail=(
                            "README must explicitly narrow stronger release language "
                            "while readiness matrix categories remain blocked"
                        ),
                    )
                )

    try:
        forbidden_start, forbidden_end = _section_bounds(text, "Forbidden Claims")
    except ValueError as exc:
        issues.append(ReadmeTruthIssue(code="missing-forbidden-claims", detail=str(exc)))
        return tuple(sorted(issues, key=lambda issue: (issue.code, issue.detail)))

    outside_forbidden = text[:forbidden_start] + text[forbidden_end:]
    outside_forbidden_lower = outside_forbidden.lower()
    for term in BANNED_STRONG_TERMS:
        if term in outside_forbidden_lower:
            issues.append(
                ReadmeTruthIssue(
                    code="banned-strong-term-outside-limits",
                    detail=f"README uses {term!r} outside the Forbidden Claims section",
                )
            )
    return tuple(sorted(issues, key=lambda issue: (issue.code, issue.detail)))
