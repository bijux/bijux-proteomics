# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from bijux_proteomics_foundation import (
    SchemaCompatibility,
    ContractConflictError,
    ContractNotFoundError,
    ContractValidationError,
    DocumentSchema,
    FoundationContractError,
    JsonModel,
    ProgramId,
    assess_schema_compatibility,
)


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
    assert touched.revision == 2
    assert touched.updated_at >= touched.created_at


def test_document_schema_content_hash_is_deterministic() -> None:
    schema = DocumentSchema(created_by="test")
    payload = {"b": 2, "a": 1}

    hashed_once = schema.with_content_hash(payload)
    hashed_twice = schema.with_content_hash({"a": 1, "b": 2})

    assert hashed_once.content_hash is not None
    assert hashed_once.content_hash == hashed_twice.content_hash


def test_stable_json_is_sorted_for_reproducible_diffs(tmp_path: Path) -> None:
    document = DemoDocument(value="demo")
    path = tmp_path / "stable.json"

    document.save_stable_json(path)
    lines = path.read_text().splitlines()

    value_line = next(index for index, line in enumerate(lines) if '"value"' in line)
    schema_line = next(index for index, line in enumerate(lines) if '"document_schema"' in line)
    assert schema_line < value_line


class IdentifierHolder(BaseModel):
    program_id: ProgramId


def test_typed_ids_enforce_non_empty_values() -> None:
    with pytest.raises(ValidationError):
        IdentifierHolder(program_id="  ")


def test_typed_ids_enforce_stable_identifier_pattern() -> None:
    IdentifierHolder(program_id="prog-1")

    with pytest.raises(ValidationError):
        IdentifierHolder(program_id="Program 1")


def test_foundation_contract_errors_share_common_base() -> None:
    assert issubclass(ContractValidationError, FoundationContractError)
    assert issubclass(ContractNotFoundError, FoundationContractError)
    assert issubclass(ContractConflictError, FoundationContractError)


def test_assess_schema_compatibility_uses_major_minor_semantics() -> None:
    assert assess_schema_compatibility("1.2.0", "1.1.0") is SchemaCompatibility.COMPATIBLE
    assert assess_schema_compatibility("1.0.0", "1.1.0") is SchemaCompatibility.FORWARD_INCOMPATIBLE
    assert assess_schema_compatibility("2.0.0", "1.9.0") is SchemaCompatibility.BACKWARD_INCOMPATIBLE
