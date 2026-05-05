# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import ConfigDict, Field, ValidationError
import pytest

from bijux_proteomics_foundation import (
    DocumentSchema,
    JsonModel,
    hash_model,
    hash_payload,
)
from bijux_proteomics_foundation.serialization.documents import (
    DurationValue,
    NullabilityState,
    NullableValue,
    SequenceCoordinateRange,
    SequenceCoordinateSystem,
    UtcTimestamp,
    absent_value,
    present_value,
)
from bijux_proteomics_foundation.serialization.hashing import (
    StableHashPolicy,
    default_hash_policy,
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


def test_utc_timestamp_normalizes_to_utc() -> None:
    timestamp = UtcTimestamp(value=datetime.fromisoformat("2026-04-29T12:00:00+02:00"))

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


def test_nullable_value_tracks_present_payloads_explicitly() -> None:
    payload = present_value(0.82)

    assert payload.presence is NullabilityState.PRESENT
    assert payload.as_optional() == 0.82


def test_nullable_value_tracks_absent_states_without_payloads() -> None:
    payload = absent_value(
        NullabilityState.NOT_MEASURED,
        absence_reason="instrument channel was disabled",
    )

    assert payload.value is None
    assert payload.absence_reason == "instrument channel was disabled"


def test_nullable_value_rejects_inconsistent_state_and_payload_combinations() -> None:
    with pytest.raises(ValidationError, match="present values must carry"):
        NullableValue(presence=NullabilityState.PRESENT, value=None)

    with pytest.raises(ValidationError, match="must not carry a payload"):
        NullableValue(presence=NullabilityState.UNKNOWN, value=1.0)

    with pytest.raises(ValidationError, match="must include a reason"):
        NullableValue(presence=NullabilityState.WITHHELD)


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


def test_json_model_supports_jsonl_and_tsv_transport_helpers(tmp_path: Path) -> None:
    document = DemoDocument(value="demo")
    jsonl_path = tmp_path / "document.jsonl"
    tsv_path = tmp_path / "document.tsv"

    document.save_jsonl(jsonl_path)
    document.save_tsv(tsv_path)

    assert jsonl_path.read_text().endswith("\n")
    header, row = document.to_tsv_row()
    assert "value" in header
    assert "demo" in row
    assert tsv_path.read_text().splitlines()[0] == header

