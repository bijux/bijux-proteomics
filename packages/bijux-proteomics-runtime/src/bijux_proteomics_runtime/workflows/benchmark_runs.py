# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime-owned flagship benchmark package catalog and execution wrappers."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.workflows.assurance import build_workflow_assurance_matrix
from bijux_proteomics_runtime.workflows.paths import (
    RuntimeReviewableOutputPath,
    run_reviewable_import_path,
    run_reviewable_sequence_path,
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
    validating_test_paths: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkRuntimeTruthRow(JsonModel):
    """Honest runtime truth posture for one flagship benchmark package."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    run_mode: BenchmarkRunMode
    replayable: bool
    externally_cross_checked: bool
    artifact_browser_ready: bool
    blocker_notes: tuple[str, ...] = Field(default_factory=tuple)
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
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_runtime_external_pack_surface.py",
            ),
            notes=(
                "runtime imports the tracked MaxQuant export and keeps provenance explicit instead of pretending to execute MaxQuant",
            ),
        ),
        BenchmarkRunSpec(
            package_id="dia-diann-pipeline-corpus",
            display_name="dia diann pipeline corpus",
            workflow_family="dia_import",
            run_mode=BenchmarkRunMode.IMPORT_ONLY,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.paths.run_reviewable_import_path",
            primary_input_path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_pipeline_export.tsv",
            companion_input_paths=(
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_report.tsv",
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_config.json",
            ),
            engine_name="dia-nn",
            engine_version="2.1.0",
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_runtime_external_pack_surface.py",
            ),
            notes=(
                "runtime imports the tracked DIA-NN export and preserves the external engine identity in review lineage",
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
        "ptm_review",
    ):
        spec = specs.get(workflow_family)
        matrix_row = matrix[workflow_family]
        if spec is None:
            rows.append(
                BenchmarkRuntimeTruthRow(
                    package_id=f"{workflow_family}-blocked-runtime-path",
                    workflow_family=workflow_family,
                    run_mode=BenchmarkRunMode.BLOCKED,
                    replayable=False,
                    externally_cross_checked=False,
                    artifact_browser_ready=False,
                    blocker_notes=matrix_row.blocker_notes
                    or (
                        "no flagship runtime benchmark path is wired for this workflow family yet",
                    ),
                    notes=matrix_row.notes,
                )
            )
            continue
        rows.append(
            BenchmarkRuntimeTruthRow(
                package_id=spec.package_id,
                workflow_family=workflow_family,
                run_mode=spec.run_mode,
                replayable=True,
                externally_cross_checked=workflow_family in {"dda_import", "dia_import"},
                artifact_browser_ready=workflow_family != "sequence_to_digest",
                blocker_notes=matrix_row.blocker_notes,
                notes=spec.notes + matrix_row.notes,
            )
        )
    return tuple(rows)


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


__all__ = [
    "BenchmarkRunMode",
    "BenchmarkRunSpec",
    "BenchmarkRuntimeTruthRow",
    "build_benchmark_run_specs",
    "build_benchmark_runtime_truth_surface",
    "run_benchmark_dda_import_path",
    "run_benchmark_dia_import_path",
    "run_benchmark_sequence_path",
]
