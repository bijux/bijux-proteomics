# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned protein functional-region parsing, mapping, and rendering workflows."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
import csv
from io import StringIO
from pathlib import Path

from bijux_proteomics.sequences.protein_region_context_models import (
    ProteinFunctionalRegionEvidence,
    ProteinFunctionalRegionKind,
    ProteinPeptideRegionContextEntry,
    ProteinPeptideRegionContextReport,
    ProteinPeptideRegionContextSummary,
    ProteinPeptideRegionReference,
    ProteinPeptideSpan,
    ProteinRegionContextColumnMapping,
    ProteinRegionContextImportReport,
    ProteinRegionContextImportSummary,
    ProteinRegionContextRecord,
    ProteinRegionContextStatus,
    ProteinRegionContextValidationIssue,
    ProteinSiteRegionContextEntry,
    ProteinSiteRegionContextReport,
    ProteinSiteRegionContextSummary,
    ProteinSiteRegionReference,
    RejectedProteinRegionContextRow,
)


def parse_protein_region_context_tsv(
    path: Path,
    *,
    mapping: ProteinRegionContextColumnMapping | None = None,
) -> ProteinRegionContextImportReport:
    """Parse one protein functional-region TSV into owned normalized records."""

    active_mapping = mapping or ProteinRegionContextColumnMapping(
        protein_ref="protein_ref",
        start="start",
        end="end",
        domain_name="domain_name",
        signal_peptide="signal_peptide",
        transmembrane_region="transmembrane_region",
        disorder_region="disorder_region",
        low_complexity_region="low_complexity_region",
        active_site_label="active_site_label",
        binding_region="binding_region",
        motif_name="motif_name",
        conservation_score="conservation_score",
        source_name="source_name",
        source_accession="source_accession",
    )
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("protein region context TSV must include a header row")
        _validate_required_columns(reader.fieldnames, active_mapping)

        accepted: list[ProteinRegionContextRecord] = []
        rejected: list[RejectedProteinRegionContextRow] = []
        for row_number, row in enumerate(reader, start=2):
            raw_fields = {
                str(key): str(value or "")
                for key, value in row.items()
                if key is not None
            }
            issues: list[ProteinRegionContextValidationIssue] = []

            protein_ref = raw_fields.get(active_mapping.protein_ref, "").strip()
            start_token = raw_fields.get(active_mapping.start, "").strip()
            end_token = raw_fields.get(active_mapping.end, "").strip()
            domain_name = _row_value(raw_fields, active_mapping.domain_name)
            signal_peptide = _row_value(raw_fields, active_mapping.signal_peptide)
            transmembrane_region = _row_value(
                raw_fields,
                active_mapping.transmembrane_region,
            )
            disorder_region = _row_value(raw_fields, active_mapping.disorder_region)
            low_complexity_region = _row_value(
                raw_fields,
                active_mapping.low_complexity_region,
            )
            active_site_label = _row_value(raw_fields, active_mapping.active_site_label)
            binding_region = _row_value(raw_fields, active_mapping.binding_region)
            motif_name = _row_value(raw_fields, active_mapping.motif_name)
            conservation_token = _row_value(
                raw_fields, active_mapping.conservation_score
            )

            if not protein_ref:
                issues.append(
                    _row_issue(
                        "missing_protein_ref",
                        "missing protein reference",
                        row_number,
                    )
                )
            if not any(
                value is not None
                for value in (
                    domain_name,
                    signal_peptide,
                    transmembrane_region,
                    disorder_region,
                    low_complexity_region,
                    active_site_label,
                    binding_region,
                    motif_name,
                    conservation_token,
                )
            ):
                issues.append(
                    _row_issue(
                        "missing_context_fields",
                        "protein region row requires at least one annotation field",
                        row_number,
                    )
                )

            start: int | None = None
            end: int | None = None
            try:
                start = int(start_token)
                if start < 1:
                    raise ValueError
            except ValueError:
                issues.append(
                    _row_issue(
                        "invalid_start",
                        "start must be a positive integer",
                        row_number,
                    )
                )
            try:
                end = int(end_token)
                if end < 1:
                    raise ValueError
            except ValueError:
                issues.append(
                    _row_issue(
                        "invalid_end",
                        "end must be a positive integer",
                        row_number,
                    )
                )
            if start is not None and end is not None and end < start:
                issues.append(
                    _row_issue(
                        "inverted_interval",
                        "end must be greater than or equal to start",
                        row_number,
                    )
                )

            conservation_score: float | None = None
            if conservation_token is not None:
                try:
                    conservation_score = float(conservation_token)
                    if conservation_score < 0.0 or conservation_score > 1.0:
                        raise ValueError
                except ValueError:
                    issues.append(
                        _row_issue(
                            "invalid_conservation_score",
                            "conservation score must be between 0.0 and 1.0",
                            row_number,
                        )
                    )

            if issues:
                rejected.append(
                    RejectedProteinRegionContextRow(
                        row_number=row_number,
                        raw_fields=raw_fields,
                        issues=tuple(issues),
                    )
                )
                continue

            if start is None or end is None:
                raise ValueError(
                    "validated protein region context rows must carry start and end coordinates"
                )
            accepted.append(
                ProteinRegionContextRecord(
                    protein_ref=protein_ref,
                    start=start,
                    end=end,
                    domain_name=domain_name,
                    signal_peptide=signal_peptide,
                    transmembrane_region=transmembrane_region,
                    disorder_region=disorder_region,
                    low_complexity_region=low_complexity_region,
                    active_site_label=active_site_label,
                    binding_region=binding_region,
                    motif_name=motif_name,
                    conservation_score=conservation_score,
                    source_name=_row_value(raw_fields, active_mapping.source_name),
                    source_accession=_row_value(
                        raw_fields,
                        active_mapping.source_accession,
                    ),
                )
            )

    accepted_records = tuple(
        sorted(
            accepted,
            key=lambda record: (
                record.protein_ref,
                record.start,
                record.end,
                record.domain_name or "",
                record.signal_peptide or "",
                record.binding_region or "",
                record.motif_name or "",
            ),
        )
    )
    return ProteinRegionContextImportReport(
        total_rows=len(accepted_records) + len(rejected),
        accepted_records=accepted_records,
        rejected_rows=tuple(rejected),
        column_mapping=active_mapping,
        summary=ProteinRegionContextImportSummary(
            accepted_record_count=len(accepted_records),
            rejected_row_count=len(rejected),
            distinct_protein_ref_count=len(
                {record.protein_ref for record in accepted_records}
            ),
            domain_record_count=sum(
                1 for record in accepted_records if record.domain_name is not None
            ),
            signal_peptide_record_count=sum(
                1 for record in accepted_records if record.signal_peptide is not None
            ),
            transmembrane_record_count=sum(
                1
                for record in accepted_records
                if record.transmembrane_region is not None
            ),
            disorder_record_count=sum(
                1 for record in accepted_records if record.disorder_region is not None
            ),
            low_complexity_record_count=sum(
                1
                for record in accepted_records
                if record.low_complexity_region is not None
            ),
            active_site_record_count=sum(
                1 for record in accepted_records if record.active_site_label is not None
            ),
            binding_region_record_count=sum(
                1 for record in accepted_records if record.binding_region is not None
            ),
            motif_record_count=sum(
                1 for record in accepted_records if record.motif_name is not None
            ),
            conservation_record_count=sum(
                1
                for record in accepted_records
                if record.conservation_score is not None
            ),
        ),
        note=(
            "protein region context import preserves functional annotations for domains, "
            "signal peptides, transmembrane spans, disorder, low-complexity segments, "
            "active sites, binding regions, motifs, and conservation before evidence mapping"
        ),
    )


def build_protein_site_region_context_report(
    site_entries: tuple[ProteinSiteRegionReference, ...],
    context_records: tuple[ProteinRegionContextRecord, ...],
) -> ProteinSiteRegionContextReport:
    """Map provided protein-region annotations onto observed protein sites."""

    context_by_protein: dict[str, list[ProteinRegionContextRecord]] = {}
    for record in context_records:
        context_by_protein.setdefault(record.protein_ref, []).append(record)

    entries: list[ProteinSiteRegionContextEntry] = []
    for site_entry in site_entries:
        matched_records = tuple(
            record
            for record in context_by_protein.get(site_entry.protein_ref, ())
            if record.start <= site_entry.position <= record.end
        )
        functional_regions = _functional_regions(
            matched_records,
            supporting_evidence_refs=(site_entry.site_key,),
        )
        entries.append(
            ProteinSiteRegionContextEntry(
                site_key=site_entry.site_key,
                protein_ref=site_entry.protein_ref,
                position=site_entry.position,
                matched_context_record_count=len(matched_records),
                context_status=(
                    ProteinRegionContextStatus.CONTEXT_ANNOTATED
                    if matched_records
                    else ProteinRegionContextStatus.OUTSIDE_PROVIDED_ANNOTATIONS
                ),
                domain_names=_unique_sorted(
                    record.domain_name
                    for record in matched_records
                    if record.domain_name is not None
                ),
                signal_peptides=_unique_sorted(
                    record.signal_peptide
                    for record in matched_records
                    if record.signal_peptide is not None
                ),
                transmembrane_regions=_unique_sorted(
                    record.transmembrane_region
                    for record in matched_records
                    if record.transmembrane_region is not None
                ),
                disorder_regions=_unique_sorted(
                    record.disorder_region
                    for record in matched_records
                    if record.disorder_region is not None
                ),
                low_complexity_regions=_unique_sorted(
                    record.low_complexity_region
                    for record in matched_records
                    if record.low_complexity_region is not None
                ),
                active_site_labels=_unique_sorted(
                    record.active_site_label
                    for record in matched_records
                    if record.active_site_label is not None
                ),
                binding_regions=_unique_sorted(
                    record.binding_region
                    for record in matched_records
                    if record.binding_region is not None
                ),
                motif_names=_unique_sorted(
                    record.motif_name
                    for record in matched_records
                    if record.motif_name is not None
                ),
                conservation_scores=_conservation_scores(matched_records),
                max_conservation_score=_max_conservation_score(matched_records),
                source_names=_unique_sorted(
                    record.source_name
                    for record in matched_records
                    if record.source_name is not None
                ),
                source_accessions=_unique_sorted(
                    record.source_accession
                    for record in matched_records
                    if record.source_accession is not None
                ),
                functional_regions=functional_regions,
            )
        )

    stable_entries = tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.protein_ref,
                entry.position,
                entry.site_key,
            ),
        )
    )
    return ProteinSiteRegionContextReport(
        entries=stable_entries,
        summary=ProteinSiteRegionContextSummary(
            site_count=len(stable_entries),
            context_annotated_site_count=sum(
                1
                for entry in stable_entries
                if entry.context_status is ProteinRegionContextStatus.CONTEXT_ANNOTATED
            ),
            outside_annotation_site_count=sum(
                1
                for entry in stable_entries
                if entry.context_status
                is ProteinRegionContextStatus.OUTSIDE_PROVIDED_ANNOTATIONS
            ),
            domain_annotated_site_count=sum(
                1 for entry in stable_entries if entry.domain_names
            ),
            signal_peptide_annotated_site_count=sum(
                1 for entry in stable_entries if entry.signal_peptides
            ),
            transmembrane_annotated_site_count=sum(
                1 for entry in stable_entries if entry.transmembrane_regions
            ),
            disorder_annotated_site_count=sum(
                1 for entry in stable_entries if entry.disorder_regions
            ),
            low_complexity_annotated_site_count=sum(
                1 for entry in stable_entries if entry.low_complexity_regions
            ),
            active_site_annotated_site_count=sum(
                1 for entry in stable_entries if entry.active_site_labels
            ),
            binding_region_annotated_site_count=sum(
                1 for entry in stable_entries if entry.binding_regions
            ),
            motif_annotated_site_count=sum(
                1 for entry in stable_entries if entry.motif_names
            ),
            conservation_annotated_site_count=sum(
                1 for entry in stable_entries if entry.conservation_scores
            ),
        ),
        note=(
            "protein site region context preserves one row for every observed site, "
            "keeps functional region annotations when present, and marks sites outside "
            "the provided annotations explicitly"
        ),
    )


def build_protein_peptide_region_context_report(
    peptide_entries: tuple[ProteinPeptideRegionReference, ...],
    *,
    protein_sequences: dict[str, str],
    context_records: tuple[ProteinRegionContextRecord, ...],
) -> ProteinPeptideRegionContextReport:
    """Map peptide evidence onto functional protein-region annotations."""

    context_by_protein: dict[str, list[ProteinRegionContextRecord]] = {}
    for record in context_records:
        context_by_protein.setdefault(record.protein_ref, []).append(record)

    entries: list[ProteinPeptideRegionContextEntry] = []
    for peptide_entry in peptide_entries:
        spans = _find_peptide_spans(
            protein_sequences.get(peptide_entry.protein_ref, ""),
            peptide_entry.peptide_sequence,
        )
        matched_records = tuple(
            record
            for record in context_by_protein.get(peptide_entry.protein_ref, ())
            if any(_spans_overlap(span, record.start, record.end) for span in spans)
        )
        if not spans:
            context_status = ProteinRegionContextStatus.UNMAPPED_TO_SEQUENCE
        elif matched_records:
            context_status = ProteinRegionContextStatus.CONTEXT_ANNOTATED
        else:
            context_status = ProteinRegionContextStatus.OUTSIDE_PROVIDED_ANNOTATIONS
        functional_regions = _functional_regions(
            matched_records,
            supporting_evidence_refs=(peptide_entry.peptide_sequence,),
        )
        entries.append(
            ProteinPeptideRegionContextEntry(
                peptide_key=peptide_entry.peptide_key,
                protein_ref=peptide_entry.protein_ref,
                peptide_sequence=peptide_entry.peptide_sequence,
                spans=spans,
                matched_context_record_count=len(matched_records),
                context_status=context_status,
                domain_names=_unique_sorted(
                    record.domain_name
                    for record in matched_records
                    if record.domain_name is not None
                ),
                signal_peptides=_unique_sorted(
                    record.signal_peptide
                    for record in matched_records
                    if record.signal_peptide is not None
                ),
                transmembrane_regions=_unique_sorted(
                    record.transmembrane_region
                    for record in matched_records
                    if record.transmembrane_region is not None
                ),
                disorder_regions=_unique_sorted(
                    record.disorder_region
                    for record in matched_records
                    if record.disorder_region is not None
                ),
                low_complexity_regions=_unique_sorted(
                    record.low_complexity_region
                    for record in matched_records
                    if record.low_complexity_region is not None
                ),
                active_site_labels=_unique_sorted(
                    record.active_site_label
                    for record in matched_records
                    if record.active_site_label is not None
                ),
                binding_regions=_unique_sorted(
                    record.binding_region
                    for record in matched_records
                    if record.binding_region is not None
                ),
                motif_names=_unique_sorted(
                    record.motif_name
                    for record in matched_records
                    if record.motif_name is not None
                ),
                conservation_scores=_conservation_scores(matched_records),
                max_conservation_score=_max_conservation_score(matched_records),
                source_names=_unique_sorted(
                    record.source_name
                    for record in matched_records
                    if record.source_name is not None
                ),
                source_accessions=_unique_sorted(
                    record.source_accession
                    for record in matched_records
                    if record.source_accession is not None
                ),
                functional_regions=functional_regions,
            )
        )

    stable_entries = tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.protein_ref,
                entry.peptide_sequence,
                entry.peptide_key,
            ),
        )
    )
    return ProteinPeptideRegionContextReport(
        entries=stable_entries,
        summary=ProteinPeptideRegionContextSummary(
            peptide_count=len(stable_entries),
            context_annotated_peptide_count=sum(
                1
                for entry in stable_entries
                if entry.context_status is ProteinRegionContextStatus.CONTEXT_ANNOTATED
            ),
            outside_annotation_peptide_count=sum(
                1
                for entry in stable_entries
                if entry.context_status
                is ProteinRegionContextStatus.OUTSIDE_PROVIDED_ANNOTATIONS
            ),
            unmapped_peptide_count=sum(
                1
                for entry in stable_entries
                if entry.context_status
                is ProteinRegionContextStatus.UNMAPPED_TO_SEQUENCE
            ),
            domain_annotated_peptide_count=sum(
                1 for entry in stable_entries if entry.domain_names
            ),
            signal_peptide_annotated_peptide_count=sum(
                1 for entry in stable_entries if entry.signal_peptides
            ),
            transmembrane_annotated_peptide_count=sum(
                1 for entry in stable_entries if entry.transmembrane_regions
            ),
            disorder_annotated_peptide_count=sum(
                1 for entry in stable_entries if entry.disorder_regions
            ),
            low_complexity_annotated_peptide_count=sum(
                1 for entry in stable_entries if entry.low_complexity_regions
            ),
            active_site_annotated_peptide_count=sum(
                1 for entry in stable_entries if entry.active_site_labels
            ),
            binding_region_annotated_peptide_count=sum(
                1 for entry in stable_entries if entry.binding_regions
            ),
            motif_annotated_peptide_count=sum(
                1 for entry in stable_entries if entry.motif_names
            ),
            conservation_annotated_peptide_count=sum(
                1 for entry in stable_entries if entry.conservation_scores
            ),
        ),
        note=(
            "protein peptide region context preserves peptide-to-region overlaps, "
            "marks peptides that do not map back to the provided sequence explicitly, "
            "and keeps the functional region labels linked to peptide evidence"
        ),
    )


def render_protein_region_context_summary_tsv(
    report: ProteinRegionContextImportReport,
) -> str:
    """Render one compact protein-region import summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("accepted_record_count", report.summary.accepted_record_count))
    writer.writerow(("rejected_row_count", report.summary.rejected_row_count))
    writer.writerow(
        ("distinct_protein_ref_count", report.summary.distinct_protein_ref_count)
    )
    writer.writerow(("domain_record_count", report.summary.domain_record_count))
    writer.writerow(
        ("signal_peptide_record_count", report.summary.signal_peptide_record_count)
    )
    writer.writerow(
        ("transmembrane_record_count", report.summary.transmembrane_record_count)
    )
    writer.writerow(("disorder_record_count", report.summary.disorder_record_count))
    writer.writerow(
        ("low_complexity_record_count", report.summary.low_complexity_record_count)
    )
    writer.writerow(
        ("active_site_record_count", report.summary.active_site_record_count)
    )
    writer.writerow(
        ("binding_region_record_count", report.summary.binding_region_record_count)
    )
    writer.writerow(("motif_record_count", report.summary.motif_record_count))
    writer.writerow(
        ("conservation_record_count", report.summary.conservation_record_count)
    )
    writer.writerow(("note", report.note))
    return buffer.getvalue()


def render_protein_site_region_context_tsv(
    report: ProteinSiteRegionContextReport,
) -> str:
    """Render site-level protein-region context rows as a TSV ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "site_key",
            "protein_ref",
            "position",
            "matched_context_record_count",
            "context_status",
            "domain_names",
            "signal_peptides",
            "transmembrane_regions",
            "disorder_regions",
            "low_complexity_regions",
            "active_site_labels",
            "binding_regions",
            "motif_names",
            "conservation_scores",
            "max_conservation_score",
            "functional_regions",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.site_key,
                entry.protein_ref,
                entry.position,
                entry.matched_context_record_count,
                entry.context_status.value,
                ";".join(entry.domain_names),
                ";".join(entry.signal_peptides),
                ";".join(entry.transmembrane_regions),
                ";".join(entry.disorder_regions),
                ";".join(entry.low_complexity_regions),
                ";".join(entry.active_site_labels),
                ";".join(entry.binding_regions),
                ";".join(entry.motif_names),
                ";".join(f"{score:g}" for score in entry.conservation_scores),
                (
                    ""
                    if entry.max_conservation_score is None
                    else f"{entry.max_conservation_score:g}"
                ),
                ";".join(
                    _functional_region_token(region)
                    for region in entry.functional_regions
                ),
            )
        )
    return buffer.getvalue()


def render_protein_peptide_region_context_tsv(
    report: ProteinPeptideRegionContextReport,
) -> str:
    """Render peptide-level protein-region context rows as a TSV ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "peptide_key",
            "protein_ref",
            "peptide_sequence",
            "spans",
            "matched_context_record_count",
            "context_status",
            "domain_names",
            "signal_peptides",
            "transmembrane_regions",
            "disorder_regions",
            "low_complexity_regions",
            "active_site_labels",
            "binding_regions",
            "motif_names",
            "conservation_scores",
            "max_conservation_score",
            "functional_regions",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.peptide_key,
                entry.protein_ref,
                entry.peptide_sequence,
                ";".join(f"{span.start}-{span.end}" for span in entry.spans),
                entry.matched_context_record_count,
                entry.context_status.value,
                ";".join(entry.domain_names),
                ";".join(entry.signal_peptides),
                ";".join(entry.transmembrane_regions),
                ";".join(entry.disorder_regions),
                ";".join(entry.low_complexity_regions),
                ";".join(entry.active_site_labels),
                ";".join(entry.binding_regions),
                ";".join(entry.motif_names),
                ";".join(f"{score:g}" for score in entry.conservation_scores),
                (
                    ""
                    if entry.max_conservation_score is None
                    else f"{entry.max_conservation_score:g}"
                ),
                ";".join(
                    _functional_region_token(region)
                    for region in entry.functional_regions
                ),
            )
        )
    return buffer.getvalue()


def _validate_required_columns(
    fieldnames: Sequence[str],
    mapping: ProteinRegionContextColumnMapping,
) -> None:
    required = (
        mapping.protein_ref,
        mapping.start,
        mapping.end,
    )
    for column in required:
        if column not in fieldnames:
            raise ValueError(
                f"missing required protein region context column {column!r}"
            )


def _row_issue(
    code: str,
    message: str,
    row_number: int,
) -> ProteinRegionContextValidationIssue:
    return ProteinRegionContextValidationIssue(
        code=code,
        message=message,
        row_number=row_number,
    )


def _row_value(raw_fields: dict[str, str], column: str | None) -> str | None:
    if column is None:
        return None
    value = raw_fields.get(column, "").strip()
    return value or None


def _conservation_scores(
    matched_records: tuple[ProteinRegionContextRecord, ...],
) -> tuple[float, ...]:
    return tuple(
        sorted(
            {
                round(record.conservation_score, 6)
                for record in matched_records
                if record.conservation_score is not None
            }
        )
    )


def _max_conservation_score(
    matched_records: tuple[ProteinRegionContextRecord, ...],
) -> float | None:
    scores = _conservation_scores(matched_records)
    return None if not scores else scores[-1]


def _find_peptide_spans(
    protein_sequence: str,
    peptide_sequence: str,
) -> tuple[ProteinPeptideSpan, ...]:
    if not protein_sequence or not peptide_sequence:
        return ()
    spans: list[ProteinPeptideSpan] = []
    offset = 0
    while True:
        position = protein_sequence.find(peptide_sequence, offset)
        if position < 0:
            break
        start = position + 1
        end = position + len(peptide_sequence)
        spans.append(ProteinPeptideSpan(start=start, end=end))
        offset = position + 1
    return tuple(spans)


def _spans_overlap(
    span: ProteinPeptideSpan,
    start: int,
    end: int,
) -> bool:
    return span.start <= end and start <= span.end


def _functional_regions(
    matched_records: tuple[ProteinRegionContextRecord, ...],
    *,
    supporting_evidence_refs: tuple[str, ...],
) -> tuple[ProteinFunctionalRegionEvidence, ...]:
    by_key: dict[
        tuple[ProteinFunctionalRegionKind, str, int, int, str | None, str | None],
        set[str],
    ] = {}
    for record in matched_records:
        for kind, label in _region_labels(record):
            key = (
                kind,
                label,
                record.start,
                record.end,
                record.source_name,
                record.source_accession,
            )
            by_key.setdefault(key, set()).update(
                ref for ref in supporting_evidence_refs if ref
            )
    return tuple(
        ProteinFunctionalRegionEvidence(
            region_kind=kind,
            label=label,
            start=start,
            end=end,
            source_name=source_name,
            source_accession=source_accession,
            supporting_evidence_refs=tuple(sorted(refs)),
        )
        for (kind, label, start, end, source_name, source_accession), refs in sorted(
            by_key.items(),
            key=lambda item: (
                item[0][0].value,
                item[0][2],
                item[0][3],
                item[0][1],
                item[0][4] or "",
                item[0][5] or "",
            ),
        )
    )


def _region_labels(
    record: ProteinRegionContextRecord,
) -> tuple[tuple[ProteinFunctionalRegionKind, str], ...]:
    labels: list[tuple[ProteinFunctionalRegionKind, str]] = []
    if record.domain_name is not None:
        labels.append((ProteinFunctionalRegionKind.DOMAIN, record.domain_name))
    if record.signal_peptide is not None:
        labels.append(
            (ProteinFunctionalRegionKind.SIGNAL_PEPTIDE, record.signal_peptide)
        )
    if record.transmembrane_region is not None:
        labels.append(
            (
                ProteinFunctionalRegionKind.TRANSMEMBRANE_REGION,
                record.transmembrane_region,
            )
        )
    if record.disorder_region is not None:
        labels.append(
            (ProteinFunctionalRegionKind.DISORDER_REGION, record.disorder_region)
        )
    if record.low_complexity_region is not None:
        labels.append(
            (
                ProteinFunctionalRegionKind.LOW_COMPLEXITY_REGION,
                record.low_complexity_region,
            )
        )
    if record.active_site_label is not None:
        labels.append(
            (ProteinFunctionalRegionKind.ACTIVE_SITE, record.active_site_label)
        )
    if record.binding_region is not None:
        labels.append(
            (ProteinFunctionalRegionKind.BINDING_REGION, record.binding_region)
        )
    if record.motif_name is not None:
        labels.append((ProteinFunctionalRegionKind.MOTIF, record.motif_name))
    return tuple(labels)


def _functional_region_token(region: ProteinFunctionalRegionEvidence) -> str:
    return f"{region.region_kind.value}:{region.label}@{region.start}-{region.end}"


def _unique_sorted(values: Iterable[str | None]) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if value}))


__all__ = [
    "build_protein_peptide_region_context_report",
    "build_protein_site_region_context_report",
    "parse_protein_region_context_tsv",
    "render_protein_peptide_region_context_tsv",
    "render_protein_region_context_summary_tsv",
    "render_protein_site_region_context_tsv",
]
