# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation import DocumentSchema
from bijux_proteomics_lab.handoffs.artifacts import (
    LabArtifactSchemaContract,
    LabArtifactContractRegistry,
    build_lab_artifact_upgrade_advisory,
    evaluate_lab_artifact_compatibility,
    evaluate_lab_artifact_schema_contract,
    evaluate_lab_artifact_with_registry,
    lint_lab_artifact_contract_registry,
)


def test_evaluate_lab_artifact_compatibility_accepts_default_schema() -> None:
    report = evaluate_lab_artifact_compatibility(DocumentSchema(created_by="tester"))

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


def test_evaluate_lab_artifact_with_registry_flags_unknown_kind() -> None:
    report = evaluate_lab_artifact_with_registry(
        DocumentSchema(schema_version="1.0.0", created_by="bijux-proteomics-lab"),
        artifact_kind="decision-log",
    )

    assert report.compatible is False
    assert "no schema contract registered" in report.notes[0]


def test_build_lab_artifact_upgrade_advisory_recommends_upgrade_for_old_schema() -> (
    None
):
    advisory = build_lab_artifact_upgrade_advisory(
        DocumentSchema(schema_version="0.9.0", created_by="bijux-proteomics-lab")
    )

    assert advisory.action == "upgrade"


def test_lint_lab_artifact_contract_registry_detects_duplicate_artifact_kinds() -> None:
    issues = lint_lab_artifact_contract_registry(
        LabArtifactContractRegistry(
            contracts=[
                LabArtifactSchemaContract(
                    artifact_kind="plan",
                    required_created_by="bijux-proteomics-lab",
                    minimum_schema_version="1.0.0",
                ),
                LabArtifactSchemaContract(
                    artifact_kind="plan",
                    required_created_by="bijux-proteomics-lab",
                    minimum_schema_version="1.0.0",
                ),
            ]
        )
    )

    assert any(issue.code == "duplicate-artifact-kind" for issue in issues)
