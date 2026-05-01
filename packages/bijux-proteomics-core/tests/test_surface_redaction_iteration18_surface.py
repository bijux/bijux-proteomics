# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.collaboration_iteration18 import (
    CollaborationSurfaceRedactionInput,
    redact_collaboration_surfaces,
)


def test_redact_collaboration_surfaces_masks_secrets_and_paths() -> None:
    report = redact_collaboration_surfaces(
        CollaborationSurfaceRedactionInput(
            log_lines=(
                "read /Users/alice/raw/run01.mzML with token=abc123",
            ),
            api_errors=(
                "failed request: api_key=topsecret path=/tmp/private.tsv",
            ),
            evidence_notes=(
                "evidence pointer kept; password=hunter2",
            ),
            review_packet_notes=(
                "Bearer qwerty-987 checked against /var/tmp/bundle.json",
            ),
        )
    )

    assert "<redacted-secret>" in report.log_lines[0]
    assert "<redacted-path>" in report.log_lines[0]
    assert "evidence pointer kept" in report.evidence_notes[0]
    assert "<redacted-secret>" in report.review_packet_notes[0]
    assert report.redaction_count >= 6
