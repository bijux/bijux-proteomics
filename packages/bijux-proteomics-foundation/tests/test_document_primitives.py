# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_foundation import (
    ContractConflictError,
    ContractNotFoundError,
    ContractValidationError,
    DocumentSchema,
    FoundationContractError,
    IdentifierKind,
    JsonModel,
    MigrationExecutionError,
    MigrationPathError,
    MigrationRegistry,
    ProgramId,
    SchemaCompatibility,
    SchemaMigration,
    assess_schema_compatibility,
    build_identifier,
    classify_identifier,
    ensure_identifier_kind,
)
from pydantic import BaseModel, ConfigDict, Field, ValidationError
import pytest


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


def test_document_schema_supports_package_lineage_fields() -> None:
    schema = DocumentSchema(
        created_by="test",
        document_id="doc-1",
        document_kind="evidence_bundle",
        package_name="bijux-proteomics-knowledge",
        package_version="0.1.0",
    )

    assert schema.document_kind == "evidence_bundle"
    assert schema.package_name == "bijux-proteomics-knowledge"
    assert schema.status == "draft"


def test_document_schema_content_hash_is_deterministic() -> None:
    schema = DocumentSchema(created_by="test")
    payload: dict[str, object] = {"b": 2, "a": 1}

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
    schema_line = next(
        index for index, line in enumerate(lines) if '"document_schema"' in line
    )
    assert schema_line < value_line


def test_json_model_content_fingerprint_is_deterministic() -> None:
    left = DemoDocument(value="demo")
    right = DemoDocument.from_dict(
        {
            "value": "demo",
            "document_schema": left.document_schema.to_dict(),
        }
    )

    assert left.content_fingerprint() == right.content_fingerprint()


class IdentifierHolder(BaseModel):
    program_id: ProgramId


def test_typed_ids_enforce_non_empty_values() -> None:
    with pytest.raises(ValidationError):
        IdentifierHolder(program_id="  ")


def test_typed_ids_enforce_stable_identifier_pattern() -> None:
    IdentifierHolder(program_id="prog-1")

    with pytest.raises(ValidationError):
        IdentifierHolder(program_id="Program 1")


def test_identifier_helpers_classify_and_validate_prefix() -> None:
    assert classify_identifier("prog-1") is IdentifierKind.PROGRAM
    assert classify_identifier("unknown-1") is None

    ensure_identifier_kind("target-1", IdentifierKind.TARGET)

    with pytest.raises(ValueError, match="should use 'prog-' prefix"):
        ensure_identifier_kind("target-1", IdentifierKind.PROGRAM)


def test_build_identifier_creates_canonical_prefixed_ids() -> None:
    identifier = build_identifier(IdentifierKind.ASSAY, "Primary Readout")

    assert identifier == "assay-primary-readout"


def test_foundation_contract_errors_share_common_base() -> None:
    assert issubclass(ContractValidationError, FoundationContractError)
    assert issubclass(ContractNotFoundError, FoundationContractError)
    assert issubclass(ContractConflictError, FoundationContractError)


def test_assess_schema_compatibility_uses_major_minor_semantics() -> None:
    assert (
        assess_schema_compatibility("1.2.0", "1.1.0") is SchemaCompatibility.COMPATIBLE
    )
    assert (
        assess_schema_compatibility("1.0.0", "1.1.0")
        is SchemaCompatibility.FORWARD_INCOMPATIBLE
    )
    assert (
        assess_schema_compatibility("2.0.0", "1.9.0")
        is SchemaCompatibility.BACKWARD_INCOMPATIBLE
    )


def test_migration_registry_applies_sequential_steps() -> None:
    registry = MigrationRegistry()
    registry.register(
        SchemaMigration(
            from_version="1.0.0",
            to_version="1.1.0",
            description="add review cadence",
            migrate=lambda payload: {
                **payload,
                "document_schema": {
                    **payload["document_schema"],
                    "schema_version": "1.1.0",
                },
                "review_cadence": "weekly",
            },
        )
    )
    payload = {
        "document_schema": {"schema_version": "1.0.0"},
        "value": "demo",
    }

    migrated = registry.migrate_to(payload, "1.1.0")

    assert migrated["document_schema"]["schema_version"] == "1.1.0"
    assert migrated["review_cadence"] == "weekly"


def test_migration_registry_reports_registered_versions() -> None:
    registry = MigrationRegistry()
    registry.register(
        SchemaMigration(
            from_version="1.0.0",
            to_version="1.1.0",
            description="step one",
            migrate=lambda payload: payload,
        )
    )
    registry.register(
        SchemaMigration(
            from_version="1.1.0",
            to_version="1.2.0",
            description="step two",
            migrate=lambda payload: payload,
        )
    )

    assert registry.registered_versions() == ["1.0.0", "1.1.0", "1.2.0"]


def test_migration_registry_validates_missing_path_with_diagnostics() -> None:
    registry = MigrationRegistry()
    registry.register(
        SchemaMigration(
            from_version="1.0.0",
            to_version="1.1.0",
            description="step one",
            migrate=lambda payload: payload,
        )
    )

    with pytest.raises(MigrationPathError, match="known versions: 1.0.0, 1.1.0"):
        registry.validate_path("1.0.0", "1.2.0")


def test_migration_registry_detects_version_mismatch_in_step_output() -> None:
    registry = MigrationRegistry()
    registry.register(
        SchemaMigration(
            from_version="1.0.0",
            to_version="1.1.0",
            description="malformed step",
            migrate=lambda payload: {
                **payload,
                "document_schema": {
                    **payload["document_schema"],
                    "schema_version": "1.0.0",
                },
            },
        )
    )
    payload = {"document_schema": {"schema_version": "1.0.0"}}

    with pytest.raises(MigrationExecutionError, match="unexpected schema version"):
        registry.migrate_to(payload, "1.1.0")


def test_migration_registry_blocks_deprecated_target_versions() -> None:
    registry = MigrationRegistry()
    registry.mark_deprecated("1.0.0")

    assert registry.is_deprecated("1.0.0") is True

    with pytest.raises(MigrationPathError, match="is deprecated"):
        registry.migrate_to({"document_schema": {"schema_version": "0.9.0"}}, "1.0.0")
