# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Published acceptance sheets that keep flagship workflow trust measurable."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from functools import lru_cache

from pydantic import ConfigDict, Field

from bijux_proteomics.benchmarks.flagship.challenge_corpora import (
    BlindedHoldoutReport,
    PerturbationReactionReport,
    build_blinded_holdout_reports,
    build_perturbation_reports,
)
from bijux_proteomics.benchmarks.flagship.public_packages import (
    list_flagship_public_benchmark_packages,
)
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.reviews.benchmarks import (
    ReviewerGroundingState,
    WorkflowBenchmarkReview,
    build_dda_benchmark_review,
    build_dia_benchmark_review,
    build_lfq_benchmark_review,
    build_multiplex_benchmark_review,
    build_ptm_benchmark_review,
    build_targeted_benchmark_review,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparator_failures import (
    ComparatorClaimSupportState,
)
from bijux_proteomics_knowledge.references.workflows.scientific_thresholds import (
    WorkflowThresholdEvidenceReport,
)

__all__ = [
    "AcceptanceObservedKind",
    "AcceptanceRelation",
    "AcceptanceReleaseLanguage",
    "AcceptanceThresholdChangeDirection",
    "FlagshipAcceptanceDashboard",
    "FlagshipAcceptanceDashboardRow",
    "FlagshipAcceptanceCriterion",
    "FlagshipAcceptanceHistoryEntry",
    "FlagshipAcceptanceHistoryLedger",
    "FlagshipAcceptanceRationaleDossier",
    "FlagshipAcceptanceRationaleEntry",
    "FlagshipAcceptanceSheet",
    "build_flagship_acceptance_dashboard",
    "build_flagship_acceptance_history_ledger",
    "build_flagship_acceptance_rationale_dossier",
    "build_flagship_acceptance_sheet",
    "list_flagship_acceptance_sheets",
]


_ASSET_ROOT = "packages/bijux-proteomics-core/benchmark-assets/flagship-acceptance"
_SUPPORTED_FAMILIES: tuple[KnowledgeWorkflowFamily, ...] = (
    KnowledgeWorkflowFamily.DDA,
    KnowledgeWorkflowFamily.DIA,
    KnowledgeWorkflowFamily.LFQ,
    KnowledgeWorkflowFamily.MULTIPLEX,
    KnowledgeWorkflowFamily.PTM,
    KnowledgeWorkflowFamily.TARGETED,
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


class AcceptanceThresholdChangeDirection(StrEnum):
    """How one threshold moved relative to the previously published bar."""

    INITIAL_PUBLISHED = "initial_published"
    STRICTER = "stricter"
    LOOSER = "looser"
    UNCHANGED = "unchanged"


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


class FlagshipAcceptanceDashboardRow(JsonModel):
    """One cross-family dashboard row over flagship acceptance posture."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_package_id: str = Field(..., min_length=1)
    public_release_language: AcceptanceReleaseLanguage
    earned_release_language: AcceptanceReleaseLanguage
    acceptance_passed: bool
    claim_ahead_of_evidence: bool
    failing_criteria: tuple[str, ...] = Field(default_factory=tuple)
    evidence_paths: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipAcceptanceDashboard(JsonModel):
    """Cross-family dashboard for current versus required flagship trust bars."""

    model_config = ConfigDict(extra="forbid")

    dashboard_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    rows: tuple[FlagshipAcceptanceDashboardRow, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipAcceptanceHistoryEntry(JsonModel):
    """One threshold record inside the flagship benchmark history ledger."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    criterion_id: str = Field(..., min_length=1)
    recorded_on: date
    required_value: str = Field(..., min_length=1)
    observed_value: str = Field(..., min_length=1)
    change_direction: AcceptanceThresholdChangeDirection
    note: str = Field(..., min_length=1)


class FlagshipAcceptanceHistoryLedger(JsonModel):
    """Ledger that prevents flagship acceptance thresholds from drifting quietly."""

    model_config = ConfigDict(extra="forbid")

    ledger_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[FlagshipAcceptanceHistoryEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipAcceptanceRationaleEntry(JsonModel):
    """One scientific rationale behind a published flagship acceptance bar."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    criterion_id: str = Field(..., min_length=1)
    threshold_summary: str = Field(..., min_length=1)
    comparator_basis: str = Field(..., min_length=1)
    literature_basis: str = Field(..., min_length=1)
    benchmark_difficulty_basis: str = Field(..., min_length=1)
    lab_consequence_basis: str = Field(..., min_length=1)
    evidence_paths: tuple[str, ...] = Field(default_factory=tuple)


class FlagshipAcceptanceRationaleDossier(JsonModel):
    """Why each published flagship acceptance threshold exists at all."""

    model_config = ConfigDict(extra="forbid")

    dossier_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[FlagshipAcceptanceRationaleEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


@lru_cache(maxsize=1)
def _reviews() -> dict[KnowledgeWorkflowFamily, WorkflowBenchmarkReview]:
    return {
        review.workflow_family: review
        for review in (
            build_dda_benchmark_review(),
            build_dia_benchmark_review(),
            build_lfq_benchmark_review(),
            build_multiplex_benchmark_review(),
            build_ptm_benchmark_review(),
            build_targeted_benchmark_review(),
        )
    }


@lru_cache(maxsize=1)
def _holdouts() -> dict[str, BlindedHoldoutReport]:
    return {
        report.workflow_family: report for report in build_blinded_holdout_reports()
    }


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
        KnowledgeWorkflowFamily.LFQ: _build_lfq_acceptance_sheet,
        KnowledgeWorkflowFamily.MULTIPLEX: _build_multiplex_acceptance_sheet,
        KnowledgeWorkflowFamily.PTM: _build_ptm_acceptance_sheet,
        KnowledgeWorkflowFamily.TARGETED: _build_targeted_acceptance_sheet,
    }
    try:
        return builders[workflow_family]()
    except KeyError as exc:  # pragma: no cover - defensive until all families land
        raise ValueError(
            f"flagship acceptance sheet is not implemented for {workflow_family.value}"
        ) from exc


def list_flagship_acceptance_sheets() -> tuple[FlagshipAcceptanceSheet, ...]:
    """Return the currently published flagship acceptance sheets."""

    return tuple(
        build_flagship_acceptance_sheet(family) for family in _SUPPORTED_FAMILIES
    )


def build_flagship_acceptance_dashboard() -> FlagshipAcceptanceDashboard:
    """Build the cross-family dashboard for flagship trust bars."""

    rows = []
    for sheet in list_flagship_acceptance_sheets():
        failing = tuple(
            criterion.criterion_id
            for criterion in sheet.criteria
            if not criterion.passed
        )
        rows.append(
            FlagshipAcceptanceDashboardRow(
                workflow_family=sheet.workflow_family,
                benchmark_package_id=sheet.benchmark_package_id,
                public_release_language=sheet.public_release_language,
                earned_release_language=sheet.earned_release_language,
                acceptance_passed=sheet.acceptance_passed,
                claim_ahead_of_evidence=sheet.claim_ahead_of_evidence,
                failing_criteria=failing,
                evidence_paths=(sheet.artifact_path,),
                note=(
                    "the current release claim is ahead of the benchmark evidence"
                    if sheet.claim_ahead_of_evidence
                    else "the current release language is still inside the measured flagship acceptance bar"
                ),
            )
        )
    return FlagshipAcceptanceDashboard(
        dashboard_id="flagship-acceptance-dashboard",
        artifact_path=f"{_ASSET_ROOT}/acceptance_dashboard.json",
        rows=tuple(rows),
        note=(
            "This dashboard compares the current public release language against the earned benchmark acceptance posture for every flagship workflow family."
        ),
    )


def build_flagship_acceptance_history_ledger() -> FlagshipAcceptanceHistoryLedger:
    """Record the currently published flagship thresholds and their direction."""

    entries = []
    today = date.today()
    for sheet in list_flagship_acceptance_sheets():
        for criterion in sheet.criteria:
            entries.append(
                FlagshipAcceptanceHistoryEntry(
                    workflow_family=sheet.workflow_family,
                    criterion_id=criterion.criterion_id,
                    recorded_on=today,
                    required_value=criterion.required_value,
                    observed_value=criterion.observed_value,
                    change_direction=AcceptanceThresholdChangeDirection.INITIAL_PUBLISHED,
                    note=(
                        "initial publication of the flagship acceptance bar; future edits must declare whether the threshold became stricter or looser"
                    ),
                )
            )
    return FlagshipAcceptanceHistoryLedger(
        ledger_id="flagship-benchmark-history-ledger",
        artifact_path=f"{_ASSET_ROOT}/benchmark_history_ledger.json",
        entries=tuple(entries),
        note=(
            "The initial ledger records the first published threshold set so later edits cannot quietly move acceptance bars in a self-serving direction."
        ),
    )


def build_flagship_acceptance_rationale_dossier() -> FlagshipAcceptanceRationaleDossier:
    """Explain why each published acceptance bar exists scientifically."""

    threshold_reports = {
        family: _reviews()[family].scientific_release_packet.threshold_evidence
        for family in _SUPPORTED_FAMILIES
    }
    perturbations = _perturbations()
    holdouts = _holdouts()
    entries: list[FlagshipAcceptanceRationaleEntry] = []
    for sheet in list_flagship_acceptance_sheets():
        threshold_report = threshold_reports[sheet.workflow_family]
        threshold_ids = tuple(entry.threshold_id for entry in threshold_report.entries)
        challenge_refs: tuple[str, ...] = ()
        if sheet.workflow_family.value in holdouts:
            challenge_refs += (holdouts[sheet.workflow_family.value].artifact_path,)
        if sheet.workflow_family.value in perturbations:
            challenge_refs += (
                perturbations[sheet.workflow_family.value].artifact_path,
            )
        for criterion in sheet.criteria:
            entries.append(
                FlagshipAcceptanceRationaleEntry(
                    workflow_family=sheet.workflow_family,
                    criterion_id=criterion.criterion_id,
                    threshold_summary=(
                        f"{criterion.dimension} is accepted only when {criterion.required_relation.value} {criterion.required_value}"
                    ),
                    comparator_basis=(
                        f"{len(_reviews()[sheet.workflow_family].comparator_positions)} comparator positions and "
                        f"{_reviews()[sheet.workflow_family].public_claim_support_state.value} public comparator support keep the threshold tied to shipped external pressure."
                    ),
                    literature_basis=_literature_basis(
                        threshold_report=threshold_report,
                        threshold_ids=threshold_ids,
                    ),
                    benchmark_difficulty_basis=(
                        "challenge evidence is part of this threshold because the flagship package already ships blinded holdout or perturbation pressure: "
                        + ", ".join(challenge_refs)
                        if challenge_refs
                        else "the threshold is anchored only to the current flagship public package because no separate challenge root exists for this family yet"
                    ),
                    lab_consequence_basis=(
                        "minimum controls that remain visible in the benchmark review: "
                        + ", ".join(
                            _reviews()[sheet.workflow_family].minimum_controls_required
                        )
                    ),
                    evidence_paths=(criterion.evidence_paths + challenge_refs),
                )
            )
    return FlagshipAcceptanceRationaleDossier(
        dossier_id="flagship-acceptance-rationale-dossier",
        artifact_path=f"{_ASSET_ROOT}/acceptance_rationale_dossier.json",
        entries=tuple(entries),
        note=(
            "The rationale dossier ties every flagship acceptance bar back to shipped comparator pressure, literature-backed threshold anchors, benchmark difficulty, or lab consequence."
        ),
    )


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
            passed=review.public_claim_support_state
            in {
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
            in {
                ReviewerGroundingState.REVIEW_GRADE,
                ReviewerGroundingState.DECISION_GRADE,
            },
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
            observed_value=_claim_metric(
                review, "library_conditioned_import_tier", "observed_fraction"
            ),
            required_relation=AcceptanceRelation.AT_LEAST,
            required_value="0.67",
            passed=_claim_metric_float(
                review, "library_conditioned_import_tier", "observed_fraction"
            )
            >= 0.67,
            evidence_paths=(
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/package_manifest.json",
            ),
            note="The current DIA package is only trusted at bounded outsider scope once at least two thirds of library-conditioned peptide evidence remains visible in the shipped decision brief.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="dia_peptide_evidence_coverage",
            dimension="peptide evidence coverage",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=_claim_metric(
                review, "protein_group_reviewability", "protein_groups"
            ),
            required_relation=AcceptanceRelation.AT_LEAST,
            required_value="4",
            passed=_claim_metric_float(
                review, "protein_group_reviewability", "protein_groups"
            )
            >= 4.0,
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
            passed=any(
                finding.revealed_outcome.value == "hit" for finding in holdout.findings
            ),
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
            observed_value=_claim_metric(
                review, "biological_interpretation_tier", "absent_expected_fraction"
            ),
            required_relation=AcceptanceRelation.AT_MOST,
            required_value="0.33",
            passed=_claim_metric_float(
                review, "biological_interpretation_tier", "absent_expected_fraction"
            )
            <= 0.33,
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
            in {
                ReviewerGroundingState.REVIEW_GRADE,
                ReviewerGroundingState.DECISION_GRADE,
            },
            evidence_paths=(
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_outsider_packets_surface.py",
            ),
            note="DIA trust can only regenerate as outsider-auditable when the decision brief is both releasable and still grounded at review-grade or stronger after its library and mobility caveats are carried through.",
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


def _build_lfq_acceptance_sheet() -> FlagshipAcceptanceSheet:
    workflow_family = KnowledgeWorkflowFamily.LFQ
    review = _reviews()[workflow_family]
    criteria = (
        FlagshipAcceptanceCriterion(
            criterion_id="lfq_missingness_burden",
            dimension="missingness burden",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=str(len(review.scientific_limits)),
            required_relation=AcceptanceRelation.AT_MOST,
            required_value="2",
            passed=len(review.scientific_limits) <= 2,
            evidence_paths=(
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
                "packages/bijux-proteomics-core/tests/quantification/test_missingness_profile_surface.py",
            ),
            note="LFQ trust stays bounded to the current flagship package only while missingness and QC caveats remain no broader than the present checked review limits.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="lfq_normalization_drift",
            dimension="normalization drift",
            observed_kind=AcceptanceObservedKind.STATE,
            observed_value="decision_grade",
            required_relation=AcceptanceRelation.EXACTLY,
            required_value="decision_grade",
            passed=_claim_support_state(review, "decision_grade_boundary")
            == "supported",
            evidence_paths=(
                "packages/bijux-proteomics-core/tests/quantification/test_effect_size_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="LFQ acceptance keeps normalization drift tied to the current decision-readiness surface rather than allowing abundance tables to claim stability on raw row count alone.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="lfq_differential_reproducibility",
            dimension="differential reproducibility",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=_claim_metric(
                review, "feature_ingestion", "accepted_records"
            ),
            required_relation=AcceptanceRelation.AT_LEAST,
            required_value="24",
            passed=_claim_metric_float(review, "feature_ingestion", "accepted_records")
            >= 24.0,
            evidence_paths=(
                "packages/bijux-proteomics-core/tests/quantification/test_quantification_scientific_benchmark_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="The current LFQ sheet requires the full tracked feature table to survive ingestion so repeatability claims remain anchored to the same differential evidence surface that the decision brief names.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="lfq_comparator_divergence",
            dimension="comparator divergence",
            observed_kind=AcceptanceObservedKind.STATE,
            observed_value=review.public_claim_support_state.value,
            required_relation=AcceptanceRelation.ONE_OF,
            required_value="advisory|supported",
            passed=review.public_claim_support_state
            in {
                ComparatorClaimSupportState.ADVISORY,
                ComparatorClaimSupportState.SUPPORTED,
            },
            evidence_paths=(
                "packages/bijux-proteomics-knowledge/tests/references/test_comparator_confrontation_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="LFQ public trust is blocked the moment comparator posture falls to refused, because that would mean quantitative interpretation is outrunning the shipped external confrontation surface.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="lfq_recommendation_promotion",
            dimension="recommendation promotion",
            observed_kind=AcceptanceObservedKind.STATE,
            observed_value=f"{review.reviewer_grounding_state.value}:{review.ready_for_release_review}".lower(),
            required_relation=AcceptanceRelation.ONE_OF,
            required_value="review_grade:true|decision_grade:true",
            passed=review.ready_for_release_review
            and review.reviewer_grounding_state
            in {
                ReviewerGroundingState.REVIEW_GRADE,
                ReviewerGroundingState.DECISION_GRADE,
            },
            evidence_paths=(
                "packages/bijux-proteomics-intelligence/tests/reviews/test_outsider_packets_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="LFQ recommendation surfaces can only be regenerated as trusted while the benchmark packet remains releasable and still grounded above thin abundance prose.",
        ),
    )
    return _sheet_from_criteria(
        workflow_family=workflow_family,
        review=review,
        criteria=criteria,
        blocked_claims=(
            "do not promote LFQ to external execution parity",
            "do not treat one stable cohort package as proof of broad quantitative transfer",
        ),
    )


def _build_multiplex_acceptance_sheet() -> FlagshipAcceptanceSheet:
    workflow_family = KnowledgeWorkflowFamily.MULTIPLEX
    review = _reviews()[workflow_family]
    perturbation = _perturbations()[workflow_family.value]
    criteria = (
        FlagshipAcceptanceCriterion(
            criterion_id="multiplex_interference",
            dimension="interference",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=_claim_metric(
                review, "channel_balance_caveats", "flagged_imbalance_count"
            ),
            required_relation=AcceptanceRelation.AT_MOST,
            required_value="1",
            passed=_claim_metric_float(
                review, "channel_balance_caveats", "flagged_imbalance_count"
            )
            <= 1.0,
            evidence_paths=(
                "packages/bijux-proteomics-core/tests/quantification/test_multiplex_artifact_pressure_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="Multiplex trust would require interference pressure to stay at or below one flagged imbalance, which the current flagship package does not earn.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="multiplex_channel_dropout",
            dimension="channel dropout",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=_claim_metric(
                review, "channel_manifest", "missing_channels"
            ),
            required_relation=AcceptanceRelation.EXACTLY,
            required_value="0",
            passed=_claim_metric_float(review, "channel_manifest", "missing_channels")
            == 0.0,
            evidence_paths=(
                "packages/bijux-proteomics-core/tests/quantification/test_multiplex_artifact_pressure_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="A multiplex package with missing reporter channels stays below trust because channel dropout makes even well-shaped ratios too fragile for stronger public language.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="multiplex_reference_channel_fragility",
            dimension="reference-channel fragility",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=_claim_metric(
                review, "channel_balance_caveats", "missing_channel_count"
            ),
            required_relation=AcceptanceRelation.EXACTLY,
            required_value="0",
            passed=_claim_metric_float(
                review, "channel_balance_caveats", "missing_channel_count"
            )
            == 0.0,
            evidence_paths=(
                "packages/bijux-proteomics-core/tests/quantification/test_multiplex_artifact_pressure_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="Reference-channel trust is intentionally strict: any missing channel count keeps multiplex below outsider-facing authority because the bridge/reference story is already brittle.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="multiplex_ratio_compression",
            dimension="ratio compression",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=_metric_value(
                perturbation, "materially_compressed_ratio_count"
            ),
            required_relation=AcceptanceRelation.EXACTLY,
            required_value="0",
            passed=_metric_float(perturbation, "materially_compressed_ratio_count")
            == 0.0,
            evidence_paths=(
                perturbation.artifact_path,
                "packages/bijux-proteomics-core/tests/benchmarks/test_flagship_challenge_corpora_surface.py",
            ),
            note="The multiplex challenge corpus currently shows material ratio compression, so outsider trust would be dishonest even if the base package looks tidy.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="multiplex_downstream_review_promotion",
            dimension="downstream review promotion",
            observed_kind=AcceptanceObservedKind.STATE,
            observed_value=review.public_claim_support_state.value,
            required_relation=AcceptanceRelation.ONE_OF,
            required_value="advisory|supported",
            passed=review.public_claim_support_state
            in {
                ComparatorClaimSupportState.ADVISORY,
                ComparatorClaimSupportState.SUPPORTED,
            },
            evidence_paths=(
                "packages/bijux-proteomics-knowledge/tests/references/test_comparator_confrontation_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="The current multiplex package remains internal-support only because downstream review promotion is still refused once comparator and chemistry caveats are carried honestly.",
        ),
    )
    return _sheet_from_criteria(
        workflow_family=workflow_family,
        review=review,
        criteria=criteria,
        blocked_claims=(
            "do not publish multiplex as outsider-auditable while channel dropout and compression remain open",
            "do not treat reporter-channel summaries as broad biological authority",
        ),
    )


def _build_ptm_acceptance_sheet() -> FlagshipAcceptanceSheet:
    workflow_family = KnowledgeWorkflowFamily.PTM
    review = _reviews()[workflow_family]
    criteria = (
        FlagshipAcceptanceCriterion(
            criterion_id="ptm_localization_quality",
            dimension="localization quality",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=_claim_metric(
                review, "phospho_review_packet", "motif_windows"
            ),
            required_relation=AcceptanceRelation.AT_LEAST,
            required_value="5",
            passed=_claim_metric_float(review, "phospho_review_packet", "motif_windows")
            >= 5.0,
            evidence_paths=(
                "packages/bijux-proteomics-core/tests/ptm/test_ptm_scientific_benchmark_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="PTM trust starts only when the flagship packet still carries at least five motif windows, keeping localized biology tied to explicit site context instead of score-only slogans.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="ptm_ambiguity_burden",
            dimension="ambiguity burden",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=_claim_metric(
                review, "site_ambiguity_visibility", "ambiguous_sites"
            ),
            required_relation=AcceptanceRelation.AT_MOST,
            required_value="2",
            passed=_claim_metric_float(
                review, "site_ambiguity_visibility", "ambiguous_sites"
            )
            <= 2.0,
            evidence_paths=(
                "packages/bijux-proteomics-core/tests/ptm/test_ptm_scientific_benchmark_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="The current PTM package keeps ambiguity burden barely inside trust by exposing exactly two ambiguous sites; anything broader would push the family back below bounded outsider authority.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="ptm_motif_credibility",
            dimension="motif credibility",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=str(len(review.supported_ptm_families)),
            required_relation=AcceptanceRelation.AT_LEAST,
            required_value="2",
            passed=len(review.supported_ptm_families) >= 2,
            evidence_paths=(
                "packages/bijux-proteomics-core/tests/ptm/test_lab_validation_packet_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="PTM motif credibility is published only because two PTM families remain explicitly supported while glyco-adjacent interpretation is still refused in the same packet.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="ptm_occupancy_stability",
            dimension="occupancy stability",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=_claim_metric(
                review, "phospho_review_packet", "quantified_samples"
            ),
            required_relation=AcceptanceRelation.AT_LEAST,
            required_value="4",
            passed=_claim_metric_float(
                review, "phospho_review_packet", "quantified_samples"
            )
            >= 4.0,
            evidence_paths=(
                "packages/bijux-proteomics-core/tests/ptm/test_occupancy_counterpart_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="The occupancy surface needs at least four quantified samples so PTM trust still reflects measurable abundance context rather than motif-only interpretation.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="ptm_targetability_promotion",
            dimension="targetability promotion",
            observed_kind=AcceptanceObservedKind.STATE,
            observed_value=_claim_support_state(review, "raw_spectrum_validation_lane"),
            required_relation=AcceptanceRelation.ONE_OF,
            required_value="advisory|supported",
            passed=_claim_support_state(review, "raw_spectrum_validation_lane")
            in {"advisory", "supported"},
            evidence_paths=(
                "packages/bijux-proteomics-core/tests/ptm/test_lab_validation_packet_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="PTM follow-up promotion remains bounded but legitimate only while the raw-spectrum validation lane is still visible as advisory or stronger instead of disappearing behind TSV-localization confidence alone.",
        ),
    )
    return _sheet_from_criteria(
        workflow_family=workflow_family,
        review=review,
        criteria=criteria,
        blocked_claims=(
            "do not present PTM as glycopeptide-ready",
            "do not flatten ambiguous-site burden into pathway certainty",
        ),
    )


def _build_targeted_acceptance_sheet() -> FlagshipAcceptanceSheet:
    workflow_family = KnowledgeWorkflowFamily.TARGETED
    review = _reviews()[workflow_family]
    criteria = (
        FlagshipAcceptanceCriterion(
            criterion_id="targeted_calibration_quality",
            dimension="calibration quality",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=_claim_metric(
                review, "calibration_and_pairing_pressure", "calibration_failed"
            ),
            required_relation=AcceptanceRelation.AT_MOST,
            required_value="1",
            passed=_claim_metric_float(
                review, "calibration_and_pairing_pressure", "calibration_failed"
            )
            <= 1.0,
            evidence_paths=(
                "packages/bijux-proteomics-core/tests/dia/test_targeted_benchmark_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="Targeted trust is capped at one failed calibration standard in the flagship package; more than that would make even bounded follow-up language dishonest.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="targeted_transition_interference",
            dimension="transition interference",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=_claim_metric(
                review, "calibration_and_pairing_pressure", "interference_flags"
            ),
            required_relation=AcceptanceRelation.AT_MOST,
            required_value="1",
            passed=_claim_metric_float(
                review, "calibration_and_pairing_pressure", "interference_flags"
            )
            <= 1.0,
            evidence_paths=(
                "packages/bijux-proteomics-core/tests/dia/test_targeted_benchmark_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="The targeted sheet allows at most one explicit interference flag, forcing follow-up trust to remain coupled to chromatogram trouble instead of hiding it under clean handoff prose.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="targeted_heavy_light_coherence",
            dimension="heavy-light coherence",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=_claim_metric(
                review, "calibration_and_pairing_pressure", "missing_pairs"
            ),
            required_relation=AcceptanceRelation.AT_MOST,
            required_value="1",
            passed=_claim_metric_float(
                review, "calibration_and_pairing_pressure", "missing_pairs"
            )
            <= 1.0,
            evidence_paths=(
                "packages/bijux-proteomics-core/tests/dia/test_targeted_benchmark_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="Heavy/light pairing is bounded tightly because targeted follow-up credibility collapses quickly when missing pairs are allowed to accumulate silently.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="targeted_carryover_posture",
            dimension="carryover posture",
            observed_kind=AcceptanceObservedKind.INTEGER,
            observed_value=_claim_metric(
                review, "chromatogram_qc_surface", "failed_metric_rows"
            ),
            required_relation=AcceptanceRelation.EXACTLY,
            required_value="0",
            passed=_claim_metric_float(
                review, "chromatogram_qc_surface", "failed_metric_rows"
            )
            == 0.0,
            evidence_paths=(
                "packages/bijux-proteomics-core/tests/dia/test_targeted_benchmark_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="Carryover posture remains acceptable only while the shipped chromatogram QC table stays free of failed metric rows in the public targeted package.",
        ),
        FlagshipAcceptanceCriterion(
            criterion_id="targeted_follow_up_promotion",
            dimension="follow-up promotion",
            observed_kind=AcceptanceObservedKind.STATE,
            observed_value=_claim_support_state(review, "raw_to_reviewed_bundle"),
            required_relation=AcceptanceRelation.EXACTLY,
            required_value="supported",
            passed=_claim_support_state(review, "raw_to_reviewed_bundle")
            == "supported",
            evidence_paths=(
                "packages/bijux-proteomics-lab/tests/benchmarks/test_benchmark_flagship_follow_up_surface.py",
                "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
            ),
            note="Targeted outsider trust depends on a supported raw-to-reviewed bundle so inflated handoffs stay caught and reconciled before any lab-facing promotion survives regeneration.",
        ),
    )
    return _sheet_from_criteria(
        workflow_family=workflow_family,
        review=review,
        criteria=criteria,
        blocked_claims=(
            "do not imply vendor-ready targeted execution from a bounded review bundle",
            "do not promote targeted follow-up when calibration and pairing caveats widen",
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
            "This sheet keeps flagship workflow trust tied to measurable bars on the shipped benchmark package, challenge corpus, and decision brief."
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
    claim = next(
        claim for claim in review.claim_summaries if claim.claim_id == claim_id
    )
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


def _claim_support_state(review: WorkflowBenchmarkReview, claim_id: str) -> str:
    claim = next(
        claim for claim in review.claim_summaries if claim.claim_id == claim_id
    )
    return claim.support_state.value


def _metric_value(report: PerturbationReactionReport, metric_id: str) -> str:
    metric = next(item for item in report.metric_deltas if item.metric_id == metric_id)
    return str(int(metric.perturbed_value))


def _metric_float(report: PerturbationReactionReport, metric_id: str) -> float:
    metric = next(item for item in report.metric_deltas if item.metric_id == metric_id)
    return float(metric.perturbed_value)


def _literature_basis(
    *,
    threshold_report: WorkflowThresholdEvidenceReport,
    threshold_ids: tuple[str, ...],
) -> str:
    if not threshold_ids:
        return "no workflow-threshold evidence anchors were published for this family"
    return (
        "workflow-threshold anchors remain visible through "
        + ", ".join(threshold_ids)
        + " with citations "
        + ", ".join(
            citation_id
            for entry in threshold_report.entries
            for citation_id in entry.citation_ids
        )
    )
