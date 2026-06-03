# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned lab protocol context parsing and protocol-aware interpretation hints."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._scientific_tables import (
    ScientificTableValidationIssue,
    build_lab_protocol_context_schema,
    validate_scientific_table,
)
from bijux_proteomics_foundation import JsonModel


class DigestionEnzyme(StrEnum):
    """Owned digestion enzyme categories for protocol-aware QC."""

    TRYPSIN = "trypsin"
    LYSC = "lysc"
    TRYPSIN_LYSC = "trypsin_lysc"
    GLUC = "gluc"
    CHYMOTRYPSIN = "chymotrypsin"
    ASPN = "aspn"
    OTHER = "other"


class AcquisitionType(StrEnum):
    """Owned acquisition categories that drive QC and interpretation behavior."""

    DDA = "dda"
    DIA = "dia"
    TARGETED = "targeted"


class LabelingMethod(StrEnum):
    """Owned labeling modes that influence proteomics interpretation defaults."""

    LABEL_FREE = "label_free"
    TMT = "tmt"
    SILAC = "silac"
    OTHER = "other"


class EnrichmentType(StrEnum):
    """Owned enrichment categories for protocol-aware QC and interpretation."""

    NONE = "none"
    PHOSPHO = "phospho"
    ACETYL = "acetyl"
    UBIQUITIN = "ubiquitin"
    GLYCO = "glyco"
    OTHER = "other"


class FractionationMode(StrEnum):
    """Owned fractionation modes that affect run-level expectations."""

    NONE = "none"
    OFFLINE_HIGH_PH = "offline_high_ph"
    GEL = "gel"
    SAX = "sax"
    OTHER = "other"


class DepletionMode(StrEnum):
    """Owned depletion modes for protocol-aware QC expectations."""

    NONE = "none"
    PLASMA_HIGH_ABUNDANCE = "plasma_high_abundance"
    RIBOSOMAL = "ribosomal"
    OTHER = "other"


class LabProtocolContextIssue(JsonModel):
    """One stable issue over a governed lab protocol context table."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=1)
    column: str | None = None


class LabProtocolContextRejectedRow(JsonModel):
    """One rejected protocol-context row."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=1)
    raw_values: dict[str, str] = Field(default_factory=dict)
    issues: tuple[LabProtocolContextIssue, ...] = Field(default_factory=tuple)


class LabProtocolContextEntry(JsonModel):
    """One experiment-level lab protocol context row."""

    model_config = ConfigDict(extra="forbid")

    protocol_id: str = Field(..., min_length=1)
    digestion_enzyme: DigestionEnzyme
    acquisition_type: AcquisitionType
    labeling_method: LabelingMethod
    enrichment_type: EnrichmentType
    fractionation_mode: FractionationMode
    depletion_mode: DepletionMode
    instrument_platform: str = Field(..., min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class LabProtocolContextSummary(JsonModel):
    """Compact summary over one parsed lab protocol context table."""

    model_config = ConfigDict(extra="forbid")

    accepted_entry_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    acquisition_types: tuple[AcquisitionType, ...] = Field(default_factory=tuple)
    labeling_methods: tuple[LabelingMethod, ...] = Field(default_factory=tuple)
    enrichment_types: tuple[EnrichmentType, ...] = Field(default_factory=tuple)


class LabProtocolContextReport(JsonModel):
    """Stable parse report for one governed lab protocol context table."""

    model_config = ConfigDict(extra="forbid")

    accepted_entries: tuple[LabProtocolContextEntry, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[LabProtocolContextRejectedRow, ...] = Field(
        default_factory=tuple
    )
    summary: LabProtocolContextSummary


class LabProtocolInterpretationProfile(JsonModel):
    """Protocol-aware interpretation defaults for biological reporting."""

    model_config = ConfigDict(extra="forbid")

    max_adjusted_p_value: float = Field(..., ge=0.0, le=1.0)
    min_absolute_log2_fold_change: float = Field(..., ge=0.0)
    heatmap_max_entity_count: int = Field(..., ge=1)
    interpretation_focus: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


def parse_lab_protocol_context_table(path: Path) -> LabProtocolContextReport:
    """Parse one governed experiment-level lab protocol context table."""

    validation_report = validate_scientific_table(
        path,
        schema=build_lab_protocol_context_schema(),
    )
    accepted_entries = tuple(
        LabProtocolContextEntry(
            protocol_id=str(row.values["protocol_id"]),
            digestion_enzyme=DigestionEnzyme(str(row.values["digestion_enzyme"])),
            acquisition_type=AcquisitionType(str(row.values["acquisition_type"])),
            labeling_method=LabelingMethod(str(row.values["labeling_method"])),
            enrichment_type=EnrichmentType(str(row.values["enrichment_type"])),
            fractionation_mode=FractionationMode(str(row.values["fractionation_mode"])),
            depletion_mode=DepletionMode(str(row.values["depletion_mode"])),
            instrument_platform=str(row.values["instrument_platform"]),
            metadata=dict(sorted(row.extra_values.items())),
        )
        for row in validation_report.accepted_rows
    )
    rejected_rows = tuple(
        LabProtocolContextRejectedRow(
            row_number=row.row_number,
            raw_values=row.raw_values,
            issues=_translate_protocol_context_issues(row.issues),
        )
        for row in validation_report.rejected_rows
    )
    return LabProtocolContextReport(
        accepted_entries=accepted_entries,
        rejected_rows=rejected_rows,
        summary=LabProtocolContextSummary(
            accepted_entry_count=len(accepted_entries),
            rejected_row_count=len(rejected_rows),
            acquisition_types=tuple(
                sorted({entry.acquisition_type for entry in accepted_entries})
            ),
            labeling_methods=tuple(
                sorted({entry.labeling_method for entry in accepted_entries})
            ),
            enrichment_types=tuple(
                sorted({entry.enrichment_type for entry in accepted_entries})
            ),
        ),
    )


def require_single_lab_protocol_context(
    report: LabProtocolContextReport,
) -> LabProtocolContextEntry:
    """Return the one experiment-level protocol context or raise."""

    if report.rejected_rows:
        raise ValueError("lab protocol context table contains rejected rows")
    if len(report.accepted_entries) != 1:
        raise ValueError(
            "lab protocol context requires exactly one experiment-level row"
        )
    return report.accepted_entries[0]


def build_lab_protocol_interpretation_profile(
    protocol_context: LabProtocolContextEntry,
) -> LabProtocolInterpretationProfile:
    """Build protocol-aware interpretation defaults for biological reporting."""

    if protocol_context.acquisition_type is AcquisitionType.TARGETED:
        return LabProtocolInterpretationProfile(
            max_adjusted_p_value=0.2,
            min_absolute_log2_fold_change=0.25,
            heatmap_max_entity_count=25,
            interpretation_focus="targeted_validation",
            note=(
                "targeted validation favors smaller candidate panels and more "
                "permissive fold-change thresholds than discovery proteomics"
            ),
        )
    if protocol_context.labeling_method is LabelingMethod.TMT:
        return LabProtocolInterpretationProfile(
            max_adjusted_p_value=0.1,
            min_absolute_log2_fold_change=0.58,
            heatmap_max_entity_count=80,
            interpretation_focus="multiplex_discovery",
            note=(
                "TMT interpretation relaxes fold-change cutoffs to account for "
                "ratio compression and allows broader multiplex heatmaps"
            ),
        )
    if protocol_context.enrichment_type is not EnrichmentType.NONE:
        return LabProtocolInterpretationProfile(
            max_adjusted_p_value=0.15,
            min_absolute_log2_fold_change=0.5,
            heatmap_max_entity_count=40,
            interpretation_focus="enriched_subproteome",
            note=(
                "enriched subproteome interpretation lowers the heatmap breadth and "
                "uses enrichment-aware significance defaults"
            ),
        )
    if protocol_context.acquisition_type is AcquisitionType.DIA:
        return LabProtocolInterpretationProfile(
            max_adjusted_p_value=0.1,
            min_absolute_log2_fold_change=1.0,
            heatmap_max_entity_count=75,
            interpretation_focus="dia_discovery",
            note=(
                "DIA interpretation favors broader heatmaps because acquisition "
                "completeness supports denser cross-sample comparisons"
            ),
        )
    return LabProtocolInterpretationProfile(
        max_adjusted_p_value=0.1,
        min_absolute_log2_fold_change=1.0,
        heatmap_max_entity_count=50,
        interpretation_focus="dda_discovery",
        note="default DDA-style interpretation thresholds apply",
    )


def render_lab_protocol_context_tsv(report: LabProtocolContextReport) -> str:
    """Render accepted protocol-context rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protocol_id",
            "digestion_enzyme",
            "acquisition_type",
            "labeling_method",
            "enrichment_type",
            "fractionation_mode",
            "depletion_mode",
            "instrument_platform",
        )
    )
    for entry in report.accepted_entries:
        writer.writerow(
            (
                entry.protocol_id,
                entry.digestion_enzyme.value,
                entry.acquisition_type.value,
                entry.labeling_method.value,
                entry.enrichment_type.value,
                entry.fractionation_mode.value,
                entry.depletion_mode.value,
                entry.instrument_platform,
            )
        )
    return buffer.getvalue()


def _translate_protocol_context_issues(
    issues: tuple[ScientificTableValidationIssue, ...],
) -> tuple[LabProtocolContextIssue, ...]:
    return tuple(
        LabProtocolContextIssue(
            code=(
                "missing_lab_protocol_column"
                if issue.code == "missing_column"
                else "missing_lab_protocol_value"
                if issue.code == "missing_value"
                else "invalid_lab_protocol_value"
            ),
            message=issue.message,
            row_number=issue.row_number,
            column=issue.column,
        )
        for issue in issues
    )


__all__ = [
    "AcquisitionType",
    "DepletionMode",
    "DigestionEnzyme",
    "EnrichmentType",
    "FractionationMode",
    "LabelingMethod",
    "LabProtocolContextEntry",
    "LabProtocolContextIssue",
    "LabProtocolContextRejectedRow",
    "LabProtocolContextReport",
    "LabProtocolContextSummary",
    "LabProtocolInterpretationProfile",
    "build_lab_protocol_interpretation_profile",
    "parse_lab_protocol_context_table",
    "render_lab_protocol_context_tsv",
    "require_single_lab_protocol_context",
]
