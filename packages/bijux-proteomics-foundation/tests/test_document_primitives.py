# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import DocumentSchema, JsonModel


class DemoDocument(JsonModel):
    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema = Field(
        default_factory=lambda: DocumentSchema(created_by="demo"),
    )
    value: str = Field(..., min_length=1)


def test_document_primitives_round_trip(tmp_path: Path) -> None:
    document = DemoDocument(value="demo")
    document.document_schema.trace_id = "trace-foundation-1"
    path = tmp_path / "document.json"

    document.save_json(path)
    restored = DemoDocument.load_json(path)

    assert restored.to_dict()["document_schema"]["trace_id"] == "trace-foundation-1"
