# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Published acceptance sheets that keep flagship workflow trust measurable."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import ConfigDict, Field

from bijux_proteomics.benchmarks.flagship_challenge_corpora import (
    BlindedHoldoutReport,
    PerturbationReactionReport,
    build_blinded_holdout_reports,
    build_perturbation_reports,
)
from bijux_proteomics.benchmarks.flagship_public_packages import (
    list_flagship_public_benchmark_packages,
)
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.reviews.benchmarks import (
    ReviewerGroundingState,
    WorkflowBenchmarkReview,
    build_dda_benchmark_review,
    build_dia_benchmark_review,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparator_failures import (
    ComparatorClaimSupportState,
)

__all__ = [
    "AcceptanceObservedKind",
    "AcceptanceRelation",
    "AcceptanceReleaseLanguage",
    "FlagshipAcceptanceCriterion",
    "FlagshipAcceptanceSheet",
    "build_flagship_acceptance_sheet",
    "list_flagship_acceptance_sheets",
]


_ASSET_ROOT = "packages/bijux-proteomics-core/benchmark-assets/flagship-acceptance"
_SUPPORTED_FAMILIES: tuple[KnowledgeWorkflowFamily, ...] = (
    KnowledgeWorkflowFamily.DDA,
    KnowledgeWorkflowFamily.DIA,
)


class AcceptanceRelation(StrEnum):
    """How one observed metric is compared against its required boundary."""

    AT_LEAST = "at_least"
    AT_MOST = "at_most"
    EXACTLY = "exactly"
    ONE_OF = "one_of"


class AcceptanceObservedKind(StrEnum):
    """Stable shape of one observed acceptance metric."""

    INTEGER = "integer"
    FRACTION = "fraction"
    BOOLEAN = "boolean"
    STATE = "state"


class AcceptanceReleaseLanguage(StrEnum):
    """Release-language tiers used when acceptance is stronger or weaker."""

    REVIEW_GRADE_BOUNDED = "review_grade_bounded"
    OUTSIDER_AUDITABLE_BOUNDED = "outsider_auditable_bounded"
    INTERNAL_SUPPORT_ONLY = "internal_support_only"


class FlagshipAcceptanceCriterion(JsonModel):
    """One measurable acceptance bar for a flagship workflow family."""

    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(..., min_length=1)
    dimension: str = Field(..., min_length=1)
    observed_kind: AcceptanceObservedKind
    observed_value: str = Field(..., min_length=1)
    required_relation: AcceptanceRelation
    required_value: str = Field(..., min_length=1)
    passed: bool
    evidence_paths: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipAcceptanceSheet(JsonModel):
    """One published acceptance sheet for a flagship benchmark family."""

    model_config = ConfigDict(extra="forbid")

    sheet_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    benchmark_package_id: str = Field(..., min_length=1)
    public_release_language: AcceptanceReleaseLanguage
    earned_release_language: AcceptanceReleaseLanguage
    acceptance_passed: bool
    claim_ahead_of_evidence: bool
    criteria: tuple[FlagshipAcceptanceCriterion, ...] = Field(default_factory=tuple)
    blocked_claims: tuple[str, ...] = Field(default_factory=tuple)
    artifact_path: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


@lru_cache(maxsize=1)
def _reviews() -> dict[KnowledgeWorkflowFamily, WorkflowBenchmarkReview]:
    return {
        review.workflow_family: review
        for review in (
            build_dda_benchmark_review(),
            build_dia_benchmark_review(),
        )
    }


@lru_cache(maxsize=1)
def _holdouts() -> dict[str, BlindedHoldoutReport]:
    return {report.workflow_family: report for report in build_blinded_holdout_reports()}


@lru_cache(maxsize=1)
def _perturbations() -> dict[str, PerturbationReactionReport]:
    return {report.workflow_family: report for report in build_perturbation_reports()}


@lru_cache(maxsize=1)
def _package_ids() -> dict[KnowledgeWorkflowFamily, str]:
    return {
        KnowledgeWorkflowFamily(package.workflow_family): package.package_id
        for package in list_flagship_public_benchmark_packages()
        if KnowledgeWorkflowFamily(package.workflow_family) in _SUPPORTED_FAMILIES
    }


def build_flagship_acceptance_sheet(
    workflow_family: KnowledgeWorkflowFamily,
) -> FlagshipAcceptanceSheet:
    """Build one flagship acceptance sheet from shipped benchmark evidence."""

    builders = {
        KnowledgeWorkflowFamily.DDA: _build_dda_acceptance_sheet,
        KnowledgeWorkflowFamily.DIA: _build_dia_acceptance_sheet,
    }
    try:
        return builders[workflow_family]()
    except KeyError as exc:  # pragma: no cover - defensive until all families land
        raise ValueError(
            f"flagship acceptance sheet is not implemented for {workflow_family.value}"
        ) from exc


def list_flagship_acceptance_sheets() -> tuple[FlagshipAcceptanceSheet, ...]:
    """Return the currently published flagship acceptance sheets."""

    return tuple(build_flagship_acceptance_sheet(family) for family in _SUPPORTED_FAMILIES)


def _build_dda_acceptance_sheet() -> FlagshipAcceptanceSheet:
    workflow_family = KnowledgeWorkflowFamily.DDA
    review = _reviews()[workflow_family]
    perturbation = _perturbations()[workflow_family.value]
    criteria = (
        FlagshipAcceptanceCriterion(
            criterion_id="dda_search_coverage",
            dimension="search coverage",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=str(len(review.comparator_positions)),
            required_relation=AcceptanceRelation.AT_LEAST,
            required_value="2",
            passed=len(review.comparator_positions) >= 2,
            evidence_paths=(
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json",
            ),
            note="DDA trust starts only when the benchmark package names at least two explicit engine positions to keep search coverage bounded by real comparator pressure.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="dda_protein_inference_stability",
            dimension="protein inference stability",
            observed_kind=AcceptanceObservedKind.BOOLEAN,
            observed_value=str(not review.known_loss_to_established_tool).lower(),
            required_relation=AcceptanceRelation.EXACTLY,
            required_value="true",
            passed=not review.known_loss_to_established_tool,
            evidence_paths=(
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
                "packages/bijux-proteomics-core/tests/identification/test_protein_inference_benchmark_surface.py",
            ),
            note="The flagship DDA package cannot claim stable protein-level reviewability if the current benchmark review still records a known loss to an established comparator.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="dda_calibration_sanity",
            dimension="calibration sanity",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=_metric_value(perturbation, "accepted_decoy_count"),
            required_relation=AcceptanceRelation.AT_LEAST,
            required_value="1",
            passed=_metric_float(perturbation, "accepted_decoy_count") >= 1.0,
            evidence_paths=(
                perturbation.artifact_path,
                "packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora/dda_calibration_decoy_perturbation/perturbation_report.json",
            ),
            note="Calibration pressure must surface at least one accepted decoy under the adversarial DDA challenge, or the trust sheet would be hiding confidence collapse instead of measuring it.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="dda_comparator_divergence_tolerance",
            dimension="comparator divergence tolerance",
            observed_kind=AcceptanceObservedKind.STATE,
            observed_value=review.public_claim_support_state.value,
            required_relation=AcceptanceRelation.ONE_OF,
            required_value="advisory|supported",
            passed=review.public_claim_support_state in {
                ComparatorClaimSupportState.ADVISORY,
                ComparatorClaimSupportState.SUPPORTED,
            },
            evidence_paths=(
                "packages/bijux-proteomics-knowledge/tests/references/test_comparator_confrontation_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="DDA public trust is allowed only while comparator divergence stays explicitly bounded as advisory or better; refused comparator posture would mean the release language is ahead of the evidence.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="dda_review_packet_promotion",
            dimension="review-packet promotion",
            observed_kind=AcceptanceObservedKind.STATE,
            observed_value=f"{review.reviewer_grounding_state.value}:{review.ready_for_release_review}".lower(),
            required_relation=AcceptanceRelation.ONE_OF,
            required_value="review_grade:true|decision_grade:true",
            passed=review.ready_for_release_review
            and review.reviewer_grounding_state
            in {ReviewerGroundingState.REVIEW_GRADE, ReviewerGroundingState.DECISION_GRADE},
            evidence_paths=(
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_outsider_packets_surface.py",
            ),
            note="DDA trust cannot be promoted into outsider review unless the benchmark packet is both releasable and grounded above thin benchmark prose.",
        ),
    )
    return _sheet_from_criteria(
        workflow_family=workflow_family,
        review=review,
        criteria=criteria,
        blocked_claims=(
            "do not promote DDA to full engine-rerun parity",
            "do not hide cross-engine protein rollup drift behind a single imported export",
        ),
    )


def _build_dia_acceptance_sheet() -> FlagshipAcceptanceSheet:
    workflow_family = KnowledgeWorkflowFamily.DIA
    review = _reviews()[workflow_family]
    holdout = _holdouts()[workflow_family.value]
    criteria = (
        FlagshipAcceptanceCriterion(
            criterion_id="dia_library_dependence",
            dimension="library dependence",
            observed_kind=AcceptanceObservedKind.FRACTION,
            observed_value=_claim_metric(review, "library_conditioned_import_tier", "observed_fraction"),
            required_relation=AcceptanceRelation.AT_LEAST,
            required_value="0.67",
            passed=_claim_metric_float(review, "library_conditioned_import_tier", "observed_fraction") >= 0.67,
            evidence_paths=(
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/package_manifest.json",
            ),
            note="The current DIA package is only trusted at bounded outsider scope once at least two thirds of library-conditioned peptide evidence remains visible in the shipped review packet.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="dia_peptide_evidence_coverage",
            dimension="peptide evidence coverage",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=_claim_metric(review, "protein_group_reviewability", "protein_groups"),
            required_relation=AcceptanceRelation.AT_LEAST,
            required_value="4",
            passed=_claim_metric_float(review, "protein_group_reviewability", "protein_groups") >= 4.0,
            evidence_paths=(
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
                "packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py",
            ),
            note="The DIA acceptance bar keeps peptide-to-protein evidence coverage anchored to a non-trivial tracked protein-group surface instead of letting library import alone stand in for interpretable biology.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="dia_protein_evidence_stability",
            dimension="protein evidence stability",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=str(
                sum(
                    finding.revealed_outcome.value == "hit"
                    for finding in holdout.findings
                )
            ),
            required_relation=AcceptanceRelation.AT_LEAST,
            required_value="1",
            passed=any(finding.revealed_outcome.value == "hit" for finding in holdout.findings),
            evidence_paths=(
                holdout.artifact_path,
                "packages/bijux-proteomics-core/tests/benchmarks/test_flagship_challenge_corpora_surface.py",
            ),
            note="DIA family trust needs at least one blinded holdout claim that survives reveal, or protein-level authority would rest only on one convenient imported package.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="dia_quantitative_coherence",
            dimension="quantitative coherence",
            observed_kind=AcceptanceObservedKind.FRACTION,
            observed_value=_claim_metric(review, "biological_interpretation_tier", "absent_expected_fraction"),
            required_relation=AcceptanceRelation.AT_MOST,
            required_value="0.33",
            passed=_claim_metric_float(review, "biological_interpretation_tier", "absent_expected_fraction") <= 0.33,
            evidence_paths=(
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
                "packages/bijux-proteomics-core/tests/dia/test_scientific_support_surface.py",
            ),
            note="DIA biological interpretation stays within bounded outsider trust only while absent-expected peptide pressure remains no worse than the current one-third benchmark limit.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="dia_review_packet_promotion",
            dimension="review-packet promotion",
            observed_kind=AcceptanceObservedKind.STATE,
            observed_value=f"{review.reviewer_grounding_state.value}:{review.ready_for_release_review}".lower(),
            required_relation=AcceptanceRelation.ONE_OF,
            required_value="review_grade:true|decision_grade:true",
            passed=review.ready_for_release_review
            and review.reviewer_grounding_state
            in {ReviewerGroundingState.REVIEW_GRADE, ReviewerGroundingState.DECISION_GRADE},
            evidence_paths=(
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_outsider_packets_surface.py",
            ),
            note="DIA trust can only regenerate as outsider-auditable when the review packet is both releasable and still grounded at review-grade or stronger after its library and mobility caveats are carried through.",
        ),
    )
    return _sheet_from_criteria(
        workflow_family=workflow_family,
        review=review,
        criteria=criteria,
        blocked_claims=(
            "do not promote DIA to direct vendor-library parity",
            "do not hide ion-mobility absence behind a clean import summary",
        ),
    )


def _sheet_from_criteria(
    *,
    workflow_family: KnowledgeWorkflowFamily,
    review: WorkflowBenchmarkReview,
    criteria: tuple[FlagshipAcceptanceCriterion, ...],
    blocked_claims: tuple[str, ...],
) -> FlagshipAcceptanceSheet:
    acceptance_passed = all(criterion.passed for criterion in criteria)
    public_release_language = _public_release_language(workflow_family)
    earned_release_language = _earned_release_language(
        workflow_family=workflow_family,
        acceptance_passed=acceptance_passed,
    )
    return FlagshipAcceptanceSheet(
        sheet_id=f"flagship-acceptance:{workflow_family.value}",
        workflow_family=workflow_family,
        benchmark_id=review.benchmark_id,
        benchmark_package_id=_package_ids()[workflow_family],
        public_release_language=public_release_language,
        earned_release_language=earned_release_language,
        acceptance_passed=acceptance_passed,
        claim_ahead_of_evidence=_release_rank(public_release_language)
        > _release_rank(earned_release_language),
        criteria=criteria,
        blocked_claims=blocked_claims,
        artifact_path=f"{_ASSET_ROOT}/{workflow_family.value}_acceptance_sheet.json",
        note=(
            "This sheet keeps flagship workflow trust tied to measurable bars on the shipped benchmark package, challenge corpus, and review packet."
        ),
    )


def _public_release_language(
    workflow_family: KnowledgeWorkflowFamily,
) -> AcceptanceReleaseLanguage:
    return (
        AcceptanceReleaseLanguage.INTERNAL_SUPPORT_ONLY
        if workflow_family is KnowledgeWorkflowFamily.MULTIPLEX
        else AcceptanceReleaseLanguage.OUTSIDER_AUDITABLE_BOUNDED
    )


def _earned_release_language(
    *,
    workflow_family: KnowledgeWorkflowFamily,
    acceptance_passed: bool,
) -> AcceptanceReleaseLanguage:
    if workflow_family is KnowledgeWorkflowFamily.MULTIPLEX:
        return AcceptanceReleaseLanguage.INTERNAL_SUPPORT_ONLY
    if acceptance_passed:
        return AcceptanceReleaseLanguage.OUTSIDER_AUDITABLE_BOUNDED
    return AcceptanceReleaseLanguage.REVIEW_GRADE_BOUNDED


def _release_rank(language: AcceptanceReleaseLanguage) -> int:
    ranks = {
        AcceptanceReleaseLanguage.REVIEW_GRADE_BOUNDED: 0,
        AcceptanceReleaseLanguage.INTERNAL_SUPPORT_ONLY: 1,
        AcceptanceReleaseLanguage.OUTSIDER_AUDITABLE_BOUNDED: 2,
    }
    return ranks[language]


def _claim_metric(
    review: WorkflowBenchmarkReview,
    claim_id: str,
    metric_key: str,
) -> str:
    claim = next(claim for claim in review.claim_summaries if claim.claim_id == claim_id)
    for reference in claim.evidence_refs:
        if reference.startswith(f"{metric_key}="):
            return reference.split("=", 1)[1]
    raise ValueError(f"missing metric {metric_key!r} in claim {claim_id!r}")


def _claim_metric_float(
    review: WorkflowBenchmarkReview,
    claim_id: str,
    metric_key: str,
) -> float:
    return float(_claim_metric(review, claim_id, metric_key))


def _metric_value(report: PerturbationReactionReport, metric_id: str) -> str:
    metric = next(item for item in report.metric_deltas if item.metric_id == metric_id)
    return str(int(metric.perturbed_value))


def _metric_float(report: PerturbationReactionReport, metric_id: str) -> float:
    metric = next(item for item in report.metric_deltas if item.metric_id == metric_id)
    return float(metric.perturbed_value)
