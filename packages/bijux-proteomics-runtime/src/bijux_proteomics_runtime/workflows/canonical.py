# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical workflow proof surfaces for the flagship reviewable proteomics family."""

from __future__ import annotations

from enum import StrEnum
import hashlib
import json

from pydantic import ConfigDict, Field

from bijux_proteomics.review.canonical_kernel import CanonicalScientificKernelReport
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.judgment.canonical_reviews import (
    CanonicalDecisionReview,
)
from bijux_proteomics_knowledge.reviews.workflow_packets import (
    CanonicalEvidenceReviewPacket,
    WorkflowClaimTier,
)
from bijux_proteomics_lab.reconciliation.canonical_follow_up import (
    CanonicalWorkflowFollowUpPacket,
)
from bijux_proteomics_runtime.workflows.runs import (
    DdaImportWorkflowRunReport,
    LabHandoffWorkflowRunReport,
    PtmRuntimeWorkflowRunReport,
    QuantRuntimeWorkflowRunReport,
    SequenceToDigestWorkflowRunReport,
)


class CanonicalWorkflowStage(StrEnum):
    """Owner-visible stages in the canonical workflow proof set."""

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


class CanonicalWorkflowStageProof(JsonModel):
    """One reviewed stage in the canonical workflow proof set."""

    model_config = ConfigDict(extra="forbid")

    stage: CanonicalWorkflowStage
    owner_package: str = Field(..., min_length=1)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class WorkflowArtifactClaim(JsonModel):
    """One machine-readable claim tied to an artifact path and validating test."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    claim_kind: WorkflowClaimKind
    claim_tier: WorkflowClaimTier
    owner_package: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    validating_test_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)


class CanonicalWorkflowScopeDossier(JsonModel):
    """Scope dossier that keeps the flagship workflow family explicit and narrow."""

    model_config = ConfigDict(extra="forbid")

    flagship_family_id: str = Field(..., min_length=1)
    approved_workflow_families: tuple[str, ...] = Field(default_factory=tuple)
    future_only_workflow_families: tuple[str, ...] = Field(default_factory=tuple)
    example_workflow_prose_scope: str = Field(..., min_length=1)
    claim_taxonomy: tuple[WorkflowClaimTier, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class CanonicalWorkflowProofBundle(JsonModel):
    """Canonical end-to-end proof set for the flagship workflow family."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    scope_dossier: CanonicalWorkflowScopeDossier
    stages: tuple[CanonicalWorkflowStageProof, ...] = Field(default_factory=tuple)
    artifact_claims: tuple[WorkflowArtifactClaim, ...] = Field(default_factory=tuple)
    proof_digest: str = Field(..., min_length=64, max_length=64)
    proof_complete: bool
    note: str = Field(..., min_length=1)


class CanonicalWorkflowDeterminismReport(JsonModel):
    """Deterministic comparison across two canonical workflow proof bundles."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    equivalent: bool
    changed_fields: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class CanonicalWorkflowBreakageFinding(JsonModel):
    """One structural breakage in the canonical workflow proof set."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    blocking: bool


class CanonicalWorkflowBreakageReport(JsonModel):
    """Structural integrity report for canonical workflow proof bundles."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    valid: bool
    findings: tuple[CanonicalWorkflowBreakageFinding, ...] = Field(default_factory=tuple)


def _stable_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_flagship_workflow_scope_dossier() -> CanonicalWorkflowScopeDossier:
    """Define the one workflow family currently allowed to speak as canonical."""

    return CanonicalWorkflowScopeDossier(
        flagship_family_id="reviewable-proteomics",
        approved_workflow_families=("reviewable-proteomics",),
        future_only_workflow_families=(
            "glycopeptide-review",
            "library-search-review",
            "external-engine-parity",
        ),
        example_workflow_prose_scope="flagship_only",
        claim_taxonomy=(
            WorkflowClaimTier.OWNED_CONTRACT,
            WorkflowClaimTier.BENCHMARK_BACKED_BEHAVIOR,
            WorkflowClaimTier.RUNTIME_PROVEN_WORKFLOW,
            WorkflowClaimTier.FUTURE_WORK,
        ),
        note=(
            "Only the reviewable-proteomics family may use canonical workflow prose. "
            "All broader workflow families remain future-only until they have their own checked proof sets."
        ),
    )


def _stage_artifact_claims(
    stages: tuple[CanonicalWorkflowStageProof, ...],
) -> tuple[WorkflowArtifactClaim, ...]:
    validating_tests = {
        CanonicalWorkflowStage.SEQUENCE_INTAKE: "packages/bijux-proteomics-runtime/tests/workflows/test_canonical_workflow_surface.py::test_build_canonical_workflow_proof_bundle_tracks_all_owner_stages",
        CanonicalWorkflowStage.SEARCH_AND_CONFIDENCE: "packages/bijux-proteomics-runtime/tests/workflows/test_canonical_workflow_surface.py::test_build_canonical_workflow_proof_bundle_tracks_all_owner_stages",
        CanonicalWorkflowStage.QUANTIFICATION: "packages/bijux-proteomics-runtime/tests/workflows/test_canonical_workflow_surface.py::test_build_canonical_workflow_proof_bundle_tracks_all_owner_stages",
        CanonicalWorkflowStage.PTM_REVIEW: "packages/bijux-proteomics-runtime/tests/workflows/test_canonical_workflow_surface.py::test_build_canonical_workflow_proof_bundle_tracks_all_owner_stages",
        CanonicalWorkflowStage.SCIENTIFIC_KERNEL: "packages/bijux-proteomics-core/tests/review/test_canonical_scientific_kernel_surface.py::test_build_canonical_scientific_kernel_report_exposes_narrow_scope_boundaries",
        CanonicalWorkflowStage.EVIDENCE_REVIEW: "packages/bijux-proteomics-knowledge/tests/reviews/test_workflow_packets_surface.py::test_build_canonical_evidence_review_packet_preserves_claim_tier_and_artifact_path",
        CanonicalWorkflowStage.DECISION_REVIEW: "packages/bijux-proteomics-intelligence/tests/judgment/test_canonical_reviews_surface.py::test_build_flagship_decision_review_allows_lab_when_kernel_and_review_are_clean",
        CanonicalWorkflowStage.LAB_HANDOFF: "packages/bijux-proteomics-runtime/tests/workflows/test_canonical_workflow_surface.py::test_build_canonical_workflow_proof_bundle_tracks_all_owner_stages",
        CanonicalWorkflowStage.FOLLOW_UP: "packages/bijux-proteomics-lab/tests/reconciliation/test_canonical_follow_up_surface.py::test_build_canonical_workflow_follow_up_packet_marks_ready_progression",
    }
    claims: list[WorkflowArtifactClaim] = []
    for stage in stages:
        for index, artifact_path in enumerate(stage.artifact_paths, start=1):
            claims.append(
                WorkflowArtifactClaim(
                    claim_id=f"{stage.stage.value}-artifact-{index}",
                    claim_kind=WorkflowClaimKind.WORKFLOW,
                    claim_tier=WorkflowClaimTier.RUNTIME_PROVEN_WORKFLOW,
                    owner_package=stage.owner_package,
                    artifact_path=artifact_path,
                    validating_test_id=validating_tests[stage.stage],
                    rationale=f"{stage.stage.value} keeps one checked artifact path for the canonical workflow proof set",
                )
            )
    claims.extend(
        (
            WorkflowArtifactClaim(
                claim_id="canonical-workflow-replay-proof",
                claim_kind=WorkflowClaimKind.REPLAY,
                claim_tier=WorkflowClaimTier.RUNTIME_PROVEN_WORKFLOW,
                owner_package="bijux-proteomics-runtime",
                artifact_path="artifacts/workflows/canonical-reviewable-proteomics/replay/determinism_report.json",
                validating_test_id="packages/bijux-proteomics-runtime/tests/workflows/test_canonical_workflow_surface.py::test_compare_canonical_workflow_proof_bundles_is_deterministic_for_same_inputs",
                rationale="the flagship workflow must prove deterministic regeneration under the same inputs",
            ),
            WorkflowArtifactClaim(
                claim_id="canonical-workflow-integrity-proof",
                claim_kind=WorkflowClaimKind.INTEGRITY,
                claim_tier=WorkflowClaimTier.RUNTIME_PROVEN_WORKFLOW,
                owner_package="bijux-proteomics-runtime",
                artifact_path="artifacts/workflows/canonical-reviewable-proteomics/integrity/breakage_report.json",
                validating_test_id="packages/bijux-proteomics-runtime/tests/workflows/test_canonical_workflow_surface.py::test_evaluate_canonical_workflow_breakage_detects_missing_follow_up_and_bad_paths",
                rationale="the flagship workflow must fail visibly when artifact paths or owner stages break",
            ),
        )
    )
    return tuple(claims)


def _bundle_payload(
    *,
    workflow_id: str,
    scope_dossier: CanonicalWorkflowScopeDossier,
    stages: tuple[CanonicalWorkflowStageProof, ...],
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


def build_canonical_workflow_proof_bundle(
    *,
    sequence_report: SequenceToDigestWorkflowRunReport,
    dda_report: DdaImportWorkflowRunReport,
    quant_report: QuantRuntimeWorkflowRunReport,
    ptm_report: PtmRuntimeWorkflowRunReport,
    scientific_kernel: CanonicalScientificKernelReport,
    evidence_review: CanonicalEvidenceReviewPacket,
    decision_review: CanonicalDecisionReview,
    lab_handoff: LabHandoffWorkflowRunReport,
    follow_up: CanonicalWorkflowFollowUpPacket,
) -> CanonicalWorkflowProofBundle:
    """Assemble the canonical workflow proof set across real owner packages."""

    workflow_id = "canonical-reviewable-proteomics"
    scope_dossier = build_flagship_workflow_scope_dossier()
    stages = (
        CanonicalWorkflowStageProof(
            stage=CanonicalWorkflowStage.SEQUENCE_INTAKE,
            owner_package="bijux-proteomics-runtime",
            artifact_paths=sequence_report.artifact_paths,
            evidence_pointers=sequence_report.evidence_pointers,
            note=sequence_report.note,
        ),
        CanonicalWorkflowStageProof(
            stage=CanonicalWorkflowStage.SEARCH_AND_CONFIDENCE,
            owner_package="bijux-proteomics-runtime",
            artifact_paths=dda_report.artifact_paths,
            evidence_pointers=dda_report.evidence_pointers,
            note=dda_report.note,
        ),
        CanonicalWorkflowStageProof(
            stage=CanonicalWorkflowStage.QUANTIFICATION,
            owner_package="bijux-proteomics-runtime",
            artifact_paths=quant_report.artifact_paths,
            evidence_pointers=quant_report.evidence_pointers,
            note=quant_report.note,
        ),
        CanonicalWorkflowStageProof(
            stage=CanonicalWorkflowStage.PTM_REVIEW,
            owner_package="bijux-proteomics-runtime",
            artifact_paths=ptm_report.artifact_paths,
            evidence_pointers=ptm_report.evidence_pointers,
            note=ptm_report.note,
        ),
        CanonicalWorkflowStageProof(
            stage=CanonicalWorkflowStage.SCIENTIFIC_KERNEL,
            owner_package="bijux-proteomics-core",
            artifact_paths=(scientific_kernel.artifact_path,),
            evidence_pointers=(
                "core.review.scientific_story",
                "core.review.scientific_conflicts",
                "core.review.untrustworthy_checklists",
            ),
            note=scientific_kernel.note,
        ),
        CanonicalWorkflowStageProof(
            stage=CanonicalWorkflowStage.EVIDENCE_REVIEW,
            owner_package="bijux-proteomics-knowledge",
            artifact_paths=(evidence_review.artifact_path,),
            evidence_pointers=evidence_review.evidence_pointers,
            note=evidence_review.note,
        ),
        CanonicalWorkflowStageProof(
            stage=CanonicalWorkflowStage.DECISION_REVIEW,
            owner_package="bijux-proteomics-intelligence",
            artifact_paths=(decision_review.artifact_path,),
            evidence_pointers=("intelligence.flagship.decision_review",),
            note=decision_review.note,
        ),
        CanonicalWorkflowStageProof(
            stage=CanonicalWorkflowStage.LAB_HANDOFF,
            owner_package="bijux-proteomics-runtime",
            artifact_paths=lab_handoff.artifact_paths,
            evidence_pointers=lab_handoff.evidence_pointers,
            note=lab_handoff.note,
        ),
        CanonicalWorkflowStageProof(
            stage=CanonicalWorkflowStage.FOLLOW_UP,
            owner_package="bijux-proteomics-lab",
            artifact_paths=(follow_up.artifact_path, follow_up.next_cycle_artifact_path),
            evidence_pointers=("lab.canonical.follow_up", "lab.canonical.next_cycle"),
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
        "This bundle is the one checked canonical workflow family. It proves a narrow "
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
    return CanonicalWorkflowProofBundle(
        workflow_id=workflow_id,
        scope_dossier=scope_dossier,
        stages=stages,
        artifact_claims=artifact_claims,
        proof_digest=_stable_sha256(payload),
        proof_complete=proof_complete,
        note=note,
    )


def compare_canonical_workflow_proof_bundles(
    baseline: CanonicalWorkflowProofBundle,
    candidate: CanonicalWorkflowProofBundle,
) -> CanonicalWorkflowDeterminismReport:
    """Compare two canonical workflow proof bundles deterministically."""

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

    return CanonicalWorkflowDeterminismReport(
        workflow_id=baseline.workflow_id,
        equivalent=not changed_fields,
        changed_fields=tuple(changed_fields),
        note=(
            "Equivalent bundles may be described as deterministic re-generation for the flagship workflow family."
            if not changed_fields
            else "The canonical proof bundle changed across repeated builds."
        ),
    )


def evaluate_canonical_workflow_breakage(
    bundle: CanonicalWorkflowProofBundle,
) -> CanonicalWorkflowBreakageReport:
    """Detect structural breakage in the canonical workflow proof set."""

    findings: list[CanonicalWorkflowBreakageFinding] = []
    required_stages = set(CanonicalWorkflowStage)
    observed_stages = {stage.stage for stage in bundle.stages}
    missing_stages = sorted(stage.value for stage in required_stages - observed_stages)
    if missing_stages:
        findings.append(
            CanonicalWorkflowBreakageFinding(
                code="missing_owner_stage",
                message="missing canonical owner stages: " + ", ".join(missing_stages),
                blocking=True,
            )
        )
    for claim in bundle.artifact_claims:
        if not claim.artifact_path.startswith("artifacts/"):
            findings.append(
                CanonicalWorkflowBreakageFinding(
                    code="artifact_path_outside_artifacts",
                    message=f"claim {claim.claim_id} points outside artifacts/",
                    blocking=True,
                )
            )
        if "::" not in claim.validating_test_id:
            findings.append(
                CanonicalWorkflowBreakageFinding(
                    code="missing_validating_test",
                    message=f"claim {claim.claim_id} has no pytest node id",
                    blocking=True,
                )
            )
    claim_kinds = {claim.claim_kind for claim in bundle.artifact_claims}
    if WorkflowClaimKind.REPLAY not in claim_kinds:
        findings.append(
            CanonicalWorkflowBreakageFinding(
                code="missing_replay_claim",
                message="canonical workflow proof set no longer carries a replay claim",
                blocking=True,
            )
        )
    if WorkflowClaimKind.INTEGRITY not in claim_kinds:
        findings.append(
            CanonicalWorkflowBreakageFinding(
                code="missing_integrity_claim",
                message="canonical workflow proof set no longer carries an integrity claim",
                blocking=True,
            )
        )
    return CanonicalWorkflowBreakageReport(
        workflow_id=bundle.workflow_id,
        valid=not findings,
        findings=tuple(findings),
    )
