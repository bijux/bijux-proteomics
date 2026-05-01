# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""DIA, spectral-library, and targeted proteomics surfaces for iteration 12."""

from __future__ import annotations

from enum import StrEnum
import json

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class DiaNativePrecursor(JsonModel):
    """DIA-native precursor quantity and confidence semantics."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    q_value: float = Field(..., ge=0.0, le=1.0)
    quantity: float = Field(..., ge=0.0)


class DiaNativeFragment(JsonModel):
    """DIA-native fragment evidence semantics."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    fragment_id: str = Field(..., min_length=1)
    mz: float = Field(..., gt=0.0)
    intensity: float = Field(..., ge=0.0)


class DiaNativeProteinGroupQuantity(JsonModel):
    """DIA-native protein-group quantity semantics."""

    model_config = ConfigDict(extra="forbid")

    protein_group_id: str = Field(..., min_length=1)
    q_value: float = Field(..., ge=0.0, le=1.0)
    quantity: float = Field(..., ge=0.0)


class DiaNativeLibraryEntryReference(JsonModel):
    """Reference from DIA-native records to a library entry."""

    model_config = ConfigDict(extra="forbid")

    library_entry_id: str = Field(..., min_length=1)
    decoy: bool = False


class DiaNativeDataModel(JsonModel):
    """Complete DIA-native data model for precursors/fragments/protein groups/library refs."""

    model_config = ConfigDict(extra="forbid")

    precursors: tuple[DiaNativePrecursor, ...] = Field(default_factory=tuple)
    fragments: tuple[DiaNativeFragment, ...] = Field(default_factory=tuple)
    protein_groups: tuple[DiaNativeProteinGroupQuantity, ...] = Field(default_factory=tuple)
    library_refs: tuple[DiaNativeLibraryEntryReference, ...] = Field(default_factory=tuple)
    precursor_count: int = Field(..., ge=0)
    fragment_count: int = Field(..., ge=0)
    protein_group_count: int = Field(..., ge=0)


def build_dia_native_data_model(
    *,
    precursors: tuple[DiaNativePrecursor, ...],
    fragments: tuple[DiaNativeFragment, ...],
    protein_groups: tuple[DiaNativeProteinGroupQuantity, ...],
    library_refs: tuple[DiaNativeLibraryEntryReference, ...],
) -> DiaNativeDataModel:
    """Build DIA-native model retaining precursor/fragment/protein/library semantics."""

    return DiaNativeDataModel(
        precursors=tuple(sorted(precursors, key=lambda entry: entry.precursor_id)),
        fragments=tuple(
            sorted(fragments, key=lambda entry: (entry.precursor_id, entry.fragment_id))
        ),
        protein_groups=tuple(sorted(protein_groups, key=lambda entry: entry.protein_group_id)),
        library_refs=tuple(sorted(library_refs, key=lambda entry: entry.library_entry_id)),
        precursor_count=len(precursors),
        fragment_count=len(fragments),
        protein_group_count=len(protein_groups),
    )


class SpectralLibraryIdentityEntry(JsonModel):
    """Identity record for one spectral-library entry."""

    model_config = ConfigDict(extra="forbid")

    library_source: str = Field(..., min_length=1)
    library_version: str = Field(..., min_length=1)
    spectrum_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    modifications: tuple[str, ...] = Field(default_factory=tuple)
    decoy: bool = False


class SpectralLibraryIdentityLedger(JsonModel):
    """Ledger of spectral-library identity records."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[SpectralLibraryIdentityEntry, ...] = Field(default_factory=tuple)
    library_source_count: int = Field(..., ge=0)


def build_spectral_library_identity_ledger(
    entries: tuple[SpectralLibraryIdentityEntry, ...],
) -> SpectralLibraryIdentityLedger:
    """Track spectral-library source/version/spectrum/peptide/charge/mod/decoy identity."""

    return SpectralLibraryIdentityLedger(
        entries=tuple(
            sorted(entries, key=lambda entry: (entry.library_source, entry.spectrum_id))
        ),
        library_source_count=len({entry.library_source for entry in entries}),
    )


class SpectralLibraryValidationIssue(JsonModel):
    """Validation issue for spectral-library identity workflows."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    spectrum_id: str | None = None


class SpectralLibraryValidationReport(JsonModel):
    """Validation report over library fields, duplicates, decoys, mods, and provenance."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    issues: tuple[SpectralLibraryValidationIssue, ...] = Field(default_factory=tuple)


def validate_spectral_library_identity_entries(
    entries: tuple[SpectralLibraryIdentityEntry, ...],
) -> SpectralLibraryValidationReport:
    """Validate spectral-library identity fields, duplicates, decoys, modifications, provenance."""

    issues: list[SpectralLibraryValidationIssue] = []
    seen: set[tuple[str, str]] = set()
    has_decoy = False
    for entry in entries:
        key = (entry.library_source, entry.spectrum_id)
        if key in seen:
            issues.append(
                SpectralLibraryValidationIssue(
                    code="duplicate_spectrum_id",
                    message="library_source/spectrum_id combination must be unique",
                    spectrum_id=entry.spectrum_id,
                )
            )
        else:
            seen.add(key)
        if entry.decoy:
            has_decoy = True
        for token in entry.modifications:
            if "[" not in token or "]" not in token:
                issues.append(
                    SpectralLibraryValidationIssue(
                        code="invalid_modification_token",
                        message="modification tokens should use Name[Residue] format",
                        spectrum_id=entry.spectrum_id,
                    )
                )
    if not has_decoy:
        issues.append(
            SpectralLibraryValidationIssue(
                code="missing_decoy_entries",
                message="at least one decoy spectral-library entry is required",
            )
        )

    return SpectralLibraryValidationReport(valid=not issues, issues=tuple(issues))


class DiaNnImportRow(JsonModel):
    """Normalized representation of one DIA-NN-style output row."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    q_value: float = Field(..., ge=0.0, le=1.0)
    quantity: float = Field(..., ge=0.0)
    protein_group_id: str = Field(..., min_length=1)


class DiaNnImportReport(JsonModel):
    """Import report mapping DIA-NN rows into DIA-native quant/evidence structures."""

    model_config = ConfigDict(extra="forbid")

    imported_precursors: tuple[DiaNativePrecursor, ...] = Field(default_factory=tuple)
    imported_protein_groups: tuple[DiaNativeProteinGroupQuantity, ...] = Field(
        default_factory=tuple
    )
    imported_count: int = Field(..., ge=0)


def import_dia_nn_rows(
    rows: tuple[DiaNnImportRow, ...],
) -> DiaNnImportReport:
    """Import DIA-NN-style rows into DIA-native precursor/protein-quant surfaces."""

    precursors = [
        DiaNativePrecursor(
            precursor_id=row.precursor_id,
            peptide_sequence=row.peptide_sequence,
            charge=row.charge,
            q_value=row.q_value,
            quantity=row.quantity,
        )
        for row in rows
    ]

    protein_quantity: dict[str, float] = {}
    protein_q: dict[str, float] = {}
    for row in rows:
        protein_quantity[row.protein_group_id] = protein_quantity.get(row.protein_group_id, 0.0) + row.quantity
        protein_q[row.protein_group_id] = min(protein_q.get(row.protein_group_id, 1.0), row.q_value)

    proteins = [
        DiaNativeProteinGroupQuantity(
            protein_group_id=protein_group_id,
            q_value=protein_q[protein_group_id],
            quantity=quantity,
        )
        for protein_group_id, quantity in sorted(protein_quantity.items())
    ]

    return DiaNnImportReport(
        imported_precursors=tuple(sorted(precursors, key=lambda entry: entry.precursor_id)),
        imported_protein_groups=tuple(proteins),
        imported_count=len(rows),
    )
