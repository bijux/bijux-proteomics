# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError
import pytest

from bijux_proteomics_foundation import (
    ContractConflictError,
    ContractNotFoundError,
    ContractValidationError,
    DocumentSchema,
    DurationValue,
    ControlledVocabularyDomain,
    ExperimentId,
    FoundationContractError,
    StableHashPolicy,
    IdentifierKind,
    JsonModel,
    MigrationExecutionError,
    MigrationPathError,
    MigrationRegistry,
    NullabilityState,
    NullableValue,
    PeptideId,
    ProteinId,
    ProgramId,
    PromotionId,
    ReviewId,
    RunId,
    SchemaCompatibility,
    SchemaMigration,
    SequenceCoordinateRange,
    SequenceCoordinateSystem,
    SpectrumId,
    UtcTimestamp,
    absent_value,
    default_hash_policy,
    hash_model,
    hash_payload,
    normalize_controlled_term,
    present_value,
    assess_schema_compatibility,
    build_identifier,
    classify_identifier,
    ensure_identifier_kind,
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


class ScientificIdentifierHolder(BaseModel):
    protein_id: ProteinId
    peptide_id: PeptideId
    spectrum_id: SpectrumId
    experiment_id: ExperimentId
    run_id: RunId
    review_id: ReviewId
    promotion_id: PromotionId


def test_typed_ids_enforce_non_empty_values() -> None:
    with pytest.raises(ValidationError):
        IdentifierHolder(program_id="  ")


def test_typed_ids_enforce_stable_identifier_pattern() -> None:
    IdentifierHolder(program_id="prog-1")

    with pytest.raises(ValidationError):
        IdentifierHolder(program_id="Program 1")


def test_identifier_helpers_classify_and_validate_prefix() -> None:
    assert classify_identifier("prog-1") is IdentifierKind.PROGRAM
    assert classify_identifier("protein-p12345") is IdentifierKind.PROTEIN
    assert classify_identifier("claim-mechanism-1") is IdentifierKind.CLAIM
    assert classify_identifier("unknown-1") is None

    ensure_identifier_kind("target-1", IdentifierKind.TARGET)

    with pytest.raises(ValueError, match="should use 'prog-' prefix"):
        ensure_identifier_kind("target-1", IdentifierKind.PROGRAM)


def test_build_identifier_creates_canonical_prefixed_ids() -> None:
    identifier = build_identifier(IdentifierKind.ASSAY, "Primary Readout")

    assert identifier == "assay-primary-readout"


def test_scientific_identifier_aliases_accept_expected_prefixes() -> None:
    payload = ScientificIdentifierHolder(
        protein_id="protein-p12345",
        peptide_id="peptide-acdefghik-2",
        spectrum_id="spectrum-run-1-scan-22",
        experiment_id="experiment-dose-response",
        run_id="run-lcms-001",
        review_id="review-gate-binding",
        promotion_id="promotion-batch-1",
    )

    assert payload.protein_id == "protein-p12345"


def test_identifier_helpers_validate_new_scientific_kinds() -> None:
    ensure_identifier_kind("review-gate-binding", IdentifierKind.REVIEW)
    ensure_identifier_kind("promotion-batch-1", IdentifierKind.PROMOTION)

    with pytest.raises(ValueError, match="should use 'run-' prefix"):
        ensure_identifier_kind("experiment-dose-response", IdentifierKind.RUN)


def test_utc_timestamp_normalizes_to_utc() -> None:
    timestamp = UtcTimestamp(
        value=datetime.fromisoformat("2026-04-29T12:00:00+02:00")
    )

    assert timestamp.value.tzinfo is UTC
    assert timestamp.to_dict()["value"] == "2026-04-29T10:00:00Z"


def test_duration_value_round_trips_with_timedelta() -> None:
    duration = DurationValue.from_timedelta(timedelta(minutes=12, seconds=30))

    assert duration.seconds == 750.0
    assert duration.to_timedelta() == timedelta(minutes=12, seconds=30)


def test_sequence_coordinate_range_uses_inclusive_one_based_coordinates() -> None:
    interval = SequenceCoordinateRange(
        start=12,
        end=19,
        coordinate_system=SequenceCoordinateSystem.ONE_BASED_CLOSED,
    )

    assert interval.length == 8


def test_sequence_coordinate_range_rejects_inverted_intervals() -> None:
    with pytest.raises(ValidationError, match="end coordinate must be greater"):
        SequenceCoordinateRange(start=9, end=4)


def test_controlled_vocabulary_normalizes_known_aliases() -> None:
    enzyme = normalize_controlled_term(ControlledVocabularyDomain.ENZYME, "lys-c")
    assay = normalize_controlled_term(
        ControlledVocabularyDomain.ASSAY_TYPE, "engagement"
    )

    assert enzyme is not None
    assert enzyme.term_id == "enzyme:lysc"
    assert assay is not None
    assert assay.term_id == "assay:target_engagement"


def test_controlled_vocabulary_returns_none_for_unknown_term() -> None:
    assert (
        normalize_controlled_term(
            ControlledVocabularyDomain.INSTRUMENT, "homebrew-quadrupole"
        )
        is None
    )


def test_nullable_value_tracks_present_payloads_explicitly() -> None:
    payload = present_value(0.82)

    assert payload.state is NullabilityState.PRESENT
    assert payload.as_optional() == 0.82


def test_nullable_value_tracks_absent_states_without_payloads() -> None:
    payload = absent_value(
        NullabilityState.NOT_MEASURED,
        reason="instrument channel was disabled",
    )

    assert payload.value is None
    assert payload.reason == "instrument channel was disabled"


def test_nullable_value_rejects_inconsistent_state_and_payload_combinations() -> None:
    with pytest.raises(ValidationError, match="present values must carry"):
        NullableValue(state=NullabilityState.PRESENT, value=None)

    with pytest.raises(ValidationError, match="must not carry a payload"):
        NullableValue(state=NullabilityState.UNKNOWN, value=1.0)

    with pytest.raises(ValidationError, match="must include a reason"):
        NullableValue(state=NullabilityState.WITHHELD)


def test_hash_payload_uses_explicit_stable_policy() -> None:
    policy = default_hash_policy()
    digest = hash_payload({"b": 2, "a": 1}, policy=policy)

    assert policy.policy_id == "scientific-object-sha256-v1"
    assert digest == hash_payload({"a": 1, "b": 2}, policy=policy)


def test_hash_model_aligns_with_json_model_fingerprint() -> None:
    document = DemoDocument(value="demo")

    assert hash_model(document) == document.content_fingerprint()


def test_stable_hash_policy_is_serializable() -> None:
    policy = StableHashPolicy(policy_id="artifact-sha256-v1")

    assert policy.to_dict()["algorithm"] == "sha256"


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
