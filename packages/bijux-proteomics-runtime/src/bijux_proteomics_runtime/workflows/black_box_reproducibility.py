# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime-owned black-box reproducibility surfaces for flagship workflow families."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.workflows.benchmark_runs import (
    BenchmarkRunMode,
    BenchmarkRunSpec,
    BenchmarkRuntimeTruthRow,
    build_benchmark_run_specs,
    build_benchmark_runtime_truth_surface,
)
from bijux_proteomics_runtime.workflows.flagship_runs import (
    FlagshipRunRegistryEntry,
    build_flagship_run_failure_replay,
    build_flagship_run_registry,
)

__all__ = [
    "RuntimeArtifactStabilityEntry",
    "RuntimeBlackBoxVerificationRoute",
    "RuntimeBlackBoxRerunGate",
    "RuntimeBlackBoxRerunIssue",
    "RuntimeEnvironmentContract",
    "RuntimeExecutionModeComparison",
    "RuntimeReplayChallenge",
    "RuntimeRerunRefusalEntry",
    "build_runtime_artifact_stability_reports",
    "build_runtime_black_box_rerun_gate",
    "build_runtime_black_box_verification_routes",
    "build_runtime_environment_contracts",
    "build_runtime_execution_mode_comparisons",
    "build_runtime_replay_challenges",
    "build_runtime_rerun_refusals",
]

_FAMILY_ORDER = ("dda", "dia", "lfq", "multiplex", "ptm", "targeted")


class RuntimeBlackBoxVerificationRoute(JsonModel):
    """Shortest shipped path from a public benchmark asset to a runtime bundle."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: str = Field(..., min_length=1)
    benchmark_package_id: str = Field(..., min_length=1)
    benchmark_entry_artifact_path: str = Field(..., min_length=1)
    benchmark_source_manifest_path: str = Field(..., min_length=1)
    runtime_package_id: str = Field(..., min_length=1)
    canonical_entrypoint: str = Field(..., min_length=1)
    run_mode: BenchmarkRunMode
    runtime_bundle_artifact_path: str = Field(..., min_length=1)
    stage_lineage_artifact_path: str = Field(..., min_length=1)
    replay_artifact_path: str = Field(..., min_length=1)
    validating_test_paths: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class RuntimeBlackBoxRerunIssue(JsonModel):
    """One blocker on stronger black-box rerun authority for a workflow family."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    detail: str = Field(..., min_length=1)


class RuntimeBlackBoxRerunGate(JsonModel):
    """Release-facing black-box rerun gate over flagship runtime families."""

    model_config = ConfigDict(extra="forbid")

    gate_id: str = Field(..., min_length=1)
    blocked_workflow_families: tuple[str, ...] = Field(default_factory=tuple)
    evidence_paths: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[RuntimeBlackBoxRerunIssue, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class RuntimeExecutionModeComparison(JsonModel):
    """Family-level raw-versus-import execution boundary."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: str = Field(..., min_length=1)
    current_run_mode: BenchmarkRunMode
    imported_dependency_paths: tuple[str, ...] = Field(default_factory=tuple)
    raw_rerun_supported: bool
    mode_difference_summary: str = Field(..., min_length=1)
    blocked_claims: tuple[str, ...] = Field(default_factory=tuple)
    claim_guard: str = Field(..., min_length=1)


class RuntimeReplayChallenge(JsonModel):
    """Minimal clean-environment replay challenge for one workflow family."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: str = Field(..., min_length=1)
    runtime_package_id: str = Field(..., min_length=1)
    clean_environment_requirements: tuple[str, ...] = Field(default_factory=tuple)
    minimal_steps: tuple[str, ...] = Field(default_factory=tuple)
    expected_artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    invalidation_cases: tuple[str, ...] = Field(default_factory=tuple)
    current_limit: str = Field(..., min_length=1)


class RuntimeEnvironmentContract(JsonModel):
    """Supported and unsupported environment combinations for one family."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: str = Field(..., min_length=1)
    runtime_package_id: str = Field(..., min_length=1)
    required_tools: tuple[str, ...] = Field(default_factory=tuple)
    external_dependencies: tuple[str, ...] = Field(default_factory=tuple)
    supported_combinations: tuple[str, ...] = Field(default_factory=tuple)
    unsupported_combinations: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class RuntimeArtifactStabilityEntry(JsonModel):
    """Which runtime surfaces must remain stable across repeated reruns."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: str = Field(..., min_length=1)
    bit_stable_paths: tuple[str, ...] = Field(default_factory=tuple)
    value_stable_surfaces: tuple[str, ...] = Field(default_factory=tuple)
    review_stable_surfaces: tuple[str, ...] = Field(default_factory=tuple)
    permitted_environment_drift: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class RuntimeRerunRefusalEntry(JsonModel):
    """Current reasons a nominal family still cannot be rerun more faithfully."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: str = Field(..., min_length=1)
    rerun_ready: bool
    refusal_reasons: tuple[str, ...] = Field(default_factory=tuple)
    blocked_claims: tuple[str, ...] = Field(default_factory=tuple)
    next_evidence_paths: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def build_runtime_black_box_verification_routes() -> tuple[
    RuntimeBlackBoxVerificationRoute, ...
]:
    """Return the shipped public-to-runtime verification route per family."""

    routes: list[RuntimeBlackBoxVerificationRoute] = []
    for registry, spec, _truth in _family_records():
        benchmark_entry_artifact_path = _preferred_package_manifest(spec)
        routes.append(
            RuntimeBlackBoxVerificationRoute(
                workflow_family=registry.workflow_family,
                benchmark_package_id=spec.package_id,
                benchmark_entry_artifact_path=benchmark_entry_artifact_path,
                benchmark_source_manifest_path=str(
                    Path(benchmark_entry_artifact_path).with_name(
                        "source_locator_manifest.json"
                    )
                ),
                runtime_package_id=registry.runtime_package_id,
                canonical_entrypoint=spec.canonical_entrypoint,
                run_mode=spec.run_mode,
                runtime_bundle_artifact_path=registry.bundle_artifact_path,
                stage_lineage_artifact_path=registry.stage_lineage_artifact_path,
                replay_artifact_path=registry.failure_replay_artifact_path,
                validating_test_paths=spec.validating_test_paths,
                note=(
                    "Open the public benchmark manifest first, then the source locator, then the checked runtime bundle, stage lineage, and replay artifact. The route is meant to survive without maintainer narration."
                ),
            )
        )
    return tuple(routes)


def build_runtime_black_box_rerun_gate() -> RuntimeBlackBoxRerunGate:
    """Return the release-facing rerun gate anchored in black-box runtime surfaces."""

    from bijux_proteomics_runtime.workflows.proof_accounting import (
        build_runtime_flagship_proof_gate,
    )

    proof_gate = build_runtime_flagship_proof_gate()
    refusal_rows = build_runtime_rerun_refusals()
    blocked = set(proof_gate.blocked_workflow_families)
    issues = [
        RuntimeBlackBoxRerunIssue(
            workflow_family=issue.workflow_family,
            code=issue.code,
            detail=issue.detail,
        )
        for issue in proof_gate.issues
    ]
    for row in refusal_rows:
        if row.rerun_ready:
            continue
        blocked.add(row.workflow_family)
        issues.append(
            RuntimeBlackBoxRerunIssue(
                workflow_family=row.workflow_family,
                code="faithful-rerun-refused",
                detail=(
                    f"{row.workflow_family} still refuses stronger rerun claims: "
                    + "; ".join(row.refusal_reasons)
                ),
            )
        )
    return RuntimeBlackBoxRerunGate(
        gate_id="runtime-black-box-rerun-gate",
        blocked_workflow_families=tuple(sorted(blocked)),
        evidence_paths=(
            "packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/black_box_reproducibility.py",
            "docs/09-bijux-proteomics-runtime/runtime-execution-boundary.md",
            "docs/09-bijux-proteomics-runtime/black-box-run-verification.md",
            "docs/09-bijux-proteomics-runtime/raw-versus-import-execution.md",
            "docs/09-bijux-proteomics-runtime/runtime-replay-challenges.md",
            "docs/09-bijux-proteomics-runtime/runtime-environment-contracts.md",
            "docs/09-bijux-proteomics-runtime/runtime-artifact-stability.md",
            "docs/09-bijux-proteomics-runtime/runtime-rerun-refusals.md",
        ),
        issues=tuple(issues),
        note=(
            "A workflow family cannot count toward stronger black-box rerun authority when the shipped route still depends on fake helpers, simulation-only execution, or an explicit faithful-rerun refusal."
        ),
    )


def build_runtime_execution_mode_comparisons() -> tuple[
    RuntimeExecutionModeComparison, ...
]:
    """Return the raw-versus-import boundary for every flagship family."""

    comparisons: list[RuntimeExecutionModeComparison] = []
    for registry, spec, truth in _family_records():
        blocked_claims, claim_guard = _mode_guardrails(
            registry.workflow_family, spec, truth
        )
        comparisons.append(
            RuntimeExecutionModeComparison(
                workflow_family=registry.workflow_family,
                current_run_mode=spec.run_mode,
                imported_dependency_paths=_imported_dependency_paths(spec),
                raw_rerun_supported=spec.run_mode is BenchmarkRunMode.RAW_EXECUTABLE,
                mode_difference_summary=_mode_difference_summary(
                    registry.workflow_family, spec
                ),
                blocked_claims=blocked_claims,
                claim_guard=claim_guard,
            )
        )
    return tuple(comparisons)


def build_runtime_replay_challenges() -> tuple[RuntimeReplayChallenge, ...]:
    """Return one clean-environment replay challenge per family."""

    challenges: list[RuntimeReplayChallenge] = []
    for registry, spec, _truth in _family_records():
        replay = build_flagship_run_failure_replay(registry.workflow_family)
        challenges.append(
            RuntimeReplayChallenge(
                workflow_family=registry.workflow_family,
                runtime_package_id=registry.runtime_package_id,
                clean_environment_requirements=_clean_environment_requirements(spec),
                minimal_steps=(
                    f"open `{_preferred_package_manifest(spec)}` to confirm the public benchmark package boundary",
                    f"run `{spec.canonical_entrypoint}` against `{spec.primary_input_path}`",
                    f"compare the emitted runtime bundle to `{registry.bundle_artifact_path}`",
                    f"challenge invalidation with `{registry.failure_replay_artifact_path}`",
                ),
                expected_artifact_paths=(
                    registry.bundle_artifact_path,
                    registry.stage_lineage_artifact_path,
                    registry.failure_replay_artifact_path,
                ),
                invalidation_cases=tuple(case.failure_kind for case in replay.cases),
                current_limit=_replay_limit(registry.workflow_family, spec),
            )
        )
    return tuple(challenges)


def build_runtime_environment_contracts() -> tuple[RuntimeEnvironmentContract, ...]:
    """Return the supported environment contract per flagship family."""

    contracts: list[RuntimeEnvironmentContract] = []
    for registry, spec, _truth in _family_records():
        contracts.append(
            RuntimeEnvironmentContract(
                workflow_family=registry.workflow_family,
                runtime_package_id=registry.runtime_package_id,
                required_tools=(
                    "python 3.11",
                    "uv",
                    "bijux-proteomics-runtime",
                    "tracked public benchmark package files",
                ),
                external_dependencies=_external_dependencies(spec),
                supported_combinations=_supported_combinations(
                    registry.workflow_family, spec
                ),
                unsupported_combinations=_unsupported_combinations(
                    registry.workflow_family, spec
                ),
                note=(
                    "The environment contract names which combinations the shipped runtime lane actually defends and which stronger combinations remain unsupported."
                ),
            )
        )
    return tuple(contracts)


def build_runtime_artifact_stability_reports() -> tuple[
    RuntimeArtifactStabilityEntry, ...
]:
    """Return the artifact-stability contract across repeated reruns."""

    entries: list[RuntimeArtifactStabilityEntry] = []
    for registry, spec, truth in _family_records():
        entries.append(
            RuntimeArtifactStabilityEntry(
                workflow_family=registry.workflow_family,
                bit_stable_paths=(
                    registry.bundle_artifact_path,
                    registry.stage_lineage_artifact_path,
                    registry.failure_replay_artifact_path,
                ),
                value_stable_surfaces=(
                    f"runtime package id `{registry.runtime_package_id}`",
                    f"run mode `{spec.run_mode.value}`",
                    f"remaining blockers `{'; '.join(truth.blocker_notes[:2]) if truth.blocker_notes else 'none'}`",
                ),
                review_stable_surfaces=(
                    "authorized claim scope in the runtime bundle",
                    "family-specific replay invalidation reasons",
                    "downstream owner links carried by the checked runtime bundle",
                ),
                permitted_environment_drift=(
                    "run_id",
                    "environment.environment_id",
                    "run_summary.artifacts_dir",
                ),
                note=(
                    "Bit-stable paths are checked fixture artifacts. Value-stable and review-stable surfaces may change wording only when the underlying runtime or scientific boundary changes in the same reviewable edit."
                ),
            )
        )
    return tuple(entries)


def build_runtime_rerun_refusals() -> tuple[RuntimeRerunRefusalEntry, ...]:
    """Return the current faithful-rerun refusal ledger per family."""

    refusals: list[RuntimeRerunRefusalEntry] = []
    routes = {
        route.workflow_family: route
        for route in build_runtime_black_box_verification_routes()
    }
    for registry, spec, truth in _family_records():
        refusal_reasons, blocked_claims = _refusal_details(
            registry.workflow_family,
            spec,
            truth,
        )
        refusals.append(
            RuntimeRerunRefusalEntry(
                workflow_family=registry.workflow_family,
                rerun_ready=not refusal_reasons,
                refusal_reasons=refusal_reasons,
                blocked_claims=blocked_claims,
                next_evidence_paths=(
                    routes[registry.workflow_family].benchmark_entry_artifact_path,
                    routes[registry.workflow_family].runtime_bundle_artifact_path,
                    routes[registry.workflow_family].replay_artifact_path,
                ),
                note=(
                    "The refusal ledger names exactly why a workflow family still stops short of a stronger rerun claim instead of letting maintainers narrate around the gap."
                ),
            )
        )
    return tuple(refusals)


def _family_records() -> tuple[
    tuple[FlagshipRunRegistryEntry, BenchmarkRunSpec, BenchmarkRuntimeTruthRow], ...
]:
    specs_by_id = {spec.package_id: spec for spec in build_benchmark_run_specs()}
    truth_by_workflow = {
        row.workflow_family: row for row in build_benchmark_runtime_truth_surface()
    }
    registry = build_flagship_run_registry()
    return tuple(
        (
            entry,
            specs_by_id[entry.runtime_package_id],
            truth_by_workflow[specs_by_id[entry.runtime_package_id].workflow_family],
        )
        for family in _FAMILY_ORDER
        for entry in registry.entries
        if entry.workflow_family == family
    )


def _preferred_package_manifest(spec: BenchmarkRunSpec) -> str:
    return next(
        path
        for path in spec.public_package_paths
        if path.endswith("package_manifest.json")
    )


def _imported_dependency_paths(spec: BenchmarkRunSpec) -> tuple[str, ...]:
    return tuple(
        path
        for path in (spec.primary_input_path, *spec.companion_input_paths)
        if path.endswith((".tsv", ".txt", ".json"))
    )


def _mode_difference_summary(workflow_family: str, spec: BenchmarkRunSpec) -> str:
    if spec.run_mode is BenchmarkRunMode.IMPORT_ONLY:
        return f"{workflow_family} currently reruns through imported exported-result evidence instead of a raw in-repository execution lane."
    return f"{workflow_family} executes inside the runtime package, but its benchmark package can still include imported or derived evidence that does not prove vendor-native parity."


def _mode_guardrails(
    workflow_family: str,
    spec: BenchmarkRunSpec,
    truth: BenchmarkRuntimeTruthRow,
) -> tuple[tuple[str, ...], str]:
    if spec.run_mode is BenchmarkRunMode.IMPORT_ONLY:
        return (
            (
                "raw external-engine parity",
                "vendor-native or engine-native reproducibility",
            ),
            (
                f"{workflow_family} must not be described as raw-executable while `{spec.package_id}` still runs in `{spec.run_mode.value}` mode."
            ),
        )
    if workflow_family == "dia":
        return (
            (
                "chromatogram-native DIA authority",
                "broad vendor-parity DIA replay",
            ),
            "DIA remains raw-executable in runtime terms, but the shipped package still stops short of chromatogram-native and vendor-parity claims.",
        )
    if workflow_family == "multiplex":
        return (
            ("outsider-auditable multiplex trust",),
            "Multiplex may rerun in runtime terms while still failing the stronger outsider-facing claim boundary.",
        )
    return (
        tuple(truth.blocker_notes[:2]),
        (
            f"{workflow_family} should keep its stronger sentence behind the current benchmark package and downstream consequence limits."
        ),
    )


def _clean_environment_requirements(spec: BenchmarkRunSpec) -> tuple[str, ...]:
    requirements = [
        "start from a clean working directory with no prior runtime artifacts",
        "use Python 3.11 and the repository-managed uv environment",
        f"open the tracked benchmark package rooted at `{Path(_preferred_package_manifest(spec)).parent.as_posix()}`",
    ]
    if spec.run_mode is BenchmarkRunMode.IMPORT_ONLY:
        requirements.append(
            "do not substitute a live external engine; the current faithful rerun path is the shipped imported-result lane"
        )
    return tuple(requirements)


def _replay_limit(workflow_family: str, spec: BenchmarkRunSpec) -> str:
    if spec.run_mode is BenchmarkRunMode.IMPORT_ONLY:
        return f"{workflow_family} replay is real for the shipped imported-result lane, but it still refuses broader raw-engine rerun claims."
    if workflow_family == "dia":
        return "DIA replay is real for the shipped runtime lane, but it still refuses chromatogram-native and broader vendor-parity claims."
    return f"{workflow_family} replay is real for the shipped runtime lane, but it still inherits the same benchmark and downstream claim limits as the checked bundle."


def _external_dependencies(spec: BenchmarkRunSpec) -> tuple[str, ...]:
    if spec.engine_name is None:
        return ("none beyond tracked repository inputs",)
    if spec.run_mode is BenchmarkRunMode.IMPORT_ONLY:
        return (
            f"tracked exported results from `{spec.engine_name}` {spec.engine_version or ''}".strip(),
            "no live external engine install is required for the shipped rerun lane",
        )
    return (
        "tracked benchmark package inputs only",
        f"reference awareness of `{spec.engine_name}` {spec.engine_version or ''} export semantics".strip(),
    )


def _supported_combinations(
    workflow_family: str, spec: BenchmarkRunSpec
) -> tuple[str, ...]:
    if spec.run_mode is BenchmarkRunMode.IMPORT_ONLY:
        return (
            "repository-managed python environment plus tracked imported benchmark exports",
        )
    if workflow_family == "dia":
        return (
            "repository-managed python environment plus tracked DIA report and comparator exports",
            "library-conditioned review over the shipped benchmark package",
        )
    return (
        "repository-managed python environment plus tracked benchmark package inputs",
    )


def _unsupported_combinations(
    workflow_family: str, spec: BenchmarkRunSpec
) -> tuple[str, ...]:
    if spec.run_mode is BenchmarkRunMode.IMPORT_ONLY:
        return (
            "claiming live external-engine parity from the shipped import lane",
            "claiming raw instrument-side rerun without new tracked inputs and runtime support",
        )
    if workflow_family == "dia":
        return (
            "claiming chromatogram-native or vendor-parity DIA authority",
            "treating library-conditioned exported reports as a substitute for raw acquisition replay",
        )
    if workflow_family == "multiplex":
        return (
            "claiming outsider-auditable multiplex authority from the current internal-support lane",
        )
    return (
        "claiming broader family authority than the shipped benchmark package and downstream consequence surfaces earn",
    )


def _refusal_details(
    workflow_family: str,
    spec: BenchmarkRunSpec,
    truth: BenchmarkRuntimeTruthRow,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if workflow_family == "dda":
        return (
            (
                "faithful rerun still stops at imported MaxQuant and comparator exports because the repository does not own a raw DDA search execution lane",
                "external-engine behavior remains proprietary or out-of-repository for the strongest DDA package",
            ),
            (
                "raw DDA search parity",
                "full outsider-auditable DDA rerun language",
            ),
        )
    if workflow_family == "dia":
        return (
            (
                "the shipped DIA lane is raw-executable in runtime terms but still depends on library-conditioned exported reports rather than chromatogram-native replay",
            ),
            (
                "chromatogram-native DIA parity",
                "broad vendor-parity DIA authority",
            ),
        )
    if workflow_family == "multiplex":
        return (
            (
                "multiplex remains below outsider-auditable trust because runtime rerun strength still outruns family-level consequence and challenge closure",
            ),
            ("outsider-auditable multiplex trust",),
        )
    if truth.blocker_notes:
        return (
            tuple(truth.blocker_notes[:2]),
            tuple(truth.blocker_notes[:2]),
        )
    return (), ()
