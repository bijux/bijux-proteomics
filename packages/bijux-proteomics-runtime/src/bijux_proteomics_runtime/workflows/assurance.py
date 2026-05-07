# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Machine-readable workflow assurance surfaces for runtime-owned execution proof."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class WorkflowAssuranceTier(StrEnum):
    """How directly one workflow surface is proven in this repository."""

    CANONICAL_OPERATOR_EXECUTION = "canonical_operator_execution"
    REAL_INPUT_CORPUS = "real_input_corpus"
    EXTERNAL_NORMALIZATION_COMPATIBILITY = "external_normalization_compatibility"
    SIMULATION_CONTRACT = "simulation_contract"


@dataclass(frozen=True)
class WorkflowAssuranceLane:
    """One governed validation lane for a workflow family."""

    lane_id: str
    workflow_family: str
    assurance_tier: WorkflowAssuranceTier
    canonical_entrypoint: str
    repo_relative_fixture_paths: tuple[str, ...]
    validating_test_paths: tuple[str, ...]
    expected_surfaces: tuple[str, ...]
    command_hint: str
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanonicalOperatorPath:
    """One undeniable runtime-owned operator execution path."""

    path_id: str
    workflow_family: str
    entrypoint: str
    execution_mode: str
    repo_relative_input_paths: tuple[str, ...]
    validating_test_paths: tuple[str, ...]
    required_artifact_kinds: tuple[str, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkflowAssuranceMatrixRow:
    """Assurance summary for one runtime workflow family."""

    workflow_family: str
    canonical_operator_path_id: str | None
    real_lane_ids: tuple[str, ...]
    external_compatibility_pack_ids: tuple[str, ...]
    simulation_lane_ids: tuple[str, ...]
    blocker_notes: tuple[str, ...]
    notes: tuple[str, ...] = ()


def major_workflow_families() -> tuple[str, ...]:
    """Return the workflow families that must have non-simulation assurance."""

    return (
        "sequence_to_digest",
        "dda_import",
        "dia_import",
        "quant_review",
        "ptm_review",
    )


def build_canonical_operator_path() -> CanonicalOperatorPath:
    """Return the runtime-owned operator path that must stay undeniable."""

    return CanonicalOperatorPath(
        path_id="runtime-sequence-review-operator-path",
        workflow_family="sequence_to_digest",
        entrypoint="bijux_proteomics_runtime.workflows.paths.run_reviewable_sequence_path",
        execution_mode="cpu",
        repo_relative_input_paths=(
            "packages/bijux-proteomics-runtime/tests/fixtures/first_useful_run/proteins.fasta",
        ),
        validating_test_paths=(
            "packages/bijux-proteomics-runtime/tests/workflows/test_runtime_operator_path_surface.py",
        ),
        required_artifact_kinds=(
            "runtime-status",
            "runtime-report",
            "runtime-replay-contract",
            "runtime-integrity-report",
        ),
        notes=(
            "This path executes the real runtime run manager without monkeypatched fake flow helpers.",
            "The sequence input comes from a tracked fixture corpus rather than an inline synthetic payload.",
        ),
    )


def workflow_assurance_lanes() -> tuple[WorkflowAssuranceLane, ...]:
    """Return the governed workflow assurance lanes."""

    lanes = (
        WorkflowAssuranceLane(
            lane_id="sequence-operator-golden-path",
            workflow_family="sequence_to_digest",
            assurance_tier=WorkflowAssuranceTier.CANONICAL_OPERATOR_EXECUTION,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.paths.run_reviewable_sequence_path",
            repo_relative_fixture_paths=build_canonical_operator_path().repo_relative_input_paths,
            validating_test_paths=build_canonical_operator_path().validating_test_paths,
            expected_surfaces=build_canonical_operator_path().required_artifact_kinds,
            command_hint="run the focused runtime operator path surface test to exercise the canonical execution lane",
            notes=build_canonical_operator_path().notes,
        ),
        WorkflowAssuranceLane(
            lane_id="sequence-first-useful-corpus",
            workflow_family="sequence_to_digest",
            assurance_tier=WorkflowAssuranceTier.REAL_INPUT_CORPUS,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.runs.SequenceToDigestWorkflowRunReport",
            repo_relative_fixture_paths=(
                "packages/bijux-proteomics-runtime/tests/fixtures/first_useful_run/proteins.fasta",
                "packages/bijux-proteomics-runtime/tests/fixtures/first_useful_run/results.tsv",
                "packages/bijux-proteomics-runtime/tests/fixtures/first_useful_run/spectra.mgf",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_first_useful_run_surface.py",
            ),
            expected_surfaces=(
                "digestion",
                "psm-normalization",
                "fdr-filtering",
                "fragment-annotation",
            ),
            command_hint="first useful run fixtures prove the runtime workflow stays grounded in tracked corpus inputs",
        ),
        WorkflowAssuranceLane(
            lane_id="dda-maxquant-compatibility-pack",
            workflow_family="dda_import",
            assurance_tier=WorkflowAssuranceTier.EXTERNAL_NORMALIZATION_COMPATIBILITY,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.paths.run_reviewable_import_path",
            repo_relative_fixture_paths=(
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_evidence.tsv",
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv",
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_settings.txt",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_runtime_external_pack_surface.py",
                "packages/bijux-proteomics-core/tests/identification/test_search_adapter_maxquant_surface.py",
                "packages/bijux-proteomics-core/tests/identification/test_search_adapter_surface.py",
            ),
            expected_surfaces=(
                "runtime-import-trace",
                "runtime-import-run-bundle",
                "search-normalization",
                "parameter-provenance",
            ),
            command_hint="runtime import lineage and core adapter normalization tests jointly prove MaxQuant compatibility",
        ),
        WorkflowAssuranceLane(
            lane_id="dia-diann-compatibility-pack",
            workflow_family="dia_import",
            assurance_tier=WorkflowAssuranceTier.EXTERNAL_NORMALIZATION_COMPATIBILITY,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.paths.run_reviewable_import_path",
            repo_relative_fixture_paths=(
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_report.tsv",
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_pipeline_export.tsv",
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_config.json",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_runtime_external_pack_surface.py",
                "packages/bijux-proteomics-core/tests/identification/test_search_adapter_diann_surface.py",
                "packages/bijux-proteomics-core/tests/identification/test_search_adapter_surface.py",
            ),
            expected_surfaces=(
                "runtime-import-trace",
                "runtime-import-run-bundle",
                "dia-normalization",
                "quantified-precursor-import",
            ),
            command_hint="runtime import lineage and core DIA-NN normalization tests jointly prove DIA import compatibility",
        ),
        WorkflowAssuranceLane(
            lane_id="quant-production-corpus",
            workflow_family="quant_review",
            assurance_tier=WorkflowAssuranceTier.REAL_INPUT_CORPUS,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.runs.QuantRuntimeWorkflowRunReport",
            repo_relative_fixture_paths=(
                "packages/bijux-proteomics-runtime/tests/fixtures/production_run/ms1_features.tsv",
                "packages/bijux-proteomics-runtime/tests/fixtures/production_run/design.tsv",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_production_run_surface.py",
            ),
            expected_surfaces=(
                "feature-quantification",
                "experimental-design-ingestion",
                "qc-benchmark-manifest",
            ),
            command_hint="production run fixtures keep quant review tied to tracked feature and design corpora",
        ),
        WorkflowAssuranceLane(
            lane_id="ptm-localization-corpus",
            workflow_family="ptm_review",
            assurance_tier=WorkflowAssuranceTier.REAL_INPUT_CORPUS,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.runs.PtmRuntimeWorkflowRunReport",
            repo_relative_fixture_paths=(
                "packages/bijux-proteomics-runtime/tests/fixtures/ptm/localization_results.tsv",
                "packages/bijux-proteomics-runtime/tests/fixtures/ptm/ptm_features.tsv",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_runtime_external_pack_surface.py",
            ),
            expected_surfaces=(
                "localization-ingestion",
                "ptm-site-mapping",
                "occupancy-counterpart-review",
            ),
            command_hint="PTM localization fixtures keep runtime PTM review grounded in tracked evidence tables",
        ),
        WorkflowAssuranceLane(
            lane_id="simulated-external-engine-contract",
            workflow_family="external_engine_simulation",
            assurance_tier=WorkflowAssuranceTier.SIMULATION_CONTRACT,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.runs.build_simulated_external_engine_harness",
            repo_relative_fixture_paths=(),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_runtime_simulated_external_engine_surface.py",
            ),
            expected_surfaces=(
                "deterministic-simulation-report",
                "replay-cache-key",
            ),
            command_hint="simulation contract tests exist to pin deterministic harness behavior without confusing it for real workflow proof",
            notes=(
                "Simulation lanes are explicitly separated so release narratives do not overclaim fake tool execution as real validation.",
            ),
        ),
    )
    return tuple(sorted(lanes, key=lambda lane: lane.lane_id))


def build_workflow_assurance_matrix() -> tuple[WorkflowAssuranceMatrixRow, ...]:
    """Return workflow-family assurance posture over real, external, and simulated lanes."""

    canonical_operator_path = build_canonical_operator_path()
    lanes_by_family: dict[str, list[WorkflowAssuranceLane]] = {}
    for lane in workflow_assurance_lanes():
        lanes_by_family.setdefault(lane.workflow_family, []).append(lane)

    rows: list[WorkflowAssuranceMatrixRow] = []
    for workflow_family in (*major_workflow_families(), "external_engine_simulation"):
        family_lanes = lanes_by_family.get(workflow_family, [])
        real_lane_ids = tuple(
            sorted(
                lane.lane_id
                for lane in family_lanes
                if lane.assurance_tier
                in {
                    WorkflowAssuranceTier.CANONICAL_OPERATOR_EXECUTION,
                    WorkflowAssuranceTier.REAL_INPUT_CORPUS,
                }
            )
        )
        external_pack_lane_ids = tuple(
            sorted(
                lane.lane_id
                for lane in family_lanes
                if lane.assurance_tier
                is WorkflowAssuranceTier.EXTERNAL_NORMALIZATION_COMPATIBILITY
            )
        )
        simulation_lane_ids = tuple(
            sorted(
                lane.lane_id
                for lane in family_lanes
                if lane.assurance_tier is WorkflowAssuranceTier.SIMULATION_CONTRACT
            )
        )
        blocker_notes = ()
        if workflow_family in major_workflow_families() and not (
            real_lane_ids or external_pack_lane_ids
        ):
            blocker_notes = (
                "major workflow family lacks real operator, corpus, or external compatibility proof",
            )
        notes = ()
        if workflow_family == "external_engine_simulation":
            notes = (
                "simulation contract rows are explicit so they cannot be mistaken for real workflow validation",
            )
        elif workflow_family not in {"sequence_to_digest", "dda_import", "dia_import", "quant_review", "ptm_review"}:
            notes = (
                "downstream review and lab handoff surfaces are governed elsewhere and are not counted as major scientific workflow families here",
            )
        rows.append(
            WorkflowAssuranceMatrixRow(
                workflow_family=workflow_family,
                canonical_operator_path_id=(
                    canonical_operator_path.path_id
                    if workflow_family == canonical_operator_path.workflow_family
                    else None
                ),
                real_lane_ids=real_lane_ids,
                external_compatibility_pack_ids=external_pack_lane_ids,
                simulation_lane_ids=simulation_lane_ids,
                blocker_notes=blocker_notes,
                notes=notes,
            )
        )
    return tuple(rows)


def simulation_contract_lane_ids() -> tuple[str, ...]:
    """Return lane ids that are simulation-only rather than real workflow proof."""

    return tuple(
        sorted(
            lane.lane_id
            for lane in workflow_assurance_lanes()
            if lane.assurance_tier is WorkflowAssuranceTier.SIMULATION_CONTRACT
        )
    )


__all__ = [
    "CanonicalOperatorPath",
    "WorkflowAssuranceLane",
    "WorkflowAssuranceMatrixRow",
    "WorkflowAssuranceTier",
    "build_canonical_operator_path",
    "build_workflow_assurance_matrix",
    "major_workflow_families",
    "simulation_contract_lane_ids",
    "workflow_assurance_lanes",
]
