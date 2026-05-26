# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation import DocumentSchema
from bijux_proteomics_foundation import (
    fingerprint_model as foundation_fingerprint_model,
)
from bijux_proteomics_foundation import (
    to_canonical_json as foundation_to_canonical_json,
)
from bijux_proteomics_lab.handoffs.serialization import (
    build_canonical_artifact_envelope,
    diff_model_payloads,
    verify_canonical_artifact_envelope,
)
from bijux_proteomics_lab.planning.assays import ExperimentPlan


def test_lab_canonical_serialization_and_fingerprint_are_stable() -> None:
    plan = ExperimentPlan(program_id="prog-ser")
    canonical = foundation_to_canonical_json(plan)
    digest_a = foundation_fingerprint_model(plan)
    digest_b = foundation_fingerprint_model(plan)

    assert canonical.startswith("{")
    assert digest_a == digest_b


def test_lab_root_does_not_reexport_foundation_helpers() -> None:
    import bijux_proteomics_lab

    assert "to_canonical_json" not in bijux_proteomics_lab.__all__
    assert "fingerprint_model" not in bijux_proteomics_lab.__all__


def test_diff_model_payloads_reports_changed_fields() -> None:
    left = ExperimentPlan(program_id="prog-ser", evidence_gaps=["structure"])
    right = ExperimentPlan(
        program_id="prog-ser", evidence_gaps=["structure", "cellular"]
    )

    diff = diff_model_payloads(left, right)

    assert diff.added_fields == ()
    assert diff.removed_fields == ()
    assert diff.changed_fields == ("evidence_gaps",)


def test_build_canonical_artifact_envelope_includes_schema_and_fingerprint() -> None:
    plan = ExperimentPlan(program_id="prog-env")
    envelope = build_canonical_artifact_envelope(
        plan,
        artifact_kind="plan",
        schema=DocumentSchema(created_by="bijux-proteomics-lab"),
    )

    assert envelope.artifact_kind == "plan"
    assert envelope.fingerprint
    assert envelope.schema_metadata.created_by == "bijux-proteomics-lab"


def test_verify_canonical_artifact_envelope_detects_tampering() -> None:
    plan = ExperimentPlan(program_id="prog-env")
    envelope = build_canonical_artifact_envelope(
        plan,
        artifact_kind="plan",
        schema=DocumentSchema(created_by="bijux-proteomics-lab"),
    )
    assert verify_canonical_artifact_envelope(envelope) is True
    envelope.payload_raw_json = {"program_id": "tampered"}
    assert verify_canonical_artifact_envelope(envelope) is False
