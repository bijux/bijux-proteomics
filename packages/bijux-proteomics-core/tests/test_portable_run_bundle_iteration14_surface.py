# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.runtime_iteration14 import (
    ArtifactInventoryRecord,
    build_portable_workflow_run_bundle,
)


def test_build_portable_workflow_run_bundle_rewrites_paths_and_hashes_manifest() -> None:
    bundle = build_portable_workflow_run_bundle(
        run_id="run-77",
        records=(
            ArtifactInventoryRecord(
                artifact_id="id-1",
                path="/mnt/cluster/study-a/psm.tsv",
                role="psm_table",
                producing_step_id="search",
                schema_ref="schema.psm.v1",
                content_sha256="a" * 64,
            ),
        ),
    )

    assert bundle.files[0].portable_path.startswith("artifacts/psm_table/")
    assert not bundle.files[0].portable_path.startswith("/")
    assert len(bundle.manifest_sha256) == 64
