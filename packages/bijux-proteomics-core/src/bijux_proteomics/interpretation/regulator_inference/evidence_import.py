# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Explicit regulator-to-target evidence table parsing."""

from __future__ import annotations

from collections import defaultdict
import csv
from pathlib import Path

from bijux_proteomics.interpretation.regulator_inference._table_io import (
    infer_delimiter,
    normalize_row,
    optional_value,
    read_delimited_lines,
    validate_required_columns,
)
from bijux_proteomics.interpretation.regulator_inference.models import (
    RegulatorEvidenceColumnMapping,
    RegulatorEvidenceImportReport,
    RegulatorEvidenceImportSummary,
    RegulatorEvidenceRecord,
    RegulatorEvidenceTargetField,
    RegulatorEvidenceType,
    RejectedRegulatorEvidenceRow,
)
from bijux_proteomics.sequences import canonicalize_protein_reference


def parse_regulator_evidence_table(
    path: Path,
    *,
    mapping: RegulatorEvidenceColumnMapping | None = None,
) -> RegulatorEvidenceImportReport:
    """Parse one explicit regulator evidence table into owned rows."""

    lines = read_delimited_lines(path)
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

    reader = csv.DictReader(lines, delimiter=infer_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("regulator evidence table must include a header row")
    validate_required_columns(
        reader.fieldnames,
        (active_mapping.regulator, active_mapping.evidence_type),
    )

    accepted_records: list[RegulatorEvidenceRecord] = []
    rejected_rows: list[RejectedRegulatorEvidenceRow] = []
    for row_number, raw_row in enumerate(reader, start=2):
        values = normalize_row(raw_row)
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
        protein_ref = optional_value(values, active_mapping.protein_ref)
        if protein_ref is not None:
            protein_ref = canonicalize_protein_reference(protein_ref)
        gene_symbol = optional_value(values, active_mapping.gene_symbol)
        pathway_id = optional_value(values, active_mapping.pathway_id)
        site_key = optional_value(values, active_mapping.site_key)
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
                source_name=optional_value(values, active_mapping.source_name),
                source_accession=optional_value(
                    values, active_mapping.source_accession
                ),
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
    counts: defaultdict[RegulatorEvidenceType, int] = defaultdict(int)
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
            kinase_substrate_record_count=counts[
                RegulatorEvidenceType.KINASE_SUBSTRATE
            ],
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


__all__ = ["parse_regulator_evidence_table"]
