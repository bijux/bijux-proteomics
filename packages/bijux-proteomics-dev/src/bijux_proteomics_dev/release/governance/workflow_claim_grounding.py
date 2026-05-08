from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from bijux_proteomics_intelligence.reviews.outsider_packets import (
    build_flagship_outsider_review_packet,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.claim_grounding import (
    ClaimNarrativeSurface,
    ScientificClaimSeverity,
    build_workflow_claim_citation_table,
    build_workflow_unsupported_claim_ledger,
)

__all__ = [
    "WorkflowClaimGroundingIssue",
    "validate_workflow_claim_grounding",
]


@dataclass(frozen=True)
class WorkflowClaimGroundingIssue:
    """One mismatch between public wording and the grounded claim tables."""

    code: str
    detail: str


_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_text(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text.strip()).lower()


def _doc_contains_claim(repo_root: Path, doc_path: str, claim_text: str) -> bool:
    text = (repo_root / doc_path).read_text(encoding="utf-8")
    return _normalize_text(claim_text) in _normalize_text(text)


def _packet_claim_texts(workflow_family: KnowledgeWorkflowFamily) -> set[str]:
    packet = build_flagship_outsider_review_packet(workflow_family)
    return {
        *packet.exact_claims,
        *packet.comparator_context,
        *packet.known_limits,
        *packet.missing_surface_reasons,
        packet.note,
    }


def _violates_threshold(
    severity: ScientificClaimSeverity,
    threshold: tuple[ScientificClaimSeverity, ...],
) -> bool:
    return severity in set(threshold)


def validate_workflow_claim_grounding(
    repo_root: Path,
) -> tuple[WorkflowClaimGroundingIssue, ...]:
    """Validate trust-page and outsider-packet grounding against shipped tables."""

    issues: list[WorkflowClaimGroundingIssue] = []
    for workflow_family in KnowledgeWorkflowFamily:
        table = build_workflow_claim_citation_table(workflow_family)
        for entry in table.entries:
            if entry.surface in {
                ClaimNarrativeSurface.TRUST_PAGE,
                ClaimNarrativeSurface.AUTHORITY_BOUNDARY,
            }:
                if not _doc_contains_claim(
                    repo_root, entry.surface_locator, entry.claim_text
                ):
                    issues.append(
                        WorkflowClaimGroundingIssue(
                            code="trust-surface-claim-missing",
                            detail=(
                                f"{workflow_family.value} trust surface is missing the "
                                f"grounded claim text: {entry.claim_text}"
                            ),
                        )
                    )
            elif entry.surface is ClaimNarrativeSurface.OUTSIDER_PACKET:
                packet_claims = _packet_claim_texts(workflow_family)
                if entry.claim_text not in packet_claims:
                    issues.append(
                        WorkflowClaimGroundingIssue(
                            code="outsider-packet-claim-missing",
                            detail=(
                                f"{workflow_family.value} outsider packet is missing the "
                                f"grounded claim text: {entry.claim_text}"
                            ),
                        )
                    )
        ledger = build_workflow_unsupported_claim_ledger(workflow_family)
        for ledger_entry in ledger.entries:
            if _violates_threshold(
                ledger_entry.scientific_severity,
                ledger.threshold_blocking_severities,
            ):
                issues.append(
                    WorkflowClaimGroundingIssue(
                        code="unsupported-claim-threshold-exceeded",
                        detail=(
                            f"{workflow_family.value} still has "
                            f"{ledger_entry.scientific_severity.value} unsupported "
                            f"claim language: {ledger_entry.claim_text}"
                        ),
                    )
                )
    return tuple(issues)
