# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Outsider-readable DDA public benchmark package surfaces."""

from __future__ import annotations

import csv
from enum import StrEnum
import hashlib
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.benchmarks.flagship_asset_roots import flagship_asset_root
from bijux_proteomics.identification.search_adapter_loss import (
    build_protein_inference_engine_disagreement_dossier,
    build_search_adapter_information_loss_report,
    build_search_adapter_parity_report,
)
from bijux_proteomics.identification.search_adapters.contracts import (
    SearchAdapterKind,
)
from bijux_proteomics.identification.search_adapters.normalization import (
    normalize_search_results_with_adapter,
)
from bijux_proteomics_foundation import JsonModel

PACKAGE_ROOT = flagship_asset_root("dda_reviewable_run")
MAXQUANT_PIPELINE_EXPORT = f"{PACKAGE_ROOT}/primary/maxquant_pipeline_export.tsv"
MAXQUANT_SETTINGS = f"{PACKAGE_ROOT}/primary/maxquant_settings.txt"
MSFRAGGER_PIPELINE_EXPORT = f"{PACKAGE_ROOT}/comparator/msfragger_pipeline_export.tsv"
MSFRAGGER_SETTINGS = f"{PACKAGE_ROOT}/comparator/msfragger.params"
RAW_SPECTRA = f"{PACKAGE_ROOT}/evidence/spectra.mgf"
EXPERIMENTAL_DESIGN = f"{PACKAGE_ROOT}/evidence/design.tsv"
EXPECTATION_MANIFEST = f"{PACKAGE_ROOT}/evidence/workflow_end_to_end_expectations.json"
QUALITY_SHEET = f"{PACKAGE_ROOT}/quality_sheet.json"
LIFECYCLE_RECORD = f"{PACKAGE_ROOT}/lifecycle.json"
SOURCE_LOCATOR_MANIFEST = f"{PACKAGE_ROOT}/source_locator_manifest.json"
CITATION_MANIFEST = f"{PACKAGE_ROOT}/citation_manifest.json"
GENERATED_BOUNDARY = f"{PACKAGE_ROOT}/generated_boundary.json"
REBUILD_INSTRUCTIONS = f"{PACKAGE_ROOT}/rebuild_instructions.md"


class DdaReviewableArtifactKind(StrEnum):
    """Tracked artifact roles inside the DDA reviewable package."""

    RAW_SPECTRA = "raw_spectra"
    EXPERIMENTAL_DESIGN = "experimental_design"
    EXPECTATION_MANIFEST = "expectation_manifest"
    PRIMARY_SEARCH_EXPORT = "primary_search_export"
    PRIMARY_SEARCH_SETTINGS = "primary_search_settings"
    COMPARATOR_SEARCH_EXPORT = "comparator_search_export"
    COMPARATOR_SEARCH_SETTINGS = "comparator_search_settings"


class DdaReviewablePackageArtifact(JsonModel):
    """One tracked file that makes the DDA package reviewable from the repo tree."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1)
    artifact_kind: DdaReviewableArtifactKind
    repo_relative_path: str = Field(..., min_length=1)
    sha256: str = Field(..., min_length=64, max_length=64)
    row_count: int | None = Field(default=None, ge=0)
    spectra_count: int | None = Field(default=None, ge=0)
    reviewer_note: str = Field(..., min_length=1)


class DdaScientificInvariant(JsonModel):
    """One concrete numeric invariant earned by the tracked DDA package."""

    model_config = ConfigDict(extra="forbid")

    invariant_id: str = Field(..., min_length=1)
    metric_name: str = Field(..., min_length=1)
    observed_numeric: float = Field(..., ge=0.0)
    expected_relation: str = Field(..., min_length=1)
    expected_numeric: float = Field(..., ge=0.0)
    summary: str = Field(..., min_length=1)
    evidence_artifact_ids: tuple[str, ...] = Field(default_factory=tuple)


class DdaWarningDemonstration(JsonModel):
    """One review warning turned into concrete public evidence."""

    model_config = ConfigDict(extra="forbid")

    warning_id: str = Field(..., min_length=1)
    warning_label: str = Field(..., min_length=1)
    demonstrated_metric: float = Field(..., ge=0.0)
    metric_summary: str = Field(..., min_length=1)
    consequence: str = Field(..., min_length=1)
    evidence_artifact_ids: tuple[str, ...] = Field(default_factory=tuple)


class DdaCitationReference(JsonModel):
    """One scientific reference attached to the DDA public package."""

    model_config = ConfigDict(extra="forbid")

    citation_id: str = Field(..., min_length=1)
    doi: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    why_it_matters: str = Field(..., min_length=1)


class DdaReviewablePackage(JsonModel):
    """Complete outsider-readable DDA package with artifacts and limits."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    package_label: str = Field(..., min_length=1)
    package_root: str = Field(..., min_length=1)
    outsider_summary: str = Field(..., min_length=1)
    benchmark_manifest_id: str = Field(..., min_length=1)
    runtime_package_id: str = Field(..., min_length=1)
    comparator_path_ids: tuple[str, ...] = Field(default_factory=tuple)
    public_package_files: tuple[str, ...] = Field(default_factory=tuple)
    artifacts: tuple[DdaReviewablePackageArtifact, ...] = Field(default_factory=tuple)
    scientific_invariants: tuple[DdaScientificInvariant, ...] = Field(
        default_factory=tuple
    )
    warning_demonstrations: tuple[DdaWarningDemonstration, ...] = Field(
        default_factory=tuple
    )
    citation_refs: tuple[DdaCitationReference, ...] = Field(default_factory=tuple)
    review_artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    validating_test_paths: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "docs").is_dir()
    )


def _repo_path(repo_relative_path: str) -> Path:
    return _repo_root() / repo_relative_path


def _sha256(repo_relative_path: str) -> str:
    return hashlib.sha256(_repo_path(repo_relative_path).read_bytes()).hexdigest()


def _tsv_row_count(repo_relative_path: str) -> int:
    with _repo_path(repo_relative_path).open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle, delimiter="\t"))


def _mgf_spectrum_count(repo_relative_path: str) -> int:
    return (
        _repo_path(repo_relative_path).read_text(encoding="utf-8").count("BEGIN IONS")
    )


def _build_artifacts() -> tuple[DdaReviewablePackageArtifact, ...]:
    return (
        DdaReviewablePackageArtifact(
            artifact_id="dda_reviewable_run:raw_spectra",
            artifact_kind=DdaReviewableArtifactKind.RAW_SPECTRA,
            repo_relative_path=RAW_SPECTRA,
            sha256=_sha256(RAW_SPECTRA),
            spectra_count=_mgf_spectrum_count(RAW_SPECTRA),
            reviewer_note=(
                "One raw-like tandem spectrum keeps the package tied to inspectable fragment evidence."
            ),
        ),
        DdaReviewablePackageArtifact(
            artifact_id="dda_reviewable_run:experimental_design",
            artifact_kind=DdaReviewableArtifactKind.EXPERIMENTAL_DESIGN,
            repo_relative_path=EXPERIMENTAL_DESIGN,
            sha256=_sha256(EXPERIMENTAL_DESIGN),
            row_count=_tsv_row_count(EXPERIMENTAL_DESIGN),
            reviewer_note=(
                "The design table records instrument, batch, and engine context for the reviewable run."
            ),
        ),
        DdaReviewablePackageArtifact(
            artifact_id="dda_reviewable_run:expectation_manifest",
            artifact_kind=DdaReviewableArtifactKind.EXPECTATION_MANIFEST,
            repo_relative_path=EXPECTATION_MANIFEST,
            sha256=_sha256(EXPECTATION_MANIFEST),
            reviewer_note=(
                "The expectation manifest states which workflow surfaces must exist before the package counts as reviewable."
            ),
        ),
        DdaReviewablePackageArtifact(
            artifact_id="dda_reviewable_run:maxquant_export",
            artifact_kind=DdaReviewableArtifactKind.PRIMARY_SEARCH_EXPORT,
            repo_relative_path=MAXQUANT_PIPELINE_EXPORT,
            sha256=_sha256(MAXQUANT_PIPELINE_EXPORT),
            row_count=_tsv_row_count(MAXQUANT_PIPELINE_EXPORT),
            reviewer_note=(
                "This is the primary imported DDA result set; it replaces the old fake-export benchmark placeholder."
            ),
        ),
        DdaReviewablePackageArtifact(
            artifact_id="dda_reviewable_run:maxquant_settings",
            artifact_kind=DdaReviewableArtifactKind.PRIMARY_SEARCH_SETTINGS,
            repo_relative_path=MAXQUANT_SETTINGS,
            sha256=_sha256(MAXQUANT_SETTINGS),
            reviewer_note=(
                "The MaxQuant settings file exposes the pinned enzyme, tolerances, and decoy prefix."
            ),
        ),
        DdaReviewablePackageArtifact(
            artifact_id="dda_reviewable_run:msfragger_export",
            artifact_kind=DdaReviewableArtifactKind.COMPARATOR_SEARCH_EXPORT,
            repo_relative_path=MSFRAGGER_PIPELINE_EXPORT,
            sha256=_sha256(MSFRAGGER_PIPELINE_EXPORT),
            row_count=_tsv_row_count(MSFRAGGER_PIPELINE_EXPORT),
            reviewer_note=(
                "The comparator export is shipped alongside the primary path so warning pressure is visible in files, not only in prose."
            ),
        ),
        DdaReviewablePackageArtifact(
            artifact_id="dda_reviewable_run:msfragger_settings",
            artifact_kind=DdaReviewableArtifactKind.COMPARATOR_SEARCH_SETTINGS,
            repo_relative_path=MSFRAGGER_SETTINGS,
            sha256=_sha256(MSFRAGGER_SETTINGS),
            reviewer_note=(
                "The comparator settings file keeps the alternate search space and tolerance assumptions inspectable."
            ),
        ),
    )


def _build_scientific_invariants() -> tuple[DdaScientificInvariant, ...]:
    maxquant = normalize_search_results_with_adapter(
        source_path=_repo_path(MAXQUANT_PIPELINE_EXPORT),
        adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
        dialect_id="pipeline-export",
    )
    msfragger = normalize_search_results_with_adapter(
        source_path=_repo_path(MSFRAGGER_PIPELINE_EXPORT),
        adapter_kind=SearchAdapterKind.MSFRAGGER,
        dialect_id="pipeline-export",
    )
    maxquant_parity = build_search_adapter_parity_report(maxquant)
    msfragger_parity = build_search_adapter_parity_report(msfragger)
    maxquant_loss = build_search_adapter_information_loss_report(maxquant)
    target_count = sum(
        record.target_decoy_label.value == "target"
        for record in maxquant.normalized_records
    )
    decoy_count = sum(
        record.target_decoy_label.value == "decoy"
        for record in maxquant.normalized_records
    )
    max_observed_q = max(
        record.q_value or 0.0 for record in maxquant.normalized_records
    )
    parity_pass_count = float(
        sum(report.release_acceptable for report in (maxquant_parity, msfragger_parity))
    )
    information_loss_free_count = float(
        sum(
            report.acceptable_for_identification_claims
            for report in (
                maxquant_loss,
                build_search_adapter_information_loss_report(msfragger),
            )
        )
    )
    return (
        DdaScientificInvariant(
            invariant_id="dda_reviewable_run:maxquant_target_psm_count",
            metric_name="maxquant target PSM count",
            observed_numeric=float(target_count),
            expected_relation="equals",
            expected_numeric=2.0,
            summary=(
                "The primary DDA export should preserve two target identifications in the pinned public package."
            ),
            evidence_artifact_ids=("dda_reviewable_run:maxquant_export",),
        ),
        DdaScientificInvariant(
            invariant_id="dda_reviewable_run:maxquant_decoy_psm_count",
            metric_name="maxquant decoy PSM count",
            observed_numeric=float(decoy_count),
            expected_relation="equals",
            expected_numeric=1.0,
            summary=(
                "The primary DDA export should preserve one explicit decoy so target-decoy visibility is not flattened away."
            ),
            evidence_artifact_ids=("dda_reviewable_run:maxquant_export",),
        ),
        DdaScientificInvariant(
            invariant_id="dda_reviewable_run:maxquant_observed_q_ceiling",
            metric_name="maxquant observed q-value ceiling",
            observed_numeric=max_observed_q,
            expected_relation="less_or_equal",
            expected_numeric=0.039,
            summary=(
                "The pinned MaxQuant export stays inside the tracked q-value ceiling used by the reviewable package."
            ),
            evidence_artifact_ids=("dda_reviewable_run:maxquant_export",),
        ),
        DdaScientificInvariant(
            invariant_id="dda_reviewable_run:adapter_parity_pass_count",
            metric_name="adapter parity pass count across shipped DDA engines",
            observed_numeric=parity_pass_count,
            expected_relation="equals",
            expected_numeric=2.0,
            summary=(
                "Both shipped DDA adapter families must satisfy the current parity release criteria before the package can anchor review claims."
            ),
            evidence_artifact_ids=(
                "dda_reviewable_run:maxquant_export",
                "dda_reviewable_run:msfragger_export",
            ),
        ),
        DdaScientificInvariant(
            invariant_id="dda_reviewable_run:identification_loss_free_count",
            metric_name="identification-loss-free engine count",
            observed_numeric=information_loss_free_count,
            expected_relation="equals",
            expected_numeric=2.0,
            summary=(
                "Neither shipped DDA export may drop material identification columns if the package is going to support bounded review claims."
            ),
            evidence_artifact_ids=(
                "dda_reviewable_run:maxquant_export",
                "dda_reviewable_run:msfragger_export",
            ),
        ),
    )


def _build_warning_demonstrations() -> tuple[DdaWarningDemonstration, ...]:
    maxquant = normalize_search_results_with_adapter(
        source_path=_repo_path(MAXQUANT_PIPELINE_EXPORT),
        adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
        dialect_id="pipeline-export",
    )
    msfragger = normalize_search_results_with_adapter(
        source_path=_repo_path(MSFRAGGER_PIPELINE_EXPORT),
        adapter_kind=SearchAdapterKind.MSFRAGGER,
        dialect_id="pipeline-export",
    )
    dossier = build_protein_inference_engine_disagreement_dossier((maxquant, msfragger))
    return (
        DdaWarningDemonstration(
            warning_id="dda_reviewable_run:protein_rollup_engine_drift",
            warning_label="protein-level agreement does not survive cross-engine rollup",
            demonstrated_metric=float(dossier.material_disagreement_count),
            metric_summary=(
                "The pinned MaxQuant and MSFragger exports produce five material protein-inference disagreements across the shipped strategy set."
            ),
            consequence=(
                "Protein-facing DDA claims must stay downgrade-heavy even when peptide-facing evidence looks clean, because the public comparator corpus demonstrates engine-dependent rollup behavior directly."
            ),
            evidence_artifact_ids=(
                "dda_reviewable_run:maxquant_export",
                "dda_reviewable_run:msfragger_export",
            ),
        ),
    )


def _build_citation_refs() -> tuple[DdaCitationReference, ...]:
    return (
        DdaCitationReference(
            citation_id="citation:target_decoy_2007",
            doi="10.1038/nmeth1019",
            url="https://www.nature.com/articles/nmeth1019",
            why_it_matters=(
                "The package keeps target-decoy evidence visible and uses this paper as the boundary for confidence-facing DDA claims."
            ),
        ),
        DdaCitationReference(
            citation_id="citation:protein_inference_2012",
            doi="10.1074/mcp.R111.014795",
            url="https://pmc.ncbi.nlm.nih.gov/articles/PMC3494198/",
            why_it_matters=(
                "The comparator warning demonstration is about protein rollup disagreement, so protein inference limits must stay cited and explicit."
            ),
        ),
        DdaCitationReference(
            citation_id="citation:uniprot_2025",
            doi="10.1093/nar/gkae1010",
            url="https://www.uniprot.org",
            why_it_matters=(
                "Reference proteome grounding remains part of the bounded DDA claim surface."
            ),
        ),
    )


def build_dda_reviewable_package() -> DdaReviewablePackage:
    """Build the outsider-readable DDA public benchmark package."""

    return DdaReviewablePackage(
        package_id="public_benchmark_package:dda_reviewable_run",
        package_label="DDA reviewable public package",
        package_root=PACKAGE_ROOT,
        outsider_summary=(
            "This package ties one reviewable DDA benchmark to raw-like spectra, a primary MaxQuant export, a comparator MSFragger export, pinned settings, runtime expectations, and concrete protein-rollup warning pressure."
        ),
        benchmark_manifest_id="benchmark:dda_search_reproducibility",
        runtime_package_id="dda-maxquant-pipeline-corpus",
        comparator_path_ids=("comparator_path:msfragger_imported_dda_review",),
        public_package_files=(
            f"{PACKAGE_ROOT}/README.md",
            f"{PACKAGE_ROOT}/package_manifest.json",
            f"{PACKAGE_ROOT}/artifact_inventory.json",
            QUALITY_SHEET,
            LIFECYCLE_RECORD,
            SOURCE_LOCATOR_MANIFEST,
            CITATION_MANIFEST,
            GENERATED_BOUNDARY,
            REBUILD_INSTRUCTIONS,
            f"{PACKAGE_ROOT}/scientific_invariants.json",
            f"{PACKAGE_ROOT}/warning_demonstrations.json",
        ),
        artifacts=_build_artifacts(),
        scientific_invariants=_build_scientific_invariants(),
        warning_demonstrations=_build_warning_demonstrations(),
        citation_refs=_build_citation_refs(),
        review_artifact_paths=(
            "artifacts/workflows/flagship-workflows/runtime/sequence_intake.json",
            "artifacts/workflows/flagship-workflows/runtime/qc_report.json",
            "artifacts/workflows/flagship-workflows/runtime/review_packet.json",
            "artifacts/workflows/flagship-workflows/core/scientific_kernel.json",
        ),
        validating_test_paths=(
            "packages/bijux-proteomics-core/tests/benchmarks/test_dda_reviewable_package_surface.py",
            "packages/bijux-proteomics-core/tests/identification/test_search_adapter_parity.py",
            "packages/bijux-proteomics-core/tests/identification/test_search_adapter_loss_surface.py",
            "packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py",
        ),
        note=(
            "The package is outsider-readable and materially stronger than the old DDA mini-study surface, but it still does not claim in-repo live-engine rerun parity."
        ),
    )


__all__ = [
    "DdaCitationReference",
    "DdaReviewableArtifactKind",
    "DdaReviewablePackage",
    "DdaReviewablePackageArtifact",
    "DdaScientificInvariant",
    "DdaWarningDemonstration",
    "build_dda_reviewable_package",
]
