# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation import DocumentSchema
from bijux_proteomics_lab import (
    ExperimentPlan,
    build_canonical_artifact_envelope,
    diff_model_payloads,
    fingerprint_model,
    to_canonical_json,
)


def test_lab_canonical_serialization_and_fingerprint_are_stable() -> None:
    plan = ExperimentPlan(program_id="prog-ser")
    canonical = to_canonical_json(plan)
    digest_a = fingerprint_model(plan)
    digest_b = fingerprint_model(plan)

    assert canonical.startswith("{")
    assert digest_a == digest_b


def test_diff_model_payloads_reports_changed_fields() -> None:
    left = ExperimentPlan(program_id="prog-ser", evidence_gaps=["structure"])
    right = ExperimentPlan(program_id="prog-ser", evidence_gaps=["structure", "cellular"])

    diff = diff_model_payloads(left, right)

    assert diff["added_fields"] == []
    assert diff["removed_fields"] == []
    assert diff["changed_fields"] == ["evidence_gaps"]


def test_build_canonical_artifact_envelope_includes_schema_and_fingerprint() -> None:
    plan = ExperimentPlan(program_id="prog-env")
    envelope = build_canonical_artifact_envelope(
        plan,
        artifact_kind="plan",
        schema=DocumentSchema(created_by="bijux-proteomics-lab"),
    )

    assert envelope["artifact_kind"] == "plan"
    assert "fingerprint" in envelope
    assert "schema" in envelope
