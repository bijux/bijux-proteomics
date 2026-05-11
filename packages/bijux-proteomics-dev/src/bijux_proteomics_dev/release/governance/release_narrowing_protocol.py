from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics.benchmarks.flagship_acceptance import (
    AcceptanceReleaseLanguage,
    FlagshipAcceptanceDashboardRow,
    build_flagship_acceptance_dashboard,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.release.governance.benchmark_freshness_review import (
    BenchmarkFreshnessReviewEntry,
    build_benchmark_freshness_review,
)
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
from bijux_proteomics_intelligence.reviews.workflow_authority import (
    WorkflowAuthorityRow,
    build_workflow_authority_matrix,
)

__all__ = [
    "RELEASE_NARROWING_PROTOCOL_PATH",
    "ReleaseNarrowingDecision",
    "ReleaseNarrowingProtocol",
    "ReleaseNarrowingRule",
    "build_release_narrowing_protocol",
    "run",
]


RELEASE_NARROWING_PROTOCOL_PATH = (
    REPO_ROOT
    / "docs"
    / "01-bijux-proteomics"
    / "foundation"
    / "release-narrowing-protocol.md"
)
_LAST_REVIEWED = "2026-05-09"


@dataclass(frozen=True)
class ReleaseNarrowingRule:
    """One ordered rule that can narrow workflow-family language."""

    rule_id: str
    trigger_surface: str
    narrowed_language: str
    rationale: str


@dataclass(frozen=True)
class ReleaseNarrowingDecision:
    """Current requested versus allowed language for one workflow family."""

    workflow_family: str
    requested_language: str
    allowed_language: str
    active_rule_ids: tuple[str, ...]
    active_reasons: tuple[str, ...]
    evidence_paths: tuple[str, ...]


@dataclass(frozen=True)
class ReleaseNarrowingProtocol:
    """Release language protocol driven by live evidence and blocker surfaces."""

    rules: tuple[ReleaseNarrowingRule, ...]
    decisions: tuple[ReleaseNarrowingDecision, ...]


def _language_rank(language: str) -> int:
    ranks = {
        AcceptanceReleaseLanguage.INTERNAL_SUPPORT_ONLY.value: 0,
        AcceptanceReleaseLanguage.REVIEW_GRADE_BOUNDED.value: 1,
        AcceptanceReleaseLanguage.OUTSIDER_AUDITABLE_BOUNDED.value: 2,
        "internal_support_only": 0,
        "review_grade_bounded": 1,
        "outsider_auditable_bounded": 2,
    }
    return ranks[language]


def _narrow(current_language: str, narrowed_language: str) -> str:
    if _language_rank(narrowed_language) < _language_rank(current_language):
        return narrowed_language
    return current_language


def _rules() -> tuple[ReleaseNarrowingRule, ...]:
    return (
        ReleaseNarrowingRule(
            rule_id="benchmark-asset-quality",
            trigger_surface="release-readiness matrix",
            narrowed_language=AcceptanceReleaseLanguage.REVIEW_GRADE_BOUNDED.value,
            rationale=(
                "If benchmark asset quality is blocked, family language falls back behind the "
                "current outsider-auditable sentence."
            ),
        ),
        ReleaseNarrowingRule(
            rule_id="black-box-rerunability",
            trigger_surface="release-readiness matrix plus rerun surfaces",
            narrowed_language=AcceptanceReleaseLanguage.REVIEW_GRADE_BOUNDED.value,
            rationale=(
                "If the rerun dossier or external review kit stops surviving hostile review, the "
                "family loses outsider-auditable language immediately."
            ),
        ),
        ReleaseNarrowingRule(
            rule_id="acceptance-bars",
            trigger_surface="flagship acceptance dashboard",
            narrowed_language=AcceptanceReleaseLanguage.REVIEW_GRADE_BOUNDED.value,
            rationale=(
                "If the earned acceptance language drops below the requested public language, the "
                "family inherits the weaker earned language."
            ),
        ),
        ReleaseNarrowingRule(
            rule_id="consequence-evidence",
            trigger_surface="release-readiness matrix",
            narrowed_language=AcceptanceReleaseLanguage.REVIEW_GRADE_BOUNDED.value,
            rationale=(
                "If consequence realism is blocked, recommendation-facing workflow language narrows "
                "until downstream evidence and lab consequence are coherent again."
            ),
        ),
    )


def _category_by_id() -> dict[str, ReleaseReadinessCategory]:
    matrix = build_release_readiness_matrix(REPO_ROOT)
    return {category.category_id: category for category in matrix.categories}


def _acceptance_by_family() -> dict[str, FlagshipAcceptanceDashboardRow]:
    dashboard = build_flagship_acceptance_dashboard()
    return {row.workflow_family.value: row for row in dashboard.rows}


def _authority_rows() -> tuple[WorkflowAuthorityRow, ...]:
    return build_workflow_authority_matrix().rows


def _kit_by_family() -> dict[str, WorkflowExternalReviewKit]:
    family = build_workflow_external_review_kit_family()
    return {kit.workflow_family.value: kit for kit in family.kits}


def _dossier_by_family() -> dict[str, WorkflowIndependentRerunDossier]:
    family = build_workflow_independent_rerun_dossier_family()
    return {dossier.workflow_family.value: dossier for dossier in family.dossiers}


def _freshness_by_family() -> dict[str, BenchmarkFreshnessReviewEntry]:
    return {
        entry.workflow_family.value: entry
        for entry in build_benchmark_freshness_review()
    }


def _decision(
    row: WorkflowAuthorityRow,
    acceptance_row: FlagshipAcceptanceDashboardRow,
    blocked_categories: dict[str, ReleaseReadinessCategory],
    kits: dict[str, WorkflowExternalReviewKit],
    dossiers: dict[str, WorkflowIndependentRerunDossier],
    freshness_rows: dict[str, BenchmarkFreshnessReviewEntry],
) -> ReleaseNarrowingDecision:
    requested_language = row.public_release_language
    allowed_language = requested_language
    active_rule_ids: list[str] = []
    active_reasons: list[str] = []
    evidence_paths: list[str] = []
    workflow_family = row.workflow_family.value

    benchmark_assets = blocked_categories["benchmark-asset-quality"]
    if not benchmark_assets.ready and requested_language != "internal_support_only":
        allowed_language = _narrow(
            allowed_language,
            AcceptanceReleaseLanguage.REVIEW_GRADE_BOUNDED.value,
        )
        active_rule_ids.append("benchmark-asset-quality")
        active_reasons.append(
            "benchmark asset quality is currently blocked in the release-readiness matrix"
        )
        evidence_paths.extend(benchmark_assets.evidence_paths)
    freshness = freshness_rows.get(workflow_family)
    if freshness is not None and freshness.blockers:
        allowed_language = _narrow(
            allowed_language,
            freshness.release_language_floor,
        )
        active_rule_ids.append("benchmark-asset-quality")
        active_reasons.append(
            "benchmark freshness review currently lowers the family release-language floor"
        )
        evidence_paths.extend(freshness.evidence_paths)

    rerunability = blocked_categories["black-box-rerunability"]
    dossier = dossiers.get(workflow_family)
    kit = kits.get(workflow_family)
    rerun_blocked = (
        not rerunability.ready
        or (dossier is not None and not dossier.scrutiny_ready)
        or (
            kit is not None
            and (
                not kit.ready_for_outsider_review
                or not kit.standalone_verifier_report.verified
            )
        )
    )
    if rerun_blocked and requested_language != "internal_support_only":
        allowed_language = _narrow(
            allowed_language,
            AcceptanceReleaseLanguage.REVIEW_GRADE_BOUNDED.value,
        )
        active_rule_ids.append("black-box-rerunability")
        active_reasons.append(
            "black-box rerunability is not strong enough to hold outsider-auditable language"
        )
        evidence_paths.extend(rerunability.evidence_paths)
        if dossier is not None:
            evidence_paths.append(dossier.artifact_path)
        if kit is not None:
            evidence_paths.append(kit.artifact_path)

    earned_language = acceptance_row.earned_release_language.value
    if (
        not acceptance_row.acceptance_passed
        or acceptance_row.public_release_language.value != earned_language
    ):
        allowed_language = _narrow(allowed_language, earned_language)
        active_rule_ids.append("acceptance-bars")
        active_reasons.append(
            "acceptance bars earn weaker language than the current requested sentence"
        )
        evidence_paths.extend(acceptance_row.evidence_paths)

    consequence = blocked_categories["consequence-realism"]
    if not consequence.ready and requested_language != "internal_support_only":
        allowed_language = _narrow(
            allowed_language,
            AcceptanceReleaseLanguage.REVIEW_GRADE_BOUNDED.value,
        )
        active_rule_ids.append("consequence-evidence")
        active_reasons.append(
            "consequence realism is blocked, so stronger workflow-family language must narrow"
        )
        evidence_paths.extend(consequence.evidence_paths)

    return ReleaseNarrowingDecision(
        workflow_family=workflow_family,
        requested_language=requested_language,
        allowed_language=allowed_language,
        active_rule_ids=tuple(dict.fromkeys(active_rule_ids)),
        active_reasons=tuple(dict.fromkeys(active_reasons)),
        evidence_paths=tuple(dict.fromkeys(evidence_paths)),
    )


def build_release_narrowing_protocol() -> ReleaseNarrowingProtocol:
    """Build the release narrowing protocol from live evidence surfaces."""

    blocked_categories = _category_by_id()
    acceptance_by_family = _acceptance_by_family()
    kits = _kit_by_family()
    dossiers = _dossier_by_family()
    freshness_rows = _freshness_by_family()
    decisions = tuple(
        _decision(
            row=row,
            acceptance_row=acceptance_by_family[row.workflow_family.value],
            blocked_categories=blocked_categories,
            kits=kits,
            dossiers=dossiers,
            freshness_rows=freshness_rows,
        )
        for row in _authority_rows()
    )
    return ReleaseNarrowingProtocol(rules=_rules(), decisions=decisions)


def _render_markdown(protocol: ReleaseNarrowingProtocol) -> str:
    lines = [
        "---",
        "title: Release Narrowing Protocol",
        "audience: mixed",
        "type: explanation",
        "status: canonical",
        "owner: bijux-proteomics-docs",
        f"last_reviewed: {_LAST_REVIEWED}",
        "---",
        "",
        "# Release Narrowing Protocol",
        "",
        "This page is generated from live release evidence. It records how workflow-family language narrows automatically when benchmark asset quality, black-box rerunability, acceptance bars, or consequence realism weaken.",
        "",
        "## Ordered Rules",
        "",
    ]
    for rule in protocol.rules:
        lines.extend(
            [
                f"### `{rule.rule_id}`",
                "",
                f"- trigger surface: {rule.trigger_surface}",
                f"- narrowed language: `{rule.narrowed_language}`",
                f"- rationale: {rule.rationale}",
                "",
            ]
        )
    lines.extend(
        [
            "## Current Workflow Decisions",
            "",
            "| workflow family | requested language | allowed language | active rules |",
            "| --- | --- | --- | --- |",
        ]
    )
    for decision in protocol.decisions:
        active_rules = (
            ", ".join(f"`{rule_id}`" for rule_id in decision.active_rule_ids)
            if decision.active_rule_ids
            else "_none_"
        )
        lines.append(
            f"| `{decision.workflow_family}` | `{decision.requested_language}` | `{decision.allowed_language}` | {active_rules} |"
        )
    lines.extend(
        [
            "",
            "## Evidence Behind The Current Decisions",
            "",
        ]
    )
    for decision in protocol.decisions:
        lines.extend(
            [
                f"### `{decision.workflow_family}`",
                "",
                f"- requested language: `{decision.requested_language}`",
                f"- allowed language: `{decision.allowed_language}`",
                f"- active reasons: {', '.join(decision.active_reasons) if decision.active_reasons else 'none'}",
                f"- evidence paths: {', '.join(f'`{path}`' for path in decision.evidence_paths[:6]) if decision.evidence_paths else 'none'}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(protocol: ReleaseNarrowingProtocol) -> bool:
    if not RELEASE_NARROWING_PROTOCOL_PATH.exists():
        return False
    return RELEASE_NARROWING_PROTOCOL_PATH.read_text(
        encoding="utf-8"
    ) == _render_markdown(protocol)


def run(check: bool = False) -> int:
    protocol = build_release_narrowing_protocol()
    if check:
        if _is_up_to_date(protocol):
            print("release narrowing protocol is up to date")
            return 0
        print("release narrowing protocol is stale; regenerate it")
        return 1
    RELEASE_NARROWING_PROTOCOL_PATH.parent.mkdir(parents=True, exist_ok=True)
    RELEASE_NARROWING_PROTOCOL_PATH.write_text(
        _render_markdown(protocol), encoding="utf-8"
    )
    print("generated release narrowing protocol")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the release narrowing protocol."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the release narrowing protocol is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
