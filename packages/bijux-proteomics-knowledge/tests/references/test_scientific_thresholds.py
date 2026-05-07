# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.lookups import (
    get_benchmark_manifest,
)
from bijux_proteomics_knowledge.references.workflows.scientific_thresholds import (
    build_decision_outcome_audit_report,
    build_workflow_threshold_evidence_report,
)


def test_workflow_threshold_evidence_report_anchors_thresholds_to_manifest() -> None:
    manifest = get_benchmark_manifest("benchmark:targeted_transition_quality_control")
    assert manifest is not None

    report = build_workflow_threshold_evidence_report(manifest)

    assert report.workflow_family.value == "targeted"
    assert report.entries
    assert any(entry.threshold_id == "transition_interference_boundary" for entry in report.entries)
    assert all(entry.benchmark_ids for entry in report.entries)


def test_decision_outcome_audit_report_tracks_follow_up_outcomes() -> None:
    manifest = get_benchmark_manifest("benchmark:dia_library_extraction_consistency")
    assert manifest is not None

    report = build_decision_outcome_audit_report(manifest)

    assert report.workflow_family.value == "dia"
    assert report.entries
    assert 0.0 <= report.trustworthy_decision_ratio <= 1.0
    assert "recommendation audits" in report.note.lower()
