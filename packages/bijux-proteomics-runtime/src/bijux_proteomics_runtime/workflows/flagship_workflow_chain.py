# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Flagship workflow-chain surfaces for the bounded workflow family."""

from __future__ import annotations

from enum import StrEnum
import hashlib
import json
from typing import Protocol

from pydantic import ConfigDict, Field

from bijux_proteomics.review.flagship_kernel import FlagshipScientificKernelReport
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.judgment.flagship_decisions import (
    FlagshipDecisionReview,
)
from bijux_proteomics_runtime.workflows.runs import (
    DdaImportWorkflowRunReport,
    LabHandoffWorkflowRunReport,
    PtmRuntimeWorkflowRunReport,
    QuantRuntimeWorkflowRunReport,
    SequenceToDigestWorkflowRunReport,
)


class _FlagshipEvidenceDecisionBriefLike(Protocol):
    artifact_path: str
    evidence_pointers: tuple[str, ...]
    note: str


class _FlagshipWorkflowFollowUpPacketLike(Protocol):
    artifact_path: str
    next_cycle_artifact_path: str
    note: str


class FlagshipWorkflowStage(StrEnum):
    """Owner-visible stages in the flagship workflow proof set."""

    SEQUENCE_INTAKE = "sequence_intake"
    SEARCH_AND_CONFIDENCE = "search_and_confidence"
    QUANTIFICATION = "quantification"
    PTM_REVIEW = "ptm_review"
    SCIENTIFIC_KERNEL = "scientific_kernel"
    EVIDENCE_REVIEW = "evidence_review"
    DECISION_REVIEW = "decision_review"
    LAB_HANDOFF = "lab_handoff"
    FOLLOW_UP = "follow_up"


class WorkflowClaimKind(StrEnum):
    """Claim kinds that must resolve to governed artifact locations."""

    WORKFLOW = "workflow"
    REPLAY = "replay"
    INTEGRITY = "integrity"


class FlagshipWorkflowClaimTier(StrEnum):
    """Runtime-owned claim tiers for the flagship workflow chain."""

    OWNED_CONTRACT = "owned_contract"
    BENCHMARK_BACKED_BEHAVIOR = "benchmark_backed_behavior"
    RUNTIME_PROVEN_WORKFLOW = "runtime_proven_workflow"
    FUTURE_WORK = "future_work"


class FlagshipWorkflowStageProof(JsonModel):
    """One reviewed stage in the flagship workflow proof set."""

    model_config = ConfigDict(extra="forbid")

    stage: FlagshipWorkflowStage
    owner_package: str = Field(..., min_length=1)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class WorkflowArtifactClaim(JsonModel):
    """One machine-readable claim tied to an artifact path and validating test."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    claim_kind: WorkflowClaimKind
    claim_tier: FlagshipWorkflowClaimTier
    owner_package: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    validating_test_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)


class FlagshipWorkflowScopeDossier(JsonModel):
    """Scope dossier that keeps the flagship workflow chain explicit and narrow."""

    model_config = ConfigDict(extra="forbid")

    flagship_family_id: str = Field(..., min_length=1)
    approved_workflow_families: tuple[str, ...] = Field(default_factory=tuple)
    future_only_workflow_families: tuple[str, ...] = Field(default_factory=tuple)
    example_workflow_prose_scope: str = Field(..., min_length=1)
    claim_taxonomy: tuple[FlagshipWorkflowClaimTier, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipWorkflowChain(JsonModel):
    """End-to-end evidence chain for the bounded flagship workflow surface."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    scope_dossier: FlagshipWorkflowScopeDossier
    stages: tuple[FlagshipWorkflowStageProof, ...] = Field(default_factory=tuple)
    artifact_claims: tuple[WorkflowArtifactClaim, ...] = Field(default_factory=tuple)
    proof_digest: str = Field(..., min_length=64, max_length=64)
    proof_complete: bool
    note: str = Field(..., min_length=1)


class FlagshipWorkflowDeterminismReport(JsonModel):
    """Deterministic comparison across two flagship workflow proof bundles."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    equivalent: bool
    changed_fields: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipWorkflowBreakageFinding(JsonModel):
    """One structural breakage in the flagship workflow proof set."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    blocking: bool


class FlagshipWorkflowBreakageReport(JsonModel):
    """Structural integrity report for flagship workflow proof bundles."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    valid: bool
    findings: tuple[FlagshipWorkflowBreakageFinding, ...] = Field(default_factory=tuple)


def _stable_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_flagship_workflow_scope_dossier() -> FlagshipWorkflowScopeDossier:
    """Define the one bounded workflow family this chain may describe directly."""

    return FlagshipWorkflowScopeDossier(
        flagship_family_id="flagship-workflows",
        approved_workflow_families=("flagship-workflows",),
        future_only_workflow_families=(
            "glycopeptide-review",
            "library-search-review",
            "external-engine-parity",
        ),
        example_workflow_prose_scope="flagship_only",
        claim_taxonomy=(
            FlagshipWorkflowClaimTier.OWNED_CONTRACT,
            FlagshipWorkflowClaimTier.BENCHMARK_BACKED_BEHAVIOR,
            FlagshipWorkflowClaimTier.RUNTIME_PROVEN_WORKFLOW,
            FlagshipWorkflowClaimTier.FUTURE_WORK,
        ),
        note=(
            "Only the flagship-workflows family may use one-family workflow language. "
            "All broader workflow families remain future-only until they have their own checked evidence chains."
        ),
    )


def _stage_artifact_claims(
    stages: tuple[FlagshipWorkflowStageProof, ...],
) -> tuple[WorkflowArtifactClaim, ...]:
    validating_tests = {
        FlagshipWorkflowStage.SEQUENCE_INTAKE: "packages/bijux-proteomics-runtime/tests/workflows/test_flagship_workflow_chain_surface.py::test_build_flagship_workflow_chain_tracks_all_owner_stages",
        FlagshipWorkflowStage.SEARCH_AND_CONFIDENCE: "packages/bijux-proteomics-runtime/tests/workflows/test_flagship_workflow_chain_surface.py::test_build_flagship_workflow_chain_tracks_all_owner_stages",
        FlagshipWorkflowStage.QUANTIFICATION: "packages/bijux-proteomics-runtime/tests/workflows/test_flagship_workflow_chain_surface.py::test_build_flagship_workflow_chain_tracks_all_owner_stages",
        FlagshipWorkflowStage.PTM_REVIEW: "packages/bijux-proteomics-runtime/tests/workflows/test_flagship_workflow_chain_surface.py::test_build_flagship_workflow_chain_tracks_all_owner_stages",
        FlagshipWorkflowStage.SCIENTIFIC_KERNEL: "packages/bijux-proteomics-core/tests/review/test_flagship_scientific_kernel_surface.py::test_build_flagship_scientific_kernel_report_exposes_narrow_scope_boundaries",
        FlagshipWorkflowStage.EVIDENCE_REVIEW: "packages/bijux-proteomics-knowledge/tests/reviews/test_flagship_evidence_surface.py::test_build_flagship_evidence_decision_brief_preserves_claim_tier_and_artifact_path",
        FlagshipWorkflowStage.DECISION_REVIEW: "packages/bijux-proteomics-intelligence/tests/judgment/test_flagship_decisions_surface.py::test_build_flagship_decision_review_allows_lab_when_kernel_and_review_are_clean",
        FlagshipWorkflowStage.LAB_HANDOFF: "packages/bijux-proteomics-runtime/tests/workflows/test_flagship_workflow_chain_surface.py::test_build_flagship_workflow_chain_tracks_all_owner_stages",
        FlagshipWorkflowStage.FOLLOW_UP: "packages/bijux-proteomics-lab/tests/reconciliation/test_reconciliation_flagship_follow_up_surface.py::test_build_flagship_workflow_follow_up_packet_marks_ready_progression",
    }
    claims: list[WorkflowArtifactClaim] = []
    for stage in stages:
        for index, artifact_path in enumerate(stage.artifact_paths, start=1):
            claims.append(
                WorkflowArtifactClaim(
                    claim_id=f"{stage.stage.value}-artifact-{index}",
                    claim_kind=WorkflowClaimKind.WORKFLOW,
                    claim_tier=FlagshipWorkflowClaimTier.RUNTIME_PROVEN_WORKFLOW,
                    owner_package=stage.owner_package,
                    artifact_path=artifact_path,
                    validating_test_id=validating_tests[stage.stage],
                    rationale=f"{stage.stage.value} keeps one checked artifact path for the flagship workflow chain",
                )
            )
    claims.extend(
        (
            WorkflowArtifactClaim(
                claim_id="flagship-workflow-replay-evidence",
                claim_kind=WorkflowClaimKind.REPLAY,
                claim_tier=FlagshipWorkflowClaimTier.RUNTIME_PROVEN_WORKFLOW,
                owner_package="bijux-proteomics-runtime",
                artifact_path="artifacts/workflows/flagship-workflow-chain/replay/determinism_report.json",
                validating_test_id="packages/bijux-proteomics-runtime/tests/workflows/test_flagship_workflow_chain_surface.py::test_compare_flagship_workflow_chains_is_deterministic_for_same_inputs",
                rationale="the flagship workflow must prove deterministic regeneration under the same inputs",
            ),
            WorkflowArtifactClaim(
                claim_id="flagship-workflow-integrity-evidence",
                claim_kind=WorkflowClaimKind.INTEGRITY,
                claim_tier=FlagshipWorkflowClaimTier.RUNTIME_PROVEN_WORKFLOW,
                owner_package="bijux-proteomics-runtime",
                artifact_path="artifacts/workflows/flagship-workflow-chain/integrity/breakage_report.json",
                validating_test_id="packages/bijux-proteomics-runtime/tests/workflows/test_flagship_workflow_chain_surface.py::test_evaluate_flagship_workflow_breakage_detects_missing_follow_up_and_bad_paths",
                rationale="the flagship workflow must fail visibly when artifact paths or owner stages break",
            ),
        )
    )
    return tuple(claims)


def _bundle_payload(
    *,
    workflow_id: str,
    scope_dossier: FlagshipWorkflowScopeDossier,
    stages: tuple[FlagshipWorkflowStageProof, ...],
    artifact_claims: tuple[WorkflowArtifactClaim, ...],
    proof_complete: bool,
    note: str,
) -> dict[str, object]:
    return {
        "workflow_id": workflow_id,
        "scope_dossier": scope_dossier.model_dump(mode="json"),
        "stages": [stage.model_dump(mode="json") for stage in stages],
        "artifact_claims": [claim.model_dump(mode="json") for claim in artifact_claims],
        "proof_complete": proof_complete,
        "note": note,
    }


def build_flagship_workflow_chain(
    *,
    sequence_report: SequenceToDigestWorkflowRunReport,
    dda_report: DdaImportWorkflowRunReport,
    quant_report: QuantRuntimeWorkflowRunReport,
    ptm_report: PtmRuntimeWorkflowRunReport,
    scientific_kernel: FlagshipScientificKernelReport,
    evidence_review: _FlagshipEvidenceDecisionBriefLike,
    decision_review: FlagshipDecisionReview,
    lab_handoff: LabHandoffWorkflowRunReport,
    follow_up: _FlagshipWorkflowFollowUpPacketLike,
) -> FlagshipWorkflowChain:
    """Assemble the flagship workflow chain across real owner packages."""

    workflow_id = "flagship-workflow-chain"
    scope_dossier = build_flagship_workflow_scope_dossier()
    stages = (
        FlagshipWorkflowStageProof(
            stage=FlagshipWorkflowStage.SEQUENCE_INTAKE,
            owner_package="bijux-proteomics-runtime",
            artifact_paths=sequence_report.artifact_paths,
            evidence_pointers=sequence_report.evidence_pointers,
            note=sequence_report.note,
        ),
        FlagshipWorkflowStageProof(
            stage=FlagshipWorkflowStage.SEARCH_AND_CONFIDENCE,
            owner_package="bijux-proteomics-runtime",
            artifact_paths=dda_report.artifact_paths,
            evidence_pointers=dda_report.evidence_pointers,
            note=dda_report.note,
        ),
        FlagshipWorkflowStageProof(
            stage=FlagshipWorkflowStage.QUANTIFICATION,
            owner_package="bijux-proteomics-runtime",
            artifact_paths=quant_report.artifact_paths,
            evidence_pointers=quant_report.evidence_pointers,
            note=quant_report.note,
        ),
        FlagshipWorkflowStageProof(
            stage=FlagshipWorkflowStage.PTM_REVIEW,
            owner_package="bijux-proteomics-runtime",
            artifact_paths=ptm_report.artifact_paths,
            evidence_pointers=ptm_report.evidence_pointers,
            note=ptm_report.note,
        ),
        FlagshipWorkflowStageProof(
            stage=FlagshipWorkflowStage.SCIENTIFIC_KERNEL,
            owner_package="bijux-proteomics-core",
            artifact_paths=(scientific_kernel.artifact_path,),
            evidence_pointers=(
                "core.review.scientific_story",
                "core.review.scientific_conflicts",
                "core.review.untrustworthy_checklists",
            ),
            note=scientific_kernel.note,
        ),
        FlagshipWorkflowStageProof(
            stage=FlagshipWorkflowStage.EVIDENCE_REVIEW,
            owner_package="bijux-proteomics-knowledge",
            artifact_paths=(evidence_review.artifact_path,),
            evidence_pointers=evidence_review.evidence_pointers,
            note=evidence_review.note,
        ),
        FlagshipWorkflowStageProof(
            stage=FlagshipWorkflowStage.DECISION_REVIEW,
            owner_package="bijux-proteomics-intelligence",
            artifact_paths=(decision_review.artifact_path,),
            evidence_pointers=("intelligence.flagship.decision_review",),
            note=decision_review.note,
        ),
        FlagshipWorkflowStageProof(
            stage=FlagshipWorkflowStage.LAB_HANDOFF,
            owner_package="bijux-proteomics-runtime",
            artifact_paths=lab_handoff.artifact_paths,
            evidence_pointers=lab_handoff.evidence_pointers,
            note=lab_handoff.note,
        ),
        FlagshipWorkflowStageProof(
            stage=FlagshipWorkflowStage.FOLLOW_UP,
            owner_package="bijux-proteomics-lab",
            artifact_paths=(
                follow_up.artifact_path,
                follow_up.next_cycle_artifact_path,
            ),
            evidence_pointers=("lab.flagship.follow_up", "lab.flagship.next_cycle"),
            note=follow_up.note,
        ),
    )
    artifact_claims = _stage_artifact_claims(stages)
    proof_complete = all(
        artifact_path.startswith("artifacts/")
        for stage in stages
        for artifact_path in stage.artifact_paths
    )
    note = (
        "This bundle is the one checked flagship workflow chain. It proves a narrow "
        "sequence-to-review-to-follow-up story and refuses to stand in for broader workflow coverage."
    )
    payload = _bundle_payload(
        workflow_id=workflow_id,
        scope_dossier=scope_dossier,
        stages=stages,
        artifact_claims=artifact_claims,
        proof_complete=proof_complete,
        note=note,
    )
    return FlagshipWorkflowChain(
        workflow_id=workflow_id,
        scope_dossier=scope_dossier,
        stages=stages,
        artifact_claims=artifact_claims,
        proof_digest=_stable_sha256(payload),
        proof_complete=proof_complete,
        note=note,
    )


def compare_flagship_workflow_chains(
    baseline: FlagshipWorkflowChain,
    candidate: FlagshipWorkflowChain,
) -> FlagshipWorkflowDeterminismReport:
    """Compare two flagship workflow proof bundles deterministically."""

    changed_fields: list[str] = []
    if baseline.scope_dossier != candidate.scope_dossier:
        changed_fields.append("scope_dossier")
    if baseline.stages != candidate.stages:
        changed_fields.append("stages")
    if baseline.artifact_claims != candidate.artifact_claims:
        changed_fields.append("artifact_claims")
    if baseline.proof_complete != candidate.proof_complete:
        changed_fields.append("proof_complete")
    if baseline.note != candidate.note:
        changed_fields.append("note")

    return FlagshipWorkflowDeterminismReport(
        workflow_id=baseline.workflow_id,
        equivalent=not changed_fields,
        changed_fields=tuple(changed_fields),
        note=(
            "Equivalent bundles may be described as deterministic regeneration for the flagship workflow chain."
            if not changed_fields
            else "The flagship workflow chain changed across repeated builds."
        ),
    )


def evaluate_flagship_workflow_breakage(
    bundle: FlagshipWorkflowChain,
) -> FlagshipWorkflowBreakageReport:
    """Detect structural breakage in the flagship workflow proof set."""

    findings: list[FlagshipWorkflowBreakageFinding] = []
    required_stages = set(FlagshipWorkflowStage)
    observed_stages = {stage.stage for stage in bundle.stages}
    missing_stages = sorted(stage.value for stage in required_stages - observed_stages)
    if missing_stages:
        findings.append(
            FlagshipWorkflowBreakageFinding(
                code="missing_owner_stage",
                message="missing flagship owner stages: " + ", ".join(missing_stages),
                blocking=True,
            )
        )
    for claim in bundle.artifact_claims:
        if not claim.artifact_path.startswith("artifacts/"):
            findings.append(
                FlagshipWorkflowBreakageFinding(
                    code="artifact_path_outside_artifacts",
                    message=f"claim {claim.claim_id} points outside artifacts/",
                    blocking=True,
                )
            )
        if "::" not in claim.validating_test_id:
            findings.append(
                FlagshipWorkflowBreakageFinding(
                    code="missing_validating_test",
                    message=f"claim {claim.claim_id} has no pytest node id",
                    blocking=True,
                )
            )
    claim_kinds = {claim.claim_kind for claim in bundle.artifact_claims}
    if WorkflowClaimKind.REPLAY not in claim_kinds:
        findings.append(
            FlagshipWorkflowBreakageFinding(
                code="missing_replay_claim",
                message="flagship workflow proof set no longer carries a replay claim",
                blocking=True,
            )
        )
    if WorkflowClaimKind.INTEGRITY not in claim_kinds:
        findings.append(
            FlagshipWorkflowBreakageFinding(
                code="missing_integrity_claim",
                message="flagship workflow proof set no longer carries an integrity claim",
                blocking=True,
            )
        )
    return FlagshipWorkflowBreakageReport(
        workflow_id=bundle.workflow_id,
        valid=not findings,
        findings=tuple(findings),
    )
