# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.collaboration import (
    RedactedCollaborationBundleInput,
    build_redacted_collaboration_bundle,
)


def test_build_redacted_collaboration_bundle_masks_sample_ids_and_paths() -> None:
    bundle = build_redacted_collaboration_bundle(
        RedactedCollaborationBundleInput(
            bundle_id="collab-1",
            sample_ids=("patient-007", "patient-008"),
            file_paths=("/private/run1/raw.mzml",),
            provenance_links=("ev-1",),
        )
    )

    assert bundle.redacted_sample_ids == ("SAMPLE_001", "SAMPLE_002")
    assert bundle.redacted_file_paths == ("<redacted-path-001>",)
