# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from bijux_proteomics_foundation import DocumentSchema, JsonModel, ProgramId


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


def test_document_schema_touch_updates_audit_metadata() -> None:
    schema = DocumentSchema(
        created_by="test",
        trace_id="trace-1",
        tags=["initial"],
    )

    touched = schema.touch("curator", tag="reviewed")

    assert touched.updated_by == "curator"
    assert touched.parent_trace_id is None
    assert touched.tags == ["initial", "reviewed"]
    assert touched.updated_at >= touched.created_at


class IdentifierHolder(BaseModel):
    program_id: ProgramId


def test_typed_ids_enforce_non_empty_values() -> None:
    with pytest.raises(ValidationError):
        IdentifierHolder(program_id="  ")
