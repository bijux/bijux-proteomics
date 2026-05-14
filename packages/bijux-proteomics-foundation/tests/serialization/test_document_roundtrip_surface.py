# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import DocumentSchema, JsonModel
from bijux_proteomics_foundation.serialization.scientific_values import (
    DurationValue,
    NullabilityState,
    NullableValue,
    SequenceCoordinateRange,
    UtcTimestamp,
)


class FoundationSurfaceDocument(JsonModel):
    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema = Field(
        default_factory=lambda: DocumentSchema(created_by="bijux-proteomics-foundation")
    )
    observed_at: UtcTimestamp
    retention_window: DurationValue
    peptide_span: SequenceCoordinateRange
    phosphorylation: str = Field(..., min_length=1)
    occupancy: NullableValue


def test_foundation_surface_round_trips_across_json_jsonl_and_tsv(
    tmp_path: Path,
) -> None:
    document = FoundationSurfaceDocument(
        observed_at=UtcTimestamp(value=datetime(2026, 4, 29, 10, 30, tzinfo=UTC)),
        retention_window=DurationValue(seconds=37.5),
        peptide_span=SequenceCoordinateRange(start=14, end=22),
        phosphorylation="mod:phospho",
        occupancy=NullableValue(
            presence=NullabilityState.NOT_MEASURED,
            absence_reason="site occupancy standard was not run",
        ),
    )

    json_path = tmp_path / "foundation-surface.json"
    jsonl_path = tmp_path / "foundation-surface.jsonl"
    tsv_path = tmp_path / "foundation-surface.tsv"

    document.save_json(json_path)
    document.save_jsonl(jsonl_path)
    document.save_tsv(tsv_path)

    restored = FoundationSurfaceDocument.load_json(json_path)
    tsv_lines = tsv_path.read_text().splitlines()

    assert restored == document
    assert restored.occupancy.absence_reason == "site occupancy standard was not run"
    assert jsonl_path.read_text().count("\n") == 1
    assert "phosphorylation" not in tsv_lines[1]
    assert "mod:phospho" in tsv_lines[1]
