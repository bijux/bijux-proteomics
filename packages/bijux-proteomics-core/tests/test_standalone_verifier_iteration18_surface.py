# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.collaboration_iteration18 import (
    StandaloneVerifierInput,
    run_standalone_bundle_verifier,
)


def test_run_standalone_bundle_verifier_rejects_absolute_artifact_paths() -> None:
    report = run_standalone_bundle_verifier(
        StandaloneVerifierInput(
            bundle_id="bundle-1",
            schema_refs=("schema.bundle.v1",),
            artifact_paths=("/tmp/local.bin",),
            hash_ledger_entries=("sha256:abc",),
        )
    )

    assert report.verified is False
    assert report.issues[0].code == "absolute_artifact_path"
