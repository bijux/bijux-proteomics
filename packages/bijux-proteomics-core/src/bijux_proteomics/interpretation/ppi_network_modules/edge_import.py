# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Delimited-edge import for governed PPI network-module reports."""

from __future__ import annotations

from collections.abc import Iterable
import csv
from pathlib import Path

from bijux_proteomics.sequences import canonicalize_protein_reference

from .models import (
    PpiEdgeColumnMapping,
    PpiEdgeImportReport,
    PpiEdgeImportSummary,
    PpiEdgeRecord,
    RejectedPpiEdgeRow,
)


def parse_ppi_edge_table(
    path: Path,
    *,
    mapping: PpiEdgeColumnMapping | None = None,
) -> PpiEdgeImportReport:
    """Parse one undirected PPI edge table into owned edge records."""

    lines = _read_delimited_lines(path)
    active_mapping = mapping or PpiEdgeColumnMapping(
        protein_ref_a="protein_ref_a",
        protein_ref_b="protein_ref_b",
        source_name="source_name",
        source_accession="source_accession",
        interaction_score="interaction_score",
    )
    if not lines:
        return PpiEdgeImportReport(
            source_path=str(path),
            total_rows=0,
            accepted_records=(),
            rejected_rows=(
                RejectedPpiEdgeRow(
                    row_number=2,
                    reason="ppi edge table is empty",
                ),
            ),
            column_mapping=active_mapping,
            summary=PpiEdgeImportSummary(
                accepted_record_count=0,
                rejected_row_count=1,
                distinct_protein_count=0,
                source_counts={},
            ),
            note="ppi edge table did not contain any readable rows",
        )

    reader = csv.DictReader(lines, delimiter=_infer_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("ppi edge table must include a header row")
    _validate_required_columns(
        reader.fieldnames,
        (active_mapping.protein_ref_a, active_mapping.protein_ref_b),
    )

    accepted_records: list[PpiEdgeRecord] = []
    rejected_rows: list[RejectedPpiEdgeRow] = []
    seen_edges: set[tuple[str, str]] = set()
    for row_number, raw_row in enumerate(reader, start=2):
        values = _normalize_row(raw_row)
        protein_token_a = values.get(active_mapping.protein_ref_a, "").strip()
        protein_token_b = values.get(active_mapping.protein_ref_b, "").strip()
        if not protein_token_a or not protein_token_b:
            rejected_rows.append(
                RejectedPpiEdgeRow(
                    row_number=row_number,
                    values=values,
                    reason="ppi edge row requires protein_ref_a and protein_ref_b",
                )
            )
            continue
        protein_ref_a = canonicalize_protein_reference(protein_token_a)
        protein_ref_b = canonicalize_protein_reference(protein_token_b)
        if protein_ref_a == protein_ref_b:
            rejected_rows.append(
                RejectedPpiEdgeRow(
                    row_number=row_number,
                    values=values,
                    reason="ppi edge row must connect two distinct proteins",
                )
            )
            continue
        edge_key = (
            (protein_ref_a, protein_ref_b)
            if protein_ref_a <= protein_ref_b
            else (protein_ref_b, protein_ref_a)
        )
        if edge_key in seen_edges:
            rejected_rows.append(
                RejectedPpiEdgeRow(
                    row_number=row_number,
                    values=values,
                    reason=(
                        "duplicate undirected ppi edge for "
                        f"{edge_key[0]} and {edge_key[1]}"
                    ),
                )
            )
            continue
        score_value = _optional_value(values, active_mapping.interaction_score)
        try:
            interaction_score = None if score_value is None else float(score_value)
        except ValueError:
            rejected_rows.append(
                RejectedPpiEdgeRow(
                    row_number=row_number,
                    values=values,
                    reason="ppi edge interaction_score must be numeric when supplied",
                )
            )
            continue
        seen_edges.add(edge_key)
        accepted_records.append(
            PpiEdgeRecord(
                protein_ref_a=edge_key[0],
                protein_ref_b=edge_key[1],
                source_name=_optional_value(values, active_mapping.source_name),
                source_accession=_optional_value(
                    values, active_mapping.source_accession
                ),
                interaction_score=interaction_score,
                metadata={
                    key: value
                    for key, value in values.items()
                    if key
                    not in {
                        active_mapping.protein_ref_a,
                        active_mapping.protein_ref_b,
                        active_mapping.source_name,
                        active_mapping.source_accession,
                        active_mapping.interaction_score,
                    }
                    and value
                },
            )
        )

    source_counts: dict[str, int] = {}
    for record in accepted_records:
        if record.source_name is not None:
            source_counts[record.source_name] = (
                source_counts.get(record.source_name, 0) + 1
            )

    return PpiEdgeImportReport(
        source_path=str(path),
        total_rows=max(len(lines) - 1, 0),
        accepted_records=tuple(accepted_records),
        rejected_rows=tuple(rejected_rows),
        column_mapping=active_mapping,
        summary=PpiEdgeImportSummary(
            accepted_record_count=len(accepted_records),
            rejected_row_count=len(rejected_rows),
            distinct_protein_count=len(
                {
                    protein_ref
                    for record in accepted_records
                    for protein_ref in (record.protein_ref_a, record.protein_ref_b)
                }
            ),
            source_counts=dict(sorted(source_counts.items())),
        ),
        note=(
            "ppi edge import preserves undirected interaction support, rejects duplicate or self edges, "
            "and keeps explicit provenance over retained interactions"
        ),
    )


def _infer_delimiter(header_line: str) -> str:
    return "\t" if "\t" in header_line else ","


def _normalize_row(raw_row: dict[str | None, str | None]) -> dict[str, str]:
    return {
        (key or "").strip(): (value or "").strip()
        for key, value in raw_row.items()
        if key is not None
    }


def _optional_value(row: dict[str, str], field_name: str | None) -> str | None:
    if field_name is None:
        return None
    value = row.get(field_name, "").strip()
    return value or None


def _read_delimited_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _validate_required_columns(
    fieldnames: Iterable[str],
    required_columns: tuple[str, ...],
) -> None:
    available = {field.strip() for field in fieldnames}
    missing = [column for column in required_columns if column not in available]
    if missing:
        raise ValueError("missing required columns: " + ", ".join(sorted(missing)))


__all__ = ["parse_ppi_edge_table"]
