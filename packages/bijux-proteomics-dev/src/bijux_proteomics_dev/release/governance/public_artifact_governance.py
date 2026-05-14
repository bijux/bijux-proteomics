from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_intelligence.reviews.public_scrutiny import (
    PublicArtifactIndex,
    PublicArtifactRoleMatrix,
    build_public_artifact_index,
    build_public_artifact_role_matrix,
)

__all__ = [
    "PUBLIC_ARTIFACT_INDEX_PATH",
    "PUBLIC_ARTIFACT_ROLE_MATRIX_PATH",
    "PublicArtifactGovernanceIssue",
    "build_public_artifact_docs",
    "run",
    "validate_public_artifact_governance",
]


FOUNDATION_DIR = REPO_ROOT / "docs" / "01-bijux-proteomics" / "foundation"
PUBLIC_ARTIFACT_INDEX_PATH = FOUNDATION_DIR / "public-artifact-index.md"
PUBLIC_ARTIFACT_ROLE_MATRIX_PATH = FOUNDATION_DIR / "public-artifact-role-matrix.md"
_LAST_REVIEWED = "2026-05-09"


@dataclass(frozen=True)
class PublicArtifactGovernanceIssue:
    """One artifact-role governance issue."""

    code: str
    detail: str


def build_public_artifact_docs() -> tuple[
    PublicArtifactIndex, PublicArtifactRoleMatrix
]:
    """Build the public artifact registry and its adjacent role matrix."""

    return build_public_artifact_index(), build_public_artifact_role_matrix()


def validate_public_artifact_governance() -> tuple[PublicArtifactGovernanceIssue, ...]:
    """Validate that public artifact count and roles stay explainable."""

    index, matrix = build_public_artifact_docs()
    issues: list[PublicArtifactGovernanceIssue] = []
    if len(index.entries) > index.artifact_budget:
        issues.append(
            PublicArtifactGovernanceIssue(
                code="public-artifact-count-growth",
                detail=(
                    f"public artifact count grew to {len(index.entries)} while the current governed budget is {index.artifact_budget}"
                ),
            )
        )
    if len({entry.entry_id for entry in index.entries}) != len(index.entries):
        issues.append(
            PublicArtifactGovernanceIssue(
                code="public-artifact-duplicate-entry-id",
                detail="public artifact registry contains duplicate entry identifiers",
            )
        )
    if len(matrix.rows) != len(index.entries):
        issues.append(
            PublicArtifactGovernanceIssue(
                code="public-artifact-role-matrix-row-mismatch",
                detail="public artifact role matrix row count drifted away from the public artifact registry",
            )
        )
    matrix_ids = {row.entry_id for row in matrix.rows}
    index_ids = {entry.entry_id for entry in index.entries}
    if matrix_ids != index_ids:
        issues.append(
            PublicArtifactGovernanceIssue(
                code="public-artifact-role-matrix-entry-drift",
                detail="public artifact role matrix no longer covers exactly the registry entry set",
            )
        )
    seen_roles: set[tuple[str, str]] = set()
    for entry in index.entries:
        if not (
            entry.owner_package
            and entry.audience
            and entry.question_answered
            and entry.coexistence_rationale
        ):
            issues.append(
                PublicArtifactGovernanceIssue(
                    code="public-artifact-entry-missing-context",
                    detail=f"{entry.entry_id} is missing owner, audience, question, or coexistence rationale",
                )
            )
        role_key = (
            entry.workflow_family.value if entry.workflow_family else "repository",
            entry.decision_role,
        )
        if role_key in seen_roles:
            issues.append(
                PublicArtifactGovernanceIssue(
                    code="public-artifact-role-overlap",
                    detail=(
                        f"{entry.entry_id} duplicates decision role {entry.decision_role!r} within {role_key[0]!r}"
                    ),
                )
            )
        seen_roles.add(role_key)
        if entry.workflow_family is not None and not (
            entry.stronger_neighbor or entry.weaker_neighbor
        ):
            issues.append(
                PublicArtifactGovernanceIssue(
                    code="workflow-artifact-missing-neighbor",
                    detail=f"{entry.entry_id} does not declare a stronger or weaker adjacent artifact",
                )
            )
    return tuple(issues)


def _front_matter(title: str) -> list[str]:
    return [
        "---",
        f"title: {title}",
        "audience: mixed",
        "type: explanation",
        "status: canonical",
        "owner: bijux-proteomics-docs",
        f"last_reviewed: {_LAST_REVIEWED}",
        "---",
        "",
    ]


def _render_public_artifact_index(index: PublicArtifactIndex) -> str:
    lines = _front_matter("Public Artifact Index")
    lines.extend(
        [
            "# Public Artifact Index",
            "",
            "This page is the reviewer-facing registry of shipped public artifacts. Every entry declares its owner package, intended audience, question answered, and why it still exists next to its neighboring surfaces.",
            "",
            f"- governed artifact budget: `{index.artifact_budget}`",
            f"- current artifact count: `{len(index.entries)}`",
            "",
            "| artifact id | owner package | audience | question answered | coexistence rationale |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for entry in index.entries:
        lines.append(
            f"| `{entry.entry_id}` | `{entry.owner_package}` | `{entry.audience}` | {entry.question_answered} | {entry.coexistence_rationale} |"
        )
    lines.extend(
        [
            "",
            "## Why This Exists",
            "",
            index.note,
            "",
            "The registry is intentionally stricter than a link list. If a new public artifact cannot name a distinct audience, question, and coexistence reason, it should replace an older surface instead of shipping beside it.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_public_artifact_role_matrix(matrix: PublicArtifactRoleMatrix) -> str:
    lines = _front_matter("Public Artifact Role Matrix")
    lines.extend(
        [
            "# Public Artifact Role Matrix",
            "",
            "This page records why each shipped public artifact still exists and which stronger or weaker artifact sits beside it.",
            "",
            "| artifact id | audience | decision role | question answered | weaker artifact | stronger artifact |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in matrix.rows:
        weaker = f"`{row.weaker_neighbor}`" if row.weaker_neighbor else "-"
        stronger = f"`{row.stronger_neighbor}`" if row.stronger_neighbor else "-"
        lines.append(
            f"| `{row.entry_id}` | `{row.audience}` | `{row.decision_role}` | {row.question_answered} | {weaker} | {stronger} |"
        )
    lines.extend(
        [
            "",
            matrix.note,
            "",
            "## Rule",
            "",
            "- a new public artifact must either replace a weaker artifact or justify a distinct decision role",
            "- workflow-family artifacts must declare the stronger or weaker surface beside them so adjacent trust pages do not drift into duplication",
            f"- current governed public artifact budget: `{len(matrix.rows)}`",
        ]
    )
    return "\n".join(lines) + "\n"


def run(check: bool = False) -> int:
    """Write or verify the public artifact registry and role matrix."""

    index, matrix = build_public_artifact_docs()
    expected = {
        PUBLIC_ARTIFACT_INDEX_PATH: _render_public_artifact_index(index),
        PUBLIC_ARTIFACT_ROLE_MATRIX_PATH: _render_public_artifact_role_matrix(matrix),
    }
    if check:
        return int(
            any(
                path.read_text(encoding="utf-8") != text
                for path, text in expected.items()
            )
        )
    for path, text in expected.items():
        path.write_text(text, encoding="utf-8")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))


if __name__ == "__main__":
    main()
