# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.scale_iteration17 import (
    ReproducibilityReleaseRun,
    build_long_horizon_reproducibility_report,
)


def test_build_long_horizon_reproducibility_report_counts_drift_entries() -> None:
    report = build_long_horizon_reproducibility_report(
        (
            ReproducibilityReleaseRun(
                release_tag="v1.0.0",
                workflow_id="wf-main",
                output_fingerprint="a" * 16,
            ),
            ReproducibilityReleaseRun(
                release_tag="v1.1.0",
                workflow_id="wf-main",
                output_fingerprint="a" * 16,
            ),
            ReproducibilityReleaseRun(
                release_tag="v1.2.0",
                workflow_id="wf-main",
                output_fingerprint="b" * 16,
            ),
        )
    )

    assert report.drift_count == 1
