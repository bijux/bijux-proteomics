# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics_lab as lab
from bijux_proteomics_lab.charter import (
    DEFAULT_LAB_MODULE_AUDIT,
    LabModuleClassification,
)


def test_lab_root_exposes_operational_behavior_beyond_packet_models() -> None:
    required_callables = tuple(lab.__all__)

    assert all(callable(getattr(lab, name)) for name in required_callables)


def test_lab_module_audit_requires_substantial_operational_surface() -> None:
    operational_modules = [
        entry
        for entry in DEFAULT_LAB_MODULE_AUDIT
        if entry.classification is LabModuleClassification.OPERATIONAL_VALUE
    ]

    assert len(operational_modules) >= 8


def test_lab_root_stays_curated_to_four_operational_entrypoints() -> None:
    assert tuple(lab.__all__) == (
        "plan_experiment_batches",
        "build_review_packet",
        "build_advisory_assay_plan",
        "build_executable_assay_plan",
    )


def test_lab_module_audit_keeps_multiple_operational_owner_modules() -> None:
    operational_paths = {
        entry.module_path
        for entry in DEFAULT_LAB_MODULE_AUDIT
        if entry.classification is LabModuleClassification.OPERATIONAL_VALUE
    }

    assert "planning/assays.py" in operational_paths
    assert "handoffs/transitions.py" in operational_paths
    assert "handoffs/explanations.py" in operational_paths
    assert "handoffs/exports.py" in operational_paths
    assert "benchmarks/claims.py" in operational_paths
    assert "benchmarks/rehearsals.py" in operational_paths
