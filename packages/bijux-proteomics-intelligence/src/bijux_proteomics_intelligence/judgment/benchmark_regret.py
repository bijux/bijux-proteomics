# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Recommendation regret ledger over blinded and counterfactual benchmark proof."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.judgment.benchmark_blinded_challenges import (
    BlindedRecommendationRevealState,
    list_workflow_blinded_recommendation_challenges,
)
from bijux_proteomics_intelligence.judgment.benchmark_confidence import (
    build_workflow_overconfidence_audit,
)
from bijux_proteomics_intelligence.judgment.benchmark_counterfactuals import (
    build_counterfactual_recommendation_report,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)

__all__ = [
    "BenchmarkRecommendationRegretEntry",
    "BenchmarkRecommendationRegretKind",
    "BenchmarkRecommendationRegretLedger",
    "build_benchmark_recommendation_regret_ledger",
]


class BenchmarkRecommendationRegretKind(StrEnum):
    """Stable regret patterns that surfaced after hidden evidence was revealed."""

    HIDDEN_REVEAL_MISS = "hidden_reveal_miss"
    HIDDEN_REVEAL_OVERCONFIDENCE = "hidden_reveal_overconfidence"
    COUNTERFACTUAL_DEPENDENCY = "counterfactual_dependency"


class BenchmarkRecommendationRegretEntry(JsonModel):
    """One family-level recommendation pattern maintainers would undo."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    regret_kind: BenchmarkRecommendationRegretKind
    summary: str = Field(..., min_length=1)
    why_it_is_regretted: str = Field(..., min_length=1)
    change_needed: str = Field(..., min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkRecommendationRegretLedger(JsonModel):
    """Cross-family ledger of recommendation patterns worth undoing."""

    model_config = ConfigDict(extra="forbid")

    ledger_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[BenchmarkRecommendationRegretEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


def build_benchmark_recommendation_regret_ledger() -> (
    BenchmarkRecommendationRegretLedger
):
    """Build the ledger of recommendation patterns maintainers would undo."""

    overconfidence_by_family = {
        entry.workflow_family: entry
        for entry in build_workflow_overconfidence_audit().entries
    }
    counterfactuals_by_family = {
        entry.workflow_family: entry
        for entry in build_counterfactual_recommendation_report().entries
    }
    entries: list[BenchmarkRecommendationRegretEntry] = []
    for report in list_workflow_blinded_recommendation_challenges():
        misses = tuple(
            finding
            for finding in report.findings
            if finding.revealed_outcome is BlindedRecommendationRevealState.MISS
        )
        if misses:
            entries.append(
                BenchmarkRecommendationRegretEntry(
                    workflow_family=report.workflow_family,
                    regret_kind=BenchmarkRecommendationRegretKind.HIDDEN_REVEAL_MISS,
                    summary=(
                        "Current recommendation posture still lets a follow-up survive until hidden evidence forces outright refusal."
                    ),
                    why_it_is_regretted=(
                        "The hidden reveal produced a miss, which means the maintainers would most want to undo the recommendation pattern that let this family stay in motion."
                    ),
                    change_needed=(
                        "Move this family to earlier refusal when interference, carryover, or comparable hidden execution debt is already visible in the open evidence."
                    ),
                    evidence_refs=tuple(finding.finding_id for finding in misses),
                )
            )
            continue
        overconfident = tuple(
            finding
            for finding in report.findings
            if finding.revealed_outcome
            is BlindedRecommendationRevealState.OVERCONFIDENT
        )
        if overconfident:
            entries.append(
                BenchmarkRecommendationRegretEntry(
                    workflow_family=report.workflow_family,
                    regret_kind=(
                        BenchmarkRecommendationRegretKind.HIDDEN_REVEAL_OVERCONFIDENCE
                    ),
                    summary=(
                        "Current recommendation posture still lets one attractive family claim sound stronger than the paired-package reveal earns."
                    ),
                    why_it_is_regretted=(
                        "The hidden reveal exposed an overconfidence pattern that the maintainers would most want to retract after seeing the withheld evidence."
                    ),
                    change_needed=(
                        "Keep this family recommendation bounded to the surviving claim surface and demote the overconfident claim class until stronger companion-package proof exists."
                    ),
                    evidence_refs=tuple(
                        finding.finding_id for finding in overconfident
                    ),
                )
            )
            continue
        counterfactual = counterfactuals_by_family[report.workflow_family]
        overconfidence = overconfidence_by_family[report.workflow_family]
        entries.append(
            BenchmarkRecommendationRegretEntry(
                workflow_family=report.workflow_family,
                regret_kind=BenchmarkRecommendationRegretKind.COUNTERFACTUAL_DEPENDENCY,
                summary=(
                    "Current recommendation posture still depends on evidence axes that collapse immediately under counterfactual removal."
                ),
                why_it_is_regretted=(
                    "No blinded miss or overconfidence surfaced first, but the current family still depends on comparator, literature, or burden assumptions that remain too fragile."
                ),
                change_needed=(
                    "Reduce decision language until the family no longer collapses so easily under counterfactual evidence removal."
                ),
                evidence_refs=(
                    *overconfidence.overconfidence_finding_ids,
                    counterfactual.comparator_note,
                    counterfactual.literature_note,
                    counterfactual.lab_burden_note,
                ),
            )
        )
    return BenchmarkRecommendationRegretLedger(
        ledger_id="flagship-benchmark-recommendation-regret",
        artifact_path="artifacts/intelligence/benchmark-decisions/recommendation_regret_ledger.json",
        entries=tuple(entries),
        note=(
            "This ledger records which benchmark-backed recommendation patterns the "
            "maintainers would most want to undo after hidden or withheld evidence is "
            "revealed."
        ),
    )
