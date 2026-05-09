# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Independent rerun dossiers for outsider-auditable flagship workflows."""

from __future__ import annotations

from functools import lru_cache

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_runtime.workflows.benchmark_runs import (
    BenchmarkRunMode,
    BenchmarkRunSpec,
    BenchmarkRuntimeTruthRow,
    build_benchmark_run_specs,
    build_benchmark_runtime_truth_surface,
)

__all__ = [
    "IndependentRerunLane",
    "WorkflowIndependentRerunDossier",
    "WorkflowIndependentRerunDossierFamily",
    "build_workflow_independent_rerun_dossier",
    "build_workflow_independent_rerun_dossier_family",
]


_WORKFLOW_FAMILIES: tuple[KnowledgeWorkflowFamily, ...] = (
    KnowledgeWorkflowFamily.DDA,
    KnowledgeWorkflowFamily.DIA,
    KnowledgeWorkflowFamily.LFQ,
    KnowledgeWorkflowFamily.PTM,
    KnowledgeWorkflowFamily.TARGETED,
)


class IndependentRerunLane(JsonModel):
    """One benchmark package lane used in an independent rerun dossier."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    run_mode: BenchmarkRunMode
    canonical_entrypoint: str = Field(..., min_length=1)
    public_package_paths: tuple[str, ...] = Field(default_factory=tuple)
    validating_test_paths: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowIndependentRerunDossier(JsonModel):
    """One public dossier explaining how a workflow rerun can be challenged."""

    model_config = ConfigDict(extra="forbid")

    dossier_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    artifact_path: str = Field(..., min_length=1)
    flagship_lane: IndependentRerunLane
    companion_lane: IndependentRerunLane
    runtime_truth_workflow: str = Field(..., min_length=1)
    independence_question: str = Field(..., min_length=1)
    cross_environment_drift_visible: bool
    scrutiny_ready: bool
    public_opening_order: tuple[str, ...] = Field(default_factory=tuple)
    drift_questions: tuple[str, ...] = Field(default_factory=tuple)
    remaining_limits: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class WorkflowIndependentRerunDossierFamily(JsonModel):
    """Family of independent rerun dossiers across flagship workflows."""

    model_config = ConfigDict(extra="forbid")

    family_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    dossiers: tuple[WorkflowIndependentRerunDossier, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


@lru_cache(maxsize=1)
def _runtime_specs_by_package_id() -> dict[str, BenchmarkRunSpec]:
    return {spec.package_id: spec for spec in build_benchmark_run_specs()}


@lru_cache(maxsize=1)
def _runtime_truth_rows_by_workflow() -> dict[str, BenchmarkRuntimeTruthRow]:
    return {row.workflow_family: row for row in build_benchmark_runtime_truth_surface()}


def _rerun_package_ids(
    workflow_family: KnowledgeWorkflowFamily,
) -> tuple[str, str, str]:
    if workflow_family is KnowledgeWorkflowFamily.DDA:
        return (
            "dda_import",
            "dda-maxquant-pipeline-corpus",
            "dda-comet-cross-engine-corpus",
        )
    if workflow_family is KnowledgeWorkflowFamily.DIA:
        return (
            "dia_import",
            "dia-diann-pipeline-corpus",
            "dia-matrix-shift-review-corpus",
        )
    if workflow_family is KnowledgeWorkflowFamily.LFQ:
        return (
            "quant_review",
            "lfq-cohort-review-corpus",
            "lfq-sparse-contrast-review-corpus",
        )
    if workflow_family is KnowledgeWorkflowFamily.PTM:
        return (
            "ptm_review",
            "ptm-localization-review-corpus",
            "ptm-ambiguity-stress-review-corpus",
        )
    if workflow_family is KnowledgeWorkflowFamily.TARGETED:
        return (
            "targeted_review",
            "targeted-transition-review-corpus",
            "targeted-carryover-review-corpus",
        )
    raise ValueError(f"unsupported workflow family: {workflow_family.value}")


def _lane_from_spec(spec: BenchmarkRunSpec) -> IndependentRerunLane:
    return IndependentRerunLane(
        package_id=spec.package_id,
        workflow_family=spec.workflow_family,
        run_mode=spec.run_mode,
        canonical_entrypoint=spec.canonical_entrypoint,
        public_package_paths=spec.public_package_paths,
        validating_test_paths=spec.validating_test_paths,
        notes=spec.notes,
    )


def _independence_question(workflow_family: KnowledgeWorkflowFamily) -> str:
    if workflow_family is KnowledgeWorkflowFamily.DDA:
        return (
            "Do the outsider-facing DDA claims survive a second checked package with a different search-engine pairing instead of one convenient import lane?"
        )
    if workflow_family is KnowledgeWorkflowFamily.DIA:
        return (
            "Do the outsider-facing DIA claims survive a second execution lane with a different vendor-conditioned matrix surface?"
        )
    if workflow_family is KnowledgeWorkflowFamily.LFQ:
        return (
            "Do the outsider-facing LFQ claims survive a second cohort-shaped execution lane when the feature density gets sparser?"
        )
    if workflow_family is KnowledgeWorkflowFamily.PTM:
        return (
            "Do the outsider-facing PTM claims survive a harsher localization ambiguity lane instead of one clean flagship corpus?"
        )
    if workflow_family is KnowledgeWorkflowFamily.TARGETED:
        return (
            "Do the outsider-facing targeted claims survive a carryover and reuse pressure lane instead of one convenient transition package?"
        )
    raise ValueError(f"unsupported workflow family: {workflow_family.value}")


def _drift_questions(workflow_family: KnowledgeWorkflowFamily) -> tuple[str, ...]:
    if workflow_family is KnowledgeWorkflowFamily.DDA:
        return (
            "Does the imported DDA evidence stay interpretable when the primary engine changes from MaxQuant to Comet?",
            "Do the warning and cross-package generalization surfaces stay aligned across both checked public packages?",
        )
    if workflow_family is KnowledgeWorkflowFamily.DIA:
        return (
            "Does the DIA recommendation stay bounded when the companion package shifts matrix and vendor context?",
            "Do the primary and companion DIA lanes preserve the same semantic recommendation boundary under different exports?",
        )
    if workflow_family is KnowledgeWorkflowFamily.LFQ:
        return (
            "Does the LFQ recommendation stay bounded when cohort density and feature sparsity drift across environments?",
            "Do the same runtime summaries still stay interpretable when the companion package weakens the evidence shape?",
        )
    if workflow_family is KnowledgeWorkflowFamily.PTM:
        return (
            "Does the PTM localization posture stay bounded when the companion package injects harsher ambiguity pressure?",
            "Do the same review outputs remain stable when site-level ambiguity rather than one flagship corpus drives the evidence surface?",
        )
    if workflow_family is KnowledgeWorkflowFamily.TARGETED:
        return (
            "Does the targeted recommendation stay bounded when carryover and reuse pressure replace the flagship transition surface?",
            "Do calibration and interference limits remain visible when the companion package changes the stress shape of the same assay family?",
        )
    raise ValueError(f"unsupported workflow family: {workflow_family.value}")


def _remaining_limits(
    workflow_family: KnowledgeWorkflowFamily,
    primary_lane: IndependentRerunLane,
) -> tuple[str, ...]:
    limits = [
        "The dossier still describes repository-owned rerun lanes, not an untracked third-party reproduction outside the repository boundary.",
    ]
    if primary_lane.run_mode is BenchmarkRunMode.IMPORT_ONLY:
        limits.append(
            "The strongest shipped rerun lane is still import-backed rather than a raw external-engine execution owned by this repository."
        )
    else:
        limits.append(
            "The strongest shipped rerun lane is raw-executable inside the repository, but vendor-parity and broader ecosystem replay are still separate questions."
        )
    if workflow_family is KnowledgeWorkflowFamily.DIA:
        limits.append(
            "The companion DIA lane is still library-conditioned and should not be overstated as broad chromatogram-side independence."
        )
    if workflow_family is KnowledgeWorkflowFamily.LFQ:
        limits.append(
            "The companion LFQ lane shows cohort drift pressure, not broad multi-cohort transfer authority."
        )
    if workflow_family is KnowledgeWorkflowFamily.PTM:
        limits.append(
            "The companion PTM lane strengthens ambiguity pressure, not broad PTM-family coverage."
        )
    if workflow_family is KnowledgeWorkflowFamily.TARGETED:
        limits.append(
            "The companion targeted lane strengthens calibration and carryover stress, not vendor-parity proof."
        )
    return tuple(limits)


def build_workflow_independent_rerun_dossier(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowIndependentRerunDossier:
    """Build one public independent rerun dossier for a flagship workflow family."""

    runtime_workflow, flagship_package_id, companion_package_id = _rerun_package_ids(
        workflow_family
    )
    specs = _runtime_specs_by_package_id()
    runtime_truth = _runtime_truth_rows_by_workflow()[runtime_workflow]
    flagship_lane = _lane_from_spec(specs[flagship_package_id])
    companion_lane = _lane_from_spec(specs[companion_package_id])
    scrutiny_ready = (
        runtime_truth.run_mode is not BenchmarkRunMode.BLOCKED
        and bool(flagship_lane.validating_test_paths)
        and bool(companion_lane.validating_test_paths)
    )
    return WorkflowIndependentRerunDossier(
        dossier_id=f"independent_rerun:{workflow_family.value}",
        workflow_family=workflow_family,
        artifact_path=(
            "artifacts/intelligence/independent-reruns/"
            f"{workflow_family.value}_independent_rerun_dossier.json"
        ),
        flagship_lane=flagship_lane,
        companion_lane=companion_lane,
        runtime_truth_workflow=runtime_workflow,
        independence_question=_independence_question(workflow_family),
        cross_environment_drift_visible=True,
        scrutiny_ready=scrutiny_ready,
        public_opening_order=(
            flagship_lane.public_package_paths[0],
            companion_lane.public_package_paths[0],
            flagship_lane.validating_test_paths[0],
            companion_lane.validating_test_paths[0],
        ),
        drift_questions=_drift_questions(workflow_family),
        remaining_limits=_remaining_limits(workflow_family, flagship_lane),
        note=(
            "The dossier turns paired runtime lanes into one public rerun story so outsider-auditable wording depends less on internal release governance and more on a direct cross-package challenge path."
        ),
    )


def build_workflow_independent_rerun_dossier_family() -> WorkflowIndependentRerunDossierFamily:
    """Build independent rerun dossiers across flagship workflow families."""

    dossiers = tuple(
        build_workflow_independent_rerun_dossier(workflow_family)
        for workflow_family in _WORKFLOW_FAMILIES
    )
    return WorkflowIndependentRerunDossierFamily(
        family_id="flagship-independent-rerun-dossiers",
        artifact_path=(
            "artifacts/intelligence/independent-reruns/"
            "flagship_independent_rerun_dossiers.json"
        ),
        dossiers=dossiers,
        note=(
            "These dossiers do not pretend to be broad external reproduction; they make the repository's strongest paired rerun lanes explicit enough for hostile review."
        ),
    )
