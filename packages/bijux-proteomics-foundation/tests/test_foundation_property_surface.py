# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
import string

from hypothesis import given
from hypothesis import strategies as st
from pydantic import ConfigDict, Field, ValidationError
import pytest

from bijux_proteomics_foundation import (
    JsonModel,
    fingerprint_model,
    hash_payload,
    to_canonical_json,
)
from bijux_proteomics_foundation.error_models import (
    ErrorCategory,
    build_error_envelope_from_exception,
    summarize_exception_chain,
)
from bijux_proteomics_foundation.ids import (
    IdentifierKind,
    build_identifier,
    ensure_identifier_kind,
)
from bijux_proteomics_foundation.ordering import stable_order_value
from bijux_proteomics_foundation.provenance import (
    ProvenancePointer,
    ProvenancePointerKind,
)
from bijux_proteomics_foundation.refusals import OperationRefusal, RefusalKind
from bijux_proteomics_foundation.results import (
    OperationDisposition,
    OperationResult,
)
from bijux_proteomics_foundation.states import SupportState


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
IDENTIFIER_SUFFIX_STRATEGY = st.lists(
    st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=8),
    min_size=1,
    max_size=4,
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


@given(kind=st.sampled_from(tuple(IdentifierKind)), parts=IDENTIFIER_SUFFIX_STRATEGY)
def test_identifier_building_normalizes_suffixes_and_preserves_kind(
    kind: IdentifierKind, parts: list[str]
) -> None:
    identifier = build_identifier(kind, " ".join(parts))

    ensure_identifier_kind(identifier, kind)
    assert identifier == identifier.lower()
    assert " " not in identifier


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


def test_shared_operation_result_distinguishes_success_refusal_and_degraded_success() -> (
    None
):
    pointer = ProvenancePointer(
        pointer_kind=ProvenancePointerKind.ARTIFACT,
        locator="artifacts/foundation/result.json",
        pointer_role="result_artifact",
    )
    refusal = OperationRefusal(
        operation="mzml_ingestion",
        kind=RefusalKind.UNSUPPORTED,
        code="unsupported construct",
        reason="the construct cannot be normalized honestly",
    )

    success = OperationResult.success(
        operation="hash_manifest",
        summary="hash computed successfully",
        provenance=(pointer,),
        output_fingerprint="a" * 64,
    )
    refused = OperationResult.refused(
        operation="mzml_ingestion",
        summary="normalization was refused",
        refusal=refusal,
    )
    degraded = OperationResult.degraded_success(
        operation="mztab_ingestion",
        summary="payload normalized with explicit loss reporting",
        state=SupportState.LOSSY,
        degradation_reasons=("native field loss", "vendor score omitted"),
        output_fingerprint="b" * 64,
    )

    assert success.disposition is OperationDisposition.SUCCESS
    assert refused.disposition is OperationDisposition.REFUSED
    assert degraded.disposition is OperationDisposition.DEGRADED_SUCCESS


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


def test_refusal_serialization_preserves_normalized_reason_codes() -> None:
    refusal = OperationRefusal(
        operation="search_ingestion",
        kind=RefusalKind.AMBIGUOUS,
        code="Engine Timeout",
        reason="the source export stopped before peptide-level evidence finished",
        reason_details=("run log truncated", "peptide section missing"),
    )

    restored = OperationRefusal.model_validate_json(refusal.model_dump_json())

    assert restored.code == "engine_timeout"
    assert restored.reason == refusal.reason


def test_error_envelopes_preserve_nested_exception_context_predictably() -> None:
    try:
        try:
            raise ValueError("missing scan id")
        except ValueError as error:
            raise RuntimeError("mzml normalization failed") from error
    except RuntimeError as error:
        envelope = build_error_envelope_from_exception(
            category=ErrorCategory.RUNTIME,
            code="Normalization Failure",
            error=error,
            context={"run_id": "run-22", "step_id": "ingest"},
        )
        chain = summarize_exception_chain(error)

    assert chain == (
        "RuntimeError: mzml normalization failed",
        "ValueError: missing scan id",
    )
    assert envelope.code == "normalization_failure"
    assert envelope.context == (("run_id", "run-22"), ("step_id", "ingest"))
    assert envelope.cause_chain == chain


def test_operation_result_rejects_inconsistent_disposition_state_combinations() -> None:
    with pytest.raises(ValidationError, match="must carry one refusal"):
        OperationResult(
            operation="ingest",
            disposition=OperationDisposition.REFUSED,
            support_state=SupportState.REFUSED,
            summary="ingestion refused",
        )
