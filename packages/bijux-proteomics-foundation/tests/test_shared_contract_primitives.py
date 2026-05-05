# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pydantic import BaseModel, ValidationError
import pytest

from bijux_proteomics_foundation import (
    DocumentSchema,
    IdentifierKind,
    SchemaCompatibility,
    assess_schema_compatibility,
    to_canonical_json,
)
from bijux_proteomics_foundation.error_models import ErrorCategory, ErrorEnvelope
from bijux_proteomics_foundation.fingerprints import (
    FingerprintScope,
    build_artifact_bundle_fingerprint,
    build_benchmark_manifest_fingerprint,
    build_dataset_fingerprint,
    build_parameter_set_fingerprint,
    build_run_context_fingerprint,
)
from bijux_proteomics_foundation.ids import (
    LabActionId,
    PtmId,
    ReviewPacketId,
    StudyId,
    build_identifier,
)
from bijux_proteomics_foundation.provenance import (
    ProvenancePointer,
    ProvenancePointerKind,
)
from bijux_proteomics_foundation.refusals import OperationRefusal, RefusalKind
from bijux_proteomics_foundation.states import SupportState


class IdentifierSurface(BaseModel):
    study_id: StudyId
    ptm_id: PtmId
    review_packet_id: ReviewPacketId
    lab_action_id: LabActionId


def test_identifier_surface_covers_foundation_owned_scientific_entities() -> None:
    surface = IdentifierSurface(
        study_id=build_identifier(IdentifierKind.STUDY, "Study-01"),
        ptm_id=build_identifier(IdentifierKind.PTM, "Phospho-S123"),
        review_packet_id=build_identifier(IdentifierKind.REVIEW_PACKET, "Panel-A"),
        lab_action_id=build_identifier(IdentifierKind.LAB_ACTION, "Queue-Transfer"),
    )

    assert surface.study_id == "study-study-01"
    assert surface.ptm_id == "ptm-phospho-s123"
    assert surface.review_packet_id == "reviewpkt-panel-a"
    assert surface.lab_action_id == "labact-queue-transfer"

    with pytest.raises(ValidationError):
        IdentifierSurface(
            study_id="bad id",
            ptm_id="ptm-ok",
            review_packet_id="reviewpkt-ok",
            lab_action_id="labact-ok",
        )


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


def test_support_state_refusal_and_error_models_serialize_deterministically() -> None:
    pointer = ProvenancePointer(
        pointer_kind=ProvenancePointerKind.ARTIFACT,
        locator="artifacts/review/run-7.json",
        role="review_artifact",
        labels=("review", "canonical"),
    )
    refusal = OperationRefusal(
        operation="mzidentml_ingestion",
        kind=RefusalKind.UNSUPPORTED,
        code="Engine Timeout",
        reason="the engine output is incomplete",
        state=SupportState.INCOMPLETE,
        details=("missing peptide evidence", "engine timeout"),
        recommended_actions=("retry with full export", "collect complete run log"),
        provenance=(pointer,),
    )
    envelope = ErrorEnvelope(
        category=ErrorCategory.RUNTIME,
        code="Engine Timeout",
        message="external engine did not complete before timeout",
        context={"step_id": "search", "run_id": "run-77"},
        cause_chain=("timeout", "adapter"),
        provenance=(pointer,),
    )

    assert refusal.code == "engine_timeout"
    assert refusal.state is SupportState.INCOMPLETE
    assert envelope.code == "engine_timeout"
    assert envelope.context[0] == ("run_id", "run-77")
    assert envelope.cause_chain == ("timeout", "adapter")
    assert to_canonical_json(envelope).count("engine_timeout") == 1


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
