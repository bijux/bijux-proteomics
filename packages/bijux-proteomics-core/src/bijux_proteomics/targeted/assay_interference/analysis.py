# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Pre-acquisition assay interference scoring for targeted follow-up panels."""

from __future__ import annotations

from dataclasses import dataclass

from bijux_proteomics.io import SpectralLibraryEntry
from bijux_proteomics.sequences.digestion import (
    DigestedPeptide,
    PeptideDigestionMode,
    ProteaseRule,
    digest_protein_records,
    get_protease_rule,
)
from bijux_proteomics.sequences.fasta import NormalizedProteinRecord
from bijux_proteomics.sequences.peptide_uniqueness_index import (
    PeptideUniquenessClass,
)
from bijux_proteomics.targeted.assay_interference.models import (
    TargetedAssayInterferenceAssayEntry,
    TargetedAssayInterferencePanelEntry,
    TargetedAssayInterferenceReason,
    TargetedAssayInterferenceReport,
    TargetedAssayInterferenceRiskTier,
    TargetedAssayInterferenceSummary,
    TargetedAssayInterferenceTransitionEntry,
)
from bijux_proteomics.targeted.assay_interference.support import (
    _background_competitor_peptides,
    _count_background_fragment_overlaps,
    _count_library_fragment_overlaps,
    _count_panel_fragment_overlaps,
    _group_digested_peptides,
    _library_competitor_entries,
    _selected_peptide_key,
)
from bijux_proteomics.targeted.discovery_peptide_selection import (
    DiscoveryTargetedPeptideSelectionEntry,
)
from bijux_proteomics.targeted.transition_selection import (
    TargetedTransitionSelectionFragment,
    TargetedTransitionSelectionPeptideEntry,
)

_DEFAULT_PRECURSOR_TOLERANCE_DA = 1.0
_DEFAULT_FRAGMENT_TOLERANCE_DA = 0.02
_DEFAULT_COELUTION_RT_WINDOW_MINUTES = 0.5
_DEFAULT_MIN_EXPORT_TRANSITIONS = 3


@dataclass(frozen=True)
class _InterferenceAnalysisContext:
    protease_rule: ProteaseRule
    selected_by_key: dict[tuple[str, str, int], DiscoveryTargetedPeptideSelectionEntry]
    digested_by_sequence: dict[str, tuple[DigestedPeptide, ...]]
    source_library_by_id: dict[str, SpectralLibraryEntry]


@dataclass(frozen=True)
class _AssayTransitionStatistics:
    intrinsic_average: float
    panel_overlap_total: int
    background_overlap_total: int
    library_overlap_total: int
    coeluting_overlap_total: int


def build_targeted_assay_interference_report(
    selected_peptides: tuple[DiscoveryTargetedPeptideSelectionEntry, ...],
    transition_entries: tuple[TargetedTransitionSelectionPeptideEntry, ...],
    protein_records: tuple[NormalizedProteinRecord, ...],
    *,
    spectral_library_entries: tuple[SpectralLibraryEntry, ...] = (),
    protease: ProteaseRule | str = "trypsin",
    missed_cleavages: int = 0,
    precursor_tolerance_da: float = _DEFAULT_PRECURSOR_TOLERANCE_DA,
    fragment_tolerance_da: float = _DEFAULT_FRAGMENT_TOLERANCE_DA,
    coelution_rt_window_minutes: float = _DEFAULT_COELUTION_RT_WINDOW_MINUTES,
    minimum_export_transitions: int = _DEFAULT_MIN_EXPORT_TRANSITIONS,
) -> TargetedAssayInterferenceReport:
    """Score pre-acquisition assay interference over selected peptides and transitions."""

    _validate_report_parameters(
        missed_cleavages=missed_cleavages,
        precursor_tolerance_da=precursor_tolerance_da,
        fragment_tolerance_da=fragment_tolerance_da,
        coelution_rt_window_minutes=coelution_rt_window_minutes,
        minimum_export_transitions=minimum_export_transitions,
    )
    context = _build_analysis_context(
        selected_peptides=selected_peptides,
        protein_records=protein_records,
        spectral_library_entries=spectral_library_entries,
        protease=protease,
        missed_cleavages=missed_cleavages,
    )

    transition_rows: list[TargetedAssayInterferenceTransitionEntry] = []
    assay_rows: list[TargetedAssayInterferenceAssayEntry] = []
    panel_rows: list[TargetedAssayInterferencePanelEntry] = []
    for assay_entry in _ordered_transition_entries(transition_entries):
        assay_transition_rows = _build_transition_rows_for_assay(
            assay_entry=assay_entry,
            transition_entries=transition_entries,
            context=context,
            spectral_library_entries=spectral_library_entries,
            precursor_tolerance_da=precursor_tolerance_da,
            fragment_tolerance_da=fragment_tolerance_da,
            coelution_rt_window_minutes=coelution_rt_window_minutes,
        )
        assay_row = _build_assay_entry(
            assay_entry=assay_entry,
            transition_rows=assay_transition_rows,
            context=context,
            minimum_export_transitions=minimum_export_transitions,
        )
        assay_rows.append(assay_row)
        transition_rows.extend(assay_transition_rows)
        panel_rows.extend(_build_panel_rows(assay_row, assay_transition_rows))

    ordered_assays = _ordered_assay_entries(assay_rows)
    ordered_transitions = _ordered_transition_rows(transition_rows)
    ordered_panel = _ordered_panel_rows(panel_rows)
    return TargetedAssayInterferenceReport(
        protease=context.protease_rule.name,
        missed_cleavages=missed_cleavages,
        precursor_tolerance_da=precursor_tolerance_da,
        fragment_tolerance_da=fragment_tolerance_da,
        coelution_rt_window_minutes=coelution_rt_window_minutes,
        minimum_export_transitions=minimum_export_transitions,
        summary=_build_summary(ordered_assays, ordered_transitions, ordered_panel),
        assay_entries=ordered_assays,
        transition_entries=ordered_transitions,
        panel_entries=ordered_panel,
        note=(
            "targeted assay interference scoring combines peptide uniqueness, "
            "selected-panel fragment overlap, theoretical background peptide overlap, "
            "and spectral-library competitor evidence so high-risk assays are "
            "downgraded before panel export rather than after targeted data is collected"
        ),
    )


def _validate_report_parameters(
    *,
    missed_cleavages: int,
    precursor_tolerance_da: float,
    fragment_tolerance_da: float,
    coelution_rt_window_minutes: float,
    minimum_export_transitions: int,
) -> None:
    if missed_cleavages < 0:
        raise ValueError("missed_cleavages must be non-negative")
    if precursor_tolerance_da <= 0.0:
        raise ValueError("precursor_tolerance_da must be greater than zero")
    if fragment_tolerance_da <= 0.0:
        raise ValueError("fragment_tolerance_da must be greater than zero")
    if coelution_rt_window_minutes <= 0.0:
        raise ValueError("coelution_rt_window_minutes must be greater than zero")
    if minimum_export_transitions < 1:
        raise ValueError("minimum_export_transitions must be at least 1")


def _build_analysis_context(
    *,
    selected_peptides: tuple[DiscoveryTargetedPeptideSelectionEntry, ...],
    protein_records: tuple[NormalizedProteinRecord, ...],
    spectral_library_entries: tuple[SpectralLibraryEntry, ...],
    protease: ProteaseRule | str,
    missed_cleavages: int,
) -> _InterferenceAnalysisContext:
    protease_rule = (
        get_protease_rule(protease) if isinstance(protease, str) else protease
    )
    digested_peptides = digest_protein_records(
        protein_records,
        protease=protease_rule,
        missed_cleavages=missed_cleavages,
        mode=PeptideDigestionMode.FULL,
    )
    return _InterferenceAnalysisContext(
        protease_rule=protease_rule,
        selected_by_key={
            _selected_peptide_key(entry): entry for entry in selected_peptides
        },
        digested_by_sequence=_group_digested_peptides(digested_peptides),
        source_library_by_id={
            entry.library_entry_id: entry for entry in spectral_library_entries
        },
    )


def _ordered_transition_entries(
    transition_entries: tuple[TargetedTransitionSelectionPeptideEntry, ...],
) -> tuple[TargetedTransitionSelectionPeptideEntry, ...]:
    return tuple(
        sorted(
            transition_entries,
            key=lambda entry: (
                entry.target_protein_ref,
                entry.peptide_rank,
                entry.canonical_peptide,
            ),
        )
    )


def _build_transition_rows_for_assay(
    *,
    assay_entry: TargetedTransitionSelectionPeptideEntry,
    transition_entries: tuple[TargetedTransitionSelectionPeptideEntry, ...],
    context: _InterferenceAnalysisContext,
    spectral_library_entries: tuple[SpectralLibraryEntry, ...],
    precursor_tolerance_da: float,
    fragment_tolerance_da: float,
    coelution_rt_window_minutes: float,
) -> tuple[TargetedAssayInterferenceTransitionEntry, ...]:
    source_library_entry = (
        None
        if assay_entry.source_library_entry_id is None
        else context.source_library_by_id.get(assay_entry.source_library_entry_id)
    )
    competing_background = _background_competitor_peptides(
        assay_entry,
        digested_by_sequence=context.digested_by_sequence,
        precursor_tolerance_da=precursor_tolerance_da,
    )
    competing_library_entries = _library_competitor_entries(
        assay_entry,
        source_library_entry=source_library_entry,
        spectral_library_entries=spectral_library_entries,
        precursor_tolerance_da=precursor_tolerance_da,
    )
    return tuple(
        _build_transition_row(
            assay_entry=assay_entry,
            transition=transition,
            transition_entries=transition_entries,
            source_library_entry=source_library_entry,
            competing_background=competing_background,
            competing_library_entries=competing_library_entries,
            precursor_tolerance_da=precursor_tolerance_da,
            fragment_tolerance_da=fragment_tolerance_da,
            coelution_rt_window_minutes=coelution_rt_window_minutes,
        )
        for transition in assay_entry.selected_transitions
    )


def _build_transition_row(
    *,
    assay_entry: TargetedTransitionSelectionPeptideEntry,
    transition: TargetedTransitionSelectionFragment,
    transition_entries: tuple[TargetedTransitionSelectionPeptideEntry, ...],
    source_library_entry: SpectralLibraryEntry | None,
    competing_background: tuple[str, ...],
    competing_library_entries: tuple[SpectralLibraryEntry, ...],
    precursor_tolerance_da: float,
    fragment_tolerance_da: float,
    coelution_rt_window_minutes: float,
) -> TargetedAssayInterferenceTransitionEntry:
    panel_overlap_count = _count_panel_fragment_overlaps(
        assay_entry_id=assay_entry.assay_entry_id,
        precursor_mz=assay_entry.precursor_mz,
        fragment_mz=transition.fragment_mz,
        all_transition_entries=transition_entries,
        precursor_tolerance_da=precursor_tolerance_da,
        fragment_tolerance_da=fragment_tolerance_da,
    )
    background_overlap_count = _count_background_fragment_overlaps(
        competing_background,
        fragment_mz=transition.fragment_mz,
        fragment_charge=transition.fragment_charge,
        fragment_tolerance_da=fragment_tolerance_da,
    )
    library_overlap_count, coeluting_overlap_count = _count_library_fragment_overlaps(
        competing_library_entries,
        source_library_entry=source_library_entry,
        fragment_mz=transition.fragment_mz,
        fragment_charge=transition.fragment_charge,
        fragment_tolerance_da=fragment_tolerance_da,
        coelution_rt_window_minutes=coelution_rt_window_minutes,
    )
    interference_risk_score = _transition_interference_risk_score(
        intrinsic_transition_risk_score=transition.interference_risk_score,
        panel_overlap_count=panel_overlap_count,
        background_overlap_count=background_overlap_count,
        library_overlap_count=library_overlap_count,
        coeluting_overlap_count=coeluting_overlap_count,
    )
    downgrade_reasons = _transition_downgrade_reasons(
        intrinsic_transition_risk_score=transition.interference_risk_score,
        panel_overlap_count=panel_overlap_count,
        background_overlap_count=background_overlap_count,
        library_overlap_count=library_overlap_count,
        coeluting_overlap_count=coeluting_overlap_count,
    )
    risk_tier = _risk_tier(interference_risk_score)
    return TargetedAssayInterferenceTransitionEntry(
        assay_entry_id=assay_entry.assay_entry_id,
        target_protein_ref=assay_entry.target_protein_ref,
        target_protein_group_id=assay_entry.target_protein_group_id,
        gene_symbol=assay_entry.gene_symbol,
        peptide_sequence=assay_entry.peptide_sequence,
        canonical_peptide=assay_entry.canonical_peptide,
        precursor_charge=assay_entry.precursor_charge,
        precursor_mz=assay_entry.precursor_mz,
        fragment_label=transition.fragment_label,
        ion_type=transition.ion_type,
        fragment_ordinal=transition.fragment_ordinal,
        fragment_charge=transition.fragment_charge,
        fragment_sequence=transition.fragment_sequence,
        fragment_mz=transition.fragment_mz,
        expected_relative_intensity=transition.expected_relative_intensity,
        selected_transition_rank=transition.rank,
        intrinsic_interference_risk_score=transition.interference_risk_score,
        panel_overlap_transition_count=panel_overlap_count,
        background_overlap_peptide_count=background_overlap_count,
        library_overlap_peptide_count=library_overlap_count,
        coeluting_library_overlap_peptide_count=coeluting_overlap_count,
        interference_risk_score=interference_risk_score,
        interference_risk_tier=risk_tier,
        downgrade_reasons=downgrade_reasons,
        export_allowed=risk_tier is not TargetedAssayInterferenceRiskTier.HIGH,
        export_caveat=_transition_export_caveat(
            risk_tier=risk_tier,
            downgrade_reasons=downgrade_reasons,
        ),
    )


def _build_assay_entry(
    *,
    assay_entry: TargetedTransitionSelectionPeptideEntry,
    transition_rows: tuple[TargetedAssayInterferenceTransitionEntry, ...],
    context: _InterferenceAnalysisContext,
    minimum_export_transitions: int,
) -> TargetedAssayInterferenceAssayEntry:
    selected_peptide = context.selected_by_key.get(
        (
            assay_entry.target_protein_ref,
            assay_entry.canonical_peptide,
            assay_entry.peptide_rank,
        )
    )
    shared_penalty = _shared_peptide_penalty(selected_peptide)
    statistics = _assay_transition_statistics(transition_rows)
    assay_risk_score = _assay_interference_risk_score(
        shared_penalty=shared_penalty,
        intrinsic_transition_risk_score=statistics.intrinsic_average,
        panel_overlap_transition_count=statistics.panel_overlap_total,
        background_overlap_peptide_count=statistics.background_overlap_total,
        library_overlap_peptide_count=statistics.library_overlap_total,
        coeluting_overlap_peptide_count=statistics.coeluting_overlap_total,
    )
    risk_tier = _risk_tier(assay_risk_score)
    exportable_transition_count = sum(entry.export_allowed for entry in transition_rows)
    downgrade_reasons = _assay_downgrade_reasons(
        selected_peptide=selected_peptide,
        intrinsic_transition_risk_score=statistics.intrinsic_average,
        panel_overlap_transition_count=statistics.panel_overlap_total,
        background_overlap_peptide_count=statistics.background_overlap_total,
        library_overlap_peptide_count=statistics.library_overlap_total,
        coeluting_overlap_peptide_count=statistics.coeluting_overlap_total,
    )
    panel_export_allowed = (
        risk_tier is not TargetedAssayInterferenceRiskTier.HIGH
        and exportable_transition_count >= minimum_export_transitions
    )
    if exportable_transition_count < minimum_export_transitions:
        downgrade_reasons = tuple(
            dict.fromkeys(
                (
                    *downgrade_reasons,
                    TargetedAssayInterferenceReason.INSUFFICIENT_EXPORTED_TRANSITIONS,
                )
            )
        )
    panel_export_caveat = _assay_export_caveat(
        risk_tier=risk_tier,
        panel_export_allowed=panel_export_allowed,
        downgrade_reasons=downgrade_reasons,
    )
    return TargetedAssayInterferenceAssayEntry(
        assay_entry_id=assay_entry.assay_entry_id,
        target_protein_ref=assay_entry.target_protein_ref,
        target_protein_group_id=assay_entry.target_protein_group_id,
        gene_symbol=assay_entry.gene_symbol,
        peptide_sequence=assay_entry.peptide_sequence,
        canonical_peptide=assay_entry.canonical_peptide,
        peptide_rank=assay_entry.peptide_rank,
        precursor_charge=assay_entry.precursor_charge,
        precursor_mz=assay_entry.precursor_mz,
        selected_transition_count=len(transition_rows),
        exported_transition_count=exportable_transition_count
        if panel_export_allowed
        else 0,
        shared_peptide_penalty=shared_penalty,
        panel_overlap_transition_count=statistics.panel_overlap_total,
        background_overlap_peptide_count=statistics.background_overlap_total,
        library_overlap_peptide_count=statistics.library_overlap_total,
        coeluting_library_overlap_peptide_count=statistics.coeluting_overlap_total,
        intrinsic_transition_risk_score=statistics.intrinsic_average,
        interference_risk_score=assay_risk_score,
        interference_risk_tier=risk_tier,
        downgrade_reasons=downgrade_reasons,
        panel_export_allowed=panel_export_allowed,
        panel_export_caveat=panel_export_caveat,
        source_library_entry_id=assay_entry.source_library_entry_id,
    )


def _assay_transition_statistics(
    transition_rows: tuple[TargetedAssayInterferenceTransitionEntry, ...],
) -> _AssayTransitionStatistics:
    return _AssayTransitionStatistics(
        intrinsic_average=(
            sum(entry.intrinsic_interference_risk_score for entry in transition_rows)
            / len(transition_rows)
            if transition_rows
            else 0.0
        ),
        panel_overlap_total=sum(
            entry.panel_overlap_transition_count for entry in transition_rows
        ),
        background_overlap_total=sum(
            entry.background_overlap_peptide_count for entry in transition_rows
        ),
        library_overlap_total=sum(
            entry.library_overlap_peptide_count for entry in transition_rows
        ),
        coeluting_overlap_total=sum(
            entry.coeluting_library_overlap_peptide_count for entry in transition_rows
        ),
    )


def _build_panel_rows(
    assay_entry: TargetedAssayInterferenceAssayEntry,
    transition_rows: tuple[TargetedAssayInterferenceTransitionEntry, ...],
) -> tuple[TargetedAssayInterferencePanelEntry, ...]:
    if not assay_entry.panel_export_allowed:
        return ()
    return tuple(
        TargetedAssayInterferencePanelEntry(
            assay_entry_id=transition_row.assay_entry_id,
            target_protein_ref=transition_row.target_protein_ref,
            target_protein_group_id=transition_row.target_protein_group_id,
            gene_symbol=transition_row.gene_symbol,
            peptide_sequence=transition_row.peptide_sequence,
            canonical_peptide=transition_row.canonical_peptide,
            precursor_charge=transition_row.precursor_charge,
            precursor_mz=transition_row.precursor_mz,
            fragment_label=transition_row.fragment_label,
            fragment_mz=transition_row.fragment_mz,
            expected_relative_intensity=transition_row.expected_relative_intensity,
            assay_interference_risk_tier=assay_entry.interference_risk_tier,
            transition_interference_risk_tier=transition_row.interference_risk_tier,
            export_caveat=assay_entry.panel_export_caveat,
        )
        for transition_row in transition_rows
        if transition_row.export_allowed
    )


def _ordered_assay_entries(
    assay_rows: list[TargetedAssayInterferenceAssayEntry],
) -> tuple[TargetedAssayInterferenceAssayEntry, ...]:
    return tuple(
        sorted(
            assay_rows,
            key=lambda entry: (
                -entry.interference_risk_score,
                entry.target_protein_ref,
                entry.peptide_rank,
            ),
        )
    )


def _ordered_transition_rows(
    transition_rows: list[TargetedAssayInterferenceTransitionEntry],
) -> tuple[TargetedAssayInterferenceTransitionEntry, ...]:
    return tuple(
        sorted(
            transition_rows,
            key=lambda entry: (
                entry.target_protein_ref,
                entry.peptide_sequence,
                entry.selected_transition_rank,
                entry.fragment_label,
            ),
        )
    )


def _ordered_panel_rows(
    panel_rows: list[TargetedAssayInterferencePanelEntry],
) -> tuple[TargetedAssayInterferencePanelEntry, ...]:
    return tuple(
        sorted(
            panel_rows,
            key=lambda entry: (
                entry.target_protein_ref,
                entry.peptide_sequence,
                entry.fragment_label,
            ),
        )
    )


def _build_summary(
    assay_entries: tuple[TargetedAssayInterferenceAssayEntry, ...],
    transition_entries: tuple[TargetedAssayInterferenceTransitionEntry, ...],
    panel_entries: tuple[TargetedAssayInterferencePanelEntry, ...],
) -> TargetedAssayInterferenceSummary:
    return TargetedAssayInterferenceSummary(
        assay_entry_count=len(assay_entries),
        low_risk_assay_count=sum(
            entry.interference_risk_tier is TargetedAssayInterferenceRiskTier.LOW
            for entry in assay_entries
        ),
        medium_risk_assay_count=sum(
            entry.interference_risk_tier is TargetedAssayInterferenceRiskTier.MEDIUM
            for entry in assay_entries
        ),
        high_risk_assay_count=sum(
            entry.interference_risk_tier is TargetedAssayInterferenceRiskTier.HIGH
            for entry in assay_entries
        ),
        downgraded_assay_count=sum(
            not entry.panel_export_allowed for entry in assay_entries
        ),
        panel_export_assay_count=sum(
            entry.panel_export_allowed for entry in assay_entries
        ),
        transition_entry_count=len(transition_entries),
        panel_export_transition_count=len(panel_entries),
    )


def _shared_peptide_penalty(
    selected_peptide: DiscoveryTargetedPeptideSelectionEntry | None,
) -> float:
    if selected_peptide is None:
        return 0.0
    uniqueness_class = selected_peptide.uniqueness_class
    if uniqueness_class is PeptideUniquenessClass.UNIQUE:
        return 0.0
    if uniqueness_class is PeptideUniquenessClass.ISOFORM_SHARED:
        return 0.25
    if uniqueness_class is PeptideUniquenessClass.FAMILY_SHARED:
        return 0.45
    if uniqueness_class in {
        PeptideUniquenessClass.SHARED,
        PeptideUniquenessClass.MIXED,
    }:
        return 0.65
    return 0.9


def _transition_interference_risk_score(
    *,
    intrinsic_transition_risk_score: float,
    panel_overlap_count: int,
    background_overlap_count: int,
    library_overlap_count: int,
    coeluting_overlap_count: int,
) -> float:
    score = (
        (0.40 * intrinsic_transition_risk_score)
        + (0.20 * min(1.0, panel_overlap_count / 3.0))
        + (0.20 * min(1.0, background_overlap_count / 3.0))
        + (0.10 * min(1.0, library_overlap_count / 2.0))
        + (0.10 * min(1.0, coeluting_overlap_count / 1.0))
    )
    competing_evidence_count = sum(
        1
        for present in (
            panel_overlap_count > 0,
            background_overlap_count > 0,
            library_overlap_count > 0,
            coeluting_overlap_count > 0,
        )
        if present
    )
    if coeluting_overlap_count > 0 and competing_evidence_count >= 3:
        score += 0.10
    elif competing_evidence_count >= 3:
        score += 0.05
    return max(0.0, min(1.0, score))


def _assay_interference_risk_score(
    *,
    shared_penalty: float,
    intrinsic_transition_risk_score: float,
    panel_overlap_transition_count: int,
    background_overlap_peptide_count: int,
    library_overlap_peptide_count: int,
    coeluting_overlap_peptide_count: int,
) -> float:
    score = (
        (0.35 * shared_penalty)
        + (0.15 * intrinsic_transition_risk_score)
        + (0.15 * min(1.0, panel_overlap_transition_count / 5.0))
        + (0.15 * min(1.0, background_overlap_peptide_count / 2.0))
        + (0.10 * min(1.0, library_overlap_peptide_count / 2.0))
        + (0.10 * min(1.0, coeluting_overlap_peptide_count / 1.0))
    )
    competing_evidence_count = sum(
        1
        for present in (
            shared_penalty > 0.0,
            panel_overlap_transition_count > 0,
            background_overlap_peptide_count > 0,
            library_overlap_peptide_count > 0,
            coeluting_overlap_peptide_count > 0,
        )
        if present
    )
    if (
        coeluting_overlap_peptide_count > 0
        and panel_overlap_transition_count > 0
        and background_overlap_peptide_count > 0
    ):
        score += 0.15
    elif competing_evidence_count >= 4:
        score += 0.08
    elif competing_evidence_count >= 3:
        score += 0.04
    return max(0.0, min(1.0, score))


def _transition_downgrade_reasons(
    *,
    intrinsic_transition_risk_score: float,
    panel_overlap_count: int,
    background_overlap_count: int,
    library_overlap_count: int,
    coeluting_overlap_count: int,
) -> tuple[TargetedAssayInterferenceReason, ...]:
    reasons: list[TargetedAssayInterferenceReason] = []
    if intrinsic_transition_risk_score >= 0.4:
        reasons.append(TargetedAssayInterferenceReason.INTRINSIC_TRANSITION_RISK)
    if panel_overlap_count > 0:
        reasons.append(TargetedAssayInterferenceReason.PANEL_FRAGMENT_OVERLAP)
    if background_overlap_count > 0:
        reasons.append(TargetedAssayInterferenceReason.BACKGROUND_PEPTIDE_OVERLAP)
    if library_overlap_count > 0:
        reasons.append(TargetedAssayInterferenceReason.LIBRARY_FRAGMENT_OVERLAP)
    if coeluting_overlap_count > 0:
        reasons.append(TargetedAssayInterferenceReason.LIBRARY_COELUTION_COMPETITOR)
    return tuple(dict.fromkeys(reasons))


def _assay_downgrade_reasons(
    *,
    selected_peptide: DiscoveryTargetedPeptideSelectionEntry | None,
    intrinsic_transition_risk_score: float,
    panel_overlap_transition_count: int,
    background_overlap_peptide_count: int,
    library_overlap_peptide_count: int,
    coeluting_overlap_peptide_count: int,
) -> tuple[TargetedAssayInterferenceReason, ...]:
    reasons: list[TargetedAssayInterferenceReason] = []
    if (
        selected_peptide is not None
        and selected_peptide.uniqueness_class is not PeptideUniquenessClass.UNIQUE
    ):
        reasons.append(TargetedAssayInterferenceReason.SHARED_PEPTIDE)
    if intrinsic_transition_risk_score >= 0.4:
        reasons.append(TargetedAssayInterferenceReason.INTRINSIC_TRANSITION_RISK)
    if panel_overlap_transition_count > 0:
        reasons.append(TargetedAssayInterferenceReason.PANEL_FRAGMENT_OVERLAP)
    if background_overlap_peptide_count > 0:
        reasons.append(TargetedAssayInterferenceReason.BACKGROUND_PEPTIDE_OVERLAP)
    if library_overlap_peptide_count > 0:
        reasons.append(TargetedAssayInterferenceReason.LIBRARY_FRAGMENT_OVERLAP)
    if coeluting_overlap_peptide_count > 0:
        reasons.append(TargetedAssayInterferenceReason.LIBRARY_COELUTION_COMPETITOR)
    return tuple(dict.fromkeys(reasons))


def _risk_tier(score: float) -> TargetedAssayInterferenceRiskTier:
    if score <= 0.25:
        return TargetedAssayInterferenceRiskTier.LOW
    if score <= 0.55:
        return TargetedAssayInterferenceRiskTier.MEDIUM
    return TargetedAssayInterferenceRiskTier.HIGH


def _transition_export_caveat(
    *,
    risk_tier: TargetedAssayInterferenceRiskTier,
    downgrade_reasons: tuple[TargetedAssayInterferenceReason, ...],
) -> str:
    if risk_tier is TargetedAssayInterferenceRiskTier.HIGH:
        return (
            "transition is withheld from panel export because pre-acquisition "
            "interference evidence is high risk"
        )
    if downgrade_reasons:
        return (
            "transition remains exportable but carries explicit pre-acquisition "
            "interference caveats"
        )
    return "transition is exportable without additional pre-acquisition interference caveats"


def _assay_export_caveat(
    *,
    risk_tier: TargetedAssayInterferenceRiskTier,
    panel_export_allowed: bool,
    downgrade_reasons: tuple[TargetedAssayInterferenceReason, ...],
) -> str:
    if not panel_export_allowed:
        return (
            "assay is downgraded out of panel export because interference evidence "
            "or surviving transition support is insufficient before acquisition"
        )
    if risk_tier is TargetedAssayInterferenceRiskTier.MEDIUM or downgrade_reasons:
        return "assay remains exportable with explicit pre-acquisition interference caveats"
    return "assay is exportable without additional pre-acquisition interference caveats"
