# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation import DocumentSchema
from bijux_proteomics_lab import (
    LabArtifactSchemaContract,
    evaluate_lab_artifact_schema_contract,
    evaluate_lab_schema_compatibility,
)


def test_evaluate_lab_schema_compatibility_accepts_default_schema() -> None:
    report = evaluate_lab_schema_compatibility(DocumentSchema(created_by="tester"))

    assert report.compatible is True
    assert any("minimum compatibility requirement" in note for note in report.notes)


def test_evaluate_lab_artifact_schema_contract_checks_created_by_and_version() -> None:
    report = evaluate_lab_artifact_schema_contract(
        DocumentSchema(schema_version="1.0.0", created_by="bijux-proteomics-lab"),
        contract=LabArtifactSchemaContract(
            artifact_kind="plan",
            required_created_by="bijux-proteomics-lab",
            minimum_schema_version="1.0.0",
        ),
    )

    assert report.compatible is True
