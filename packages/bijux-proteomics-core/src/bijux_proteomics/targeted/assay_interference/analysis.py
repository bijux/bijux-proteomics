# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Pre-acquisition assay interference scoring for targeted follow-up panels."""

from __future__ import annotations

from bijux_proteomics.chemistry import (
    FragmentIonSeries,
    calculate_fragment_ions,
    calculate_peptide_mz,
)
from bijux_proteomics.io import SpectralLibraryEntry
from bijux_proteomics.sequences import (
    NormalizedProteinRecord,
    PeptideUniquenessClass,
)
from bijux_proteomics.sequences.digestion import (
    DigestedPeptide,
    PeptideDigestionMode,
    ProteaseRule,
    digest_protein_records,
    get_protease_rule,
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
from bijux_proteomics.targeted.discovery_peptide_selection import (
    DiscoveryTargetedPeptideSelectionEntry,
)
from bijux_proteomics.targeted.transition_selection import (
    TargetedTransitionSelectionPeptideEntry,
)

_DEFAULT_PRECURSOR_TOLERANCE_DA = 1.0
_DEFAULT_FRAGMENT_TOLERANCE_DA = 0.02
_DEFAULT_COELUTION_RT_WINDOW_MINUTES = 0.5
_DEFAULT_MIN_EXPORT_TRANSITIONS = 3


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

    protease_rule = (
        get_protease_rule(protease) if isinstance(protease, str) else protease
    )
    selected_by_key = {
        _selected_peptide_key(entry): entry for entry in selected_peptides
    }
    digested_peptides = digest_protein_records(
        protein_records,
        protease=protease_rule,
        missed_cleavages=missed_cleavages,
        mode=PeptideDigestionMode.FULL,
    )
    digested_by_sequence = _group_digested_peptides(digested_peptides)
    source_library_by_id = {
        entry.library_entry_id: entry for entry in spectral_library_entries
    }

    transition_rows: list[TargetedAssayInterferenceTransitionEntry] = []
    assay_rows: list[TargetedAssayInterferenceAssayEntry] = []
    panel_rows: list[TargetedAssayInterferencePanelEntry] = []
    for assay_entry in sorted(
        transition_entries,
        key=lambda entry: (
            entry.target_protein_ref,
            entry.peptide_rank,
            entry.canonical_peptide,
        ),
    ):
        selected_peptide = selected_by_key.get(
            (
                assay_entry.target_protein_ref,
                assay_entry.canonical_peptide,
                assay_entry.peptide_rank,
            )
        )
        shared_penalty = _shared_peptide_penalty(selected_peptide)
        source_library_entry = (
            None
            if assay_entry.source_library_entry_id is None
            else source_library_by_id.get(assay_entry.source_library_entry_id)
        )
        competing_background = _background_competitor_peptides(
            assay_entry,
            digested_by_sequence=digested_by_sequence,
            precursor_tolerance_da=precursor_tolerance_da,
        )
        competing_library_entries = _library_competitor_entries(
            assay_entry,
            source_library_entry=source_library_entry,
            spectral_library_entries=spectral_library_entries,
            precursor_tolerance_da=precursor_tolerance_da,
        )

        assay_transition_rows: list[TargetedAssayInterferenceTransitionEntry] = []
        for transition in assay_entry.selected_transitions:
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
            library_overlap_count, coeluting_overlap_count = (
                _count_library_fragment_overlaps(
                    competing_library_entries,
                    source_library_entry=source_library_entry,
                    fragment_mz=transition.fragment_mz,
                    fragment_charge=transition.fragment_charge,
                    fragment_tolerance_da=fragment_tolerance_da,
                    coelution_rt_window_minutes=coelution_rt_window_minutes,
                )
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
            export_allowed = risk_tier is not TargetedAssayInterferenceRiskTier.HIGH
            assay_transition_rows.append(
                TargetedAssayInterferenceTransitionEntry(
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
                    export_allowed=export_allowed,
                    export_caveat=_transition_export_caveat(
                        risk_tier=risk_tier,
                        downgrade_reasons=downgrade_reasons,
                    ),
                )
            )

        intrinsic_average = (
            sum(
                entry.intrinsic_interference_risk_score
                for entry in assay_transition_rows
            )
            / len(assay_transition_rows)
            if assay_transition_rows
            else 0.0
        )
        panel_overlap_total = sum(
            entry.panel_overlap_transition_count for entry in assay_transition_rows
        )
        background_overlap_total = sum(
            entry.background_overlap_peptide_count for entry in assay_transition_rows
        )
        library_overlap_total = sum(
            entry.library_overlap_peptide_count for entry in assay_transition_rows
        )
        coeluting_overlap_total = sum(
            entry.coeluting_library_overlap_peptide_count
            for entry in assay_transition_rows
        )
        assay_risk_score = _assay_interference_risk_score(
            shared_penalty=shared_penalty,
            intrinsic_transition_risk_score=intrinsic_average,
            panel_overlap_transition_count=panel_overlap_total,
            background_overlap_peptide_count=background_overlap_total,
            library_overlap_peptide_count=library_overlap_total,
            coeluting_overlap_peptide_count=coeluting_overlap_total,
        )
        risk_tier = _risk_tier(assay_risk_score)
        export_transition_rows = [
            entry for entry in assay_transition_rows if entry.export_allowed
        ]
        downgrade_reasons = _assay_downgrade_reasons(
            selected_peptide=selected_peptide,
            intrinsic_transition_risk_score=intrinsic_average,
            panel_overlap_transition_count=panel_overlap_total,
            background_overlap_peptide_count=background_overlap_total,
            library_overlap_peptide_count=library_overlap_total,
            coeluting_overlap_peptide_count=coeluting_overlap_total,
        )
        panel_export_allowed = (
            risk_tier is not TargetedAssayInterferenceRiskTier.HIGH
            and len(export_transition_rows) >= minimum_export_transitions
        )
        if len(export_transition_rows) < minimum_export_transitions:
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
        assay_rows.append(
            TargetedAssayInterferenceAssayEntry(
                assay_entry_id=assay_entry.assay_entry_id,
                target_protein_ref=assay_entry.target_protein_ref,
                target_protein_group_id=assay_entry.target_protein_group_id,
                gene_symbol=assay_entry.gene_symbol,
                peptide_sequence=assay_entry.peptide_sequence,
                canonical_peptide=assay_entry.canonical_peptide,
                peptide_rank=assay_entry.peptide_rank,
                precursor_charge=assay_entry.precursor_charge,
                precursor_mz=assay_entry.precursor_mz,
                selected_transition_count=len(assay_transition_rows),
                exported_transition_count=(
                    len(export_transition_rows) if panel_export_allowed else 0
                ),
                shared_peptide_penalty=shared_penalty,
                panel_overlap_transition_count=panel_overlap_total,
                background_overlap_peptide_count=background_overlap_total,
                library_overlap_peptide_count=library_overlap_total,
                coeluting_library_overlap_peptide_count=coeluting_overlap_total,
                intrinsic_transition_risk_score=intrinsic_average,
                interference_risk_score=assay_risk_score,
                interference_risk_tier=risk_tier,
                downgrade_reasons=downgrade_reasons,
                panel_export_allowed=panel_export_allowed,
                panel_export_caveat=panel_export_caveat,
                source_library_entry_id=assay_entry.source_library_entry_id,
            )
        )
        for transition_row in assay_transition_rows:
            transition_rows.append(transition_row)
            if panel_export_allowed and transition_row.export_allowed:
                panel_rows.append(
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
                        assay_interference_risk_tier=risk_tier,
                        transition_interference_risk_tier=transition_row.interference_risk_tier,
                        export_caveat=panel_export_caveat,
                    )
                )

    ordered_assays = tuple(
        sorted(
            assay_rows,
            key=lambda entry: (
                -entry.interference_risk_score,
                entry.target_protein_ref,
                entry.peptide_rank,
            ),
        )
    )
    ordered_transitions = tuple(
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
    ordered_panel = tuple(
        sorted(
            panel_rows,
            key=lambda entry: (
                entry.target_protein_ref,
                entry.peptide_sequence,
                entry.fragment_label,
            ),
        )
    )
    return TargetedAssayInterferenceReport(
        protease=protease_rule.name,
        missed_cleavages=missed_cleavages,
        precursor_tolerance_da=precursor_tolerance_da,
        fragment_tolerance_da=fragment_tolerance_da,
        coelution_rt_window_minutes=coelution_rt_window_minutes,
        minimum_export_transitions=minimum_export_transitions,
        summary=TargetedAssayInterferenceSummary(
            assay_entry_count=len(ordered_assays),
            low_risk_assay_count=sum(
                1
                for entry in ordered_assays
                if entry.interference_risk_tier is TargetedAssayInterferenceRiskTier.LOW
            ),
            medium_risk_assay_count=sum(
                1
                for entry in ordered_assays
                if entry.interference_risk_tier
                is TargetedAssayInterferenceRiskTier.MEDIUM
            ),
            high_risk_assay_count=sum(
                1
                for entry in ordered_assays
                if entry.interference_risk_tier
                is TargetedAssayInterferenceRiskTier.HIGH
            ),
            downgraded_assay_count=sum(
                1 for entry in ordered_assays if not entry.panel_export_allowed
            ),
            panel_export_assay_count=sum(
                1 for entry in ordered_assays if entry.panel_export_allowed
            ),
            transition_entry_count=len(ordered_transitions),
            panel_export_transition_count=len(ordered_panel),
        ),
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


def _selected_peptide_key(
    entry: DiscoveryTargetedPeptideSelectionEntry,
) -> tuple[str, str, int]:
    return (entry.target_protein_ref, entry.canonical_peptide, entry.rank)


def _group_digested_peptides(
    peptides: tuple[DigestedPeptide, ...],
) -> dict[str, tuple[DigestedPeptide, ...]]:
    grouped: dict[str, list[DigestedPeptide]] = {}
    for peptide in peptides:
        grouped.setdefault(peptide.sequence, []).append(peptide)
    return {key: tuple(value) for key, value in grouped.items()}


def _background_competitor_peptides(
    assay_entry: TargetedTransitionSelectionPeptideEntry,
    *,
    digested_by_sequence: dict[str, tuple[DigestedPeptide, ...]],
    precursor_tolerance_da: float,
) -> tuple[str, ...]:
    competing_sequences: list[str] = []
    for sequence in sorted(digested_by_sequence):
        if sequence == assay_entry.peptide_sequence:
            continue
        competitor_precursor_mz = calculate_peptide_mz(
            sequence,
            charge=assay_entry.precursor_charge,
        )
        if (
            abs(competitor_precursor_mz - assay_entry.precursor_mz)
            <= precursor_tolerance_da
        ):
            competing_sequences.append(sequence)
    return tuple(competing_sequences)


def _library_competitor_entries(
    assay_entry: TargetedTransitionSelectionPeptideEntry,
    *,
    source_library_entry: SpectralLibraryEntry | None,
    spectral_library_entries: tuple[SpectralLibraryEntry, ...],
    precursor_tolerance_da: float,
) -> tuple[SpectralLibraryEntry, ...]:
    competitors = [
        entry
        for entry in spectral_library_entries
        if entry.canonical_peptide != assay_entry.canonical_peptide
        and abs(entry.precursor_mz - assay_entry.precursor_mz) <= precursor_tolerance_da
        and (
            source_library_entry is None
            or entry.library_entry_id != source_library_entry.library_entry_id
        )
    ]
    return tuple(
        sorted(
            competitors,
            key=lambda entry: (
                abs(entry.precursor_mz - assay_entry.precursor_mz),
                entry.canonical_peptide,
                entry.library_entry_id,
            ),
        )
    )


def _count_panel_fragment_overlaps(
    *,
    assay_entry_id: str,
    precursor_mz: float,
    fragment_mz: float,
    all_transition_entries: tuple[TargetedTransitionSelectionPeptideEntry, ...],
    precursor_tolerance_da: float,
    fragment_tolerance_da: float,
) -> int:
    overlap_count = 0
    for assay_entry in all_transition_entries:
        if assay_entry.assay_entry_id == assay_entry_id:
            continue
        if abs(assay_entry.precursor_mz - precursor_mz) > precursor_tolerance_da:
            continue
        overlap_count += sum(
            1
            for transition in assay_entry.selected_transitions
            if abs(transition.fragment_mz - fragment_mz) <= fragment_tolerance_da
        )
    return overlap_count


def _count_background_fragment_overlaps(
    background_sequences: tuple[str, ...],
    *,
    fragment_mz: float,
    fragment_charge: int,
    fragment_tolerance_da: float,
) -> int:
    overlap_count = 0
    for sequence in background_sequences:
        fragments = calculate_fragment_ions(
            sequence,
            charges=(fragment_charge,),
            series=(FragmentIonSeries.B, FragmentIonSeries.Y),
            include_neutral_losses=False,
        )
        if any(
            abs(candidate.mz_monoisotopic - fragment_mz) <= fragment_tolerance_da
            for candidate in fragments
        ):
            overlap_count += 1
    return overlap_count


def _count_library_fragment_overlaps(
    library_entries: tuple[SpectralLibraryEntry, ...],
    *,
    source_library_entry: SpectralLibraryEntry | None,
    fragment_mz: float,
    fragment_charge: int,
    fragment_tolerance_da: float,
    coelution_rt_window_minutes: float,
) -> tuple[int, int]:
    overlap_count = 0
    coeluting_count = 0
    for entry in library_entries:
        fragments = calculate_fragment_ions(
            entry.canonical_peptide,
            charges=(fragment_charge,),
            series=(FragmentIonSeries.B, FragmentIonSeries.Y),
            include_neutral_losses=False,
        )
        if not any(
            abs(candidate.mz_monoisotopic - fragment_mz) <= fragment_tolerance_da
            for candidate in fragments
        ):
            continue
        overlap_count += 1
        if (
            source_library_entry is not None
            and source_library_entry.spectrum.retention_time_seconds is not None
            and entry.spectrum.retention_time_seconds is not None
            and abs(
                source_library_entry.spectrum.retention_time_seconds
                - entry.spectrum.retention_time_seconds
            )
            / 60.0
            <= coelution_rt_window_minutes
        ):
            coeluting_count += 1
    return overlap_count, coeluting_count


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
