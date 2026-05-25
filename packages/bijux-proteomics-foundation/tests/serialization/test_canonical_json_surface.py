# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
import string
from typing import cast

import pytest

pytest.importorskip("hypothesis")
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import (
    DocumentSchema,
    JsonModel,
    fingerprint_model,
    hash_payload,
    to_canonical_json,
)
from bijux_proteomics_foundation.compatibility import (
    SchemaCompatibility,
    assess_schema_compatibility,
)
from bijux_proteomics_foundation.serialization.canonical_json import (
    normalize_json_value,
)
from bijux_proteomics_foundation.serialization.fingerprints import (
    FingerprintScope,
    build_artifact_bundle_fingerprint,
    build_benchmark_manifest_fingerprint,
    build_dataset_fingerprint,
    build_parameter_set_fingerprint,
    build_run_context_fingerprint,
)
from bijux_proteomics_foundation.serialization.stable_values import stable_order_value

JSON_SCALAR_STRATEGY = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-10_000, max_value=10_000),
    st.text(alphabet=string.ascii_letters + string.digits + "-_", max_size=12),
)
JSON_VALUE_STRATEGY = st.recursive(
    JSON_SCALAR_STRATEGY,
    lambda children: st.one_of(
        st.lists(children, max_size=4),
        st.dictionaries(
            st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=8),
            children,
            max_size=4,
        ),
    ),
    max_leaves=10,
)
JSON_OBJECT_STRATEGY = st.dictionaries(
    st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=8),
    JSON_VALUE_STRATEGY,
    max_size=5,
)


class SerializationSurfaceJsonModel(JsonModel):
    model_config = ConfigDict(extra="forbid")

    document_schema: dict[str, str] = Field(
        default_factory=lambda: {
            "created_by": "bijux-proteomics-foundation",
            "schema_version": "1.0.0",
        }
    )
    name: str
    values: list[int]
    attributes: dict[str, str]


def _structurally_equivalent_value(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _structurally_equivalent_value(inner)
            for key, inner in reversed(tuple(value.items()))
        }
    if isinstance(value, list):
        return tuple(_structurally_equivalent_value(item) for item in value)
    return value


def test_fingerprint_records_cover_dataset_parameter_run_benchmark_and_bundle_scopes() -> (
    None
):
    payload = {"name": "alpha", "replicates": [2, 1]}

    records = (
        build_dataset_fingerprint(payload, subject_id="dataset-a"),
        build_parameter_set_fingerprint(payload, subject_id="params-a"),
        build_run_context_fingerprint(payload, subject_id="runctx-a"),
        build_benchmark_manifest_fingerprint(payload, subject_id="bench-a"),
        build_artifact_bundle_fingerprint(payload, subject_id="bundle-a"),
    )

    assert tuple(record.scope for record in records) == (
        FingerprintScope.DATASET,
        FingerprintScope.PARAMETER_SET,
        FingerprintScope.RUN_CONTEXT,
        FingerprintScope.BENCHMARK_MANIFEST,
        FingerprintScope.ARTIFACT_BUNDLE,
    )
    assert all(
        record.hash_policy_id == "scientific-object-sha256-v1" for record in records
    )


def test_document_schema_uses_normalized_additive_versions() -> None:
    schema = DocumentSchema(
        created_by="bijux-proteomics-foundation", schema_version="01.002.003"
    )

    assert schema.schema_version == "1.2.3"
    assert (
        assess_schema_compatibility("1.4.0", "1.2.0") is SchemaCompatibility.COMPATIBLE
    )
    assert (
        assess_schema_compatibility("1.1.9", "1.2.0")
        is SchemaCompatibility.FORWARD_INCOMPATIBLE
    )


def test_canonical_json_orders_nested_values_and_sets() -> None:
    payload = {
        "b": {"y": 2, "x": 1},
        "a": [{"z": 2, "y": 1}],
        "tags": {"gamma", "alpha"},
    }

    rendered = to_canonical_json(payload)

    assert rendered == (
        '{"a":[{"y":1,"z":2}],"b":{"x":1,"y":2},"tags":["alpha","gamma"]}'
    )


@given(payload=JSON_OBJECT_STRATEGY)
def test_hashing_and_ordering_are_deterministic_for_equivalent_payloads(
    payload: dict[str, object],
) -> None:
    reordered = {
        key: stable_order_value(value)
        for key, value in reversed(tuple(payload.items()))
    }

    assert stable_order_value(payload) == stable_order_value(reordered)
    assert hash_payload(payload) == hash_payload(reordered)


@given(payload=JSON_OBJECT_STRATEGY)
def test_hashing_is_stable_under_recursive_ordering_noise(
    payload: dict[str, object],
) -> None:
    equivalent = cast(dict[str, object], _structurally_equivalent_value(payload))

    assert hash_payload(payload) == hash_payload(equivalent)


@given(payload=JSON_OBJECT_STRATEGY)
def test_canonical_json_is_stable_for_structurally_equivalent_payloads(
    payload: dict[str, object],
) -> None:
    equivalent = cast(dict[str, object], _structurally_equivalent_value(payload))

    assert normalize_json_value(payload) == normalize_json_value(equivalent)
    assert to_canonical_json(payload) == to_canonical_json(equivalent)


def test_serialization_helpers_cover_json_jsonl_tsv_and_canonical_round_trip(
    tmp_path: Path,
) -> None:
    document = SerializationSurfaceJsonModel(
        name="foundation",
        values=[3, 1, 2],
        attributes={"lane": "A", "instrument": "orbitrap"},
    )

    json_path = tmp_path / "surface.json"
    stable_json_path = tmp_path / "surface.stable.json"
    jsonl_path = tmp_path / "surface.jsonl"
    tsv_path = tmp_path / "surface.tsv"

    document.save_json(json_path)
    document.save_stable_json(stable_json_path)
    document.save_jsonl(jsonl_path)
    document.save_tsv(tsv_path)

    assert SerializationSurfaceJsonModel.from_dict(document.to_dict()) == document
    assert SerializationSurfaceJsonModel.from_json(document.to_json()) == document
    assert SerializationSurfaceJsonModel.load_json(json_path) == document
    assert json.loads(document.to_jsonl_line()) == document.to_dict()
    assert json.loads(to_canonical_json(document)) == document.to_dict()
    assert fingerprint_model(document) == document.content_fingerprint()

    header, row = document.to_tsv_row()
    tsv_lines = tsv_path.read_text().splitlines()
    assert tsv_lines == [header, row]
    assert sorted(document.to_flat_dict()) == header.split("\t")
    assert stable_json_path.read_text().startswith("{\n")
