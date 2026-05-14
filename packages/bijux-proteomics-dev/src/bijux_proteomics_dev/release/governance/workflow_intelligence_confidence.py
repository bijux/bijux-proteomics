from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from bijux_proteomics_intelligence.judgment.benchmark_blinded_challenges import (
    build_workflow_blinded_recommendation_challenge,
)
from bijux_proteomics_intelligence.judgment.benchmark_confidence import (
    build_workflow_overconfidence_audit,
    build_workflow_underconfidence_audit,
)
from bijux_proteomics_intelligence.reviews.outsider_packets import (
    build_flagship_outsider_review_packet,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)

__all__ = [
    "WorkflowIntelligenceConfidenceIssue",
    "validate_workflow_intelligence_confidence",
]


@dataclass(frozen=True)
class WorkflowIntelligenceConfidenceIssue:
    """One unsupported use of decision-grade intelligence language."""

    code: str
    detail: str


_DECISION_GRADE_INTELLIGENCE_RE = re.compile(
    r"\bdecision-grade intelligence\b", re.IGNORECASE
)

_TRUST_PAGE_PATHS: dict[KnowledgeWorkflowFamily, str] = {
    KnowledgeWorkflowFamily.DDA: "docs/01-bijux-proteomics/foundation/why-trust-dda.md",
    KnowledgeWorkflowFamily.DIA: "docs/01-bijux-proteomics/foundation/why-trust-dia.md",
    KnowledgeWorkflowFamily.LFQ: "docs/01-bijux-proteomics/foundation/why-trust-lfq.md",
    KnowledgeWorkflowFamily.PTM: "docs/01-bijux-proteomics/foundation/why-trust-ptm.md",
    KnowledgeWorkflowFamily.TARGETED: "docs/01-bijux-proteomics/foundation/why-trust-targeted.md",
}


def _doc_contains_decision_grade_intelligence(
    repo_root: Path,
    workflow_family: KnowledgeWorkflowFamily,
) -> bool:
    doc_path = repo_root / _TRUST_PAGE_PATHS[workflow_family]
    return bool(
        _DECISION_GRADE_INTELLIGENCE_RE.search(doc_path.read_text(encoding="utf-8"))
    )


def _packet_contains_decision_grade_intelligence(
    workflow_family: KnowledgeWorkflowFamily,
) -> bool:
    packet = build_flagship_outsider_review_packet(workflow_family)
    texts = (
        *packet.exact_claims,
        *packet.comparator_context,
        *packet.known_limits,
        *packet.missing_surface_reasons,
        packet.note,
    )
    return any(_DECISION_GRADE_INTELLIGENCE_RE.search(text) for text in texts)


def validate_workflow_intelligence_confidence(
    repo_root: Path,
) -> tuple[WorkflowIntelligenceConfidenceIssue, ...]:
    """Require published challenge and confidence audits before stronger language."""

    issues: list[WorkflowIntelligenceConfidenceIssue] = []
    overconfidence_by_family = {
        entry.workflow_family: entry
        for entry in build_workflow_overconfidence_audit().entries
    }
    underconfidence_by_family = {
        entry.workflow_family: entry
        for entry in build_workflow_underconfidence_audit().entries
    }
    for workflow_family in _TRUST_PAGE_PATHS:
        if not (
            _doc_contains_decision_grade_intelligence(repo_root, workflow_family)
            or _packet_contains_decision_grade_intelligence(workflow_family)
        ):
            continue
        try:
            challenge = build_workflow_blinded_recommendation_challenge(workflow_family)
        except ValueError:
            issues.append(
                WorkflowIntelligenceConfidenceIssue(
                    code="decision-grade-intelligence-without-blinded-challenge",
                    detail=(
                        f"{workflow_family.value} uses decision-grade intelligence language "
                        "without a published blinded recommendation challenge"
                    ),
                )
            )
            continue
        overconfidence = overconfidence_by_family.get(workflow_family)
        underconfidence = underconfidence_by_family.get(workflow_family)
        if not challenge.findings:
            issues.append(
                WorkflowIntelligenceConfidenceIssue(
                    code="decision-grade-intelligence-with-empty-challenge",
                    detail=(
                        f"{workflow_family.value} uses decision-grade intelligence language "
                        "without revealed blinded challenge findings"
                    ),
                )
            )
        if overconfidence is None:
            issues.append(
                WorkflowIntelligenceConfidenceIssue(
                    code="decision-grade-intelligence-without-overconfidence-audit",
                    detail=(
                        f"{workflow_family.value} uses decision-grade intelligence language "
                        "without a published overconfidence audit row"
                    ),
                )
            )
        if underconfidence is None:
            issues.append(
                WorkflowIntelligenceConfidenceIssue(
                    code="decision-grade-intelligence-without-underconfidence-audit",
                    detail=(
                        f"{workflow_family.value} uses decision-grade intelligence language "
                        "without a published underconfidence audit row"
                    ),
                )
            )
    return tuple(issues)
