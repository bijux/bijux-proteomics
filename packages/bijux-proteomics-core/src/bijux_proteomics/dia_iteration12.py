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
