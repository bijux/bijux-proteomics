from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.artifact_schemas import (
    load_high_value_artifact_schemas,
    validate_high_value_artifact_schemas,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_high_value_artifact_schema_manifest_covers_curated_outputs() -> None:
    schemas = load_high_value_artifact_schemas(REPO_ROOT)
    document_kinds = {schema.document_kind for schema in schemas}

    assert len(schemas) == 11
    assert document_kinds == {
        "evidence_bundle",
        "workflow_runtime_export_bundle",
        "workflow_runtime_validation_report",
        "workflow_replay_proof_report",
        "proteomics_artifact_inventory",
        "review_ready_evidence_bundle",
        "label_free_provenance_bundle",
        "quant_reproducibility_manifest",
        "quant_artifact_bundle",
        "qc_evidence_manifest",
        "search_result_provenance_manifest",
    }


def test_high_value_artifact_schema_manifest_is_valid_for_current_repo() -> None:
    assert validate_high_value_artifact_schemas(REPO_ROOT) == ()
