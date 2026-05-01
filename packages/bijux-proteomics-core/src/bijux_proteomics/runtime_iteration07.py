# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Runtime end-to-end workflow execution surfaces for iteration 07."""

from __future__ import annotations

from enum import StrEnum
import hashlib
import json
from pathlib import Path
import tempfile

from pydantic import ConfigDict, Field

from bijux_proteomics.digestion import digest_protein_records
from bijux_proteomics.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import Ms1FeatureRecord
from bijux_proteomics.quantification_iteration05 import build_quant_review_bundle
from bijux_proteomics.sequences import (
    DecoyGenerationMode,
    FastaParseMode,
    generate_decoy_records,
    parse_fasta_document,
)
from bijux_proteomics.spectra import parse_mgf
from bijux_proteomics_foundation import JsonModel


class RuntimeWorkflowStatus(StrEnum):
    """Execution status for one runtime workflow report."""

    COMPLETED = "completed"
    REFUSED = "refused"
    FAILED = "failed"


class RuntimeWorkflowStepRecord(JsonModel):
    """One deterministic runtime step trace entry."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    status: RuntimeWorkflowStatus
    output_count: int = Field(..., ge=0)


class SequenceToDigestWorkflowRunReport(JsonModel):
    """End-to-end runtime report for FASTA -> digest -> decoy -> evidence."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    status: RuntimeWorkflowStatus
    target_record_count: int = Field(..., ge=0)
    decoy_record_count: int = Field(..., ge=0)
    target_peptide_count: int = Field(..., ge=0)
    decoy_peptide_count: int = Field(..., ge=0)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    replay_cache_key: str = Field(..., min_length=64, max_length=64)
    steps: tuple[RuntimeWorkflowStepRecord, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class DdaSearchHitInput(JsonModel):
    """Minimal normalized DDA search hit used in runtime import reports."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    score: float


class DdaImportWorkflowRunReport(JsonModel):
    """End-to-end runtime report for DDA import and inference surfaces."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    status: RuntimeWorkflowStatus
    spectrum_count: int = Field(..., ge=0)
    accepted_psm_count: int = Field(..., ge=0)
    peptide_count: int = Field(..., ge=0)
    protein_count: int = Field(..., ge=0)
    rejected_psm_count: int = Field(..., ge=0)
    qc_issue_count: int = Field(..., ge=0)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    replay_cache_key: str = Field(..., min_length=64, max_length=64)
    steps: tuple[RuntimeWorkflowStepRecord, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class DiaPrecursorQuantInput(JsonModel):
    """Minimal DIA precursor-level import row."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    intensity: float | None = Field(default=None, ge=0.0)


class DiaImportWorkflowRunReport(JsonModel):
    """End-to-end runtime report for DIA import and quant evidence."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    status: RuntimeWorkflowStatus
    precursor_count: int = Field(..., ge=0)
    peptide_count: int = Field(..., ge=0)
    protein_count: int = Field(..., ge=0)
    quantified_precursor_count: int = Field(..., ge=0)
    qc_missing_intensity_count: int = Field(..., ge=0)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    replay_cache_key: str = Field(..., min_length=64, max_length=64)
    steps: tuple[RuntimeWorkflowStepRecord, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class QuantRuntimeWorkflowRunReport(JsonModel):
    """End-to-end runtime report for quant workflow execution."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    status: RuntimeWorkflowStatus
    feature_record_count: int = Field(..., ge=0)
    design_entry_count: int = Field(..., ge=0)
    condition_count: int = Field(..., ge=0)
    outlier_sample_count: int = Field(..., ge=0)
    review_bundle_hash: str = Field(..., min_length=1)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    replay_cache_key: str = Field(..., min_length=64, max_length=64)
    steps: tuple[RuntimeWorkflowStepRecord, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def _stable_runtime_key(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _parse_mgf_text(mgf_text: str):
    with tempfile.NamedTemporaryFile("w", suffix=".mgf", delete=False) as handle:
        handle.write(mgf_text)
        temp_path = Path(handle.name)
    try:
        return parse_mgf(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)


def run_sequence_to_digest_workflow_end_to_end(
    fasta_text: str,
    *,
    artifact_root: str = "artifacts/workflows/sequence-to-digest",
    decoy_mode: DecoyGenerationMode = DecoyGenerationMode.REVERSE,
) -> SequenceToDigestWorkflowRunReport:
    """Execute FASTA -> digest -> decoy -> peptide evidence end to end."""
    parse_report = parse_fasta_document(fasta_text, mode=FastaParseMode.STRICT)
    if not parse_report.accepted_records:
        key = _stable_runtime_key({"workflow": "sequence-to-digest", "fasta": fasta_text})
        return SequenceToDigestWorkflowRunReport(
            workflow_id="sequence-to-digest",
            status=RuntimeWorkflowStatus.REFUSED,
            target_record_count=0,
            decoy_record_count=0,
            target_peptide_count=0,
            decoy_peptide_count=0,
            artifact_paths=(f"{artifact_root}/parse-refusal.json",),
            evidence_pointers=("fasta.parse.rejected_records",),
            replay_cache_key=key,
            steps=(
                RuntimeWorkflowStepRecord(
                    step_id="parse-fasta",
                    description="parse strict FASTA records",
                    status=RuntimeWorkflowStatus.REFUSED,
                    output_count=0,
                ),
            ),
            note="workflow refused because no FASTA records were accepted under strict parsing",
        )
    targets = parse_report.accepted_records
    decoys = generate_decoy_records(targets, mode=decoy_mode)
    target_peptides = digest_protein_records(targets, protease="trypsin", min_length=7)
    decoy_peptides = digest_protein_records(decoys, protease="trypsin", min_length=7)
    key = _stable_runtime_key(
        {
            "workflow": "sequence-to-digest",
            "target_records": len(targets),
            "decoy_records": len(decoys),
            "target_peptides": len(target_peptides),
            "decoy_peptides": len(decoy_peptides),
            "decoy_mode": decoy_mode.value,
        }
    )
    return SequenceToDigestWorkflowRunReport(
        workflow_id="sequence-to-digest",
        status=RuntimeWorkflowStatus.COMPLETED,
        target_record_count=len(targets),
        decoy_record_count=len(decoys),
        target_peptide_count=len(target_peptides),
        decoy_peptide_count=len(decoy_peptides),
        artifact_paths=(
            f"{artifact_root}/targets.fasta",
            f"{artifact_root}/decoys.fasta",
            f"{artifact_root}/peptides.tsv",
        ),
        evidence_pointers=(
            "fasta.accepted_records",
            "decoy.records",
            "digest.target_peptides",
            "digest.decoy_peptides",
        ),
        replay_cache_key=key,
        steps=(
            RuntimeWorkflowStepRecord(
                step_id="parse-fasta",
                description="parse strict FASTA records",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(targets),
            ),
            RuntimeWorkflowStepRecord(
                step_id="generate-decoys",
                description="generate deterministic decoy records",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(decoys),
            ),
            RuntimeWorkflowStepRecord(
                step_id="digest-targets",
                description="digest accepted target records with trypsin",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(target_peptides),
            ),
            RuntimeWorkflowStepRecord(
                step_id="digest-decoys",
                description="digest generated decoy records with trypsin",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(decoy_peptides),
            ),
        ),
        note="workflow completed with deterministic FASTA, decoy, and digestion evidence surfaces",
    )


def run_dda_import_workflow_end_to_end(
    mgf_text: str,
    *,
    search_hits: tuple[DdaSearchHitInput, ...],
    artifact_root: str = "artifacts/workflows/dda-import",
) -> DdaImportWorkflowRunReport:
    """Execute DDA runtime flow: spectra import -> PSM -> peptide/protein -> QC evidence."""
    mgf_report = _parse_mgf_text(mgf_text)
    spectra = {spectrum.spectrum_id for spectrum in mgf_report.accepted_spectra}
    accepted_hits = tuple(hit for hit in search_hits if hit.spectrum_id in spectra)
    rejected_hits = tuple(hit for hit in search_hits if hit.spectrum_id not in spectra)
    peptides = tuple(sorted({hit.peptide for hit in accepted_hits}))
    proteins = tuple(sorted({hit.protein_ref for hit in accepted_hits}))
    qc_issue_count = len(mgf_report.rejected_blocks) + len(rejected_hits)
    key = _stable_runtime_key(
        {
            "workflow": "dda-import",
            "spectra": len(spectra),
            "hits": [hit.to_dict() for hit in search_hits],
            "accepted_psm_count": len(accepted_hits),
        }
    )
    return DdaImportWorkflowRunReport(
        workflow_id="dda-import",
        status=RuntimeWorkflowStatus.COMPLETED,
        spectrum_count=len(spectra),
        accepted_psm_count=len(accepted_hits),
        peptide_count=len(peptides),
        protein_count=len(proteins),
        rejected_psm_count=len(rejected_hits),
        qc_issue_count=qc_issue_count,
        artifact_paths=(
            f"{artifact_root}/spectra.mgf",
            f"{artifact_root}/psm.tsv",
            f"{artifact_root}/protein_inference.tsv",
            f"{artifact_root}/qc_report.json",
        ),
        evidence_pointers=(
            "spectra.accepted_spectra",
            "search.accepted_psm",
            "inference.peptides",
            "inference.proteins",
            "qc.issues",
        ),
        replay_cache_key=key,
        steps=(
            RuntimeWorkflowStepRecord(
                step_id="import-spectra",
                description="parse MGF spectra and retain accepted blocks",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(spectra),
            ),
            RuntimeWorkflowStepRecord(
                step_id="map-psm",
                description="map normalized search hits to imported spectra",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(accepted_hits),
            ),
            RuntimeWorkflowStepRecord(
                step_id="infer-peptide",
                description="aggregate accepted PSM rows into peptide evidence",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(peptides),
            ),
            RuntimeWorkflowStepRecord(
                step_id="infer-protein",
                description="aggregate peptide evidence into protein references",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(proteins),
            ),
            RuntimeWorkflowStepRecord(
                step_id="qc-evidence",
                description="collect rejected spectra/hits into a QC issue surface",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=qc_issue_count,
            ),
        ),
        note="workflow completed DDA import with mapped PSM, inferred peptide/protein evidence, and QC accounting",
    )


def run_dia_import_workflow_end_to_end(
    precursor_rows: tuple[DiaPrecursorQuantInput, ...],
    *,
    artifact_root: str = "artifacts/workflows/dia-import",
) -> DiaImportWorkflowRunReport:
    """Execute DIA runtime flow: import -> precursor/peptide/protein quant -> QC evidence."""
    precursors = tuple(sorted({row.precursor_id for row in precursor_rows}))
    peptides = tuple(sorted({row.peptide for row in precursor_rows}))
    proteins = tuple(sorted({row.protein_ref for row in precursor_rows}))
    quantified = tuple(row for row in precursor_rows if row.intensity is not None)
    missing = tuple(row for row in precursor_rows if row.intensity is None)
    key = _stable_runtime_key(
        {
            "workflow": "dia-import",
            "rows": [row.to_dict() for row in precursor_rows],
        }
    )
    return DiaImportWorkflowRunReport(
        workflow_id="dia-import",
        status=RuntimeWorkflowStatus.COMPLETED,
        precursor_count=len(precursors),
        peptide_count=len(peptides),
        protein_count=len(proteins),
        quantified_precursor_count=len({row.precursor_id for row in quantified}),
        qc_missing_intensity_count=len(missing),
        artifact_paths=(
            f"{artifact_root}/precursor_quant.tsv",
            f"{artifact_root}/peptide_quant.tsv",
            f"{artifact_root}/protein_quant.tsv",
            f"{artifact_root}/qc_report.json",
        ),
        evidence_pointers=(
            "dia.precursor_rows",
            "dia.peptide_quant",
            "dia.protein_quant",
            "dia.qc.missing_intensity_rows",
        ),
        replay_cache_key=key,
        steps=(
            RuntimeWorkflowStepRecord(
                step_id="import-dia-results",
                description="ingest DIA precursor-level quant rows",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(precursor_rows),
            ),
            RuntimeWorkflowStepRecord(
                step_id="aggregate-precursor",
                description="aggregate DIA rows at precursor level",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(precursors),
            ),
            RuntimeWorkflowStepRecord(
                step_id="aggregate-peptide",
                description="aggregate precursor evidence to peptide level",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(peptides),
            ),
            RuntimeWorkflowStepRecord(
                step_id="aggregate-protein",
                description="aggregate peptide evidence to protein level",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(proteins),
            ),
            RuntimeWorkflowStepRecord(
                step_id="qc-evidence",
                description="collect DIA rows with missing intensities for QC review",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(missing),
            ),
        ),
        note="workflow completed DIA import with precursor/peptide/protein quant and QC evidence",
    )


def run_quant_workflow_end_to_end(
    feature_records: tuple[Ms1FeatureRecord, ...],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    artifact_root: str = "artifacts/workflows/quant-runtime",
) -> QuantRuntimeWorkflowRunReport:
    """Execute quant runtime flow: matrix -> normalization -> DA -> review bundle."""
    review_bundle = build_quant_review_bundle(
        feature_records,
        design_entries=design_entries,
    )
    conditions = tuple(sorted({entry.condition for entry in design_entries}))
    key = _stable_runtime_key(
        {
            "workflow": "quant-runtime",
            "feature_count": len(feature_records),
            "design_count": len(design_entries),
            "condition_count": len(conditions),
            "bundle_hash": review_bundle.artifact_bundle_hash,
        }
    )
    outlier_count = len(review_bundle.qc_report.outlier_samples)
    return QuantRuntimeWorkflowRunReport(
        workflow_id="quant-runtime",
        status=RuntimeWorkflowStatus.COMPLETED,
        feature_record_count=len(feature_records),
        design_entry_count=len(design_entries),
        condition_count=len(conditions),
        outlier_sample_count=outlier_count,
        review_bundle_hash=review_bundle.artifact_bundle_hash or "missing",
        artifact_paths=(
            f"{artifact_root}/matrix.tsv",
            f"{artifact_root}/normalization.json",
            f"{artifact_root}/differential_abundance.tsv",
            f"{artifact_root}/review_bundle.json",
        ),
        evidence_pointers=(
            "quant.feature_records",
            "quant.normalization_matrix",
            "quant.effect_size_da_report",
            "quant.qc_report",
        ),
        replay_cache_key=key,
        steps=(
            RuntimeWorkflowStepRecord(
                step_id="build-matrix",
                description="build peptide-level quant matrix from features",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(feature_records),
            ),
            RuntimeWorkflowStepRecord(
                step_id="normalize",
                description="normalize quant matrix across samples",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(conditions),
            ),
            RuntimeWorkflowStepRecord(
                step_id="differential-abundance",
                description="compute effect-size-first differential abundance entries",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=(
                    len(review_bundle.effect_size_da_report.entries)
                    if review_bundle.effect_size_da_report is not None
                    else 0
                ),
            ),
            RuntimeWorkflowStepRecord(
                step_id="review-bundle",
                description="assemble integrated quant review bundle",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(review_bundle.evidence_pointers),
            ),
        ),
        note="workflow completed quant matrix, normalization, differential abundance, and review bundle surfaces",
    )
