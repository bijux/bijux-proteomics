from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics.benchmarks.flagship_acceptance import (
    build_flagship_acceptance_dashboard,
)
from bijux_proteomics_dev.governance.package_shape.package_readme_maturity import (
    build_package_readme_maturity_report,
)
from bijux_proteomics_dev.governance.package_shape.package_reopened_completion_claims import (
    build_package_reopened_completion_claim_report,
)
from bijux_proteomics_dev.governance.package_shape.package_scorecard import (
    build_package_scorecard_report,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.release.governance.release_readiness_matrix import (
    ReleaseReadinessCategory,
    build_release_readiness_matrix,
)
from bijux_proteomics_intelligence.reviews.external_review_kits import (
    WorkflowExternalReviewKit,
    build_workflow_external_review_kit_family,
)
from bijux_proteomics_intelligence.reviews.independent_reruns import (
    WorkflowIndependentRerunDossier,
    build_workflow_independent_rerun_dossier_family,
)
from bijux_proteomics_intelligence.reviews.outsider_packets import (
    FlagshipOutsiderReviewPacket,
    build_flagship_outsider_review_packet_family,
)
from bijux_proteomics_intelligence.reviews.release_candidates import (
    build_flagship_release_candidate_bundle,
)

__all__ = [
    "HOSTILE_REVIEW_KIT_PATH",
    "WHAT_MAKES_READY_PATH",
    "WHY_NOT_READY_PATH",
    "HostileReviewFamilyEntry",
    "HostileReviewPageSet",
    "RepositoryBlockerGroup",
    "build_hostile_review_page_set",
    "run",
]


FOUNDATION_DIR = REPO_ROOT / "docs" / "01-bijux-proteomics" / "foundation"
HOSTILE_REVIEW_KIT_PATH = FOUNDATION_DIR / "hostile-review-kit.md"
WHY_NOT_READY_PATH = FOUNDATION_DIR / "why-this-repository-is-not-ready-yet.md"
WHAT_MAKES_READY_PATH = FOUNDATION_DIR / "what-would-make-this-repository-ready.md"
_LAST_REVIEWED = "2026-05-09"


@dataclass(frozen=True)
class HostileReviewFamilyEntry:
    """One flagship workflow lane inside the hostile review kit."""

    workflow_family: str
    public_release_language: str
    packet_id: str
    review_kit_path: str
    rerun_dossier_path: str
    trust_page_path: str
    challenge_question: str
    opening_order: tuple[str, ...]
    exact_claims: tuple[str, ...]
    known_limits: tuple[str, ...]


@dataclass(frozen=True)
class RepositoryBlockerGroup:
    """One grouped set of blockers that explains remaining release debt."""

    title: str
    intro: str
    issues: tuple[str, ...]


@dataclass(frozen=True)
class HostileReviewPageSet:
    """Rendered hostile-review page inputs for the repository foundation."""

    root_promise: str
    family_entries: tuple[HostileReviewFamilyEntry, ...]
    blocked_categories: tuple[ReleaseReadinessCategory, ...]
    blocker_groups: tuple[RepositoryBlockerGroup, ...]


def _packet_by_family() -> dict[str, FlagshipOutsiderReviewPacket]:
    family = build_flagship_outsider_review_packet_family()
    return {packet.workflow_family.value: packet for packet in family.packets}


def _kit_by_family() -> dict[str, WorkflowExternalReviewKit]:
    family = build_workflow_external_review_kit_family()
    return {kit.workflow_family.value: kit for kit in family.kits}


def _dossier_by_family() -> dict[str, WorkflowIndependentRerunDossier]:
    family = build_workflow_independent_rerun_dossier_family()
    return {dossier.workflow_family.value: dossier for dossier in family.dossiers}


def _family_entries() -> tuple[HostileReviewFamilyEntry, ...]:
    bundle = build_flagship_release_candidate_bundle()
    packets = _packet_by_family()
    kits = _kit_by_family()
    dossiers = _dossier_by_family()

    entries: list[HostileReviewFamilyEntry] = []
    for workflow_family in bundle.outsider_auditable_workflow_families:
        family_id = workflow_family.value
        packet = packets[family_id]
        kit = kits[family_id]
        dossier = dossiers[family_id]
        entries.append(
            HostileReviewFamilyEntry(
                workflow_family=family_id,
                public_release_language="outsider_auditable_bounded",
                packet_id=packet.packet_id,
                review_kit_path=kit.artifact_path,
                rerun_dossier_path=dossier.artifact_path,
                trust_page_path=f"docs/01-bijux-proteomics/foundation/why-trust-{family_id}.md",
                challenge_question=dossier.independence_question,
                opening_order=dossier.public_opening_order[:4],
                exact_claims=packet.exact_claims[:2],
                known_limits=tuple(
                    dict.fromkeys(
                        (*packet.known_limits[:2], *dossier.remaining_limits[:2], *kit.known_exclusions[:2])
                    )
                ),
            )
        )
    return tuple(entries)


def _root_promise() -> str:
    bundle = build_flagship_release_candidate_bundle()
    outsider = ", ".join(
        f"`{workflow_family.value}`"
        for workflow_family in bundle.outsider_auditable_workflow_families
    )
    internal = ", ".join(
        f"`{workflow_family.value}`"
        for workflow_family in bundle.internal_support_workflow_families
    )
    return (
        "The repository currently promises one bounded proteomics review system: "
        f"outsider-auditable workflow families {outsider} and internal-support-only "
        f"workflow families {internal}. No broader release language is earned."
    )


def _blocked_categories() -> tuple[ReleaseReadinessCategory, ...]:
    matrix = build_release_readiness_matrix(REPO_ROOT)
    return tuple(category for category in matrix.categories if not category.ready)


def _blocker_groups() -> tuple[RepositoryBlockerGroup, ...]:
    blocked_by_id = {
        category.category_id: category for category in build_release_readiness_matrix(REPO_ROOT).categories
    }
    acceptance_dashboard = build_flagship_acceptance_dashboard()
    scorecard = build_package_scorecard_report()
    reopened = build_package_reopened_completion_claim_report()
    maturity = build_package_readme_maturity_report()

    workflow_family_issues = [
        (
            f"`{row.workflow_family.value}` remains `{row.earned_release_language.value}` "
            f"because acceptance still fails or stays intentionally narrowed: "
            + ", ".join(row.failing_criteria or ("current bounded posture still caps broader language",))
        )
        for row in acceptance_dashboard.rows
        if not row.acceptance_passed or row.public_release_language != row.earned_release_language
    ]
    artifact_issues: list[str] = []
    for category_id in (
        "workflow-family-product-evidence",
        "black-box-rerunability",
        "benchmark-asset-quality",
        "artifact-hygiene",
    ):
        category = blocked_by_id.get(category_id)
        if category is None or category.ready:
            continue
        artifact_issues.extend(
            f"`{code}`: {detail}"
            for code, detail in zip(category.blocker_codes, category.blocker_details, strict=True)
        )
    docs_issues: list[str] = []
    docs_category = blocked_by_id.get("docs-clarity")
    if docs_category is not None and not docs_category.ready:
        docs_issues.extend(
            f"`{code}`: {detail}"
            for code, detail in zip(
                docs_category.blocker_codes,
                docs_category.blocker_details,
                strict=True,
            )
        )
    package_quality_issues = [
        f"`{entry.distribution_name}` is still not architectural-ready"
        for entry in scorecard.entries
        if not entry.architectural_ready
    ]
    package_quality_issues.extend(
        f"`{entry.distribution_name}` still carries reopened completion pressure: "
        + "; ".join(entry.reopened_reasons)
        for entry in reopened.entries
        if entry.reopened_completion_claim
    )
    package_quality_issues.extend(
        f"`{entry.distribution_name}` still claims completion while architectural-ready is false"
        for entry in maturity.entries
        if entry.completion_claims_while_not_ready
    )
    groups = (
        RepositoryBlockerGroup(
            title="Blocking artifacts",
            intro=(
                "These blockers keep the repository from claiming cleaner release posture because "
                "tracked artifacts, runtime evidence, or generated evidence are still not strong enough."
            ),
            issues=tuple(artifact_issues),
        ),
        RepositoryBlockerGroup(
            title="Workflow-family gaps",
            intro=(
                "These blockers still weaken workflow-family trust because the current public sentence "
                "would outrun rerun, acceptance, or family-specific evidence."
            ),
            issues=tuple(workflow_family_issues),
        ),
        RepositoryBlockerGroup(
            title="Package-quality gaps",
            intro=(
                "These blockers show where package maturity or cross-package release coverage still falls "
                "short of a repository-wide stronger claim."
            ),
            issues=tuple(dict.fromkeys(package_quality_issues)),
        ),
        RepositoryBlockerGroup(
            title="Docs failures",
            intro=(
                "These blockers show where public wording, routing, or scrutiny surfaces drift away from "
                "the evidence they are supposed to defend."
            ),
            issues=tuple(docs_issues),
        ),
    )
    return tuple(group for group in groups if group.issues)


def build_hostile_review_page_set() -> HostileReviewPageSet:
    """Build the hostile-review foundation pages from live repository evidence."""

    return HostileReviewPageSet(
        root_promise=_root_promise(),
        family_entries=_family_entries(),
        blocked_categories=_blocked_categories(),
        blocker_groups=_blocker_groups(),
    )


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


def _render_hostile_review_kit(pages: HostileReviewPageSet) -> str:
    bundle = build_flagship_release_candidate_bundle()
    lines = _front_matter("Hostile Review Kit")
    lines.extend(
        [
            "# Hostile Review Kit",
            "",
            pages.root_promise,
            "",
            "This page is the shortest whole-repository challenge route for a skeptical expert. It starts from the root promise, then moves directly into the strongest shipped workflow families, their paired rerun dossiers, and the current release boundary.",
            "",
            "## Open In This Order",
            "",
            "- `docs/01-bijux-proteomics/foundation/release-readiness-matrix.md`",
            "- `docs/01-bijux-proteomics/foundation/flagship-release-candidate.md`",
            "- `docs/01-bijux-proteomics/foundation/public-artifact-index.md`",
            "- `docs/01-bijux-proteomics/foundation/why-this-repository-is-not-ready-yet.md`",
            "- `docs/01-bijux-proteomics/foundation/what-would-make-this-repository-ready.md`",
            "",
            "## Root Bundle",
            "",
            f"- bundle id: `{bundle.bundle_id}`",
            "- root challenge: ask whether every public sentence stays inside the current outsider-auditable bounded family set and its published limits",
            "- first refusal: if a claim cannot be traced from the root page into one flagship family packet, its rerun dossier, and its external review kit, reject the sentence",
            "",
            "## Family Challenge Lanes",
            "",
            "| workflow family | public language | outsider packet | independent rerun dossier | external review kit | trust page |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for entry in pages.family_entries:
        lines.append(
            f"| `{entry.workflow_family}` | `{entry.public_release_language}` | `{entry.packet_id}` | `{entry.rerun_dossier_path}` | `{entry.review_kit_path}` | `{entry.trust_page_path}` |"
        )
    lines.extend(
        [
            "",
            "## How To Challenge Each Family",
            "",
        ]
    )
    for entry in pages.family_entries:
        lines.extend(
            [
                f"### `{entry.workflow_family}`",
                "",
                f"- challenge question: {entry.challenge_question}",
                f"- packet id: `{entry.packet_id}`",
                f"- opening order: {', '.join(f'`{path}`' for path in entry.opening_order)}",
                f"- exact claims: {', '.join(entry.exact_claims)}",
                f"- current limits: {', '.join(entry.known_limits)}",
                "",
            ]
        )
    lines.extend(
        [
            "## Non-Negotiable Reading Rule",
            "",
            "If the current release-readiness matrix still shows blocked categories, no reviewer should widen the root promise by interpretation alone. The blocker pages below are part of the review kit because they keep the failure modes visible before maintainers start explaining them away.",
            "",
        ]
    )
    return "\n".join(lines)


def _render_why_not_ready(pages: HostileReviewPageSet) -> str:
    lines = _front_matter("Why This Repository Is Not Ready Yet")
    lines.extend(
        [
            "# Why This Repository Is Not Ready Yet",
            "",
            "This page is generated from the current release-readiness matrix. It exists so blocked release bars stay visible in plain language and cannot be softened manually.",
            "",
            f"- blocked release bars: {len(pages.blocked_categories)}",
            "- source of truth: `packages/bijux-proteomics-dev/src/bijux_proteomics_dev/release/governance/release_readiness_matrix.py`",
            "",
        ]
    )
    for category in pages.blocked_categories:
        lines.extend(
            [
                f"## {category.title}",
                "",
                category.rationale,
                "",
                "Evidence paths:",
            ]
        )
        lines.extend(f"- `{path}`" for path in category.evidence_paths)
        lines.append("")
        lines.append("Current blockers:")
        lines.extend(
            f"- `{code}`: {detail}"
            for code, detail in zip(category.blocker_codes, category.blocker_details, strict=True)
        )
        lines.append("")
    return "\n".join(lines)


def _render_what_makes_ready(pages: HostileReviewPageSet) -> str:
    lines = _front_matter("What Would Make This Repository Ready")
    lines.extend(
        [
            "# What Would Make This Repository Ready",
            "",
            "This page is generated from the current release matrix, acceptance dashboard, and package quality reports. It names the exact remaining blockers instead of broad roadmap language.",
            "",
            "- source of truth: `packages/bijux-proteomics-dev/src/bijux_proteomics_dev/release/governance/hostile_review_pages.py`",
            "",
        ]
    )
    for group in pages.blocker_groups:
        lines.extend(
            [
                f"## {group.title}",
                "",
                group.intro,
                "",
            ]
        )
        lines.extend(f"- {issue}" for issue in group.issues)
        lines.append("")
    return "\n".join(lines)


def _rendered_pages() -> dict[Path, str]:
    pages = build_hostile_review_page_set()
    return {
        HOSTILE_REVIEW_KIT_PATH: _render_hostile_review_kit(pages),
        WHY_NOT_READY_PATH: _render_why_not_ready(pages),
        WHAT_MAKES_READY_PATH: _render_what_makes_ready(pages),
    }


def _is_up_to_date() -> bool:
    for path, expected in _rendered_pages().items():
        if not path.exists():
            return False
        if path.read_text(encoding="utf-8") != expected:
            return False
    return True


def run(check: bool = False) -> int:
    if check:
        if _is_up_to_date():
            print("hostile review foundation pages are up to date")
            return 0
        print("hostile review foundation pages are stale; regenerate them")
        return 1

    for path, text in _rendered_pages().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print("generated hostile review foundation pages")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the hostile-review foundation pages."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the hostile-review foundation pages are not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
