# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation import DocumentSchema
from bijux_proteomics_knowledge import evaluate_schema_compatibility


def test_evaluate_schema_compatibility_reports_match_for_default_version() -> None:
    report = evaluate_schema_compatibility(
        DocumentSchema(
            schema_version="1.0.0",
            created_by="test",
        )
    )

    assert report.compatible is True
    assert any("minimum compatibility requirement" in note for note in report.notes)
