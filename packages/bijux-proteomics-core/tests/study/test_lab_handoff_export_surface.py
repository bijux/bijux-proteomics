# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.study import (
    LabRequestSchema,
    LabRequestTarget,
    PlateLayoutEntry,
    build_lab_handoff_export_bundle,
)


def test_build_lab_handoff_export_bundle_renders_json_and_tsv_labels() -> None:
    bundle = build_lab_handoff_export_bundle(
        LabRequestSchema(
            request_id="req-001",
            method="prm",
            target_entries=(
                LabRequestTarget(
                    target_id="target-1",
                    assay_type="PTM_validation",
                    expected_evidence=("fragment_ion_series",),
                ),
            ),
            sample_ids=("sample-01",),
            control_ids=("ctrl-01",),
            constraints=("max_run_minutes=30",),
        ),
        (
            PlateLayoutEntry(
                sample_id="sample-01",
                replicate_id="R1",
                well_position="A1",
                control=False,
                randomized=True,
            ),
        ),
    )

    assert '"label":"advisory"' in bundle.request_json
    assert (
        "sample_id\treplicate_id\twell_position\tcontrol\trandomized\tlabel"
        in bundle.plate_layout_tsv
    )
    assert "\texecutable" in bundle.plate_layout_tsv
    assert bundle.advisory_label == "advisory"
    assert bundle.executable_label == "executable"
