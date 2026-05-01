# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Realistic mini-study and corpus surfaces for iteration 11."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class CorpusLicenseStatus(StrEnum):
    """License/caveat states for corpus assets."""

    BUNDLED = "bundled"
    REFERENCED = "referenced"
    USER_SUPPLIED = "user_supplied"


class CorpusAssetEntry(JsonModel):
    """One curated corpus asset with provenance and licensing state."""

    model_config = ConfigDict(extra="forbid")

    role: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    sha256: str = Field(..., min_length=8)
    license_status: CorpusLicenseStatus
    caveat: str = Field(..., min_length=1)


class DdaMiniStudyBundle(JsonModel):
    """Complete DDA mini-study fixture package with expected outputs."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    asset_entries: tuple[CorpusAssetEntry, ...] = Field(default_factory=tuple)
    expected_outputs: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)


def build_complete_dda_mini_study_bundle(
    *,
    study_id: str,
    asset_entries: tuple[CorpusAssetEntry, ...],
    expected_outputs: tuple[str, ...],
    evidence_pointers: tuple[str, ...],
) -> DdaMiniStudyBundle:
    """Curate DDA mini-study inputs, expected outputs, and evidence pointers."""

    required_roles = {
        "spectra",
        "engine_output",
        "fasta",
        "design_metadata",
        "identification",
        "protein_inference",
        "qc",
        "evidence",
    }
    roles = {entry.role for entry in asset_entries}
    missing = sorted(required_roles - roles)
    if missing:
        raise ValueError(f"DDA mini-study is missing required asset roles: {', '.join(missing)}")
    return DdaMiniStudyBundle(
        study_id=study_id,
        asset_entries=tuple(sorted(asset_entries, key=lambda entry: (entry.role, entry.path))),
        expected_outputs=tuple(sorted(expected_outputs)),
        evidence_pointers=tuple(sorted(evidence_pointers)),
    )


class DiaMiniStudyBundle(JsonModel):
    """Complete DIA mini-study fixture package with quant/evidence outputs."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    asset_entries: tuple[CorpusAssetEntry, ...] = Field(default_factory=tuple)
    precursor_quantity_rows: int = Field(..., ge=0)
    protein_quantity_rows: int = Field(..., ge=0)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)


def build_complete_dia_mini_study_bundle(
    *,
    study_id: str,
    asset_entries: tuple[CorpusAssetEntry, ...],
    precursor_quantity_rows: int,
    protein_quantity_rows: int,
    evidence_pointers: tuple[str, ...],
) -> DiaMiniStudyBundle:
    """Curate DIA mini-study inputs, quant outputs, and evidence pointers."""

    required_roles = {
        "library",
        "result_matrix",
        "design_metadata",
        "qc",
        "evidence",
    }
    roles = {entry.role for entry in asset_entries}
    missing = sorted(required_roles - roles)
    if missing:
        raise ValueError(f"DIA mini-study is missing required asset roles: {', '.join(missing)}")
    return DiaMiniStudyBundle(
        study_id=study_id,
        asset_entries=tuple(sorted(asset_entries, key=lambda entry: (entry.role, entry.path))),
        precursor_quantity_rows=precursor_quantity_rows,
        protein_quantity_rows=protein_quantity_rows,
        evidence_pointers=tuple(sorted(evidence_pointers)),
    )


class LfqMiniStudyBundle(JsonModel):
    """Complete LFQ mini-study package with normalization and DA context."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    feature_matrix_path: str = Field(..., min_length=1)
    peptide_matrix_path: str = Field(..., min_length=1)
    protein_matrix_path: str = Field(..., min_length=1)
    normalization_method: str = Field(..., min_length=1)
    missingness_summary_path: str = Field(..., min_length=1)
    differential_abundance_report_path: str = Field(..., min_length=1)
    review_packet_path: str = Field(..., min_length=1)


def build_complete_lfq_mini_study_bundle(
    *,
    study_id: str,
    feature_matrix_path: str,
    peptide_matrix_path: str,
    protein_matrix_path: str,
    normalization_method: str,
    missingness_summary_path: str,
    differential_abundance_report_path: str,
    review_packet_path: str,
) -> LfqMiniStudyBundle:
    """Curate LFQ matrices and downstream review outputs for a complete mini-study."""

    if normalization_method.lower() not in {"median", "vsn", "quantile", "none"}:
        raise ValueError("LFQ mini-study normalization method is not recognized")
    return LfqMiniStudyBundle(
        study_id=study_id,
        feature_matrix_path=feature_matrix_path,
        peptide_matrix_path=peptide_matrix_path,
        protein_matrix_path=protein_matrix_path,
        normalization_method=normalization_method,
        missingness_summary_path=missingness_summary_path,
        differential_abundance_report_path=differential_abundance_report_path,
        review_packet_path=review_packet_path,
    )
