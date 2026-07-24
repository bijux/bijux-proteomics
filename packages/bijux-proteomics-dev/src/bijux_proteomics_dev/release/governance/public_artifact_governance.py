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
_LAST_REVIEWED = "2026-07-21"


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
        "type: reference",
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
            "Public claims in Bijux Proteomics are backed by different artifact classes. Each artifact has an owner package, a review question it can answer, and a boundary beyond which it provides no authority. Review starts with the claim, opens the strongest relevant evidence, and follows its identifiers back to the underlying source and run records.",
            "",
            "## Evidence Flow",
            "",
            "```mermaid",
            "flowchart LR",
            '    lineage["Core lineage + benchmark manifest"] --> run["Runtime run bundle"]',
            '    run --> grounding["Knowledge evidence bundle"]',
            '    grounding --> decision["Intelligence recommendation record"]',
            '    decision --> lab["Lab readiness or outcome dossier"]',
            '    lab --> release["release candidate evidence"]',
            "```",
            "",
            "## Governed Artifact Registry",
            "",
            f"The registry contains `{len(index.entries)}` artifacts under a governed budget of `{index.artifact_budget}`.",
            "",
            "| Artifact id | Owner package | Audience | Question answered | Evidence locator |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for entry in index.entries:
        lines.append(
            f"| `{entry.entry_id}` | `{entry.owner_package}` | `{entry.audience}` | {entry.question_answered} | `{entry.locator}` |"
        )
    lines.extend(
        [
            "",
            "## Open Evidence In Order",
            "",
            "1. Identify the exact workflow family and proposed public sentence.",
            "2. Open its benchmark manifest, companion package, and Core lineage.",
            "3. Verify Runtime entrypoints, environment, run identity, artifacts, and comparison policy.",
            "4. Inspect support, contradiction, and unresolved context in Knowledge.",
            "5. Inspect recommendation sensitivity, downgrade, refusal, and human-review state.",
            "6. Inspect laboratory readiness, burden, controls, and observed outcome.",
            "7. Compare the surviving sentence with the current release claim limit.",
            "",
            "An [independent rerun dossier](independent-rerun-dossiers.md) gives the runtime and comparison opening path. An [external review kit](external-review-kits.md) adds scientific, decision, and consequence pressure without requiring private maintainer context.",
            "",
            "## Artifact Coexistence",
            "",
            index.note,
            "",
            "The coexistence rationale must identify the distinct review question or authority layer preserved by each artifact. A benchmark manifest defines scientific inputs; a run bundle records execution. A generated summary provides navigation; its source records carry the proof.",
            "",
            "Coexistence is not justified when two pages repeat the same conclusion, a generated view has no freshness check, or readers can mistake a weaker artifact for the stronger authority. In those cases, consolidate the duplicate or make the authority difference explicit.",
            "",
            "Use the [Public Artifact Role Matrix](public-artifact-role-matrix.md) to compare stronger and weaker neighbors for every governed artifact.",
            "",
            "## Integrity Rules",
            "",
            "- every artifact identity resolves to an owner and versioned source;",
            "- generated artifacts name their generator and freshness check;",
            "- summaries retain identifiers for the records they omit;",
            "- local run products remain under `artifacts/` until explicitly promoted;",
            "- a stale, missing, contradicted, or refused artifact narrows the public claim;",
            "- artifact count never substitutes for independent challenge value.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_public_artifact_role_matrix(matrix: PublicArtifactRoleMatrix) -> str:
    lines = _front_matter("Public Artifact Role Matrix")
    lines.extend(
        [
            "# Public Artifact Role Matrix",
            "",
            "Artifacts that discuss the same workflow can carry different authority. This matrix distinguishes navigation from proof, primary evidence from derived views, and a bounded positive result from challenge evidence that can overturn it.",
            "",
            "A weaker artifact answers a narrower question or derives from evidence elsewhere. A stronger artifact is the more direct or demanding authority for the claim under review.",
            "",
            "## Authority Order",
            "",
            "```mermaid",
            "flowchart LR",
            '    guide["guide or index"] --> summary["generated summary"]',
            '    summary --> record["versioned evidence record"]',
            '    record --> challenge["independent challenge result"]',
            '    challenge --> refusal["release acceptance or refusal"]',
            "```",
            "",
            "Authority is question-specific. A benchmark manifest is stronger than a prose summary for input identity, while a Runtime run bundle is stronger for what executed. Neither can answer the other question by itself.",
            "",
            "## Artifact Roles",
            "",
            "| Artifact id | Audience | Decision role | Question answered | Weaker artifact | Stronger artifact |",
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
            "## Coexistence Rules",
            "",
            matrix.note,
            "",
            "Two public artifacts may coexist when:",
            "",
            "- they have different owner packages or authority questions;",
            "- one is a stable derived view with a freshness check and resolvable source;",
            "- one preserves historical or compatibility evidence required for replay;",
            "- one applies independent pressure absent from the primary artifact.",
            "",
            "Consolidate or remove an artifact when:",
            "",
            "- it repeats another artifact's conclusion without adding evidence or a reader route;",
            "- its owner, generator, source identity, or freshness check is unknown;",
            "- readers can mistake it for a stronger authority surface;",
            "- no compatibility contract requires its continued publication.",
            "",
            "When artifacts disagree, open their source identities, owner contracts, and validators. Narrow the claim until the conflict is resolved; the preferred conclusion does not select the winner.",
            "",
            f"The current governed public artifact budget is `{len(matrix.rows)}`.",
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
