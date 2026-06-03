# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Chemistry-driven fragment transition selection for targeted follow-up assays."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import (
    FragmentIon,
    FragmentIonSeries,
    calculate_fragment_ions,
    calculate_peptide_mz,
)
from bijux_proteomics.identification.contracts import TargetDecoyLabel
from bijux_proteomics.io import SpectralLibraryEntry, match_spectrum_peaks_to_fragments
from bijux_proteomics.targeted.discovery_peptide_selection import (
    DiscoveryTargetedPeptideSelectionEntry,
)
from bijux_proteomics_foundation import JsonModel

_DEFAULT_FRAGMENT_CHARGES = (1, 2)
_DEFAULT_SERIES = (FragmentIonSeries.Y, FragmentIonSeries.B)
_MIN_FRAGMENT_ORDINAL = 3
_LOW_MZ_RISK_BOUNDARY = 350.0
_MEDIUM_MZ_RISK_BOUNDARY = 450.0
_NEAR_PRECURSOR_RISK_BOUNDARY = 25.0
_FRAGMENT_CLUSTER_TOLERANCE_DA = 0.6


class TargetedTransitionInterferenceRisk(StrEnum):
    """Practical interference risk tiers for candidate assay transitions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TargetedTransitionSelectionRejectionCode(StrEnum):
    """Stable refusal reasons for transition candidates."""

    FRAGMENT_TOO_SHORT = "fragment_too_short"
    FRAGMENT_MZ_BELOW_WINDOW = "fragment_mz_below_window"
    FRAGMENT_MZ_ABOVE_WINDOW = "fragment_mz_above_window"
    TOO_CLOSE_TO_PRECURSOR = "too_close_to_precursor"
    LOWER_RANK_THAN_SELECTED = "lower_rank_than_selected"


class TargetedTransitionSelectionFragment(JsonModel):
    """One selected fragment transition for a peptide-target assay entry."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(..., ge=1)
    fragment_label: str = Field(..., min_length=1)
    ion_type: FragmentIonSeries
    fragment_ordinal: int = Field(..., ge=1)
    fragment_charge: int = Field(..., ge=1)
    fragment_sequence: str = Field(..., min_length=1)
    fragment_mz: float = Field(..., gt=0.0)
    expected_relative_intensity: float | None = Field(default=None, ge=0.0, le=1.0)
    interference_risk: TargetedTransitionInterferenceRisk
    interference_risk_score: float = Field(..., ge=0.0, le=1.0)
    interference_risk_reasons: tuple[str, ...] = Field(default_factory=tuple)
    selection_score: float = Field(..., ge=0.0, le=1.0)
    selection_reasons: tuple[str, ...] = Field(default_factory=tuple)


class TargetedTransitionSelectionPeptideEntry(JsonModel):
    """One peptide-target entry with ranked fragment transitions."""

    model_config = ConfigDict(extra="forbid")

    assay_entry_id: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    target_protein_group_id: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    peptide_rank: int = Field(..., ge=1)
    precursor_charge: int = Field(..., ge=1)
    precursor_mz: float = Field(..., gt=0.0)
    source_library_entry_id: str | None = None
    chemistry_supported_transition_count: int = Field(..., ge=0)
    selected_transition_count: int = Field(..., ge=0)
    sufficient_transition_support: bool
    instrument_caveats: tuple[str, ...] = Field(default_factory=tuple)
    selected_transitions: tuple[TargetedTransitionSelectionFragment, ...] = Field(
        default_factory=tuple
    )


class TargetedTransitionSelectionRejectionEntry(JsonModel):
    """One rejected transition candidate kept visible beside the final panel."""

    model_config = ConfigDict(extra="forbid")

    assay_entry_id: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    target_protein_group_id: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    precursor_charge: int = Field(..., ge=1)
    precursor_mz: float = Field(..., gt=0.0)
    fragment_label: str = Field(..., min_length=1)
    ion_type: FragmentIonSeries
    fragment_ordinal: int = Field(..., ge=1)
    fragment_charge: int = Field(..., ge=1)
    fragment_sequence: str = Field(..., min_length=1)
    fragment_mz: float = Field(..., gt=0.0)
    expected_relative_intensity: float | None = Field(default=None, ge=0.0, le=1.0)
    interference_risk: TargetedTransitionInterferenceRisk
    interference_risk_score: float = Field(..., ge=0.0, le=1.0)
    interference_risk_reasons: tuple[str, ...] = Field(default_factory=tuple)
    selection_score: float = Field(..., ge=0.0, le=1.0)
    rejection_codes: tuple[TargetedTransitionSelectionRejectionCode, ...] = Field(
        default_factory=tuple
    )
    explanation: str = Field(..., min_length=1)


class TargetedTransitionSelectionSummary(JsonModel):
    """Compact accounting over one targeted transition-selection pass."""

    model_config = ConfigDict(extra="forbid")

    peptide_entry_count: int = Field(..., ge=0)
    peptide_with_minimum_transition_count: int = Field(..., ge=0)
    peptide_without_minimum_transition_count: int = Field(..., ge=0)
    selected_transition_count: int = Field(..., ge=0)
    rejected_transition_count: int = Field(..., ge=0)
    library_backed_transition_count: int = Field(..., ge=0)


class TargetedTransitionSelectionReport(JsonModel):
    """Targeted transition-selection report over already selected peptides."""

    model_config = ConfigDict(extra="forbid")

    minimum_transition_count: int = Field(..., ge=1)
    maximum_transition_count: int = Field(..., ge=1)
    minimum_fragment_mz: float = Field(..., gt=0.0)
    maximum_fragment_mz: float = Field(..., gt=0.0)
    precursor_exclusion_da: float = Field(..., gt=0.0)
    library_match_tolerance_da: float = Field(..., gt=0.0)
    summary: TargetedTransitionSelectionSummary
    peptide_entries: tuple[TargetedTransitionSelectionPeptideEntry, ...] = Field(
        default_factory=tuple
    )
    rejected_transitions: tuple[TargetedTransitionSelectionRejectionEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


def build_targeted_transition_selection_report(
    selected_peptides: tuple[DiscoveryTargetedPeptideSelectionEntry, ...],
    *,
    spectral_library_entries: tuple[SpectralLibraryEntry, ...] = (),
    default_precursor_charge: int = 2,
    fragment_charges: tuple[int, ...] = _DEFAULT_FRAGMENT_CHARGES,
    minimum_transition_count: int = 3,
    maximum_transition_count: int = 5,
    minimum_fragment_mz: float = 300.0,
    maximum_fragment_mz: float = 1500.0,
    precursor_exclusion_da: float = 8.0,
    library_match_tolerance_da: float = 0.02,
) -> TargetedTransitionSelectionReport:
    """Choose targeted fragment transitions from peptide chemistry and library evidence."""

    if default_precursor_charge < 1:
        raise ValueError("default_precursor_charge must be at least 1")
    if not fragment_charges:
        raise ValueError("fragment_charges must not be empty")
    if any(charge < 1 for charge in fragment_charges):
        raise ValueError("fragment_charges must all be at least 1")
    if minimum_transition_count < 1:
        raise ValueError("minimum_transition_count must be at least 1")
    if maximum_transition_count < minimum_transition_count:
        raise ValueError(
            "maximum_transition_count must be greater than or equal to minimum_transition_count"
        )
    if minimum_fragment_mz <= 0.0:
        raise ValueError("minimum_fragment_mz must be greater than zero")
    if maximum_fragment_mz <= minimum_fragment_mz:
        raise ValueError("maximum_fragment_mz must be greater than minimum_fragment_mz")
    if precursor_exclusion_da <= 0.0:
        raise ValueError("precursor_exclusion_da must be greater than zero")
    if library_match_tolerance_da <= 0.0:
        raise ValueError("library_match_tolerance_da must be greater than zero")

    sorted_peptides = tuple(
        sorted(
            selected_peptides,
            key=lambda entry: (
                entry.target_protein_ref,
                entry.rank,
                entry.canonical_peptide,
            ),
        )
    )
    peptide_entries: list[TargetedTransitionSelectionPeptideEntry] = []
    rejected_transitions: list[TargetedTransitionSelectionRejectionEntry] = []

    for peptide_entry in sorted_peptides:
        selected_entry, rejected_entries = _build_peptide_transition_selection(
            peptide_entry,
            spectral_library_entries=spectral_library_entries,
            default_precursor_charge=default_precursor_charge,
            fragment_charges=tuple(sorted(dict.fromkeys(fragment_charges))),
            minimum_transition_count=minimum_transition_count,
            maximum_transition_count=maximum_transition_count,
            minimum_fragment_mz=minimum_fragment_mz,
            maximum_fragment_mz=maximum_fragment_mz,
            precursor_exclusion_da=precursor_exclusion_da,
            library_match_tolerance_da=library_match_tolerance_da,
        )
        peptide_entries.append(selected_entry)
        rejected_transitions.extend(rejected_entries)

    ordered_entries = tuple(
        sorted(
            peptide_entries,
            key=lambda entry: (
                entry.target_protein_ref,
                entry.peptide_rank,
                entry.canonical_peptide,
            ),
        )
    )
    ordered_rejections = tuple(
        sorted(
            rejected_transitions,
            key=lambda entry: (
                entry.target_protein_ref,
                entry.peptide_sequence,
                entry.fragment_mz,
                entry.fragment_label,
            ),
        )
    )
    return TargetedTransitionSelectionReport(
        minimum_transition_count=minimum_transition_count,
        maximum_transition_count=maximum_transition_count,
        minimum_fragment_mz=minimum_fragment_mz,
        maximum_fragment_mz=maximum_fragment_mz,
        precursor_exclusion_da=precursor_exclusion_da,
        library_match_tolerance_da=library_match_tolerance_da,
        summary=TargetedTransitionSelectionSummary(
            peptide_entry_count=len(ordered_entries),
            peptide_with_minimum_transition_count=sum(
                1 for entry in ordered_entries if entry.sufficient_transition_support
            ),
            peptide_without_minimum_transition_count=sum(
                1
                for entry in ordered_entries
                if not entry.sufficient_transition_support
            ),
            selected_transition_count=sum(
                len(entry.selected_transitions) for entry in ordered_entries
            ),
            rejected_transition_count=len(ordered_rejections),
            library_backed_transition_count=sum(
                1
                for entry in ordered_entries
                for fragment in entry.selected_transitions
                if fragment.expected_relative_intensity is not None
            ),
        ),
        peptide_entries=ordered_entries,
        rejected_transitions=ordered_rejections,
        note=(
            "targeted transition selection ranks chemistry-derived b and y fragments, "
            "uses spectral-library peaks only to annotate expected relative intensity "
            "when available, and keeps filtered or lower-ranked fragments visible "
            "instead of copying transitions from an input table"
        ),
    )


def render_targeted_transition_selection_summary_tsv(
    report: TargetedTransitionSelectionReport,
) -> str:
    """Render compact targeted transition-selection summary accounting as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("minimum_transition_count", report.minimum_transition_count))
    writer.writerow(("maximum_transition_count", report.maximum_transition_count))
    writer.writerow(("minimum_fragment_mz", f"{report.minimum_fragment_mz:.6f}"))
    writer.writerow(("maximum_fragment_mz", f"{report.maximum_fragment_mz:.6f}"))
    writer.writerow(("precursor_exclusion_da", f"{report.precursor_exclusion_da:.6f}"))
    writer.writerow(
        ("library_match_tolerance_da", f"{report.library_match_tolerance_da:.6f}")
    )
    writer.writerow(("peptide_entry_count", report.summary.peptide_entry_count))
    writer.writerow(
        (
            "peptide_with_minimum_transition_count",
            report.summary.peptide_with_minimum_transition_count,
        )
    )
    writer.writerow(
        (
            "peptide_without_minimum_transition_count",
            report.summary.peptide_without_minimum_transition_count,
        )
    )
    writer.writerow(
        ("selected_transition_count", report.summary.selected_transition_count)
    )
    writer.writerow(
        ("rejected_transition_count", report.summary.rejected_transition_count)
    )
    writer.writerow(
        (
            "library_backed_transition_count",
            report.summary.library_backed_transition_count,
        )
    )
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_targeted_transition_selection_selected_tsv(
    report: TargetedTransitionSelectionReport,
) -> str:
    """Render selected targeted transition candidates as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "assay_entry_id",
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "peptide_sequence",
            "canonical_peptide",
            "peptide_rank",
            "precursor_charge",
            "precursor_mz",
            "source_library_entry_id",
            "chemistry_supported_transition_count",
            "selected_transition_count",
            "sufficient_transition_support",
            "transition_rank",
            "fragment_label",
            "ion_type",
            "fragment_ordinal",
            "fragment_charge",
            "fragment_sequence",
            "fragment_mz",
            "expected_relative_intensity",
            "interference_risk",
            "interference_risk_score",
            "interference_risk_reasons",
            "selection_score",
            "selection_reasons",
            "instrument_caveats",
        )
    )
    for entry in report.peptide_entries:
        caveats = ";".join(entry.instrument_caveats)
        for fragment in entry.selected_transitions:
            writer.writerow(
                (
                    entry.assay_entry_id,
                    entry.target_protein_ref,
                    entry.target_protein_group_id,
                    "" if entry.gene_symbol is None else entry.gene_symbol,
                    entry.peptide_sequence,
                    entry.canonical_peptide,
                    entry.peptide_rank,
                    entry.precursor_charge,
                    f"{entry.precursor_mz:.6f}",
                    ""
                    if entry.source_library_entry_id is None
                    else entry.source_library_entry_id,
                    entry.chemistry_supported_transition_count,
                    entry.selected_transition_count,
                    str(entry.sufficient_transition_support).lower(),
                    fragment.rank,
                    fragment.fragment_label,
                    fragment.ion_type.value,
                    fragment.fragment_ordinal,
                    fragment.fragment_charge,
                    fragment.fragment_sequence,
                    f"{fragment.fragment_mz:.6f}",
                    ""
                    if fragment.expected_relative_intensity is None
                    else f"{fragment.expected_relative_intensity:.6f}",
                    fragment.interference_risk.value,
                    f"{fragment.interference_risk_score:.6f}",
                    ";".join(fragment.interference_risk_reasons),
                    f"{fragment.selection_score:.6f}",
                    ";".join(fragment.selection_reasons),
                    caveats,
                )
            )
    return handle.getvalue()


def render_targeted_transition_selection_rejected_tsv(
    report: TargetedTransitionSelectionReport,
) -> str:
    """Render rejected targeted transition candidates as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "assay_entry_id",
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "peptide_sequence",
            "canonical_peptide",
            "precursor_charge",
            "precursor_mz",
            "fragment_label",
            "ion_type",
            "fragment_ordinal",
            "fragment_charge",
            "fragment_sequence",
            "fragment_mz",
            "expected_relative_intensity",
            "interference_risk",
            "interference_risk_score",
            "interference_risk_reasons",
            "selection_score",
            "rejection_codes",
            "explanation",
        )
    )
    for entry in report.rejected_transitions:
        writer.writerow(
            (
                entry.assay_entry_id,
                entry.target_protein_ref,
                entry.target_protein_group_id,
                "" if entry.gene_symbol is None else entry.gene_symbol,
                entry.peptide_sequence,
                entry.canonical_peptide,
                entry.precursor_charge,
                f"{entry.precursor_mz:.6f}",
                entry.fragment_label,
                entry.ion_type.value,
                entry.fragment_ordinal,
                entry.fragment_charge,
                entry.fragment_sequence,
                f"{entry.fragment_mz:.6f}",
                ""
                if entry.expected_relative_intensity is None
                else f"{entry.expected_relative_intensity:.6f}",
                entry.interference_risk.value,
                f"{entry.interference_risk_score:.6f}",
                ";".join(entry.interference_risk_reasons),
                f"{entry.selection_score:.6f}",
                ";".join(code.value for code in entry.rejection_codes),
                entry.explanation,
            )
        )
    return handle.getvalue()


def _build_peptide_transition_selection(
    peptide_entry: DiscoveryTargetedPeptideSelectionEntry,
    *,
    spectral_library_entries: tuple[SpectralLibraryEntry, ...],
    default_precursor_charge: int,
    fragment_charges: tuple[int, ...],
    minimum_transition_count: int,
    maximum_transition_count: int,
    minimum_fragment_mz: float,
    maximum_fragment_mz: float,
    precursor_exclusion_da: float,
    library_match_tolerance_da: float,
) -> tuple[
    TargetedTransitionSelectionPeptideEntry,
    tuple[TargetedTransitionSelectionRejectionEntry, ...],
]:
    assay_entry_id = (
        f"{peptide_entry.target_protein_ref}:{peptide_entry.peptide_sequence}:"
        f"{peptide_entry.rank}"
    )
    library_entry = _pick_best_library_entry(
        peptide_entry.canonical_peptide,
        spectral_library_entries,
    )
    precursor_charge = (
        default_precursor_charge
        if library_entry is None
        else library_entry.precursor_charge
    )
    precursor_mz = (
        calculate_peptide_mz(
            peptide_entry.canonical_peptide,
            charge=precursor_charge,
        )
        if library_entry is None
        else library_entry.precursor_mz
    )
    fragments = calculate_fragment_ions(
        peptide_entry.canonical_peptide,
        charges=fragment_charges,
        series=_DEFAULT_SERIES,
        include_neutral_losses=False,
    )
    maximum_fragment_ordinal = max(
        (fragment.ordinal for fragment in fragments), default=1
    )
    expected_intensity_by_label = _expected_relative_intensity_by_label(
        peptide_entry.canonical_peptide,
        fragments,
        library_entry=library_entry,
        library_match_tolerance_da=library_match_tolerance_da,
    )
    fragment_cluster_counts = _fragment_cluster_counts(fragments)

    candidate_rows: list[tuple[TargetedTransitionSelectionFragment, str]] = []
    rejected_entries: list[TargetedTransitionSelectionRejectionEntry] = []
    for fragment in fragments:
        fragment_label = _fragment_label(
            fragment.series, fragment.ordinal, fragment.charge
        )
        risk_score, risk_reasons = _score_interference_risk(
            fragment_mz=fragment.mz_monoisotopic,
            precursor_mz=precursor_mz,
            fragment_charge=fragment.charge,
            fragment_series=fragment.series,
            fragment_ordinal=fragment.ordinal,
            cluster_count=fragment_cluster_counts[fragment_label],
        )
        expected_relative_intensity = expected_intensity_by_label.get(fragment_label)
        selection_score = _score_transition_selection(
            fragment_ordinal=fragment.ordinal,
            maximum_fragment_ordinal=maximum_fragment_ordinal,
            fragment_charge=fragment.charge,
            fragment_series=fragment.series,
            expected_relative_intensity=expected_relative_intensity,
            interference_risk_score=risk_score,
        )
        rejection_codes = _screen_fragment(
            fragment_mz=fragment.mz_monoisotopic,
            precursor_mz=precursor_mz,
            fragment_ordinal=fragment.ordinal,
            minimum_fragment_mz=minimum_fragment_mz,
            maximum_fragment_mz=maximum_fragment_mz,
            precursor_exclusion_da=precursor_exclusion_da,
        )
        if rejection_codes:
            rejected_entries.append(
                TargetedTransitionSelectionRejectionEntry(
                    assay_entry_id=assay_entry_id,
                    target_protein_ref=peptide_entry.target_protein_ref,
                    target_protein_group_id=peptide_entry.target_protein_group_id,
                    gene_symbol=peptide_entry.gene_symbol,
                    peptide_sequence=peptide_entry.peptide_sequence,
                    canonical_peptide=peptide_entry.canonical_peptide,
                    precursor_charge=precursor_charge,
                    precursor_mz=precursor_mz,
                    fragment_label=fragment_label,
                    ion_type=fragment.series,
                    fragment_ordinal=fragment.ordinal,
                    fragment_charge=fragment.charge,
                    fragment_sequence=fragment.sequence,
                    fragment_mz=fragment.mz_monoisotopic,
                    expected_relative_intensity=expected_relative_intensity,
                    interference_risk=_risk_category(risk_score),
                    interference_risk_score=risk_score,
                    interference_risk_reasons=risk_reasons,
                    selection_score=selection_score,
                    rejection_codes=rejection_codes,
                    explanation=_rejection_explanation(rejection_codes),
                )
            )
            continue
        candidate_rows.append(
            (
                TargetedTransitionSelectionFragment(
                    rank=1,
                    fragment_label=fragment_label,
                    ion_type=fragment.series,
                    fragment_ordinal=fragment.ordinal,
                    fragment_charge=fragment.charge,
                    fragment_sequence=fragment.sequence,
                    fragment_mz=fragment.mz_monoisotopic,
                    expected_relative_intensity=expected_relative_intensity,
                    interference_risk=_risk_category(risk_score),
                    interference_risk_score=risk_score,
                    interference_risk_reasons=risk_reasons,
                    selection_score=selection_score,
                    selection_reasons=_selection_reasons(
                        fragment_series=fragment.series,
                        fragment_charge=fragment.charge,
                        expected_relative_intensity=expected_relative_intensity,
                        interference_risk_score=risk_score,
                    ),
                ),
                fragment_label,
            )
        )

    ordered_candidates = sorted(
        candidate_rows,
        key=lambda row: (
            -row[0].selection_score,
            row[0].interference_risk_score,
            -1.0
            if row[0].expected_relative_intensity is None
            else -row[0].expected_relative_intensity,
            row[0].fragment_mz,
            row[1],
        ),
    )
    selected_fragments = tuple(
        fragment.model_copy(update={"rank": index})
        for index, (fragment, _) in enumerate(
            ordered_candidates[:maximum_transition_count], start=1
        )
    )
    for rejected_fragment, _ in ordered_candidates[maximum_transition_count:]:
        rejected_entries.append(
            TargetedTransitionSelectionRejectionEntry(
                assay_entry_id=assay_entry_id,
                target_protein_ref=peptide_entry.target_protein_ref,
                target_protein_group_id=peptide_entry.target_protein_group_id,
                gene_symbol=peptide_entry.gene_symbol,
                peptide_sequence=peptide_entry.peptide_sequence,
                canonical_peptide=peptide_entry.canonical_peptide,
                precursor_charge=precursor_charge,
                precursor_mz=precursor_mz,
                fragment_label=rejected_fragment.fragment_label,
                ion_type=rejected_fragment.ion_type,
                fragment_ordinal=rejected_fragment.fragment_ordinal,
                fragment_charge=rejected_fragment.fragment_charge,
                fragment_sequence=rejected_fragment.fragment_sequence,
                fragment_mz=rejected_fragment.fragment_mz,
                expected_relative_intensity=rejected_fragment.expected_relative_intensity,
                interference_risk=rejected_fragment.interference_risk,
                interference_risk_score=rejected_fragment.interference_risk_score,
                interference_risk_reasons=rejected_fragment.interference_risk_reasons,
                selection_score=rejected_fragment.selection_score,
                rejection_codes=(
                    TargetedTransitionSelectionRejectionCode.LOWER_RANK_THAN_SELECTED,
                ),
                explanation=(
                    "fragment passed chemistry and m/z filters but ranked below the "
                    "final transition set for this peptide"
                ),
            )
        )

    caveats: list[str] = []
    if library_entry is None:
        caveats.append(
            "expected relative intensity is unavailable because no spectral-library evidence matched this peptide"
        )
    elif not any(
        fragment.expected_relative_intensity is not None
        for fragment in selected_fragments
    ):
        caveats.append(
            "spectral-library evidence was supplied but no selected fragment matched an observed library peak under the requested tolerance"
        )
    if len(selected_fragments) < minimum_transition_count:
        caveats.append(
            "fewer than the requested minimum number of chemistry-supported transitions remain after fragment m/z and precursor-distance filtering"
        )
    entry = TargetedTransitionSelectionPeptideEntry(
        assay_entry_id=assay_entry_id,
        target_protein_ref=peptide_entry.target_protein_ref,
        target_protein_group_id=peptide_entry.target_protein_group_id,
        gene_symbol=peptide_entry.gene_symbol,
        peptide_sequence=peptide_entry.peptide_sequence,
        canonical_peptide=peptide_entry.canonical_peptide,
        peptide_rank=peptide_entry.rank,
        precursor_charge=precursor_charge,
        precursor_mz=precursor_mz,
        source_library_entry_id=None
        if library_entry is None
        else library_entry.library_entry_id,
        chemistry_supported_transition_count=len(candidate_rows),
        selected_transition_count=len(selected_fragments),
        sufficient_transition_support=len(selected_fragments)
        >= minimum_transition_count,
        instrument_caveats=tuple(caveats),
        selected_transitions=selected_fragments,
    )
    return entry, tuple(rejected_entries)


def _pick_best_library_entry(
    canonical_peptide: str,
    spectral_library_entries: tuple[SpectralLibraryEntry, ...],
) -> SpectralLibraryEntry | None:
    peptide_matches = [
        entry
        for entry in spectral_library_entries
        if entry.canonical_peptide == canonical_peptide
    ]
    if not peptide_matches:
        return None
    return sorted(
        peptide_matches,
        key=lambda entry: (
            0 if entry.target_decoy_label is TargetDecoyLabel.TARGET else 1,
            -sum(peak.intensity for peak in entry.spectrum.peaks),
            -len(entry.spectrum.peaks),
            entry.library_entry_id,
        ),
    )[0]


def _expected_relative_intensity_by_label(
    canonical_peptide: str,
    fragments: tuple[FragmentIon, ...],
    *,
    library_entry: SpectralLibraryEntry | None,
    library_match_tolerance_da: float,
) -> dict[str, float]:
    if library_entry is None:
        return {}
    match_report = match_spectrum_peaks_to_fragments(
        library_entry.spectrum,
        peptide=canonical_peptide,
        theoretical_fragments=fragments,
        tolerance_da=library_match_tolerance_da,
    )
    absolute_intensity_by_label: dict[str, float] = {}
    for match in match_report.matches:
        absolute_intensity_by_label[match.fragment_label] = max(
            absolute_intensity_by_label.get(match.fragment_label, 0.0),
            match.observed_intensity,
        )
    if not absolute_intensity_by_label:
        return {}
    maximum_intensity = max(absolute_intensity_by_label.values())
    return {
        label: intensity / maximum_intensity
        for label, intensity in absolute_intensity_by_label.items()
    }


def _fragment_cluster_counts(fragments: tuple[FragmentIon, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for fragment in fragments:
        label = _fragment_label(fragment.series, fragment.ordinal, fragment.charge)
        counts[label] = sum(
            1
            for candidate in fragments
            if candidate is not fragment
            and abs(candidate.mz_monoisotopic - fragment.mz_monoisotopic)
            <= _FRAGMENT_CLUSTER_TOLERANCE_DA
        )
    return counts


def _screen_fragment(
    *,
    fragment_mz: float,
    precursor_mz: float,
    fragment_ordinal: int,
    minimum_fragment_mz: float,
    maximum_fragment_mz: float,
    precursor_exclusion_da: float,
) -> tuple[TargetedTransitionSelectionRejectionCode, ...]:
    rejection_codes: list[TargetedTransitionSelectionRejectionCode] = []
    if fragment_ordinal < _MIN_FRAGMENT_ORDINAL:
        rejection_codes.append(
            TargetedTransitionSelectionRejectionCode.FRAGMENT_TOO_SHORT
        )
    if fragment_mz < minimum_fragment_mz:
        rejection_codes.append(
            TargetedTransitionSelectionRejectionCode.FRAGMENT_MZ_BELOW_WINDOW
        )
    if fragment_mz > maximum_fragment_mz:
        rejection_codes.append(
            TargetedTransitionSelectionRejectionCode.FRAGMENT_MZ_ABOVE_WINDOW
        )
    if abs(fragment_mz - precursor_mz) < precursor_exclusion_da:
        rejection_codes.append(
            TargetedTransitionSelectionRejectionCode.TOO_CLOSE_TO_PRECURSOR
        )
    return tuple(dict.fromkeys(rejection_codes))


def _score_interference_risk(
    *,
    fragment_mz: float,
    precursor_mz: float,
    fragment_charge: int,
    fragment_series: FragmentIonSeries,
    fragment_ordinal: int,
    cluster_count: int,
) -> tuple[float, tuple[str, ...]]:
    reasons: list[str] = []
    risk_score = 0.0
    if fragment_ordinal < 4:
        risk_score += 0.25
        reasons.append("short fragment ions are more exposed to chemical background")
    if fragment_mz < _LOW_MZ_RISK_BOUNDARY:
        risk_score += 0.35
        reasons.append("low fragment m/z sits in the crowded chemical background range")
    elif fragment_mz < _MEDIUM_MZ_RISK_BOUNDARY:
        risk_score += 0.15
        reasons.append("mid-low fragment m/z remains more interference-prone")
    if abs(fragment_mz - precursor_mz) < _NEAR_PRECURSOR_RISK_BOUNDARY:
        risk_score += 0.2
        reasons.append("fragment sits near the precursor isolation region")
    if fragment_charge > 1:
        risk_score += 0.1
        reasons.append(
            "higher-charge fragments are less instrument-friendly in routine targeted methods"
        )
    if fragment_series is FragmentIonSeries.B:
        risk_score += 0.1
        reasons.append("b ions are less preferred than y ions for targeted follow-up")
    if cluster_count > 0:
        risk_score += min(0.2, cluster_count * 0.1)
        reasons.append("nearby fragment m/z neighbors increase transition crowding")
    return min(1.0, risk_score), tuple(reasons)


def _score_transition_selection(
    *,
    fragment_ordinal: int,
    maximum_fragment_ordinal: int,
    fragment_charge: int,
    fragment_series: FragmentIonSeries,
    expected_relative_intensity: float | None,
    interference_risk_score: float,
) -> float:
    ordinal_fraction = fragment_ordinal / maximum_fragment_ordinal
    intensity_component = (
        ordinal_fraction
        if expected_relative_intensity is None
        else expected_relative_intensity
    )
    score = (
        (0.55 * intensity_component)
        + (0.20 * ordinal_fraction)
        + (0.15 if fragment_series is FragmentIonSeries.Y else 0.0)
        + (0.10 if fragment_charge == 1 else 0.0)
        - (0.45 * interference_risk_score)
    )
    return max(0.0, min(1.0, score))


def _selection_reasons(
    *,
    fragment_series: FragmentIonSeries,
    fragment_charge: int,
    expected_relative_intensity: float | None,
    interference_risk_score: float,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if expected_relative_intensity is not None:
        reasons.append("spectral-library intensity supports this fragment")
    else:
        reasons.append("theoretical ordinal coverage supports this fragment")
    if fragment_series is FragmentIonSeries.Y:
        reasons.append("y ions are preferred for targeted follow-up")
    if fragment_charge == 1:
        reasons.append("singly charged fragments are instrument-friendly")
    if interference_risk_score <= 0.25:
        reasons.append("fragment has low intrinsic interference risk")
    return tuple(reasons)


def _rejection_explanation(
    rejection_codes: tuple[TargetedTransitionSelectionRejectionCode, ...],
) -> str:
    if (
        TargetedTransitionSelectionRejectionCode.FRAGMENT_TOO_SHORT in rejection_codes
        and len(rejection_codes) == 1
    ):
        return "fragment ordinal is too short for durable targeted quantification"
    if (
        TargetedTransitionSelectionRejectionCode.FRAGMENT_MZ_BELOW_WINDOW
        in rejection_codes
        and len(rejection_codes) == 1
    ):
        return "fragment m/z falls below the practical targeted transition window"
    if (
        TargetedTransitionSelectionRejectionCode.FRAGMENT_MZ_ABOVE_WINDOW
        in rejection_codes
        and len(rejection_codes) == 1
    ):
        return "fragment m/z exceeds the practical targeted transition window"
    if (
        TargetedTransitionSelectionRejectionCode.TOO_CLOSE_TO_PRECURSOR
        in rejection_codes
        and len(rejection_codes) == 1
    ):
        return "fragment lies too close to the precursor isolation region"
    return (
        "fragment fails one or more targeted transition chemistry filters and is "
        "kept visible with explicit rejection codes"
    )


def _fragment_label(
    fragment_series: FragmentIonSeries,
    fragment_ordinal: int,
    fragment_charge: int,
) -> str:
    return f"{fragment_series.value}{fragment_ordinal}+{fragment_charge}"


def _risk_category(risk_score: float) -> TargetedTransitionInterferenceRisk:
    if risk_score <= 0.25:
        return TargetedTransitionInterferenceRisk.LOW
    if risk_score <= 0.55:
        return TargetedTransitionInterferenceRisk.MEDIUM
    return TargetedTransitionInterferenceRisk.HIGH
