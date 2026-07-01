# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Site-regulation input parsing and PTM signal projection."""

from __future__ import annotations

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
    RegulatorSiteSignalColumnMapping,
    RegulatorSiteSignalEntry,
    RegulatorSiteSignalImportReport,
    RegulatorSiteSignalImportSummary,
    RejectedRegulatorSiteSignalRow,
)
from bijux_proteomics.ptm import PtmEvidenceCardReport


def parse_regulator_site_signal_table(
    path: Path,
    *,
    mapping: RegulatorSiteSignalColumnMapping | None = None,
) -> RegulatorSiteSignalImportReport:
    """Parse one explicit site differential table for regulator inference."""

    lines = read_delimited_lines(path)
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

    reader = csv.DictReader(lines, delimiter=infer_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("regulator site signal table must include a header row")
    validate_required_columns(
        reader.fieldnames,
        (active_mapping.site_key, active_mapping.log2_fold_change),
    )

    accepted_entries: list[RegulatorSiteSignalEntry] = []
    rejected_rows: list[RejectedRegulatorSiteSignalRow] = []
    seen_site_keys: set[str] = set()
    for row_number, raw_row in enumerate(reader, start=2):
        values = normalize_row(raw_row)
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
            log2_fold_change = float(
                values.get(active_mapping.log2_fold_change, "").strip()
            )
        except ValueError:
            rejected_rows.append(
                RejectedRegulatorSiteSignalRow(
                    row_number=row_number,
                    values=values,
                    reason="regulator site signal log2_fold_change must be numeric",
                )
            )
            continue
        adjusted_p_value = optional_value(values, active_mapping.adjusted_p_value)
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
                protein_ref=optional_value(values, active_mapping.protein_ref),
                log2_fold_change=log2_fold_change,
                adjusted_p_value=adjusted_value,
            )
        )

    accepted_tuple = tuple(
        sorted(
            accepted_entries,
            key=lambda entry: (entry.site_key, entry.protein_ref or ""),
        )
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
        for card in sorted(
            report.cards, key=lambda card: (card.protein_ref, card.site_key)
        )
    )


__all__ = [
    "build_regulator_site_signal_entries_from_ptm_evidence_cards",
    "parse_regulator_site_signal_table",
]
