# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Upstream regulator inference from explicit target evidence and observed signal."""

from __future__ import annotations

from collections import defaultdict
import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path
from typing import DefaultDict, Sequence

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.pathway_activity import (
    PathwayActivityConfidenceStatus,
    PathwayActivityReport,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationMappingReport,
)
from bijux_proteomics.io.stable_outputs import sort_strings
from bijux_proteomics.ptm import PtmEvidenceCardReport
from bijux_proteomics.quantification.contracts import DifferentialAbundanceReport
from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel


class RegulatorEvidenceType(StrEnum):
    """Explicit upstream evidence classes supported by the regulator engine."""

    KINASE_SUBSTRATE = "kinase_substrate"
    TRANSCRIPTION_FACTOR_TARGET = "transcription_factor_target"
    PATHWAY = "pathway"
    PPI = "ppi"


class RegulatorSignalSurface(StrEnum):
    """Observed signal surface used to support one regulator result."""

    SITE_REGULATION = "site_regulation"
    PROTEIN_ABUNDANCE = "protein_abundance"
    PATHWAY_ACTIVITY = "pathway_activity"


class RegulatorInferenceDirection(StrEnum):
    """Stable direction labels preserved on one regulator result."""

    UP = "up"
    DOWN = "down"
    MIXED = "mixed"
    UNSUPPORTED = "unsupported"


class RegulatorEvidenceTargetField(StrEnum):
    """Explicit target field linked from one regulator evidence row."""

    PROTEIN_REF = "protein_ref"
    GENE_SYMBOL = "gene_symbol"
    PATHWAY_ID = "pathway_id"
    SITE_KEY = "site_key"


class RegulatorEvidenceColumnMapping(JsonModel):
    """Column mapping from one user-supplied regulator evidence table."""

    model_config = ConfigDict(extra="forbid")

    regulator: str = Field(default="regulator", min_length=1)
    evidence_type: str = Field(default="evidence_type", min_length=1)
    protein_ref: str | None = "protein_ref"
    gene_symbol: str | None = "gene_symbol"
    pathway_id: str | None = "pathway_id"
    site_key: str | None = "site_key"
    source_name: str | None = "source_name"
    source_accession: str | None = "source_accession"


class RegulatorEvidenceRecord(JsonModel):
    """One normalized regulator-to-target evidence row."""

    model_config = ConfigDict(extra="forbid")

    regulator: str = Field(..., min_length=1)
    evidence_type: RegulatorEvidenceType
    protein_ref: str | None = None
    gene_symbol: str | None = None
    pathway_id: str | None = None
    site_key: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class RejectedRegulatorEvidenceRow(JsonModel):
    """One rejected regulator evidence row with a durable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class RegulatorEvidenceImportSummary(JsonModel):
    """Stable summary over one regulator evidence import."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    regulator_count: int = Field(..., ge=0)
    kinase_substrate_record_count: int = Field(..., ge=0)
    transcription_factor_target_record_count: int = Field(..., ge=0)
    pathway_record_count: int = Field(..., ge=0)
    ppi_record_count: int = Field(..., ge=0)


class RegulatorEvidenceImportReport(JsonModel):
    """Governed import report over one regulator evidence table."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[RegulatorEvidenceRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedRegulatorEvidenceRow, ...] = Field(default_factory=tuple)
    column_mapping: RegulatorEvidenceColumnMapping
    summary: RegulatorEvidenceImportSummary
    note: str = Field(..., min_length=1)


class RegulatorSiteSignalColumnMapping(JsonModel):
    """Column mapping from one user-supplied site differential table."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(default="site_key", min_length=1)
    protein_ref: str | None = "protein_ref"
    log2_fold_change: str = Field(default="log2_fold_change", min_length=1)
    adjusted_p_value: str | None = "adjusted_p_value"


class RegulatorSiteSignalEntry(JsonModel):
    """One normalized site-level differential signal row."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str | None = None
    log2_fold_change: float
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)


class RejectedRegulatorSiteSignalRow(JsonModel):
    """One rejected site-signal row with a durable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class RegulatorSiteSignalImportSummary(JsonModel):
    """Stable summary over one site-signal import."""

    model_config = ConfigDict(extra="forbid")

    accepted_entry_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    distinct_site_count: int = Field(..., ge=0)


class RegulatorSiteSignalImportReport(JsonModel):
    """Governed import report over one site differential table."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    total_rows: int = Field(..., ge=0)
    accepted_entries: tuple[RegulatorSiteSignalEntry, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedRegulatorSiteSignalRow, ...] = Field(default_factory=tuple)
    column_mapping: RegulatorSiteSignalColumnMapping
    summary: RegulatorSiteSignalImportSummary
    note: str = Field(..., min_length=1)


class RegulatorInferenceEntry(JsonModel):
    """One aggregated upstream regulator result over one evidence surface."""

    model_config = ConfigDict(extra="forbid")

    regulator: str = Field(..., min_length=1)
    evidence_type: RegulatorEvidenceType
    signal_surface: RegulatorSignalSurface
    source_name: str | None = None
    source_accession: str | None = None
    target_count: int = Field(..., ge=0)
    matched_target_count: int = Field(..., ge=0)
    coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    supporting_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    supporting_site_keys: tuple[str, ...] = Field(default_factory=tuple)
    supporting_pathway_ids: tuple[str, ...] = Field(default_factory=tuple)
    direction: RegulatorInferenceDirection
    score: float = Field(..., ge=0.0, le=1.0)
    mean_log2_fold_change: float | None = None
    mean_activity_score_delta: float | None = None
    note: str = Field(..., min_length=1)


class UnresolvedRegulatorTargetEntry(JsonModel):
    """One explicit target row that could not be linked to observed evidence."""

    model_config = ConfigDict(extra="forbid")

    regulator: str = Field(..., min_length=1)
    evidence_type: RegulatorEvidenceType
    target_field: RegulatorEvidenceTargetField
    target_value: str = Field(..., min_length=1)
    source_name: str | None = None
    source_accession: str | None = None
    reason: str = Field(..., min_length=1)


class RegulatorInferenceSummary(JsonModel):
    """Stable summary over one regulator-inference run."""

    model_config = ConfigDict(extra="forbid")

    regulator_count: int = Field(..., ge=0)
    entry_count: int = Field(..., ge=0)
    site_regulation_entry_count: int = Field(..., ge=0)
    protein_abundance_entry_count: int = Field(..., ge=0)
    pathway_activity_entry_count: int = Field(..., ge=0)
    unresolved_target_count: int = Field(..., ge=0)
    high_scoring_entry_count: int = Field(..., ge=0)


class RegulatorInferencePolicy(JsonModel):
    """Confidence policy for regulator inference coverage and scoring."""

    model_config = ConfigDict(extra="forbid")

    minimum_target_coverage_fraction: float = Field(default=0.5, ge=0.0, le=1.0)
    low_coverage_score_cap: float = Field(default=0.49, ge=0.0, le=1.0)


class RegulatorInferenceReport(JsonModel):
    """Owned upstream regulator inference report over explicit evidence rows."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    entries: tuple[RegulatorInferenceEntry, ...] = Field(default_factory=tuple)
    unresolved_targets: tuple[UnresolvedRegulatorTargetEntry, ...] = Field(
        default_factory=tuple
    )
    summary: RegulatorInferenceSummary
    note: str = Field(..., min_length=1)


def parse_regulator_evidence_table(
    path: Path,
    *,
    mapping: RegulatorEvidenceColumnMapping | None = None,
) -> RegulatorEvidenceImportReport:
    """Parse one explicit regulator evidence table into owned rows."""

    lines = _read_delimited_lines(path)
    active_mapping = mapping or RegulatorEvidenceColumnMapping()
    if not lines:
        return RegulatorEvidenceImportReport(
            source_path=str(path),
            total_rows=0,
            accepted_records=(),
            rejected_rows=(
                RejectedRegulatorEvidenceRow(
                    row_number=2,
                    reason="regulator evidence table is empty",
                ),
            ),
            column_mapping=active_mapping,
            summary=RegulatorEvidenceImportSummary(
                accepted_record_count=0,
                rejected_row_count=1,
                regulator_count=0,
                kinase_substrate_record_count=0,
                transcription_factor_target_record_count=0,
                pathway_record_count=0,
                ppi_record_count=0,
            ),
            note="regulator evidence import rejected an empty table",
        )

    reader = csv.DictReader(lines, delimiter=_infer_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("regulator evidence table must include a header row")
    _validate_required_columns(
        reader.fieldnames,
        (active_mapping.regulator, active_mapping.evidence_type),
    )

    accepted_records: list[RegulatorEvidenceRecord] = []
    rejected_rows: list[RejectedRegulatorEvidenceRow] = []
    for row_number, raw_row in enumerate(reader, start=2):
        values = _normalize_row(raw_row)
        regulator = values.get(active_mapping.regulator, "").strip()
        evidence_token = values.get(active_mapping.evidence_type, "").strip().lower()
        if not regulator:
            rejected_rows.append(
                RejectedRegulatorEvidenceRow(
                    row_number=row_number,
                    values=values,
                    reason="regulator evidence row requires regulator",
                )
            )
            continue
        try:
            evidence_type = RegulatorEvidenceType(evidence_token)
        except ValueError:
            rejected_rows.append(
                RejectedRegulatorEvidenceRow(
                    row_number=row_number,
                    values=values,
                    reason=(
                        "regulator evidence_type must be one of "
                        "kinase_substrate, transcription_factor_target, pathway, or ppi"
                    ),
                )
            )
            continue
        protein_ref = _optional_value(values, active_mapping.protein_ref)
        if protein_ref is not None:
            protein_ref = canonicalize_protein_reference(protein_ref)
        gene_symbol = _optional_value(values, active_mapping.gene_symbol)
        pathway_id = _optional_value(values, active_mapping.pathway_id)
        site_key = _optional_value(values, active_mapping.site_key)
        target_fields = tuple(
            field
            for field, value in (
                (RegulatorEvidenceTargetField.PROTEIN_REF, protein_ref),
                (RegulatorEvidenceTargetField.GENE_SYMBOL, gene_symbol),
                (RegulatorEvidenceTargetField.PATHWAY_ID, pathway_id),
                (RegulatorEvidenceTargetField.SITE_KEY, site_key),
            )
            if value is not None
        )
        if len(target_fields) != 1:
            rejected_rows.append(
                RejectedRegulatorEvidenceRow(
                    row_number=row_number,
                    values=values,
                    reason=(
                        "regulator evidence row must supply exactly one of protein_ref, "
                        "gene_symbol, pathway_id, or site_key"
                    ),
                )
            )
            continue
        target_field = target_fields[0]
        if evidence_type is RegulatorEvidenceType.KINASE_SUBSTRATE:
            if target_field is not RegulatorEvidenceTargetField.SITE_KEY:
                rejected_rows.append(
                    RejectedRegulatorEvidenceRow(
                        row_number=row_number,
                        values=values,
                        reason="kinase_substrate evidence rows must target site_key",
                    )
                )
                continue
        elif evidence_type is RegulatorEvidenceType.PATHWAY:
            if target_field is not RegulatorEvidenceTargetField.PATHWAY_ID:
                rejected_rows.append(
                    RejectedRegulatorEvidenceRow(
                        row_number=row_number,
                        values=values,
                        reason="pathway evidence rows must target pathway_id",
                    )
                )
                continue
        elif target_field not in {
            RegulatorEvidenceTargetField.PROTEIN_REF,
            RegulatorEvidenceTargetField.GENE_SYMBOL,
        }:
            rejected_rows.append(
                RejectedRegulatorEvidenceRow(
                    row_number=row_number,
                    values=values,
                    reason=(
                        "transcription_factor_target and ppi evidence rows must target "
                        "protein_ref or gene_symbol"
                    ),
                )
            )
            continue

        accepted_records.append(
            RegulatorEvidenceRecord(
                regulator=regulator,
                evidence_type=evidence_type,
                protein_ref=protein_ref,
                gene_symbol=gene_symbol,
                pathway_id=pathway_id,
                site_key=site_key,
                source_name=_optional_value(values, active_mapping.source_name),
                source_accession=_optional_value(values, active_mapping.source_accession),
                metadata={
                    key: value
                    for key, value in values.items()
                    if key
                    not in {
                        active_mapping.regulator,
                        active_mapping.evidence_type,
                        active_mapping.protein_ref,
                        active_mapping.gene_symbol,
                        active_mapping.pathway_id,
                        active_mapping.site_key,
                        active_mapping.source_name,
                        active_mapping.source_accession,
                    }
                },
            )
        )

    accepted_tuple = tuple(
        sorted(
            accepted_records,
            key=lambda record: (
                record.regulator,
                record.evidence_type.value,
                record.source_name or "",
                record.source_accession or "",
                record.protein_ref or "",
                record.gene_symbol or "",
                record.pathway_id or "",
                record.site_key or "",
            ),
        )
    )
    counts: DefaultDict[RegulatorEvidenceType, int] = defaultdict(int)
    for record in accepted_tuple:
        counts[record.evidence_type] += 1
    return RegulatorEvidenceImportReport(
        source_path=str(path),
        total_rows=max(len(lines) - 1, 0),
        accepted_records=accepted_tuple,
        rejected_rows=tuple(rejected_rows),
        column_mapping=active_mapping,
        summary=RegulatorEvidenceImportSummary(
            accepted_record_count=len(accepted_tuple),
            rejected_row_count=len(rejected_rows),
            regulator_count=len({record.regulator for record in accepted_tuple}),
            kinase_substrate_record_count=counts[RegulatorEvidenceType.KINASE_SUBSTRATE],
            transcription_factor_target_record_count=counts[
                RegulatorEvidenceType.TRANSCRIPTION_FACTOR_TARGET
            ],
            pathway_record_count=counts[RegulatorEvidenceType.PATHWAY],
            ppi_record_count=counts[RegulatorEvidenceType.PPI],
        ),
        note=(
            "regulator evidence import preserves explicit regulator names and target rows "
            "instead of inferring regulators from downstream annotations"
        ),
    )


def parse_regulator_site_signal_table(
    path: Path,
    *,
    mapping: RegulatorSiteSignalColumnMapping | None = None,
) -> RegulatorSiteSignalImportReport:
    """Parse one explicit site differential table for regulator inference."""

    lines = _read_delimited_lines(path)
    active_mapping = mapping or RegulatorSiteSignalColumnMapping()
    if not lines:
        return RegulatorSiteSignalImportReport(
            source_path=str(path),
            total_rows=0,
            accepted_entries=(),
            rejected_rows=(
                RejectedRegulatorSiteSignalRow(
                    row_number=2,
                    reason="regulator site signal table is empty",
                ),
            ),
            column_mapping=active_mapping,
            summary=RegulatorSiteSignalImportSummary(
                accepted_entry_count=0,
                rejected_row_count=1,
                distinct_site_count=0,
            ),
            note="regulator site signal import rejected an empty table",
        )

    reader = csv.DictReader(lines, delimiter=_infer_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("regulator site signal table must include a header row")
    _validate_required_columns(
        reader.fieldnames,
        (active_mapping.site_key, active_mapping.log2_fold_change),
    )

    accepted_entries: list[RegulatorSiteSignalEntry] = []
    rejected_rows: list[RejectedRegulatorSiteSignalRow] = []
    seen_site_keys: set[str] = set()
    for row_number, raw_row in enumerate(reader, start=2):
        values = _normalize_row(raw_row)
        site_key = values.get(active_mapping.site_key, "").strip()
        if not site_key:
            rejected_rows.append(
                RejectedRegulatorSiteSignalRow(
                    row_number=row_number,
                    values=values,
                    reason="regulator site signal row requires site_key",
                )
            )
            continue
        if site_key in seen_site_keys:
            rejected_rows.append(
                RejectedRegulatorSiteSignalRow(
                    row_number=row_number,
                    values=values,
                    reason=f"duplicate regulator site signal row for {site_key}",
                )
            )
            continue
        try:
            log2_fold_change = float(values.get(active_mapping.log2_fold_change, "").strip())
        except ValueError:
            rejected_rows.append(
                RejectedRegulatorSiteSignalRow(
                    row_number=row_number,
                    values=values,
                    reason="regulator site signal log2_fold_change must be numeric",
                )
            )
            continue
        adjusted_p_value = _optional_value(values, active_mapping.adjusted_p_value)
        try:
            adjusted_value = (
                None if adjusted_p_value is None else float(adjusted_p_value)
            )
        except ValueError:
            rejected_rows.append(
                RejectedRegulatorSiteSignalRow(
                    row_number=row_number,
                    values=values,
                    reason="regulator site signal adjusted_p_value must be numeric",
                )
            )
            continue
        seen_site_keys.add(site_key)
        accepted_entries.append(
            RegulatorSiteSignalEntry(
                site_key=site_key,
                protein_ref=_optional_value(values, active_mapping.protein_ref),
                log2_fold_change=log2_fold_change,
                adjusted_p_value=adjusted_value,
            )
        )

    accepted_tuple = tuple(
        sorted(accepted_entries, key=lambda entry: (entry.site_key, entry.protein_ref or ""))
    )
    return RegulatorSiteSignalImportReport(
        source_path=str(path),
        total_rows=max(len(lines) - 1, 0),
        accepted_entries=accepted_tuple,
        rejected_rows=tuple(rejected_rows),
        column_mapping=active_mapping,
        summary=RegulatorSiteSignalImportSummary(
            accepted_entry_count=len(accepted_tuple),
            rejected_row_count=len(rejected_rows),
            distinct_site_count=len(accepted_tuple),
        ),
        note="regulator site signal import preserves explicit site-level fold changes",
    )


def build_regulator_site_signal_entries_from_ptm_evidence_cards(
    report: PtmEvidenceCardReport,
) -> tuple[RegulatorSiteSignalEntry, ...]:
    """Project site-level differential signal from PTM evidence cards."""

    return tuple(
        RegulatorSiteSignalEntry(
            site_key=card.site_key,
            protein_ref=card.protein_ref,
            log2_fold_change=card.differential_result.log2_fold_change,
            adjusted_p_value=card.differential_result.adjusted_p_value,
        )
        for card in sorted(report.cards, key=lambda card: (card.protein_ref, card.site_key))
    )


def build_regulator_inference_report(
    evidence_records: tuple[RegulatorEvidenceRecord, ...],
    differential_report: DifferentialAbundanceReport,
    *,
    protein_refs_by_entity: dict[str, tuple[str, ...]] | None = None,
    annotation_report: ProteinAnnotationMappingReport | None = None,
    pathway_activity_report: PathwayActivityReport | None = None,
    site_signal_entries: tuple[RegulatorSiteSignalEntry, ...] = (),
    policy: RegulatorInferencePolicy | None = None,
) -> RegulatorInferenceReport:
    """Infer upstream regulator support from explicit user-supplied evidence rows."""

    active_policy = policy or RegulatorInferencePolicy()
    differential_by_protein_ref = _protein_signal_lookup(
        differential_report,
        protein_refs_by_entity=protein_refs_by_entity,
    )
    gene_symbol_to_protein_refs = _gene_symbol_lookup(annotation_report)
    pathway_lookup = _pathway_signal_lookup(
        pathway_activity_report,
        condition_a=differential_report.condition_a,
        condition_b=differential_report.condition_b,
    )
    site_signal_lookup = {entry.site_key: entry for entry in site_signal_entries}
    pathway_support_proteins = _pathway_supporting_protein_lookup(pathway_activity_report)

    grouped_records: dict[
        tuple[str, RegulatorEvidenceType, str | None, str | None],
        list[RegulatorEvidenceRecord],
    ] = defaultdict(list)
    for record in evidence_records:
        grouped_records[
            (
                record.regulator,
                record.evidence_type,
                record.source_name,
                record.source_accession,
            )
        ].append(record)

    entries: list[RegulatorInferenceEntry] = []
    unresolved_targets: list[UnresolvedRegulatorTargetEntry] = []
    for key in sorted(
        grouped_records,
        key=lambda item: (item[0], item[1].value, item[2] or "", item[3] or ""),
    ):
        regulator, evidence_type, source_name, source_accession = key
        records = grouped_records[key]
        if evidence_type is RegulatorEvidenceType.KINASE_SUBSTRATE:
            entry, unresolved = _build_site_regulation_entry(
                regulator=regulator,
                evidence_type=evidence_type,
                source_name=source_name,
                source_accession=source_accession,
                records=records,
                site_signal_lookup=site_signal_lookup,
                policy=active_policy,
            )
        elif evidence_type is RegulatorEvidenceType.PATHWAY:
            entry, unresolved = _build_pathway_activity_entry(
                regulator=regulator,
                evidence_type=evidence_type,
                source_name=source_name,
                source_accession=source_accession,
                records=records,
                pathway_lookup=pathway_lookup,
                pathway_support_proteins=pathway_support_proteins,
                policy=active_policy,
            )
        else:
            entry, unresolved = _build_protein_abundance_entry(
                regulator=regulator,
                evidence_type=evidence_type,
                source_name=source_name,
                source_accession=source_accession,
                records=records,
                differential_by_protein_ref=differential_by_protein_ref,
                gene_symbol_to_protein_refs=gene_symbol_to_protein_refs,
                policy=active_policy,
            )
        entries.append(entry)
        unresolved_targets.extend(unresolved)

    entry_tuple = tuple(
        sorted(
            entries,
            key=lambda entry: (
                -entry.score,
                entry.regulator,
                entry.evidence_type.value,
                entry.signal_surface.value,
                entry.source_name or "",
                entry.source_accession or "",
            ),
        )
    )
    unresolved_tuple = tuple(
        sorted(
            unresolved_targets,
            key=lambda entry: (
                entry.regulator,
                entry.evidence_type.value,
                entry.target_field.value,
                entry.target_value,
                entry.reason,
            ),
        )
    )
    summary = RegulatorInferenceSummary(
        regulator_count=len({entry.regulator for entry in entry_tuple}),
        entry_count=len(entry_tuple),
        site_regulation_entry_count=sum(
            1
            for entry in entry_tuple
            if entry.signal_surface is RegulatorSignalSurface.SITE_REGULATION
        ),
        protein_abundance_entry_count=sum(
            1
            for entry in entry_tuple
            if entry.signal_surface is RegulatorSignalSurface.PROTEIN_ABUNDANCE
        ),
        pathway_activity_entry_count=sum(
            1
            for entry in entry_tuple
            if entry.signal_surface is RegulatorSignalSurface.PATHWAY_ACTIVITY
        ),
        unresolved_target_count=len(unresolved_tuple),
        high_scoring_entry_count=sum(1 for entry in entry_tuple if entry.score >= 0.7),
    )
    return RegulatorInferenceReport(
        condition_a=differential_report.condition_a,
        condition_b=differential_report.condition_b,
        entries=entry_tuple,
        unresolved_targets=unresolved_tuple,
        summary=summary,
        note=(
            "regulator inference preserves site-regulation, protein-abundance, and "
            "pathway-activity support as separate evidence surfaces instead of "
            "collapsing kinase-site evidence into generic abundance support"
        ),
    )


def render_regulator_inference_summary_tsv(report: RegulatorInferenceReport) -> str:
    """Render the stable summary over one regulator inference report."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "condition_a",
            "condition_b",
            "regulator_count",
            "entry_count",
            "site_regulation_entry_count",
            "protein_abundance_entry_count",
            "pathway_activity_entry_count",
            "unresolved_target_count",
            "high_scoring_entry_count",
            "note",
        )
    )
    writer.writerow(
        (
            report.condition_a,
            report.condition_b,
            report.summary.regulator_count,
            report.summary.entry_count,
            report.summary.site_regulation_entry_count,
            report.summary.protein_abundance_entry_count,
            report.summary.pathway_activity_entry_count,
            report.summary.unresolved_target_count,
            report.summary.high_scoring_entry_count,
            report.note,
        )
    )
    return buffer.getvalue()


def render_regulator_inference_tsv(report: RegulatorInferenceReport) -> str:
    """Render one stable regulator inference table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "regulator",
            "evidence_type",
            "signal_surface",
            "source_name",
            "source_accession",
            "target_count",
            "matched_target_count",
            "coverage_fraction",
            "supporting_protein_refs",
            "supporting_site_keys",
            "supporting_pathway_ids",
            "direction",
            "score",
            "mean_log2_fold_change",
            "mean_activity_score_delta",
            "note",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.regulator,
                entry.evidence_type.value,
                entry.signal_surface.value,
                entry.source_name or "",
                entry.source_accession or "",
                entry.target_count,
                entry.matched_target_count,
                _format_float(entry.coverage_fraction),
                ";".join(entry.supporting_protein_refs),
                ";".join(entry.supporting_site_keys),
                ";".join(entry.supporting_pathway_ids),
                entry.direction.value,
                _format_float(entry.score),
                _format_optional_float(entry.mean_log2_fold_change),
                _format_optional_float(entry.mean_activity_score_delta),
                entry.note,
            )
        )
    return buffer.getvalue()


def render_unresolved_regulator_target_tsv(report: RegulatorInferenceReport) -> str:
    """Render explicit unresolved regulator targets and why they failed."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "regulator",
            "evidence_type",
            "target_field",
            "target_value",
            "source_name",
            "source_accession",
            "reason",
        )
    )
    for entry in report.unresolved_targets:
        writer.writerow(
            (
                entry.regulator,
                entry.evidence_type.value,
                entry.target_field.value,
                entry.target_value,
                entry.source_name or "",
                entry.source_accession or "",
                entry.reason,
            )
        )
    return buffer.getvalue()


def render_rejected_regulator_evidence_tsv(report: RegulatorEvidenceImportReport) -> str:
    """Render rejected regulator evidence rows with stable reasons."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("row_number", "reason", "values"))
    for row in report.rejected_rows:
        writer.writerow((row.row_number, row.reason, _format_values(row.values)))
    return buffer.getvalue()


def render_rejected_regulator_site_signal_tsv(
    report: RegulatorSiteSignalImportReport,
) -> str:
    """Render rejected regulator site signal rows with stable reasons."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("row_number", "reason", "values"))
    for row in report.rejected_rows:
        writer.writerow((row.row_number, row.reason, _format_values(row.values)))
    return buffer.getvalue()


def _build_site_regulation_entry(
    *,
    regulator: str,
    evidence_type: RegulatorEvidenceType,
    source_name: str | None,
    source_accession: str | None,
    records: list[RegulatorEvidenceRecord],
    site_signal_lookup: dict[str, RegulatorSiteSignalEntry],
    policy: RegulatorInferencePolicy,
) -> tuple[RegulatorInferenceEntry, list[UnresolvedRegulatorTargetEntry]]:
    values: list[float] = []
    significance: list[float] = []
    supporting_protein_refs: set[str] = set()
    supporting_site_keys: set[str] = set()
    unresolved: list[UnresolvedRegulatorTargetEntry] = []
    matched_target_count = 0
    for record in records:
        if record.site_key is None:
            raise RuntimeError(
                "site-regulation regulator inference requires evidence records with site keys"
            )
        signal = site_signal_lookup.get(record.site_key)
        if signal is None:
            unresolved.append(
                UnresolvedRegulatorTargetEntry(
                    regulator=regulator,
                    evidence_type=evidence_type,
                    target_field=RegulatorEvidenceTargetField.SITE_KEY,
                    target_value=record.site_key,
                    source_name=source_name,
                    source_accession=source_accession,
                    reason="site_key was not present in the supplied site regulation surface",
                )
            )
            continue
        matched_target_count += 1
        values.append(signal.log2_fold_change)
        significance.append(_significance_score(signal.adjusted_p_value))
        supporting_site_keys.add(signal.site_key)
        if signal.protein_ref is not None:
            supporting_protein_refs.add(canonicalize_protein_reference(signal.protein_ref))
    return (
        _build_inference_entry(
            regulator=regulator,
            evidence_type=evidence_type,
            signal_surface=RegulatorSignalSurface.SITE_REGULATION,
            source_name=source_name,
            source_accession=source_accession,
            target_count=len(records),
            matched_target_count=matched_target_count,
            supporting_protein_refs=supporting_protein_refs,
            supporting_site_keys=supporting_site_keys,
            supporting_pathway_ids=set(),
            signal_values=values,
            significance_scores=significance,
            policy=policy,
        ),
        unresolved,
    )


def _build_protein_abundance_entry(
    *,
    regulator: str,
    evidence_type: RegulatorEvidenceType,
    source_name: str | None,
    source_accession: str | None,
    records: list[RegulatorEvidenceRecord],
    differential_by_protein_ref: dict[str, tuple[float, float | None]],
    gene_symbol_to_protein_refs: dict[str, tuple[str, ...]],
    policy: RegulatorInferencePolicy,
) -> tuple[RegulatorInferenceEntry, list[UnresolvedRegulatorTargetEntry]]:
    values: list[float] = []
    significance: list[float] = []
    supporting_protein_refs: set[str] = set()
    unresolved: list[UnresolvedRegulatorTargetEntry] = []
    matched_target_count = 0
    for record in records:
        resolved_protein_refs: tuple[str, ...]
        if record.protein_ref is not None:
            resolved_protein_refs = (record.protein_ref,)
            target_field = RegulatorEvidenceTargetField.PROTEIN_REF
            target_value = record.protein_ref
        else:
            if record.gene_symbol is None:
                raise RuntimeError(
                    "protein-abundance regulator inference requires a gene symbol when no protein ref is provided"
                )
            resolved_protein_refs = gene_symbol_to_protein_refs.get(
                record.gene_symbol.upper(),
                (),
            )
            target_field = RegulatorEvidenceTargetField.GENE_SYMBOL
            target_value = record.gene_symbol
        if not resolved_protein_refs:
            unresolved.append(
                UnresolvedRegulatorTargetEntry(
                    regulator=regulator,
                    evidence_type=evidence_type,
                    target_field=target_field,
                    target_value=target_value,
                    source_name=source_name,
                    source_accession=source_accession,
                    reason="target did not resolve onto the observed protein differential surface",
                )
            )
            continue
        matched_for_target = False
        for protein_ref in resolved_protein_refs:
            signal = differential_by_protein_ref.get(protein_ref)
            if signal is None:
                continue
            matched_for_target = True
            supporting_protein_refs.add(protein_ref)
            values.append(signal[0])
            significance.append(_significance_score(signal[1]))
        if matched_for_target:
            matched_target_count += 1
        else:
            unresolved.append(
                UnresolvedRegulatorTargetEntry(
                    regulator=regulator,
                    evidence_type=evidence_type,
                    target_field=target_field,
                    target_value=target_value,
                    source_name=source_name,
                    source_accession=source_accession,
                    reason="target resolved to annotations but none of those proteins carried observed differential signal",
                )
            )
    return (
        _build_inference_entry(
            regulator=regulator,
            evidence_type=evidence_type,
            signal_surface=RegulatorSignalSurface.PROTEIN_ABUNDANCE,
            source_name=source_name,
            source_accession=source_accession,
            target_count=len(records),
            matched_target_count=matched_target_count,
            supporting_protein_refs=supporting_protein_refs,
            supporting_site_keys=set(),
            supporting_pathway_ids=set(),
            signal_values=values,
            significance_scores=significance,
            policy=policy,
        ),
        unresolved,
    )


def _build_pathway_activity_entry(
    *,
    regulator: str,
    evidence_type: RegulatorEvidenceType,
    source_name: str | None,
    source_accession: str | None,
    records: list[RegulatorEvidenceRecord],
    pathway_lookup: dict[str, tuple[float | None, PathwayActivityConfidenceStatus]],
    pathway_support_proteins: dict[str, tuple[str, ...]],
    policy: RegulatorInferencePolicy,
) -> tuple[RegulatorInferenceEntry, list[UnresolvedRegulatorTargetEntry]]:
    values: list[float] = []
    significance: list[float] = []
    supporting_protein_refs: set[str] = set()
    supporting_pathway_ids: set[str] = set()
    unresolved: list[UnresolvedRegulatorTargetEntry] = []
    matched_target_count = 0
    for record in records:
        if record.pathway_id is None:
            raise RuntimeError(
                "pathway regulator inference requires evidence records with pathway ids"
            )
        pathway_signal = pathway_lookup.get(record.pathway_id)
        if pathway_signal is None or pathway_signal[0] is None:
            unresolved.append(
                UnresolvedRegulatorTargetEntry(
                    regulator=regulator,
                    evidence_type=evidence_type,
                    target_field=RegulatorEvidenceTargetField.PATHWAY_ID,
                    target_value=record.pathway_id,
                    source_name=source_name,
                    source_accession=source_accession,
                    reason="pathway_id was not present in the supplied pathway activity surface",
                )
            )
            continue
        matched_target_count += 1
        delta_value, confidence = pathway_signal
        if delta_value is None:
            raise RuntimeError("validated pathway signal unexpectedly lost its delta")
        values.append(delta_value)
        significance.append(1.0 if confidence is PathwayActivityConfidenceStatus.HIGH_CONFIDENCE else 0.5)
        supporting_pathway_ids.add(record.pathway_id)
        supporting_protein_refs.update(pathway_support_proteins.get(record.pathway_id, ()))
    return (
        _build_inference_entry(
            regulator=regulator,
            evidence_type=evidence_type,
            signal_surface=RegulatorSignalSurface.PATHWAY_ACTIVITY,
            source_name=source_name,
            source_accession=source_accession,
            target_count=len(records),
            matched_target_count=matched_target_count,
            supporting_protein_refs=supporting_protein_refs,
            supporting_site_keys=set(),
            supporting_pathway_ids=supporting_pathway_ids,
            signal_values=values,
            significance_scores=significance,
            policy=policy,
        ),
        unresolved,
    )


def _build_inference_entry(
    *,
    regulator: str,
    evidence_type: RegulatorEvidenceType,
    signal_surface: RegulatorSignalSurface,
    source_name: str | None,
    source_accession: str | None,
    target_count: int,
    matched_target_count: int,
    supporting_protein_refs: set[str],
    supporting_site_keys: set[str],
    supporting_pathway_ids: set[str],
    signal_values: list[float],
    significance_scores: list[float],
    policy: RegulatorInferencePolicy,
) -> RegulatorInferenceEntry:
    coverage_fraction = 0.0 if target_count == 0 else matched_target_count / target_count
    direction = _resolve_direction(signal_values)
    mean_log2_fold_change = None
    mean_activity_score_delta = None
    if signal_surface is RegulatorSignalSurface.PATHWAY_ACTIVITY:
        if signal_values:
            mean_activity_score_delta = sum(signal_values) / len(signal_values)
    elif signal_values:
        mean_log2_fold_change = sum(signal_values) / len(signal_values)
    score = _score_regulator_support(
        coverage_fraction=coverage_fraction,
        matched_signal_count=len(signal_values),
        signal_values=signal_values,
        significance_scores=significance_scores,
        direction=direction,
    )
    if coverage_fraction < policy.minimum_target_coverage_fraction:
        score = min(score, policy.low_coverage_score_cap)
    note = _build_inference_note(
        evidence_type=evidence_type,
        signal_surface=signal_surface,
        target_count=target_count,
        matched_target_count=matched_target_count,
        direction=direction,
        coverage_fraction=coverage_fraction,
        policy=policy,
    )
    return RegulatorInferenceEntry(
        regulator=regulator,
        evidence_type=evidence_type,
        signal_surface=signal_surface,
        source_name=source_name,
        source_accession=source_accession,
        target_count=target_count,
        matched_target_count=matched_target_count,
        coverage_fraction=round(coverage_fraction, 4),
        supporting_protein_refs=sort_strings(tuple(supporting_protein_refs)),
        supporting_site_keys=sort_strings(tuple(supporting_site_keys)),
        supporting_pathway_ids=sort_strings(tuple(supporting_pathway_ids)),
        direction=direction,
        score=round(score, 4),
        mean_log2_fold_change=None
        if mean_log2_fold_change is None
        else round(mean_log2_fold_change, 4),
        mean_activity_score_delta=None
        if mean_activity_score_delta is None
        else round(mean_activity_score_delta, 4),
        note=note,
    )


def _protein_signal_lookup(
    report: DifferentialAbundanceReport,
    *,
    protein_refs_by_entity: dict[str, tuple[str, ...]] | None,
) -> dict[str, tuple[float, float | None]]:
    lookup: dict[str, tuple[float, float | None]] = {}
    for entry in report.entries:
        protein_refs = (
            protein_refs_by_entity.get(entry.entity_id, (entry.entity_id,))
            if protein_refs_by_entity is not None
            else (entry.entity_id,)
        )
        for protein_ref in protein_refs:
            protein_ref = canonicalize_protein_reference(protein_ref)
            existing = lookup.get(protein_ref)
            if existing is None or _is_better_signal(
                candidate_adjusted_p_value=entry.adjusted_p_value,
                candidate_log2_fold_change=entry.log2_fold_change,
                current_adjusted_p_value=existing[1],
                current_log2_fold_change=existing[0],
            ):
                lookup[protein_ref] = (entry.log2_fold_change, entry.adjusted_p_value)
    return lookup


def _gene_symbol_lookup(
    annotation_report: ProteinAnnotationMappingReport | None,
) -> dict[str, tuple[str, ...]]:
    mapping: dict[str, set[str]] = defaultdict(set)
    if annotation_report is None:
        return {}
    for entry in annotation_report.mapped_entries:
        if entry.gene_symbol:
            mapping[entry.gene_symbol.upper()].add(entry.protein_ref)
    return {
        gene_symbol: sort_strings(tuple(protein_refs))
        for gene_symbol, protein_refs in mapping.items()
    }


def _pathway_signal_lookup(
    report: PathwayActivityReport | None,
    *,
    condition_a: str,
    condition_b: str,
) -> dict[str, tuple[float | None, PathwayActivityConfidenceStatus]]:
    if report is None:
        return {}
    return {
        entry.pathway_id: (
            entry.activity_score_delta,
            entry.comparison_confidence_status,
        )
        for entry in report.condition_comparisons
        if entry.condition_a == condition_a and entry.condition_b == condition_b
    }


def _pathway_supporting_protein_lookup(
    report: PathwayActivityReport | None,
) -> dict[str, tuple[str, ...]]:
    if report is None:
        return {}
    proteins_by_pathway: dict[str, set[str]] = defaultdict(set)
    for entry in report.member_contributions:
        proteins_by_pathway[entry.pathway_id].update(entry.observed_protein_refs)
    return {
        pathway_id: sort_strings(tuple(protein_refs))
        for pathway_id, protein_refs in proteins_by_pathway.items()
    }


def _score_regulator_support(
    *,
    coverage_fraction: float,
    matched_signal_count: int,
    signal_values: list[float],
    significance_scores: list[float],
    direction: RegulatorInferenceDirection,
) -> float:
    support_count_score = min(1.0, matched_signal_count / 3.0)
    effect_score = (
        0.0
        if not signal_values
        else min(1.0, sum(abs(value) for value in signal_values) / len(signal_values) / 2.0)
    )
    significance_score = (
        0.0
        if not significance_scores
        else sum(significance_scores) / len(significance_scores)
    )
    score = (
        (0.35 * coverage_fraction)
        + (0.20 * support_count_score)
        + (0.25 * effect_score)
        + (0.20 * significance_score)
    )
    if direction is RegulatorInferenceDirection.MIXED:
        score -= 0.15
    return max(0.0, min(1.0, score))


def _resolve_direction(values: list[float]) -> RegulatorInferenceDirection:
    positive = any(value > 0.0 for value in values)
    negative = any(value < 0.0 for value in values)
    if positive and negative:
        return RegulatorInferenceDirection.MIXED
    if positive:
        return RegulatorInferenceDirection.UP
    if negative:
        return RegulatorInferenceDirection.DOWN
    return RegulatorInferenceDirection.UNSUPPORTED


def _build_inference_note(
    *,
    evidence_type: RegulatorEvidenceType,
    signal_surface: RegulatorSignalSurface,
    target_count: int,
    matched_target_count: int,
    direction: RegulatorInferenceDirection,
    coverage_fraction: float,
    policy: RegulatorInferencePolicy,
) -> str:
    coverage_note = _build_low_coverage_note(
        coverage_fraction=coverage_fraction,
        policy=policy,
    )
    if matched_target_count == 0:
        note = (
            f"{evidence_type.value} evidence did not resolve onto the supplied "
            f"{signal_surface.value} surface"
        )
        return note if coverage_note is None else f"{note}; {coverage_note}"
    if direction is RegulatorInferenceDirection.MIXED:
        note = (
            f"{matched_target_count} of {target_count} explicit {evidence_type.value} "
            "targets were observed with conflicting directions"
        )
        return note if coverage_note is None else f"{note}; {coverage_note}"
    note = (
        f"{matched_target_count} of {target_count} explicit {evidence_type.value} "
        f"targets were observed on the {signal_surface.value} surface"
    )
    return note if coverage_note is None else f"{note}; {coverage_note}"


def _build_low_coverage_note(
    *,
    coverage_fraction: float,
    policy: RegulatorInferencePolicy,
) -> str | None:
    if coverage_fraction >= policy.minimum_target_coverage_fraction:
        return None
    return (
        "target coverage "
        f"{coverage_fraction:g} was below minimum {policy.minimum_target_coverage_fraction:g}"
    )


def _significance_score(adjusted_p_value: float | None) -> float:
    if adjusted_p_value is None:
        return 0.5
    return max(0.0, min(1.0, 1.0 - adjusted_p_value))


def _is_better_signal(
    *,
    candidate_adjusted_p_value: float | None,
    candidate_log2_fold_change: float,
    current_adjusted_p_value: float | None,
    current_log2_fold_change: float,
) -> bool:
    candidate_key = (
        1.0 if candidate_adjusted_p_value is None else candidate_adjusted_p_value,
        -abs(candidate_log2_fold_change),
    )
    current_key = (
        1.0 if current_adjusted_p_value is None else current_adjusted_p_value,
        -abs(current_log2_fold_change),
    )
    return candidate_key < current_key


def _read_delimited_lines(path: Path) -> list[str]:
    return [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _infer_delimiter(header_line: str) -> str:
    return "\t" if header_line.count("\t") >= header_line.count(",") else ","


def _validate_required_columns(
    fieldnames: Sequence[str],
    required: tuple[str | None, ...],
) -> None:
    missing = [field for field in required if field is not None and field not in fieldnames]
    if missing:
        raise ValueError(
            "table is missing required columns: " + ", ".join(sorted(missing))
        )


def _normalize_row(row: dict[str, str | None]) -> dict[str, str]:
    return {key: (value or "").strip() for key, value in row.items() if key is not None}


def _optional_value(values: dict[str, str], field: str | None) -> str | None:
    if field is None:
        return None
    value = values.get(field, "").strip()
    return value or None


def _format_float(value: float) -> str:
    return f"{value:.4g}"


def _format_optional_float(value: float | None) -> str:
    return "" if value is None else f"{value:.4g}"


def _format_values(values: dict[str, str]) -> str:
    return "; ".join(f"{key}={value}" for key, value in sorted(values.items()))


__all__ = [
    "RegulatorEvidenceColumnMapping",
    "RegulatorEvidenceImportReport",
    "RegulatorEvidenceImportSummary",
    "RegulatorEvidenceRecord",
    "RegulatorEvidenceTargetField",
    "RegulatorEvidenceType",
    "RegulatorInferenceDirection",
    "RegulatorInferenceEntry",
    "RegulatorInferencePolicy",
    "RegulatorInferenceReport",
    "RegulatorInferenceSummary",
    "RegulatorSignalSurface",
    "RegulatorSiteSignalColumnMapping",
    "RegulatorSiteSignalEntry",
    "RegulatorSiteSignalImportReport",
    "RegulatorSiteSignalImportSummary",
    "RejectedRegulatorEvidenceRow",
    "RejectedRegulatorSiteSignalRow",
    "UnresolvedRegulatorTargetEntry",
    "build_regulator_inference_report",
    "build_regulator_site_signal_entries_from_ptm_evidence_cards",
    "parse_regulator_evidence_table",
    "parse_regulator_site_signal_table",
    "render_rejected_regulator_evidence_tsv",
    "render_rejected_regulator_site_signal_tsv",
    "render_regulator_inference_summary_tsv",
    "render_regulator_inference_tsv",
    "render_unresolved_regulator_target_tsv",
]
