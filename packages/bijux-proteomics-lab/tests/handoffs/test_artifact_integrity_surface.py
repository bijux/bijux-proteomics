# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation import DocumentSchema
from bijux_proteomics_lab.handoffs.artifacts import (
    default_lab_artifact_profile,
    evaluate_lab_artifact_with_registry,
)
from bijux_proteomics_lab.handoffs.serialization import (
    build_canonical_artifact_envelope,
    verify_canonical_artifact_envelope,
)


def test_lab_artifact_integrity_envelope_detects_payload_tampering() -> None:
    envelope = build_canonical_artifact_envelope(
        default_lab_artifact_profile(),
        artifact_kind="plan",
        schema=DocumentSchema(created_by="bijux-proteomics-lab"),
    )

    assert verify_canonical_artifact_envelope(envelope) is True

    envelope.payload_raw_json["state"] = "tampered"

    assert verify_canonical_artifact_envelope(envelope) is False


def test_lab_artifact_integrity_registry_keeps_reviewable_contracts_visible() -> None:
    report = evaluate_lab_artifact_with_registry(
        DocumentSchema(schema_version="1.0.0", created_by="bijux-proteomics-lab"),
        artifact_kind="feedback",
    )

    assert report.compatible is True
    assert any("artifact schema contract is satisfied" in note for note in report.notes)
