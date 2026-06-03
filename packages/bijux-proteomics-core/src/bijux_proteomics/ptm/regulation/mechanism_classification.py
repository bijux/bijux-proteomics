# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned PTM mechanism-classification surfaces."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields
from bijux_proteomics.ptm.localization.localization_scoring import (
    PtmLocalizationConfidenceTier,
)
from bijux_proteomics.ptm.quant.differential_analysis import (
    PtmDifferentialAnalysisReport,
    PtmProteinCorrectionStatus,
    PtmSiteDifferentialEntry,
)
from bijux_proteomics.ptm.quant.site_quantification import PtmSiteQuantRow
from bijux_proteomics_foundation import JsonModel


class PtmMechanismClass(StrEnum):
    """Stable mechanism classes for regulated PTM sites."""

    ABUNDANCE_DRIVEN = "abundance_driven"
    SITE_SPECIFIC = "site_specific"
    AMBIGUOUS = "ambiguous"
    UNSUPPORTED = "unsupported"


class PtmMechanismReasonCode(StrEnum):
    """Stable reason codes behind one PTM mechanism call."""

    LOW_LOCALIZATION_SUPPORT = "low_localization_support"
    AMBIGUOUS_SITE_LOCALIZATION = "ambiguous_site_localization"
    LIMITED_PEPTIDE_SUPPORT = "limited_peptide_support"
    CORRECTION_NOT_REQUESTED = "correction_not_requested"
    MISSING_PROTEIN_BASELINE = "missing_protein_baseline"
    PROTEIN_TRACKS_RAW_SITE_EFFECT = "protein_tracks_raw_site_effect"
    RESIDUAL_SITE_EFFECT_AFTER_CORRECTION = "residual_site_effect_after_correction"
    MIXED_SITE_AND_PROTEIN_SIGNAL = "mixed_site_and_protein_signal"


class PtmMechanismClassificationPolicy(JsonModel):
    """Decision policy for PTM mechanism classification."""

    model_config = ConfigDict(extra="forbid")

    significant_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    minimum_absolute_effect: float = Field(default=0.5, ge=0.0)
    maximum_corrected_fraction_for_abundance_driven: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
    )
    minimum_corrected_fraction_for_site_specific: float = Field(
        default=0.6,
        ge=0.0,
    )
    minimum_localized_peptide_count: int = Field(default=1, ge=1)


class PtmMechanismClassificationEntry(JsonModel):
    """One PTM site annotated with a governed mechanism class."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    position: int = Field(..., ge=1)
    modification_name: str = Field(..., min_length=1)
    mechanism_class: PtmMechanismClass
    reason_codes: tuple[PtmMechanismReasonCode, ...] = Field(default_factory=tuple)
    raw_log2_fold_change: float
    corrected_log2_fold_change: float | None = None
    protein_log2_fold_change: float | None = None
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    protein_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    localization_tier: PtmLocalizationConfidenceTier
    localized_peptide_count: int = Field(..., ge=0)
    observed_sample_count: int = Field(..., ge=0)
    complete_pair_count: int = Field(..., ge=0)
    protein_correction_status: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class PtmMechanismClassificationSummary(JsonModel):
    """Stable summary over one PTM mechanism-classification pass."""

    model_config = ConfigDict(extra="forbid")

    site_count: int = Field(..., ge=0)
    abundance_driven_count: int = Field(..., ge=0)
    site_specific_count: int = Field(..., ge=0)
    ambiguous_count: int = Field(..., ge=0)
    unsupported_count: int = Field(..., ge=0)


class PtmMechanismClassificationReport(JsonModel):
    """Owned PTM mechanism-classification report."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    policy: PtmMechanismClassificationPolicy
    entries: tuple[PtmMechanismClassificationEntry, ...] = Field(default_factory=tuple)
    summary: PtmMechanismClassificationSummary
    note: str = Field(..., min_length=1)


def build_ptm_mechanism_classification_report(
    differential_analysis: PtmDifferentialAnalysisReport,
    *,
    policy: PtmMechanismClassificationPolicy | None = None,
) -> PtmMechanismClassificationReport:
    """Classify regulated PTM sites as abundance-driven, site-specific, ambiguous, or unsupported."""

    active_policy = policy or PtmMechanismClassificationPolicy()
    quant_rows_by_site = {
        row.site_key: row for row in differential_analysis.site_quantification.rows
    }
    entries = tuple(
        _classify_mechanism_entry(
            entry,
            quant_row=quant_rows_by_site[entry.site_key],
            policy=active_policy,
        )
        for entry in sort_rows_by_fields(
            differential_analysis.differential_report.entries,
            "protein_ref",
            "position",
            "modification_name",
            "site_key",
        )
    )
    return PtmMechanismClassificationReport(
        condition_a=differential_analysis.differential_report.condition_a,
        condition_b=differential_analysis.differential_report.condition_b,
        policy=active_policy,
        entries=entries,
        summary=PtmMechanismClassificationSummary(
            site_count=len(entries),
            abundance_driven_count=sum(
                1
                for entry in entries
                if entry.mechanism_class is PtmMechanismClass.ABUNDANCE_DRIVEN
            ),
            site_specific_count=sum(
                1
                for entry in entries
                if entry.mechanism_class is PtmMechanismClass.SITE_SPECIFIC
            ),
            ambiguous_count=sum(
                1
                for entry in entries
                if entry.mechanism_class is PtmMechanismClass.AMBIGUOUS
            ),
            unsupported_count=sum(
                1
                for entry in entries
                if entry.mechanism_class is PtmMechanismClass.UNSUPPORTED
            ),
        ),
        note=(
            "ptm mechanism classification preserves raw and protein-corrected site "
            "effects so abundance-driven and site-specific interpretations remain "
            "separate from ambiguous or unsupported PTM claims"
        ),
    )


def render_ptm_mechanism_classification_summary_tsv(
    report: PtmMechanismClassificationReport,
) -> str:
    """Render the PTM mechanism-classification summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "condition_a",
            "condition_b",
            "site_count",
            "abundance_driven_count",
            "site_specific_count",
            "ambiguous_count",
            "unsupported_count",
        )
    )
    writer.writerow(
        (
            report.condition_a,
            report.condition_b,
            report.summary.site_count,
            report.summary.abundance_driven_count,
            report.summary.site_specific_count,
            report.summary.ambiguous_count,
            report.summary.unsupported_count,
        )
    )
    return buffer.getvalue()


def render_ptm_mechanism_classification_tsv(
    report: PtmMechanismClassificationReport,
) -> str:
    """Render PTM mechanism classifications as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "site_key",
            "protein_ref",
            "residue",
            "position",
            "modification_name",
            "mechanism_class",
            "reason_codes",
            "raw_log2_fold_change",
            "corrected_log2_fold_change",
            "protein_log2_fold_change",
            "adjusted_p_value",
            "protein_adjusted_p_value",
            "localization_tier",
            "localized_peptide_count",
            "observed_sample_count",
            "complete_pair_count",
            "protein_correction_status",
            "note",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.site_key,
                entry.protein_ref,
                entry.residue,
                entry.position,
                entry.modification_name,
                entry.mechanism_class.value,
                ";".join(reason.value for reason in entry.reason_codes),
                entry.raw_log2_fold_change,
                (
                    ""
                    if entry.corrected_log2_fold_change is None
                    else entry.corrected_log2_fold_change
                ),
                (
                    ""
                    if entry.protein_log2_fold_change is None
                    else entry.protein_log2_fold_change
                ),
                "" if entry.adjusted_p_value is None else entry.adjusted_p_value,
                (
                    ""
                    if entry.protein_adjusted_p_value is None
                    else entry.protein_adjusted_p_value
                ),
                entry.localization_tier.value,
                entry.localized_peptide_count,
                entry.observed_sample_count,
                entry.complete_pair_count,
                entry.protein_correction_status,
                entry.note,
            )
        )
    return buffer.getvalue()


def export_ptm_mechanism_classification_summary_tsv(
    report: PtmMechanismClassificationReport,
    path: Path,
) -> None:
    """Write PTM mechanism-classification summary TSV."""

    write_output_table_tsv(
        path, render_ptm_mechanism_classification_summary_tsv(report)
    )


def export_ptm_mechanism_classification_tsv(
    report: PtmMechanismClassificationReport,
    path: Path,
) -> None:
    """Write PTM mechanism-classification TSV."""

    write_output_table_tsv(path, render_ptm_mechanism_classification_tsv(report))


def _classify_mechanism_entry(
    differential_entry: PtmSiteDifferentialEntry,
    *,
    quant_row: PtmSiteQuantRow,
    policy: PtmMechanismClassificationPolicy,
) -> PtmMechanismClassificationEntry:
    reason_codes: list[PtmMechanismReasonCode] = []
    localized_peptide_count = len(quant_row.localized_peptides)
    observed_sample_count = sum(
        1 for value in quant_row.values if value.abundance is not None
    )
    raw_effect = abs(differential_entry.log2_fold_change)
    corrected_effect = (
        None
        if differential_entry.corrected_log2_fold_change is None
        else abs(differential_entry.corrected_log2_fold_change)
    )
    protein_effect = (
        None
        if differential_entry.protein_log2_fold_change is None
        else abs(differential_entry.protein_log2_fold_change)
    )
    protein_significant = (
        differential_entry.protein_adjusted_p_value is not None
        and differential_entry.protein_adjusted_p_value
        <= policy.significant_adjusted_p_value
    )
    same_direction = (
        differential_entry.protein_log2_fold_change is not None
        and differential_entry.log2_fold_change != 0.0
        and differential_entry.protein_log2_fold_change != 0.0
        and (differential_entry.log2_fold_change > 0.0)
        is (differential_entry.protein_log2_fold_change > 0.0)
    )

    mechanism_class: PtmMechanismClass
    note: str
    if differential_entry.low_localization or differential_entry.localization_tier in {
        PtmLocalizationConfidenceTier.AMBIGUOUS,
        PtmLocalizationConfidenceTier.REFUSED,
    }:
        reason_codes.append(PtmMechanismReasonCode.LOW_LOCALIZATION_SUPPORT)
        if differential_entry.ambiguous:
            reason_codes.append(PtmMechanismReasonCode.AMBIGUOUS_SITE_LOCALIZATION)
        mechanism_class = PtmMechanismClass.UNSUPPORTED
        note = (
            f"{differential_entry.site_key} remains unsupported for mechanism calling "
            "because localization evidence is too weak"
        )
    elif localized_peptide_count < policy.minimum_localized_peptide_count:
        reason_codes.append(PtmMechanismReasonCode.LIMITED_PEPTIDE_SUPPORT)
        mechanism_class = PtmMechanismClass.UNSUPPORTED
        note = (
            f"{differential_entry.site_key} remains unsupported for mechanism calling "
            "because peptide support is insufficient"
        )
    elif (
        differential_entry.protein_correction_status
        == PtmProteinCorrectionStatus.NOT_REQUESTED.value
    ):
        reason_codes.append(PtmMechanismReasonCode.CORRECTION_NOT_REQUESTED)
        mechanism_class = PtmMechanismClass.AMBIGUOUS
        note = (
            f"{differential_entry.site_key} stays ambiguous because no protein-level "
            "correction was supplied to separate abundance from site regulation"
        )
    elif (
        differential_entry.protein_correction_status
        == PtmProteinCorrectionStatus.MISSING_PROTEIN_BASELINE.value
        or differential_entry.corrected_log2_fold_change is None
        or differential_entry.protein_log2_fold_change is None
    ):
        reason_codes.append(PtmMechanismReasonCode.MISSING_PROTEIN_BASELINE)
        mechanism_class = PtmMechanismClass.AMBIGUOUS
        note = (
            f"{differential_entry.site_key} stays ambiguous because the matched protein "
            "baseline needed for correction is missing"
        )
    else:
        corrected_fraction = (
            0.0
            if raw_effect == 0.0 or corrected_effect is None
            else corrected_effect / raw_effect
        )
        if (
            same_direction
            and protein_significant
            and protein_effect is not None
            and protein_effect >= policy.minimum_absolute_effect
            and corrected_effect is not None
            and corrected_effect
            <= max(
                policy.minimum_absolute_effect * 0.5,
                raw_effect * policy.maximum_corrected_fraction_for_abundance_driven,
            )
        ):
            reason_codes.append(PtmMechanismReasonCode.PROTEIN_TRACKS_RAW_SITE_EFFECT)
            mechanism_class = PtmMechanismClass.ABUNDANCE_DRIVEN
            note = (
                f"{differential_entry.site_key} looks abundance-driven because the "
                "protein effect tracks the raw PTM shift and little residual remains "
                "after correction"
            )
        elif (
            corrected_effect is not None
            and corrected_effect >= policy.minimum_absolute_effect
            and (
                not same_direction
                or not protein_significant
                or corrected_fraction
                >= policy.minimum_corrected_fraction_for_site_specific
            )
        ):
            reason_codes.append(
                PtmMechanismReasonCode.RESIDUAL_SITE_EFFECT_AFTER_CORRECTION
            )
            mechanism_class = PtmMechanismClass.SITE_SPECIFIC
            note = (
                f"{differential_entry.site_key} looks site-specific because a material "
                "PTM effect remains after protein correction"
            )
        else:
            reason_codes.append(PtmMechanismReasonCode.MIXED_SITE_AND_PROTEIN_SIGNAL)
            mechanism_class = PtmMechanismClass.AMBIGUOUS
            note = (
                f"{differential_entry.site_key} remains ambiguous because the corrected "
                "effect still mixes protein abundance and site-specific signal"
            )

    return PtmMechanismClassificationEntry(
        site_key=differential_entry.site_key,
        protein_ref=differential_entry.protein_ref,
        residue=differential_entry.residue,
        position=differential_entry.position,
        modification_name=differential_entry.modification_name,
        mechanism_class=mechanism_class,
        reason_codes=tuple(reason_codes),
        raw_log2_fold_change=differential_entry.log2_fold_change,
        corrected_log2_fold_change=differential_entry.corrected_log2_fold_change,
        protein_log2_fold_change=differential_entry.protein_log2_fold_change,
        adjusted_p_value=differential_entry.adjusted_p_value,
        protein_adjusted_p_value=differential_entry.protein_adjusted_p_value,
        localization_tier=differential_entry.localization_tier,
        localized_peptide_count=localized_peptide_count,
        observed_sample_count=observed_sample_count,
        complete_pair_count=differential_entry.complete_pair_count,
        protein_correction_status=differential_entry.protein_correction_status,
        note=note,
    )


__all__ = (
    "PtmMechanismClass",
    "PtmMechanismClassificationEntry",
    "PtmMechanismClassificationPolicy",
    "PtmMechanismClassificationReport",
    "PtmMechanismClassificationSummary",
    "PtmMechanismReasonCode",
    "build_ptm_mechanism_classification_report",
    "export_ptm_mechanism_classification_summary_tsv",
    "export_ptm_mechanism_classification_tsv",
    "render_ptm_mechanism_classification_summary_tsv",
    "render_ptm_mechanism_classification_tsv",
)
