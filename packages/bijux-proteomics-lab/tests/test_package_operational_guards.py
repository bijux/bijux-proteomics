# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics_lab as lab
from bijux_proteomics_lab.charter import (
    DEFAULT_LAB_MODULE_AUDIT,
    LabModuleClassification,
)


def test_lab_root_exposes_operational_behavior_beyond_packet_models() -> None:
    required_callables = (
        "build_executable_assay_plan",
        "schedule_experiment_plan",
        "build_operational_readiness_report",
        "build_follow_up_practicality_report",
        "build_lab_protocol_evidence_bundle",
        "build_lims_export_bundle",
        "build_targeted_benchmark_report",
        "build_targeted_failure_rehearsal",
        "build_targeted_external_review_report",
        "build_targeted_operator_run_report",
        "build_operational_follow_up_path",
        "review_targeted_transition_candidates",
        "validate_candidate_follow_up_handoff",
        "promote_outcome_to_evidence",
        "recommend_rerun_policy",
    )

    assert all(callable(getattr(lab, name)) for name in required_callables)


def test_lab_module_audit_requires_substantial_operational_surface() -> None:
    operational_modules = [
        entry
        for entry in DEFAULT_LAB_MODULE_AUDIT
        if entry.classification is LabModuleClassification.OPERATIONAL_VALUE
    ]

    assert len(operational_modules) >= 8


def test_lab_root_is_not_dominated_by_packet_and_report_exports() -> None:
    root_exports = tuple(lab.__all__)
    behavior_exports = [
        name
        for name in root_exports
        if callable(getattr(lab, name, None))
        and not name.startswith("test_")
    ]
    schema_like_exports = [
        name
        for name in root_exports
        if name.endswith(("Packet", "Report", "Bundle", "Metadata"))
    ]

    assert len(behavior_exports) > len(schema_like_exports) / 2


def test_lab_root_keeps_new_operational_surfaces_public() -> None:
    assert "build_protocol_attachment" in lab.__all__
    assert "build_operational_readiness_report" in lab.__all__
    assert "build_follow_up_practicality_report" in lab.__all__
    assert "build_lims_export_bundle" in lab.__all__
    assert "build_targeted_benchmark_report" in lab.__all__
    assert "build_targeted_failure_rehearsal" in lab.__all__
    assert "build_targeted_external_review_report" in lab.__all__
    assert "build_targeted_operator_run_report" in lab.__all__
    assert "build_operational_follow_up_path" in lab.__all__
    assert "review_targeted_transition_candidates" in lab.__all__
    assert "validate_candidate_follow_up_handoff" in lab.__all__
