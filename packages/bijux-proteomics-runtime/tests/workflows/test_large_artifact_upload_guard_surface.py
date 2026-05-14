# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.workflows.reproducibility import (
    ArtifactTrustLevel,
    LargeArtifactUploadDescriptor,
    LargeArtifactUploadGuardPolicy,
    guard_large_artifact_uploads,
)


def test_guard_large_artifact_uploads_refuses_large_untrusted_artifact() -> None:
    report = guard_large_artifact_uploads(
        artifacts=(
            LargeArtifactUploadDescriptor(
                artifact_name="run01.mzml",
                format_name="mzml",
                file_size_bytes=900_000_000,
                trust_level=ArtifactTrustLevel.UNTRUSTED,
                content_sha256="a" * 64,
            ),
        ),
        policy=LargeArtifactUploadGuardPolicy(
            max_size_bytes_total=1_000_000_000,
            max_size_bytes_by_format={"mzml": 1_000_000_000},
            allowed_formats=("mzml", "mgf", "tsv"),
            max_untrusted_size_bytes=500_000_000,
        ),
    )

    assert report.accepted is False
    assert report.decisions[0].accepted is False
    assert "untrusted artifact exceeds max_untrusted_size_bytes policy threshold" in (
        report.decisions[0].reasons
    )
