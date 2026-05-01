# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab_planning_iteration16 import (
    LimsExportInputRow,
    build_lims_oriented_export_bundle,
)


def test_build_lims_oriented_export_bundle_renders_caveat_column() -> None:
    bundle = build_lims_oriented_export_bundle(
        (
            LimsExportInputRow(
                sample_id="sample-1",
                assay_id="assay-a",
                request_id="req-9",
                priority="high",
                caveats=("advisory-only", "requires-control"),
            ),
        )
    )

    assert bundle.rows[0].caveat_text
    assert "sample_id\tassay_id\trequest_id\tpriority\tcaveats" in bundle.tsv_payload
