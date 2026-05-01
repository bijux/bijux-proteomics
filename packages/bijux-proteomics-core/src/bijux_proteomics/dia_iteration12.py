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


class LibrarySearchComparisonEntry(JsonModel):
    """Comparison entry for shared peptides across library vs database search evidence."""

    model_config = ConfigDict(extra="forbid")

    peptide_sequence: str = Field(..., min_length=1)
    library_q_value: float = Field(..., ge=0.0, le=1.0)
    database_q_value: float = Field(..., ge=0.0, le=1.0)
    preferred_source: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class LibrarySearchComparisonReport(JsonModel):
    """Comparison report between library-search and database-search evidence."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[LibrarySearchComparisonEntry, ...] = Field(default_factory=tuple)
    shared_peptide_count: int = Field(..., ge=0)


def compare_library_and_database_search_evidence(
    *,
    library_q_values: dict[str, float],
    database_q_values: dict[str, float],
) -> LibrarySearchComparisonReport:
    """Compare shared-peptide evidence between library-search and database-search outputs."""

    shared = sorted(set(library_q_values) & set(database_q_values))
    entries: list[LibrarySearchComparisonEntry] = []
    for peptide in shared:
        library_q = library_q_values[peptide]
        database_q = database_q_values[peptide]
        preferred = "library" if library_q <= database_q else "database"
        note = "library evidence is stronger" if preferred == "library" else "database evidence is stronger"
        entries.append(
            LibrarySearchComparisonEntry(
                peptide_sequence=peptide,
                library_q_value=library_q,
                database_q_value=database_q,
                preferred_source=preferred,
                note=note,
            )
        )

    return LibrarySearchComparisonReport(
        entries=tuple(entries),
        shared_peptide_count=len(shared),
    )


class DiaMissingnessReason(StrEnum):
    """Library/method-driven missingness reasons in DIA quantification."""

    LIBRARY_COVERAGE_GAP = "library_coverage_gap"
    SIGNAL_BELOW_THRESHOLD = "signal_below_threshold"
    INTERFERENCE_FILTERED = "interference_filtered"
    ACQUISITION_MISSING = "acquisition_missing"


class DiaQuantMissingnessEntry(JsonModel):
    """One DIA missingness observation across precursor/peptide/protein/run."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    protein_group_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    reason: DiaMissingnessReason


class DiaQuantMissingnessReport(JsonModel):
    """Missingness report for DIA quant semantics."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[DiaQuantMissingnessEntry, ...] = Field(default_factory=tuple)
    reason_counts: dict[str, int] = Field(default_factory=dict)


def build_dia_quant_missingness_report(
    entries: tuple[DiaQuantMissingnessEntry, ...],
) -> DiaQuantMissingnessReport:
    """Represent DIA quant missingness by precursor/peptide/protein/run and reason."""

    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry.reason.value] = counts.get(entry.reason.value, 0) + 1
    return DiaQuantMissingnessReport(
        entries=tuple(
            sorted(entries, key=lambda entry: (entry.run_id, entry.protein_group_id, entry.precursor_id))
        ),
        reason_counts=dict(sorted(counts.items())),
    )


class DiaIonMobilityEvidenceEntry(JsonModel):
    """Ion mobility / CCS evidence retained in DIA-native reports."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    ion_mobility_ms_per_cm2: float = Field(..., gt=0.0)
    ccs_angstrom2: float = Field(..., gt=0.0)
    evidence_used: bool
    note: str = Field(..., min_length=1)


class DiaIonMobilityEvidenceReport(JsonModel):
    """Report preserving mobility/CCS evidence usage in DIA workflows."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[DiaIonMobilityEvidenceEntry, ...] = Field(default_factory=tuple)
    used_count: int = Field(..., ge=0)


def build_dia_ion_mobility_evidence_report(
    entries: tuple[DiaIonMobilityEvidenceEntry, ...],
) -> DiaIonMobilityEvidenceReport:
    """Preserve ion mobility/CCS fields and whether they were used in evidence."""

    return DiaIonMobilityEvidenceReport(
        entries=tuple(sorted(entries, key=lambda entry: (entry.run_id, entry.precursor_id))),
        used_count=sum(1 for entry in entries if entry.evidence_used),
    )


class TargetedAssayOptimizationCandidate(JsonModel):
    """Candidate peptide/transition for targeted assay optimization."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    uniqueness_score: float = Field(..., ge=0.0, le=1.0)
    detectability_score: float = Field(..., ge=0.0, le=1.0)
    ptm_ambiguity_penalty: float = Field(..., ge=0.0, le=1.0)
    qc_score: float = Field(..., ge=0.0, le=1.0)


class TargetedAssayOptimizationEntry(JsonModel):
    """Ranked optimization entry with rationale."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    rank: int = Field(..., ge=1)
    optimization_score: float = Field(..., ge=0.0)
    rationale: str = Field(..., min_length=1)


class TargetedAssayOptimizationReport(JsonModel):
    """Optimization ranking report for targeted peptide/transition candidates."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[TargetedAssayOptimizationEntry, ...] = Field(default_factory=tuple)


def optimize_targeted_assay_candidates(
    candidates: tuple[TargetedAssayOptimizationCandidate, ...],
) -> TargetedAssayOptimizationReport:
    """Rank targeted candidates by uniqueness, detectability, PTM ambiguity, and QC."""

    scored: list[tuple[str, float]] = []
    for candidate in candidates:
        score = (
            (candidate.uniqueness_score * 0.35)
            + (candidate.detectability_score * 0.35)
            + (candidate.qc_score * 0.30)
            - (candidate.ptm_ambiguity_penalty * 0.40)
        )
        scored.append((candidate.candidate_id, score))

    scored.sort(key=lambda item: (-item[1], item[0]))
    entries = []
    for rank, (candidate_id, score) in enumerate(scored, start=1):
        entries.append(
            TargetedAssayOptimizationEntry(
                candidate_id=candidate_id,
                rank=rank,
                optimization_score=score,
                rationale=(
                    "ranking balances uniqueness/detectability/QC while penalizing PTM ambiguity"
                ),
            )
        )

    return TargetedAssayOptimizationReport(entries=tuple(entries))


class TransitionListExportEntry(JsonModel):
    """Transition list export row for targeted validation handoff."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    transition_label: str = Field(..., min_length=1)
    precursor_mz: float = Field(..., gt=0.0)
    fragment_mz: float = Field(..., gt=0.0)
    control: bool = False
    caveat: str = ""


class TransitionListExportBundle(JsonModel):
    """Exported transition list payload for targeted validation."""

    model_config = ConfigDict(extra="forbid")

    tsv_payload: str = Field(..., min_length=1)
    row_count: int = Field(..., ge=0)


def export_transition_list_candidates(
    entries: tuple[TransitionListExportEntry, ...],
) -> TransitionListExportBundle:
    """Export targeted validation transition candidates with caveats and controls."""

    header = "candidate_id\tpeptide_sequence\ttransition_label\tprecursor_mz\tfragment_mz\tcontrol\tcaveat"
    rows = [
        "\t".join(
            (
                entry.candidate_id,
                entry.peptide_sequence,
                entry.transition_label,
                f"{entry.precursor_mz:.4f}",
                f"{entry.fragment_mz:.4f}",
                "1" if entry.control else "0",
                entry.caveat,
            )
        )
        for entry in sorted(entries, key=lambda entry: (entry.candidate_id, entry.transition_label))
    ]
    payload = "\n".join([header, *rows]) + ("\n" if rows else "")
    return TransitionListExportBundle(tsv_payload=payload, row_count=len(entries))
