# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime-owned flagship benchmark package catalog and execution wrappers."""

from __future__ import annotations

import csv
from enum import StrEnum
import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.runs.contracts import RunContextContract
from bijux_proteomics_runtime.runs.ledger import RuntimeArtifactLedger
from bijux_proteomics_runtime.runs.recovery import (
    RuntimeFailureRecoveryAudit,
    build_runtime_failure_recovery_audit,
)
from bijux_proteomics_runtime.runs.replay import ReplayContract
from bijux_proteomics_runtime.runs.reruns import (
    PartialRerunPlan,
    build_partial_rerun_plan,
)
from bijux_proteomics_runtime.support.workspace import RunWorkspace
from bijux_proteomics_runtime.workflows.assurance import build_workflow_assurance_matrix
from bijux_proteomics_runtime.workflows.paths import (
    RuntimeReviewableOutputPath,
    run_reviewable_import_path,
    run_reviewable_sequence_path,
)
from bijux_proteomics_runtime.workflows.proof_classes import RuntimeProofClass
from bijux_proteomics_runtime.workflows.runs import (
    DiaImportWorkflowRunReport,
    DiaPrecursorQuantInput,
    MultiplexRuntimeWorkflowRunReport,
    PtmRuntimeWorkflowRunReport,
    QuantRuntimeWorkflowRunReport,
    TargetedRuntimeWorkflowRunReport,
    run_dia_import_workflow_end_to_end,
    run_multiplex_workflow_end_to_end,
    run_ptm_workflow_end_to_end,
    run_quant_workflow_end_to_end,
    run_targeted_workflow_end_to_end,
)


class BenchmarkRunMode(StrEnum):
    """Execution posture for one runtime benchmark package."""

    RAW_EXECUTABLE = "raw_executable"
    IMPORT_ONLY = "import_only"
    BLOCKED = "blocked"


class BenchmarkRunSpec(JsonModel):
    """One runtime-owned benchmark package specification."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    run_mode: BenchmarkRunMode
    canonical_entrypoint: str = Field(..., min_length=1)
    primary_input_path: str = Field(..., min_length=1)
    companion_input_paths: tuple[str, ...] = Field(default_factory=tuple)
    engine_name: str | None = Field(default=None)
    engine_version: str | None = Field(default=None)
    public_package_paths: tuple[str, ...] = Field(default_factory=tuple)
    validating_test_paths: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkRuntimeTruthRow(JsonModel):
    """Honest runtime truth posture for one flagship benchmark package."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    run_mode: BenchmarkRunMode
    proof_class: RuntimeProofClass | None = Field(default=None)
    replayable: bool
    externally_cross_checked: bool
    artifact_browser_ready: bool
    blocker_notes: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkArtifactEntry(JsonModel):
    """Human-readable artifact row for runtime benchmark inspection."""

    model_config = ConfigDict(extra="forbid")

    artifact_kind: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    sha256: str = Field(..., min_length=64, max_length=64)
    summary: str = Field(..., min_length=1)
    preview_lines: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkArtifactBrowser(JsonModel):
    """Reviewable benchmark artifact browser for one runtime run."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    command: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    parameter_choices: tuple[str, ...] = Field(default_factory=tuple)
    public_package_artifacts: tuple[BenchmarkArtifactEntry, ...] = Field(
        default_factory=tuple
    )
    input_artifacts: tuple[BenchmarkArtifactEntry, ...] = Field(default_factory=tuple)
    imported_results: tuple[BenchmarkArtifactEntry, ...] = Field(default_factory=tuple)
    review_outputs: tuple[BenchmarkArtifactEntry, ...] = Field(default_factory=tuple)
    handoff_outputs: tuple[BenchmarkArtifactEntry, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkReplayDecision(JsonModel):
    """One replay scenario over a runtime benchmark package."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    eligible: bool
    invalidation_reasons: tuple[str, ...] = Field(default_factory=tuple)
    reused_nodes: tuple[str, ...] = Field(default_factory=tuple)
    rerun_nodes: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkReplayAudit(JsonModel):
    """Replay and invalidation posture for one runtime benchmark run."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    exact_reuse: BenchmarkReplayDecision
    tool_change: BenchmarkReplayDecision
    input_change: BenchmarkReplayDecision


class BenchmarkFailureRecoveryBundle(JsonModel):
    """Engineering-failure and scientific-invalidation split for one run."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    engineering_recovery: RuntimeFailureRecoveryAudit
    scientific_invalidation_reasons: tuple[str, ...] = Field(default_factory=tuple)
    preserved_artifact_kinds: tuple[str, ...] = Field(default_factory=tuple)
    blocked_artifact_kinds: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkDigestRecord(JsonModel):
    """One input or artifact digest entry used by provenance reports."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    sha256: str = Field(..., min_length=64, max_length=64)


class BenchmarkRunProvenanceReport(JsonModel):
    """Exact provenance surface for one runtime benchmark run."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    command: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    proof_class: RuntimeProofClass
    runtime_app_version: str = Field(..., min_length=1)
    runtime_git_commit: str = Field(..., min_length=1)
    provider_name: str = Field(..., min_length=1)
    provider_version: str | None = Field(default=None)
    external_engine_name: str | None = Field(default=None)
    external_engine_version: str | None = Field(default=None)
    parameter_choices: tuple[str, ...] = Field(default_factory=tuple)
    input_digests: tuple[BenchmarkDigestRecord, ...] = Field(default_factory=tuple)
    artifact_digests: tuple[BenchmarkDigestRecord, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkCostArtifact(JsonModel):
    """One cost-relevant runtime artifact."""

    model_config = ConfigDict(extra="forbid")

    artifact_kind: str = Field(..., min_length=1)
    size_bytes: int = Field(..., ge=0)


class BenchmarkExecutionCostReport(JsonModel):
    """Execution-cost realism surface for one runtime benchmark run."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    wall_time_ms: float = Field(..., ge=0.0)
    cost_metrics: dict[str, float] = Field(default_factory=dict)
    total_artifact_bytes: int = Field(..., ge=0)
    largest_artifacts: tuple[BenchmarkCostArtifact, ...] = Field(default_factory=tuple)
    critical_bottlenecks: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkPortabilityCheck(JsonModel):
    """Portability result across two runtime environments."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    primary_run_id: str = Field(..., min_length=1)
    secondary_run_id: str = Field(..., min_length=1)
    semantic_signature_match: bool
    environment_specific_differences: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


def build_benchmark_run_specs() -> tuple[BenchmarkRunSpec, ...]:
    """Return the runtime-owned flagship benchmark packages."""
    return (
        BenchmarkRunSpec(
            package_id="sequence-first-useful-corpus",
            display_name="sequence first useful corpus",
            workflow_family="sequence_to_digest",
            run_mode=BenchmarkRunMode.RAW_EXECUTABLE,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.paths.run_reviewable_sequence_path",
            primary_input_path="packages/bijux-proteomics-runtime/tests/fixtures/first_useful_run/proteins.fasta",
            companion_input_paths=(
                "packages/bijux-proteomics-runtime/tests/fixtures/first_useful_run/results.tsv",
                "packages/bijux-proteomics-runtime/tests/fixtures/first_useful_run/spectra.mgf",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_runtime_operator_path_surface.py",
            ),
            notes=(
                "runtime executes this corpus directly instead of replaying a toy result payload",
            ),
        ),
        BenchmarkRunSpec(
            package_id="dda-maxquant-pipeline-corpus",
            display_name="dda maxquant pipeline corpus",
            workflow_family="dda_import",
            run_mode=BenchmarkRunMode.IMPORT_ONLY,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.paths.run_reviewable_import_path",
            primary_input_path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv",
            companion_input_paths=(
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_evidence.tsv",
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_settings.txt",
            ),
            engine_name="maxquant",
            engine_version="19.0",
            public_package_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/README.md",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/scientific_invariants.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/warning_demonstrations.json",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_runtime_external_pack_surface.py",
            ),
            notes=(
                "runtime imports the tracked MaxQuant export and keeps provenance explicit instead of pretending to execute MaxQuant",
                "the runtime DDA lane points directly to the shipped public package metadata and warning ledgers",
            ),
        ),
        BenchmarkRunSpec(
            package_id="dda-comet-cross-engine-corpus",
            display_name="dda comet cross engine corpus",
            workflow_family="dda_generalization_import",
            run_mode=BenchmarkRunMode.IMPORT_ONLY,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_dda_generalization_import_path",
            primary_input_path="packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/primary/comet_pipeline_export.tsv",
            companion_input_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/primary/comet.params",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/comparator/sage_pipeline_export.tsv",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/comparator/sage_config.json",
            ),
            engine_name="comet",
            engine_version="2024.01",
            public_package_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/README.md",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/package_manifest.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/quality_sheet.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/lifecycle.json",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py",
            ),
            notes=(
                "runtime imports the companion DDA export so family-level DDA trust is not tied to one MaxQuant-only package",
            ),
        ),
        BenchmarkRunSpec(
            package_id="dia-diann-pipeline-corpus",
            display_name="dia diann pipeline corpus",
            workflow_family="dia_import",
            run_mode=BenchmarkRunMode.RAW_EXECUTABLE,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_dia_review_path",
            primary_input_path="packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_report.tsv",
            companion_input_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_pipeline_export.tsv",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_settings.txt",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/comparator/diann_pipeline_export.tsv",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/comparator/diann_config.json",
            ),
            public_package_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/README.md",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/package_manifest.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/quality_sheet.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/lifecycle.json",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_runtime_external_pack_surface.py",
            ),
            notes=(
                "runtime executes the tracked DIA package directly from the flagship public package instead of treating DIA as import-only proof",
                "the raw-executable DIA lane preserves that the tracked package is library-conditioned and intensity-thin rather than inventing chromatogram-side certainty",
            ),
        ),
        BenchmarkRunSpec(
            package_id="dia-matrix-shift-review-corpus",
            display_name="dia matrix shift review corpus",
            workflow_family="dia_generalization_review",
            run_mode=BenchmarkRunMode.RAW_EXECUTABLE,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_dia_generalization_review_path",
            primary_input_path="packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/primary/diann_report.tsv",
            companion_input_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/primary/diann_pipeline_export.tsv",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/comparator/spectronaut_pipeline_export.tsv",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/comparator/spectronaut_settings.txt",
            ),
            public_package_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/README.md",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/package_manifest.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/quality_sheet.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/lifecycle.json",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py",
            ),
            notes=(
                "runtime executes the DIA companion package so matrix-conditioned family transfer can be checked directly",
            ),
        ),
        BenchmarkRunSpec(
            package_id="lfq-cohort-review-corpus",
            display_name="lfq cohort review corpus",
            workflow_family="quant_review",
            run_mode=BenchmarkRunMode.RAW_EXECUTABLE,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_lfq_review_path",
            primary_input_path="packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale_ms1_features.tsv",
            companion_input_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale.design.tsv",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/quant_reproducibility_manifest.json",
            ),
            public_package_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/README.md",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/package_manifest.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/quality_sheet.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/lifecycle.json",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_flagship_run_bundle_surface.py",
            ),
            notes=(
                "runtime executes the tracked LFQ feature and design corpus instead of leaving flagship LFQ as a blocked review-only posture",
            ),
        ),
        BenchmarkRunSpec(
            package_id="lfq-sparse-contrast-review-corpus",
            display_name="lfq sparse contrast review corpus",
            workflow_family="quant_generalization_review",
            run_mode=BenchmarkRunMode.RAW_EXECUTABLE,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_lfq_generalization_review_path",
            primary_input_path="packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/evidence/edge_case_ms1_features.tsv",
            companion_input_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/evidence/edge_case.design.tsv",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/evidence/sparse_reproducibility_manifest.json",
            ),
            public_package_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/README.md",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/package_manifest.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/quality_sheet.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/lifecycle.json",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py",
            ),
            notes=(
                "runtime executes the LFQ companion package so family transfer can be checked against a sparser cohort contrast",
            ),
        ),
        BenchmarkRunSpec(
            package_id="multiplex-tmtpro-review-corpus",
            display_name="multiplex tmtpro review corpus",
            workflow_family="multiplex_review",
            run_mode=BenchmarkRunMode.RAW_EXECUTABLE,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_multiplex_review_path",
            primary_input_path="packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/evidence/multiplex_ms1_features.tsv",
            companion_input_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/evidence/multiplex.design.tsv",
            ),
            public_package_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/README.md",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/package_manifest.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/quality_sheet.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/lifecycle.json",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_flagship_run_bundle_surface.py",
            ),
            notes=(
                "runtime executes the tracked multiplex TMTpro corpus and keeps channel-level downgrade pressure explicit",
            ),
        ),
        BenchmarkRunSpec(
            package_id="multiplex-channel-stress-review-corpus",
            display_name="multiplex channel stress review corpus",
            workflow_family="multiplex_generalization_review",
            run_mode=BenchmarkRunMode.RAW_EXECUTABLE,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_multiplex_generalization_review_path",
            primary_input_path="packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/evidence/multiplex_channel_stress_ms1_features.tsv",
            companion_input_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/evidence/multiplex_channel_stress.design.tsv",
            ),
            public_package_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/README.md",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/package_manifest.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/quality_sheet.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/lifecycle.json",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py",
            ),
            notes=(
                "runtime executes the multiplex stress package so internal-support-only posture is checked under stronger channel imbalance",
            ),
        ),
        BenchmarkRunSpec(
            package_id="ptm-localization-review-corpus",
            display_name="ptm localization review corpus",
            workflow_family="ptm_review",
            run_mode=BenchmarkRunMode.RAW_EXECUTABLE,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_ptm_review_path",
            primary_input_path="packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/localization_results.tsv",
            companion_input_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/ptm_features.tsv",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/ptm_sites.fasta",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/spectra.mgf",
            ),
            public_package_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/README.md",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/package_manifest.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/quality_sheet.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/lifecycle.json",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_flagship_run_bundle_surface.py",
            ),
            notes=(
                "runtime executes the tracked PTM localization corpus and keeps ambiguity and lab-targeting outputs reviewable inside the repository boundary",
            ),
        ),
        BenchmarkRunSpec(
            package_id="ptm-ambiguity-stress-review-corpus",
            display_name="ptm ambiguity stress review corpus",
            workflow_family="ptm_generalization_review",
            run_mode=BenchmarkRunMode.RAW_EXECUTABLE,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_ptm_generalization_review_path",
            primary_input_path="packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/evidence/localization_results.tsv",
            companion_input_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/evidence/ptm_features.tsv",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/evidence/ptm_sites.fasta",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/evidence/spectra.mgf",
            ),
            public_package_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/README.md",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/package_manifest.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/quality_sheet.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/lifecycle.json",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py",
            ),
            notes=(
                "runtime executes the PTM ambiguity-stress package so family transfer can be checked under harsher localization pressure",
            ),
        ),
        BenchmarkRunSpec(
            package_id="targeted-transition-review-corpus",
            display_name="targeted transition review corpus",
            workflow_family="targeted_review",
            run_mode=BenchmarkRunMode.RAW_EXECUTABLE,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_targeted_review_path",
            primary_input_path="packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/evidence/targeted_benchmark_qc.tsv",
            companion_input_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/follow_up/supported_targeted_follow_up.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/follow_up/failed_targeted_transition_follow_up.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/follow_up/refused_targeted_follow_up.json",
            ),
            public_package_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/README.md",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/package_manifest.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/quality_sheet.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/lifecycle.json",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_flagship_run_bundle_surface.py",
            ),
            notes=(
                "runtime executes the tracked targeted QC and follow-up artifacts directly from the flagship public package",
                "the raw-executable targeted lane still keeps calibration and interference limits explicit instead of inflating the package into vendor-parity proof",
            ),
        ),
        BenchmarkRunSpec(
            package_id="targeted-carryover-review-corpus",
            display_name="targeted carryover review corpus",
            workflow_family="targeted_generalization_review",
            run_mode=BenchmarkRunMode.RAW_EXECUTABLE,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_targeted_generalization_review_path",
            primary_input_path="packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/evidence/targeted_benchmark_qc.tsv",
            companion_input_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/follow_up/supported_targeted_follow_up.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/follow_up/failed_targeted_transition_follow_up.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/follow_up/refused_targeted_follow_up.json",
            ),
            public_package_paths=(
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/README.md",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/package_manifest.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/quality_sheet.json",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/lifecycle.json",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py",
            ),
            notes=(
                "runtime executes the targeted carryover package so family transfer can be checked under stronger calibration and reuse drift",
            ),
        ),
    )


def run_benchmark_sequence_path(
    base_dir: Path,
    *,
    artifacts_dir: Path | None = None,
) -> RuntimeReviewableOutputPath:
    """Execute the flagship raw runtime benchmark package."""
    spec = _spec_by_id("sequence-first-useful-corpus")
    return run_reviewable_sequence_path(
        base_dir,
        sequence=_sequence_from_fasta(_repo_root() / spec.primary_input_path),
        execution_mode="cpu",
        artifacts_dir=artifacts_dir,
    )


def run_benchmark_dda_import_path(
    base_dir: Path,
    *,
    artifacts_dir: Path | None = None,
) -> RuntimeReviewableOutputPath:
    """Import the flagship DDA comparator export into runtime lineage."""
    return _run_import_benchmark_path(
        base_dir,
        package_id="dda-maxquant-pipeline-corpus",
        artifacts_dir=artifacts_dir,
    )


def run_benchmark_dda_generalization_import_path(
    base_dir: Path,
    *,
    artifacts_dir: Path | None = None,
) -> RuntimeReviewableOutputPath:
    """Import the companion DDA export into runtime lineage."""

    return _run_import_benchmark_path(
        base_dir,
        package_id="dda-comet-cross-engine-corpus",
        artifacts_dir=artifacts_dir,
    )


def run_benchmark_dia_import_path(
    base_dir: Path,
    *,
    artifacts_dir: Path | None = None,
) -> RuntimeReviewableOutputPath:
    """Import the flagship DIA comparator export into runtime lineage."""
    return _run_import_benchmark_path(
        base_dir,
        package_id="dia-diann-pipeline-corpus",
        artifacts_dir=artifacts_dir,
    )


def run_benchmark_dia_review_path() -> DiaImportWorkflowRunReport:
    """Execute the flagship DIA review corpus from tracked public-package rows."""

    return run_dia_import_workflow_end_to_end(
        _load_flagship_dia_precursor_rows(),
        artifact_root="artifacts/workflows/flagship-dia-review",
    )


def run_benchmark_dia_generalization_review_path() -> DiaImportWorkflowRunReport:
    """Execute the companion DIA review corpus from tracked public-package rows."""

    return run_dia_import_workflow_end_to_end(
        _load_companion_dia_precursor_rows(),
        artifact_root="artifacts/workflows/generalization-dia-review",
    )


def run_benchmark_lfq_review_path() -> QuantRuntimeWorkflowRunReport:
    """Execute the flagship LFQ review corpus inside the runtime layer."""

    repo_root = _repo_root()
    features = parse_ms1_feature_table(
        repo_root
        / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale_ms1_features.tsv"
    ).accepted_records
    design_entries = parse_experimental_design_table(
        repo_root
        / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale.design.tsv"
    ).accepted_entries
    return run_quant_workflow_end_to_end(
        features,
        design_entries=design_entries,
        artifact_root="artifacts/workflows/flagship-lfq-review",
    )


def run_benchmark_lfq_generalization_review_path() -> QuantRuntimeWorkflowRunReport:
    """Execute the companion LFQ review corpus inside the runtime layer."""

    repo_root = _repo_root()
    features = parse_ms1_feature_table(
        repo_root
        / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/evidence/edge_case_ms1_features.tsv"
    ).accepted_records
    design_entries = parse_experimental_design_table(
        repo_root
        / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/evidence/edge_case.design.tsv"
    ).accepted_entries
    return run_quant_workflow_end_to_end(
        features,
        design_entries=design_entries,
        artifact_root="artifacts/workflows/generalization-lfq-review",
    )


def run_benchmark_multiplex_review_path() -> MultiplexRuntimeWorkflowRunReport:
    """Execute the flagship multiplex review corpus inside the runtime layer."""

    repo_root = _repo_root()
    features = parse_ms1_feature_table(
        repo_root
        / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/evidence/multiplex_ms1_features.tsv"
    ).accepted_records
    design_entries = parse_experimental_design_table(
        repo_root
        / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/evidence/multiplex.design.tsv"
    ).accepted_entries
    return run_multiplex_workflow_end_to_end(
        features,
        design_entries=design_entries,
        artifact_root="artifacts/workflows/flagship-multiplex-review",
    )


def run_benchmark_multiplex_generalization_review_path() -> MultiplexRuntimeWorkflowRunReport:
    """Execute the companion multiplex review corpus inside the runtime layer."""

    repo_root = _repo_root()
    features = parse_ms1_feature_table(
        repo_root
        / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/evidence/multiplex_channel_stress_ms1_features.tsv"
    ).accepted_records
    design_entries = parse_experimental_design_table(
        repo_root
        / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/evidence/multiplex_channel_stress.design.tsv"
    ).accepted_entries
    return run_multiplex_workflow_end_to_end(
        features,
        design_entries=design_entries,
        artifact_root="artifacts/workflows/generalization-multiplex-review",
    )


def run_benchmark_ptm_review_path() -> PtmRuntimeWorkflowRunReport:
    """Execute the flagship PTM review corpus inside the runtime layer."""

    repo_root = _repo_root()
    feature_records = parse_ms1_feature_table(
        repo_root
        / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/ptm_features.tsv"
    ).accepted_records
    fasta_report = parse_fasta_document(
        (
            repo_root
            / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/ptm_sites.fasta"
        ).read_text(encoding="utf-8"),
        mode=FastaParseMode.STRICT,
    )
    protein_sequences = {
        record.canonical_accession: record.residues
        for record in fasta_report.accepted_records
    }
    return run_ptm_workflow_end_to_end(
        repo_root
        / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/localization_results.tsv",
        protein_sequences=protein_sequences,
        feature_records=feature_records,
        artifact_root="artifacts/workflows/flagship-ptm-review",
    )


def run_benchmark_ptm_generalization_review_path() -> PtmRuntimeWorkflowRunReport:
    """Execute the companion PTM review corpus inside the runtime layer."""

    repo_root = _repo_root()
    feature_records = parse_ms1_feature_table(
        repo_root
        / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/evidence/ptm_features.tsv"
    ).accepted_records
    fasta_report = parse_fasta_document(
        (
            repo_root
            / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/evidence/ptm_sites.fasta"
        ).read_text(encoding="utf-8"),
        mode=FastaParseMode.STRICT,
    )
    protein_sequences = {
        record.canonical_accession: record.residues
        for record in fasta_report.accepted_records
    }
    return run_ptm_workflow_end_to_end(
        repo_root
        / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/evidence/localization_results.tsv",
        protein_sequences=protein_sequences,
        feature_records=feature_records,
        artifact_root="artifacts/workflows/generalization-ptm-review",
    )


def run_benchmark_targeted_review_path() -> TargetedRuntimeWorkflowRunReport:
    """Execute the flagship targeted review corpus inside the runtime layer."""

    repo_root = _repo_root()
    return run_targeted_workflow_end_to_end(
        repo_root
        / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/evidence/targeted_benchmark_qc.tsv",
        supported_follow_up_payload=_load_json_dict(
            repo_root
            / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/follow_up/supported_targeted_follow_up.json"
        ),
        failed_follow_up_payload=_load_json_dict(
            repo_root
            / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/follow_up/failed_targeted_transition_follow_up.json"
        ),
        refused_follow_up_payload=_load_json_dict(
            repo_root
            / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/follow_up/refused_targeted_follow_up.json"
        ),
        artifact_root="artifacts/workflows/flagship-targeted-review",
    )


def run_benchmark_targeted_generalization_review_path() -> TargetedRuntimeWorkflowRunReport:
    """Execute the companion targeted review corpus inside the runtime layer."""

    repo_root = _repo_root()
    return run_targeted_workflow_end_to_end(
        repo_root
        / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/evidence/targeted_benchmark_qc.tsv",
        supported_follow_up_payload=_load_json_dict(
            repo_root
            / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/follow_up/supported_targeted_follow_up.json"
        ),
        failed_follow_up_payload=_load_json_dict(
            repo_root
            / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/follow_up/failed_targeted_transition_follow_up.json"
        ),
        refused_follow_up_payload=_load_json_dict(
            repo_root
            / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/follow_up/refused_targeted_follow_up.json"
        ),
        artifact_root="artifacts/workflows/generalization-targeted-review",
    )


def build_benchmark_runtime_truth_surface() -> tuple[BenchmarkRuntimeTruthRow, ...]:
    """Return the honest runtime posture across flagship benchmark packages."""
    matrix = {row.workflow_family: row for row in build_workflow_assurance_matrix()}
    specs = {spec.workflow_family: spec for spec in build_benchmark_run_specs()}
    rows: list[BenchmarkRuntimeTruthRow] = []
    for workflow_family in (
        "sequence_to_digest",
        "dda_import",
        "dia_import",
        "quant_review",
        "multiplex_review",
        "ptm_review",
        "targeted_review",
    ):
        spec = specs.get(workflow_family)
        matrix_row = matrix.get(workflow_family)
        if spec is None:
            rows.append(
                BenchmarkRuntimeTruthRow(
                    package_id=f"{workflow_family}-blocked-runtime-path",
                    workflow_family=workflow_family,
                    run_mode=BenchmarkRunMode.BLOCKED,
                    proof_class=None,
                    replayable=False,
                    externally_cross_checked=False,
                    artifact_browser_ready=False,
                    blocker_notes=(matrix_row.blocker_notes if matrix_row is not None else ())
                    or (
                        "no flagship runtime benchmark path is wired for this workflow family yet",
                    ),
                    notes=matrix_row.notes if matrix_row is not None else (),
                )
            )
            continue
        rows.append(
            BenchmarkRuntimeTruthRow(
                package_id=spec.package_id,
                workflow_family=workflow_family,
                run_mode=spec.run_mode,
                proof_class=_proof_class_for_run_mode(spec.run_mode),
                replayable=True,
                externally_cross_checked=workflow_family in {"dda_import", "dia_import"},
                artifact_browser_ready=workflow_family in {"dda_import", "dia_import"},
                blocker_notes=matrix_row.blocker_notes if matrix_row is not None else (),
                notes=spec.notes + (matrix_row.notes if matrix_row is not None else ()),
            )
        )
    return tuple(rows)


def build_benchmark_artifact_browser(
    base_dir: Path,
    *,
    package_id: str,
    manifest: RuntimeReviewableOutputPath,
    artifacts_dir: Path | None = None,
) -> BenchmarkArtifactBrowser:
    """Build one human-readable artifact browser for a runtime benchmark run."""
    spec = _spec_by_id(package_id)
    workspace = RunWorkspace.for_run(
        base_dir,
        manifest.run_id,
        artifacts_root_override=artifacts_dir,
    )
    run_context = RunContextContract.load_json(workspace.run_context_path)
    replay_contract = ReplayContract.load_json(workspace.replay_contract_path)
    input_paths = (_repo_root() / spec.primary_input_path,) + tuple(
        _repo_root() / path for path in spec.companion_input_paths
    )
    imported_results = ()
    public_package_artifacts = tuple(
        _summarize_source_path(_repo_root() / path) for path in spec.public_package_paths
    )
    handoff_outputs: list[BenchmarkArtifactEntry] = []
    if manifest.import_trace_path is not None:
        imported_payload = _load_json_dict(
            workspace.artifact_items_dir / "imported_evidence.json"
        )
        imported_results = (
            _summarize_imported_payload(
                path=workspace.artifact_items_dir / "imported_evidence.json",
                imported_payload=imported_payload,
            ),
        )
        for path, artifact_kind in (
            (workspace.artifact_items_dir / "evidence_bundle.json", "runtime-evidence-bundle"),
            (workspace.artifact_items_dir / "review_packet.json", "runtime-review-packet"),
        ):
            if path.exists():
                handoff_outputs.append(
                    BenchmarkArtifactEntry(
                        artifact_kind=artifact_kind,
                        path=str(path),
                        sha256=_sha256(path),
                        summary=f"{artifact_kind} stays downstream-readable from the runtime import lane",
                        preview_lines=_preview_for_json(path),
                    )
                )
    return BenchmarkArtifactBrowser(
        package_id=package_id,
        run_id=manifest.run_id,
        command=manifest.command,
        workflow_family=manifest.workflow_family,
        parameter_choices=(
            f"provider_name={run_context.provider_name}",
            f"command={run_context.workflow.command}",
            f"config_fingerprint={run_context.config_fingerprint}",
            f"parameter_fingerprint={replay_contract.parameter_fingerprint}",
            f"tool_fingerprint={replay_contract.tool_fingerprint}",
        ),
        public_package_artifacts=public_package_artifacts,
        input_artifacts=tuple(_summarize_source_path(path) for path in input_paths),
        imported_results=imported_results,
        review_outputs=tuple(
            _summarize_runtime_output(path, artifact_kind)
            for path, artifact_kind in (
                (workspace.run_summary_path, "runtime-status"),
                (workspace.report_path, "runtime-report"),
                (workspace.replay_contract_path, "runtime-replay-contract"),
                (workspace.integrity_report_path, "runtime-integrity-report"),
            )
            if path.exists()
        ),
        handoff_outputs=tuple(handoff_outputs),
        notes=(
            "artifact browser surfaces reviewable runtime files without requiring a human to open raw run JSON by hand",
        ),
    )


def build_benchmark_replay_audit(
    base_dir: Path,
    *,
    package_id: str,
    manifest: RuntimeReviewableOutputPath,
    artifacts_dir: Path | None = None,
) -> BenchmarkReplayAudit:
    """Build replay and invalidation posture for one runtime benchmark run."""
    workspace = RunWorkspace.for_run(
        base_dir,
        manifest.run_id,
        artifacts_root_override=artifacts_dir,
    )
    run_context = RunContextContract.load_json(workspace.run_context_path)
    replay_contract = ReplayContract.load_json(workspace.replay_contract_path)
    artifact_ledger = RuntimeArtifactLedger.load_json(workspace.artifact_ledger_path)
    exact_plan = build_partial_rerun_plan(
        previous_run_context=run_context,
        previous_replay_contract=replay_contract,
        current_replay_contract=replay_contract,
        artifact_ledger=artifact_ledger,
    )
    tool_change_contract = replay_contract.model_copy(
        update={
            "tool_fingerprint": _stable_fingerprint(
                {
                    "provider_name": run_context.provider_name,
                    "tool_versions": {run_context.provider_name: "changed"},
                }
            )
        }
    )
    tool_change_plan = build_partial_rerun_plan(
        previous_run_context=run_context,
        previous_replay_contract=replay_contract,
        current_replay_contract=tool_change_contract,
        artifact_ledger=artifact_ledger,
    )
    input_change_contract = replay_contract.model_copy(
        update={"input_fingerprint": "changed_" + replay_contract.input_fingerprint}
    )
    input_change_plan = build_partial_rerun_plan(
        previous_run_context=run_context,
        previous_replay_contract=replay_contract,
        current_replay_contract=input_change_contract,
        artifact_ledger=artifact_ledger,
    )
    return BenchmarkReplayAudit(
        package_id=package_id,
        run_id=manifest.run_id,
        exact_reuse=_replay_decision("exact_reuse", exact_plan),
        tool_change=_replay_decision("tool_change", tool_change_plan),
        input_change=_replay_decision("input_change", input_change_plan),
    )


def build_benchmark_failure_recovery_bundle(
    base_dir: Path,
    *,
    package_id: str,
    manifest: RuntimeReviewableOutputPath,
    artifacts_dir: Path | None = None,
) -> BenchmarkFailureRecoveryBundle:
    """Build engineering-failure and scientific-invalidation split for one run."""
    workspace = RunWorkspace.for_run(
        base_dir,
        manifest.run_id,
        artifacts_root_override=artifacts_dir,
    )
    engineering = build_runtime_failure_recovery_audit(workspace, run_id=manifest.run_id)
    replay_audit = build_benchmark_replay_audit(
        base_dir,
        package_id=package_id,
        manifest=manifest,
        artifacts_dir=artifacts_dir,
    )
    return BenchmarkFailureRecoveryBundle(
        package_id=package_id,
        run_id=manifest.run_id,
        engineering_recovery=engineering,
        scientific_invalidation_reasons=replay_audit.input_change.invalidation_reasons,
        preserved_artifact_kinds=tuple(
            _normalize_recovery_artifact_kind(artifact.artifact_kind, artifact.path)
            for artifact in engineering.preserved_artifacts
        ),
        blocked_artifact_kinds=tuple(
            _normalize_recovery_artifact_kind(artifact.artifact_kind, artifact.path)
            for artifact in engineering.blocked_artifacts
        ),
        notes=(
            "engineering failure is determined from artifact survivability and integrity checks",
            "scientific invalidation is determined from replay fingerprint changes rather than filesystem corruption",
        ),
    )


def build_benchmark_run_provenance_report(
    base_dir: Path,
    *,
    package_id: str,
    manifest: RuntimeReviewableOutputPath,
    artifacts_dir: Path | None = None,
) -> BenchmarkRunProvenanceReport:
    """Build exact provenance for one runtime benchmark run."""
    spec = _spec_by_id(package_id)
    workspace = RunWorkspace.for_run(
        base_dir,
        manifest.run_id,
        artifacts_root_override=artifacts_dir,
    )
    run_context = RunContextContract.load_json(workspace.run_context_path)
    replay_contract = ReplayContract.load_json(workspace.replay_contract_path)
    run_summary = _load_json_dict(workspace.run_summary_path)
    provider_version = None
    version_payload = run_summary.get("version")
    if isinstance(version_payload, dict):
        tool_versions = version_payload.get("tool_versions")
        if isinstance(tool_versions, dict):
            value = tool_versions.get(run_context.provider_name)
            provider_version = str(value) if value is not None else None
    return BenchmarkRunProvenanceReport(
        package_id=package_id,
        run_id=manifest.run_id,
        command=manifest.command,
        workflow_family=manifest.workflow_family,
        proof_class=_proof_class_for_run_mode(spec.run_mode),
        runtime_app_version=str(run_summary["version"]["app"]),
        runtime_git_commit=str(run_summary["version"]["git_commit"]),
        provider_name=run_context.provider_name,
        provider_version=provider_version,
        external_engine_name=_spec_by_id(package_id).engine_name,
        external_engine_version=_spec_by_id(package_id).engine_version,
        parameter_choices=(
            f"config_fingerprint={run_context.config_fingerprint}",
            f"parameter_fingerprint={replay_contract.parameter_fingerprint}",
            f"tool_fingerprint={replay_contract.tool_fingerprint}",
            f"artifact_policy_fingerprint={replay_contract.artifact_policy_fingerprint}",
        ),
        input_digests=tuple(
            _build_digest_record(label, path)
            for label, path in _iter_input_paths(spec)
        ),
        artifact_digests=tuple(
            BenchmarkDigestRecord(
                label=entry.artifact_kind,
                path=entry.path,
                sha256=entry.content_sha256,
            )
            for entry in RuntimeArtifactLedger.load_json(workspace.artifact_ledger_path).entries
        ),
        notes=(
            "runtime provenance fixes the exact input and artifact digests before downstream review consumers interpret benchmark results",
        ),
    )


def build_benchmark_execution_cost_report(
    base_dir: Path,
    *,
    package_id: str,
    manifest: RuntimeReviewableOutputPath,
    artifacts_dir: Path | None = None,
) -> BenchmarkExecutionCostReport:
    """Build cost realism for one runtime benchmark run."""
    workspace = RunWorkspace.for_run(
        base_dir,
        manifest.run_id,
        artifacts_root_override=artifacts_dir,
    )
    telemetry = _load_json_dict(workspace.telemetry_path)
    ledger = RuntimeArtifactLedger.load_json(workspace.artifact_ledger_path)
    timers = telemetry.get("timers", {})
    run_total = 0.0
    if isinstance(timers, dict):
        values = timers.get("run_total_ms", [])
        if isinstance(values, list) and values:
            run_total = max(float(value) for value in values)
    largest_entries = sorted(
        ledger.entries,
        key=lambda entry: entry.size_bytes,
        reverse=True,
    )[:3]
    critical_bottlenecks = []
    if isinstance(timers, dict):
        critical_bottlenecks.extend(
            sorted(
                timers,
                key=lambda name: max(float(value) for value in timers[name]),
                reverse=True,
            )[:3]
        )
    if not critical_bottlenecks:
        critical_bottlenecks = ["artifact_serialization"]
    return BenchmarkExecutionCostReport(
        package_id=package_id,
        run_id=manifest.run_id,
        workflow_family=manifest.workflow_family,
        wall_time_ms=run_total,
        cost_metrics={
            key: float(value)
            for key, value in _dict_items(telemetry.get("cost", {}))
        },
        total_artifact_bytes=sum(entry.size_bytes for entry in ledger.entries),
        largest_artifacts=tuple(
            BenchmarkCostArtifact(
                artifact_kind=entry.artifact_kind,
                size_bytes=entry.size_bytes,
            )
            for entry in largest_entries
        ),
        critical_bottlenecks=tuple(critical_bottlenecks),
    )


def build_benchmark_portability_check(
    primary_base_dir: Path,
    *,
    package_id: str,
    primary_manifest: RuntimeReviewableOutputPath,
    secondary_base_dir: Path,
    secondary_manifest: RuntimeReviewableOutputPath,
    primary_artifacts_dir: Path | None = None,
    secondary_artifacts_dir: Path | None = None,
) -> BenchmarkPortabilityCheck:
    """Check that benchmark semantics survive execution in another environment."""
    primary_workspace = RunWorkspace.for_run(
        primary_base_dir,
        primary_manifest.run_id,
        artifacts_root_override=primary_artifacts_dir,
    )
    secondary_workspace = RunWorkspace.for_run(
        secondary_base_dir,
        secondary_manifest.run_id,
        artifacts_root_override=secondary_artifacts_dir,
    )
    primary_signature = _semantic_signature(primary_workspace, primary_manifest)
    secondary_signature = _semantic_signature(secondary_workspace, secondary_manifest)
    return BenchmarkPortabilityCheck(
        package_id=package_id,
        primary_run_id=primary_manifest.run_id,
        secondary_run_id=secondary_manifest.run_id,
        semantic_signature_match=primary_signature == secondary_signature,
        environment_specific_differences=(
            "run_id",
            "environment.environment_id",
            "run_summary.artifacts_dir",
        ),
        notes=(
            "portability checks compare runtime semantics separately from environment-bound identifiers that are expected to drift across machines",
        ),
    )


def _run_import_benchmark_path(
    base_dir: Path,
    *,
    package_id: str,
    artifacts_dir: Path | None = None,
) -> RuntimeReviewableOutputPath:
    spec = _spec_by_id(package_id)
    return run_reviewable_import_path(
        base_dir,
        sequence="MPEPTIDE",
        source_path=_repo_root() / spec.primary_input_path,
        engine_name=str(spec.engine_name),
        engine_version=str(spec.engine_version),
        artifacts_dir=artifacts_dir,
    )


def _load_flagship_dia_precursor_rows() -> tuple[DiaPrecursorQuantInput, ...]:
    repo_root = _repo_root()
    roots = (
        (
            repo_root
            / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_report.tsv",
            "spectronaut_primary",
            "EG.PrecursorId",
            "PEP.StrippedSequence",
            "PG.ProteinAccessions",
        ),
        (
            repo_root
            / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/comparator/diann_pipeline_export.tsv",
            "diann_comparator",
            "precursor_id",
            "sequence",
            "protein_ids",
        ),
    )
    rows: list[DiaPrecursorQuantInput] = []
    for path, sample_id, precursor_key, peptide_key, protein_key in roots:
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                protein_refs = [
                    token.strip()
                    for token in str(row[protein_key]).replace(";", ",").split(",")
                    if token.strip()
                ]
                rows.append(
                    DiaPrecursorQuantInput(
                        precursor_id=str(row[precursor_key]).strip(),
                        peptide=str(row[peptide_key]).strip(),
                        protein_ref=protein_refs[0] if protein_refs else "unknown_protein",
                        sample_id=sample_id,
                        intensity=None,
                    )
                )
    return tuple(rows)


def _load_companion_dia_precursor_rows() -> tuple[DiaPrecursorQuantInput, ...]:
    repo_root = _repo_root()
    roots = (
        (
            repo_root
            / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/primary/diann_report.tsv",
            "diann_primary_companion",
            "Precursor.Id",
            "Stripped.Sequence",
            "Protein.Ids",
        ),
        (
            repo_root
            / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/comparator/spectronaut_pipeline_export.tsv",
            "spectronaut_comparator_companion",
            "precursor_key",
            "stripped_sequence",
            "protein_accessions",
        ),
    )
    rows: list[DiaPrecursorQuantInput] = []
    for path, sample_id, precursor_key, peptide_key, protein_key in roots:
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                protein_refs = [
                    token.strip()
                    for token in str(row[protein_key]).replace(";", ",").split(",")
                    if token.strip()
                ]
                rows.append(
                    DiaPrecursorQuantInput(
                        precursor_id=str(row[precursor_key]).strip(),
                        peptide=str(row[peptide_key]).strip(),
                        protein_ref=protein_refs[0] if protein_refs else "unknown_protein",
                        sample_id=sample_id,
                        intensity=None,
                    )
                )
    return tuple(rows)


def _spec_by_id(package_id: str) -> BenchmarkRunSpec:
    return next(spec for spec in build_benchmark_run_specs() if spec.package_id == package_id)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "configs").is_dir()
    )


def _sequence_from_fasta(path: Path) -> str:
    return "".join(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith(">")
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_fingerprint(payload: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _load_json_dict(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"expected JSON object at {path}")
    return payload


def _proof_class_for_run_mode(run_mode: BenchmarkRunMode) -> RuntimeProofClass:
    if run_mode is BenchmarkRunMode.RAW_EXECUTABLE:
        return RuntimeProofClass.RAW_EXECUTION
    if run_mode is BenchmarkRunMode.IMPORT_ONLY:
        return RuntimeProofClass.IMPORT_BACKED_EXECUTION
    raise ValueError(f"unsupported proof class for blocked runtime mode: {run_mode}")


def _preview_for_json(path: Path, *, limit: int = 3) -> tuple[str, ...]:
    payload = _load_json_dict(path)
    return tuple(
        f"{key}={json.dumps(value, sort_keys=True)}"
        for key, value in list(payload.items())[:limit]
    )


def _summarize_source_path(path: Path) -> BenchmarkArtifactEntry:
    preview = path.read_text(encoding="utf-8").splitlines()[:3]
    return BenchmarkArtifactEntry(
        artifact_kind="benchmark-source-input",
        path=str(path),
        sha256=_sha256(path),
        summary=f"tracked benchmark source input {path.name}",
        preview_lines=tuple(preview),
    )


def _summarize_imported_payload(
    *,
    path: Path,
    imported_payload: dict[str, Any],
) -> BenchmarkArtifactEntry:
    payload = imported_payload.get("payload", {})
    preview_lines: list[str] = []
    if isinstance(payload, dict) and "rows" in payload:
        columns = payload.get("columns", ())
        row_count = payload.get("row_count", 0)
        preview_lines.append(
            f"columns={','.join(str(column) for column in columns)}"
        )
        preview_lines.append(f"row_count={row_count}")
        rows = payload.get("rows", [])
        if isinstance(rows, list) and rows:
            first = rows[0]
            if isinstance(first, dict):
                preview_lines.append(
                    ",".join(f"{key}={value}" for key, value in list(first.items())[:4])
                )
        summary = f"imported tabular comparator payload with {row_count} rows"
    else:
        preview_lines.extend(_preview_for_json(path))
        summary = "imported json comparator payload"
    return BenchmarkArtifactEntry(
        artifact_kind="runtime-imported-evidence",
        path=str(path),
        sha256=_sha256(path),
        summary=summary,
        preview_lines=tuple(preview_lines),
    )


def _summarize_runtime_output(path: Path, artifact_kind: str) -> BenchmarkArtifactEntry:
    if path.suffix == ".json":
        preview = _preview_for_json(path)
    else:
        preview = tuple(path.read_text(encoding="utf-8").splitlines()[:3])
    return BenchmarkArtifactEntry(
        artifact_kind=artifact_kind,
        path=str(path),
        sha256=_sha256(path),
        summary=f"runtime review output {path.name}",
        preview_lines=preview,
    )


def _replay_decision(scenario_id: str, plan: PartialRerunPlan) -> BenchmarkReplayDecision:
    return BenchmarkReplayDecision(
        scenario_id=scenario_id,
        eligible=plan.replay_eligibility.eligible,
        invalidation_reasons=plan.replay_eligibility.invalidation_reasons,
        reused_nodes=tuple(step.node_id for step in plan.reuse_steps),
        rerun_nodes=tuple(step.node_id for step in plan.rerun_steps),
    )


def _normalize_recovery_artifact_kind(artifact_kind: str, path: str) -> str:
    name = Path(path).name
    if artifact_kind == "runtime-artifact-item":
        if name == "review_packet.json":
            return "runtime-review-packet"
        if name == "evidence_bundle.json":
            return "runtime-evidence-bundle"
        if name == "reviewable_import_path.json":
            return "runtime-reviewable-import-path"
    return artifact_kind


def _build_digest_record(label: str, path: Path) -> BenchmarkDigestRecord:
    return BenchmarkDigestRecord(label=label, path=str(path), sha256=_sha256(path))


def _iter_input_paths(spec: BenchmarkRunSpec) -> tuple[tuple[str, Path], ...]:
    repo_root = _repo_root()
    return (
        ("primary_input", repo_root / spec.primary_input_path),
        *(
            (f"companion_input_{index}", repo_root / path)
            for index, path in enumerate(spec.companion_input_paths, start=1)
        ),
    )


def _dict_items(payload: object) -> tuple[tuple[str, object], ...]:
    if not isinstance(payload, dict):
        return ()
    return tuple((str(key), value) for key, value in payload.items())


def _semantic_signature(
    workspace: RunWorkspace,
    manifest: RuntimeReviewableOutputPath,
) -> str:
    run_context = RunContextContract.load_json(workspace.run_context_path)
    summary = _load_json_dict(workspace.run_summary_path)
    signature_payload: dict[str, Any] = {
        "command": manifest.command,
        "workflow_family": manifest.workflow_family,
        "import_only": manifest.import_only,
        "provider_name": run_context.provider_name,
        "dataset_fingerprint": run_context.dataset.dataset_fingerprint,
        "outcome": summary["outcome"],
        "tool_status": summary["tool_status"],
    }
    if manifest.import_trace_path is not None:
        imported_payload = _load_json_dict(
            workspace.artifact_items_dir / "imported_evidence.json"
        )
        signature_payload["imported_payload"] = imported_payload.get("payload")
    return _stable_fingerprint(signature_payload)


__all__ = [
    "BenchmarkArtifactBrowser",
    "BenchmarkArtifactEntry",
    "BenchmarkCostArtifact",
    "BenchmarkDigestRecord",
    "BenchmarkExecutionCostReport",
    "BenchmarkFailureRecoveryBundle",
    "BenchmarkPortabilityCheck",
    "BenchmarkReplayAudit",
    "BenchmarkReplayDecision",
    "BenchmarkRunMode",
    "BenchmarkRunProvenanceReport",
    "BenchmarkRunSpec",
    "BenchmarkRuntimeTruthRow",
    "build_benchmark_artifact_browser",
    "build_benchmark_execution_cost_report",
    "build_benchmark_failure_recovery_bundle",
    "build_benchmark_portability_check",
    "build_benchmark_replay_audit",
    "build_benchmark_run_provenance_report",
    "build_benchmark_run_specs",
    "build_benchmark_runtime_truth_surface",
    "run_benchmark_dda_generalization_import_path",
    "run_benchmark_dda_import_path",
    "run_benchmark_dia_generalization_review_path",
    "run_benchmark_dia_review_path",
    "run_benchmark_dia_import_path",
    "run_benchmark_lfq_generalization_review_path",
    "run_benchmark_lfq_review_path",
    "run_benchmark_multiplex_generalization_review_path",
    "run_benchmark_multiplex_review_path",
    "run_benchmark_ptm_generalization_review_path",
    "run_benchmark_ptm_review_path",
    "run_benchmark_targeted_generalization_review_path",
    "run_benchmark_targeted_review_path",
    "run_benchmark_sequence_path",
]
