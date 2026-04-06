# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation import DocumentSchema
from bijux_proteomics_lab import evaluate_lab_schema_compatibility


def test_evaluate_lab_schema_compatibility_accepts_default_schema() -> None:
    report = evaluate_lab_schema_compatibility(DocumentSchema(created_by="tester"))

    assert report.compatible is True
    assert any("minimum compatibility requirement" in note for note in report.notes)
