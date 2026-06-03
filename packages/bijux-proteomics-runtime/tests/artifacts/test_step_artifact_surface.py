# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics_runtime.artifacts import StepArtifact, build_step_artifact


def test_step_artifact_preserves_checksums_counts_and_schema_names() -> None:
    artifact = build_step_artifact(
        step_id="normalize-identifications",
        description="normalize imported identification rows",
        status="completed",
        input_payloads={
            "identifications": (
                {"peptide": "PEPTIDEK", "protein_ref": "P11111"},
                {"peptide": "PEPTIDER", "protein_ref": "Q22222"},
            ),
            "mapping_policy": {"collapse_isoforms": False},
        },
        output_payloads={
            "normalized_rows": (
                {"peptide": "PEPTIDEK", "protein_ref": "P11111"},
                {"peptide": "PEPTIDER", "protein_ref": "Q22222"},
            ),
        },
        entity_counts={"normalized_rows": 2},
        schema_names=("dda_search_hit_input", "normalized_identification_row"),
    )

    assert isinstance(artifact, StepArtifact)
    assert artifact.step_id == "normalize-identifications"
    assert artifact.status == "completed"
    assert set(artifact.input_checksums) == {"identifications", "mapping_policy"}
    assert set(artifact.output_checksums) == {"normalized_rows"}
    assert artifact.entity_counts == {"normalized_rows": 2}
    assert artifact.schema_names == (
        "dda_search_hit_input",
        "normalized_identification_row",
    )
    assert artifact.allowed_empty_reason is None


def test_step_artifact_requires_reason_when_all_outputs_are_empty() -> None:
    with pytest.raises(ValueError, match="allowed-empty reason"):
        build_step_artifact(
            step_id="qc-evidence",
            description="collect QC issues from imported rows",
            status="completed",
            input_payloads={"accepted_rows": ()},
            output_payloads={"qc_issues": ()},
            entity_counts={"qc_issues": 0},
            schema_names=("qc_issue_row",),
        )

    artifact = build_step_artifact(
        step_id="qc-evidence",
        description="collect QC issues from imported rows",
        status="completed",
        input_payloads={"accepted_rows": ()},
        output_payloads={"qc_issues": ()},
        entity_counts={"qc_issues": 0},
        schema_names=("qc_issue_row",),
        allowed_empty_reason="no imported rows violated the QC rule set",
    )

    assert artifact.allowed_empty_reason == "no imported rows violated the QC rule set"
