# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.runtime.contracts import (
    ArtifactFormat,
    SchemaFormatContract,
    build_schema_format_contract,
    default_schema_format_contracts,
    evaluate_schema_format_contract,
)


def test_schema_format_contract_covers_default_transport_formats() -> None:
    contracts = default_schema_format_contracts(
        document_kind="evidence_bundle",
        schema_version="1.0.0",
    )

    assert [contract.artifact_format for contract in contracts] == [
        ArtifactFormat.JSON,
        ArtifactFormat.JSONL,
        ArtifactFormat.TSV,
        ArtifactFormat.ARTIFACT_BUNDLE,
    ]


def test_schema_format_contract_reports_version_or_hash_mismatch() -> None:
    contract = build_schema_format_contract(
        document_kind="review_packet",
        artifact_format=ArtifactFormat.JSON,
        schema_version="1.0.0",
    )

    incompatible = evaluate_schema_format_contract(
        contract,
        expected_schema_version="1.1.0",
        expected_hash_policy_id="different-policy",
    )

    assert incompatible.compatible is False
    assert len(incompatible.notes) == 2


def test_schema_format_contract_is_serializable() -> None:
    contract = SchemaFormatContract(
        document_kind="lab_plan",
        artifact_format=ArtifactFormat.ARTIFACT_BUNDLE,
        schema_version="1.0.0",
        hash_policy_id="scientific-object-sha256-v1",
    )

    assert contract.to_dict()["artifact_format"] == "artifact_bundle"
