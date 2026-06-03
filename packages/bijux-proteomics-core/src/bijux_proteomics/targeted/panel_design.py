# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Build reviewable targeted transition panels from owned assay-design surfaces."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.peptide_evidence import PeptideEvidenceClass
from bijux_proteomics.io import SpectralLibraryEntry
from bijux_proteomics.sequences import (
    PeptideChemicalLiabilityTier,
    PeptideDetectabilityTier,
    PeptideUniquenessClass,
)
from bijux_proteomics.targeted.assay_interference import (
    TargetedAssayInterferenceReason,
    TargetedAssayInterferenceRiskTier,
)
from bijux_proteomics_foundation import JsonModel

_DEFAULT_RETENTION_WINDOW_RADIUS_MINUTES = 1.5


class TargetedPanelCandidateKind(StrEnum):
    """Stable biomarker-candidate classes supported by targeted panel design."""

    PROTEIN = "protein"
    PTM_SITE = "ptm_site"


class TargetedPanelWarningCode(StrEnum):
    """Stable warnings preserved on targeted panel rows."""

    CANDIDATE_PENALIZED = "candidate_penalized"
    ELEVATED_INTERFERENCE_RISK = "elevated_interference_risk"
    MISSING_EXPECTED_RETENTION_TIME = "missing_expected_retention_time"
    NON_UNIQUE_TARGET = "non_unique_target"
    REDUCED_TRANSITION_SUPPORT = "reduced_transition_support"


class TargetedPanelBiomarkerCandidateInput(JsonModel):
    """Minimal biomarker-candidate context needed for targeted panel assembly."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_kind: TargetedPanelCandidateKind
    display_label: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    site_key: str | None = None
    priority_rank: int = Field(..., ge=1)
    final_score: float = Field(..., ge=0.0, le=1.0)
    penalty_total: float = Field(..., ge=0.0)
    rank_reason_codes: tuple[str, ...] = Field(default_factory=tuple)


class TargetedPanelSelectedPeptideInput(JsonModel):
    """Minimal selected-peptide context needed for targeted panel assembly."""

    model_config = ConfigDict(extra="forbid")

    target_protein_ref: str = Field(..., min_length=1)
    target_protein_group_id: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    rank: int = Field(..., ge=1)
    observed_in_discovery: bool
    observed_psm_count: int | None = Field(default=None, ge=0)
    run_count: int | None = Field(default=None, ge=0)
    detection_frequency: float | None = Field(default=None, ge=0.0, le=1.0)
    replicate_consistency: float | None = Field(default=None, ge=0.0, le=1.0)
    primary_evidence_class: PeptideEvidenceClass | None = None
    uniqueness_class: PeptideUniquenessClass
    uniqueness_score: float = Field(..., ge=0.0, le=1.0)
    detectability_score: float = Field(..., ge=0.0, le=1.0)
    detectability_tier: PeptideDetectabilityTier
    suitability_score: float = Field(..., ge=0.0, le=1.0)
    liability_tier: PeptideChemicalLiabilityTier
    liability_codes: tuple[str, ...] = Field(default_factory=tuple)
    selection_score: float = Field(..., ge=0.0, le=1.0)
    selection_reasons: tuple[str, ...] = Field(default_factory=tuple)


class TargetedPanelAssayInput(JsonModel):
    """Minimal assay-level interference context needed for panel assembly."""

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
    selected_transition_count: int = Field(..., ge=0)
    exported_transition_count: int = Field(..., ge=0)
    interference_risk_score: float = Field(..., ge=0.0, le=1.0)
    interference_risk_tier: TargetedAssayInterferenceRiskTier
    downgrade_reasons: tuple[TargetedAssayInterferenceReason, ...] = Field(
        default_factory=tuple
    )
    panel_export_allowed: bool
    panel_export_caveat: str = Field(..., min_length=1)
    source_library_entry_id: str | None = None


class TargetedPanelTransitionInput(JsonModel):
    """Minimal retained transition context needed for panel assembly."""

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
    ion_type: str = Field(..., min_length=1)
    fragment_ordinal: int = Field(..., ge=1)
    fragment_charge: int = Field(..., ge=1)
    fragment_sequence: str = Field(..., min_length=1)
    fragment_mz: float = Field(..., gt=0.0)
    expected_relative_intensity: float | None = Field(default=None, ge=0.0, le=1.0)
    selected_transition_rank: int = Field(..., ge=1)
    interference_risk_score: float = Field(..., ge=0.0, le=1.0)
    interference_risk_tier: TargetedAssayInterferenceRiskTier
    downgrade_reasons: tuple[TargetedAssayInterferenceReason, ...] = Field(
        default_factory=tuple
    )
    export_allowed: bool
    export_caveat: str = Field(..., min_length=1)


class TargetedPanelAssayEntry(JsonModel):
    """One peptide-target assay promoted into the targeted panel."""

    model_config = ConfigDict(extra="forbid")

    assay_entry_id: str = Field(..., min_length=1)
    biomarker_candidate_id: str = Field(..., min_length=1)
    biomarker_candidate_kind: TargetedPanelCandidateKind
    biomarker_display_label: str = Field(..., min_length=1)
    biomarker_priority_rank: int = Field(..., ge=1)
    target_protein_ref: str = Field(..., min_length=1)
    target_protein_group_id: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    uniqueness_class: PeptideUniquenessClass
    uniqueness_score: float = Field(..., ge=0.0, le=1.0)
    precursor_charge: int = Field(..., ge=1)
    precursor_mz: float = Field(..., gt=0.0)
    expected_retention_time_minutes: float | None = Field(default=None, ge=0.0)
    retention_window_start_minutes: float | None = Field(default=None, ge=0.0)
    retention_window_end_minutes: float | None = Field(default=None, ge=0.0)
    selected_transition_count: int = Field(..., ge=0)
    exported_transition_count: int = Field(..., ge=0)
    assay_interference_risk_tier: TargetedAssayInterferenceRiskTier
    warning_codes: tuple[TargetedPanelWarningCode, ...] = Field(default_factory=tuple)
    warning_note: str = Field(..., min_length=1)
    source_library_entry_id: str | None = None


class TargetedPanelTransitionEntry(JsonModel):
    """One transition-list row that can be reviewed directly or imported downstream."""

    model_config = ConfigDict(extra="forbid")

    transition_id: str = Field(..., min_length=1)
    precursor_id: str = Field(..., min_length=1)
    assay_entry_id: str = Field(..., min_length=1)
    biomarker_candidate_id: str = Field(..., min_length=1)
    biomarker_candidate_kind: TargetedPanelCandidateKind
    biomarker_priority_rank: int = Field(..., ge=1)
    target_protein_ref: str = Field(..., min_length=1)
    target_protein_group_id: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    uniqueness_class: PeptideUniquenessClass
    uniqueness_score: float = Field(..., ge=0.0, le=1.0)
    precursor_charge: int = Field(..., ge=1)
    precursor_mz: float = Field(..., gt=0.0)
    fragment_label: str = Field(..., min_length=1)
    ion_type: str = Field(..., min_length=1)
    fragment_ordinal: int = Field(..., ge=1)
    fragment_charge: int = Field(..., ge=1)
    fragment_sequence: str = Field(..., min_length=1)
    fragment_mz: float = Field(..., gt=0.0)
    expected_relative_intensity: float | None = Field(default=None, ge=0.0, le=1.0)
    expected_retention_time_minutes: float | None = Field(default=None, ge=0.0)
    retention_window_start_minutes: float | None = Field(default=None, ge=0.0)
    retention_window_end_minutes: float | None = Field(default=None, ge=0.0)
    assay_interference_risk_tier: TargetedAssayInterferenceRiskTier
    transition_interference_risk_tier: TargetedAssayInterferenceRiskTier
    warning_codes: tuple[TargetedPanelWarningCode, ...] = Field(default_factory=tuple)
    warning_note: str = Field(..., min_length=1)


class TargetedPanelOmittedCandidateEntry(JsonModel):
    """One biomarker candidate left out of the final targeted panel with a stable reason."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_kind: TargetedPanelCandidateKind
    display_label: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    site_key: str | None = None
    priority_rank: int = Field(..., ge=1)
    omission_reason: str = Field(..., min_length=1)


class TargetedPanelDesignSummary(JsonModel):
    """Compact accounting over one targeted panel design pass."""

    model_config = ConfigDict(extra="forbid")

    biomarker_candidate_count: int = Field(..., ge=0)
    retained_assay_count: int = Field(..., ge=0)
    panel_transition_count: int = Field(..., ge=0)
    omitted_candidate_count: int = Field(..., ge=0)
    assay_with_expected_retention_time_count: int = Field(..., ge=0)
    warning_entry_count: int = Field(..., ge=0)


class TargetedPanelDesignReport(JsonModel):
    """Owned targeted panel design from ranked biomarker and assay-design evidence."""

    model_config = ConfigDict(extra="forbid")

    retention_window_radius_minutes: float = Field(..., gt=0.0)
    summary: TargetedPanelDesignSummary
    assay_entries: tuple[TargetedPanelAssayEntry, ...] = Field(default_factory=tuple)
    panel_entries: tuple[TargetedPanelTransitionEntry, ...] = Field(
        default_factory=tuple
    )
    omitted_candidates: tuple[TargetedPanelOmittedCandidateEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


def build_targeted_panel_design_report(
    biomarker_candidates: tuple[TargetedPanelBiomarkerCandidateInput, ...],
    selected_peptides: tuple[TargetedPanelSelectedPeptideInput, ...],
    assay_entries: tuple[TargetedPanelAssayInput, ...],
    transition_entries: tuple[TargetedPanelTransitionInput, ...],
    *,
    spectral_library_entries: tuple[SpectralLibraryEntry, ...] = (),
    retention_window_radius_minutes: float = _DEFAULT_RETENTION_WINDOW_RADIUS_MINUTES,
) -> TargetedPanelDesignReport:
    """Build a reviewable targeted panel from retained assays and transitions."""

    if retention_window_radius_minutes <= 0.0:
        raise ValueError("retention_window_radius_minutes must be greater than zero")

    protein_candidates_by_ref: dict[
        str, list[TargetedPanelBiomarkerCandidateInput]
    ] = {}
    omitted_candidates: list[TargetedPanelOmittedCandidateEntry] = []
    for candidate in sorted(
        biomarker_candidates,
        key=lambda item: (
            item.priority_rank,
            item.target_protein_ref,
            item.candidate_id,
        ),
    ):
        if candidate.candidate_kind is TargetedPanelCandidateKind.PROTEIN:
            protein_candidates_by_ref.setdefault(
                candidate.target_protein_ref, []
            ).append(candidate)
        else:
            omitted_candidates.append(
                TargetedPanelOmittedCandidateEntry(
                    candidate_id=candidate.candidate_id,
                    candidate_kind=candidate.candidate_kind,
                    display_label=candidate.display_label,
                    target_protein_ref=candidate.target_protein_ref,
                    site_key=candidate.site_key,
                    priority_rank=candidate.priority_rank,
                    omission_reason=(
                        "PTM-site candidate requires site-specific targeted assay design; "
                        "protein-level peptide panels are not promoted as PTM validation by default"
                    ),
                )
            )

    selected_by_key = {
        (entry.target_protein_ref, entry.canonical_peptide, entry.rank): entry
        for entry in selected_peptides
    }
    assay_by_id = {entry.assay_entry_id: entry for entry in assay_entries}
    retained_transitions_by_assay: dict[str, list[TargetedPanelTransitionInput]] = {}
    for transition in transition_entries:
        assay = assay_by_id.get(transition.assay_entry_id)
        if (
            assay is None
            or not assay.panel_export_allowed
            or not transition.export_allowed
        ):
            continue
        retained_transitions_by_assay.setdefault(transition.assay_entry_id, []).append(
            transition
        )
    library_by_id = {
        entry.library_entry_id: entry for entry in spectral_library_entries
    }

    matched_candidate_ids: set[str] = set()
    assay_rows: list[TargetedPanelAssayEntry] = []
    panel_rows: list[TargetedPanelTransitionEntry] = []
    for assay in sorted(
        assay_entries,
        key=lambda item: (
            _candidate_priority_rank_for_protein(
                protein_candidates_by_ref.get(item.target_protein_ref, ())
            ),
            item.target_protein_ref,
            item.peptide_rank,
            item.assay_entry_id,
        ),
    ):
        if not assay.panel_export_allowed:
            continue
        protein_candidate = _best_candidate_for_protein(
            protein_candidates_by_ref.get(assay.target_protein_ref, ())
        )
        if protein_candidate is None:
            continue
        retained_transitions = tuple(
            sorted(
                retained_transitions_by_assay.get(assay.assay_entry_id, ()),
                key=lambda item: (
                    item.selected_transition_rank,
                    item.fragment_mz,
                    item.fragment_label,
                ),
            )
        )
        if not retained_transitions:
            continue
        selected_peptide = selected_by_key.get(
            (assay.target_protein_ref, assay.canonical_peptide, assay.peptide_rank)
        )
        expected_retention_time_minutes = _expected_retention_time_minutes(
            assay.source_library_entry_id,
            library_by_id=library_by_id,
        )
        retention_window = _retention_window(
            expected_retention_time_minutes,
            radius_minutes=retention_window_radius_minutes,
        )
        warning_codes = _warning_codes_for_assay(
            candidate=protein_candidate,
            selected_peptide=selected_peptide,
            assay=assay,
            expected_retention_time_minutes=expected_retention_time_minutes,
        )
        warning_note = _warning_note_for_assay(
            candidate=protein_candidate,
            selected_peptide=selected_peptide,
            assay=assay,
            expected_retention_time_minutes=expected_retention_time_minutes,
            warning_codes=warning_codes,
        )
        assay_rows.append(
            TargetedPanelAssayEntry(
                assay_entry_id=assay.assay_entry_id,
                biomarker_candidate_id=protein_candidate.candidate_id,
                biomarker_candidate_kind=protein_candidate.candidate_kind,
                biomarker_display_label=protein_candidate.display_label,
                biomarker_priority_rank=protein_candidate.priority_rank,
                target_protein_ref=assay.target_protein_ref,
                target_protein_group_id=assay.target_protein_group_id,
                gene_symbol=assay.gene_symbol,
                peptide_sequence=assay.peptide_sequence,
                canonical_peptide=assay.canonical_peptide,
                uniqueness_class=(
                    PeptideUniquenessClass.UNIQUE
                    if selected_peptide is None
                    else selected_peptide.uniqueness_class
                ),
                uniqueness_score=(
                    1.0
                    if selected_peptide is None
                    else selected_peptide.uniqueness_score
                ),
                precursor_charge=assay.precursor_charge,
                precursor_mz=assay.precursor_mz,
                expected_retention_time_minutes=expected_retention_time_minutes,
                retention_window_start_minutes=retention_window[0],
                retention_window_end_minutes=retention_window[1],
                selected_transition_count=assay.selected_transition_count,
                exported_transition_count=assay.exported_transition_count,
                assay_interference_risk_tier=assay.interference_risk_tier,
                warning_codes=warning_codes,
                warning_note=warning_note,
                source_library_entry_id=assay.source_library_entry_id,
            )
        )
        for transition in retained_transitions:
            panel_rows.append(
                TargetedPanelTransitionEntry(
                    transition_id=(
                        f"{assay.assay_entry_id}:{transition.fragment_label}"
                    ),
                    precursor_id=assay.assay_entry_id,
                    assay_entry_id=assay.assay_entry_id,
                    biomarker_candidate_id=protein_candidate.candidate_id,
                    biomarker_candidate_kind=protein_candidate.candidate_kind,
                    biomarker_priority_rank=protein_candidate.priority_rank,
                    target_protein_ref=assay.target_protein_ref,
                    target_protein_group_id=assay.target_protein_group_id,
                    gene_symbol=assay.gene_symbol,
                    peptide_sequence=assay.peptide_sequence,
                    canonical_peptide=assay.canonical_peptide,
                    uniqueness_class=(
                        PeptideUniquenessClass.UNIQUE
                        if selected_peptide is None
                        else selected_peptide.uniqueness_class
                    ),
                    uniqueness_score=(
                        1.0
                        if selected_peptide is None
                        else selected_peptide.uniqueness_score
                    ),
                    precursor_charge=assay.precursor_charge,
                    precursor_mz=assay.precursor_mz,
                    fragment_label=transition.fragment_label,
                    ion_type=transition.ion_type,
                    fragment_ordinal=transition.fragment_ordinal,
                    fragment_charge=transition.fragment_charge,
                    fragment_sequence=transition.fragment_sequence,
                    fragment_mz=transition.fragment_mz,
                    expected_relative_intensity=transition.expected_relative_intensity,
                    expected_retention_time_minutes=expected_retention_time_minutes,
                    retention_window_start_minutes=retention_window[0],
                    retention_window_end_minutes=retention_window[1],
                    assay_interference_risk_tier=assay.interference_risk_tier,
                    transition_interference_risk_tier=transition.interference_risk_tier,
                    warning_codes=warning_codes,
                    warning_note=warning_note,
                )
            )
        matched_candidate_ids.add(protein_candidate.candidate_id)

    for candidate in biomarker_candidates:
        if candidate.candidate_id in matched_candidate_ids:
            continue
        if candidate.candidate_kind is TargetedPanelCandidateKind.PTM_SITE:
            continue
        omitted_candidates.append(
            TargetedPanelOmittedCandidateEntry(
                candidate_id=candidate.candidate_id,
                candidate_kind=candidate.candidate_kind,
                display_label=candidate.display_label,
                target_protein_ref=candidate.target_protein_ref,
                site_key=candidate.site_key,
                priority_rank=candidate.priority_rank,
                omission_reason=(
                    "no retained targeted assay survived peptide selection and interference scoring "
                    "for this ranked biomarker candidate"
                ),
            )
        )

    ordered_assays = tuple(
        sorted(
            assay_rows,
            key=lambda entry: (
                entry.biomarker_priority_rank,
                entry.target_protein_ref,
                entry.assay_entry_id,
            ),
        )
    )
    ordered_panel = tuple(
        sorted(
            panel_rows,
            key=lambda entry: (
                entry.biomarker_priority_rank,
                entry.target_protein_ref,
                entry.assay_entry_id,
                entry.fragment_mz,
                entry.fragment_label,
            ),
        )
    )
    ordered_omitted = tuple(
        sorted(
            omitted_candidates,
            key=lambda entry: (
                entry.priority_rank,
                entry.target_protein_ref,
                entry.candidate_id,
            ),
        )
    )
    return TargetedPanelDesignReport(
        retention_window_radius_minutes=retention_window_radius_minutes,
        summary=TargetedPanelDesignSummary(
            biomarker_candidate_count=len(biomarker_candidates),
            retained_assay_count=len(ordered_assays),
            panel_transition_count=len(ordered_panel),
            omitted_candidate_count=len(ordered_omitted),
            assay_with_expected_retention_time_count=sum(
                1
                for entry in ordered_assays
                if entry.expected_retention_time_minutes is not None
            ),
            warning_entry_count=sum(
                1 for entry in ordered_assays if entry.warning_codes
            ),
        ),
        assay_entries=ordered_assays,
        panel_entries=ordered_panel,
        omitted_candidates=ordered_omitted,
        note=(
            "targeted panel design assembles protein-backed biomarker candidates into "
            "reviewable transition-list rows with peptide uniqueness, retained transitions, "
            "expected retention time when governed library evidence exists, and explicit warnings"
        ),
    )


def render_targeted_panel_design_summary_tsv(
    report: TargetedPanelDesignReport,
) -> str:
    """Render compact targeted panel-design accounting as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(
        (
            "retention_window_radius_minutes",
            f"{report.retention_window_radius_minutes:.6f}",
        )
    )
    writer.writerow(
        ("biomarker_candidate_count", report.summary.biomarker_candidate_count)
    )
    writer.writerow(("retained_assay_count", report.summary.retained_assay_count))
    writer.writerow(("panel_transition_count", report.summary.panel_transition_count))
    writer.writerow(("omitted_candidate_count", report.summary.omitted_candidate_count))
    writer.writerow(
        (
            "assay_with_expected_retention_time_count",
            report.summary.assay_with_expected_retention_time_count,
        )
    )
    writer.writerow(("warning_entry_count", report.summary.warning_entry_count))
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_targeted_panel_design_assay_tsv(
    report: TargetedPanelDesignReport,
) -> str:
    """Render assay-level targeted panel design rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "assay_entry_id",
            "biomarker_candidate_id",
            "biomarker_candidate_kind",
            "biomarker_display_label",
            "biomarker_priority_rank",
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "peptide_sequence",
            "canonical_peptide",
            "uniqueness_class",
            "uniqueness_score",
            "precursor_charge",
            "precursor_mz",
            "expected_retention_time_minutes",
            "retention_window_start_minutes",
            "retention_window_end_minutes",
            "selected_transition_count",
            "exported_transition_count",
            "assay_interference_risk_tier",
            "warning_codes",
            "warning_note",
            "source_library_entry_id",
        )
    )
    for entry in report.assay_entries:
        writer.writerow(
            (
                entry.assay_entry_id,
                entry.biomarker_candidate_id,
                entry.biomarker_candidate_kind.value,
                entry.biomarker_display_label,
                entry.biomarker_priority_rank,
                entry.target_protein_ref,
                entry.target_protein_group_id,
                "" if entry.gene_symbol is None else entry.gene_symbol,
                entry.peptide_sequence,
                entry.canonical_peptide,
                entry.uniqueness_class.value,
                f"{entry.uniqueness_score:.6f}",
                entry.precursor_charge,
                f"{entry.precursor_mz:.6f}",
                ""
                if entry.expected_retention_time_minutes is None
                else f"{entry.expected_retention_time_minutes:.6f}",
                ""
                if entry.retention_window_start_minutes is None
                else f"{entry.retention_window_start_minutes:.6f}",
                ""
                if entry.retention_window_end_minutes is None
                else f"{entry.retention_window_end_minutes:.6f}",
                entry.selected_transition_count,
                entry.exported_transition_count,
                entry.assay_interference_risk_tier.value,
                ";".join(code.value for code in entry.warning_codes),
                entry.warning_note,
                ""
                if entry.source_library_entry_id is None
                else entry.source_library_entry_id,
            )
        )
    return handle.getvalue()


def render_targeted_panel_design_panel_tsv(
    report: TargetedPanelDesignReport,
) -> str:
    """Render transition-list-style targeted panel rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "transition_id",
            "precursor_id",
            "assay_entry_id",
            "biomarker_candidate_id",
            "biomarker_candidate_kind",
            "biomarker_priority_rank",
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "peptide_sequence",
            "canonical_peptide",
            "uniqueness_class",
            "uniqueness_score",
            "precursor_charge",
            "precursor_mz",
            "fragment_label",
            "ion_type",
            "fragment_ordinal",
            "fragment_charge",
            "fragment_sequence",
            "fragment_mz",
            "expected_relative_intensity",
            "expected_retention_time_minutes",
            "retention_window_start_minutes",
            "retention_window_end_minutes",
            "assay_interference_risk_tier",
            "transition_interference_risk_tier",
            "warning_codes",
            "warning_note",
        )
    )
    for entry in report.panel_entries:
        writer.writerow(
            (
                entry.transition_id,
                entry.precursor_id,
                entry.assay_entry_id,
                entry.biomarker_candidate_id,
                entry.biomarker_candidate_kind.value,
                entry.biomarker_priority_rank,
                entry.target_protein_ref,
                entry.target_protein_group_id,
                "" if entry.gene_symbol is None else entry.gene_symbol,
                entry.peptide_sequence,
                entry.canonical_peptide,
                entry.uniqueness_class.value,
                f"{entry.uniqueness_score:.6f}",
                entry.precursor_charge,
                f"{entry.precursor_mz:.6f}",
                entry.fragment_label,
                entry.ion_type,
                entry.fragment_ordinal,
                entry.fragment_charge,
                entry.fragment_sequence,
                f"{entry.fragment_mz:.6f}",
                ""
                if entry.expected_relative_intensity is None
                else f"{entry.expected_relative_intensity:.6f}",
                ""
                if entry.expected_retention_time_minutes is None
                else f"{entry.expected_retention_time_minutes:.6f}",
                ""
                if entry.retention_window_start_minutes is None
                else f"{entry.retention_window_start_minutes:.6f}",
                ""
                if entry.retention_window_end_minutes is None
                else f"{entry.retention_window_end_minutes:.6f}",
                entry.assay_interference_risk_tier.value,
                entry.transition_interference_risk_tier.value,
                ";".join(code.value for code in entry.warning_codes),
                entry.warning_note,
            )
        )
    return handle.getvalue()


def render_targeted_panel_design_omitted_candidate_tsv(
    report: TargetedPanelDesignReport,
) -> str:
    """Render omitted biomarker candidates beside the final targeted panel."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "candidate_id",
            "candidate_kind",
            "display_label",
            "target_protein_ref",
            "site_key",
            "priority_rank",
            "omission_reason",
        )
    )
    for entry in report.omitted_candidates:
        writer.writerow(
            (
                entry.candidate_id,
                entry.candidate_kind.value,
                entry.display_label,
                entry.target_protein_ref,
                "" if entry.site_key is None else entry.site_key,
                entry.priority_rank,
                entry.omission_reason,
            )
        )
    return handle.getvalue()


def _best_candidate_for_protein(
    candidates: tuple[TargetedPanelBiomarkerCandidateInput, ...]
    | list[TargetedPanelBiomarkerCandidateInput]
    | None,
) -> TargetedPanelBiomarkerCandidateInput | None:
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (item.priority_rank, item.candidate_id))[
        0
    ]


def _candidate_priority_rank_for_protein(
    candidates: tuple[TargetedPanelBiomarkerCandidateInput, ...]
    | list[TargetedPanelBiomarkerCandidateInput]
    | None,
) -> int:
    candidate = _best_candidate_for_protein(candidates)
    return 10_000 if candidate is None else candidate.priority_rank


def _expected_retention_time_minutes(
    source_library_entry_id: str | None,
    *,
    library_by_id: dict[str, SpectralLibraryEntry],
) -> float | None:
    if source_library_entry_id is None:
        return None
    library_entry = library_by_id.get(source_library_entry_id)
    if library_entry is None or library_entry.spectrum.retention_time_seconds is None:
        return None
    return float(library_entry.spectrum.retention_time_seconds) / 60.0


def _retention_window(
    expected_retention_time_minutes: float | None,
    *,
    radius_minutes: float,
) -> tuple[float | None, float | None]:
    if expected_retention_time_minutes is None:
        return (None, None)
    return (
        max(0.0, expected_retention_time_minutes - radius_minutes),
        expected_retention_time_minutes + radius_minutes,
    )


def _warning_codes_for_assay(
    *,
    candidate: TargetedPanelBiomarkerCandidateInput,
    selected_peptide: TargetedPanelSelectedPeptideInput | None,
    assay: TargetedPanelAssayInput,
    expected_retention_time_minutes: float | None,
) -> tuple[TargetedPanelWarningCode, ...]:
    warnings: list[TargetedPanelWarningCode] = []
    if candidate.penalty_total > 0.0:
        warnings.append(TargetedPanelWarningCode.CANDIDATE_PENALIZED)
    if assay.interference_risk_tier is not TargetedAssayInterferenceRiskTier.LOW:
        warnings.append(TargetedPanelWarningCode.ELEVATED_INTERFERENCE_RISK)
    if expected_retention_time_minutes is None:
        warnings.append(TargetedPanelWarningCode.MISSING_EXPECTED_RETENTION_TIME)
    if (
        selected_peptide is not None
        and selected_peptide.uniqueness_class is not PeptideUniquenessClass.UNIQUE
    ):
        warnings.append(TargetedPanelWarningCode.NON_UNIQUE_TARGET)
    if assay.exported_transition_count < assay.selected_transition_count:
        warnings.append(TargetedPanelWarningCode.REDUCED_TRANSITION_SUPPORT)
    return tuple(dict.fromkeys(warnings))


def _warning_note_for_assay(
    *,
    candidate: TargetedPanelBiomarkerCandidateInput,
    selected_peptide: TargetedPanelSelectedPeptideInput | None,
    assay: TargetedPanelAssayInput,
    expected_retention_time_minutes: float | None,
    warning_codes: tuple[TargetedPanelWarningCode, ...],
) -> str:
    notes: list[str] = []
    if TargetedPanelWarningCode.CANDIDATE_PENALIZED in warning_codes:
        notes.append(
            "ranked candidate carries evidence penalties and should stay reviewable beside the panel"
        )
    if TargetedPanelWarningCode.ELEVATED_INTERFERENCE_RISK in warning_codes:
        notes.append(
            "retained assay still carries elevated interference risk after pre-run downgrading"
        )
    if TargetedPanelWarningCode.MISSING_EXPECTED_RETENTION_TIME in warning_codes:
        notes.append(
            "expected retention time is unavailable because no governed library retention anchor was supplied"
        )
    if TargetedPanelWarningCode.NON_UNIQUE_TARGET in warning_codes:
        notes.append("selected peptide is not unique to one target protein")
    if TargetedPanelWarningCode.REDUCED_TRANSITION_SUPPORT in warning_codes:
        notes.append(
            "one or more chemistry-supported transitions were withheld from export"
        )
    if not notes:
        uniqueness_text = (
            "unique peptide support"
            if selected_peptide is None
            or selected_peptide.uniqueness_class is PeptideUniquenessClass.UNIQUE
            else "non-unique peptide support"
        )
        rt_text = (
            "with expected retention time"
            if expected_retention_time_minutes is not None
            else "without expected retention time anchor"
        )
        notes.append(
            f"panel row is retained for ranked biomarker candidate {candidate.display_label} with {uniqueness_text} {rt_text}"
        )
    if (
        assay.panel_export_caveat
        and "retained for panel export" not in assay.panel_export_caveat.lower()
    ):
        notes.append(assay.panel_export_caveat)
    return " ".join(notes)


__all__ = [
    "TargetedPanelAssayEntry",
    "TargetedPanelAssayInput",
    "TargetedPanelBiomarkerCandidateInput",
    "TargetedPanelCandidateKind",
    "TargetedPanelDesignReport",
    "TargetedPanelDesignSummary",
    "TargetedPanelOmittedCandidateEntry",
    "TargetedPanelSelectedPeptideInput",
    "TargetedPanelTransitionEntry",
    "TargetedPanelTransitionInput",
    "TargetedPanelWarningCode",
    "build_targeted_panel_design_report",
    "render_targeted_panel_design_assay_tsv",
    "render_targeted_panel_design_omitted_candidate_tsv",
    "render_targeted_panel_design_panel_tsv",
    "render_targeted_panel_design_summary_tsv",
]
