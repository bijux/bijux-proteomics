# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime-owned flagship run bundles and registry surfaces."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import tempfile

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.workflows.benchmark_runs import (
    BenchmarkFailureRecoveryBundle,
    BenchmarkRunMode,
    BenchmarkRunSpec,
    BenchmarkRuntimeTruthRow,
    build_benchmark_artifact_browser,
    build_benchmark_failure_recovery_bundle,
    build_benchmark_run_specs,
    build_benchmark_runtime_truth_surface,
    run_benchmark_dda_import_path,
    run_benchmark_dia_import_path,
    run_benchmark_lfq_review_path,
    run_benchmark_multiplex_review_path,
    run_benchmark_ptm_review_path,
    run_benchmark_targeted_review_path,
)
from bijux_proteomics_runtime.workflows.proof_classes import RuntimeProofClass

__all__ = [
    "FlagshipCrossFamilyRunBundle",
    "FlagshipRunArtifact",
    "FlagshipRunBundle",
    "FlagshipRunFailureReplayArtifact",
    "FlagshipRunFailureReplayCase",
    "FlagshipRunRegistry",
    "FlagshipRunRegistryEntry",
    "FlagshipRunStageLineageArtifact",
    "FlagshipRunStageLineageEntry",
    "FlagshipRuntimeSurfaceSnapshot",
    "build_flagship_cross_family_run_bundle",
    "build_flagship_run_bundle",
    "build_flagship_run_bundle_family",
    "build_flagship_run_failure_replay",
    "build_flagship_run_registry",
    "build_flagship_run_stage_lineage",
]

_FAMILY_ORDER: tuple[str, ...] = (
    "dda",
    "dia",
    "lfq",
    "multiplex",
    "ptm",
    "targeted",
)

_FIXTURE_ROOT = (
    "packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs"
)


class FlagshipRunArtifact(JsonModel):
    """One stable artifact link inside a flagship runtime bundle."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1)
    owner_package: str = Field(..., min_length=1)
    artifact_role: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    review_purpose: str = Field(..., min_length=1)


class FlagshipRuntimeSurfaceSnapshot(JsonModel):
    """Stable summary of one runtime-owned flagship execution surface."""

    model_config = ConfigDict(extra="forbid")

    surface_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    runtime_package_id: str = Field(..., min_length=1)
    run_mode: BenchmarkRunMode
    proof_class: RuntimeProofClass
    canonical_entrypoint: str = Field(..., min_length=1)
    toolchain_or_import_path: str = Field(..., min_length=1)
    input_artifact_ids: tuple[str, ...] = Field(default_factory=tuple)
    runtime_artifact_ids: tuple[str, ...] = Field(default_factory=tuple)
    execution_summary: tuple[str, ...] = Field(default_factory=tuple)
    validating_test_paths: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipRunStageLineageEntry(JsonModel):
    """One stable runtime stage lineage edge."""

    model_config = ConfigDict(extra="forbid")

    stage_id: str = Field(..., min_length=1)
    owner_package: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    consumed_artifact_ids: tuple[str, ...] = Field(default_factory=tuple)
    produced_artifact_ids: tuple[str, ...] = Field(default_factory=tuple)


class FlagshipRunStageLineageArtifact(JsonModel):
    """Per-family lineage artifact for one flagship run bundle."""

    model_config = ConfigDict(extra="forbid")

    lineage_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    stages: tuple[FlagshipRunStageLineageEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipRunFailureReplayCase(JsonModel):
    """One explicit failure or invalidation replay case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)
    failure_kind: str = Field(..., min_length=1)
    surfaced_artifact_ids: tuple[str, ...] = Field(default_factory=tuple)
    blocked_artifact_ids: tuple[str, ...] = Field(default_factory=tuple)
    invalidation_reasons: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipRunFailureReplayArtifact(JsonModel):
    """Per-family failure replay artifact for flagship runtime execution."""

    model_config = ConfigDict(extra="forbid")

    replay_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    cases: tuple[FlagshipRunFailureReplayCase, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipRunBundle(JsonModel):
    """Full reviewable flagship runtime bundle for one workflow family."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    benchmark_id: str = Field(..., min_length=1)
    benchmark_package_id: str | None = None
    runtime_package_id: str = Field(..., min_length=1)
    runtime_surface: FlagshipRuntimeSurfaceSnapshot
    authorized_claim_scope: tuple[str, ...] = Field(default_factory=tuple)
    remaining_blockers: tuple[str, ...] = Field(default_factory=tuple)
    artifact_inventory: tuple[FlagshipRunArtifact, ...] = Field(default_factory=tuple)
    stage_lineage_artifact_path: str = Field(..., min_length=1)
    failure_replay_artifact_path: str = Field(..., min_length=1)
    linked_owner_artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    last_reproduced_on: date
    note: str = Field(..., min_length=1)


class FlagshipCrossFamilyRunBundle(JsonModel):
    """Cross-family bundle linking runtime proof to downstream owners."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    workflow_families: tuple[str, ...] = Field(default_factory=tuple)
    per_family_bundle_paths: tuple[str, ...] = Field(default_factory=tuple)
    core_artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    knowledge_artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    intelligence_artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    lab_artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipRunRegistryEntry(JsonModel):
    """Registry row for one checked flagship runtime run."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: str = Field(..., min_length=1)
    benchmark_id: str = Field(..., min_length=1)
    runtime_package_id: str = Field(..., min_length=1)
    proof_class: RuntimeProofClass
    bundle_artifact_path: str = Field(..., min_length=1)
    stage_lineage_artifact_path: str = Field(..., min_length=1)
    failure_replay_artifact_path: str = Field(..., min_length=1)
    toolchain_or_import_path: str = Field(..., min_length=1)
    last_reproduced_on: date
    authorized_claim_scope: tuple[str, ...] = Field(default_factory=tuple)
    remaining_blockers: tuple[str, ...] = Field(default_factory=tuple)


class FlagshipRunRegistry(JsonModel):
    """Registry of every flagship public runtime run."""

    model_config = ConfigDict(extra="forbid")

    registry_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[FlagshipRunRegistryEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def build_flagship_run_bundle_family(
    *,
    base_dir: Path | None = None,
) -> tuple[FlagshipRunBundle, ...]:
    """Build bundles for every flagship runtime workflow family."""

    return tuple(
        build_flagship_run_bundle(workflow_family, base_dir=base_dir)
        for workflow_family in _FAMILY_ORDER
    )


def build_flagship_run_bundle(
    workflow_family: str,
    *,
    base_dir: Path | None = None,
) -> FlagshipRunBundle:
    """Build one runtime-owned flagship run bundle."""

    if workflow_family not in _FAMILY_ORDER:
        raise ValueError(f"unsupported flagship workflow family: {workflow_family}")
    if base_dir is None:
        with tempfile.TemporaryDirectory(prefix=f"bijux-{workflow_family}-run-") as temp_dir:
            return _build_flagship_run_bundle(workflow_family, Path(temp_dir))
    return _build_flagship_run_bundle(workflow_family, base_dir)


def build_flagship_run_stage_lineage(
    workflow_family: str,
) -> FlagshipRunStageLineageArtifact:
    """Build the checked lineage artifact for one flagship runtime family."""

    spec = _runtime_spec_for_family(workflow_family)
    with tempfile.TemporaryDirectory(
        prefix=f"bijux-{workflow_family}-lineage-"
    ) as temp_dir:
        runtime_surface, _ = _runtime_surface_snapshot(
            workflow_family=workflow_family,
            spec=spec,
            base_dir=Path(temp_dir),
        )
    return _build_stage_lineage_artifact(
        workflow_family=workflow_family,
        spec=spec,
        runtime_artifact_ids=runtime_surface.runtime_artifact_ids,
    )


def build_flagship_run_failure_replay(
    workflow_family: str,
    *,
    base_dir: Path | None = None,
) -> FlagshipRunFailureReplayArtifact:
    """Build the checked failure replay artifact for one flagship runtime family."""

    spec = _runtime_spec_for_family(workflow_family)
    runtime_truth = _runtime_truth_for_family(spec.workflow_family)
    if base_dir is None:
        with tempfile.TemporaryDirectory(prefix=f"bijux-{workflow_family}-failure-") as temp_dir:
            return _build_failure_replay_artifact(
                workflow_family=workflow_family,
                spec=spec,
                runtime_truth=runtime_truth,
                base_dir=Path(temp_dir),
            )
    return _build_failure_replay_artifact(
        workflow_family=workflow_family,
        spec=spec,
        runtime_truth=runtime_truth,
        base_dir=base_dir,
    )


def build_flagship_cross_family_run_bundle(
    *,
    base_dir: Path | None = None,
) -> FlagshipCrossFamilyRunBundle:
    """Build the cross-family bundle that links runtime proof to downstream owners."""

    bundles = build_flagship_run_bundle_family(base_dir=base_dir)
    context = _downstream_context()
    return FlagshipCrossFamilyRunBundle(
        bundle_id="flagship-cross-family-run-bundle",
        artifact_path=f"{_FIXTURE_ROOT}/cross_family_run_bundle.json",
        workflow_families=tuple(bundle.workflow_family for bundle in bundles),
        per_family_bundle_paths=tuple(bundle.artifact_path for bundle in bundles),
        core_artifact_paths=tuple(
            dict.fromkeys(
                bundle.artifact_inventory[0].artifact_path
                for bundle in bundles
                if bundle.artifact_inventory
            )
        ),
        knowledge_artifact_paths=tuple(
            context["reading_pack_paths"][family] for family in _FAMILY_ORDER
        ),
        intelligence_artifact_paths=tuple(
            context["recommendation_paths"][family] for family in _FAMILY_ORDER
        ),
        lab_artifact_paths=tuple(
            context["lab_paths"][family] for family in _FAMILY_ORDER
        ),
        note=(
            "This bundle keeps the exact core, knowledge, intelligence, and lab artifacts visible beside the runtime-owned flagship run bundles so the workflow stops looking like adjacent islands."
        ),
    )


def build_flagship_run_registry(
    *,
    base_dir: Path | None = None,
) -> FlagshipRunRegistry:
    """Build the registry of checked flagship runtime runs."""

    bundles = build_flagship_run_bundle_family(base_dir=base_dir)
    entries = tuple(
        FlagshipRunRegistryEntry(
            workflow_family=bundle.workflow_family,
            benchmark_id=bundle.benchmark_id,
            runtime_package_id=bundle.runtime_package_id,
            proof_class=bundle.runtime_surface.proof_class,
            bundle_artifact_path=bundle.artifact_path,
            stage_lineage_artifact_path=bundle.stage_lineage_artifact_path,
            failure_replay_artifact_path=bundle.failure_replay_artifact_path,
            toolchain_or_import_path=bundle.runtime_surface.toolchain_or_import_path,
            last_reproduced_on=bundle.last_reproduced_on,
            authorized_claim_scope=bundle.authorized_claim_scope,
            remaining_blockers=bundle.remaining_blockers,
        )
        for bundle in bundles
    )
    return FlagshipRunRegistry(
        registry_id="flagship-runtime-run-registry",
        artifact_path=f"{_FIXTURE_ROOT}/runtime_run_registry.json",
        entries=entries,
        note=(
            "The registry records which flagship public runs exist, when they were last reproduced, what runtime path they used, what claims they authorize, and what blockers still limit broader trust."
        ),
    )


def _build_flagship_run_bundle(
    workflow_family: str,
    base_dir: Path,
) -> FlagshipRunBundle:
    context = _downstream_context()
    review = context["reviews"][workflow_family]
    recommendation = context["recommendations"][workflow_family]
    spec = _runtime_spec_for_family(workflow_family)
    runtime_truth = _runtime_truth_for_family(spec.workflow_family)

    runtime_surface, runtime_artifacts = _runtime_surface_snapshot(
        workflow_family=workflow_family,
        spec=spec,
        base_dir=base_dir / workflow_family,
    )
    stage_lineage = _build_stage_lineage_artifact(
        workflow_family=workflow_family,
        spec=spec,
        runtime_artifact_ids=runtime_surface.runtime_artifact_ids,
    )
    failure_replay = _build_failure_replay_artifact(
        workflow_family=workflow_family,
        spec=spec,
        runtime_truth=runtime_truth,
        base_dir=base_dir / f"{workflow_family}-failure",
    )
    artifact_inventory = (
        *_public_package_artifacts(spec),
        *_input_artifacts(spec),
        *runtime_artifacts,
    )
    return FlagshipRunBundle(
        bundle_id=f"flagship-run-bundle:{workflow_family}",
        artifact_path=f"{_FIXTURE_ROOT}/{workflow_family}/run_bundle.json",
        workflow_family=workflow_family,
        benchmark_id=review.benchmark_id,
        benchmark_package_id=review.benchmark_package_id,
        runtime_package_id=spec.package_id,
        runtime_surface=runtime_surface,
        authorized_claim_scope=review.authorized_claim_scope,
        remaining_blockers=_remaining_blockers(
            workflow_family=workflow_family,
            runtime_truth=runtime_truth,
            review_limits=review.scientific_limits,
            recommendation_blockers=recommendation.blocker_set,
        ),
        artifact_inventory=tuple(artifact_inventory),
        stage_lineage_artifact_path=stage_lineage.artifact_path,
        failure_replay_artifact_path=failure_replay.artifact_path,
        linked_owner_artifact_paths=(
            context["reading_pack_paths"][workflow_family],
            context["recommendation_paths"][workflow_family],
            context["lab_paths"][workflow_family],
        ),
        last_reproduced_on=date(2026, 5, 7),
        note=(
            "This bundle is the runtime-owned checked artifact set for the flagship public benchmark run, not a governance placeholder."
        ),
    )


def _runtime_surface_snapshot(
    *,
    workflow_family: str,
    spec: BenchmarkRunSpec,
    base_dir: Path,
) -> tuple[FlagshipRuntimeSurfaceSnapshot, tuple[FlagshipRunArtifact, ...]]:
    if workflow_family == "dda":
        manifest = run_benchmark_dda_import_path(base_dir)
        return _import_runtime_surface_snapshot(
            workflow_family=workflow_family,
            spec=spec,
            base_dir=base_dir,
            manifest=manifest,
        )
    if workflow_family == "dia":
        manifest = run_benchmark_dia_import_path(base_dir)
        return _import_runtime_surface_snapshot(
            workflow_family=workflow_family,
            spec=spec,
            base_dir=base_dir,
            manifest=manifest,
        )
    if workflow_family == "lfq":
        report = run_benchmark_lfq_review_path()
        return _report_runtime_surface_snapshot(
            workflow_family=workflow_family,
            spec=spec,
            report_summary=(
                f"feature_record_count={report.feature_record_count}",
                f"design_entry_count={report.design_entry_count}",
                f"condition_count={report.condition_count}",
                f"outlier_sample_count={report.outlier_sample_count}",
                f"review_bundle_hash={report.review_bundle_hash}",
            ),
            artifact_paths=report.artifact_paths,
            evidence_pointers=report.evidence_pointers,
        )
    if workflow_family == "multiplex":
        report = run_benchmark_multiplex_review_path()
        return _report_runtime_surface_snapshot(
            workflow_family=workflow_family,
            spec=spec,
            report_summary=(
                f"feature_record_count={report.feature_record_count}",
                f"multiplex_group_count={report.multiplex_group_count}",
                f"channel_count={report.channel_count}",
                f"reference_channel_count={report.reference_channel_count}",
                f"flagged_imbalance_count={report.flagged_imbalance_count}",
                f"carrier_effect_channel_count={report.carrier_effect_channel_count}",
            ),
            artifact_paths=report.artifact_paths,
            evidence_pointers=report.evidence_pointers,
        )
    if workflow_family == "ptm":
        report = run_benchmark_ptm_review_path()
        return _report_runtime_surface_snapshot(
            workflow_family=workflow_family,
            spec=spec,
            report_summary=(
                f"accepted_identification_count={report.accepted_identification_count}",
                f"mapped_site_count={report.mapped_site_count}",
                f"motif_window_count={report.motif_window_count}",
                f"occupancy_entry_count={report.occupancy_entry_count}",
                f"lab_packet_target_count={report.lab_packet_target_count}",
                f"unresolved_risk_count={report.unresolved_risk_count}",
            ),
            artifact_paths=report.artifact_paths,
            evidence_pointers=report.evidence_pointers,
        )
    report = run_benchmark_targeted_review_path()
    return _report_runtime_surface_snapshot(
        workflow_family=workflow_family,
        spec=spec,
        report_summary=(
            f"qc_point_count={report.qc_point_count}",
            f"approved_transition_count={report.approved_transition_count}",
            f"exploratory_transition_count={report.exploratory_transition_count}",
            f"refused_transition_count={report.refused_transition_count}",
            f"blocked_follow_up_count={report.blocked_follow_up_count}",
            f"observed_outcome_count={report.observed_outcome_count}",
        ),
        artifact_paths=report.artifact_paths,
        evidence_pointers=report.evidence_pointers,
    )


def _import_runtime_surface_snapshot(
    *,
    workflow_family: str,
    spec: BenchmarkRunSpec,
    base_dir: Path,
    manifest: object,
) -> tuple[FlagshipRuntimeSurfaceSnapshot, tuple[FlagshipRunArtifact, ...]]:
    runtime_manifest = manifest
    browser = build_benchmark_artifact_browser(
        base_dir,
        package_id=spec.package_id,
        manifest=runtime_manifest,
    )
    runtime_artifacts = tuple(
        FlagshipRunArtifact(
            artifact_id=f"{workflow_family}:{entry.artifact_kind}",
            owner_package="bijux-proteomics-runtime",
            artifact_role=entry.artifact_kind,
            artifact_path=_normalize_artifact_path(entry.path),
            review_purpose=entry.summary,
        )
        for entry in (
            *browser.imported_results,
            *browser.review_outputs,
            *browser.handoff_outputs,
        )
    )
    execution_summary = (
        browser.imported_results[0].summary if browser.imported_results else "no imported comparator payload",
        f"review_outputs={','.join(entry.artifact_kind for entry in browser.review_outputs)}",
        f"handoff_outputs={','.join(entry.artifact_kind for entry in browser.handoff_outputs)}",
    )
    surface = FlagshipRuntimeSurfaceSnapshot(
        surface_id=f"flagship-runtime-surface:{workflow_family}",
        workflow_family=workflow_family,
        runtime_package_id=spec.package_id,
        run_mode=spec.run_mode,
        proof_class=RuntimeProofClass.IMPORT_BACKED_EXECUTION,
        canonical_entrypoint=spec.canonical_entrypoint,
        toolchain_or_import_path=(
            f"{spec.engine_name}:{spec.engine_version}"
            if spec.engine_name and spec.engine_version
            else spec.display_name
        ),
        input_artifact_ids=tuple(
            artifact.artifact_id
            for artifact in (*_public_package_artifacts(spec), *_input_artifacts(spec))
            if artifact.artifact_role in {"primary_input", "companion_input"}
        ),
        runtime_artifact_ids=tuple(artifact.artifact_id for artifact in runtime_artifacts),
        execution_summary=execution_summary,
        validating_test_paths=spec.validating_test_paths,
        note=(
            "This runtime surface is normalized from a real import-path execution so the checked-in snapshot keeps runtime lineage visible without preserving random run ids or temporary absolute paths."
        ),
    )
    return surface, runtime_artifacts


def _report_runtime_surface_snapshot(
    *,
    workflow_family: str,
    spec: BenchmarkRunSpec,
    report_summary: tuple[str, ...],
    artifact_paths: tuple[str, ...],
    evidence_pointers: tuple[str, ...],
) -> tuple[FlagshipRuntimeSurfaceSnapshot, tuple[FlagshipRunArtifact, ...]]:
    runtime_artifacts = tuple(
        FlagshipRunArtifact(
            artifact_id=f"{workflow_family}:runtime:{index}",
            owner_package="bijux-proteomics-runtime",
            artifact_role="runtime-output",
            artifact_path=_normalize_artifact_path(path),
            review_purpose=(
                evidence_pointers[min(index - 1, len(evidence_pointers) - 1)]
                if evidence_pointers
                else "runtime output"
            ),
        )
        for index, path in enumerate(artifact_paths, start=1)
    )
    surface = FlagshipRuntimeSurfaceSnapshot(
        surface_id=f"flagship-runtime-surface:{workflow_family}",
        workflow_family=workflow_family,
        runtime_package_id=spec.package_id,
        run_mode=spec.run_mode,
        proof_class=(
            RuntimeProofClass.RAW_EXECUTION
            if spec.run_mode is BenchmarkRunMode.RAW_EXECUTABLE
            else RuntimeProofClass.IMPORT_BACKED_EXECUTION
        ),
        canonical_entrypoint=spec.canonical_entrypoint,
        toolchain_or_import_path=spec.display_name,
        input_artifact_ids=tuple(
            artifact.artifact_id
            for artifact in (*_public_package_artifacts(spec), *_input_artifacts(spec))
            if artifact.artifact_role in {"primary_input", "companion_input"}
        ),
        runtime_artifact_ids=tuple(artifact.artifact_id for artifact in runtime_artifacts),
        execution_summary=report_summary,
        validating_test_paths=spec.validating_test_paths,
        note=(
            "This runtime surface is built from a tracked end-to-end runtime report rather than an imported comparator workspace."
        ),
    )
    return surface, runtime_artifacts


def _build_stage_lineage_artifact(
    *,
    workflow_family: str,
    spec: BenchmarkRunSpec,
    runtime_artifact_ids: tuple[str, ...],
) -> FlagshipRunStageLineageArtifact:
    input_ids = tuple(
        artifact.artifact_id for artifact in (*_public_package_artifacts(spec), *_input_artifacts(spec))
        if artifact.artifact_role in {"primary_input", "companion_input"}
    )
    midpoint = max(1, len(runtime_artifact_ids) // 2)
    stages = (
        FlagshipRunStageLineageEntry(
            stage_id="ingest-package-inputs",
            owner_package="bijux-proteomics-runtime",
            summary="ingest the tracked flagship package inputs into the runtime lane",
            consumed_artifact_ids=input_ids,
            produced_artifact_ids=runtime_artifact_ids[:midpoint],
        ),
        FlagshipRunStageLineageEntry(
            stage_id="publish-runtime-review",
            owner_package="bijux-proteomics-runtime",
            summary="publish the reviewable runtime artifacts that downstream owners consume",
            consumed_artifact_ids=runtime_artifact_ids[:midpoint],
            produced_artifact_ids=runtime_artifact_ids[midpoint:],
        ),
    )
    return FlagshipRunStageLineageArtifact(
        lineage_id=f"flagship-stage-lineage:{workflow_family}",
        artifact_path=f"{_FIXTURE_ROOT}/{workflow_family}/stage_lineage.json",
        workflow_family=workflow_family,
        stages=stages,
        note=(
            "The lineage artifact keeps the input-to-output chain visible at the runtime stage boundary instead of hiding it behind generic bundle prose."
        ),
    )


def _build_failure_replay_artifact(
    *,
    workflow_family: str,
    spec: BenchmarkRunSpec,
    runtime_truth: BenchmarkRuntimeTruthRow,
    base_dir: Path,
) -> FlagshipRunFailureReplayArtifact:
    if workflow_family in {"dda", "dia"}:
        manifest = (
            run_benchmark_dda_import_path(base_dir)
            if workflow_family == "dda"
            else run_benchmark_dia_import_path(base_dir)
        )
        failure_bundle = build_benchmark_failure_recovery_bundle(
            base_dir,
            package_id=spec.package_id,
            manifest=manifest,
        )
        return _import_failure_replay_artifact(
            workflow_family=workflow_family,
            failure_bundle=failure_bundle,
        )
    return _report_failure_replay_artifact(
        workflow_family=workflow_family,
        runtime_truth=runtime_truth,
    )


def _import_failure_replay_artifact(
    *,
    workflow_family: str,
    failure_bundle: BenchmarkFailureRecoveryBundle,
) -> FlagshipRunFailureReplayArtifact:
    cases = (
        FlagshipRunFailureReplayCase(
            case_id=f"{workflow_family}:execution_failure",
            failure_kind="execution_failure",
            surfaced_artifact_ids=tuple(
                f"{workflow_family}:{kind}"
                for kind in failure_bundle.preserved_artifact_kinds
            ),
            blocked_artifact_ids=tuple(
                f"{workflow_family}:{kind}"
                for kind in failure_bundle.blocked_artifact_kinds
            ),
            invalidation_reasons=(),
            note="engineering failure keeps preserved runtime artifacts visible while naming which outputs become blocked",
        ),
        FlagshipRunFailureReplayCase(
            case_id=f"{workflow_family}:scientific_invalidation",
            failure_kind="scientific_invalidation",
            surfaced_artifact_ids=tuple(
                f"{workflow_family}:{kind}"
                for kind in failure_bundle.preserved_artifact_kinds
            ),
            blocked_artifact_ids=(),
            invalidation_reasons=failure_bundle.scientific_invalidation_reasons,
            note="scientific invalidation is recorded separately from filesystem corruption so reviewers can distinguish wrong assumptions from broken execution",
        ),
        FlagshipRunFailureReplayCase(
            case_id=f"{workflow_family}:structurally_incomplete_import",
            failure_kind="structurally_incomplete_import",
            surfaced_artifact_ids=(f"{workflow_family}:runtime-imported-evidence",),
            blocked_artifact_ids=(
                f"{workflow_family}:runtime-evidence-bundle",
                f"{workflow_family}:runtime-review-packet",
            ),
            invalidation_reasons=("structurally_incomplete_imported_artifact",),
            note="if imported result tables are structurally incomplete, runtime keeps the import trace but blocks downstream review and handoff outputs",
        ),
    )
    return FlagshipRunFailureReplayArtifact(
        replay_id=f"flagship-failure-replay:{workflow_family}",
        artifact_path=f"{_FIXTURE_ROOT}/{workflow_family}/failure_replay.json",
        workflow_family=workflow_family,
        cases=cases,
        note=(
            "This artifact demonstrates how runtime distinguishes execution failure, scientific invalidation, and structurally incomplete imports on the flagship import lanes."
        ),
    )


def _report_failure_replay_artifact(
    *,
    workflow_family: str,
    runtime_truth: BenchmarkRuntimeTruthRow,
) -> FlagshipRunFailureReplayArtifact:
    cases = (
        FlagshipRunFailureReplayCase(
            case_id=f"{workflow_family}:execution_failure",
            failure_kind="execution_failure",
            surfaced_artifact_ids=(f"{workflow_family}:runtime:1",),
            blocked_artifact_ids=(f"{workflow_family}:runtime:4",),
            invalidation_reasons=(),
            note="runtime preserves early-stage evidence but blocks later review outputs when execution breaks mid-flight",
        ),
        FlagshipRunFailureReplayCase(
            case_id=f"{workflow_family}:scientific_invalidation",
            failure_kind="scientific_invalidation",
            surfaced_artifact_ids=(f"{workflow_family}:runtime:2",),
            blocked_artifact_ids=(),
            invalidation_reasons=runtime_truth.blocker_notes or ("scientific_limits_remain",),
            note="runtime still records the run, but the review posture is downgraded when the scientific assumptions or claim boundaries fail.",
        ),
        FlagshipRunFailureReplayCase(
            case_id=f"{workflow_family}:structurally_incomplete_input",
            failure_kind="structurally_incomplete_input",
            surfaced_artifact_ids=(f"{workflow_family}:primary_input",),
            blocked_artifact_ids=(f"{workflow_family}:runtime:3",),
            invalidation_reasons=("required_input_fields_missing",),
            note="runtime should name structurally incomplete inputs directly before downstream interpretation leaves the workflow boundary.",
        ),
    )
    return FlagshipRunFailureReplayArtifact(
        replay_id=f"flagship-failure-replay:{workflow_family}",
        artifact_path=f"{_FIXTURE_ROOT}/{workflow_family}/failure_replay.json",
        workflow_family=workflow_family,
        cases=cases,
        note=(
            "This artifact demonstrates how runtime records execution failure, scientific invalidation, and structurally incomplete inputs on the flagship review lanes."
        ),
    )


def _runtime_spec_for_family(workflow_family: str) -> BenchmarkRunSpec:
    mapping = {
        "dda": "dda_import",
        "dia": "dia_import",
        "lfq": "quant_review",
        "multiplex": "multiplex_review",
        "ptm": "ptm_review",
        "targeted": "targeted_review",
    }
    runtime_family = mapping[workflow_family]
    return next(
        spec for spec in build_benchmark_run_specs() if spec.workflow_family == runtime_family
    )


def _runtime_truth_for_family(workflow_family: str) -> BenchmarkRuntimeTruthRow:
    return next(
        row
        for row in build_benchmark_runtime_truth_surface()
        if row.workflow_family == workflow_family
    )


def _public_package_artifacts(spec: BenchmarkRunSpec) -> tuple[FlagshipRunArtifact, ...]:
    artifacts: list[FlagshipRunArtifact] = []
    for index, path in enumerate(spec.public_package_paths, start=1):
        artifacts.append(
            FlagshipRunArtifact(
                artifact_id=f"{spec.package_id}:public:{index}",
                owner_package=_owner_package(path),
                artifact_role="public_package_artifact",
                artifact_path=path,
                review_purpose="public package anchor for the flagship runtime run",
            )
        )
    return tuple(artifacts)


def _input_artifacts(spec: BenchmarkRunSpec) -> tuple[FlagshipRunArtifact, ...]:
    artifacts = [
        FlagshipRunArtifact(
            artifact_id=f"{spec.package_id}:primary_input",
            owner_package=_owner_package(spec.primary_input_path),
            artifact_role="primary_input",
            artifact_path=spec.primary_input_path,
            review_purpose="primary runtime input consumed by the flagship run",
        )
    ]
    artifacts.extend(
        FlagshipRunArtifact(
            artifact_id=f"{spec.package_id}:companion_input:{index}",
            owner_package=_owner_package(path),
            artifact_role="companion_input",
            artifact_path=path,
            review_purpose="companion runtime input needed for the flagship run",
        )
        for index, path in enumerate(spec.companion_input_paths, start=1)
    )
    return tuple(artifacts)


def _normalize_artifact_path(path: str) -> str:
    repo_root = _repo_root()
    artifact_path = Path(path)
    try:
        repo_relative = str(artifact_path.relative_to(repo_root))
        if repo_relative.startswith(("packages/", "docs/", "configs/")):
            return repo_relative
        return f"runtime-generated/{artifact_path.name}"
    except ValueError:
        return f"runtime-generated/{artifact_path.name}"


def _remaining_blockers(
    *,
    workflow_family: str,
    runtime_truth: BenchmarkRuntimeTruthRow,
    review_limits: tuple[str, ...],
    recommendation_blockers: tuple[str, ...],
) -> tuple[str, ...]:
    blockers = [
        *runtime_truth.blocker_notes,
        *review_limits[:2],
        *recommendation_blockers[:2],
    ]
    if workflow_family in {"lfq", "ptm", "targeted"}:
        blockers.append("release-facing trust remains narrower than runtime execution because comparator or grounding limits still apply")
    return tuple(dict.fromkeys(blockers))


def _downstream_context() -> dict[str, dict[str, object]]:
    from bijux_proteomics_intelligence.judgment.benchmark_corpora import (
        list_flagship_benchmark_reviews,
    )
    from bijux_proteomics_intelligence.judgment.benchmark_packets import (
        build_flagship_benchmark_recommendation_packet_family,
    )
    from bijux_proteomics_knowledge.references.workflows.benchmarks import (
        KnowledgeWorkflowFamily,
    )
    from bijux_proteomics_knowledge.references.workflows.reference_support import (
        get_benchmark_manifest_for_family,
    )
    from bijux_proteomics_knowledge.references.workflows.scientific_reading_packs import (
        build_workflow_scientific_reading_pack,
    )
    from bijux_proteomics_lab.benchmarks.follow_up import (
        build_flagship_lab_follow_up_packet_family,
        build_flagship_lab_review_board,
        build_flagship_minimum_controls_table,
    )

    families = {family.value: family for family in KnowledgeWorkflowFamily}
    manifests = {
        workflow_family: get_benchmark_manifest_for_family(family_enum)
        for workflow_family, family_enum in families.items()
    }
    reviews = {
        review.workflow_family.value: review
        for review in list_flagship_benchmark_reviews()
    }
    recommendations = {
        packet.workflow_family.value: packet
        for packet in build_flagship_benchmark_recommendation_packet_family().packets
    }
    reading_pack_paths = {
        workflow_family: (
            "artifacts/knowledge/scientific-reading-packs/"
            f"{build_workflow_scientific_reading_pack(family_enum).workflow_family.value}.json"
        )
        for workflow_family, family_enum in families.items()
    }
    lab_paths = {
        packet.workflow_family.value: packet.artifact_path
        for packet in build_flagship_lab_follow_up_packet_family().packets
    }
    minimum_controls = build_flagship_minimum_controls_table()
    review_board = build_flagship_lab_review_board()
    lab_paths["multiplex"] = minimum_controls.artifact_path
    lab_paths["targeted"] = lab_paths["targeted"]
    return {
        "manifests": manifests,
        "reviews": reviews,
        "recommendations": recommendations,
        "reading_pack_paths": reading_pack_paths,
        "recommendation_paths": {
            workflow_family: packet.artifact_path
            for workflow_family, packet in recommendations.items()
        },
        "lab_paths": {
            **lab_paths,
            "multiplex_review_board": review_board.artifact_path,
        },
    }


def _owner_package(repo_relative_path: str) -> str:
    if not repo_relative_path.startswith("packages/"):
        return "bijux-proteomics-docs"
    return repo_relative_path.split("/")[1]


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "configs").is_dir()
    )
