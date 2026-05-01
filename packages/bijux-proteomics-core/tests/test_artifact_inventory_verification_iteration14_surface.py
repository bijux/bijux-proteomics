# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.runtime_iteration14 import (
    ArtifactInventoryRecord,
    verify_workflow_artifact_inventory,
)


def test_verify_workflow_artifact_inventory_detects_hash_and_lineage_issues() -> None:
    report = verify_workflow_artifact_inventory(
        records=(
            ArtifactInventoryRecord(
                artifact_id="psm-1",
                path="/run/psm.tsv",
                role="psm_table",
                producing_step_id="search",
                schema_ref="schema.psm.v1",
                content_sha256="a" * 64,
                lineage_parent_ids=("spectra-1",),
            ),
        ),
        observed_hashes_by_path={"/run/psm.tsv": "b" * 64},
        allowed_schema_refs=("schema.psm.v1", "schema.qc.v1"),
    )

    assert report.verified is False
    codes = {issue.code for issue in report.issues}
    assert "hash_mismatch" in codes
    assert "missing_lineage_parent" in codes
